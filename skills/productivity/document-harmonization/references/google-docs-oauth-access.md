# Connecting Hermes to Google Docs (Drive + Docs only)

Goal: create, read, and update the user's Google Docs directly, without a manual upload step.

## Steps that work

1. **Prerequisite (user, one-time):** a Google Cloud **Desktop app** OAuth client.
   - Create/select project → enable **Google Docs API** and **Google Drive API** → Credentials → *Create credentials* → *OAuth client ID* → Application type **Desktop app** → download the JSON.
   - If the app is still in *Testing*, the account must be added under *Audience → Test users*, otherwise the consent screen returns `Error 403: access_denied`.
2. **Install the Python clients into the Hermes-managed interpreter:**
   `python -m pip install google-api-python-client google-auth-oauthlib google-auth-httplib2`
   (check the interpreter with `python -c "import sys; print(sys.executable)"` — it should be the Hermes tools Python.)
3. **Store the client secret:**
   `python <skills>/productivity/google-workspace/scripts/setup.py --client-secret "<path to client_secret_*.json>"`
   → prints `OK: Client secret saved to <HERMES_HOME>/google_client_secret.json`.
4. **Produce the consent URL** and send it to the user as a single line. Tell them: approve → the browser lands on a failing `http://localhost:1/?code=...` page (expected, keep it open) → copy the **whole address bar** back.
5. **Exchange** the pasted URL/code, then verify with `setup.py --check` → `AUTHENTICATED`. Token lives at `<HERMES_HOME>/google_token.json` and auto-refreshes.

## Check the shipped script's real flags first

The bundled `google-workspace` skill documents `--services` and `--format json`, but the installed `setup.py` may instead hard-code one `SCOPES` list and accept only `--check | --check-live | --client-secret | --auth-url | --auth-code | --revoke | --install-deps`. Run `python setup.py --help` (or read the `SCOPES` list near the top) before composing a command that this version rejects.

## Wrapper pattern: narrow scopes + bypass the Hermes-env gate

The default scope list requests Gmail read/send/modify, Calendar, Contacts, Sheets and more. To request only what the task needs without editing the shipped skill file, drive the script from a small wrapper:

```python
import sys
from pathlib import Path

HERMES_HOME = Path.home() / "AppData" / "Local" / "hermes"   # Windows; adapt per platform
SCRIPTS = HERMES_HOME / "skills" / "productivity" / "google-workspace" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import setup as gws

gws._ensure_deps = lambda: None          # outside the full Hermes package env pm is None and this gate exits(1)
gws.SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]

if sys.argv[1] == "url":
    gws.get_auth_url()
else:
    gws.exchange_auth_code(sys.argv[2])
```

- Run **both** the `url` and the `code` step through the same wrapper: the pending PKCE session and the requested scope set must match for the exchange to succeed.
- If the exchange reports an expired/already-used code, regenerate the URL and retry with the newest browser redirect only.

## Pitfalls

- `setup.py --install-deps` prints "Run this script in the Hermes environment; use hermes setup first." when the `hermes` package is not importable. Install the Python clients into the Hermes tools Python (step 2) instead.
- Scopes are baked into the token: narrowing to Drive+Docs means Gmail/Calendar/Sheets calls fail later. Re-run steps 4-5 with a wider list if the user later wants those services.
- Never type the Google password or a 2FA code, and never ask for one in chat. The user signs in and approves in their own browser; the agent only ever handles the redirect URL.
