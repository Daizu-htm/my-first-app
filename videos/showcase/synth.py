"""サウンドトラックを波形から合成する(素材・有料サービス不使用)。
出力: out/showcase.wav と videos/showcase/audio.js(映像と同期させるための音量・スペクトル)。"""
import json
import os
import wave

import numpy as np

SR, DUR, FPS = 44100, 32, 30
N = SR * DUR
rng = np.random.default_rng(7)
ROOT = os.path.join(os.path.dirname(__file__), "..", "..")

SAW = [(k, 1 / k) for k in range(1, 7)]
SQ = [(1, 1), (3, 0.33), (5, 0.2), (7, 0.14)]
SOFT = [(1, 1), (2, 0.3), (3, 0.1)]


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def tone(m, dur, harm, vib=0.0, det=0.0):
    x = np.arange(int(dur * SR)) / SR
    ph = 2 * np.pi * hz(m + det) * x
    if vib:
        ph = ph + vib * np.sin(2 * np.pi * 5.5 * x)
    return sum(a * np.sin(k * ph) for k, a in harm)


def env(n, a, d):
    x = np.arange(n) / SR
    return np.minimum(x / a, 1) * np.exp(-x / d)


def add(buf, start, sig, gain=1.0):
    i = int(start * SR)
    if i >= N:
        return
    j = min(N, i + len(sig))
    buf[i:j] += sig[: j - i] * gain


def kick():
    x = np.arange(int(0.4 * SR)) / SR
    f = 45 + 120 * np.exp(-x / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x / 0.13)


def noise(dur, decay, hp=True):
    n = int(dur * SR)
    w = rng.standard_normal(n)
    if hp:
        w = np.diff(w, prepend=0)
    return w * np.exp(-np.arange(n) / SR / decay)


def snare():
    x = np.arange(int(0.25 * SR)) / SR
    return noise(0.25, 0.07) * 0.6 + np.sin(2 * np.pi * 190 * x) * np.exp(-x / 0.05) * 0.5


PROG = [(45, [57, 60, 64]), (41, [53, 57, 60]), (48, [60, 64, 67]), (43, [55, 59, 62])]
DRUM_BARS = set(range(2, 10)) | {13, 14}
BACKBEAT_BARS = set(range(6, 10)) | {13, 14}

drums, bass, pad, fx = (np.zeros(N) for _ in range(4))
arpL, arpR, leadL, leadR = (np.zeros(N) for _ in range(4))
kick_times, impact_times = [], [4.0, 12.0, 26.0, 30.0]
K = kick()

for b in range(16):
    t0 = 2.0 * b
    root, ch = PROG[b % 4]
    # パッド
    if b < 15:
        for m in ch + [ch[0] + 12]:
            for det in (-0.08, 0, 0.08):
                s = tone(m, 2.4, SOFT, det=det)
                e = np.minimum(np.arange(len(s)) / SR / 0.35, 1) * np.minimum((2.4 - np.arange(len(s)) / SR) / 0.4, 1)
                add(pad, t0, s * e, 0.035 * (0.5 + 0.5 * min(1, (b + 1) / 2)))
    # アルペジオ(16分音符)
    if 2 <= b <= 14:
        seq = [ch[0], ch[1], ch[2], ch[0] + 12, ch[2], ch[1], ch[0] + 12, ch[2] + 12] * 2
        g = 0.07 if b in (10, 11, 12) else 0.11
        for i, m in enumerate(seq):
            s = tone(m + 12, 0.3, SQ)
            s = s * env(len(s), 0.004, 0.11)
            tt = t0 + i * 0.125
            add(arpL if i % 2 == 0 else arpR, tt, s, g)
            add(arpR if i % 2 == 0 else arpL, tt + 0.375, s, g * 0.35)
            add(arpL if i % 2 == 0 else arpR, tt + 0.75, s, g * 0.15)
    # ドラムとベース
    if b in DRUM_BARS:
        for q in range(4):
            tb = t0 + q * 0.5
            add(drums, tb, K, 0.95)
            kick_times.append(tb)
            add(drums, tb + 0.25, noise(0.08, 0.025), 0.13)
            if b in BACKBEAT_BARS:
                add(drums, tb + 0.125, noise(0.05, 0.012), 0.05)
                add(drums, tb + 0.375, noise(0.05, 0.012), 0.05)
                if q in (1, 3):
                    add(drums, tb, snare(), 0.5)
        for i in range(8):
            s = tone(root - 12 if i % 2 == 0 else root, 0.26, SAW)
            add(bass, t0 + i * 0.25, s * env(len(s), 0.005, 0.16), 0.2)

