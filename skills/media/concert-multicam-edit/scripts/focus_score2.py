"""Focus score v2: per-tile fine/coarse ratio relative to the SAME tile's sharp level in the set
(static stage detail: LED bars, drum kit, truss), median over the textured stage tiles.
Foreground spectators are masked; a passing head only disturbs a few tiles, the median ignores it.
Output focus/score.npz: {cam}_time, {cam}_rel (1.0 = as sharp as this camera gets in this set), {cam}_set."""
from pathlib import Path
import numpy as np
import region_match as rm
from focus_score import SETS, STAGE, TH, TW, box_mask

ROOT = Path(__file__).resolve().parent


def camera(cam):
    z = np.load(ROOT / 'focus' / f'{cam}.npz')
    native, ta, fine, coarse = z['native'], z['time_a'], z['fine'], z['coarse']
    ptimes, prow = rm.load_people(cam)
    x0, y0, x1, y1 = STAGE[cam]
    stage = box_mask(x0, y0, x1, min(y1, 0.72))
    ratio = fine / (coarse + 1.0)
    fg = np.zeros(ratio.shape, bool)
    for i, t in enumerate(native):
        k = int(np.clip(np.searchsorted(ptimes, t), 1, len(ptimes) - 1))
        k = k - 1 if abs(ptimes[k - 1] - t) <= abs(ptimes[k] - t) else k
        if abs(ptimes[k] - t) <= 0.6:
            for p in prow[k]['people']:
                if rm.foreground(p['box'], p['score']):
                    fg[i] |= box_mask(*p['box'])
    rel = np.full(len(ta), np.nan); sid_of = np.zeros(len(ta), int)
    for sid, (s, e) in SETS.items():
        sel = np.where((ta >= s - 2) & (ta < e + 2))[0]
        sid_of[sel] = sid
        r = np.where(fg[sel], np.nan, ratio[sel])
        weight = np.nanmedian(np.where(fg[sel], np.nan, coarse[sel]), 0)
        cand = stage & np.isfinite(weight)
        thr = np.percentile(weight[cand], 60)
        use = cand & (weight >= thr)
        base = np.nanpercentile(r[:, use], 80, axis=0)
        tile_rel = r[:, use] / base
        enough = np.isfinite(tile_rel).sum(1) >= max(8, int(0.4 * use.sum()))
        sc = np.where(enough, np.nanmedian(tile_rel, 1), np.nan)
        rel[sel] = sc / np.nanpercentile(sc, 80)
        q = rel[sel]
        print(f'{cam} set {sid}: tiles {use.sum()} valid {enough.mean():.0%} rel p1/p5/p20/p50 {np.nanpercentile(q, [1, 5, 20, 50]).round(2)} '
              f'<0.8: {np.nanmean(q < 0.8):.1%} <0.65: {np.nanmean(q < 0.65):.1%}')
    return ta, rel, sid_of


if __name__ == '__main__':
    store = {}
    for cam in 'AB':
        store[f'{cam}_time'], store[f'{cam}_rel'], store[f'{cam}_set'] = camera(cam)
    np.savez_compressed(ROOT / 'focus' / 'score.npz', **store)
    for cam, ts in (('A', (2886, 2631, 2764, 2074, 9156, 8785, 8302)), ('B', (3320, 1560, 1440, 1453))):
        t, r = store[f'{cam}_time'], store[f'{cam}_rel']
        print(cam, [(x, round(float(np.nanmedian(r[np.abs(t - x) < 1.5])), 2)) for x in ts])
