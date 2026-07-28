# drawthings-adobestock

Generate Adobe Stock images via **DrawThings** API → upscale to 4MP → embed XMP metadata (title + keywords) → ready for upload.

## How It Works

1. DrawThings generates image at 1024×1024 (steps=12, ~90s)
2. Pillow upscales 2× to 2048×2048 (4MP minimum for Adobe Stock)
3. exiftool embeds XMP metadata (title + 15-20 keywords)
4. Saves to `~/Documents/drawthings/YYYY-MM-DD_HHMMSS/`
5. User uploads manually to [Adobe Stock Contributor](https://contributor.stock.adobe.com/en/uploads)

## Requirements

- [Draw Things](https://drawthings.ai) running with API server enabled (`localhost:7860`)
- Python 3 + Pillow (`pip3 install Pillow`)
- [exiftool](https://exiftool.org) (`brew install exiftool`)
- Optional: LLM endpoint at `localhost:20128/v1` for metadata generation

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | OpenClaw skill definition |
| `drawthings_batch.py` | Main batch generator + metadata |
| `add_keywords_fast.py` | Add keywords to existing JPEGs |

## Usage

```bash
# Generate 40 images (runs from OpenClaw workspace)
python3 drawthings_batch.py

# Add keywords to existing batch
python3 add_keywords_fast.py
```

Or invoke via OpenClaw: `drawthings-adobestock` — skill will ask quantity + theme first.

## License

MIT © 2026 ardith666 — see [LICENSE](LICENSE) for full text.

Covers scripts, skill definitions, and documentation in this repo.
Not covered: generated images (subject to Adobe Stock ToS), third-party dependencies.
