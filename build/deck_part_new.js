// Slides added for the recorded video series and the SDLC live session (November 2026).
// Each export draws one slide; build order is decided by the hooks in deck_part_a.js / deck_part_b.js.
const fi = require("react-icons/fi");
const tb = require("react-icons/tb");
const { HEX } = require("./deck_helpers");

const SRC_NOTE = "Sources are listed in docs/streaming/codecs-and-ffmpeg.md and workshop/resources/References.md.";

// ---------------------------------------------------------------- Why streaming is underrated
exports.worldRunsOnCompression = async ({ H, content }) => {
  const { col, text, rich, box, stat, iconCircle } = H;
  const s = content("Opening", "Why streaming is underrated", "The world quietly runs on video compression",
    "Video is about two thirds of all internet traffic: Sandvine's 2023 Global Internet Phenomena Report put video at 65 % of all traffic in 2022, growing 24 % in one year. " +
    "Each codec generation needs roughly half the bits of the previous one for the same quality: HEVC (2013) about 50 % below H.264, VVC (2020) about 50 % below HEVC and about 75 % below H.264. " +
    "H.264's developers, the Joint Video Team of ITU-T and ISO/IEC, received two Technology & Engineering Emmy awards (2008 Primetime and 2009). " +
    "Point: nobody notices compression until it fails. Every video call, every stream, every ROV camera depends on it. " + SRC_NOTE);
  const stats = [
    ["65 %", "of all internet traffic in 2022 was video (Sandvine)", col.cyan],
    ["≈ 50 %", "fewer bits per codec generation: H.264 2003 → HEVC 2013 → VVC 2020", col.teal],
    ["2 Emmys", "for the H.264 standards team (2008, 2009). Engineers, not actors.", col.amber],
  ];
  stats.forEach(([v, l, c], i) => {
    box(s, 0.6 + i * 4.1, 1.8, 3.85, 2.55, { fill: col.card });
    stat(s, 0.85 + i * 4.1, 1.95, 3.4, v, l, c, { size: 46, labelSize: 14, lh: 0.9 });
  });
  box(s, 0.6, 4.6, 12.1, 1.15, { fill: HEX.cardHi });
  rich(s, [{ text: "“a jewel in the crown of international standards collaboration”", italic: true, fontSize: 20, color: col.text },
    { text: "Malcolm Johnson, ITU, accepting the 2008 Emmy for H.264", fontSize: 13, color: col.muted }], 0.9, 4.72, 11.5, 0.95);
  await iconCircle(s, fi.FiGlobe, 0.6, 6.0, 0.55);
  text(s, "Netflix, video calls, CCTV, drones and our eight ROV cameras all exist because someone made the bits smaller. Nobody notices it until it fails.",
    { x: 1.3, y: 5.98, w: 11.4, h: 0.65, fontSize: 15, color: col.muted, valign: "middle" });
};

// ---------------------------------------------------------------- Egypt cost example
exports.egyptCost = async ({ H, content }) => {
  const { col, text, rich, box, table, stat } = H;
  const s = content("Bandwidth", "Counting bits · in Egyptian pounds", "One hour of video on an Egyptian home internet line",
    "Prices: WE (Telecom Egypt) entry-level home package, 100 GB for EGP 150 per month before 14 % VAT (EGP 171 with VAT) after the NTRA decision effective 1 November 2026. That is about EGP 1.71 per GB. Other WE Space tiers: 150 GB for EGP 260, 200 GB for EGP 330 (VAT exclusive). " +
    "Raw 1080p30 in RGB (24 bits/pixel) = 1920 × 1080 × 30 × 24 = 1.49 Gb/s = 672 GB per hour. At EGP 1.71/GB that is about EGP 1,150 for one hour, or 6.7 months of the base package; the whole month's 100 GB lasts 9 minutes. " +
    "The same hour in H.264 at 5 Mb/s is 2.25 GB, about EGP 3.85; a 2 Mb/s ROV pilot stream is 0.9 GB, about EGP 1.54. A 30 Mb/s WE line could not even carry the raw stream: it would need about 50 times more speed. " +
    "Prices change often: re-check te.eg before presenting. Calculator: demos/01_why_streaming/egypt_cost.py.");
  table(s, [
    ["One hour of 1080p30 video", "Data", "Cost at EGP 1.71/GB", "100 GB package lasts"],
    ["Raw RGB (24 bits/pixel) · 1.49 Gb/s", "672 GB", { text: "≈ EGP 1,150", color: HEX.rose, bold: true }, { text: "9 minutes", color: HEX.rose, bold: true }],
    ["Raw YUV 4:2:0 (12 bits/pixel) · 0.75 Gb/s", "336 GB", { text: "≈ EGP 575", color: HEX.rose }, "18 minutes"],
    ["H.264 · 5 Mb/s (streaming HD)", "2.25 GB", { text: "≈ EGP 3.85", color: HEX.teal, bold: true }, { text: "44 hours", color: HEX.teal, bold: true }],
    ["H.264 · 2 Mb/s (our ROV pilot camera)", "0.9 GB", { text: "≈ EGP 1.54", color: HEX.teal }, "111 hours"],
  ], 0.6, 1.75, 12.1, [4.6, 1.8, 2.9, 2.8], { fontSize: 14, rowH: 0.52 });
  box(s, 0.6, 4.7, 5.9, 1.95, { fill: col.card });
  stat(s, 0.85, 4.75, 5.4, "≈ 300×", "cheaper with H.264 at 5 Mb/s than raw RGB, for the same hour", col.teal, { size: 44, labelSize: 14 });
  box(s, 6.8, 4.7, 5.9, 1.95, { fill: col.card });
  stat(s, 7.05, 4.75, 5.4, "50×", "more speed than a 30 Mb/s WE line would be needed just to carry raw 1080p30", col.amber, { size: 44, labelSize: 14 });
  text(s, "Prices: WE entry package, 100 GB = EGP 150 + 14 % VAT (from 1 Nov 2026). Prices change; check te.eg.", { x: 0.6, y: 6.72, w: 12.1, h: 0.3, fontSize: 11, color: col.muted, italic: true });
};

