// Slides 42–68: engineering practice, testing, code review, Git, organisation, UX, final challenge.
const fi = require("react-icons/fi");
const tb = require("react-icons/tb");
const { HEX } = require("./deck_helpers");

module.exports = async function partB(ctx) {
  const { pres, H, D, content, section } = ctx;
  const { col, text, bullets, rich, box, iconCircle, card, arrow, flow, table, stat, code, pill } = H;

  // ================================================================ SECTION 5 Engineering practice
  section("Engineering practice", "05", "Engineering practice", "A lightweight development process for a student team", D.img.section2,
    "Session 2 opens here. Start with 5–10 minutes of results from the diagnostic homework, then transition: 'We found things we didn't know. How do we make sure we keep finding them before competition day, not on it?'");
  // ---------------------------------------------------------------- integration cliff
  {
    const s = content("Engineering practice", "Why process?", "“We'll integrate the week before competition”",
      "Tell a story (yours or a typical one): every subsystem 'works' alone; the week before competition everything is connected for the first time; the camera driver conflicts with the thruster controller over USB power, the web app can't keep up with 8 streams, nobody remembers why a setting was chosen. The chart is illustrative, not data: big-bang integration discovers defects late, when they're most expensive. Continuous integration spreads discovery out. Process is not bureaucracy — it is a way to find problems while there is still time to fix them.");
    s.addChart(pres.charts.LINE, [
      { name: "Big-bang integration (defects found)", labels: ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8", "W9", "W10"], values: [0, 0, 1, 0, 1, 1, 2, 3, 14, 22] },
      { name: "Continuous integration (defects found)", labels: ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8", "W9", "W10"], values: [3, 5, 6, 5, 6, 4, 4, 3, 2, 1] }], {
      x: 0.6, y: 1.7, w: 7.6, h: 4.9, chartColors: [HEX.rose, HEX.teal], lineSize: 2.5, lineDataSymbol: "circle", lineDataSymbolSize: 7, showLegend: true, legendPos: "b",
      showTitle: true, title: "Illustrative: when are defects discovered? (weeks before competition)", catAxisLabelColor: HEX.muted, valAxisLabelColor: HEX.muted,
      valGridLine: { color: HEX.grid, size: 0.75 }, catGridLine: { style: "none" }, legendColor: HEX.muted, titleColor: HEX.text, titleFontSize: 14,
      catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", legendFontFace: "+mn-lt", titleFontFace: "+mj-lt", objectName: "integration-chart" });
    const pts = [["Late discovery is expensive", "A defect found the night before the mission has no good fix."], ["Integration is where systems fail", "Interfaces between hardware, firmware and web app — not inside them."], ["Decisions get lost", "Six months later, nobody remembers why GOP = 60."]];
    pts.forEach(([a, b], i) => { const y = 1.75 + i * 1.6; box(s, 8.5, y, 4.2, 1.42, { fill: col.card });
      text(s, a, { x: 8.75, y: y + 0.12, w: 3.8, h: 0.42, fontSize: 16, bold: true, color: col.cyan }); text(s, b, { x: 8.75, y: y + 0.56, w: 3.8, h: 0.8, fontSize: 14, color: col.muted }); });
  }
  await require("./deck_part_new").qualityTimesEfficiency(ctx);
  // ---------------------------------------------------------------- SDLC loop
  {
    const s = content("Engineering practice", "The software development lifecycle", "Nine stages, sized for a student team",
      "Walk the loop with the ROV example for each stage: Requirements ('pilot camera latency ≤ 200 ms'); Analysis & architecture (where to encode, which protocol); Planning (break into tasks, assign owners); Implementation (small branches); Testing (unit, integration, pool); Code review (every PR); Integration (merge to main weekly, run on the real ROV); Release (tag v0.3-pool-test); Maintenance (retrospective, fix, improve). It's a loop, iterated every 1–2 weeks — not a waterfall.");
    const st = [["Requirements", "what must it do? how well?"], ["Analysis & architecture", "where to encode? which protocol?"], ["Planning", "tasks, owners, order"], ["Implementation", "small branches"], ["Testing", "unit → pool test"], ["Code review", "every pull request"], ["Integration", "weekly, on the real ROV"], ["Release", "tag a version"], ["Maintenance", "retro, fix, improve"]];
    const cx = 6.65, cy = 4.3, Ry = 1.95, Rx = 4.3;
    st.forEach(([a, b], i) => {
      const ang = -Math.PI / 2 + i * 2 * Math.PI / st.length; const x = cx + Rx * Math.cos(ang) - 1.15, y = cy + Ry * Math.sin(ang) - 0.39;
      box(s, x, y, 2.3, 0.78, { fill: col.card, line: i === 0 ? HEX.cyan : undefined });
      text(s, `${i + 1}  ${a}`, { x: x + 0.12, y: y + 0.05, w: 2.1, h: 0.36, fontSize: 13, bold: true, color: col.cyan });
      text(s, b, { x: x + 0.12, y: y + 0.4, w: 2.1, h: 0.32, fontSize: 11, color: col.muted });
    });
    s.addShape(pres.shapes.OVAL, { x: cx - 1.3, y: cy - 0.72, w: 2.6, h: 1.44, fill: { color: col.cyan, transparency: 85 }, line: { color: col.cyan, width: 1.5, dashType: "dash" }, objectName: "sdlc-hub" });
    text(s, "1–2 week loop", { x: cx - 1.3, y: cy - 0.36, w: 2.6, h: 0.4, fontSize: 16, bold: true, align: "center" });
    text(s, "not a waterfall", { x: cx - 1.3, y: cy + 0.04, w: 2.6, h: 0.35, fontSize: 13, color: col.muted, align: "center" });
  }
  // ---------------------------------------------------------------- Requirements
  {
    const s = content("Engineering practice", "Requirements engineering", "Functional vs non-functional requirements",
      "Functional = what the system does. Non-functional = how well (performance, reliability, usability, safety). Good requirements are testable: they contain a number and a condition. Turn 'low latency' into '≤ 200 ms median glass-to-glass, all cameras streaming'. Use the diagnostic measurements from the homework to set realistic numbers. Ask students to rewrite one vague requirement into a testable one — 2-minute exercise.");
    const fr = ["The pilot can switch the primary camera with one key or click", "The UI shows every camera's state: live, degraded, paused, lost", "The system records the primary camera at full quality", "A lost camera reconnects automatically"];
    const nfr = [["Latency", "Primary camera ≤ 200 ms median, ≤ 300 ms worst (10 trials, all streaming)"], ["Bandwidth", "Video ≤ 70 % of measured tether throughput"], ["Reliability", "Camera reconnects within 3 s after USB/IP reconnection"], ["Usability", "A new pilot switches cameras correctly in ≤ 2 s, 9/10 trials"]];
    box(s, 0.6, 1.75, 5.6, 4.8, { fill: col.card });
    pill(s, "FUNCTIONAL — what it does", 0.85, 1.95, 3.4, col.cyan);
    bullets(s, fr, 0.85, 2.55, 5.1, 3.8, { fontSize: 15, gap: 10 });
    box(s, 6.5, 1.75, 6.2, 4.8, { fill: col.card });
    pill(s, "NON-FUNCTIONAL — how well", 6.75, 1.95, 3.6, col.teal);
    nfr.forEach(([a, b], i) => { text(s, a, { x: 6.75, y: 2.55 + i * 0.95, w: 1.6, h: 0.8, fontSize: 15, bold: true, color: col.teal }); text(s, b, { x: 8.35, y: 2.55 + i * 0.95, w: 4.2, h: 0.85, fontSize: 14 }); });
    text(s, "Vague: “low latency”.  Testable: a number, a condition, a method.", { x: 0.6, y: 6.62, w: 12.1, h: 0.35, fontSize: 14, color: col.amber, bold: true });
  }
  // ---------------------------------------------------------------- Epic → task
  {
    const s = content("Engineering practice", "Worked example", "From epic to test case: camera switching",
      "Walk the hierarchy top-down with the camera switching example. Epic = a big capability (multi-camera pilot video). Feature = a deliverable chunk (primary camera selection). User story = one user-visible slice, written from the pilot's point of view, with acceptance criteria in Given/When/Then form. Tasks = developer work items (hours to a day or two). Test cases trace back to acceptance criteria. Point out that the acceptance criteria include a non-functional one (≤ 1 s) and a failure case (camera offline).");
    const lv = [["EPIC", "Multi-camera pilot video", col.violet], ["FEATURE", "Primary camera selection", col.blue], ["USER STORY", "As a pilot, I want to switch the primary camera with one key, so that I can follow the task without looking away from the video.", col.cyan]];
    lv.forEach(([a, b, c], i) => { const y = 1.75 + i * 0.7; box(s, 0.6 + i * 0.3, y, 6.4 - i * 0.3, i === 2 ? 1.05 : 0.58, { fill: col.card, line: c });
      text(s, a, { x: 0.8 + i * 0.3, y: y + 0.08, w: 1.5, h: 0.45, fontSize: 12, bold: true, color: c, valign: "top" }); text(s, b, { x: 2.3 + i * 0.3, y: y + 0.08, w: 4.6 - i * 0.3, h: i === 2 ? 0.92 : 0.45, fontSize: i === 2 ? 13 : 14, valign: "top" }); });
    box(s, 0.6, 4.4, 6.4, 2.25, { fill: col.card });
    text(s, "Acceptance criteria", { x: 0.85, y: 4.48, w: 5.9, h: 0.38, fontSize: 15, bold: true, color: col.cyan });
    bullets(s, ["Given 8 cameras live, when the pilot presses 1–8, the chosen camera is primary within ≤ 1 s", "The selected camera is highlighted in the thumbnail strip", "If the camera is offline, the UI says so — it never shows a frozen frame as live", "Other streams keep running during the switch"], 0.85, 4.9, 6.0, 1.7, { fontSize: 13, gap: 3 });
    box(s, 7.3, 1.75, 5.4, 2.3, { fill: col.card });
    text(s, "Tasks", { x: 7.55, y: 1.85, w: 5, h: 0.38, fontSize: 15, bold: true, color: col.teal });
    bullets(s, ["Keyboard shortcut handler (web)", "Stream manager: attach/detach stream, request keyframe", "Camera state model (live / connecting / lost)", "Thumbnail highlight + offline overlay", "Tests + switch-latency measurement"], 7.55, 2.3, 5.0, 1.75, { fontSize: 13, gap: 2 });
    box(s, 7.3, 4.25, 5.4, 2.35, { fill: col.card });
    text(s, "Test cases (trace to criteria)", { x: 7.55, y: 4.35, w: 5, h: 0.38, fontSize: 15, bold: true, color: col.amber });
    bullets(s, ["TC-01 switch 1→8 ×20, measure time (≤ 1 s)", "TC-02 unplug camera 3, press 3 → offline shown", "TC-03 mash keys 1–8 rapidly for 10 s → no crash, final selection correct", "TC-04 switch during full-bandwidth load"], 7.55, 4.8, 5.0, 1.75, { fontSize: 13, gap: 2 });
  }
  // ---------------------------------------------------------------- DoR / DoD
  {
    const s = content("Engineering practice", "Shared agreements", "Definition of Ready & Definition of Done",
      "Definition of Ready: a story may only be started when it meets these — avoids 'I started but nobody knew what done looks like'. Definition of Done: a story is only done when ALL apply — avoids 'it works on my laptop'. Keep both lists short, print them, stick them on the wall, and review them at retrospectives. The DoD here deliberately includes 'tested on the real ROV hardware' and 'pilot has tried it' for UI work.");
    const dor = ["User story written from the user's point of view", "Acceptance criteria are testable (numbers, conditions)", "Dependencies known (hardware? another team?)", "Small enough for ≤ 1 week", "Someone can test it"];
    const dod = ["Code reviewed and merged to main", "Tests written and passing (unit + the relevant integration test)", "Acceptance criteria verified — on the real ROV for hardware-related work", "Failure cases tested (disconnect, overload)", "Docs / decision log updated", "UI changes tried by a pilot"];
    await card(s, 0.6, 1.75, 5.9, 4.8, { icon: fi.FiPlayCircle, title: "Definition of Ready", bullets: dor, bodySize: 18, gap: 12 });
    await card(s, 6.8, 1.75, 5.9, 4.8, { icon: fi.FiCheckCircle, title: "Definition of Done", bullets: dod, bodySize: 17, gap: 10, iconColor: HEX.teal, iconFill: col.teal });
  }
  // ---------------------------------------------------------------- Testing levels
  {
    const s = content("Engineering practice", "Testing", "Testing levels and techniques",
      "Pyramid: many fast unit tests (pure functions: bitrate allocator, command parser, PID maths), fewer integration tests (stream manager + real FFmpeg/GStreamer pipeline, web app + backend), few system tests (whole ROV in the pool). Acceptance tests check the acceptance criteria with the pilot. Techniques cut across levels: boundary (0, 1, 8, 9 cameras; max bitrate), negative (invalid commands, unplugged camera), stress (8 cameras + full thrust + 10 minutes), performance (latency, CPU), regression (re-run old tests after every change).");
    const lv = [["System / acceptance", "whole ROV in the pool · with the pilot", 3.2, col.violet], ["Integration", "stream manager + FFmpeg · web app + backend", 6.2, col.blue], ["Unit", "allocator · command parser · PID maths", 9.2, col.cyan]];
    lv.forEach(([a, b, w, c], i) => { const x = 0.6 + (9.2 - w) / 2, y = 1.8 + i * 1.25; box(s, x, y, w, 1.05, { fill: c, transparency: 70, line: c });
      text(s, a, { x, y: y + 0.08, w, h: 0.45, fontSize: 16, bold: true, align: "center" }); text(s, b, { x, y: y + 0.52, w, h: 0.45, fontSize: 13, align: "center", color: col.muted }); });
    text(s, "more tests, faster, cheaper  ↓", { x: 0.6, y: 5.6, w: 9.2, h: 0.35, fontSize: 13, color: col.muted, align: "center", italic: true });
    const tech = [["Boundary", "0 / 1 / 8 / 9 cameras, max bitrate"], ["Negative", "invalid commands, unplugged camera"], ["Stress", "8 cams + full thrust, 10 min"], ["Performance", "latency, CPU, temperature"], ["Regression", "re-run old tests after changes"]];
    tech.forEach(([a, b], i) => { const y = 1.8 + i * 0.95; box(s, 10.05, y, 2.65, 0.82, { fill: col.card });
      text(s, a, { x: 10.2, y: y + 0.05, w: 2.4, h: 0.35, fontSize: 14, bold: true, color: col.amber }); text(s, b, { x: 10.2, y: y + 0.4, w: 2.45, h: 0.4, fontSize: 11, color: col.muted }); });
  }
  // ---------------------------------------------------------------- Testing mindset
  {
    const s = content("Engineering practice", "The tester's mindset", "Testing is about discovering how it fails",
      "Key sentence: 'A test that cannot fail is not a test.' Developers test to confirm; testers test to break. Read through the scenarios and ask: 'For which of these do we already know what our system does?' Usually: none. Each scenario has an expected safe behaviour — that is the acceptance criterion. These scenarios feed directly into the competition.");
    const sc = [[fi.FiCameraOff, "Camera disconnected while streaming", "UI shows LOST, others unaffected, auto-reconnect"], [fi.FiWifiOff, "Tether / network lost", "Thrusters go to safe state; UI shows disconnected"], [fi.FiRepeat, "Rapid camera switching", "No crash, no leak, final selection correct"], [fi.FiTrendingUp, "Bandwidth exceeded", "Graceful degradation, control traffic protected"], [fi.FiAlertTriangle, "Corrupted / partial frames", "Decoder recovers at next keyframe, no freeze"], [fi.FiSlash, "Invalid control commands", "Rejected, logged, never executed"], [fi.FiMaximize, "Unsupported resolution", "Clear error, fallback, no crash"], [fi.FiThermometer, "CPU overload / thermal throttling", "Video degrades before control does"]];
    for (let i = 0; i < 8; i++) { const x = 0.6 + (i % 4) * 3.05, y = 1.75 + Math.floor(i / 4) * 2.45;
      box(s, x, y, 2.85, 2.25, { fill: col.card }); await iconCircle(s, sc[i][0], x + 0.2, y + 0.2, 0.52, HEX.amber, col.amber);
      text(s, sc[i][1], { x: x + 0.2, y: y + 0.82, w: 2.45, h: 0.7, fontSize: 14, bold: true }); text(s, "Expect: " + sc[i][2], { x: x + 0.2, y: y + 1.5, w: 2.5, h: 0.7, fontSize: 12, color: col.muted }); }
  }
  // ---------------------------------------------------------------- Testing competition
  {
    const s = content("Engineering practice", "Activity 4 · 60 minutes", "Break the Other Team's Software!",
      "Rules are in Testing_Competition_Guide.md. Teams receive a small implementation (provided in the guide: a camera manager / command validator with seeded defects) or build one in 15 minutes. Then they swap: each team tests the other's code for 20 minutes and files bug reports with the template; developers then get 15 minutes to fix and add regression tests. The referee (you) validates every defect claim. Scoring encourages clear reproduction steps and penalises false positives, so teams learn that a bug report is a product.");
    flow(s, [{ title: "Build", sub: "15 min · implement or receive the module" }, { title: "Swap & attack", sub: "20 min · test the other team's code" }, { title: "Report", sub: "bug reports with steps to reproduce" }, { title: "Fix & regress", sub: "15 min · fix + regression test" }, { title: "Score", sub: "referee validates every claim" }], 0.6, 1.8, 12.1, 1.45, { titleSize: 15, subSize: 11 });
    table(s, [["Event", "Points"], ["Real defect found", "+10"], ["Critical defect (safety, crash, data loss)", "+20"], ["Clear, reproducible steps", "+5"], ["Bug report rejected (false positive / not reproducible)", "−5"], ["Developers fix + regression test passes", "+10"], ["Fix breaks something else (found by referee)", "−10"]], 0.6, 3.6, 7.4, [5.9, 1.5], { fontSize: 14, rowH: 0.44 });
    box(s, 8.3, 3.6, 4.4, 3.08, { fill: col.card, line: HEX.amber });
    text(s, "The lesson", { x: 8.55, y: 3.75, w: 4, h: 0.4, fontSize: 17, bold: true, color: col.amber });
    text(s, "Testing does not prove software works. It discovers how it can fail — before the pool does.", { x: 8.55, y: 4.25, w: 3.95, h: 2.2, fontSize: 16 });
  }
  await require("./deck_part_new").bugHuntLeague(ctx);
  // ---------------------------------------------------------------- Code review
  {
    const s = content("Engineering practice", "Code review", "Reviewing code — without reviewing people",
      "Why: find defects early, spread knowledge (the bus factor of a student team is terrifying), keep consistency. Keep PRs small (< 400 lines) so they can be reviewed in 20 minutes. Comment on the code, not the person: 'This function doesn't handle a disconnected camera' not 'you forgot'. Label comments: blocking vs suggestion vs question. Approve when it improves the codebase and meets the DoD — not when it's perfect. Disagreements: discuss with data or a quick prototype; if still stuck, the subsystem lead decides and it goes in the decision log.");
    const ck = [["Correctness", "does it meet the acceptance criteria? edge cases?"], ["Readability & naming", "would a new member understand it?"], ["Architecture", "right layer? new dependency justified?"], ["Error handling", "camera lost, timeout, bad input?"], ["Resources", "streams, sockets, timers closed?"], ["Concurrency", "races between callbacks / threads?"], ["Performance", "per-frame work, copies, allocations?"], ["Tests & docs", "tests added? decision log updated?"]];
    box(s, 0.6, 1.75, 7.0, 4.85, { fill: col.card });
    text(s, "Reviewer checklist", { x: 0.85, y: 1.88, w: 6.5, h: 0.4, fontSize: 16, bold: true, color: col.cyan });
    ck.forEach(([a, b], i) => { const y = 2.38 + i * 0.52; text(s, a, { x: 0.85, y, w: 2.3, h: 0.45, fontSize: 14, bold: true, valign: "middle" }); text(s, b, { x: 3.15, y, w: 4.3, h: 0.45, fontSize: 13, color: col.muted, valign: "middle" }); });
    const tips = [["Small PRs", "< 400 lines, one purpose"], ["Label comments", "blocking · suggestion · question"], ["Code, not people", "“this misses…”, never “you forgot…”"], ["Approve progress", "better + meets DoD, not perfect"]];
    tips.forEach(([a, b], i) => { const y = 1.75 + i * 1.23; box(s, 7.9, y, 4.8, 1.08, { fill: col.card });
      text(s, a, { x: 8.15, y: y + 0.1, w: 4.4, h: 0.4, fontSize: 16, bold: true, color: col.teal }); text(s, b, { x: 8.15, y: y + 0.52, w: 4.4, h: 0.45, fontSize: 14, color: col.muted }); });
  }
  // ---------------------------------------------------------------- Bad vs good code
  {
    const s = content("Engineering practice", "Live review exercise", "Review this: camera switching in the web app",
      "Show the left snippet first and ask teams to find at least five problems in 3 minutes. Expected: cryptic names; hard-coded IP; no validation of the camera id; fire-and-forget fetch with no error handling; the UI claims success immediately (shows the new src even if the camera is offline); no state feedback; string concatenation into a URL. Then reveal the right version and discuss trade-offs: more code, but every state is explicit and failures are visible to the pilot.");
    code(s, "// switch cam\nfunction sw(c) {\n  fetch('/cam?id=' + c);\n  document.getElementById('v').src =\n    'http://192.168.2.2:8080/' + c;\n  document.getElementById('lbl')\n    .innerText = 'CAM ' + c + ' OK';\n}", 0.6, 1.95, 5.0, 3.55, { fontSize: 14, line: HEX.rose });
    pill(s, "BEFORE", 0.6, 1.5, 1.3, col.rose);
    code(s, "async function switchPrimaryCamera(cameraId) {\n  if (!cameraRegistry.has(cameraId)) {\n    throw new RangeError(`Unknown camera: ${cameraId}`);\n  }\n  ui.setCameraState(cameraId, CameraState.CONNECTING);\n  try {\n    await streamManager.makePrimary(cameraId,\n      { timeoutMs: SWITCH_TIMEOUT_MS });\n    ui.setCameraState(cameraId, CameraState.LIVE);\n  } catch (error) {\n    ui.setCameraState(cameraId, CameraState.LOST,\n                      error.message);\n    log.warn('camera switch failed', { cameraId, error });\n  }\n}", 5.9, 1.95, 6.8, 3.55, { fontSize: 11.5, line: HEX.teal });
    pill(s, "AFTER", 5.9, 1.5, 1.2, col.teal);
    const f = ["Names say what they do", "No hard-coded IP: configuration", "Input validated", "Every state is explicit", "Failure is visible to the pilot", "Nothing claims success before it happens"];
    f.forEach((t, i) => { const x = 0.6 + (i % 3) * 4.1, y = 5.75 + Math.floor(i / 3) * 0.48; text(s, "✔  " + t, { x, y, w: 3.95, h: 0.42, fontSize: 14, color: col.teal }); });
  }
  // ---------------------------------------------------------------- Git
  {
    const s = content("Engineering practice", "Version control", "A Git workflow that fits a student team",
      "Recommend trunk-based development with short-lived feature branches: main is always runnable on the ROV; every change goes through a PR with one reviewer; branches live < 1 week to avoid merge hell. Commit messages: imperative, explain why (Conventional Commits prefixes are optional but handy). Tag releases before every pool test and competition (v0.4-pool-2026-03-14) so you can always go back to 'the version that worked'. Merge conflicts: pull main often; small PRs make conflicts small.");
    const y0 = 2.6;
    s.addShape(pres.shapes.LINE, { x: 0.8, y: y0, w: 11.7, h: 0, line: { color: HEX.cyan, width: 3 }, objectName: "main-line" });
    text(s, "main — always runnable on the ROV", { x: 0.8, y: y0 - 0.62, w: 6, h: 0.35, fontSize: 13, bold: true, color: col.cyan });
    [1.2, 3.0, 4.6, 6.3, 8.1, 9.8, 11.6].forEach((x, i) => s.addShape(pres.shapes.OVAL, { x: x - 0.11, y: y0 - 0.11, w: 0.22, h: 0.22, fill: { color: HEX.cyan }, line: { color: HEX.bg, width: 1 }, objectName: `c-${i}` }));
    const br = [[1.2, 3.0, "feature/camera-switch", col.teal], [4.6, 6.3, "fix/reconnect-timeout", col.amber], [8.1, 9.8, "feature/substreams", col.violet]];
    br.forEach(([a, b, n, c], i) => { const yb = y0 + 0.9; arrow(s, a, y0, a + 0.4, yb, c, { noHead: true }); s.addShape(pres.shapes.LINE, { x: a + 0.4, y: yb, w: b - a - 0.8, h: 0, line: { color: c, width: 2 }, objectName: `br-${i}` }); arrow(s, b - 0.4, yb, b, y0 + 0.1, c);
      text(s, n, { x: a + 0.2, y: yb + 0.1, w: 2.6, h: 0.35, fontSize: 12, color: c, fontFace: "Courier New" }); });
    pill(s, "v0.4-pool-test", 6.0, y0 - 0.62, 1.8, col.amber); pill(s, "v1.0-competition", 10.9, y0 - 0.62, 1.8, col.rose);
    const rules = [["Short branches", "≤ 1 week; pull main often"], ["Pull request + 1 review", "nothing lands on main unreviewed"], ["Meaningful commits", "“fix: reconnect after USB reset (#42)”"], ["Tag before every pool test", "you can always return to what worked"]];
    rules.forEach(([a, b], i) => { const x = 0.6 + i * 3.05; box(s, x, 4.3, 2.85, 1.95, { fill: col.card });
      text(s, a, { x: x + 0.2, y: 4.45, w: 2.5, h: 0.65, fontSize: 15, bold: true }); text(s, b, { x: x + 0.2, y: 5.15, w: 2.5, h: 1.0, fontSize: 13, color: col.muted }); });
  }
  await require("./deck_part_new").githubWorkflow(ctx);
  // ---------------------------------------------------------------- Kanban
  {
    const s = content("Engineering practice", "Organising the work", "One board, five columns, weekly rhythm",
      "Use GitHub Projects, Trello, Jira — the tool doesn't matter. Five columns. Limit work in progress (e.g. max 2 cards per person in 'In progress'). Card types: story, task, bug, tech debt — tag them. Weekly rhythm: 30-min planning at the start of the week (pick from backlog, check DoR), 10-min async daily/bi-daily update ('done / next / blocked'), 30-min review + retrospective at the end (what went well, what didn't, one improvement). Milestones = pool tests and the competition.");
    const colsK = [["Backlog", [["Story", "Record primary camera at full quality"], ["Debt", "Replace hard-coded IPs"], ["Story", "Telemetry HUD on video"]]], ["Ready", [["Story", "Substream for aux cameras"], ["Task", "Measure tether with iperf3"]]], ["In progress  (WIP ≤ 2/person)", [["Story", "Camera switch ≤ 1 s"], ["Bug", "Cam 3 fails to start on USB hub"]]], ["Review", [["Task", "GStreamer pipeline: zerolatency"]]], ["Done", [["Task", "Diagnostic checklist filled"], ["Bug", "Wrong GOP after reboot"]]]];
    const tagCol = { Story: col.cyan, Task: col.blue, Bug: col.rose, Debt: col.amber };
    colsK.forEach(([h, cards], i) => { const x = 0.6 + i * 2.45; box(s, x, 1.75, 2.3, 4.85, { fill: col.card });
      text(s, h, { x: x + 0.15, y: 1.85, w: 2.0, h: 0.6, fontSize: 13, bold: true });
      cards.forEach(([t, d], j) => { const y = 2.55 + j * 1.3; box(s, x + 0.12, y, 2.06, 1.15, { fill: HEX.cardHi });
        pill(s, t, x + 0.22, y + 0.1, 0.8, tagCol[t], { h: 0.28, fontSize: 10 }); text(s, d, { x: x + 0.22, y: y + 0.45, w: 1.86, h: 0.65, fontSize: 12 }); }); });
    text(s, "Weekly: Mon planning 30 min · async “done / next / blocked” updates · Fri review + retro 30 min", { x: 0.6, y: 6.7, w: 12.1, h: 0.35, fontSize: 13, color: col.amber });
  }
  // ---------------------------------------------------------------- Team & metrics
  {
    const s = content("Engineering practice", "Engineering mindset", "Measure outcomes, not activity",
      "Talk through the mindset items with short examples: write down decisions (a one-paragraph decision log: context, options, decision, why); raise blockers the day you hit them; agree interfaces between hardware and software early (connector pinout, message formats, power budget); failed experiments are data — log them. Then metrics: use ones that reflect outcomes. Lines of code and commit counts reward the wrong behaviour.");
    const mind = ["Work toward measurable objectives", "Break big problems into testable pieces", "Write down decisions (decision log)", "Raise blockers early — the same day", "Integrate hardware + software continuously", "Treat failed experiments as data", "Disagree with evidence, decide, move on"];
    box(s, 0.6, 1.75, 5.9, 4.85, { fill: col.card });
    text(s, "Habits", { x: 0.85, y: 1.88, w: 5.4, h: 0.4, fontSize: 17, bold: true, color: col.cyan });
    bullets(s, mind, 0.85, 2.45, 5.4, 4.1, { fontSize: 17, gap: 12 });
    box(s, 6.8, 1.75, 2.85, 4.85, { fill: col.card, line: HEX.teal });
    text(s, "Useful metrics", { x: 7.0, y: 1.88, w: 2.5, h: 0.4, fontSize: 16, bold: true, color: col.teal });
    bullets(s, ["Requirements met (measured)", "Test pass rate", "Defects found vs fixed", "Features done (DoD)", "Build / main runnable", "Latency, bandwidth vs targets"], 7.0, 2.4, 2.5, 4.1, { fontSize: 14, gap: 6 });
    box(s, 9.85, 1.75, 2.85, 4.85, { fill: col.card, line: HEX.rose });
    text(s, "Vanity metrics", { x: 10.05, y: 1.88, w: 2.5, h: 0.4, fontSize: 16, bold: true, color: col.rose });
    bullets(s, ["Lines of code", "Number of commits", "Hours spent", "Number of features started", "Slides in the presentation"], 10.05, 2.4, 2.5, 4.1, { fontSize: 14, gap: 6 });
  }

  // ================================================================ SECTION 6 UX
  section("UX", "06", "Designing software around the pilot", "UX and UI engineering for ROV control", D.img.section3,
    "Transition: we've made the system faster and more reliable. Now: is it usable by a human under pressure? The central message of this section is on the next slide.");
  // ---------------------------------------------------------------- Central message
  {
    const s = content("UX", "The central message", "Great software lets the pilot act with confidence",
      "Read the quote slowly. Then the list: what the pilot must do simultaneously. Ask a pilot in the room to describe their worst moment on mission day — usually it's a UX failure (didn't notice a camera froze, pressed the wrong control, couldn't find the depth). A beautiful UI is not necessarily usable: aesthetic choices (thin fonts, low-contrast dark-on-dark, animated decorations) can actively hurt under pressure.");
    box(s, 0.6, 1.75, 12.1, 1.35, { fill: col.card });
    text(s, "“An excellent engineering system is not just one that works technically. It is one that allows its operator to use it effectively, confidently, and safely.”", { x: 0.95, y: 1.85, w: 11.4, h: 1.15, fontSize: 18, italic: true, valign: "middle" });
    const tasks = [[tb.TbSubmarine, "Understand the ROV's situation"], [fi.FiGrid, "Monitor several camera feeds"], [fi.FiNavigation, "Control movement & orientation"], [tb.TbHandGrab, "Operate the manipulator"], [fi.FiActivity, "Watch telemetry & sensors"], [fi.FiZap, "React to the unexpected — fast"]];
    for (let i = 0; i < 6; i++) { const x = 0.6 + (i % 3) * 4.1, y = 3.45 + Math.floor(i / 3) * 1.15; box(s, x, y, 3.85, 0.98, { fill: col.card });
      await iconCircle(s, tasks[i][0], x + 0.2, y + 0.2, 0.58); text(s, tasks[i][1], { x: x + 0.95, y, w: 2.8, h: 0.98, fontSize: 15, valign: "middle" }); }
    text(s, "…all at the same time, under time pressure, with limited visibility. Attractive ≠ usable.", { x: 0.6, y: 5.95, w: 12.1, h: 0.45, fontSize: 15, color: col.amber, bold: true });
  }
  // ---------------------------------------------------------------- Vocabulary
  {
    const s = content("UX", "Vocabulary", "UX, UI, HCI, human factors — and two key ideas",
      "UI is what's on the screen; UX is the whole experience of using it to get a job done; HCI is the research field; human factors engineering applies knowledge of human abilities and limits to system design (aviation, nuclear, subsea). Cognitive load: working memory is small — every extra thing to remember or search for costs attention. Situational awareness (Endsley): perceive → comprehend → project. Good ROV UIs support all three levels: show the data, show what it means (e.g. 'depth 2.3 m — 0.2 m above target'), show trends.");
    const defs = [["UI", "the screens, controls and visuals"], ["UX", "the whole experience of using it to get a job done"], ["HCI", "the discipline that studies people + computers"], ["Human factors", "designing for human abilities and limits"], ["Accessibility", "usable by people with different abilities, in different conditions"]];
    defs.forEach(([a, b], i) => { const y = 1.75 + i * 0.97; box(s, 0.6, y, 6.0, 0.83, { fill: col.card });
      text(s, a, { x: 0.85, y, w: 1.9, h: 0.83, fontSize: 16, bold: true, color: col.cyan, valign: "middle" }); text(s, b, { x: 2.75, y, w: 3.75, h: 0.83, fontSize: 14, color: col.muted, valign: "middle" }); });
    await card(s, 6.9, 1.75, 5.8, 2.3, { icon: fi.FiLayers, title: "Cognitive load", body: "Working memory is small. Every extra thing to remember, search for or interpret steals attention from driving.", bodySize: 14 });
    await card(s, 6.9, 4.25, 5.8, 2.3, { icon: fi.FiEye, title: "Situational awareness", body: "Perceive the data → comprehend what it means → project what happens next. The UI should support all three.", bodySize: 14, iconColor: HEX.teal, iconFill: col.teal });
  }
  // ---------------------------------------------------------------- Persona & journey
  {
    const s = content("UX", "Understand the pilot first", "Persona and user journey",
      "A persona is a realistic composite of your users, based on observation — not a fantasy. Build yours by interviewing and watching your actual pilots. The journey maps a mission run step by step, with what the pilot does, needs, and where pain points occur (red). Pain points become requirements: 'camera froze without me noticing' → 'a stale camera must be visibly marked within 1 s'. Full persona and journey are in the UX Pack.");
    box(s, 0.6, 1.75, 4.2, 4.85, { fill: col.card });
    await iconCircle(s, fi.FiUser, 0.85, 1.95, 0.8);
    text(s, "Mariam, 21 · pilot", { x: 1.8, y: 2.0, w: 2.9, h: 0.4, fontSize: 17, bold: true });
    text(s, "3rd-year mechatronics · 2 seasons", { x: 1.8, y: 2.4, w: 2.9, h: 0.35, fontSize: 12, color: col.muted });
    bullets(s, [{ text: "Goals", bold: true }, { text: "Finish mission tasks fast, without damaging props", sub: true }, { text: "Frustrations", bold: true }, { text: "Doesn't notice a frozen feed", sub: true }, { text: "Hunts for depth/heading", sub: true }, { text: "Unclear if a command was executed", sub: true }, { text: "Context", bold: true }, { text: "Gamepad in both hands; glances only", sub: true }], 0.85, 3.0, 3.75, 3.5, { fontSize: 15, gap: 2 });
    const steps = [["Pre-dive check", "all cams? link?", false], ["Launch & descend", "depth, heading", false], ["Navigate to task", "main cam, low latency", false], ["Grab object", "manipulator cam", true], ["Camera freezes", "didn't notice!", true], ["Surface & recover", "tether, status", false]];
    steps.forEach(([a, b, pain], i) => { const x = 5.1 + i * 1.28; const c = pain ? HEX.rose : HEX.cyan;
      s.addShape(pres.shapes.OVAL, { x: x + 0.39, y: 2.2, w: 0.42, h: 0.42, fill: { color: c, transparency: 60 }, line: { color: c, width: 1.5 }, objectName: `j-${i}` });
      if (i < steps.length - 1) s.addShape(pres.shapes.LINE, { x: x + 0.81, y: 2.41, w: 0.86, h: 0, line: { color: HEX.grid, width: 2 }, objectName: `jl-${i}` });
      text(s, a, { x, y: 2.75, w: 1.2, h: 0.75, fontSize: 12, bold: true, align: "center" }); text(s, b, { x, y: 3.5, w: 1.2, h: 0.6, fontSize: 11, color: pain ? col.rose : col.muted, align: "center" }); });
    text(s, "Mission journey (red = pain point)", { x: 5.1, y: 1.75, w: 7.6, h: 0.35, fontSize: 13, bold: true, color: col.muted });
    box(s, 5.1, 4.4, 7.6, 2.2, { fill: col.card, line: HEX.amber });
    text(s, "Pain point → requirement", { x: 5.35, y: 4.5, w: 7, h: 0.4, fontSize: 16, bold: true, color: col.amber });
    bullets(s, ["“Didn't notice the feed froze” → a stale feed is visibly marked within 1 s", "“Hunting for depth” → depth & heading overlaid on the primary video", "“Did the gripper close?” → show commanded vs confirmed state"], 5.35, 5.0, 7.2, 1.5, { fontSize: 14, gap: 4 });
  }
  // ---------------------------------------------------------------- Principles
  {
    const s = content("UX", "Seven principles", "UX principles for ROV pilot applications",
      "Spend a minute per principle with one concrete ROV example each (they are on the cards). The most important two for safety: feedback (requested vs confirmed state) and error prevention (dangerous actions deliberate). Consistency: never move a control between screens/modes — muscle memory is how pilots operate under stress. Customization: allow layouts per pilot, but keep a known-good default and an easy reset.");
    const p = [[fi.FiList, "Information hierarchy", "Critical first: primary video, connection, depth, heading, alarms."], [fi.FiLayers, "Low cognitive load", "Fewer clicks for common tasks; hide what isn't needed now."], [fi.FiEye, "Situational awareness", "State always visible: cameras, link, vehicle health."], [fi.FiMessageSquare, "Feedback", "Every action answers. Requested ≠ confirmed."], [fi.FiShield, "Error prevention", "Dangerous actions deliberate; easy recovery."], [fi.FiCopy, "Consistency", "Same colours, icons, words and positions everywhere."], [fi.FiSliders, "Customization", "Pilot layouts — with a known-good default and reset."]];
    for (let i = 0; i < 7; i++) { const x = 0.6 + (i % 4) * 3.05, y = 1.75 + Math.floor(i / 4) * 2.45;
      await card(s, x, y, 2.85, 2.25, { icon: p[i][0], title: p[i][1], body: p[i][2], titleSize: 14, bodySize: 13 }); }
    box(s, 9.75, 4.2, 2.95, 2.25, { fill: col.cyan, transparency: 80, line: HEX.cyan });
    text(s, "Test every principle with a pilot, not with the developer who built it.", { x: 9.95, y: 4.35, w: 2.55, h: 1.95, fontSize: 15, bold: true, valign: "middle" });
  }
  // ---------------------------------------------------------------- Before / after wireframe
  {
    const s = content("UX", "Before & after", "Pilot dashboard: from feature list to mission tool",
      "Left: a typical developer-built layout — eight equal tiles, telemetry as small text in a corner, buttons of equal weight everywhere (including dangerous ones), no indication of camera or link state. Right: the redesign — a large primary feed with a telemetry HUD overlaid; a thumbnail strip with explicit states (LIVE, DEGRADED, LOST); a connection bar always visible at the top; the mode and armed state prominent; emergency stop separated and distinct; secondary panels collapsed. Ask: 'Where does your eye go first on each?'");
    // BEFORE
    pill(s, "BEFORE", 0.6, 1.62, 1.3, col.rose);
    box(s, 0.6, 2.05, 6.0, 4.15, { fill: HEX.code, line: HEX.grid, r: 0.03 });
    for (let i = 0; i < 8; i++) { const x = 0.75 + (i % 4) * 1.18, y = 2.2 + Math.floor(i / 4) * 0.95; s.addShape(pres.shapes.RECTANGLE, { x, y, w: 1.1, h: 0.85, fill: { color: HEX.cardHi }, line: { color: HEX.grid, width: 0.75 }, objectName: `bt-${i}` });
      text(s, `cam${i}`, { x, y: y + 0.3, w: 1.1, h: 0.3, fontSize: 10, color: col.muted, align: "center" }); }
    text(s, "d:2.31 h:184 v:12.1 t:21.4 p:0.4 i:0.1 d:0.02 ...", { x: 0.75, y: 4.2, w: 4.7, h: 0.3, fontSize: 10, color: col.muted, fontFace: "Courier New" });
    ["ARM", "STOP", "REC", "PID", "LIGHT", "RESET", "CFG", "GRIP"].forEach((b, i) => { const x = 0.75 + (i % 4) * 1.18, y = 4.65 + Math.floor(i / 4) * 0.55; s.addShape(pres.shapes.RECTANGLE, { x, y, w: 1.1, h: 0.45, fill: { color: HEX.card }, line: { color: HEX.grid, width: 0.75 }, objectName: `bb-${i}` });
      text(s, b, { x, y, w: 1.1, h: 0.45, fontSize: 10, align: "center", valign: "middle" }); });
    text(s, "No camera state · no link state · STOP looks like LIGHT", { x: 0.6, y: 6.28, w: 6.0, h: 0.35, fontSize: 12, color: col.rose });
    // AFTER
    pill(s, "AFTER", 6.9, 1.62, 1.2, col.teal);
    box(s, 6.9, 2.05, 5.8, 4.15, { fill: HEX.code, line: HEX.grid, r: 0.03 });
    s.addShape(pres.shapes.RECTANGLE, { x: 7.0, y: 2.13, w: 5.6, h: 0.32, fill: { color: HEX.card }, line: { type: "none" }, objectName: "a-status" });
    text(s, "● LINK 94 Mb/s · 18 ms     MODE: DEPTH HOLD     ARMED", { x: 7.1, y: 2.13, w: 4.3, h: 0.32, fontSize: 10, color: col.teal, valign: "middle", bold: true });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 11.55, y: 2.15, w: 1.0, h: 0.28, rectRadius: 0.06, fill: { color: HEX.rose }, line: { type: "none" }, objectName: "a-estop" });
    text(s, "E-STOP", { x: 11.55, y: 2.15, w: 1.0, h: 0.28, fontSize: 10, bold: true, align: "center", valign: "middle" });
    s.addShape(pres.shapes.RECTANGLE, { x: 7.0, y: 2.55, w: 4.3, h: 2.65, fill: { color: HEX.cardHi }, line: { color: HEX.cyan, width: 1.25 }, objectName: "a-primary" });
    text(s, "PRIMARY · CAM 1 PILOT · LIVE", { x: 7.1, y: 2.6, w: 3, h: 0.3, fontSize: 10, bold: true, color: col.cyan });
    text(s, "DEPTH 2.31 m ▲0.2 to target     HDG 184°", { x: 7.1, y: 4.85, w: 4.1, h: 0.3, fontSize: 10, bold: true });
    s.addShape(pres.shapes.LINE, { x: 8.95, y: 3.75, w: 0.4, h: 0, line: { color: HEX.cyan, width: 1 }, objectName: "a-cross-h" }); s.addShape(pres.shapes.LINE, { x: 9.15, y: 3.55, w: 0, h: 0.4, line: { color: HEX.cyan, width: 1 }, objectName: "a-cross-v" });
    const states = [["CAM 2 MANIP", "LIVE", HEX.teal], ["CAM 3 REAR", "LIVE", HEX.teal], ["CAM 4", "DEGRADED", HEX.amber], ["CAM 5", "LOST", HEX.rose]];
    states.forEach(([n, st, c], i) => { const y = 2.55 + i * 0.67; s.addShape(pres.shapes.RECTANGLE, { x: 11.4, y, w: 1.2, h: 0.6, fill: { color: HEX.cardHi }, line: { color: c, width: 1.25 }, objectName: `a-th-${i}` });
      text(s, n, { x: 11.45, y: y + 0.03, w: 1.1, h: 0.25, fontSize: 9, bold: true }); text(s, st, { x: 11.45, y: y + 0.3, w: 1.1, h: 0.25, fontSize: 9, bold: true, color: c }); });
    s.addShape(pres.shapes.RECTANGLE, { x: 7.0, y: 5.3, w: 5.6, h: 0.8, fill: { color: HEX.card }, line: { type: "none" }, objectName: "a-bottom" });
    text(s, "GRIPPER  commanded: CLOSE · confirmed: CLOSED ✔     LIGHTS 60 %     REC ●", { x: 7.1, y: 5.3, w: 5.4, h: 0.8, fontSize: 10, valign: "middle" });
    text(s, "Clear hierarchy · explicit states · E-stop separated · commanded vs confirmed", { x: 6.9, y: 6.28, w: 5.8, h: 0.35, fontSize: 12, color: col.teal });
  }
  // ---------------------------------------------------------------- Layout strategies
  {
    const s = content("UX", "Layout strategies", "The right layout depends on the task, not on taste",
      "Four common strategies. Primary + previews suits navigation: one large feed, everything else small. Grid suits search/survey tasks where every view matters equally — but tiles get small and compete for attention. Picture-in-picture suits manipulation: the manipulator camera large, pilot camera inset so the pilot keeps orientation. Task workspaces: saved layouts per mission phase (navigate, manipulate, inspect), switched with one key, with consistent control positions. Don't assume every feature must be visible simultaneously.");
    const L = [["Primary + previews", "navigation", (x, y) => { s.addShape(pres.shapes.RECTANGLE, { x, y, w: 2.1, h: 1.3, fill: { color: HEX.cyan, transparency: 70 }, line: { color: HEX.cyan }, objectName: "l1a" }); for (let k = 0; k < 4; k++) s.addShape(pres.shapes.RECTANGLE, { x: x + 2.2, y: y + k * 0.33, w: 0.5, h: 0.28, fill: { color: HEX.cardHi }, line: { color: HEX.grid }, objectName: `l1b${k}` }); }],
      ["Grid", "search, survey", (x, y) => { for (let k = 0; k < 8; k++) s.addShape(pres.shapes.RECTANGLE, { x: x + (k % 4) * 0.68, y: y + Math.floor(k / 4) * 0.66, w: 0.62, h: 0.6, fill: { color: HEX.cardHi }, line: { color: HEX.grid }, objectName: `l2${k}` }); }],
      ["Picture-in-picture", "manipulation", (x, y) => { s.addShape(pres.shapes.RECTANGLE, { x, y, w: 2.7, h: 1.3, fill: { color: HEX.teal, transparency: 70 }, line: { color: HEX.teal }, objectName: "l3a" }); s.addShape(pres.shapes.RECTANGLE, { x: x + 1.95, y: y + 0.08, w: 0.68, h: 0.45, fill: { color: HEX.cyan, transparency: 50 }, line: { color: HEX.cyan }, objectName: "l3b" }); }],
      ["Task workspaces", "per mission phase", (x, y) => { ["NAV", "GRAB", "INSPECT"].forEach((t, k) => { s.addShape(pres.shapes.RECTANGLE, { x: x + k * 0.18, y: y + k * 0.2, w: 2.2, h: 0.9, fill: { color: HEX.cardHi }, line: { color: [HEX.cyan, HEX.teal, HEX.violet][k] }, objectName: `l4${k}` }); text(s, t, { x: x + k * 0.18 + 0.1, y: y + k * 0.2 + 0.05, w: 1.5, h: 0.28, fontSize: 10, bold: true }); }); }]];
    L.forEach(([a, b, draw], i) => { const x = 0.6 + i * 3.05; box(s, x, 1.75, 2.85, 3.6, { fill: col.card }); draw(x + 0.08, 2.0);
      text(s, a, { x: x + 0.2, y: 3.6, w: 2.5, h: 0.45, fontSize: 16, bold: true }); text(s, "Best for: " + b, { x: x + 0.2, y: 4.05, w: 2.5, h: 0.4, fontSize: 13, color: col.cyan }); });
    box(s, 0.6, 5.6, 12.1, 0.95, { fill: col.card });
    text(s, "Rule: keep controls in the same place in every layout. Pilots operate from muscle memory under stress.", { x: 0.85, y: 5.6, w: 11.6, h: 0.95, fontSize: 16, valign: "middle" });
  }
  // ---------------------------------------------------------------- UX & safety
  {
    const s = content("UX", "UX is a safety feature", "Never show success the system hasn't confirmed",
      "The key rule: the UI must never imply that an operation succeeded when the system has not confirmed it. Show 'commanded' and 'confirmed' separately, with an age/timestamp on telemetry. Dangerous actions (arming thrusters, opening the gripper with an object, changing PID gains in the water) require a deliberate action: hold-to-confirm, two-step, or a dedicated control. Define what happens on connection loss — and show it. Emergency stop: always reachable, never moved, visually distinct. Note: exact safety behaviour must be designed with the actual ROV control architecture and the competition's safety rules — I'm not prescribing an implementation.");
    const items = [[fi.FiCheckSquare, "Commanded vs confirmed", "Show both. Grey = requested, solid = acknowledged by the ROV."], [fi.FiClock, "Data age", "Telemetry older than ~1 s is marked stale, never shown as current."], [fi.FiLock, "Deliberate dangerous actions", "Arm, PID changes in water: hold-to-confirm or two-step."], [fi.FiWifiOff, "Connection-loss behaviour", "Defined safe state on the ROV; unmistakable banner topside."], [fi.FiOctagon, "Emergency stop", "Always reachable, never moves, distinct shape and colour."], [fi.FiToggleLeft, "Safe defaults", "Start disarmed, lights low, known-good layout."]];
    for (let i = 0; i < 6; i++) await card(s, 0.6 + (i % 3) * 4.1, 1.75 + Math.floor(i / 3) * 2.35, 3.85, 2.15, { icon: items[i][0], title: items[i][1], body: items[i][2], titleSize: 15, iconColor: i === 4 ? HEX.rose : HEX.cyan, iconFill: i === 4 ? col.rose : col.cyan });
    text(s, "Design the exact behaviour with your control architecture and the competition safety rules.", { x: 0.6, y: 6.5, w: 12.1, h: 0.35, fontSize: 13, italic: true, color: col.muted });
  }
  // ---------------------------------------------------------------- Usability testing
  {
    const s = content("UX", "Validate with users", "Usability testing: watch, don't ask",
      "Recruit a pilot who did not build the UI. Give tasks, not instructions: 'Switch to the rear camera, find out which camera has a problem, and return to the pilot camera — while holding depth.' Ask them to think aloud. Measure: completion (yes/no), time on task, errors, and afterwards a short questionnaire (SUS — System Usability Scale, 10 questions). Five users find most of the big problems (Nielsen). Heuristic evaluation is a cheap expert review against principles. A/B test only when you have two concrete alternatives and enough trials.");
    box(s, 0.6, 1.75, 6.2, 2.15, { fill: col.card, line: HEX.cyan });
    text(s, "Example task", { x: 0.85, y: 1.88, w: 5.7, h: 0.38, fontSize: 15, bold: true, color: col.cyan });
    text(s, "“While holding depth, switch to the rear camera, find which camera has a problem, then return to the pilot camera.”", { x: 0.85, y: 2.3, w: 5.75, h: 1.5, fontSize: 15, italic: true });
    const m = [["Task completion", "did they succeed?", col.teal], ["Time on task", "seconds, stopwatch", col.cyan], ["Errors", "wrong camera, wrong control", col.rose], ["Satisfaction", "SUS questionnaire (0–100)", col.violet]];
    m.forEach(([a, b, c], i) => { const x = 7.1 + (i % 2) * 2.85, y = 1.75 + Math.floor(i / 2) * 1.1; box(s, x, y, 2.7, 0.98, { fill: col.card });
      text(s, a, { x: x + 0.18, y: y + 0.08, w: 2.4, h: 0.4, fontSize: 15, bold: true, color: c }); text(s, b, { x: x + 0.18, y: y + 0.5, w: 2.4, h: 0.4, fontSize: 12, color: col.muted }); });
    const methods = [["Think-aloud", "pilot narrates what they look for and expect"], ["Heuristic evaluation", "experts check the UI against principles"], ["A/B test", "two concrete variants, same tasks, compare metrics"], ["5 users", "find most of the big problems — test early, test often"]];
    methods.forEach(([a, b], i) => { const y = 4.2 + i * 0.6; text(s, a, { x: 0.6, y, w: 2.6, h: 0.5, fontSize: 15, bold: true, color: col.cyan, valign: "middle" }); text(s, b, { x: 3.2, y, w: 9.5, h: 0.5, fontSize: 14, valign: "middle" }); });
  }
  // ---------------------------------------------------------------- UX in SDLC
  {
    const s = content("UX", "UX is not a styling phase", "UX inside the development lifecycle",
      "UX starts before code and continues after release. The loop: understand the user → needs → requirements → wireframes → prototype → test with pilots → refine → implement → validate usability → improve. The user story example shows how a UX need becomes acceptance criteria and a DoD that includes a usability test. Cheap prototyping: paper first, then Figma (free education plan) or Penpot (open source).");
    flow(s, [{ title: "Understand", sub: "observe pilots" }, { title: "Require", sub: "needs → stories" }, { title: "Wireframe", sub: "paper / Figma" }, { title: "Prototype", sub: "clickable" }, { title: "Test", sub: "with pilots" }, { title: "Build", sub: "implement" }, { title: "Validate", sub: "usability test" }], 0.6, 1.8, 12.1, 1.15, { titleSize: 13, subSize: 11, gap: 0.22 });
    box(s, 0.6, 3.25, 12.1, 0.8, { fill: col.card, line: HEX.cyan });
    rich(s, [{ text: "User story  ", bold: true, color: col.cyan, nl: false }, { text: "As an ROV pilot, I want to identify disconnected cameras immediately, so that I can react without wasting time." }], 0.85, 3.25, 11.6, 0.8, { valign: "middle", fontSize: 15 });
    box(s, 0.6, 4.25, 6.9, 2.35, { fill: col.card });
    text(s, "Acceptance criteria", { x: 0.85, y: 4.35, w: 6.4, h: 0.38, fontSize: 15, bold: true, color: col.teal });
    bullets(s, ["Disconnected cameras have an unmistakable status indicator", "A frozen frame is never displayed as if it were live", "Clear feedback when a camera disconnects; reconnection status shown", "The remaining camera feeds continue functioning"], 0.85, 4.8, 6.5, 1.75, { fontSize: 13, gap: 3 });
    box(s, 7.8, 4.25, 4.9, 2.35, { fill: col.card });
    text(s, "Definition of Done", { x: 8.05, y: 4.35, w: 4.4, h: 0.38, fontSize: 15, bold: true, color: col.amber });
    bullets(s, ["Implemented and reviewed", "Disconnect + reconnect tested", "Visual states reviewed", "Usability-tested with a pilot", "No regressions in other feeds"], 8.05, 4.8, 4.5, 1.75, { fontSize: 13, gap: 3 });
  }
  // ---------------------------------------------------------------- UX activity
  {
    const s = content("UX", "Activity 6 · 40 minutes", "Design the Perfect ROV Pilot Experience",
      "Same scenario for every team (in UX_Pilot_Experience_Pack.md). 20 minutes: paper wireframe (A3) or a quick Figma prototype. Then teams swap: another team's member acts as pilot and performs the scripted tasks using the prototype while the designers 'play computer' (swap paper overlays when the pilot acts). Observers time tasks and count errors. Score with the rubric; the pilot's feedback counts. Debrief: what surprised the designers?");
    flow(s, [{ title: "Brief", sub: "5 min · same scenario for all" }, { title: "Design", sub: "20 min · wireframe / prototype" }, { title: "Swap & test", sub: "10 min · another team pilots it" }, { title: "Score", sub: "5 min · rubric + pilot feedback" }], 0.6, 1.8, 7.3, 1.35, { titleSize: 14, subSize: 11, gap: 0.25 });
    box(s, 0.6, 3.45, 7.3, 3.15, { fill: col.card });
    text(s, "Pilot tasks (timed)", { x: 0.85, y: 3.58, w: 6.8, h: 0.38, fontSize: 15, bold: true, color: col.cyan });
    bullets(s, ["Make the rear camera primary, then return", "Find which camera has failed", "Read the current depth and heading", "Close the gripper and confirm it closed", "React to: “link lost” and “leak detected”"], 0.85, 4.05, 6.8, 2.5, { fontSize: 14, gap: 5 });
    table(s, [["Criterion", "Pts"], ["Task completion", "25"], ["Ease of use (time, clicks)", "15"], ["Information clarity", "15"], ["Unnecessary interactions (fewer = more)", "10"], ["Error prevention", "15"], ["Situational awareness", "10"], ["Pilot feedback", "10"]], 8.2, 1.8, 4.5, [3.6, 0.9], { fontSize: 13, rowH: 0.52 });
  }

  // ================================================================ SECTION 7 Close
  section("Close", "07", "The challenge", "Design the next-generation ROV video system", D.img.section1,
    "Transition: you now have the tools — measurement, compression, stream management, process, testing, UX. Time to put them together.");
  // ---------------------------------------------------------------- Final challenge
  {
    const s = content("Close", "Activity 5 + post-workshop challenge", "Design the next-generation ROV video system",
      "Brief the Architecture Challenge (20 minutes in the session, as a sketch) and the 6-week Boss level of the ROV experiments. Mission statement on screen. Emphasise: no architecture is prescribed — the first deliverable is the measured baseline; the final demo is judged against requirements with measurements. Point to the Boss level in docs/experiments/ROV_Experiments.md for requirements, acceptance criteria, DoD and demo criteria.");
    box(s, 0.6, 1.75, 12.1, 1.15, { fill: col.card, line: HEX.cyan });
    text(s, "“Optimize the ROV video system to provide the best possible operator experience under limited network bandwidth and processing resources.”", { x: 0.9, y: 1.8, w: 11.5, h: 1.05, fontSize: 17, italic: true, valign: "middle" });
    const ph = [["Week 1", "Baseline", "Fill the diagnostic checklist; measure bandwidth, latency, CPU"], ["Weeks 2–3", "Design", "Compare ≥ 2 architectures with numbers; write the decision log"], ["Weeks 3–5", "Build & test", "Implement, test failure cases, usability-test with pilots"], ["Week 6", "Demonstrate", "Before/after measurements against the requirements"]];
    ph.forEach(([w, a, b], i) => { const x = 0.6 + i * 3.05; box(s, x, 3.15, 2.85, 2.6, { fill: col.card });
      pill(s, w, x + 0.2, 3.32, 1.35, col.teal); text(s, a, { x: x + 0.2, y: 3.8, w: 2.5, h: 0.45, fontSize: 17, bold: true }); text(s, b, { x: x + 0.2, y: 4.3, w: 2.5, h: 1.35, fontSize: 15, color: col.muted }); });
    text(s, "Judged on: requirements met (measured) · quality of evidence · failure handling · pilot usability · documentation", { x: 0.6, y: 6.0, w: 12.1, h: 0.5, fontSize: 15, color: col.amber, bold: true });
  }
  // ---------------------------------------------------------------- Takeaways
  {
    const s = content("Close", "Take it back to the ROV", "Seven things to remember",
      "Read them as a checklist and ask the room to pick the one they will act on first. End with the mindset line from the opening slide.");
    const t = ["Find out what you actually have — then measure it", "Compression beats resolution cuts", "Plan on peaks, keep ≥ 30 % headroom", "Not every camera needs full quality all the time", "Latency is designed: zerolatency, short GOP, small buffers", "Know your silicon: Nano encodes in HW, Pi 5 doesn't", "Test how it fails — and design the UI around the pilot"];
    t.forEach((x, i) => { const y = 1.75 + i * 0.68; box(s, 0.6, y, 12.1, 0.58, { fill: col.card });
      text(s, String(i + 1), { x: 0.8, y, w: 0.5, h: 0.58, fontSize: 18, bold: true, color: col.cyan, valign: "middle" }); text(s, x, { x: 1.35, y, w: 11.2, h: 0.58, fontSize: 17, valign: "middle" }); });
    text(s, "“How would we measure that?” before “How do we fix that?”", { x: 0.6, y: 6.6, w: 12.1, h: 0.4, fontSize: 15, italic: true, color: col.amber });
  }
  // ---------------------------------------------------------------- Resources / thanks
  {
    const s = pres.addSlide({ masterName: "MIA_TITLE", sectionTitle: "Close" });
    s.addImage({ path: D.img.hero2, x: 0, y: 0, w: 13.333, h: 7.5, objectName: "end-image", altText: "Synthetic underwater frame" });
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 13.333, h: 7.5, fill: { color: col.bg, transparency: 18 }, line: { type: "none" }, objectName: "end-overlay" });
    s.addText("Thank you — questions?", { placeholder: "title" });
    s.addText("Everything from today is in the workshop folder: notebook, cheat sheet, diagnostic checklist, testing competition, UX pack, references.", { placeholder: "body" });
    const r = [["FFmpeg & GStreamer docs", "ffmpeg.org · gstreamer.freedesktop.org"], ["NVIDIA Jetson Linux — Accelerated GStreamer", "docs.nvidia.com/jetson"], ["Raspberry Pi 5 H.264 encoding white paper", "raspberrypi.com"], ["MATE ROV Competition", "materovcompetition.org"]];
    r.forEach(([a, b], i) => { text(s, a, { x: 0.8 + (i % 2) * 6.0, y: 5.2 + Math.floor(i / 2) * 0.75, w: 5.8, h: 0.35, fontSize: 14, bold: true }); text(s, b, { x: 0.8 + (i % 2) * 6.0, y: 5.53 + Math.floor(i / 2) * 0.75, w: 5.8, h: 0.35, fontSize: 12, color: col.cyan }); });
    s.addNotes("Close. Remind them of the homework / post-workshop challenge and where the materials are. Offer to review their baseline measurements in two weeks. Collect feedback: what was most useful, what was unclear.");
  }
};
