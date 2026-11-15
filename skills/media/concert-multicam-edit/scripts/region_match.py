"""Cam 1 (A) -> Cam 2 (B) colour matching on surfaces both cameras see.

For each lighting window (+-90 s) we pool, per shared region (stage curtain + band, tent valance,
sand), the RGB histograms of both cameras (foreground spectators masked), take quantile pairs and fit
per channel a lift/gamma/gain curve  y = a + b * x**g  (weighted least squares, bounded).
That parametric form cannot invent hue shifts the way free per-channel histogram matching did.
"""
from pathlib import Path
import glob, json
import numpy as np

ROOT = Path(__file__).resolve().parent
SETS = {1: (381, 3568), 2: (4654, 6878), 3: (8169, 10737), 4: (13408, 17588)}
CROP_X = {'A': 0, 'B': 384}
Q = np.array([0.05, 0.10, 0.20, 0.35, 0.50, 0.65, 0.80, 0.90, 0.95])

# Regions in wide-crop (rendered frame) coordinates u0,u1,v0,v1; per set group; weight.
DAY = {
    'curtain': ({'A': (0.15, 0.95, 0.35, 0.70), 'B': (0.08, 0.84, 0.36, 0.70)}, 1.0),
    'valance': ({'A': (0.03, 0.72, 0.22, 0.28), 'B': (0.05, 0.42, 0.22, 0.31)}, 0.5),
    'sand':    ({'A': (0.66, 0.97, 0.87, 0.99), 'B': (0.33, 0.62, 0.88, 0.99)}, 0.7),
}
REGIONS = {1: DAY, 2: DAY,
           3: {'curtain': DAY['curtain']},
           4: {'curtain': ({'A': (0.05, 0.95, 0.10, 0.55), 'B': (0.10, 0.95, 0.33, 0.62)}, 1.0)}}


def foreground(box, score):
    x1, y1, x2, y2 = box
    h = y2 - y1
    return score >= 0.25 and ((y2 >= 0.94 and h >= 0.20 and y1 < 0.78) or (h >= 0.65 and y2 >= 0.80))


def load_people(cam):
    rows = []
    for path in sorted(glob.glob(str(ROOT / 'analysis-full' / cam / '*.people.jsonl'))):
        with open(path, encoding='utf-8') as fh:
            rows.extend(json.loads(line) for line in fh if line.strip())
    rows.sort(key=lambda r: r['frame_index'])
    return np.array([r['frame_index'] / 25 for r in rows]), rows


def region_mask(cam, box, h, w):
    u0, u1, v0, v1 = box
    x0 = (CROP_X[cam] + u0 * 3456) / 3840; x1 = (CROP_X[cam] + u1 * 3456) / 3840
    y0 = (216 + v0 * 1944) / 2160; y1 = (216 + v1 * 1944) / 2160
    m = np.zeros((h, w), bool)
    m[int(y0 * h):int(np.ceil(y1 * h)), int(x0 * w):int(np.ceil(x1 * w))] = True
    return m


def build_hists(frames_npz, cam):
    """-> time_a [N], set_id [N], {region: hist [N,3,256]}"""
    d = np.load(frames_npz)
    ta, native, frames = d['time_a'], d['native'], d['frames']
    n, h, w, _ = frames.shape
    ptimes, prow = load_people(cam)
    sid_of = np.zeros(n, int)
    for sid, (s, e) in SETS.items():
        sid_of[(ta >= s) & (ta < e)] = sid
    names = sorted({r for sid in REGIONS for r in REGIONS[sid]})
    hists = {r: np.zeros((n, 3, 256), np.int32) for r in names}
    for i in range(n):
        sid = sid_of[i]
        if not sid:
            continue
        fg = np.zeros((h, w), bool)
        k = int(np.clip(np.searchsorted(ptimes, native[i]), 1, len(ptimes) - 1))
        k = k - 1 if abs(ptimes[k - 1] - native[i]) <= abs(ptimes[k] - native[i]) else k
        if abs(ptimes[k] - native[i]) > 0.6:
            continue
        for p in prow[k]['people']:
            if foreground(p['box'], p['score']):
                bx1, by1, bx2, by2 = p['box']
                fg[int(by1 * h):int(np.ceil(by2 * h)), int(bx1 * w):int(np.ceil(bx2 * w))] = True
        for name, (boxes, _) in REGIONS[sid].items():
            m = region_mask(cam, boxes[cam], h, w) & ~fg
            if m.sum() < 60:
                continue
            px = frames[i][m]
            for c in range(3):
                hists[name][i, c] = np.bincount(px[:, c], minlength=256)
    return ta, sid_of, hists


