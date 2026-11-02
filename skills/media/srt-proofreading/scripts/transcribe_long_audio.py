#!/usr/bin/env python3
"""Transcribe long audio with mlx-whisper in chunks, repairing decoder loops.

The mlx_whisper CLI defaults --temperature to a single 0, which disables
Whisper's fallback; on long recordings the decoder then locks into repeating one
phrase (compression_ratio > 10) for tens of minutes. This driver calls the
library with the fallback tuple, chunks the audio, and recursively halves any
chunk whose output still shows a repetition loop.

Usage:
    transcribe_long_audio.py MODEL_DIR AUDIO OUT_JSON [--language et]
                             [--chunk 300] [--overlap 5] [--ffmpeg PATH]

MODEL_DIR is a local MLX model dir (download with curl -L -C -: config.json +
weights.npz). ffmpeg is required by mlx; if --ffmpeg is omitted, PATH and the
imageio-ffmpeg bundled binary are tried in turn.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import wave
from collections import Counter

from mlx_whisper.transcribe import transcribe

OPS = dict(temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
           compression_ratio_threshold=2.4,
           condition_on_previous_text=False,
           verbose=None)


def find_ffmpeg(explicit=None):
    if explicit:
        return explicit
    if shutil.which('ffmpeg'):
        return shutil.which('ffmpeg')
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        sys.exit('no ffmpeg: pass --ffmpeg PATH or pip install imageio-ffmpeg')


def cut(ffmpeg, audio, start, dur, out):
    subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y',
                    '-ss', f'{start:.3f}', '-t', f'{dur:.3f}', '-i', audio,
                    '-ar', '16000', '-ac', '1', out], check=True)


def max_repeat(segs):
    c = Counter(s['text'].strip().lower() for s in segs if s['end'] - s['start'] < 6)
    return c.most_common(1)[0][1] if c else 0


def run(model, path, language, offset=0.0):
    r = transcribe(path, path_or_hf_repo=model, language=language,
                   task='transcribe', **OPS)
    return [{'start': s['start'] + offset, 'end': s['end'] + offset,
             'text': s['text']} for s in r['segments'] if s['text'].strip()]


def transcribe_span(ffmpeg, model, audio, language, start, dur, tmpdir):
    path = os.path.join(tmpdir, f'span_{start:.0f}_{dur:.0f}.wav')
    if not os.path.exists(path):
        cut(ffmpeg, audio, start, dur, path)
    segs = run(model, path, language, offset=start)
    reps = max_repeat(segs)
    if reps >= 5 and dur > 40:
        print(f'  loop x{reps} at {start:.0f}s for {dur:.0f}s -> halving', flush=True)
        half = dur / 2
        return (transcribe_span(ffmpeg, model, audio, language, start, half, tmpdir) +
                transcribe_span(ffmpeg, model, audio, language, start + half,
                                dur - half, tmpdir))
    print(f'  span {start:6.0f}s +{dur:5.0f}s -> {len(segs):3d} segs, max repeat {reps}',
          flush=True)
    return segs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('model')
    ap.add_argument('audio')
    ap.add_argument('out')
    ap.add_argument('--language', default='et')
    ap.add_argument('--chunk', type=float, default=300.0)
    ap.add_argument('--overlap', type=float, default=5.0)
    ap.add_argument('--ffmpeg', default=None)
    args = ap.parse_args()
    ffmpeg = find_ffmpeg(args.ffmpeg)

    tmpdir = os.path.join(os.path.dirname(os.path.abspath(args.out)), 'spans')
    os.makedirs(tmpdir, exist_ok=True)
    with wave.open(args.audio) as w:
        total = w.getnframes() / w.getframerate()
    print(f'audio {total:.1f}s | chunk {args.chunk}s | overlap {args.overlap}s | '
          f'lang {args.language}', flush=True)

    allsegs, start, i = [], 0.0, 0
    while start < total and i < 400:
        segs = transcribe_span(ffmpeg, args.model, args.audio, args.language,
                               start, min(args.chunk, total - start), tmpdir)
        if i:  # drop the overlap region already covered by the previous chunk
            keep_from = start + args.overlap / 2
            segs = [s for s in segs if (s['start'] + s['end']) / 2 >= keep_from]
        allsegs += segs
        i += 1
        start += args.chunk - args.overlap

    allsegs.sort(key=lambda s: s['start'])
    json.dump({'text': ' '.join(s['text'].strip() for s in allsegs),
               'segments': allsegs, 'language': args.language},
              open(args.out, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'wrote {args.out}: {len(allsegs)} segments', flush=True)


if __name__ == '__main__':
    main()
