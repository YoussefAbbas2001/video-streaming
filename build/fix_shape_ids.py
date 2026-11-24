"""Give every shape on a slide a unique id (PowerPoint asks to *repair* a deck when two shapes share one).

pptxgenjs sometimes gives a table the same <p:cNvPr id> as a text box on the same slide. LibreOffice and the
schema validator accept that; PowerPoint does not. This renumbers every repeat of an id to a new, unused id.
Animations that pointed at a repeated id are ambiguous afterwards: the slide numbers are printed so the click
builds can be regenerated with add_click_builds.py --only.

    python3 build/fix_shape_ids.py presentation/MIA_Video_Streaming.pptx      # fixes in place
"""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ID = re.compile(rb'(<p:cNvPr id=")(\d+)(")')


def fix_slide(xml: bytes) -> tuple[bytes, bool, bool]:
    """Return (new xml, changed, an animation referenced a repeated id)."""
    ids = [int(m.group(2)) for m in ID.finditer(xml)]
    nxt = max(ids, default=0) + 1
    seen: set[int] = set()
    repeated: set[int] = set()

    def repl(m: re.Match) -> bytes:
        nonlocal nxt
        i = int(m.group(2))
        if i in seen:
            repeated.add(i)
            new = nxt; nxt += 1
            return m.group(1) + str(new).encode() + m.group(3)
        seen.add(i)
        return m.group(0)

    out = ID.sub(repl, xml)
    anim = any(f'spid="{i}"'.encode() in xml for i in repeated)
    return out, bool(repeated), anim


def slide_order(z: zipfile.ZipFile) -> list[str]:
    pres = z.read("ppt/presentation.xml").decode()
    rels = z.read("ppt/_rels/presentation.xml.rels").decode()
    target = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels)) | {a: b for b, a in re.findall(r'Target="([^"]+)"[^>]*Id="(rId\d+)"', rels)}
    return ["ppt/" + target[r] for r in re.findall(r'<p:sldId [^>]*r:id="(rId\d+)"', pres)]


def fix(path: Path) -> list[int]:
    """Fix the deck in place; return the 1-based numbers of slides whose animations need regenerating."""
    with zipfile.ZipFile(path) as z:
        order = slide_order(z)
        items = [(i, z.read(i.filename)) for i in z.infolist()]
    changed, need_anim = [], []
    tmp = Path(tempfile.mkdtemp()) / path.name
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as out:
        for info, data in items:
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", info.filename):
                data, ch, anim = fix_slide(data)
                if ch:
                    n = order.index(info.filename) + 1
                    changed.append(n)
                    if anim:
                        need_anim.append(n)
            out.writestr(info, data)
    shutil.move(tmp, path)
    print(f"{path}: fixed repeated shape ids on slides {sorted(changed) or 'none'}"
          + (f"; regenerate click builds on {sorted(need_anim)}" if need_anim else ""))
    return sorted(need_anim)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        fix(Path(p))
