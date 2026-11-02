---
name: macos-app-without-xcode
description: "Use when building a native macOS app without Xcode."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [macos, swift, appkit, swiftc, tcc, eventkit]
---

# Native macOS app with CLT only (no Xcode)

Build a real, launchable `.app` with `swiftc` from Command Line Tools. Worked example: `~/Projects/UniHub` (source layout, `build.sh`, `--selftest`).

**Gate first:** run `xcodebuild -version`. If full Xcode is installed (and `xcrun --sdk iphoneos --show-sdk-version` returns a number), this skill is unnecessary — build a normal SwiftUI project with `xcodebuild`, where the macro plugins, SDKs and simulators all work. Everything below applies only to CLT-only machines.

## Rules

1. **Do not use SwiftUI on a CLT-only machine.** On SDKs without Xcode `@State`/`@StateObject` are Swift macros whose plugin (`SwiftUIMacros`) ships only inside Xcode; `swiftc` fails with "external macro implementation type 'SwiftUIMacros.StateMacro' could not be found". Use programmatic AppKit (`NSSplitViewController`, `NSTableView` `.sourceList`, `NSStackView`, `NSButton`) instead. `Combine` `ObservableObject`/`@Published` are plain property wrappers and work fine.
2. **Compile with Swift 5 mode:** `swiftc -swift-version 5 -O -parse-as-library -o build/App src/*.swift`. Swift 6 language mode adds strict-concurrency errors for no benefit in a small app.
3. **Bundle by hand:** `App.app/Contents/{MacOS/App, Info.plist, Resources/, PkgInfo ('APPL????')}`, then `codesign --force --deep -s - App.app` (ad-hoc). Ship to `~/Applications/`.
4. **Info.plist usage keys are mandatory** for permissions: `NSAppleEventsUsageDescription` (AppleScript/JXA automation), `NSCalendarsFullAccessUsageDescription` + `NSCalendarsUsageDescription` (EventKit). Missing keys → TCC denies with confusing errors.
5. **Put a `--selftest` mode in `main()`** before `NSApplication.run()`: exercise the real bridges (network, EventKit, JXA) and print results. Launched normally stdout is detached — have selftest also write a log file under Application Support.
6. **TCC inheritance trap:** a process spawned from a terminal inherits the terminal's grants; e.g. EventKit may report `writeOnly` (raw 4) with no prompt and the app can create but not read events. To get the real permission prompt for the app's own bundle id, launch via `open -n App.app --args --selftest` (LaunchServices gives it its own responsible-process identity). Reset a wrong grant with `tccutil reset <Service> <bundle-id>` (e.g. `tccutil reset Calendar com.example.app`).
7. **EventKit:** status enum: 0 notDetermined, 3 fullAccess (legacy `authorized`), 4 writeOnly. Request with `store.requestFullAccessToEvents` (macOS 14+; callback on background queue). Events created in a Google-synced calendar appear in Google Calendar automatically; list calendars via `store.calendars(for: .event)` and pick by title (e.g. the gmail-address-titled calendar).
8. **Apple Notes has no public API** — drive Notes.app with `osascript -l JavaScript` child processes; see the `apple-notes` skill "Direct JXA" section and `~/Projects/UniHub/tools/notes_*.js`.
9. **Icons:** render an SF Symbol over a gradient into all `AppIcon.iconset` sizes with a small AppKit script (`NSBitmapImageRep` + `NSGraphicsContext`), then `iconutil -c icns AppIcon.iconset -o AppIcon.icns`.
10. **Verify visually when possible** (screenshots via computer_use); if that tool is unavailable, at least confirm the process stays alive (`pgrep -fl`) and that the app's own state files are written by the live app.

## Reusable patterns

- Keep `Store`/`Bridges`/models UI-free (testable from CLI selftest); UI files only wire them up.
- Never leave `print` as the only output of a selftest run through `open` — mirror to a log file.
- Row-action buttons in rebuilt lists: store `[T]` arrays and use `sender.tag` indices; re-render whole detail view on store change (`objectWillChange` → `DispatchQueue.main.async(render)`).
- `NSButton(title:target:action:)` requires a non-optional Selector; for buttons wired later construct `NSButton()` and set title/target/action individually.
