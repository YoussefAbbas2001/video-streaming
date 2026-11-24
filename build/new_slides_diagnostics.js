// Video-diagnostics slides (Nov 2026): 6 slides for the talk + the field-guide appendix (1 overview + 16 slides).
// Content comes from build/diagnostics_catalog.py (same source as docs/streaming/video-diagnostics.md):
//
//   python3 build/make_diagnostic_images.py     # pictures (once)
//   python3 build/diagnostics_catalog.py        # doc + out/diagnostics.json
//   node build/new_slides_diagnostics.js        # → out/new_slides_diagnostics.pptx (+ .json key → slide number)
//   python3 build/insert_slides.py …            # see build/README.md
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const { THEME, HEX, makeHelpers } = require("./deck_helpers");
const { writeTheme } = require("./write_theme");

const ROOT = path.join(__dirname, "..");
const OUT = path.join(ROOT, "out", "new_slides_diagnostics.pptx");
const D = JSON.parse(fs.readFileSync(path.join(ROOT, "out", "diagnostics.json"), "utf8"));
const IMG = (n) => path.join(ROOT, "docs", "streaming", "img", "diagnostics", `${n}.jpg`);
const byId = Object.fromEntries(D.items.map((c) => [c.id, c]));

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const H = makeHelpers(pres);
  const { col, text, rich, box, card, arrow, flow, table, code, pill } = H;
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
  const foot = (s, t) => text(s, t, { x: 0.6, y: 6.62, w: 12.1, h: 0.3, fontSize: 11, color: col.muted, italic: true });

  // ======================================================================= D1 · find the stage
  {
    const s = content("d_stage", "Diagnostics · where is the problem?", "A bad picture has one cause in one stage: find the stage",
      "The pilot only sees the result on the screen, but the cause can be in any of eight stages. The same symptom can come from different stages, and a healthy-looking number can hide a problem. " +
      "Examples on the slide: high latency with a perfect 30 fps (encoder hold-back or a queue that only grows); low fps with plenty of bandwidth (CPU, heat or USB); a frozen picture while the connection is up (stale frame); blur only when the camera moves (bitrate cap or long exposure); smooth video but late telemetry (video buffering); a delay that grows during the dive (a queue). " +
      "Rule: measure each stage separately. Otherwise a delay in the pilot laptop's render queue gets blamed on the tether, and the team changes the wrong thing. " +
      "Full guide with 45 symptoms and pictures: docs/streaming/video-diagnostics.md, and the Field guide appendix of this deck.");
    flow(s, [
      { title: "Camera", sub: "exposure, gain, fps" }, { title: "Capture", sub: "dropped frames, USB" }, { title: "Encoder", sub: "ms, frames held, bitrate" },
      { title: "Network", sub: "Mb/s, loss, jitter" }, { title: "Receiver", sub: "jitter buffer, reorder" }, { title: "Decoder", sub: "ms, errors, queue" },
      { title: "Renderer", sub: "pacing, frame age" }, { title: "Display", sub: "vsync, TV lag" }], 0.6, 1.7, 12.1, 1.15, { titleSize: 13, subSize: 10.5, gap: 0.2 });
    const traps = [
      ["High latency, perfect 30 fps", "fps says nothing about delay: encoder hold-back or a growing queue", col.rose],
      ["Low fps, plenty of bandwidth", "the network is fine: CPU, heat or USB", col.amber],
      ["Frozen picture, link still up", "a stale frame: show its age, not just fps", col.rose],
      ["Blur only when moving", "bitrate cap, or a long exposure in low light", col.amber],
      ["Smooth video, late telemetry", "or the reverse: the video waits in a buffer", col.cyan],
      ["Delay grows during the dive", "a queue that only grows: bound it, drop old frames", col.cyan]];
    traps.forEach(([t, b, c], i) => {
      const x = 0.6 + (i % 3) * 4.07, y = 3.15 + Math.floor(i / 3) * 1.6;
      box(s, x, y, 3.95, 1.42, { line: c });
      text(s, t, { x: x + 0.2, y: y + 0.15, w: 3.6, h: 0.4, fontSize: 15, bold: true, color: c });
      text(s, b, { x: x + 0.2, y: y + 0.6, w: 3.6, h: 0.75, fontSize: 13, color: col.muted });
    });
    foot(s, "Measure each stage separately, or a delay in the pilot laptop gets blamed on the tether.");
  }

  // ======================================================================= D2 · symptom matrix
  {
    const s = content("d_matrix", "Diagnostics · troubleshooting matrix", "Symptom → first suspect → what to inspect",
      "Use this table in the pool: start from what the pilot reports, check the first suspect, and inspect the listed numbers before changing anything. " +
      D.matrix.map((r) => `${r[0]}: suspect ${r[1]}; inspect ${r[2]}.`).join(" ") +
      " Each row points to a page of the Field guide appendix with a picture, the cause and the fix.");
    table(s, [["Symptom", "First suspect", "Inspect"], ...D.matrix.map((r) => [{ text: r[0], bold: true }, r[1], r[2]])],
      0.6, 1.65, 12.1, [3.55, 3.75, 4.8], { fontSize: 12, rowH: 0.32 });
  }

  // ======================================================================= D3 · metrics
  {
    const s = content("d_metrics", "Diagnostics · measure, don't guess", "What to measure at each stage, and where we get it",
      "Symptoms tell you that something is wrong; numbers tell you why. Nine categories cover the whole pipeline. " +
      D.metrics.map((m) => `${m[0]}: ${m[1]} (${m[2]}), from ${m[3]}.`).join(" ") +
      " Add one more number to the pilot GUI: frame age, the time since the frame on screen was captured. It catches stale frames that the fps counter hides. " +
      "Most of these already exist: the Encoding Lab measures encoder time, frames held, fps and bitrate; encoding_lab/tools/rtp_probe.py measures throughput, loss and jitter of a live RTP stream.");
    table(s, [["Category", "Metrics", "Unit", "Where we get it"], ...D.metrics.map((m) => [{ text: m[0], bold: true }, m[1], m[2], m[3]])],
      0.6, 1.65, 12.1, [1.6, 5.0, 1.55, 3.95], { fontSize: 12, rowH: 0.44 });
    foot(s, "Plus frame age (now − capture time of the frame on screen): it catches the stale frames that fps hides.");
  }

  // ======================================================================= D4 · latency measurement
  {
    const s = content("d_latency", "Diagnostics · latency", "Measure latency three ways; report the median and p95",
      "Glass-to-glass latency is display time minus capture time. It is the number the pilot feels, and it is the sum of every stage (the chart shows typical values, not a measurement). " +
      "Method 1, optical: point the camera at a millisecond clock on the pilot laptop, take a phone photo of the clock and the video of the clock together, subtract, repeat 10 times. It needs no clock synchronisation and is the ground truth. " +
      "Method 2, timestamp overlay: stamp the capture time into the frame or into metadata (RTP header extension, H.264 SEI) and compare with the receiver's clock; needs chrony or PTP so the clocks agree. " +
      "Method 3, stage timestamps: log a monotonic timestamp at capture, encoder output, network receive, decoder output and presentation. Inside one machine, monotonic clocks need no sync; between machines they do. " +
      "Always report the median and the 95th percentile, never one number, and correlate over time: latency rising with queue depth means buffering; latency steady while capture fps falls means camera or CPU.");
    s.addImage({ path: IMG("glass-to-glass"), x: 0.6, y: 1.7, w: 6.2, h: 3.49, objectName: "g2g-chart" });
    text(s, "L(glass-to-glass) = T(display) − T(capture)", { x: 0.6, y: 5.35, w: 6.2, h: 0.4, fontSize: 16, bold: true, color: col.cyan, fontFace: "Courier New" });
    text(s, "Correlate over time: latency ↑ with queue depth ↑ = buffering. Latency steady, capture fps ↓ = camera or CPU.", { x: 0.6, y: 5.85, w: 6.2, h: 0.7, fontSize: 13, color: col.muted });
    [["1 · Optical (ms clock)", "Camera films a ms clock; photograph clock + video together, 10 repeats. No clock sync. The truth.", col.teal],
     ["2 · Timestamp overlay", "Capture time in the frame or RTP/SEI metadata; needs chrony or PTP between ROV and topside.", col.cyan],
     ["3 · Stage timestamps", "Monotonic time at capture, encode, receive, decode, present: shows which stage grew.", col.amber]].forEach(([t, b, c], i) => {
      const y = 1.7 + i * 1.62;
      box(s, 7.05, y, 5.65, 1.45, { line: c });
      text(s, t, { x: 7.25, y: y + 0.13, w: 5.3, h: 0.4, fontSize: 16, bold: true, color: c });
      text(s, b, { x: 7.25, y: y + 0.6, w: 5.3, h: 0.8, fontSize: 13, color: col.muted });
    });
  }

  // ======================================================================= D5 · first 15
  {
    const s = content("d_first15", "Diagnostics · build order", "The first 15 diagnostics, and which ones we already have",
      "If the team builds only fifteen diagnostics, build these. The coloured tag says where each one comes from today: LAB means the Encoding Lab already measures it (Live camera shows encoder ms, frames held, fps, dropped frames; Encode shows peak bitrate); PROBE means encoding_lab/tools/rtp_probe.py measures it on a live RTP stream (throughput, loss, jitter); MANUAL means a procedure (the ms-clock photo); GUI means it still has to be built into the pilot GUI (decode and display timing, presentation intervals, queue depth and frame age). " +
      "Nine of the fifteen are available now. The remaining six are all receiver-side timers in the GUI, a good first task for the software sub-team.");
    const tag = { lab: ["LAB", col.teal], probe: ["PROBE", col.cyan], manual: ["MANUAL", col.amber], todo: ["GUI", col.rose] };
    D.first15.forEach(([name, where, st], i) => {
      const c = Math.floor(i / 8), r = i % 8, x = 0.6 + c * 6.15, y = 1.7 + r * 0.6;
      box(s, x, y, 5.95, 0.5, {});
      text(s, `${i + 1}`, { x: x + 0.12, y, w: 0.4, h: 0.5, fontSize: 14, bold: true, color: col.muted, valign: "middle" });
      text(s, name, { x: x + 0.55, y, w: 2.85, h: 0.5, fontSize: 13.5, bold: true, valign: "middle" });
      text(s, where, { x: x + 3.35, y, w: 1.65, h: 0.5, fontSize: 10.5, color: col.muted, valign: "middle" });
      pill(s, tag[st][0], x + 5.0, y + 0.1, 0.85, tag[st][1], { solid: true, h: 0.3, fontSize: 10 });
    });
    foot(s, "9 of 15 exist today. The 6 GUI ones are receiver-side timers: a good first task for the software sub-team.");
  }

  // ======================================================================= D6 · dashboard
  {
    const s = content("d_dashboard", "Diagnostics · the pilot's screen", "Four numbers and six lights, not forty metrics",
      "Do not put forty numbers in front of the pilot. Show four: glass-to-glass latency (median and p95), video bitrate (average and peak), display fps (what is actually presented) and packet loss. Below them, one health light per pipeline stage: green when its numbers are inside budget, amber when close, red when out, grey when not measured. " +
      "Everything else (queue depths, decode times, temperatures) goes in a tooltip or a debug view for the software team. " +
      "And correlate over time instead of reading numbers in isolation: if latency rises at the same time as queue depth, you have evidence of buffering; if latency is steady but capture fps falls, look at the camera or the CPU, not the network. " +
      "The numbers on this mock-up are an example layout, not measurements.");
    [["Glass-to-glass", "142 ms", "p95 188 ms · target 150", col.amber], ["Video bitrate", "2.4 Mb/s", "peak 6.1 · budget 3.0", col.teal],
     ["Display fps", "30.0", "pacing ±2 ms", col.teal], ["Packet loss", "0.02 %", "last 60 s · jitter 3 ms", col.teal]].forEach(([l, v, sub, c], i) => {
      const x = 0.6 + i * 3.05;
      box(s, x, 1.7, 2.9, 1.7, { line: c });
      text(s, l.toUpperCase(), { x: x + 0.2, y: 1.82, w: 2.5, h: 0.3, fontSize: 11, bold: true, color: col.muted, charSpacing: 1 });
      text(s, v, { x: x + 0.2, y: 2.12, w: 2.5, h: 0.75, fontSize: 34, bold: true, color: c, fontFace: "Arial" });
      text(s, sub, { x: x + 0.2, y: 2.9, w: 2.6, h: 0.4, fontSize: 11.5, color: col.muted });
    });
    text(s, "PIPELINE HEALTH", { x: 0.6, y: 3.65, w: 6, h: 0.3, fontSize: 11, bold: true, color: col.muted, charSpacing: 1 });
    [["Camera", col.teal], ["Encoder", col.teal], ["Network", col.teal], ["Receiver", col.amber], ["Decoder", col.teal], ["Renderer", col.muted]].forEach(([n, c], i) => {
      const x = 0.6 + i * 2.03;
      box(s, x, 4.0, 1.9, 0.62, {});
      s.addShape(pres.shapes.OVAL, { x: x + 0.15, y: 4.16, w: 0.3, h: 0.3, fill: { color: c }, line: { type: "none" }, objectName: `light-${i}` });
      text(s, n, { x: x + 0.55, y: 4.0, w: 1.3, h: 0.62, fontSize: 13.5, bold: true, valign: "middle" });
    });
    text(s, "green = in budget · amber = close · red = out · grey = not measured", { x: 0.6, y: 4.68, w: 12.1, h: 0.3, fontSize: 11, color: col.muted, italic: true });
    [["Latency ↑ and queue depth ↑ together", "buffering: bound the queue, drop old frames", col.rose],
     ["Latency steady, capture fps ↓", "camera or CPU, not the network", col.amber],
     ["Loss ↑ when thrusters run", "electrical noise on the tether or powerline", col.cyan]].forEach(([t, b, c], i) => {
      const x = 0.6 + i * 4.07;
      box(s, x, 5.1, 3.95, 1.4, { line: c });
      text(s, t, { x: x + 0.2, y: 5.2, w: 3.6, h: 0.55, fontSize: 14, bold: true, color: c });
      text(s, b, { x: x + 0.2, y: 5.78, w: 3.6, h: 0.6, fontSize: 12.5, color: col.muted });
    });
  }

  // ======================================================================= A0 · field guide overview
  const groupPages = {
    timing: [["g2g", "drift", "jitter", "Late, later and uneven"], ["stale", "pacing", "burst", "Stuck, jerky and bursty"], ["hold", "dlag", null, "Delay we add ourselves"]],
    compression: [["blocking", "ringing", "blur", "Too few bits: blocks, halos, blur"], ["pixelation", "banding", "iframe", "Coarse, banded and bursty"]],
    network: [["loss", "corrupt", "buffering", "Lost and damaged bits"], ["dropout", "linkspeed", "mtu", "Links that fail quietly"]],
    motion: [["rolling", "ghost", "mblur", "Faster than the sensor"], ["judder", "combing", "strobe", "Faster than the frame rate"]],
    camera: [["haze", "backscatter", "noise", "Water and light"], ["focus", "exposure", "wb", "Lens and camera settings"], ["condensation", "pwm", "flicker", "It looks like the network, but it is the camera"]],
    display: [["tearing", "black", "aspect", "Showing the frame goes wrong"], ["reswitch", "range", "desync", "Wrong size, wrong colours, wrong time"]],
    system: [["thermal", "usb", null, "The ROV computer runs out"], ["cpu", "clock", null, "CPU and clocks"]],
  };
  const tips = {
    timing_2: ["Measure it", "Encoding Lab → Live camera shows encoder ms and frames held; the ms-clock photo gives glass-to-glass. Report median and p95."],
    system_0: ["Soak test before every competition", "30 minutes, enclosure closed, all cameras streaming, GUI running: log temperature, throttling, fps and latency together."],
    system_1: ["Log every pool test", "fps, latency, loss, bitrate, CPU and temperature with timestamps, one file per run: compare runs, not memories."],
  };
  {
    const thumb = { timing: "stale-frame", compression: "blocking", network: "packet-loss", motion: "rolling-shutter", camera: "backscatter", display: "aspect-ratio", system: "thermal" };
    const s = content("a_overview", "Appendix · field guide", "45 things that go wrong with ROV video",
      "This appendix is a reference for the pool, not part of the talk. Every page shows up to three symptoms with a picture, the cause, what it means on our ROV and the fix; the speaker notes add what you see and how to confirm it. " +
      "Groups: timing and latency, compression, network and transport, motion, camera and optics, display and sync, and the ROV computer itself. " +
      "The pictures were made from the Encoding Lab's synthetic clip: compression artifacts are real encodes at bad settings, packet loss and decoder corruption are real damaged streams, camera and display effects are simulated from how they happen, timing problems are charts. " +
      "The same content, with a symptom → cause table, is in docs/streaming/video-diagnostics.md.");
    D.groups.forEach(([g, title, intro], i) => {
      const n = D.items.filter((c) => c.group === g).length;
      const x = 0.6 + (i % 4) * 3.05, y = 1.65 + Math.floor(i / 4) * 2.5;
      box(s, x, y, 2.9, 2.35, {});
      s.addImage({ path: IMG(thumb[g]), x: x + 0.1, y: y + 0.1, w: 2.7, h: 1.25, sizing: { type: "cover", w: 2.7, h: 1.25 }, objectName: `thumb-${g}` });
      text(s, `${title} · ${n}`, { x: x + 0.15, y: y + 1.4, w: 2.6, h: 0.35, fontSize: 13.5, bold: true, color: col.cyan });
      text(s, intro, { x: x + 0.15, y: y + 1.75, w: 2.65, h: 0.58, fontSize: 10.5, color: col.muted });
    });
    box(s, 0.6 + 3 * 3.05, 1.65 + 2.5, 2.9, 2.35, { line: col.amber });
    text(s, "Use it with the troubleshooting matrix", { x: 9.9, y: 4.3, w: 2.6, h: 0.65, fontSize: 14, bold: true, color: col.amber });
    text(s, "Start from the symptom table in the Diagnostics section, then open the page for the suspect. Full text: docs/streaming/video-diagnostics.md", { x: 9.9, y: 4.95, w: 2.6, h: 1.4, fontSize: 11.5, color: col.muted });
  }

  // ======================================================================= field-guide pages
  const gname = Object.fromEntries(D.groups.map((g) => [g[0], g[1]]));
  for (const [g, pages] of Object.entries(groupPages)) {
    for (const [pi, [a, b, c, title]] of pages.entries()) {
      const ids = [a, b, c].filter(Boolean);
      const notes = ids.map((id) => { const e = byId[id];
        return `${e.name}. What you see: ${e.see} Why: ${e.why} On our ROV: ${e.rov} Confirm: ${e.check} Fix: ${e.fix}`; }).join("\n\n");
      const s = content(`fg_${g}_${pi}`, `Field guide · ${gname[g]} (${pi + 1}/${pages.length})`, title, notes);
      ids.forEach((id, k) => {
        const e = byId[id], x = 0.6 + k * 4.075, y = 1.62, w = 3.95;
        box(s, x, y, w, 4.98, {});
        if (e.img) s.addImage({ path: IMG(e.img), x: x + 0.1, y: y + 0.1, w: w - 0.2, h: (w - 0.2) * 9 / 16, objectName: `img-${id}` });
        else code(s, e.code, x + 0.1, y + 0.1, w - 0.2, (w - 0.2) * 9 / 16, { fontSize: 10 });
        const ty = y + 0.1 + (w - 0.2) * 9 / 16 + 0.08;
        text(s, e.name, { x: x + 0.15, y: ty, w: w - 0.3, h: 0.36, fontSize: 15, bold: true, color: col.cyan });
        rich(s, [
          { text: "Why  ", bold: true, color: col.amber, fontSize: 12, breakLine: false }, { text: e.why, fontSize: 12, color: col.text, paraSpaceAfter: 4 },
          { text: "On our ROV  ", bold: true, color: col.rose, fontSize: 12, breakLine: false }, { text: e.rov, fontSize: 12, color: col.text, paraSpaceAfter: 4 },
          { text: "Fix  ", bold: true, color: col.teal, fontSize: 12, breakLine: false }, { text: e.fix, fontSize: 12, color: col.text }],
          x + 0.15, ty + 0.4, w - 0.3, y + 4.98 - (ty + 0.4) - 0.08, { fit: "none" });
      });
      const tip = tips[`${g}_${pi}`];
      if (ids.length < 3 && tip) {
        const x = 0.6 + ids.length * 4.075;
        box(s, x, 1.62, 3.95, 4.98, { line: col.amber });
        text(s, tip[0], { x: x + 0.25, y: 1.85, w: 3.45, h: 0.8, fontSize: 18, bold: true, color: col.amber });
        text(s, tip[1], { x: x + 0.25, y: 2.75, w: 3.45, h: 3.5, fontSize: 14, color: col.muted });
      }
    }
  }

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  await pres.writeFile({ fileName: OUT });
  await writeTheme(OUT, THEME);
  fs.writeFileSync(OUT.replace(/\.pptx$/, ".json"), JSON.stringify(slides, null, 1));
  console.log("wrote", OUT, Object.keys(slides).length, "slides");
})();
