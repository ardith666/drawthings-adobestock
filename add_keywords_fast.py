#!/usr/bin/env python3
"""Add keywords to existing JPEGs using keyword extraction from prompt text."""
import json, subprocess, re
from pathlib import Path

OUT_DIR = Path.home() / "Documents" / "drawthings" / "2026-07-28_073545"

# Generate minimum 15 keywords per prompt by splitting/expanding
def prompt_to_keywords(prompt):
    # Split description into individual keywords
    parts = re.split(r"[,.]", prompt)
    keywords = set()
    for p in parts:
        p = p.strip()
        if not p:
            continue
        keywords.add(p.lower())
        # Add individual words
        for w in p.split():
            w = w.strip().lower()
            if len(w) > 2 and w not in ["and", "the", "for", "with", "style", "high", "ultra", "macro"]:
                keywords.add(w)
    
    # Add Adobe Stock stock photo keywords
    kw_list = list(keywords)
    
    # Ensure minimum 16 keywords by adding common stock photo keywords
    fallbacks = ["abstract", "background", "design", "pattern", "texture", "wallpaper", 
                 "decorative", "ornamental", "modern", "contemporary", "creative", "artistic",
                 "high resolution", "digital art", "graphic design", "visual", "aesthetic",
                 "seamless", "luxury", "elegant", "professional", "print", "poster",
                 "decoration", "style", "colorful", "beautiful", "artwork", "illustration",
                 "element", "motif", "ornament", "detail", "close up"]
    
    for fb in fallbacks:
        if len(kw_list) >= 20:
            break
        if fb not in kw_list:
            kw_list.append(fb)
    
    # Remove duplicates while preserving order
    seen = set()
    result = []
    for kw in kw_list:
        if kw not in seen:
            seen.add(kw)
            result.append(kw)
    
    return ", ".join(result[:20])

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

def main():
    files = sorted(OUT_DIR.glob("image_*.jpg"))
    count = 0
    for fp in files:
        n = int(fp.stem.split("_")[1])
        prompt = PROMPTS[n - 1] if n <= len(PROMPTS) else ""
        
        # Skip if keywords exist
        kw_check = subprocess.run(["exiftool", "-XMP-dc:Subject", str(fp)], capture_output=True, text=True, timeout=10)
        if "Subject" in kw_check.stdout:
            existing = kw_check.stdout.split("Subject:", 1)[-1].strip() if "Subject:" in kw_check.stdout else ""
            if existing and len(existing) > 10:
                print(f"[{n}] SKIP (has keywords)")
                continue
        
        keywords = prompt_to_keywords(prompt)
        cmd = ["exiftool", "-overwrite_original", f"-XMP-dc:Subject={keywords}", str(fp)]
        subprocess.run(cmd, capture_output=True, timeout=10)
        kw_count = len(keywords.split(","))
        print(f"[{n}] Added {kw_count} keywords: {keywords[:80]}...")
        count += 1
    
    print(f"\nDone: {count} images updated")

if __name__ == "__main__":
    main()
