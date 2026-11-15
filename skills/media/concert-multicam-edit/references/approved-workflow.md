# Approved workflow: two-camera concert day -> Resolve timelines

The user approved this form and wants every later day/event done the same way ("do the same style").
Deliverable = Resolve timelines, not graded mp4s.

## What the user gets

- One Resolve timeline per performance in his project, named `<n> <Artist> v<k>`; his existing
  timelines untouched. A change he asks for later (e.g. one set from the A camera only) becomes a
  new `v<k+1>` timeline next to the old one.
- Cuts on V2 (camera switches only, full 4K frame, no crop, no zoom), V1 empty.
- Continuous audio from the `A...` camera on A2, A1 empty, gain untouched. One clip, or one clip
  per A file when the set crosses a recorder split (clips butt-joined; tell him where the join is).
- No grade, no titles on the timeline: he grades and places titles himself.
- Title PNGs (1920x1080 RGBA lower thirds, artist + event name) in
  `<media folder>/Resolve-v<k>/tiitrid/`, the FCPXMLs next to them. A changed title text is a new
  PNG beside the old one; do not rename timelines unless asked.
- A short Estonian report: a table (timeline, length, clips, A-camera share, longest hold), what was
  verified and what was NOT, what he must check himself (audio sync by ear, save the project).

## Use the event.json pipeline (not the Day 1 hard-coded scripts)

`~/Hermes/bluesfest/day2/` (and `day3/`) hold the parameterised version: every `d2_*.py` reads
`event.json` next to it. For a new day: copy `d2_*.py` + `run-scan.ps1` into a new folder, write a
new `event.json`, and change only the three literal strings (FCPXML event name in `d2_fcpxml.py`;
Resolve folder and A-file prefix in `d2_rb.py`; folder in `run-scan.ps1`). Mirror the folder to the
PC (`Hermes/bluesfest/<day>`); it imports `../v2` (venv, YOLOX model, `plan_v3.py`, `rbq.py`).
The `scripts/` copies in this skill are the Day 1 originals with constants at the top.

`event.json`: `media`, `fps`, `A` [[file, frames, start timecode]], `B` [[file, frames]], `names`
{set: artist}, `sets` {set: [start, end]} in A-concatenated seconds, `B_segments`
[{file, a_start, slope, frames, a_from, a_to}], optional `moving_camera` ["B:2", ...].

1. **Probe.** ffprobe every file. Contiguous A timecodes = one recording. Drop seconds-long test
   clips from `B` (the sync fit crashes on them) and say so in the report.
2. **Audio envelopes** `d2_audio.py` on the PC, copy `audio/*.npy` back.
3. **Sync** `d2_sync.py`: one fit per B recording (B recordings are separate, each has its own
   offset). Check `covers A ..` lines for B gaps and overlaps, then write `B_segments`.
   - `d2_sync.py` drops failed windows silently: a fit that looks clean (10/10) can cover only the
     part before an A pause. Require the good windows to span the whole B file, correlate B in
     10-minute chunks to find an offset jump at the A file split, and compare A/B thumbnails of
     the same moment in EVERY set before planning (wrong offset = cuts ~200 s apart).
   - If the coarse lag is ambiguous or windows disagree by a constant, the A camera paused:
     timecode contiguity does not prove continuity. Fit the B file in two parts, split at the A
     file boundary, as two `B_segments` with different `a_start`.
   - Where two B recordings overlap, pick one hand-over time; `d2_fcpxml.py` splits a shot that
     crosses it into two clips.
4. **Set boundaries.** Per-minute p50 of the A envelope is only a first guess (limiter flattens
   sets, PA music between sets is loud). Confirm with A-camera contact sheets (`d2_thumbs.py`,
   every ~150 s, then every 30 s around edges) and 2 s envelope prints. Start after the MC intro
   when the MC talks before the first song; keep encores after a short pause inside the set.
   List every uncertain boundary in the report as a question rather than guessing silently.
   Transcribing MC speech with the local Whisper model is slow on the VPS and added little; use it
   only when picture and loudness cannot decide.
5. **Scan on the PC** as a Scheduled Task (`run-scan.ps1` -> `d2_scan.py A|B` in parallel): person
   boxes, focus tiles, luma tiles and a 64x36 thumbnail per keyframe, only inside the sets.
   About 4x realtime per camera with both running. Unregister the task afterwards.
