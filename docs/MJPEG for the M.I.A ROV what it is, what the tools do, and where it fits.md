# MJPEG for the M.I.A ROV: what it is, what the tools do, and where it fits

Nov 19, 2026 · @Abbas

## TL;DR

MJPEG is video made of separate JPEG photos sent one after another. No frame depends on any other, so encoding is cheap, there is no frame hold, and one bad frame never smears into the next. The cost is size: MJPEG needs about 5–8× more bits than H.264 for the same picture.

The two links are two different tools for serving MJPEG over HTTP:

- **[mjpg-streamer](https://github.com/jacksonliam/mjpg-streamer)** is a small C program. It can take JPEG frames straight from a USB camera, with no re-encoding, and serve them to a browser.
- **[mjpeg-streamer](https://pypi.org/project/mjpeg-streamer/)** is a Python library. It takes OpenCV frames, JPEG-encodes them, and serves them over HTTP.

**Verdict for our ROV:**

- **Where MJPEG fits:** auxiliary and low-rate cameras, a zero-encode path on the Pi 5 (which has no hardware H.264 encoder), browser views in the GUI, and CV debug streams.
- **Where it doesn't:** it is the wrong choice for the pilot and manipulator cameras over a shared 100 Mb/s tether. Those stay H.264 over RTP/UDP.

## What MJPEG actually is

MJPEG (Motion JPEG) compresses each frame on its own as a JPEG image: DCT blocks, quantisation set by a 1–100 quality factor, then entropy coding. That's all it does. There are no motion vectors, no reference frames, and no GOP, so every frame is in effect an I-frame.

The consequences follow directly from that:

| Property | MJPEG | H.264 / H.265 |
| --- | --- | --- |
| Frame dependency | None; every frame decodes alone | P/B frames need earlier (and later) frames |
| Encoder frame hold | 0 frames | 0 with zerolatency; 31 frames with x264 defaults (measured in our Encoding Lab) |
| Bits for the same quality | High (our Bandwidth tab default: 0.34 bits per pixel) | Low (0.045 bpp for H.264, 0.058 for H.265) |
| Effect of a lost frame | One frame is missing; the next is perfect | Smearing until the next I-frame |
| CPU to encode | Low, and often zero (done in the camera) | High in software; needs a hardware encoder on SBCs |
| Seeking and frame-accurate cutting | Any frame | Only at keyframes |

### How it travels over the network

There is no special protocol. The common way is plain HTTP with the content type `multipart/x-mixed-replace`: the server keeps one HTTP response open and pushes JPEG after JPEG, each separated by a boundary line. Browsers display this natively in an `<img>` tag, which is why MJPEG is the default for IP cameras, 3D-printer cams (OctoPrint) and robot dashboards.

```
HTTP/1.0 200 OK
Content-Type: multipart/x-mixed-replace; boundary=frame

--frame
Content-Type: image/jpeg
Content-Length: 48213

<JPEG bytes of frame 1>
--frame
Content-Type: image/jpeg
Content-Length: 47990

<JPEG bytes of frame 2>
...
```

The other ways to carry it:

- **RTP:** MJPEG can also ride RTP over UDP (RTP payload format RFC 2435), which is what GStreamer's `rtpjpegpay` does.
- **Files:** it can be stored in AVI or MOV containers.

### Why USB cameras give it to us for free

Most UVC (USB) cameras offer two formats: raw YUYV and MJPEG. Raw 1080p30 YUYV is 1920 × 1080 × 2 bytes × 30 fps ≈ 995 Mb/s, which does not fit through USB 2.0's 480 Mb/s. So the camera's own chip JPEG-compresses each frame, and high-resolution or high-fps modes are usually MJPEG-only.

That means MJPEG arrives on the Pi or Jetson already compressed, with no CPU spent on encoding. Check what your camera offers with `v4l2-ctl --list-formats-ext -d /dev/video0`.

## mjpg-streamer (C, jacksonliam fork)

mjpg-streamer is a tiny C program built for weak embedded boards. It has one job: take JPEG frames from an **input plugin** and copy them to one or more **output plugins**. When the camera already outputs MJPEG, it does no encoding at all; it just moves bytes, so it runs at a few percent CPU even on a Pi Zero.

The [repository](https://github.com/jacksonliam/mjpg-streamer) is a GPLv2 fork of the original SourceForge project, with about 3.3k stars. Its last commit is from 20 February 2021, so treat it as **stable but unmaintained**.

### Plugins

| Plugin | What it does | Use on our ROV? |
| --- | --- | --- |
| `input_uvc` | Grabs frames from a V4L2/USB camera. Default is the camera's own MJPEG; `-y` (YUYV) or `-u` (UYVY) makes it JPEG-encode on the CPU at `-q` quality (default 80) | Yes: the main one for USB cameras |
| `input_raspicam` | Pi CSI camera through the legacy MMAL stack | No: MMAL doesn't exist on Pi 5 / Bookworm (libcamera) |
| `input_opencv` | Frames from OpenCV, with optional filter plugins | Possible, but Python is easier for CV |
| `input_http` | Pulls another MJPEG HTTP stream (relay) | Topside fan-out of one ROV stream |
| `input_file` | Watches a folder and streams new JPEGs | Replaying saved stills |
| `input_testpicture` | Built-in test images | Testing the GUI without a camera |
| `output_http` | Web server: stream, snapshot, controls page | Yes: what the GUI or browser connects to |
| `output_file` | Writes JPEGs or an MJPEG file to disk | Onboard recording of evidence frames |
| `output_rtsp`, `output_udp` | Network outputs | No: the project lists both as not functional |
| `output_zmqserver`, `output_viewer` | ZeroMQ publisher and a local SDL window | ZMQ is handy for feeding a CV process |

### output\_http options and URLs

**Options:**

- `-p` sets the port (default 8080).
- `-w` sets the web folder for the built-in page.
- `-l` sets the listen IP.
- `-c user:pass` turns on HTTP basic auth.
- `-n` disables the command interface.

**URLs:**

- `/?action=stream`: the live MJPEG. With several inputs, use `stream_0`, `stream_1`, and so on.
- `/?action=snapshot`: the latest single JPEG.

Responses carry `Access-Control-Allow-Origin: *`, so a browser GUI on another host can embed them.

### Typical commands

```bash
# Build (Pi OS / Ubuntu on Jetson)
sudo apt install cmake libjpeg-dev gcc g++
git clone https://github.com/jacksonliam/mjpg-streamer.git
cd mjpg-streamer/mjpg-streamer-experimental && make && sudo make install

# One USB camera, camera-side MJPEG, zero CPU encode
mjpg_streamer -i "input_uvc.so -d /dev/video0 -r 1280x720 -f 30" \
              -o "output_http.so -p 8080 -w /usr/local/share/mjpg-streamer/www"

# Two cameras on one server -> /?action=stream_0 and /?action=stream_1
mjpg_streamer -i "input_uvc.so -d /dev/video0 -r 640x480 -f 15" \
              -i "input_uvc.so -d /dev/video2 -r 640x480 -f 15" \
              -o "output_http.so -p 8080 -n"

# Camera only does YUYV: CPU encodes JPEG at quality 70
mjpg_streamer -i "input_uvc.so -d /dev/video4 -y -q 70 -r 640x480 -f 15" -o "output_http.so -p 8081"
```

Then open `http://<rov-ip>:8080/?action=stream` in a browser, VLC or OpenCV.

## mjpeg-streamer (Python, PyPI)

[mjpeg-streamer](https://pypi.org/project/mjpeg-streamer/) is a pure-Python library (version 2024.2.8, AGPLv3, one maintainer). You hand it NumPy/OpenCV frames; it JPEG-encodes them with `cv2.imencode` and serves them over HTTP with aiohttp in a background thread.

Its value is that **you choose what goes in the frame**: the camera image with bounding boxes, a depth map, a mask, a stitched mosaic. mjpg-streamer can only forward what the camera gives it.

### API in five lines

```python
import cv2
from mjpeg_streamer import MjpegServer, Stream

cap = cv2.VideoCapture(0)                                   # or a GStreamer pipeline string
raw = Stream("front_raw", size=(640, 360), quality=60, fps=15)
dbg = Stream("front_detections", size=(640, 360), quality=50, fps=10)
server = MjpegServer("0.0.0.0", 8090)                      # default is "localhost" = not reachable from topside
server.add_stream(raw); server.add_stream(dbg)              # must be added before start()
server.start()

while True:
    ok, frame = cap.read()
    if not ok: break
    raw.set_frame(frame)
    dbg.set_frame(draw_boxes(frame, detector(frame)))       # your CV output
# topside: http://<rov-ip>:8090/front_raw  and  /front_detections ; index at /
```

- **`Stream(name, size, quality, fps)`**: the name becomes the URL path (lower-cased, spaces become `_`). `quality` runs 1–100, default 50.
- **`get_bandwidth()`**: bytes JPEG-encoded in the last window.
- **CLI:** for a quick test, `mjpeg-streamer -s 0 --quality 60 --fps 15 --show-bandwidth`.

### What the source code tells us (read from the 2024.2.8 wheel)

1. **It encodes once per viewer, not once per frame.** Each HTTP client runs its own loop that resizes and `imencode`s the current frame. Two topside viewers cost twice the CPU, which matters on a Pi 5 with no spare cores.
2. **Pacing is a timer, not new frames.** Each client loop sleeps `1/fps`, then sends whatever frame is current. If the camera is slower it sends duplicates; if encoding is slow the real fps falls below the setting.
3. **It binds to localhost by default.** Pass `"0.0.0.0"` or the tether IP, or topside can't connect.
4. **There is no authentication** and no way to remove a stream after `start()`.
5. **Dependencies:** `aiohttp`, `netifaces`, `numpy` and **`opencv-python`**. On the Jetson, pip's `opencv-python` can shadow JetPack's OpenCV (the one built with GStreamer/CUDA), so install with `pip install --no-deps mjpeg-streamer aiohttp netifaces`.
6. **AGPLv3** is fine for a student team, but anyone given the software over a network is entitled to its source.

Bottom line: use it for **debug and CV views**, where flexibility matters more than efficiency, not as the camera transport.

## MJPEG vs H.264 on our tether

At the same picture quality, MJPEG needed **4–5× the bitrate of H.264** in our test. Its advantages are elsewhere: cheaper encoding, no frame hold, and constant frame sizes.

&#91;embedded content: Measured 2026-11-19 with FFmpeg 6.1 (libx264 veryfast + zerolatency, GOP 30; FFmpeg mjpeg encoder) on the Encoding Lab's synthetic 720p30 clip, 6 s, SSIM on raw-decoded frames\]

The best MJPEG setting (q=3, about JPEG quality 90) reached the SSIM that H.264 gets at CRF 21. Every H.264 point beats every MJPEG point below 12 Mb/s. Real footage with less noise usually widens the gap, because H.264 gains most where consecutive frames are similar.

### Encode speed and frame sizes (720p30, one core, same run)

| Setting | Encode speed (fps, 1 core) | Average frame (kB) | Largest frame (kB) |
| --- | --- | --- | --- |
| MJPEG q=3 | 181 | 48.4 | 53.2 |
| MJPEG q=5 | 217 | 32.3 | 35.6 |
| H.264 ultrafast, zerolatency, CRF 23 | 210 | 12.2 | 65.0 |
| H.264 veryfast, zerolatency, CRF 23 | 84 | 8.0 | 65.0 |

- **Speed:** MJPEG encodes 2.6× faster than x264 veryfast (4.6 ms per 720p frame at q=5).
- **Frame sizes:** MJPEG frames are all about the same size (largest ≈ 1.1× average). H.264 I-frames are 5–8× its average frame. MJPEG therefore has no keyframe spikes for the tether and switch buffers to absorb, but its *average* is 4× higher.

### What the 100 Mb/s tether can carry

These totals use the measured bits per pixel (MJPEG q=5: 0.288; H.264 veryfast CRF 23: 0.072). Our plan caps video at 70% of the measured 94 Mb/s, which is about 66 Mb/s.

| Camera mix | All MJPEG q=5 (Mb/s) | All H.264 (Mb/s) |
| --- | --- | --- |
| Encoding Lab Bandwidth-tab mix: 1080p30 pilot, 720p30 manipulator, 6 small aux at 10–15 fps | 32.0 | 7.9 |
| 8 × 720p30 | 63.7 | 15.8 |
| 2 × 1080p30 + 6 × 720p30 | 83.6 (over budget) | 20.8 |

Small, slow aux cameras are cheap in MJPEG: a 640×480 camera at 15 fps costs about 1.3 Mb/s. The pilot camera alone costs about 17.9 Mb/s at 1080p30, so that is where H.264 pays.

### Latency, loss and hardware

| Factor | MJPEG | H.264 |
| --- | --- | --- |
| Encoder hold | 0 frames | 0 with zerolatency; 31 frames (≈ 1 s) with x264 defaults |
| One lost packet over UDP/RTP | One damaged frame, then clean | Artefacts spread until the next I-frame |
| One lost packet over HTTP/TCP (how both tools send) | Everything stalls until the retransmit; latency can creep up | Same; that's why our main streams use RTP/UDP |
| Raspberry Pi 5 | USB camera MJPEG passes through at zero CPU; CSI camera means software JPEG (fast) | No hardware encoder; software x264 only |
| Jetson Nano | Hardware JPEG encoder (`nvjpegenc`), or passthrough | Hardware H.264/H.265 encoder (`nvv4l2h264enc`) |
| Topside decode | Trivial: any browser `<img>`, OpenCV, VLC | Needs a decoder (GStreamer/FFmpeg); browsers need WebRTC or similar |

## What we could do with it on our ROV

The winning pattern is hybrid. H.264 over RTP/UDP for the cameras the pilot drives with; MJPEG wherever it is free (the camera already makes it) or flexible (we draw on the frames).

&#91;embedded content: Proposed hybrid layout · 3 paths, ports are examples\]

Only the two highlighted boxes are new software; the H.264 path stays as it is.

1. **Auxiliary cameras at almost zero cost.** Rear, claw, sampling or tool cameras: run `mjpg-streamer` with `input_uvc` and the camera's own MJPEG. No CPU encoding, which matters on the Pi 5, and about 1–1.3 Mb/s for each 640×480 camera at 10–15 fps.
2. **Browser GUI tiles with no decoder.** `<img src="http://rov:8080/?action=stream">` is a working video tile in any browser, PyQt `QWebEngineView` or Streamlit page. Each viewer pulls its own copy over the tether, though, so relay it topside (pitfalls section).
3. **CV debug streams.** Publish what the detector sees (bounding boxes, segmentation masks, SLAM keypoints, the 3D-reconstruction mosaic) with the Python `mjpeg-streamer` at low fps and quality. This lets the CV and GUI teams debug in the pool without building a video pipeline.
4. **Measurement and evidence snapshots.** `/?action=snapshot` returns the latest full-quality JPEG in one request. Use it for MATE tasks that need measuring, identifying or photographing something, and as clean stills for photogrammetry.
5. **Training-data recording.** Every MJPEG frame is a clean, standalone image, so recordings (`output_file`, or MJPEG in AVI) become YOLO datasets with no keyframe artefacts and no transcoding.
6. **Fallback stream.** If the H.264 pipeline dies (encoder crash, or overheating like our 2023 failure), a low-res MJPEG passthrough from a USB camera keeps the pilot driving. It barely loads the CPU, so it adds almost no heat.
7. **Bench and pool-day checks.** Plug in a camera, start one command, open a browser. It's the fastest way to check a camera, its focus and its housing.

**Not for:** the pilot and manipulator main views, any camera over about 8 Mb/s in MJPEG, or anything that must stay smooth while the tether is congested (TCP stalls).

## Hands-on recipes

These commands cover the whole loop: check the camera, stream it, view it, then measure it.

### 1. See what your camera can give you

```bash
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video0 --list-formats-ext   # look for 'MJPG' and its sizes/fps
v4l2-ctl -d /dev/video0 --list-ctrls | grep -i -E 'quality|compression'   # some cameras let you set JPEG quality
```

### 2. Stream it

Options **A** and **B** serve HTTP; **C** and **D** use RTP/UDP, matching how our H.264 streams travel.

```bash
# A. USB camera, MJPEG passthrough over HTTP (Pi 5 or Jetson)
mjpg_streamer -i "input_uvc.so -d /dev/video0 -r 640x480 -f 15" -o "output_http.so -p 8080 -n"

# B. Your own frames from Python (CV debug)
pip install mjpeg-streamer --prefer-binary            # Jetson: add --no-deps, keep JetPack's OpenCV
python3 my_cv_node.py                                  # uses Stream(..., fps=<your real CV rate>)

# C. MJPEG over RTP/UDP instead of HTTP: no TCP stalls
#    USB camera, still zero encode:
gst-launch-1.0 v4l2src device=/dev/video0 ! image/jpeg,width=1280,height=720,framerate=30/1 ! \
  rtpjpegpay ! udpsink host=192.168.1.100 port=5600 sync=false

# D. Pi 5 CSI camera (libcamera) -> software JPEG -> RTP
gst-launch-1.0 libcamerasrc ! video/x-raw,width=1280,height=720,framerate=30/1 ! videoconvert ! \
  jpegenc quality=80 ! rtpjpegpay ! udpsink host=192.168.1.100 port=5600 sync=false
```

RTP/JPEG (RFC 2435) is limited to 2040 × 2040 pixels, which is no problem for our cameras.

### 3. View it topside

```bash
# Browser / GUI
<img src="http://192.168.1.10:8080/?action=stream">

# Low-latency player
ffplay -fflags nobuffer -flags low_delay -f mjpeg "http://192.168.1.10:8080/?action=stream"

# GStreamer, HTTP source
gst-launch-1.0 souphttpsrc location="http://192.168.1.10:8080/?action=stream" is-live=true ! \
  multipartdemux ! jpegdec ! autovideosink sync=false

# GStreamer, RTP source (recipes C/D)
gst-launch-1.0 udpsrc port=5600 caps="application/x-rtp,encoding-name=JPEG,payload=26" ! \
  rtpjpegdepay ! jpegdec ! autovideosink sync=false
```

```python
# OpenCV (GUI or topside CV)
cap = cv2.VideoCapture("http://192.168.1.10:8080/?action=stream")
ok, frame = cap.read()
```

### 4. Measure it

```bash
# Real bitrate of one stream (bytes/s -> Mb/s), 10 s sample
curl -s -o /dev/null --max-time 10 -w '%{speed_download}\n' "http://192.168.1.10:8080/?action=stream" \
  | awk '{printf "%.2f Mb/s\n", $1*8/1e6}'

# Per-interface view while all streams run
sudo iftop -i eth0        # or: python3 demos/02_pipeline/monitor.py

# CPU cost on the ROV
pidstat -u -p $(pgrep -d, mjpg_streamer) 1
```

For glass-to-glass latency, use our existing test: point the camera at `demos/01_why_streaming/clock.html` and photograph the screen next to the stream view. Compare MJPEG over HTTP, MJPEG over RTP, and H.264 zerolatency under the same conditions.

## Pitfalls and gotchas

Most MJPEG trouble on an ROV comes from HTTP and USB, not from JPEG itself.

| Pitfall | What you'll see | Fix |
| --- | --- | --- |
| TCP head-of-line blocking | One lost packet freezes the picture until it is retransmitted (Linux's minimum retransmit timeout is 200 ms). If the tether is congested, the socket buffers fill and lag grows | Keep MJPEG streams small; use RTP/UDP (recipes C/D) for anything the pilot watches |
| One copy per viewer | Three laptops watching = 3× the bitrate on the tether | One topside relay: `mjpg_streamer -i "input_http.so ..." -o "output_http.so"` on the topside PC; viewers connect to that |
| Browser connection limit | Browsers allow about 6 open HTTP/1.1 connections per host. A GUI with 7+ MJPEG tiles from one host:port shows a frozen tile, and its API calls hang | Spread streams across ports or hosts, or send one mosaic stream |
| USB bandwidth | The 3rd camera on one controller fails with `No space left on device`, or frames drop | MJPEG mode (never YUYV for several cameras), lower resolution/fps, spread cameras across USB controllers |
| Camera-fixed JPEG quality | Bitrate set by the camera; you can't cap it | Lower resolution/fps, use the quality control if `v4l2-ctl` lists one, or `-y -q 70` to encode yourself (costs CPU) |
| Garbage frames in low light | Tiny corrupt JPEGs flashing | `input_uvc -m <bytes>` drops frames below a size threshold |
| Python lib sends duplicates | Measured: a 5 fps source with `fps=15` sent about 14 fps to the viewer, nearly 3× the needed bandwidth | Set `Stream(fps=...)` to the real camera/CV rate |
| Python lib encodes per viewer | Measured: 2 viewers = 28 encodes/s vs 14 for one viewer | One viewer per stream, or the topside relay above |
| Python lib binds localhost | Topside can't connect | `MjpegServer("0.0.0.0", port)` or the tether IP |
| Full-range colour | Washed-out or crushed colours after converting MJPEG to H.264 or comparing it | MJPEG is full range (`yuvj420p`); convert range explicitly (`-vf scale=out_range=tv`) |
| No security by default | Anyone on the network can view the stream; the project warns against untrusted networks | `-l <tether IP>`, `-c user:pass`, `-n` (no commands); never bridge to the venue Wi-Fi |
| Age of the tools | mjpg-streamer: last commit Feb 2021, `input_raspicam` needs MMAL (absent on Pi 5). mjpeg-streamer: last release Feb 2024, one maintainer, AGPLv3 | Use `input_uvc` and GStreamer for CSI cameras. Both tools are small enough to keep a copy in our repo |

## Decision guide and recommendation

Recommendation: keep H.264 over RTP/UDP for the pilot and manipulator cameras, and adopt MJPEG for aux, debug, snapshot and fallback streams.

| If the stream is… | Use | Why |
| --- | --- | --- |
| What the pilot drives with (1080p/720p, 30 fps) | H.264 over RTP/UDP | 4–5× fewer bits, no TCP stalls |
| A USB aux camera at ≤ 640×480, ≤ 15 fps | mjpg-streamer passthrough | No CPU encode, about 1–1.3 Mb/s |
| Frames we drew on (detections, masks, mosaic) | Python mjpeg-streamer, 5–10 fps, quality 50 | One line per stream, opens in any browser |
| A still for measuring or photogrammetry | `/?action=snapshot` | Full-quality single JPEG on demand |
| Recording for a training dataset | MJPEG file (`output_file` or AVI) | Every frame is a clean image |
| The backup if the H.264 path fails | Low-res MJPEG passthrough | Almost no CPU or heat |

### Next steps

- [ ] Run `v4l2-ctl --list-formats-ext` on every camera we own and record which offer MJPEG and at what sizes
- [ ] Bench-test one aux camera with mjpg-streamer on the Pi 5: CPU %, Mb/s (curl recipe), glass-to-glass latency
- [ ] Compare MJPEG over HTTP vs RTP for the same camera with `demos/02_pipeline/impair.sh` adding 1% loss
- [ ] Add a CV debug stream with the Python library to the detector node, `fps` set to the detector's real rate
- [ ] Add the 'MJPEG' rows in the Encoding Lab Bandwidth tab using our measured 0.288 bpp at q=5, and re-check the tether budget
- [ ] Decide the topside relay: one PC pulls each MJPEG stream once and serves the GUI

## Sources

- [jacksonliam/mjpg-streamer on GitHub](https://github.com/jacksonliam/mjpg-streamer): plugin list, build, usage, licence, security warning. Plugin options and defaults were read from the repository's source (`input_uvc.c`, `output_http.c`, `httpd.c`) at its latest commit, 20 Feb 2021.
- [mjpeg-streamer on PyPI](https://pypi.org/project/mjpeg-streamer/): API, CLI, version 2024.2.8, licence. Behaviour was read from the 2024.2.8 wheel's source and tested locally (duplicate frames, encode per viewer).
- Rate, quality, speed and frame-size figures: measured 2026-11-19 with FFmpeg 6.1 on the Encoding Lab's synthetic 720p30 clip, 2-core Xeon. Re-run on the Pi 5 / Jetson and real pool footage before final decisions.
