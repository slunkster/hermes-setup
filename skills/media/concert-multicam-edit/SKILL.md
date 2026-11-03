---
name: concert-multicam-edit
description: "Cut a 2-camera live concert from recorder files to mp4."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [video, multicam, ffmpeg, concert, sync, obstruction]
---

# Two-camera live concert edit (ffmpeg pipeline)

## When to Use

A festival/concert delivered as continuous camera files (not per-song), where you must
produce one mp4 per artist, cut between angles on a musical grid, avoid frames where
a body crosses the lens, and match the cameras' look.

## First, establish the real shape of the footage

`ffprobe -show_format -show_streams` every file before planning anything. Check for:
- **Continuous timecode** (Panasonic `timecode` tag): lets you concatenate split files exactly.
- **Creation time vs file mtime**: consumer cameras often have the card clock wrong by weeks.
  Use the tag, not mtime, to map recording time to wall clock.
- **Split points**: a 4 GB/3 h recorder split is one recording, not two takes.
- **Pairwise durations**: cameras started/stopped at different times; compute coverage gaps.

Ask whether angle count really is what the folder suggests — a 7-file, 330 GB folder can
still be only two angles, which changes the edit from "multicam" to "A/B".

## Sync: waveform correlation will fail, envelope correlation will not

Two cameras at different positions in a reverberant room with AGC produce waveforms that
correlate at ~0.00. Do not conclude the offset is unknown and do not trust the NLE's
auto-sync.

Instead: decode both to 8 kHz mono, take **10 ms RMS envelopes** (log), and scan the offset
grid on 30 s windows, averaging the normalised correlation across many windows. Peaks come
out sharp (0.30–0.50) and agree with a correct offset to ~10 ms.

Then **re-scan in 30-minute blocks** to prove there is no drift. Real result on a 5 h pair:
50 ms total drift, i.e. sub-frame inside any single set.

## Obstruction map

Per-frame metric on a 160x90 luma downsample: fraction of pixels whose |delta| from the
previous frame exceeds 35. Musicians moving sit at ~0.001–0.003; a body sweeping the lens
spikes to 0.4–0.7. Smooth with a rolling max (~±0.75 s) and threshold. Mask = `rolling_max < 0.03`.

Cost: ~7x realtime for 4K H.264 decode. Only cover the ranges you need (the sets, plus
margin) — breaks between sets do not need mapping.

**Pitfall that will silently ruin timing:** reading a pipe in fixed-size chunks. `stream.read(n)`
returns short reads, and if you prepend the previous frame and then drop the first score you
lose one frame per chunk; over 5 h that is ~30 s of accumulated offset. Use a `read_exact()`
loop and keep exactly n scores per block.

## Set boundaries without a schedule

Loudness plateaus alone are unreliable (between-set PA music is loud, and a limiter flattens
everything). The discriminator that worked: **fraction of seconds above the limiter ceiling**
(e.g. >73.5 dB) in 2-minute bins. Playing sets sit at 0.6–1.0; breaks at 0.00–0.17. Refine
edges with a 5 s mean and a 60 s hold test. Cross-check the last-note time with spectral
flatness — applause is broadband (flatness ~0.3) while the final chord is harmonic (~0.07).

Ignore single loud bursts (30 s of soundcheck/line check) when locating a set start; require
sustained energy.

## Cut engine

- Snap to **bar lines** from `librosa.beat.beat_track`, grouped in 4s from the phase whose
  beats carry most onset energy. Fall back to beats, then unsnapped.
- Keep everything in ONE camera's reference time so audio stays a single continuous slice.
- Greedy loop: at each cut point compute, per camera, `cap = min(time until that camera is
  next blocked, MAX_SHOT)`. Size the shot to the available clean run; never place a shot that
  overruns it.
- **Do not require the other camera to have a full target-length clean run before switching.**
  Demanding 25 s when the usable windows are 10–14 s produces multi-minute single-angle holds
  (observed: 24% of a set). Lower the switch threshold to the shortest shot you're willing to
  accept (~10 s) and holds collapse to zero.
