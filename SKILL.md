# Skill: drawthings-adobestock

Generate stock images via DrawThings API, upscale to 4MP, embed XMP, save. Start with discussion about quantity and theme.

## Conversation Flow

When user invokes this skill:

1. **Ask:** "Mau berapa gambar?" and "Tema/deskripsi apa?"
2. Or suggest themes from Adobe Stock Contributor Insights
3. Generate with agreed settings into new folder per batch

## DrawThings API

- Endpoint: http://localhost:7860/sdapi/v1/txt2img
- Model: juggernaut_xl_x_q6p_q8p.ckpt
- Recommended: 1024x1024 steps=12 (~90s each), then upscale 2x
- Alternative: 1536x1536 steps=20 (~240s each), then upscale
- Seed mode: Scale Alike
- Timeout: Set 300s for draw, 120s for LLM

### Request JSON

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

## Workflow per Batch

1. Create folder ~/Documents/drawthings/YYYY-MM-DD_HHMMSS/
2. Generate image via DrawThings API to base64 PNG
3. Upscale 2x via Pillow LANCZOS to 2048x2048 (4MP)
4. Save as JPEG quality 95
5. Generate metadata (title + keywords) via LLM for-claw
6. Embed XMP via exiftool
7. Report to user when done

### Resume Support

Script detects existing folder, counts images, skips existing files.

## LLM Metadata (for-claw)

Model is reasoning-heavy. Fix:
- max_tokens=1000 so reasoning doesn't eat all tokens
- Parse content field first, fallback to reasoning_content
- Temperature 0.1 with forceful system prompt
- Always use system -> user message structure

## XMP Embedding

exiftool -overwrite_original -XMP-dc:Title="Title" -XMP-dc:Subject="kw1, kw2, kw3" image.jpg

When uploaded to Adobe Stock, title and keywords auto-populate.

## Rules

1. No human content - no people, faces, body parts
2. Minimum 4MP - upscale to 2048x2048
3. JPEG format
4. XMP metadata embedded for auto-detection
5. New folder per batch: ~/Documents/drawthings/YYYY-MM-DD_HHMMSS/
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
