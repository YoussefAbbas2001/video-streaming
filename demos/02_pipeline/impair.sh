#!/usr/bin/env bash
# Make the network worse on purpose (Linux, needs sudo). Run it on the SENDER side, on the interface the stream leaves through.
#
#   sudo ./impair.sh eth0 limit 3mbit      # bandwidth cap: the "tether is too thin" experiment
#   sudo ./impair.sh eth0 delay 150ms      # added one-way delay: the "operator lag" experiment
#   sudo ./impair.sh eth0 jitter 80ms      # 20 ms ± 80 ms random delay: frames arrive out of rhythm
#   sudo ./impair.sh eth0 loss 2%          # random packet loss: watch the picture break and heal at the next keyframe
#   sudo ./impair.sh eth0 show             # what is active now
#   sudo ./impair.sh eth0 clear            # back to normal — ALWAYS run this after the demo
#
# Testing on one laptop? Use the loopback interface "lo" with DEST=127.0.0.1 in sender.sh.
set -euo pipefail
IF=${1:?interface, e.g. eth0 or lo}; CMD=${2:?limit|delay|jitter|loss|show|clear}; VAL=${3:-}
command -v tc >/dev/null || { echo "tc not found: install it with  sudo apt install iproute2"; exit 1; }
tc qdisc del dev "$IF" root 2>/dev/null || true
case "$CMD" in
  limit)  tc qdisc add dev "$IF" root tbf rate "${VAL:?e.g. 3mbit}" burst 32kbit latency 50ms ;;
  delay)  tc qdisc add dev "$IF" root netem delay "${VAL:?e.g. 150ms}" ;;
  jitter) tc qdisc add dev "$IF" root netem delay 20ms "${VAL:?e.g. 80ms}" distribution normal ;;
  loss)   tc qdisc add dev "$IF" root netem loss "${VAL:?e.g. 2%}" ;;
  clear)  echo "cleared $IF" ;;
  show)   ;;
  *) echo "unknown command $CMD"; exit 1 ;;
esac
tc qdisc show dev "$IF"
