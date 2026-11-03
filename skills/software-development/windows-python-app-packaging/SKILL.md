---
name: windows-python-app-packaging
description: "Use when packaging a Python tool as a Windows .exe app."
version: 1.0.0
author: Nous Research
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [pyinstaller, exe, windows, packaging, desktop, gui, http-server]
    category: software-development
    related_skills: [pdf, hermes-agent]
---

# Packaging a Python tool as a Windows .exe (with a GUI)

## When to Use

- The user asks for an `.exe`, a "desktop app", or "double-click and it runs" for a script you built.
- A CLI tool needs a GUI for a non-technical user.
- The tool already works and must be handed over without a Python install.

## Give it a web GUI, not tkinter

For a tool UI, prefer a stdlib `http.server` + one HTML file opened in the browser over tkinter:
no dependencies, no widget layout fights, and the same HTML works if it later gets hosted.

- Bind `127.0.0.1` only. Generate a random per-process token, inject it into the served HTML
  (`replace("__TOKEN__", TOKEN)`), and require it as a header on every API call. Other web pages
  cannot read the token and preflight/CORS blocks them, so this is a cheap CSRF guard for a
  localhost server that can create real business documents.
- Keep one implementation: the server imports the existing module and calls its functions.
  Convert the CLI's error path into a plain exception (see below) so handlers can return
  `{ok: false, error}` and the JS can toast it; let unexpected exceptions return 500 with a
  short traceback.
- Common shape that works: `GET /` (HTML), `GET /api/state` (everything the view needs),
  `GET /api/detail?id=`, `POST /api/<action>` per operation, `GET /api/pdf?id=` for binary
  output (fetch it as a blob and `window.open(URL.createObjectURL(blob))` — a plain
  `window.open` cannot send the token header).
- UI details that earn their keep in a business tool: status pills per record, an empty state
  that says what to click, live totals while typing, a log modal for multi-step operations, and
  a settings form that writes the same config file the CLI reads.

## Make the CLI error path catchable first

`die()` implementations that `print(...); raise SystemExit(1)` cannot be caught by a request
handler without swallowing everything. Change `die()` to raise a custom `EarveError`-style
exception, and let `main()` convert it to `print("VIGA: ..."); SystemExit(code)`. CLI behaviour
stays identical, and the server can catch one type.

## Package with PyInstaller (onefile)

```bash
python -m PyInstaller --noconfirm --clean --onefile --name earve \
  --add-data "gui.html;." --add-data "config.example.json;." \
  --hidden-import gui --collect-all reportlab earve.py
```

- Windows `--add-data` uses `source;dest`; the dest `.` puts assets next to the module at runtime.
- `--hidden-import` for a local module imported lazily inside a function body.
- `--collect-all <lib>` for libraries that load data files (reportlab fonts, jinja templates).
- Copy `dist/<name>.exe` next to the sources so the CLI and the GUI share `config.json`, the
  SQLite register and the output folder. Ship a `build.bat` (see `templates/build.bat`) so a
  rebuild after an edit is one command.
- Keep the console subsystem (no `--noconsole`): the user needs the printed URL and the error
  text. A windowed exe that fails silently is worse than a console window.

## Frozen-path discipline (the change that breaks everything)

```python
def _base_dir():   # writable: config, db, output
    return Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent

def _asset_dir():  # read-only bundled files
    return Path(getattr(sys, "_MEIPASS", _base_dir())) if getattr(sys, "frozen", False) else Path(__file__).parent
```

- Never derive data paths from `__file__` in a frozen app: it points inside the temporary
  `_MEIPASS` extraction dir and everything written there vanishes.
- Auto-create `config.json` from a bundled `config.example.json` on first run, and make the
  GUI subcommand the default when `sys.argv` has no arguments — that is what makes
  double-click work.

## Console encoding on Windows

A frozen console exe writes through the legacy code page, so Estonian/Chinese/accented text
comes out mangled mid-word (`s?nkroni`). Fix at startup on `win32`:

```python
ctypes.windll.kernel32.SetConsoleOutputCP(65001)
ctypes.windll.kernel32.SetConsoleCP(65001)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
```

Verify by running the exe and reading a line that contains a non-ASCII character — not by
reading the source.

## Verification ("Build complete" is not evidence)

1. Copy the exe into an **empty** temp directory and run it: proves first-run config creation
   and that bundled assets resolve from `_MEIPASS`.
2. Exercise the real work path and inspect the artifact, not the exit code — e.g. extract text
   from the produced PDF to prove fonts and bundled data files survived packaging.
3. If it serves a GUI: `curl` `/`, pull the token out of the HTML, then hit every endpoint; check
   that a wrong token returns 403 and that a bad request returns a readable error.
4. Open the GUI in a real browser, screenshot it and read the image: empty state, list, modal,
   totals, status pills. Layout bugs (invisible status pill because the JS read `v.status` from
   the wrong object, misaligned totals row) only show up here.
5. Test the error paths from the UI too (send on a record that cannot be sent, missing price).

## Pitfalls

- **`cmd //c build.bat` does not run the batch** from git-bash: cmd prints its banner and exits.
  Use `MSYS_NO_PATHCONV=1 cmd /c build.bat` (or call PyInstaller directly).
- **Windows keeps handles on generated files.** A running server holds its SQLite DB and a
  rasterizer holds the PDF it rendered, so `rm`/`mv` fails with "Device or resource busy" while
  writes still succeed. Stop the server and close rasterizer documents before cleaning state;
  if a file stays locked, overwrite it rather than deleting (a stale sample file is cosmetic).
- **Onefile exes are ~25-30 MB and take 2-4 s to start** — expected, not a regression.
- **Unsigned exes trip SmartScreen** ("More info" → "Run anyway"). Say this up front so the user
  does not think the build is broken; code-signing needs a paid certificate.
- **Don't test with the user's live data.** Build the test invoice in a scratch copy of the app
  folder; test artifacts otherwise consume real invoice numbers and get baked into the handover
  state (reset `config.json` from the example and delete the test DB before handing over).
- **Validate inputs in the API layer, not only in the form.** A POST with a missing quantity
  silently produced a 0,00 € invoice until the server started rejecting it — a validation gap
  the browser form hid.

## Support files

- `templates/build.bat` — working PyInstaller build script (builds `dist/<name>.exe`, copies it
  next to the sources).
