"""Turn source-photo.jpg into a self-typing ASCII portrait SVG.

1. cut the person out of the background (rembg, isnet-general-use)
2. crop to head + shoulders, boost local contrast (CLAHE)
3. map brightness to a glyph ramp, one <text> row per line
4. every row wipes in left-to-right with a cursor riding its edge
   (pure CSS keyframes - GitHub renders README SVGs as <img>, so no JS)

Run locally once (or whenever you change your photo):
    pip install -r scripts/requirements-portrait.txt
    python scripts/make_ascii_svg.py
"""
import os
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = next(p for p in (ROOT / "source-photo.jpg", ROOT / "source-photo.png") if p.exists())
CUTOUT = ROOT / "data" / "cutout.png"
OUT = ROOT / "ascii-portrait.svg"

COLS = int(os.environ.get("COLS", 76))
CROP = (0.20, 0.125, 0.86, 0.74)      # left, top, right, bottom as fractions of the photo
RAMP = " .'`^,:;Il!i~+_-?][}{1)(|tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
GAMMA = 0.85
CW, LH, FS = 6.0, 10.4, 10          # cell width, line height, font size
PAD = 14
ROW_DELAY = 0.045                    # seconds between rows starting
ROW_DUR = 0.32                       # seconds for one row to type in
BG = "#0d1117"
BORDER = "#30363d"
INK = "#c9d1d9"
CURSOR = "#3fb950"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,DejaVu Sans Mono,Liberation Mono,monospace"


def cutout() -> Image.Image:
    if CUTOUT.exists():
        return Image.open(CUTOUT)
    from rembg import new_session, remove
    img = remove(Image.open(SRC).convert("RGB"), session=new_session("isnet-general-use"))
    CUTOUT.parent.mkdir(exist_ok=True)
    img.save(CUTOUT)
    return img


def to_rows(img: Image.Image) -> list[str]:
    w, h = img.size
    l, t, r, b = CROP
    img = img.crop((int(l * w), int(t * h), int(r * w), int(b * h)))
    rgba = np.array(img)
    alpha = rgba[..., 3].astype(np.float32) / 255
    gray = cv2.cvtColor(rgba[..., :3], cv2.COLOR_RGB2GRAY)
    gray = cv2.createCLAHE(clipLimit=2.6, tileGridSize=(8, 8)).apply(gray)
    blur = cv2.GaussianBlur(gray, (0, 0), 6)
    gray = cv2.addWeighted(gray, 1.8, blur, -0.8, 0)   # unsharp mask: eyes, brows, beard pop

    cw, ch = img.size
    rows = int(round(COLS * (ch / cw) * (CW / LH)))
    g = cv2.resize(gray, (COLS, rows), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    a = cv2.resize(alpha, (COLS, rows), interpolation=cv2.INTER_AREA)

    # stretch the subject's own range so dark skin/hair still reads on a dark card
    inside = g[a > 0.5]
    lo, hi = np.percentile(inside, 2), np.percentile(inside, 99)
    g = np.clip((g - lo) / max(hi - lo, 1e-3), 0, 1) ** GAMMA
    g = 0.12 + 0.88 * g                       # nothing inside the subject drops to blank

    lines = []
    for y in range(rows):
        chars = []
        for x in range(COLS):
            if a[y, x] < 0.35:
                chars.append(" ")
            else:
                chars.append(RAMP[min(int(g[y, x] * (len(RAMP) - 1)), len(RAMP) - 1)])
        lines.append("".join(chars).rstrip())
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(lines: list[str]) -> str:
    W = PAD * 2 + COLS * CW
    H = PAD * 2 + 22 + len(lines) * LH
    static = os.environ.get("STATIC") == "1"
    css = "" if static else (
        "<style>"
        ".r{white-space:pre;clip-path:inset(0 100% 0 0);"
        f"animation:type {ROW_DUR}s steps(24,end) both}}"
        "@keyframes type{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 -20% 0 0)}}"
        ".blink{animation:blink 1s steps(1) infinite}"
        "@keyframes blink{50%{opacity:0}}"
        "</style>"
    )
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" '
        f'height="{H:.0f}" role="img" aria-label="ASCII portrait of Saikiran">',
        css,
        f'<rect x="0.5" y="0.5" width="{W-1:.0f}" height="{H-1:.0f}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        # window chrome dots
        '<circle cx="18" cy="16" r="4.5" fill="#ff5f56"/><circle cx="32" cy="16" r="4.5" fill="#ffbd2e"/>'
        '<circle cx="46" cy="16" r="4.5" fill="#27c93f"/>',
        f'<text x="{W/2:.0f}" y="20" text-anchor="middle" font-family="{FONT}" font-size="11" '
        f'fill="#8b949e">saikiran@github: ~/portrait</text>',
        f'<g font-family="{FONT}" font-size="{FS}" fill="{INK}" xml:space="preserve">',
    ]
    y0 = PAD + 22
    for i, line in enumerate(lines):
        y = y0 + (i + 1) * LH - 2
        delay = i * ROW_DELAY
        style = ' style="white-space:pre"' if static else \
            f' class="r" style="white-space:pre;animation-delay:{delay:.3f}s"'
        out.append(f'<text x="{PAD}" y="{y:.1f}" xml:space="preserve"{style}>{esc(line)}</text>')
    out.append("</g>")
    # resting cursor after the last row
    last = y0 + len(lines) * LH + 2
    cls = "" if static else f' class="blink" style="animation-delay:{len(lines) * ROW_DELAY + ROW_DUR:.2f}s"'
    out.append(f'<rect{cls} x="{PAD}" y="{last - FS:.1f}" width="{CW:.0f}" height="{FS:.0f}" fill="{CURSOR}" opacity="0.9"/>')
    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    lines = to_rows(cutout())
    OUT.write_text(render(lines), encoding="utf-8")
    (ROOT / "data" / "portrait.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT.name}: {COLS} cols x {len(lines)} rows")


if __name__ == "__main__":
    main()
