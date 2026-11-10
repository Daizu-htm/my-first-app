"""48秒のサウンドトラックを波形から合成する(素材・有料サービス不使用)。
出力: out/showcase2.wav と videos/showcase2/audio.js(映像を音に同期させるためのデータ)。"""
import json
import os
import wave

import numpy as np

SR, DUR, FPS = 44100, 48, 30
N = SR * DUR
rng = np.random.default_rng(11)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")

SAW = [(k, 1 / k) for k in range(1, 7)]
SQ = [(1, 1), (3, 0.33), (5, 0.2), (7, 0.14)]
SOFT = [(1, 1), (2, 0.3), (3, 0.1)]
BELL = [(1, 1), (2.76, 0.35), (5.4, 0.15)]
count = 0


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
    global count
    count += 1
    i = int(start * SR)
    if i >= N or i < 0:
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


def boom(dur=2.5):
    x = np.arange(int(dur * SR)) / SR
    return np.sin(2 * np.pi * 46 * x) * np.exp(-x / 0.5)


PROG = [(45, [57, 60, 64]), (41, [53, 57, 60]), (48, [60, 64, 67]), (43, [55, 59, 62])]
DRUM = set(range(6, 14)) | {18, 19, 20, 21, 22}
BACK = set(range(10, 14)) | {20, 21, 22}
BASS = set(range(6, 14)) | {20, 21, 22}

drums, bass, pad, fx, bell = (np.zeros(N) for _ in range(5))
arpL, arpR, leadL, leadR = (np.zeros(N) for _ in range(4))
kick_times = []
impacts = [0.5, 1.5, 2.5, 4.0, 12.0, 20.0, 28.0, 40.0, 46.0]
K = kick()

for b in range(24):
    t0 = 2.0 * b
    root, ch = PROG[b % 4]
    # パッド(風景の場面でだんだん大きく)
    if b < 23:
        pg = 0.03 + 0.03 * min(1, b / 5)
        for m in ch + [ch[0] + 12, ch[0] - 12]:
            for det in (-0.09, 0, 0.09):
                s = tone(m, 2.4, SOFT, det=det)
                x = np.arange(len(s)) / SR
                add(pad, t0, s * np.minimum(x / 0.4, 1) * np.minimum((2.4 - x) / 0.4, 1), pg)
    # 風景: やわらかい分散和音と低音
    if 2 <= b <= 5:
        seq = [ch[0], ch[2], ch[1] + 12, ch[2], ch[0] + 12, ch[2], ch[1] + 12, ch[2] + 12]
        for i, m in enumerate(seq):
            s = tone(m, 0.7, SOFT)
            add(arpL if i % 2 else arpR, t0 + i * 0.25, s * env(len(s), 0.005, 0.28), 0.07 + 0.012 * (b - 2))
        s = tone(root - 12, 2.0, [(1, 1), (2, 0.2)])
        x = np.arange(len(s)) / SR
        add(bass, t0, s * np.minimum(x / 0.2, 1) * np.minimum((2.0 - x) / 0.3, 1), 0.22)
        if b >= 4:
            add(drums, t0, K, 0.5)
            add(drums, t0 + 1.0, K, 0.5)
            kick_times += [t0, t0 + 1.0]
    # アルペジオ(16分音符)
    if 6 <= b <= 22:
        seq = [ch[0], ch[1], ch[2], ch[0] + 12, ch[2], ch[1], ch[0] + 12, ch[2] + 12] * 2
        g = 0.055 if 14 <= b <= 19 else 0.1
        for i, m in enumerate(seq):
            s = tone(m + 12, 0.3, SQ)
            s = s * env(len(s), 0.004, 0.11)
            tt = t0 + i * 0.125
            add(arpL if i % 2 == 0 else arpR, tt, s, g)
            add(arpR if i % 2 == 0 else arpL, tt + 0.375, s, g * 0.35)
            add(arpL if i % 2 == 0 else arpR, tt + 0.75, s, g * 0.15)
    # ドラムとベース
    if b in DRUM:
        for q in range(4):
            tb = t0 + q * 0.5
            add(drums, tb, K, 0.95)
            kick_times.append(tb)
            add(drums, tb + 0.25, noise(0.08, 0.025), 0.13)
            if b in BACK:
                add(drums, tb + 0.125, noise(0.05, 0.012), 0.05)
                add(drums, tb + 0.375, noise(0.05, 0.012), 0.05)
                if q in (1, 3):
                    add(drums, tb, snare(), 0.5)
    if b in BASS:
        for i in range(8):
            s = tone(root - 12 if i % 2 == 0 else root, 0.26, SAW)
            add(bass, t0 + i * 0.25, s * env(len(s), 0.005, 0.16), 0.2)
    # 銀河: ベルの旋律
    if 14 <= b <= 17:
        for i, m in enumerate([ch[2] + 24, ch[1] + 24, ch[0] + 24, ch[1] + 24]):
            s = tone(m, 1.6, BELL)
            add(bell, t0 + i * 0.5, s * env(len(s), 0.003, 0.5), 0.07)
    # コードの場面: タイプ音
    if b in (18, 19):
        for i in range(16):
            add(fx, t0 + i * 0.125, noise(0.03, 0.006), 0.06)

