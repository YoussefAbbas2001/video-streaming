// Builds the slides added in November 2026 into a scratch deck (out/new_slides_nov2026.pptx).
// They are then inserted into the hand-edited decks by insert_slides.py, so the decks' own edits are kept:
//
//   node build/new_slides_nov2026.js
//   python3 build/insert_slides.py ...          (see build/README_slides.md)
//
// Every number on these slides is either measured by us (Encoding Lab, 19–21 Nov 2026) or sourced in the speaker notes.
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const { THEME, HEX, makeHelpers } = require("./deck_helpers");
const { writeTheme } = require("./write_theme");

const OUT = path.join(__dirname, "..", "out", "new_slides_nov2026.pptx");

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const H = makeHelpers(pres);
  const { C, col, text, bullets, rich, box, card, arrow, flow, table, stat, code, pill } = H;
  // same layout name and placeholders as the decks: insert_slides.py maps the slides onto the decks' own MIA_CONTENT layout
  pres.defineSlideMaster({
    title: "MIA_CONTENT", background: { color: HEX.bg },
    objects: [
      { placeholder: { options: { name: "kicker", type: "body", x: 0.6, y: 0.32, w: 10, h: 0.3, fontSize: 12, bold: true, color: C.accent1, fontFace: "Arial", charSpacing: 2, margin: 0, valign: "middle" }, text: "" } },
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.66, w: 12.1, h: 0.85, fontSize: 32, bold: true, color: C.background1, fontFace: "Arial", margin: 0, valign: "middle", align: "left" }, text: "" } },
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
  const foot = (s, t) => text(s, t, { x: 0.6, y: 6.68, w: 12.1, h: 0.3, fontSize: 11, color: col.muted, italic: true });

  // ======================================================================= 1 · why chroma subsampling is free
  {
    const s = content("chroma", "Digital video fundamentals · why 4:2:0", "Why chroma subsampling is (almost) free",
      "The eye resolves fine detail in brightness much better than in colour: the retina has roughly 120 million rods and about 6 million cones, and our colour vision has far lower spatial resolution than our brightness vision. " +
      "Video exploits this: convert RGB to one brightness channel (luma, Y) and two colour-difference channels (Cb, Cr), keep Y at full resolution and store colour at half resolution in both directions (4:2:0). That is 12 bits per pixel instead of 24, half the data, before any compression, and most viewers cannot see it. " +
      "Luma is mostly green: Y = 0.299 R + 0.587 G + 0.114 B (BT.601; BT.709 uses 0.2126 / 0.7152 / 0.0722). " +
      "Underwater bonus: water absorbs red first, so the colour channels already carry little detail; the edges the pilot needs (cracks, pipe joints, text on gauges) live in luma. " +
      "Where it hurts: thin coloured lines, such as a red overlay line or colour-coded wires one pixel wide, bleed into their neighbours. Draw overlays on the pilot laptop, after decoding, not into the encoded video.");
    [["≈ 120 M", "rods: see brightness, fine detail", col.cyan], ["≈ 6 M", "cones: see colour, coarser detail", col.amber], ["− 50 %", "4:2:0 = 12 bits/pixel instead of 24, before any compression", col.teal]]
      .forEach(([v, l, c], i) => { box(s, 0.6 + i * 4.1, 1.75, 3.85, 1.7); stat(s, 0.85 + i * 4.1, 1.8, 3.4, v, l, c, { size: 40, labelSize: 13, vh: 0.85, lh: 0.65 }); });
    await card(s, 0.6, 3.7, 5.95, 2.85, { title: "Luma carries the detail", titleColor: col.cyan, bodySize: 14, bullets: [
      "RGB → Y (brightness) + Cb, Cr (colour differences)",
      "Y = 0.299 R + 0.587 G + 0.114 B: mostly green, like the eye",
      "Keep Y at full resolution; one Cb/Cr pair per 2 × 2 pixels",
      "Every codec on our ROV (H.264, H.265, AV1, MJPEG) uses 4:2:0 by default"] });
    await card(s, 6.75, 3.7, 5.95, 2.85, { title: "Underwater: even better, with one trap", titleColor: col.amber, bodySize: 14, bullets: [
      "Water absorbs red first: colour is already low-detail",
      "Cracks, pipe joints and gauge text are luma edges",
      "Trap: 1-pixel coloured lines (overlays, wire colours) bleed",
      "So draw overlays on the pilot laptop, after decoding"] });
  }

  // ======================================================================= 2 · intra prediction
  {
    const s = content("intra", "Prediction · intra (inside one frame)", "Intra prediction: guess a block from its neighbours",
      "Intra prediction uses only pixels of the same frame that are already decoded: the row above and the column to the left of the block. " +
      "The encoder tries several modes (vertical, horizontal, DC = average, planar, and many angles), picks the one whose prediction is closest, and sends only the mode number plus the residual (block minus prediction). " +
      "H.264 has 9 directional modes for 4×4 and 8×8 blocks and 4 for 16×16; H.265 has 35 (planar, DC and 33 angles); AV1 has 56 directional angles plus smooth, Paeth and chroma-from-luma. More modes = better guesses = smaller residuals, at more search effort. " +
      "I-frames use only intra prediction, which is why they are the largest frames and the ones a decoder can start from. Intra refresh spreads intra-coded blocks over many frames instead of one big I-frame. " +
      "Try it in the Encoding Lab: Bitrate over time shows the I-frame spikes; Packet loss compares a long GOP with intra refresh.");
    // the picture: neighbours (amber) + 4×4 block, vertical mode
    const cx = 0.9, cy = 2.25, cs = 0.62;
    box(s, 0.6, 1.75, 4.35, 4.85);
    text(s, "Vertical mode: copy the row above downwards", { x: 0.8, y: 1.88, w: 4.0, h: 0.35, fontSize: 13, bold: true, color: col.cyan });
    for (let i = 0; i < 4; i++) {
      s.addShape(pres.shapes.RECTANGLE, { x: cx + cs * (i + 1), y: cy + 0.25, w: cs - 0.06, h: cs - 0.06, fill: { color: HEX.amber }, line: { type: "none" }, objectName: `nb-top-${i}` });
      s.addShape(pres.shapes.RECTANGLE, { x: cx, y: cy + 0.25 + cs * (i + 1), w: cs - 0.06, h: cs - 0.06, fill: { color: HEX.amber, transparency: 35 }, line: { type: "none" }, objectName: `nb-left-${i}` });
      for (let j = 0; j < 4; j++) {
        s.addShape(pres.shapes.RECTANGLE, { x: cx + cs * (i + 1), y: cy + 0.25 + cs * (j + 1), w: cs - 0.06, h: cs - 0.06, fill: { color: HEX.amber, transparency: 70 - j * 8 }, line: { color: HEX.cyan, width: 0.75 }, objectName: `blk-${i}-${j}` });
      }
      arrow(s, cx + cs * (i + 1) + cs / 2 - 0.03, cy + 0.25 + cs - 0.02, cx + cs * (i + 1) + cs / 2 - 0.03, cy + 0.25 + cs * 4.6, HEX.cyan, { width: 1.25 });
    }
    text(s, "amber = already-decoded neighbours · outlined = the 4 × 4 block being predicted", { x: 0.8, y: 5.75, w: 4.0, h: 0.7, fontSize: 11.5, color: col.muted });
    flow(s, [{ title: "Try every mode", sub: "vertical, horizontal, DC, planar, angles" }, { title: "Keep the best guess", sub: "closest to the real block" },
      { title: "Residual", sub: "real block − prediction (small numbers)" }, { title: "Send", sub: "mode number + coded residual" }], 5.2, 1.75, 7.5, 1.25, { titleSize: 13, subSize: 11 });
    table(s, [["Codec", "Intra modes", "Largest block"], ["H.264", "9 directions (4×4, 8×8) · 4 for 16×16", "16 × 16"], ["H.265", "35: planar, DC, 33 angles", "32 × 32"],
      ["AV1", "56 angles + smooth, Paeth, chroma-from-luma", "64 × 64"]], 5.2, 3.25, 7.5, [1.2, 4.3, 2.0], { fontSize: 13, rowH: 0.42 });
    await card(s, 5.2, 5.05, 7.5, 1.55, { title: "Why I-frames are big", titleColor: col.amber, bodySize: 13.5,
      body: "An I-frame is all intra: no help from earlier frames. In our 720p30 test an I-frame was 5–8× the average frame — the spike the tether must absorb." });
  }

  // ======================================================================= 3 · inter prediction
  {
    const s = content("inter", "Prediction · inter (between frames)", "Inter prediction: find the block in the last frame",
      "Inter prediction is where most of the compression comes from. For every block the encoder searches a window of a reference frame for the best-matching block (motion estimation), then sends only the motion vector and the small difference (residual). The decoder copies the block from its own copy of the reference frame and adds the residual (motion compensation). " +
      "Vectors have quarter-pixel precision in H.264/H.265 (1/8 in AV1): the reference is interpolated between pixels. More reference frames and B-frames (which also look at a future frame) find better matches but cost search time, memory and, for B-frames, latency. " +
      "The search is the expensive part of encoding, and presets mostly change how hard it searches: x264 ultrafast uses the diamond search, no sub-pixel refinement and 1 reference; medium uses hexagon search, sub-pixel level 7 and 3 references. Raspberry Pi's own low-latency Pi 5 configuration uses me=dia, subme=0 and refs=1. " +
      "Underwater: marine snow and moving caustics have no match in the previous frame, so the residual stays large and costs bits — that is why our clips need more bitrate than a dry-land scene.");
    box(s, 0.5, 1.68, 6.6, 2.85, { fill: HEX.bg, line: HEX.grid });     // one container = one click for the whole picture
    box(s, 0.6, 1.75, 3.0, 2.35, { fill: col.card }); text(s, "Frame N − 1 (reference)", { x: 0.6, y: 4.15, w: 3.0, h: 0.3, fontSize: 11.5, color: col.muted, align: "center" });
    box(s, 1.25, 2.2, 1.75, 1.45, { fill: col.card, line: HEX.muted, dash: "dash" });
    text(s, "search window", { x: 1.3, y: 2.25, w: 1.6, h: 0.25, fontSize: 10.5, color: col.muted });
    box(s, 1.55, 2.75, 0.55, 0.55, { fill: HEX.amber, r: 0.02 });
    box(s, 4.0, 1.75, 3.0, 2.35, { fill: col.card }); text(s, "Frame N (being coded)", { x: 4.0, y: 4.15, w: 3.0, h: 0.3, fontSize: 11.5, color: col.muted, align: "center" });
    box(s, 5.6, 2.55, 0.55, 0.55, { fill: HEX.cyan, r: 0.02 });
    arrow(s, 5.55, 2.82, 2.15, 3.02, HEX.amber, { width: 1.75, dash: "dash" });
    text(s, "motion vector (−14.25, +1.75)", { x: 2.5, y: 3.15, w: 2.9, h: 0.3, fontSize: 11.5, color: col.amber, align: "center" });
    await card(s, 0.6, 4.7, 6.4, 1.9, { title: "Underwater: why our scenes cost more", titleColor: col.amber, bodySize: 13.5, bullets: [
      "Marine snow and moving caustics have no match in the last frame",
      "No match → large residual → more bits at the same quality",
      "Good lighting and a stable camera are bitrate savings"] });
    await card(s, 7.25, 1.75, 5.45, 2.35, { title: "What the encoder sends", titleColor: col.cyan, bodySize: 13.5, bullets: [
      "Motion vector at ¼-pixel precision (⅛ in AV1)",
      "Reference index: which earlier frame (refs)",
      "Residual: what the copied block got wrong",
      "B-frames may also point at a FUTURE frame → latency"] });
    table(s, [["x264 preset", "Search", "Sub-pixel", "Refs", "Speed"], ["ultrafast", "diamond", "0", "1", "fastest"], ["veryfast", "hexagon", "2", "1", "≈ 2.5× slower*"],
      ["medium (default)", "hexagon", "7", "3", "slow for live"]], 7.25, 4.35, 5.45, [1.55, 1.05, 1.0, 0.65, 1.2], { fontSize: 12.5, rowH: 0.4 });
    text(s, "Presets mostly change how hard the encoder searches. *measured, one core, 720p", { x: 7.25, y: 6.05, w: 5.45, h: 0.4, fontSize: 12.5, color: col.muted, italic: true });
  }

  // ======================================================================= 4 · transform + quantization
  {
    const s = content("dct", "Transform · quantize", "Transform + quantize: where bits are thrown away",
      "After prediction, the encoder is left with a residual block. A 2-D DCT (an integer approximation of it in H.264/H.265) re-expresses the block as frequencies: smooth content puts almost all its energy into a few low-frequency coefficients in the top-left corner. " +
      "Quantization divides every coefficient by a step size and rounds. This is the ONLY lossy step in the encoder; everything else is exactly reversible. Small, high-frequency coefficients become zero, and runs of zeros cost almost nothing to send. " +
      "The step size is set by the quantization parameter (QP): in H.264 and H.265, +6 QP doubles the step, which roughly halves the bitrate. CRF and bitrate control both work by choosing QP per frame and per block. " +
      "The numbers on this slide are a real 8×8 example (a gradient with a diagonal edge, like a pipe), computed with an orthonormal DCT and the classic JPEG luma quantization table: 64 pixel values become 11 non-zero numbers. " +
      "Block sizes: H.264 uses 4×4 and 8×8 transforms, H.265 up to 32×32, AV1 up to 64×64 — bigger transforms suit big smooth areas like open water.");
    const pix = [[90, 96, 102, 108, 114, 120, 166, 172], [93, 99, 105, 111, 117, 163, 169, 175], [96, 102, 108, 114, 160, 166, 172, 178], [99, 105, 111, 117, 163, 169, 175, 181], [102, 108, 114, 160, 166, 172, 178, 184], [105, 111, 117, 163, 169, 175, 181, 187], [108, 114, 160, 166, 172, 178, 184, 190], [111, 157, 163, 169, 175, 181, 187, 193]];
    const dct = [[128, -228, -13, -6, 0, -5, -5, 0], [-112, -14, 47, 14, -4, 2, 0, 6], [0, 23, 14, -31, -18, 6, 0, 1], [-20, -3, 0, -9, 18, 21, -7, -9], [0, 10, 5, -8, 0, -6, -13, 2], [-8, -1, 0, -3, 4, -1, 5, 21], [0, 1, 0, 4, 8, -9, -14, 2], [6, 2, -9, -6, 6, 4, 0, 4]];
    const q = [[8, -21, -1, 0, 0, 0, 0, 0], [-9, -1, 3, 1, 0, 0, 0, 0], [0, 2, 1, -1, 0, 0, 0, 0], [-1, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]];
    const grid = (x0, y0, m, fill, label, sub) => {
      box(s, x0 - 0.12, y0 - 0.5, 3.6, 4.15);
      text(s, label, { x: x0, y: y0 - 0.45, w: 3.4, h: 0.35, fontSize: 14, bold: true, color: col.cyan });
      const cs = 0.42;
      m.forEach((row, r) => row.forEach((v, c) => {
        const f = fill(v);
        s.addShape(pres.shapes.RECTANGLE, { x: x0 + c * cs, y: y0 + r * cs, w: cs - 0.03, h: cs - 0.03, fill: { color: f.color, transparency: f.t }, line: { type: "none" }, objectName: `cell-${label}-${r}-${c}` });
        s.addText(String(v), { x: x0 + c * cs, y: y0 + r * cs, w: cs - 0.03, h: cs - 0.03, fontSize: 8, color: f.ink || "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `v-${label}-${r}-${c}` });
      }));
      text(s, sub, { x: x0, y: y0 + 8 * 0.42 + 0.05, w: 3.4, h: 0.35, fontSize: 12, color: col.muted });
    };
    const gy = 2.35;
    grid(0.75, gy, pix, (v) => { const g = Math.round(v).toString(16).padStart(2, "0"); return { color: g + g + g, t: 0, ink: v > 140 ? "06101F" : "FFFFFF" }; }, "1 · Pixels (residual)", "64 values, all different");
    arrow(s, 4.3, gy + 1.6, 4.75, gy + 1.6, col.cyan);
    grid(4.95, gy, dct, (v) => ({ color: HEX.cyan, t: Math.max(0, 100 - Math.min(100, Math.abs(v) * 1.6)), ink: Math.abs(v) > 40 ? "06101F" : "FFFFFF" }), "2 · DCT: frequencies", "energy piles up top-left");
    arrow(s, 8.5, gy + 1.6, 8.95, gy + 1.6, col.cyan);
    grid(9.15, gy, q, (v) => ({ color: v ? HEX.amber : HEX.card, t: v ? 0 : 0, ink: v ? "06101F" : "5A7290" }), "3 · Quantized", "11 numbers left, 53 zeros");
    foot(s, "The only lossy step. +6 QP doubles the step size ≈ half the bitrate — CRF and bitrate caps both work by choosing QP.");
  }

  // ======================================================================= 5 · entropy coding + loop filters
  {
    const s = content("entropy", "Entropy coding · loop filters · profiles", "The last steps: entropy coding and loop filters",
      "Entropy coding packs the mode numbers, motion vectors and quantized coefficients into as few bits as possible: frequent symbols get short codes. H.264 offers CAVLC (simple, fast) and CABAC (arithmetic coding that adapts to the content). CABAC typically saves around 10 % of the bitrate at the same quality but costs more CPU and is strictly sequential. H.265 and AV1 always use arithmetic coding. " +
      "Loop filters run INSIDE the encoder's prediction loop, so the filtered frame becomes the reference: the deblocking filter smooths block edges; H.265 adds SAO; AV1 adds CDEF and loop restoration. Turning deblocking off saves CPU but leaves visible blocks at low bitrates. " +
      "Raspberry Pi's own low-latency configuration for the Pi 5 (April 2026 white paper) disables both CABAC and deblocking to bring 1080p30 down to about 62–90 % of one Cortex-A76 core; its high-quality configuration keeps them and needs about 100–150 % of a core. That is exactly this trade-off. " +
      "Profiles bundle the tools: Baseline (no B-frames, no CABAC), Main, High (adds the 8×8 transform). The pilot's decoder — browser, laptop, phone — must support the profile you send.");
    await card(s, 0.6, 1.75, 5.95, 2.6, { title: "Entropy coding: CAVLC vs CABAC", titleColor: col.cyan, bodySize: 14, bullets: [
      "Frequent symbols get short codes",
      "CABAC: adaptive arithmetic coding, ≈ 10 % fewer bits",
      "…but more CPU and strictly sequential",
      "H.265 and AV1: arithmetic coding only"] });
    await card(s, 6.75, 1.75, 5.95, 2.6, { title: "Loop filters: fix the blocks inside the loop", titleColor: col.teal, bodySize: 14, bullets: [
      "Deblocking smooths block edges (H.264+)",
      "SAO (H.265), CDEF + loop restoration (AV1)",
      "Filtered frame = the next reference frame",
      "Off = less CPU, visible blocks at low bitrate"] });
    table(s, [["Raspberry Pi 5, 1080p30 x264 (Raspberry Pi white paper, Apr 2026)", "Low latency", "High quality"],
      ["Preset · tune", "ultrafast · zerolatency", "superfast"], ["CABAC · deblocking · B-frames", "off · off · 0", "on · on · 1"],
      ["CPU (one A76 core)", "≈ 62–90 %", "≈ 98–153 %"], ["Quality at ≈ 1 Mb/s (PSNR · SSIM)", "39.1 dB · 0.956", "41.8 dB · 0.974"]],
      0.6, 4.6, 12.1, [6.1, 3.0, 3.0], { fontSize: 13, rowH: 0.38 });
  }

  // ======================================================================= 6 · containers
  {
    const s = content("containers", "Codec ≠ container", "Containers: the box around the bitstream",
      "The codec compresses the pictures; the container packs one or more streams (video, audio, telemetry, subtitles) with their timestamps, codec settings (for H.264: SPS/PPS) and an index for seeking. Changing the container does not touch the pictures: `ffmpeg -i dive.mkv -c copy dive.mp4` takes seconds and loses nothing (a remux). " +
      "MP4 writes its index (the moov atom) at the END of the file by default: if the ROV loses power mid-recording, the MP4 is unplayable. Fragmented MP4 writes small self-contained fragments; Matroska (MKV) and MPEG-TS stay playable up to the last good byte. So record during the dive in MKV, fragmented MP4 or MPEG-TS, and remux to MP4 afterwards if needed. " +
      "MPEG-TS is made of 188-byte packets and resynchronises after loss, which is why it is used for UDP and broadcast. RTP carries the bare codec bitstream with its own timestamps and sequence numbers and has the least overhead, which is why our live pilot stream uses it. AVI is old but fine for MJPEG recordings.");
    table(s, [["Container", "Built for", "Survives a power cut?", "Live streaming", "Use on our ROV"],
      ["MP4", "files, the web", { text: "✘ index written at the end", color: HEX.rose }, "only fragmented", "final archive, after the dive"],
      ["Fragmented MP4", "streaming segments", { text: "✔ per fragment", color: HEX.teal }, "HLS / DASH", "recording during the dive"],
      ["Matroska (MKV)", "flexible files", { text: "✔ playable to the last byte", color: HEX.teal }, "rarely", "onboard recording, any codec"],
      ["MPEG-TS", "broadcast, UDP", { text: "✔ 188-byte packets resync", color: HEX.teal }, "UDP, SRT", "live + record in one"],
      ["AVI", "old, simple files", { text: "partly", color: HEX.amber }, "no", "MJPEG recordings"],
      ["none: RTP", "real-time transport", "—", { text: "✔ least overhead", color: HEX.teal }, "the live pilot stream"]],
      0.6, 1.75, 12.1, [2.0, 2.25, 2.95, 1.95, 2.95], { fontSize: 13.5, rowH: 0.48 });
    await card(s, 0.6, 5.3, 5.95, 1.3, { title: "A container holds", titleColor: col.cyan, bodySize: 13,
      body: "streams (video, audio, telemetry) · timestamps · codec settings · an index for seeking" });
    code(s, "# new box, same pictures: seconds, lossless\nffmpeg -i dive.mkv -c copy dive.mp4", 6.75, 5.3, 5.95, 1.3, { fontSize: 13 });
  }

  // ======================================================================= 7 · encoder tuning at scale (Fermi)
  {
    const s = content("fermi", "Why the big streamers obsess over bits", "At Netflix scale, 1 % of bitrate is worth millions",
      "A Fermi estimate: each factor is rounded and labelled, so you can argue with any one of them. " +
      "Viewing: Netflix reported over 95 billion hours watched in January–June 2025 and 96 billion in July–December 2025 (What We Watched engagement reports), so about 191 billion hours in 2025 — over 500 million hours a day. " +
      "Data per hour: Netflix's own data-usage settings say up to 1 GB per hour for SD, up to 3 GB for HD and up to 7 GB for 4K. Our assumption for the blend of phones, laptops and TVs: about 2 GB per hour. That gives about 380 exabytes a year. " +
      "Cost per GB delivered: Netflix runs its own CDN (Open Connect), whose cost per GB is not public. Negotiated commercial streaming CDN rates are reported around $0.03–$0.05 per GB, and the cheapest volume CDNs list about $0.005 per GB. Using $0.005–$0.03 per GB as the range: $1.9–11 billion a year. " +
      "So 1 % fewer bits is worth about $19–115 million a year, before counting fewer rebuffers and lower data bills for members. Netflix reported that per-title encoding (2015) saved around 20 % and shot-based encoding (the Dynamic Optimizer) a further 17 % bitrate at +3.7 VMAF. Video is about 65 % of all internet traffic (Sandvine, 2022). " +
      "The lesson for us is the asymmetry: a Netflix title is encoded once and watched millions of times, so spending a lot of CPU per encode to save bits pays off. Our ROV stream is encoded once and watched once, live: we spend bits to buy low latency and low CPU, never the other way round.");
    const steps = [["191 B hours", "watched on Netflix in 2025", col.cyan], ["× ≈ 2 GB / hour", "assumed blend of SD / HD / 4K", col.cyan], ["≈ 380 EB / year", "delivered", col.cyan],
      ["× $0.005–0.03 / GB", "assumed delivery cost", col.cyan], ["$1.9–11 B / year", "to deliver it", col.amber]];
    steps.forEach(([v, l, c], i) => {
      const y = 1.75 + i * 0.97;
      box(s, 0.6, y, 5.4, 0.82, { fill: i === 4 ? col.card : col.card, line: i === 4 ? HEX.amber : undefined });
      text(s, v, { x: 0.8, y: y + 0.08, w: 2.6, h: 0.66, fontSize: 21, bold: true, color: c, valign: "middle", fontFace: "Arial" });
      text(s, l, { x: 3.45, y: y + 0.08, w: 2.45, h: 0.66, fontSize: 12.5, color: col.muted, valign: "middle" });
      if (i < 4) arrow(s, 3.3, y + 0.83, 3.3, y + 0.96, col.cyan, { width: 1.5 });
    });
    box(s, 6.25, 1.75, 6.45, 1.75, { line: HEX.amber });
    stat(s, 6.5, 1.78, 6.0, "1 % = $19–115 M / yr", "fewer bits, every year, at the same quality", col.amber, { size: 30, vh: 0.85, labelSize: 14 });
    [["≈ 20 %", "saved by per-title encoding (2015)"], ["17 %", "more by shot-based encoding, +3.7 VMAF"], ["≈ 65 %", "of internet traffic is video (2022)"]].forEach(([v, l], i) => {
      box(s, 6.25 + i * 2.2, 3.7, 2.05, 1.45);
      stat(s, 6.4 + i * 2.2, 3.72, 1.8, v, l, col.cyan, { size: 24, vh: 0.6, labelSize: 11.5, lh: 0.75 });
    });
    await card(s, 6.25, 5.35, 6.45, 1.25, { title: "The asymmetry", titleColor: col.teal, bodySize: 13,
      body: "Netflix: encode once, stream millions of times → spend CPU to save bits. Our ROV: encode once, watch once, live → spend bits to save latency and CPU." });
  }

  // ======================================================================= 8 · what the big streamers use
  {
    const s = content("bigco", "Published encoding practice", "What the big streamers actually do",
      "Exact production encoder parameters are not published by any of these companies; their methods are. " +
      "Netflix: per-title bitrate ladders since 2015 (around 20 % savings); shot-based encoding with its Dynamic Optimizer, which picks resolution and QP per shot (reported 17 % fewer bits at +3.7 VMAF); VMAF, its own perceptual quality metric; H.264 still serves the majority of views, and AV1 about 30 % of viewing as of December 2025. " +
      "YouTube: VP9 and AV1, transcoded on Argos, Google's own Video (trans)Coding Unit ASIC, announced in 2021 with 20–33× better compute efficiency than its previous software encoding on servers; around 500 hours of video are uploaded every minute. " +
      "Meta: AV1 for Facebook and Instagram Reels since early 2022; videos with high predicted watch time get the convex-hull dynamic optimizer; a hybrid approach uses hardware AVC at upload and premium software encodes later; by September 2023 about 70 % of Reels watch time on iOS was AV1. " +
      "Twitch: Enhanced Broadcasting moves the encoding ladder to the streamer's own GPU (NVENC), sending up to three renditions; NVIDIA reports about 25 % better efficiency for HEVC over H.264 on its encoder, and Twitch about 40 % for AV1. " +
      "The pattern: video on demand uses slow, multi-pass, per-shot software encoding because each encode is watched many times. Live video uses fast hardware encoders and fixed ladders. Our ROV is live.");
    const cards4 = [
      ["Netflix", col.rose, ["Per-title ladders (2015): ≈ 20 % fewer bits", "Per-shot Dynamic Optimizer: 17 % fewer bits, +3.7 VMAF", "Built VMAF, the quality metric", "AV1 ≈ 30 % of viewing (Dec 2025); H.264 still the majority"]],
      ["YouTube", col.amber, ["VP9 + AV1 for most views", "Argos VCU: own transcoding chip (2021)", "20–33× more compute-efficient than software", "≈ 500 hours uploaded every minute"]],
      ["Meta (Facebook, Instagram)", col.blue, ["AV1 for Reels since early 2022", "Dynamic optimizer for high-watch-time videos", "Hardware AVC at upload, premium encodes later", "≈ 70 % of iOS Reels watch time in AV1 (2023)"]],
      ["Twitch (live)", col.violet, ["Enhanced Broadcasting: the streamer's GPU encodes", "NVENC, up to 3 renditions at once", "HEVC ≈ 25 %, AV1 ≈ 40 % more efficient than H.264", "Live = hardware, fixed ladders, no per-shot search"]],
    ];
    for (let i = 0; i < 4; i++) {
      const [t, c, b] = cards4[i];
      await card(s, 0.6 + (i % 2) * 6.15, 1.75 + Math.floor(i / 2) * 2.25, 5.95, 2.1, { title: t, titleColor: c, bullets: b, bodySize: 13, gap: 2 });
    }
    foot(s, "Pattern: on demand = slow per-shot software encodes, watched millions of times. Live = fast hardware encoders. Our ROV is live.");
  }

  // ======================================================================= 9 · MJPEG resolution trap
  {
    const s = content("restrap", "MJPEG on the ROV · the resolution trap", "Shrinking an MJPEG camera: free, or decode → encode?",
      "The team streams USB cameras with mjpeg-streamer and lowers the resolution. Whether that costs anything depends on WHERE the resolution is lowered. " +
      "1) Asking the camera for a smaller mode (mjpg-streamer input_uvc -r 640x480, or FFmpeg -video_size 640x480 -input_format mjpeg with -c:v copy): the camera's own chip makes smaller JPEGs, nothing is decoded or encoded on the ROV. This only works for sizes the camera offers in MJPG: check with v4l2-ctl --list-formats-ext. If the camera does not offer the size, the V4L2 driver picks the nearest one it has. " +
      "2) Shrinking in software (the PyPI mjpeg-streamer library's Stream(size=...), any OpenCV resize, FFmpeg -vf scale): every frame is decoded, scaled and encoded again. Measured in the Encoding Lab Live camera tab, 720p30 MJPEG to 640×360: JPEG decode ≈ 2.4 ms, scale ≈ 0.4 ms, JPEG encode ≈ 0.9 ms per frame, about 13 % of a core instead of about 1 % — and the PyPI library repeats the encode for every viewer. " +
      "3) mjpg-streamer with -y (YUYV) receives raw frames and encodes JPEG on the CPU: no decode, but an encode per frame. " +
      "If the camera cannot give the size you need, a transcode is unavoidable — then make it count: encode that camera to H.264 (4–5× fewer bits than MJPEG at the same quality) instead of to a smaller MJPEG.");
    const row = (y, tag, tagCol, steps, cost, costCol) => {
      box(s, 0.5, y - 0.07, 12.3, 1.14, { fill: HEX.bg, line: HEX.grid });   // one container = one click per row
      pill(s, tag, 0.6, y + 0.28, 1.35, tagCol, { solid: true, h: 0.42, fontSize: 12 });
      flow(s, steps, 2.15, y, 7.15, 1.0, { titleSize: 12.5, subSize: 10.5, gap: 0.28 });
      box(s, 9.55, y, 3.15, 1.0, { line: costCol });
      text(s, cost, { x: 9.7, y: y + 0.08, w: 2.9, h: 0.84, fontSize: 13, bold: true, color: costCol, valign: "middle" });
    };
    row(1.82, "FREE", HEX.teal, [{ title: "Camera", sub: "asked for 640×480 MJPEG" }, { title: "Copy", sub: "no decode, no encode" }, { title: "Tether", sub: "small JPEGs" }],
      "≈ 1 % of a core\n(measured, 720p30 copy)", HEX.teal);
    row(3.07, "COSTLY", HEX.rose, [{ title: "Camera", sub: "1280×720 JPEG" }, { title: "Decode", sub: "≈ 2.4 ms" }, { title: "Scale", sub: "≈ 0.4 ms" }, { title: "Encode", sub: "≈ 0.9 ms (per viewer in the Python lib)" }],
      "≈ 13 % of a core\nper camera at 30 fps", HEX.rose);
    row(4.32, "HALF", HEX.amber, [{ title: "Camera", sub: "raw YUYV (-y)" }, { title: "Encode JPEG", sub: "on the ROV's CPU" }, { title: "Tether", sub: "JPEGs" }],
      "encode only\n(USB 2.0 limits raw sizes)", HEX.amber);
    code(s, "# sizes the camera compresses itself (look for MJPG):\nv4l2-ctl -d /dev/video0 --list-formats-ext\n# ask the camera = FREE:\nmjpg_streamer -i \"input_uvc.so -r 640x480 -f 15\" ...", 0.6, 5.5, 7.6, 1.15, { fontSize: 10.5 });
    await card(s, 8.45, 5.5, 4.25, 1.15, { title: "Size not offered? Encode to H.264", titleColor: col.cyan, titleSize: 14 });
    text(s, "one encode, 4–5× fewer bits than a smaller MJPEG", { x: 8.7, y: 6.05, w: 3.85, h: 0.45, fontSize: 12.5, color: col.muted });
  }

  // ======================================================================= 10 · knowledge exchange (SDLC deck)
  {
    const s = content("kx", "Knowledge exchange program", "One hour a week that makes the whole team faster",
      "Recommendation: a weekly Knowledge Exchange session, 60 minutes, same day and time every week, run by the mentors (alumni). " +
      "First 15 minutes: every sub-team (mechanical, electrical, software, GUI, CV…) gives a 2–3 minute update on ONE technical enhancement since last week and ONE blocker. No status reports — what changed and what we learned. " +
      "Next 35 minutes: one or two topic talks of 15–20 minutes each. Mentors keep a topic backlog and assign each topic to a member two weeks ahead, often pairing a junior with a senior; the mentor reviews the outline a few days before. " +
      "Last 10 minutes: questions, then next week's topics and presenters are confirmed. " +
      "Every talk leaves something behind: a one-page summary and the slides in the repo (docs/knowledge/), the recording on the team Drive, and the backlog item closed. Over a season this becomes the onboarding library for next year's team. " +
      "Track it like any process: topics delivered per month, the share of members who have presented, and how often a past talk is linked when answering a question or reviewing a PR.");
    flow(s, [{ title: "15 min · Team updates", sub: "each sub-team: 1 enhancement + 1 blocker, 2–3 min", color: col.card },
      { title: "35 min · 1–2 topic talks", sub: "assigned by mentors two weeks ahead", color: col.card },
      { title: "10 min · Q&A + next week", sub: "confirm topics and presenters", color: col.card }], 0.6, 1.75, 12.1, 1.15, { titleSize: 15, subSize: 12 });
    await card(s, 0.6, 3.15, 3.9, 2.85, { title: "Mentors (alumni) run it", titleColor: col.cyan, bodySize: 13.5, bullets: [
      "Keep a topic backlog (GitHub issues, label knowledge)", "Assign 1–2 topics per week, two weeks ahead", "Pair a junior with a senior", "Review the outline before the talk"] });
    await card(s, 4.7, 3.15, 3.9, 2.85, { title: "Example topics", titleColor: col.amber, bodySize: 13.5, bullets: [
      "RTP vs RTSP vs WebRTC on our tether", "Reading an encoder's frame sizes", "Depth-hold PID tuning", "Writing a pytest for the camera manager", "Thermal design of the ROV computer"] });
    await card(s, 8.8, 3.15, 3.9, 2.85, { title: "What each talk leaves behind", titleColor: col.teal, bodySize: 13.5, bullets: [
      "One-page summary + slides in docs/knowledge/", "Recording on the team Drive", "Next season's onboarding library", "Measured: topics/month, % members who presented"] });
    foot(s, "Start it as a 6-week pilot, review it in a retro, keep what works. Full guide: docs/sdlc/knowledge-exchange.md");
  }

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  await pres.writeFile({ fileName: OUT });
  await writeTheme(OUT, THEME);
  fs.writeFileSync(OUT.replace(/\.pptx$/, ".json"), JSON.stringify(slides, null, 1));
  console.log("wrote", OUT, slides);
})();
