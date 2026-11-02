# TalTechNLP Estonian ASR models (decision table)

TalTech's language-technology lab publishes the public Estonian ASR checkpoints
under one HF org. Check what is newest before committing to a download:

```
curl -s 'https://huggingface.co/api/models?author=TalTechNLP&sort=lastModified&direction=-1&limit=20'
```

## Whisper family

| Model | Base | Text style | Pre-converted weights | Use |
|---|---|---|---|---|
| `whisper-large-v3-turbo-et-verbatim-2604` | large-v3-turbo | verbatim | `ct2/`, `ggml/`, `native/` + `demo/` | **default choice** |
| `whisper-large-v3-turbo-et-verbatim` | large-v3-turbo | verbatim | `ct2/`, `demo/` | superseded; card points to 2604 |
| `whisper-large-et` | large-v2 | normalized | none (needs converter + torch) | legacy, ~11–12% WER Common Voice |
| `whisper-large-v3-turbo-et-subs`, `whisper-large-v3-et-subs` | v3-turbo / v3 | subtitle-oriented | varies | not evaluated — check the demo transcript first |
| `whisper-large-v3-turbo-et-adolescent` | v3-turbo | verbatim | varies | youth speech |
| `whisper-large-v3-et-en-ru.translate` | large-v3 | translation | varies | et→en/ru translation, not plain ASR |

Training data behind the two verbatim turbo models: 1400 h manual verbatim
transcripts from the TalTech Estonian Speech Dataset 1.0; 2604 adds ~4000 h
contextually-biased, auto-transcribed Estonian broadcast news plus ~500 h English
podcast/YouTube speech — which is why it also handles English terms inside
Estonian sentences.

Measured (M5, 16 GB, CT2 int8, 8 CPU threads): 2604 on the repo's own demo —
WER 0.0% (104/104 words), RTF 0.24–0.29, model load ~1.5 s.

## Non-Whisper options from the same org

- `Voxtral-Mini-4B-Realtime-estonian-2609`, `Voxtral-Mini-3B-2507-estonian` —
  newer realtime ASR (speech-LLM based). Much heavier than turbo-Whisper; only
  reach for these when streaming / low latency is the actual requirement.
- `streaming-zipformer-large.et-en`, `streaming-zipformer.et-en` — icefall /
  sherpa streaming models, Estonian + English.

None of the non-Whisper rows were benchmarked here; test any candidate on
`demo/etteütlus2024.wav` against its reference transcript before adopting it.

## What to fetch for faster-whisper

Five files from `<repo>/ct2/`: `config.json`, `model.bin`,
`preprocessor_config.json`, `tokenizer.json`, `vocabulary.json` — roughly 1.6 GB
for the turbo models. Passing that directory to `WhisperModel(dir)` needs no
network at run time, which keeps repeat runs instant and offline.
