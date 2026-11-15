"""Edit plan -> FCPXML 1.10 for DaVinci Resolve: one timeline per set, plain asset-clips.

Video: camera switches on the spine (video only). Audio: ONE continuous clip from the A camera, connected
(lane -1) to the first spine clip. No grade, no titles, no transforms (the user does those in Resolve).
python make_fcpxml.py [PLAN] [OUT] [SET ...]
"""
from pathlib import Path
from urllib.parse import quote
import json, math, sys

ROOT = Path(__file__).resolve().parent
FPS = 25
MEDIA = 'G:/Active Media/Blues Fest'
# name, id, frames, start timecode in frames (ffprobe: A 22:58:02:00 / 02:02:02:12, B has none)
FILES = {'A': [('A089C001_260904_DJ0B.MOV', 'r1', 276012, 2067050), ('A089C002_260904_DJ0B.MOV', 'r2', 175692, 183062)],
         'B': [('S1310001.MP4', 'r3', 276024, 0), ('S1310002.MP4', 'r4', 170640, 0)]}
NAMES = {1: 'Autt of Office', 2: 'Kapten Jack', 3: 'Multifunk', 4: 'Louie Digman & Heiki Vilep'}
sync = json.loads((ROOT / 'sync_model.json').read_text())


def native_frame(cam, frame):
    """A-global frame -> camera-native global frame (same rounding as render_v2.map_parts)."""
    if cam == 'A':
        return frame
    sec = frame / FPS
    return math.floor((sec - (sync['intercept_seconds'] + sync['slope'] * sec)) * FPS + .5)


def pieces(cam, a, b):
    """Shot [a,b) in A-global frames -> [(asset id, source start incl. timecode, frames)], split at file ends."""
    n0, count, done, out = native_frame(cam, a), b - a, 0, []
    while done < count:
        pos, base = n0 + done, 0
        for name, rid, frames, tc in FILES[cam]:
            if base <= pos < base + frames:
                take = min(count - done, base + frames - pos)
                out.append((rid, tc + pos - base, take))
                done += take
                break
            base += frames
        else:
            raise ValueError(f'unmapped {cam} frame {pos}')
    return out


def t(frames):
    return f'{frames}/{FPS}s'


def build(plan, set_ids, suffix):
    x = ['<?xml version="1.0" encoding="UTF-8"?>', '<!DOCTYPE fcpxml>', '<fcpxml version="1.10">', '  <resources>',
         '    <format id="r0" name="FFVideoFormat1080p25" frameDuration="1/25s" width="1920" height="1080"/>']
    for cam in 'AB':
        for name, rid, frames, tc in FILES[cam]:
            src = 'file://localhost/' + quote(f'{MEDIA}/{name}', safe='/')
            x += [f'    <asset name="{name}" audioSources="1" hasVideo="1" audioChannels="2" id="{rid}" duration="{t(frames)}" '
                  f'format="r0" start="{t(tc)}" hasAudio="1">', f'      <media-rep src="{src}" kind="original-media"/>', '    </asset>']
    x += ['  </resources>', '  <library>', f'    <event name="Bluesfest Day 1 {suffix}">']
    report = {}
    for item in plan['sets']:
        sid = item['id']
        if sid not in set_ids:
            continue
        s0, s1 = item['start_frame'], item['end_frame']
        audio = pieces('A', s0, s1)
        if len(audio) != 1:
            raise ValueError(f'set {sid}: A audio spans a file split')
        clips = []
        for shot in item['shots']:
            pos = shot['start_frame']
            for rid, start, n in pieces(shot['camera'], shot['start_frame'], shot['end_frame']):
                clips.append((rid, pos - s0, n, start))
                pos += n
        assert clips[0][1] == 0 and all(a[1] + a[2] == b[1] for a, b in zip(clips, clips[1:])) and clips[-1][1] + clips[-1][2] == s1 - s0
        name = f'{sid} {NAMES[sid]} {suffix}'.replace('&', '&amp;')
        x += [f'      <project name="{name}">', f'        <sequence format="r0" duration="{t(s1 - s0)}" tcStart="0s" tcFormat="NDF">', '          <spine>']
        for i, (rid, off, n, start) in enumerate(clips):
            head = f'            <asset-clip ref="{rid}" offset="{t(off)}" duration="{t(n)}" start="{t(start)}" srcEnable="video"'
            if i == 0:
                arid, astart, an = audio[0]
                x += [head + '>',
                      f'              <asset-clip ref="{arid}" lane="-1" offset="{t(start)}" duration="{t(an)}" start="{t(astart)}" '
                      'srcEnable="audio" audioRole="dialogue"/>', '            </asset-clip>']
            else:
                x.append(head + '/>')
        x += ['          </spine>', '        </sequence>', '      </project>']
        report[sid] = {'name': name.replace('&amp;', '&'), 'clips': len(clips), 'frames': s1 - s0}
    x += ['    </event>', '  </library>', '</fcpxml>']
    return '\r\n'.join(x) + '\r\n', report


if __name__ == '__main__':
    plan_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'plan-v9/plan.json'
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'resolve' / 'bluesfest-day1-v9.fcpxml'
    sets = [int(s) for s in sys.argv[3:]] or [1, 2, 3, 4]
    text, report = build(json.loads(plan_path.read_text()), sets, 'v9')
    out.parent.mkdir(exist_ok=True)
    out.write_text(text, encoding='utf-8', newline='')
    print(json.dumps(report, ensure_ascii=False))
