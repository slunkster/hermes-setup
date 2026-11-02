---
name: srt-proofreading
description: "Proofread .srt subtitle files: validate, fix grammar."
---

# SRT subtitle proofreading

Goal: the same subtitles, but grammatically correct. Never reflow, retime,
renumber or reword beyond the minimal fix. Always validate structure and back up
before editing; report per cue what changed and what you deliberately left.

## Workflow

1. Locate files: `search_files(pattern='*.srt', target='files')` under the folder
   the user named (often `~/Documents`, may be nested). Count must match what the
   user said; if not, say so instead of guessing.
2. Back up every file first in the same directory. Use `x.srt.bak` only if it
   does not exist; otherwise choose the first unused `.bak.1`, `.bak.2`, etc.
   Never overwrite an earlier backup. Record the exact backup paths and use
   those copies as the baseline for this pass; include the paths in the report.
3. Run `scripts/validate_srt.py` on each file (structure) before editing, so you
   can tell pre-existing structural damage apart from your own edits.
4. Read every cue in full with `read_file` (paged, 2000 lines) — grammar review
   needs the whole text, not samples. When several language versions exist, read
   them side by side: the translation often reveals what the source should say.
5. Edit with the `patch` tool, one unique cue line per patch, so the diff proves
   exactly which lines changed (`diff a.bak a.srt` afterwards).
6. Re-run the validator, then `diff` each file against its `.bak`.
7. Report per cue: number, before -> after, one-line reason. List borderline
   spots you deliberately left alone; do not silently edit them.

## Rules

- Fix only clear grammar: agreement, case, doubled case markers, missing or
  duplicated words, wrong word form. Leave style, register and spoken-language
  disfluencies that are not ungrammatical.
- Never touch timings, cue numbers, `<b>` tags, line breaks inside a cue, quote
  style, or the file's line endings.
- Never re-translate a translation to "improve" it. Faithfulness of meaning beats
  elegance; report fidelity notes separately and let the user decide.
- A sentence that looks wrong is often right: check language-specific rules in
  `references/estonian-and-russian-checks.md` before editing (e.g. Estonian `on`
  is number-neutral, so `... on päris ja avaldavad ...` is not an error).
- When in doubt, flag it in the report and offer a fix rather than applying one.

## Checking subtitles against the audio

See `references/audio-subtitle-check.md` for the full procedure (setup, model
download, silence detection). Short version:

1. Convert/keep a 16 kHz mono wav; record duration and channel layout with
   `afinfo` first — the subtitle timeline end should match the audio length.
2. Transcribe locally with `scripts/transcribe_long_audio.py` (mlx-whisper on
   Apple Silicon). Never use the `mlx_whisper` CLI as-is: it defaults to
   `--temperature 0`, which disables Whisper's fallback and lets the decoder
   loop one phrase for tens of minutes. The script enables the fallback tuple,
   chunks the audio, and halves any chunk that still shows a repetition loop.
   For Estonian audio the better recognizer is TalTech's Estonian turbo-Whisper
   (roughly half the word errors, ~4x realtime on CPU) — see the
   `estonian-speech-transcription` skill for its CT2 setup and WER smoke test,
   then feed that transcript into the same block comparison.
3. Compare with `scripts/compare_blocks.py` (30 s blocks) — per-cue alignment
   fails because ASR segments are longer than cues.
4. For every cue, also measure the audio: fraction of all-zero samples and peak
   level. A cue with all-zero samples has NO audio to check, which is a
   finding about the recording (gaps/muted segments), not a subtitle error.
5. Re-decode any suspicious window on its own (60-120 s, fallback on,
   `condition_on_previous_text=True`): standalone decodes recover speech that
   the chunked pass dropped, so a gap in the transcript is not proof of a gap
   in the audio.
6. Report ASR-spelling differences as transcript noise, never as subtitle
   errors. Confirm sentence presence/absence, numbers and names only.

## Verification (must all hold before reporting success)

- Cue count identical to before the edit; numbering still 1..N sequential.
- All timestamps match the regex, have valid minute/second fields and positive
  durations, and match their own pre-edit backups byte-for-byte. Also compare
  timings across language versions of the same track; agreement between two
  edited files alone does not prove preservation.
- Compare raw bytes/physical lines against the exact backup created for this
  pass: cue numbers, timestamps, tags, separators, text line counts, BOM status,
  line-ending convention and final newline must remain unchanged.
- `diff BACKUP.srt.bak CURRENT.srt` shows only the intended text changes. Use
  the actual backup path, including its numeric suffix if one was needed.
- Every claimed fix is quoted from the file after editing, not from memory.

## Pitfalls

- `re.split(r'\n\s*\n', text)` yields cue *blocks*; each block still needs
  `.split('\n')`. Forgetting the second split makes `c[0]` a character and
  produces a bogus "numbering broken" report.
- Line-final commas are normal in wrapped subtitles; a regex like `,[^\s\d]`
  fires on `</b>` at line end. Eyeball matches before believing them.
- `huggingface_hub` model downloads can stall at 0 bytes (xet bridge 403).
  Download `weights.npz` + `config.json` with `curl -L -C -` and pass the local
  directory as `--model`/`path_or_hf_repo`.
- mlx shells out to `ffmpeg`; there may be none installed. `imageio-ffmpeg`
  ships a static binary — symlink it into a dir on `PATH`.
- A background shell started by the terminal tool may have a login shell PATH
  without `uv`; use absolute paths (`~/.hermes/bin/uv`).
- The `patch` tool warns that a paged read is a partial view; harmless as long as
  `old_string` is unique in the file.
- Keep each cue's `<b>` wrapper inside `old_string` and `new_string`; dropping it
  silently changes rendering.
