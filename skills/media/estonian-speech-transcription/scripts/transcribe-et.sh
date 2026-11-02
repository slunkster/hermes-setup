#!/bin/bash
# Transcribe Estonian audio/video with TalTechNLP/whisper-large-v3-turbo-et-verbatim-2604
# Usage: ./transcribe-et.sh <file-or-dir> [more files...]
# Output: <name>.txt, <name>.srt (<=4 words/cue), <name>.karaoke.srt (word-by-word highlight)
#        ./transcribe-et.sh --fast <files...>   # whisper.cpp + Metal GPU (~3x faster, slightly less accurate)
set -euo pipefail
DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"

if [ "${1:-}" = "--fast" ]; then
  shift
  [ $# -eq 0 ] && { echo "usage: $0 --fast <audio|video> [...]"; exit 1; }
  for f in "$@"; do
    base="${f%.*}"; tmp="$(mktemp -t et).wav"
    ffmpeg -nostdin -loglevel error -y -i "$f" -ar 16000 -ac 1 "$tmp"
    whisper-cli -m "$DIR/models/ggml-et-verbatim-2604.bin" -l et -f "$tmp" \
      --vad -vm "$DIR/models/ggml-silero-v5.1.2.bin" -bs 5 -mc 0 -np \
      -otxt -osrt -of "$base" >/dev/null 2>&1
    rm -f "$tmp"; echo "$f -> $base.txt/.srt"
  done
  exit 0
fi
PY="$DIR/.venv/bin/python"
MODEL="$DIR/model2604/ct2"
WORDS="${ET_WORDS:-4}"          # max words per subtitle (env ET_WORDS=3 to change)
HL="${ET_HIGHLIGHT:-#E10600}"   # highlight colour for the karaoke SRT

[ $# -eq 0 ] && { echo "usage: $0 <audio|video|dir> [...]"; exit 1; }

"$PY" - "$MODEL" "$WORDS" "$HL" "$@" <<'EOF'
import sys, os, time
from faster_whisper import WhisperModel

model_dir, maxw, hl, targets = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4:]
LONG = 24   # a 4-word line longer than this many characters becomes 3 words
EXT = {".wav",".mp3",".m4a",".mp4",".mov",".ogg",".flac",".webm",".mkv",".aac"}
files = []
for t in targets:
    if os.path.isdir(t):
        files += [os.path.join(t, f) for f in sorted(os.listdir(t)) if os.path.splitext(f)[1].lower() in EXT]
    else:
        files.append(t)

print(f"loading {model_dir} ...", file=sys.stderr)
model = WhisperModel(model_dir, device="cpu", compute_type="int8", cpu_threads=8)

def ts(s):
    h, r = divmod(max(s, 0), 3600); m, sec = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{sec:06.3f}".replace(".", ",")

def merge_punct(words):
    """Attach stray punctuation tokens ("-", ",") to the previous word: haridus- ja."""
    out = []
    for w in words:
        if out and all(c in "-–.,?!:;…" for c in w["text"]):
            out[-1]["text"] += w["text"]; out[-1]["end"] = w["end"]
        else:
            out.append(w)
    return out

def group(words):
    """Split at clause ends/pauses, then cut each clause into balanced chunks of <= maxw words."""
    clauses, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        if nxt is None or nxt["start"] - w["end"] > 0.5 or w["text"].endswith((".", "?", "!", ",", ":", ";", "…")):
            clauses.append(cur); cur = []
    def balanced(c, n):
        size, extra = divmod(len(c), n); k = 0; res = []
        for j in range(n):
            m = size + (1 if j < extra else 0); res.append(c[k:k + m]); k += m
        return res
    def ok(ch):  # 4 words only if short; with long words max 3
        return len(ch) <= min(maxw, 3) or len(" ".join(w["text"] for w in ch)) <= LONG
    out = []
    for c in clauses:
        n = -(-len(c) // maxw)
        while not all(ok(ch) for ch in balanced(c, n)):
            n += 1
        out += balanced(c, n)
    return out

for path in files:
    t1 = time.time()
    segments, info = model.transcribe(path, language="et", task="transcribe",
                                      beam_size=5, vad_filter=True, word_timestamps=True)
    segs = list(segments)
    words = [{"text": w.word.strip(), "start": w.start, "end": w.end}
             for s in segs for w in (s.words or []) if w.word.strip()]
    words = merge_punct(words)
    base = os.path.splitext(path)[0]
    with open(base + ".txt", "w") as f:
        f.write(" ".join(s.text.strip() for s in segs).strip() + "\n")
    groups = group(words)
    # plain SRT: one cue per 3-4 word group
    with open(base + ".srt", "w") as f:
        for i, g in enumerate(groups, 1):
            f.write(f"{i}\n{ts(g[0]['start'])} --> {ts(g[-1]['end'])}\n{' '.join(w['text'] for w in g)}\n\n")
    # karaoke SRT: one cue per word, whole group shown, active word coloured
    n = 0
    with open(base + ".karaoke.srt", "w") as f:
        for g in groups:
            for j, w in enumerate(g):
                end = g[j + 1]["start"] if j + 1 < len(g) else w["end"]   # no flicker inside a group
                line = " ".join(f'<font color="{hl}">{x["text"]}</font>' if k == j else x["text"]
                                for k, x in enumerate(g))
                n += 1
                f.write(f"{n}\n{ts(w['start'])} --> {ts(end)}\n{line}\n\n")
    dur = info.duration or 1; wall = time.time() - t1
    print(f"{path}: {dur:.1f}s audio, {wall:.1f}s wall (RTF {wall/dur:.2f}), {len(groups)} cues "
          f"-> {base}.txt / .srt / .karaoke.srt")
EOF
