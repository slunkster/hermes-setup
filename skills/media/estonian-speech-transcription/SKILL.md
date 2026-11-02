---
name: estonian-speech-transcription
description: "Transcribe Estonian audio locally: TalTech Whisper."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [asr, transcription, estonian, whisper, faster-whisper]
    related_skills: [srt-proofreading, estonian-proofreading, youtube-content]
---

# Estonian speech transcription (local, no cloud)

## When to Use

Use when the user wants text out of Estonian audio or video: interviews,
lectures, meetings, podcast/broadcast clips, voice memos, or the audio behind a
set of subtitles. Also use when asked whether a TalTechNLP Whisper model "can be
used" here — the answer is yes, and this is the setup that works.

Goal: a trustworthy Estonian transcript on this Mac with the best current
Estonian ASR model, plus timings so the user knows what it cost.

## Model choice — do not improvise

Use `TalTechNLP/whisper-large-v3-turbo-et-verbatim-2604` (large-v3-turbo
fine-tune, verbatim, MIT). Its repo already ships converted weights:
`ct2/` (faster-whisper), `ggml/` (whisper.cpp), `native/` (whisper.pt).

Before a long job, check for a newer upload — TalTech supersedes these models
and flags it at the top of the older card:

```
curl -s 'https://huggingface.co/api/models?author=TalTechNLP&sort=lastModified&direction=-1&limit=20'
```

Never fall back to `TalTechNLP/whisper-large-et` (the well-known 2024 one):
large-v2 based, normalized text, ~11–12% WER on Common Voice, and **no** `ct2/`
in the repo, so using it means installing torch and downloading 3.2 GB of fp32
weights for a worse model. Full family and non-Whisper alternatives:
`references/taltech-asr-models.md`.

## Setup (once)

```
UV=~/.hermes/bin/uv
mkdir -p ~/Hermes/whisper-et && cd ~/Hermes/whisper-et
$UV venv --python 3.12 .venv
$UV pip install --python .venv/bin/python faster-whisper "av<16"
```

Homebrew python3 is PEP 668 externally managed — never `pip install` into it;
let uv provision the interpreter for the venv.

Download the CT2 model directly, no conversion step:

```
base=https://huggingface.co/TalTechNLP/whisper-large-v3-turbo-et-verbatim-2604/resolve/main
mkdir -p model2604/ct2 && for f in config.json model.bin preprocessor_config.json tokenizer.json vocabulary.json; do
  curl -sL -o model2604/ct2/$f "$base/ct2/$f"; done
```

~1.6 GB. `ct2-transformers-converter` only for repos that lack a `ct2/` folder —
it needs torch plus the full fp32 safetensors, a multi-GB detour with no payoff.

## Transcribe

```
~/Hermes/whisper-et/transcribe-et.sh FILE_OR_DIR [...]   # or scripts/transcribe-et.sh
```

Writes `<name>.txt`, `<name>.srt` (≤4 words/cue, `ET_WORDS=3` to change) and
`<name>.karaoke.srt` next to each input; accepts
wav/mp3/m4a/mp4/mov/ogg/flac/webm/mkv/aac, directories are expanded. Settings
that matter: `language="et"`, `beam_size=5`, `vad_filter=True`,
`compute_type="int8"`, `cpu_threads=8`.

Measured on M5 / 16 GB: model ready ~1.5 s from cache, **RTF ≈ 0.25–0.3**
(4× realtime; 77 s of speech → ~20 s). Report that ratio to the user so they
can judge whether a long recording is worth running. When Metal speed matters,
`whisper.cpp` with the repo's `ggml/` model is the alternative.

## Short / word-highlight subtitles (DaVinci Resolve)

User wants 3–4 words per cue and words lighting up as spoken. Use
`word_timestamps=True`; attach stray punctuation tokens (`-`, `,`) to the
previous word (else `haridus - ja`); split at clause ends/pauses >0.5 s, then cut
each clause into *balanced* chunks (5 words → 3+2, never 4+1 orphans).
User preference: 4 words only when the line is ≤24 chars, otherwise max 3
(`LONG` in the script); highlight colour `#E10600` (red).
Resolve's built-in AI Animated Subtitles / Word Highlight only work on
subtitles Resolve generated itself — imported SRTs have no word timing. What
survives SRT import is `<font color>`, so the karaoke SRT is one cue per word
showing the whole chunk with the active word coloured (cue ends at next word's
start to avoid flicker). `--fast` (whisper.cpp) does not chunk/karaoke.

