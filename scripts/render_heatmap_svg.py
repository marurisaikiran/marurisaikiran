"""Render data/contributions.json as an animated 53 x 7 heatmap SVG.

Boxes drop in diagonally (CSS keyframes, play once and freeze); every box
has a native tooltip. With no data yet it draws an empty "waiting" grid.
"""
import json
import os
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

W = 860
CELL, GAP = 12, 3
STEP = CELL + GAP
LEFT, TOP = 46, 50
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#7ee787"]
BG, BORDER, TEXT, BRIGHT, GREEN = "#0d1117", "#30363d", "#8b949e", "#c9d1d9", "#3fb950"
DIAG = 0.045
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,DejaVu Sans Mono,Liberation Mono,monospace"


def load() -> dict:
    if SRC.exists():
        return json.loads(SRC.read_text(encoding="utf-8"))
    end = date.today()
    start = end - timedelta(days=364)
    days = [{"date": (start + timedelta(i)).isoformat(), "count": 0, "level": 0} for i in range(365)]
    return {"username": "marurisaikiran", "generated_at": "", "days": days, "stats": None}


def level(d: dict, top: int) -> int:
    if d["count"] <= 0:
        return 0
    if top and d["count"] >= top * 0.75 and d["level"] >= 4:
        return 5
    return max(1, min(d["level"] or 1, 4))


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    data = load()
    days, s = data["days"], data["stats"]
    top = max(d["count"] for d in days)
    first = date.fromisoformat(days[0]["date"])
    origin = first - timedelta(days=(first.weekday() + 1) % 7)   # columns start on Sunday

    cells, months = [], {}
    for d in days:
        dt = date.fromisoformat(d["date"])
        col, row = (dt - origin).days // 7, (dt.weekday() + 1) % 7
        cells.append((col, row, d))
        if row == 0 and dt.day <= 7:
            months.setdefault(col, dt.strftime("%b"))
    cols = max(c for c, _, _ in cells) + 1
    grid_w, grid_h = cols * STEP - GAP, 7 * STEP - GAP
    x0 = LEFT + max(0, (W - LEFT - 24 - grid_w) / 2)
    H = TOP + grid_h + 66

    head = (f'{s["total"]:,} contributions in the last year' if s
            else "waiting for the first daily refresh…")
    css = "" if static else (
        "<style>"
        ".c{opacity:0;transform-box:fill-box;transform-origin:center;"
        "animation:drop .55s cubic-bezier(.2,.8,.2,1) both}"
        "@keyframes drop{from{opacity:0;transform:translateY(-9px) scale(.5)}to{opacity:1;transform:none}}"
        ".f{opacity:0;animation:fade .6s ease-out both}@keyframes fade{to{opacity:1}}"
        "</style>"
    )
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="{head}">', css,
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        f'<g font-family="{FONT}" font-size="11" fill="{TEXT}">',
        f'<text x="22" y="26"><tspan fill="{GREEN}">$</tspan> <tspan fill="{BRIGHT}" font-weight="bold">{head}</tspan></text>',
        f'<text x="{W-22}" y="26" text-anchor="end">@{data["username"]}</text>',
    ]
    for col, name in months.items():
        if col * STEP + 24 < grid_w:
            out.append(f'<text x="{x0 + col*STEP:.1f}" y="{TOP-8}">{name}</text>')
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="{x0-8:.1f}" y="{TOP + row*STEP + 9.5}" text-anchor="end">{name}</text>')
    out.append("</g>")

    last = 0.0
    for col, row, d in cells:
        delay = (col + row) * DIAG
        last = max(last, delay)
        a = "" if static else f' class="c" style="animation-delay:{delay:.3f}s"'
        tip = f'{d["count"]} contribution{"" if d["count"] == 1 else "s"} on {d["date"]}'
        out.append(f'<rect{a} x="{x0 + col*STEP:.1f}" y="{TOP + row*STEP}" width="{CELL}" height="{CELL}" '
                   f'rx="2.5" fill="{PALETTE[level(d, top)]}"><title>{tip}</title></rect>')

    fy = TOP + grid_h + 28
    fade = "" if static else f' class="f" style="animation-delay:{last + .3:.2f}s"'
    out.append(f'<g{fade} font-family="{FONT}" font-size="11" fill="{TEXT}">')
    if s:
        b = s["best_day"]
        out.append(
            f'<text x="22" y="{fy}">streak <tspan fill="{BRIGHT}">{s["current_streak"]}d</tspan>'
            f'  ·  longest <tspan fill="{BRIGHT}">{s["longest_streak"]}d</tspan>'
            f'  ·  best day <tspan fill="{BRIGHT}">{b["count"]}</tspan>'
            f' ({date.fromisoformat(b["date"]).strftime("%d %b")})'
            f'  ·  active days <tspan fill="{BRIGHT}">{s["active_days"]}</tspan></text>')
    lx = W - 22 - (len(PALETTE) * 15 + 66)
    out.append(f'<text x="{lx}" y="{fy}">Less</text>')
    out += [f'<rect x="{lx + 32 + i*15}" y="{fy-10}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c}"/>'
            for i, c in enumerate(PALETTE)]
    out.append(f'<text x="{lx + 36 + len(PALETTE)*15}" y="{fy}">More</text>')
    if data["generated_at"]:
        out.append(f'<text x="22" y="{fy+20}" font-size="10" fill="#6e7681">refreshed {data["generated_at"][:10]} by GitHub Actions</text>')
    out.append("</g></svg>")
    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {OUT.name} ({cols} weeks)")


if __name__ == "__main__":
    main()
