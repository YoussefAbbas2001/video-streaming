"""Build the FULL experiment library notebook (every experiment we wrote, about 35) in the old slide order.

The session notebook, encoding_lab/notebooks/ROV_Video_Streaming_Workshop.ipynb, is now edited by hand: it was cut
down to the eight experiments worth running live. This script no longer touches it; it writes the full library to
out/ for leaders who want more experiments to pick from (slide numbers in it refer to the older 87-slide deck).

    python3 build/make_session_notebook.py                                      # write out/ROV_Video_Streaming_Full_Library.ipynb
    python3 build/run_nb.py out/ROV_Video_Streaming_Full_Library.ipynb          # run it unattended, keep outputs

The cells live in snb_1.py … snb_4.py (one file per group of deck parts). Every experiment starts with exp(slide, …),
which also adds it to the contents table on the first page.
"""
import sys
from pathlib import Path

import nbformat

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import snb_common as common  # noqa: E402
import snb_1  # noqa: E402,F401  (each part appends its cells to common.CELLS)
import snb_2  # noqa: E402,F401
import snb_3  # noqa: E402,F401
import snb_4  # noqa: E402,F401

OUT = HERE.parent / "out" / "ROV_Video_Streaming_Full_Library.ipynb"


def main():
    toc = "**Contents**\n\n" + common.toc_markdown()
    cells = []
    for kind, text in common.CELLS:
        text = text.replace("{{TOC}}", toc)
        cells.append(nbformat.v4.new_markdown_cell(text) if kind == "markdown" else nbformat.v4.new_code_cell(text))
    nb = nbformat.v4.new_notebook(cells=cells, metadata={
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"}})
    OUT.parent.mkdir(exist_ok=True)
    nbformat.write(nb, OUT)
    print(f"wrote {OUT.relative_to(HERE.parent)}: {len(cells)} cells, {len(common.TOC)} experiments")


if __name__ == "__main__":
    main()
