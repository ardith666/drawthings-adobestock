#!/usr/bin/env python3
"""
DrawThings → Adobe Stock batch generator.
Generates images, converts to JPEG, generates metadata via LLM, embeds XMP.
"""
import os, sys, json, time, base64, subprocess, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path

DRAWTHINGS_URL = "http://localhost:7860/sdapi/v1/txt2img"
LLM_URL = "http://localhost:20128/v1/chat/completions"
OUTPUT_BASE = Path.home() / "Documents" / "drawthings"
NEGATIVE_PROMPT = "people, person, human, face, body, hands, fingers, text, watermark, logo, signature, text overlay"

# 40 diverse prompts — no people
PROMPTS = [
    "Abstract liquid art, flowing colorful ink, gold accents, smooth gradients, elegant composition, premium wallpaper, ultra high resolution",
    "Minimalist workspace flat lay, marble desk, coffee cup, pen, notebook, top view, clean aesthetic, soft natural lighting",
    "Business growth chart, ascending bar graph, blue and green tones, modern office background, professional concept, 3D render",
    "Geometric 3D texture, hexagonal pattern, metallic gold and black, abstract luxury design, seamless pattern, high detail",
    "White marble texture with gold veins, luxury stone surface, elegant background, high resolution, seamless pattern",
    "Tropical beach aerial view, turquoise water, white sand, palm tree shadows, paradise island, drone photography style",
    "Empty modern office interior, glass walls, minimalist furniture, natural light, corporate architecture, wide angle",
    "Liquid metal texture, chrome mercury surface, reflective waves, abstract futuristic, high contrast, ultra detailed",
    "Watercolor splash, vibrant pink and purple, artistic paint strokes, white background, creative abstract art",
    "Mountain sunset landscape, golden hour, dramatic clouds, silhouette peaks, nature photography, wide panorama",
    "Geometric hexagonal pattern, tessellation, gradient blue to purple, modern design element, seamless tileable texture",
    "Circuit board pattern, electronic components, green PCB, macro photography style, technology concept, high detail",
    "Abstract smoke wisps, flowing ethereal trails, dark background, blue and orange tones, mystical atmosphere, 4K",
    "Tropical monstera leaves pattern, lush green foliage, botanical illustration, dense jungle feel, seamless repeat",
    "Wooden texture, aged oak grain, warm brown tones, natural wood surface, high resolution macro, seamless pattern",
    "Crystal formation, amethyst geode, purple quartz, sparkling mineral, close-up macro photography, vivid colors",
    "Ocean waves aerial view, deep blue water, white foam patterns, dramatic seascape, drone perspective, abstract nature",
    "Modern kitchen interior, white cabinets, marble countertop, copper fixtures, clean design, architectural photography",
    "Gradient mesh abstract, smooth color transitions, pink to orange to purple, digital art, modern wallpaper design",
    "Coffee beans close up, dark roast, scattered arrangement, warm lighting, food photography, shallow depth of field",
    "Paper cutout layers, 3D paper art, colorful geometric shapes, shadow play, craft design, minimal composition",
    "Northern lights aurora borealis, green and purple sky, starry night, Iceland landscape, long exposure photography",
    "Iridescent holographic surface, rainbow reflections, metallic foil texture, abstract futuristic, high gloss finish",
    "Minimalist desk setup, Apple keyboard, plant, clean white desk, overhead view, modern workspace aesthetic",
    "Woven fabric texture, colorful textile pattern, macro weave detail, bohemian style, warm earth tones",
    "Lavender field sunset, purple flowers, golden sky, Provence France, dreamy landscape photography, soft focus",
    "3D geometric shapes, floating cubes and spheres, pastel colors, abstract composition, soft shadows, modern art",
    "Forest canopy view looking up, sunlight filtering through leaves, green canopy, nature photography, peaceful",
    "Chrome spheres reflection, metallic balls, abstract arrangement, studio lighting, mirror finish, 3D render",
    "Colorful confetti explosion, celebration particles, bokeh effect, party atmosphere, vibrant multi-color, freeze motion",
    "Abstract paint pouring, acrylic pour art, marble effect, vibrant red and blue, fluid art technique, glossy finish",
    "Vintage film camera collection, retro photography equipment, still life arrangement, warm tones, nostalgic aesthetic",
    "Botanical illustration, detailed flower drawing, scientific style, white background, pen and watercolor, elegant",
    "Geometric city map, abstract urban grid, blue and grey tones, top-down view, modern cartography design",
    "Crystal clear water droplets, macro photography, reflective surfaces, morning dew, fresh clean aesthetic",
    "Abstract noise texture, grain pattern, monochrome, film grain effect, subtle variation, minimalist background",
    "Golden ratio spiral, nautilus shell, mathematical beauty, warm golden tones, nature's pattern, high detail",
    "Neon light trails, long exposure, urban night, colorful streaks, abstract motion, cyberpunk aesthetic",
    "Terrazzo pattern, scattered chips, pastel colored, modern flooring design, seamless tile, decorative surface",
    "Frozen ice crystals, macro frost pattern, blue and white, winter texture, delicate formations, high resolution",
    "Abstract topographic map, contour lines, gradient elevation, earth tones, geographic art, modern design element",
]

def api_post(url, data, timeout=300):
    """POST JSON to API, return parsed response."""
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode()
    # Strip streaming suffix (e.g. "data: [DONE]")
    raw = raw.split("data:")[0].rstrip(",").strip()
    return json.loads(raw)