// ---------------------------------------------------------------- USB vs IP cameras
exports.usbVsIp = async ({ H, content }) => {
  const { col, text, rich, box, table } = H;
  const s = content("Underwater video", "Camera choice", "USB cameras vs IP cameras",
    "Both can give us eight cameras; the difference is where encoding and bandwidth limits live. " +
    "USB 2.0: 480 Mb/s signalling shared by everything on the bus; UVC cameras reserve isochronous bandwidth, so several raw or MJPEG cameras on one hub fail to start. Passive USB cables are limited to 5 m. Some UVC cameras encode H.264 on board — the Blue Robotics Low-Light HD USB camera offers H.264, MJPEG and YUY2 at 1080p30 and draws up to 220 mA at 5 V. " +
    "IP cameras: each camera encodes H.264/H.265 itself and sends RTSP/RTP over Ethernet; cable runs up to 100 m; PoE 802.3af delivers 15.4 W per port at the switch (12.95 W at the camera). This is why network video recorders can ingest dozens of cameras: the recorder never encodes, it only receives. " +
    "Trade-offs: IP boards are bigger, need more power and an Ethernet switch inside the ROV, and their internal buffering sets latency — measure glass-to-glass before trusting a datasheet.");
  table(s, [
    ["", "USB (UVC) camera", "IP camera"],
    ["Link", "USB 2.0: 480 Mb/s shared by the whole bus · 5 m passive cable", "Ethernet: own 100 Mb/s or 1 Gb/s port · 100 m cable"],
    ["Power", "5 V from USB (e.g. 220 mA for the Blue Robotics low-light camera)", "PoE 802.3af: 15.4 W per switch port, or a separate supply"],
    ["Who encodes?", "Raw YUYV / MJPEG → the SBC encodes; or onboard H.264 in some models", { text: "Always the camera (H.264/H.265); the SBC is optional", color: HEX.teal, bold: true }],
    ["Scaling to 8", { text: "Bus bandwidth + isochronous reservations: hubs fail first", color: HEX.rose }, "Add switch ports. NVRs ingest dozens of cameras because they never encode"],
    ["Latency", "Lowest when raw/MJPEG is used locally", "Set by the camera's own buffering: measure it"],
    ["Size & integration", "Small, cheap, easy to seal", "Larger board, more heat, switch inside the hull"],
  ], 0.6, 1.75, 12.1, [2.3, 4.9, 4.9], { fontSize: 13, rowH: 0.55 });
  box(s, 0.6, 5.85, 12.1, 0.8, { fill: col.card, line: HEX.cyan });
  rich(s, [{ text: "Key idea: ", bold: true, color: col.cyan, nl: false }, { text: "8 cameras work either way. Choose where the encoding happens and which bus carries the bits, then measure with lsusb -t, v4l2-ctl and ffprobe." }], 0.85, 5.95, 11.6, 0.6, { fontSize: 15, valign: "middle" });
};

