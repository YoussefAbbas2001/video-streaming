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

## E. Software testing

- **The Practical Test Pyramid** (Ham Vocke, martinfowler.com) — <https://martinfowler.com/articles/practical-test-pyramid.html> ✔
- **pytest** documentation — <https://docs.pytest.org/> · **GoogleTest** (C++) — <https://google.github.io/googletest/>
- **ISTQB Glossary** (testing terminology) — <https://glossary.istqb.org/>
- Glenford Myers et al., *The Art of Software Testing*, 3rd ed., Wiley ○

## F. Code review and Git

- **Google Engineering Practices — Code Review** — <https://google.github.io/eng-practices/review/> ✔ (both the reviewer's and the author's guide)
- **Conventional Commits** — <https://www.conventionalcommits.org/en/v1.0.0/> ✔
- **Pro Git** (free book) — <https://git-scm.com/book/en/v2>
- **Trunk-Based Development** — <https://trunkbaseddevelopment.com/> ✔
- **Semantic Versioning** — <https://semver.org/>
- GitHub Docs: pull requests, protected branches, Projects — <https://docs.github.com/>

## G. Team organisation

- **The Kanban Guide** — <https://kanbanguides.org/> ✔
- **The Scrum Guide** (for vocabulary: sprint, backlog refinement, retrospective) — <https://scrumguides.org/>
- **Architecture Decision Records** (decision log format) — <https://adr.github.io/>
- Atlassian Agile Coach (practical articles on boards, user stories, DoD) — <https://www.atlassian.com/agile>

## H. UX, human factors and safety

- **Nielsen's 10 usability heuristics** — <https://www.nngroup.com/articles/ten-usability-heuristics/> ✔
- **Why you only need to test with 5 users** — <https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/> ✔
- **System Usability Scale (SUS)** — <https://measuringu.com/sus/> ✔ · original: J. Brooke, "SUS: a 'quick and dirty' usability scale", 1996 ○
- **Situational awareness** — M. R. Endsley, "Toward a Theory of Situation Awareness in Dynamic Systems", *Human Factors* 37(1), 1995 ○
- **Cognitive load / workload** — NASA-TLX (task load index) for measuring pilot workload: <https://humansystems.arc.nasa.gov/groups/tlx/>
- **Design tools** — Figma for Education: <https://www.figma.com/education/> · Penpot (open source): <https://penpot.app/> ✔ · Excalidraw: <https://excalidraw.com/>
- Don Norman, *The Design of Everyday Things* (revised ed., 2013) ○ — feedback, mapping, error prevention

## I. Underwater imaging & ROVs (background)

- **MATE ROV Competition** — <https://materovcompetition.org/> (competition manuals, scoring, specs; check the current season)
- **Marine Technology Society ROV Committee** — <https://www.rov.org/>
- R. D. Christ & R. L. Wernli, *The ROV Manual: A User Guide for Remotely Operated Vehicles*, 2nd ed., Butterworth-Heinemann, 2013 ○ — chapters on cameras, lighting, tethers and telemetry
