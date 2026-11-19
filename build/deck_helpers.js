// Shared helpers for the M.I.A Robotics workshop deck (pptxgenjs, LAYOUT_WIDE 13.333" x 7.5").
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");

const HEX = {
  bg: "0A1628", card: "13294A", cardHi: "1B3A66", text: "FFFFFF", muted: "9FB3C8",
  cyan: "22D3EE", blue: "3B82F6", teal: "14B8A6", amber: "F59E0B", rose: "F43F5E", violet: "8B5CF6",
  code: "06101F", grid: "24406A",
};
// Data-viz categorical palette (dark steps), validated against the navy surface.
const SERIES = ["3987E5", "D95926", "199E70", "C98500", "D55181", "0CA30C", "9085E9", "E66767"];

const THEME = {
  name: "MIA ROV Engineering",
  headFontFace: "Arial",
  bodyFontFace: "Calibri",
  colors: {
    dk1: HEX.bg, lt1: HEX.text, dk2: HEX.card, lt2: HEX.muted,
    accent1: HEX.cyan, accent2: HEX.blue, accent3: HEX.teal, accent4: HEX.amber, accent5: HEX.rose, accent6: HEX.violet,
    hlink: HEX.cyan, folHlink: HEX.violet,
  },
};

const iconCache = new Map();
async function icon(Comp, color = HEX.cyan, size = 256) {
  const key = `${Comp.name}-${color}`;
  if (iconCache.has(key)) return iconCache.get(key);
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  const data = "image/png;base64," + buf.toString("base64");
  iconCache.set(key, data);
  return data;
}

