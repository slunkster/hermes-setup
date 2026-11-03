---
name: hermes-vps-hosting
description: "Use when hosting Hermes on a VPS or linking devices to it."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [hermes, vps, hosting, deployment, ssh, tailscale, estonia, remote-access, mac]
    related_skills: [hermes-agent]
---

# Hermes VPS Hosting & Remote Machine Access

Host Hermes on an always-on VPS (near Estonia / in the EU) while the user's real workspace stays on a Mac (Apple CLIs: memo, remindctl, imsg; FindMy; Obsidian vault; local files). Covers VPS choice, deployment, connectivity from the VPS to the Mac, wiring it into Hermes (two patterns), and keeping skills aligned across machines.

Reply in the language the user writes in (Estonian or English) and quote prices in EUR. For facts about Hermes itself, check the docs index first: fetch `https://hermes-agent.nousresearch.com/docs/llms.txt` and grep it; the bundled `hermes-agent` skill has the command/routing reference.

## When to Use

- User asks which VPS to use for hosting Hermes — near Estonia, in Europe, easy to set up.
- User wants a VPS-hosted Hermes to keep accessing their Mac (Apple apps, Obsidian, files).
- User asks how to use one agent / one skill set across several machines.
- User wants BOTH a full local Mac Hermes AND a 24/7 VPS Hermes (Telegram) — see "Two-instance setup" below.
- User wants the setup extended to more devices (Windows PC, iPhone) — see "More devices" below.

## More devices (Windows PC, iPhone)

1. Check the current state before you propose anything: `tailscale status` (which devices are on the tailnet and online), `nc -zv -w3 <device-ts-ip> 22` (is there an SSH server yet), and the `~/.ssh/config` aliases.
2. State the hard limits up front. iOS has no Hermes app and can't be controlled remotely, so the phone only sends requests in (chat, Siri/Shortcuts, Share). iCloud data still goes through the Mac.
3. Ask with ONE clarify call: the PC's role (peripheral `ssh pc` / full local Hermes plus shared skills and Honcho / client only), the iPhone integrations (multi-select), and what on the PC the agent may use. This user picked a full local Hermes on the PC, Siri "Ask Hermes" on the phone, and programs, files and video projects on the PC.
4. Get SSH access to the PC first, even when a full local Hermes is the goal. You can then do the install, the `.env` copy, the skills clone and `honcho.json` from the VPS yourself, so the user runs only one admin script.
5. Recipes: the Windows OpenSSH bootstrap and the iPhone API server with the Siri Shortcut are in `references/more-devices.md`. For Siri, build on the polling Runs API from the start, because a blocking call times out on tool-using questions. Then follow "Skills across machines" and `references/shared-memory-honcho.md` for the PC.
6. Hand secrets such as the API key over as a 600 file delivered via `MEDIA:`, not as text in chat. Chat text gets stored in session history and Honcho.

## Two-instance setup (local Mac Hermes + 24/7 VPS Hermes)

Default recommendation when the user keeps a full local Hermes on the Mac:

