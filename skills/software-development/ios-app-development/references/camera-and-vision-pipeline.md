# Camera capture + on-device vision/AI pipeline

For apps that analyse the live camera feed and guide the user (framing coach, auto-zoom, smart capture).

## Split the app into three loops at three timescales

| Loop | Rate | Tech | Job |
|---|---|---|---|
| Analyse | 10–15 fps | Vision | subject boxes, horizon, saliency, aesthetics score |
| Reason | 0.3–1 fps or on tap | Foundation Models | semantics + one phrased instruction |
| Control | 30–60 Hz | AVFoundation + Core Animation | zoom ramp, overlay, haptics, shutter gate |

An LLM/VLM never drives the control loop: inference is hundreds of ms to seconds per frame, so it can only explain or make semantic judgements. Deterministic geometry does the work.

## The control model: zoom is not pan

Programmatic zoom scales about the optical axis; it cannot move the camera. Every "adjust the shot" instruction therefore decomposes into exactly four channels — zoom (automatic), pan/tilt (human), distance (human), shutter timing (can be automatic). Design the guidance UI around that split or you ship an app that zooms into a badly composed crop.

## Capture setup

- `AVCaptureSession` with a **virtual device** (`builtInDualWideCamera` / `builtInTripleCamera`) so zoom spans lenses without a hard cut.
- `AVCaptureVideoPreviewLayer` for display — Apple's stated most-efficient path. Wrap it in `UIViewRepresentable`; do not push frames through SwiftUI `Image`.
- `AVCaptureVideoDataOutput` with `alwaysDiscardsLateVideoFrames = true`, YUV 420, capped around 720p–1080p. Downscale before analysis (≈720p long edge for Vision, ≈512–768 for an LLM). Ask for that size in `videoOutput.videoSettings` (`kCVPixelBufferWidthKey` / `HeightKey`, e.g. 1280×960 for 4:3) so a full-sensor format does not push 12 MP frames into Vision every tick; keep a Core Image downscale as the fallback for devices that ignore the hint.
- **Choose the format by pixel count, never by first match.** `device.formats.first { is4x3 && fps >= 30 }` routinely lands on a low-resolution mode, and the active format simultaneously caps preview sharpness *and* the still's `maxPhotoDimensions` — so the viewfinder looks soft and photos come out small while everything still compiles and runs. Filter for shape and frame rate, then `max(by: pixelCount)`, and print the chosen dimensions once so sharpness claims are checkable from the device log.
- `AVCaptureDevice.RotationCoordinator` (iOS 17+) for orientation.
- Rotating only the **preview** connection leaves the saved still misoriented relative to what the user framed. After `addOutput(photoOutput)`, set `photoOutput.connection(with: .video)?.videoRotationAngle` (guarded by `isVideoRotationAngleSupported`) to the same angle as the preview; leave the data-output connection at 0 so the constant you pass to Vision stays consistent.
- Pin the physical lens while auto-zooming: `setPrimaryConstituentDeviceSwitchingBehaviorLockedWithDevice(_:)` (iOS 27+), guarded by `primaryConstituentDeviceSwitchingBehaviorLockedWithDeviceSupported`. Without it the system swaps lenses mid-ramp and the image character changes under the user's nose.

## Lens map: factor 1.0 is not "1x"

- On `builtInTripleCamera` / `builtInDualWideCamera`, `videoZoomFactor` 1.0 is the **0.5x ultra-wide**. Read `virtualDeviceSwitchOverVideoZoomFactors` (iPhone 16 Pro Max: `[2.0, 10.0]`): the first entry is the main lens ("1x"), the last is the tele optical limit. Start at the first, cap automatic zoom at the last; `maxAvailableVideoZoomFactor` (189) is digital mush.
- `ramp(toVideoZoomFactor:withRate:)` rate is **doublings per second** (`pow(2, rate*t)`), not factor units: `rate = |log2(to/from)| / seconds`. It is imported non-throwing; calling it without `lockForConfiguration()` raises an uncatchable ObjC exception.
- Pick the format explicitly: highest-resolution 4:3 with ≥30 fps. "First 4:3 match" silently gives a soft preview and small photos.

## Framing apps: decide once, then guide