// ---------------------------------------------------------------- Pi 5 verdict
exports.pi5Verdict = async ({ H, content }) => {
  const { col, text, rich, box, iconCircle } = H;
  const s = content("Hardware & transport", "This year's decision", "Can the Raspberry Pi 5 replace the Jetson Nano?",
    "Answer: it depends on who encodes. 1) If the cameras deliver H.264 (UVC cameras with onboard H.264 or IP cameras), the SBC only forwards packets; the Pi 5's much faster CPU (4× Cortex-A76 at 2.4 GHz vs 4× A57 at 1.43 GHz) is an upgrade. " +
    "2) If the SBC must encode several raw or MJPEG USB cameras, the Nano wins: its hardware encoder handles 4× 1080p30 or 9× 720p30, while Raspberry Pi's April 2026 white paper measured 62–90 % of one core for a single 1080p30 low-latency libx264 encode — so roughly three such streams at most, plus heat. " +
    "3) Computer vision: the Nano has a CUDA GPU (TensorRT); the Pi 5 needs the AI HAT+ (Hailo-8L 13 TOPS or Hailo-8 26 TOPS) or runs CV on the CPU. " +
    "Lifecycle: NVIDIA lists the Jetson Nano Developer Kit as end of life, JetPack 4 reached end of life in November 2024, and Nano production modules are available until January 2027. " +
    "Nobody has tested the Pi 5 on our ROV yet, so the right answer is a soak test before buying: 8 streams, 30 minutes, sealed enclosure, logging CPU, temperature, throttling and dropped frames.");
  const cards = [
    [fi.FiCamera, "Cameras encode", "UVC H.264 or IP cameras: the SBC only forwards packets", "Pi 5 is a good replacement — faster CPU, current OS", col.teal, "✔ Pi 5"],
    [fi.FiCpu, "SBC must encode", "Several raw / MJPEG USB cameras", "Nano: HW encoder 4× 1080p30. Pi 5: 0.62–0.9 core per 1080p30 stream", col.rose, "✔ Nano"],
    [fi.FiEye, "On-board vision", "Detection, SLAM, autonomy on the ROV", "Nano: CUDA GPU. Pi 5: CPU or AI HAT+ (13 / 26 TOPS)", col.amber, "≈ Tie (+ HAT)"],
  ];
  for (let i = 0; i < 3; i++) {
    const [ic, t, w, b, c, v] = cards[i]; const x = 0.6 + i * 4.1;
    box(s, x, 1.75, 3.85, 3.35, { fill: col.card });
    await iconCircle(s, ic, x + 0.25, 1.95, 0.6);
    text(s, v, { x: x + 1.0, y: 2.0, w: 2.6, h: 0.5, fontSize: 18, bold: true, color: c, align: "right", valign: "middle" });
    text(s, t, { x: x + 0.25, y: 2.7, w: 3.4, h: 0.45, fontSize: 18, bold: true });
    text(s, w, { x: x + 0.25, y: 3.15, w: 3.4, h: 0.7, fontSize: 13, color: col.muted });
    text(s, b, { x: x + 0.25, y: 3.9, w: 3.4, h: 1.1, fontSize: 14 });
  }
  box(s, 0.6, 5.3, 6.0, 1.4, { fill: HEX.cardHi });
  rich(s, [{ text: "Lifecycle", bold: true, color: col.cyan }, { text: "Nano dev kit: end of life · JetPack 4: EOL Nov 2024 · Nano modules until Jan 2027. Pi 5: current product." }], 0.85, 5.4, 5.6, 1.2, { fontSize: 13 });
  box(s, 6.8, 5.3, 5.9, 1.4, { fill: col.card, line: HEX.amber });
  rich(s, [{ text: "Before buying: soak test", bold: true, color: col.amber }, { text: "8 streams · 30 min · sealed enclosure · log CPU, temperature, throttling, dropped frames." }], 7.05, 5.4, 5.5, 1.2, { fontSize: 13 });
};

