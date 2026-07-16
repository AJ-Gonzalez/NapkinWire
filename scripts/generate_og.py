#!/usr/bin/env python3
"""Generate NapkinWire Open Graph / social preview cards with PIL.

Composition: site background color, the app logo centered, the
"NapkinWire" wordmark and the "From sketch to prompt in seconds"
tagline beneath it. One 1200x630 card covers both `og:image` and
Twitter `summary_large_image`.

Re-run after changing the logo or copy; output is deterministic.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
LOGO_PATH = WEB / "icon-512.png"
OUT_PATH = WEB / "og-image.png"

# Brand palette (kept in sync with web/style.css :root)
BG = (0x1A, 0x1E, 0x16)        # --bg
FG = (0xE8, 0xE6, 0xD8)        # --fg (wordmark)
TAGLINE = (0x9A, 0x9A, 0x8A)   # .tagline color
ACCENT = (0x16, 0x65, 0x34)    # --button_bg / theme_color
BORDER = (0x3A, 0x3F, 0x33)    # --border

# Inter.ttc face indices (probed via ImageFont.getname()).
INTER_DISPLAY_BLACK = 18
INTER_MEDIUM_ITALIC = 11

CARD_W, CARD_H = 1200, 630

# Safe-zone padding: platforms crop ~5% off the edges.
SAFE = 60


def load_font(size: int, index: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype("/usr/share/fonts/truetype/Inter.ttc", size, index=index)


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont):
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    return r - l, b - t


def centered_text(draw, text, font, fill, cx, y):
    w, h = text_size(draw, text, font)
    draw.text((cx - w / 2, y), text, font=font, fill=fill)
    return h


def main():
    card = Image.new("RGB", (CARD_W, CARD_H), BG)
    draw = ImageDraw.Draw(card)

    # --- Logo ----------------------------------------------------------
    logo = Image.open(LOGO_PATH).convert("RGBA")
    logo_size = 300
    logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
    # Paste with alpha composite onto an RGBA copy, then flatten back.
    card_rgba = card.convert("RGBA")
    lx = (CARD_W - logo_size) // 2
    ly = SAFE + 10
    card_rgba.alpha_composite(logo, (lx, ly))
    card = card_rgba.convert("RGB")
    draw = ImageDraw.Draw(card)

    # --- Wordmark ------------------------------------------------------
    wordmark = "NapkinWire"
    wm_font = load_font(82, INTER_DISPLAY_BLACK)
    wm_h = centered_text(draw, wordmark, wm_font, FG, CARD_W // 2, ly + logo_size + 26)

    # --- Accent divider ------------------------------------------------
    divider_y = ly + logo_size + 26 + wm_h + 22
    divider_w = 140
    draw.rectangle(
        [(CARD_W // 2 - divider_w // 2, divider_y),
         (CARD_W // 2 + divider_w // 2, divider_y + 5)],
        fill=ACCENT,
    )

    # --- Tagline -------------------------------------------------------
    tagline = "From sketch to prompt in seconds"
    tag_font = load_font(38, INTER_MEDIUM_ITALIC)
    centered_text(draw, tagline, tag_font, TAGLINE, CARD_W // 2, divider_y + 24)

    # --- Subtle inner frame (within safe zone) ------------------------
    draw.rectangle(
        [(SAFE, SAFE), (CARD_W - SAFE, CARD_H - SAFE)],
        outline=BORDER, width=2,
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    card.save(OUT_PATH, "PNG", optimize=True)
    print(f"wrote {OUT_PATH} ({CARD_W}x{CARD_H})")


if __name__ == "__main__":
    main()
