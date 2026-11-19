// Builds presentation/MIA_Robotics_Workshop.pptx. Data measured by the notebook is read from deck_data.json.
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const { THEME, HEX, makeHelpers } = require("./deck_helpers");
const { writeTheme } = require("./write_theme");

(async () => {
  const D = JSON.parse(fs.readFileSync(path.join(__dirname, "deck_data.json"), "utf8"));
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.title = "Engineering Better ROV Systems";
  pres.subject = "M.I.A Robotics industry workshop: video streaming, engineering practice and pilot UX";
  pres.author = "M.I.A Robotics workshop";
  pres.company = "M.I.A Robotics";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const H = makeHelpers(pres);
  const { C } = H;

  const footer = (dark = true) => [
    { text: { text: "M.I.A Robotics · Engineering Better ROV Systems", options: { x: 0.6, y: 7.05, w: 6, h: 0.3, fontSize: 10, color: C.background2, fontFace: "Calibri" } } },
  ];
  pres.defineSlideMaster({
    title: "MIA_TITLE", background: { color: HEX.bg },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.05, w: 11.5, h: 1.6, fontSize: 48, bold: true, color: C.background1, fontFace: "Arial", valign: "bottom", margin: 0, align: "left" }, text: "" } },
      { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.8, w: 10.5, h: 1.1, fontSize: 20, color: C.background1, fontFace: "Calibri", valign: "top", margin: 0 }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "MIA_SECTION", background: { color: HEX.bg },
    objects: [
      { placeholder: { options: { name: "kicker", type: "body", x: 0.8, y: 1.3, w: 5.8, h: 0.9, fontSize: 54, bold: true, color: C.accent1, fontFace: "Arial", margin: 0, valign: "bottom" }, text: "" } },
      { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.35, w: 5.8, h: 2.1, fontSize: 40, bold: true, color: C.background1, fontFace: "Arial", margin: 0, valign: "top", align: "left" }, text: "" } },
      { placeholder: { options: { name: "sub", type: "body", x: 0.8, y: 4.6, w: 5.8, h: 1.4, fontSize: 20, color: C.background2, fontFace: "Calibri", margin: 0, valign: "top" }, text: "" } },
      ...footer(),
    ],
    slideNumber: { x: 12.2, y: 7.05, w: 0.6, h: 0.3, fontSize: 10, color: C.background2, align: "right" },
  });
  pres.defineSlideMaster({
    title: "MIA_CONTENT", background: { color: HEX.bg },
    objects: [
      { placeholder: { options: { name: "kicker", type: "body", x: 0.6, y: 0.32, w: 10, h: 0.3, fontSize: 12, bold: true, color: C.accent1, fontFace: "Arial", charSpacing: 2, margin: 0, valign: "middle" }, text: "" } },
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.66, w: 12.1, h: 0.85, fontSize: 32, bold: true, color: C.background1, fontFace: "Arial", margin: 0, valign: "middle", align: "left" }, text: "" } },
      ...footer(),
    ],
    slideNumber: { x: 12.2, y: 7.05, w: 0.6, h: 0.3, fontSize: 10, color: C.background2, align: "right" },
  });

  const sectionsSeen = new Set();
  const ensureSection = (name) => { if (!sectionsSeen.has(name)) { pres.addSection({ title: name }); sectionsSeen.add(name); } };
  const content = (sectionTitle, kicker, title, notes) => {
    ensureSection(sectionTitle);
    const s = pres.addSlide({ masterName: "MIA_CONTENT", sectionTitle });
    s.addText(kicker.toUpperCase(), { placeholder: "kicker" });
    s.addText(title, { placeholder: "title" });
    s.addNotes(notes);
    return s;
  };
  const section = (sectionTitle, num, title, sub, img, notes) => {
    ensureSection(sectionTitle);
    const s = pres.addSlide({ masterName: "MIA_SECTION", sectionTitle });
    s.addImage({ path: img, x: 6.9, y: 0, w: 6.433, h: 7.5, sizing: { type: "cover", w: 6.433, h: 7.5 }, objectName: "section-image", altText: "Synthetic underwater frame" });
    s.addShape(pres.shapes.RECTANGLE, { x: 6.9, y: 0, w: 6.433, h: 7.5, fill: { color: H.col.bg, transparency: 45 }, line: { type: "none" }, objectName: "section-overlay" });
    s.addText(num, { placeholder: "kicker" });
    s.addText(title, { placeholder: "title" });
    s.addText(sub, { placeholder: "sub" });
    s.addNotes(notes);
    return s;
  };
  // Title slide needs its section first.
  ensureSection("Opening");
  const ctx = { pres, H, D, content, section };
  await require("./deck_part_a")(ctx);
  await require("./deck_part_b")(ctx);

  const out = path.join(__dirname, "..", "presentation", "MIA_Robotics_Workshop.pptx");
  await pres.writeFile({ fileName: out });
  await writeTheme(out, THEME);
  console.log("wrote", out);
})().catch((e) => { console.error(e); process.exit(1); });
