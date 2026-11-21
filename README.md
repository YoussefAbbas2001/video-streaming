# M.I.A Robotics · ROV Video Streaming

Everything for our video-streaming session: two slide decks, three recorded videos, the **ROV Encoding Lab** app we use live in the session, write-ups, and the engineering-practice session.

> A video stream is not just a camera feed. It is a real-time information pipeline with limited bandwidth, processing power and latency budget.

## Start here

| I am… | Go to |
|---|---|
| **In the session** | Run the [Encoding Lab](encoding_lab/) (below). Every experiment in the deck is done there, live. |
| **Watching the videos** | [`videos/`](videos/): three videos, about 25 min |
| **Trying a camera and an encoder live** | Encoding Lab → **Live camera** tab (laptop camera, MJPEG passthrough vs x264 vs NVENC, with a latency overlay) |
| **Benchmarking the Pi 5 / Jetson / laptop** | Run the Encoding Lab on that computer → **Benchmark** tab |
| **Choosing Jetson Nano 2GB vs Raspberry Pi 5** | [`docs/streaming/jetson-nano-vs-pi5.md`](docs/streaming/jetson-nano-vs-pi5.md) |
| **MJPEG cameras, lowering their resolution, NVENC** | [`docs/streaming/mjpeg-and-ffmpeg.md`](docs/streaming/mjpeg-and-ffmpeg.md) |
| **Adding bandwidth and loss to the pilot GUI** | [`docs/streaming/gui-stream-metrics.md`](docs/streaming/gui-stream-metrics.md) |
| **Measuring our ROV** | [`docs/streaming/measuring-performance.md`](docs/streaming/measuring-performance.md) |
| **Testing the GUI (everyone!)** | [`docs/sdlc/bug-hunt-league.md`](docs/sdlc/bug-hunt-league.md), then open an issue with the 🐞 Bug report form |
| **Running the weekly knowledge exchange** | [`docs/sdlc/knowledge-exchange.md`](docs/sdlc/knowledge-exchange.md) |
| **Contributing code** | [`docs/sdlc/github-workflow.md`](docs/sdlc/github-workflow.md) |
| **Presenting** | [`presentation/`](presentation/) + [`workshop/presenter_guide/`](workshop/presenter_guide/) + [`docs/sdlc/live-session-plan.md`](docs/sdlc/live-session-plan.md) |

## What's in the repo

```
├── presentation/   MIA_Video_Streaming.pptx (56 slides) and MIA_Software_Dev_Cycle.pptx (36 slides), click-by-click builds, speaker notes
├── encoding_lab/   ROV Encoding Lab: Streamlit app — Encode, Live camera, Sweep, Benchmark, Packet loss, Bandwidth, Report, Learn
├── docs/
│   ├── streaming/  compression economics, USB vs IP, Jetson Nano vs Pi 5, MJPEG + FFmpeg, GUI stream metrics, measuring
│   └── sdlc/       Quality × Efficiency, Bug Hunt League, GitHub workflow, knowledge exchange, postmortems
├── videos/         Arabic scripts for the 3 recorded videos + recording checklist
├── workshop/       the full workshop (presenter guide, student materials, activities, UX pack)
├── assets/         sample 4K clips to upload into the Encoding Lab
├── build/          scripts that generate slides and insert them into the decks (see build/README.md)
└── .github/        bug and task forms, PR template, CI that runs the tests on every pull request
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
| [MJPEG on our ROV, and why we use FFmpeg for it](https://docs.google.com/document/d/1814_NgCNUHJoMfy_53jX56oLAWMsYRoZREwSixIuZwM/edit) | Reading version of `docs/streaming/mjpeg-and-ffmpeg.md` (Nov 19 version) |
| [Streaming Deep-Dive: 2026–27 additions](https://docs.google.com/document/d/1LyPRCtvt5-wCSomRh4We0snjWo5Yv7CyVO2TjXJWTn8/edit) | Reading version of `docs/streaming/` |
| [SDLC Live Session Handbook](https://docs.google.com/document/d/1fNSU7e_k30IwDUwo2Okes1AsU7UCkOBIDUMoYps5qBU/edit) | Reading version of `docs/sdlc/` |
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

- Nothing goes to `main` without a pull request and one review (see [`docs/sdlc/github-workflow.md`](docs/sdlc/github-workflow.md)).
- Tag the version that goes into the water before every pool test: `git tag -a v0.x-pool-test`.
- Numbers beat opinions: put measurements in your PR.
