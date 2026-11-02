---
name: macos-terminal-glyph-diagnosis
description: "Use when a macOS terminal shows '?' for icons/emoji."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [terminal, fonts, nerd-font, apple-terminal, diagnostics]
---

# macOS Terminal: '?' / boxes instead of icons

Symptom: "weird question marks" (or boxes/tofu) where emoji-like icons should appear — prompt icons, powerline arrows, Nerd Font symbols, some CLI output. Diagnose the missing glyph and fix it.

## When to Use

- A macOS terminal shows `?`, boxes, or tofu where icons/emoji-like symbols should be (prompt icons, powerline arrows, CLI icons).
- A starship / p10k / mybash-style prompt renders wrong after installing it.
- To distinguish a locale/encoding problem from a missing-font-glyph problem before fixing.

## Decision tree

1. **Locale first.** Run `locale`. If `LC_CTYPE`/`LANG` is not UTF-8 (e.g. `C`/`POSIX`), that alone explains `?` — fix with `export LANG=en_US.UTF-8` (or matching locale) and Terminal setting "Set locale environment variables on startup". If UTF-8, continue.
2. **Nerd Font / Powerline glyphs** (U+E000–U+F8FF BMP PUA, U+F0000+ plane-15 PUA) missing → macOS CoreText does NOT reliably fall back for PUA glyphs; a font that is *installed* but not *selected* does not help. Fix: select the patched font in the terminal profile.
3. **Read the active terminal font** (Apple Terminal stores it as NSKeyedArchiver data, NOT plain text — `defaults read` shows binary blobs): decode with Python `plistlib`. `scripts/check_font_cmap.py font` prints every profile's font+size.
4. **Extract required codepoints** from whatever draws the output (e.g. starship config: `python3 scripts/check_font_cmap.py cps ~/.config/starship.toml`).
5. **Check coverage** of installed Nerd Fonts: `python3 scripts/check_font_cmap.py cover <configfile>`. Nerd fonts from older releases may miss newer codepoints (e.g. U+F6A4, U+F718, U+F0219 — nf-md range); a codepoint no installed font has stays `?` even after the switch.

## Fix (Apple Terminal)

Terminal → Settings… (⌘,) → Profiles → *<active profile>* → Text → Font → **Change…** → Family: e.g. `MesloLGS Nerd Font` (Regular, 12) → OK. "Mono" variant if icons look too wide / misalign. No restart needed; prompt redraws on next Enter.

## Pitfalls

- **Installing ≠ selecting.** mybash (ChrisTitusTech) & p10k-style setups install Meslo LG Nerd Font but can only auto-select it on Linux terminals (GNOME/Ptyxis); on macOS the user must set it manually in the profile.
- **Real emoji (😀,🌈) are unaffected** — Apple Color Emoji fallback renders them even with a plain font. Only PUA/Nerd glyphs break.
- Other emulators: iTerm2 → Settings → Profiles → Text → Font → Nerd Font; VSCode integrated terminal → `terminal.integrated.fontFamily`.
- While a full-screen TUI (e.g. an agent CLI) is running, the shell prompt is hidden — diagnose the prompt with a bare shell/new window visible.
