"""Colour statistics for camera matching.

Decodes keyframes only (GOP = 12 frames = 0.48 s), keeps every Nth, converts exactly like the
renderer does (BT.709, tv range -> RGB) at 480x270, and stores per-sample RGB histograms of the
shared stage region with foreground spectators masked out (from analysis/*.people.jsonl).
Output: color-stats/{A,B}.npz with time_a (A-global seconds), hist [N,3,256], full_mean [N,3].
"""
from pathlib import Path
import json, re, subprocess, sys, glob
import numpy as np

ROOT = Path(__file__).resolve().parent
FF = Path.home() / 'AppData/Local/hermes/tools/ffmpeg-9.0.1-win32-x64/bin/ffmpeg.exe'
BASE = Path('G:/Active Media/Blues Fest')
SETS = {1: (381, 3568), 2: (4654, 6878), 3: (8169, 10737), 4: (13408, 17588)}
FILES = {'A': (('A089C001_260904_DJ0B.MOV', 0.0, 11040.48), ('A089C002_260904_DJ0B.MOV', 11040.48, 1e9)),
         'B': (('S1310001.MP4', 0.0, 11040.96), ('S1310002.MP4', 11040.96, 1e9))}
ROI = {'A': (0.10, 0.30, 0.86, 0.78), 'B': (0.18, 0.30, 0.98, 0.78)}
W, H = 480, 270
EVERY = int(sys.argv[2]) if len(sys.argv) > 2 else 5
sync = json.loads((ROOT / 'sync_model.json').read_text())


def to_native(cam, t):
    return t if cam == 'A' else t - (sync['intercept_seconds'] + sync['slope'] * t)


def to_a(cam, native):
    return native if cam == 'A' else (native + sync['intercept_seconds']) / (1 - sync['slope'])


def foreground(box, score):
    x1, y1, x2, y2 = box
    h = y2 - y1
    return score >= 0.25 and ((y2 >= 0.94 and h >= 0.20 and y1 < 0.78) or (h >= 0.65 and y2 >= 0.80))


def load_people(cam):
    rows = []
    for path in sorted(glob.glob(str(ROOT / 'analysis' / cam / '*.people.jsonl'))):
        with open(path, encoding='utf-8') as fh:
            rows.extend(json.loads(line) for line in fh if line.strip())
    rows.sort(key=lambda r: r['frame_index'])
    return np.array([r['frame_index'] / 25 for r in rows]), rows


def decode(cam, native_start, native_end):
    """Yield (native_seconds, rgb) for kept keyframes in [start, end) of one camera."""
    for name, f0, f1 in FILES[cam]:
        a, b = max(native_start, f0), min(native_end, f1)
        if a >= b:
            continue
        log = ROOT / 'color-stats' / f'{cam}_{int(a)}.log'
        cmd = [str(FF), '-hide_banner', '-nostdin', '-loglevel', 'info', '-skip_frame', 'nokey',
               '-ss', f'{a - f0:.3f}', '-t', f'{b - a:.3f}', '-copyts', '-i', str(BASE / name), '-an',
               '-vf', f"select='not(mod(n\\,{EVERY}))',scale={W}:{H}:flags=area:in_color_matrix=bt709:"
                      "in_range=tv,format=rgb24,showinfo",
               '-fps_mode', 'passthrough', '-f', 'rawvideo', '-']
        with open(log, 'wb') as err:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=err, check=True)
        frames = np.frombuffer(proc.stdout, np.uint8).reshape(-1, H, W, 3)
        times = [float(m) for m in re.findall(rb'pts_time:\s*([0-9.]+)', log.read_bytes())]
        if len(times) != len(frames):
            raise RuntimeError(f'{cam} {name}: {len(frames)} frames but {len(times)} timestamps')
        for t, rgb in zip(times, frames):
            yield f0 + t, rgb


def main(cam):
    (ROOT / 'color-stats').mkdir(exist_ok=True)
    ptimes, prow = load_people(cam)
    x1, y1, x2, y2 = ROI[cam]
    base_mask = np.zeros((H, W), bool)
    base_mask[int(y1 * H):int(y2 * H), int(x1 * W):int(x2 * W)] = True
    out_t, out_h, out_m, out_n = [], [], [], []
    for sid, (s, e) in SETS.items():
        for native, rgb in decode(cam, to_native(cam, s) - 2, to_native(cam, e) + 2):
            mask = base_mask.copy()
            k = int(np.clip(np.searchsorted(ptimes, native), 1, len(ptimes) - 1))
            k = k - 1 if abs(ptimes[k - 1] - native) <= abs(ptimes[k] - native) else k
            if abs(ptimes[k] - native) <= 0.6:
                for p in prow[k]['people']:
                    if foreground(p['box'], p['score']):
                        bx1, by1, bx2, by2 = p['box']
                        mask[int(by1 * H):int(np.ceil(by2 * H)), int(bx1 * W):int(np.ceil(bx2 * W))] = False
            else:
                mask[:] = False       # no detections nearby: do not trust this sample
            px = rgb[mask]
            hist = np.stack([np.bincount(px[:, c], minlength=256) for c in range(3)]) if len(px) else np.zeros((3, 256), int)
            out_t.append(to_a(cam, native)); out_h.append(hist.astype(np.int32))
            out_m.append(rgb.reshape(-1, 3).mean(0)); out_n.append(len(px))
        print(cam, 'set', sid, 'samples so far', len(out_t), flush=True)
    np.savez_compressed(ROOT / 'color-stats' / f'{cam}.npz', time_a=np.array(out_t), hist=np.array(out_h),
                        full_mean=np.array(out_m), roi_pixels=np.array(out_n))
    print(cam, 'done', len(out_t))


if __name__ == '__main__':
    main(sys.argv[1])
