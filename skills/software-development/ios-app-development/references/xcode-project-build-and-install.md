# Scaffolding, building and installing an iOS app from the CLI

For producing a real, device-buildable project without hand-editing `.pbxproj`, and for proving it builds before anyone opens Xcode.

## 1. Generate the project with xcodegen

`xcodegen` (brew) turns a small YAML file into a project. Minimal single-target app:

```yaml
name: MyApp
options:
  bundleIdPrefix: com.example
  deploymentTarget:
    iOS: "26.0"
  createIntermediateGroups: true
settings:
  base:
    SWIFT_VERSION: "5.0"
targets:
  MyApp:
    type: application
    platform: iOS
    sources:
      - path: MyApp
    settings:
      base:
        PRODUCT_BUNDLE_IDENTIFIER: com.example.myapp
        TARGETED_DEVICE_FAMILY: "1"
        INFOPLIST_KEY_UIStatusBarHidden: YES
    info:
      path: MyApp/Info.plist
      properties:
        UILaunchScreen: {}
        UISupportedInterfaceOrientations:
          - UIInterfaceOrientationPortrait
        NSCameraUsageDescription: "..."
        NSPhotoLibraryAddUsageDescription: "..."
```

- Keep `SWIFT_VERSION: "5.0"` when the code base is not concurrency-audited: Swift 6 language mode turns AVFoundation callback captures into errors instead of warnings, which costs a day for no product value.
- Usage strings for camera/photo-library go in `info.properties`; no entitlements file is needed for camera or HEIF capture.
- **Sources are globbed at generate time.** After adding files, re-run `xcodegen generate` or the new files are silently absent from the build.
- `UILaunchScreen: {}` is what stops the app from being letterboxed to iPhone-class 4-inch metrics.

## 2. Prove it compiles — no signing team needed

```bash
xcodebuild -project MyApp.xcodeproj -scheme MyApp -configuration Debug \
  -destination 'generic/platform=iOS' CODE_SIGNING_ALLOWED=NO build
```

`generic/platform=iOS` plus `CODE_SIGNING_ALLOWED=NO` compiles against the real device SDK (arm64, device-only APIs) with no team, no device and no simulator boot. Fastest honest gate after any edit; the simulator build does not catch device-only availability mistakes.

Useful output filter when iterating:

```bash
... build 2>&1 | grep -E "error:|BUILD (SUCCEEDED|FAILED)" | head -20
```

## 3. Sign and install on a paired iPhone

Team ID straight from the local certificate — no need to ask the user:

```bash
security find-identity -v -p codesigning            # is there a dev identity at all?
TEAM=$(security find-certificate -c "Apple Development" -p \
  | openssl x509 -noout -subject | grep -oE 'OU ?= ?[A-Z0-9]+' | head -1 | sed 's/.*= *//')
```

```bash
xcodebuild -project MyApp.xcodeproj -scheme MyApp -configuration Debug \
  -destination 'generic/platform=iOS' -allowProvisioningUpdates \
  DEVELOPMENT_TEAM="$TEAM" CODE_SIGN_STYLE=Automatic build
```

`-allowProvisioningUpdates` creates the team provisioning profile on the fly; the build log then shows `Signing Identity:` and `Provisioning Profile:` per target. Confirm the bundle id and usage strings in the product:

```bash
plutil -p "$APP/Info.plist" | grep -E "CFBundleIdentifier|MinimumOSVersion|NSCamera"
```

## 4. Install and launch

```bash
xcrun devicectl list devices
xcrun devicectl device install app --device <UDID> <path>/Debug-iphoneos/MyApp.app
xcrun devicectl device process launch --device <UDID> com.example.myapp
```

Prerequisites on the device, else the install dies before it starts:

- **Trust the certificate before the first launch.** A freshly installed development build refuses to open with `FBSOpenApplicationServiceErrorDomain error 1`: "Unable to launch … because it has an invalid code signature, inadequate entitlements or its profile has not been explicitly trusted." Nothing in that message says *trust*, and no CLI flag fixes it — hand the user Settings → General → VPN & Device Management → the developer certificate → Trust, then relaunch. Expect it once per certificate/device pair.
- **Unlocked screen.** A locked phone returns `The developer disk image could not be mounted on this device` (CoreDeviceError 12040) with `NSLocalizedFailureReason = The device is currently locked` — it reads like a signing failure and is not one. Hand the unlock step to the user rather than retrying in a loop.
- **Developer Mode enabled** (Settings → Privacy & Security → Developer Mode) on iOS 16+, or launching a development-signed app is refused.

## 5. Watch it run — device log and screenshot

The build log says nothing about whether the camera app works. Two commands close that gap:

```bash
# app stdout/stderr, including print() — run as a BACKGROUND terminal process
xcrun devicectl device process launch --console --terminate-existing \
  --device <UDID> com.example.myapp > "$TMPDIR/app.log" 2>&1

# the actual rendered UI
xcrun devicectl device capture screenshot --device <UDID> --destination shot.png
```

- `--console` streams until the app exits, so start it with the terminal tool's `background=true` (a shell `&` inside a foreground command is rejected) and read the log in a follow-up call.
- Instrument with a throttled `#if DEBUG print` at ≈1 Hz printing the quantities you would otherwise guess: chosen format dimensions, detection counts, subject rect, score, produced zoom. That one log line separates "Vision is broken" from "the decision layer is wrong", and explains a screenshot that looks empty because no detection passed threshold.
- Read the screenshot yourself; do not ask the user what they see. Crop into regions to check overlay clipping and coordinate mapping — a bracket frame or subject box that lands off-target is visible immediately.
- Screenshot + log together are the evidence standard: "no overlay" is ambiguous alone, "no overlay + `sal 0 att 0`" is a diagnosis.
- Eyeballing aspect is not verification. `swift scripts/measure-frame-aspect.swift shot.png 0.75` prints the bright content rect and its ratio and exits non-zero on mismatch — that is how a viewfinder or target frame is proven to match the saved 3:4 photo rather than merely looking close.

## Pitfalls

- Typechecking each file in isolation hides cross-file errors (a missing `import Foundation` that only surfaces when another file needs `TimeInterval`). Compile the whole target, or have the audit pass typecheck the module as one unit.
- The simulator has no camera, no gyro and no phone-class Neural Engine: it is a layout tool only. Every camera, thermal and latency claim needs the physical device.
- Keep one owner of `xcodegen generate` + `xcodebuild` when subagents are involved; two concurrent builds on one project corrupt DerivedData and produce phantom failures.
