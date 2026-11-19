# Live session: Engineering Practice (≈ 75 minutes)

**Audience:** the whole electrical/robotics team (≈ 20 people), not only the 3–4 GUI developers.
**Goal:** leave with three habits running: a Bug Hunt League, GitHub used as a workflow, and blameless postmortems.
**Slides:** 49–64 of `presentation/MIA_Robotics_Workshop.pptx` (new: 50, 58, 62).

## The idea behind the session

> **Work force = Quality × Efficiency**

It is a product, not a sum: if either factor is zero, the team's output is zero.

- **Fast but broken = 0.** The stream freezes in the pool, the GUI crashes during the demo run.
- **Perfect but late = 0.** Flawless code that is ready the week after the competition.

Each part of the session gives one lever:

| Lever | Improves | Habit we start today |
|---|---|---|
| Everybody tests | Quality | Bug Hunt League (`bug-hunt-league.md`) |
| Work in the open | Efficiency and quality | GitHub workflow (`github-workflow.md`) |
| Learn from failures | Quality | Blameless postmortem (`postmortem-template.md`), starting with the 2023 heat failure |

## Agenda

| Time | Block | Slides | What happens |
|---|---|---|---|
| 0:00 | Why process? | 49–50 | The integration-cliff story. Then **Quality × Efficiency**: ask everyone to write which factor is weaker in our team today (anonymous sticky notes). Read them out |
| 0:10 | Lifecycle in 5 minutes | 51–54 | The SDLC loop with ROV examples; Definition of Done includes "tested in the pool" |
| 0:15 | Testing mindset | 55–56 | "A test that cannot fail is not a test." Developers test the paths they imagined; others find the rest |
| 0:20 | **Bug Hunt League kick-off** | 58 | Explain points and rules. Show the board and the bug form on GitHub |
| 0:25 | **Live Bug Bash (25 min)** | — | Teams of 3, each with at least one non-GUI member. Target: the current GUI build (or the `testing_competition_code` module if the GUI isn't runnable). Every bug must be filed through the GitHub form. Leaderboard on the projector |
| 0:50 | Triage together | — | GUI developers confirm or reject each bug live. Points awarded. Announce the first weekly leader |
| 0:55 | **GitHub is a workflow** | 61–62 | Live demo: issue → branch → small change → PR → review → CI turns green → merge → tag. Show the four-week ladder; agree on week 1 today |
| 1:05 | **Postmortem: 2023 heat failure** | 37 | Fill in `postmortem-template.md` with the people who were there: timeline, causes, what we change. No names, only systems |
| 1:15 | Close | 63–64 | Commitments: who sets up the board (today), Bug Bash before the next pool test, postmortem published in the repo |

## Before the session (presenter checklist)

- [ ] Repo on GitHub with the `.github/` templates from this folder (bug form, PR template, CI)
- [ ] Labels created: run `sdlc/setup_github_labels.sh` (needs the GitHub CLI `gh`, logged in)
- [ ] A GitHub Project board with columns Reported · Confirmed · Fixing · Verify · Closed
- [ ] A runnable GUI build on 6–7 laptops (or the testing-competition module as a fallback)
- [ ] A leaderboard: a pinned issue or a slide you update live
- [ ] Prizes. Cheap but visible: the Bug Hunter badge on the team chat, choosing the next team snack, picking a feature for the next sprint
- [ ] Ask in advance who remembers the 2023 trial details (board, enclosure, temperature, minutes into the run)

## After the session

- Weekly: 5 minutes in the team meeting for the leaderboard and the "bug of the week"
- Before every pool test: a 45-minute Bug Bash, then tag the version that goes into the water
- Monthly: Bug Hunter award, plus a quick look at the GitHub ladder (which step are we on?)
