// Builds the encoder picture slides into a scratch deck (out/new_slides_encoder.pptx):
//   * three explanation slides (1-pixel chroma bleed, motion search, deblocking) that follow the encoder slides they illustrate;
//   * five "one knob at a time" slides (CRF, codec, preset, resolution, noise) after the encoder section.
//
//   python3 build/make_encoder_images.py [--source your_dive.mp4]   # makes the pictures + out/encoder_panels/
//   node build/new_slides_encoder.js
//   python3 build/insert_slides.py out/new_slides_encoder.pptx presentation/MIA_Video_Streaming.pptx --place ...   (see build/README.md)
//
// Every picture is a real encode; every number on these slides comes from docs/streaming/img/encoder/measurements.json.
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const { THEME, HEX, makeHelpers } = require("./deck_helpers");
const { writeTheme } = require("./write_theme");

const ROOT = path.join(__dirname, "..");
const OUT = path.join(ROOT, "out", "new_slides_encoder.pptx");
const PANELS = path.join(ROOT, "out", "encoder_panels");
const P = JSON.parse(fs.readFileSync(path.join(PANELS, "panels.json"), "utf8"));
const M = JSON.parse(fs.readFileSync(path.join(ROOT, "docs", "streaming", "img", "encoder", "measurements.json"), "utf8"));
const SRC = M.source.name === "Synthetic underwater clip" ? "the synthetic underwater clip" : M.source.name;
const f2 = (x) => x.toFixed(2), f3 = (x) => x.toFixed(3);

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const H = makeHelpers(pres);
  const { col, text, box, card } = H;
  pres.defineSlideMaster({
    title: "MIA_CONTENT", background: { color: HEX.bg },
    objects: [
      { placeholder: { options: { name: "kicker", type: "body", x: 0.6, y: 0.32, w: 10, h: 0.3, fontSize: 12, bold: true, color: H.C.accent1, fontFace: "Arial", charSpacing: 2, margin: 0, valign: "middle" }, text: "" } },
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.66, w: 12.1, h: 0.85, fontSize: 32, bold: true, color: H.C.background1, fontFace: "Arial", margin: 0, valign: "middle", align: "left" }, text: "" } },
    ],
  });
  const content = (kicker, title, notes) => {
    const s = pres.addSlide({ masterName: "MIA_CONTENT" });
    s.addText(kicker.toUpperCase(), { placeholder: "kicker" });
    s.addText(title, { placeholder: "title" });
    s.addNotes(notes);
    return s;
  };
  // a row of real-encode crops: label above, measurement below, all native text
  const panels = (s, key, x, y, w, gap = 0.2, o = {}) => {
    let bottom = y;
    P[key].forEach((p, k) => {
      const px = x + k * (w + gap), h = (w * p.h) / p.w;
      const hi = o.highlight === k;
      text(s, p.title, { x: px, y, w, h: 0.32, fontSize: 14, bold: true, color: hi ? col.amber : col.cyan, align: "center", valign: "middle" });
      s.addImage({ path: path.join(PANELS, p.file), x: px, y: y + 0.36, w, h, altText: `${p.title}: ${p.sub} (${SRC})`, objectName: `${key}-img-${k}` });
      if (hi) s.addShape(pres.shapes.RECTANGLE, { x: px, y: y + 0.36, w, h, fill: { type: "none" }, line: { color: HEX.amber, width: 2 }, objectName: `${key}-hl-${k}` });
      text(s, p.sub, { x: px, y: y + 0.4 + h, w, h: 0.3, fontSize: 12, color: col.muted, align: "center", valign: "middle" });
      bottom = y + 0.7 + h;
    });
    return bottom;
  };
  const foot = (s, t, y = 6.28) => text(s, t, { x: 0.6, y, w: 12.1, h: 0.3, fontSize: 11, color: col.muted, italic: true });
  const takeaways = async (s, y, left, right, h = 1.75) => {
    await card(s, 0.6, y, 5.95, h, { ...left, titleColor: left.titleColor || col.cyan, bodySize: 14 });
    await card(s, 6.75, y, 5.95, h, { ...right, titleColor: right.titleColor || col.amber, bodySize: 14 });
  };
  const note = (lines) => lines.join(" ");

  // ======================================================================= A · after "why 4:2:0"
  {
    const s = content("Digital video fundamentals · the 1-pixel trap", "The 1-pixel bleed, on a real encode",
      note([`A pilot overlay (a red 1-pixel crosshair) drawn INTO a frame of ${SRC}, then encoded with x264 at CRF 16 twice: once in 4:4:4 (full-resolution colour) and once in 4:2:0. Shown ×10, nearest-neighbour, so you see real pixels.`,
        "In 4:2:0 each 2 × 2 block of pixels shares one colour sample. A 1-pixel line covers only half of its block, so the colour sample becomes the average of red and water: the line turns into a 2-pixel band at half the saturation. Brightness (luma) is still sharp, which is why the line is still there but no longer red.",
        "Same thing happens to thin colour-coded wires, coloured text and coloured laser dots.",
        "The fix: send clean video and draw the HUD on the pilot laptop after decoding (third panel). If a thin coloured detail really must survive, encode 4:4:4 (x264 High 4:4:4 profile), but most hardware decoders and browsers cannot play it, and it costs about 50 % more raw data.",
        "Re-make this picture from your own footage: python3 build/make_encoder_images.py --source your_dive.mp4"]));
    const b = panels(s, "chroma-bleed", 0.6, 1.7, 3.9, 0.2, { highlight: 1 });
    await takeaways(s, b + 0.15,
      { title: "Why it smears", bullets: ["4:2:0 keeps one colour sample per 2 × 2 pixels", "A 1-px line shares its sample with the water", "Brightness stays sharp; the red halves and spreads"] },
      { title: "What to do", bullets: ["Draw overlays on the laptop, after decoding", "4:4:4 keeps it, but few decoders can play it"] }, 1.7);
  }

  // ======================================================================= B · after "inter prediction"
  {
    const mv = M.motion;
    const s = content("Prediction · inter, measured", "Motion search on two real frames",
      note([`Two consecutive frames of ${SRC}. For every 16 × 16 block of the second frame we searched ±6 pixels in the first frame for the best match (sum of absolute differences), the same idea as x264's search, without sub-pixel steps.`,
        `Left: the vectors found (red, ×2.5 for visibility). The camera pans, so most vectors point the same way. Middle: what would be left to send if we just subtracted the previous frame (no search): mean error ${mv.error_without.toFixed(1)}. Right: what is left after moving each block by its vector: mean error ${mv.error_with.toFixed(1)}, ${Math.round((1 - mv.error_with / mv.error_without) * 100)} % less.`,
        "The bright dots that remain on the right are marine snow: particles that move on their own and have no match in the last frame. That residual is what costs bits underwater.",
        "Presets mostly change how hard this search tries (diamond vs hexagon vs exhaustive, sub-pixel refinement, number of reference frames). Slide on presets: the extra search buys a little quality for a lot of CPU."]));
    const b = panels(s, "motion-search", 0.6, 1.7, 3.9, 0.2, { highlight: 2 });
    await takeaways(s, b + 0.15,
      { title: "What the search buys", bullets: [`Error left to send: ${mv.error_without.toFixed(1)} → ${mv.error_with.toFixed(1)} (${Math.round((1 - mv.error_with / mv.error_without) * 100)} % less)`, "Send a vector + a small residual, not the block"] },
      { title: "What it cannot fix", bullets: ["Marine snow moves on its own: no match, so it stays", "Light and a stable camera save more than any preset"] }, 1.45);
  }

  // ======================================================================= C · after "entropy coding · loop filters"
  {
    const on = M.deblock_on, off = M.deblock_off;
    const s = content("Loop filters · on a real picture", "Deblocking: the same bits, fewer visible blocks",
      note([`The same clip encoded with x264 at CRF 40 (a starved bitrate, about ${f2(on.mbps)} Mb/s), once with the deblocking filter turned off (-x264-params no-deblock=1) and once with the default.`,
        `Off: you see the transform blocks, because each block was quantized on its own. On: the filter smooths block edges inside the coding loop, so the next frame is predicted from the smoothed picture too. SSIM ${f3(off.ssim)} → ${f3(on.ssim)} at the same bitrate.`,
        "The low-latency x264 recipe on the Raspberry Pi turns deblocking off to save CPU. That is fine at a healthy bitrate and visible when the tether is tight. If you see blocks, check the bitrate first, then whether deblocking is on.",
        "H.265 adds SAO; AV1 adds CDEF and loop restoration. Same idea: clean the picture before it becomes the reference."]));
    const b = panels(s, "deblocking", 0.6, 1.7, 4.1, 0.2);
    await card(s, 9.2, 2.06, 3.5, b - 2.36, { title: "What the filter does", titleColor: col.cyan, bodySize: 14, bullets: [
      "Smooths block edges after quantizing", "Inside the loop: the next frame predicts from the clean picture", `SSIM ${f3(off.ssim)} → ${f3(on.ssim)}, same bits`] });
    foot(s, "Turning it off saves CPU (Pi low-latency recipe). Fine at a healthy bitrate; visible when the tether is tight.", b + 0.2);
  }

  // ======================================================================= D–H · one knob at a time
  const kicker = (n) => `Encoder settings · one knob at a time (${n}/5)`;
  {
    const a = M.crf18, b2 = M.crf28, c = M.crf38, d = M.crf46;
    const s = content(kicker(1), "CRF: the quality dial, and what each step costs",
      note([`${SRC}, x264 veryfast, only CRF changes. Crops of the same frame, enlarged.`,
        `CRF 18 → 28 cut the bitrate ${f2(a.mbps / b2.mbps)}× (${f2(a.mbps)} → ${f2(b2.mbps)} Mb/s) and SSIM went ${f3(a.ssim)} → ${f3(b2.ssim)}: most people cannot tell. CRF 38 and 46 save little more in absolute bits and the blocks appear.`,
        "Rule of thumb: +6 CRF (or +6 QP) doubles the quantizer step and roughly halves the bits. The saving is biggest at the top of the ladder: the first steps are almost free.",
        "CRF is quality-based: on a busy scene (marine snow, a fast pan) the bitrate jumps. For the live tether, pair it with a cap (-maxrate and -bufsize), see the CRF vs bitrate slide.",
        "In the session: ask which panel they would accept as a pilot. That is the number to put in the configuration, decided by eye, then checked with SSIM."]));
    const bt = panels(s, "knob-crf", 0.6, 1.7, 2.875, 0.2, { highlight: 1 });
    await takeaways(s, bt + 0.2,
      { title: "What it does", bullets: [`18 → 28: ${f2(a.mbps / b2.mbps)}× fewer bits, SSIM ${f3(a.ssim)} → ${f3(b2.ssim)}`, "+6 CRF ≈ half the bits; the first steps are almost free", "Past ≈ 35 the blocks show"] },
      { title: "How to set it", bullets: ["Pick the highest CRF the pilot accepts in a blind test", "Live tether: add -maxrate/-bufsize so peaks are capped"] });
  }
  {
    const x = M.codec_libx264, h5 = M.codec_libx265, av = M.codec_libsvtav1, mj = M.codec_mjpeg;
    const s = content(kicker(2), "Same starved bitrate, four codecs",
      note([`${SRC}. H.264 (x264 veryfast), H.265 (x265 veryfast) and AV1 (SVT-AV1 preset 10) were each asked for 150 kb/s with a 150 kb buffer; they delivered ${f2(x.mbps)}, ${f2(h5.mbps)} and ${f2(av.mbps)} Mb/s (rate control undershoots on an easy clip; the numbers under each picture are what was actually sent).`,
        `At about the same bits, the newer codecs keep more detail: SSIM ${f3(x.ssim)} → ${f3(h5.ssim)} → ${f3(av.ssim)}. MJPEG cannot go that low at all: at its LOWEST quality setting it still needed ${f2(mj.mbps)} Mb/s, about ${Math.round(mj.mbps / x.mbps)}× H.264, and looks worse (SSIM ${f3(mj.ssim)}), because every frame is a JPEG with no prediction from the last one.`,
        "Codec choice is decided by what the ROV computer can encode in real time and what the laptop can decode, not by these pictures alone: AV1 at this speed used far more CPU. See the hardware section.",
        "Why it matters on the tether: at a tight budget, H.264 → H.265 is the difference between blocks and a usable picture. MJPEG only makes sense when the bandwidth is plentiful and the CPU is not."]));
    const bt = panels(s, "knob-codec", 0.6, 1.7, 2.875, 0.2, { highlight: 3 });
    await takeaways(s, bt + 0.2,
      { title: "At ≈ the same bits", bullets: [`SSIM: H.264 ${f3(x.ssim)} · H.265 ${f3(h5.ssim)} · AV1 ${f3(av.ssim)}`, "Each generation keeps more detail per bit"] },
      { title: "MJPEG cannot go that low", titleColor: col.rose, bullets: [`Lowest quality still ${f2(mj.mbps)} Mb/s (≈ ${Math.round(mj.mbps / x.mbps)}× H.264)`, "No prediction between frames: every frame pays in full", "Choose by encoder CPU + laptop decoder, then by picture"] });
  }
  {
    const u = M.preset_ultrafast, v = M.preset_veryfast, md = M.preset_medium, sl = M.preset_slow;
    const s = content(kicker(3), "Presets: same bitrate, more search, a little more quality",
      note([`${SRC}, x264 capped at 500 kb/s, only the preset changes.`,
        `ultrafast → veryfast is the big step: SSIM ${f3(u.ssim)} → ${f3(v.ssim)}. ultrafast turns off most tools (CABAC, deblocking strength, sub-pixel search), so at the same bitrate it shows blocks. veryfast → medium → slow adds only ${f3(sl.ssim - v.ssim)} SSIM: invisible in the picture.`,
        "The cost is on the CPU chart of Experiment 4: each step to the right costs more CPU per frame than the one before. On the ROV computer that CPU is what limits how many cameras you can encode.",
        "So for live ROV video: veryfast (or superfast) with -tune zerolatency is the usual knee. Slower presets belong to recordings that are encoded after the dive."]));
    const bt = panels(s, "knob-preset", 0.6, 1.7, 2.875, 0.2, { highlight: 1 });
    await takeaways(s, bt + 0.2,
      { title: "What it does", bullets: [`ultrafast → veryfast: SSIM ${f3(u.ssim)} → ${f3(v.ssim)}`, `veryfast → slow: + ${f3(sl.ssim - v.ssim)}, invisible`, "Slower = more search for the same bits"] },
      { title: "How to set it", bullets: ["Live: veryfast or superfast + zerolatency", "CPU per frame grows fast (Experiment 4 chart)", "Slow presets: for recordings after the dive"] });
  }
  {
    const r1 = M.res_1280, r2 = M.res_640, r3 = M.res_320;
    const s = content(kicker(4), "At a starved bitrate, send fewer pixels",
      note([`${SRC}, x264 veryfast capped at 150 kb/s. The same bits spent on 1280×720, 640×360 or 320×180, then all scaled back to 1280×720 on the laptop, as the pilot would see them.`,
        `At this bitrate the full-resolution stream runs out of bits and shows blocks (SSIM ${f3(r1.ssim)}); half resolution looks cleaner (${f3(r2.ssim)}), quarter resolution is soft but calm (${f3(r3.ssim)}).`,
        "Careful with the conclusion: SSIM on this soft synthetic clip prefers blur. On real footage with text on a gauge or a thin crack, the pixels may matter more. Re-make this slide from your own footage (make_encoder_images.py --source) before you decide.",
        "This is the opposite of the resolution trap (MJPEG at high resolution through USB). Here the resolution is reduced on purpose, after capture, to fit the tether."]));
    const bt = panels(s, "knob-resolution", 0.6, 1.7, 3.9, 0.2, { highlight: 1 });
    await takeaways(s, bt + 0.15,
      { title: "Same 150 kb/s", bullets: [`1280×720: blocks · SSIM ${f3(r1.ssim)}`, `640×360: cleaner · SSIM ${f3(r2.ssim)}`] },
      { title: "Check with your footage", bullets: ["Gauge text and thin cracks need pixels", "Decide with --source on real dive video"] }, 1.4);
  }
  {
    const a = M.noise_False, b = M.noise_True;
    const s = content(kicker(5), `Sensor noise: same CRF, ${(b.mbps / a.mbps).toFixed(1)}× the bits`,
      note([`${SRC} encoded at CRF 23, once as filmed and once with added temporal noise, like a camera pushing its gain in low light.`,
        `The noise looks harmless but it is random: nothing predicts it, so the encoder must send it. Bitrate went ${f2(a.mbps)} → ${f2(b.mbps)} Mb/s (${(b.mbps / a.mbps).toFixed(1)}×) at the same CRF.`,
        "If the bitrate is capped instead (the live tether), the bitrate stays put and the quality falls: the noise takes the bits the pipe edges needed.",
        "Fixes in order of value: more light on the scene (cheapest bits you will ever buy), fix the camera gain/exposure instead of auto, then a light denoise before encoding (ffmpeg -vf hqdn3d=2:1:3:3) if CPU allows."]));
    const bt = panels(s, "knob-noise", 0.6, 1.7, 3.9, 0.2, { highlight: 1 });
    await card(s, 8.8, 2.06, 3.9, bt - 2.36, { title: "Noise is random detail", titleColor: col.rose, bodySize: 14, bullets: [
      `${f2(a.mbps)} → ${f2(b.mbps)} Mb/s at CRF 23`, "Capped bitrate: quality drops instead", "Light the scene, fix the gain", "Then denoise: -vf hqdn3d"] });
    foot(s, "Murky, dark water is the most expensive video there is. Lights are a bitrate setting.", bt + 0.2);
  }

  await pres.writeFile({ fileName: OUT });
  await writeTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