- Re-deciding the framing every frame makes the guide jump and the score swing 40 points/s. Acquire a stable subject (~8 frames), plan once, commit.
- Plan by **candidate search**: photo-shaped crops (a square in normalised space of a 3:4 frame *is* the 3:4 photo) around every subject — faces, each person, the whole group, person+pet, animals (`RecognizeAnimalsRequest`), salient objects, and the unzoomed view — at several sizes and placements. Rules veto (sliced face, person split at a side edge, pet cut in half); `CalculateImageAestheticsScoresRequest` on the cropped pixels ranks the rest (`overallScore` is −1…1).
- Pick finalists per subject, not by global heuristic rank — otherwise one subject's variants crowd out the group shot and the uncropped view.
- Size crops to fit the subject's width as well as its height, and place people by headroom, not by eye line (an eye-on-third full-body crop cuts the head off).
- Clip detections to the visible frame before judging cuts, and score the unzoomed view against the real subject so "already well framed" can win.
- Keep subject identity with stateful `TrackObjectRequest`; re-detecting each frame lets the subject silently change. The tracker cannot follow a zoom ramp: pause it, then re-seed at the box projected about the centre (`0.5 + (p − 0.5)·k`). On tracker loss, re-find by detection near the last box before declaring "lost".
- Never zoom before the chosen crop is centred: zoom is centred, so an off-centre crop leaves the screen. Show the frame at the current zoom, let the user dock it, then one ramp.
- Alignment must be reachable by panning alone: judge centre distance with hysteresis, not IoU against a photo-shaped target.
- Arrow and text must name the same motion — the way to turn the phone. Showing the frame's travel (the opposite direction) next to "Pan right" reads as a contradiction.
- Verify planner quality offline: compile the planner file for macOS together with a small harness, run it on a varied photo set, render picks to a contact sheet and review it visually.

### Learning composition from expert photos (verified)

- Learn the rule weights with a linear pairwise ranker (RankNet + Adam, plain Swift; no ML stack needed) over measurable rule features. Use attention-heat distribution (edge mass, thirds/centre distance, spread, balance, mirror symmetry), cut objects/faces/people, eye height vs the upper third, lead room from face yaw (nose offset between the eyes in `DetectFaceLandmarksRequest`), headroom, and horizon on a third. Add `CalculateImageAestheticsScoresRequest` as one feature. Compile the trainer from the **same** feature source files the app ships.
- Positives are Wikimedia Commons Featured/Quality pictures. A 700-photo set fetched as 960px thumbs via the API takes ~30 min, and Vision feature extraction for 6k crops takes ~20 s on an M-series Mac.
- **Compare only crops of the same size.** Expert frame vs smaller re-crops gives 99.6% held-out accuracy and a useless model: it learns "wider is better", and rule weights come out with the wrong sign. Instead make positives by zooming the expert frame about its own subject point (eyes, else attention centroid). This homothety keeps the photographer's placement. Negatives are same-size shifts, an edge through the subject, and a bullseye. Honest result: ~90% held-out pairwise accuracy vs ~64% for aesthetics alone.
- At runtime the model therefore knows *where*, not *how big*. Score a crop against similar-size peers (side ratio 0.85–1.18, z-scored and clamped), and let rules own size (fill bands, integrity, zoom cost). Add a local search that slides each finalist ±8% to the model's preferred position, accepting only moves that do not reduce integrity. Feeding the raw learned score across sizes made it zoom 4–5× into faces and cut a dog's ears.
- Bullseye vs expert placement came out near a coin flip on expert photos, so don't hard-code "never centre".
- `DetectHumanRectanglesRequest` defaults to `upperBodyOnly = true`. For planning set it to `false`, or the planner believes head-and-shoulders is the whole person and crops legs and companions freely.
- Detection confidence can't be one threshold: real faces in a group score 0.30 and real people 0.11, while blurry desk clutter also yields a face. Accept weak detections only when corroborated (face inside a person box, ≥2 solid faces).
- Scene labels are noisy: a desk photo gets "outdoor 0.21, hill 0.20". Treat a scene as outdoor only on labels ≥0.4 with no indoor label in the top 8. Vision's horizon gives an angle only; find its height via the strongest straight luminance step across a 72×96 grayscale downscale.
- Group rule: a crop that keeps some faces must not drop same-size faces at the same height (penalise each). Without it a saliency crop drops two of seven people.

### Declutter zoom without losing detail (verified)

