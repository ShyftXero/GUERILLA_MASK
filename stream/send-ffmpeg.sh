#!/usr/bin/env bash
# Re-serve anything ffmpeg can open (file, webcam, RTSP camera, another stream) as MJPEG with a CORS header,
# so GUERILLA_MASK effects can read it. One viewer at a time.
#   stream/send-ffmpeg.sh rtsp://admin:pw@10.0.0.5/stream1
#   stream/send-ffmpeg.sh clip.mp4 8090
#   stream/send-ffmpeg.sh /dev/video0
# Viewer URL: http://<this-ip>:PORT/stream.mjpg
set -euo pipefail
SRC="${1:-}"; PORT="${2:-8080}"; WIDTH="${WIDTH:-960}"; FPS="${FPS:-15}"; Q="${Q:-6}"
[ -n "$SRC" ] || { sed -n '2,7p' "$0"; exit 1; }
command -v ffmpeg >/dev/null || { echo "ffmpeg not found. apt install ffmpeg / brew install ffmpeg"; exit 1; }
IN=(); case "$SRC" in
  rtsp://*) IN=(-rtsp_transport tcp -i "$SRC");;
  /dev/video*) IN=(-f v4l2 -framerate "$FPS" -i "$SRC");;
  *://*) IN=(-i "$SRC");;
  *) IN=(-stream_loop -1 -re -i "$SRC");;
esac
IP=$(hostname -I 2>/dev/null | awk '{print $1}' || ipconfig getifaddr en0 2>/dev/null || echo "<this-ip>")
echo "Streaming $SRC  ->  http://$IP:$PORT/stream.mjpg   (Ctrl+C stops; restarts when the viewer reconnects)"
while :; do
  ffmpeg -hide_banner -loglevel warning "${IN[@]}" -an -vf "scale=$WIDTH:-2,fps=$FPS" -c:v mjpeg -q:v "$Q" \
    -f mpjpeg -listen 1 -content_type 'multipart/x-mixed-replace;boundary=ffmpeg' -headers $'Access-Control-Allow-Origin: *\r\n' "http://0.0.0.0:$PORT/stream.mjpg" || true
  sleep 0.5
done
