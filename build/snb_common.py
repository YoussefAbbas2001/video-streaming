"""Shared pieces for the session notebook builder (make_session_notebook.py).

The notebook follows the deck: every experiment starts with a banner that names its slide.
Parts snb_1 … snb_4 append cells to CELLS in order; make_session_notebook.py writes them out.
"""
RED = "#C00000"
DARK = "#1d1d1f"

CELLS = []   # (kind, text) in notebook order
TOC = []     # (slide, part, title, mode) for the contents table

MODE_LABEL = {"live": "live: changes as you drag", "encode": "press Encode", "run": "runs once"}


def md(text):
    CELLS.append(("markdown", text.strip("\n")))


def code(text):
    CELLS.append(("code", text.strip("\n")))


def part(num, title, slides, line):
    md(f"""<div style="border-radius:18px; padding:22px 26px; margin:40px 0 6px; background:{DARK}; color:#ffffff">
<div style="font-size:11px; letter-spacing:.3em; color:#ff8a8a">PART {num} · SLIDES {slides}</div>
<div style="font-size:26px; font-weight:800; margin-top:6px">{title}</div>
<div style="font-size:14px; color:#c8c8c8; margin-top:4px">{line}</div>
</div>""")


def exp(slide, part_name, title, line, mode):
    """Banner for one experiment. mode: live | encode | run."""
    TOC.append((slide, part_name, title, mode))
    md(f"""<div style="border-radius:16px; padding:15px 22px; margin:30px 0 8px; color:#ffffff;
background:linear-gradient(115deg, {RED} 0%, #7d0000 100%); box-shadow:0 6px 18px rgba(192,0,0,.16)">
<div style="font-size:11px; letter-spacing:.22em; color:#ffd0d0">SLIDE {slide} · {part_name.upper()} · {MODE_LABEL[mode].upper()}</div>
<div style="font-size:21px; font-weight:700; margin-top:4px">{title}</div>
<div style="font-size:13px; color:#ffe3e3; margin-top:3px">{line}</div>
</div>""")


def toc_markdown():
    rows = ["| Slide | Part | Experiment | How |", "|---|---|---|---|"]
    rows += [f"| {s} | {p} | {t} | {MODE_LABEL[m]} |" for s, p, t, m in TOC]
    return "\n".join(rows)
