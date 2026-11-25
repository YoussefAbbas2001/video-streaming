# Workshop, session 1: Video Engineering

Session 1 of *Engineering Better ROV Systems*: bandwidth, encoding, hardware, latency and multi-camera strategy.

Session 2 (requirements, testing, code review, Git, team organisation and UX for ROV pilots) is in the [mia-software-practice repo](https://github.com/YoussefAbbas2001/mia-software-practice/tree/HEAD/workshop).

The guiding idea: *students leave asking "how would we measure that?" before "how do we fix that?"*

> **Paths inside this folder** (e.g. `student_materials/…` in the presenter script) are relative to `workshop/`. Repo-level items are written with `../` (e.g. `../encoding_lab/`).

## What's here

```
workshop/
├── presenter_guide/
│   ├── Workshop_Design.md                 audience, objectives, agenda, equipment, KNOWN / UNKNOWN about the ROV
│   └── Presenter_Script.md                block-by-block script for session 1: what to say, questions, misconceptions, timing
├── student_materials/
│   ├── Video_Streaming_Cheat_Sheet.md     formulas, vocabulary, FFmpeg/GStreamer/Linux commands
│   └── Proposed_Architecture_Options.md   5 architecture options with trade-offs + decision-log template
├── workshop_activities/
│   └── Activity_Instructions.md           Activities 1, 2, 3, 5 with materials and answer keys
└── resources/
    └── References.md                      sources for every hardware claim + video, networking and ROV resources
```

Related, at the repo level:
- the deck: `../presentation/MIA_Video_Streaming.pptx`, click-by-click builds and speaker notes;
- the **Encoding Lab** app, used for every live demo: `../encoding_lab/`;
- the video series: `../videos/`;
- the write-ups: `../docs/streaming/`, the experiments `../docs/experiments/` and the debug checklist `../docs/debug/`;
- the original notebook (optional, not used in the session): `../encoding_lab/notebooks/`.

## Recommended session sequence

Two half-day sessions (≈ 3 h 50 min each, incl. breaks). Full timing for session 1 is in `presenter_guide/Workshop_Design.md` and in `Presenter_Script.md` (Appendix B).

| Session | Content | Activities |
|---|---|---|
| **1 · Video engineering** | Why video matters → architecture and unknowns → bandwidth → how encoding works → codecs, rate control, GOP and loss → quality metrics → Jetson Nano vs Raspberry Pi 5 → heat and reliability → protocols and latency → multi-camera and computer vision | 1 Estimate the Bandwidth · 3 Compression Challenge · 2 Diagnose the ROV · homework: the [ROV experiments](../docs/experiments/ROV_Experiments.md), run by team leaders with the [Leader's Recipe](../docs/experiments/Leader_Guide.md) · tool: the [debug checklist](../docs/debug/ROV_Debug_Checklist.md) |
| **2 · Engineering practice and UX** | in the [mia-software-practice repo](https://github.com/YoussefAbbas2001/mia-software-practice) | 4 Break the Other Team's Software · 6 Design the Perfect Pilot Experience · 5 Architecture Challenge (its instructions stay here, in `workshop_activities/Activity_Instructions.md`) |

**Before session 1:**
- Send the questionnaire in `Workshop_Design.md` §6.5 to the team lead.
- Run the Encoding Lab once (one encode, one benchmark, one Live camera start).
- Print the handouts (the list is in `Presenter_Script.md`).

## Running the Encoding Lab

Requirements: **Python 3.10+** and **FFmpeg 5+** with `libx264` (`libx265`, `libsvtav1` optional; VMAF only if FFmpeg has `libvmaf`).

```bash
sudo apt install ffmpeg                       # macOS: brew install ffmpeg · Windows: winget install ffmpeg
pip install -r ../encoding_lab/requirements.txt
streamlit run ../encoding_lab/app.py          # http://localhost:8501
```

- **Use your own footage:** sidebar → *Upload your own video*. Without it, a synthetic underwater clip is generated.
- **Live camera tab:** uses the laptop's camera; Windows and macOS ask for permission the first time.
- Results are cached in `encoding_lab/.lab_work/` (safe to delete). The presenter script's notebook-experiment → Lab-tab table is at the top of `Presenter_Script.md`.

## Important caveats

- **We do not yet know** the team's exact cameras, board, tether speed or streaming software. The material labels every assumption and gives the measurement that resolves it.
- Hardware facts are cited in `resources/References.md` and `../docs/streaming/hardware-and-encoders.md`.
- Latency budgets in the deck are **estimates** (labelled), except the measured x264 encoder hold.
