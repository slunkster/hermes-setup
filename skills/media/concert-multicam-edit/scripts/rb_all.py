import subprocess, sys
from rbq import g, post
py = sys.executable
for sid, name, n in ((1, '1 Autt of Office v9', 214), (3, '3 Multifunk v9', 159), (4, '4 Louie Digman & Heiki Vilep v9', 168)):
    r = post('/mediapool/timeline/import', {'filePath': f'G:\\Active Media\\Blues Fest\\Resolve-v9\\set{sid}.fcpxml',
             'importOptions': {'timelineName': name, 'importSourceClips': True, 'sourceClipsPath': 'G:\\Active Media\\Blues Fest'}})
    print(sid, r, flush=True)
    if not r.get('success') or g('/timeline')['name'] != r['timeline']:
        print('STOP: import failed or not current'); break
    for script in (['rb_clean.py', str(n)], ['rb_verify.py', str(sid)]):
        out = subprocess.run([py] + script, capture_output=True, text=True)
        print(out.stdout.strip(), out.stderr.strip()[-600:], flush=True)
print(g('/project'))
