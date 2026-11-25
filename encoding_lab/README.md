# ROV Encoding Lab

An interactive app for seeing how each encoder setting changes **file size, bitrate, picture quality, encoding speed and robustness to packet loss**. You can use a synthetic underwater clip or your own ROV footage.

It is the tool we use in the workshop session itself: every experiment is run here, live, on the presenter's laptop and on the ROV's computer. The **Live camera** tab streams the laptop's own camera through a choice of encoders (MJPEG passthrough, x264, NVENC, …) with a head-up display of what each stage costs.

## Run it

```bash
# 1. FFmpeg with libx264 (libx265 / libsvtav1 optional: missing encoders are hidden automatically)
sudo apt install ffmpeg            # Ubuntu / Jetson / Raspberry Pi OS
#    macOS: brew install ffmpeg    Windows: winget install ffmpeg

# 2. Python packages
pip install -r requirements.txt

# 3. Start
streamlit run app.py               # or ./run_lab.sh  /  run_lab.bat
```

The lab opens at <http://localhost:8501>. To use it from other laptops on the same network, start it with `streamlit run app.py --server.address 0.0.0.0` and open `http://<this-computer-ip>:8501`.

If `ffmpeg` is not on your PATH, point to it explicitly:

```bash
FFMPEG_BIN=/path/to/ffmpeg FFPROBE_BIN=/path/to/ffprobe streamlit run app.py
```

## What is in it

Set **your targets** once in the sidebar (bitrate budget per camera, glass-to-glass latency target, measured tether throughput, quality floor). Every verdict in the app (green / amber / red) is judged against them.

| Tab | What you do | What you get |
|---|---|---|
| **Encode** (master tab) | One compact control bar: codec, CRF or bitrate cap, preset, keyframe interval, resolution, frame rate, low latency (B-frames, VBV and VMAF under **More**) | Verdict chips: real time? quality? within budget? encoder hold? how many such streams fit this CPU? Cards: size, bitrate, compression, bits/pixel, PSNR, SSIM, encode speed, CPU per stream, each with the change since your last try. Views: frame compare / diff ×8 / zoom, bitrate over time (I/P/B), quality over time, side-by-side playback, **🧮 Show the math**. Below them: the **glass-to-glass latency graph** of this encode (stage by stage, typical and worst, hover a block for its source) and **Compare**, the rate–quality chart of every run with your budget, quality floor and best trade-offs |
| **Live camera** | Pick a camera (or a simulated MJPEG camera), the size and fps to ask it for, an encoder, an output size, bitrate, speed, keyframe interval, low latency; press **Start** | The live picture with a head-up display: encoder latency (average and 95th percentile), frames held, bitrate, frame size, bits/pixel, JPEG decode, convert/scale, pilot-side decode, CPU, dropped frames, a keyframe flash and a 30 s bitrate sparkline. A pipeline strip shows which stages run and what each costs; charts show bitrate and encoder time over time; a **scoreboard** compares every run. Encoders: MJPEG passthrough, MJPEG re-encode, x264, NVENC (H.264/H.265), Quick Sync, AMF, VideoToolbox, V4L2 M2M, x265, SVT-AV1 — each probed with a real test encode, with the reason when it can't run |
| **Sweep** | Vary one knob across several values | Bitrate and SSIM curves plus encode speed against real time |
| **Bandwidth budget** | Pick a starting setup, the ROV computer (Jetson Nano hardware, Pi 5, Orin Nano, or this computer once measured), the tether, headroom, control traffic, transport and packet loss; edit the camera table (pipeline, camera and stream resolution, fps, quality, GOP) | **Plan the budget:** fits / over plan / doesn't fit; Mb/s on the tether per camera; encode-computer load (CPU cores or Jetson hardware Mpx/s); keyframe pile-up delay; how often each camera glitches and how much of the time its picture is broken; spare room; the cheapest one-change fixes; a Markdown plan to download. **Measure this computer** (run it on the ROV computer and the pilot laptop): capacity per resolution × preset, hardware encoders that really work, encoder hold, decode speed. **Packet-loss lab:** delete kB of an MPEG-TS stream and see how long the picture stays broken, GOP vs intra refresh |
| **Report** | Download | One Markdown report (this computer, every encode, capacity, hold, decode, latency budget) + CSV, ready for a GitHub issue |
| **Learn** | Read | What each knob and each number means, with a "try it" for each |

