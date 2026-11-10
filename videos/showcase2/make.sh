#!/usr/bin/env bash
# 絵も音もコードだけで作る48秒の縦動画(1080x1920)。有料サービス・素材は使わない。
set -euo pipefail
cd "$(dirname "$0")/../.."
export NODE_PATH="${NODE_PATH:-$(npm root -g)}"
FR=out/showcase2_frames
rm -rf "$FR" && mkdir -p "$FR"
python3 videos/showcase2/synth.py
# 8区間に分け、4並列で撮影
seq 0 7 | xargs -P 4 -I{} sh -c 'node videos/showcase2/render.cjs $(( {} * 180 )) $(( ({} + 1) * 180 )) '"$FR"
[ "$(ls "$FR" | wc -l)" = 1440 ] || { echo "frame count mismatch"; exit 1; }
ffmpeg -y -loglevel error -framerate 30 -i "$FR/%05d.jpg" -i out/showcase2.wav \
  -c:v libx264 -preset slow -crf 21 -maxrate 9M -bufsize 18M -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart out/showcase2.mp4
rm -rf "$FR"
echo done