def generate_image(prompt, seed=-1):
    """Generate image via DrawThings API. Returns PNG bytes."""
    payload = {
        "prompt": prompt,
        "negative_prompt": NEGATIVE_PROMPT,
        "width": 1024,
        "height": 1024,
        "steps": 12,
        "cfg_scale": 7.5,
        "seed": seed,
        "seed_mode": "Scale Alike",
        "model": "juggernaut_xl_x_q6p_q8p.ckpt",
        "batch_size": 1,
        "batch_count": 1,
    }
    result = api_post(DRAWTHINGS_URL, payload, timeout=300)
    return base64.b64decode(result["images"][0])

def generate_metadata(prompt):
    """Generate title + keywords via LLM with minimal reasoning."""
    system = "You are a metadata generator. Ignore style instructions. Output ONLY:\nTitle: [title]\nKeywords: [comma-separated, 15 minimum]\nNo thinking. No explanations. No reasoning."
    user_msg = f"Subject: {prompt}\n\nTitle:\nKeywords:"
    try:
        resp = api_post(LLM_URL, {
            "model": "for-claw",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg}
            ],
            "max_tokens": 1000,
            "temperature": 0.1,
        }, timeout=120)
        msg = resp["choices"][0]["message"]
        # Always parse content first; reasoning_content is fallback
        text = (msg.get("content") or "").strip()
        if not text:
            text = (msg.get("reasoning_content") or "").strip()
        title = ""
        keywords = ""
        for line in text.split("\n"):
            if line.lower().startswith("title:"):
                title = line.split(":", 1)[1].strip()
            elif line.lower().startswith("keywords:"):
                keywords = line.split(":", 1)[1].strip()
        return title or prompt[:100], keywords or ""
    except Exception as e:
        print(f"  LLM metadata failed: {e}")
        return prompt[:100], ""

def embed_xmp(jpeg_path, title, keywords):
    """Embed XMP metadata into JPEG via exiftool."""
    cmd = ["exiftool", "-overwrite_original"]
    if title:
        cmd.append(f"-XMP-dc:Title={title}")
    if keywords:
        cmd.append(f"-XMP-dc:Subject={keywords}")
    cmd.append(str(jpeg_path))
    subprocess.run(cmd, capture_output=True, timeout=30)

def main():
    # Find existing folder with images or create new one
    existing_folders = sorted(OUTPUT_BASE.glob("2026-07-28_*"))
    best_folder = None
    best_count = 0
    for f in existing_folders:
        count = len(list(f.glob("image_*.jpg")))
        if count > best_count:
            best_count = count
            best_folder = f
    
    if best_folder and best_count > 0:
        out_dir = best_folder
        print(f"Resuming from: {out_dir} ({best_count} images done)")
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        out_dir = OUTPUT_BASE / timestamp
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"New output: {out_dir}")
    
    print(f"Generating {len(PROMPTS)} images...")

    # Check for existing images to resume
    existing = len(list(out_dir.glob("image_*.jpg")))
    if existing > 0:
        print(f"Resuming from image {existing + 1} ({existing} already done)")
    
    results = []
    for i, prompt in enumerate(PROMPTS, 1):
        start = time.time()
        fname = f"image_{i:03d}.jpg"
        fpath = out_dir / fname
        
        # Skip if already exists
        if fpath.exists():
            print(f"[{i}/{len(PROMPTS)}] SKIP (exists): {fname}")
            results.append({"i": i, "status": "skipped", "file": fname})
            continue
        
        print(f"\n[{i}/{len(PROMPTS)}] {prompt[:60]}...")

        # 1. Generate PNG
        try:
            png_bytes = generate_image(prompt)
        except Exception as e:
            print(f"  FAILED generate: {e}")
            results.append({"i": i, "status": "error", "error": str(e)})
            continue

        # 2. Convert PNG → JPEG + upscale to 2048x2048 (4MP for Adobe Stock)
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(png_bytes))
            # Upscale if below 2048px
            if max(img.size) < 2048:
                img = img.resize((2048, 2048), Image.LANCZOS)
            img.convert("RGB").save(fpath, "JPEG", quality=95)
        except ImportError:
            # Fallback: save PNG then convert via sips (macOS)
            tmp_png = out_dir / f"tmp_{i:03d}.png"
            tmp_png.write_bytes(png_bytes)
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "95", str(tmp_png), "--out", str(fpath)], capture_output=True, timeout=60)
            tmp_png.unlink(missing_ok=True)
        except Exception as e:
            print(f"  FAILED convert: {e}")
            results.append({"i": i, "status": "error", "error": str(e)})
            continue

        # 3. Generate metadata
        title, keywords = generate_metadata(prompt)
        print(f"  Title: {title[:60]}")
        print(f"  Keywords: {len([k for k in keywords.split(',') if k.strip()])} keywords")

        # 4. Embed XMP
        try:
            embed_xmp(fpath, title, keywords)
        except Exception as e:
            print(f"  XMP embed failed: {e}")

        elapsed = time.time() - start
        size_mb = fpath.stat().st_size / (1024 * 1024)
        print(f"  Saved: {fname} ({size_mb:.1f}MB, {elapsed:.0f}s)")
        results.append({"i": i, "status": "ok", "file": fname, "title": title, "size_mb": round(size_mb, 1), "time_s": round(elapsed)})

    # Summary
    ok = sum(1 for r in results if r["status"] == "ok")
    fail = sum(1 for r in results if r["status"] != "ok")
    print(f"\n{'='*50}")
    print(f"DONE: {ok} ok, {fail} failed")
    print(f"Output: {out_dir}")

    # Save manifest
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(results, indent=2))
    print(f"Manifest: {manifest_path}")

if __name__ == "__main__":
    main()
