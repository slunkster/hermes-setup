# Running the VPS Hermes day to day: backups, health alerts, scheduled jobs, remote clients

All scripts live on the VPS; Hermes-env python for Google scripts:
`P=$(ls -td ~/.hermes/installs/*/environments/*/venv | head -1)/bin/python` (resolve it at run time — the env hash changes on `hermes update`).

## Nightly encrypted backup (not to the Mac — it sleeps)

- Encrypt with `age` to a key pair generated ON THE MAC (`age-keygen -o ~/.config/hermes-backup/age-key.txt`); copy only the public key to the VPS. The VPS can write backups but never read them; tell the user to put the private key in a password manager (it is the only way to restore).
- Destination: Google Drive folder via the google-workspace script (`drive create-folder`, `drive upload --parent ID`); retention = list with `drive search "'ID' in parents and trashed = false" --raw-query`, sort by name, `drive delete` (trash) beyond N.
- Contents: `config.yaml .env auth.json SOUL.md memories cron sessions mcp-tokens google_*.json pairing`, `state.db` via `sqlite3 state.db ".backup '<dest>'"` (consistent copy of a live DB), plus `~/Hermes` (exclude multi-GB model dirs), `~/.ssh`, `~/.config/systemd/user`, `~/bin`, `crontab -l`, small secret files outside `~/.hermes` that a rebuild needs (`~/.config/hc-ping-url`, `~/.config/honcho-jwt`), and — if Honcho runs — its `pg_dump` + `.env` + compose file + JWT (see `shared-memory-honcho.md`). ~10 MB.
- Schedule with the user's crontab (`30 3 * * *`, log to `~/Hermes/backups/backup.log`) — no LLM needed.
- Verify by a real restore on the Mac: download with the Mac's google_api.py, `age -d -i key FILE | tar tzf -`.
- Remind the user to also take a provider snapshot after setup (one click, whole-server restore).

## Health alerts — silent unless broken

`hermes cron create "0 9 * * *" --no-agent --script healthcheck.sh --deliver telegram --name …` with the script in `~/.hermes/scripts/`. No-agent mode delivers stdout verbatim and empty stdout = no message, so print ONLY problems. Check: newest Drive backup < 26 h and no errors in the backup log; disk < 85 %; `setup.py --check` prints AUTHENTICATED (Google login drives briefing + backups); skills repo `git fetch` works and nothing unpushed; user services active; Honcho `/health` answers and `docker compose ps --services --status running` lists all four services (via `sg docker -c`). Update notice in the same script: `bash -lc "hermes update --check"` locally and `ssh -o ConnectTimeout=8 mac 'bash -lc "hermes update --check"'`; grep `release available: <channel> v<ver>` (exit code is 0 either way, so parse the text) and print the install command — never run `hermes update` from the job. Test both paths: real run silent, then a copy with a broken value (bad folder ID, threshold 1 %) produces the alert. It cannot report a dead VPS/gateway — pair it with the external dead-man switch below.

## External dead-man switch (VPS or gateway down)

