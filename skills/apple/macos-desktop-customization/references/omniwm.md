# OmniWM: integrated macOS tiling candidate

## Evidence boundary

The commands and settings below were checked against official stable-release documentation and source, including the v0.8.0 release. They were **not exercised in a local installation** during the research that established this reference. Recheck the installed version and perform acceptance tests before calling the setup working. Do not pin an old release solely because it is named here.

Sources:
- https://github.com/OmniNull/OmniWM/releases/latest
- https://omniwm.app/help/known-limitations/
- https://omniwm.app/config/configuration/
- https://omniwm.app/config/settings-reference/
- https://omniwm.app/omnishell/configuration/profiles-palettes/
- https://omniwm.app/guides/multi-monitor/
- https://omniwm.app/reference/cli/queries/
- Release-tag source: `Sources/OmniWM/ShellDefault/themes/catppuccin.toml`

## Why evaluate it

Official documentation describes a single application containing Hyprland-style Dwindle BSP, Niri scrolling layouts, display-paced animations, focus borders, an interactive workspace bar, and an embedded shell/theme system. Supported hardware is Apple Silicon with macOS 26 or later; official releases keep SIP enabled and are Developer ID signed/notarized. This makes it a closer candidate for one-app animated tiling than a separate tiler/bar/border stack, but it is not the Hyprland compositor.

## Installation and permissions gate

After authorization to implement:

```sh
brew install --cask omniwm
brew list --cask --versions omniwm
codesign --verify --deep --strict --verbose=2 /Applications/OmniWM.app
spctl --assess --type execute --verbose=2 /Applications/OmniWM.app
open -a OmniWM
```

Expect signature verification to pass and Gatekeeper to accept the app. Do not bypass a failure by stripping quarantine. Let the user grant Accessibility and Input Monitoring. Screen Recording is optional for previews; Full Disk Access is optional for Hidden Bar/notifications and is unnecessary for basic tiling. Keep clipboard history, notification integration, and third-party style code out of the initial setup.

Check **Displays have separate Spaces** in macOS. If changing it requires logout, stop for the user's saved-work/logout step. Do not delete existing native Spaces; the recommendation of one native Space per display is not permission to remove them. Do not run another resident window manager concurrently.

## Configuration order and traps

1. Let OmniWM generate `${XDG_CONFIG_HOME:-$HOME/.config}/omniwm/settings.toml`; an absolute XDG path is honored. Back it up before edits. The schema is strict: a parseable TOML fragment is not necessarily a complete valid application configuration.
2. Set `general.defaultLayoutType = "dwindle"` **and inspect every workspace's `layoutType`**. Explicit `niri` entries override the default. Preserve workspace UUIDs.
3. Set `general.animationsEnabled = true`; start with `animationSpeed = 1.0`. macOS Reduce Motion overrides animation settings. Verify actual motion rather than just reading this flag.
4. Use Appearance Dark, Default style, and its Catppuccin palette. The bundled dark palette uses Mocha colors: `#11111B`, `#181825`, `#1E1E2E`, text `#CDD6F4`, accent `#CBA6F7`. Set the focus border independently if necessary; a 3 pt mauve border and 10 pt inner gaps are a restrained starting point.
5. Read `shell/shell.toml` as well as `settings.toml`: active profile settings can override global workspace-bar appearance. Select the palette via Settings rather than editing managed `shell/default/themes/` files, which upgrades replace.
6. Start the full-width bar **below the macOS menu bar**, with Reserve Layout Space enabled. Other full-width placements can change macOS menu-bar auto-hide globally; abnormal exits may leave that preference changed. Do not also add the bar's full height to top gaps, which double-reserves screen space.
7. Keep app menus, notch clearance, and window controls accessible. Use bundled widgets initially, such as workspaces, clock, and volume. Do not install external themes merely to obtain a bundled palette.
8. Rebind hotkeys in place: duplicate or unknown action IDs can reject the whole config. Option-based defaults may intercept typed symbols. Test text entry and expose Pause/Resume Shortcuts. Dwindle Move may join/extract tab groups rather than always swap positions; describe the actual behavior.
9. Set Start at Login only after successful testing. It is a macOS login-item setting, not a TOML key; do not create a parallel LaunchAgent or brew service.

## Read-back via bundled CLI

Homebrew provides `omniwmctl`; it is not a second resident window manager. Enable IPC temporarily in the app for queries:

```sh
omniwmctl query workspaces --fields raw-name,layout,display --format table
omniwmctl query displays --fields name,is-main,has-notch,reserved-insets --format table
omniwmctl query windows --visible --fields app,frame,mode --format table
omniwmctl query shell-widgets
```

Check all intended workspaces resolve to Dwindle, display insets match the bar, windows settle into valid frames, and shell widgets load without configuration problems. Avoid saving private window titles in reports. Disable IPC after testing unless continued automation is desired: its trust boundary is the local user account, not individual applications.

## Multi-monitor caveat

The documented setup uses a technical staircase arrangement in macOS and a separate physical-desk routing map inside OmniWM, typically with Mouse Warp. Explain this before altering the user's display layout. Run the monitor setup assistant with actual displays connected and assign at least one workspace to every display. Do not manufacture UUIDs or infer hot-plug restoration from the existence of monitor support. Test disconnect, accessibility of remaining windows, reconnect, and restored routing; otherwise report NOT TESTED.

## Recovery acceptance

Verify normal Quit removes the bar/border and stops rearranging windows; reopen and recheck settings. Disable Start at Login before abandoning the tool. Restore backed-up configuration only while OmniWM is stopped. If uninstalling, `brew uninstall --cask omniwm` without `--zap` preserves configuration for recovery. Preserve the original monitor arrangement separately; quitting the app does not promise bit-identical original window positions.
