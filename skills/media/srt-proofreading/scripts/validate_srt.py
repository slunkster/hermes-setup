#!/usr/bin/env python3
"""Validate .srt structure and optionally compare timings between two files.

Usage:
    python3 validate_srt.py FILE [FILE2]

With two files (same track, different languages) it also reports whether the
cue timings are identical, which is the usual requirement for translated subs.
"""
import re
import sys

TS = r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}'


def parse(path):
    raw = open(path, encoding='utf-8').read()
    # split into cue blocks, then split each block into lines
    return [b.split('\n') for b in re.split(r'\n\s*\n', raw.strip())]


def ts(t):
    h, m, rest = t.split(':')
    s, ms = rest.split(',')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def validate(path):
    problems = []
    raw = open(path, encoding='utf-8').read()
    cues = parse(path)
    prev_end = None
    for i, c in enumerate(cues, 1):
        if len(c) < 3:
            problems.append((i, 'short block', c[:2]))
            continue
        if c[0].strip() != str(i):
            problems.append((i, 'numbering', c[0]))
        if not re.fullmatch(TS, c[1]):
            problems.append((i, 'timestamp', c[1]))
        else:
            start, end = c[1].split(' --> ')
            if prev_end is not None and ts(start) < prev_end:
                problems.append((i, 'overlap', c[1]))
            prev_end = ts(end)
        text = '\n'.join(c[2:])
        if text.count('<b>') != text.count('</b>'):
            problems.append((i, 'unbalanced <b>', text[:60]))
        if text.count('<i>') != text.count('</i>'):
            problems.append((i, 'unbalanced <i>', text[:60]))
        if '  ' in text:
            problems.append((i, 'double space', text[:60]))
        if re.search(r'[ \t]+\n', text):
            problems.append((i, 'trailing space', text[:60]))
    if raw and not raw.endswith('\n'):
        problems.append((len(cues), 'no final newline', ''))
    return cues, problems


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    parsed = {}
    for path in sys.argv[1:]:
        cues, problems = validate(path)
        parsed[path] = cues
        print(f'{path}: {len(cues)} cues')
        if problems:
            print(f'  {len(problems)} PROBLEM(S):')
            for p in problems[:40]:
                print('   ', p)
        else:
            print('  structure OK (numbering, timestamps, tags, whitespace)')
    if len(sys.argv) == 3:
        a, b = sys.argv[1], sys.argv[2]
        ta = [c[1] for c in parsed[a] if len(c) > 1]
        tb = [c[1] for c in parsed[b] if len(c) > 1]
        print('timings identical:', ta == tb)
        if ta != tb:
            for i, (x, y) in enumerate(zip(ta, tb), 1):
                if x != y:
                    print(f'  first difference at cue {i}: {x} | {y}')
                    break
    return 0


if __name__ == '__main__':
    sys.exit(main())
