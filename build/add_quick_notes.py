"""Put a short QUICK NOTES cue card at the top of every slide's speaker notes.

The detailed notes stay underneath. Running it again replaces the cue cards instead of adding a second copy.

    python3 build/add_quick_notes.py presentation/MIA_Video_Streaming.pptx

Edit the cue cards in QUICK below. Lines starting with "Ask:" and "Next:" are printed as they are; every other
line becomes a bullet. Keep each card to what you need at a glance: 3 to 5 short lines.
"""
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

HEADER = "QUICK NOTES"
DIVIDER = "────────── details ──────────"

QUICK = {
    1: ["Hook: who has felt the video lag or freeze at the worst moment?",
        "Today: turn that feeling into numbers and decisions.",
        "Next: the agenda."],
    2: ["Seven parts, an activity every 20–30 min.",
        "Understand → measure → design.",
        "Keep it under a minute."],
    3: ["Video is the pilot's main sensor.",
        "Four cameras, four jobs: pilot, manipulator, inspection, rear.",
        "Each job needs different quality and latency.",
        "Ask: lose depth reading vs lose main camera: which ends the task?"],
    4: ["Video = 65 % of internet traffic (2022).",
        "Each codec generation ≈ half the bits.",
        "Nobody notices compression until it fails."],
    5: ["Section 01: first the water, then our own system."],
    6: ["Water kills red, adds haze, specks, noise.",
        "Random detail can't be predicted, so it costs bits.",
        "Murky water = the most expensive video.",
        "Point at the image: our synthetic clip."],
    7: ["Same physics as industry; the gap is discipline.",
        "Measuring, budgeting, testing, pilot tests: all free.",
        "Be respectful: volunteers, built in months."],
    8: ["Key question: who encodes, camera or computer?",
        "A: USB → SBC encodes (bottleneck: encoder, USB).",
        "B: camera encodes, SBC forwards (transcode = expensive).",
        "Ask: which one are we? How would you prove it?"],
    9: ["USB 2.0 = 480 Mb/s per BUS, cameras reserve it.",
        "IP camera: own port, 100 m, encodes itself, PoE 15.4 W.",
        "8 cameras work either way: choose where encoding happens.",
        "Prove it: lsusb -t, v4l2-ctl, ffprobe."],
    10: ["Seven stages: capture → encode → packetize → network → buffer → decode → render.",
         "Latency hides in encoder and buffers, not the cable.",
         "8 streams = 8 decoders on the laptop."],
    11: ["Codec = folded clothes, container = box, protocol = delivery.",
         "RTSP is a remote control; video travels on RTP.",
         "\"We stream in MP4\" is wrong."],
    12: ["Section 02: count the bits. The most useful skill today."],
    13: ["R = W × H × bpp × fps.",
         "Do it live: 1920×1080×24×30 = 1.49 Gb/s.",
         "Pause: one camera > gigabit Ethernet.",
         "Small b = bits, big B = bytes."],
    14: ["Log scale: say it.",
         "Raw YUYV fits USB 2.0 only at ~640×480@30 (147 Mb/s).",
         "That's why webcams switch to MJPEG; 3rd camera fails."],
    15: ["1 hour raw 1080p = 672 GB ≈ EGP 1,150.",
         "H.264 5 Mb/s = 2.25 GB ≈ EGP 3.85 (≈ 300× cheaper).",
         "Monthly 100 GB lasts 9 minutes of raw video.",
         "Check WE prices the day before."],
    16: ["Activity 1, 15 min, teams of 3–5, one card each.",
         "Raw → compressed → +overhead → vs 70 % → verdict → measurement.",
         "A: USB bus over (2 cameras fit). C: Nano encoder over.",
         "Next: reveal with the Encoding Lab budget tab."],
    17: ["Raw 332 → MJPEG 8.2 → H.264 1.5 Mb/s (720p30).",
         "MJPEG → H.264 saved 8× with no detail lost.",
         "Better codec beats smaller picture."],
    18: ["Bitrate (encoder) · capacity (link) · throughput (measured) · headroom (≥ 30 %).",
         "RTP/UDP adds ~5 %, MPEG-TS ~7 %.",
         "Budget = 70 % of measured throughput."],
    19: ["Section 03: how an encoder throws away 99 % of the bits."],
    20: ["Predict → transform → quantize → pack.",
         "Only quantization loses quality.",
         "Rate control picks the quantizer: the knob you turn most.",
         "Lost reference → wrong until next I-frame."],
    21: ["4:4:4 = 24 bpp, 4:2:2 = 16, 4:2:0 = 12.",
         "Half the data before any compression.",
         "Browsers and HW decoders expect 4:2:0 8-bit."],
    22: ["120 M rods vs 6 M cones: we see brightness detail, not colour.",
         "Underwater even better: red is already gone.",
         "Trap: thin coloured lines bleed → draw overlays after decoding."],
    23: ["Repeats in space (intra) and time (inter) are free.",
         "H.265 blocks up to 64×64: open water = one cheap block.",
         "Marine snow, noise, caustics can't be predicted → bits."],
    24: ["Guess the block from neighbours, send mode + error.",
         "H.264 9 modes, H.265 35, AV1 56+.",
         "I-frames are 5–8× an average frame: the tether spike."],
    25: ["Search the last frame, send motion vector + residual.",
         "Presets = how hard it searches.",
         "B-frames look at the future → latency."],
    26: ["DCT gathers energy top-left.",
         "Quantize: 64 values → 11 numbers, 53 zeros.",
         "+6 QP ≈ half the bitrate."],
    27: ["CABAC saves ~10 % bits, costs CPU.",
         "Deblocking hides blocks, costs CPU.",
         "Pi 5 low-latency: both off, ~62–90 % of a core for 1080p30."],
    28: ["I = big, standalone · P = small · B = waits for future.",
         "Measured: I 45 kB vs P 12 kB (~4×).",
         "Short GOP = fast join and recovery, more bits."],
    29: ["CRF: fixed quality, bitrate jumps → recording.",
         "Bitrate + VBV: capped → live tether.",
         "CRF 23 avg 1.5 peaked 2.6 Mb/s; VBV peaked 2.0.",
         "Best codec depends on the operating point."],
    30: ["Netflix: 191 B hours × ~2 GB × $0.005–0.03/GB.",
         "1 % fewer bits ≈ $19–115 M a year (estimate).",
         "They spend CPU to save bits; we spend bits to save latency."],
    31: ["On demand: slow per-shot software encodes.",
         "Live (Twitch): fast hardware, fixed ladders.",
         "Our ROV is live."],
    32: ["Never say \"X is better\" without \"for what\".",
         "H.264 = live default · MJPEG = aux · H.265 if HW · AV1 later.",
         "Pi 5 has NO H.264 hardware encoder."],
    33: ["Codec = pictures, container = box + timestamps + index.",
         "Plain MP4 dies in a power cut (index at the end).",
         "Record MKV / fragmented MP4 / TS; remux later with -c copy."],
    34: ["MJPEG: 4.7× the bits, 0 frames held, 1.3 % of a core to copy.",
         "Aux cameras ≤ 640×480 @ 10–15 fps, CV debug, fallback.",
         "Pilot camera stays H.264."],
    35: ["Ask the camera for the size: free (~1 % core).",
         "Resize in software: decode + scale + encode (~13 % core per camera).",
         "Check sizes: v4l2-ctl --list-formats-ext.",
         "Size not offered? Encode to H.264 instead."],
    36: ["FFmpeg: copy MJPEG for 1.3 % of a core, encode once, RTP, record.",
         "Python mjpeg-streamer: re-encodes per viewer, duplicate frames.",
         "FFmpeg's one gap: one HTTP viewer per process."],
    37: ["Four tested recipes: browser passthrough, tee, CV debug, topside fan-out.",
         "-content_type is required for the browser.",
         "One RTP copy on the tether, many viewers topside."],
    38: ["Each knob trades bandwidth, quality, latency, CPU.",
         "veryslow = 36× the CPU of ultrafast for ~half the bits.",
         "Live on an SBC: ultrafast–veryfast + zerolatency."],
    39: ["Lost packets damage until the next I-frame.",
         "GOP 30: ~0.6 s · GOP 150: up to 3.6 s · intra refresh: 0.6 s, no spikes.",
         "Slow camera switch often = long GOP."],
    40: ["PSNR cheap but blind · SSIM structure · VMAF trained on TV.",
         "Activity 3: 5 clips, rank blind, guess bitrate, reveal.",
         "Metrics compare; the pilot decides."],
    41: ["Section 04: who does the work, how bits travel, how long it takes."],
    42: ["Software: flexible, eats CPU and heat.",
         "Hardware: almost free, fixed capacity.",
         "Listed ≠ working: always do a 1-second test encode."],
    43: ["Nano: HW encode 4×1080p30 (GStreamer nvv4l2h264enc).",
         "Pi 5: no HW encoder, ~0.62–0.9 core per 1080p30.",
         "Orin Nano has NO encoder either: cat /etc/nv_tegra_release."],
    44: ["Encode as early as possible: camera → SBC HW → SBC SW.",
         "Encoding on the laptop saves zero tether bandwidth.",
         "Measure before deciding."],
    45: ["Pi 5 vs Nano: who encodes?",
         "Cameras encode → Pi 5. SBC encodes many → Nano.",
         "Nano EOL, modules until Jan 2027.",
         "Soak test before buying."],
    46: ["2023: stream died from heat, in front of the judges.",
         "Throttle at 80 °C; a fan in a sealed hull doesn't help.",
         "Measure · heat path to hull · reduce · soak test · show temp (warn 75 °C)."],
    47: ["Pilot: RTP/UDP or WebRTC. Never HLS/DASH.",
         "TCP waits: delay grows after loss.",
         "Bridge: RTSP → MediaMTX → WebRTC → browser."],
    48: ["ESTIMATES: MJPEG 91 ms · H.264 defaults 2.4 s · zerolatency 128 ms.",
         "FPS ≠ latency.",
         "Show the ms-clock method."],
    49: ["x264 defaults hold 41 frames (~1.4 s); zerolatency 0.",
         "Jitter buffer: fewer late frames, more latency.",
         "Pick 30–60 ms on a clean tether."],
    50: ["8 main = 19.8 Mb/s · 1 main + 7 sub = 5.4 Mb/s (~27 %).",
         "Substream 640×360@15 ≈ 0.42 Mb/s.",
         "Paused cameras must look paused."],
    51: ["Measure → budget (70 %) → minimums by priority → top up → show.",
         "Pilot min 1.5, manipulator 0.8, aux 0.15 Mb/s.",
         "Manipulator becomes priority 1 while gripping."],
    52: ["CV only sees what the encoder kept.",
         "Blocks kill SLAM corners; old frames make autonomy overshoot.",
         "CV gets its own stream or the raw frames."],
    53: ["Eight tools: ffprobe, v4l2-ctl/lsusb, ethtool, iperf3, iftop, tegrastats, webrtc-internals, ms clock.",
         "Every claim needs a measurement."],
    54: ["One cause, one stage: find the stage.",
         "30 fps says nothing about latency.",
         "Measure each stage or the tether gets blamed."],
    55: ["Start from the pilot's symptom → first suspect → inspect.",
         "Pick three rows they lived: 3rd camera, growing delay, freeze.",
         "Every row has an appendix page."],
    56: ["Nine categories of numbers.",
         "Add frame age: it catches stale frames fps hides.",
         "Most already exist: Encoding Lab + rtp_probe.py."],
    57: ["Optical ms clock = the truth, no clock sync.",
         "Overlay and stage timestamps show which stage grew.",
         "Always median + p95."],
    58: ["15 diagnostics; most exist today (Lab, probe, manual).",
         "Missing ones are GUI receiver timers: first software task.",
         "Note: the tags add up to 10 existing, not 9."],
    59: ["Pilot sees 4 numbers + 6 lights, not 40 metrics.",
         "Latency + queue up together = buffering.",
         "Loss up with thrusters = electrical noise."],
    60: ["Activity 2, 20 min: read the scenario aloud.",
         "≥ 5 hypotheses, each with a measurement.",
         "Expect: USB, CPU, heat, link speed, TCP, buffer, laptop, power.",
         "Punchline: lowering resolution fixes almost none."],
    61: ["Check in pipeline order; first ❌ = the cause.",
         "45 checks, 25 automatic in 10 s (rov_healthcheck.sh).",
         "Example: under-voltage → USB resets → freezes.",
         "Paste the output into the bug report."],
    62: ["Measure → stop wasting → stream smart → design latency → design failure → verify.",
         "Resolution is the last lever.",
         "Good slide to leave up for questions."],
    63: ["27 experiments, 6 badges, 775 points, 1 boss level.",
         "Predict → measure → explain → post.",
         "Ask: who wants to be the first Latency Hunter?"],
    64: ["15 / 30 / 50 points; bonuses +5 +10 +20 +10.",
         "Cadet → Technician 100 → Engineer 250 → Chief 450 + 3 badges.",
         "Wrong predictions cost nothing."],
    65: ["E0 inventory first (required).",
         "Point at E14 (UI lies?), E21 (3rd camera), E16 (2023 heat).",
         "Dots: green 15, amber 30, red 50."],
    66: ["Everyone writes a guess in ms first.",
         "ms_clock.html, photo, subtract, 10×: 567 − 441 = 126 ms.",
         "Target ≤ 150 median, ≤ 250 worst.",
         "Do it live if there is time."],
    67: ["Break it on the bench before the pool does.",
         "netem loss, tbf squeeze, kill -STOP.",
         "Props off · tc hits control too · always tc qdisc del."],
    68: ["Eye chart 40 → 5 mm, 1 m from the camera, under water.",
         "Step 8 → 4 → 2 → 1 → 0.5 Mb/s.",
         "Lowest readable bitrate = requirement N2.",
         "Ask: what's the smallest marking in this year's mission?"],
    69: ["W1 baseline · W2 latency · W3 chaos · W4–5 pool · W6 advanced · W7–12 boss.",
         "Boss scored: requirements 30, evidence 20, failures 20, pilot 15, docs 15.",
         "TONIGHT: E0 + E1."],
    70: ["Leaders run 90 min a week (Leader_Guide.md).",
         "Facilitator · safety officer · referee.",
         "Cut measuring, never the debrief.",
         "Ask leaders to book their first session now."],
    71: ["Field guide: 45 problems in 7 families.",
         "Use it from the matrix (slide 55); don't present page by page."],
    72: ["Latency: remove the biggest stage.",
         "Drift: a queue that only grows (30 vs 29.7 fps = +10 ms/s).",
         "Jitter: wired tether, buffer = measured p95."],
    73: ["Stale frame: STALE badge after 500 ms.",
         "Pacing: vsync, 1-frame queue.",
         "Bursts: UDP, CPU < 70 %, drop late frames."],
    74: ["Encoder hold: zerolatency, -bf 0.",
         "Display lag: game mode or a monitor.",
         "31 frames here vs 41 on slide 49: both ≈ 1 s."],
    75: ["Blocking, ringing, blur = too few bits.",
         "More bits for that camera, better light, overlays after decoding."],
    76: ["Pixelation: switch to main stream when full screen.",
         "Banding: a bit more bitrate or 10-bit.",
         "Keyframe pile-up: stagger cameras, intra refresh."],
    77: ["Loss smears until a keyframe: fix the link first.",
         "Green blocks: keyframe + SPS/PPS on join.",
         "Buffering: never HLS for piloting."],
    78: ["Dropouts: strain relief, auto-reconnect, LOST state.",
         "Bad pair: 94 → 9 Mb/s. Check ethtool.",
         "Fragmentation: RTP payload 1200–1400 bytes."],
    79: ["Rolling shutter, ghosting, motion blur.",
         "Fixes: global shutter for CV, less noise reduction, more light."],
    80: ["Judder: 30/60 fps cameras on 60 Hz.",
         "Interlacing: deinterlace (yadif).",
         "Strobing thrusters: trust telemetry rpm."],
    81: ["Haze: closer, side light.",
         "Backscatter: lights away from the lens.",
         "Noise: 1.41 → 5.12 Mb/s at the same quality."],
    82: ["Focus under water and lock it.",
         "Manual exposure for the lit target.",
         "Manual white balance at working depth."],
    83: ["Condensation: seal dry, silica gel.",
         "PWM banding: constant-current drivers.",
         "Flicker: set power_line_frequency."],
    84: ["Tearing: vsync.",
         "Black frames: HEVC in a browser shows black, no error → H.264.",
         "Aspect: letterbox, never stretch."],
    85: ["Resolution switch: fixed output size.",
         "Colour range: tag 16–235, right matrix.",
         "Telemetry runs ahead of video: delay it or show ages."],
    86: ["Thermal throttling = our 2023 failure.",
         "USB bandwidth = the 3rd camera."],
    87: ["CPU saturation: hardware encoder, < 70 % CPU.",
         "Clock drift: chrony with topside as server.",
         "Close on slide 62 or 69, not here."],
}

NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"


def run_xml(text, bold=False, colour="000000"):
    return (f'<a:r><a:rPr lang="en-US" sz="2000" b="{1 if bold else 0}" dirty="0"><a:solidFill><a:srgbClr val="{colour}"/>'
            f'</a:solidFill><a:latin typeface="Arial"/></a:rPr><a:t>{escape(text)}</a:t></a:r>')


def para(text, bold=False, colour="000000"):
    return f'<a:p><a:pPr indent="0"><a:buNone/></a:pPr>{run_xml(text, bold, colour)}</a:p>'


def card_xml(lines):
    out = [para(HEADER, bold=True, colour="C00000")]
    for line in lines:
        if line.startswith(("Ask:", "Next:")):
            out.append(para(line, bold=True))
        else:
            out.append(para("• " + line))
    out.append(para(DIVIDER, colour="808080"))
    return "".join(out)


def add_card(notes_xml, lines):
    """Insert the card at the top of the notes body; remove an older card first."""
    m = re.search(r'(<p:sp>(?:(?!</p:sp>).)*?<p:ph type="body"[^>]*/>(?:(?!</p:sp>).)*?<p:txBody>)(.*?)(</p:txBody>)', notes_xml, re.S)
    if not m:
        raise ValueError("no notes body placeholder")
    body = m.group(2)
    head = re.match(r'\s*(?:<a:bodyPr[^>]*/>|<a:bodyPr[^>]*>.*?</a:bodyPr>)\s*(?:<a:lstStyle\s*/>|<a:lstStyle>.*?</a:lstStyle>)?', body, re.S)
    prefix, rest = (head.group(0), body[head.end():]) if head else ("", body)
    paras = re.findall(r'<a:p>.*?</a:p>|<a:p/>', rest, re.S)
    if "".join(paras) != rest.strip():
        raise ValueError("unexpected content in the notes body")
    texts = ["".join(re.findall(r"<a:t>(.*?)</a:t>", p)) for p in paras]
    if texts and texts[0] == HEADER and escape(DIVIDER) in texts:       # older card: drop it and its divider
        paras = paras[texts.index(escape(DIVIDER)) + 1:]
    return notes_xml[:m.start(2)] + prefix + card_xml(lines) + "".join(paras) + notes_xml[m.end(2):]


