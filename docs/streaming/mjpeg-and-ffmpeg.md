# MJPEG on our ROV, and why we use FFmpeg for it

*M.I.A Robotics · streaming reading · measured 19–21 Nov 2026 (FFmpeg 6.1, Encoding Lab synthetic 720p30 clip)*

**In one paragraph.** MJPEG is video made of separate JPEG photos. No frame depends on another, so encoding is cheap, there is no frame hold, and a broken frame never smears into the next one. The price is size: about **4–5× the bitrate of H.264** for the same picture quality (measured below). We keep **H.264 over RTP/UDP** for the pilot and manipulator cameras, and use MJPEG for aux cameras, CV debug views, snapshots, recordings and the fallback stream. **We build all of it with FFmpeg**, not with `mjpeg-streamer` (Python) or `mjpg-streamer` (C).

**Try it live:** Encoding Lab → **Live camera** tab: your laptop camera with MJPEG passthrough, MJPEG re-encode, x264 or NVENC, and what each stage costs.

**Two things the team should know first:**

1. Lowering an MJPEG camera's resolution is free **only if the camera does it** ([§ The resolution trap](#the-resolution-trap)).
2. When a camera must be re-encoded, a hardware encoder such as NVENC or the Jetson's beats software MJPEG ([§ Better than re-encoding MJPEG](#better-than-re-encoding-mjpeg-nvenc-and-friends)).

---

## 1. What MJPEG is

Each frame is compressed on its own as a JPEG (DCT blocks, quantisation set by a quality factor, entropy coding). There are no motion vectors, reference frames or GOP; every frame is effectively an I-frame.

| Property | MJPEG | H.264 / H.265 |
|---|---|---|
| Frame dependency | None | P/B frames need earlier (and later) frames |
| Encoder frame hold | 0 frames | 0 with `-tune zerolatency`; 31 frames with x264 defaults (Encoding Lab) |
| Bits for the same quality | High (0.29 bits/pixel at q=5, measured) | Low (0.07 bits/pixel, x264 veryfast CRF 23) |
| A lost packet over UDP | One frame damaged, the next is clean | Artefacts until the next I-frame |
| CPU to encode | Low, often zero (the camera does it) | High in software; needs a hardware encoder on small boards |

**How it travels.** The common way is HTTP with `Content-Type: multipart/x-mixed-replace`: one response that never ends, carrying JPEG after JPEG between boundary lines. Browsers show it in a plain `<img>` tag. It can also travel as RTP over UDP (RFC 2435, payload type 26), or be stored in AVI/MOV.

**Why USB cameras give it to us for free.** Raw 1080p30 YUYV is about 995 Mb/s, more than USB 2.0's 480 Mb/s. So UVC cameras compress to MJPEG on their own chip, and the Pi or Jetson receives frames that are already compressed. Check with `v4l2-ctl -d /dev/video0 --list-formats-ext` (look for `MJPG`).

## 2. MJPEG vs H.264, measured

720p30, 6 s synthetic underwater clip, SSIM against the source on raw-decoded frames, one CPU core.

| Setting | Bitrate (Mb/s) | SSIM | Encode speed (fps, 1 core) | Avg / largest frame (kB) |
|---|---|---|---|---|
| MJPEG q=12 (≈ JPEG 55) | 4.06 | 0.958 | 284 | 16.5 / 17.9 |
| MJPEG q=8 (≈ JPEG 70) | 5.50 | 0.968 | 246 | 22.3 / 24.5 |
| MJPEG q=5 (≈ JPEG 80) | 7.96 | 0.978 | 217 | 32.3 / 35.6 |
| MJPEG q=3 (≈ JPEG 90) | 11.90 | 0.984 | 181 | 48.4 / 53.2 |
| H.264 veryfast zerolatency CRF 23 | 1.98 | 0.981 | 84 | 8.0 / 65.0 |
| H.264 veryfast zerolatency CRF 21 | 2.52 | 0.984 | — | — |
| H.264 ultrafast zerolatency CRF 23 | 3.00 | 0.978 | 210 | 12.2 / 65.0 |

- **Same quality:** MJPEG q=3 matches H.264 CRF 21's SSIM at **4.7× the bitrate**.
- **Frame sizes:** MJPEG frames are all about the same size. H.264 I-frames spike to 5–8× its average frame.
- **Speed:** MJPEG encodes about 2.6× faster than x264 veryfast.

**What the 100 Mb/s tether can carry.** We plan video at 70% of the measured 94 Mb/s, which is about 66 Mb/s.

