"""Current Resolve timeline (just imported from make_fcpxml): remove the stray full-length A video under the cuts
and the per-cut camera audio, leaving cuts on V2 and one continuous A audio clip on A2."""
import sys
from rbq import g, post
expect = int(sys.argv[1])
tl = g('/timeline')
def clips(tt, i): return g(f'/timeline/clips?track_type={tt}&track_index={i}')['clips']
v1, v2, a1, a2 = clips('video', 1), clips('video', 2), clips('audio', 1), clips('audio', 2)
assert len(v1) == 1 and len(a2) == 1 and len(v2) == len(a1) == expect, (len(v1), len(v2), len(a1), len(a2))
assert v1[0]['name'].startswith('A089') and a2[0]['name'].startswith('A089')
r = post('/timeline/clips/link', {'linked': False, 'clips': [{'trackType': 'video', 'trackIndex': 1, 'clipIndex': 0}, {'trackType': 'audio', 'trackIndex': 2, 'clipIndex': 0}]}); assert r.get('success'), r
bad = 0
for i in range(expect):
    r = post('/timeline/clips/link', {'linked': False, 'clips': [{'trackType': 'video', 'trackIndex': 2, 'clipIndex': i}, {'trackType': 'audio', 'trackIndex': 1, 'clipIndex': i}]})
    bad += not r.get('success')
print('unlink failures', bad)
assert bad == 0
print(post('/timeline/clips/delete', {'clips': [{'trackType': 'video', 'trackIndex': 1, 'clipIndex': 0}], 'ripple': False}))
print(post('/timeline/clips/delete', {'clips': [{'trackType': 'audio', 'trackIndex': 1, 'clipIndex': i} for i in range(expect)], 'ripple': False}))
v1, v2n, a1, a2 = clips('video', 1), clips('video', 2), clips('audio', 1), clips('audio', 2)
ok = (len(v1) == 0 and len(a1) == 0 and len(a2) == 1 and a2[0]['duration'] == tl['endFrame']
      and [(c['name'], c['start'], c['end']) for c in v2n] == [(c['name'], c['start'], c['end']) for c in v2])
print(tl['name'], 'V1', len(v1), 'V2', len(v2n), 'A1', len(a1), 'A2', len(a2), a2[0]['duration'] if a2 else None, 'OK' if ok else 'MISMATCH')
