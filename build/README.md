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

(These commands were run on 21 Nov 2026 against the decks as they were that day. To add more slides later, write a new generator like `new_slides_nov2026.js` and insert only those.)

| Script | What it does |
|---|---|
| `new_slides_nov2026.js` | The November 2026 slides: chroma subsampling, intra and inter prediction, transform + quantization, entropy coding + loop filters, containers, Netflix-scale Fermi estimate, what the big streamers do, the MJPEG resolution trap, the weekly knowledge exchange. Numbers are measured by us or sourced in the speaker notes. |
| `insert_slides.py` | Copies slides (with their pictures and speaker notes) into a hand-edited deck after given slide numbers, mapped onto the target's own layout of the same name, so they take its footer, logo and theme. Touches nothing else. |
| `add_click_builds.py` | Click-by-click Fade builds: each card, chart or row appears on its own click. `--only` limits it to the slides you name, so hand-made animations elsewhere are kept. |
| `build_deck.js`, `deck_part_*.js`, `deck_helpers.js`, `write_theme.js` | Generate the original single combined deck (before it was split and hand-edited). Kept as the source of the shared style; do not use them to overwrite `presentation/`. |
| `make_notebook.py`, `nb_*.py`, `run_nb.py` | Generate and run the original notebook (no longer used in the session). |
