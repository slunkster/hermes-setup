# Checking a .srt against its audio recording

Turns "do the subtitles match the audio?" into measurements instead of
guesses. The answer has three parts: what the audio contains, what the
transcript says, and what is simply absent from the recording.

## 1. Inspect the audio

```
ls -la; afinfo "recording.wav"     # duration, channels, sample rate, bit depth
```

The subtitle timeline end should match the audio duration to within a second.
Convert to a working copy for ASR:

```
afconvert -f WAVE -d LEI16@16000 -c 1 input.wav work/audio16k.wav
```

If a mono downmix is silent in places, verify against the ORIGINAL per channel
before concluding anything: read each channel with ffmpeg (`-f f32le -ac 2`) and
compute the channel correlation. corr = +1 with both channels silent = a real
gap; anti-phase channels (corr = -1) would be a downmix artefact.

## 2. Set up the transcriber (Apple Silicon)

```
UV=/Users/<user>/.hermes/bin/uv        # absolute path: login shells may lack it
$UV venv --python 3.12 ~/srt-audio-check/venv
$UV pip install --python ~/srt-audio-check/venv/bin/python mlx-whisper imageio-ffmpeg
~/srt-audio-check/venv/bin/python -c "import imageio_ffmpeg,os;os.symlink(imageio_ffmpeg.get_ffmpeg_exe(), os.path.expanduser('~/srt-audio-check/bin/ffmpeg'))"
export PATH=~/srt-audio-check/bin:$PATH     # mlx shells out to `ffmpeg`
```

Model download: `huggingface_hub`/xet can stall at 0 bytes. Use curl instead:

```
curl -L --retry 8 -C - -o models/whisper-large-v3-mlx/weights.npz \
  https://huggingface.co/mlx-community/whisper-large-v3-mlx/resolve/main/weights.npz
curl -sL -o models/whisper-large-v3-mlx/config.json \
  https://huggingface.co/mlx-community/whisper-large-v3-mlx/resolve/main/config.json
```

List the repo files first with `https://huggingface.co/api/models/<repo>?blobs=true`
(the big file is `weights.npz`, not `weights.safetensors`).

## 3. Transcribe

```
venv/bin/python scripts/transcribe_long_audio.py models/whisper-large-v3-mlx \
    audio16k.wav transcript.json --language et --chunk 300 --overlap 5
```

Expect roughly 1 minute of compute per 10 minutes of audio on an M-series Mac.
Roughly 54 min of Estonian audio = ~11 chunks, ~7 min wall clock.

Why not the CLI: `mlx_whisper --temperature` defaults to a single `0`, killing
the fallback; a long file then degenerates into one repeated phrase
(compression_ratio > 10, hundreds of identical 1 s segments). The library
default is the tuple `(0.0, 0.2, 0.4, 0.6, 0.8, 1.0)` — keep it.

## 4. Compare

```
python3 scripts/compare_blocks.py subtitles.srt transcript.json --block 30 --worst 40
```

Per-cue alignment is the wrong unit when ASR segments span several cues; 30 s
blocks compare everything exactly once. Then READ the worst blocks: with a
typical Estonian ASR, expect a mean similarity around 0.55-0.6 where the
subtitles and audio actually agree — the deficit is spelling, not content.

## 5. Decide audio-gap vs decode failure

For each cue compute (a) mean dB, (b) peak, (c) the fraction of exactly-zero
samples in `[start, end]`:

* peak == 0 (or >90% zero samples) -> the recording has no audio there. List
  those cues: that is a finding about the export (timeline gaps, muted track),
  and those cues cannot be verified from this file at all.
* audio present but no transcript text -> re-decode that 60-120 s window on its
  own with `condition_on_previous_text=True`; chunked passes drop speech at
  boundaries and around quiet stretches, and standalone decodes recover it.

## 6. What to report

* Cue counts: verified / no-audio / unverified, plus the timestamps of the
  no-audio cues (grouped, in a table) — that is the actionable part.
* Each earlier grammar fix: quote the ASR around it and say whether the audio
  supports the fix, contradicts it, or is silent.
* Where the audio's wording differs from the subtitle's, offer both repair
  options instead of silently picking one.
* State the method's limits: machine transcription mangles names, numbers and
  endings, so no single word in the transcript is proof; sentence-level
  presence/absence is.