// ---------------------------------------------------------------- Heat reliability
exports.heatReliability = async ({ H, content }) => {
  const { col, text, rich, box, flow, bullets } = H;
  const s = content("Hardware & transport", "Reliability · lesson from 2023", "When the stream died from heat",
    "What we know: during a competition trial in 2023 the streaming stopped working because the SBC got too hot. Ask the team for the details (which board, which cameras, enclosure, ambient temperature, how long into the run) and write a blameless postmortem — template in sdlc/postmortem-template.md. " +
    "Mechanism: a sealed enclosure has no airflow, encoding is a constant heavy load, the SoC reaches its limit and throttles. On Raspberry Pi boards throttling starts at 80 °C and gets aggressive at 85 °C; the Pi 5 Active Cooler's fan starts at 60 °C, but a fan only moves hot air around inside a sealed hull — the heat has to leave through the hull into the water. " +
    "A throttled CPU encodes fewer frames per second than the cameras produce: queues grow, latency grows, frames drop, and eventually the pipeline stalls. " +
    "Fixes are engineering, not luck: measure (log temperature and throttle flags every second), design a heat path, cut the load (cameras that encode themselves), soak-test in warm water, and show the temperature to the pilot.");
  flow(s, [
    { title: "Sealed hull", sub: "no airflow" },
    { title: "Constant encode load", sub: "CPU near 100 %" },
    { title: "SoC ≥ 80 °C", sub: "firmware throttles", color: HEX.cardHi },
    { title: "Encoder too slow", sub: "queues grow, frames drop" },
    { title: "Stream stops", sub: "in front of the judges", titleColor: HEX.rose },
  ], 0.6, 1.8, 12.1, 1.2, { titleSize: 14, subSize: 11 });
  const fixes = [
    ["Measure", "Log temperature + throttle flags every second (vcgencmd get_throttled · tegrastats)"],
    ["Design", "Heat path to the hull: thermal pad → aluminium plate → hull → water"],
    ["Reduce", "Let cameras encode; lower FPS/resolution for aux cameras"],
    ["Soak-test", "30 min in the sealed enclosure in warm water before every event"],
    ["Show", "Temperature on the pilot screen; warning at 75 °C, before throttling"],
  ];
  fixes.forEach(([a, b], i) => {
    const y = 3.3 + i * 0.68;
    box(s, 0.6, y, 12.1, 0.58, { fill: i % 2 ? col.card : HEX.cardHi });
    text(s, a, { x: 0.85, y, w: 1.8, h: 0.58, fontSize: 15, bold: true, color: col.cyan, valign: "middle" });
    text(s, b, { x: 2.7, y, w: 9.8, h: 0.58, fontSize: 14, valign: "middle" });
  });
};

// ---------------------------------------------------------------- CV and SLAM
exports.cvAndSlam = async ({ H, content }) => {
  const { col, text, rich, box, iconCircle, bullets } = H;
  const s = content("Hardware & transport", "Streaming for computer vision", "The robot's eyes only see what the encoder kept",
    "Competition tasks often include object detection, 3D reconstruction, autonomous movement, and SLAM. If those algorithms run topside on the pilot stream, they inherit every streaming decision. " +
    "Evidence: O'Byrne et al. (2022) ran YOLOv5 on H.264 video at CRF 22–47: CRF 37 instead of 22 barely changed detection, but performance dropped at higher compression, especially in poor light and with fast motion — which describes underwater footage. " +
    "Feature-based SLAM depends on corners and texture; compression removes exactly those details, so fewer feature points survive and matching gets worse (ORBBuf, 2020, on JPEG-compressed images). " +
    "Latency and jitter matter for anything closed-loop: an autonomous controller acting on a frame that is 300 ms old overshoots. " +
    "Practical rules on the slide. The Encoding Lab can generate the compressed versions of your footage for testing.");
  const tasks = [[fi.FiTarget, "Object detection"], [tb.TbCube3dSphere, "3D reconstruction"], [tb.TbRoute, "Autonomous moves"], [fi.FiMap, "SLAM"]];
  for (let i = 0; i < 4; i++) {
    const x = 0.6 + i * 3.05;
    box(s, x, 1.75, 2.85, 0.85, { fill: col.card });
    await iconCircle(s, tasks[i][0], x + 0.15, 1.88, 0.58);
    text(s, tasks[i][1], { x: x + 0.85, y: 1.75, w: 1.95, h: 0.85, fontSize: 15, bold: true, valign: "middle" });
  }
  box(s, 0.6, 2.85, 5.9, 3.8, { fill: col.card });
  text(s, "What streaming does to them", { x: 0.85, y: 2.98, w: 5.4, h: 0.4, fontSize: 17, bold: true, color: col.rose });
  bullets(s, [
    "Blocking and blur erase the corners SLAM tracks",
    "Detection holds at moderate compression, then drops — worst in low light and fast motion (YOLOv5 study, 2022)",
    "Old frames → autonomous control overshoots",
    "Dropped frames and bad timestamps → wrong motion estimates",
    "Keyframe pulsing → quality changes every GOP",
  ], 0.85, 3.45, 5.45, 3.1, { fontSize: 14, gap: 5 });
  box(s, 6.8, 2.85, 5.9, 3.8, { fill: col.card });
  text(s, "Rules for our team", { x: 7.05, y: 2.98, w: 5.4, h: 0.4, fontSize: 17, bold: true, color: col.teal });
  bullets(s, [
    "Run CV next to the raw frames (on the ROV) when you can",
    "Topside CV gets its own stream: higher bitrate, no B-frames, constant FPS, timestamps",
    "Photogrammetry: capture stills or record locally at high quality, not the pilot stream",
    "Measure detection accuracy vs bitrate on our own footage",
  ], 7.05, 3.45, 5.45, 3.1, { fontSize: 14, gap: 5 });
};

