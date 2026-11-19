"""Assemble the workshop notebook from nb_part1..3 (+ tuning panels) and write it next to the other deliverables."""
import re
import sys
from pathlib import Path

import nbformat

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import nb_part1  # noqa: E402  (defines CELLS and the md/code helpers)
import nb_part2  # noqa: E402,F401
import nb_part3  # noqa: E402,F401
import nb_tuning  # noqa: E402

RED = "#C00000"

HERO = f"""<div align="center" style="background-color:{RED}; color:#ffffff; border-radius:18px; padding:30px 18px 24px; margin-bottom:14px;">
<div style="font-size:11px; letter-spacing:5px; color:#ffd0d0;">M.I.A ROBOTICS · ENGINEERING BETTER ROV SYSTEMS</div>
<h1 style="color:#ffffff; margin:10px 0 6px; border:none;">ROV Video Streaming Workshop</h1>
<div style="font-size:15px; color:#ffe6e6;">Hands-on notebook · measure first, compress smart, stream only what the pilot needs</div>
</div>"""


def banner(num: str, title: str) -> str:
    return (f'<div align="center" style="background-color:{RED}; color:#ffffff; border-radius:14px; padding:14px 12px 12px; margin:22px 0 10px;">\n'
            f'<div style="font-size:11px; letter-spacing:4px; color:#ffd0d0;">EXPERIMENT {num}</div>\n'
            f'<h2 style="color:#ffffff; margin:6px 0 0; border:none;">{title}</h2>\n</div>\n')


def centre(block: str) -> str:
    # A blank line after the opening tag lets Markdown inside the div render normally (CommonMark HTML-block rule).
    return f'<div align="center">\n\n{block}\n\n</div>\n'   # trailing blank line: the next paragraph/list must not join the HTML block


def stylize(text: str) -> str:
    """Centre headings and tables, turn experiment headings into banners; never touch fenced code."""
    text = text.replace("# ROV Video Streaming Workshop — Hands-on Notebook\n### M.I.A Robotics · *Engineering Better ROV Systems*", HERO)
    out, in_code, table = [], False, []
    lines = text.split("\n")

    def flush_table():
        if table:
            out.append(centre("\n".join(table))); table.clear()

    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            flush_table(); in_code = not in_code; out.append(line); continue
        if in_code:
            out.append(line); continue
        if line.startswith("|"):
            table.append(line); continue
        flush_table()
        m = re.match(r"^## Experiment (\d+) — (.+)$", line)
        if m:
            if out and out[-1].strip() == "---":   # the banner replaces the horizontal rule
                out.pop()
            out.append(banner(*m.groups())); continue
        if re.match(r"^#{2,3} ", line):
            out.append(centre(line)); continue
        out.append(line)
    flush_table()
    return "\n".join(out)


cells = list(nb_part1.CELLS)
for anchor, new in reversed(nb_tuning.INSERTS):
    idx = [i for i, (_, t) in enumerate(cells) if anchor in t]
    assert len(idx) == 1, f"anchor not unique/found: {anchor} -> {idx}"
    cells[idx[0] + 1:idx[0] + 1] = [(k, t.strip("\n")) for k, t in new]
for start, replacement in nb_tuning.REPLACE.items():
    idx = [i for i, (_, t) in enumerate(cells) if t.startswith(start)]
    assert len(idx) == 1, start
    cells[idx[0]] = ("code", replacement.strip("\n"))

nb = nbformat.v4.new_notebook()
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nb.metadata["language_info"] = {"name": "python"}
for kind, text in cells:
    nb.cells.append(nbformat.v4.new_markdown_cell(stylize(text)) if kind == "markdown" else nbformat.v4.new_code_cell(text))
out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "notebooks" / "ROV_Video_Streaming_Workshop.ipynb"
nbformat.write(nb, out)
print(f"wrote {out} with {len(nb.cells)} cells")
