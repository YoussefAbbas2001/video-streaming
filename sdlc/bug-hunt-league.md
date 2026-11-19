# The Bug Hunt League

**Why:** about 20 people are on the team and only 3–4 write the GUI. Developers have a narrow view: they test the paths they already imagined. The other 16 think like pilots, electrical engineers and mechanical designers, which makes them the best testers we have. The League turns testing into a game with visible credit.

## Points

| Severity | Examples | Points |
|---|---|---|
| **Critical** | Stream freezes or dies; GUI crash; a wrong or unsafe command reaches the thrusters or gripper; the ROV keeps moving after the controller is released | **10** |
| **Major** | A feature doesn't work; the wrong camera is shown; settings or data are lost; the UI shows "connected" when it isn't | **5** |
| **Minor** | Works with a workaround; a glitch on one screen; slow but usable | **2** |
| **UX** | Confusing label, missing feedback, hard to find under stress, too small to read with gloves or at a distance | **1** |
| Bonus: evidence | A screen recording, or a failing automated test that reproduces it | **+2** |
| Bonus: regression | It's back: a bug that was already marked fixed | **+3** |
| Bonus: fix | A non-GUI member submits the PR that fixes it (reviewed by a developer) | **+5** |

GUI developers confirm the severity during triage. When in doubt, the higher severity wins if it touches safety.

## Rules

1. **Reproducible or it doesn't count.** Steps, expected result, actual result and the version or commit (the bug form asks for all of them).
2. **First reporter wins duplicates.** Search the open issues before filing.
3. **No points on your own code.** Developers can hunt, but only in code they didn't write.
4. **The hunter verifies the fix.** A bug is closed only when the person who found it confirms the fix on the real setup. This also teaches hunters how the code works.
5. **Be kind in reports.** Describe the system's behaviour, never the person who wrote it.
6. **Safety bugs go to the team lead immediately**, as well as on the board.

## The board (GitHub Projects)

| Column | Meaning | Who moves it |
|---|---|---|
| Reported | Filed through the bug form | Hunter |
| Confirmed | Reproduced by a developer; severity and points set | Developer (triage) |
| Fixing | Someone is assigned; a branch or PR exists | Developer |
| Verify | Fix merged; waiting for the hunter | Developer |
| Closed | Hunter confirmed it on the real setup; points counted | Hunter |

Labels (created by `setup_github_labels.sh`): `bug`, `sev:critical`, `sev:major`, `sev:minor`, `sev:ux`, `bonus:evidence`, `bonus:fix`, `regression`, `needs-repro`, `area:gui`, `area:streaming`, `area:control`, `area:electrical`, `good first fix`. During triage the developer adds the severity label (and any bonus label); `leaderboard.py` counts points from these labels.

## Rhythm

- **Weekly:** leaderboard and "bug of the week" in the team meeting (5 minutes).
- **Before every pool test:** a 45-minute **Bug Bash**. Everybody hunts on the build that will go in the water, then we tag it.
- **Monthly:** the **Bug Hunter of the Month** gets the badge and picks the team snack.
- **Season:** the champion **picks one feature** for the next sprint, which earns real influence on the product.

## How to write a bug that scores

```
Title:     Camera 3 shows camera 1's picture after switching twice quickly
Version:   main @ 4f2a9c1 (or tag v0.6-pool-test)
Steps:     1. Start the GUI with all 8 cameras  2. Click Cam 3, then Cam 1, then Cam 3 within 1 s
Expected:  Camera 3's picture
Actual:    Camera 1's picture with Camera 3's label (stays until the GUI restarts)
Evidence:  screen recording attached
Severity:  Major (a wrong camera can mislead the pilot)
```

## Keeping score

The simplest way: count points from the closed issues' severity labels. `sdlc/leaderboard.py` does this from the GitHub CLI:

```bash
gh issue list --state closed --label bug --limit 500 --json number,title,labels,author,closedAt > closed_bugs.json
python3 sdlc/leaderboard.py closed_bugs.json --since 2026-12-01
```
