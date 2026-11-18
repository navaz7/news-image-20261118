#!/usr/bin/env python3
"""Compose entry.png — a newspaper front page summing up 18 November 2026.

Layout: masthead + date line, hero story (summit), two story panels,
a second row (cyclone + a text-led health story) and a navy ticker band.
All text is shrink-to-fit wrapped so nothing overflows its box.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ART = HERE.parents[1] / "art"  # .../news-image/art (script lives in work/<repo>/)
OUT = HERE / "entry.png"

W = H = 1024
MARGIN = 36
CW = W - 2 * MARGIN  # content width = 952

CREAM = (244, 236, 216)
NAVY = (20, 33, 61)
CRIMSON = (179, 32, 44)
PAPER_PANEL = (250, 246, 235)

FONT_DIR = Path("/usr/share/fonts/truetype")
SERIF_BLACK = [
    FONT_DIR / "noto/NotoSerifDisplay-Black.ttf",
    FONT_DIR / "dejavu/DejaVuSerif-Bold.ttf",
]
SANS_BLACK = [
    FONT_DIR / "noto/NotoSansDisplay-Black.ttf",
    FONT_DIR / "dejavu/DejaVuSans-Bold.ttf",
]
SANS_BOLD = [
    FONT_DIR / "noto/NotoSans-Bold.ttf",
    FONT_DIR / "dejavu/DejaVuSans-Bold.ttf",
]
SANS = [
    FONT_DIR / "noto/NotoSans-Regular.ttf",
    FONT_DIR / "dejavu/DejaVuSans.ttf",
]


def font(candidates, size):
    for p in candidates:
        if p.exists():
            return ImageFont.truetype(str(p), size)
    raise FileNotFoundError(candidates)


def text_w(draw, s, f):
    return draw.textlength(s, font=f)


def fit_one_line(draw, s, candidates, max_w, start, minimum=12):
    """Largest font (<= start) whose single line fits max_w."""
    size = start
    while size > minimum:
        f = font(candidates, size)
        if text_w(draw, s, f) <= max_w:
            return f
        size -= 1
    return font(candidates, minimum)


def wrap(draw, s, f, max_w):
    words, lines, cur = s.split(), [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if text_w(draw, trial, f) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_wrapped(draw, s, candidates, max_w, max_lines, start, minimum=11):
    """Largest font whose wrapped text fits within max_lines lines."""
    size = start
    while size > minimum:
        f = font(candidates, size)
        lines = wrap(draw, s, f, max_w)
        if len(lines) <= max_lines:
            return f, lines
        size -= 1
    f = font(candidates, minimum)
    return f, wrap(draw, s, f, max_w)[:max_lines]


def line_h(f, ratio=1.22):
    return int(f.size * ratio)


def draw_lines(draw, lines, f, x, y, fill, lh=None, anchor_center_x=None):
    lh = lh or line_h(f)
    for ln in lines:
        if anchor_center_x is not None:
            draw.text((anchor_center_x - text_w(draw, ln, f) / 2, y), ln, font=f, fill=fill)
        else:
            draw.text((x, y), ln, font=f, fill=fill)
        y += lh
    return y


def draw_tracked(draw, s, f, cx, y, fill, tracking=4):
    """Draw text centered at cx with extra letter tracking."""
    widths = [text_w(draw, ch, f) for ch in s]
    total = sum(widths) + tracking * (len(s) - 1)
    x = cx - total / 2
    for ch, wch in zip(s, widths):
        draw.text((x, y), ch, font=f, fill=fill)
        x += wch + tracking
    return y + line_h(f)


def crop_to_fill(img, tw, th, fx=0.5, fy=0.5):
    """Center-crop (around focus point fx, fy in 0..1) to fill tw x th."""
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale + 0.5), int(sh * scale + 0.5)
    img = img.resize((nw, nh), Image.LANCZOS)
    x0 = min(max(int(fx * nw - tw / 2), 0), nw - tw)
    y0 = min(max(int(fy * nh - th / 2), 0), nh - th)
    return img.crop((x0, y0, x0 + tw, y0 + th))


def paste_art(page, draw, name, box, fx=0.5, fy=0.5):
    x, y, w, h = box
    art = Image.open(ART / name).convert("RGB")
    page.paste(crop_to_fill(art, w, h, fx, fy), (x, y))
    draw.rectangle([x, y, x + w - 1, y + h - 1], outline=NAVY, width=2)


def panel(page, draw, x, y, w, row_h, art_name, headline, sub, fx=0.5, fy=0.5):
    """Image panel: art strip on top, headline, subline. Returns bottom y."""
    art_h = 84
    paste_art(page, draw, art_name, (x, y, w, art_h), fx, fy)
    cy = y + art_h + 8
    hf, hlines = fit_wrapped(draw, headline, SERIF_BLACK, w, 2, 26, 18)
    cy = draw_lines(draw, hlines, hf, x, cy, NAVY, lh=line_h(hf, 1.22))
    sf, slines = fit_wrapped(draw, sub, SANS, w, 2, 17, 13)
    draw_lines(draw, slines, sf, x, cy + 2, NAVY, lh=line_h(sf, 1.18))
    return y + row_h


def text_panel(draw, x, y, w, row_h, kicker, headline, sub):
    """Text-led panel with a crimson kicker, vertically balanced."""
    draw.rectangle([x, y, x + w - 1, y + row_h - 1], fill=PAPER_PANEL, outline=CRIMSON, width=2)
    pad = 16
    cx = x + pad
    cw = w - 2 * pad
    cy = y + 12
    kf = font(SANS_BLACK, 15)
    draw.text((cx, cy), kicker, font=kf, fill=CRIMSON)
    cy += line_h(kf, 1.1) + 2
    hf, hlines = fit_wrapped(draw, headline, SERIF_BLACK, cw, 2, 27, 19)
    cy = draw_lines(draw, hlines, hf, cx, cy, NAVY, lh=line_h(hf, 1.22))
    sf, slines = fit_wrapped(draw, sub, SANS, cw, 3, 17, 13)
    draw_lines(draw, slines, sf, cx, cy + 3, NAVY, lh=line_h(sf, 1.2))


def main():
    page = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(page)
    cx = W // 2

    # --- Masthead -------------------------------------------------------
    draw.line([(MARGIN, 26), (W - MARGIN, 26)], fill=NAVY, width=2)
    mf = fit_one_line(draw, "THE WORLD TODAY", SERIF_BLACK, CW, 112)
    y = 36
    draw.text((cx - text_w(draw, "THE WORLD TODAY", mf) / 2, y),
              "THE WORLD TODAY", font=mf, fill=NAVY)
    y += line_h(mf, 1.04)
    draw.rectangle([MARGIN, y + 2, W - MARGIN, y + 8], fill=CRIMSON)
    y += 16

    # --- Date line ------------------------------------------------------
    df = fit_one_line(draw, "WEDNESDAY · 18 NOVEMBER 2026", SANS_BLACK, CW - 40, 36)
    y = draw_tracked(draw, "WEDNESDAY · 18 NOVEMBER 2026", df, cx, y, NAVY, tracking=3)
    draw.line([(MARGIN, y + 2), (W - MARGIN, y + 2)], fill=NAVY, width=2)
    y += 14

    # --- Hero -----------------------------------------------------------
    hero_h = 208
    paste_art(page, draw,
              "media-generation-art-summit-0-99204868-b5da-4b19-a4f8-ff32c0522e62.png",
              (MARGIN, y, CW, hero_h), fx=0.5, fy=0.56)
    y += hero_h + 12
    hf = fit_one_line(draw, "THREE PRESIDENTS, ONE TABLE", SERIF_BLACK, CW, 50)
    draw.text((cx - text_w(draw, "THREE PRESIDENTS, ONE TABLE", hf) / 2, y),
              "THREE PRESIDENTS, ONE TABLE", font=hf, fill=NAVY)
    y += line_h(hf, 1.06) + 2
    sf, slines = fit_wrapped(
        draw, "Trump flies to Shenzhen for a first-ever summit with Xi and Putin",
        SANS_BOLD, CW, 1, 25, 16)
    y = draw_lines(draw, slines, sf, 0, y, NAVY, lh=line_h(sf, 1.15), anchor_center_x=cx)
    y += 8
    draw.line([(MARGIN, y), (W - MARGIN, y)], fill=NAVY, width=2)
    y += 12

    # --- Story rows -----------------------------------------------------
    ticker_h = 104
    rows_top = y
    row_h = (H - ticker_h - rows_top - 14) // 2
    col_w = (CW - 48) // 2
    col2_x = MARGIN + col_w + 48
    div_x = MARGIN + col_w + 24

    panel(page, draw, MARGIN, rows_top, col_w, row_h,
          "media-generation-art-bridge-0-b85adaa7-5f74-4fd0-8a22-937953905a83.png",
          "CRIMEA BRIDGE HIT AGAIN",
          "Ukraine strikes Putin's prized bridge; Russia answers on Kyiv's crossings",
          fx=0.56, fy=0.58)
    panel(page, draw, col2_x, rows_top, col_w, row_h,
          "media-generation-art-chip-0-00589081-fb68-4ec7-b6e0-423e78eeb77b.png",
          "NVIDIA TOPS $100 BILLION",
          "Sales double as the AI chip race heats up",
          fx=0.5, fy=0.5)
    draw.line([(div_x, rows_top + 4), (div_x, rows_top + row_h - 6)], fill=NAVY, width=1)

    row2_y = rows_top + row_h + 14
    draw.line([(MARGIN, row2_y - 8), (W - MARGIN, row2_y - 8)], fill=NAVY, width=1)
    panel(page, draw, MARGIN, row2_y, col_w, row_h,
          "media-generation-art-cyclone-0-18e624c2-afc3-42a9-b502-3ab2d8b6d963.png",
          "CYCLONE AKVAN CLOSES IN",
          "200,000 moved to safety as the storm aims at India's Andhra coast",
          fx=0.5, fy=0.45)
    text_panel(draw, col2_x, row2_y, col_w, row_h,
               "HEALTH · UNITED STATES",
               "AMERICA LOSES MEASLES-FREE STATUS",
               "5,400 cases this year — the worst outbreak in three decades")

    # --- Ticker ---------------------------------------------------------
    ty = H - ticker_h
    draw.rectangle([0, ty, W, H], fill=NAVY)
    draw.rectangle([0, ty, W, ty + 5], fill=CRIMSON)
    ticker = ("IN BRIEF — 200 top websites hacked in a global cyber wave · "
              "Russian military plane down in Siberia, 19 dead · "
              "Gold slides to a one-year low · "
              "India beat Pakistan 2–1 to lift a record 10th SAFF crown")
    tf, tlines = fit_wrapped(draw, ticker, SANS_BOLD, CW, 2, 21, 14)
    total_h = line_h(tf, 1.25) * len(tlines)
    draw_lines(draw, tlines, tf, MARGIN, ty + (ticker_h - total_h) // 2 + 2,
               CREAM, lh=line_h(tf, 1.25))

    page.save(OUT, optimize=True)
    size = OUT.stat().st_size
    print(f"saved {OUT} {page.size} {size} bytes")
    if size > 1024 * 1024:
        q = page.quantize(colors=256, method=Image.MEDIANCUT)
        q.save(OUT, optimize=True)
        print(f"quantized -> {OUT.stat().st_size} bytes")


if __name__ == "__main__":
    main()
