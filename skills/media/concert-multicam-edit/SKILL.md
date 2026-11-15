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

## Default: follow the approved workflow

The user approved one end-to-end form (camera-switch-only cut chosen for focus and visibility, delivered as Resolve timelines with continuous A-camera audio, title PNGs alongside; he grades and titles himself). For a new day or event, load `references/approved-workflow.md` and follow it; it points to the `event.json`-driven pipeline (`~/Hermes/bluesfest/day2`, copy per day) that replaced the hard-coded Day 1 scripts in `scripts/`, and lists the Resolve bridge gates (no import while he is exporting; no project open = HTTP 500). The sections below are background and pitfalls for the individual steps. Graded mp4 renders are the fallback, only when he asks for finished files.

## User's approved live-concert delivery preferences

- Start with the user's active media folder (`G:\Active Media` for this workflow), not archive copies on other drives. Resolve the project subfolder there before searching elsewhere; archive duplicates can carry stale edits.
- Export 1920×1080 from 3840×2160 with modest reframing; the user dislikes aggressive zoom. Treat approximately 1.2× as a conservative starting proposal, not an approved fixed zoom. Keep a 16:9 crop of at least 1920×1080 source pixels, crop before scaling, and review every camera across changing light and performer positions. No upscaling does not mean lossless re-encoding.
- Keep uninterrupted master audio exclusively from the `A...` camera files regardless of video angle changes. Never splice out music to conceal obstruction.
- When both views are blocked, prefer the less-obstructed live angle. Suitable audience cutaways are allowed, but do not substitute unrelated performance footage as if synchronous.
- Include restrained band-name lower thirds. Preserve old exports and existing Resolve timelines; rebuild in a new version.
- **Previews first, full render only on the user's explicit go.** Iterate with 1–2 minute previews per set (cover the worst spots); never start a multi-hour full render on your own, even to a new folder.
- **No punch-in framings.** The user dislikes zoom-in/zoom-out as cuts: every cut must be a camera switch, one fixed crop per camera (`plan_v3.py --no-tight`). Accept the longer single-camera holds this causes when the other view is blocked.

## Production sequence and gates

1. Open the active media folder and inspect the existing edit read-only. Preserve original files, grades/transforms and previous exports; create a versioned rebuild.
2. Compare synchronized raw A/raw B/old-output frames from the beginning, middle and end of every set. Inspect small batches at readable resolution; an entire evening squeezed into one contact sheet hides color and obstruction problems.
3. Verify source splits, audio offsets and set identities before relying on an old XML. Keep the requested A-camera master audio independent of all video cuts.
4. Test the detector and crop on representative daylight/night/foreground-blocker examples. A successful model import or a few detections establishes feasibility, not calibrated full-video accuracy.
5. Start a resumable full-range analysis job, then build the new edit from verified usable intervals. Benchmark a real clip on the target machine before estimating runtime; compare CPU and `-hwaccel d3d11va` where supported rather than assuming GPU inference or decode performance.
6. Verify moving daylight/night color samples and rendered lower thirds before the full render; then inspect the finished outputs, not only the cut list.

When asked to start a full edit, distinguish **environment prepared**, **analysis running**, **render running** and **verified export**. Do not report analysis or rendering as started until the real process has produced progress. A title preview or generated script is not a full edit.

## First, establish the real shape of the footage

`ffprobe -show_format -show_streams` every file before planning anything. Check for:
- **Continuous timecode** (Panasonic `timecode` tag): lets you concatenate split files exactly.
- **Creation time vs file mtime**: consumer cameras often have the card clock wrong by weeks.
  Use the tag, not mtime, to map recording time to wall clock.
- **Split points**: a 4 GB/3 h recorder split is one recording, not two takes.
- **Pairwise durations**: cameras started/stopped at different times; compute coverage gaps.

Ask whether angle count really is what the folder suggests — a 7-file, 330 GB folder can
still be only two angles, which changes the edit from "multicam" to "A/B".

## Sync: use envelope correlation when waveforms are unreliable