| Camera mix | All MJPEG q=5 | All H.264 |
|---|---|---|
| Encoding Lab Bandwidth-budget mix (1080p30 pilot, 720p30 manipulator, 6 small aux at 10–15 fps) | 32.0 Mb/s | 7.9 Mb/s |
| 8 × 720p30 | 63.7 Mb/s | 15.8 Mb/s |
| 2 × 1080p30 + 6 × 720p30 | 83.6 Mb/s (over budget) | 20.8 Mb/s |

A 640×480 aux camera at 15 fps costs about 1.3 Mb/s in MJPEG. The pilot camera at 1080p30 would cost about 17.9 Mb/s, so that is where H.264 pays for itself.

## 3. The three tools, compared

[mjpg-streamer](https://github.com/jacksonliam/mjpg-streamer) is a C program with input/output plugins. It was last changed in Feb 2021, and its Pi camera plugin needs MMAL, which the Pi 5 doesn't have. [mjpeg-streamer](https://pypi.org/project/mjpeg-streamer/) is a Python library: OpenCV frames in, HTTP out (2024.2.8, AGPLv3).

| Capability | mjpeg-streamer (Python) | mjpg-streamer (C) | **FFmpeg** |
|---|---|---|---|
| Camera MJPEG passthrough, no encode | No: decodes, then re-encodes | Yes | **Yes**, `-c:v copy`: 1.3% of one core for 720p30 (measured) |
| Encode our own CV frames | Yes, but once **per viewer** (measured: 2 viewers = 2× encodes) | Only via `input_opencv` | **Yes, once per frame** (OpenCV → stdin pipe) |
| Frame pacing | Timer: duplicates (measured ≈ 3× the frames of a 5 fps source) | Camera-driven | **Source-driven**, one out per one in |
| HTTP stream to a browser | Yes, many viewers | Yes, many viewers | Yes, **one viewer per process** (`-listen 1` + `-content_type`) |
| RTP/UDP (no TCP stalls) | No | Listed as not functional | **Yes**, `-f rtp` (`-huffman default` when encoding) |
| Stream + record + snapshot, one capture | No | Separate plugins | **`tee` muxer**, no re-encode |
| Scale, crop, colour-correct, timestamp | Resize only | Camera controls only | **Hundreds of filters** |
| Switch to H.264/H.265 | No | No | **Same command**, different `-c:v` |
| Measure quality and speed | No | No | **`ssim`, `psnr`, `-benchmark`** (the Encoding Lab uses them) |
| Maintenance | One maintainer, Feb 2024 | Last commit Feb 2021 | Active, in every Linux distro |

**Verdict:** use FFmpeg. It is already installed for the Encoding Lab, it does every job above, and it grows with us when a stream needs H.264, a filter or a recording.

## 4. FFmpeg recipes (all tested except the `/dev/video0` capture lines)

```bash
# 1. USB camera MJPEG passthrough to a browser
ffmpeg -f v4l2 -input_format mjpeg -video_size 1280x720 -framerate 30 -i /dev/video0 \
       -c:v copy -f mpjpeg -content_type "multipart/x-mixed-replace;boundary=ffmpeg" \
       -listen 1 http://0.0.0.0:8080/aux1.mjpg
# browser: <img src="http://<rov-ip>:8080/aux1.mjpg">   (without -content_type the browser won't display it)

# 2. Same camera over RTP/UDP: no TCP stalls, one copy on the tether
ffmpeg -f v4l2 -input_format mjpeg -video_size 1280x720 -framerate 30 -i /dev/video0 \
       -c:v copy -f rtp -sdp_file aux1.sdp rtp://192.168.1.100:5600
# topside: ffplay -protocol_whitelist file,udp,rtp -fflags nobuffer -flags low_delay aux1.sdp

# 3. One capture -> live RTP + recording + always-fresh snapshot (no re-encode)
ffmpeg -f v4l2 -input_format mjpeg -video_size 1280x720 -framerate 30 -i /dev/video0 -map 0:v -c:v copy \
       -f tee "[f=rtp]rtp://192.168.1.100:5600|[f=avi]dive_$(date +%H%M%S).avi|[f=image2:update=1]/tmp/aux1_latest.jpg"

# 4. Smaller, time-stamped stream for a GUI tile (re-encode, about 13% of one core 720p -> 640x360)
ffmpeg -f v4l2 -input_format mjpeg -video_size 1280x720 -framerate 30 -i /dev/video0 \
       -vf "scale=640:-2,drawtext=text='%{localtime}':x=10:y=10:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.5" \
       -c:v mjpeg -q:v 7 -huffman default -f rtp rtp://192.168.1.100:5602
```

```python
# 5. CV debug stream: OpenCV draws, FFmpeg encodes each frame once
import subprocess, cv2
W, H, FPS = 640, 360, 10                                  # FPS = the detector's real rate
ff = subprocess.Popen(["ffmpeg", "-loglevel", "error",
    "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-c:v", "mjpeg", "-q:v", "7", "-huffman", "default",
    "-f", "rtp", "-sdp_file", "det.sdp", "rtp://192.168.1.100:5610"], stdin=subprocess.PIPE)
while True:
    frame = cv2.resize(camera.read(), (W, H))
    ff.stdin.write(draw_detections(frame, model(frame)).tobytes())
```

**The one gap.** FFmpeg's built-in HTTP server takes one viewer, and the process ends when that viewer disconnects. Three ways to cover it:

- **One GUI tile per stream:** run it in a loop (a `while true; do ffmpeg …; sleep 0.5; done` loop) or as a systemd service with `Restart=always`.
- **Several viewers:** send RTP once over the tether, and let every viewer on the topside PC open the same `.sdp`.
- **Several browsers:** put a relay on the topside PC, never on the ROV, so only one copy crosses the tether.

## The resolution trap

The team streams USB cameras with mjpeg-streamer and **lowers the resolution**. Whether that costs anything depends on **where** the resolution is lowered.

| How the resolution is lowered | What happens to every frame | Cost (720p30 → 640×360, measured) |
|---|---|---|
| **Ask the camera:** mjpg-streamer `input_uvc -r 640x480`, FFmpeg `-input_format mjpeg -video_size 640x480 … -c:v copy` | The camera's chip makes the smaller JPEGs. **Nothing is decoded or encoded** on the ROV. | ≈ 1 % of a core (copy only) |
| **Shrink in software:** PyPI mjpeg-streamer `Stream(size=…)`, any OpenCV `resize`, FFmpeg `-vf scale` | **decode → scale → encode**. The PyPI library repeats the encode **for every viewer**. | JPEG decode ≈ 2.4 ms + scale ≈ 0.4 ms + JPEG encode ≈ 0.9 ms per frame ≈ **13 % of a core** per camera |
| **Ask for raw frames:** mjpg-streamer `-y` (YUYV) | the CPU encodes every JPEG (no decode) | an encode per frame; USB 2.0 also limits raw frames to small sizes |

Measured with the Encoding Lab's Live camera tab (passthrough vs Output size 50 %) on a 2-core test PC; an ARM board pays more.

**How to tell which one you have:**

```bash
v4l2-ctl -d /dev/video0 --list-formats-ext        # every size listed under 'MJPG' is made by the camera itself
ffmpeg -f v4l2 -list_formats all -i /dev/video0   # the same list, from FFmpeg
```

mjpg-streamer asks the camera (V4L2) for the size you pass with `-r`. If the camera does not offer that size in MJPG, the driver picks the closest size it has and mjpg-streamer prints `The specified resolution is unavailable, using: width … height … instead` (from its `v4l2uvc.c`). mjpg-streamer has no scaler of its own, so with `input_uvc` in MJPEG mode it never decodes or re-encodes. The **PyPI** `mjpeg-streamer` library always works on decoded OpenCV frames, so shrinking with it is always decode → scale → encode.

**If the size you need is not offered,** a transcode is unavoidable, so make it count. Encode that camera to **H.264**: one encode, and 4–5 × fewer bits than a smaller MJPEG. Do it in hardware where you can (next section).

## Better than re-encoding MJPEG: NVENC and friends

Once a camera has to be decoded anyway, re-encoding to MJPEG wastes the work. An H.264 encoder gives 4–5 × fewer bits for the same decode, and a **hardware** encoder does it with almost no CPU. Each option below shows up in the Live camera tab when the computer running the lab has it.

| Option | Where it exists | FFmpeg / GStreamer | Notes |
|---|---|---|---|
| **NVENC** | NVIDIA GPUs (pilot laptop, desktop) | `-c:v h264_nvenc -preset p1 -tune ull -zerolatency 1 -bf 0 -b:v 2M` | very low latency, near-zero CPU; also `hevc_nvenc` (and `av1_nvenc` on RTX 40+) |
| **Jetson hardware encoder** | Jetson Nano / Orin | GStreamer `nvv4l2h264enc` (MJPEG in: `nvv4l2decoder mjpeg=1`) | ≈ 4 × 1080p30; mainline FFmpeg cannot use it; see [jetson-nano-vs-pi5.md](jetson-nano-vs-pi5.md) |
| **Intel Quick Sync** | most Intel laptops | `-c:v h264_qsv -preset veryfast -async_depth 1` | good for a topside relay or recorder |
| **AMD AMF** | AMD GPUs (Windows) | `-c:v h264_amf -usage ultralowlatency` | |
| **VA-API** | Intel/AMD on Linux | `-vaapi_device /dev/dri/renderD128 -vf format=nv12,hwupload -c:v h264_vaapi` | |
| **V4L2 M2M** | Raspberry Pi 4 (not Pi 5) | `-c:v h264_v4l2m2m` | the Pi 5 has no hardware H.264 encoder |
| **x264 ultrafast + zerolatency** | any CPU, incl. Pi 5 | `-c:v libx264 -preset ultrafast -tune zerolatency` | the universal fallback; ≈ 62–90 % of a Pi 5 core per 1080p30 stream (Raspberry Pi white paper, Apr 2026) |
| **Cameras that encode H.264 themselves** | IP cameras, UVC H.264 cameras | `-c:v copy` | no ROV CPU at all; check their GOP and latency settings |

Rule of thumb for our ROV:

- **Small aux cameras:** MJPEG passthrough at a size the camera offers.
- **Main cameras:** H.264, from the camera itself, from a hardware encoder, or from x264 zerolatency.
- **Never shrink MJPEG in software.**

## 5. Where MJPEG helps us

1. **Aux cameras at almost zero cost:** `-c:v copy` of the camera's own MJPEG, about 1–1.3 Mb/s per 640×480 camera at 10–15 fps.
2. **Browser GUI tiles** with no decoder: a plain `<img>` tag.
3. **CV debug streams:** detections, masks, SLAM keypoints, the 3D-reconstruction mosaic.
4. **Measurement snapshots:** `image2` with `update=1` keeps the latest full-quality JPEG on disk.
5. **Training data:** every recorded frame is a clean standalone image for YOLO labelling.
6. **Fallback stream** if the H.264 path fails (crash, or heat like 2023). Passthrough adds almost no CPU heat.
7. **Bench and pool checks:** one command, one browser tab.

**Not for:** the pilot and manipulator main views, cameras above about 8 Mb/s, or anything that must stay smooth on a congested tether.

## 6. Pitfalls

| Pitfall | What you'll see | Fix |
|---|---|---|
| HTTP is TCP | One lost packet freezes the picture until it is retransmitted (≥ 200 ms on Linux); lag grows when congested | RTP/UDP for anything the pilot watches |
| One copy per viewer | 3 laptops watching = 3× the bitrate on the tether | RTP once, or a topside relay |
| Browser connection limit | Browsers allow about 6 HTTP/1.1 connections per host, so the 7th tile freezes | Spread streams across ports or hosts, or send one mosaic |
| USB bandwidth | `No space left on device` on the 3rd camera | MJPEG mode, lower resolution/fps, spread across USB controllers |
| Camera-fixed JPEG quality | You can't cap the bitrate | Lower resolution/fps, or re-encode (recipe 4) |
| RTP needs standard Huffman tables | `RFC 2435 requires standard Huffman tables` | `-huffman default` when FFmpeg encodes |
| Full-range colour | Washed-out or crushed colours after conversion | MJPEG is `yuvj420p` (full range); convert explicitly |
| FFmpeg HTTP output looks like a download | Browser shows nothing | Add `-content_type "multipart/x-mixed-replace;boundary=ffmpeg"` |
| No security | Anyone on the network can watch | Bind to the tether IP; never bridge to venue Wi-Fi |

## 7. Next steps

- [ ] List the formats of every camera we own (`v4l2-ctl --list-formats-ext`)
- [ ] Bench one aux camera on the Pi 5 with recipe 3 (tee): CPU %, Mb/s, glass-to-glass latency (photograph a phone stopwatch next to the pilot screen)
- [ ] For every camera, check whether the size we stream is one the camera makes itself (`v4l2-ctl --list-formats-ext`); if not, switch that camera to H.264
- [ ] Compare MJPEG over HTTP vs RTP with 1% loss (`impair.sh`)
- [ ] Put the CV debug pipe (recipe 5) behind the real detector, at its real frame rate
- [ ] Re-run the measurements on the Pi 5 / Jetson with pool footage

Sources: [mjpg-streamer on GitHub](https://github.com/jacksonliam/mjpg-streamer) (plugin options read from its source at the 20 Feb 2021 commit) · [mjpeg-streamer on PyPI](https://pypi.org/project/mjpeg-streamer/) (behaviour read from the 2024.2.8 source and tested) · all numbers measured by us on 19 Nov 2026.
