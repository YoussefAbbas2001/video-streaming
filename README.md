# M.I.A Robotics · ROV Video Streaming

Everything for our video-streaming session: slides, three recorded videos, runnable demos, a hands-on notebook, an encoding app, and the engineering-practice live session.

> A video stream is not just a camera feed. It is a real-time information pipeline with limited bandwidth, processing power and latency budget.

## Start here

| I am… | Go to |
|---|---|
| **Watching the videos** | [`videos/`](videos/): three videos, about 25 min |
| **Trying it myself** | [`encoding_lab/`](encoding_lab/) app → [`demos/`](demos/) → [`notebooks/`](notebooks/) |
| **Benchmarking the Pi 5 / Jetson / laptop** | run the Encoding Lab on that computer → **Benchmark**, **Latency budget** and **Live monitor** tabs |
| **Measuring our ROV** | [`docs/measuring-performance.md`](docs/measuring-performance.md) and `demos/02_pipeline/monitor.py` |
| **Deciding Pi 5 vs Jetson Nano** | [`docs/streaming-additions.md`](docs/streaming-additions.md) §4 |
| **Testing the GUI (everyone!)** | [`sdlc/bug-hunt-league.md`](sdlc/bug-hunt-league.md), then open an issue with the 🐞 Bug report form |
| **Contributing code** | [`sdlc/github-workflow.md`](sdlc/github-workflow.md) |
| **Presenting** | [`presentation/`](presentation/) + [`workshop/presenter_guide/`](workshop/presenter_guide/) + [`sdlc/live-session-plan.md`](sdlc/live-session-plan.md) |

## What's in the repo

```
├── presentation/   the deck (79 slides, speaker notes on every slide)
├── videos/         Arabic scripts for the 3 recorded videos + recording checklist
├── demos/          runnable demos for each video (latency clock, cost in EGP, bottleneck lab, encoding matrix…)
├── encoding_lab/   ROV Encoding Lab: Streamlit app to tune every encoder setting on real video
├── notebooks/      hands-on notebook: 11 experiments with interactive tuning panels
├── docs/           write-ups: compression economics, USB vs IP, Pi 5 vs Nano, heat, computer vision, measuring
├── sdlc/           live session: Quality × Efficiency, Bug Hunt League, GitHub workflow, postmortems
├── workshop/       the full two-session workshop (presenter guide, student materials, activities, UX pack)
├── build/          scripts that regenerate the deck and the notebook
└── .github/        bug and task forms, PR template, CI that runs the tests on every pull request
```

## Quick start

```bash
sudo apt install ffmpeg                      # macOS: brew install ffmpeg · Windows: winget install ffmpeg
pip install -r encoding_lab/requirements.txt
streamlit run encoding_lab/app.py            # the Encoding Lab, at http://localhost:8501
python3 demos/01_why_streaming/egypt_cost.py # what raw video would cost on a WE home line
```

## Documents (Google Docs)

| Document | For |
|---|---|
| [Video Scripts (Arabic)](https://docs.google.com/document/d/1SWHGTSIQwwm1V1WtW0lmQqg6DUTXLM_mvFM8sI3jAlc/edit) | Recording the three videos |
| [Streaming Deep-Dive: 2026–27 additions](https://docs.google.com/document/d/1LyPRCtvt5-wCSomRh4We0snjWo5Yv7CyVO2TjXJWTn8/edit) | Reading version of `docs/` |
| [SDLC Live Session Handbook](https://docs.google.com/document/d/1fNSU7e_k30IwDUwo2Okes1AsU7UCkOBIDUMoYps5qBU/edit) | Reading version of `sdlc/` |
| [Workshop Reader](https://docs.google.com/document/d/1vyha2504cYxIiiDhl5IKH1ydGZGvKrHlJblZICibaT0/edit) | The whole workshop at moderate detail |
| [Video Streaming Brief (2 pages)](https://docs.google.com/document/d/1hb-U9hiFSG3xVDgvLhOdzBjFPkTLvZAK1YtnlFWPguw/edit) | Two-page, two-column summary of video streaming |

The Markdown in this repo is the source; the Google Docs are for reading and printing. The docs are private until shared, so share them with the team from Drive.

## Big files on Drive

Git is for code and text. These live in Drive; add the links when they exist:

| Item | Why not in Git | Link |
|---|---|---|
| Recorded videos 1–3 | Hundreds of MB each | *add link* |
| Raw ROV footage for the demos | Large media | *add link* |
| Presenter-only `referee/` (testing-competition answer key) | Must stay secret from the team | *add link* |
| Notebook cache `notebooks/work/` (~400 MB) | Re-created by running the notebook | not needed |

Files over 50 MB trigger GitHub warnings, and files over 100 MB are rejected.

## Rules of the road

- Nothing goes to `main` without a pull request and one review (see [`sdlc/github-workflow.md`](sdlc/github-workflow.md)).
- Tag the version that goes into the water before every pool test: `git tag -a v0.x-pool-test`.
- Numbers beat opinions: put measurements in your PR.
