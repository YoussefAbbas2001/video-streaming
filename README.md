# M.I.A Robotics ·  Video Streaming

Everything for video streaming on the ROV: the slide deck, three recorded videos, the **ROV Encoding Lab** app we use live in the session, the write-ups, the ROV experiments and the debug checklist.


> A video stream is not just a camera feed. It is a real-time information pipeline with limited bandwidth, processing power and latency budget.

## Start here

| I am… | Go to |
|---|---|
| **In the session** | Run the [Encoding Lab](encoding_lab/) (below). Every experiment in the deck is done there, live. |
| **Following the slides in a notebook** | [`encoding_lab/notebooks/ROV_Video_Streaming_Workshop.ipynb`](encoding_lab/notebooks/ROV_Video_Streaming_Workshop.ipynb): 35 experiments in slide order, most with live sliders |
| **Trying a camera and an encoder live** | Encoding Lab → **Live camera** tab (laptop camera, MJPEG passthrough vs x264 vs NVENC, with a latency overlay) |
| **Benchmarking the Pi 5 / Jetson / laptop** | Run the Encoding Lab on that computer → **Bandwidth budget → Measure this computer** |
| **🧪 Homework: experiments on the real ROV** (members) | [`docs/experiments/ROV_Experiments.md`](docs/experiments/ROV_Experiments.md) |
| **🧑‍🍳 A team leader running the experiments with members** | [`docs/experiments/Leader_Guide.md`](docs/experiments/Leader_Guide.md): six 90-minute session recipes, answer key, result sheet |
| **🩺 The video is broken right now** | [`docs/debug/ROV_Debug_Checklist.md`](docs/debug/ROV_Debug_Checklist.md) + `bash docs/debug/rov_healthcheck.sh` on the ROV (✅ ⚠️ ❌ for about 20 checks in 10 s) |
| **Measuring our ROV, diagnosing a bad picture (45 symptoms with pictures), throughput and loss in the GUI** | [`docs/streaming/measure-and-diagnose.md`](docs/streaming/measure-and-diagnose.md) |
| **Choosing cameras and the encoder board (Jetson Nano 2GB vs Raspberry Pi 5), heat** | [`docs/streaming/hardware-and-encoders.md`](docs/streaming/hardware-and-encoders.md) |
| **Why compression matters, MJPEG cameras, lowering their resolution, NVENC, FFmpeg recipes** | [`docs/streaming/codecs-and-ffmpeg.md`](docs/streaming/codecs-and-ffmpeg.md) |
| **Testing, the Bug Hunt League, the GitHub workflow, the knowledge exchange** | the [mia-software-practice](https://github.com/YoussefAbbas2001/mia-software-practice) repo |
| **Presenting** | [`presentation/`](presentation/) + [`workshop/presenter_guide/`](workshop/presenter_guide/) |

## What's in the repo

```
├── presentation/   MIA_Video_Streaming.pptx (87 slides), click-by-click builds, speaker notes
├── encoding_lab/   ROV Encoding Lab: Streamlit app — Encode, Live camera, Sweep, Bandwidth budget, Report, Learn
│                   + notebooks/: the session notebook, every experiment in slide order
├── docs/
│   ├── streaming/  measure and diagnose (45-problem field guide), hardware and encoders, codecs and FFmpeg
│   ├── experiments/ the ROV experiments: member handbook, leader's recipe, ms clock, leaderboard
│   └── debug/      the debug checklist and rov_healthcheck.sh
├── assets/         sample 4K clips to upload into the Encoding Lab
├── build/          scripts that generate slides and insert them into the decks (see build/README.md)
└── .github/        video bug, task and experiment-result forms, PR template, CI that runs the tests on every pull request
```

## Quick start

```bash
sudo apt install ffmpeg                      # macOS: brew install ffmpeg · Windows: winget install ffmpeg
pip install -r encoding_lab/requirements.txt
streamlit run encoding_lab/app.py            # the Encoding Lab, at http://localhost:8501
```

## Documents (Google Docs)

| Document | For |
|---|---|
| [Video Scripts (Arabic)](https://docs.google.com/document/d/1SWHGTSIQwwm1V1WtW0lmQqg6DUTXLM_mvFM8sI3jAlc/edit) | Recording the three videos |
| [MJPEG on our ROV, and why we use FFmpeg for it](https://docs.google.com/document/d/1814_NgCNUHJoMfy_53jX56oLAWMsYRoZREwSixIuZwM/edit) | Reading version of `docs/streaming/codecs-and-ffmpeg.md` (Nov 19 version) |
| [Streaming Deep-Dive: 2026–27 additions](https://docs.google.com/document/d/1LyPRCtvt5-wCSomRh4We0snjWo5Yv7CyVO2TjXJWTn8/edit) | Reading version of `docs/streaming/` |
| [Workshop Reader](https://docs.google.com/document/d/1vyha2504cYxIiiDhl5IKH1ydGZGvKrHlJblZICibaT0/edit) | The whole workshop at moderate detail |
| [Video Streaming Brief (2 pages)](https://docs.google.com/document/d/1hb-U9hiFSG3xVDgvLhOdzBjFPkTLvZAK1YtnlFWPguw/edit) | Two-page, two-column summary of video streaming |

The Markdown in this repo is the source; the Google Docs are for reading and printing and can lag behind it. They are private until shared, so share them with the team from Drive.

## Big files on Drive

Git is for code and text. These live in Drive; add the links when they exist:

| Item | Why not in Git | Link |
|---|---|---|
| Recorded videos 1–3 | Hundreds of MB each | *add link* |
| Raw ROV footage for the Encoding Lab | Large media | *add link* |
| Presenter-only `referee/` (testing-competition answer key) | Must stay secret from the team | *add link* |

Files over 50 MB trigger GitHub warnings, and files over 100 MB are rejected. The 4K clips in `assets/` are close to that limit; new footage goes to Drive.

## Rules of the road

- Nothing goes to `master` without a pull request and one review (see the [GitHub workflow](https://github.com/YoussefAbbas2001/mia-software-practice/blob/HEAD/docs/github-workflow.md)).
- Tag the version that goes into the water before every pool test: `git tag -a v0.x-pool-test`.
- Numbers beat opinions: put measurements in your PR.


# References and Recommended Learning Resources

Selected for quality and practicality: official documentation first, then excellent tutorials and standards.
**Link status** (checked 18 Nov 2026): ✔ = opened successfully during preparation · ◐ = valid site, but it blocks automated checks (open it in a browser) · ○ = standard/book reference, not fetched.

---

## A. Facts used in the workshop (cite these if a judge asks)

| Claim in the material | Source | Status |
|---|---|---|
| Jetson Nano: hardware encode 4Kp30 · 4× 1080p30 · 9× 720p30 (H.264/H.265); decode 4Kp60 · 8× 1080p30 | NVIDIA Jetson Store / Nano module specifications — <https://www.nvidia.com/en-au/autonomous-machines/jetson-store/> | ✔ |
| Jetson Nano encoders in GStreamer: `nvv4l2h264enc`, `nvv4l2h265enc` | NVIDIA L4T *Accelerated GStreamer* guide (Jetson Nano, R32.x) — <https://docs.nvidia.com/jetson/archives/l4t-archived/l4t-3242/Tegra%20Linux%20Driver%20Package%20Development%20Guide/accelerated_gstreamer.html> | ✔ (search) |
| FFmpeg does not use the Jetson's hardware encoder upstream; community patch exists | NVIDIA developer forum (NVIDIA staff answer) — <https://forums.developer.nvidia.com/t/using-fully-accelerated-hardware-based-video-decoding-and-encoding-with-ffmpeg-on-jetson-nano/122949/3> · community patch: <https://github.com/jocover/jetson-ffmpeg> | ✔ (search) |
| Jetson Nano supported up to JetPack 4.6.x | NVIDIA developer forum — <https://forums.developer.nvidia.com/t/does-jetson-nano-support-hardware-encoding-nvenc-in-deepstream-7-1/354032> | ✔ (search) |
| Jetson **Orin** Nano has no hardware video encoder (1080p30 via 1–2 CPU cores) | Jetson Orin Nano datasheet / NVIDIA spec tables; RidgeRun — <https://www.ridgerun.com/post/jetson-orin-nano-how-to-achieve-real-time-performance-for-video-encoding> | ✔ (search) |
| Raspberry Pi 5: 4Kp60 HEVC decoder; no hardware H.264 encoder | Raspberry Pi 5 launch post — <https://www.raspberrypi.com/news/introducing-raspberry-pi-5/> · Raspberry Pi processor documentation (BCM2712) — <https://www.raspberrypi.com/documentation/computers/processors.html> | ✔ |
| Raspberry Pi 5 libx264 1080p30: ≈ 62–90 % of one core (low-latency config), ≈ 98–153 % (higher-quality config) | Raspberry Pi Ltd, *H.264 encoding performance on Raspberry Pi 5-series computers*, white paper, Apr 2026 — <https://pip-assets.raspberrypi.com/categories/685-app-notes-guides-whitepapers/documents/RP-010033-WP-1-H.264%20encoding%20performance%20on%20Raspberry%20Pi%205_series%20computers.pdf> | ✔ |
| RTP payload format for H.264 | RFC 6184 — <https://www.rfc-editor.org/rfc/rfc6184> | ✔ |
| MediaMTX converts between RTSP, WebRTC, SRT, HLS… | <https://github.com/bluenviron/mediamtx> | ✔ (search) |
| MATE ROV Competition structure and current season | <https://materovcompetition.org/> | ✔ (search) |
| Five users find most usability problems | Nielsen Norman Group — <https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/> | ✔ |

Note: the Raspberry Pi processor documentation quotes "H264 1080p30 encode (from ISP) ~30–40 % CPU", while the 2026 white paper reports % of a *single core* for a different pipeline. The two use different set-ups and units — measure on your own board.

---

## B. Video, codecs, FFmpeg

- **FFmpeg documentation** — <https://ffmpeg.org/documentation.html> · `ffmpeg` tool: <https://ffmpeg.org/ffmpeg.html> · filters (psnr, ssim, libvmaf, scale, fps…): <https://ffmpeg.org/ffmpeg-filters.html> ✔ · formats/protocols: <https://ffmpeg.org/ffmpeg-formats.html>, <https://ffmpeg.org/ffmpeg-protocols.html>
- **FFmpeg wiki** (practical guides) — H.264: <https://trac.ffmpeg.org/wiki/Encode/H.264> ◐ · H.265: <https://trac.ffmpeg.org/wiki/Encode/H.265> ◐ · Streaming guide: <https://trac.ffmpeg.org/wiki/StreamingGuide> ◐ · Hardware acceleration: <https://trac.ffmpeg.org/wiki/HWAccelIntro> ◐
- **x264 options** — `x264 --fullhelp` (presets, tunes, rate control); FFmpeg: `ffmpeg -h encoder=libx264`
- **VMAF** — <https://github.com/Netflix/vmaf> ✔
- **SSIM** — Z. Wang, A. Bovik, H. Sheikh, E. Simoncelli, "Image quality assessment: from error visibility to structural similarity", *IEEE Trans. Image Processing*, 13(4), 2004 ○
- **Books** — I. Richardson, *The H.264 Advanced Video Compression Standard*, 2nd ed., Wiley, 2010 ○ · V. Sze, M. Budagavi, G. Sullivan (eds.), *High Efficiency Video Coding (HEVC): Algorithms and Architectures*, Springer, 2014 (open access) ○
- **Codec overview** — G. Sullivan et al., "Overview of the High Efficiency Video Coding (HEVC) Standard", *IEEE TCSVT*, 2012 ○ · T. Wiegand et al., "Overview of the H.264/AVC Video Coding Standard", *IEEE TCSVT*, 2003 ○

## C. GStreamer and the boards

- **GStreamer documentation** — <https://gstreamer.freedesktop.org/documentation/> · tutorials: <https://gstreamer.freedesktop.org/documentation/tutorials/>
- **NVIDIA Jetson Linux Developer Guide (archives)** — <https://docs.nvidia.com/jetson/archives/> (pick the L4T R32.x release that matches your Jetson Nano's JetPack)
- **Jetson Multimedia API** — samples for V4L2 M2M encode/decode (in the Jetson Linux docs above)
- **Raspberry Pi documentation** — <https://www.raspberrypi.com/documentation/> · camera software (`rpicam-apps`): <https://www.raspberrypi.com/documentation/computers/camera_software.html>
- **V4L2 / UVC on Linux** — `v4l2-ctl` (package `v4l-utils`); kernel media docs: <https://docs.kernel.org/userspace-api/media/v4l/v4l2.html>
- **USB 2.0 specification** (periodic bandwidth, isochronous transfers) — <https://www.usb.org/document-library/usb-20-specification> ○

## D. Networking and real-time streaming

- **RTP** RFC 3550 — <https://www.rfc-editor.org/rfc/rfc3550> · **RTSP 2.0** RFC 7826 — <https://www.rfc-editor.org/rfc/rfc7826> (RTSP 1.0: RFC 2326) · **H.264 over RTP** RFC 6184 ✔ · **H.265 over RTP** RFC 7798
- **WebRTC** — <https://webrtc.org/> · MDN WebRTC API: <https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API> · WHEP (WebRTC playback over HTTP): IETF draft "WebRTC-HTTP Egress Protocol"
- **MediaMTX** — <https://github.com/bluenviron/mediamtx> ✔
- **iperf3** — <https://iperf.fr/> · **tc netem** (simulate delay/loss) — <https://man7.org/linux/man-pages/man8/tc-netem.8.html> ✔
- **Wireshark** user guide — <https://www.wireshark.org/docs/>

Testing, code review, team organisation and UX references moved to the [mia-software-practice repo](https://github.com/YoussefAbbas2001/mia-software-practice/blob/HEAD/workshop/resources/References.md).

## E. Underwater imaging & ROVs (background)

- **MATE ROV Competition** — <https://materovcompetition.org/> (competition manuals, scoring, specs; check the current season)
- **Marine Technology Society ROV Committee** — <https://www.rov.org/>
- R. D. Christ & R. L. Wernli, *The ROV Manual: A User Guide for Remotely Operated Vehicles*, 2nd ed., Butterworth-Heinemann, 2013 ○ — chapters on cameras, lighting, tethers and telemetry
