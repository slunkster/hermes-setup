---
name: macos-desktop-customization
description: "Use when customizing macOS tiling, bars, or themes."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [macos, tiling, window-management, themes, desktop]
    related_skills: [computer-use]
---

# macOS desktop customization

## When to Use

Use for choosing, planning, configuring, or validating macOS window managers, workspaces, desktop bars, and coordinated themes, including Hyprland-like setups. Choose and configure existing desktop tools before proposing custom software. For GUI interaction mechanics, load `computer-use` separately.

## User defaults

For this user's Hyprland-like Mac setup, prefer **one integrated application**, automatic tiling, visible movement animations, and **Catppuccin Mocha**. Treat a single launcher hiding several independently configured daemons as a multi-tool stack, not compliance with the one-app preference. Design first for the built-in display, with explicit external-display readiness and testing. Ask only about unresolved choices that change the architecture; do not repeatedly reconfirm these established preferences.

## Workflow

1. **Identify the desired behavior before selecting tools.** Distinguish automatic tiling from manual snapping; distinguish Linux-style workflows from compositor effects. Establish whether animations, coordinated bars/borders, native macOS Spaces, and one-app operation are requirements. Keep normal Command shortcuts intact unless the user requests changes.
2. **Inspect the live Mac read-only.** Use `sw_vers`, `uname -m`, `csrutil status`, `command -v brew`, application/config existence checks, and a process check for competing window managers. Inspect `XDG_CONFIG_HOME` before choosing paths. Check Reduce Motion and the actual GUI value of Displays have separate Spaces; a missing `defaults` key is not proof of the effective setting.
3. **Research the current stable release, not just familiar products.** Search for integrated alternatives before recommending several tools or writing an app. Match release-tag documentation and bundled theme/config sources to the version available through the official installer. Main-branch documentation may describe unreleased settings. For integrated Hyprland-style behavior, investigate OmniWM using [the topical reference](references/omniwm.md); its cited capabilities are documentation-grounded, not a claim of local installation success.
4. **Explain real tradeoffs before disruptive changes.** Cover private APIs, native Spaces versus emulated workspaces, security permissions, hotkey collisions, and any altered monitor arrangement. Preserve SIP and Gatekeeper. Do not assume the user accepts full-disk or screen-recording access just because window management was requested.
5. **Establish recovery before activation.** Back up existing configuration and note login-item and display settings. Warn that starting an automatic manager rearranges open windows. Keep generated reports/backups under `~/Hermes/<topic>/`, while application-owned settings stay at their native paths. Do not initialize the home directory as a Git repository; configuration checkpoints are sufficient when no scoped repository exists.
6. **Configure incrementally through the app or exact versioned schema.** Let the application emit a complete valid config first; change values in place rather than replacing strict configuration with partial examples. Apply layout, motion, theme, bar, and shortcuts as separate verified steps. Do not add unrelated wallpaper, terminal, font, or system-wide window-chrome changes.
7. **Validate behavior, not just flags.** Exercise three ordinary test windows, creation/closure, focus, moving between workspaces, floating mode, dialogs, fullscreen, and Quit/reopen. Test Estonian letters and Option-produced symbols on the actual keyboard layout. Provide a hotkey-pause path rather than silently sacrificing text entry. A screenshot cannot prove animation smoothness; use live observation or user confirmation.
8. **Test external displays separately.** Never invent display identifiers or claim hot-plug works without a connected display. Preserve the original macOS arrangement; explain any technical arrangement and mouse-warp dependency before changing it. Distinguish configured support from a passed plug/unplug/reconnect test.
9. **Enable login startup last and hand over briefly.** Use the application's login mechanism rather than an additional daemon. Document actual shortcuts, quit/recovery, and explicit PASS/FAIL/NOT TESTED results. A checked login item does not prove successful operation after a new login.

## Scope and completion rules

- Keep plan-only work separate from installation; capability research is not an executed setup.
- Reconsider the product when a new requirement invalidates the original choice instead of adding wrappers and helper processes automatically.
- Use before-test → one change → after-test → checkpoint for configuration work; do not invent unit-test projects or commits merely to imitate software TDD.
- Do not equate a shared palette with theming every application's content; state which surfaces the chosen tool actually controls.
- Stop at an unmet requirement and discuss the compromise instead of silently installing another manager.
