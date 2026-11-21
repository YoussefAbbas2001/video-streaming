# Workshop package: Engineering Better ROV Systems

The full two-session workshop:
- **Session 1, video engineering:** bandwidth, encoding, hardware, latency and multi-camera strategy.
- **Session 2, engineering practice and UX:** requirements, testing, code review, Git, team organisation and UX for ROV pilots.

The guiding idea: *students leave asking "how would we measure that?" before "how do we fix that?"*

> **Paths inside this folder** (e.g. `student_materials/…` in the presenter script) are relative to `workshop/`. Repo-level items are written with `../` (e.g. `../encoding_lab/`).

## What's here

```
workshop/
├── presenter_guide/
│   ├── Workshop_Design.md                 audience, objectives, agenda, equipment, KNOWN / UNKNOWN about the ROV
│   └── Presenter_Script.md                block-by-block script for all 82 slides: what to say, questions, misconceptions, timing
├── student_materials/
│   ├── Video_Streaming_Cheat_Sheet.md     formulas, vocabulary, FFmpeg/GStreamer/Linux commands, review checklist
│   ├── ROV_System_Diagnostic_Checklist.md measure-your-own-ROV checklist (homework after session 1)
│   ├── Testing_Competition_Guide.md       "Break the Other Team's Software!" rules, scoring, templates, scenarios
│   └── Proposed_Architecture_Options.md   5 architecture options with trade-offs + decision-log template
├── workshop_activities/
│   ├── Activity_Instructions.md           Activities 1, 2, 3, 5 with materials and answer keys
│   ├── Post_Workshop_Challenge.md         6-week challenge: requirements, constraints, DoD, metrics, demo criteria
│   └── testing_competition_code/          small Python module (spec + code with seeded defects + starter tests)
├── ux_materials/
│   ├── UX_Pilot_Experience_Pack.md        persona, journey, wireframes, usability script, activity, rubric, user stories
│   └── pilot_dashboard_wireframe.svg      printable before/after dashboard wireframe (A3)
└── resources/
    └── References.md                      sources for every hardware claim + curated learning resources
```

Related, at the repo level:
- the decks: `../presentation/` (MIA_Video_Streaming.pptx, MIA_Software_Dev_Cycle.pptx), click-by-click builds and speaker notes;
- the **Encoding Lab** app, used for every live demo: `../encoding_lab/`;
- the video series: `../videos/`;
- the write-ups: `../docs/streaming/` and the SDLC live session: `../docs/sdlc/`;
- the original notebook (optional, not used in the session): `../encoding_lab/notebooks/`.

**Presenter-only (not in this repo):** the testing-competition referee key and the seeded-defect proof tests live in the presenter's Drive folder (see the main README), so the team can't read the answers before the competition.

## Recommended session sequence

Two half-day sessions (≈ 3 h 50 min each, incl. breaks). Full timing is in `presenter_guide/Workshop_Design.md` and in `Presenter_Script.md` (Appendix B).

| Session | Content | Activities |
|---|---|---|
| **1 · Video engineering** | Why video matters → architecture and unknowns → bandwidth → how encoding works → codecs, rate control, GOP and loss → quality metrics → Jetson Nano vs Raspberry Pi 5 → heat and reliability → protocols and latency → multi-camera and computer vision | 1 Estimate the Bandwidth · 3 Compression Challenge · 2 Diagnose the ROV · homework: Diagnostic Checklist |
| **2 · Engineering practice and UX** | Quality × Efficiency → SDLC → requirements, DoR/DoD → testing and the Bug Hunt League → code review, GitHub workflow, board, metrics → UX for pilots → final challenge | 4 Break the Other Team's Software · 6 Design the Perfect Pilot Experience · 5 Architecture Challenge |

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

## Running the testing competition code

```bash
cd workshop_activities/testing_competition_code
pip install pytest
python -m pytest -q          # 7 starter tests pass, which proves nothing
```

## Important caveats

- **We do not yet know** the team's exact cameras, board, tether speed or streaming software. The material labels every assumption and gives the measurement that resolves it.
- Hardware facts are cited in `resources/References.md` and `../docs/streaming-additions.md`.
- Latency budgets in the deck are **estimates** (labelled), except the measured x264 encoder hold.
- Safety-related UX guidance describes principles. The actual safety behaviour must be designed with the vehicle's control architecture and the competition rules.
