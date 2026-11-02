# Connecting the user's accounts on the VPS Hermes

Goal: everything that has a cloud API runs natively on the VPS (works while the Mac sleeps); only Mac-bound sources go through `ssh mac`.

## Decision table

| Source | Where | How |
|---|---|---|
| Gmail, Drive, Docs, Sheets, Google Calendar (incl. iCal subscriptions like Moodle) | VPS native | copy Google token (below) |
| Todoist | VPS native | own MCP OAuth login (below) |
| Other MCP/API services (Notion, GitHub, Slack…) | VPS native | same pattern as Todoist / API key in `.env` |
| School/university Microsoft 365 mail (Exchange, @ut.ee) | Mac only | `ssh mac` + Mail.app JXA. Direct Graph/IMAP needs tenant admin consent; auto-forwarding to Gmail is often blocked and moves org mail out — don't do it without the user asking IT |
| Apple Notes / Reminders / Calendar.app / local files | Mac only | `ssh mac "osascript -l JavaScript …"` |

## Google (google-workspace skill)

1. Copy `~/.hermes/google_token.json` and `google_client_secret.json` to the VPS `~/.hermes/` (`scp -p`, then `chmod 600`). Google refresh tokens don't rotate, so sharing one token between machines is safe.
2. Run the skill scripts with the Hermes dependency-environment python, not the bare tools python: `P=$(ls -td ~/.hermes/installs/*/environments/*/venv | head -1)/bin/python`. The tools python under `~/.hermes/tools/python-*` lacks the Google libs and `setup.py` refuses it ("Run this script in the Hermes environment"). `hermes pm status` shows whether the `google` extra is installed.
3. Verify: `$P …/google_api.py gmail search newer_than:1d --max 2` and a `drive search`.

## Todoist (and any `auth: oauth` MCP server)

1. Mirror the Mac's `mcp_servers.<name>` block with `hermes config set mcp_servers.todoist.url …`, `.auth oauth`, `.enabled true`, `.tools.exclude "[a, b]"`; check with `hermes mcp list`.
2. Give the VPS its OWN login — never copy `~/.hermes/mcp-tokens/*.json`: refresh tokens rotate, so one machine's refresh signs the other out.
3. The user runs `ssh -t vps hermes mcp login todoist`, approves in the browser, then pastes the full failed-redirect URL (`http://127.0.0.1:<port>/callback?code=…`) back at the prompt. Don't relay the code through chat.

## After connecting

Update the VPS agent's MEMORY.md with which sources are native vs Mac-only, so it doesn't try `ssh mac` for Gmail or the Google API for Outlook.
