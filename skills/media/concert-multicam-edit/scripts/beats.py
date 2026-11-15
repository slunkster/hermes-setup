"""Beat, downbeat and quiet-span analysis of the continuous A-camera audio per set.
Output times are A-global seconds."""
from pathlib import Path
import json, subprocess, sys
import numpy as np
import librosa

ROOT = Path(__file__).resolve().parent
FF = Path.home() / 'AppData/Local/hermes/tools/ffmpeg-9.0.1-win32-x64/bin/ffmpeg.exe'
BASE = Path('G:/Active Media/Blues Fest')
SPLIT = 11040.48
SETS = {1: (381, 3568), 2: (4654, 6878), 3: (8169, 10737), 4: (13408, 17588)}
SR, HOP = 22050, 512


def load(start, end):
    if start < SPLIT <= end:
        raise ValueError('set crosses A split; not expected for Day 1')
    src = BASE / ('A089C001_260904_DJ0B.MOV' if start < SPLIT else 'A089C002_260904_DJ0B.MOV')
    local = start if start < SPLIT else start - SPLIT
    cmd = [str(FF), '-hide_banner', '-loglevel', 'error', '-nostdin', '-ss', f'{local:.6f}', '-i', str(src),
           '-t', f'{end - start:.6f}', '-map', '0:a:0', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    y = np.frombuffer(raw, dtype=np.float32)
    expected = int(round((end - start) * SR))
    if abs(len(y) - expected) > SR // 10:
        raise RuntimeError(f'decoded {len(y)} samples, expected ~{expected}')
    return y


def quiet_spans(y):
    rms = librosa.feature.rms(y=y, hop_length=HOP)[0]
    step = SR / HOP
    win = int(4 * step)
    smooth = np.convolve(rms, np.ones(win) / win, mode='same')
    quiet = smooth < 0.5 * np.median(rms)
    spans, i = [], 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]:
                j += 1
            if (j - i) / step >= 4:
                spans.append([i / step, j / step])
            i = j
        else:
            i += 1
    return spans


def analyse(sid):
    start, end = SETS[sid]
    y = load(start, end)
    onset = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP)
    tempo, beats = librosa.beat.beat_track(onset_envelope=onset, sr=SR, hop_length=HOP,
                                           units='time', tightness=100)
    beats = np.asarray(beats, dtype=float)
    frames = np.clip(np.round(beats * SR / HOP).astype(int), 0, len(onset) - 1)
    strength = onset[frames]
    spans = quiet_spans(y)
    # Music segments between quiet spans; choose the downbeat phase per segment.
    edges = [0.0] + [v for s in spans for v in s] + [end - start]
    segments = [(edges[k], edges[k + 1]) for k in range(0, len(edges), 2)]
    downbeats = []
    for a, b in segments:
        idx = np.where((beats >= a) & (beats < b))[0]
        if len(idx) < 8:
            continue
        phase = max(range(4), key=lambda p: strength[idx[p::4]].sum())
        downbeats.extend(beats[idx[phase::4]].tolist())
    ibi = np.diff(beats)
    result = {'set_id': sid, 'tempo_bpm': float(np.atleast_1d(tempo)[0]), 'beat_count': int(len(beats)),
              'ibi_p10_p50_p90': np.percentile(ibi, [10, 50, 90]).round(3).tolist() if len(ibi) else [],
              'beats': (beats + start).round(4).tolist(),
              'downbeats': (np.asarray(downbeats) + start).round(4).tolist(),
              'quiet_spans': [[round(a + start, 3), round(b + start, 3)] for a, b in spans],
              'music_segments': [[round(a + start, 3), round(b + start, 3)] for a, b in segments]}
    print(json.dumps({k: v for k, v in result.items() if k not in ('beats', 'downbeats')}), flush=True)
    return result


if __name__ == '__main__':
    ids = [int(a) for a in sys.argv[1:]] or [1, 2, 3, 4]
    out = {str(sid): analyse(sid) for sid in ids}
    (ROOT / 'beats.json').write_text(json.dumps(out), encoding='utf-8')
    print('wrote', ROOT / 'beats.json')