Two cameras at different positions in a reverberant room with AGC produce waveforms that
correlate at ~0.00. Do not conclude the offset is unknown and do not trust the NLE's
auto-sync.

Instead: decode both to 8 kHz mono, take **10 ms RMS envelopes** (log), and scan the offset
grid on 30 s windows, averaging the normalised correlation across many windows. Peaks come
out sharp (0.30–0.50) and agree with a correct offset to ~10 ms.

Then **re-scan across the recording and after each file split** to measure drift. Record the offset sign explicitly (for example, `B_time = A_time - offset`), validate it with a synthetic known-delay test, and report peak ambiguity. Neither an old XML offset nor a single correlation peak proves synchronization.

## Obstruction map

**Do not use motion-only scores as a clean-shot certificate.** Stationary spectators can obscure most of the stage while scoring as motionless; real output review must include semantic foreground-person detection and visual checks. Define camera-specific performer/stage regions, distinguish foreground audience from musicians, retain uncertain cases for review, and expand blocked intervals before/after entry/exit. Use motion only as a supplementary crossing signal. When both cameras are blocked, flag the interval rather than claiming a clean edit; agree on cutaways or the least-obstructed angle without silently deleting performance audio.

Per-frame metric on a 160x90 luma downsample: fraction of pixels whose |delta| from the
previous frame exceeds 35. Musicians moving sit at ~0.001–0.003; a body sweeping the lens
spikes to 0.4–0.7. Smooth with a rolling max (~±0.75 s) and threshold. Mask = `rolling_max < 0.03`.

Cost: ~7x realtime for 4K H.264 decode. Only cover the ranges you need (the sets, plus
margin) — breaks between sets do not need mapping.

**Pitfall that will silently ruin timing:** reading a pipe in fixed-size chunks. `stream.read(n)`
returns short reads, and if you prepend the previous frame and then drop the first score you
lose one frame per chunk; over 5 h that is ~30 s of accumulated offset. Use a `read_exact()`
loop and keep exactly n scores per block.

For resumable full-frame analysis, plan half-open intervals on an integer frame grid,
cap chunks at 300 seconds, and split them again at recorder-file boundaries. Decode
one preceding frame for each chunk (or explicitly fetch the preceding file's last
frame at a split) so chunking does not erase boundary motion. Store native/source/
reference integer indexes alongside timestamps; keep the sync offset provisional in
metadata until verified. Send decoder stderr directly to a log file, not an unread
pipe. Publish data atomically and mark a chunk complete only after decoder exit zero
**and** an exact frame count; verify output hashes and analysis/source signatures
before resuming. A completion flag alone is not evidence of a usable chunk.

### Calibrate semantic detection before using it for cuts

Start with person detection at roughly 2 Hz plus full-rate motion cues. Score foreground-person overlap with camera-specific performer/stage regions, not total people count. Treat size and bottom-edge gates as calibration parameters: a small head may cover a face, while a large onstage musician is not an obstruction. Preserve uncertain intervals for review and treat decoder/model failures as unknown, never automatically clean.

See `references/obstruction-validation.md` for the validation procedure, tested detector baseline, temporal padding and output checks. Do not use a workspace research note as an unquestioned production specification.

## Set boundaries without a schedule

Loudness plateaus alone are unreliable (between-set PA music is loud, and a limiter flattens
everything). The discriminator that worked: **fraction of seconds above the limiter ceiling**
(e.g. >73.5 dB) in 2-minute bins. Playing sets sit at 0.6–1.0; breaks at 0.00–0.17. Refine
edges with a 5 s mean and a 60 s hold test. Cross-check the last-note time with spectral
flatness — applause is broadband (flatness ~0.3) while the final chord is harmonic (~0.07).

Ignore single loud bursts (30 s of soundcheck/line check) when locating a set start; require
sustained energy.

## Camera selection that actually avoids obstruction (worked on Bluesfest Day 1)

