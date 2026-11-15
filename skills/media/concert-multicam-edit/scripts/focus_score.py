"""Focus score per camera from focus/CAM.npz + person detections.

score(t) = fine/coarse gradient energy over the tiles where the performers are (non-foreground person
boxes inside the stage region; falls back to the whole stage region), relative to that camera's own
sharp level in the same set (80th percentile). 1.0 = as sharp as this camera gets, lower = softer.
Output focus/score.npz: for each cam time_a, rel, set_id.
"""
from pathlib import Path
import json
import numpy as np
import region_match as rm          # load_people, foreground

ROOT = Path(__file__).resolve().parent
SETS = {1: (381, 3568), 2: (4654, 6878), 3: (8169, 10737), 4: (13408, 17588)}
STAGE = {'A': (0.10, 0.30, 0.86, 0.78), 'B': (0.18, 0.30, 0.98, 0.78)}
TH, TW = 18, 32


def box_mask(x1, y1, x2, y2):
    m = np.zeros((TH, TW), bool)
    m[int(y1 * TH):max(int(np.ceil(y2 * TH)), int(y1 * TH) + 1), int(x1 * TW):max(int(np.ceil(x2 * TW)), int(x1 * TW) + 1)] = True
    return m


def raw_scores(cam):
    z = np.load(ROOT / 'focus' / f'{cam}.npz')
    d = {k: z[k] for k in ('native', 'time_a', 'fine', 'coarse')}   # npz re-decompresses on every access
    ptimes, prow = rm.load_people(cam)
    stage = box_mask(*[STAGE[cam][i] for i in (0, 1, 2, 3)])
    out = np.full(len(d['native']), np.nan)
    used_people = np.zeros(len(out), bool)
    for i, t in enumerate(d['native']):
        fine, coarse = d['fine'][i], d['coarse'][i]
        k = int(np.clip(np.searchsorted(ptimes, t), 1, len(ptimes) - 1))
        k = k - 1 if abs(ptimes[k - 1] - t) <= abs(ptimes[k] - t) else k
        perf = np.zeros((TH, TW), bool); fg = np.zeros((TH, TW), bool)
        if abs(ptimes[k] - t) <= 0.6:
            for p in prow[k]['people']:
                b = p['box']
                if rm.foreground(b, p['score']):
                    fg |= box_mask(*b)
                elif p['score'] >= 0.3:
                    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
                    if STAGE[cam][0] <= cx <= STAGE[cam][2] and STAGE[cam][1] <= cy <= STAGE[cam][3]:
                        perf |= box_mask(*b)
        m = perf & stage & ~fg
        if m.sum() >= 4:
            used_people[i] = True
        else:
            m = stage & ~fg
        if m.sum() < 4 or coarse[m].sum() <= 0:
            continue
        out[i] = fine[m].sum() / coarse[m].sum()
    return d['time_a'], out, used_people


def main():
    store = {}
    for cam in 'AB':
        ta, raw, used = raw_scores(cam)
        rel = np.full(len(raw), np.nan); sid_of = np.zeros(len(raw), int)
        for sid, (s, e) in SETS.items():
            sel = (ta >= s - 2) & (ta < e + 2)
            sid_of[sel] = sid
            base = np.nanpercentile(raw[sel], 80)
            rel[sel] = raw[sel] / base
            r = rel[sel]
            print(f'{cam} set {sid}: n={sel.sum()} base={base:.3f} people-tiles {used[sel].mean():.0%} '
                  f'rel p1/p5/p20/p50 = {np.nanpercentile(r, [1, 5, 20, 50]).round(2)}  <0.7: {np.nanmean(r < 0.7):.1%}  <0.5: {np.nanmean(r < 0.5):.1%}')
        store[f'{cam}_time'], store[f'{cam}_rel'], store[f'{cam}_raw'], store[f'{cam}_set'] = ta, rel, raw, sid_of
    np.savez_compressed(ROOT / 'focus' / 'score.npz', **store)


if __name__ == '__main__':
    main()