// ---------------------------------------------------------------- SDLC: Quality × Efficiency
exports.qualityTimesEfficiency = async ({ H, content }) => {
  const { col, text, rich, box, bullets } = H;
  const s = content("Engineering practice", "Our equation", "Work force = Quality × Efficiency",
    "It is a product, not a sum: if either factor is zero, the result is zero. A team that ships fast but the stream freezes in the pool delivered nothing; perfect code that is ready the week after the competition also delivered nothing. " +
    "Quality levers are about doing the right thing correctly: clear requirements, review, tests, a definition of done. Efficiency levers are about not wasting the team's hours: automation, small pull requests, one board, fewer context switches, reusing what exists. " +
    "Ask the room: which factor is our weaker one today? Improving the weaker factor multiplies everything else.");
  box(s, 0.6, 1.8, 12.1, 1.3, { fill: HEX.cardHi });
  rich(s, [{ text: "Work force", bold: true, color: col.text, fontSize: 34, nl: false }, { text: "  =  ", fontSize: 34, color: col.muted, nl: false },
    { text: "Quality", bold: true, color: col.teal, fontSize: 34, nl: false }, { text: "  ×  ", fontSize: 34, color: col.muted, nl: false },
    { text: "Efficiency", bold: true, color: col.cyan, fontSize: 34 }], 0.6, 1.95, 12.1, 1.0, { align: "center", valign: "middle" });
  const cols = [
    ["Quality: doing it right", col.teal, ["Requirements with acceptance tests", "Every change reviewed", "Bug Hunt League finds what developers miss", "Definition of Done includes a pool test"]],
    ["Efficiency: no wasted hours", col.cyan, ["CI runs the tests automatically", "Small pull requests, merged within days", "One board: everyone sees what's next", "Reuse demos, scripts and templates"]],
  ];
  cols.forEach(([t, c, items], i) => {
    const x = 0.6 + i * 6.2;
    box(s, x, 3.35, 5.9, 2.65, { fill: col.card });
    text(s, t, { x: x + 0.25, y: 3.48, w: 5.4, h: 0.45, fontSize: 18, bold: true, color: c });
    bullets(s, items, x + 0.25, 4.0, 5.4, 1.9, { fontSize: 15, gap: 5 });
  });
  text(s, "Fast but broken = 0.   Perfect but late = 0.   Fix the weaker factor first.", { x: 0.6, y: 6.25, w: 12.1, h: 0.45, fontSize: 17, bold: true, color: col.amber, align: "center" });
};

