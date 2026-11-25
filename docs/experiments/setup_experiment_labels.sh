#!/usr/bin/env bash
# Creates (or updates) the labels for the ROV experiments (docs/experiments/ROV_Experiments.md):
# `experiment` on every result issue, `exp:E##` worth the experiment's points, and the bonus labels.
# experiment_board.py reads these labels to build the leaderboard.
# Needs the GitHub CLI, logged in:  gh auth login
#   bash docs/experiments/setup_experiment_labels.sh OWNER/REPO
# (The Bug Hunt League labels are created by docs/setup_github_labels.sh in the mia-software-practice repo.)
set -euo pipefail
REPO=${1:?usage: $0 OWNER/REPO}
label() { gh label create "$1" --repo "$REPO" --color "$2" --description "$3" --force; }

# ROV experiments homework (docs/experiments/ROV_Experiments.md)
label "experiment"       "0e8a16" "A posted experiment result"
label "exp:E0" "bfdadc" "30 pts · Know your ROV (inventory)"
label "exp:E1" "bfdadc" "15 pts · How late is the pilot? (glass-to-glass)"
label "exp:E2" "bfdadc" "30 pts · Where do the milliseconds go?"
label "exp:E3" "bfdadc" "30 pts · Hunt the frames the encoder hides"
label "exp:E4" "bfdadc" "15 pts · Camera switch stopwatch"
label "exp:E5" "bfdadc" "30 pts · The long dive (latency drift)"
label "exp:E6" "bfdadc" "15 pts · Tether truth"
label "exp:E7" "bfdadc" "15 pts · Bandwidth census"
label "exp:E8" "bfdadc" "50 pts · Keyframe pile-up"
label "exp:E9" "bfdadc" "30 pts · The MTU detective"
label "exp:E10" "bfdadc" "30 pts · Packet-loss torture"
label "exp:E11" "bfdadc" "30 pts · Jitter vs the buffer"
label "exp:E12" "bfdadc" "50 pts · The squeeze"
label "exp:E13" "bfdadc" "30 pts · Pull the plug"
label "exp:E14" "bfdadc" "15 pts · Does the UI tell the truth?"
label "exp:E15" "bfdadc" "15 pts · Recording vs power cut"
label "exp:E16" "bfdadc" "30 pts · The 30-minute soak"
label "exp:E17" "bfdadc" "30 pts · Power under thruster load"
label "exp:E18" "bfdadc" "15 pts · Your footage's bits-per-pixel"
label "exp:E19" "bfdadc" "50 pts · How many cameras can the ROV computer encode?"
label "exp:E20" "bfdadc" "15 pts · The resolution trap"
label "exp:E21" "bfdadc" "30 pts · USB bus limit"
label "exp:E22" "bfdadc" "15 pts · Lights vs backscatter (bucket of milk)"
label "exp:E23" "bfdadc" "30 pts · Camera settings under water"
label "exp:E24" "bfdadc" "30 pts · Eye test for the ROV"
label "exp:E25" "bfdadc" "50 pts · Pilot blind test"
label "exp:E26" "bfdadc" "50 pts · The LED race (telemetry vs video)"
label "bonus:prediction" "c2e0c6" "+5 · prediction within 20 %"
label "bonus:replicated" "c2e0c6" "+10 · reproduced by another pair"
label "bonus:bug"        "c2e0c6" "+20 · the experiment found a real defect"
label "bonus:chart"      "c2e0c6" "+10 · chart of the week"
echo "experiment labels ready on $REPO"
