#!/usr/bin/env bash
# Creates (or updates) the labels used by the Bug Hunt League and the GitHub workflow.
# Needs the GitHub CLI, logged in:  gh auth login
#   ./setup_github_labels.sh OWNER/REPO
set -euo pipefail
REPO=${1:?usage: $0 OWNER/REPO}
label() { gh label create "$1" --repo "$REPO" --color "$2" --description "$3" --force; }
label "bug"              "d73a4a" "Something doesn't work"
label "sev:critical"     "b60205" "10 pts · crash, frozen stream, unsafe command"
label "sev:major"        "e99695" "5 pts · feature broken, wrong camera, data lost"
label "sev:minor"        "fbca04" "2 pts · works with a workaround"
label "sev:ux"           "c5def5" "1 pt · confusing, missing feedback, hard to use under stress"
label "bonus:evidence"   "0e8a16" "+2 · video or failing test attached"
label "bonus:fix"        "0e8a16" "+5 · fixed by a non-GUI member"
label "regression"       "5319e7" "+3 · a fixed bug came back"
label "needs-repro"      "ededed" "Can't reproduce yet: add steps or a video"
label "area:gui"         "1d76db" "Pilot GUI / web app"
label "area:streaming"   "1d76db" "Cameras, encoding, network"
label "area:control"     "1d76db" "Control, thrusters, gripper"
label "area:electrical"  "1d76db" "Power, wiring, sensors"
label "good first fix"   "7057ff" "Small and well described: good for a first PR"
label "task"             "a2eeef" "Planned work"
echo "labels ready on $REPO"
