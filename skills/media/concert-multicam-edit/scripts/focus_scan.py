"""Focus scan: per keyframe (every 0.48 s), a 32x18 tile map of fine vs coarse gradient energy.

Fine = squared gradients of the 1080p luma, coarse = same after 4x box downscale. Their ratio drops when
the picture is defocused and does not depend on brightness/contrast.
python focus_scan.py CAM -> focus/CAM.npz (time_a, native, fine[N,18,32], coarse[N,18,32], luma[N,18,32])
"""
from pathlib import Path
import re, subprocess, sys
import numpy as np
import color_stats as cs

W, H, T = 1920, 1080, 60


def tiles(a, t):
    h, w = a.shape
    return a.reshape(h // t, t, w // t, t).sum((1, 3))


def measure(gray):
    a = gray.astype(np.float32)
    gx = np.zeros_like(a); gy = np.zeros_like(a)
    gx[:, :-1] = a[:, 1:] - a[:, :-1]
    gy[:-1] = a[1:] - a[:-1]
    fine = tiles(gx * gx + gy * gy, T)
    b = a.reshape(H // 4, 4, W // 4, 4).mean((1, 3))
    bx = np.zeros_like(b); by = np.zeros_like(b)
    bx[:, :-1] = b[:, 1:] - b[:, :-1]
    by[:-1] = b[1:] - b[:-1]
    coarse = tiles(bx * bx + by * by, T // 4)
    return fine, coarse, tiles(a, T) / (T * T)


def scan(cam, native_start, native_end, out):
    for name, f0, f1 in cs.FILES[cam]:
        a, b = max(native_start, f0), min(native_end, f1)
        if a >= b:
            continue
        log = cs.ROOT / 'focus' / f'{cam}_{int(a)}.log'
        cmd = [str(cs.FF), '-hide_banner', '-nostdin', '-loglevel', 'info', '-skip_frame', 'nokey',
               '-ss', f'{a - f0:.3f}', '-t', f'{b - a:.3f}', '-copyts', '-i', str(cs.BASE / name), '-an',
               '-vf', f'scale={W}:{H}:flags=area,format=gray,showinfo',
               '-fps_mode', 'passthrough', '-f', 'rawvideo', '-']
        rows = []
        with open(log, 'wb') as err:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=err, bufsize=W * H * 4)
            while True:
                buf = proc.stdout.read(W * H)
                if len(buf) < W * H:
                    break
                rows.append(measure(np.frombuffer(buf, np.uint8).reshape(H, W)))
            if proc.wait() != 0:
                raise RuntimeError(f'ffmpeg failed, see {log}')
        times = [float(m) for m in re.findall(rb'pts_time:\s*([0-9.]+)', log.read_bytes())]
        if len(times) != len(rows):
            raise RuntimeError(f'{cam} {name}: {len(rows)} frames but {len(times)} timestamps')
        for t, r in zip(times, rows):
            out.append((f0 + t, r))


def main(cam):
    (cs.ROOT / 'focus').mkdir(exist_ok=True)
    out = []
    for sid, (s, e) in cs.SETS.items():
        scan(cam, cs.to_native(cam, s) - 2, cs.to_native(cam, e) + 2, out)
        print(cam, 'set', sid, len(out), flush=True)
    native = np.array([t for t, _ in out])
    np.savez_compressed(cs.ROOT / 'focus' / f'{cam}.npz', native=native,
                        time_a=np.array([cs.to_a(cam, t) for t in native]),
                        fine=np.array([r[0] for _, r in out], np.float32),
                        coarse=np.array([r[1] for _, r in out], np.float32),
                        luma=np.array([r[2] for _, r in out], np.float32))
    print(cam, 'done', len(out), flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
