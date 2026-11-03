# Windows / Brave: connecting and driving

## Enabling remote debugging (one-time, manual)

The daemon searches the profile dirs of Chrome, Chrome Beta/Dev/SxS, Chromium,
Edge variants and Brave for `DevToolsActivePort`. If none has it, the call fails:

```text
fatal: DevToolsActivePort not found in [...] — enable chrome://inspect/#remote-debugging, or set BU_CDP_WS for a remote browser
```

That means the browser is running without remote debugging. install.md's first
checkbox is deliberately manual and cannot be done by the harness.

- Open `chrome://inspect/#remote-debugging` (Brave: `brave://inspect/#remote-debugging`)
  and tick "Allow remote debugging for this browser instance".
- **Open that page by launching the browser binary with the URL as an argument**:
  `"<path to brave.exe>" "brave://inspect/#remote-debugging"`. On Windows,
  `cmd //c start "" "<scheme-url>"` returns success but silently does nothing for
  custom schemes, so the user sees no page and reports the checkbox missing.
- Verify from the shell before blaming the harness: is the browser LISTENING on the
  port from line 1 of `DevToolsActivePort`? (`powershell Get-NetTCPConnection -State
  Listen` filtered to the brave/chrome process, or `curl -si .../json/version`).
  New-style inspect-page debugging answers `/json/version` with an empty **404** —
  that means CDP is ON (HTTP discovery is just disabled). Only a refused/silent
  connection means it is off. The file's mtime can be days old and still valid.

## Attaching to the user's real browser (when the default daemon is headless)

The `mcp__browser_exec` tool / default daemon may be attached to a Hermes-bundled
headless Chromium. To drive the user's visible Brave/Chrome instead, use a separate
named daemon with the WebSocket URL built from `DevToolsActivePort` (line 1 = port,
line 2 = `/devtools/browser/<id>` path):

```bash
cd "<scratch dir>"   # script file must be reachable from cwd
ws=$(sed -n 2p "$LOCALAPPDATA/BraveSoftware/Brave-Browser/User Data/DevToolsActivePort")
BU_NAME=brave1 BU_CDP_WS="ws://127.0.0.1:9222$ws" ~/.local/bin/browser-harness.exe < step1.py
# later calls: BU_NAME=brave1 ~/.local/bin/browser-harness.exe < stepN.py
```

- First connect can fail with `CDP WS handshake failed: timed out` because the
  browser shows an "Allow remote debugging?" prompt. Re-run the same command as a
  background process (notify on exit) and tell the user to click Allow; it then
  completes. Do not reconnect in a loop.
- Print `cdp('Browser.getVersion')['product']` in the first script to confirm you
  are on the real browser (no `HeadlessChrome`).
- Set `PYTHONIOENCODING=utf-8` when printing non-ASCII page text, and write long
  results to JSON files in the scratch dir rather than stdout.
- Cloudflare-protected sites the user browses normally (e.g. auto24.ee) pass
  without any challenge in the real profile — so for bot-walled sites, attach to
  the real browser FIRST instead of trying the headless one.
- This hands the harness control of that browser's logged-in session, cookies
  included. Say so once when asking the user to enable it.

## Stuck daemon

Symptom — every call fails with:

```text
_IPCResponseTimeout: Page.navigate timed out after 5s waiting for the daemon
```

Fix: run `browser-harness --reload` (reports "daemon stopped — will restart fresh
on next call"), then retry the same call. Do not conclude the browser or harness
is unusable. The same recovery applies after closing the user's browser to free a
locked profile.

## Bot checks (Cloudflare)

With the user's real, non-headless profile the managed challenge passes **on its
own**: navigate, `wait_for_load()`, sleep a few seconds, re-read the page.

- **Before handing a challenge to the user, confirm which browser you are attached
  to**: `cdp('Browser.getVersion')`. A `userAgent` containing `HeadlessChrome` (or
  `product` from a Hermes-bundled `chromium-*` / `--user-data-dir=...agent-browser-chrome-*`)
  means the session silently fell back to an invisible headless browser — the user
  cannot see or click anything there, and Cloudflare will never pass on its own.
  Telling them to "click the checkbox" wastes a round trip. Instead get the real
  browser attached: check the profile's `DevToolsActivePort` (Brave:
  `%LOCALAPPDATA%/BraveSoftware/Brave-Browser/User Data/DevToolsActivePort`) and
  check the port is listening (see above). If nothing listens, relaunch the inspect
  page as described above and ask the user to tick the checkbox; then attach via
  `BU_CDP_WS` (section "Attaching to the user's real browser").
- Window titles from `Get-Process brave | % MainWindowTitle` show what the user's
  real browser has open; if it differs from `list_tabs()`, you are on another browser.
- Never click a "Verify you are human" / Turnstile checkbox. That widget exists
  to assert a human is present; a click from automation is a false assertion no
  matter who authorised it. If it is still showing after the wait, stop and hand
  that step to the user. State this once, plainly, and do not re-litigate it when
  the user repeats "just do it".
- A plain `curl` returning 403 with `<title>Just a moment...</title>` is expected
  on these hosts, not a broken URL. Escalate to the browser rather than hunting
  for an alternative link.

## Invoking scripts

Write the Python to a file and pipe it in:

```bash
browser-harness < script.py
```

A heredoc wrapped inside a shell command mangles `\n`, regex escapes and quotes,
producing `SyntaxError: Invalid or unexpected token` at a column you cannot see.
A file also survives a timeout and is re-runnable. Return structured data as JSON
from `js(...)` and parse it in Python instead of joining fields with newlines
inside the JS.

## Install location

```bash
uv tool install --python 3.12 --upgrade --force browser-harness
```

The executable lands in `~/.local/bin`, which is **not on PATH** by default —
call it by full path or run `uv tool update-shell`. If `uv` is missing entirely,
`python -m pip install uv` is enough to get it.
