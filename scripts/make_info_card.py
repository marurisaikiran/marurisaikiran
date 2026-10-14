"""Render info-card.svg: a neofetch-style card, lines slide in one by one.

Edit the PROFILE list below and re-run:
    python scripts/make_info_card.py

Each entry is (key, value). key=None prints a section header, ("", value)
continues the previous key on a new line.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"

USER = "saikiran@github"
PROFILE = [
    ("OS", "B.Tech Mathematics & Computing"),
    ("Host", "NIT Warangal  ·  2024 – 2028"),
    ("Uptime", "2nd year  ·  CGPA 8.35"),
    ("Kernel", "DSA  ·  DBMS  ·  System Design  ·  ML"),
    ("Shell", "competitive programming  ·  ICPC '26"),
    ("Status", "open to SWE internships"),
    (None, "Languages"),
    ("Code", "C++  ·  Python  ·  JavaScript  ·  SQL"),
    ("Stack", "MongoDB  ·  Express  ·  React  ·  Node"),
    ("Data", "MySQL  ·  MongoDB Atlas  ·  PL/SQL"),
    (None, "Projects"),
    ("BloodConnect", "geospatial donor matching (MERN)"),
    ("PARK'D", "BCNF MySQL parking + ACID locking"),
    ("JARVIS", "clap-to-wake voice assistant"),
    ("SAHVA", "AI receptionist for clinics"),
    (None, "Wins"),
    ("Velocity", "Hackathon winner — MeshPay"),
    ("SIH 2025", "3rd place — agritech"),
    (None, "Off-screen"),
    ("Hobbies", "gym  ·  chess  ·  HAM radio"),
    (None, "Contact"),
    ("Email", "marurisaikiran@gmail.com"),
    ("LinkedIn", "in/saikiran-maruri-1aa963321"),
    ("GitHub", "marurisaikiran"),
]

W = 490
PAD = 22
LH = 17.2
FS = 12
STEP = 0.07           # seconds between lines
START = 0.25
BG = "#0d1117"
BORDER = "#30363d"
KEY = "#58a6ff"       # neofetch blue
VAL = "#c9d1d9"
DIM = "#8b949e"
HEAD = "#3fb950"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,DejaVu Sans Mono,Liberation Mono,monospace"
SWATCH = ["#484f58", "#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#c9d1d9"]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    keyw = max(len(k) for k, _ in PROFILE if k) + 1   # column where values start
    cw = FS * 0.6

    lines: list[str] = []
    y = PAD + 26
    n = 0

    def anim(i: int) -> str:
        return "" if static else f' class="l" style="animation-delay:{START + i * STEP:.2f}s"'

    # title + underline
    user, host = USER.split("@")
    lines.append(f'<text x="{PAD}" y="{y}"{anim(n)}><tspan fill="{HEAD}" font-weight="bold">{user}</tspan>'
                 f'<tspan fill="{VAL}">@</tspan><tspan fill="{HEAD}" font-weight="bold">{host}</tspan></text>')
    n += 1
    y += LH
    lines.append(f'<text x="{PAD}" y="{y}" fill="{DIM}"{anim(n)}>{"-" * len(USER)}</text>')
    n += 1
    y += LH

    for key, val in PROFILE:
        if key is None:
            y += LH * 0.45
            dashes = "─" * max(2, 44 - len(val))
            lines.append(f'<text x="{PAD}" y="{y:.1f}"{anim(n)}><tspan fill="{HEAD}">─ {esc(val)} </tspan>'
                         f'<tspan fill="{BORDER}">{dashes}</tspan></text>')
        else:
            label = (esc(key) + ":") if key else ""
            lines.append(
                f'<text x="{PAD}" y="{y:.1f}"{anim(n)}><tspan fill="{KEY}" font-weight="bold">{label}</tspan>'
                f'<tspan x="{PAD + keyw * cw + 6:.1f}" fill="{VAL}">{esc(val)}</tspan></text>'
            )
        n += 1
        y += LH

    # neofetch colour blocks
    y += 6
    blocks = "".join(
        f'<rect x="{PAD + i * 26}" y="{y - 12:.1f}" width="24" height="14" rx="2" fill="{c}"/>'
        for i, c in enumerate(SWATCH)
    )
    lines.append(f'<g{anim(n)}>{blocks}</g>')
    n += 1
    y += 22
    cursor_delay = START + n * STEP
    blink = "" if static else f' class="b" style="animation-delay:{cursor_delay:.2f}s"'
    lines.append(f'<text x="{PAD}" y="{y:.1f}" fill="{DIM}">saikiran@github ~ $ '
                 f'<tspan fill="{HEAD}"{blink}>█</tspan></text>')
    H = int(y + PAD)

    css = "" if static else (
        "<style>"
        ".l{opacity:0;animation:in .45s cubic-bezier(.2,.8,.2,1) both}"
        "@keyframes in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}"
        ".b{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
        "</style>"
    )
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="Saikiran Maruri - profile card">',
        css,
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        '<circle cx="18" cy="16" r="4.5" fill="#ff5f56"/><circle cx="32" cy="16" r="4.5" fill="#ffbd2e"/>'
        '<circle cx="46" cy="16" r="4.5" fill="#27c93f"/>',
        f'<text x="{W/2:.0f}" y="20" text-anchor="middle" font-family="{FONT}" font-size="11" '
        f'fill="{DIM}">saikiran@github: ~/neofetch</text>',
        f'<g font-family="{FONT}" font-size="{FS}" xml:space="preserve">',
        *lines,
        "</g></svg>",
    ]
    OUT.write_text("\n".join(svg), encoding="utf-8")
    print(f"wrote {OUT.name} ({W}x{H}, {n} lines)")


if __name__ == "__main__":
    main()