- VPS = always-on brain with the Telegram gateway, `terminal.backend: local`; Mac touched on demand via Pattern B (`ssh mac`). Never Pattern A here — it syncs `~/.hermes` onto the Mac and collides with the local install.
- Mac = unchanged local agent (TUI, Apple CLIs, computer-use).
- Telegram: one bot token can be polled by only ONE gateway (Telegram returns getUpdates conflicts). Either move the existing bot to the VPS (comment out `TELEGRAM_BOT_TOKEN` in the Mac `~/.hermes/.env` and restart the Mac gateway) or create a second bot. Check first with `grep -oE '^TELEGRAM_[A-Z_]+' ~/.hermes/.env` and `hermes gateway status` — the Mac may already run the bot. Ask the user which (clarify).
- Skills: shared git repo + `skills.create_dir` (see "Skills across machines").
- Memories: copy `USER.md` as-is; REWRITE `MEMORY.md` for the VPS instead of copying — drop Mac-only tool quirks (they mislead a Linux agent), add where it runs, what is only on the Mac, and how to reach it (`ssh mac "…"`). Entries are joined by `\n§\n` — edit the file with Python split/join, never append with a heredoc (glues the separator onto the previous entry). After that, memories drift — say so.
- Accounts (Gmail/Drive/Todoist/Outlook…): connect natively on the VPS wherever possible so they work while the Mac sleeps — decision table and recipes in `references/services-on-vps.md`.
- After the core works, offer (don't impose — user prefers few automations): nightly encrypted backup to Drive, a silent-unless-broken health check (incl. update notice), a daily briefing cron, a Desktop/phone client via the dashboard, chat-to-Drive filing (skill `telegram-to-drive`), shared memory (Honcho). Recipes: `references/vps-operations.md`. Lead with cheap, no-LLM items; present a short numbered menu, recommend 2–3, and build only what the user picks. When the user keeps asking "anything else?", say plainly when returns diminish and recommend running the setup for a week or two before adding more; offer personal (non-business) ideas too when asked.
- Close-out checklist for the user (they do these themselves): fresh provider snapshot AFTER the build (the pre-build one is stale), 2FA on every account that controls the stack (VPS provider, GitHub, Google, Tailscale, password manager), the age backup key stored as a password-manager secure note (`pbcopy < key`, paste, clear clipboard — never through chat), a test notification from the dead-man switch, and a one-time reboot test (`references/vps-operations.md`). Finish by offering the stack README with a TL;DR (`references/vps-operations.md` § "Stack documentation") — it is the cheapest, highest-value last step.
- Voice messages: user prefers accuracy over speed — local TalTech model on the VPS, see skill `estonian-speech-transcription` § "Hermes voice messages".

## Choose the VPS

Default recommendation: **Hetzner Cloud, location Helsinki** — closest major datacenter to Tallinn (~10 ms), EU/GDPR, cheapest credible option, best tooling (console, hcloud API, snapshots, firewall, backups, hourly billing).

- Wants Estonian-language support and local invoicing? Zone.ee CloudServer (Tallinn) or GetVPS.ee / Core Hosting (Tallinn, TIER III).
- Wants the absolute cheapest? Time4VPS (Vilnius, LT).
- Provider table, example specs and price anchors: `references/eu-vps-providers.md`. Re-verify prices at order time — Hetzner repriced sharply through 2026 and old numbers are stale.
- Sizing: 2 vCPU / 4 GB / 40 GB is the comfortable minimum for a personal gateway. Take 4 vCPU / 8 GB for Docker sandboxing, Playwright/browser automation, or multiple profiles. Prefer x86_64 (Hetzner's ARM CAX11 is now pricier than the x86 CX22).
- Mention that Hetzner account creation may require ID verification.

## Deploy Hermes on the VPS

Previously tinkered server of unknown state → recommend a provider rebuild (back up any `.env`/configs first; revoke any bot token that was on it).

1. OS image: plain **Ubuntu 24.04 (LTS)** — never the "with cPanel/Plesk" variants (web-hosting panels: extra services, open ports, licences); prefer 24.04 over a just-released LTS for Playwright/tooling support. Pick the EU location, enable backups.
2. SSH key access from the Mac — recipe in `references/vps-bootstrap.md` (keygen, provider without key field → `ssh-copy-id` with root password, passphrase → keychain, `Host vps` alias, diagnosing rejection).
3. Harden as root, then switch to a sudo user — exact order and commands in `references/vps-bootstrap.md`. Verify the new user's key login BEFORE disabling root/password login.
4. Install as the non-root user: `curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash -s -- --skip-setup --skip-computer-use` (non-interactive; takes >10 min, so it becomes a background process — wait on it). Launcher lands in `~/.local/bin/hermes`; use `bash -lc` over ssh.
5. Configure without the interactive wizard: copy credentials from the Mac `.env` (piped over ssh, never printed) and `hermes config set` the model/auxiliary settings — see `references/vps-bootstrap.md`. Test with `hermes chat -q "Reply with exactly: VPS OK"`.
6. Gateway as a service: `sudo loginctl enable-linger <user>` + `hermes gateway install`. Messaging deps (python-telegram-bot) lazy-install at gateway start — don't hunt for a venv to pip into.
7. Firewall: only SSH inbound — the gateway dials out. Inbound ports only if webhooks/dashboard are used.
8. Verify: `hermes gateway status`, `systemctl --user is-active hermes-gateway`, `tail ~/.hermes/logs/gateway.log` (look for "Connected to Telegram (polling mode)" and no "polling conflict"). `hermes doctor` warnings about other providers/platforms are optional noise.

PITFALLS:
- `hermes chat -q` on a host with Telegram creds starts an idle non-service gateway (`gateway run --quiet --idl…`) that polls the bot; it then blocks/conflicts with the systemd service. Before `gateway install`, check `ps -u <user> -o pid,cmd | grep '[g]ateway run'` and have it stopped.
- From inside a gateway-hosted session (TUI via gateway), the terminal tool blocks ANY command that restarts/stops/kills a gateway — even remote over ssh. Don't retry or rephrase; give the user the exact commands to run in a separate Terminal (e.g. `hermes gateway restart` on the Mac; `ssh vps 'kill <pid>; systemctl --user restart hermes-gateway'`), then verify the logs yourself afterwards.
- Browser tool (browser_exec) fails with `Chrome exited early (exit code: 127)` / `libatk-1.0.so.0: cannot open shared object file` on a fresh Ubuntu server: the bundled Chromium lacks system libs. Find them with `ldd ~/.hermes/tools/chromium-*/chrome-linux64/chrome | grep 'not found'`, then on 24.04 (t64 package names): `sudo DEBIAN_FRONTEND=noninteractive apt-get install -y libatk1.0-0t64 libatk-bridge2.0-0t64 libcups2t64 libatspi2.0-0t64 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libcairo2 libpango-1.0-0 libasound2t64 libnss3 libxkbcommon0 fonts-liberation`. Re-run `ldd` (expect 0 missing) and retry the browser call — no Hermes restart needed. Fix it directly when the user asks; don't send them to `hermes tools`.
- Set the timezone on every layer: `sudo timedatectl set-timezone Europe/Tallinn` (provider images often default to CET) AND `hermes config set timezone Europe/Tallinn` on each machine — audit list in `references/vps-operations.md` § "Timezone audit".

## Reach the Mac (connectivity foundation)

The Mac sits behind NAT; the VPS cannot reach it unaided. Recommended: **Tailscale**.

1. Mac: install Tailscale, sign in; System Settings → General → Sharing → Remote Login = ON.
2. VPS: `curl -fsSL https://tailscale.com/install.sh | sudo sh`, then `tailscale up --hostname=<name>` in the background (see pitfall below) and hand the user the login URL (same account as the Mac).
3. Key on the VPS: `ssh-keygen -t ed25519 -f ~/.ssh/mac_access -N ""`; append `mac_access.pub` to the Mac's `~/.ssh/authorized_keys`.
4. VPS `~/.ssh/config` alias: `Host mac` / `HostName <mac-tailscale-name>` / `User <macuser>` / `IdentityFile ~/.ssh/mac_access` / `ServerAliveInterval 30`. From then on `ssh mac` works from any Hermes session.
5. Optionally restrict the key on the Mac side with `from="<VPS tailscale IP>"`.

Alternative without a third-party service: reverse tunnel — the Mac runs autossh `-R 127.0.0.1:2222:localhost:22` to the VPS (autossh + LaunchAgent with KeepAlive for persistence); the VPS uses the same `Host mac` alias but with `HostName 127.0.0.1`, `Port 2222`.

## Add a Windows PC (same pattern as the Mac)

- Reach it: Windows has no sshd by default. Hand the user ONE admin PowerShell script (template: `~/Hermes/windows-pc/setup-ssh.ps1`): `Add-WindowsCapability OpenSSH.Server`, sshd auto-start, firewall rule `-RemoteAddress <VPS tailscale IP>` (disable the default any-source rule), VPS key with `from="<ip>"` into `C:\ProgramData\ssh\administrators_authorized_keys` (admins ignore `~/.ssh/authorized_keys`; ACL `icacls /inheritance:r /grant Administrators:F SYSTEM:F`), `HKLM:\SOFTWARE\OpenSSH DefaultShell` = powershell.exe. User fetches it with `scp vps:path "$env:USERPROFILE\Downloads\file.ps1"` — a trailing `\` before the closing quote breaks the path when the username has a space.
- Windows usernames often contain a space (`User "Siim Alve"` in `~/.ssh/config`, quoted).
- PITFALL quoting: nested quotes through `ssh pc '…'` into PowerShell break (and PS 5.1 drops empty-string args, so `ssh-keygen -N ""` silently gets a passphrase). Write a .ps1 locally, `scp` it to `AppData/Local/Temp/`, run `powershell -NoProfile -ExecutionPolicy Bypass -File …` with `</dev/null`. Generate keys for the PC on the VPS and scp them over.
- Hermes may already be installed (Desktop bundle); inventory first: version, `.env` keys (a different `TELEGRAM_BOT_TOKEN` = its own bot, no conflict — compare hashes), MEMORY.md, custom skills (not in `.bundled_manifest`). Move custom skills into the git repo (backup first), repo-scoped deploy key per machine, `scripts/sync.ps1` via Scheduled Task (`conhost.exe --headless powershell …`, every 15 min).
- `hermes update` while the user's own `hermes --tui` or the Desktop app runs: code updates, but "CLI exposure failed: source launcher publication failed" and every later `hermes` call re-runs "completing source-update dependencies". Have the user close the TUI/Desktop, then rerun `hermes update`.
- Honcho client on Windows: copy `honcho.json` to `%LOCALAPPDATA%\hermes\`, `hermes plugins install honcho`, `hermes config set memory.provider honcho`; check reach with `Invoke-WebRequest http://<vps-ts-ip>:8000/health`.

## Wire it into Hermes — pick one pattern

### Pattern A — native SSH terminal backend (agent's hands = the Mac)

Right choice when the user's work is Mac-centric: every existing skill (Apple CLIs, Obsidian, files) keeps working unchanged.

- VPS: `hermes config set terminal.backend ssh`.
- In `~/.hermes/.env`: `TERMINAL_SSH_HOST=<mac>` and `TERMINAL_SSH_USER=<macuser>` (both required), plus optional `TERMINAL_SSH_PORT=22`, `TERMINAL_SSH_KEY=<absolute path>`.
- What runs where: terminal commands, the file tools (read_file / write_file / patch / search_files) and execute_code all execute on the Mac — file operations are implemented as shell commands *through the backend*, so they follow it too. Gateway, cron and web tools stay on the VPS.
- Behavior: persistent shell on by default; connects with `BatchMode=yes` + `StrictHostKeyChecking=accept-new`; commands needing stdin or sudo fall back to one-shot mode.
- After switching, restart the gateway; verify with `hermes doctor` or `hermes chat -q "hostname"` (must return the Mac's name). Revert anytime with `hermes config set terminal.backend local`.
- PITFALL — state collision: the SSH backend pushes the Hermes `~/.hermes` state (credentials, skills, cache) to the remote during sessions and syncs changed files back. A second, independent Hermes on the same Mac user collides with this — retire (or leave idle) the Mac's local Hermes when the VPS takes over.
- PITFALL — one backend per Hermes instance: to cover several machines, either send explicit `ssh <alias>` commands (Pattern B style) or run separate profiles, each pinning its own backend — but profiles then have their own memory and sessions.

### Pattern B — local backend + explicit `ssh mac` (Mac as peripheral)

Right choice when the VPS should stay self-contained and the Mac is touched on demand.

- Keep `terminal.backend: local`; record "Mac tasks run via `ssh mac ...`" in AGENTS.md or memory.
- To keep the Apple skills working unmodified, install tiny wrappers on the VPS: `/usr/local/bin/memo` = `#!/bin/sh` + `exec ssh -o BatchMode=yes mac memo "$@"`; same for `remindctl` and `imsg`. If a CLI is not on PATH over non-interactive SSH, fix the Mac's login-shell PATH.
- Obsidian: file tools run on the VPS here — the vault must be synced (git/Syncthing; iCloud does not sync to Linux) or read over ssh. Pattern A avoids this entirely.

## Mac-side pitfalls (both patterns)

- Check before writing wrappers: the Apple CLIs (memo/remindctl/imsg) may not be installed at all — this user's Mac reaches Notes/Mail/Reminders/Calendar via `osascript -l JavaScript`, which works over plain SSH without new TCC prompts. Teach the VPS agent `ssh mac "<cmd>"` via its MEMORY.md instead.
- EventKit CLIs (e.g. `ekcal`) fail over SSH with `no calendar access (status 4)` — sshd has no Calendars grant and can't prompt; use Calendar.app via JXA as the remote fallback.
- Tailscale on Mac: `brew install --cask tailscale-app` needs the user's sudo password (pkg installer) — hand it to the user. On the VPS run `sudo nohup timeout 1800 tailscale up --hostname=<name> &` and give the user the login URL from its log (a foreground `tailscale up` with a short timeout cancels the login).
- Restrict the VPS key on the Mac: `from="<VPS tailscale IP>"` prefix in `~/.ssh/authorized_keys`.

- The Mac must be awake and logged in: disable sleep on power (`sudo pmset -c sleep 0` or Energy settings); a closed MacBook lid sleeps it. With FileVault, the Mac is unreachable after a reboot until someone logs in locally.
- TCC permissions: first runs of Apple-app CLIs may raise prompts that can only be granted on the Mac itself (Automation, Full Disk Access). If sshd cannot reach protected folders, grant Full Disk Access to `/usr/sbin/sshd`.
- GUI-only capabilities (FindMy app, computer-use/desktop automation) do not work over plain SSH — keep them on the Mac (a minimal local Hermes) or accept they are unavailable.
- Security: the VPS now holds a full-access key to the Mac — keys-only SSH on the VPS, ufw, updates, and `from=` restrictions on the Mac's authorized_keys where possible.

## Skills across machines

- Skills are files per install (`~/.hermes/skills`). A central agent behind a gateway (Telegram/desktop) already gives access to all skills from any device — skill availability is not the same thing as machine reachability.
- Keep sets aligned across installs: `hermes skills tap add <repo>` (GitHub repo as skill source), `skills.external_dirs` (shared folder scanned alongside), `skills.create_dir` (route agent-created skills into a git-tracked repo).
- Whole-profile moves: `hermes profile export` → .tar.gz, `hermes profile import` on the other machine (auth.json and .env always excluded; may carry more user data — inspect before sharing). Versioned multi-machine deployments: profile distributions (git repo, `hermes profile install/update`; never carries memories/sessions).
- Proven git-synced setup: private repo with `skills/` subdir; set `skills.create_dir` to `<clone>/skills` on each machine; a `scripts/sync.sh` (add -A, commit, `pull --rebase --autostash`, push) every 15 min via launchd (Mac) / crontab (VPS). VPS gets a repo-scoped write deploy key (`gh repo deploy-key add --allow-write`) behind a `Host github-skills` ssh alias.
- PITFALL — precedence is `local ~/.hermes/skills → create_dir → external_dirs`: MOVE custom skills out of `~/.hermes/skills` (backup first), or the local copies shadow the repo ones. Custom = skills not listed in `~/.hermes/skills/.bundled_manifest`.
- PITFALL — on the Mac use an https remote + `gh auth setup-git`; ssh remotes with a passphrase key can fail from launchd/agent shells.
- Skills with `platforms: [macos]` are hidden on the Linux VPS — expected, not a sync bug.
- Memories and sessions never sync automatically. When the user wants one memory across machines, self-host Honcho on the VPS and point every Hermes at it (built-in MEMORY.md/USER.md stay per machine; raise their limits too). Full recipe — Docker server, DeepSeek Flash as the cheap analysis model, client honcho.json, speed tuning, backup: `references/shared-memory-honcho.md`.
- "Skill present" ≠ "skill works": a skill needs its tools and permissions in the environment where its commands execute — this is exactly why the SSH backend beats copying skill files around.

## Verification

- `ssh mac hostname` from the VPS returns the Mac's hostname; then smoke-test each Mac data source the user relies on (Notes/Mail/Reminders/Calendar via JXA, the daily-briefing collector) and report a per-source table.
- Pattern A: `hermes doctor` passes; `hermes chat -q "which memo; hostname"` runs on the Mac.
- Pattern B: `memo --help` on the VPS reaches the Mac's memo CLI through the wrapper.

## Research pitfall

- Hermes facts: fetch and grep `https://hermes-agent.nousresearch.com/docs/llms.txt` first. If a docs page comes back empty from the extractor, retry with `curl -fsSL <url>` inside execute_code and strip HTML tags — the docs pages are large Docusaurus HTML. In the stripped text, the first match for a heading is the table of contents. Search for variable or flag names (e.g. `API_SERVER_`) with `re.finditer` to land in the body.