Threshold/greedy selectors fail on night sets where both views are partly blocked: they jitter
(0.5 s shots) and still hold 10+ minutes. What worked (`~/Hermes/bluesfest/v2/plan_v3.py`):
- Score per detector sample = clipped union of *foreground* person boxes over a **weighted
  performer band** (frame y .34–.60 weight 1, .60–.74 weight 0.4) inside the camera's stage x-range.
  Heads at the bottom edge barely count; a back in front of the singer counts fully.
- Per-frame obstruction = rolling max ±3 samples (fail closed = 1.0 on gaps).
- Step cost `o + max(0,o-.25) + .25*motion_spike + 3*(o>.85)`. The last term matters: a view above
  ~0.85 is a black silhouette, not an "audience shot" — without it the DP cut to black frames.
- **Semi-Markov DP (Viterbi over framing × shot-duration states)** on the 12-frame detector grid:
  min shot 6 s (hard), no penalty <12 s, small 12–24 s, larger 24–45 s, ramping to a cap at 90 s,
  cut cost lower on downbeats, higher in quiet (talk/applause) spans, free on a song's first downbeat.
  Linear-only hold penalties never split long holds; the ramp is what creates occasional cutaways.
- Add **tight punch-in framings** (2560×1440 or 2880×1620 from 4K, still downscaled to 1080p) as
  extra DP states, scored only on what the punch-in shows. Auto-frame from non-foreground person
  boxes on stage (p3–p97 extents); when a standing crowd contaminates that (night set), frame by
  hand from an inspected frame. Punch-ins broke every >60 s hold in sets 1–3 and most in set 4 and
  cut side silhouettes out of frame. Keep the wide↔tight scale jump ≥1.2× or it reads as a glitch.
- Visually verify with A|B contact sheets at cutaways, largest-difference shots and random shots
  before rendering; this is what caught the cut-to-black problem.

## Autofocus misses: pick the camera that is in focus

Cameras on autofocus go soft for seconds to minutes (the user: "it cuts to a point where the artists are very out of focus"). Obstruction scoring cannot see this. What worked (`~/Hermes/bluesfest/v2/focus_scan.py`, `focus_score2.py`, `plan_v3.py --focus`):
- Scan every keyframe (`-skip_frame nokey`, ~9× realtime for 4K) as 1080p luma; per 60 px tile store fine gradient energy (1080p) and coarse (after 4× box downscale). Stream frames from the pipe; do not buffer a set in memory.
- Score = per-tile fine/coarse ratio divided by the SAME tile's 80th-percentile ratio in that set, median over the textured stage tiles (static detail: LED bars, drum kit, truss), spectators masked, then normalised by the camera's own p80. ~1.0 sharp, ≤0.65 visibly soft.
- A single frame-wide ratio over performer boxes failed: a sharp foreground head scores high while the stage is blurred, and content changes the ratio.
- Validate at 1:1 source pixels. Downscaled contact sheets hide defocus completely and made a correct metric look wrong.
- Planner: add `0.6 * blur` to the step cost, blur = clip((0.85 − rel)/0.2, 0, 1), unknown = 0. Soft share of the chosen angle fell from 11 % to 1.6 % (day set) and 7 % to 0.7 % (dusk); with a standing crowd it only halved, because obstruction competes.
- The per-set normalisation is blind to a camera that is soft for a WHOLE set (underexposed, heavy in-camera noise reduction, focus slightly off): the user still sees it ("the second set is soft/looks weird"). Compare 1:1 source crops of both cameras in every set; where one is soft throughout, bias the planner against it (`--cam-bias 2:A:0.3` moved it from 63 % to 35 % of screen time with obstruction almost unchanged) and add a luma-only `unsharp=7:7:0.9:7:7:0` after the grade. Sharpening only partly helps; say so.
- `np.load` on an `.npz` re-decompresses the whole array on every `z['key'][i]`; copy arrays out once.
- A preview whose start lands a frame or two before a cut makes the concat mux fail ("Non-monotonic DTS"); shift the offset.

## Long Windows jobs over SSH

