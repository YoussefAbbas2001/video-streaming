# Demo: hardware vs software encoding

Run the same 1080p30 test pattern through a software encoder and (on a Jetson Nano) the hardware encoder. Watch `../02_pipeline/monitor.py` in a second terminal. The point: **CPU cores used** and **temperature**, not just "it works".

> These pipelines need the real board. They were not run in the workshop sandbox, so treat this as the procedure and record your own numbers in the table at the bottom.

## Software (any Linux, Raspberry Pi 5, Jetson)

```bash
# 1080p30 for 30 s, x264 low-latency, encoded and thrown away (no network: pure encoder cost)
gst-launch-1.0 -e videotestsrc num-buffers=900 is-live=true pattern=ball ! video/x-raw,width=1920,height=1080,framerate=30/1 \
  ! x264enc tune=zerolatency speed-preset=ultrafast bitrate=4000 key-int-max=30 ! fakesink sync=false

# FFmpeg equivalent
ffmpeg -hide_banner -re -f lavfi -i testsrc2=size=1920x1080:rate=30 -t 30 \
  -c:v libx264 -preset ultrafast -tune zerolatency -b:v 4M -g 30 -bf 0 -f null -
```

## Hardware (Jetson Nano, GStreamer, JetPack 4.x)

```bash
gst-launch-1.0 -e videotestsrc num-buffers=900 is-live=true pattern=ball ! video/x-raw,width=1920,height=1080,framerate=30/1 \
  ! nvvidconv ! 'video/x-raw(memory:NVMM),format=NV12' \
  ! nvv4l2h264enc bitrate=4000000 iframeinterval=30 insert-sps-pps=true maxperf-enable=1 ! fakesink sync=false
# In another terminal: sudo tegrastats --interval 1000   (look at CPU % and the NVENC clock)
```

To feel the difference, run **four** of each at the same time (`&` after each command). The Nano hardware encoder is rated for 4× 1080p30. In software, four 1080p30 streams need roughly three Pi 5 cores, based on Raspberry Pi's measured 0.62–0.9 core per stream.

## Raspberry Pi 5 note

The Pi 5 has **no** hardware H.264 encoder, so there is nothing to compare against on that board. Use the software pipeline and log CPU and temperature for a 30-minute soak test (`monitor.py --csv`).

## Results to record

| Board | Encoder | Streams | CPU cores used | Max temp after 10 min | Throttled? | Encoder speed (≥ 1.0×) |
|---|---|---|---|---|---|---|
| | | | | | | |