- Split the view into **keep** and **clutter**. Keep = subject + people/pets with it + objects overlapping it + attention-heat blobs connected to it. Clutter = stray attention blobs + Sobel edge energy outside the keep box (busy texture). Generate tighter crops by zooming about the subject key point (preserves placement), then solve the feasible origin interval so every essential keeps a margin. On sides where the base framing already cut the subject, the tight crop may not cut further.
- Judge clutter on **one shared map** (main subject = the anchor with the most attention, over the whole view) for every candidate. Per-candidate maps or a neutral 0 for horizon/scene crops make the comparison unfair, e.g. the full frame beat a horizon-on-third crop.
- Add an attention-kept penalty, `0.5 · max(0, 0.65 − kept)`. Without it a tight crop of a tiny side building beat the church.
- Learned placement z-scores are meaningless for the full view (no same-size peers): set z = 0. The non-learned formula branch also has a different scale; mixing branches made the full frame win.
- Pet–person proximity must use **box gap**, not centre distance. A dog on a leash at the feet is far from the person's centre.
- Lossless zoom: `activeFormat.secondaryNativeResolutionZoomFactors` plus switch-overs (16 Pro Max: `[1, 2, 4, 10]`; `videoZoomFactorUpscaleThreshold` 1.0). Cost digital zoom by `log2(upscale)` and snap down to a stop when ≤15% past it. A cost of 0.10/doubling over-penalised 1.4x crops; 0.05 works.

### Smoothness (verified)

- Pass the frame's capture time (`CMSampleBufferGetPresentationTimeStamp`, host clock = `CACurrentMediaTime`) through to the UI. One Euro filter the subject box: centre minCutoff 1.0 Hz / beta 6, size 0.35 Hz / beta 1.5. Size noise matters most, because the photo frame is several times the subject.
- Draw in `TimelineView(.animation(minimumInterval: 1/60))` with a class follower held in `@State`. Predict the box to now (velocity × age, cap 150 ms), ease with τ ≈ 50 ms, and snap on jumps > 0.35. Derive the arrow from the drawn frame. Fade with an opacity ramp rather than `if` pops.
- Re-seed the smoother with the projected box after each zoom ramp.
- Zoom ramp duration 0.6 + 0.35·doublings s (≤ 1.3 s).
- Guard `@Published` assignments with `!=` for per-frame values; every set fires `objectWillChange`.

### Field data beats curated test photos (verified)

- Curated photos are already well framed and flatter a planner that fails on real viewfinder frames. Record every plan on the device: frame JPEG plus JSON of detections and ranked candidates in Documents. Add a 👎 button that marks one as flagged, and mark the plan when the user shoots. Pull with `xcrun devicectl device copy from --domain-type appDataContainer --domain-identifier <bundle> --source Documents/plans --destination ...`.
- Replay with the **phone's recorded detections**. The Mac's Vision models found 1 of 4 small faces where the phone found 4.
- Group failures found this way:
  - Salient-object anchors (backdrop, the screen the people are on) won over people. When faces or people are present, drop object anchors.
  - The learned model's portrait habit (eyes on the upper third) penalised full-length group crops. Compare learned scores only among the **same kind** of framing.
  - Vision returns inconsistent person boxes (one full body, neighbours head-and-shoulders), so the size filter split the group. Extend each person box down to the body its face implies (adult ≈ 7.5 heads), synthesise bodies for faces without a box, and group by face scale.
  - Group crops must fit the group's width at every shot size. Widen the face union by about one face-width per side for shoulders.
  - Penalise any crop that leaves a same-scale group member mostly out.
- Reject plans with aesthetics < 0.2 and no people (a blurred hand over the lens), with a 1.5 s cooldown.

## Zoom controller (where these apps die)

```
target = clamp(current * (subjectHeightPx / (desiredFraction * frameHeightPx)), 1, practicalCeiling)
// then: EMA smoothing ~0.15, ~8% deadband, rate-limited ramp,
// skip while isRampingVideoZoom or while a still is being captured
```

- `maxAvailableVideoZoomFactor` is not a usable upper bound on a virtual device: it reports roughly 189× of digital upscaling. Define your own ceiling (≈5× — the optical tele limit on current Pro phones; 3× is too low to fill a 60%-of-frame target from across a room) and clamp the **crop side** to `1/ceiling` as well, so the ghost frame and the zoom pill can never disagree. A 6%-wide face otherwise yields a 9× suggestion, which is mush and reads as a bug. Apply the same ceiling to pinch zoom.

- No deadband plus hysteresis = visible zoom hunting, which reads as "broken" instantly.
- `ramp(toVideoZoomFactor:withRate:)` is imported **non-throwing** (rate is `Float`), so a `try` on it is a warning that catches nothing — without exclusive access it raises an uncatchable ObjC exception. Only `lockForConfiguration()` / `unlockForConfiguration()` belong in the `do`/`catch`:

```swift
try device.lockForConfiguration()
device.ramp(toVideoZoomFactor: target, withRate: 8)   // no try
device.unlockForConfiguration()
```