# リード
PH1 = [(76, 0, 1), (79, 1, .5), (81, 1.5, 1.5), (79, 3, .5), (76, 3.5, .5), (77, 4, 1), (76, 5, .5), (72, 5.5, 1.5), (74, 7, 1)]
PH2 = [(79, 0, 1), (84, 1, .5), (83, 1.5, 1.5), (79, 3, 1), (74, 4, 1), (79, 5, .5), (83, 5.5, 1.5), (81, 7, 1)]
PH3 = [(79, 0, 1), (84, 1, .5), (83, 1.5, 1.5), (79, 3, 1)]
for start, ph in ((20, PH1), (24, PH2), (40, PH1), (44, PH3)):
    for m, beat, dur in ph:
        s = tone(m, dur * 0.5 + 0.25, SQ, vib=0.25)
        s = s * env(len(s), 0.02, dur * 0.5)
        tt = start + beat * 0.5
        add(leadL, tt, s, 0.085)
        add(leadR, tt + 0.01, s, 0.085)
        add(leadR, tt + 0.375, s, 0.03)
        add(leadL, tt + 0.75, s, 0.015)

# インパクト
for ti in impacts:
    big = ti >= 12 and ti != 28.0
    add(fx, ti, noise(2.5, 0.7), 0.16 if big else 0.07)
    add(fx, ti, boom(), 0.6 if big else 0.45)


def riser(start, dur, gain):
    x = np.arange(int(dur * SR)) / SR
    sweep = np.sin(2 * np.pi * np.cumsum(200 * (10 ** (x / dur))) / SR)
    add(fx, start, (rng.standard_normal(len(x)) * 0.5 + sweep * 0.5) * (x / dur) ** 2, gain)


riser(3, 1, 0.12)
riser(10, 2, 0.12)
riser(34, 2, 0.2)
riser(38, 2, 0.22)
for i in range(8):
    add(drums, 38 + i * 0.125, snare(), 0.15 + 0.03 * i)
for i in range(16):
    add(drums, 39 + i * 0.0625, snare(), 0.3 + 0.02 * i)
# 最後の和音
for m in (33, 45, 57, 60, 64, 71, 76):
    s = tone(m, 2.0, SOFT)
    add(pad, 46, s * env(len(s), 0.01, 0.9), 0.09)

# サイドチェイン
tt = np.arange(N) / SR
kenv = np.zeros(N)
for tk in kick_times:
    i = int(tk * SR)
    seg = np.exp(-np.arange(min(N - i, SR // 2)) / SR / 0.15)
    kenv[i:i + len(seg)] = np.maximum(kenv[i:i + len(seg)], seg)
duck = 1 - 0.55 * kenv
L = drums + (bass + pad) * duck + arpL * duck + leadL + fx + bell
R = drums + (bass + pad) * duck + arpR * duck + leadR + np.roll(fx, 300) + np.roll(bell, 200)

# リバーブ(減衰するノイズとの畳み込み)
def reverb(sig, seed):
    r = np.random.default_rng(seed)
    n = int(1.8 * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / 0.42)
    size = 1 << int(np.ceil(np.log2(N + n)))
    out = np.fft.irfft(np.fft.rfft(sig, size) * np.fft.rfft(ir, size), size)[:N]
    return out / np.sqrt(np.sum(ir ** 2))


sendL = pad * 0.5 + arpL * 0.6 + leadL * 0.6 + fx * 0.3 + bell
sendR = pad * 0.5 + arpR * 0.6 + leadR * 0.6 + fx * 0.3 + bell
L = L + reverb(sendL, 1) * 0.28
R = R + reverb(sendR, 2) * 0.28

mix = np.tanh(np.stack([L, R], 1) * 1.25)
mix *= np.clip((DUR - tt) / 0.8, 0, 1)[:, None]
mix = mix / np.abs(mix).max() * 0.92

os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
with wave.open(os.path.join(ROOT, "out", "showcase2.wav"), "wb") as w:
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
hits = np.array(kick_times + impacts)
kf, spec, wav = [], [], []
for f in range(frames):
    c = int((f + 0.5) / FPS * SR)
    seg = mono[max(0, c - 2048):c + 2048]
    seg = np.pad(seg, (0, 4096 - len(seg)))
    mag = np.abs(np.fft.rfft(seg * win))
    spec.append([float(np.sqrt(np.mean(mag[(freqs >= a) & (freqs < b)] ** 2) + 1e-9)) for a, b in zip(edges[:-1], edges[1:])])
    tf = f / FPS
    past = hits[hits <= tf + 1e-6]
    kf.append(float(np.exp(-(tf - past.max()) / 0.14)) if len(past) else 0.0)
    w0 = int(f / FPS * SR)
    wav.append([round(float(v), 2) for v in mono[w0:w0 + 1470:15][:96]])
spec = np.log1p(np.array(spec))
spec = spec / spec.max(0, keepdims=True)
data = {"k": [round(v, 3) for v in kf], "spec": [[round(float(v), 3) for v in r] for r in spec], "wave": wav, "notes": count}
with open(os.path.join(HERE, "audio.js"), "w") as fh:
    fh.write("window.AUDIO=" + json.dumps(data, separators=(",", ":")) + ";\n")
print("audio ok", frames, "frames", count, "sounds")
