#!/usr/bin/env bash
# MJPEG streaming with FFmpeg only: the jobs mjpg-streamer / mjpeg-streamer do, and more.
# Reading: docs/mjpeg-and-ffmpeg.md
#
#   ./mjpeg_ffmpeg.sh http                        # browser stream  -> http://<rov-ip>:8080/aux1.mjpg  (restarts after each viewer)
#   ./mjpeg_ffmpeg.sh rtp                         # RTP/UDP to DEST:PORT, writes aux1.sdp for the receiver
#   ./mjpeg_ffmpeg.sh tee                         # RTP + recording (.avi) + always-fresh latest.jpg, one capture, no re-encode
#   ./mjpeg_ffmpeg.sh small                       # re-encode: 640x360 + timestamp overlay, RTP (for the GUI tile)
#   SOURCE=/dev/video0 RES=1280x720 FPS=30 ./mjpeg_ffmpeg.sh tee
#
# Receivers (topside):
#   browser   <img src="http://192.168.1.10:8080/aux1.mjpg">
#   RTP       ffplay -protocol_whitelist file,udp,rtp -fflags nobuffer -flags low_delay aux1.sdp
#
# Variables: SOURCE (testsrc | /dev/videoN), RES, FPS, Q (JPEG quality 2..31, lower = better; used when encoding),
#            DEST, PORT, HTTP_PORT, NAME, DURATION (s, 0 = forever)
set -euo pipefail
FFMPEG=${FFMPEG:-ffmpeg}
MODE=${1:-http}
SOURCE=${SOURCE:-testsrc}; RES=${RES:-1280x720}; FPS=${FPS:-30}; Q=${Q:-5}
DEST=${DEST:-127.0.0.1}; PORT=${PORT:-5600}; HTTP_PORT=${HTTP_PORT:-8080}; NAME=${NAME:-aux1}; DURATION=${DURATION:-0}

LIMIT=(); [[ "$DURATION" != "0" ]] && LIMIT=(-t "$DURATION")
case "$SOURCE" in
  # A real UVC camera: ask for its own MJPEG, then copy it (no CPU encode).
  /dev/video*) IN=(-f v4l2 -input_format mjpeg -video_size "$RES" -framerate "$FPS" -i "$SOURCE"); CODEC=(-c:v copy) ;;
  # Test pattern: FFmpeg has to make the JPEGs. -huffman default keeps them RTP-legal (RFC 2435).
  testsrc)     IN=(-re -f lavfi -i "testsrc2=size=${RES}:rate=${FPS}"); CODEC=(-c:v mjpeg -q:v "$Q" -huffman default -pix_fmt yuvj420p) ;;
  *) echo "SOURCE must be testsrc or /dev/videoN" >&2; exit 1 ;;
esac
RUN=("$FFMPEG" -hide_banner -loglevel "${LOGLEVEL:-error}" "${IN[@]}" "${LIMIT[@]}" -map 0:v -an)

case "$MODE" in
  http)
    echo "serving http://0.0.0.0:${HTTP_PORT}/${NAME}.mjpg  (one viewer at a time; Ctrl+C twice to stop)"
    # FFmpeg's HTTP server takes one viewer and exits when it leaves, so loop it.
    while true; do
      "${RUN[@]}" "${CODEC[@]}" -f mpjpeg -content_type "multipart/x-mixed-replace;boundary=ffmpeg" \
        -listen 1 "http://0.0.0.0:${HTTP_PORT}/${NAME}.mjpg" || true   # an "Error writing trailer: Broken pipe" when the viewer leaves is normal
      [[ "$DURATION" != "0" ]] && break
      sleep 0.5
    done ;;
  rtp)
    echo "RTP/JPEG -> rtp://${DEST}:${PORT}  (SDP: ${NAME}.sdp)"
    exec "${RUN[@]}" "${CODEC[@]}" -f rtp -sdp_file "${NAME}.sdp" "rtp://${DEST}:${PORT}" ;;
  tee)
    REC="${NAME}_$(date +%Y%m%d_%H%M%S).avi"
    echo "RTP -> rtp://${DEST}:${PORT} · recording ${REC} · latest frame ${NAME}_latest.jpg"
    exec "${RUN[@]}" "${CODEC[@]}" -f tee \
      "[f=rtp]rtp://${DEST}:${PORT}|[f=avi]${REC}|[f=image2:update=1]${NAME}_latest.jpg" ;;
  small)
    # Re-encode: smaller picture + clock overlay for the GUI tile (about 13% of one core for 720p in -> 360p out).
    echo "640x360 + timestamp -> rtp://${DEST}:${PORT}  (SDP: ${NAME}_small.sdp)"
    exec "${RUN[@]}" -vf "scale=640:-2,drawtext=text='%{localtime}':x=10:y=10:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.5" \
      -c:v mjpeg -q:v 7 -huffman default -pix_fmt yuvj420p -f rtp -sdp_file "${NAME}_small.sdp" "rtp://${DEST}:${PORT}" ;;
  *) echo "mode must be http | rtp | tee | small" >&2; exit 1 ;;
esac