- Merge adjacent same-camera shots afterwards, then print min/median/max shot length, % on
  each camera, % blocked, and minutes spent in holds >60 s. Those four numbers tell you if the
  cut is doing what was asked.
- Concatenate shots covering `[start, end]` **with no gaps** — then output duration equals input
  duration and the audio is one uninterrupted slice, which makes sync structurally guaranteed.

## Grade (8-bit 4:2:0 source, two mismatched cameras)

1. Measure per-channel p10/p50/p90 over many simultaneous frame pairs.
2. Map both cameras onto a shared target with `colorlevels` (per-channel in/out range).
   Aim to meet in the middle rather than forcing one camera's look onto the other.
3. Check white balance on a real neutral (gravel ground, concrete) before correcting it. Seen
   here: cameras agreed within 1.4%, so an apparent "cool" cast was genuine scene content
   (one camera framed more sky), not a camera fault. Do not neutralise it.
4. Apply the look on top: gentle S-curve with lifted toe (`curves`), small warm `colorbalance`,
   slight saturation. Verify on frames from dusk AND full dark — a fixed look reads differently
   at 19:00 and 23:00.

## Render

Per shot encode then concat — resumable, predictable, and each shot starts on a keyframe:
- `-hwaccel d3d11va -ss <t> -t <d> -i <src> -an -vf "scale=1920:1080:flags=lanczos,format=yuv444p,<levels>,<look>,format=yuv420p"`
- `-c:v libx264 -crf 19 -preset veryfast -maxrate 14M -bufsize 28M -g 50 -keyint_min 25 -sc_threshold 0`
- concat demuxer `-c copy`; AAC 320k audio from the master camera; `-movflags +faststart`.
- ~14 s wall per 25 s shot at 1080p on a 16-thread/AMD machine; 4 workers in parallel is stable.

## Audio loudness — two ffmpeg traps

- **`alimiter` defaults to `level=1`** (auto level), which *raises* the output ~1.6 dB and
  silently blows the loudness target. Always pass `level=0`.
- Single-pass `loudnorm` with `linear=true` still behaves dynamically and pumps between quiet
  and loud passages. Run a measurement pass first (`print_format=json`), then apply with
  `measured_I/TP/LRA/thresh` so it is a static gain and dynamics survive.
- A +0.9 dBTP true peak from a linear gain will clip in AAC playback; the `alimiter` at
  -1.5 dB after it only touches overs.

## Verify on the OUTPUT, not the plan

Re-run the obstruction metric on the finished file. **Exclude ±1.2 s around every cut** — a
camera change is a total picture change and the rolling max smears it into ~1.5 s per cut
(120 cuts read as a false 5.8% obstruction). With cuts excluded, real results were 0.00–0.10%
on the clean sets and 2.7% on the knowingly-obstructed one.

Also assert: duration equals expected to 0.00 s, frame count = duration x fps, loudness ≈ -14 LUFS,
TP below -1.0 dBTP.

## Resolve timeline hand-off

Free Resolve has no external scripting; the practical route is an FCPXML of plain
`asset-clip`s (video cuts on the spine, one continuous audio clip) rather than rebuilding
an `mc-clip` multicam.
- Video clips must **not** carry `lane="1"` — that makes them connected clips over an empty
  spine. Only the audio clip takes `lane="-1"`.
- `asset-clip/@start` is in the **source's timecode space**: asset `start` = source start TC in
  seconds, so clip start = TC + (t - file offset).
- Validate by parsing the result and asserting last `offset+duration` equals sequence duration.

## Pitfalls

- NLE auto-sync can misplace a file by tens of seconds; verify every file's offset, not just the first.
- Do not trust the NLE's own multicam to be the reference for your offsets — measure independently.
- A person standing still in front of the lens is invisible to a motion-based metric; pair it with
  person detection if static blocking matters.
