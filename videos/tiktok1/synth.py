"""シミュレーションの衝突タイミング(events.json)から効果音と音楽を合成する。素材・有料サービス不使用。"""
import json
import os
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
ev = json.load(open(os.path.join(HERE, "events.json")))
SR = 44100
DUR = ev["frames"] / ev["fps"]
N = int(SR * DUR)
rng = np.random.default_rng(3)
L, R, send = np.zeros(N), np.zeros(N), np.zeros(N)
# パッヘルベルのカノン(著作権切れ)のコード進行
CH = [[62, 66, 69], [61, 64, 69], [59, 62, 66], [57, 61, 66], [59, 62, 67], [62, 66, 69], [59, 62, 67], [61, 64, 69]]


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def add(start, sig, gain=1.0, pan=0.5, rev=0.3):
    i = int(start * SR)
    if i >= N:
        return
    j = min(N, i + len(sig))
    s = sig[: j - i] * gain
    L[i:j] += s * np.cos(pan * np.pi / 2)
    R[i:j] += s * np.sin(pan * np.pi / 2)
    send[i:j] += s * rev


def kalimba(m, dur=0.9):
    x = np.arange(int(dur * SR)) / SR
    f = hz(m)
    s = np.sin(2 * np.pi * f * x) * np.exp(-x / 0.28) + 0.4 * np.sin(4 * np.pi * f * x) * np.exp(-x / 0.07) + 0.25 * np.sin(2 * np.pi * f * 5.4 * x) * np.exp(-x / 0.02)
    return s * np.minimum(x / 0.002, 1)


def noise(dur, decay):
    n = int(dur * SR)
    return np.diff(rng.standard_normal(n), prepend=0) * np.exp(-np.arange(n) / SR / decay)


def boom(f0=50, dur=1.2, dec=0.3):
    x = np.arange(int(dur * SR)) / SR
    f = f0 + 90 * np.exp(-x / 0.04)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x / dec)


def sweep(f1, f2, dur):
    x = np.arange(int(dur * SR)) / SR
    f = f1 * (f2 / f1) ** (x / dur)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x / (dur * 0.5))


k, last = 0, -1.0
for e in ev["events"]:
    t, pan = e["t"], 0.5 + (e["x"] - 540) / 540 * 0.35
    if e["type"] == 0:
        if t - last < 0.03:
            continue
        ch = CH[(k // 8) % 8]
        m = ch[k % 3] + 12 * ((k % 6) // 3) + 12 * min(2, e["ring"] // 5)
        add(t, kalimba(m), 0.2, pan, 0.35)
        last = t
        k += 1
    elif e["type"] == 1:
        ch = CH[e["ring"] % 8]
        add(t, noise(0.5, 0.09), 0.2, 0.5, 0.5)
        add(t, boom(), 0.75, 0.5, 0.1)
        add(t, sweep(1800, 300, 0.25), 0.12, 0.5, 0.4)
        for i, m in enumerate(ch + [ch[0] + 12]):
            add(t + i * 0.02, kalimba(m + 12, 1.4), 0.22, 0.3 + 0.13 * i, 0.5)
    else:
        add(t, noise(2.2, 0.6), 0.22, 0.5, 0.5)
        add(t, boom(46, 2.0, 0.6), 0.9, 0.5, 0.1)
        for i, m in enumerate([62, 66, 69, 74, 78, 81, 86, 90]):
            add(t + i * 0.06, kalimba(m, 2.2), 0.3, 0.2 + 0.08 * i, 0.6)

# 低く続くパッド
x = np.arange(N) / SR
pad = sum(np.sin(2 * np.pi * hz(m) * x) for m in (38, 45, 50, 57)) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.2 * x) ** 2)
pad *= np.minimum(x / 0.5, 1) * (0.02 + 0.02 * x / DUR)
L += pad
R += pad
send += pad * 0.5


def reverb(sig, seed):
    r = np.random.default_rng(seed)
    n = int(1.6 * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / 0.35)
    size = 1 << int(np.ceil(np.log2(N + n)))
    out = np.fft.irfft(np.fft.rfft(sig, size) * np.fft.rfft(ir, size), size)[:N]
    return out / np.sqrt(np.sum(ir ** 2))


mix = np.stack([L + reverb(send, 1) * 0.5, R + reverb(send, 2) * 0.5], 1)
mix = np.tanh(mix * 1.6)
mix *= np.clip((DUR - x) / 0.25, 0, 1)[:, None]
mix = mix / np.abs(mix).max() * 0.93
os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
with wave.open(os.path.join(ROOT, "out", "tiktok1.wav"), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print("audio ok", round(DUR, 2), "s", k, "notes")
