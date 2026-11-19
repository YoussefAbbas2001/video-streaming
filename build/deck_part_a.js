// Slides 1–37: opening, underwater video, architecture, bandwidth, encoding, hardware, transport, latency, multi-camera.
const fi = require("react-icons/fi");
const tb = require("react-icons/tb");
const { HEX, SERIES } = require("./deck_helpers");

module.exports = async function partA(ctx) {
  const { pres, H, D, content, section } = ctx;
  const { col, text, bullets, rich, box, iconCircle, card, arrow, flow, table, stat, code, pill } = H;
  const chartBase = (o = {}) => ({
    catAxisLabelColor: HEX.muted, valAxisLabelColor: HEX.muted, catAxisLabelFontSize: 11, valAxisLabelFontSize: 11,
    catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt", legendFontFace: "+mn-lt",
    titleFontFace: "+mj-lt", valGridLine: { color: HEX.grid, size: 0.75 }, catGridLine: { style: "none" },
    catAxisLineShow: false, valAxisLineShow: false, legendColor: HEX.muted, legendFontSize: 11, titleColor: HEX.text, titleFontSize: 14,
    dataLabelColor: HEX.text, dataLabelFontSize: 11, ...o,
  });

  // ---------------------------------------------------------------- 1 Title
  {
    const s = pres.addSlide({ masterName: "MIA_TITLE", sectionTitle: "Opening" });
    s.addImage({ path: D.img.hero, x: 0, y: 0, w: 13.333, h: 7.5, objectName: "hero-image", altText: "Synthetic underwater inspection frame: a pipeline seen through blue-green water" });
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 13.333, h: 7.5, fill: { color: col.bg, transparency: 22 }, line: { type: "none" }, objectName: "hero-overlay" });
    s.addText("Engineering Better ROV Systems", { placeholder: "title" });
    s.addText("Video streaming, measurement, testing and pilot-centred design — an industry workshop for M.I.A Robotics", { placeholder: "body" });
    pill(s, "SESSION 1 · VIDEO ENGINEERING", 0.8, 5.35, 3.6, col.cyan);
    pill(s, "SESSION 2 · ENGINEERING PRACTICE & UX", 4.6, 5.35, 4.2, col.teal);
    text(s, "Presented by: [Your name] · C++ & Computer Vision Engineer, MCS Oil & Gas", { x: 0.8, y: 6.15, w: 9, h: 0.4, fontSize: 14, color: col.muted });
    s.addNotes("Welcome everyone. Open with a question, not a definition: 'Who here has driven the ROV and felt the video lag, freeze or go blurry at the worst moment?' Let a few hands go up. Then: today is about turning those moments into measurements and engineering decisions. Background image: a frame from the synthetic underwater clip used in the notebook — swap it for a photo of the team's own ROV if you have one.");
  }
  // ---------------------------------------------------------------- 2 Why this session
  {
    const s = content("Opening", "Why we are here", "From bench-ready to mission-ready",
      "Introduce yourself briefly: you build professional video systems — capture, encoding, decoding, rendering, streaming — in the oil & gas industry, where ROV video is how humans see subsea assets. Then state the three promises of the day. Emphasise the mindset line at the bottom; it returns at the end of the session.");
    const items = [
      [fi.FiActivity, "Measure", "Find out what your video system actually does — codec, bitrate, latency, CPU — instead of guessing."],
      [fi.FiCpu, "Engineer", "Use compression, hardware encoders and smart stream management instead of cutting resolution."],
      [fi.FiUsers, "Collaborate", "Requirements, testing, reviews and pilot-centred UX — the habits that make a team reliable."],
    ];
    for (let i = 0; i < 3; i++) await card(s, 0.6 + i * 4.1, 1.75, 3.8, 3.3, { icon: items[i][0], title: items[i][1], body: items[i][2], bodySize: 18, titleSize: 19 });
    box(s, 0.6, 5.4, 12.1, 1.1, { fill: col.card });
    rich(s, [{ text: "The mindset for today:  ", bold: true, color: col.cyan, fontSize: 18, nl: false }, { text: "“How would we measure that?” comes before “How do we fix that?”", fontSize: 18, italic: true }], 0.9, 5.62, 11.6, 0.7, { valign: "middle" });
  }
  // ---------------------------------------------------------------- 3 MATE
  {
    const s = content("Opening", "M.I.A Robotics × MATE ROV", "MATE judges engineering, not only driving",
      "MATE ROV is an international underwater robotics competition run by the MATE Center and the Marine Technology Society. Missions are themed around real ocean-industry tasks. Points come from the product demonstration (pool missions) AND from technical documentation, an engineering presentation and a marketing display. Everything we do today makes all four stronger: measured performance is a great story for the presentation, and a clear process is great documentation. Check the current season's manual for exact scoring — it changes every year.");
    const cols = [
      [tb.TbSubmarine, "Product demonstration", "Pool missions under time pressure — this is where video latency and reliability decide points."],
      [fi.FiFileText, "Technical documentation", "Design rationale, testing, safety. Measurements and decisions belong here."],
      [fi.FiMic, "Engineering presentation", "Judges ask “why did you choose this?”. Evidence beats opinion."],
      [fi.FiShield, "Safety & reliability", "Inspections, safe operation, failure handling — the system must behave predictably."],
    ];
    for (let i = 0; i < 4; i++) await card(s, 0.6 + i * 3.05, 1.75, 2.85, 3.55, { icon: cols[i][0], title: cols[i][1], body: cols[i][2], titleSize: 15, bodySize: 16 });
    text(s, "Today's material is designed to produce artefacts you can reuse in all four: measurements, test reports, design decisions, and a pilot interface backed by usability tests.", { x: 0.6, y: 5.65, w: 12.1, h: 0.8, fontSize: 16, color: col.muted });
  }
  // ---------------------------------------------------------------- 4 Agenda
  {
    const s = content("Opening", "Agenda", "Two sessions, six hands-on activities",
      "Walk through the agenda quickly. Point out that there is an activity every 20–30 minutes. If you only have one day, use the compressed agenda in Workshop_Design.md.");
    const left = [["Why video matters underwater", ""], ["Your architecture & the unknowns", ""], ["Bandwidth engineering", "Activity 1"], ["How encoding works · codecs · GOP", "Notebook"], ["Quality metrics", "Activity 3"], ["Hardware · protocols · latency", ""], ["Multi-camera strategy", "Activity 2"]];
    const right = [["Software development lifecycle", ""], ["Requirements · user stories · DoD", ""], ["Testing", "Activity 4"], ["Code review & Git", ""], ["UX for ROV pilots", ""], ["Design the pilot experience", "Activity 6"], ["Final challenge", "Activity 5"]];
    [[left, "SESSION 1 · VIDEO ENGINEERING", col.cyan, 0.6], [right, "SESSION 2 · ENGINEERING PRACTICE & UX", col.teal, 6.85]].forEach(([list, head, c, x]) => {
      text(s, head, { x, y: 1.7, w: 5.9, h: 0.4, fontSize: 14, bold: true, color: c, fontFace: "Arial" });
      list.forEach(([t, a], i) => {
        const y = 2.2 + i * 0.62; box(s, x, y, 5.85, 0.52, { fill: col.card });
        text(s, `${String(i + 1).padStart(2, "0")}`, { x: x + 0.15, y, w: 0.5, h: 0.52, fontSize: 14, bold: true, color: c, valign: "middle" });
        text(s, t, { x: x + 0.65, y, w: 3.6, h: 0.52, fontSize: 15, valign: "middle" });
        if (a) pill(s, a, x + 4.35, y + 0.09, 1.35, c);
      });
    });
  }
  // ---------------------------------------------------------------- 5 Why video
  {
    const s = content("Opening", "Video is the primary sensor", "The pilot only knows what the cameras show",
      "Ask: 'If you lose depth telemetry, can you still finish a task? If you lose the main camera?' Professional work-class ROVs carry several cameras with distinct jobs: a pilot/navigation camera, manipulator cameras, an inspection or zoom camera, sometimes a rear camera for tether management. Each job has different quality and latency needs — that is the seed of the main/substream idea later. Situational awareness (Endsley): perceive, comprehend, project. Video feeds all three.");
    const jobs = [
      [fi.FiNavigation, "Pilot / navigation", "Wide view, lowest latency. Used continuously for driving."],
      [tb.TbHandGrab, "Manipulator", "Close-up of the gripper. Depth perception and latency matter most."],
      [fi.FiSearch, "Inspection", "Highest detail, often recorded. Latency matters less."],
      [fi.FiRotateCcw, "Rear / tether", "Occasional glances. Low frame rate is acceptable."],
    ];
    for (let i = 0; i < 4; i++) await card(s, 0.6 + (i % 2) * 3.55, 1.75 + Math.floor(i / 2) * 2.25, 3.35, 2.05, { icon: jobs[i][0], title: jobs[i][1], body: jobs[i][2], titleSize: 15 });
    box(s, 7.9, 1.75, 4.8, 4.3, { fill: col.card });
    text(s, "Situational awareness", { x: 8.15, y: 1.95, w: 4.3, h: 0.45, fontSize: 18, bold: true, fontFace: "Arial" });
    const lv = [["1  Perceive", "What is around the vehicle?"], ["2  Comprehend", "What does it mean for my task?"], ["3  Project", "What will happen next if I act?"]];
    lv.forEach(([a, b], i) => {
      box(s, 8.15, 2.6 + i * 1.08, 4.3, 0.9, { fill: col.cardHi });
      text(s, a, { x: 8.35, y: 2.65 + i * 1.08, w: 4, h: 0.4, fontSize: 16, bold: true, color: col.cyan });
      text(s, b, { x: 8.35, y: 3.02 + i * 1.08, w: 4, h: 0.4, fontSize: 14, color: col.muted });
    });
    text(s, "Every video defect — lag, freeze, blur — attacks one of these levels.", { x: 0.6, y: 6.3, w: 12, h: 0.45, fontSize: 15, italic: true, color: col.muted });
  }

  await require("./deck_part_new").worldRunsOnCompression(ctx);
  // ================================================================ SECTION 1
  section("Underwater video", "01", "Underwater video & your architecture", "Why video is hard down there — and what we know (and don't) about your system", D.img.section1,
    "Transition: before optimising anything, we need to understand the environment and the system we are optimising.");
  // ---------------------------------------------------------------- 7 Challenges
  {
    const s = content("Underwater video", "Physics first", "Underwater video fights the water itself",
      "Water absorbs red first, then orange and yellow — within a few metres the scene is blue-green. Suspended particles cause turbidity and backscatter: lights on the ROV illuminate particles between camera and target ('marine snow'). Low light pushes camera gain up, which adds noise that changes every frame. For compression this is bad news: noise and particles are unpredictable, so they cost bits. Point at the image: this is the synthetic clip from the notebook, built to have exactly these properties.");
    s.addImage({ path: D.img.frame, x: 0.6, y: 1.75, w: 6.4, h: 3.6, objectName: "underwater-frame", altText: "Synthetic underwater frame showing colour cast, haze and particles" });
    text(s, "Frame from the notebook's synthetic clip — colour cast, haze, caustics, marine snow, sensor noise.", { x: 0.6, y: 5.45, w: 6.4, h: 0.5, fontSize: 11, color: col.muted, italic: true });
    const ch = [
      ["Colour loss", "Red is absorbed within metres → blue-green cast, poor contrast."],
      ["Turbidity & backscatter", "Particles scatter the ROV's own lights back into the lens."],
      ["Low light → noise", "High gain = random noise every frame = expensive to compress."],
      ["Limited visibility", "Pilots rely on fine detail and depth cues at short range."],
      ["Tether constraints", "Every bit crosses one cable shared with control and telemetry."],
    ];
    ch.forEach(([a, b], i) => {
      text(s, a, { x: 7.4, y: 1.75 + i * 0.93, w: 5.3, h: 0.36, fontSize: 16, bold: true, color: col.cyan });
      text(s, b, { x: 7.4, y: 2.1 + i * 0.93, w: 5.3, h: 0.5, fontSize: 14, color: col.muted });
    });
  }
  // ---------------------------------------------------------------- 8 Student vs industrial
  {
    const s = content("Underwater video", "Same physics, different engineering", "Student ROV vs industrial ROV",
      "Be respectful: the point is not that student ROVs are worse — they are built in months by volunteers. The point is which practices from industry are cheap to adopt. Highlight the right-hand column items that cost little: measuring, documenting decisions, testing failure modes, designing for the pilot. Industrial systems often use fibre-optic tethers with multiplexers carrying many HD streams, but they ALSO plan bandwidth, prioritise streams and test failures. The difference is discipline as much as budget.");
    table(s, [
      ["Aspect", "Typical student ROV", "Industrial (work-class / inspection) ROV", "Cheap to adopt?"],
      ["Tether", "Cat5/Cat6 Ethernet, often 100 Mb/s", "Fibre optic + multiplexers, Gb/s per fibre", "Measure what you have"],
      ["Cameras", "USB webcams or cheap IP cameras", "Dedicated subsea cameras, defined roles", "Give each camera a role"],
      ["Encoding", "Whatever the camera/library does by default", "Chosen codec, rate control and GOP per stream", { text: "Yes — configuration", color: HEX.teal, bold: true }],
      ["Bandwidth", "Reduce resolution until it works", "Budgeted with headroom, prioritised streams", { text: "Yes — a spreadsheet", color: HEX.teal, bold: true }],
      ["Latency", "“Feels OK”", "Specified and measured glass-to-glass", { text: "Yes — a phone photo", color: HEX.teal, bold: true }],
      ["Failures", "Discovered on mission day", "Tested: camera loss, link loss, overload", { text: "Yes — test plan", color: HEX.teal, bold: true }],
      ["Pilot interface", "Built by developers for developers", "Designed and validated with pilots", { text: "Yes — usability test", color: HEX.teal, bold: true }],
    ], 0.6, 1.75, 12.1, [1.7, 3.4, 4.3, 2.7], { fontSize: 13, rowH: 0.56 });
  }
  // ---------------------------------------------------------------- 9 What we know
  {
    const s = content("Underwater video", "Honesty about uncertainty", "What we know — and what we still need to find out",
      "This slide models the behaviour we want from students: separating facts, assumptions and hypotheses. The USB-vs-IP contradiction is real in the brief I received — ask the team which it is. If it is USB cameras into a hub, the bottleneck may be the USB bus, not the tether. If it is IP cameras into a switch, the cameras probably already encode H.264. Hand out the questionnaire (Workshop_Design §6.5) if not done before the session.");
    const colsDef = [
      ["CONFIRMED", col.teal, ["Jetson Nano or Raspberry Pi 5 onboard", "Up to 8 cameras", "Ethernet tether to a surface laptop", "Web app for video + control (PID, RC config)", "Resolution was reduced to fit bandwidth", "Cameras appear to stream continuously"]],
      ["UNCLEAR", col.amber, ["USB cameras via a hub… or IP cameras via a switch?", "Which board flies: Jetson Nano or Jetson ORIN Nano?", "Tether link speed: 100 Mb/s or 1 Gb/s?", "Streaming software and protocol to the browser"]],
      ["HYPOTHESES TO TEST", col.violet, ["The bottleneck may be USB, CPU or decoding — not the tether", "Streams may be MJPEG (5–10× less efficient than H.264)", "Latency may be dominated by buffering", "Unwatched cameras still consume full bandwidth"]],
    ];
    colsDef.forEach(([head, c, list], i) => {
      const x = 0.6 + i * 4.1; box(s, x, 1.75, 3.85, 4.9, { fill: col.card });
      pill(s, head, x + 0.25, 1.95, 2.6, c);
      bullets(s, list, x + 0.25, 2.5, 3.4, 4.0, { fontSize: 14, gap: 8 });
    });
  }
  // ---------------------------------------------------------------- 10 Architectures A/B/C
  {
    const s = content("Underwater video", "Where does encoding happen?", "Three possible architectures",
      "Draw these on the whiteboard as well. A: IP cameras encode H.264/H.265 themselves; the switch and SBC just forward packets. B: USB cameras send raw YUYV or MJPEG over USB to the SBC, which encodes — the SBC's encoder (hardware on Jetson Nano, CPU on Pi 5) is the bottleneck. C: the SBC receives encoded streams and forwards, remuxes, or transcodes them (e.g. to WebRTC for the browser). Transcoding costs a full decode + encode per stream. Ask: 'Which one are we? How would you prove it?' Answer: ffprobe the stream, lsusb, v4l2-ctl --list-formats-ext, check the camera's web page.");
    const rows = [
      ["A", "Camera encodes", [["IP camera", "sensor + H.264 encoder"], ["Switch", "forwards packets"], ["SBC (optional)", "relay / control only"], ["Tether", "encoded streams"], ["Laptop", "decode + display"]], col.cyan],
      ["B", "SBC encodes", [["USB camera", "raw YUYV / MJPEG"], ["USB hub", "shared USB bus!"], ["SBC encoder", "HW (Nano) or CPU (Pi 5)"], ["Tether", "encoded streams"], ["Laptop", "decode + display"]], col.teal],
      ["C", "SBC forwards / transcodes", [["Camera", "already encoded"], ["SBC", "remux · relay · transcode?"], ["Media server", "RTSP → WebRTC"], ["Tether", "re-packaged streams"], ["Browser", "decode + display"]], col.violet],
    ];
    rows.forEach(([l, name, steps, c], i) => {
      const y = 1.75 + i * 1.62;
      s.addShape(pres.shapes.OVAL, { x: 0.6, y: y + 0.18, w: 0.75, h: 0.75, fill: { color: c, transparency: 75 }, line: { color: c, width: 1.5 }, objectName: `arch-${l}` });
      text(s, l, { x: 0.6, y: y + 0.18, w: 0.75, h: 0.75, fontSize: 24, bold: true, align: "center", valign: "middle" });
      text(s, name, { x: 1.5, y: y + 0.3, w: 1.9, h: 0.6, fontSize: 15, bold: true, color: c, valign: "middle" });
      flow(s, steps.map(([t, sub]) => ({ title: t, sub })), 3.5, y, 9.2, 1.15, { titleSize: 13, subSize: 11, gap: 0.3, arrowColor: c });
    });
  }
  await require("./deck_part_new").usbVsIp(ctx);
  // ---------------------------------------------------------------- 11 Following a frame
  {
    const s = content("Underwater video", "Following a frame", "From photons to the pilot's eyes",
      "Walk the pipeline left to right, and ask at each box: 'where does this run on OUR system?' Stress three things: (1) encoding happens where the encoder is — camera or SBC; (2) the network section is often NOT the biggest delay; buffers are; (3) the browser decodes and renders — a weak topside laptop decoding 8 streams can be the bottleneck. Each stage adds latency; we'll measure them in Experiment 9.");
    flow(s, [
      { title: "Capture", sub: "exposure, sensor readout, driver buffers" },
      { title: "Encode", sub: "camera or SBC; may hold frames back" },
      { title: "Packetize", sub: "RTP / MPEG-TS / HTTP chunks" },
      { title: "Network", sub: "switch → tether → laptop; queues!" },
      { title: "Buffer", sub: "jitter buffer, player cache" },
      { title: "Decode", sub: "browser / GPU / CPU" },
      { title: "Render", sub: "compositor + monitor refresh" },
    ], 0.6, 2.0, 12.1, 1.75, { titleSize: 14, subSize: 11, gap: 0.28 });
    const facts = [
      ["Where is it encoded?", "In the camera (IP / H.264 UVC) or on the SBC. Find out with ffprobe and v4l2-ctl."],
      ["Where is it decoded?", "On the topside laptop — in the browser or a native player. 8 streams = 8 decoders."],
      ["Where does latency hide?", "Usually in encoder lookahead and receiver buffers, rarely in the cable."],
    ];
    for (let i = 0; i < 3; i++) await card(s, 0.6 + i * 4.1, 4.2, 3.85, 2.2, { icon: [fi.FiCamera, fi.FiMonitor, fi.FiClock][i], title: facts[i][0], body: facts[i][1], titleSize: 15 });
  }
  // ---------------------------------------------------------------- 12 Codec vs container vs protocol
  {
    const s = content("Underwater video", "Three different words", "Codec ≠ container ≠ transport protocol",
      "This confusion is extremely common — 'we stream in MP4' or 'we use RTSP as our codec'. Use the parcel analogy: the codec is how you folded the clothes to make them small; the container is the box with a label of what's inside and when; the transport is the delivery service. You can put H.264 into MP4, MPEG-TS, or RTP; you can carry MPEG-TS over UDP, SRT or HTTP. RTSP is a control protocol (play/pause/setup) — the video itself usually travels over RTP.");
    const layers = [
      ["Codec", "How pixels are compressed", "H.264 · H.265 · MJPEG · AV1 · VP8/VP9", col.cyan, "the folded clothes"],
      ["Container / payload format", "How compressed frames are packaged with timing", "MP4 · MKV · MPEG-TS · RTP payload (RFC 6184)", col.teal, "the labelled box"],
      ["Streaming / control protocol", "How a session is set up and media is delivered", "RTSP (control) · RTP · WebRTC · HLS · HTTP-MJPEG · SRT", col.blue, "the delivery service"],
      ["Transport", "How packets move", "UDP (fast, may lose) · TCP (reliable, may stall)", col.violet, "the road"],
      ["Network / link", "Addresses and the physical cable", "IP · Ethernet · the tether", col.muted, "the ground"],
    ];
    layers.forEach(([a, b, c, colr, an], i) => {
      const y = 1.75 + i * 0.97; const inset = i * 0.18;
      box(s, 0.6 + inset, y, 8.6 - 2 * inset, 0.82, { fill: col.card, line: colr });
      text(s, a, { x: 0.85 + inset, y: y + 0.06, w: 3.6, h: 0.36, fontSize: 15, bold: true, color: colr });
      text(s, b, { x: 0.85 + inset, y: y + 0.42, w: 3.75 - inset, h: 0.36, fontSize: 11, color: col.muted });
      text(s, c, { x: 4.75, y: y + 0.06, w: 4.3 - 2 * inset, h: 0.72, fontSize: 13, valign: "middle" });
      text(s, an, { x: 9.5, y: y + 0.2, w: 3.2, h: 0.42, fontSize: 14, italic: true, color: col.muted, valign: "middle" });
    });
    text(s, "The parcel analogy →", { x: 9.5, y: 1.4, w: 3.2, h: 0.32, fontSize: 12, bold: true, color: col.cyan });
  }

  // ================================================================ SECTION 2 Bandwidth
  section("Bandwidth", "02", "Bandwidth engineering", "Where the bits go — and how to know if they fit", D.img.section2,
    "Transition: now that we know the pipeline, let's count bits. This is the most important quantitative skill of the day.");
  // ---------------------------------------------------------------- 14 Formula
  {
    const s = content("Bandwidth", "Counting bits", "Raw bandwidth = pixels × bits × frames",
      "Write the formula on the board and compute 1080p30 RGB together: 1920 × 1080 = 2,073,600 pixels; × 24 bits = 49.8 Mbit per frame; × 30 = 1.49 Gbit/s. Pause on that number: one camera, uncompressed, is bigger than gigabit Ethernet. Explain bpp per pixel format: RGB24 = 24, YUYV 4:2:2 = 16 (what USB webcams send raw), NV12/YUV420 = 12. Use decimal units for networks: 1 Mb/s = 10^6 bit/s.");
    box(s, 0.6, 1.75, 12.1, 1.35, { fill: col.card });
    rich(s, [{ text: "R", bold: true, fontSize: 34, color: col.cyan, nl: false }, { text: "raw", fontSize: 18, color: col.cyan, nl: false, subscript: true },
      { text: "  =  W × H  ×  bpp  ×  f", fontSize: 34, bold: true, nl: false }, { text: "      [bit/s]", fontSize: 18, color: col.muted }], 1.0, 1.95, 11.3, 1.0, { valign: "middle", fontFace: "Arial" });
    const terms = [["W × H", "pixels per frame", "1920 × 1080 = 2.07 M"], ["bpp", "bits per pixel (pixel format)", "RGB 24 · YUYV 16 · NV12 12"], ["f", "frames per second", "30"]];
    terms.forEach(([a, b, c], i) => {
      const x = 0.6 + i * 4.1; box(s, x, 3.35, 3.85, 1.4, { fill: col.card });
      text(s, a, { x: x + 0.25, y: 3.45, w: 3.4, h: 0.5, fontSize: 22, bold: true, color: col.cyan, fontFace: "Arial" });
      text(s, b, { x: x + 0.25, y: 3.95, w: 3.4, h: 0.35, fontSize: 14 });
      text(s, c, { x: x + 0.25, y: 4.3, w: 3.4, h: 0.35, fontSize: 13, color: col.muted });
    });
    stat(s, 0.6, 5.0, 4.0, "1.49 Gb/s", "one 1080p30 camera, RGB24, uncompressed", col.amber, { size: 44, vh: 0.8 });
    stat(s, 4.7, 5.0, 4.0, "11.9 Gb/s", "eight of them", col.rose, { size: 44, vh: 0.8 });
    stat(s, 8.8, 5.0, 4.0, "0.1–1 Gb/s", "what an Ethernet tether carries", col.teal, { size: 44, vh: 0.8 });
  }
  // ---------------------------------------------------------------- 15 Raw chart
  {
    const s = content("Bandwidth", "Experiment 1", "Raw video does not fit any link you own",
      "Native chart, log scale. The three bars per resolution are the pixel formats. Compare with 100 Mb/s (Fast Ethernet), ~197 Mb/s (max isochronous for one USB 2.0 camera) and 480 Mb/s (USB 2.0 signalling, shared by every device on that bus). Key insight for USB cameras: uncompressed YUYV only fits USB 2.0 at about 640x480@30, which is why webcams switch to MJPEG at higher resolutions. With 3-4 USB cameras on one hub, cameras can fail to start because USB periodic bandwidth is reserved per camera.");
    const res = ["640×480", "1280×720", "1920×1080", "3840×2160"]; const px = [640 * 480, 1280 * 720, 1920 * 1080, 3840 * 2160];
    const series = [["RGB24", 24], ["YUYV 4:2:2", 16], ["NV12 4:2:0", 12]].map(([n, b]) => ({ name: n, labels: res, values: px.map((p) => Math.round(p * b * 30 / 1e6)) }));
    s.addChart(pres.charts.BAR, series, { x: 0.6, y: 1.7, w: 8.0, h: 5.0, barDir: "col", barGapWidthPct: 60, chartColors: SERIES.slice(0, 3),
      valAxisLogScaleBase: 10, valAxisMinVal: 10, valAxisMaxVal: 10000, showLegend: true, legendPos: "b", showTitle: true, title: "One camera at 30 FPS (Mb/s, log scale)",
      valAxisLabelFormatCode: "#,##0", ...chartBase(), objectName: "raw-bandwidth-chart" });
    const lines = [["100 Mb/s", "Fast Ethernet tether", col.amber], ["≈ 197 Mb/s", "max for one USB 2.0 UVC camera (isochronous)", col.violet], ["480 Mb/s", "USB 2.0 — shared by every device on the bus", col.blue], ["1,000 Mb/s", "Gigabit Ethernet", col.teal]];
    lines.forEach(([a, b, c], i) => {
      box(s, 8.9, 1.75 + i * 1.23, 3.8, 1.05, { fill: col.card });
      text(s, a, { x: 9.1, y: 1.82 + i * 1.23, w: 3.4, h: 0.45, fontSize: 20, bold: true, color: c, fontFace: "Arial" });
      text(s, b, { x: 9.1, y: 2.27 + i * 1.23, w: 3.4, h: 0.48, fontSize: 12, color: col.muted });
    });
  }
  await require("./deck_part_new").egyptCost(ctx);
  // ---------------------------------------------------------------- 16 Activity 1
  {
    const s = content("Bandwidth", "Activity 1 · 15 minutes", "Estimate the bandwidth",
      "Teams of 3–5. Hand out the worksheet from Activity_Instructions.md. Each team gets a different configuration card. They must compute raw and compressed bandwidth, add overhead, compare against 70% of the link and give a verdict. Scoring: 4 points correct arithmetic, 3 points correct headroom verdict, 3 points for naming what they would measure to confirm. Reveal answers using the notebook's Experiment 7 simulator.");
    const cards = [["Card A", "8 × USB YUYV 640×480@30 on one USB 2.0 hub"], ["Card B", "8 × MJPEG 1280×720@30 over a 100 Mb/s tether"], ["Card C", "8 × H.264 1080p30 at 4 Mb/s over 100 Mb/s"], ["Card D", "1 × H.264 1080p30 @ 6 Mb/s + 7 × 640×360@15 @ 0.5 Mb/s"]];
    cards.forEach(([a, b], i) => { const x = 0.6 + (i % 2) * 3.45, y = 1.75 + Math.floor(i / 2) * 1.6; box(s, x, y, 3.25, 1.4, { fill: col.card, line: HEX.cyan });
      text(s, a, { x: x + 0.2, y: y + 0.12, w: 2.9, h: 0.35, fontSize: 15, bold: true, color: col.cyan }); text(s, b, { x: x + 0.2, y: y + 0.5, w: 2.9, h: 0.8, fontSize: 14 }); });
    box(s, 7.75, 1.75, 4.95, 4.9, { fill: col.card });
    text(s, "For your card, compute:", { x: 8.0, y: 1.95, w: 4.5, h: 0.4, fontSize: 17, bold: true });
    bullets(s, ["Raw bandwidth per camera and total", "Compressed total (use the given bitrate or bpp)", "On-the-wire total: + 5 % (RTP/UDP) or + 7 % (MPEG-TS)", "Utilisation vs 70 % of the link — verdict: OK / tight / over", "One measurement that would confirm your answer"], 8.0, 2.45, 4.5, 3.2, { fontSize: 15, gap: 8 });
    text(s, "Scoring: arithmetic 4 · verdict 3 · measurement 3", { x: 8.0, y: 5.9, w: 4.5, h: 0.4, fontSize: 13, color: col.amber, bold: true });
    text(s, "Hint: R = W × H × bpp × f.  YUYV = 16 bpp.  USB 2.0 periodic budget ≈ 80 % of 480 Mb/s.", { x: 0.6, y: 5.15, w: 6.8, h: 0.9, fontSize: 14, color: col.muted, italic: true });
  }
  // ---------------------------------------------------------------- 17 Why compression
  {
    const s = content("Bandwidth", "Measured in the notebook", "Compression is the core of the system",
      `These are measured numbers from the notebook on the 1280x720 synthetic clip. Raw 4:2:0 is ${D.rawMbps} Mb/s. x264 at CRF 23 compresses it about ${D.e2.h264.ratio}:1. Then make the point that matters for the team: switching codec typically buys far more than halving resolution (halving both dimensions only divides raw pixels by 4). Caveat: compression ratios depend on content — noisy, turbid footage compresses less. Measure with your own footage.`);
    stat(s, 0.6, 1.8, 3.8, `${D.rawMbps} Mb/s`, "raw 1280×720@30 (4:2:0)", col.rose, { size: 46 });
    stat(s, 4.6, 1.8, 3.8, `${D.e2.mjpeg.mbps} Mb/s`, `MJPEG — ${D.e2.mjpeg.ratio}:1`, col.amber, { size: 46 });
    stat(s, 8.6, 1.8, 4.1, `${D.e2.h264.mbps} Mb/s`, `H.264 CRF 23 — ${D.e2.h264.ratio}:1`, col.teal, { size: 46 });
    box(s, 0.6, 4.0, 12.1, 2.55, { fill: col.card });
    text(s, "Halving resolution vs changing codec", { x: 0.9, y: 4.15, w: 11.5, h: 0.45, fontSize: 18, bold: true });
    bullets(s, ["Halving width and height divides the pixels by 4 — and throws away detail the pilot may need.",
      `Moving from MJPEG to H.264 at similar quality saved ≈ ${D.eqq.mjpegVsH264}× in our measurement — with no loss of resolution.`,
      "Real gains come from: a better codec, capped rate control, fewer active full-quality streams (substreams)."], 0.9, 4.7, 11.5, 1.8, { fontSize: 16, gap: 8 });
  }
  // ---------------------------------------------------------------- 18 Bitrate vs bandwidth vs throughput, overhead & headroom
  {
    const s = content("Bandwidth", "Words that get mixed up", "Bitrate, bandwidth, throughput, headroom",
      "Bitrate is what the stream produces; bandwidth/capacity is what the link could carry; throughput is what actually got delivered (measure with iperf3). Overhead: Ethernet adds 38 bytes per frame on the wire, IP 20, UDP 8, RTP 12 — about 5% at 1500 MTU. Headroom: plan ≤ 70% sustained because I-frame bursts, retransmissions, control traffic. Full duplex: modern switched Ethernet sends both directions simultaneously; hubs (true Ethernet hubs) are half duplex and collide — check you don't have one. Packet loss on UDP corrupts video; on TCP it causes retransmission and growing delay.");
    const defs = [["Bitrate", "bits per second the encoder produces", "e.g. 4 Mb/s per camera"], ["Bandwidth / capacity", "what the link could carry", "100 or 1000 Mb/s (negotiated)"], ["Throughput", "what is actually delivered", "measure with iperf3 — e.g. 94 Mb/s"], ["Headroom", "capacity you leave unused on purpose", "≥ 30 % for bursts, control, telemetry"]];
    defs.forEach(([a, b, c], i) => { const y = 1.75 + i * 1.18; box(s, 0.6, y, 6.2, 1.02, { fill: col.card });
      text(s, a, { x: 0.85, y: y + 0.1, w: 5.8, h: 0.4, fontSize: 17, bold: true, color: col.cyan }); text(s, `${b} · ${c}`, { x: 0.85, y: y + 0.5, w: 5.8, h: 0.42, fontSize: 14, color: col.muted }); });
    box(s, 7.1, 1.75, 5.6, 4.55, { fill: col.card });
    text(s, "What one RTP packet costs on the wire", { x: 7.35, y: 1.9, w: 5.2, h: 0.4, fontSize: 16, bold: true });
    const parts = [["Ethernet framing + gap", 38, HEX.muted], ["IPv4", 20, HEX.violet], ["UDP", 8, HEX.blue], ["RTP", 12, HEX.teal], ["Video payload", 1460, HEX.cyan]];
    parts.forEach(([n, b, c], i) => { const y = 2.45 + i * 0.52;
      s.addShape(pres.shapes.RECTANGLE, { x: 7.35, y, w: Math.max(0.12, (b / 1538) * 3.4), h: 0.36, fill: { color: c }, line: { type: "none" }, objectName: `pkt-${i}` });
      text(s, `${n} · ${b} B`, { x: 7.35 + Math.max(0.12, (b / 1538) * 3.4) + 0.12, y, w: 3.6, h: 0.36, fontSize: 13, valign: "middle" }); });
    text(s, "1538 / 1460 ≈ 1.053 → ~5 % overhead. MPEG-TS over UDP ≈ 7 %.", { x: 7.35, y: 5.15, w: 5.2, h: 0.8, fontSize: 14, color: col.amber, bold: true });
    text(s, "Check: ethtool eth0 (speed, duplex) · iperf3 -c <rov> -u -b 80M (throughput, loss, jitter)", { x: 0.6, y: 6.5, w: 12.1, h: 0.35, fontSize: 13, color: col.muted, fontFace: "Courier New" });
  }

  // ================================================================ SECTION 3 Encoding
  section("Encoding", "03", "How video encoding works", "From first principles to the knobs you can turn", D.img.section3,
    "Transition: compression is the core — so let's open the box and see how an encoder throws away 99% of the bits without the pilot noticing.");
  // ---------------------------------------------------------------- 20 Pipeline
  {
    const s = content("Encoding", "The hybrid video encoder", "Four ideas behind H.264, H.265 and AV1",
      "Every modern codec (H.264, H.265, AV1) is a 'hybrid' codec built from these four steps. Prediction removes redundancy (spatial within a frame, temporal between frames). Transform turns the remaining error into frequency coefficients (DCT-like). Quantization is the ONLY lossy step — it divides coefficients and rounds; the quantizer is what CRF and bitrate control. Entropy coding (CAVLC/CABAC in H.264) packs the result with no further loss. Rate control decides the quantizer per frame/block to hit a quality or bitrate target.");
    flow(s, [
      { title: "1 · Predict", sub: "guess each block from neighbours (intra) or earlier frames (inter)", color: col.card },
      { title: "2 · Transform", sub: "turn the prediction error into frequencies (DCT-like)", color: col.card },
      { title: "3 · Quantize", sub: "divide & round — the ONLY lossy step", color: col.card, line: HEX.amber },
      { title: "4 · Entropy-code", sub: "pack symbols tightly (CABAC / CAVLC)", color: col.card },
    ], 0.6, 1.85, 12.1, 1.9, { titleSize: 17, subSize: 13, gap: 0.45 });
    box(s, 0.6, 4.15, 5.9, 2.4, { fill: col.card });
    text(s, "Rate control sits on top", { x: 0.85, y: 4.3, w: 5.4, h: 0.4, fontSize: 17, bold: true, color: col.cyan });
    text(s, "It chooses the quantizer for every frame and block, to hit either a quality (CRF) or a bitrate (CBR/VBR + VBV buffer). This is the knob you turn most.", { x: 0.85, y: 4.8, w: 5.4, h: 1.6, fontSize: 15, color: col.muted });
    box(s, 6.8, 4.15, 5.9, 2.4, { fill: col.card });
    text(s, "The decoder runs the same predictions", { x: 7.05, y: 4.3, w: 5.4, h: 0.4, fontSize: 17, bold: true, color: col.cyan });
    text(s, "The encoder only sends instructions + corrections. If a reference frame is lost, every frame predicted from it is wrong — until the next I-frame.", { x: 7.05, y: 4.8, w: 5.4, h: 1.6, fontSize: 15, color: col.muted });
  }
  // ---------------------------------------------------------------- 21 YUV & chroma
  {
    const s = content("Encoding", "Digital video fundamentals", "YUV and chroma subsampling: free 50 %",
      "Human vision resolves brightness detail much better than colour detail. YUV separates luma (Y) from two chroma components (U/V or Cb/Cr). 4:2:0 keeps one chroma sample per 2x2 pixel block: 8 bits Y + (8+8)/4 = 12 bits per pixel vs 24 for RGB. NV12 and YUV420P are both 4:2:0 — NV12 interleaves U and V in one plane (common for hardware encoders), YUV420P stores three planes. Almost all hardware decoders and browsers expect 4:2:0, 8-bit.");
    const grids = [["4:4:4", "every pixel has its own colour", 24, 1], ["4:2:2", "colour shared by 2 pixels (horizontal)", 16, 2], ["4:2:0", "colour shared by a 2×2 block", 12, 4]];
    grids.forEach(([name, desc, bpp, share], gi) => {
      const x0 = 0.6 + gi * 4.1; box(s, x0, 1.75, 3.85, 4.1, { fill: col.card });
      text(s, name, { x: x0 + 0.25, y: 1.88, w: 2, h: 0.5, fontSize: 24, bold: true, color: col.cyan, fontFace: "Arial" });
      pill(s, `${bpp} bpp`, x0 + 2.55, 1.95, 1.05, col.teal);
      const cell = 0.5, gx = x0 + 0.92, gy = 2.6;
      for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++) {
        s.addShape(pres.shapes.RECTANGLE, { x: gx + c * cell, y: gy + r * cell, w: cell, h: cell, fill: { color: HEX.cardHi }, line: { color: HEX.grid, width: 0.75 }, objectName: `px-${gi}-${r}-${c}` });
        const isChroma = share === 1 || (share === 2 && c % 2 === 0) || (share === 4 && c % 2 === 0 && r % 2 === 0);
        if (isChroma) s.addShape(pres.shapes.OVAL, { x: gx + c * cell + 0.13, y: gy + r * cell + 0.13, w: 0.24, h: 0.24, fill: { color: HEX.amber }, line: { type: "none" }, objectName: `cs-${gi}-${r}-${c}` });
      }
      text(s, desc, { x: x0 + 0.25, y: 4.75, w: 3.4, h: 0.9, fontSize: 14, color: col.muted });
    });
    text(s, "Squares = luma (Y) samples, always full resolution.   Dots = one chroma (U + V) pair.", { x: 0.6, y: 6.05, w: 12.1, h: 0.4, fontSize: 14, color: col.muted, italic: true });
  }
  // ---------------------------------------------------------------- 22 Redundancy & motion
  {
    const s = content("Encoding", "Prediction", "Spatial and temporal redundancy",
      "Blocks: H.264 uses 16x16 macroblocks (split down to 4x4); H.265 uses coding tree units up to 64x64 that split recursively — big flat areas like open water become one cheap block. Slices are independently decodable chunks of a frame — useful for error resilience and low-latency threading. Motion estimation searches the reference frame for the best match; motion compensation sends a vector plus the residual. Underwater: particles, noise and caustics are hard to predict → the residual is large → more bits. That is why our synthetic clip costs more than a clean test pattern.");
    // Frame N-1 and frame N with a block and a motion vector
    const fx = [0.6, 4.0];
    fx.forEach((x, i) => {
      box(s, x, 1.9, 3.0, 2.2, { fill: HEX.cardHi, r: 0.03 });
      for (let k = 1; k < 6; k++) s.addShape(pres.shapes.LINE, { x: x + k * 0.5, y: 1.9, w: 0, h: 2.2, line: { color: HEX.grid, width: 0.5 }, objectName: `gv-${i}-${k}` });
      for (let k = 1; k < 5; k++) s.addShape(pres.shapes.LINE, { x, y: 1.9 + k * 0.44, w: 3.0, h: 0, line: { color: HEX.grid, width: 0.5 }, objectName: `gh-${i}-${k}` });
      text(s, i ? "Frame N (being coded)" : "Frame N − 1 (reference)", { x, y: 4.15, w: 3.0, h: 0.35, fontSize: 13, color: col.muted, align: "center" });
    });
    s.addShape(pres.shapes.RECTANGLE, { x: 1.1, y: 2.34, w: 0.5, h: 0.44, fill: { color: HEX.amber, transparency: 30 }, line: { color: HEX.amber, width: 1.5 }, objectName: "ref-block" });
    s.addShape(pres.shapes.RECTANGLE, { x: 5.5, y: 2.78, w: 0.5, h: 0.44, fill: { color: HEX.cyan, transparency: 30 }, line: { color: HEX.cyan, width: 1.5 }, objectName: "cur-block" });
    arrow(s, 5.5, 3.0, 1.6, 2.56, col.amber, { dash: "dash" });
    text(s, "motion vector (−8, −2) + small residual", { x: 1.7, y: 3.15, w: 3.5, h: 0.35, fontSize: 12, color: col.amber });
    const kinds = [["Spatial redundancy", "Neighbouring pixels are similar → predict a block from its neighbours (intra prediction)."], ["Temporal redundancy", "Consecutive frames are similar → send a motion vector + correction (inter prediction)."], ["Blocks", "H.264: 16×16 macroblocks. H.265: coding tree units up to 64×64 — large flat water = one cheap block."], ["Slices", "Independently decodable parts of a frame: error resilience and low-latency threading."]];
    kinds.forEach(([a, b], i) => { text(s, a, { x: 7.6, y: 1.8 + i * 1.18, w: 5.1, h: 0.38, fontSize: 16, bold: true, color: col.cyan }); text(s, b, { x: 7.6, y: 2.17 + i * 1.18, w: 5.1, h: 0.75, fontSize: 14, color: col.muted }); });
    box(s, 0.6, 4.75, 6.4, 1.75, { fill: col.card });
    text(s, "Why underwater video costs more bits", { x: 0.85, y: 4.88, w: 6, h: 0.4, fontSize: 16, bold: true });
    text(s, "Particles, sensor noise and moving caustics cannot be predicted from the previous frame — so the residual stays large. Good lighting and lower gain save bandwidth.", { x: 0.85, y: 5.3, w: 6, h: 1.1, fontSize: 14, color: col.muted });
  }
  // ---------------------------------------------------------------- 23 I/P/B & GOP
  {
    const s = content("Encoding", "Frame types", "I-frames, P-frames, B-frames and the GOP",
      `I-frames are self-contained (big); P-frames reference earlier frames (small); B-frames also reference a future frame, so the encoder must wait for it — that adds latency, which is why live low-latency streams disable B-frames. In our measurement (GOP 30, CRF 23) an average I-frame was ${D.e5.iKB} kB vs ${D.e5.pKB} kB for a P-frame — about ${D.e5.ipRatio}x. The GOP is the run from one I-frame to the next; shorter GOP = faster join and recovery, more bits.`);
    const seq = ["I", "B", "B", "P", "B", "B", "P", "B", "B", "P", "B", "B", "I"];
    const cw = 0.8, x0 = 0.95;
    seq.forEach((t, i) => {
      const h = t === "I" ? 1.6 : t === "P" ? 0.75 : 0.45; const c = t === "I" ? HEX.amber : t === "P" ? HEX.blue : HEX.teal;
      s.addShape(pres.shapes.RECTANGLE, { x: x0 + i * (cw + 0.12), y: 3.6 - h, w: cw, h, fill: { color: c }, line: { type: "none" }, objectName: `ft-${i}` });
      text(s, t, { x: x0 + i * (cw + 0.12), y: 3.68, w: cw, h: 0.35, fontSize: 15, bold: true, align: "center" });
    });
    text(s, "one GOP", { x: x0, y: 4.05, w: 12 * (cw + 0.12), h: 0.35, fontSize: 13, color: col.amber, align: "center" });
    arrow(s, x0 + 5.2, 4.22, x0, 4.22, col.amber); arrow(s, x0 + 5.9, 4.22, x0 + 12 * (cw + 0.12), 4.22, col.amber);
    text(s, "bar height ≈ relative size", { x: 9.6, y: 1.75, w: 3.1, h: 0.3, fontSize: 11, color: col.muted, italic: true, align: "right" });
    const tiles = [["I-frame", "Intra-only. Decoder can start here. Big.", col.amber], ["P-frame", "Predicted from earlier frames. Small.", col.blue], ["B-frame", "Also uses a FUTURE frame → encoder waits → adds latency.", col.teal]];
    tiles.forEach(([a, b, c], i) => { const x = 0.6 + i * 4.1; box(s, x, 4.65, 3.85, 1.85, { fill: col.card });
      text(s, a, { x: x + 0.25, y: 4.8, w: 3.4, h: 0.4, fontSize: 17, bold: true, color: c }); text(s, b, { x: x + 0.25, y: 5.25, w: 3.4, h: 1.1, fontSize: 14, color: col.muted }); });
  }
  // ---------------------------------------------------------------- 24 CRF vs bitrate
  {
    const s = content("Encoding", "Experiments 3 & 6", "Quality-based vs bitrate-based encoding",
      "CRF holds quality roughly constant and lets bitrate float: great for recording, dangerous for a fixed-capacity tether because bitrate spikes when the scene gets complex (sediment cloud!). Target bitrate with a VBV buffer (maxrate + bufsize) caps the peaks and lets quality float — right for live streams. Chart: bitrate each codec needs for the same SSIM at two operating points, measured in the notebook (metric-neutral tuning). The curves cross — at the tight-tether point AV1 needs about a quarter of H.264's bits while H.265 is roughly level with H.264; at the high-quality end x264 holds up best on this synthetic clip. Lesson: 'which codec is best' depends on the operating point and the content; measure with your footage.");
    const eq = D.eqq.rows;
    s.addChart(pres.charts.BAR, [
      { name: `tight tether (SSIM ${D.eqq.low})`, labels: eq.map((r) => r.codec), values: eq.map((r) => r.low) },
      { name: `high quality (SSIM ${D.eqq.target})`, labels: eq.map((r) => r.codec), values: eq.map((r) => r.high) }], {
      x: 0.6, y: 1.7, w: 6.4, h: 4.9, barDir: "bar", catAxisOrientation: "maxMin", chartColors: [SERIES[0], SERIES[1]], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0",
      showLegend: true, legendPos: "b", showTitle: true, title: "Mb/s needed for equal quality — two operating points", valAxisMinVal: 0, barGapWidthPct: 40, ...chartBase(), objectName: "equal-quality-chart" });
    const modes = [["CRF (quality-based)", "-crf 23", "Constant quality, bitrate floats with content. Use for recording.", col.teal], ["Target bitrate + VBV", "-b:v 4M -maxrate 4M -bufsize 2M", "Bitrate capped, quality floats. Use for the live tether.", col.cyan]];
    modes.forEach(([a, cmd, b, c], i) => { const y = 1.75 + i * 2.1; box(s, 7.3, y, 5.4, 1.9, { fill: col.card });
      text(s, a, { x: 7.55, y: y + 0.12, w: 5, h: 0.4, fontSize: 17, bold: true, color: c }); text(s, cmd, { x: 7.55, y: y + 0.55, w: 5, h: 0.35, fontSize: 13, fontFace: "Courier New", color: col.amber });
      text(s, b, { x: 7.55, y: y + 0.95, w: 5, h: 0.8, fontSize: 14, color: col.muted }); });
    text(s, `Measured: CRF 23 averaged ${D.crf23.avg} Mb/s but peaked at ${D.crf23.peak} Mb/s in 200 ms windows; the VBV encode at the same average peaked at ${D.crf23.vbvPeak} Mb/s.`, { x: 7.3, y: 6.0, w: 5.4, h: 0.75, fontSize: 13, color: col.amber });
  }
  // ---------------------------------------------------------------- 25 Codecs compared
  {
    const s = content("Encoding", "Choosing a codec", "H.264 vs H.265 vs MJPEG vs AV1",
      "Don't say 'X is better'. Each codec is right somewhere. MJPEG: trivial decoding, no inter-frame error propagation, lowest latency — but several times the bitrate; many USB webcams produce it natively. H.264: universal — every browser, every hardware decoder, Jetson Nano encodes it in hardware. H.265: ~25–50% better compression at similar quality on typical content (our measurement in the notebook may differ), Jetson Nano encodes it in hardware, Pi 5 decodes it in hardware, but browser support is uneven. AV1: best efficiency, very expensive to encode in software, no hardware encoder on either board — not for the ROV today.");
    table(s, [
      ["", "MJPEG", "H.264 / AVC", "H.265 / HEVC", "AV1"],
      ["Compression", "low (intra-only)", "good", "better", "best"],
      ["Encode cost (software)", "very low", "low → high (preset)", "high", "very high"],
      ["Latency", "lowest (no inter-frame)", "low with zerolatency", "low (tuned)", "harder to keep low"],
      ["Loss resilience", "excellent (frames independent)", "needs short GOP / intra refresh", "same as H.264", "same"],
      ["Jetson Nano HW", "JPEG decode/encode engine", "✔ encode + decode", "✔ encode + decode", "✘"],
      ["Raspberry Pi 5 HW", "✘ (software)", "✘ software encode & decode", "✔ decode only", "✘"],
      ["Browser support", "universal (<img>)", "universal", "partial / platform-dependent", "modern browsers"],
      ["Good ROV use", "a simple aux camera", "default for live streams", "if HW encode + client decode", "recording/archive later"],
    ], 0.6, 1.75, 12.1, [2.4, 2.3, 2.5, 2.5, 2.4], { fontSize: 12.5, rowH: 0.52 });
  }
  // ---------------------------------------------------------------- 26 Parameters & presets
  {
    const s = content("Encoding", "Experiment 4", "Encoder parameters: what each knob does",
      "Go through the table quickly, then the preset chart from the notebook (measured on this machine — the shape matters, not the absolute numbers). Slower presets search harder and save bits, with diminishing returns after medium/slow; for live encoding on an SBC without a hardware encoder you'll live at ultrafast–veryfast with tune zerolatency. Profiles and levels matter for compatibility: Constrained Baseline/Main/High, and level limits resolution x frame rate x bitrate the decoder must support.");
    table(s, [
      ["Knob", "Bandwidth", "Quality", "Latency", "CPU"],
      ["Bitrate ↑", "↑", "↑", "—", "—"],
      ["CRF ↓", "↑ (varies)", "↑", "—", "—"],
      ["Slower preset", "↓", "↑", "↑ (lookahead)", "↑↑"],
      ["GOP shorter", "↑", "↓ slightly", "faster join/recovery", "—"],
      ["B-frames on", "↓", "↑", "↑", "↑"],
      ["Lookahead ↑", "↓", "↑", "↑↑", "↑"],
      ["Resolution ↓", "↓", "↓ detail", "—", "↓"],
      ["Frame rate ↓", "↓", "motion judder", "↑ per frame", "↓"],
    ], 0.6, 1.75, 6.3, [1.7, 1.15, 1.15, 1.3, 1.0], { fontSize: 12.5, rowH: 0.5 });
    const pr = D.e4;
    s.addChart(pres.charts.BAR, [{ name: "CPU ms per frame", labels: pr.map((r) => r.preset), values: pr.map((r) => r.cpu) }], {
      x: 7.1, y: 1.7, w: 5.6, h: 2.5, barDir: "col", chartColors: [HEX.violet], showValue: false, showLegend: false, showTitle: true, title: "x264 CPU time per frame (ms) — this laptop",
      catAxisLabelRotate: -35, ...chartBase({ catAxisLabelFontSize: 10 }), objectName: "preset-cpu-chart" });
    s.addChart(pres.charts.BAR, [{ name: "Mb/s at CRF 23", labels: pr.map((r) => r.preset), values: pr.map((r) => r.mbps) }], {
      x: 7.1, y: 4.25, w: 5.6, h: 2.5, barDir: "col", chartColors: [HEX.cyan], showValue: false, showLegend: false, showTitle: true, title: "Bitrate at CRF 23 (Mb/s)",
      catAxisLabelRotate: -35, ...chartBase({ catAxisLabelFontSize: 10 }), objectName: "preset-bitrate-chart" });
  }
  // ---------------------------------------------------------------- 27 GOP & loss
  {
    const s = content("Encoding", "Experiment 5 · measured", "Packet loss: why GOP length matters on a tether",
      `We deleted ${D.e5.dropKB} kB of MPEG-TS (six UDP datagrams) at three different moments and decoded. Averaged over the three: GOP 150 stayed damaged about ${D.e5.loss[1].s} s (worst ${D.e5.loss[1].worst} s); GOP 30 about ${D.e5.loss[0].s} s; intra refresh ${D.e5.loss[2].s} s — within about one refresh period — and without any I-frame bitrate spikes. Note for GOP 150: the loss at 2.5 s happened to be rescued early by the camera cut at t = 4 s (an almost all-intra frame); the other losses lasted until the next I-frame at 5 s. Plan for the worst case. Also connects to camera switching: a player joining mid-GOP shows nothing until the next I-frame — 'camera switching takes 2 seconds' often means a 2-second GOP. TCP would not corrupt, it would stall and add delay instead.`);
    D.img.loss.forEach((p, i) => {
      s.addImage({ path: p, x: 0.6 + i * 4.1, y: 1.75, w: 3.85, h: 2.166, objectName: `loss-img-${i}`, altText: `Decoded frame 0.5 s after packet loss, ${D.e5.loss[i].name}` });
      text(s, D.e5.loss[i].name, { x: 0.6 + i * 4.1, y: 3.98, w: 3.85, h: 0.35, fontSize: 14, bold: true });
      text(s, `damaged ≈ ${D.e5.loss[i].s} s on average · worst ${D.e5.loss[i].worst} s`, { x: 0.6 + i * 4.1, y: 4.32, w: 3.85, h: 0.35, fontSize: 14, color: [col.teal, col.rose, col.amber][i] });
    });
    text(s, "Frames 0.5 s after a loss at t = 1.4 s. Durations: mean of three loss positions.", { x: 0.6, y: 4.7, w: 9, h: 0.3, fontSize: 11, italic: true, color: col.muted });
    box(s, 0.6, 5.15, 12.1, 1.4, { fill: col.card });
    bullets(s, ["Short GOP (0.5–1 s) or intra refresh for the live stream if you see any loss — and find the cause of the loss.", "Camera switch lag ≈ time to the next I-frame. Request a keyframe on switch, or keep substreams decoding."], 0.85, 5.3, 11.6, 1.2, { fontSize: 15, gap: 6 });
  }
  // ---------------------------------------------------------------- 28 Quality metrics + Activity 3
  {
    const s = content("Encoding", "Experiment 6 · Activity 3", "Measuring quality — and its limits",
      "PSNR is 10·log10(255²/MSE): cheap, but blind to perception (the notebook shows a harmless brightness shift scored worse than a blur that destroys detail). SSIM compares local luminance, contrast and structure — better correlated with humans. VMAF fuses features with a model trained on human scores for TV/film — best for entertainment, not validated for ROV piloting. Then run Activity 3: show 4–5 encodes blind (A–E) on the projector, teams rank them by quality and guess the bitrate; reveal the measured numbers. Points for closeness of ranking.");
    const m = [["PSNR", "10·log₁₀(255² / MSE)", "Cheap and simple. Every pixel error counts the same — blind to perception.", col.blue],
      ["SSIM", "luminance × contrast × structure", "Compares local structure. Much better at catching blur and blocking.", col.teal],
      ["VMAF", "ML fusion trained on human scores", "Best match to viewers for TV/film. Needs libvmaf. Not trained on ROV tasks.", col.violet]];
    m.forEach(([a, f, b, c], i) => { const y = 1.75 + i * 1.6; box(s, 0.6, y, 6.6, 1.42, { fill: col.card });
      text(s, a, { x: 0.85, y: y + 0.12, w: 1.6, h: 0.45, fontSize: 20, bold: true, color: c, fontFace: "Arial" }); text(s, f, { x: 2.5, y: y + 0.16, w: 4.5, h: 0.4, fontSize: 13, fontFace: "Courier New", color: col.amber });
      text(s, b, { x: 0.85, y: y + 0.62, w: 6.2, h: 0.75, fontSize: 14, color: col.muted }); });
    box(s, 7.5, 1.75, 5.2, 4.62, { fill: col.card, line: HEX.cyan });
    text(s, "Activity 3 · Compression Challenge", { x: 7.75, y: 1.9, w: 4.8, h: 0.4, fontSize: 17, bold: true, color: col.cyan });
    bullets(s, ["Five clips, labelled A–E, same scene", "Rank them by quality — blind", "Guess each bitrate", "Reveal: measured bitrate, PSNR, SSIM", "Discuss: did the metric agree with you? With the pilot?"], 7.75, 2.45, 4.7, 2.7, { fontSize: 15, gap: 7 });
    text(s, "Metrics compare settings. Pilots decide what is good enough.", { x: 7.75, y: 5.35, w: 4.7, h: 0.8, fontSize: 15, bold: true, color: col.amber });
  }

  // ================================================================ SECTION 4 Hardware & transport
  section("Hardware & transport", "04", "Hardware, protocols & latency", "What your silicon can do — and where the milliseconds go", D.img.section1,
    "Transition: we know how to compress. Now: who does the work, how do the bits travel, and how long does it all take?");
  // ---------------------------------------------------------------- 30 CPU vs HW
  {
    const s = content("Hardware & transport", "Who does the work?", "Software encoding vs hardware encoding",
      "A software encoder (x264, x265) runs on CPU cores: flexible, high quality per bit, but expensive. A hardware encoder is a dedicated block of silicon (NVIDIA calls it NVENC; the decoder NVDEC): almost free for the CPU, fixed capacity, fewer tuning knobs. Note: on Jetson the GPU (CUDA cores) is NOT what encodes — the separate encoder block does. Important: an encoder showing in 'ffmpeg -encoders' only means FFmpeg was compiled with it; always run a test encode. Thermal: an SBC in a sealed, warm enclosure throttles — measure inside the enclosure.");
    await card(s, 0.6, 1.75, 5.9, 3.2, { icon: fi.FiCpu, title: "Software (CPU) encoding", bullets: ["x264 / x265 / SVT-AV1 on general-purpose cores", "Best quality per bit, every knob available", "Cost scales with resolution × FPS × streams", "Competes with control software, web server, telemetry", "Heat → thermal throttling → dropped frames"] });
    await card(s, 6.8, 1.75, 5.9, 3.2, { icon: tb.TbCircuitResistor, title: "Hardware encoding", bullets: ["Dedicated encoder block (e.g. NVIDIA NVENC on Jetson)", "Near-zero CPU, predictable latency", "FIXED total capacity shared by all streams", "Fewer tuning options, vendor-specific APIs", "Memory bandwidth still shared with everything"] });
    box(s, 0.6, 5.2, 12.1, 1.35, { fill: col.card });
    rich(s, [{ text: "Listed ≠ working. ", bold: true, color: col.amber, nl: false }, { text: "On this laptop FFmpeg lists h264_nvenc, h264_qsv, h264_vaapi and h264_v4l2m2m — and every one failed a test encode (no GPU / device). Always run a 1-second test encode on the real machine." }], 0.85, 5.35, 11.6, 1.1, { fontSize: 15 });
  }
  // ---------------------------------------------------------------- 31 Nano vs Pi 5
  {
    const s = content("Hardware & transport", "Verified against vendor documentation", "Jetson Nano vs Raspberry Pi 5",
      "This is the most important hardware slide. Jetson Nano (2019, Maxwell, JetPack 4.x, max JetPack 4.6): hardware encoder 4K30 or 4x1080p30 or 9x720p30 H.264/H.265; decoder 4K60 / 8x1080p30. Use it through GStreamer (nvv4l2h264enc). Upstream FFmpeg does not use the Nano's encoder — NVIDIA's FFmpeg build accelerates decode; community patches (jetson-ffmpeg) exist. Raspberry Pi 5: NO hardware H.264 encoder, NO H.264 hardware decoder; it has a 4Kp60 HEVC decoder. Encoding is libx264 on the A76 cores — Raspberry Pi's 2026 white paper measured roughly 62–90% of one core for one 1080p30 low-latency encode. And warn about Orin Nano: no hardware encoder at all.");
    table(s, [
      ["", "NVIDIA Jetson Nano", "Raspberry Pi 5"],
      ["Hardware H.264/H.265 ENCODE", { text: "✔  4K30 · 4× 1080p30 · 9× 720p30", color: HEX.teal, bold: true }, { text: "✘  none — software (libx264) only", color: HEX.rose, bold: true }],
      ["Hardware DECODE", "✔  H.264/H.265: 4K60 · 8× 1080p30", "HEVC only (4Kp60); H.264 in software"],
      ["How to use the encoder", "GStreamer nvv4l2h264enc / nvv4l2h265enc", "FFmpeg / GStreamer x264, rpicam-vid"],
      ["FFmpeg HW encode", "✘ upstream (community patches exist)", "n/a"],
      ["CPU", "4× Cortex-A57 @ 1.43 GHz", "4× Cortex-A76 @ 2.4 GHz"],
      ["Measured software cost", "—", "1080p30 low-latency ≈ 0.62–0.9 core"],
      ["Software stack", "JetPack 4.x (Ubuntu 18.04), up to 4.6.x", "Raspberry Pi OS (Bookworm / Trixie)"],
    ], 0.6, 1.75, 12.1, [3.3, 4.4, 4.4], { fontSize: 13, rowH: 0.5 });
    box(s, 0.6, 5.95, 12.1, 0.75, { fill: col.card, line: HEX.amber });
    rich(s, [{ text: "⚠ Jetson Nano ≠ Jetson ORIN Nano. ", bold: true, color: col.amber, nl: false }, { text: "The Orin Nano has no hardware video encoder (1080p30 uses 1–2 CPU cores). Check: cat /etc/nv_tegra_release" }], 0.85, 6.05, 11.6, 0.55, { fontSize: 14, valign: "middle" });
  }
  // ---------------------------------------------------------------- 32 Where to encode
  {
    const s = content("Hardware & transport", "A decision, not a default", "Where should the encoding happen?",
      "Present this as a decision tree. 1) If the cameras can encode H.264 themselves with decent settings (IP cameras, or UVC cameras with an onboard H.264 encoder), let them — the SBC just forwards; no generation loss, no SBC load. 2) If cameras send raw or MJPEG and you have a Jetson Nano, use its hardware encoder via GStreamer, within its ~4x1080p30 budget; MJPEG must be decoded first (nvjpegdec/nvv4l2decoder mjpeg=1). 3) On a Pi 5, software encoding is possible for a few modest streams at ultrafast + zerolatency — measure the CPU and the temperature. 4) Encoding on the topside laptop does not save tether bandwidth at all.");
    const opts = [
      [fi.FiCamera, "In the camera", "IP cameras or UVC cameras with built-in H.264", "No SBC load, no re-encode loss", "Depends on camera's settings & quirks", col.teal],
      [tb.TbCircuitResistor, "SBC hardware", "Jetson Nano NVENC via GStreamer", "Low CPU, predictable", "Fixed ~4× 1080p30 budget; MJPEG must be decoded first", col.cyan],
      [fi.FiCpu, "SBC software", "Raspberry Pi 5 / Orin Nano: libx264", "Flexible, best quality per bit", "CPU + heat; few streams only", col.amber],
      [fi.FiMonitor, "Topside laptop", "Re-encode for recording / browser", "Plenty of power", "Saves ZERO tether bandwidth", col.rose],
    ];
    for (let i = 0; i < 4; i++) {
      const [ic, t, w, p, c, colr] = opts[i]; const x = 0.6 + i * 3.05;
      box(s, x, 1.75, 2.85, 4.7, { fill: col.card });
      await iconCircle(s, ic, x + 0.22, 1.95, 0.6);
      text(s, t, { x: x + 0.22, y: 2.7, w: 2.45, h: 0.45, fontSize: 17, bold: true, color: colr });
      text(s, w, { x: x + 0.22, y: 3.15, w: 2.45, h: 0.9, fontSize: 13, color: col.muted });
      text(s, "+ " + p, { x: x + 0.22, y: 4.1, w: 2.45, h: 0.9, fontSize: 14, color: col.teal });
      text(s, "– " + c, { x: x + 0.22, y: 5.0, w: 2.45, h: 1.2, fontSize: 14, color: col.rose });
    }
    text(s, "Prefer left to right — but only after measuring what each option really delivers on your hardware.", { x: 0.6, y: 6.55, w: 12.1, h: 0.35, fontSize: 14, italic: true, color: col.muted });
  }
  await require("./deck_part_new").pi5Verdict(ctx);
  await require("./deck_part_new").heatReliability(ctx);
  // ---------------------------------------------------------------- 33 Protocols
  {
    const s = content("Hardware & transport", "Getting bits to the browser", "RTSP, RTP, UDP, TCP, WebRTC, HTTP",
      "UDP: no retransmission — lost packets are lost, but no waiting. TCP: reliable but head-of-line blocking — when the link hiccups, everything waits and delay grows. RTP over UDP is the classic low-latency video transport; RTSP sets it up (it can also interleave RTP over TCP). Browsers can't play RTSP directly — WebRTC is the browser-native low-latency path (UDP, congestion control, keyframe requests); a media server such as MediaMTX can convert RTSP to WebRTC. MJPEG over HTTP is simple and low-latency but bandwidth-hungry. HLS/DASH are for watching TV, with seconds of delay — never for piloting.");
    table(s, [
      ["Technology", "What it is", "Typical latency", "ROV fit"],
      ["UDP", "Transport: fire-and-forget datagrams", "minimal", "carries RTP / WebRTC media"],
      ["TCP", "Transport: reliable, ordered, retransmits", "grows under loss/congestion", "OK on a clean link; stalls when stressed"],
      ["RTP (+RTCP)", "Media packets with timestamps & sequence numbers; RTCP feedback", "low", { text: "★ good — the classic choice", color: HEX.teal }],
      ["RTSP", "Session control (DESCRIBE / SETUP / PLAY) for RTP", "low (player buffer!)", "IP cameras speak it; browsers don't"],
      ["WebRTC", "Browser-native real-time media over UDP, with congestion control", "low (≈ 100–300 ms typical)", { text: "★ good for a web pilot UI", color: HEX.teal }],
      ["HTTP MJPEG", "JPEG frames pushed over one HTTP response", "low", "simple, but bandwidth-hungry"],
      ["HLS / DASH", "Segmented HTTP streaming for viewers", "seconds", { text: "✘ never for piloting", color: HEX.rose }],
    ], 0.6, 1.75, 12.1, [1.8, 4.6, 2.6, 3.1], { fontSize: 13, rowH: 0.56 });
    text(s, "Bridge example: cameras → RTSP → MediaMTX on the SBC or laptop → WebRTC (WHEP) → browser.", { x: 0.6, y: 6.4, w: 12.1, h: 0.4, fontSize: 14, color: col.amber });
  }
  // ---------------------------------------------------------------- 34 Latency budget
  {
    const s = content("Hardware & transport", "Experiment 9 · ESTIMATE", "Where the milliseconds go",
      `Stacked bars are ESTIMATES for three typical pipelines, using the measured x264 encoder hold from the notebook (${D.e9.defaultFrames} frames ≈ ${D.e9.defaultMs} ms with defaults). The lesson: in a badly configured pipeline the cable is irrelevant — encoder lookahead and the player's buffer dominate. Distinguish latency (time per frame) from FPS (frames per second) and throughput (bits per second): conveyor-belt analogy. Show how to measure glass-to-glass: ms clock on the laptop screen, camera pointed at it, phone photo of both, 10 repeats, report median and worst.`);
    const stages = ["capture", "encode", "network", "jitter buffer", "decode", "render + display"];
    const pip = D.e9.budgets; // [{name, vals[6]}]
    s.addChart(pres.charts.BAR, stages.map((st, k) => ({ name: st, labels: pip.map((p) => p.name), values: pip.map((p) => p.vals[k]) })), {
      x: 0.6, y: 1.7, w: 8.2, h: 4.4, barDir: "bar", catAxisOrientation: "maxMin", barGrouping: "stacked", chartColors: SERIES.slice(0, 6), showLegend: true, legendPos: "b",
      showTitle: true, title: "Glass-to-glass latency budget (ms) — ESTIMATE", valAxisMinVal: 0, ...chartBase(), objectName: "latency-chart" });
    pip.forEach((p, i) => { stat(s, 9.1, 1.75 + i * 1.45, 3.6, `≈ ${p.total.toLocaleString("en-US")} ms`, p.name, [col.teal, col.rose, col.cyan][i], { size: 30, vh: 0.55, lh: 0.75, labelSize: 12 }); });
    text(s, "FPS ≠ latency: a perfect 30 FPS stream can still be two seconds late.", { x: 0.6, y: 6.25, w: 12.1, h: 0.45, fontSize: 15, bold: true, color: col.amber });
  }
  // ---------------------------------------------------------------- 35 Encoder delay & jitter
  {
    const s = content("Hardware & transport", "Experiment 9 · measured", "Latency is designed, not discovered",
      `Measured with PyAV, feeding one frame at a time: x264 with default settings held ${D.e9.defaultFrames} frames before producing its first packet (rc-lookahead 40 + frame threads), i.e. about ${D.e9.defaultMs} ms at 30 FPS regardless of CPU speed. With tune zerolatency it held ${D.e9.zlFrames}. The jitter-buffer chart shows the other side: every millisecond of receiver buffer reduces late frames but adds latency. Choose deliberately — e.g. 30–60 ms on a clean tether.`);
    stat(s, 0.6, 1.8, 3.0, `${D.e9.defaultFrames} frames`, `held by x264 defaults ≈ ${D.e9.defaultMs} ms`, col.rose, { size: 44 });
    stat(s, 3.7, 1.8, 3.0, `${D.e9.zlFrames} frames`, "with -tune zerolatency", col.teal, { size: 44 });
    box(s, 0.6, 3.9, 6.1, 2.65, { fill: col.card });
    text(s, "Low-latency recipe (x264)", { x: 0.85, y: 4.0, w: 5.6, h: 0.4, fontSize: 16, bold: true });
    code(s, "-preset veryfast -tune zerolatency\n-b:v 2500k -maxrate 2500k -bufsize 1250k\n-g 30 -bf 0      # short GOP, no B-frames\n# receiver: small jitter buffer, no HLS", 0.85, 4.5, 5.6, 1.85, { fontSize: 13 });
    s.addChart(pres.charts.LINE, [{ name: "late frames (%)", labels: D.jitter.buffers.slice(2).map(String), values: D.jitter.late.slice(2) }], {
      x: 7.0, y: 1.7, w: 5.7, h: 4.9, chartColors: [HEX.cyan], lineSize: 2.5, lineDataSymbol: "circle", lineDataSymbolSize: 7, showLegend: false, showTitle: true,
      title: "Simulated tether: late frames vs jitter-buffer size", catAxisTitle: "jitter buffer (ms)", showCatAxisTitle: true, catAxisTitleColor: HEX.muted, catAxisTitleFontSize: 11,
      valAxisTitle: "% of frames too late", showValAxisTitle: true, valAxisTitleColor: HEX.muted, valAxisTitleFontSize: 11, valAxisMinVal: 0, ...chartBase(), objectName: "jitter-chart" });
  }
  // ---------------------------------------------------------------- 36 Main vs substreams
  {
    const s = content("Hardware & transport", "Experiment 8 · measured", "Main streams and substreams",
      `Each camera produces a main stream (full resolution, for the big screen and recording) and a substream (small, for thumbnails). Measured: main 720p30 ≈ ${D.e8.main} Mb/s, sub 640x360@15 ≈ ${D.e8.sub} Mb/s, thumbnail 320x180@10 ≈ ${D.e8.thumb} Mb/s. 1 main + 7 subs needs ${D.e8.pct1} of 'everything at full quality'. IP cameras usually offer substreams natively; on an SBC, GStreamer tee or one FFmpeg process with two outputs — at a cost in encoder capacity.`);
    const st = D.e8.strategies;
    s.addChart(pres.charts.BAR, [{ name: "Mb/s", labels: st.map((r) => r.name), values: st.map((r) => r.mbps) }], {
      x: 0.6, y: 1.7, w: 7.4, h: 4.9, barDir: "bar", catAxisOrientation: "maxMin", chartColors: [HEX.cyan], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0",
      showLegend: false, showTitle: true, title: "Eight cameras, measured streams (aggregate Mb/s)", valAxisMinVal: 0, ...chartBase(), objectName: "strategy-chart" });
    const t = [["Main stream", "full resolution & FPS · for the camera on the big screen and for recording", col.cyan], ["Substream", "640×360@15 · for the thumbnail grid: “is something happening there?”", col.teal], ["Thumbnail / paused", "320×180@5–10, or off — shown honestly as paused in the UI", col.violet]];
    t.forEach(([a, b, c], i) => { const y = 1.75 + i * 1.6; box(s, 8.3, y, 4.4, 1.42, { fill: col.card });
      text(s, a, { x: 8.55, y: y + 0.12, w: 4, h: 0.4, fontSize: 17, bold: true, color: c }); text(s, b, { x: 8.55, y: y + 0.55, w: 4, h: 0.8, fontSize: 13, color: col.muted }); });
  }
  // ---------------------------------------------------------------- 37 Adaptive / priorities
  {
    const s = content("Hardware & transport", "Camera selection & adaptive streaming", "Spend the budget where the pilot is looking",
      "A priority allocator runs every second or so: (1) give each active camera its minimum, highest priority first; pause the lowest if minimums don't fit; (2) top up in priority order to each camera's maximum. Requires: encoders whose bitrate can change at runtime, a throughput estimate (RTCP receiver reports, WebRTC congestion control, probing), and a UI that tells the truth about paused/degraded cameras. Priorities change with the task — the manipulator camera is priority 1 during a grab.");
    flow(s, [{ title: "Measure", sub: "throughput, loss, RTT (RTCP / WebRTC stats)" }, { title: "Budget", sub: "70 % of throughput − control/telemetry" }, { title: "Allocate", sub: "minimums by priority, then top up" }, { title: "Apply", sub: "set encoder bitrates, pause/resume streams" }, { title: "Show", sub: "UI states: live · degraded · paused · lost" }], 0.6, 1.8, 12.1, 1.6, { titleSize: 15, subSize: 11 });
    const rows = [["Pilot camera", "priority 1", "min 1.5 · max 8 Mb/s", col.cyan], ["Manipulator camera", "priority 2 (1 while gripping)", "min 0.8 · max 5 Mb/s", col.teal], ["6 aux cameras", "priority 3–8", "min 0.15 · max 1 Mb/s — paused first", col.violet]];
    rows.forEach(([a, b, c, colr], i) => { const y = 3.8 + i * 0.9; box(s, 0.6, y, 7.3, 0.75, { fill: col.card });
      text(s, a, { x: 0.85, y, w: 2.4, h: 0.75, fontSize: 15, bold: true, color: colr, valign: "middle" }); text(s, b, { x: 3.3, y, w: 2.2, h: 0.75, fontSize: 13, valign: "middle" }); text(s, c, { x: 5.5, y, w: 2.3, h: 0.75, fontSize: 13, color: col.muted, valign: "middle" }); });
    box(s, 8.2, 3.8, 4.5, 2.55, { fill: col.card, line: HEX.amber });
    text(s, "Measured in the notebook", { x: 8.45, y: 3.95, w: 4, h: 0.4, fontSize: 16, bold: true, color: col.amber });
    text(s, "Tether degrading 100 → 40 → 20 → 6 Mb/s: the pilot camera stays sharp, aux cameras degrade, then pause — visibly.", { x: 8.45, y: 4.45, w: 4, h: 1.8, fontSize: 14, color: col.muted });
  }
  await require("./deck_part_new").cvAndSlam(ctx);
  // ---------------------------------------------------------------- 38 How to measure
  {
    const s = content("Hardware & transport", "Your measurement toolbox", "How to measure streaming performance",
      "Walk through each tool briefly and point to the Diagnostic Checklist, which has the full commands. The point: every claim in the team's design document should come with one of these measurements. ffprobe tells you codec/resolution/fps/bitrate of a stream; v4l2-ctl lists what USB cameras can output; lsusb -t shows which bus and speed each camera is on; ethtool shows negotiated link speed and duplex; iperf3 measures throughput, jitter and loss; tegrastats / top / vcgencmd show CPU, encoder and temperature; the browser's chrome://webrtc-internals shows WebRTC stats including frames dropped and jitter buffer delay.");
    const tools = [
      ["Stream", "ffprobe -hide_banner rtsp://…", "codec, resolution, FPS, bitrate"],
      ["USB cameras", "v4l2-ctl --list-formats-ext · lsusb -t", "formats, bus, speed, sharing"],
      ["Link", "ethtool eth0", "negotiated speed & duplex"],
      ["Throughput", "iperf3 -c <rov> -u -b 80M", "throughput, jitter, loss"],
      ["Traffic", "iftop · nload · tcpdump / Wireshark", "who uses the tether"],
      ["SBC load", "tegrastats · top · vcgencmd measure_temp", "CPU, encoder, heat, throttling"],
      ["Browser", "chrome://webrtc-internals · DevTools", "decode time, drops, jitter buffer"],
      ["Glass-to-glass", "ms clock + phone photo", "real latency, median & worst"],
    ];
    tools.forEach(([a, c, b], i) => { const x = 0.6 + (i % 2) * 6.15, y = 1.75 + Math.floor(i / 2) * 1.2; box(s, x, y, 5.95, 1.05, { fill: col.card });
      text(s, a, { x: x + 0.2, y: y + 0.1, w: 1.8, h: 0.85, fontSize: 15, bold: true, color: col.cyan, valign: "middle" });
      text(s, c, { x: x + 2.0, y: y + 0.1, w: 3.85, h: 0.45, fontSize: 12, fontFace: "Courier New", color: col.amber });
      text(s, b, { x: x + 2.0, y: y + 0.55, w: 3.85, h: 0.4, fontSize: 13, color: col.muted }); });
  }
  // ---------------------------------------------------------------- 39 Activity 2
  {
    const s = content("Hardware & transport", "Activity 2 · 20 minutes", "Diagnose the ROV",
      "Read the scenario aloud. Teams list hypotheses (at least 5), rank by likelihood, and for each give the measurement that would confirm or reject it. Good answers: USB bus saturation (lsusb -t, camera fails to start), SBC CPU saturation from MJPEG decode + re-encode (top), thermal throttling (vcgencmd get_throttled / tegrastats), tether negotiated at 100 Mb/s or with errors (ethtool -S), TCP head-of-line blocking (latency grows over time), player buffering, browser decoding 8 streams on a weak laptop (DevTools performance). Scoring: 1 point per plausible hypothesis, 2 per correct measurement, 3 bonus for the best-ranked root cause.");
    box(s, 0.6, 1.75, 6.3, 4.8, { fill: col.card, line: HEX.amber });
    text(s, "The scenario", { x: 0.85, y: 1.9, w: 5.8, h: 0.4, fontSize: 17, bold: true, color: col.amber });
    bullets(s, ["Eight cameras streaming at 640×480", "After ~10 minutes in the water, video lags by ~1 s", "Two cameras freeze occasionally; one sometimes fails to start", "Thruster response 'feels slow' too", "The team's plan: reduce the resolution again"], 0.85, 2.45, 5.8, 3.0, { fontSize: 15, gap: 8 });
    text(s, "What would you measure before changing anything?", { x: 0.85, y: 5.6, w: 5.8, h: 0.8, fontSize: 15, bold: true, italic: true });
    box(s, 7.2, 1.75, 5.5, 4.8, { fill: col.card });
    text(s, "Your team's answer sheet", { x: 7.45, y: 1.9, w: 5, h: 0.4, fontSize: 17, bold: true });
    table(s, [["#", "Hypothesis", "Measurement"], ["1", "", ""], ["2", "", ""], ["3", "", ""], ["4", "", ""], ["5", "", ""]], 7.45, 2.45, 5.0, [0.4, 2.3, 2.3], { fontSize: 12, rowH: 0.5 });
    text(s, "Scoring: 1 per hypothesis · 2 per correct measurement · +3 best root cause", { x: 7.45, y: 5.75, w: 5, h: 0.65, fontSize: 13, color: col.amber });
  }
  // ---------------------------------------------------------------- 40 Optimization strategy
  {
    const s = content("Hardware & transport", "Putting it together", "A practical optimization strategy",
      "This is the takeaway procedure for the video system — in order. 1 Inventory and measure. 2 Remove wasted bits: right codec, capped rate control, no unneeded B-frames/lookahead. 3 Stream smart: main/sub, priorities, pause unwatched. 4 Engineer latency: zerolatency, short GOP, small buffers, UDP-based transport. 5 Engineer failure: reconnection, keyframe on switch, honest UI states. 6 Verify against requirements, inside the enclosure, with everything running. Only then consider resolution.");
    const steps = [["1", "Inventory & measure", "cameras, codec, link speed, CPU, latency"], ["2", "Stop wasting bits", "H.264 instead of MJPEG; capped bitrate"], ["3", "Stream smart", "main + substreams, priorities, pause unwatched"], ["4", "Design latency", "zerolatency, short GOP, small buffers, UDP"], ["5", "Design failure", "reconnect, keyframe on switch, honest UI"], ["6", "Verify", "against requirements, in the enclosure, all running"]];
    steps.forEach(([n, a, b], i) => { const x = 0.6 + (i % 3) * 4.1, y = 1.8 + Math.floor(i / 3) * 2.25; box(s, x, y, 3.85, 2.0, { fill: col.card });
      text(s, n, { x: x + 0.25, y: y + 0.15, w: 0.8, h: 0.8, fontSize: 40, bold: true, color: col.cyan, fontFace: "Arial" });
      text(s, a, { x: x + 1.05, y: y + 0.25, w: 2.7, h: 0.6, fontSize: 17, bold: true, valign: "middle" }); text(s, b, { x: x + 0.25, y: y + 1.05, w: 3.4, h: 0.8, fontSize: 14, color: col.muted }); });
    text(s, "Reducing resolution is the last lever, not the first.", { x: 0.6, y: 6.35, w: 12.1, h: 0.45, fontSize: 16, bold: true, color: col.amber });
  }
  // ---------------------------------------------------------------- 41 Recap session 1
  {
    const s = content("Hardware & transport", "End of session 1", "Homework: measure your own ROV",
      "Hand out the ROV System Diagnostic Checklist. Ask each subsystem owner to fill in their part before session 2. Even partial answers are valuable — 'we don't know' is a finding. Open session 2 with the results.");
    const items = [[fi.FiClipboard, "Fill in the Diagnostic Checklist", "Camera models, formats, codec, link speed, CPU, temperature, latency."], [fi.FiFilm, "Record 60 s of real footage", "Re-run the notebook on it (set ROV_SOURCE). Your bits-per-pixel, not ours."], [fi.FiClock, "Measure glass-to-glass latency", "One camera, then all eight. Median and worst of 10."]];
    for (let i = 0; i < 3; i++) await card(s, 0.6 + i * 4.1, 1.8, 3.85, 3.3, { icon: items[i][0], title: items[i][1], body: items[i][2], titleSize: 16, bodySize: 15 });
    box(s, 0.6, 5.4, 12.1, 1.1, { fill: col.card });
    text(s, "Bring the numbers to session 2 — we will turn them into requirements, tests and a better pilot interface.", { x: 0.9, y: 5.5, w: 11.6, h: 0.9, fontSize: 17, valign: "middle" });
  }
};