(`ssh pc` works only while the dual-boot desktop is booted into Windows.) A job run inside `ssh pc "..."` dies (or loses stdout, `OSError: [Errno 22]`) when the SSH session
drops. Launch long renders as a Scheduled Task (`Register-ScheduledTask` + `Start-ScheduledTask`,
log to a file) and poll the log. Short previews are dominated by per-shot startup/verification;
the full render ran ~2.3× realtime (4 workers, `-hwaccel d3d11va`, x264 fast CRF18).
Verification: `ffprobe -count_frames` is itself a full decode; one counted probe + one ebur128
decode of the muxed temp file is enough. Publish by hardlink and do a header-only readback —
a second full decode added ~10 min per hour of output for no new information.

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
- Concatenate shots covering `[start, end]` **with no gaps** and keep audio as one uninterrupted reference slice. This guarantees timeline continuity, not source synchronization: independently verify each camera's offset, drift and file-boundary mapping.
- Prefer performer visibility over beat snapping or a target shot length. When neither angle is clean, apply the user's less-obstructed-view policy and retain an explicit exception interval; never label that interval obstruction-free.

## Grade (8-bit 4:2:0 source, two mismatched cameras)

**Do not automatically match whole-frame RGB percentiles or apply a global warm look across an entire festival.** Different sky, canopy and audience proportions bias these statistics; this workflow has produced visibly green/yellow, over-bright output. Start from the ungraded originals, compare synchronized views of shared stage/neutral objects, verify input range/gamma, and grade each camera separately for daylight/dusk/night. Preserve intentional colored stage lights. Approve actual before/after video samples before a full render.

1. Measure per-channel p10/p50/p90 over matched scene regions in simultaneous frame pairs, as a diagnostic rather than an automatic correction.
2. Match exposure/contrast conservatively using shared stage details, not whole-frame quantiles. Only adjust RGB channels when neutral reference patches support that change.
3. Check white balance on a real shared neutral (gravel, concrete) before correcting it; different framing and colored lighting can mimic a camera white-balance mismatch. Do not infer a log profile solely from flat appearance, or assume BT.709 metadata proves the camera's picture profile.
4. Default to natural source colors with minimal correction. Do not add a lifted toe, warm tint or extra saturation without reviewing a short moving sample from daylight AND full dark; real colored stage lighting must remain intentional.
5. "Natural source colours" can still read as grey: overcast daylight + grey canopy + a flat
   camera profile. The user rejected an ungraded deliverable as "liiga hallid". What was accepted:
   per set (daylight / dusk / night) and per camera, in 16-bit RGB right out of the downscale
   (`scale=...:in_color_matrix=bt709:in_range=tv,format=gbrp16le` ... `scale=out_color_matrix=bt709:out_range=tv,format=yuv420p`):
   master `curves` S-curve (blacks 0.06→0.025, 0.8→0.86), `vibrance` 0.1–0.2, and a
   luma-preserving saturation **`colorchannelmixer` matrix** (BT.709 weights, s≈1.1–1.2).
   Measure luma p1/p50/p95 per camera per set first: one camera was ~1.5 stops under in one set
   (median 0.08 vs 0.23) and needed its own mid lift. Pitfalls: `huesaturation=saturation` barely
   changes anything; `eq` is 8-bit only; vibrance > ~0.2 turns beige sand yellow; without explicit
   matrices the RGB round trip uses BT.601 and shifts hue. Tag output `-colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv`.
   Show the user a before/after still from the real render pipeline, not only local tests.