// ---------------------------------------------------------------- SDLC: Bug Hunt League
exports.bugHuntLeague = async ({ H, content }) => {
  const { col, text, rich, box, table, bullets, iconCircle } = H;
  const s = content("Engineering practice", "Everybody tests", "The Bug Hunt League",
    "Problem: only 3–4 of about 20 members write the GUI, and developers test the paths they already imagined. The other 16 are the best testers we have: they think like pilots and electrical engineers, not like the author. " +
    "Mechanics: every confirmed bug earns points by severity, with bonuses for a reproduction video or a failing test, and for catching a regression of something already fixed. Duplicates go to the first reporter; developers cannot score on their own code. Weekly leaderboard in the meeting, monthly Bug Hunter award, and the season champion picks a feature for the next sprint. " +
    "All bugs live in GitHub Issues using the Bug report form; the GitHub Projects board shows Reported → Confirmed → Fixing → Verify → Closed. The hunter who found it verifies the fix — that closes the loop and teaches them the code. " +
    "Event: a 45-minute Bug Bash before every pool test. Full rules: sdlc/bug-hunt-league.md.");
  table(s, [
    ["Severity", "Example", "Points"],
    ["Critical", "Stream freezes, crash, wrong thruster command, unsafe default", { text: "10", bold: true, color: HEX.rose, align: "center" }],
    ["Major", "Feature broken, wrong camera shown, data lost", { text: "5", bold: true, color: HEX.amber, align: "center" }],
    ["Minor", "Works with a workaround, cosmetic glitch on one screen", { text: "2", bold: true, align: "center" }],
    ["UX", "Confusing label, missing feedback, hard to find under stress", { text: "1", bold: true, align: "center" }],
    ["Bonus", "+2 repro video or failing test · +3 regression of a fixed bug", { text: "+2 / +3", bold: true, color: HEX.teal, align: "center" }],
  ], 0.6, 1.75, 7.6, [1.4, 4.9, 1.3], { fontSize: 13, rowH: 0.52 });
  box(s, 8.45, 1.75, 4.25, 3.1, { fill: col.card });
  text(s, "Rules", { x: 8.7, y: 1.88, w: 3.8, h: 0.4, fontSize: 17, bold: true, color: col.cyan });
  bullets(s, ["Reproducible steps or it doesn't count", "First reporter wins duplicates", "No points on your own code", "The hunter verifies the fix"], 8.7, 2.35, 3.85, 2.4, { fontSize: 14, gap: 5 });
  const flowSteps = ["Reported", "Confirmed", "Fixing", "Verify", "Closed"];
  flowSteps.forEach((t, i) => {
    const x = 0.6 + i * 2.45;
    box(s, x, 5.15, 2.2, 0.62, { fill: i === 3 ? HEX.cardHi : col.card, line: i === 3 ? HEX.teal : undefined });
    text(s, t, { x, y: 5.15, w: 2.2, h: 0.62, fontSize: 15, bold: true, align: "center", valign: "middle" });
  });
  await iconCircle(s, tb.TbTrophy, 0.6, 6.05, 0.55, HEX.amber, col.amber);
  text(s, "Weekly leaderboard · monthly Bug Hunter award · season champion picks a feature · Bug Bash before every pool test",
    { x: 1.3, y: 6.02, w: 11.4, h: 0.62, fontSize: 15, color: col.muted, valign: "middle" });
};

// ---------------------------------------------------------------- SDLC: GitHub as a workflow
exports.githubWorkflow = async ({ H, content }) => {
  const { col, text, rich, box, iconCircle, bullets } = H;
  const s = content("Engineering practice", "GitHub beyond storage", "GitHub is a workflow, not a folder",
    "Today the repo is used as a backup drive. That keeps files, but loses the reasons: why a change was made, who reviewed it, which version worked in the pool. " +
    "Use the features we already have for free: Issues for bugs and tasks, a Projects board, pull requests with one review, Actions to run tests on every pull request, tags/releases before every pool test, and branch protection so main always runs. " +
    "Adopt it as a four-week ladder, one step per week, so nobody is overwhelmed. Templates for issues, pull requests and CI are in the repo's .github folder. Guide: sdlc/github-workflow.md.");
  const feats = [
    [fi.FiList, "Issues", "Every bug and task, with labels and owners"],
    [fi.FiGitPullRequest, "Pull requests", "One review before anything reaches main"],
    [fi.FiZap, "Actions (CI)", "Tests run on every pull request, automatically"],
    [fi.FiTag, "Releases", "A tag before every pool test: know what worked"],
    [fi.FiShield, "Branch protection", "main always runs on the ROV"],
    [fi.FiActivity, "Projects board", "One view of who does what this week"],
  ];
  for (let i = 0; i < 6; i++) {
    const x = 0.6 + (i % 3) * 4.1, y = 1.75 + Math.floor(i / 3) * 1.45;
    box(s, x, y, 3.85, 1.3, { fill: col.card });
    await iconCircle(s, feats[i][0], x + 0.2, y + 0.33, 0.6);
    text(s, feats[i][1], { x: x + 0.95, y: y + 0.15, w: 2.75, h: 0.45, fontSize: 16, bold: true });
    text(s, feats[i][2], { x: x + 0.95, y: y + 0.58, w: 2.75, h: 0.65, fontSize: 13, color: col.muted });
  }
  const ladder = [["Week 1", "Issues + board"], ["Week 2", "PRs + 1 review"], ["Week 3", "CI runs tests"], ["Week 4", "Tags + protection"]];
  ladder.forEach(([w, t], i) => {
    const x = 0.6 + i * 3.05, y = 5.0 - i * 0.12;
    box(s, x, y, 2.85, 1.55 + i * 0.12, { fill: i === 3 ? HEX.cardHi : col.card, line: i === 3 ? HEX.cyan : undefined });
    text(s, w, { x: x + 0.2, y: y + 0.12, w: 2.45, h: 0.4, fontSize: 14, bold: true, color: col.cyan });
    text(s, t, { x: x + 0.2, y: y + 0.55, w: 2.45, h: 0.6, fontSize: 16, bold: true });
  });
};

