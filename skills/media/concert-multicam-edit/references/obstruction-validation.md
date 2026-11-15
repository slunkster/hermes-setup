# Validating foreground obstruction in live concert footage

## 1. Establish a visual baseline

Extract synchronized raw A, raw B and previous-output stills at several points per set. Keep native source timestamps and the provisional sync mapping beside them. Inspect daylight, dusk and night separately, including seated spectators, a standing silhouette, entry/exit and a near-lens torso. Inspect contact sheets in readable crops rather than relying on a heavily downscaled full-evening image.

Manually label a small representative sample before setting thresholds. Record whether performers are visible, partially hidden or unusable; do not define every person as a blocker.

## 2. Detector baseline and limits

The official YOLOX tiny ONNX model has been exercised with ONNX Runtime CPU on actual concert stills and detected large dark foreground silhouettes. This validates a lightweight baseline, not full-sequence accuracy. Download from the official YOLOX release and follow its ONNX preprocessing/postprocessing rather than substituting another YOLO family's conventions:

- Inspect the model input shape; the tested tiny export takes 416×416.
- Preserve aspect ratio; resize the BGR image and top-left pad with 114, then use float32 NCHW without an invented normalization step.
- Decode grid/stride outputs following the official implementation; person confidence combines objectness and class score. Apply NMS and map boxes back through the resize ratio.
- Keep low-confidence candidates for review rather than interpreting their absence as visibility. Around 0.15 confidence and 0.45 NMS are initial test settings, not calibrated acceptance thresholds.

Official references:
- https://github.com/Megvii-BaseDetection/YOLOX/releases
- https://github.com/Megvii-BaseDetection/YOLOX/tree/main/demo/ONNXRuntime

A larger detector, segmentation model or GPU provider is an alternative to benchmark, not a validated improvement until tested on this footage. Never promise that a generic COCO detector recognizes a featureless jacket filling the lens.

## 3. Convert detections into usable intervals

1. Define each camera's stage and performer regions. Separate foreground spectators from musicians using position, size, temporal persistence and visual review.
2. Compute union overlap, not the sum of overlapping boxes, so duplicate detections do not inflate coverage.
3. Combine low-rate semantic checks with full-rate motion cues for fast crossings. Dark stage lighting can change motion/texture statistics without a person entering.
4. Add safety margins before and after blocked intervals and require sustained clear evidence before switching back; sparse sampling cannot locate boundaries to the frame.
5. Retain uncertain and both-blocked intervals with their source times. Resolve using contextual frames and the user's fallback policy, not by calling the lower score clean.
6. Re-evaluate overlap after cropping, because a crop changes which performers are visible and the fraction covered. Cropping cannot recover a performer behind a spectator.

## 4. Verification gates

- Before full analysis: real video smoke test, exact decoded frame count, detector outputs and output-file readback.
- Before final rendering: verify source-time mapping and inspect each proposed transition into/out of a blocked interval.
- After rendering: full decode, expected duration/frame count, continuous master audio, sync spot checks, readable titles and daytime/nighttime color comparisons.
- Exclude cut discontinuities only from motion-difference statistics, never from semantic or visual QA.
- Report remaining both-blocked intervals. Sampling and automated scores support review; they do not establish that every frame is clear.
