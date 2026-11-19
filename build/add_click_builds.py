#!/usr/bin/env python3
"""Add click-by-click builds (Fade in, one logical chunk per click) to every slide of the deck.

pptxgenjs cannot write animations, so build_deck.js produces a static deck and this
script post-processes it:

    node build/build_deck.js && python3 build/add_click_builds.py presentation/MIA_Robotics_Workshop.pptx

What becomes one click ("unit"):
  * a box / card / circle together with everything drawn inside it;
  * a heading sitting just above a box joins that box;
  * an icon joins the label right next to it; an arrow joins the unit it starts from;
  * anything else (table, chart, picture, free text) is its own unit.
What never animates: title / kicker placeholders, full-slide decoration, section images,
footnotes along the bottom edge. A slide whose content is a single unit is left static.

Order = reading order by recursive XY-cut (rows top to bottom; inside a row, columns left
to right; inside a column, top to bottom). More than MAX_STEPS units -> rows are merged.
Re-running is safe: existing <p:timing> elements are replaced.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

EMU = 914400
NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
P = "{%s}" % NS["p"]

MAX_STEPS = 8            # more clicks than this on one slide gets tiring
FADE_MS = 350
EPS = 0.02 * EMU         # tolerance for "touching"
CONTAINER_GEOMS = {"rect", "roundRect", "ellipse", "snipRoundRect", "round2SameRect", "flowChartProcess"}
STATIC_NAMES = ("section-image", "section-overlay", "end-image", "title-image")


@dataclass
class El:
    node: etree._Element
    sid: str
    name: str
    x: int
    y: int
    w: int
    h: int
    kind: str              # sp | txt | pic | frame | line
    geom: str = ""
    flip_h: bool = False
    flip_v: bool = False

    @property
    def cx(self): return self.x + self.w / 2
    @property
    def cy(self): return self.y + self.h / 2
    @property
    def area(self): return self.w * self.h

    def contains_point(self, px, py):
        return self.x - EPS <= px <= self.x + self.w + EPS and self.y - EPS <= py <= self.y + self.h + EPS


@dataclass
class Unit:
    els: list = field(default_factory=list)

    @property
    def x(self): return min(e.x for e in self.els)
    @property
    def y(self): return min(e.y for e in self.els)
    @property
    def r(self): return max(e.x + e.w for e in self.els)
    @property
    def b(self): return max(e.y + e.h for e in self.els)


def read_el(node) -> El | None:
    tag = etree.QName(node).localname
    nv = node.find(".//p:cNvPr", NS)
    if nv is None:
        return None
    if node.find(".//p:nvPr/p:ph", NS) is not None:          # placeholders (title, kicker, sub) stay static
        return None
    xfrm = node.find("p:spPr/a:xfrm", NS) if tag in ("sp", "pic", "cxnSp") else node.find("p:xfrm", NS)
    if xfrm is None:
        return None
    off, ext = xfrm.find("a:off", NS), xfrm.find("a:ext", NS)
    if off is None or ext is None:
        return None
    geom_el = node.find("p:spPr/a:prstGeom", NS)
    geom = geom_el.get("prst") if geom_el is not None else ""
    if tag == "sp":
        is_txbox = node.find("p:nvSpPr/p:cNvSpPr", NS) is not None and node.find("p:nvSpPr/p:cNvSpPr", NS).get("txBox") == "1"
        kind = "line" if geom in ("line", "straightConnector1") else ("txt" if is_txbox else "sp")
    elif tag == "cxnSp":
        kind = "line"
    elif tag == "pic":
        kind = "pic"
    else:
        kind = "frame"
    return El(node, nv.get("id"), nv.get("name", ""), int(off.get("x")), int(off.get("y")),
              int(ext.get("cx")), int(ext.get("cy")), kind, geom,
              xfrm.get("flipH") == "1", xfrm.get("flipV") == "1")


def is_static(e: El, slide_w: int, slide_h: int) -> bool:
    if any(e.name.startswith(n) for n in STATIC_NAMES):
        return True
    if e.w >= 0.9 * slide_w and e.h >= 0.85 * slide_h:       # full-slide decoration
        return True
    if e.kind == "pic" and e.h >= 0.95 * slide_h:             # half-bleed images on section/title slides
        return True
    if e.kind == "txt" and e.y >= 6.62 * EMU and e.h <= 0.45 * EMU:   # footnotes / source lines
        return True
    return False


def build_units(els: list[El]) -> list[Unit]:
    containers = [e for e in els if e.kind == "sp" and e.geom in CONTAINER_GEOMS and e.area >= 0.12 * EMU * EMU]

    def parent_of(e: El):
        best = None
        for c in containers:
            if c is e or c.area <= e.area:
                continue
            if c.contains_point(e.cx, e.cy) and (best is None or c.area < best.area):
                best = c
        return best

    def top(e: El):
        seen = set()
        while True:
            p = parent_of(e)
            if p is None or id(p) in seen:
                return e
            seen.add(id(p)); e = p

    groups: dict[int, Unit] = {}
    loose_lines = []
    for e in els:
        if e.kind == "line" and parent_of(e) is None:
            loose_lines.append(e); continue
        root = top(e)
        groups.setdefault(id(root), Unit()).els.append(e)
    units = list(groups.values())

    # a heading right above a box joins the box
    def is_bare_text(u): return len(u.els) == 1 and u.els[0].kind == "txt"
    for u in [u for u in units if is_bare_text(u)]:
        for v in units:
            if v is u or is_bare_text(v) or u not in units:
                continue
            gap = v.y - u.b
            overlap = min(u.r, v.r) - max(u.x, v.x)
            if -EPS <= gap <= 0.25 * EMU and overlap >= 0.5 * (u.r - u.x):
                v.els.extend(u.els); units.remove(u); break

    # a text directly below a text, picture or chart joins it (value + label, image + caption, heading + bullets)
    changed = True
    while changed:
        changed = False
        for u in [u for u in units if is_bare_text(u)]:
            best, best_gap = None, 0.2 * EMU
            for v in units:
                if v is u:
                    continue
                if not (is_bare_text(v) or any(e.kind in ("pic", "frame") for e in v.els)) or any(e.kind == "sp" for e in v.els):
                    continue
                gap = u.y - v.b
                overlap = min(u.r, v.r) - max(u.x, v.x)
                if -EPS <= gap < best_gap and overlap >= 0.5 * (u.r - u.x):
                    best, best_gap = v, gap
            if best is not None:
                best.els.extend(u.els); units.remove(u); changed = True
                break

    # an icon (small picture / circle) joins the label next to it
    def is_icon(u): return (u.r - u.x) <= 0.85 * EMU and (u.b - u.y) <= 0.85 * EMU and any(e.kind in ("pic", "sp") for e in u.els)
    for u in [u for u in units if is_icon(u)]:
        if u not in units:
            continue
        best, best_gap = None, 0.4 * EMU
        for v in units:
            if v is u:
                continue
            vo = min(u.b, v.b) - max(u.y, v.y)
            gap = v.x - u.r
            if vo > 0 and -EPS <= gap < best_gap:
                best, best_gap = v, gap
        if best is not None:
            best.els.extend(u.els); units.remove(u)

    # an arrow joins the unit it starts from
    for ln in loose_lines:
        sx = ln.x + (ln.w if ln.flip_h else 0); sy = ln.y + (ln.h if ln.flip_v else 0)
        def dist(u):
            dx = max(u.x - sx, 0, sx - u.r); dy = max(u.y - sy, 0, sy - u.b)
            return dx * dx + dy * dy
        if units:
            min(units, key=dist).els.append(ln)
        else:
            units.append(Unit([ln]))
    return units


def xy_cut(units: list[Unit], horizontal_first: bool = True) -> list[list[Unit]]:
    """Return units in reading order, as a list of leaves; each leaf is a list of units in one row band."""
    if len(units) <= 1:
        return [units] if units else []

    def cut(us, by_y):
        key_lo = (lambda u: u.y) if by_y else (lambda u: u.x)
        key_hi = (lambda u: u.b) if by_y else (lambda u: u.r)
        us = sorted(us, key=key_lo)
        bands, cur, hi = [], [us[0]], key_hi(us[0])
        for u in us[1:]:
            if key_lo(u) >= hi - EPS:
                bands.append(cur); cur = [u]
            else:
                cur.append(u)
            hi = max(hi, key_hi(u))
        bands.append(cur)
        return bands

    for by_y in ((True, False) if horizontal_first else (False, True)):
        bands = cut(units, by_y)
        if len(bands) > 1:
            out = []
            for b in bands:
                out.extend(xy_cut(b, horizontal_first=not by_y))
            return out
    return [[u] for u in sorted(units, key=lambda u: (u.y, u.x))]


def plan_steps(units: list[Unit]) -> list[list[El]]:
    leaves = xy_cut(units)
    steps = [[e for u in leaf for e in u.els] for leaf in leaves]
    def size(step):
        xs = [e.x for e in step] + [e.x + e.w for e in step]; ys = [e.y for e in step] + [e.y + e.h for e in step]
        return (max(xs) - min(xs)) * (max(ys) - min(ys))
    while len(steps) > MAX_STEPS:                 # merge the two smallest neighbours, keep reading order
        i = min(range(len(steps) - 1), key=lambda k: size(steps[k]) + size(steps[k + 1]))
        steps[i:i + 2] = [steps[i] + steps[i + 1]]
    return steps


def timing_xml(steps: list[list[El]]) -> etree._Element:
    ids = iter(range(1, 100000))
    t = etree.Element(P + "timing", nsmap={"p": NS["p"], "a": NS["a"]})
    tn = etree.SubElement(t, P + "tnLst")
    root_par = etree.SubElement(tn, P + "par")
    root = etree.SubElement(root_par, P + "cTn", id=str(next(ids)), dur="indefinite", restart="never", nodeType="tmRoot")
    seq = etree.SubElement(etree.SubElement(root, P + "childTnLst"), P + "seq", concurrent="1", nextAc="seek")
    main = etree.SubElement(seq, P + "cTn", id=str(next(ids)), dur="indefinite", nodeType="mainSeq")
    main_children = etree.SubElement(main, P + "childTnLst")

    def cond(parent, delay):
        etree.SubElement(etree.SubElement(parent, P + "stCondLst"), P + "cond", delay=delay)

    for step in steps:
        click_par = etree.SubElement(main_children, P + "par")
        click = etree.SubElement(click_par, P + "cTn", id=str(next(ids)), fill="hold")
        cond(click, "indefinite")
        inner_par = etree.SubElement(etree.SubElement(click, P + "childTnLst"), P + "par")
        inner = etree.SubElement(inner_par, P + "cTn", id=str(next(ids)), fill="hold")
        cond(inner, "0")
        inner_children = etree.SubElement(inner, P + "childTnLst")
        for i, e in enumerate(step):
            ep = etree.SubElement(inner_children, P + "par")
            ec = etree.SubElement(ep, P + "cTn", id=str(next(ids)), presetID="10", presetClass="entr", presetSubtype="0",
                                  fill="hold", grpId="0", nodeType="clickEffect" if i == 0 else "withEffect")
            cond(ec, "0")
            beh = etree.SubElement(ec, P + "childTnLst")
            st = etree.SubElement(beh, P + "set")
            cb = etree.SubElement(st, P + "cBhvr")
            c1 = etree.SubElement(cb, P + "cTn", id=str(next(ids)), dur="1", fill="hold")
            cond(c1, "0")
            etree.SubElement(etree.SubElement(cb, P + "tgtEl"), P + "spTgt", spid=e.sid)
            etree.SubElement(etree.SubElement(cb, P + "attrNameLst"), P + "attrName").text = "style.visibility"
            etree.SubElement(etree.SubElement(st, P + "to"), P + "strVal", val="visible")
            ae = etree.SubElement(beh, P + "animEffect", transition="in", filter="fade")
            cb2 = etree.SubElement(ae, P + "cBhvr")
            etree.SubElement(cb2, P + "cTn", id=str(next(ids)), dur=str(FADE_MS))
            etree.SubElement(etree.SubElement(cb2, P + "tgtEl"), P + "spTgt", spid=e.sid)
    prev = etree.SubElement(etree.SubElement(seq, P + "prevCondLst"), P + "cond", evt="onPrev", delay="0")
    etree.SubElement(etree.SubElement(prev, P + "tgtEl"), P + "sldTgt")
    nxt = etree.SubElement(etree.SubElement(seq, P + "nextCondLst"), P + "cond", evt="onNext", delay="0")
    etree.SubElement(etree.SubElement(nxt, P + "tgtEl"), P + "sldTgt")

    bld = etree.SubElement(t, P + "bldLst")
    for step in steps:
        for e in step:
            if e.kind in ("sp", "txt", "line"):
                etree.SubElement(bld, P + "bldP", spid=e.sid, grpId="0", animBg="1")
            elif e.kind == "frame":
                etree.SubElement(etree.SubElement(bld, P + "bldGraphic", spid=e.sid, grpId="0"), P + "bldAsOne")
    if len(bld) == 0:
        t.remove(bld)
    return t


STATIC_LAYOUTS = ("MIA_TITLE", "MIA_SECTION")      # title, section dividers and the closing slide stay still


def process_slide(xml: bytes, slide_w: int, slide_h: int, layout_name: str = ""):
    root = etree.fromstring(xml)
    for old in root.findall("p:timing", NS):
        root.remove(old)
    if layout_name in STATIC_LAYOUTS:
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True), []
    tree = root.find("p:cSld/p:spTree", NS)
    els = []
    for node in tree:
        if etree.QName(node).localname not in ("sp", "pic", "graphicFrame", "cxnSp", "grpSp"):
            continue
        e = read_el(node)
        if e is not None and not is_static(e, slide_w, slide_h):
            els.append(e)
    units = build_units(els)
    steps = plan_steps(units) if len(units) > 1 else []
    if steps:
        t = timing_xml(steps)
        # schema order: cSld, clrMapOvr, transition, timing, extLst
        anchor = root.find("p:transition", NS)
        if anchor is None:
            anchor = root.find("p:clrMapOvr", NS)
        if anchor is None:
            anchor = root.find("p:cSld", NS)
        anchor.addnext(t)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True), steps


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pptx", type=Path)
    ap.add_argument("-o", "--out", type=Path, help="output file (default: overwrite input)")
    ap.add_argument("-v", "--verbose", action="store_true", help="print the plan for every slide")
    a = ap.parse_args()

    src = a.pptx
    with zipfile.ZipFile(src) as z:
        pres = etree.fromstring(z.read("ppt/presentation.xml"))
        sz = pres.find("p:sldSz", NS)
        slide_w, slide_h = int(sz.get("cx")), int(sz.get("cy"))
        # slide order from presentation.xml.rels
        rels = etree.fromstring(z.read("ppt/_rels/presentation.xml.rels"))
        rid_to_target = {r.get("Id"): r.get("Target") for r in rels}
        order = ["ppt/" + rid_to_target[s.get("{%s}id" % NS["r"])].lstrip("/").replace("ppt/", "")
                 for s in pres.find("p:sldIdLst", NS)]
        tmp = Path(tempfile.mkstemp(suffix=".pptx")[1])
        total_clicks, animated = 0, 0
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as out:
            plans = {}
            names = set(z.namelist())
            def layout_of(slide):
                rel = slide.replace("slides/", "slides/_rels/") + ".rels"
                if rel not in names:
                    return ""
                for r in etree.fromstring(z.read(rel)):
                    if r.get("Type", "").endswith("/slideLayout"):
                        lay = "ppt/slideLayouts/" + r.get("Target").split("/")[-1]
                        c = etree.fromstring(z.read(lay)).find("p:cSld", NS)
                        return c.get("name", "") if c is not None else ""
                return ""
            for name in order:
                new_xml, steps = process_slide(z.read(name), slide_w, slide_h, layout_of(name))
                plans[name] = (new_xml, steps)
            for item in z.infolist():
                if item.filename.endswith("/"):        # folder entries break some cloud viewers
                    continue
                data = plans[item.filename][0] if item.filename in plans else z.read(item.filename)
                out.writestr(item, data)
        for n, name in enumerate(order, 1):
            steps = plans[name][1]
            total_clicks += len(steps); animated += bool(steps)
            if a.verbose:
                desc = " | ".join("+".join(e.name for e in s[:4]) + ("…" if len(s) > 4 else "") for s in steps)
                print(f"slide {n:2d}: {len(steps)} clicks  {desc[:160]}")
    dst = a.out or src
    shutil.move(tmp, dst)
    print(f"{animated}/{len(order)} slides animated, {total_clicks} clicks in total -> {dst}")


if __name__ == "__main__":
    sys.exit(main())
