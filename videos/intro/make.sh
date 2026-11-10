#!/usr/bin/env bash
# 無料(ffmpegのみ)で縦動画(1080x1920, 8秒)を生成する。APIや有料サービスは使わない。
set -euo pipefail
cd "$(dirname "$0")/../.."
FONT=$(fc-list | grep -i 'NotoSansCJK-Bold.ttc' | head -1 | cut -d: -f1)
ffmpeg -y -loglevel error \
  -f lavfi -i "gradients=s=1080x1920:d=8:c0=0x1b2a6b:c1=0x6c3bd1:x0=0:y0=0:x1=1080:y1=1920:speed=0.02:r=30" \
  -f lavfi -i "sine=frequency=440:duration=8:sample_rate=44100" \
  -filter_complex "[0:v]\
drawtext=fontfile=$FONT:text='公開テスト成功':fontsize=110:fontcolor=white:x=(w-text_w)/2:y=(h/2-200)+(1-min(t/1\,1))*60:alpha='min(t/1,1)',\
drawtext=fontfile=$FONT:text='Claude Codeから自動公開':fontsize=58:fontcolor=white:x=(w-text_w)/2:y=h/2+10:alpha='if(lt(t,1.5),0,min((t-1.5)/1,1))',\
drawtext=fontfile=$FONT:text='fertilizer.jp/tool/clco/':fontsize=52:fontcolor=0xffd86b:x=(w-text_w)/2:y=h/2+140:alpha='if(lt(t,3),0,min((t-3)/1,1))',\
fade=t=out:st=7.2:d=0.8[v];[1:a]volume=0.0,afade=t=out:st=7:d=1[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -pix_fmt yuv420p -crf 23 -c:a aac -shortest out/intro.mp4
