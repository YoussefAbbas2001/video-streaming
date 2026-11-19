#!/usr/bin/env bash
# Shows the frame-type pattern (I / P / B) and frame sizes of a video, so the GOP becomes visible.
#   ./gop_view.sh                 # makes two short test encodes: default x264 vs low-latency, then shows both
#   ./gop_view.sh myvideo.mp4     # any file
set -euo pipefail
cd "$(dirname "$0")"
FFMPEG=${FFMPEG:-ffmpeg}; FFPROBE=${FFPROBE:-ffprobe}
show() {
  echo "== $1"
  "$FFPROBE" -v error -select_streams v:0 -show_entries frame=pict_type,pkt_size -of csv=p=0 "$1" | head -90 | awk -F, '
    { types = types $2; size[NR] = $1; t[NR] = $2 }
    END {
      print "pattern: " types
      for (i = 1; i <= NR && i <= 32; i++) { bar = ""; n = int(size[i] / 1500); for (j = 0; j < n && j < 60; j++) bar = bar "#"; printf "%3d %s %7d B %s\n", i, t[i], size[i], bar }
    }'
  echo
}
if [[ $# -ge 1 ]]; then show "$1"; exit 0; fi
mkdir -p out
"$FFMPEG" -hide_banner -loglevel error -y -f lavfi -i "testsrc2=size=1280x720:rate=30:duration=3" -c:v libx264 -preset medium -g 30 -pix_fmt yuv420p out/gop_default.mp4
"$FFMPEG" -hide_banner -loglevel error -y -f lavfi -i "testsrc2=size=1280x720:rate=30:duration=3" -c:v libx264 -preset ultrafast -tune zerolatency -g 30 -bf 0 -pix_fmt yuv420p out/gop_lowlatency.mp4
show out/gop_default.mp4
show out/gop_lowlatency.mp4
echo "Default x264 uses B-frames (needs future frames → extra delay). Low-latency: only I and P. The I-frame is the big spike."
