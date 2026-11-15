import json, sys, urllib.request
def g(p):
    return json.loads(urllib.request.urlopen('http://127.0.0.1:9876' + p, timeout=240).read())
def post(p, body):
    r = urllib.request.Request('http://127.0.0.1:9876' + p, json.dumps(body).encode(), {'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(r, timeout=240).read())
if __name__ == '__main__':
    tl = g('/timeline'); print(tl['name'], tl['endFrame'], tl['trackCount'])
    for tt, n in (('video', tl['trackCount']['video']), ('audio', tl['trackCount']['audio'])):
        for i in range(1, n + 1):
            c = g(f'/timeline/clips?track_type={tt}&track_index={i}')['clips']
            print(tt, i, len(c), 'total', sum(x['duration'] for x in c), 'first', (c[0]['name'], c[0]['start'], c[0]['end']) if c else None)
            if c and tt == 'video' and i == 1: print(' keys', sorted(c[0].keys()))
