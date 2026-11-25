# M.I.A Robotics · ROV Video Streaming

Everything for video streaming on the ROV: the slide deck, three recorded videos, the **ROV Encoding Lab** app we use live in the session, the write-ups, the ROV experiments and the debug checklist.

Software practice (SDLC, testing, the Bug Hunt League, code review, the GitHub workflow, the knowledge exchange and pilot UX) lives in its own repo: **[mia-software-practice](https://github.com/YoussefAbbas2001/mia-software-practice)**.

> A video stream is not just a camera feed. It is a real-time information pipeline with limited bandwidth, processing power and latency budget.

## Start here

| I am… | Go to |
|---|---|
| **In the session** | Run the [Encoding Lab](encoding_lab/) (below). Every experiment in the deck is done there, live. |
| **Watching the videos** | [`videos/`](videos/): three videos, about 25 min |
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
├── docs/
│   ├── streaming/  measure and diagnose (45-problem field guide), hardware and encoders, codecs and FFmpeg
│   ├── experiments/ the ROV experiments: member handbook, leader's recipe, ms clock, leaderboard
│   └── debug/      the debug checklist and rov_healthcheck.sh
├── videos/         Arabic scripts for the 3 recorded videos + recording checklist
├── workshop/       session 1 of the workshop (presenter guide, student materials, activities)
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
