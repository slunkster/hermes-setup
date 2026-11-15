"""v3 edit planner: weighted stage-visibility scores + optimal (DP) camera selection.

Inputs (all A-global time, 25 fps):
  analysis-full/{A,B}/*.people.jsonl   detector samples (native frames)
  plan-all/scored_timeline.npz          per-frame motion_a / motion_b (A-global)
  sync_model.json                       B -> A mapping
  beats.json                            beats / downbeats / quiet spans (optional)
Output: plan-v3/plan.json in the render_v2 schema, plus plan-v3/scores.npz and stats.
"""
from pathlib import Path
import argparse, glob, json
import numpy as np

FPS = 25
STEP = 12                      # frames per DP step (= detector sample interval, 0.48 s)
SETS = {1: ('Autt of Office', 9525, 89200), 2: ('Kapten Jack', 116350, 171950),
        3: ('Multifunk', 204225, 268425), 4: ('Louie Digman & Heiki Vilep', 335200, 439700)}
STAGE_X = {'A': (0.10, 0.86), 'B': (0.18, 0.98)}
BANDS = ((0.34, 0.60, 1.0), (0.60, 0.74, 0.4))   # performer heads/torsos weigh most
GW, GH = 160, 90


def foreground(box, score):
    x1, y1, x2, y2 = box
    h = y2 - y1
    return score >= 0.25 and ((y2 >= 0.94 and h >= 0.20 and y1 < 0.78) or (h >= 0.65 and y2 >= 0.80))


def weight_map(camera, crop=None):
    w = np.zeros((GH, GW))
    x_lo, x_hi = STAGE_X[camera]
    y_cut = 1.0
    if crop is not None:                      # only what the punch-in actually shows matters
        x_lo, x_hi = max(x_lo, crop[0] / 3840), min(x_hi, (crop[0] + crop[2]) / 3840)
        y_cut = (crop[1] + crop[3]) / 2160
    xs = slice(int(x_lo * GW), int(np.ceil(x_hi * GW)))
    for top, bottom, weight in BANDS:
        w[int(top * GH):int(np.ceil(min(bottom, y_cut) * GH)), xs] = weight
    return w


def sample_scores(rows, camera, crop=None):
    w = weight_map(camera, crop)
    total = w.sum()
    out = np.empty(len(rows))
    for i, row in enumerate(rows):
        mask = np.zeros((GH, GW), bool)
        for p in row['people']:
            if foreground(p['box'], p['score']):
                x1, y1, x2, y2 = p['box']
                mask[int(y1 * GH):int(np.ceil(y2 * GH)), int(x1 * GW):int(np.ceil(x2 * GW))] = True
        out[i] = (w * mask).sum() / total
    return out


def load_camera(root, camera, sync):
    rows = []
    for path in sorted(glob.glob(str(root / camera / '*.people.jsonl'))):
        with open(path, encoding='utf-8') as fh:
            rows.extend(json.loads(line) for line in fh if line.strip())
    rows.sort(key=lambda r: r['frame_index'])
    native = np.array([r['frame_index'] for r in rows], float) / FPS
    if camera == 'B':
        t = (native + sync['intercept_seconds']) / (1 - sync['slope'])
    else:
        t = native
    return t * FPS, sample_scores(rows, camera), rows


TIGHT_SIZES = ((2560, 1440), (2880, 1620))   # 1.5x / 1.33x of full frame; both still downscale to 1080p
# Set 4 (night, standing crowd): auto-framing is contaminated by audience boxes, so the punch-ins were
# framed by hand from inspected frames (13622.96 s A, 15723.84 s B) around both performers.
TIGHT_OVERRIDE = {4: {'A': [828, 560, 2560, 1440], 'B': [1280, 720, 2560, 1440]}}


