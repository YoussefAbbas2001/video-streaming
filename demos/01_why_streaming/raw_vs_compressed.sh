#!/usr/bin/env bash
# Demo: the same 10 seconds of video, raw vs compressed at 8 / 4 / 2 / 1 Mb/s.
# Usage: ./raw_vs_compressed.sh [input.mp4]     (without input: an FFmpeg test pattern with motion)
# Output: ./out/ with the files, and a size table printed to the terminal. Open the files side by side afterwards.
set -euo pipefail
cd "$(dirname "$0")"
FFMPEG=${FFMPEG:-ffmpeg}
OUT=out; mkdir -p "$OUT"
SECONDS_TO_USE=10
W=1920; H=1080; FPS=30

if [[ $# -ge 1 ]]; then
  SRC=(-ss 0 -t "$SECONDS_TO_USE" -i "$1")
else
  SRC=(-f lavfi -i "testsrc2=size=${W}x${H}:rate=${FPS}:duration=${SECONDS_TO_USE}")
fi

echo "1/5  raw YUV 4:2:0 (what the encoder receives)"
"$FFMPEG" -hide_banner -loglevel error -y "${SRC[@]}" -vf "scale=${W}:${H},fps=${FPS}" -pix_fmt yuv420p -f rawvideo "$OUT/raw_1080p30.yuv"

for MB in 8 4 2 1; do
  echo "     H.264 at ${MB} Mb/s (ultrafast, zerolatency, GOP 1 s, no B-frames)"
  "$FFMPEG" -hide_banner -loglevel error -y -f rawvideo -pix_fmt yuv420p -s "${W}x${H}" -r "$FPS" -i "$OUT/raw_1080p30.yuv" \
    -c:v libx264 -preset ultrafast -tune zerolatency -b:v "${MB}M" -maxrate "${MB}M" -bufsize "$((MB / 2 + 1))M" -g "$FPS" -bf 0 \
    -pix_fmt yuv420p -an "$OUT/h264_${MB}mbps.mp4"
done

echo
printf "%-24s %12s %14s\n" "file" "size" "vs raw"
RAW=$(stat -c %s "$OUT/raw_1080p30.yuv")
for f in "$OUT"/raw_1080p30.yuv "$OUT"/h264_*mbps.mp4; do
  S=$(stat -c %s "$f")
  printf "%-24s %10.1f MB %12.0f:1\n" "$(basename "$f")" "$(echo "$S/1000000" | bc -l)" "$(echo "$RAW/$S" | bc -l)"
done
echo
echo "Now play out/h264_8mbps.mp4 and out/h264_1mbps.mp4 side by side and look at fine detail and moving edges."
