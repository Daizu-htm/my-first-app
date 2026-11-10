#!/usr/bin/env bash
# TikTok用の縦動画(1080x1920, 60fps)。物理シミュレーションと音をコードだけで作る。
set -euo pipefail
cd "$(dirname "$0")/../.."
export NODE_PATH="${NODE_PATH:-$(npm root -g)}"
D=videos/tiktok1 FR=out/tiktok1_frames
rm -rf "$FR" && mkdir -p "$FR"
node $D/events.cjs
python3 $D/synth.py
N=$(node -e "console.log(require('./$D/events.json').frames)")
C=$(( (N + 7) / 8 ))
seq 0 7 | xargs -P 4 -I{} sh -c 's=$(( {} * '$C' )); e=$(( s + '$C' )); [ $e -gt '$N' ] && e='$N'; node '$D'/render.cjs $s $e '"$FR"
[ "$(ls "$FR" | wc -l)" = "$N" ] || { echo "frame count mismatch"; exit 1; }
ffmpeg -y -loglevel error -framerate 60 -i "$FR/%05d.jpg" -i out/tiktok1.wav \
  -c:v libx264 -preset slow -crf 19 -maxrate 10M -bufsize 20M -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart out/tiktok1.mp4
rm -rf "$FR"
echo done
