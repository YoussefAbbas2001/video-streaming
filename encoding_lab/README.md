# ROV Encoding Lab

An interactive app for seeing how each encoder setting changes **file size, bitrate, picture quality, encoding speed and robustness to packet loss**. You can use a synthetic underwater clip or your own ROV footage.

It is the hands-on companion to Experiments 3–9 of the workshop notebook. The notebook explains each idea once; the lab lets you keep turning the knobs.

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
| **Encode** | Codec, CRF or bitrate cap + VBV, preset, keyframe interval, B-frames, low latency, resolution, frame rate | Verdict chips: real time? quality? within budget? encoder hold? how many such streams fit this CPU? Colour-coded cards: size, bitrate, compression, bits/pixel, PSNR, SSIM, encode speed, CPU per stream, each with the change since your last try. Views: frame compare / diff ×8 / zoom, bitrate over time (I/P/B), quality over time, side-by-side playback, and **🧮 Show the math**, every formula with your numbers |
| **Compare** | Every encode is collected automatically | Rate–quality chart with your budget and quality floor, the best trade-offs line, the best setting inside your budget, CSV export |
| **Sweep** | Vary one knob across several values | Bitrate and SSIM curves plus encode speed against real time |
| **Benchmark** | Run it **on the ROV computer and on the pilot laptop** | This computer's specs; **capacity**: fps on one core, CPU ms per frame, streams per core, real-time streams the machine can carry at 70 % CPU, per resolution × preset; hardware encoders (listed vs actually working); decode speed; encoder hold: x264 defaults vs low latency |
| **Latency budget** | Capture buffering, network, jitter buffer, monitor refresh | Glass-to-glass estimate, stage by stage (typical and worst), each labelled measured / estimated / your input, against your target, plus the biggest stage and what to do about it |
| **Packet loss** | Delete kB of an MPEG-TS stream | How long the picture stays broken: GOP length vs intra refresh |
| **Bandwidth** | Edit the 8-camera table | Fits / tight / doesn't fit the tether; Jetson Nano encoder load |
| **Live monitor** | Toggle it on while streaming | CPU per core, temperature, clock, Raspberry Pi throttling, busiest link (Mb/s vs your tether), with a CSV log: the soak-test view |
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
├── lab/bench.py           benchmarking: system info, HW encoders, capacity, decode, encoder hold, latency budget, live monitor, report
├── tests/test_engine.py   self-test of engine + benchmarks (pytest, ~10 s)
├── .streamlit/config.toml theme (M.I.A red)
├── requirements.txt
└── run_lab.sh / run_lab.bat
```

`lab/engine.py` has no Streamlit dependency, so you can reuse it in scripts or in your own test rig.