## Hermes voice messages (Telegram STT via the gateway)

The same model can transcribe the user's voice notes inside Hermes. User decision: **accuracy over speed** — keep TalTech even though it is slower; offer cloud only if they complain about waiting.

1. Download the CT2 model as above (on the VPS: `~/Hermes/whisper-et/model2604/ct2`).
2. `hermes pm install --extra stt-whisper` (installs faster-whisper into Hermes' own env; never pip into it).
3. `hermes config set stt.provider local`, `stt.language et`, `stt.local.model <absolute path to ct2 dir>` (a path works, not only size names), `stt.local.device cpu`, `stt.local.compute_type int8`.
4. The user restarts the gateway once (new dependency); later `stt.*` switches apply live.
5. Verify in `agent.log`: `Transcribed … via local whisper (<path>, lang=et, N s audio)`.

Speed: Hermes hardcodes `beam_size=5`. On a 4-vCPU x86 VPS (AVX2, no GPU) RTF ≈ 2 (77 s → 160 s; beam 1 would be RTF 1.3); a 6 s voice note took ~30 s including the ~10 s first model load. Tell the user up front.

Cloud comparison on the shipped dictation (104 words): TalTech 104/104; OpenAI `gpt-transcribe` 92/104 ($0.0045/min); `gpt-4o-transcribe` ~75/104 ($0.006/min); OpenAI ~5 s. On a real voice command OpenAI mangled the key word ("kalendrisse" → "lennsse") while TalTech only spelled numbers as words ("neliteist nelikümmend viis") — harmless for the agent. Test a cloud alternative on the user's own sentence before recommending it; WER on the demo understates the gap on commands.

## Verify before trusting a model

The repos ship `demo/etteütlus2024.wav` with the reference
`demo/etteütlus2024.txt` (read speech, 77.5 s). Transcribe it and compute WER —
the shipped pair scores **0.0%** (104/104 words). Anything above
punctuation-level difference means the wrong model dir, a missing
tokenizer/vocabulary file, or a broken pin. Run this after every upgrade or
re-download.

## Rules

- Verbatim model: it keeps fillers and false starts (`no, nii-öelda`). Do not
  clean up the text unless asked; if polished subtitles are the goal, edit
  deliberately afterwards and say so.
- Always report audio duration, wall time and RTF with the transcript.
- Keep venv, model and outputs under `~/Hermes/whisper-et/`; generated files do
  not belong in the home root.
- To check existing subtitles against their audio (block similarity, audio-gap
  detection, gap-vs-decode-failure decision), use the `srt-proofreading` skill's
  `audio-subtitle-check` reference; point its transcription step at the Estonian
  model above for better Estonian decoding.

## Pitfalls

- Never run the script on `demo/etteütlus2024.wav` in place: outputs overwrite
  the shipped reference `.txt`/`.srt`. Copy the wav elsewhere first.

- `TypeError: open() got an unexpected keyword argument 'metadata_errors'`:
  PyAV too new for faster-whisper 1.2.x — pin `av<16` in that venv and re-run.
- `huggingface_hub`/xet downloads can stall near 0 bytes. Fetch files with
  `curl -sL` and get the exact file list from
  `https://huggingface.co/api/models/<repo>/tree/main?recursive=true` — the
  recursive listing also reveals the `ct2/`, `ggml/`, `native/` and `demo/`
  subdirs, which is how you avoid a pointless conversion.
- Read model cards by opening the HF page in `browser_exec` and taking
  `document.body.innerText`; the card carries the superseding-model note and the
  demo reference transcript.
- Do not judge a model on single-word TTS/pronunciation clips — the decoder
  punctuates them arbitrarily and it says nothing about real speech.
