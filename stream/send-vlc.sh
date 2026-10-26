#!/usr/bin/env bash
# Stream a file, webcam, or screen as MJPEG over HTTP with VLC, for GUERILLA_MASK on the same hotspot.
#   stream/send-vlc.sh clip.mp4              loops a file on port 8080
#   stream/send-vlc.sh /dev/video0           Linux webcam
#   stream/send-vlc.sh avcapture://          macOS webcam
#   stream/send-vlc.sh screen://             share this screen
#   stream/send-vlc.sh clip.mp4 8090 1280    port, width
# Viewer URL: http://<this-ip>:PORT/stream.mjpg
# VLC adds no CORS header: projects fine, effects cannot read it. Use send-ffmpeg.sh or ustreamer for effects.
set -euo pipefail
SRC="${1:-}"; PORT="${2:-8080}"; WIDTH="${3:-960}"; FPS="${FPS:-15}"
[ -n "$SRC" ] || { sed -n '2,8p' "$0"; exit 1; }
case "$SRC" in /dev/video*) SRC="v4l2://$SRC";; esac
VLC=$(command -v cvlc || command -v vlc || echo /Applications/VLC.app/Contents/MacOS/VLC)
[ -x "$VLC" ] || { echo "VLC not found. apt install vlc / brew install --cask vlc"; exit 1; }
EXTRA=(); case "$SRC" in screen://) EXTRA=(--screen-fps="$FPS");; *://*) ;; *) EXTRA=(--loop);; esac
IP=$(hostname -I 2>/dev/null | awk '{print $1}' || ipconfig getifaddr en0 2>/dev/null || echo "<this-ip>")
echo "Streaming $SRC  ->  http://$IP:$PORT/stream.mjpg   (Ctrl+C stops)"
exec "$VLC" -I dummy "$SRC" "${EXTRA[@]}" --no-audio \
  --sout "#transcode{vcodec=MJPG,venc=ffmpeg{strict=1},fps=$FPS,width=$WIDTH}:standard{access=http{mime=multipart/x-mixed-replace;boundary=--7b3cc56e5f51db803f790dad720ed50a},mux=mpjpeg,dst=:$PORT/stream.mjpg}"