### The calculations

| Quantity | Formula |
|---|---|
| Raw bitrate | W × H × 12 bits (4:2:0) × fps |
| Compression ratio | raw size ÷ encoded size |
| Bits per pixel | bitrate ÷ (W × H × fps) |
| Real-time factor | encode fps ÷ video fps (must be ≥ 1) |
| CPU per frame · cores per stream | CPU time ÷ frames · CPU ms per frame × fps ÷ 1000 |
| Streams this computer can encode | streams per core × cores × 70 % headroom (one-thread benchmark) |
| On the wire · streams the tether carries | bitrate × (1 + protocol overhead) · link × 70 % ÷ on-the-wire rate |
| Encoder hold | frames held before the first output ÷ fps (measured with PyAV, else estimated) |
| Glass-to-glass | capture + hold + encode + send (frame size ÷ link) + network + jitter buffer + decode + display |
| Recording size | bitrate × 3600 ÷ 8 per hour |

## Live camera tab

* **Cameras.** Windows (DirectShow), Linux (V4L2) and macOS (AVFoundation) cameras are listed automatically; ↻ looks again. With no camera, use one of the two simulated MJPEG cameras (a test pattern, or the lab clip looped).
* **How it works.** FFmpeg asks the camera for its own MJPEG mode and copies it (`-c:v copy`). Everything after that runs in the lab with PyAV, one stage at a time, so each stage gets its own clock. The picture reaches your browser as an MJPEG stream from a small local server (`127.0.0.1:8765`, `/stream.mjpg` and `/stats`).
* **The resolution trap.** Passthrough costs almost nothing. Set *Output size* below Native and the lab has to decode, scale and re-encode every frame, which is exactly what happens when an MJPEG camera is shrunk in software. Compare the two rows on the scoreboard, then ask the camera for the smaller size instead.
* **Encoder latency** is measured per frame from the moment a frame enters the encoder until its packet comes out, so frames held back by lookahead or B-frames count (x264 with Low latency off holds about 30 frames ≈ 1 s).
* **Settings.** `LAB_LIVE_PORT` changes the port. To watch from another computer (e.g. the lab runs on the ROV), start it with `LAB_LIVE_HOST=0.0.0.0` and only on a network you trust: the camera is then visible to that network.
* **Shortcuts.** H hides the overlay, F goes full screen.

## Using real ROV footage

Pick **Upload your own video** in the sidebar. The clip is cut to the length and start time you choose and scaled to the working resolution. It is then stored once as a **lossless reference**, and every encode is compared against that reference.

Encodes are cached in `.lab_work/`, so going back to a setting is instant. Delete the folder to free space.

## Important: measure on the robot's computer

The **Encode speed** and **CPU cores used** numbers describe the computer running the lab. A laptop is several times faster than a Raspberry Pi 5 or a Jetson Nano CPU.

To learn what your topside or ROV computer can sustain, run the lab on that board, or run the same FFmpeg command there.

The Jetson Nano's hardware encoder is used through GStreamer (`nvv4l2h264enc`), not through the libx264 in this app. Its quality and speed are different, so measure them separately.

## Files

```
encoding_lab/
├── app.py                 Streamlit user interface
├── lab/engine.py          FFmpeg logic: encode, measure (PSNR/SSIM/VMAF), frame stats, packet-loss experiment
├── lab/bench.py           benchmarking: system info, HW encoders, capacity, decode, encoder hold, latency budget, report
├── lab/live.py            Live camera: capture, per-stage timing, encoders, MJPEG server for the browser
├── lab/budget.py          Bandwidth budget planner: pipelines, encode computers, loss and keyframe pile-up, fixes
├── assets/mia_logo.png    header logo
├── tools/rtp_probe.py     throughput, packet loss and jitter of an RTP stream (for the pilot GUI; see docs/streaming/measure-and-diagnose.md (section 5))
├── tests/test_engine.py   self-test of engine, benchmarks and the live pipeline (pytest, ~30 s)
├── tests/test_rtp_probe.py tests for the probe
├── tests/test_budget.py   tests for the planner
├── .streamlit/config.toml theme (dark, M.I.A red)
├── requirements.txt
└── run_lab.sh / run_lab.bat
```

`lab/engine.py` has no Streamlit dependency, so you can reuse it in scripts or in your own test rig.
