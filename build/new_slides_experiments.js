// "ROV experiments" homework section (Nov 2026): 7 slides that replace the old "Practice: measure your own ROV" slide.
// Experiments, points and badges are read from docs/experiments/ROV_Experiments.md (the mission map), so slides and doc agree.
//
//   python3 build/make_experiment_images.py      # pictures (once)
//   node build/new_slides_experiments.js         # → out/new_slides_experiments.pptx
//   see build/README.md for the insert command
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const { THEME, HEX, makeHelpers } = require("./deck_helpers");
const { writeTheme } = require("./write_theme");

const ROOT = path.join(__dirname, "..");
const OUT = path.join(ROOT, "out", "new_slides_experiments.pptx");
const DOC = fs.readFileSync(path.join(ROOT, "docs", "experiments", "ROV_Experiments.md"), "utf8");
const EXPS = [...DOC.matchAll(/^\| (E\d+) \| (.+?) \| (.+?) \| (🟢|🟡|🔴) \| (\d+) \| (.+?) \|$/gm)]
  .map((m) => ({ id: m[1], name: m[2], badge: m[3].trim(), level: m[4], pts: +m[5], where: m[6] }));
const TOTAL = EXPS.reduce((a, e) => a + e.pts, 0);
const IMG = (...p) => path.join(ROOT, "docs", ...p);

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const H = makeHelpers(pres);
  const { col, text, rich, box, arrow, code, pill } = H;
  pres.defineSlideMaster({
    title: "MIA_CONTENT", background: { color: HEX.bg },
    objects: [
      { placeholder: { options: { name: "kicker", type: "body", x: 0.6, y: 0.32, w: 10, h: 0.3, fontSize: 12, bold: true, color: col.cyan, fontFace: "Arial", charSpacing: 2, margin: 0, valign: "middle" }, text: "" } },
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.66, w: 12.1, h: 0.85, fontSize: 32, bold: true, color: col.text, fontFace: "Arial", margin: 0, valign: "middle", align: "left" }, text: "" } },
    ],
  });
  const slides = {};
  const content = (key, kicker, title, notes) => {
    const s = pres.addSlide({ masterName: "MIA_CONTENT" });
    s.addText(kicker.toUpperCase(), { placeholder: "kicker" });
    s.addText(title, { placeholder: "title" });
    s.addNotes(notes);
    slides[key] = Object.keys(slides).length + 1;
    return s;
  };
  const LV = { "🟢": col.teal, "🟡": col.amber, "🔴": col.rose };
  const BADGE = { "⏱": "Latency Hunter", "📡": "Tether Whisperer", "💥": "Chaos Monkey", "🔥": "Heat and Power", "🎯": "Encoder Tuner", "👁": "Pilot's Eye" };
  const nb = Object.keys(BADGE).length;

  // ======================================================================= X1 · mission briefing
  {
    const s = content("x_mission", "Homework · the ROV experiments", `${EXPS.length} experiments. One real ROV. Every number is yours.`,
      `This replaces the old "measure your own ROV" homework. Everything we argued about today (latency, bandwidth, loss, heat, encoder limits, what the pilot can read) can be measured on our own ROV, and docs/experiments/ROV_Experiments.md turns each of those numbers into an experiment: ${EXPS.length} of them, from 15-minute bench checks to pool-day tests with a pilot. ` +
      `It is a game on purpose. Every experiment follows four steps: predict (everyone writes a number before touching anything), measure (repeat, report median and worst), explain (which stage causes it, using the field guide), post (a GitHub issue with the Experiment result template). A mentor verifies it and the points go on the leaderboard, which we read out at every weekly knowledge exchange. ` +
      `There are ${nb} badges, ${TOTAL} points in total, ranks from Cadet to Chief Engineer, and a 6-week boss level for the team that turns the numbers into a better system. Ask the room: who wants to be the first Latency Hunter?`);
    [[`${EXPS.length}`, "experiments", col.cyan], [`${nb}`, "badges", col.amber], [`${TOTAL}`, "points to win", col.teal], ["1", "boss level", col.rose]].forEach(([v, l, c], i) => {
      const x = 0.6 + i * 3.05;
      box(s, x, 1.75, 2.9, 1.55, { line: c });
      text(s, v, { x, y: 1.85, w: 2.9, h: 0.9, fontSize: 48, bold: true, color: c, align: "center", fontFace: "Arial" });
      text(s, l.toUpperCase(), { x, y: 2.75, w: 2.9, h: 0.4, fontSize: 13, bold: true, color: col.muted, align: "center", charSpacing: 1 });
    });
    const steps = [["1 · Predict", "Write a number before you touch anything", col.cyan], ["2 · Measure", "Repeat it. Report median and worst", col.teal],
                   ["3 · Explain", "Which stage causes it? Use the field guide", col.amber], ["4 · Post", "GitHub issue → a mentor verifies → points", col.rose]];
    steps.forEach(([t, b, c], i) => {
      const x = 0.6 + i * 3.05;
      s.addShape(pres.shapes.OVAL, { x: x + 0.95, y: 3.6, w: 1.0, h: 1.0, fill: { color: col.card }, line: { color: c, width: 3 }, objectName: `step-${i}` });
      text(s, `${i + 1}`, { x: x + 0.95, y: 3.6, w: 1.0, h: 1.0, fontSize: 30, bold: true, color: c, align: "center", valign: "middle" });
      text(s, t.split(" · ")[1], { x, y: 4.7, w: 2.9, h: 0.45, fontSize: 18, bold: true, color: c, align: "center" });
      text(s, b, { x: x + 0.15, y: 5.15, w: 2.6, h: 0.75, fontSize: 13, color: col.muted, align: "center" });
      if (i < 3) arrow(s, x + 2.05, 4.1, x + 2.98, 4.1, col.muted);
    });
    text(s, "docs/experiments/ROV_Experiments.md  ·  start tonight with E0 and E1", { x: 0.6, y: 6.1, w: 12.1, h: 0.4, fontSize: 14, color: col.amber, bold: true, align: "center" });
  }

  // ======================================================================= X2 · rules
  {
    const s = content("x_rules", "Homework · how the game works", "Points, bonuses, ranks: measured, not claimed",
      "Three levels: Starter experiments are 15 points and take up to half an hour on the bench; Core experiments are 30 points, about an hour, sometimes in the pool; Advanced are 50 points and take an afternoon of careful work. " +
      "Bonuses reward good engineering habits, not speed: a written prediction within 20 % of the result (+5), another pair reproducing your result (+10 for both pairs), finding a real defect that becomes an issue with a fix plan (+20), and the clearest chart or photo of the week (+10). " +
      "Ranks: everyone starts as Cadet; 100 points makes a Technician, 250 an Engineer, and Chief Engineer needs 450 points and three badges, so nobody gets there by repeating easy experiments. A badge means every experiment in its category is done. " +
      "Work in pairs and rotate roles every experiment: the operator runs the commands, the recorder writes numbers, conditions and photos; in bigger groups a skeptic looks for what could make the result wrong.");
    text(s, "LEVELS", { x: 0.6, y: 1.7, w: 5.8, h: 0.3, fontSize: 12, bold: true, color: col.muted, charSpacing: 1 });
    [["🟢  Starter", "15 pts", "≤ 30 min, bench", col.teal], ["🟡  Core", "30 pts", "≈ 1 h, sometimes the pool", col.amber], ["🔴  Advanced", "50 pts", "an afternoon, careful work", col.rose]].forEach(([n, p, d, c], i) => {
      const y = 2.05 + i * 0.72;
      box(s, 0.6, y, 5.8, 0.6, { line: c });
      text(s, n, { x: 0.8, y, w: 2.2, h: 0.6, fontSize: 16, bold: true, color: c, valign: "middle" });
      text(s, p, { x: 2.9, y, w: 1.0, h: 0.6, fontSize: 16, bold: true, valign: "middle" });
      text(s, d, { x: 3.9, y, w: 2.45, h: 0.6, fontSize: 12.5, color: col.muted, valign: "middle" });
    });
    text(s, "BONUSES", { x: 0.6, y: 4.3, w: 5.8, h: 0.3, fontSize: 12, bold: true, color: col.muted, charSpacing: 1 });
    [["🎯 Prediction within 20 %", "+5"], ["🔁 Replicated by another pair", "+10"], ["🐞 Found a real defect", "+20"], ["📊 Chart of the week", "+10"]].forEach(([n, p], i) => {
      const x = 0.6 + (i % 2) * 2.95, y = 4.65 + Math.floor(i / 2) * 0.72;
      box(s, x, y, 2.85, 0.6, {});
      text(s, n, { x: x + 0.12, y, w: 2.1, h: 0.6, fontSize: 12, valign: "middle" });
      text(s, p, { x: x + 2.15, y, w: 0.62, h: 0.6, fontSize: 15, bold: true, color: col.teal, valign: "middle", align: "right" });
    });
    text(s, "RANKS", { x: 6.9, y: 1.7, w: 5.8, h: 0.3, fontSize: 12, bold: true, color: col.muted, charSpacing: 1 });
    [["🪸 Cadet", "start", col.muted], ["🔧 Technician", "100 pts", col.cyan], ["⚙️ Engineer", "250 pts", col.amber], ["🧠 Chief Engineer", "450 pts + 3 badges", col.rose]].forEach(([n, p, c], i) => {
      const h = 0.9 + i * 0.55, x = 6.9 + i * 1.47, y = 5.95 - h;
      box(s, x, y, 1.37, h, { line: c });
      text(s, n, { x: x + 0.05, y: y + 0.08, w: 1.27, h: 0.75, fontSize: 12.5, bold: true, color: c, align: "center" });
      text(s, p, { x: x + 0.05, y: y + h - 0.45, w: 1.27, h: 0.38, fontSize: 10.5, color: col.muted, align: "center" });
    });
    text(s, "Work in pairs · rotate roles: operator · recorder · skeptic", { x: 0.6, y: 6.15, w: 12.1, h: 0.35, fontSize: 13, color: col.muted, italic: true });
  }

  // ======================================================================= X3 · mission map
  {
    const groups = Object.keys(BADGE).map((b) => [b, EXPS.filter((e) => e.badge === b)]);
    const s = content("x_map", "Homework · the mission map", `Six badges, ${EXPS.length} experiments, camera to pilot`,
      "Every experiment, grouped by badge. Start with E0, the inventory: it is required before anything else, because every later number refers back to it. " +
      groups.map(([b, list]) => `${BADGE[b]}: ${list.map((e) => `${e.id} ${e.name}`).join("; ")}.`).join(" ") +
      " Colour dots show the level: green 15 points, amber 30, red 50. The doc has, for each one, the question, a prediction prompt, exact commands, a result table, what good looks like and a go-further bonus.");
    box(s, 0.6, 1.62, 12.1, 0.45, { line: col.amber });
    text(s, "START HERE  ·  E0 Know your ROV: the inventory of computer, cameras, streams and topside (required, 30 pts)", { x: 0.8, y: 1.62, w: 11.8, h: 0.45, fontSize: 13, bold: true, color: col.amber, valign: "middle" });
    groups.forEach(([b, list], i) => {
      const x = 0.6 + (i % 3) * 4.075, y = 2.22 + Math.floor(i / 3) * 2.2, w = 3.95;
      box(s, x, y, w, 2.08, {});
      text(s, `${b}  ${BADGE[b]}`, { x: x + 0.15, y: y + 0.07, w: w - 0.3, h: 0.4, fontSize: 16, bold: true, color: col.cyan });
      const runs = [];
      list.forEach((e, k) => {
        runs.push({ text: "● ", color: LV[e.level], fontSize: 12, breakLine: false });
        runs.push({ text: `${e.id}  `, bold: true, fontSize: 13, breakLine: false });
        runs.push({ text: e.name, fontSize: 13, color: col.text, breakLine: k < list.length - 1 });
      });
      rich(s, runs, x + 0.15, y + 0.5, w - 0.3, 1.52, { fit: "none" });
    });
  }

  // ======================================================================= X4 · spotlight E1
  {
    const s = content("x_e1", "Spotlight · E1 ⏱ Latency Hunter", "How late is the pilot? Write your guess now",
      "Do this one live if there is time. Before showing anything, everyone writes down how many milliseconds late they think the pilot camera is. Then: open docs/experiments/ms_clock.html full screen on the topside laptop, point the pilot camera at it, put the video window on the same screen, and take a phone photo of both. The difference between the two clocks is the glass-to-glass latency; in the picture it is 567 − 441 = 126 ms. " +
      "Repeat ten times and report the median and the worst; a slow-motion video gives ten samples in ten seconds. Then repeat with all cameras streaming and with the thrusters running, which is where the surprises are. " +
      "Target: median at or below 150 ms, worst at or below 250 ms. The closest prediction in the room wins the first bonus of the season.");
    s.addImage({ path: IMG("experiments", "img", "g2g-photo.jpg"), x: 0.6, y: 1.7, w: 6.6, h: 3.71, objectName: "g2g-photo" });
    text(s, "latency = clock on the screen − clock in the video", { x: 0.6, y: 5.55, w: 6.6, h: 0.4, fontSize: 15, bold: true, color: col.cyan });
    text(s, "Slow-motion phone video: 10 samples in 10 s.", { x: 0.6, y: 5.95, w: 6.6, h: 0.4, fontSize: 13, color: col.muted });
    [["Open ms_clock.html full screen (press F)", col.cyan], ["Point the pilot camera at it; video window next to it", col.cyan],
     ["Photograph both. Subtract. Repeat 10×", col.teal], ["Again with all cameras, then with thrusters on", col.amber],
     ["Post median + worst. Target ≤ 150 / 250 ms", col.rose]].forEach(([t, c], i) => {
      const y = 1.7 + i * 0.93;
      s.addShape(pres.shapes.OVAL, { x: 7.5, y: y + 0.1, w: 0.6, h: 0.6, fill: { color: col.card }, line: { color: c, width: 2 }, objectName: `n-${i}` });
      text(s, `${i + 1}`, { x: 7.5, y: y + 0.1, w: 0.6, h: 0.6, fontSize: 18, bold: true, color: c, align: "center", valign: "middle" });
      text(s, t, { x: 8.25, y, w: 4.45, h: 0.8, fontSize: 15, valign: "middle" });
    });
  }

  // ======================================================================= X5 · spotlight chaos monkey
  {
    const s = content("x_chaos", "Spotlight · 💥 Chaos Monkey", "Break it on purpose, before the pool does it for you",
      "The Chaos Monkey experiments (E10 to E15) recreate competition failures on the bench: packet loss with tc netem, a sudden bandwidth squeeze with tc tbf, a frozen encoder with kill -STOP, unplugged cameras and tethers, a CPU at 100 %, and a power cut in the middle of a recording. " +
      "For each, the team records what the pilot sees and whether the system recovers by itself. The picture is a real result from the Encoding Lab: 7.5 kB lost from a stream smears the image until the next keyframe. " +
      "Safety first: tc affects all traffic including control, so these run on the bench with the props off, and the qdisc is removed and checked afterwards. " +
      "The most valuable result is a bug: if a frozen picture looks live, or control stops when video saturates the link, the team found the most important defect of the season and earns the +20 bonus.");
    code(s, "# E10 · lose 1 % of packets\nsudo tc qdisc add dev eth0 root netem loss 1%\n\n# E12 · squeeze the tether to 5 Mb/s\nsudo tc qdisc change dev eth0 root tbf rate 5mbit \\\n     burst 32kbit latency 50ms\n\n# E14 · freeze one encoder\nkill -STOP <pid>     # … then kill -CONT <pid>\n\n# afterwards, ALWAYS\nsudo tc qdisc del dev eth0 root",
      0.6, 1.7, 6.0, 3.6, { fontSize: 13 });
    s.addImage({ path: IMG("streaming", "img", "diagnostics", "packet-loss.jpg"), x: 6.85, y: 1.7, w: 5.85, h: 3.29, objectName: "loss-img" });
    text(s, "What does the pilot see? Does it recover by itself? Does the UI tell the truth?", { x: 6.85, y: 5.05, w: 5.85, h: 0.6, fontSize: 13.5, color: col.muted });
    box(s, 0.6, 5.75, 12.1, 0.7, { line: col.rose });
    text(s, "⚠  Bench only · props off · tc affects control traffic too · remove the qdisc and check with  tc qdisc show", { x: 0.8, y: 5.75, w: 11.8, h: 0.7, fontSize: 14, bold: true, color: col.rose, valign: "middle" });
  }

  // ======================================================================= X6 · spotlight eye test
  {
    const s = content("x_eye", "Spotlight · 👁 Pilot's Eye", "Eye test for the ROV: the lowest readable bitrate",
      "Pilot's Eye experiments put a human in the loop. E24 is an eye test for the ROV: print and laminate a chart of letters and digits from 40 down to 5 mm, add the smallest marking from the mission props, put it one metre in front of the pilot camera under water, and step the bitrate down: 8, 4, 2, 1, 0.5 Mb/s. " +
      "The pictures are a real x264 encode of a drifting, slightly noisy underwater view: at 1 Mb/s every row is readable; at 0.2 Mb/s the bottom row is gone and the row above it breaks up. The lowest readable bitrate becomes requirement N2 of the boss level. " +
      "E25 goes further: a blind A/B test where the pilot does a timed task with two settings in a hidden order. E22 (lights in a bucket of milky water) and E23 (manual exposure and white balance) round off the badge.");
    s.addImage({ path: IMG("experiments", "img", "eye-test.jpg"), x: 0.6, y: 1.68, w: 12.1, h: 3.51, objectName: "eye-test" });
    [["1 · Print the chart", "letters 40 → 5 mm + the mission's smallest marking; laminate it", col.cyan],
     ["2 · Step the bitrate down", "8 → 4 → 2 → 1 → 0.5 Mb/s; the pilot reads, the recorder checks", col.amber],
     ["3 · Write the requirement", "the lowest readable bitrate becomes N2 for the boss level", col.teal]].forEach(([t, b, c], i) => {
      const x = 0.6 + i * 4.075;
      box(s, x, 5.35, 3.95, 1.2, { line: c });
      text(s, t, { x: x + 0.18, y: 5.42, w: 3.6, h: 0.4, fontSize: 15, bold: true, color: c });
      text(s, b, { x: x + 0.18, y: 5.83, w: 3.6, h: 0.65, fontSize: 12.5, color: col.muted });
    });
  }

  // ======================================================================= X7 · schedule + boss
  {
    const s = content("x_plan", "Homework · the plan", "Six weeks of experiments, then the boss level",
      "A suggested schedule. Week 1 is the baseline on the bench (E0, E1, E6, E7, E20, E21). Week 2 is latency and encoders (E2, E3, E4, E9, E19). Week 3 is chaos week, bench only with props off (E10 to E15). Weeks 4 and 5 are pool days (E16, E17, E18, E23, then E5, E22, E24, E25). Week 6 is for the advanced experiments (E8, E26) and replications. " +
      "Weeks 7 to 12 are the boss level: the team turns the numbers into requirements (F1–F6, N1–N7), compares at least two architecture options with measurements, builds and tests, and gives a 10-minute demonstration judged on measured results, evidence, failure handling, pilot usability and documentation. " +
      "Results are posted as GitHub issues with the Experiment result template; a mentor verifies and labels them, and docs/experiments/experiment_board.py prints the leaderboard and badges for the weekly knowledge exchange. Tonight: everyone does E0 and E1.");
    const weeks = [["W1", "Baseline", "E0 E1 E6 E7 E20 E21", col.cyan], ["W2", "Latency + encoders", "E2 E3 E4 E9 E19", col.cyan], ["W3", "Chaos week", "E10 → E15", col.rose],
                   ["W4", "Pool day 1", "E16 E17 E18 E23", col.teal], ["W5", "Pool day 2", "E5 E22 E24 E25", col.teal], ["W6", "Advanced", "E8 E26 + replications", col.amber]];
    weeks.forEach(([w, t, e, c], i) => {
      const x = 0.6 + i * 1.72;
      s.addShape(pres.shapes.CHEVRON, { x, y: 1.75, w: 1.82, h: 0.75, fill: { color: c }, line: { type: "none" }, objectName: `wk-${i}` });
      text(s, w, { x: x + 0.3, y: 1.75, w: 1.2, h: 0.75, fontSize: 18, bold: true, color: HEX.bg, align: "center", valign: "middle" });
      text(s, t, { x: x + 0.05, y: 2.6, w: 1.65, h: 0.45, fontSize: 13, bold: true, color: c, align: "center" });
      text(s, e, { x: x + 0.05, y: 3.05, w: 1.65, h: 0.7, fontSize: 11.5, color: col.muted, align: "center" });
    });
    s.addShape(pres.shapes.CHEVRON, { x: 10.92, y: 1.75, w: 1.82, h: 0.75, fill: { color: col.amber }, line: { type: "none" }, objectName: "wk-boss" });
    text(s, "W7–12", { x: 11.15, y: 1.75, w: 1.3, h: 0.75, fontSize: 16, bold: true, color: HEX.bg, align: "center", valign: "middle" });
    text(s, "👑 Boss level", { x: 10.95, y: 2.6, w: 1.75, h: 0.45, fontSize: 13, bold: true, color: col.amber, align: "center" });
    text(s, "the 6-week challenge", { x: 10.95, y: 3.05, w: 1.75, h: 0.7, fontSize: 11.5, color: col.muted, align: "center" });
    [["Post", "GitHub issue → 🧪 Experiment result template: prediction, result, method, evidence, explanation", col.cyan],
     ["Verify", "a mentor adds exp:E07 + bonus labels", col.teal],
     ["Leaderboard", "experiment_board.py → read out at every knowledge exchange", col.amber]].forEach(([t, b, c], i) => {
      const x = 0.6 + i * 3.1;
      box(s, x, 4.0, 2.95, 1.45, { line: c });
      text(s, t, { x: x + 0.15, y: 4.08, w: 2.65, h: 0.4, fontSize: 16, bold: true, color: c });
      text(s, b, { x: x + 0.15, y: 4.5, w: 2.7, h: 0.9, fontSize: 12, color: col.muted });
    });
    box(s, 9.9, 4.0, 2.8, 1.45, { line: col.rose, fill: col.card });
    text(s, "TONIGHT", { x: 10.05, y: 4.08, w: 2.5, h: 0.35, fontSize: 12, bold: true, color: col.rose, charSpacing: 2 });
    text(s, "E0 + E1", { x: 10.05, y: 4.4, w: 2.5, h: 0.6, fontSize: 30, bold: true, color: col.text });
    text(s, "inventory + latency", { x: 10.05, y: 4.98, w: 2.5, h: 0.4, fontSize: 12, color: col.muted });
    text(s, "Boss level judged on: requirements met (measured) 30 % · evidence 20 % · failure handling 20 % · pilot usability 15 % · documentation 15 %",
      { x: 0.6, y: 5.65, w: 12.1, h: 0.7, fontSize: 13, color: col.muted, italic: true });
  }

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  await pres.writeFile({ fileName: OUT });
  await writeTheme(OUT, THEME);
  fs.writeFileSync(OUT.replace(/\.pptx$/, ".json"), JSON.stringify(slides, null, 1));
  console.log("wrote", OUT, Object.keys(slides).length, "slides;", EXPS.length, "experiments,", TOTAL, "points");
})();
