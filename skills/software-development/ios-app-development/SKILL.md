---
name: ios-app-development
description: "Use when building or planning an iOS app in Swift."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [ios, swift, avfoundation, vision, foundation-models, camera, xcode]
---

# iOS app development

Planning, scaffolding, and reviewing iOS/iPadOS apps in Swift. For macOS-only work without Xcode see `macos-app-without-xcode`.

## When to Use

- The user asks how to build, plan, review or debug an iOS/iPadOS app, or whether a given iOS feature is feasible and on which OS version.
- Any camera, Vision, Core ML or Foundation Models work on Apple platforms — the reference below carries the capture/analysis pipeline.
- Not for macOS-only apps (use `macos-app-without-xcode`) or for cross-platform framework choices.

## 1. Toolchain gate — check before advising or coding

```bash
xcodebuild -version                       # full Xcode installed?
xcrun --sdk iphoneos --show-sdk-version   # exact SDK you can build against
xcrun simctl list devices available       # what you can actually run
```

- iOS builds require full Xcode (iOS SDK + simulators). Command Line Tools alone can only build macOS targets.
- Choose the deployment target deliberately: newest-SDK-only APIs gate the whole app to the newest iOS. Foundation Models image input (`Attachment` with a pixel buffer) and Private Cloud Compute are newest-iOS-only, while the Vision Swift request API and most capture APIs work two versions back.
- The simulator has no camera and no phone-class Neural Engine. Camera, thermal and latency work happens on a physical device — state that up front instead of planning around the simulator.

## 2. Verify every Apple API name against the SDK — never from memory

```bash
SDK=$(xcrun --sdk iphoneos --show-sdk-path)
# Swift frameworks: authoritative symbol list
SI="$SDK/System/Library/Frameworks/Vision.framework/Modules/Vision.swiftmodule/arm64e-apple-ios.swiftinterface"
grep -oE 'public struct [A-Za-z]+Request' "$SI" | sort -u
# ObjC frameworks: grep the headers instead
grep -n 'videoZoomFactor\|rampToVideoZoomFactor' "$SDK/System/Library/Frameworks/AVFoundation.framework/Headers/AVCaptureDevice.h"
```

Availability (no browser needed):

```bash
curl -s "https://developer.apple.com/tutorials/data/documentation/foundationmodels/attachment.json" -o /tmp/a.json
python3 -c 'import json;m=json.load(open("/tmp/a.json"))["metadata"];print(m["title"],[(p["name"],p["introducedAt"]) for p in m["platforms"]])'
```

- **Write the curl output to a file, then parse it.** Piping a large doc JSON through a shell command truncates it and `json.loads` dies on "Invalid control character" / "Expecting ',' delimiter".
- Doc slugs are camelCase and Swift types sometimes need a suffix: `-swift.property`, `-swift.enum`, `-swift.class`. On a 404-sized response, fetch the parent class or framework JSON and read its `references` keys to get the exact slug instead of guessing variants.
- The `.swiftinterface` also carries `@available(iOS x.y, ...)` lines — one grep answers both "does this exist" and "what's the minimum OS".

## 3. Answer shape for "how should this be done?"

- Lead with feasibility and the single architectural decision that determines success. No tutorial, no framework tour.
- Name the control problem and its timescale split (what runs at 30 Hz vs 1 Hz) before naming frameworks — framework lists without a latency budget produce designs that cannot work.
- State platform limits and hard parts explicitly, then a milestone order where every step is demoable on device.
- If the app has a real App Store competitor, check the live listing and name the wedge. "AI does X" alone is not differentiation.

## 4. When the ask turns into building: interview first

"Ask me things before starting" is this user's standing preference when a design discussion becomes a build. Run it as **two rounds of at most 5 discrete questions**, recommended option first, and do not scaffold until round 2 is answered.

- Round 1 — product: audience/use case, how guidance appears on screen, how much authority automation gets, when the AI model runs, output format.
- Round 2 — technical: deployment target, where inference runs (on-device vs Private Cloud Compute vs own server), scorer/algorithm approach, distribution (TestFlight / App Store / paid), plus one open question (test device and working name).
- Read the answers for **contradictions before coding**, then state the resolution in one line instead of asking a third round. The recurring collision: "no text anywhere in the UI" + "target the older iOS whose model is text-only" — resolve by making the model emit a **number** (e.g. desired subject height fraction) rather than prose, so a text-free UI still has something to consume.
- Constraints dropped in passing ("pan/tilt is mine", "distance is a nice touch", "auto-fire is optional") are invariants: bake them in as defaults and say so, do not re-litigate them in round 2.

## 5. Build with subagents — but only one process runs the build

The build-fix loop is serial (one `xcodebuild` owns DerivedData); everything else parallelises. This user expects agents to be used to shorten a build ("use agents and stuff to make it quicker") — split by file and dispatch rather than building solo, but keep the state machine and the build in the parent.

- UI child: hand it the exact public API surface of the controller (types, published properties, method signatures) and the normalised→view mapping formula verbatim, and forbid `xcodebuild`.
- Audit child: list the risky API assumptions and have it typecheck probes against the `.swiftinterface`; it reports verdicts and edits nothing. Cheap insurance — one pass found a hard error and two silent-behaviour bugs.
- Parent keeps `xcodegen generate`, the build and the install. Never let two agents write to the same sources directory.

## 6. A green build proves nothing about a camera app

Compiling, launching, and even a live preview do not prove that: the active format is high-resolution, boxes land where the user sees them, the score is stable, or the saved photo matches the framed preview. Install, then run the log + screenshot loop in `references/xcode-project-build-and-install.md` §5 before reporting camera, overlay or guidance work as done. State explicitly which claims are device-verified and which are still assumptions.

## References

- `references/camera-and-vision-pipeline.md` — capture session, programmatic zoom control, Vision + Foundation Models analysis loops, framing/guidance overlay, third-party camera limits.
- `references/xcode-project-build-and-install.md` — xcodegen `project.yml`, unsigned device-SDK compile check, team-ID extraction, signed build, `devicectl` install and certificate trust, plus the on-device log/screenshot verification loop.
- `scripts/measure-frame-aspect.swift` — measure a device screenshot's content rect and aspect ratio (`swift … shot.png 0.75`) to prove the preview or target frame matches the saved photo.
