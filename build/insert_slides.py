#!/usr/bin/env python3
"""Insert slides from a generated deck into a hand-edited deck, keeping every edit in the target.

    python3 build/insert_slides.py SRC.pptx DST.pptx --place 1:21 --place 2:22 ... [-o OUT.pptx]

--place SRC_SLIDE:AFTER puts slide SRC_SLIDE of SRC (1-based) after slide AFTER of DST as it is NOW
(numbers refer to the original DST order; several slides after the same AFTER keep their command-line order).
AFTER = 0 inserts at the start.

What is copied per slide: the slide XML, its pictures (renamed, never overwriting the target's media),
its speaker notes, and the link to the target layout with the SAME NAME (e.g. MIA_CONTENT), so the slide
takes the target deck's current footer, logo and theme. Nothing else in the target is touched.
Prints the final slide number of every inserted slide (feed them to add_click_builds.py --only).
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from lxml import etree

NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
      "ct": "http://schemas.openxmlformats.org/package/2006/content-types"}
SLIDE_CT = "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"
NOTES_CT = "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"
REL_SLIDE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"


def unzip(path: Path, to: Path) -> Path:
    with zipfile.ZipFile(path) as z:
        z.extractall(to)
    return to


def rels_of(part: Path) -> Path:
    return part.parent / "_rels" / (part.name + ".rels")


def layout_names(root: Path) -> dict[str, str]:
    out = {}
    for f in sorted((root / "ppt/slideLayouts").glob("slideLayout*.xml")):
        c = etree.parse(str(f)).getroot().find("p:cSld", NS)
        out[c.get("name", "")] = f.name
    return out


def slide_order(root: Path) -> list[str]:
    pres = etree.parse(str(root / "ppt/presentation.xml")).getroot()
    rels = etree.parse(str(root / "ppt/_rels/presentation.xml.rels")).getroot()
    rid = {r.get("Id"): r.get("Target") for r in rels}
    return [Path(rid[s.get("{%s}id" % NS["r"])]).name for s in pres.find("p:sldIdLst", NS)]


def next_free(folder: Path, stem: str, ext: str) -> Path:
    n = 1
    while (folder / f"{stem}{n}{ext}").exists():
        n += 1
    return folder / f"{stem}{n}{ext}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", type=Path); ap.add_argument("dst", type=Path)
    ap.add_argument("--place", action="append", required=True, help="SRC_SLIDE:AFTER_DST_SLIDE")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()
    places = [tuple(map(int, p.split(":"))) for p in a.place]

    tmp = Path(tempfile.mkdtemp())
    S, D = unzip(a.src, tmp / "src"), unzip(a.dst, tmp / "dst")
    src_order, dst_order = slide_order(S), slide_order(D)
    dst_layouts = layout_names(D)
    src_layout_name = {v: k for k, v in layout_names(S).items()}
    ct = etree.parse(str(D / "[Content_Types].xml"))
    ctr = ct.getroot()
    prels_path = D / "ppt/_rels/presentation.xml.rels"
    prels = etree.parse(str(prels_path)); prr = prels.getroot()
    pres_path = D / "ppt/presentation.xml"
    pres = etree.parse(str(pres_path)); pr = pres.getroot()
    sld_lst = pr.find("p:sldIdLst", NS)
    existing_ids = [int(s.get("id")) for s in sld_lst]
    next_id = max(existing_ids) + 1
    rid_nums = [int(re.sub(r"\D", "", r.get("Id")) or 0) for r in prr]
    next_rid = max(rid_nums) + 1
    anchors = list(sld_lst)                 # original entries, so AFTER numbers refer to the original order
    inserted_after: dict[int, etree._Element] = {}
    new_parts: list[tuple[int, str]] = []   # (after, slide part name) in insertion order

    for src_no, after in places:
        src_part = S / "ppt/slides" / src_order[src_no - 1]
        new_slide = next_free(D / "ppt/slides", "slide", ".xml")
        shutil.copy(src_part, new_slide)
        rel_root = etree.parse(str(rels_of(src_part))).getroot()
        for rel in list(rel_root):
            typ, tgt = rel.get("Type"), rel.get("Target")
            if typ.endswith("/slideLayout"):
                name = src_layout_name[Path(tgt).name]
                if name not in dst_layouts:
                    sys.exit(f"target deck has no layout named {name!r}")
                rel.set("Target", f"../slideLayouts/{dst_layouts[name]}")
            elif typ.endswith("/image"):
                src_media = (src_part.parent / tgt).resolve()
                dst_media = next_free(D / "ppt/media", "image_nov26_", src_media.suffix)
                shutil.copy(src_media, dst_media)
                rel.set("Target", f"../media/{dst_media.name}")
                ext = src_media.suffix.lstrip(".").lower()
                if ctr.find(f"ct:Default[@Extension='{ext}']", NS) is None:
                    etree.SubElement(ctr, "{%s}Default" % NS["ct"], Extension=ext, ContentType=f"image/{'jpeg' if ext == 'jpg' else ext}")
            elif typ.endswith("/notesSlide"):
                src_notes = (src_part.parent / tgt).resolve()
                dst_notes = next_free(D / "ppt/notesSlides", "notesSlide", ".xml")
                shutil.copy(src_notes, dst_notes)
                nrel = etree.parse(str(rels_of(src_notes))).getroot()
                for r2 in nrel:
                    if r2.get("Type").endswith("/slide"):
                        r2.set("Target", f"../slides/{new_slide.name}")
                    elif r2.get("Type").endswith("/notesMaster"):
                        r2.set("Target", "../notesMasters/notesMaster1.xml")
                rels_of(dst_notes).parent.mkdir(exist_ok=True)
                etree.ElementTree(nrel).write(str(rels_of(dst_notes)), xml_declaration=True, encoding="UTF-8", standalone=True)
                rel.set("Target", f"../notesSlides/{dst_notes.name}")
                etree.SubElement(ctr, "{%s}Override" % NS["ct"], PartName=f"/ppt/notesSlides/{dst_notes.name}", ContentType=NOTES_CT)
        etree.ElementTree(rel_root).write(str(rels_of(new_slide)), xml_declaration=True, encoding="UTF-8", standalone=True)
        etree.SubElement(ctr, "{%s}Override" % NS["ct"], PartName=f"/ppt/slides/{new_slide.name}", ContentType=SLIDE_CT)
        rid = f"rId{next_rid}"; next_rid += 1
        etree.SubElement(prr, "{%s}Relationship" % NS["rel"], Id=rid, Type=REL_SLIDE, Target=f"slides/{new_slide.name}")
        el = etree.Element("{%s}sldId" % NS["p"]); el.set("id", str(next_id)); el.set("{%s}id" % NS["r"], rid); next_id += 1
        prev = inserted_after.get(after)
        if prev is not None:
            prev.addnext(el)
        elif after == 0:
            sld_lst.insert(0, el)
        else:
            anchors[after - 1].addnext(el)
        inserted_after[after] = el
        new_parts.append((after, new_slide.name))

    ct.write(str(D / "[Content_Types].xml"), xml_declaration=True, encoding="UTF-8", standalone=True)
    prels.write(str(prels_path), xml_declaration=True, encoding="UTF-8", standalone=True)
    pres.write(str(pres_path), xml_declaration=True, encoding="UTF-8", standalone=True)
    app = D / "docProps/app.xml"
    if app.exists():
        t = app.read_text(encoding="utf-8")
        app.write_text(re.sub(r"<Slides>\d+</Slides>", f"<Slides>{len(sld_lst)}</Slides>", t), encoding="utf-8")

    out = a.out or a.dst
    tmp_out = tmp / "out.pptx"
    with zipfile.ZipFile(tmp_out, "w", zipfile.ZIP_DEFLATED) as z:
        ctp = D / "[Content_Types].xml"
        z.write(ctp, "[Content_Types].xml")            # must be the first entry
        for f in sorted(D.rglob("*")):
            if f.is_file() and f != ctp:
                z.write(f, f.relative_to(D).as_posix())
    shutil.move(tmp_out, out)
    final = slide_order(unzip(out, tmp / "check"))
    numbers = [final.index(name) + 1 for _, name in new_parts]
    print(f"{out}: {len(final)} slides; inserted at " + ",".join(map(str, numbers)))
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