6. **Beats** `d2_beats.py` on the PC -> `beats.json` (re-run or expect clamping if set ends change).
7. **Framing + scores** locally: `d2_framing.py <sets>` (where a camera was moved/zoomed), then
   `d2_score.py <sets>` (stage ROI per framing segment, obstruction, relative focus, lit share,
   performer seen). Read the printed per-camera lines before planning.
8. **Plan** `d2_plan.py [--cutaway SET:CAM] [--dim SET:CAM:W:THR] [--cam-bias SET:CAM:COST]`.
9. **Visual QA** `d2_qa.py` -> thumbs on the PC -> `d2_qa_sheet.py`: A|B rows with the chosen side
   marked, for EVERY set. Fix the scoring and re-plan until no row has a clearly better other side.
10. **FCPXML + titles** `d2_fcpxml.py` -> `resolve/set<n>.fcpxml` + `report.json`; titles with the
    `make_title.py` layout; copy both to `<media>/Resolve-v<k>/`.
11. **Import + clean + verify** `d2_rb.py [SET ...]` on the PC (one set per ssh call fits the
    timeout; later sets ~2 min each). It stops on any count mismatch and compares exported stills
    with the planned source frame at offsets -2..+2.

## Resolve bridge gates

- Probe `GET /project` first. HTTP 500 there (with `/page` -> null) means Resolve is open with no
  project loaded: ask him to open the project, do not retry blindly.
- Do not import while he is rendering/exporting in Resolve: an import switches the current
  timeline. Prepare FCPXMLs and titles, report, and import when he says the export is done.
  Analysis may run meanwhile at `BelowNormal` priority.
- An FCPXML import yields a stray full-length A video on V1 and per-cut camera audio on A1, even
  for a single-clip timeline; unlink, delete those, then verify V1/A1 empty and A2 covers the
  whole length.
- Non-ASCII timeline names print garbled over ssh; verify with `ascii(name)`, not by eye.

## Scoring rules that the QA sheets forced

- A hand-held or re-framed camera: detect framing segments, compute the stage ROI per segment,
  and penalise samples within ~4 s of a framing change so the cut never shows the move.
- Per-segment ROI focus stays usable in daylight for a moved camera. The frame-wide focus ratio
  (`moving_camera`) is for dark sets with tiny segments only; in daylight it flagged a third of a
  set as soft because wide and zoomed framings differ in content.
- Night sets: a large "foreground" box that is brightly lit is a performer close-up, not a
  blocker (gate on box luma); a nearly black frame is fully blocked whatever the detector says;
  add a term for how little lit stage is in view, raised for a camera that mostly sees
  silhouettes (`--dim`).
- Obstruction above ~0.6 is not worth even a cutaway; add a step penalty there, or the hold
  ramp inserts 6 s shots of someone's back.
- A camera behind a standing crowd for a whole set: `--cutaway SET:CAM` (short audience cutaways
  only) and ASK whether he wants that set from one camera. He chose A-only.
- Prefer the closer view of performers slightly (performer box area) when both are clean.
- When the other camera is blocked for many minutes by one person, a 10-minute single-camera
  hold is correct; report it with the reason instead of forcing cutaways.

## Decisions that are settled (do not re-ask)

- Camera switches only; no punch-ins. Longer single-camera holds are accepted.
- Prefer the camera that is in focus; then the less obstructed one; audience in view is fine.
- Cuts on the beat, min shot ~6 s, typical ~11 s.
- Audio always continuous from the A camera.
- Colour is his job in Resolve. If he asks for help: one neutral primary per camera per set
  (black level, exposure, small white balance), nothing styled.
- Use the Sol model for subagents.

## Worth telling him every time

- The Resolve frame is the full sensor view (wider than a cropped render).
- Which camera is soft, dark, moved or blocked in which set, and any B recording gap.
- Which sets were NOT visually checked, and that focus was not checked at 1:1 if it was not.
- Audio sync was not listened to; he should check lips in a few places and any audio join.
- Save the project (Ctrl+S); the bridge cannot.
- Free disk space on the media drive when it is low and he is exporting.
