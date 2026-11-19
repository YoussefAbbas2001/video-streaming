#!/usr/bin/env bash
# Sends one live H.264 stream over UDP (MPEG-TS), the way an ROV computer would.
# Change ONE thing at a time (env variables) and watch monitor.py + the receiver.
#
#   ./sender.sh                                   # test pattern, 1280x720@30, 2 Mb/s, to 127.0.0.1:5600
#   DEST=192.168.2.1 ./sender.sh                  # send to the topside laptop
#   SOURCE=/dev/video0 ./sender.sh                # a real USB camera
#   RES=1920x1080 FPS=60 BITRATE=6M ./sender.sh   # the "bigger is better" experiment
#   PRESET=medium ./sender.sh                     # watch CPU and latency grow
#
# Variables: SOURCE (testsrc | /dev/videoN | file.mp4), RES, FPS, BITRATE, PRESET, GOP_S, DEST, PORT, DURATION (s, 0 = forever)
set -euo pipefail
FFMPEG=${FFMPEG:-ffmpeg}
SOURCE=${SOURCE:-testsrc}; RES=${RES:-1280x720}; FPS=${FPS:-30}; BITRATE=${BITRATE:-2M}
PRESET=${PRESET:-veryfast}; GOP_S=${GOP_S:-1}; DEST=${DEST:-127.0.0.1}; PORT=${PORT:-5600}; DURATION=${DURATION:-0}

case "$SOURCE" in
  testsrc)   IN=(-re -f lavfi -i "testsrc2=size=${RES}:rate=${FPS}") ;;
  /dev/video*) IN=(-f v4l2 -framerate "$FPS" -video_size "$RES" -i "$SOURCE") ;;
  *)         IN=(-re -stream_loop -1 -i "$SOURCE") ;;
esac
LIMIT=(); [[ "$DURATION" != "0" ]] && LIMIT=(-t "$DURATION")
GOP=$(( ${FPS%.*} * GOP_S ))

echo "sending $SOURCE → udp://$DEST:$PORT · $RES@$FPS · $BITRATE · preset $PRESET · GOP ${GOP_S}s"
exec "$FFMPEG" -hide_banner -loglevel warning -stats "${IN[@]}" "${LIMIT[@]}" \
  -vf "scale=${RES/x/:},format=yuv420p" -r "$FPS" \
  -c:v libx264 -preset "$PRESET" -tune zerolatency -b:v "$BITRATE" -maxrate "$BITRATE" -bufsize "$BITRATE" \
  -g "$GOP" -bf 0 -an -f mpegts "udp://$DEST:$PORT?pkt_size=1316"
