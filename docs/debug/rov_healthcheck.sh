#!/usr/bin/env bash
# rov_healthcheck.sh: 10-second health check of the ROV video system.
#
# Runs on the ROV computer (Raspberry Pi, Jetson or any Linux). Checks power and heat (A),
# cameras and USB (B), the computer (C), the stream settings it can see (D) and the tether (E),
# and prints ✅ / ⚠️ / ❌ per check with what a bad result means and what to do.
# The IDs (A1, B4, E7, …) are the rows of docs/debug/ROV_Debug_Checklist.md.
#
# Usage:
#   bash rov_healthcheck.sh --top 192.168.2.1 --cams 4          # normal use
#   bash rov_healthcheck.sh --top 192.168.2.1 --iperf           # + 5 s throughput test (needs `iperf3 -s` on topside)
#   sudo bash rov_healthcheck.sh --top 192.168.2.1 --md > health.md   # markdown, to paste into an issue
#
# Options:
#   --top IP      topside laptop IP (enables the ping, MTU and iperf checks)
#   --if NAME     tether interface (default: the interface of the default route, else eth0)
#   --cams N      number of cameras that should be connected
#   --speed MBPS  expected link speed in Mb/s (default 100; use 1000 for a gigabit tether)
#   --iperf       also measure throughput to the topside for 5 s
#   --md          print a markdown table instead of coloured text
#
# Exit code: 0 all good · 1 warnings · 2 at least one failure.
# Needs only bash and coreutils; uses v4l2-ctl, lsusb, ethtool, ping, tc, iperf3 and vcgencmd when present.
# Run with sudo to read the kernel log on systems that restrict dmesg.

TOP="" IFACE="" CAMS="" SPEED=100 DO_IPERF=0 MD=0
N_PASS=0 N_WARN=0 N_FAIL=0 N_SKIP=0 FIRST_FAIL="" FIRST_WARN=""
PROBLEMS=()

# ----------------------------------------------------------------------------- output
if [[ -t 1 ]]; then R=$'\e[31m' G=$'\e[32m' Y=$'\e[33m' D=$'\e[2m' B=$'\e[1m' N=$'\e[0m'; else R="" G="" Y="" D="" B="" N=""; fi

section() {  # section "A · Power and heat"
  if (( MD )); then printf '| **%s** | | | |\n' "$1"; else printf '\n%s%s%s\n' "$B" "$1" "$N"; fi
}

# result ID STATUS(PASS|WARN|FAIL|SKIP|INFO) "check" "measured value" ["what it means" "what to do"]
result() {
  local id=$1 st=$2 name=$3 val=$4 means=${5:-} fix=${6:-} icon col
  case $st in
    PASS) icon="✅"; col=$G; ((N_PASS++)) ;;
    WARN) icon="⚠️ "; col=$Y; ((N_WARN++)); [[ -z $FIRST_WARN ]] && FIRST_WARN="$id $name" ;;
    FAIL) icon="❌"; col=$R; ((N_FAIL++)); [[ -z $FIRST_FAIL ]] && FIRST_FAIL="$id $name" ;;
    SKIP) icon="➖"; col=$D; ((N_SKIP++)) ;;
    *)    icon="ℹ️ "; col=$D ;;
  esac
  if [[ $st == WARN || $st == FAIL ]] && [[ -n $means ]]; then PROBLEMS+=("$icon $id $name: $means → $fix"); fi
  if (( MD )); then
    printf '| %s | %s %s | %s | %s |\n' "$id" "$icon" "$st" "$name" "${val//|/\\|}"
  else
    printf '  %s %s%-4s%s %-34s %s\n' "$icon" "$col" "$id" "$N" "$name" "$val"
    if [[ $st == WARN || $st == FAIL ]] && [[ -n $means ]]; then
      printf '         %s→ means:%s %s\n         %s→ do:%s    %s\n' "$col" "$N" "$means" "$col" "$N" "$fix"
    fi
  fi
}

have() { command -v "$1" >/dev/null 2>&1; }

# ----------------------------------------------------------------------------- parsers (pure: text in, text out; tested in docs/debug/test_healthcheck.sh)

# Decode a Raspberry Pi `vcgencmd get_throttled` value (e.g. 0x50005) into words; empty when 0x0.
decode_throttled() {
  local v=$(( $1 )) out=()
  (( v & 0x1 ))     && out+=("under-voltage NOW")
  (( v & 0x2 ))     && out+=("frequency capped NOW")
  (( v & 0x4 ))     && out+=("throttled NOW")
  (( v & 0x8 ))     && out+=("soft temperature limit NOW")
  (( v & 0x10000 )) && out+=("under-voltage since boot")
  (( v & 0x20000 )) && out+=("frequency capped since boot")
  (( v & 0x40000 )) && out+=("throttled since boot")
  (( v & 0x80000 )) && out+=("soft temperature limit since boot")
  local IFS=,; echo "${out[*]}"
}

