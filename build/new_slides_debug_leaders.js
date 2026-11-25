// Two slides (Nov 2026): "When it breaks: the debug checklist" (after Activity 2) and
// "Leaders: one 90-minute session a week" (after the experiments plan).
//   node build/new_slides_debug_leaders.js      # → out/new_slides_debug_leaders.pptx
//   see build/README.md for the insert command
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const { THEME, HEX, makeHelpers } = require("./deck_helpers");
const { writeTheme } = require("./write_theme");

const ROOT = path.join(__dirname, "..");
const OUT = path.join(ROOT, "out", "new_slides_debug_leaders.pptx");

// Count the checklist rows per stage straight from the doc, so the slide cannot drift from it.
const CHECKLIST = fs.readFileSync(path.join(ROOT, "docs", "debug", "ROV_Debug_Checklist.md"), "utf8");
const ROWS = [...CHECKLIST.matchAll(/^\| ☐ \*\*([A-G])(\d+)\*\*( 🤖)?/gm)].map((m) => ({ stage: m[1], auto: !!m[3] }));
const per = (s) => ROWS.filter((r) => r.stage === s);
const ROUTES = (CHECKLIST.match(/^### [^\n]+$/gm) || []).filter((h) => /^### (⬛|🧊|🐢|📈|🧱|🎞️|🔌|🕹️|🏊)/u.test(h)).length;

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const { col, text, box, code } = makeHelpers(pres);
  pres.defineSlideMaster({
    title: "MIA_CONTENT", background: { color: HEX.bg },
    objects: [
      { placeholder: { options: { name: "kicker", type: "body", x: 0.6, y: 0.32, w: 10, h: 0.3, fontSize: 12, bold: true, color: col.cyan, fontFace: "Arial", charSpacing: 2, margin: 0, valign: "middle" }, text: "" } },
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.66, w: 12.1, h: 0.85, fontSize: 32, bold: true, color: col.text, fontFace: "Arial", margin: 0, valign: "middle", align: "left" }, text: "" } },
    ],
  });
  const content = (kicker, title, notes) => {
    const s = pres.addSlide({ masterName: "MIA_CONTENT" });
    s.addText(kicker.toUpperCase(), { placeholder: "kicker" });
    s.addText(title, { placeholder: "title" });
    s.addNotes(notes);
    return s;
  };

  // ======================================================================= D1 · the debug checklist
  {
    const stages = [["A", "Power + heat", col.rose], ["B", "Cameras + USB", col.amber], ["C", "ROV computer", col.amber], ["D", "Streams", col.cyan],
                    ["E", "Tether", col.cyan], ["F", "Topside", col.teal], ["G", "Pilot", col.teal]];
    const auto = ROWS.filter((r) => r.auto).length;
    const s = content("Diagnostics · the checklist", "When it breaks: check in order. The first ❌ is the cause",
      `This is the tool for what we just did in Activity 2. docs/debug/ROV_Debug_Checklist.md has ${ROWS.length} checks in the order the video travels: power and heat, cameras and USB, the ROV computer, the streams, the tether, the topside and finally what the pilot feels. A problem early in the chain causes symptoms everywhere after it, so the rule is: go in order, and the first red line is almost always the cause. ` +
      `Every row has the command, the good value, and what a bad value means with the fix. There is a symptom finder at the top and ${ROUTES} step-by-step routes for the common symptoms (frozen picture, late picture, picture getting later, blocks and smears, a camera that resets…). ` +
      `${auto} of the checks are automatic: rov_healthcheck.sh runs on the ROV computer in about 10 seconds and prints a green, amber or red line for each, with the meaning and the fix. The output on the slide is an example of a story we have seen: under-voltage when the thrusters pull, so the cameras reset on USB, so the pilot sees freezes. The freezes are the symptom; the power is the cause; the script says to start with A3. ` +
      "Map it back to the activity: every hypothesis on the answer sheet is one row of this checklist. On Monday, run the checklist before anyone forms an opinion, and paste the output into the bug report: the bug template now has a field for it.");
    stages.forEach(([l, n, c], i) => {
      const x = 0.6 + i * 1.74, list = per(l), a = list.filter((r) => r.auto).length;
      box(s, x, 1.68, 1.62, 1.12, { line: c });
      text(s, l, { x: x + 0.12, y: 1.72, w: 0.5, h: 0.55, fontSize: 26, bold: true, color: c });
      text(s, `${list.length}`, { x: x + 0.9, y: 1.76, w: 0.6, h: 0.45, fontSize: 18, bold: true, color: col.text, align: "right" });
      text(s, n, { x: x + 0.12, y: 2.24, w: 1.45, h: 0.3, fontSize: 12.5, bold: true, color: col.text });
      text(s, a ? (a === list.length ? "🤖 automatic" : `🤖 ${a} automatic`) : "manual", { x: x + 0.12, y: 2.5, w: 1.45, h: 0.25, fontSize: 10.5, color: a ? col.teal : col.muted });
    });
    code(s,
      "$ sudo bash docs/debug/rov_healthcheck.sh --top 192.168.2.1 --cams 4\n" +
      "A · Power and heat\n" +
      "  ✅ A1  SoC temperature          64 °C\n" +
      "  ❌ A3  Under-voltage            0x50005\n" +
      "         → means: the supply sagged below 4.63 V\n" +
      "B · Cameras and USB\n" +
      "  ⚠️ B4  USB bus sharing          3 cameras on bus 1 @480M\n" +
      "  ❌ B5  USB / camera errors      7 resets/disconnects\n" +
      "E · Tether and network\n" +
      "  ⚠️ E4  Ping topside             avg 3.1 ms, max 24 ms\n" +
      "Start with A3: the first ❌ in pipeline order\nis usually the cause of the rest.",
      0.6, 3.0, 7.3, 3.2, { fontSize: 12 });
    text(s, "example output", { x: 0.6, y: 6.22, w: 7.3, h: 0.28, fontSize: 10.5, italic: true, color: col.muted, align: "right" });
    [["Write the symptom", "what, which cameras, when, what changed", col.cyan],
     ["Run the health check", "10 s on the ROV · ✅ ⚠️ ❌ with the fix", col.teal],
     ["Manual checks F + G", "topside, screen, glass-to-glass", col.amber],
     ["Change one thing", "measure again · post it in the bug report", col.rose]].forEach(([t, b, c], i) => {
      const y = 3.0 + i * 0.8;
      s.addShape(pres.shapes.OVAL, { x: 8.2, y: y + 0.08, w: 0.52, h: 0.52, fill: { color: col.card }, line: { color: c, width: 2 }, objectName: `dstep-${i}` });
      text(s, `${i + 1}`, { x: 8.2, y: y + 0.08, w: 0.52, h: 0.52, fontSize: 16, bold: true, color: c, align: "center", valign: "middle" });
      text(s, t, { x: 8.85, y: y + 0.02, w: 3.85, h: 0.35, fontSize: 15, bold: true, color: c });
      text(s, b, { x: 8.85, y: y + 0.36, w: 3.85, h: 0.32, fontSize: 12, color: col.muted });
    });
    text(s, `ROV_Debug_Checklist.md · ${ROWS.length} checks · ${ROUTES} routes`, { x: 8.2, y: 6.22, w: 4.5, h: 0.28, fontSize: 11, bold: true, color: col.amber });
  }

  // ======================================================================= L1 · leaders' session
  {
    const s = content("Homework · for team leaders", "Leaders: run it as one 90-minute session a week",
      "The experiments are not homework that members do alone and forget. Each team leader runs them with their members as a weekly mini-workshop, and docs/experiments/Leader_Guide.md is the recipe. Members get the handbook; leaders get the recipe, which has a plan for each of the six weeks, the kit list, an answer key with typical results, common mistakes and debrief questions, and a printable result sheet. " +
      "Every session has the same rhythm. Ten minutes: ask one big question, and everyone writes a prediction on a sticky note for the prediction board. Five minutes of briefing: why it matters and the safety rules. Five minutes of pre-flight: the health check, because an experiment on a broken ROV measures the fault. Forty minutes of measuring at stations, where the leader walks around asking questions and never touches the keyboard. Fifteen minutes for each pair to explain its number. Ten minutes to reveal the predictions and agree one action. Five minutes to post results and clean up. " +
      "The leader wears three hats: facilitator (ask, don't tell), safety officer (props off, one person in a red cap types the tc commands, nobody leaves until the clean-up check passes), and referee (verify the evidence, add the labels, read out the leaderboard). If time runs short, cut measuring, never the debrief: that is where the learning happens.");
    const segs = [["Hook + predict", 10, col.cyan], ["Brief", 5, col.muted], ["Pre-flight", 5, col.teal], ["Measure at stations", 40, col.amber],
                  ["Explain", 15, col.cyan], ["Reveal + debrief", 10, col.rose], ["Post", 5, col.muted]];
    const X0 = 0.6, W = 12.1, total = 90;
    let x = X0, t = 0;
    segs.forEach(([n, m, c], i) => {
      const w = W * m / total;
      s.addShape(pres.shapes.RECTANGLE, { x: x + 0.02, y: 2.2, w: w - 0.04, h: 0.62, fill: { color: c }, line: { type: "none" }, objectName: `seg-${i}` });
      text(s, `${m}′`, { x, y: 2.2, w, h: 0.62, fontSize: m >= 10 ? 15 : 12, bold: true, color: col.bg, align: "center", valign: "middle" });
      const lw = Math.max(w, 1.3), lx = Math.min(Math.max(x + w / 2 - lw / 2, X0), X0 + W - lw);
      text(s, n, { x: lx, y: i % 2 ? 2.9 : 1.72, w: lw, h: 0.4, fontSize: 12.5, bold: true, color: c === col.muted ? col.text : c, align: "center", valign: i % 2 ? "top" : "bottom" });
      x += w; t += m;
    });
    text(s, "0:00", { x: X0, y: 3.3, w: 0.8, h: 0.3, fontSize: 10.5, color: col.muted });
    text(s, "1:30", { x: X0 + W - 0.8, y: 3.3, w: 0.8, h: 0.3, fontSize: 10.5, color: col.muted, align: "right" });
    [["🧭 Facilitator", "Ask, don't tell. Coaching questions, never the keyboard. The answer key is for you, not for reading out.", col.cyan],
     ["🦺 Safety officer", "Props off on the bench. One red cap types tc, with a 5-minute auto-undo. Nobody leaves until E7 is ✅.", col.rose],
     ["⚖️ Referee", "Prediction, repeats, units, evidence, a stage named. Then label the issue; the board does the rest.", col.amber]].forEach(([h, b, c], i) => {
      const bx = 0.6 + i * 4.075;
      box(s, bx, 3.8, 3.95, 1.65, { line: c });
      text(s, h, { x: bx + 0.18, y: 3.9, w: 3.6, h: 0.42, fontSize: 17, bold: true, color: c });
      text(s, b, { x: bx + 0.18, y: 4.35, w: 3.62, h: 1.05, fontSize: 12.5, color: col.muted });
    });
    box(s, 0.6, 5.65, 12.1, 0.8, { line: col.teal });
    text(s, [
      { text: "Leaders get ", options: { color: col.muted } }, { text: "Leader_Guide.md", options: { bold: true, color: col.teal } },
      { text: ": 6 session plans · kit list · answer key · result sheet.   Members get ", options: { color: col.muted } },
      { text: "ROV_Experiments.md", options: { bold: true, color: col.teal } }, { text: ". Short on time? Cut measuring, never the debrief.", options: { color: col.muted } },
    ], { x: 0.8, y: 5.65, w: 11.8, h: 0.8, fontSize: 13.5, valign: "middle" });
  }

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  await pres.writeFile({ fileName: OUT });
  await writeTheme(OUT, THEME);
  console.log("wrote", OUT, `| checklist: ${ROWS.length} checks (${ROWS.filter((r) => r.auto).length} automatic), ${ROUTES} routes`);
})();
