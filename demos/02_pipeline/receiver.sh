#!/usr/bin/env bash
# Receives the stream from sender.sh and shows it with as little buffering as possible.
#   ./receiver.sh            # window (ffplay, low-latency flags)
#   ./receiver.sh --stats    # no window: prints fps / bitrate / dropped frames (works over SSH)
#   PORT=5601 ./receiver.sh
# Compare with a default player to *see* what receiver buffering costs: in ffplay's status line, vq= is the video
# waiting in the queue. Measured with a 2 Mb/s stream: plain ffplay ≈ 1.2 MB queued (seconds of delay); these flags ≈ 23 kB.
#   ./receiver.sh --plain   # ffplay with default buffering, for the comparison
set -euo pipefail
PORT=${PORT:-5600}
URL="udp://@:${PORT}?fifo_size=1000000&overrun_nonfatal=1"
if [[ "${1:-}" == "--plain" ]]; then
  exec "${FFPLAY:-ffplay}" -hide_banner -window_title "ROV stream :$PORT (default buffering)" "$URL"
elif [[ "${1:-}" == "--stats" ]]; then
  # The ffmpeg CLI needs a bigger probe window to find the H.264 headers when it joins a stream that is already
  # running, and must not use -fflags nobuffer (it then decodes nothing). ffplay below is fine with both.
  exec "${FFMPEG:-ffmpeg}" -hide_banner -probesize 5000000 -analyzeduration 3000000 -flags low_delay -i "$URL" \
    -map 0:v -vsync 0 -f null -
else
  exec "${FFPLAY:-ffplay}" -hide_banner -fflags nobuffer -flags low_delay -framedrop -probesize 32 -analyzeduration 0 \
    -sync ext -window_title "ROV stream :$PORT" "$URL"
fi