def main(deck):
    deck = Path(deck)
    tmp = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(deck) as z:
        z.extractall(tmp)
        names = z.namelist()
    pres = (tmp / "ppt/presentation.xml").read_text()
    rels = (tmp / "ppt/_rels/presentation.xml.rels").read_text()
    order = re.findall(r'<p:sldId [^>]*r:id="(rId\d+)"', pres)
    targets = {m.group(1): m.group(2) for m in re.finditer(r'<Relationship [^>]*?Id="(rId\d+)"[^>]*?Target="([^"]+)"', rels)}
    targets.update({m.group(2): m.group(1) for m in re.finditer(r'<Relationship [^>]*?Target="([^"]+)"[^>]*?Id="(rId\d+)"', rels)})
    done = 0
    for n, rid in enumerate(order, 1):
        if n not in QUICK:
            continue
        slide = Path(targets[rid]).name
        srel = (tmp / "ppt/slides/_rels" / f"{slide}.rels").read_text()
        notes = re.search(r'Target="\.\./notesSlides/(notesSlide\d+\.xml)"', srel)
        if not notes:
            print(f"slide {n}: no notes page, skipped")
            continue
        path = tmp / "ppt/notesSlides" / notes.group(1)
        path.write_text(add_card(path.read_text(), QUICK[n]))
        done += 1
    out = deck.with_suffix(".tmp.pptx")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name in names:                       # keep the original part order ([Content_Types].xml first)
            if not name.endswith("/"):
                z.write(tmp / name, name)
    shutil.move(out, deck)
    shutil.rmtree(tmp)
    print(f"quick notes on {done} of {len(order)} slides")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "presentation/MIA_Video_Streaming.pptx")
