"""Verify the current Resolve timeline against the plan: export stills at mid-shot frames and compare with the
source frame ffmpeg decodes at the planned position (and its neighbours)."""
import json, subprocess, sys, time
import numpy as np
from pathlib import Path
from rbq import g, post
import make_fcpxml as mf
SID = int(sys.argv.pop(1)); del sys.argv[1:]
import color_stats as cs

sid = SID; plan = json.loads((cs.ROOT / 'plan-v9' / 'plan.json').read_text())
item = [s for s in plan['sets'] if s['id'] == sid][0]; s0 = item['start_frame']
out = cs.ROOT / 'resolve-verify'; out.mkdir(exist_ok=True)
page0 = g('/page'); post('/page', {'page': 'color'})
def rgb(path):
    r = subprocess.run([str(cs.FF), '-v', 'error', '-i', str(path), '-vf', 'scale=480:270,format=gray', '-f', 'rawvideo', '-'], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.uint8).astype(float)
shots = item['shots']; picks = [shots[i] for i in sorted({1, len(shots) // 3, len(shots) // 2, 2 * len(shots) // 3, len(shots) - 2})]
for sh in picks:
    f = (sh['start_frame'] + sh['end_frame']) // 2; tf = f - s0
    tc = '%02d:%02d:%02d:%02d' % (tf // 90000, tf // 1500 % 60, tf // 25 % 60, tf % 25)
    post('/playhead', {'timecode': tc}); time.sleep(1.0)
    still = out / f's{sid}_{tf}.png'
    r = post('/project/export-frame', {'filePath': str(still)})
    if not r.get('success'): print('export failed', r); continue
    a = rgb(still); res = {}
    for d in (-2, -1, 0, 1, 2):
        (rid, start, n), = mf.pieces(sh['camera'], f + d, f + d + 1)
        name, _, frames, tcbase = [x for x in mf.FILES[sh['camera']] if x[1] == rid][0]
        src = out / 'src.png'
        subprocess.run([str(cs.FF), '-v', 'error', '-ss', f'{(start - tcbase) / 25:.3f}', '-i', str(cs.BASE / name), '-frames:v', '1', '-vf', 'scale=1920:1080', '-y', str(src)], check=True)
        res[d] = round(float(np.abs(a - rgb(src)).mean()), 2)
    best = min(res, key=res.get)
    print(f'{tc} cam {sh["camera"]} mean abs diff by offset {res} -> best {best:+d}')
post('/page', {'page': page0.get('page', 'edit') if isinstance(page0, dict) else 'edit'})