The user creates a free healthchecks.io check (period 10 min, grace 20 min, email + optional Telegram via @HealthchecksBot — never the user's own bot, it is the thing that may be dead) and sends the ping URL. VPS: store it in `~/.config/hc-ping-url` (umask 077) and run `~/bin/hc-ping.sh` from crontab `*/10 * * * *`: if `systemctl --user is-active -q hermes-gateway` → `curl -fsS -m 10 --retry 3 -o /dev/null $URL`, else `curl … --data-raw "hermes-gateway not active" $URL/fail`. In cron, `export XDG_RUNTIME_DIR=/run/user/$(id -u)` first or `systemctl --user` cannot reach the user manager. Verify with one manual run (HTTP 200) and ask the user to press "Send test notification".

## Reboot test (do once after setup)

Everything must come back unattended: schedule the reboot so ssh returns cleanly — `sudo systemd-run --on-active=5 --unit=test-reboot /bin/systemctl reboot` — wait ~2 min, then check `uptime -s`, `tailscale ip -4`, `systemctl --user is-active hermes-gateway hermes-dashboard`, `systemctl is-active docker cron fail2ban`, `ufw status`, `docker compose ps` for Honcho, Honcho `/health`, dashboard `/api/status`, "Connected to Telegram" in gateway.log, and run healthcheck.sh. Only after it passes offer automatic security-update reboots:
- `/etc/apt/apt.conf.d/52hermes-auto-reboot`: `Unattended-Upgrade::Automatic-Reboot "true";`, `…-WithUsers "true";`, `…-Time "04:30";`.
- Move the upgrade run before that time with a timer drop-in `/etc/systemd/system/apt-daily-upgrade.timer.d/override.conf`: `[Timer]` `OnCalendar=` (empty line clears the default) `OnCalendar=*-*-* 04:00` `RandomizedDelaySec=10m`, then `daemon-reload` + restart the timer. Why: `Automatic-Reboot-Time` waits for the NEXT 04:30, and the stock ~06:00 run would leave a pending kernel unbooted for ~22 h.
- Order to state to the user: backup 03:30 → updates ~04:00 → reboot 04:30 only if `/var/run/reboot-required` → briefing 08:00. The dead-man switch grace (20 min) absorbs the ~1 min outage.

## Scheduled agent jobs with pre-collected data

For briefings, collect data in a script and let the agent only write: `hermes cron create "0 8 * * *" "<prompt>" --skill <skill> --script <name>.sh --deliver telegram`. The script's stdout is injected into the prompt, so print compact text (one line per event/mail/task), not file paths; tell the prompt not to re-collect. For Telegram ask for lists instead of wide tables. Test immediately with `hermes cron run <id>`, then check `~/.hermes/cron/output/<id>/` and `delivered to telegram` in `agent.log`. A Mac-dependent source must time out quickly and print a one-line `MAC_UNREACHABLE` marker so the job still delivers.

## Hermes Desktop / phone browser as a client of the VPS

- Desktop's Remote gateway talks to `hermes dashboard`, not the messaging gateway. Run it as a systemd user unit: `ExecStart=%h/.local/bin/hermes dashboard --host <VPS tailscale IP> --port 9119 --no-open`, `EnvironmentFile=%h/.hermes/.env`, `Restart=always`.
- Bind to the Tailscale IP (not 0.0.0.0) and open only `sudo ufw allow in on tailscale0 to any port 9119 proto tcp` — ufw's default-deny also applies to tailscale0. Clients must use exactly `http://<that IP>:9119` (Host-header guard rejects other names).
- A non-loopback bind fails closed without auth: put `HERMES_DASHBOARD_BASIC_AUTH_USERNAME` and `_SECRET` (`openssl rand -base64 32`) in `.env`; the password must be set by the user via a small `read -rs` script that writes `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD` and restarts the unit — never type or see it.
- Verify: `curl http://<ip>:9119/api/status` → `auth_required: true`, providers `["basic"]`; public IP port unreachable; `~/.hermes/logs/dashboard-auth.log` shows `ws_ticket_minted` from the client's Tailscale IP.
- A separate local Hermes on another PC is fine as long as it never gets the Telegram bot token.

## Web previews (static sites the agent builds)

There are three tiers. Tailnet-only is a systemd user unit running `http.server` bound to the Tailscale IP, plus a ufw rule on tailscale0. Temporary public access is a Cloudflare quick tunnel (cloudflared, trycloudflare.com URL, no open ports). A permanent public site is a domain plus Caddy on 80/443. Recipe: skill `claude-design` → `references/multi-page-static-site.md`. Default to tailnet-only. Open public access only when the user asks for it, and stop it when asked. If the site gets an editable admin view, the unit runs the project's `server.py` instead of `http.server`, bound to the same Tailscale IP. Google login needs an https hostname, so enable `tailscale serve` (→ `*.ts.net`) or use a domain; a bare IP won't work.

## Timezone audit

Set and check every layer: `timedatectl` on the VPS, `hermes config set timezone Europe/Tallinn` on EVERY machine (unset = follows the system clock silently), crontab and systemd timers follow the system zone, Hermes cron shows `Next run …+02:00`. Docker containers (Honcho, Postgres) run in UTC — harmless for scheduling, but memory timestamps injected into prompts are UTC, so a late-night fact can appear dated the previous day. Use zone names, never fixed offsets, so DST switches need no edits.

## Stack documentation (offer at the end of a build)

Write one README at the root of the shared skills repo — user wants it thorough with a TL;DR on top. Sections that proved useful: architecture diagram, machines (IPs, users, paths), network/SSH aliases/firewall, Hermes config per machine, connected services with calendar/doc/folder IDs, memory, skills sync, a table of ALL scheduled jobs, backups + restore A (snapshot) / B (fresh server, numbered) / C (lost Mac), monitoring, updates, where each secret lives (location only, never values), symptom→fix runbook, costs, limitations, history. Copy live scripts/units/compose/cron into `infra/vps/…` and `infra/mac/…` (copies, not the live files — say so), and dump only non-secret `.env` lines. Before pushing: `grep -rnE "sk-[A-Za-z0-9]{16}|eyJ[A-Za-z0-9_-]{20}|hc-ping.com/[0-9a-f]{8}|AGE-SECRET"` must find nothing. Gather facts live (`crontab -l`, `hermes cron list`, `hermes config get …`, versions) instead of from chat memory.

### Sharing the setup publicly (sanitized copy)

When the user wants to show the setup to someone, don't open the private repo. Build a separate public repo instead:
1. Copy only the tracked files into `~/Hermes/<name>-public/` (`git ls-files -z | xargs -0 -I{} cp --parents {} $D/`). Then `git init` there so the private history never leaks.
2. Scan with a regex: IPv4 addresses, emails, Estonian phones (`\+?372…`, `\b5\d{3} ?\d{4}\b`), UUIDs, long IDs (`[A-Za-z0-9_-]{28,}` catches Drive, Sheet and calendar IDs), the Telegram user id, device UDIDs, Apple team IDs, `hc-ping` URLs and token prefixes. Also grep for `password|secret|token|jwt|udid`.
3. Replace each real value in Python with a fixed map to `<PLACEHOLDERS>`, e.g. `<VPS_PUBLIC_IP>`, `<VPS_TAILSCALE_IP>`, `you@gmail.com`, `<SHEET_ID>`. Third-party contacts in skill references count too. Re-run the scan until only localhost and example addresses remain, then add a one-line "sanitized public copy" note at the top of the README.
4. Commit with the GitHub noreply author (`$(gh api user --jq .id)+<login>@users.noreply.github.com`), because commit metadata is public too. Then `gh repo create <owner>/<name> --public --source . --push`.
5. Verify `gh repo view --json visibility` and an anonymous `curl` returning 200 before sending the link. Tell the user the copy does not update itself.

## Files sent in chat → Google Drive

Skill `telegram-to-drive` (uploads land in `~/.hermes/cache/documents/`; its script resolves fuzzy Drive folder paths and uploads with a descriptive name).

## Voice messages (Telegram STT)

See the `estonian-speech-transcription` skill, section "Hermes voice messages". After installing the STT extra (`hermes pm install --extra stt-whisper`) the user must restart the gateway; provider/model switches in `stt.*` apply without restart.
