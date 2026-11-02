#!/usr/bin/env python3
"""Compare an .srt with a Whisper transcript block by block.

Per-cue alignment fails when ASR segments are longer than cues (one 10 s segment
covering three 3 s cues can only match one of them, leaving false gaps). Fixed
time blocks compare every part of the audio exactly once.

Usage:
    compare_blocks.py SUBTITLE.srt TRANSCRIPT.json [--block 30] [--worst 40]
                      [--out blocks.tsv]

Read the worst blocks yourself: ASR mangles endings and proper nouns and can
drop "ei", so a low score is not proof of a subtitle error. A mean score around
0.55-0.6 is normal for a subtitle text that actually matches the audio.
"""
import argparse
import difflib
import json
import re
import sys


def sec(t):
    h, m, rest = t.split(':')
    s, ms = rest.split(',')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def parse_srt(path):
    cues = []
    for block in re.split(r'\n\s*\n', open(path, encoding='utf-8').read().strip()):
        lines = block.split('\n')
        if len(lines) < 3:
            continue
        start, end = lines[1].strip().split(' --> ')
        text = re.sub(r'</?[^>]+>', '', ' '.join(lines[2:]))
        cues.append({'n': int(lines[0].strip()), 'start': sec(start), 'end': sec(end),
                     'text': re.sub(r'\s+', ' ', text).strip()})
    return cues


def parse_asr(path):
    segs = []
    for s in json.load(open(path, encoding='utf-8')).get('segments', []):
        t = re.sub(r'\s+', ' ', s.get('text', '')).strip()
        if t:
            segs.append({'start': s['start'], 'end': s['end'], 'text': t})
    return segs


def words(t):
    return re.findall(r'\w+', t.lower(), flags=re.UNICODE)


def score(a, b):
    return difflib.SequenceMatcher(None, words(a), words(b)).ratio()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('srt')
    ap.add_argument('asr')
    ap.add_argument('--block', type=float, default=30.0)
    ap.add_argument('--worst', type=int, default=40)
    ap.add_argument('--out', default='blocks.tsv')
    args = ap.parse_args()

    cues = parse_srt(args.srt)
    segs = parse_asr(args.asr)
    total = max(max(c['end'] for c in cues), max(s['end'] for s in segs))
    rows, t = [], 0.0
    while t < total:
        end = t + args.block
        srt_txt = ' '.join(c['text'] for c in cues if c['start'] < end and c['end'] > t)
        asr_txt = ' '.join(s['text'] for s in segs if s['start'] < end and s['end'] > t)
        if srt_txt or asr_txt:
            rows.append((t, score(srt_txt, asr_txt) if (srt_txt and asr_txt) else 0.0,
                         srt_txt, asr_txt))
        t = end

    with open(args.out, 'w', encoding='utf-8') as fh:
        fh.write('block_start\tscore\tsrt\tasr\n')
        for t, sc, a, b in rows:
            fh.write(f'{t:.0f}\t{sc:.2f}\t{a}\t{b}\n')

    scored = [r for r in rows if r[2] and r[3]]
    print(f'blocks={len(rows)} scored={len(scored)} '
          f'mean={sum(s for _, s, _, _ in scored)/len(scored):.3f}')
    print(f'wrote {args.out}\n--- worst {args.worst} blocks ---')
    for t, sc, a, b in sorted(scored, key=lambda r: r[1])[:args.worst]:
        m, s = divmod(int(t), 60)
        print(f'\n[{m:02d}:{s:02d}] score {sc:.2f}')
        print(f'  SRT: {a[:300]}')
        print(f'  ASR: {b[:300]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