def quantiles(hist):
    out = np.empty((3, len(Q)))
    edges = np.arange(1, 257) / 256.0
    for c in range(3):
        cdf = np.cumsum(hist[c]).astype(float)
        cdf /= max(cdf[-1], 1)
        out[c] = np.interp(Q, np.concatenate([[0], cdf]), np.concatenate([[0], edges]))
    return out


def fit_lgg(x, y, wt):
    """Weighted fit of y = a + b*x**g with bounds; returns (a, b, g)."""
    best = None
    for g in np.arange(0.6, 1.62, 0.02):
        X = np.stack([np.ones_like(x), x ** g], 1) * np.sqrt(wt)[:, None]
        a, b = np.linalg.lstsq(X, y * np.sqrt(wt), rcond=None)[0]
        a, b = float(np.clip(a, -0.06, 0.08)), float(np.clip(b, 0.6, 1.6))
        err = float((wt * (a + b * x ** g - y) ** 2).sum())
        if best is None or err < best[0]:
            best = (err, a, b, float(g))
    return best[1:]


class RegionMatcher:
    def __init__(self, frames_dir=ROOT / 'color-frames', window=90.0, cache=ROOT / 'color-frames' / 'region_hists.npz'):
        cache = Path(cache)
        if cache.exists():
            z = np.load(cache, allow_pickle=True)
            self.data = z['data'].item()
        else:
            self.data = {cam: build_hists(Path(frames_dir) / f'{cam}.npz', cam) for cam in 'AB'}
            np.savez_compressed(cache, data=np.array(self.data, dtype=object))
        self.window = window

    def params(self, t, sid):
        xs, ys, ws = [[], [], []], [[], [], []], [[], [], []]
        w = self.window
        for name, (_, weight) in REGIONS[sid].items():
            pooled = {}
            for cam in 'AB':
                ta, sids, hists = self.data[cam]
                sel = (sids == sid) & (np.abs(ta - t) <= w)
                pooled[cam] = hists[name][sel].sum(0)
            if min(pooled['A'].sum(), pooled['B'].sum()) < 3 * 2000:
                continue
            qa, qb = quantiles(pooled['A']), quantiles(pooled['B'])
            for c in range(3):
                ok = (qa[c] < 0.985) & (qb[c] < 0.985)           # clipped values carry no information
                xs[c] += list(qa[c][ok]); ys[c] += list(qb[c][ok]); ws[c] += [weight] * int(ok.sum())
        if min(len(v) for v in xs) < 5:
            return None
        return [fit_lgg(np.array(xs[c]), np.array(ys[c]), np.array(ws[c])) for c in range(3)]

    def curves(self, t, sid):
        prm = self.params(t, sid)
        w = self.window
        while prm is None and w < 900:          # widen if this moment has too little usable data
            self.window *= 1.5; prm = self.params(t, sid); w = self.window
        self.window = 90.0
        if prm is None:
            return None
        xs = np.array([0, 0.05, 0.1, 0.2, 0.35, 0.5, 0.65, 0.8, 0.9, 1.0])
        out = {}
        for ch, (a, b, g) in zip('rgb', prm):
            y = np.clip(a + b * xs ** g, 0, 1)
            y = np.maximum.accumulate(y)
            out[ch] = [[float(x), round(float(v), 4)] for x, v in zip(xs, y)]
        return out, prm