- Assigning `videoZoomFactor` directly cancels an active ramp and snaps to the new value.
- A user pinch or a lock always wins; auto-zoom must be visible and reversible.

## Analysis with Vision

Verified request names in current SDKs: `GenerateObjectnessBasedSaliencyImageRequest` (what the subject is), `GenerateAttentionBasedSaliencyImageRequest`, `DetectFaceRectanglesRequest`, `DetectHumanRectanglesRequest`, `DetectHumanBodyPoseRequest`, `DetectHorizonRequest` (tilt/level), `CalculateImageAestheticsScoresRequest` (score + `isUtility`), `GeneratePersonInstanceMaskRequest`, `ClassifyImageRequest`, `DetectLensSmudgeRequest` ("wipe the lens" prompt).

Batch every request into **one** handler call — the variadic overload prepares the buffer once instead of six times:

```swift
let handler = ImageRequestHandler(pixelBuffer, orientation: .right)  // .right = portrait back camera
let (saliency, faces, humans, horizon, aesthetics, labels) = try await handler.perform(
    GenerateObjectnessBasedSaliencyImageRequest(),   // SaliencyImageObservation
    DetectFaceRectanglesRequest(),                   // [FaceObservation]
    DetectHumanRectanglesRequest(),                  // [HumanObservation]
    DetectHorizonRequest(),                          // HorizonObservation?  <- optional, needs if-let
    CalculateImageAestheticsScoresRequest(),         // ImageAestheticsScoresObservation
    ClassifyImageRequest()                           // [ClassificationObservation]
)
```

- `salientObjects` is `[RectangleObservation]`, **not** `NormalizedRect`: reach `.boundingBox` (conforms via `QuadrilateralProviding: BoundingBoxProviding`) then `.cgRect`.
- `horizon.angle` is a `Measurement<UnitAngle>`: `.converted(to: .radians).value`.
- Subject priority that works: faces → largest human → largest salient object. Union the face boxes so a group reads as one subject.

Vision returns boxes, not taste. A usable composition score is a weighted deterministic function over: subject size ratio, distance from rule-of-thirds intersections, headroom, lead room in the look direction, horizon deviation, background clutter (saliency spread / edge density), symmetry. Output the score plus **one** highest-impact fix; refresh no faster than ~400 ms.

## Temporal stability — the difference between a coach and a twitch

Per-frame detections jitter: on a static scene the same pipeline scored 42 ↔ 87 within one second and the ghost frame jumped between objects. Stabilise before scoring, or the app feels broken no matter how good the geometry is.

- Median (component-wise) of the last ~5 subject rects — not an average, which smears across two different objects.
- Hold the last box through up to ~3 consecutive misses, then clear it, so a single dropped detection does not blank the ghost.
- EMA the final score (~0.3) so the alignment ring, haptics and auto-fire gate cannot chatter.
- Keep auto-fire behind N consecutive `isAligned` frames plus a cooldown, and let a pinch or a manual capture cancel any pending state.

`TrackObjectRequest` (a stateful class) supersedes the median filter once the interaction works — see *Commit to one shot* below for seeding order, loss handling and fallback selection.

## Commit to one shot — the decision layer most guide apps get wrong

Re-deciding the framing every frame earns the same review comment every time: "it keeps changing its mind". The fix is a state machine, not a better score.

```
searching --(N consistent frames)--> framing --(centred && sized)--> aligned
     ^                                  |
     +-- subject lost > ~2.5 s | pinch | explicit re-frame
```

- **Acquire slowly on purpose.** Require ~8 consecutive frames (~0.7 s at 11 fps) before committing. Compare frame-to-frame (IoU ≥ ~0.35), then commit only when the window as a whole agrees (first vs last ≥ ~0.5); a strict first-vs-latest test never passes, because every detector breathes a few percent per frame.
- **Commit to a value object, not a running decision.** Freeze zoom factor, ghost centre, subject height fraction and aspect into one `LockedShot`; the ghost is derived from it, so it cannot drift while the user moves.
- **Act once, correct once.** Ramp to the locked zoom (~0.55 s: `rate = Δzoom / 0.55`), then allow exactly one corrective ramp behind a per-shot flag — a box measured at 1× under-reports subject size, so the first ramp routinely lands big or small. Without the flag this becomes a zoom control loop.
- **Give up slowly.** Release only on subject loss past ~2.5 s, a user pinch, or an explicit re-frame tap. Anything faster reintroduces the mind-changing.
- **The ghost is the photo, not the subject.** The target frame carries the output aspect. On a 4:3 sensor a 4:3 crop is a **square in normalised coordinates** (a 3:4 rectangle on a 3:4 screen); building the ghost from the subject's own width and height makes "line up the frame" mean nothing. Clamp it inside `[0, 1]`, and when the zoom ceiling stops you short, shrink it to what is actually achievable: `achieved = desired * (target / wanted)`.
- **Frame size that survives review**: desired subject-height fraction by scene type — group 0.76, food 0.72, portrait 0.70, animal 0.68, general 0.62, architecture 0.58, landscape 0.56. Lower values read as "the frame is tiny" even when the geometry is correct.