# リード
PH1 = [(76, 0, 1), (79, 1, .5), (81, 1.5, 1.5), (79, 3, .5), (76, 3.5, .5), (77, 4, 1), (76, 5, .5), (72, 5.5, 1.5), (74, 7, 1)]
PH2 = [(79, 0, 1), (84, 1, .5), (83, 1.5, 1.5), (79, 3, 1), (74, 4, 1), (79, 5, .5), (83, 5.5, 1.5), (81, 7, 1)]
for start, ph in ((12, PH1), (16, PH2), (26, PH1)):
    for m, beat, dur in ph:
        s = tone(m, dur * 0.5 + 0.25, SQ, vib=0.25)
        s = s * env(len(s), 0.02, dur * 0.5)
        tt = start + beat * 0.5
        add(leadL, tt, s, 0.085)
        add(leadR, tt + 0.01, s, 0.085)
        add(leadR, tt + 0.375, s, 0.03)
        add(leadL, tt + 0.75, s, 0.015)

# イントロのタイプ音
for i in range(4, 28):
    if rng.random() < 0.8:
        add(fx, i * 0.125, noise(0.03, 0.006), 0.07)
# インパクト
for ti in impact_times:
    x = np.arange(int(2.5 * SR)) / SR
    add(fx, ti, noise(2.5, 0.7), 0.16)
    add(fx, ti, np.sin(2 * np.pi * 48 * x) * np.exp(-x / 0.5), 0.6)
# ライザーとスネアロール(24〜26秒)
x = np.arange(2 * SR) / SR
sweep = np.sin(2 * np.pi * np.cumsum(200 * (10 ** (x / 2))) / SR)
add(fx, 24, (rng.standard_normal(len(x)) * 0.5 + sweep * 0.5) * (x / 2) ** 2, 0.22)
for i in range(8):
    add(drums, 24 + i * 0.125, snare(), 0.15 + 0.03 * i)
for i in range(16):
    add(drums, 25 + i * 0.0625, snare(), 0.3 + 0.02 * i)
# 最後の和音
for m in (45, 57, 60, 64, 71, 76):
    s = tone(m, 2.0, SOFT)
    add(pad, 30, s * env(len(s), 0.01, 0.9), 0.09)

# サイドチェイン(キックに合わせて他の音を下げる)
tt = np.arange(N) / SR
kenv = np.zeros(N)
for tk in kick_times:
    i = int(tk * SR)
    seg = np.exp(-np.arange(min(N - i, SR // 2)) / SR / 0.15)
    kenv[i:i + len(seg)] = np.maximum(kenv[i:i + len(seg)], seg)
duck = 1 - 0.55 * kenv
L = drums + (bass + pad) * duck + arpL * duck + leadL + fx
R = drums + (bass + pad) * duck + arpR * duck + leadR + np.roll(fx, 300)
mix = np.stack([L, R], 1)
mix = np.tanh(mix * 1.3)
fade = np.clip((DUR - tt) / 0.8, 0, 1)
mix *= fade[:, None]
mix = mix / np.abs(mix).max() * 0.92

os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
with wave.open(os.path.join(ROOT, "out", "showcase.wav"), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())

# 映像用の特徴量(フレームごと)
mono = mix.mean(1)
frames = DUR * FPS
BANDS = 24
edges = np.geomspace(40, 12000, BANDS + 1)
freqs = np.fft.rfftfreq(4096, 1 / SR)
win = np.hanning(4096)
kf, rms, spec = [], [], []
for f in range(frames):
    c = int((f + 0.5) / FPS * SR)
    seg = mono[max(0, c - 2048):c + 2048]
    seg = np.pad(seg, (0, 4096 - len(seg)))
    mag = np.abs(np.fft.rfft(seg * win))
    row = [float(np.sqrt(np.mean(mag[(freqs >= a) & (freqs < b)] ** 2) + 1e-9)) for a, b in zip(edges[:-1], edges[1:])]
    spec.append(row)
    rms.append(float(np.sqrt(np.mean(seg ** 2))))
    tf = f / FPS
    kv = max([np.exp(-(tf - tk) / 0.14) for tk in kick_times + impact_times if tf >= tk - 1e-6] or [0])
    kf.append(float(kv))
spec = np.log1p(np.array(spec))
spec = spec / spec.max(0, keepdims=True)
rms = np.array(rms) / max(rms)
data = {"k": [round(v, 3) for v in kf], "rms": [round(float(v), 3) for v in rms],
        "spec": [[round(float(v), 3) for v in r] for r in spec]}
with open(os.path.join(os.path.dirname(__file__), "audio.js"), "w") as fh:
    fh.write("window.AUDIO=" + json.dumps(data, separators=(",", ":")) + ";\n")
print("audio ok", len(kf), "frames")