// ---------------------------------------------------------------- MJPEG: where it fits (added 19 Nov 2026)
const MJ_NOTE = "Measured 19 Nov 2026 on the Encoding Lab's synthetic 720p30 clip (FFmpeg 6.1). Reading: docs/streaming/codecs-and-ffmpeg.md.";
exports.mjpegWhere = async ({ H, content }) => {
  const { col, text, box, stat, card } = H;
  const s = content("Encoding", "MJPEG on the ROV", "MJPEG: costly in bits, cheap in everything else",
    "MJPEG = every frame is its own JPEG. No reference frames, so no encoder hold and a lost frame never smears into the next one. " +
    "The price is bits: at the same SSIM, MJPEG q=3 needed 11.9 Mb/s where H.264 veryfast zerolatency CRF 21 needed 2.52 Mb/s, 4.7 times more. " +
    "Copying a USB camera's own MJPEG with FFmpeg (-c:v copy) cost 1.3 % of one CPU core for 720p30: no encoding at all, which matters on the Pi 5. " +
    "So: H.264 for what the pilot drives with; MJPEG where it is free (the camera already makes it) or flexible (we draw on the frames). " + MJ_NOTE);
  const stats = [
    ["4.7×", "more bits than H.264 for the same SSIM (MJPEG q=3 vs CRF 21)", col.rose],
    ["0 frames", "encoder hold: every frame leaves as soon as it is compressed", col.teal],
    ["1.3 %", "of one core to pass a USB camera's 720p30 MJPEG through FFmpeg", col.cyan],
  ];
  stats.forEach(([v, l, c], i) => {
    box(s, 0.6 + i * 4.1, 1.75, 3.85, 1.95, { fill: col.card });
    stat(s, 0.85 + i * 4.1, 1.8, 3.4, v, l, c, { size: 42, labelSize: 13, lh: 0.75 });
  });
  await card(s, 0.6, 3.95, 5.95, 2.65, { title: "Use MJPEG for", titleColor: col.teal, line: HEX.teal, bodySize: 15,
    bullets: ["Aux cameras ≤ 640×480 at 10–15 fps (≈ 1–1.3 Mb/s each)", "CV debug views: boxes, masks, SLAM keypoints",
      "Measurement snapshots and training-data recordings", "The fallback stream when the H.264 path fails"] });
  await card(s, 6.75, 3.95, 5.95, 2.65, { title: "Keep H.264 for", titleColor: col.rose, line: HEX.rose, bodySize: 15,
    bullets: ["Pilot and manipulator cameras", "Anything above ≈ 8 Mb/s in MJPEG",
      "Any stream that must stay smooth on a busy tether (HTTP is TCP: a lost packet stalls it)"] });
  text(s, MJ_NOTE, { x: 0.6, y: 6.72, w: 12.1, h: 0.3, fontSize: 11, color: col.muted, italic: true });
};

// ---------------------------------------------------------------- FFmpeg vs the MJPEG streamers
exports.ffmpegVsStreamers = async ({ H, content }) => {
  const { col, text, table } = H;
  const s = content("Encoding", "Tool choice", "Use FFmpeg, not mjpeg-streamer",
    "Three tools can serve MJPEG. mjpeg-streamer is a Python library (PyPI, AGPLv3, one maintainer, last release Feb 2024). mjpg-streamer is a C program (last commit Feb 2021; its Pi-camera plugin needs MMAL, which the Pi 5 does not have). FFmpeg is the tool we already use in the Encoding Lab. " +
    "We read the Python library's source and tested it: it re-encodes the frame for every viewer (2 viewers = 28 encodes/s instead of 14) and paces by a timer, so a 5 fps source went out at about 14 fps of duplicates. " +
    "FFmpeg passes a camera's MJPEG through untouched (-c:v copy), encodes our own CV frames exactly once, and adds RTP, recording, snapshots, filters, H.264/H.265 and quality metrics. " +
    "Its one gap: the built-in HTTP server serves one viewer per process. Cover it by sending RTP once over the tether and fanning out topside. " + MJ_NOTE);
  const ok = (t) => ({ text: t, color: HEX.teal, bold: true });
  const no = (t) => ({ text: t, color: HEX.rose });
  const meh = (t) => ({ text: t, color: HEX.amber });
  table(s, [
    ["Job", "mjpeg-streamer (Python)", "mjpg-streamer (C)", "FFmpeg"],
    ["Pass camera MJPEG through, no encode", no("✘ decodes + re-encodes"), ok("✔"), ok("✔ -c:v copy · 1.3 % of a core")],
    ["Encode our own CV frames", meh("once per viewer (2 viewers = 2×)"), meh("input_opencv only"), ok("✔ once per frame (stdin pipe)")],
    ["Frame pacing", no("timer: ≈ 3× duplicates at 5 fps"), ok("✔ camera-driven"), ok("✔ source-driven")],
    ["RTP/UDP (no TCP stalls)", no("✘"), no("✘ listed as not functional"), ok("✔ -f rtp")],
    ["Stream + record + snapshot", no("✘"), meh("separate plugins"), ok("✔ tee, no re-encode")],
    ["Filters · H.264/H.265 · quality metrics", no("✘"), no("✘"), ok("✔ same tool")],
    ["Browser viewers (HTTP)", ok("✔ many"), ok("✔ many"), meh("one per process → RTP + topside fan-out")],
    ["Maintenance", meh("1 maintainer · Feb 2024"), no("last commit Feb 2021"), ok("✔ active · every distro")],
  ], 0.6, 1.75, 12.1, [3.3, 2.95, 2.55, 3.3], { fontSize: 13, rowH: 0.5 });
  text(s, "Verdict: FFmpeg. One tool we already know, from camera to recording, H.264 and testing.",
    { x: 0.6, y: 6.4, w: 12.1, h: 0.5, fontSize: 16, bold: true, color: col.amber, valign: "middle" });
};

