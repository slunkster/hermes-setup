# Extending the VPS Hermes to a Windows PC and an iPhone

## iPhone: Siri / Shortcuts "Ask Hermes"

The gateway's OpenAI-compatible API server, bound to the VPS Tailscale IP.

1. Add to `~/.hermes/.env` (back it up first; `API_SERVER_*` are env vars):
   `API_SERVER_ENABLED=true`, `API_SERVER_HOST=<vps-ts-ip>`, `API_SERVER_PORT=8642`, `API_SERVER_KEY=$(openssl rand -hex 24)`.
2. `sudo ufw allow in on tailscale0 to any port 8642 proto tcp`.
3. `systemctl --user restart hermes-gateway`. Shutdown can take ~60 s (the watchdog forces the exit), so wait ~30 s more before checking. Verify:
   - `ss -ltn | grep 8642`
   - `curl http://<ts-ip>:8642/health` returns `{"status":"ok"}`
   - the log shows `api_server connected`
   - a request without the key gets 401
   - The log warning "network-accessible AND terminal backend local" is expected when the API server is bound to Tailscale only.
4. **Use the Runs API with polling, not one blocking chat/completions call.** Questions that need tools take 30–65 s (calendar ≈ 34 s, simple ≈ 8–15 s), and Siri drops a long open request with "Something went wrong" even though the VPS log shows `response ready`. A faster model does not help, because the time goes into tool calls: Sonnet took the same time as Opus, and Haiku was slower because it made more calls.
   - `POST /v1/runs` `{"model":"hermes-agent","input":"<text>"}` returns at once with `{"run_id","status":"started"}`.
   - `GET /v1/runs/<run_id>` returns a flat `status` (`completed` when done) and `output` (a plain string), which is easy to read in Shortcuts.
   - There is no system-message slot, so prefix the brevity instruction into `input`.
5. Shortcut actions:
   1. Dictate Text.
   2. Get Contents of URL: POST `/v1/runs` with JSON `model` plus `input` = "Answer briefly for reading aloud, no markdown. Question: " + Dictated Text.
   3. Get Dictionary Value `run_id`, then Set Variable `RunID`.
   4. Repeat 30×: Wait 3 s; GET `/v1/runs/`+RunID (same Authorization header); Get Dictionary Value `status`; If `completed`: Get Dictionary Value `output` (source = the GET inside the loop, which users often pick wrong), Speak Text, Stop This Shortcut.
   5. After the loop: Speak "still working, ask again in a minute".
   - If Siri still cuts the polling off, the next step is to deliver slow answers to Telegram.
6. Diagnose "Something went wrong" from the VPS: `grep 'platform=api_server' ~/.hermes/logs/gateway.log` shows `time=` per request. If a response was ready, the client timed out; otherwise look at the server.
7. On the phone: the Tailscale app with **VPN On Demand** on. Each run is a fresh session with no history. Keep a step-by-step guide in the workspace (`~/Hermes/iphone/`) and the key as a 600 file delivered via `MEDIA:`.
8. Siri triggers a shortcut by saying its name, and Siri doesn't support Estonian, so the name must be an easy English word (e.g. "Jarvis", "My Brain"). It must not clash with an app or contact, and must not start with a built-in verb (Message/Call/Play/Set). The Dictate Text language can still be Estonian. Other triggers: Action Button, Back Tap, a Home Screen icon.
9. When the user already built an earlier version and asks what to change, answer as an edit list against their existing actions (keep / edit field X / delete / add), not a full rebuild.

## Windows PC: let the VPS in (`ssh pc`) — the ssh part is not yet run end-to-end; once it is, fix this section in place

Generate the key on the VPS: `ssh-keygen -t ed25519 -f ~/.ssh/pc_access -N ""`, plus a `Host pc` alias (Tailscale IP, `IdentityFile ~/.ssh/pc_access`, `IdentitiesOnly yes`). Fill in `User` once the username is known.

The user runs one ASCII-only `.ps1` in an **admin** PowerShell. Get the file onto the PC with scp, which works because the PC already has key access to the VPS. Always give a full destination file path in quotes: `scp <vpsuser>@<vps-ts-ip>:path/setup-ssh.ps1 "$env:USERPROFILE\Downloads\setup-ssh.ps1"`. Windows usernames often contain a space (e.g. `C:\Users\Siim Alve`), PowerShell then quotes the argument, and a trailing `\` escapes the closing quote, so scp looks for a folder named `Downloads"`. Then run `powershell -ExecutionPolicy Bypass -File "..."`. The script does this:
- `Add-WindowsCapability -Online -Name OpenSSH.Server*`, `Set-Service sshd -StartupType Automatic`, `Start-Service sshd`.
- Firewall: disable the default `OpenSSH-Server-In-TCP` rule (it allows any source) and add an inbound TCP 22 rule with `-RemoteAddress <vps-ts-ip>`.
- Key: write it to `C:\ProgramData\ssh\administrators_authorized_keys` with `icacls ... /inheritance:r /grant Administrators:F /grant SYSTEM:F`. Admin accounts ignore `~\.ssh\authorized_keys`, and sshd rejects the file if its ACL is looser. Also add it to the user's file as a fallback. Prefix the key with `from="<vps-ts-ip>"`.
- `HKLM:\SOFTWARE\OpenSSH DefaultShell` = Windows PowerShell, then restart sshd. The script prints `$env:USERNAME` for the alias. If it contains a space, quote it in `~/.ssh/config` (`User "Siim Alve"`).

The PC must be awake for this to work. Suggest turning off sleep when plugged in.

Then install the local Hermes over ssh with the Windows one-liner `iex (irm https://hermes-agent.nousresearch.com/install.ps1)`. Use the `-NonInteractive` / `-SkipComputerUse` flags as needed. The data dir is `%LOCALAPPDATA%\hermes\` and the gateway runs as a Scheduled Task (`hermes gateway install`, no admin). No Telegram on the PC, because the VPS owns the bot.
