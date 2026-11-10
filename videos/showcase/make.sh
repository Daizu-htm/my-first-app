#!/usr/bin/env bash
# 絵も音もコードだけで作る32秒の縦動画(1080x1920)。有料サービス・素材は使わない。
set -euo pipefail
cd "$(dirname "$0")/../.."
export NODE_PATH="${NODE_PATH:-$(npm root -g)}"
FR=out/showcase_frames
rm -rf "$FR" && mkdir -p "$FR"
python3 videos/showcase/synth.py
# 4分割して並列に撮影
for i in 0 1 2 3; do node videos/showcase/render.cjs $((i*240)) $(((i+1)*240)) "$FR" & done
wait
[ "$(ls "$FR" | wc -l)" = 960 ] || { echo "frame count mismatch"; exit 1; }
ffmpeg -y -loglevel error -framerate 30 -i "$FR/%05d.jpg" -i out/showcase.wav \
  -c:v libx264 -preset slow -crf 24 -maxrate 6M -bufsize 12M -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart out/showcase.mp4
rm -rf "$FR"
echo done