// ---------------------------------------------------------------- FFmpeg recipes
exports.ffmpegRecipes = async ({ H, content }) => {
  const { col, text, code } = H;
  const s = content("Encoding", "FFmpeg recipes · all tested", "FFmpeg does the same jobs, and more",
    "Four recipes cover what the team asked mjpeg-streamer for, and more. All were tested on 19 Nov 2026 with FFmpeg 6.1, except the /dev/video0 capture lines (no camera on the test machine). " +
    "1) Passthrough to a browser: -content_type is required, otherwise the browser treats the stream as a download. FFmpeg's HTTP server takes one viewer and exits when it leaves; demos/02_pipeline/mjpeg_ffmpeg.sh http restarts it in a loop. " +
    "2) tee: one capture feeds live RTP, a recording and an always-fresh latest.jpg, with no re-encode. " +
    "3) CV debug: OpenCV draws, FFmpeg encodes each frame once. -huffman default is needed for RTP (RFC 2435 requires the standard Huffman tables). Full script: demos/02_pipeline/cv_debug_ffmpeg.py. " +
    "4) Topside: one RTP copy crosses the tether; every viewer opens the same .sdp.");
  const cells = [
    ["1 · Camera → browser, zero encode",
      "ffmpeg -f v4l2 -input_format mjpeg \\\n  -video_size 1280x720 -framerate 30 -i /dev/video0 \\\n  -c:v copy -f mpjpeg -content_type \\\n  \"multipart/x-mixed-replace;boundary=ffmpeg\" \\\n  -listen 1 http://0.0.0.0:8080/aux1.mjpg"],
    ["2 · One capture → live + recording + snapshot",
      "ffmpeg -f v4l2 -input_format mjpeg -i /dev/video0 \\\n  -map 0:v -c:v copy -f tee \\\n  \"[f=rtp]rtp://192.168.1.100:5600|\\\n[f=avi]dive.avi|\\\n[f=image2:update=1]latest.jpg\""],
    ["3 · CV debug: OpenCV draws, FFmpeg encodes once",
      "ff = subprocess.Popen([\"ffmpeg\",\n    \"-f\", \"rawvideo\", \"-pix_fmt\", \"bgr24\",\n    \"-s\", \"640x360\", \"-r\", \"10\", \"-i\", \"-\",\n    \"-c:v\", \"mjpeg\", \"-q:v\", \"7\", \"-huffman\", \"default\",\n    \"-f\", \"rtp\", \"-sdp_file\", \"det.sdp\",\n    \"rtp://192.168.1.100:5610\"], stdin=subprocess.PIPE)\nff.stdin.write(draw_boxes(frame).tobytes())"],
    ["4 · Topside: one copy on the tether, many viewers",
      "# browser tile (recipe 1)\n<img src=\"http://rov:8080/aux1.mjpg\">\n\n# RTP (recipes 2 and 3): any number of viewers\nffplay -protocol_whitelist file,udp,rtp \\\n  -fflags nobuffer -flags low_delay aux1.sdp"],
  ];
  cells.forEach(([title, src], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.7 + Math.floor(i / 2) * 2.55;
    text(s, title, { x, y, w: 5.95, h: 0.38, fontSize: 15, bold: true, color: col.cyan, valign: "middle" });
    code(s, src, x, y + 0.42, 5.95, 2.0, { fontSize: 11.5 });
  });
};
