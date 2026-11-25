# build/

The two decks in `presentation/` are **edited by hand** in PowerPoint. Never regenerate them wholesale, or the edits are lost. New slides are generated separately and **inserted**:

```bash
node build/new_slides_nov2026.js            # → out/new_slides_nov2026.pptx (10 slides, same layouts and style)
python3 build/insert_slides.py out/new_slides_nov2026.pptx presentation/MIA_Video_Streaming.pptx \
    --place 1:21 --place 2:22 --place 3:22 --place 4:22 --place 5:22 --place 7:24 --place 8:24 --place 6:25 --place 9:26
python3 build/insert_slides.py out/new_slides_nov2026.pptx presentation/MIA_Software_Dev_Cycle.pptx --place 10:19
python3 build/add_click_builds.py presentation/MIA_Video_Streaming.pptx --only 22,24,25,26,27,30,31,33,35   # numbers printed by insert_slides.py
python3 build/add_click_builds.py presentation/MIA_Software_Dev_Cycle.pptx --only 20
```

Video-diagnostics slides (24 Nov 2026): pictures and text come from one catalog, shared with `docs/streaming/measure-and-diagnose.md`:

```bash
python3 build/make_diagnostic_images.py     # 41 pictures + measurements.json in docs/streaming/img/diagnostics/ (≈ 2 min)
python3 build/diagnostics_catalog.py        # → docs/streaming/measure-and-diagnose.md + out/diagnostics.json
node build/new_slides_diagnostics.js        # → out/new_slides_diagnostics.pptx (6 talk slides + 17 appendix slides)
python3 build/insert_slides.py out/new_slides_diagnostics.pptx presentation/MIA_Video_Streaming.pptx \
    $(for i in 1 2 3 4 5 6; do echo --place $i:53; done) $(for i in $(seq 7 23); do echo --place $i:56; done)
python3 build/add_click_builds.py presentation/MIA_Video_Streaming.pptx --only 54,55,56,57,58,59
```

ROV experiments section (25 Nov 2026): 7 slides that replaced the old "Practice: measure your own ROV" slide. The experiment list, points and badges are read from the mission map in `docs/experiments/ROV_Experiments.md`, so the slides and the doc cannot disagree:

```bash
python3 build/make_experiment_images.py     # docs/experiments/img/g2g-photo.jpg + eye-test.jpg (real x264 encodes)
node build/new_slides_experiments.js        # → out/new_slides_experiments.pptx (7 slides)
python3 build/insert_slides.py out/new_slides_experiments.pptx presentation/MIA_Video_Streaming.pptx \
    $(for i in 1 2 3 4 5 6 7; do echo --place $i:62; done)
# then the old slide 62 was removed from <p:sldIdLst> and the pptx skill's clean.py run
python3 build/add_click_builds.py presentation/MIA_Video_Streaming.pptx --only 62,63,64,65,66,67,68
```

Debug checklist and leaders slides (25 Nov 2026): two slides; the check counts are read from `docs/debug/ROV_Debug_Checklist.md`. The insert positions refer to the deck before the insert (after Activity 2, and after the experiments plan):

```bash
node build/new_slides_debug_leaders.js        # → out/new_slides_debug_leaders.pptx (2 slides)
python3 build/insert_slides.py out/new_slides_debug_leaders.pptx presentation/MIA_Video_Streaming.pptx --place 1:60 --place 2:68
python3 build/add_click_builds.py presentation/MIA_Video_Streaming.pptx --only 61,70
```

Note: the generated regions of `docs/streaming/measure-and-diagnose.md` (between `<!-- gen:NAME -->` markers) come from `diagnostics_catalog.py`; edit the catalog, not those regions.

(These commands were run on 21 Nov 2026 against the decks as they were that day. To add more slides later, write a new generator like `new_slides_nov2026.js` and insert only those.)

| Script | What it does |
|---|---|
| `new_slides_nov2026.js` | The November 2026 slides: chroma subsampling, intra and inter prediction, transform + quantization, entropy coding + loop filters, containers, Netflix-scale Fermi estimate, what the big streamers do, the MJPEG resolution trap, the weekly knowledge exchange. Numbers are measured by us or sourced in the speaker notes. |
| `make_diagnostic_images.py`, `diagnostics_catalog.py`, `new_slides_diagnostics.js` | The video-diagnostics field guide: pictures (real bad encodes, real damaged streams, simulated camera/display effects, charts), the catalog of 45 problems, and the slides. |
| `make_experiment_images.py`, `new_slides_experiments.js` | The homework experiments: the glass-to-glass photo and the eye-test encodes, and the 7 experiment slides built from the doc's mission map. |
| `new_slides_debug_leaders.js` | The *When it breaks: the debug checklist* slide and the *Leaders: one 90-minute session a week* slide. |
| `fix_shape_ids.py` | Gives every shape on a slide a unique id. pptxgenjs can give a table the same id as a text box; LibreOffice accepts that but PowerPoint asks to repair the file. `insert_slides.py` runs it automatically; re-run `add_click_builds.py --only` on the slides it lists. |
| `insert_slides.py` | Copies slides (with their pictures and speaker notes) into a hand-edited deck after given slide numbers, mapped onto the target's own layout of the same name, so they take its footer, logo and theme. Touches nothing else. |
| `add_click_builds.py` | Click-by-click Fade builds: each card, chart or row appears on its own click. `--only` limits it to the slides you name, so hand-made animations elsewhere are kept. |
| `build_deck.js`, `deck_part_*.js`, `deck_helpers.js`, `write_theme.js` | Generate the original single combined deck (before it was split and hand-edited). Kept as the source of the shared style; do not use them to overwrite `presentation/`. |
| `make_notebook.py`, `nb_*.py`, `run_nb.py` | Generate and run the original notebook (no longer used in the session). |
