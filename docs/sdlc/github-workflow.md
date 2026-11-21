# GitHub is a workflow, not a folder

## Why change anything?

Today our repos work like a shared drive: files go in, and that's it. Here is what that costs us:

| Question before a competition | Storage-only answer | Workflow answer |
|---|---|---|
| Which version worked in the last pool test? | "I think the one from Thursday…" | `git checkout v0.6-pool-test` |
| Why was this timeout changed to 500 ms? | Nobody remembers | The PR that changed it explains why and links the bug |
| Did anyone check this change? | Unknown | A review is required before it reaches `main` |
| Did the change break the tests? | We find out in the pool | CI ran the tests on the PR, and the check is red or green |
| What is everyone working on? | Ask in the chat | The Projects board |
| Which bugs are still open? | Scattered in chat messages | Issues with labels and owners |

All of these features are **free** on GitHub, for public and private repos.

## The four-week ladder (one habit per week)

| Week | Habit | Done when |
|---|---|---|
| **1** | **Issues + board.** Every bug and task becomes an issue (bugs through the Bug Hunt form). One Projects board for the team | No task lives only in the chat |
| **2** | **Pull requests + 1 review.** Nobody pushes to `main`. Make a branch, open a PR, get one approval, merge | Every change on `main` has a PR |
| **3** | **CI.** GitHub Actions runs the tests on every PR (`.github/workflows/ci.yml` is ready) | Red CI blocks the merge |
| **4** | **Tags + branch protection.** Tag every version that goes into the water. Protect `main` (require PR, review and CI) | `git tag` lists every pool test |

## The daily flow (copy-paste)

```bash
git switch main && git pull                      # start from the latest main
git switch -c fix/camera-switch-race              # one short branch per issue
# … change code, run it, test it …
git add -p                                        # review your own diff, chunk by chunk
git commit -m "fix: show the right camera after fast switching (#42)"
git push -u origin fix/camera-switch-race
gh pr create --fill                               # or use the GitHub website
```

Then:
1. Fill in the PR template.
2. Ask one reviewer.
3. Fix the comments.
4. Merge when CI is green.
5. Delete the branch.

Keep branches **short (≤ 1 week)** and PRs **small (≤ 300 changed lines)**: small PRs get reviewed in minutes, big ones get rubber-stamped.

**Commit messages:** `type: what changed (#issue)`, where the type is `feat`, `fix`, `test`, `docs`, `refactor` or `chore`. Writing `#42` links the commit to issue 42, and writing `Fixes #42` in the PR closes the issue when the PR merges.

## Before every pool test

```bash
git switch main && git pull
git tag -a v0.7-pool-test -m "Pool test 2026-12-12: 8 cams, Pi 5, new heat sink"
git push origin v0.7-pool-test
```

After the test, write the results in a GitHub Release for that tag: what worked, what broke, and measurements such as latency, temperature and dropped frames. Before the competition, that page becomes the team's memory.

## Branch protection settings (week 4)

Settings → Branches → Add rule for `main`:
- ☑ Require a pull request before merging, with 1 approval
- ☑ Require status checks to pass, and select the CI job
- ☑ Do not allow bypassing the above settings (yes, admins too)

## What goes where

| Put in Git | Put in Drive (and link from the README) |
|---|---|
| Code, scripts, configs, CAD exports you diff, Markdown docs, small images (< 1 MB) | Videos, raw footage, large datasets, big CAD/STEP files, competition photos, anything over about 50 MB |
| `.github/` templates and CI | Presenter-only material (e.g. the referee key for the testing competition) |

GitHub warns about files over 50 MB and blocks files over 100 MB. Big binaries also make every clone slow forever, even after you delete them.

## Common objections

- **"It slows us down."** For the first two weeks, a little. After that it is faster, because nobody debugs the same thing twice and nobody wonders which version worked.
- **"We're electrical, not software."** Firmware, test scripts, wiring tables in Markdown and calibration files all benefit from history and review just as much.
- **"Reviews are awkward."** Review the code, not the person. Ask questions ("what happens if the camera disconnects here?") instead of giving verdicts.

## One-time setup

```bash
gh auth login                                   # once per laptop
./sdlc/setup_github_labels.sh OWNER/REPO        # creates the Bug Hunt League labels
```

Then create the Projects board in the GitHub web UI (Projects → New project → Board) with the columns Reported · Confirmed · Fixing · Verify · Closed.