0. **Start with the neutral primary, and only escalate if the user asks.** The user rejected both a styled look and an elaborate match (per-tone gains, hue rotation, vibrance) as "not good... just make it look neutral, without any weirdness". Default recipe (`~/Hermes/bluesfest/v2/neutral.py`): reference camera as shot plus a soft highlight shoulder; other camera per set gets only per-channel black level + gain (`y = g_c*(x - black_c)`) fitted on stage-ROI quantiles, white balance limited to ±4 % (exposure-only when stage and canopy disagree about the cast), gain capped where the reference view is blocked, luma-only drift. No saturation, vibrance, hue or contrast curve. Item 6 below is the escalation, not the default.
6. **Camera matching (user: "most important that the two cameras look alike", "cam 1 is too magenta").**
   Pick one camera as reference (B) and match the other (A) to it *before* one shared look per
   lighting regime. What worked (`~/Hermes/bluesfest/v2/match_v5.py`, `build_v5.py`):
   - Model, not free curves: luma `a + b·x^g` from stage-box luma quantiles; one luma-preserving RGB
     gain set per tone knot (0.08/0.3/0.65/0.9); a small shadow-only per-channel offset; one saturation
     factor. Free per-channel histogram matching invents hue twists, because the two viewpoints see
     different content.
   - Hand-check "shared" patches: from different angles the same canopy can be sunlit in one view
     and shaded in the other. Draw the boxes on frames and vision-check them before trusting them.
   - Tune the per-set base on ~6 synced still pairs per set, with an objective residual: A−B mean
     (R−G, B−G) per luma band in the stage box AND the whole frame. Iterate 2–3 times with damped
     updates, clip gains to ±12%, and leave the highlight band mostly alone (it is LED/content dominated).
   - Lighting changes: one camera may auto-expose while the other drifts darker at dusk. Add a
     time-varying correction for how the A/B relation drifts against the set mean (±2 min windows,
     10 s grid, rolling median, clip ±0.6 stop / ±3% chroma). Skip it where the drift is crowd noise:
     a standing audience makes it slam between the limits.
   - Saturated stage LEDs render at different hues per sensor (A 247° vs B 262°). Check the
     circular-mean hue of chroma>0.15 pixels per camera and align with
     `huesaturation=hue=12:colors=b:strength=1..5`. Hue-selective desaturation
     (`huesaturation=saturation=-0.9:colors=c:strength=40:lightness=1`) neutralises a sky-lit cyan canopy.
   - Pitfalls: (1) per-channel gains with a hard ceiling (R 0.97, G 1.0, B 0.91) turn every
     near-white area green/teal. Use a soft shoulder (tanh knee from ~0.72) and fade the gains to 1
     toward white. (2) The shared look's vibrance/saturation amplifies any small residual cast, so
     evaluate after the full chain. (3) `hqdn3d` has no RGB support, and in a gbrp16le chain ffmpeg
     silently auto-inserts an unspecified-matrix conversion. Denoise in `yuv444p16le` right after
     the downscale, then convert to RGB with explicit BT.709. A one-stop lift on night footage raised
     x264 CRF18 bitrate +64%; light hqdn3d (2:1.5:6:4.5) brought it back without visible smearing.
   - Verify at real cuts: extract the frames 0.2 s before/after every camera change in short
     rendered previews (`cut_pairs.py`) and compare against the previous deliverable at the same cuts.
     Take the camera labels from the plan, never from memory.

## Lower thirds

Verify the artist's spelling against an authoritative lineup, and map that name to the actual set using announcements/project evidence; filenames and published running order are not sufficient alone. Keep source identifiers unchanged even when correcting display text. Add song titles only from a verified set list.

Use a restrained lower-left treatment: readable cream/white artist name, smaller festival name, translucent dark backing and a muted accent. Keep the graphic inside title-safe margins and off performers' faces. A transparent 1920×1080 PNG is a portable asset: apply alpha fades with `fade=t=in:st=1:d=0.4:alpha=1` and `fade=t=out:st=9:d=0.4:alpha=1` before overlaying. These timings are starting values, not mandatory for every set. Inspect a frame extracted from the rendered proof and fully decode that proof; previewing the source PNG alone does not verify compositing.

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

Re-run semantic obstruction checks on the finished file and independently check selected source intervals against the obstruction map. Exclude a small cut neighborhood only from the frame-difference statistic, because a camera change creates a false motion spike. Do not exclude those frames from visual/person checks: a cut can land directly on a blocked view. Review cut boundaries and every unresolved both-blocked interval explicitly; a low motion score is not proof of a clean export.

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