### Aligned must be reachable by panning alone

IoU against a photo-shaped ghost tops out near 0.65 for a wide subject, so an IoU gate above that can never be met however well the user frames — it reads as a broken app, not a strict one. Gate on the two quantities a pan can actually change:

- centre error < ~0.10 of the frame, and
- subject height within ~18% of the target height.

Keep IoU for diagnostics and logs only.

### Keep the subject's identity

Per-frame re-detection silently swaps the subject: saliency returns whatever is most salient *now*, so a bottle becomes a cloth mid-shot and alignment never completes.

- Seed `TrackObjectRequest` (stateful class; `DetectedObjectObservation(boundingBox:)`; optional `Result`) **after the zoom ramp settles**, not at lock time — seeded earlier it watches the box grow under the zoom and loses the object.
- A `nil` result means lost: hold the last box through ~3 misses, then reseed from detection.
- On detection fallback, do **not** choose the candidate with the highest IoU against the ghost: a scene-filling box always overlaps more than the small object you locked, so identity drifts to the biggest thing in frame. Score centre distance plus size similarity, with a size gate (height within ~2× of target).
- Overlay hygiene: hide the thin subject box once it covers more than ~45% of the frame — that is the scene, not a subject, and it only adds noise around the target.

### The direction cue has two defensible conventions

An arrow can point where the **subject must travel** (subject centre → ghost centre) or where the **camera must pan** (the opposite sign). Both are usable; a sign slip makes the app actively wrong. Choose one, state it in the comment beside the vector, and derive the arrow from the same convention as the alignment metric.

## Semantics with Foundation Models

`Attachment` initialisers accept `CVPixelBuffer` directly, so camera frames go in without conversion:

```swift
let session = LanguageModelSession()
let r = try await session.respond(generating: ShotAdvice.self,
                                  options: GenerationOptions(samplingMode: .greedy)) {
    "Analyse this camera frame. Name the subject and the single most impactful framing change."
    Attachment(pixelBuffer, orientation: .right)
}
```

Use an `@Generable` struct rather than free prose, and guard availability first — without the guard, devices lacking the model throw on every scan and the feature silently no-ops:

```swift
guard case .available = SystemLanguageModel.default.availability else { return nil }
```

`PrivateCloudComputeLanguageModel` exists for heavier reasoning but has a quota and needs the `com.apple.developer.private-cloud-compute` entitlement — optional "deep analysis", never the live loop.

## Overlay coordinate mapping

Vision coordinates are normalised with the origin bottom-left; the preview may be mirrored. Pick one of two strategies deliberately:

- **Preferred when you control the layout:** lock the preview container to the sensor aspect (3:4 portrait) with `videoGravity = .resizeAspect`, then map directly — `x = n.minX * W`, `y = (1 - n.maxY) * H`. Exact, and WYSIWYG with the saved photo. Switching that view to aspect-fill silently breaks every overlay.
- **Aspect-filled preview:** map through `AVCaptureVideoPreviewLayer.layerPointConverted(fromCaptureDevicePoint:)`. Hand-rolled transforms for this case are the number one source of "the box is in the wrong place".

## Third-party camera limits (state these before promising)

- No Photographic Styles; Smart HDR / Deep Fusion behave differently than the stock Camera app, so captures look slightly different — budget time for "why does my photo look worse".
- 48MP output requires setting `maxPhotoDimensions` on `AVCapturePhotoOutput`; ProRAW needs an entitlement.
- Decide the output aspect ratio early. If the app offers crops (4:5, 1:1, 9:16), the guided frame is a crop of the sensor and the zoom math must include the crop factor, or the guide will not match the saved photo.
- `NSCameraUsageDescription` is mandatory; a privacy manifest is required if you touch listed APIs; the camera does not capture in the background.

## Power and thermal

KVO `AVCaptureDevice.systemPressureState` and watch `ProcessInfo.thermalState`; drop the analysis frame rate before pressure reaches shutdown (which interrupts the session). Throttling the data-output frame rate is the cheapest mitigation.