def tight_crop(rows, frames, start, end, camera):
    """Auto-frame a punch-in around where the performers actually stand during this set."""
    x_lo, x_hi = STAGE_X[camera]
    x1s, x2s, y1s, y2s = [], [], [], []
    for row, f in zip(rows, frames):
        if not start <= f < end:
            continue
        for p in row['people']:
            bx1, by1, bx2, by2 = p['box']
            cx, h = (bx1 + bx2) / 2, by2 - by1
            if (p['score'] >= 0.4 and not foreground(p['box'], p['score']) and x_lo <= cx <= x_hi
                    and 0.55 <= by2 <= 0.92 and 0.12 <= h <= 0.55):
                x1s.append(bx1); x2s.append(bx2); y1s.append(by1); y2s.append(by2)
    if len(x1s) < 200:
        return None
    left, right = np.percentile(x1s, 3) * 3840, np.percentile(x2s, 97) * 3840
    top, bottom = np.percentile(y1s, 3) * 2160, np.percentile(y2s, 97) * 2160
    for w, h in TIGHT_SIZES:
        mx, my = 0.04 * w, 0.06 * h
        if right - left + 2 * mx <= w and bottom - top + 2 * my <= h:
            x = min(max(0, (left + right) / 2 - w / 2), 3840 - w)
            y = min(max(0, top - 2 * my), 2160 - h)          # headroom first
            if y + h < bottom + my:
                y = min(2160 - h, bottom + my - h)
            return [int(x) // 2 * 2, int(y) // 2 * 2, w, h]
    return None


def per_frame(sample_frames, values, start, end, pad_samples=3):
    """Conservative step function: rolling max over +-pad samples, nearest-sample hold."""
    k = 2 * pad_samples + 1
    padded = np.pad(values, pad_samples, mode='edge')
    rolled = np.max(np.lib.stride_tricks.sliding_window_view(padded, k), axis=1)
    frames = np.arange(start, end)
    idx = np.clip(np.searchsorted(sample_frames, frames), 1, len(sample_frames) - 1)
    left, right = sample_frames[idx - 1], sample_frames[idx]
    nearest = np.where(frames - left <= right - frames, idx - 1, idx)
    gap = np.abs(sample_frames[nearest] - frames)
    out = rolled[nearest]
    out[gap > STEP] = 1.0          # fail closed if samples are missing
    return out


def step_costs(o, motion):
    g = (o + 1.0 * np.maximum(0, o - 0.25) + 0.25 * (motion > 0.03)
         + 3.0 * (o > 0.85))           # a near-black silhouette is not an acceptable audience view
    n = int(np.ceil(len(g) / STEP))
    padded = np.pad(g, (0, n * STEP - len(g)), mode='edge')
    return padded.reshape(n, STEP).mean(axis=1)


def step_mean(v):
    n = int(np.ceil(len(v) / STEP))
    return np.pad(v, (0, n * STEP - len(v)), mode='edge').reshape(n, STEP).mean(axis=1)


def focus_blur(z, cam, start, end, sharp=0.85, soft=0.65):
    """Per-frame blur 0..1 (0 = in focus, 1 = clearly soft) from the relative focus score; unknown = 0."""
    t, rel = z[f'{cam}_time'] * FPS, z[f'{cam}_rel'].astype(float)
    ok = np.isfinite(rel)
    t, rel = t[ok], rel[ok]
    pad = np.pad(rel, 2, mode='edge')
    rel = np.median(np.lib.stride_tricks.sliding_window_view(pad, 5), axis=1)
    frames = np.arange(start, end)
    r = np.interp(frames, t, rel)
    idx = np.clip(np.searchsorted(t, frames), 1, len(t) - 1)
    gap = np.minimum(np.abs(t[idx] - frames), np.abs(t[idx - 1] - frames))
    blur = np.clip((sharp - r) / (sharp - soft), 0, 1)
    blur[gap > 3 * FPS] = 0.0
    return blur


def plan_set(sid, cost, cut_cost, params):
    lmin = int(np.ceil(params['min_shot'] * FPS / STEP))
    soft = int(params['soft_start'] * FPS / STEP)
    long_ = int(params['hard_soft'] * FPS / STEP)
    very = int(params['very_long'] * FPS / STEP)
    d_max = int(params['cap'] * FPS / STEP)
    def pen(d):
        if d < soft:
            return 0.0
        if d < long_:
            return params['pen_mid']
        if d < very:
            return params['pen_long']
        # Beyond ~45 s a short audience/other-angle cutaway becomes worthwhile even if that
        # view is partly blocked; ramps to pen_max at the cap (memoryless beyond it).
        frac = (d - very) / max(1, d_max - very)
        return params['pen_long'] + frac * (params['pen_max'] - params['pen_long'])
    pens = np.array([pen(d) for d in range(d_max + 1)])
    K, n = cost.shape
    inf = 1e18
    V = np.full((K, d_max + 1), inf)
    V[:, 1] = cost[:, 0]
    back_d = np.zeros((n, K, d_max + 1), np.int16)   # previous duration state
    back_k = np.zeros((n, K), np.int8)               # previous framing for a cut (d == 1)
    for t in range(1, n):
        W = np.full_like(V, inf)
        W[:, 2:] = V[:, 1:-1] + pens[2:]
        back_d[t, :, 2:] = np.arange(1, d_max)
        stay_cap = V[:, d_max] + pens[d_max]
        better = stay_cap < W[:, d_max]
        W[better, d_max] = stay_cap[better]
        back_d[t, better, d_max] = d_max
        best_d = np.argmin(V[:, lmin:], axis=1) + lmin
        best_v = V[np.arange(K), best_d]
        for k in range(K):
            masked = best_v.copy()
            masked[k] = inf
            src = int(np.argmin(masked))
            W[k, 1] = masked[src] + cut_cost[t]
            back_k[t, k] = src
            back_d[t, k, 1] = best_d[src]
        W += cost[:, t][:, None]
        V = W
    V[:, :lmin] = inf                                # no sub-minimum final shot
    c, d = np.unravel_index(np.argmin(V), V.shape)
    cams = np.empty(n, np.int8)
    for t in range(n - 1, -1, -1):
        cams[t] = c
        if t == 0:
            break
        if d == 1:
            c, d = int(back_k[t, c]), int(back_d[t, c, 1])
        else:
            d = int(back_d[t, c, d])
    return cams


def main():
    ap = argparse.ArgumentParser()
    root = Path(__file__).resolve().parent
    ap.add_argument('--analysis', type=Path, default=root / 'analysis-full')
    ap.add_argument('--motion', type=Path, default=root / 'plan-all/scored_timeline.npz')
    ap.add_argument('--sync', type=Path, default=root / 'sync_model.json')
    ap.add_argument('--beats', type=Path, default=root / 'beats.json')
    ap.add_argument('--out', type=Path, default=root / 'plan-v3')
    ap.add_argument('--min-shot', type=float, default=6.0)
    ap.add_argument('--soft-start', type=float, default=12.0)
    ap.add_argument('--hard-soft', type=float, default=24.0)
    ap.add_argument('--pen-mid', type=float, default=0.006)
    ap.add_argument('--pen-long', type=float, default=0.02)
    ap.add_argument('--very-long', type=float, default=45.0)
    ap.add_argument('--cap', type=float, default=90.0)
    ap.add_argument('--pen-max', type=float, default=0.15)
    ap.add_argument('--cut', type=float, default=0.12)
    ap.add_argument('--cut-downbeat', type=float, default=0.05)
    ap.add_argument('--cut-quiet', type=float, default=0.30)
    ap.add_argument('--tight-bias', type=float, default=0.012)
    ap.add_argument('--focus', type=Path, help='focus/score.npz from focus_score2.py: prefer the camera that is in focus')
    ap.add_argument('--focus-weight', type=float, default=0.6)
    ap.add_argument('--cam-bias', action='append', default=[], help='SET:CAM:COST, e.g. 2:A:0.3 when a camera is soft for a whole set')
    ap.add_argument('--no-tight', action='store_true', help='camera switches only, never punch in (user preference)')
    args = ap.parse_args()
    params = {k: getattr(args, k) for k in ('min_shot', 'soft_start', 'hard_soft', 'pen_mid', 'pen_long',
                                           'very_long', 'cap', 'pen_max')}
    sync = json.loads(args.sync.read_text())
    motion = np.load(args.motion)
    beats = json.loads(args.beats.read_text()) if args.beats.exists() else {}
    cams = {c: load_camera(args.analysis, c, sync) for c in 'AB'}
    args.out.mkdir(parents=True, exist_ok=True)
    out_sets, store = [], {}
    focus_data = np.load(args.focus) if args.focus else None
    for sid, (name, start, end) in SETS.items():
        m = motion['set_id'] == sid
        assert motion['frame_index'][m][0] == start and motion['frame_index'][m][-1] == end - 1
        o = {c: per_frame(*cams[c][:2], start, end) for c in 'AB'}
        mo = {'A': motion['motion_a'][m], 'B': motion['motion_b'][m]}
        tight = {c: TIGHT_OVERRIDE.get(sid, {}).get(c) or tight_crop(cams[c][2], cams[c][0], start, end, c)
                 for c in 'AB'}
        o_tight = {}
        for c in 'AB':
            if tight[c] is None or args.no_tight:
                continue
            frames, _, rows = cams[c]
            inside = (frames >= start - 2 * FPS) & (frames < end + 2 * FPS)
            sub_rows = [r for r, keep in zip(rows, inside) if keep]
            o_tight[c] = per_frame(frames[inside], sample_scores(sub_rows, c, tight[c]), start, end)
        # Framings: 0 A wide, 1 A tight, 2 B wide, 3 B tight. Tight carries a small bias so wide is the
        # default; it is scored only on what the punch-in shows (side silhouettes can fall outside it).
        framings = [('A', None), ('A', tight['A']), ('B', None), ('B', tight['B'])]
        cost = np.vstack([step_costs(o_tight[c] if k % 2 else o[c], mo[c]) + (args.tight_bias if k % 2 else 0.0)
                          if (k % 2 == 0 or c in o_tight) else np.full(int(np.ceil((end - start) / STEP)), 1e6)
                          for k, (c, crop) in enumerate(framings)])
        blur = {}
        if args.focus:
            for c in 'AB':
                blur[c] = focus_blur(focus_data, c, start, end)
            for k, (c, crop) in enumerate(framings):
                cost[k] += args.focus_weight * step_mean(blur[c])
        for spec in args.cam_bias:
            bs, bc, bv = spec.split(':')
            if int(bs) == sid:
                for k, (c, crop) in enumerate(framings):
                    if c == bc:
                        cost[k] += float(bv)
        n = cost.shape[1]
        b = beats.get(str(sid), {})
        cut_cost = np.full(n, args.cut)
        down = np.array(b.get('downbeats', []))
        beat_t = np.array(b.get('beats', []))
        down_step = ((down * FPS - start) // STEP).astype(int) if len(down) else np.array([], int)
        down_step = down_step[(down_step >= 0) & (down_step < n)]
        cut_cost[down_step] = args.cut_downbeat
        for a, e in b.get('quiet_spans', []):
            s0, s1 = int((a * FPS - start) // STEP), int(np.ceil((e * FPS - start) / STEP))
            cut_cost[max(0, s0):max(0, min(n, s1))] += args.cut_quiet
        for a, e in b.get('music_segments', [])[1:]:       # first downbeat of each new song: free cut
            first = down[(down >= a) & (down < a + 4)] if len(down) else []
            if len(first):
                cut_cost[int((first[0] * FPS - start) // STEP)] = 0.0
        sel = plan_set(sid, cost, cut_cost, params)
        # Shots on the step grid, then snap cuts to the downbeat/beat inside that step.
        cut_steps = np.where(np.diff(sel) != 0)[0] + 1
        cuts = []
        for s in cut_steps:
            lo, hi = start + s * STEP, start + (s + 1) * STEP
            frame = lo
            for pool in (down, beat_t):
                if len(pool):
                    f = np.round(pool * FPS).astype(int)
                    inside = f[(f >= lo) & (f < hi)]
                    if len(inside):
                        frame = int(inside[0])
                        break
            cuts.append(frame)
        edges = [start] + cuts + [end]
        shots = []
        for i in range(len(edges) - 1):
            a, e = edges[i], edges[i + 1]
            k = int(sel[min(n - 1, (a - start) // STEP)])
            cam, crop = framings[k]
            other = 'B' if cam == 'A' else 'A'
            own = o_tight[cam] if crop else o[cam]
            cam_risk = float(own[a - start:e - start].mean())
            other_risk = float(np.minimum(o[other], o_tight.get(other, o[other]))[a - start:e - start].mean())
            shot = {'start_frame': int(a), 'end_frame': int(e), 'camera': cam, 'framing': 'tight' if crop else 'wide',
                    'risk': round(cam_risk, 4), 'other_risk': round(other_risk, 4),
                    'reason': ('cutaway_partly_blocked_view' if cam_risk > other_risk + 0.1
                               else 'dp_min_visible_obstruction')}
            if crop:
                shot['crop'] = crop
            shots.append(shot)
        # Integrity checks
        assert shots[0]['start_frame'] == start and shots[-1]['end_frame'] == end
        assert all(x['end_frame'] == y['start_frame'] for x, y in zip(shots, shots[1:]))
        assert all((x['camera'], x['framing']) != (y['camera'], y['framing']) for x, y in zip(shots, shots[1:]))
        lengths = np.array([(s['end_frame'] - s['start_frame']) / FPS for s in shots])
        chosen = np.concatenate([(o_tight[s['camera']] if 'crop' in s else o[s['camera']])
                                 [s['start_frame'] - start:s['end_frame'] - start] for s in shots])
        best = np.minimum.reduce([o['A'], o['B']] + list(o_tight.values()))
        stats = {'shots': len(shots), 'min_s': round(float(lengths.min()), 2),
                 'median_s': round(float(np.median(lengths)), 2), 'max_s': round(float(lengths.max()), 2),
                 'pct_A': round(float(sum(l for l, s in zip(lengths, shots) if s['camera'] == 'A') / lengths.sum()), 3),
                 'mean_chosen_obstruction': round(float(chosen.mean()), 4),
                 'mean_best_possible': round(float(best.mean()), 4),
                 'mean_A': round(float(o['A'].mean()), 4), 'mean_B': round(float(o['B'].mean()), 4),
                 'chosen_over_0.25_pct': round(float((chosen > 0.25).mean() * 100), 2),
                 'both_over_0.25_pct': round(float((best > 0.25).mean() * 100), 2),
                 'chosen_worse_than_other_by_0.1_pct': round(float((chosen - best > 0.1).mean() * 100), 2),
                 'cutaways': sum(1 for s in shots if s['reason'].startswith('cutaway')),
                 'cutaway_s': round(sum(l for l, s in zip(lengths, shots) if s['reason'].startswith('cutaway')), 1),
                 'holds_over_60s': int((lengths > 60).sum()),
                 'tight_pct': round(float(sum(l for l, s in zip(lengths, shots) if s['framing'] == 'tight') / lengths.sum()), 3),
                 'tight_crops': {c: tight[c] for c in 'AB'},
                 'focus_blur_chosen': (round(float(np.concatenate([blur[x['camera']][x['start_frame'] - start:x['end_frame'] - start] for x in shots]).mean()), 4) if blur else None),
                 'focus_soft_pct_chosen': (round(float((np.concatenate([blur[x['camera']][x['start_frame'] - start:x['end_frame'] - start] for x in shots]) > 0.5).mean() * 100), 2) if blur else None),
                 'focus_soft_pct_A_B': ([round(float((blur[c] > 0.5).mean() * 100), 1) for c in 'AB'] if blur else None),
                 'cuts_on_downbeat': int(sum(1 for c in cuts if len(down) and np.min(np.abs(down * FPS - c)) < 1))}
        print(sid, name, json.dumps(stats), flush=True)
        out_sets.append({'id': sid, 'name': name, 'start_frame': start, 'end_frame': end,
                         'shots': shots, 'unavoidable_intervals': [], 'stats': stats})
        store[f'o_a_{sid}'], store[f'o_b_{sid}'] = o['A'].astype(np.float32), o['B'].astype(np.float32)
    plan = {'fps': FPS, 'frame_domain': 'A_global_native_25fps_half_open', 'sets': out_sets,
            'parameters': vars(args) | {'bands': BANDS, 'stage_x': STAGE_X}, 'audio': 'continuous A camera'}
    plan['parameters'] = {k: (str(v) if isinstance(v, Path) else v) for k, v in plan['parameters'].items()}
    (args.out / 'plan.json').write_text(json.dumps(plan, indent=1), encoding='utf-8')
    np.savez_compressed(args.out / 'scores.npz', **store)
    print('wrote', args.out / 'plan.json')


if __name__ == '__main__':
    main()