function makeHelpers(pres) {
  const C = pres.SchemeColor;
  const col = {
    bg: C.text1, card: C.text2, text: C.background1, muted: C.background2,
    cyan: C.accent1, blue: C.accent2, teal: C.accent3, amber: C.accent4, rose: C.accent5, violet: C.accent6,
  };
  let n = 0;
  const nm = (p) => `${p}-${++n}`;

  function text(s, t, o) {
    s.addText(t, { isTextBox: true, fontSize: 16, color: col.text, valign: "top", margin: 0, objectName: nm("text"), ...o });
  }
  function bullets(s, items, x, y, w, h, o = {}) {
    const size = o.fontSize || 16;
    const runs = items.map((it, i) => {
      const isObj = typeof it === "object";
      const content = isObj ? it.text : it;
      return { text: content, options: { bullet: isObj && it.sub ? { indent: 18 } : { indent: 16 }, indentLevel: isObj && it.sub ? 1 : 0,
        fontSize: isObj && it.sub ? size - 2 : size, color: isObj && it.sub ? col.muted : col.text, bold: isObj && it.bold,
        breakLine: i < items.length - 1, paraSpaceAfter: o.gap ?? 6 } };
    });
    s.addText(runs, { isTextBox: true, x, y, w, h, valign: "top", margin: 0, objectName: nm("bullets"), fit: "none" });
  }
  function rich(s, runs, x, y, w, h, o = {}) {
    s.addText(runs.map((r, i) => ({ text: r.text, options: { fontSize: 16, color: col.text, ...r, breakLine: r.breakLine ?? (i < runs.length - 1 && r.nl !== false) } })),
      { isTextBox: true, x, y, w, h, valign: "top", margin: 0, objectName: nm("rich"), ...o });
  }
  function box(s, x, y, w, h, o = {}) {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: o.r ?? 0.08, fill: { color: o.fill || col.card, transparency: o.transparency || 0 },
      line: o.line ? { color: o.line, width: o.lineW || 1.25, dashType: o.dash || "solid" } : { type: "none" }, objectName: nm("box") });
  }
  async function iconCircle(s, Comp, x, y, d = 0.6, color = HEX.cyan, fillCol = col.cyan) {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fillCol, transparency: 82 }, line: { color: fillCol, width: 1.25 }, objectName: nm("iconbg") });
    const pad = d * 0.24;
    s.addImage({ data: await icon(Comp, color), x: x + pad, y: y + pad, w: d - 2 * pad, h: d - 2 * pad, objectName: nm("icon") });
  }
  async function card(s, x, y, w, h, o) {
    box(s, x, y, w, h, { fill: o.fill, line: o.line });
    let ty = y + 0.2;
    if (o.icon) { await iconCircle(s, o.icon, x + 0.22, y + 0.22, 0.56, o.iconColor || HEX.cyan, o.iconFill || col.cyan); }
    const tx = o.icon ? x + 0.92 : x + 0.25;
    if (o.title) {
      text(s, o.title, { x: tx, y: o.icon ? y + 0.24 : ty, w: w - (tx - x) - 0.2, h: 0.5, fontSize: o.titleSize || 17, bold: true, color: o.titleColor || col.text, valign: "middle", fontFace: "Arial" });
    }
    const by = o.icon ? y + 0.92 : y + 0.75;
    if (o.body) text(s, o.body, { x: x + 0.25, y: by, w: w - 0.5, h: h - (by - y) - 0.15, fontSize: o.bodySize || 14, color: col.muted });
    if (o.bullets) bullets(s, o.bullets, x + 0.25, by, w - 0.45, h - (by - y) - 0.15, { fontSize: o.bodySize || 14, gap: o.gap ?? 4 });
  }
  function arrow(s, x1, y1, x2, y2, color = col.cyan, o = {}) {
    s.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1) || 0.001, h: Math.abs(y2 - y1) || 0.001,
      flipH: x2 < x1, flipV: y2 < y1, line: { color, width: o.width || 2, endArrowType: o.noHead ? undefined : "triangle", dashType: o.dash || "solid" }, objectName: nm("arrow") });
  }
  // Horizontal process flow of labelled boxes with arrows between them.
  function flow(s, steps, x, y, w, h, o = {}) {
    const gap = o.gap ?? 0.32; const bw = (w - gap * (steps.length - 1)) / steps.length;
    steps.forEach((st, i) => {
      const bx = x + i * (bw + gap); const c = st.color || col.card;
      box(s, bx, y, bw, h, { fill: c, line: st.line });
      text(s, st.title, { x: bx + 0.08, y: y + 0.1, w: bw - 0.16, h: st.sub ? h * 0.42 : h - 0.2, fontSize: o.titleSize || 14, bold: true, align: "center", valign: st.sub ? "bottom" : "middle", color: st.titleColor || col.text });
      if (st.sub) text(s, st.sub, { x: bx + 0.08, y: y + h * 0.5, w: bw - 0.16, h: h * 0.46, fontSize: o.subSize || 11, align: "center", color: st.subColor || col.muted });
      if (i < steps.length - 1) arrow(s, bx + bw + 0.04, y + h / 2, bx + bw + gap - 0.04, y + h / 2, o.arrowColor || col.cyan);
    });
    return bw;
  }
  function table(s, rows, x, y, w, colW, o = {}) {
    const fs = o.fontSize || 12;
    const data = rows.map((r, ri) => r.map((c) => {
      const cell = typeof c === "object" && c !== null && c.text !== undefined ? c : { text: String(c) };
      const head = ri === 0;
      return { text: cell.text, options: { fontSize: head ? fs : fs, bold: head || cell.bold, color: head ? col.bg : (cell.color || col.text),
        fill: { color: head ? (o.headFill || col.cyan) : (ri % 2 ? col.card : col.bg) }, valign: "middle", margin: [3, 6, 3, 6], fontFace: head ? "Arial" : "Calibri", align: cell.align || "left" } };
    }));
    s.addTable(data, { x, y, w, colW, border: { type: "solid", pt: 0.75, color: HEX.grid }, rowH: o.rowH || 0.36, autoPage: false, objectName: nm("table") });
  }
  function stat(s, x, y, w, value, label, color = col.cyan, o = {}) {
    text(s, value, { x, y, w, h: o.vh || 0.95, fontSize: o.size || 54, bold: true, color, fontFace: "Arial", align: o.align || "left", valign: "bottom" });
    text(s, label, { x, y: y + (o.vh || 0.95) + 0.05, w, h: o.lh || 0.7, fontSize: o.labelSize || 14, color: col.muted, align: o.align || "left" });
  }
  function code(s, src, x, y, w, h, o = {}) {
    box(s, x, y, w, h, { fill: HEX.code, line: o.line || HEX.grid, r: 0.05 });
    s.addText(src, { isTextBox: true, x: x + 0.15, y: y + 0.1, w: w - 0.3, h: h - 0.2, fontFace: "Courier New", fontSize: o.fontSize || 12, color: o.color || "D6E4F0", valign: "top", margin: 0, objectName: nm("code") });
  }
  function pill(s, label, x, y, w, color = col.cyan, o = {}) {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: o.h || 0.34, rectRadius: 0.17, fill: { color, transparency: o.solid ? 0 : 78 }, line: { color, width: 1 }, objectName: nm("pill") });
    text(s, label, { x, y, w, h: o.h || 0.34, fontSize: o.fontSize || 11, bold: true, color: o.solid ? col.bg : col.text, align: "center", valign: "middle" });
  }
  return { C, col, text, bullets, rich, box, iconCircle, card, arrow, flow, table, stat, code, pill };
}

module.exports = { HEX, SERIES, THEME, icon, makeHelpers };