# From `lsusb -t` on stdin, print one line per USB camera: "<bus> <speed>" (a camera with two
# uvcvideo interfaces is counted once).
usb_cameras() {
  awk '
    /Bus [0-9]+/ { if (match($0, /Bus [0-9]+/)) bus = substr($0, RSTART + 4, RLENGTH - 4) + 0 }
    /Driver=uvcvideo/ {
      dev = ""; if (match($0, /Dev [0-9]+/)) dev = substr($0, RSTART + 4, RLENGTH - 4)
      spd = ""; if (match($0, /[0-9.]+M *$/)) spd = substr($0, RSTART, RLENGTH); gsub(/ /, "", spd)
      key = bus ":" dev; if (!(key in seen)) { seen[key] = 1; print bus, spd }
    }'
}

# From `ping` output on stdin, print "<loss%> <min> <avg> <max>" (ms); prints "100 - - -" if no reply.
parse_ping() {
  awk '
    /packet loss/ { for (i = 1; i <= NF; i++) if ($i ~ /%$/) { loss = $i; sub(/%/, "", loss) } }
    /^(rtt|round-trip)/ { split($4, a, "/"); mn = a[1]; av = a[2]; mx = a[3] }
    END { if (loss == "") loss = 100; if (av == "") print loss, "-", "-", "-"; else print loss, mn, av, mx }'
}

# Look at the command lines of the running video processes (stdin, one per line) and print
# "<ID>|<WARN|INFO>|<finding>|<what to do>" for settings known to add latency or fragility.
pipeline_findings() {
  awk '
    function out(id, st, what, fix) { if (!((id what) in done)) { done[id what] = 1; print id "|" st "|" what "|" fix } }
    {
      line = $0
      if (line ~ /libx264/ && line !~ /zerolatency/)
        out("D4", "WARN", "x264 without -tune zerolatency (holds ~30-40 frames, about 1 s)", "add -tune zerolatency -bf 0 to the live stream")
      if (line ~ /x264enc/ && line !~ /zerolatency/)
        out("D4", "WARN", "GStreamer x264enc without tune=zerolatency", "add tune=zerolatency speed-preset=ultrafast")
      if (line ~ /-bf [1-9]/ || line ~ /b-frames=[1-9]|bframes=[1-9]/)
        out("D4", "WARN", "B-frames enabled on a live stream", "use -bf 0 / no B-frames for live video")
      if (line ~ /rtsp_transport tcp|protocols=(tcp|4)|-rtsp_flags prefer_tcp/)
        out("D6", "WARN", "a stream uses TCP transport", "use UDP/RTP for the live view; after any loss TCP delay only grows")
      if (match(line, /-g [0-9]+/)) { g = substr(line, RSTART + 3, RLENGTH - 3) + 0; if (g > 60) out("D3", "WARN", "GOP of " g " frames (over 2 s at 30 fps)", "use -g 30 (1 s) or intra refresh: faster recovery and camera switch") }
      if (match(line, /iframeinterval=[0-9]+/)) { g = substr(line, RSTART + 15, RLENGTH - 15) + 0; if (g > 60) out("D3", "WARN", "Jetson iframeinterval=" g, "use iframeinterval=30 and idrinterval=30") }
      if (match(line, /rtpjitterbuffer[^!]*latency=[0-9]+/)) { s = substr(line, RSTART, RLENGTH); sub(/.*latency=/, "", s); if (s + 0 > 200) out("F3", "FAIL", "rtpjitterbuffer latency=" s " ms", "start at latency=50 and raise only if it stutters"); else if (s + 0 > 50) out("F3", "WARN", "rtpjitterbuffer latency=" s " ms", "try latency=50") }
      if (line ~ /input_format mjpeg/ && line ~ /scale=/)
        out("C5", "WARN", "an MJPEG camera is decoded and resized on the CPU (the resolution trap)", "ask the camera for the size you want (-video_size) and copy it")
      if (line ~ /nvv4l2h264enc/ && line !~ /insert-sps-pps/)
        out("D5", "INFO", "nvv4l2h264enc without insert-sps-pps=1", "add insert-sps-pps=1 so a late-joining player can start")
    }'
}

# ----------------------------------------------------------------------------- checks

