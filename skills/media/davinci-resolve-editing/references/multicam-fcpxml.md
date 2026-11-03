# Multicam in Resolve FCPXML (1.10)

## Structure

- `<resources><media id="rN" name="... Multicam"><multicam>` holds one `<mc-angle name="Angle 1" angleID="<uuid>">` per angle; inside are the angle's asset-clips with `offset` (position in multicam), `start` (source TC in seconds) and `<adjust-transform scale=... position=...>` (the in-multicam zoom).
- Timeline: `<library><event><project><sequence><spine>` of
  ```xml
  <mc-clip ref="rN" offset="<timeline frame>/25s" duration="<frames>/25s" start="<multicam frame>/25s">
      <mc-source angleID="<uuid>" srcEnable="video">...</mc-source>
  </mc-clip>
  ```
  Audio is a separate `mc-clip lane="2"` with `srcEnable="audio"` nested inside the first spine clip — leave it alone when recutting video.
- Times are rational seconds, often reduced (`4837/5s` = 24185/25s). Parse with `Fraction`.

## Mapping timeline frame → source file second

`multicam_frame = timeline_frame + (start - offset)` of the clip in question.
When the angle asset-clip `start` equals the media's start TC: `source_sec = multicam_sec - angle_clip_offset_sec`. Confirm media TC with `ffprobe -show_entries stream_tags=timecode`.

## Recutting

Replace the target `<mc-clip>` (regex on its exact offset/duration/start attrs, DOTALL) with consecutive clips: `offset=a`, `duration=b-a`, `start=a+delta`, alternating `angleID`. Assert the summed durations equal the original duration. Rename the project/event so the imported timeline is distinguishable; write with `newline=""` to keep CRLF.
