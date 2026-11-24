"""The video-diagnostics field guide: one entry per phenomenon. Single source for the doc and the slides.

    python3 build/diagnostics_catalog.py    # writes docs/streaming/video-diagnostics.md and out/diagnostics.json

Fields: name · img (docs/streaming/img/diagnostics/<img>.jpg, or None + code) · see · why · rov (why it matters on OUR ROV) ·
check (how to confirm) · fix. Keep each field to one sentence: the slides print them as they are.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEAS = json.loads((ROOT / "docs/streaming/img/diagnostics/measurements.json").read_text())

GROUPS = [
    ("timing", "Timing and latency", "The picture is late, uneven or stuck, even though FPS looks fine."),
    ("compression", "Compression", "The encoder had too few bits for what the camera sees."),
    ("network", "Network and transport", "Bits were lost, late or never sent."),
    ("motion", "Motion", "Something moves faster than the camera, encoder or screen can follow."),
    ("camera", "Camera and optics", "The problem is in the picture before any encoding: water, light, lens, sensor."),
    ("display", "Display and sync", "The frames arrive fine; showing them goes wrong."),
    ("system", "The ROV computer", "The hardware runs out of something: heat, USB, CPU, a shared clock."),
]

C = [
    # ------------------------------------------------------------------ timing
    dict(id="g2g", group="timing", name="Glass-to-glass latency", img="glass-to-glass",
         see="The picture is always behind reality: the gripper closes, the video shows it a moment later.",
         why="Every stage adds delay: exposure, encoder look-ahead, network, jitter buffer, decode and the display queue.",
         rov="Above ≈ 150 ms pilots over-correct; a manipulator grab becomes trial and error.",
         check="Film a ms clock on the pilot laptop, photograph camera view and clock together, 10 repeats, report median and worst.",
         fix="Measure each stage, then remove the biggest: zerolatency, no B-frames, small jitter buffer, UDP, game-mode display."),
    dict(id="drift", group="timing", name="Latency drift", img="latency-drift",
         see="The stream starts sharp, then the delay grows minute by minute.",
         why="Frames arrive faster than they are shown, so a queue somewhere only grows (a 30 vs 29.7 fps mismatch adds 10 ms every second).",
         rov="After 10 minutes of a dive the pilot can be seconds behind without noticing.",
         check="Plot latency over 10 minutes and queue depth at every stage; a straight rising line is a queue, not the network.",
         fix="Bound every queue to 1–2 frames and drop the oldest frame; for low latency use sync=false / no-buffer on the player."),
    dict(id="jitter", group="timing", name="Jitter", img="jitter",
         see="Motion is uneven: some frames come early, some late, although the average is right.",
         why="Packets and frames take different times through switches, Wi-Fi, CPU scheduling and the encoder.",
         rov="The jitter buffer must be as deep as the worst jitter, and every ms of buffer is a ms of latency.",
         check="RFC 3550 jitter from rtp_probe.py or chrome://webrtc-internals; frame-interval histogram at the receiver.",
         fix="Wired tether, no Wi-Fi hop, QoS or a dedicated video link, then size the jitter buffer to the measured p95."),
    dict(id="stale", group="timing", name="Frozen / stale frame", img="stale-frame",
         see="The picture stops but the app looks alive: same frame, FPS counter still says 30.",
         why="Capture, network or decoder stopped delivering, and the renderer keeps redrawing the last frame it has.",
         rov="A still scene and a dead stream look identical: the pilot keeps driving on an old picture.",
         check="Show the age of the displayed frame (now − capture timestamp) and the time since the last packet.",
         fix="Show a STALE badge after 500 ms without a new frame, and LOST after a few seconds; never show success the system has not confirmed."),
    dict(id="pacing", group="timing", name="Uneven frame pacing", img="frame-pacing",
         see="Panning looks jerky although the counter reports a steady 30 fps.",
         why="Frames are shown for 17, 50, 17, 50 ms: the average is right, the rhythm is not (vsync, timer resolution, bursty delivery).",
         rov="Jerky motion makes small, slow manipulator moves hard to judge.",
         check="Log presentation timestamps and plot the intervals; the counter alone hides this.",
         fix="Present on vsync with a 1-frame queue, match camera fps to the display, avoid timers coarser than the frame time."),
    dict(id="burst", group="timing", name="Frame bursts", img="frame-burst",
         see="The video freezes for a moment, then fast-forwards through several frames.",
         why="Frames were held somewhere (a congested switch, a TCP retransmission, a busy CPU) and released together.",
         rov="The pilot loses 200–300 ms of picture, then sees it too fast to use.",
         check="Frame arrival timestamps at the receiver: look for a gap followed by several frames within a few ms.",
         fix="Use UDP for live video, keep the CPU below 70 %, and drop late frames instead of playing them all."),
    dict(id="hold", group="timing", name="Encoder hold-back", img="encoder-hold",
         see="A constant delay of about a second appears after switching encoder or preset.",
         why="x264 defaults use look-ahead, B-frames and frame threads; it holds 30+ frames before the first output.",
         rov="Measured in the Lab: defaults held 31 frames (≈ 1047 ms) at 720p30; -tune zerolatency held 0.",
         check="Encoding Lab → Live camera: the 'held' metric; or count frames in vs packets out.",
         fix="-tune zerolatency (x264), -tune ull / -delay 0 / -bf 0 (NVENC), -bf 0 for every live encoder."),
    dict(id="dlag", group="timing", name="Display lag", img="display-lag",
         see="The video is behind the telemetry or the mouse pointer on the same screen.",
         why="After decoding, frames wait in the app's render queue, the compositor and the TV's picture processing.",
         rov="A TV used as pilot monitor can add 30–60 ms by itself.",
         check="Film the pilot screen and a ms clock on a second screen; compare a game-mode and a normal display.",
         fix="Game mode on TVs, a monitor instead of a TV, 1-frame render queue, fullscreen to skip the compositor."),
    # ------------------------------------------------------------------ compression
    dict(id="blocking", group="compression", name="Blocking / macroblocking", img="blocking",
         see="Square tiles appear, worst in busy scenes and right after the camera moves.",
         why="Too few bits: the quantizer is so coarse that each block becomes one flat colour; the deblocking filter can only hide part of it.",
         rov="Marine snow and moving sediment eat bits, so blocks appear exactly when the pilot needs detail.",
         check="Encoding Lab → Encode at your bitrate: Frame compare with Diff ×8; check QP and bits per pixel.",
         fix="More bitrate for that camera, fewer pixels or fps for it, a better codec (H.265/AV1 in hardware), or better lighting."),
    dict(id="ringing", group="compression", name="Ringing / mosquito noise", img="ringing",
         see="Shimmering dots and halos around sharp edges: text, gauges, cable outlines.",
         why="Quantization removes the high frequencies that make an edge sharp; what remains oscillates around it.",
         rov="Gauge needles and printed markings (the things you inspect) are high-contrast edges.",
         check="Zoom on an edge in Frame compare; MJPEG at low quality shows it most.",
         fix="Raise quality for that camera, avoid sharpening in the camera (it adds edges to encode), draw text overlays after decoding."),
    dict(id="blur", group="compression", name="Blur / loss of detail", img="blur",
         see="Fine detail disappears, especially while the ROV or the object moves.",
         why="A bitrate cap forces the encoder to drop detail; the deblocking filter smooths what is left.",
         rov="Cracks, corrosion and small text on a prop vanish during the moment the pilot is looking for them.",
         check="SSIM / VMAF in the Encoding Lab at your real bitrate; compare still and moving parts of the clip.",
         fix="Bitrate for the camera that needs detail (main stream), lower fps rather than resolution for inspection cameras."),
    dict(id="pixelation", group="compression", name="Pixelation", img="pixelation",
         see="The picture looks like coarse squares even without movement.",
         why="A small stream is scaled up to a big window (a 640×360 substream shown full screen), or the encoder was given very few pixels.",
         rov="Substreams are for thumbnails; shown full screen they look broken.",
         check="Compare stream resolution with window size; ffprobe the stream.",
         fix="Switch to the main stream when a camera goes full screen; scale with bilinear or better, never nearest."),
    dict(id="banding", group="compression", name="Colour banding", img="banding",
         see="Smooth gradients (open water, a lit wall) turn into visible steps.",
         why="8-bit video has 256 levels; quantization merges neighbouring levels in flat areas into wide bands.",
         rov="Open water is one big gradient, so banding shows on almost every camera.",
         check="Look at a flat gradient; banding grows as QP rises.",
         fix="A little more bitrate, x264 aq-mode / psy settings, 10-bit H.265 where hardware supports it, keep some sensor noise (it dithers)."),
    dict(id="iframe", group="compression", name="Keyframe pile-up", img="keyframe-burst",
         see="Periodic hiccups or latency spikes once per GOP, worse with more cameras.",
         why=f"A keyframe is ≈ {MEAS['iframe_ratio']}× a normal frame (measured); cameras started together send their keyframes in the same 33 ms.",
         rov="On a thin tether the combined burst queues for tens of ms every second.",
         check="Bitrate over time in the Encoding Lab shows the spikes; Bandwidth budget shows the pile-up delay.",
         fix="Stagger camera start-up, use intra refresh instead of big I-frames, cap with VBV (-maxrate/-bufsize)."),
    # ------------------------------------------------------------------ network
    dict(id="loss", group="network", name="Packet-loss artifacts", img="packet-loss",
         see="Smears and wrong blocks that slide around and only clear at the next keyframe.",
         why="A lost packet removes part of a frame; every later frame predicts from the broken one, so the damage spreads.",
         rov="On UDP a 1 s GOP shows the error for up to a second; a long GOP for several seconds.",
         check="rtp_probe.py loss % per camera; Bandwidth budget → Packet-loss lab to see it on your clip.",
         fix="Fix the link first (connectors, powerline noise), then shorter GOP or intra refresh, and FEC if loss stays."),
    dict(id="corrupt", group="network", name="Decoder corruption (green / grey blocks)", img="decoder-corruption",
         see="Green or grey rectangles, half-drawn frames, garbage after a stream starts or recovers.",
         why="The decoder got a damaged bitstream or started without the reference frame it needs (joined mid-GOP).",
         rov="Joining a camera mid-stream shows garbage until the next keyframe.",
         check="FFmpeg logs ('error while decoding MB', 'non-existing PPS'); count decode errors per minute.",
         fix="Request a keyframe on join, send SPS/PPS with every keyframe (repeat-headers / config-interval=1), check memory and cables."),
    dict(id="buffering", group="network", name="Buffering", img="buffering",
         see="Playback pauses with a spinner, then continues.",
         why="The receiver buffer drains because the stream needs more than the link delivers.",
         rov="Players built for the internet (HLS, a browser <video>) buffer seconds: never use them for piloting.",
         check="Compare stream bitrate with iperf3 throughput; watch the player's buffer level.",
         fix="Bitrate under 70 % of measured throughput, a live protocol (RTP/WebRTC), and a player that drops instead of waits."),
    dict(id="dropout", group="network", name="Intermittent dropouts", img="dropouts",
         see="The picture disappears for seconds and comes back.",
         why="The link or socket closes and reopens: a loose connector, a reboot, an encoder crash, a powerline adapter resyncing.",
         rov="Each dropout costs reconnect time plus the wait for the next keyframe.",
         check="dmesg / journalctl on both ends for link down/up; ethtool -S error counters; a timestamped log of reconnects.",
         fix="Strain-relieve tether connectors, separate power from video, auto-reconnect with exponential back-off, LOST state in the UI."),
    dict(id="linkspeed", group="network", name="Link at the wrong speed", img=None,
         code="$ ethtool eth0\n  Speed: 10Mb/s   ← want 100\n  Duplex: Half    ← want Full",
         see="Everything works on the bench, but on the tether the video is slow, lossy or late.",
         why="A long or damaged cable, or a bad pair, makes Ethernet fall back to 10 Mb/s or half duplex.",
         rov="One bad pair in a 20 m tether turns 94 Mb/s into ≈ 9 Mb/s.",
         check="ethtool on both ends, then iperf3 through the real tether.",
         fix="Re-terminate or replace the tether, check pairs with a cable tester, pin the speed only if both ends agree."),
    dict(id="mtu", group="network", name="IP fragmentation", img=None,
         code="$ tcpdump -ni eth0 'ip[6:2]&0x3fff!=0'\n  IP … frag (id 4512) …\n  → the video is being fragmented",
         see="Loss is much worse than the link statistics suggest, especially at high bitrate.",
         why="UDP datagrams bigger than the MTU are split; losing any fragment loses the whole datagram.",
         rov="Some powerline adapters and tunnels have an MTU below 1500 bytes.",
         check="tcpdump for fragments; ping -M do -s 1472 to find the real MTU.",
         fix="Keep RTP payloads ≤ 1200–1400 bytes (pkt_size / mtu on the payloader); never send raw frames as one datagram."),
    # ------------------------------------------------------------------ motion
    dict(id="rolling", group="motion", name="Rolling shutter", img="rolling-shutter",
         see="Vertical things (piles, pipes, the gripper) lean or bend while the ROV yaws.",
         why="Most cheap sensors read rows one after another; the bottom row is captured up to a frame later than the top.",
         rov="Fast yaw is normal for an ROV; measurements from a skewed picture are wrong.",
         check="Pan quickly past a vertical edge; the lean grows with yaw speed.",
         fix="Global-shutter camera for measurement/CV, faster sensor readout modes, slower yaw while measuring."),
    dict(id="ghost", group="motion", name="Ghosting", img="ghosting",
         see="Moving objects leave faint trails or a second copy.",
         why="Frames are blended: temporal noise reduction in the camera, frame-rate conversion, or a slow display.",
         rov="Camera noise reduction is tuned for still scenes, not a moving ROV.",
         check="Wave something quickly in front of the camera; trails appear before encoding?",
         fix="Turn temporal noise reduction down in the camera (v4l2-ctl), avoid frame-rate conversion, fast-response display."),
    dict(id="mblur", group="motion", name="Motion blur", img="motion-blur",
         see="Moving things are smeared, even though every frame arrives on time.",
         why="Long exposure: in low light the camera keeps the shutter open for most of the frame time.",
         rov="Under water the camera is often light-starved, so exposure grows automatically.",
         check="Read exposure_time_absolute with v4l2-ctl while moving; blur that is in every frame is optical, not network.",
         fix="More light, a fixed shorter exposure (raise gain a little), a faster lens."),
    dict(id="judder", group="motion", name="Judder", img="judder",
         see="Panning moves in uneven steps, repeating some frames.",
         why="The camera rate and the display rate do not divide: 25 or 24 fps on 60 Hz shows frames for 2 then 3 refreshes.",
         rov="Cameras that default to 25 fps (PAL) on a 60 Hz pilot screen.",
         check="Compare camera fps (v4l2-ctl --get-parm) with the display refresh rate.",
         fix="Use 30 or 60 fps cameras on 60 Hz screens, or set the display to 50 Hz for 25 fps cameras."),
    dict(id="combing", group="motion", name="Combing (interlacing)", img="combing",
         see="Moving edges show horizontal comb teeth.",
         why="An interlaced source (old analog cameras, capture cards) sends odd and even lines from different moments.",
         rov="Analog/AHD cameras through a USB capture dongle are often interlaced.",
         check="ffprobe field_order; pause on motion and zoom.",
         fix="Deinterlace before encoding (FFmpeg yadif / bwdif), or use progressive digital cameras."),
    dict(id="strobe", group="motion", name="Strobing (wagon-wheel)", img="strobing",
         see="Thruster blades seem frozen or turning slowly backwards.",
         why="The frame rate samples a periodic motion too slowly: each frame the blade is almost where another blade was.",
         rov="Harmless for piloting, but it confuses anyone judging thruster speed from video.",
         check="Change the frame rate: the apparent speed changes.",
         fix="Do not judge rotation from video; use telemetry (ESC rpm) instead."),
    # ------------------------------------------------------------------ camera
    dict(id="haze", group="camera", name="Low visibility / haze", img="haze",
         see="Washed-out, low-contrast, everything the colour of the water.",
         why="Turbidity scatters light between the object and the lens; contrast falls with distance.",
         rov="The pool after thrusters stir the floor, or murky open water.",
         check="Same scene clear vs stirred; it is in the raw camera image, so encoding cannot fix it.",
         fix="Get closer, light from the side, contrast stretch / CLAHE for display (after decoding, for the pilot only)."),
    dict(id="backscatter", group="camera", name="Backscatter", img="backscatter",
         see="Bright floating specks all over the picture, worst near the lights.",
         why="Light from lamps next to the lens reflects off particles straight back into the camera.",
         rov="Specks are new detail in every frame: they cost bits and trigger false CV detections.",
         check="Turn the lights off and on, or move them: the specks follow the light geometry.",
         fix="Mount lights away from and behind the lens plane, angled outward; dim them in turbid water."),
    dict(id="noise", group="camera", name="Sensor noise", img="sensor-noise",
         see="Grain and fizzing pixels, even when nothing moves.",
         why="Low light makes the camera raise gain, which amplifies sensor noise; heat adds more.",
         rov=f"Noise is detail the encoder must send: measured {MEAS['noise_clean_mbps']} → {MEAS['noise_noisy_mbps']} Mb/s (× {MEAS['noise_factor']}) at the same CRF.",
         check="Bitrate of a still scene: it should be tiny; a high still-scene bitrate means noise.",
         fix="More light, lower gain, camera noise reduction (spatial), keep the electronics cool."),
    dict(id="focus", group="camera", name="Focus problems", img="focus",
         see="Everything is soft, even a still scene with plenty of bitrate.",
         why="Wrong focus, a dirty or scratched port, or autofocus hunting through particles.",
         rov="Focus set in air shifts under water behind a flat port.",
         check="A still frame from the camera before encoding: blur there is optical.",
         fix="Focus under water and lock it (v4l2-ctl focus_auto=0), clean the dome, dome ports for wide lenses."),
    dict(id="exposure", group="camera", name="Over- / under-exposure", img="exposure",
         see="Lost detail in the bright (blown white) or dark (crushed black) parts.",
         why="Auto exposure averages the whole frame; a bright lit target on black water fools it.",
         rov="The lit object the pilot cares about is exactly what auto exposure gets wrong.",
         check="Histogram of a raw frame; v4l2-ctl exposure/gain values.",
         fix="Manual exposure for the task, or spot/centre metering if the camera has it; adjust light power."),
    dict(id="wb", group="camera", name="White balance / colour cast", img="white-balance",
         see="Everything is blue-green, reds are gone.",
         why="Water absorbs red first; auto white balance under water has nothing white to lock on to.",
         rov="Colour-coded cables, red markers and rust are hard to tell apart.",
         check="Hold a white/grey card in front of the camera at depth.",
         fix="Manual white balance at working depth (v4l2-ctl white_balance_temperature), red filter, or colour correction after decoding."),
    dict(id="condensation", group="camera", name="Condensation in the housing", img="condensation",
         see="A milky fog that grows during the dive, worst in the centre of the dome.",
         why="Warm, moist air sealed in the housing condenses on the cold dome when the ROV enters cold water.",
         rov="Looks like turbid water but does not change when the ROV moves.",
         check="Fog that stays fixed to the camera, not the scene; fog that clears when the electronics heat the dome.",
         fix="Seal the housing in dry air, add silica gel, keep heat-producing boards away from the dome."),
    dict(id="pwm", group="camera", name="Light banding (PWM)", img="light-banding",
         see="Dark horizontal bands that roll slowly up or down the picture.",
         why="PWM-dimmed LEDs blink faster than the eye sees; a rolling-shutter sensor captures the blinking row by row.",
         rov="Dimmable ROV lights driven by PWM from the ESC or controller.",
         check="Bands change with light brightness and vanish with the lights at 100 % or off.",
         fix="Constant-current LED drivers, a PWM frequency far above the line rate, or an exposure that is a multiple of the PWM period."),
    dict(id="flicker", group="camera", name="Flicker", img="flicker",
         see="The brightness of the whole picture pumps up and down between frames.",
         why="Auto exposure hunting on a changing scene, mains-powered lights (50/60 Hz), or rendering sync problems.",
         rov="Pumping brightness also makes the encoder spend bits on every frame.",
         check="Plot mean frame brightness over time; set exposure to manual and see if it stops.",
         fix="Manual or slower auto exposure, power_line_frequency set correctly, steady lights."),
    # ------------------------------------------------------------------ display
    dict(id="tearing", group="display", name="Tearing", img="tearing",
         see="A horizontal line where the top and bottom of the picture do not match.",
         why="The screen is refreshed while the next frame is being copied in (no vsync), or a capture grabs half-updated memory.",
         rov="Distracting during fast yaw; a screen recording of the GUI shows it too.",
         check="Turn vsync on: if it disappears, it was the display path.",
         fix="Present with vsync / double buffering (OpenGL swap interval 1), copy whole frames between threads."),
    dict(id="black", group="display", name="Black frames", img="black-frames",
         see="Single black frames or a black window although data is arriving.",
         why="Capture timeout, a decoder reset, a surface format the renderer does not support, or HEVC in a browser that cannot decode it.",
         rov="A browser without H.265 support shows black for an H.265 stream with no error.",
         check="Decoder log and the browser console; chrome://media-internals shows the decoder in use.",
         fix="H.264 for browser pilots, check the pixel format (yuv420p), handle decoder errors by requesting a keyframe."),
    dict(id="aspect", group="display", name="Wrong aspect ratio", img="aspect-ratio",
         see="Round things are ovals, the picture looks squashed or stretched.",
         why="The stream size and the window or the pixel aspect ratio do not match (a 4:3 camera in a 16:9 box).",
         rov="Distances and sizes read from video are wrong.",
         check="ffprobe width, height and sample_aspect_ratio; compare with the window.",
         fix="Letterbox instead of stretch (object-fit: contain), set SAR 1:1, keep the camera's native shape."),
    dict(id="reswitch", group="display", name="Resolution switching", img="resolution-switch",
         see="A blank moment, then the picture is the wrong size or position.",
         why="The source changed resolution (camera restart, adaptive stream) and the decoder/renderer had to reinitialise.",
         rov="Switching a camera between main and substream causes this every time.",
         check="Log decoder reconfiguration events with timestamps.",
         fix="Fixed output size with scaling in the renderer, keep the last frame until the new one decodes."),
    dict(id="range", group="display", name="Colour range / colour space", img="color-range",
         see="Washed-out greys where black should be, or crushed blacks and clipped whites.",
         why="Video uses 16–235 (limited range); a player that assumes 0–255 shows it washed out, or the reverse crushes it.",
         rov="OpenGL/WebGL renderers that convert YUV → RGB themselves often get this wrong.",
         check="ffprobe color_range; render a known black/white test pattern.",
         fix="Tag the stream (-color_range tv) and convert with the matching matrix (BT.601 vs BT.709) in the shader."),
    dict(id="desync", group="display", name="Telemetry–video (and audio) desync", img="desync",
         see="The depth or heading overlay disagrees with what the video shows; audio, if any, drifts.",
         why="Telemetry arrives in milliseconds while video waits in buffers; separate clocks drift apart.",
         rov="The HUD shows where the ROV is, the video shows where it was.",
         check="Timestamp both at the ROV; show their age difference in the GUI.",
         fix="Delay telemetry to match video for the overlay, or show both ages; one clock (PTP/chrony) for all timestamps."),
    # ------------------------------------------------------------------ system
    dict(id="thermal", group="system", name="Thermal throttling", img="thermal",
         see="Fine on the bench, FPS drops after 10–15 minutes in the sealed hull.",
         why="The SoC slows its clocks when hot; a closed enclosure in warm water cannot get rid of the heat.",
         rov="Our 2023 heat failure: everything passed the bench test.",
         check="vcgencmd get_throttled / measure_temp (Pi), tegrastats (Jetson) during a 30-minute soak test, enclosure closed.",
         fix="Heat sink to the hull, fan inside, lower encoder load (hardware encoder), log temperature with the video."),
    dict(id="usb", group="system", name="USB bandwidth", img="usb-bandwidth",
         see="The third or fourth camera refuses to start ('No space left on device') or drops frames.",
         why="USB 2.0 reserves bandwidth per camera; uncompressed modes reserve a lot and the bus runs out.",
         rov="All cameras on one hub share one 480 Mb/s bus.",
         check="lsusb -t (which bus), v4l2-ctl --list-formats-ext (MJPEG vs YUYV), dmesg.",
         fix="MJPEG modes, spread cameras over separate USB controllers, USB 3.0 ports, lower fps for aux cameras."),
    dict(id="cpu", group="system", name="CPU saturation", img=None,
         code="$ htop\n  CPU0 [||||||||100%]  ffmpeg\n  CPU1 [||||||||100%]  ffmpeg\n  → decode → scale → encode",
         see="FPS falls and latency rises together when more cameras or a GUI are added.",
         why="Software encode, the resolution trap (decode → scale → encode) or colour conversion runs out of CPU.",
         rov="One resized MJPEG camera costs ≈ 13 % of a core; software H.264 on a Pi 5 ≈ 0.6–0.9 core per 1080p30.",
         check="htop per thread; the Lab's Bandwidth budget → Measure this computer.",
         fix="Hardware encoder, ask the camera for the size you need, stay under 70 % CPU."),
    dict(id="clock", group="system", name="Clock drift (bad measurements)", img=None,
         code="$ chronyc tracking\n  System time: 0.183 s fast\n  → every latency number\n    is 183 ms wrong",
         see="Latency numbers that are negative, jump, or slowly change for no reason.",
         why="Timestamps from two computers are compared, but their clocks disagree and drift.",
         rov="The ROV computer has no internet time under water; its clock drifts from the topside.",
         check="chronyc tracking on both ends; compare with the optical (ms-clock photo) measurement.",
         fix="Run chrony with the topside as the server (or PTP); use monotonic clocks for stage timings on one machine."),
]

METRICS = [
    ("Latency", "glass-to-glass, capture→encode, network transit, decode→display, frame age", "ms (median, p95)",
     "ms-clock photo; stage timestamps; Encoding Lab Live camera"),
    ("Frame delivery", "fps at capture, encode, decode and display; dropped and duplicated frames per stage", "fps, frames, %",
     "Encoding Lab Live camera (dropped, fps); player stats"),
    ("Frame timing", "frame interval and its jitter at the receiver", "ms", "presentation timestamps"),
    ("Network", "throughput, packet loss, jitter, RTT, retransmissions, socket/queue depth", "Mb/s, %, ms",
     "rtp_probe.py; iperf3; ethtool -S; ss -tmi"),
    ("Encoding", "average and peak bitrate, encoder time, frames held, VBV fullness, keyframe size", "Mb/s, ms, frames",
     "Encoding Lab (Encode, Live camera)"),
    ("Quality", "PSNR, SSIM, VMAF on recorded clips", "dB, 0–1, 0–100", "Encoding Lab Encode / Sweep"),
    ("Decoding", "decode errors, decode time, decoder queue depth", "count, ms, frames",
     "FFmpeg log; chrome://webrtc-internals"),
    ("Rendering", "render time, presentation interval, GPU load", "ms, %", "the GUI's own timers; GPU tools"),
    ("Resources", "CPU per thread, RAM, GPU memory, temperature, throttling", "%, MB, °C",
     "htop; tegrastats; vcgencmd get_throttled"),
]

MATRIX = [
    ("Delay grows over time", "a queue that only grows", "queue depth per stage, socket buffers", "drift"),
    ("Constant high delay", "encoder look-ahead, big jitter buffer, TV", "stage-by-stage latency, frames held", "hold"),
    ("FPS drops", "CPU/GPU, heat, USB", "fps at each stage, CPU per thread, temperature", "thermal"),
    ("FPS fine but motion jerky", "frame pacing, judder", "presentation intervals, camera vs display rate", "pacing"),
    ("Picture freezes, app alive", "capture, network or decoder stopped", "time since last packet / last decoded frame", "stale"),
    ("Blocks or blur when moving", "too few bits", "bitrate, QP, bits per pixel, VMAF", "blocking"),
    ("Poor picture, high bitrate", "noise, backscatter, flicker", "still-scene bitrate, gain, lights", "noise"),
    ("Smears that clear at keyframes", "packet loss", "loss %, GOP length", "loss"),
    ("Green / grey garbage", "corrupt stream or missing reference", "decoder log, keyframe on join", "corrupt"),
    ("Video late, telemetry current", "video buffering", "video queue depth, frame age", "desync"),
    ("Network use above plan", "keyframe bursts, overhead, noise", "peak bitrate, packet rate", "iframe"),
    ("Works on the bench, fails on the tether", "link speed, fragmentation, heat", "ethtool, iperf3 on the tether, soak test", "linkspeed"),
    ("Delay jumps after reconnect", "start-up buffering, waiting for a keyframe", "keyframe arrival, decoder init", "dropout"),
    ("3rd camera will not start", "USB bandwidth", "lsusb -t, formats", "usb"),
]

FIRST15 = [
    ("Glass-to-glass latency", "ms-clock photo (manual)", "manual"), ("Capture → encode latency", "Encoding Lab Live camera", "lab"),
    ("Network transit / RTT", "rtp_probe.py jitter, ping", "probe"), ("Decode → display latency", "GUI timers", "todo"),
    ("Capture fps", "Encoding Lab Live camera", "lab"), ("Encode fps", "Encoding Lab Live camera", "lab"),
    ("Decode fps", "GUI / player stats", "todo"), ("Display fps", "GUI presentation timestamps", "todo"),
    ("Dropped frames per stage", "Live camera (dropped); GUI", "lab"), ("Frame-interval jitter", "GUI presentation timestamps", "todo"),
    ("Average bitrate", "rtp_probe.py; Encoding Lab", "probe"), ("Peak bitrate", "Encoding Lab Bitrate over time", "lab"),
    ("Network throughput", "rtp_probe.py", "probe"), ("Packet loss", "rtp_probe.py", "probe"),
    ("Queue depth at every stage + frame age", "GUI (STALE badge)", "todo"),
]


def markdown() -> str:
    by = {g: [c for c in C if c["group"] == g] for g, *_ in GROUPS}
    L = ["# Video diagnostics field guide: what you see, why, and how to fix it", "",
         "*M.I.A Robotics · streaming docs · 24 Nov 2026*", "",
         "A video problem shows up as a symptom on the pilot's screen, but its cause can be in any stage: "
         "**camera → capture → encoder → network → receiver → decoder → renderer → display**. "
         "This guide lists the symptoms we can meet on the ROV, what causes each one, how to confirm it, and how to fix it. "
         "It started from a generic checklist and adds the ROV-specific problems we have met or measured: encoder hold-back, "
         "keyframe pile-up, the wrong link speed, IP fragmentation, condensation, PWM light banding, thermal throttling, USB bandwidth "
         "and clock drift.", "",
         "**How the pictures were made.** Every picture comes from the Encoding Lab's synthetic underwater clip "
         "(`build/make_diagnostic_images.py`). Compression artifacts are real encodes at bad settings; packet loss and decoder "
         "corruption are real damaged streams decoded by FFmpeg; camera, motion and display effects are simulated from how they "
         "happen; timing problems are charts. Charts marked *illustration* show the shape of a problem, not a measurement.", "",
         "The same material is in the deck: *Diagnostics* (after *Your measurement toolbox*) and the *Field guide* appendix.", "",
         "## 1. Diagnose by stage, not by symptom", "",
         "The same symptom can come from different stages, and a healthy-looking number can hide a problem:", "",
         "- high latency with a perfect 30 fps (encoder hold-back, a growing queue);",
         "- low fps with plenty of bandwidth (CPU, heat, USB);",
         "- a frozen picture while the connection is still up (stale frame);",
         "- blur only while the camera moves (bitrate cap, or exposure);",
         "- smooth video but late telemetry, or the reverse (desync);",
         "- a delay that grows during the dive (a queue that only grows).", "",
         "So measure each stage separately. Otherwise a delay in the pilot laptop's render queue gets blamed on the tether.", "",
         "| Stage | Measure |", "|---|---|",
         "| Camera / capture | capture fps, exposure and gain, source resolution, dropped frames, camera errors (dmesg) |",
         "| Encoder | encode fps, encoder time, frames held, average and peak bitrate, GOP, VBV |",
         "| Network | throughput, packet loss, jitter, RTT, send queue, link speed |",
         "| Receiver | receive fps, loss, reordering, jitter buffer depth |",
         "| Decoder | decode fps, decode time, decode errors, queue depth |",
         "| Renderer / display | render fps, presentation interval, frame age, display lag |", "",
         "## 2. Symptom → first suspect → what to inspect", "",
         "| Symptom | First suspect | Inspect | Field-guide entry |", "|---|---|---|---|"]
    name = {c["id"]: c["name"] for c in C}
    for s, sus, ins, ref in MATRIX:
        L.append(f"| {s} | {sus} | {ins} | [{name[ref]}](#{slug(name[ref])}) |")
    L += ["", "## 3. Measure, don't guess", "", "| Category | Metrics | Unit | Where we get it |", "|---|---|---|---|"]
    L += [f"| {a} | {b} | {u} | {w} |" for a, b, u, w in METRICS]
    L += ["", "Add one more: **frame age** (now − capture timestamp of the frame on screen). It catches stale frames that the fps counter hides.", "",
          "## 4. Measuring latency properly", "",
          "Glass-to-glass latency is *L = T(display) − T(capture)*. Three methods, from simplest to most detailed:", "",
          "1. **Optical (ms clock):** point the camera at a millisecond clock on the pilot laptop, photograph the clock and the video of the clock together, "
          "repeat 10 times, report the median and the worst. No clock synchronisation needed. This is the number the pilot feels.",
          "2. **Timestamp overlay:** stamp the capture time into the frame (or into RTP/SEI metadata) and compare with the receiver clock. "
          "Needs synchronised clocks (chrony or PTP, see *Clock drift* below).",
          "3. **Stage timestamps:** log a monotonic timestamp at capture, encode out, network receive, decode out and present. "
          "Stage times on one machine need no synchronisation; across machines they do.", "",
          "Report **median and p95**, never a single number, and correlate over time: latency rising together with queue depth is buffering; "
          "latency steady while capture fps falls points at the camera or CPU.", "",
          "## 5. The first 15 diagnostics to build", "",
          "| # | Diagnostic | Where | Status |", "|---|---|---|---|"]
    st = {"lab": "available in the Encoding Lab", "probe": "available: `encoding_lab/tools/rtp_probe.py`", "manual": "manual procedure",
          "todo": "to build in the pilot GUI"}
    L += [f"| {i} | {a} | {b} | {st[c]} |" for i, (a, b, c) in enumerate(FIRST15, 1)]
    L += ["", "For the pilot GUI, show four numbers (latency p50/p95, bitrate, display fps, loss %) and one health light per stage; "
              "details go in a tooltip or a debug view. See [gui-stream-metrics.md](gui-stream-metrics.md).", "",
          "## 6. Field guide", ""]
    for g, title, intro in GROUPS:
        L += [f"### {title}", "", f"*{intro}*", ""]
        for c in by[g]:
            L += [f"#### {c['name']}", ""]
            if c.get("img"):
                L += [f"![{c['name']}](img/diagnostics/{c['img']}.jpg)", ""]
            else:
                L += ["```", c["code"], "```", ""]
            L += [f"- **What you see:** {c['see']}", f"- **Why:** {c['why']}", f"- **On our ROV:** {c['rov']}",
                  f"- **Confirm:** {c['check']}", f"- **Fix:** {c['fix']}", ""]
    L += ["## Related", "", "- [measuring-performance.md](measuring-performance.md): the measurement toolbox",
          "- [gui-stream-metrics.md](gui-stream-metrics.md): throughput and loss in the pilot GUI",
          "- [mjpeg-and-ffmpeg.md](mjpeg-and-ffmpeg.md): the resolution trap",
          "- [jetson-nano-vs-pi5.md](jetson-nano-vs-pi5.md): encoder capacity and heat",
          "- Encoding Lab: Encode (Frame compare, Bitrate over time), Live camera, Bandwidth budget (Packet-loss lab)", ""]
    return "\n".join(L)


def slug(s: str) -> str:
    import re
    return re.sub(r"[^a-z0-9 -]", "", s.lower()).replace(" ", "-")


if __name__ == "__main__":
    assert len({c["id"] for c in C}) == len(C)
    for c in C:
        if c.get("img"):
            assert (ROOT / f"docs/streaming/img/diagnostics/{c['img']}.jpg").exists(), c["img"]
    (ROOT / "docs/streaming/video-diagnostics.md").write_text(markdown())
    (ROOT / "out").mkdir(exist_ok=True)
    (ROOT / "out/diagnostics.json").write_text(json.dumps({"groups": GROUPS, "items": C, "metrics": METRICS, "matrix": MATRIX,
                                                            "first15": FIRST15, "meas": MEAS}, ensure_ascii=False, indent=1))
    print(len(C), "entries,", sum(1 for c in C if c.get("img")), "with pictures")
