---
name: davinci-resolve-editing
description: "Use when editing in DaVinci Resolve via its script bridge."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [davinci-resolve, video, multicam, fcpxml, beat-detection, mcp]
---

# DaVinci Resolve editing (scripted)

## When to Use

Any request to inspect or change a Resolve project from Hermes: recut timelines, switch multicam angles (on beat, on cues), add markers, transfer grades, export frames/audio, render.

## Setup facts

User runs **free** DaVinci Resolve (21.x) on Windows; media on `G:\Active Media\...`. Control goes through the community `davinci-resolve-mcp` repo (`~/Downloads/davinci-resolve-mcp`): `src/CursorBridge.py` runs INSIDE Resolve (Workspace → Scripts → CursorBridge) and serves HTTP on `127.0.0.1:9876`; `src/resolve_mcp_bridge.py` is the MCP server registered in Hermes as `davinci-resolve` (registration: see the MCP reference in the hermes-agent skill). Free Resolve has no external scripting, so everything goes through that in-app bridge.

## Procedure

1. **Check the bridge**: `GET /status` → `connected: true`. If refused, ask the user to run Workspace → Scripts → CursorBridge (only they can start it). After editing CursorBridge.py, copy it to `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility\`, `POST /bridge/shutdown`, and ask the user to rerun it.
2. **Talk to the bridge directly** when MCP tools aren't loaded: GET routes take snake_case query params (`/timeline/clips?track_type=video&track_index=1`; camelCase is silently ignored → always track 1). Most actions are POST JSON (`/render/formats` is POST). The route table is at the bottom of CursorBridge.py — grep it rather than guessing. Use a 240 s timeout: long tracks take >30 s to list. Keep g/post helpers in a scratch `rb.py` because execute_code kernels reset.
3. **Survey before editing**: `/project`, `/timeline`, clips on every track, `/mediapool` (+ `/mediapool/clip/info?clip_name=`). Note which parts the user already cut by hand — edit only the untouched remainder, and never modify the user's timeline: build a NEW timeline.
4. **Export FCPXML** (`/timeline/export`, `FCPXML_1_10`) — it lands as a *directory* `<name>.fcpxml/Info.fcpxml`. It is the ground truth for multicam angle IDs and the timeline→source mapping (`references/multicam-fcpxml.md`).
5. **Before re-importing anything, ask where the user's grades and zoom live** (inside the multicam angles, on source clips, or on timeline clips). An FCPXML import creates a NEW multicam clip and drops timeline-clip grades, so in-multicam grades, Inspector transforms and per-clip Color-page tweaks are lost. Say so up front, not after.
6. **Audio analysis**: extract straight from the source file with ffmpeg (`-ss` before `-i`, `-map 0:<audio idx>`, `-ac 1 -ar 22050`) — seconds even on 100+ GB files. Compute the source offset from the FCPXML of the exact clip you're replacing. Run librosa via `uv run --no-project --python 3.12 --with librosa python script.py`. Recipe: `references/beat-cut-recipe.md`.
7. **Build + import**: rewrite the target `<mc-clip>` into many clips in the FCPXML, then `POST /mediapool/timeline/import` with `{"timelineName": ..., "importSourceClips": true, "sourceClipsPath": "<media folder>"}`. `importSourceClips: false` produces an OFFLINE multicam.
8. **Verify**: compare clip counts/lengths with the original; confirm untouched clips match 1:1; check new source pool items have real `File Path`s. Then export the same frames from both timelines (`/page` color → `/playhead` → `/project/export-frame`) and compare with `ffmpeg -lavfi psnr` plus a side-by-side hstack viewed with vision. Tell the user what you could not verify (offline status, look of the cuts).

## Cutting preferences (this user)

- Live blues/band footage: cut **on the beat** (bar boundaries), not on "drops". Ask what the music is before assuming EDM-style drop cuts.
- "Don't cut too fast": shots of 4 or 8 bars (~8–16 s at ~120 BPM), min ~6 s, mixed so it doesn't feel mechanical; no cuts during between-song talk/applause; cut on the first beat of each new song.

## Pitfalls

- **Media pool lookups are by name and return the first match** (`_find_pool_item`). After an import there are two identically named multicams — delete/edit by name hits the ORIGINAL. Patch the lookup to also match `GetMediaId()` (done in the user's copy) and verify the target via `/mediapool/clip/info?clip_name=<mediaId>` (Date Added differs) before deleting.
- Switch away from a timeline (`/timeline/switch` index) before deleting it.
- Angle cuts on timeline items and grade transfer between multicams have no script route here; the FCPXML round-trip is the working path for angle cuts, and grade transfer between multicams is a manual gallery-still job for the user.
- Render format/codec setting through the API can return `success: false`; check every return before `AddRenderJob`, delete stray jobs, and tell the user if you changed project render settings (TargetDir/audio-only).
- Don't assume a constant timeline→multicam offset from the first clip; hand-slipped earlier clips use different offsets — read the `start` of the specific clip you replace.
