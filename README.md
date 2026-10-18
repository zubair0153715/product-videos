# Product Videos

Motion-graphics product promo video builder — reel-style 30s vertical videos
(1080×1920): hook → phone mockups → feature cards → "Comment LINK" CTA.

## Usage

```bash
python3 builder.py configs/<slug>.json <out_dir>
```

Needs: Python 3 + Pillow + gTTS + ffmpeg. (~2 min per video.)

## Layout

- `builder.py` — config-driven renderer (PIL stills + ffmpeg zoompan/drawtext + gTTS voiceover)
- `configs/<slug>.json` — one config per product (hook lines, phone screens, cards, CTA, voice script)
- `shoot.py` — headless-Chromium screenshot helper (for real app captures)

## Products

16 product videos built with this pipeline (Oct 2026), all in the
`your_files/` folder: PharmaReg AI, SecureAPK, Receptionist bot, Hotel PMS,
GEO Portal, No-Show Guard, Review Booster, Lead Qualifier, Self-Check,
LeadForge, MediScribe, PharmaAI, MedExplain, Style Advisor, PocketStat,
ZakatCalc PK.

Rendered MP4s/PNGs are build artifacts and are NOT committed here.