check_power_heat() {
  section "A · Power and heat"
  # A1 temperature: hottest thermal zone, ignoring the Jetson PMIC zone that always reads 100 °C
  local max=-1 z t typ
  for z in /sys/class/thermal/thermal_zone*; do
    [[ -r $z/temp ]] || continue
    typ=$(cat "$z/type" 2>/dev/null); [[ $typ == *PMIC* ]] && continue
    t=$(cat "$z/temp" 2>/dev/null) || continue; [[ $t =~ ^[0-9]+$ ]] || continue
    (( t > max )) && max=$t
  done
  if (( max < 0 )); then result A1 SKIP "SoC temperature" "no thermal sensor found"
  else
    local c=$(( max / 1000 ))
    if   (( c >= 80 )); then result A1 FAIL "SoC temperature" "${c} °C" "the board is at its throttle point and slows down" "improve the heat path (heatsink on the hull, fan), less software encoding; run soak test E16"
    elif (( c >= 70 )); then result A1 WARN "SoC temperature" "${c} °C" "little margin: it will throttle in a closed, warm hull" "check again after 30 min closed (E16)"
    else result A1 PASS "SoC temperature" "${c} °C"; fi
  fi
  # A2 + A3 throttling and under-voltage (Raspberry Pi)
  if have vcgencmd; then
    local raw words; raw=$(vcgencmd get_throttled 2>/dev/null | cut -d= -f2)
    if [[ $raw =~ ^0x[0-9a-fA-F]+$ ]]; then
      words=$(decode_throttled "$raw")
      local thr=$(( raw & 0xE000E )) uv=$(( raw & 0x10001 ))
      if (( thr )); then result A2 FAIL "Throttling" "$raw" "the CPU slowed down (${words})" "cooling or power: see A1 and A3"
      else result A2 PASS "Throttling" "$raw (never)"; fi
      if (( uv )); then result A3 FAIL "Under-voltage" "$raw" "the supply sagged below 4.63 V" "separate regulated 5 V for computer and cameras; thicker, shorter wires; check while thrusters reverse"
      else result A3 PASS "Under-voltage" "none since boot"; fi
    else result A2 SKIP "Throttling" "vcgencmd gave no value"; fi
  elif [[ -r /etc/nv_tegra_release ]]; then
    result A2 INFO "Throttling" "Jetson: watch clocks in 'sudo tegrastats' under load"
    local uvj=""; [[ -n $KLOG ]] && uvj=$(grep -ciE "under.?voltage|over.?current|soctherm.*(throttl|oc)" <<<"$KLOG")
    if [[ -z $uvj ]]; then result A3 SKIP "Under-voltage" "cannot read kernel log (run with sudo)"
    elif (( uvj > 0 )); then result A3 FAIL "Under-voltage / over-current" "$uvj kernel messages" "the supply or the board's current limit was hit" "check the 5 V supply under thruster load; Jetson: use the barrel jack (J25 jumper), not micro-USB"
    else result A3 PASS "Under-voltage / over-current" "none in kernel log"; fi
  else
    result A2 SKIP "Throttling" "not a Raspberry Pi or Jetson"
  fi
  local up; up=$(awk '{printf "%d", $1/60}' /proc/uptime)
  if (( up < 5 )); then result A4 WARN "Uptime" "${up} min" "the computer started less than 5 min ago: was that planned?" "if not, it rebooted: check power (A3) and 'last -x reboot'"
  else result A4 INFO "Uptime" "${up} min since boot"; fi
}

KLOG=""
read_kernel_log() {  # the kernel log since boot, or empty if this user may not read it
  KLOG=$(dmesg 2>/dev/null) || KLOG=""
  if [[ -z $KLOG ]] && have journalctl; then KLOG=$(journalctl -k -b --no-pager 2>/dev/null) || KLOG=""; fi
}

