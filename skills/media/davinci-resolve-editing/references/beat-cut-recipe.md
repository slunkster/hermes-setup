# Beat-aligned cut plan (live music)

1. Beats: `onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)`; `tempo, beats = librosa.beat.beat_track(onset_envelope=onset, sr=sr, hop_length=512, units="time", tightness=100)`. Live blues ~117 BPM tracked cleanly (IBI p10–p90 within ±10%).
2. Quiet spans (between songs): RMS (hop 512), downsample, moving-average over ~4 s, threshold `0.5 * median(rms)`, keep spans ≥ 4 s. Music segments = gaps between quiet spans.
3. Per segment: cut on its first beat (song start), then step through beats by a random choice of `[16,16,16,32,32]` beats (4/8 bars, seeded RNG for reproducibility); stop when < MIN_SHOT (6 s) remains.
4. Drop cuts inside quiet spans, enforce min shot length, convert `frame = audio0_frame + round(t*fps)`, clamp to the region being recut, keep edges `[region_start, *cuts, region_end]`.
5. Report shot-length min/median/mean/max and cut count to the user. Typical result: median ~9 s, mean ~13 s.

Save beats/plan as JSON in the scratch dir so the plan can be regenerated with a different bar pattern without re-running analysis.
