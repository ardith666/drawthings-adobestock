# Skill: drawthings-adobestock

Generate stock images via DrawThings API, upscale to 4MP, embed XMP, save. Start with discussion about quantity and theme.

## Conversation Flow

When user invokes this skill:

1. **Ask:** "Mau berapa gambar?" and "Tema/deskripsi apa?"
2. Or suggest themes from Adobe Stock Contributor Insights
3. **Ask format:** "JPG atau transparent PNG?"
   - **JPG** → tanya background: "Putih atau random?" Random = random vibrant color gradient
   - **Transparent PNG** → pakai LoRA `layer_xl_transparent_attn_v1.0_lora_f16.ckpt`, render di black bg, post-process shadow
4. Ask about shadow (if PNG): "Tambahkan dramatic shadow?" default yes
5. Generate with agreed settings into new folder per batch

## DrawThings API

- Endpoint: http://localhost:7860/sdapi/v1/txt2img
- Model: juggernaut_xl_x_q6p_q8p.ckpt
- Recommended: 1024x1024 steps=12 (~90s each), then upscale 2x
- Alternative: 1536x1536 steps=20 (~240s each), then upscale
- Seed mode: Scale Alike
- Timeout: Set 300s for draw, 120s for LLM
- LoRA syntax in prompt: `<lora:layer_xl_transparent_attn_v1.0_lora_f16.ckpt:1>`

### Request JSON (JPG)

```json
{
  "prompt": "...",
  "negative_prompt": "people, person, human, face, body, hands, fingers, text, watermark, logo",
  "width": 1024,
  "height": 1024,
  "steps": 12,
  "cfg_scale": 7.5,
  "seed": -1,
  "seed_mode": "Scale Alike",
  "model": "juggernaut_xl_x_q6p_q8p.ckpt"
}
```

### Request JSON (Transparent PNG)

```json
{
  "prompt": "<lora:layer_xl_transparent_attn_v1.0_lora_f16.ckpt:1> ... on pure black background",
  "negative_prompt": "people, person, human, hands, text, watermark, logo, white background, gray background",
  "width": 1024,
  "height": 1024,
  "steps": 12,
  "cfg_scale": 7.5,
  "seed": -1,
  "seed_mode": "Scale Alike",
  "model": "juggernaut_xl_x_q6p_q8p.ckpt"
}
```

## Workflow per Batch

### JPG Workflow
1. Create folder ~/Documents/drawthings/YYYYMMDD_HHMMSS/
2. Generate image via DrawThings API — use bg color in prompt if random, or "on white background" if white
3. Upscale 2x via Pillow LANCZOS to 2048x2048 (4MP)
4. Save as JPEG quality 95
5. Generate metadata (title + keywords) via LLM for-claw
6. Embed XMP via exiftool
7. Report to user when done

### Transparent PNG Workflow
1. Create folder ~/Documents/drawthings/YYYYMMDD_HHMMSS/
2. Generate image via DrawThings API with LoRA transparency + "on pure black background"
3. Decode RGBA — black bg becomes transparent alpha channel
4. Post-process: add dramatic shadow
   - Extract alpha channel
   - Offset alpha (default 25,25 px down-right)
   - Gaussian blur (default radius 12)
   - Darken shadow color (~85% opacity, dark purple-black)
   - Composite shadow layer behind object
5. Save as PNG (2048x2048 after upscale)
6. Generate metadata (title + keywords) via LLM
7. Embed XMP via exiftool
8. Report to user when done

### Resume Support

Script detects existing folder, counts images, skips existing files.

## Shadow Parameters (defaults)

| Parameter | Default | Notes |
|-----------|---------|-------|
| Offset X  | 25px    | Right shift |
| Offset Y  | 25px    | Down shift |
| Blur radius | 12px  | Soft dramatic |
| Shadow color | (20,15,30) | Dark purple-black |
| Opacity | 0.85 | 0-1 scale |

## LLM Metadata (for-claw)

Model is reasoning-heavy. Fix:
- max_tokens=1000 so reasoning doesn't eat all tokens
- Parse content field first, fallback to reasoning_content
- Temperature 0.1 with forceful system prompt
- Always use system -> user message structure

## XMP Embedding

```bash
# JPEG
exiftool -overwrite_original -XMP-dc:Title="Title" -XMP-dc:Subject="kw1, kw2, kw3" image.jpg

# PNG
exiftool -overwrite_original -XMP-dc:Title="Title" -XMP-dc:Subject="kw1, kw2, kw3" image.png
```

When uploaded to Adobe Stock, title and keywords auto-populate.

## Rules

1. No human content - no people, faces, body parts
2. Minimum 4MP - upscale to 2048x2048
3. Format: JPEG if JPG mode, PNG if transparent mode
4. XMP metadata embedded for auto-detection
5. New folder per batch: ~/Documents/drawthings/YYYYMMDD_HHMMSS/
6. User handles upload manually (captcha required)
7. Must check "Created using generative AI tools" on upload
8. Must check "People and Property are fictional" on upload

## Scripts (in workspace/scripts/)

- drawthings_batch.py - main batch generator with metadata
- add_keywords_fast.py - add keywords to existing JPEGs

## Session History

- 2026-07-26: First 30 images, browser automation tested
- 2026-07-27: Decided user handles upload manually
- 2026-07-28: 41 images generated with fixes: 1024+upscale, LLM tokens increased, API resume support
- 2026-07-29: Added transparent PNG support with LoRA + dramatic shadow post-processing