check_cameras_usb() {
  section "B · Cameras and USB"
  # B1 capture devices: a UVC camera makes two /dev/video nodes; the capture node has index 0
  local devs=() v
  for v in /sys/class/video4linux/video*; do
    [[ -e $v ]] || continue
    [[ $(cat "$v/index" 2>/dev/null) == 0 ]] && devs+=("/dev/$(basename "$v")")
  done
  local n=${#devs[@]}
  if [[ -n $CAMS ]]; then
    if (( n < CAMS )); then result B1 FAIL "Cameras detected" "$n of $CAMS" "$(( CAMS - n )) camera(s) not seen by Linux" "reseat the cable, try another port, check B4/B5; 'v4l2-ctl --list-devices'"
    else result B1 PASS "Cameras detected" "$n of $CAMS"; fi
  elif (( n == 0 )); then result B1 WARN "Cameras detected" "0 (no USB/CSI camera)" "no camera on this computer" "fine for IP cameras; otherwise check cables. Use --cams N"
  else result B1 INFO "Cameras detected" "$n (use --cams N to check the count)"; fi

  # B2 + B3 format, size and fps in use per camera
  if (( n > 0 )) && have v4l2-ctl; then
    local d name fmt wh fps
    for d in "${devs[@]}"; do
      name=$(cat "/sys/class/video4linux/$(basename "$d")/name" 2>/dev/null | cut -c1-22)
      fmt=$(v4l2-ctl -d "$d" --get-fmt-video 2>/dev/null | awk -F"'" '/Pixel Format/ {print $2}')
      wh=$(v4l2-ctl -d "$d" --get-fmt-video 2>/dev/null | awk -F': *' '/Width\/Height/ {print $2}' | tr / x)
      fps=$(v4l2-ctl -d "$d" --get-parm 2>/dev/null | awk -F': *' '/Frames per second/ {printf "%.0f", $2}')
      if [[ $fmt == YUYV || $fmt == NV12 || $fmt == YU12 ]]; then

        result B2 WARN "$d format" "$name: $fmt ${wh} @${fps}" "raw video: ~10x the USB bandwidth of MJPEG; a 3rd camera will not start" "switch to MJPG or H264 (v4l2-ctl -d $d --list-formats-ext)"
      else
        result B2 PASS "$d format" "$name: ${fmt:-?} ${wh} @${fps:-?}"
      fi
    done
  elif (( n > 0 )); then result B2 SKIP "Camera formats" "install v4l-utils (v4l2-ctl)"; fi

  # B4 USB bus speed and sharing
  if have lsusb; then
    local cams; cams=$(lsusb -t 2>/dev/null | usb_cameras)
    if [[ -z $cams ]]; then result B4 INFO "USB cameras on buses" "no uvcvideo device"
    else
      local slow busiest busy_n summary
      slow=$(awk '$2 == "12M" || $2 == "1.5M"' <<<"$cams" | wc -l)
      summary=$(awk '{c[$1]++; s[$1]=$2} END {for (b in c) printf "bus %s: %d cam @%s  ", b, c[b], s[b]}' <<<"$cams")
      read -r busiest busy_n < <(awk '$2 == "480M" {c[$1]++} END {m = 0; for (b in c) if (c[b] > m) {m = c[b]; k = b} print k, m}' <<<"$cams")
      if (( slow > 0 )); then result B4 FAIL "USB bus speed" "$summary" "$slow camera(s) run at USB 1.1 speed (12M)" "a USB 1.1 hub or a bad cable: plug the camera into a USB 2/3 port directly"
      elif (( ${busy_n:-0} >= 4 )); then result B4 FAIL "USB bus sharing" "$summary" "$busy_n cameras share USB 2.0 bus $busiest (480 Mb/s total)" "too many for one bus: move cameras to other controllers (USB 3 ports, another root port)"
      elif (( ${busy_n:-0} >= 3 )); then result B4 WARN "USB bus sharing" "$summary" "$busy_n cameras share USB 2.0 bus $busiest (480 Mb/s total)" "spread cameras over different controllers (USB 3 ports, a second hub on another root port)"
      else result B4 PASS "USB bus speed and sharing" "$summary"; fi
    fi
  else result B4 SKIP "USB buses" "install usbutils (lsusb)"; fi

  # B5 kernel errors about USB and cameras since boot
  local klog=$KLOG
  if [[ -z $klog ]]; then result B5 SKIP "USB / camera kernel errors" "cannot read kernel log (run with sudo)"
  else
    local resets nospace uvc
    resets=$(grep -ciE "usb [0-9-]+(\.[0-9]+)*: (reset|USB disconnect)" <<<"$klog")
    nospace=$(grep -ciE "no space left on device|not enough bandwidth" <<<"$klog")
    uvc=$(grep -ciE "uvcvideo.*(fail|error|timeout)" <<<"$klog")
    if (( nospace > 0 )); then result B5 FAIL "USB / camera kernel errors" "$nospace bandwidth errors" "a camera asked for more USB bandwidth than the bus has" "use MJPEG, lower fps/size, or move cameras to other buses (B4)"
    elif (( resets > 2 || uvc > 0 )); then result B5 FAIL "USB / camera kernel errors" "$resets resets/disconnects, $uvc uvc errors" "cameras dropped off the bus" "power dips (A3) or loose cables; run 'dmesg -w' while reversing thrusters"
    elif (( resets > 0 )); then result B5 WARN "USB / camera kernel errors" "$resets resets/disconnects" "something reconnected since boot (maybe a planned unplug)" "if not planned: cable or power; watch 'dmesg -w'"
    else result B5 PASS "USB / camera kernel errors" "none since boot"; fi
  fi
}

PROC_LINES=""
check_computer() {
  section "C · ROV computer"
  # C1 CPU per core over the sample window (filled by sample_window)
  local busiest_core=${CPU_MAX:-} total=${CPU_TOTAL:-}
  if [[ -z $total ]]; then result C1 SKIP "CPU" "no sample"
  elif (( total >= 85 )); then result C1 FAIL "CPU (all cores / busiest)" "${total} % / ${busiest_core} %" "the computer is saturated: frames will be dropped or delayed" "stop re-encoding on the CPU (C5), use the camera's H.264 or the hardware encoder, fewer streams"
  elif (( total >= 70 )); then result C1 WARN "CPU (all cores / busiest)" "${total} % / ${busiest_core} %" "little CPU left: one more stream or a hot hull will tip it over" "plan for at least one free core (experiment E19)"
  elif (( busiest_core >= 95 )); then result C1 WARN "CPU (all cores / busiest)" "${total} % / ${busiest_core} %" "one core is full: a single-threaded stage is the bottleneck" "find it in 'htop' (sort by CPU); give that stream its own process or use hardware"
  else result C1 PASS "CPU (all cores / busiest)" "${total} % / ${busiest_core} %"; fi
  # C2 memory
  local avail total_kb swap_used
  avail=$(awk '/MemAvailable/ {print $2}' /proc/meminfo); total_kb=$(awk '/MemTotal/ {print $2}' /proc/meminfo)
  swap_used=$(awk '/SwapTotal/ {t=$2} /SwapFree/ {f=$2} END {print int((t-f)/1024)}' /proc/meminfo)
  local pct=$(( avail * 100 / total_kb ))
  if   (( pct < 10 )); then result C2 FAIL "Memory available" "${pct} % ($(( avail / 1024 )) MB), swap ${swap_used} MB" "almost out of memory: stalls, then the kernel kills a process" "find the biggest process (htop, sort MEM); a growing one means a queue that never empties"
  elif (( pct < 20 || swap_used > 50 )); then result C2 WARN "Memory available" "${pct} % ($(( avail / 1024 )) MB), swap ${swap_used} MB" "little memory left or swapping (slow)" "check again after 10 min: if it keeps falling, something leaks"
  else result C2 PASS "Memory available" "${pct} % ($(( avail / 1024 )) MB)"; fi
  # C3 disk
  local free_mb; free_mb=$(df -Pm "${HOME:-/}" 2>/dev/null | awk 'NR == 2 {print $4}')
  if [[ -z $free_mb ]]; then result C3 SKIP "Disk free" "df failed"
  elif (( free_mb < 1024 )); then result C3 FAIL "Disk free (home)" "${free_mb} MB" "recordings will stop and some apps crash when the disk is full" "delete or move old recordings"
  elif (( free_mb < 4096 )); then result C3 WARN "Disk free (home)" "${free_mb} MB" "about $(( free_mb / 15 / 60 )) h of one 2 Mb/s recording left" "make room before the dive"
  else result C3 PASS "Disk free (home)" "${free_mb} MB"; fi
  # C4 video processes
  PROC_LINES=$(ps -eo pid=,etimes=,pcpu=,args= 2>/dev/null | grep -Ei "ffmpeg|gst-launch|gst-rtsp|mediamtx|ustreamer|mjpg_streamer|rpicam-vid|libcamera-vid|nvgstcapture" | grep -v -E "grep|rov_healthcheck")
  local np young
  np=$(grep -c . <<<"$PROC_LINES")
  young=$(awk '$2 < 60' <<<"$PROC_LINES" | grep -c .)
  if (( np == 0 )); then result C4 WARN "Video processes running" "none found" "no ffmpeg/GStreamer/streamer process: the video is not running (or runs under another name)" "start the video service; read its log: journalctl -u <service> -n 50"
  elif (( young > 0 )); then result C4 WARN "Video processes running" "$np, $young started < 1 min ago" "a stream restarted recently: it may be in a crash-restart loop" "run this check again in 1 min; read the service log"
  else result C4 PASS "Video processes running" "$np (avg CPU: $(awk '{printf "%s%% ", $3}' <<<"$PROC_LINES"))"; fi
}

check_streams() {
  section "D · Stream settings (from the running command lines)"
  if [[ -z $PROC_LINES ]]; then result D0 SKIP "Encoder settings" "no video process to inspect"; return; fi
  local findings id st what fix
  findings=$(awk '{$1 = $2 = $3 = ""; print}' <<<"$PROC_LINES" | pipeline_findings)
  if [[ -z $findings ]]; then result D4 PASS "Latency-related settings" "nothing suspicious in $(grep -c . <<<"$PROC_LINES") command line(s)"; return; fi
  while IFS='|' read -r id st what fix; do
    [[ -z $id ]] && continue
    result "$id" "$st" "Pipeline setting" "$what" "$what" "$fix"
  done <<<"$findings"
}

CPU_TOTAL="" CPU_MAX="" TX_MBPS="" RX_MBPS="" ERR_DELTA=0
sample_window() {  # 3-second sample of CPU and tether traffic, so the numbers are live, not averages since boot
  local s=/sys/class/net/$IFACE/statistics a b
  mapfile -t a < /proc/stat
  local tx0 rx0 e0 tx1 rx1 e1
  tx0=$(cat "$s/tx_bytes" 2>/dev/null || echo 0); rx0=$(cat "$s/rx_bytes" 2>/dev/null || echo 0)
  e0=$(( $(cat "$s/rx_errors" 2>/dev/null || echo 0) + $(cat "$s/tx_errors" 2>/dev/null || echo 0) ))
  sleep 3
  mapfile -t b < /proc/stat
  tx1=$(cat "$s/tx_bytes" 2>/dev/null || echo 0); rx1=$(cat "$s/rx_bytes" 2>/dev/null || echo 0)
  e1=$(( $(cat "$s/rx_errors" 2>/dev/null || echo 0) + $(cat "$s/tx_errors" 2>/dev/null || echo 0) ))
  TX_MBPS=$(awk -v d=$(( tx1 - tx0 )) 'BEGIN {printf "%.1f", d * 8 / 3 / 1e6}')
  RX_MBPS=$(awk -v d=$(( rx1 - rx0 )) 'BEGIN {printf "%.1f", d * 8 / 3 / 1e6}')
  ERR_DELTA=$(( e1 - e0 ))
  local i max=0 total=0
  for i in "${!a[@]}"; do
    [[ ${a[$i]} == cpu* ]] || continue
    local u
    u=$(awk -v x="${a[$i]}" -v y="${b[$i]}" 'BEGIN {
          n = split(x, p); split(y, q); t = 0; idle = 0
          for (k = 2; k <= n && k <= 9; k++) t += q[k] - p[k]    # guest time is already in user
          idle = (q[5] - p[5]) + (q[6] - p[6])
          printf "%d", (t > 0) ? 100 * (t - idle) / t : 0 }')
    if [[ ${a[$i]} == "cpu "* ]]; then total=$u; elif (( u > max )); then max=$u; fi
  done
  CPU_TOTAL=$total CPU_MAX=$max
}

check_tether() {
  section "E · Tether and network ($IFACE)"
  local s=/sys/class/net/$IFACE
  if [[ ! -d $s ]]; then result E1 FAIL "Interface $IFACE" "does not exist" "wrong interface name" "list them with 'ip -br link' and use --if"; return; fi
  # E1 speed and duplex
  local sp du; sp=$(cat "$s/speed" 2>/dev/null); du=$(cat "$s/duplex" 2>/dev/null)
  local state; state=$(cat "$s/operstate" 2>/dev/null)
  if [[ $state == down || $state == lowerlayerdown || $state == notpresent ]]; then result E1 FAIL "Link" "DOWN" "no Ethernet link on the tether" "cable, connector, power of the topside switch; 'ethtool $IFACE'"
  elif [[ -z $sp || $sp == -1 ]]; then result E1 SKIP "Link speed / duplex" "not reported by this interface"
  elif (( sp < SPEED )) || [[ $du != full ]]; then result E1 FAIL "Link speed / duplex" "$sp Mb/s $du (expected $SPEED full)" "the link negotiated down: everything above $sp Mb/s will be lost or queued" "a broken pair or connector in the tether, or a 100 Mb/s switch port; check both ends with ethtool"
  else result E1 PASS "Link speed / duplex" "$sp Mb/s $du"; fi
  # E2 errors
  local errs crc
  errs=$(( $(cat "$s/statistics/rx_errors" 2>/dev/null || echo 0) + $(cat "$s/statistics/tx_errors" 2>/dev/null || echo 0) ))
  crc=$(cat "$s/statistics/rx_crc_errors" 2>/dev/null || echo 0)
  if (( ERR_DELTA > 0 )); then result E2 FAIL "Interface errors" "+$ERR_DELTA in 3 s (total $errs, CRC $crc)" "errors are happening right now: damaged frames on the tether" "electrical noise (test with thrusters on and off), a bad pair or connector, cable too long"
  elif (( errs > 0 )); then result E2 WARN "Interface errors" "total $errs since boot (CRC $crc), none now" "errors happened earlier, maybe during thrust or a cable move" "watch 'ethtool -S $IFACE | grep -i err' while running thrusters"
  else result E2 PASS "Interface errors" "0"; fi
  # E8 utilisation
  local link=${sp:-0}; (( link > 0 )) || link=$SPEED
  local pct; pct=$(awk -v t="$TX_MBPS" -v l="$link" 'BEGIN {printf "%d", 100 * t / l}')
  if   (( pct > 85 )); then result E8 FAIL "Tether use, ROV to topside" "$TX_MBPS Mb/s = ${pct} % of $link" "the tether is full: loss, keyframe bursts and late control" "cut bitrate or cameras (Encoding Lab → Bandwidth budget)"
  elif (( pct > 70 )); then result E8 WARN "Tether use, ROV to topside" "$TX_MBPS Mb/s = ${pct} % of $link" "above the 70 % planning limit: keyframe bursts will hit the ceiling" "lower bitrates or stagger keyframes (E8)"
  else result E8 PASS "Tether use, ROV to topside" "$TX_MBPS Mb/s = ${pct} % of $link (in: $RX_MBPS)"; fi
  # E7 leftover test rules
  if have tc; then
    local q; q=$(tc qdisc show dev "$IFACE" 2>/dev/null | grep -oE "netem|tbf" | sort -u | tr '\n' ' ')
    if [[ -n $q ]]; then result E7 FAIL "Leftover test rules (tc)" "$q" "someone left a Chaos Monkey rule: it adds loss, delay or a speed limit" "sudo tc qdisc del dev $IFACE root"
    else result E7 PASS "Leftover test rules (tc)" "none"; fi
  fi
  # MTU on the interface
  local mtu; mtu=$(cat "$s/mtu" 2>/dev/null)
  if [[ -n $mtu ]] && (( mtu < 1500 )); then result E6 WARN "Interface MTU" "$mtu" "packets above $mtu bytes get fragmented" "keep RTP payloads ≤ $(( mtu - 100 )) bytes (pkt_size=)"; fi

  if [[ -z $TOP ]]; then result E4 SKIP "Ping / MTU / throughput" "give --top <topside IP> to test the path"; return; fi
  if ! have ping; then result E4 SKIP "Ping" "ping not installed"; return; fi
  # E4 round trip
  local loss av mx
  read -r loss _ av mx < <(ping -c 20 -i 0.2 -W 1 "$TOP" 2>/dev/null | parse_ping)
  if [[ $av == - ]]; then result E4 FAIL "Ping topside $TOP" "no reply" "the topside is unreachable from the ROV" "IP addresses (ip -br addr), cable, firewall on the laptop"
  elif awk -v l="$loss" 'BEGIN {exit !(l > 0)}'; then result E4 FAIL "Ping topside $TOP" "${loss} % loss, avg $av ms, max $mx ms" "packets are lost on the tether even for tiny pings" "E1/E2: link and errors; a full link (E8)"
  elif awk -v m="$mx" 'BEGIN {exit !(m > 30)}'; then result E4 FAIL "Ping topside $TOP" "avg $av ms, max $mx ms" "long queueing: control packets can wait $mx ms behind video" "the link is full (E8); give control priority (E9)"
  elif awk -v a="$av" -v m="$mx" 'BEGIN {exit !(a > 2 || m > 10)}'; then result E4 WARN "Ping topside $TOP" "avg $av ms, max $mx ms" "queueing: packets wait behind video (a tether should be < 2 ms)" "the link is near full (E8); give control priority (E9)"
  else result E4 PASS "Ping topside $TOP" "0 % loss, avg $av ms, max $mx ms"; fi
  # E6 path MTU
  if ping -M "do" -s 1472 -c 2 -W 1 "$TOP" >/dev/null 2>&1; then result E6 PASS "Path MTU 1500" "1472-byte ping passes unfragmented"
  elif [[ $av != - ]]; then result E6 WARN "Path MTU 1500" "1472-byte ping blocked" "something on the path has MTU < 1500: big video packets get fragmented" "keep RTP payloads at 1200-1400 bytes (pkt_size=1316; mtu=1400)"; fi
  # E3 throughput
  if (( DO_IPERF )); then
    if have iperf3; then
      local mbps; mbps=$(iperf3 -c "$TOP" -t 5 -f m 2>/dev/null | grep -E "sender$" | grep -oE "[0-9.]+ Mbits/sec" | head -1 | cut -d' ' -f1)
      if [[ -z $mbps ]]; then result E3 SKIP "Throughput (iperf3)" "no iperf3 server: run 'iperf3 -s' on the topside"
      else
        local p; p=$(awk -v m="$mbps" -v l="$link" 'BEGIN {printf "%d", 100 * m / l}')
        if   (( p < 50 )); then result E3 FAIL "Throughput to topside" "$mbps Mb/s (${p} % of $link)" "the tether carries far less than its speed" "errors (E2), duplex mismatch (E1), a slow switch or laptop adapter"
        elif (( p < 90 )); then result E3 WARN "Throughput to topside" "$mbps Mb/s (${p} % of $link)" "less than expected (video was running during the test?)" "repeat with video stopped; if still low see E1/E2"
        else result E3 PASS "Throughput to topside" "$mbps Mb/s (${p} % of $link)"; fi
      fi
    else result E3 SKIP "Throughput" "install iperf3"; fi
  fi
}

summary() {
  if (( MD )); then
    printf '\n**Result:** %d ✅ · %d ⚠️ · %d ❌ · %d skipped\n' "$N_PASS" "$N_WARN" "$N_FAIL" "$N_SKIP"
    if (( ${#PROBLEMS[@]} )); then printf '\n**Problems**\n\n'; printf -- '- %s\n' "${PROBLEMS[@]}"; fi
  else
    printf '\n%sResult:%s %s%d ✅%s  %s%d ⚠️%s  %s%d ❌%s  %d skipped\n' "$B" "$N" "$G" "$N_PASS" "$N" "$Y" "$N_WARN" "$N" "$R" "$N_FAIL" "$N" "$N_SKIP"
  fi
  (( MD )) && echo
  if [[ -n $FIRST_FAIL ]]; then printf '%sStart with %s%s: the first ❌ in pipeline order is usually the cause of the rest.\n' "$B" "$FIRST_FAIL" "$N"
  elif [[ -n $FIRST_WARN ]]; then printf '%sNo failures. Look first at %s%s.\n' "$B" "$FIRST_WARN" "$N"
  else printf 'Everything this script can see is healthy. Next: the manual checks F (topside) and G (pilot) in docs/debug/ROV_Debug_Checklist.md.\n'; fi
  printf 'Manual checks the script cannot do: F1–F7 (topside and display), G1–G6 (what the pilot sees).\n'
}

usage() { sed -n '2,25p' "$0" | sed 's/^# \{0,1\}//'; }

main() {
  while (( $# )); do
    case $1 in
      --top) TOP=$2; shift ;;
      --if) IFACE=$2; shift ;;
      --cams) CAMS=$2; shift ;;
      --speed) SPEED=$2; shift ;;
      --iperf) DO_IPERF=1 ;;
      --md) MD=1; R="" G="" Y="" D="" B="" N="" ;;
      -h|--help) usage; exit 0 ;;
      *) echo "unknown option: $1 (try --help)" >&2; exit 64 ;;
    esac
    shift
  done
  [[ -z $IFACE ]] && IFACE=$(awk '$2 == "00000000" {print $1; exit}' /proc/net/route 2>/dev/null)    # interface of the default route
  [[ -z $IFACE ]] && IFACE=eth0
  local model; model=$(tr -d '\0' 2>/dev/null < /proc/device-tree/model || uname -n)
  if (( MD )); then
    printf '### ROV health check · %s · %s\n\n| ID | Status | Check | Result |\n|---|---|---|---|\n' "$model" "$(date '+%Y-%m-%d %H:%M')"
  else
    printf '%sROV video health check%s · %s · %s · tether %s%s\n' "$B" "$N" "$model" "$(date '+%Y-%m-%d %H:%M')" "$IFACE" "${TOP:+ → $TOP}"
    printf '%sSampling CPU and tether traffic for 3 s…%s\n' "$D" "$N"
  fi
  read_kernel_log
  sample_window
  check_power_heat
  check_cameras_usb
  check_computer
  check_streams
  check_tether
  summary
  (( N_FAIL )) && exit 2
  (( N_WARN )) && exit 1
  exit 0
}

[[ ${BASH_SOURCE[0]} == "$0" ]] && main "$@"
