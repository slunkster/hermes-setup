# Siim's Hermes stack

> **Public sanitized copy** of my private Hermes setup repo. IP addresses, e-mails, calendar/Drive/Sheet IDs, device IDs and contacts are replaced with `<PLACEHOLDERS>`. No secrets were ever stored here; section 12 says where they live.

Personal AI-assistant setup: one always-on Hermes agent on a VPS (Telegram, 24/7) plus a
local Hermes on the MacBook and on the Windows PC, all sharing skills (this repo) and long-term
memory (Honcho). The iPhone talks to the VPS (Telegram; Siri shortcut in progress).

Built 28–29 Oct 2026. This file is the single source of truth for *what runs where* — read it
before changing or repairing anything. No secrets are stored in this repo; section 12 says
where each one lives.

---

## TL;DR

- **VPS** `ssh vps` (Contabo, Ubuntu 24.04, user `siim`, <VPS_PUBLIC_IP> / Tailscale **<VPS_TAILSCALE_IP>**)
  runs Hermes 24/7: **Telegram bot**, Gmail/Drive/Calendar, Todoist, Estonian voice messages
  (local TalTech Whisper), **08:00 briefing**, **09:00 health check**, **03:30 encrypted backup → Google Drive**,
  and **Honcho** shared memory (Docker).
- **Mac** (Tailscale **<MAC_TAILSCALE_IP>**) runs its own local Hermes (TUI, Apple apps, Xcode…).
  The VPS reaches the Mac with `ssh mac "…"` for Notes / Mail.app (Outlook + UT mail) / Reminders — **only while the Mac is awake**.
- **Windows PC** `slunkpc` (Tailscale **<PC_TAILSCALE_IP>**) runs its own local Hermes (Desktop app / `hermes --tui`,
  DaVinci Resolve MCP, ETS2, video projects). The VPS reaches it with `ssh pc "…"` (PowerShell) — **only while the PC is awake**.
  The Desktop app can also connect to the VPS dashboard `http://<VPS_TAILSCALE_IP>:9119` (user `siim`).
- **iPhone** = Telegram (works) + Siri shortcut "Jarvis" → VPS API server `:8642` over Tailscale — **⚠ not working yet** (section 2).
- **Skills** = this private repo, auto-synced every 15 min on all three machines. **Memory** = Honcho on the VPS, shared by all three.
- **Alerts:** problems → Telegram at 09:00 (silent when fine); VPS/bot dead → healthchecks.io email/Telegram after ~30 min.
- **Backup key** (decrypts backups) is ONLY on the Mac `~/.config/hermes-backup/age-key.txt` + Bitwarden note
  "Hermes VPS backup key (age)". Lose both = backups are useless.
- **Things only you can do:** restart gateways after updates, OAuth logins, passwords.
  Hermes refuses to restart a gateway from inside a chat — run these in a normal Terminal:
  ```
  ssh vps 'systemctl --user restart hermes-gateway'   # VPS bot
  hermes gateway restart                              # Mac
  ```
- **Updating:** `hermes update` (Mac) / `ssh vps 'hermes update'` → then the restart line above. The 09:00 check tells you when.
- **Nightly order (VPS):** 03:30 backup → ~04:00 security updates → 04:30 reboot *only if needed* → 08:00 briefing → 09:00 check.

---

## Contents

1. [Architecture](#1-architecture)
2. [Machines](#2-machines)
3. [Network, SSH & firewall](#3-network-ssh--firewall)
4. [Hermes configuration](#4-hermes-configuration)
5. [Connected services](#5-connected-services)
6. [Memory](#6-memory)
7. [Skills & sync](#7-skills--sync)
8. [Scheduled jobs](#8-scheduled-jobs)
9. [Backups & restore](#9-backups--restore)
10. [Monitoring & alerts](#10-monitoring--alerts)
11. [Updates & maintenance](#11-updates--maintenance)
12. [Where secrets live](#12-where-secrets-live)
13. [Runbook — when something breaks](#13-runbook--when-something-breaks)
14. [Costs](#14-costs)
15. [Known limitations](#15-known-limitations)
16. [Files in this repo](#16-files-in-this-repo)
17. [History](#17-history)

---

## 1. Architecture

```
                        Telegram (phone, anywhere)
                                 │
                                 ▼
┌──────────────────────── VPS  (Contabo, 24/7) ─────────────────────────┐
│ hermes-gateway (systemd --user)   ← Telegram bot, cron jobs            │
│ hermes-dashboard :9119 (Tailscale only) ← Windows/Mac desktop app      │
│ API server :8642 (inside hermes-gateway, Tailscale only) ← iPhone Siri │
│ Honcho (Docker: api :8000, deriver, postgres, redis) ← shared memory   │
│ TalTech Whisper (local Estonian speech-to-text)                        │
│ cron: skills sync 15 min · backup 03:30 · healthchecks ping 10 min     │
│ Direct APIs: Google (Gmail/Drive/Calendar/Docs), Todoist MCP,          │
│              Anthropic, OpenAI, DeepSeek, Open-Meteo, Ilmateenistus    │
└───────────────┬───────────────────────────────┬──────────────────────┘
                │ Tailscale (WireGuard mesh)     │ HTTPS
       ssh mac "…" (only when awake)             ▼
                ▼                         Google Drive "Hermes VPS backups"
┌──────── MacBook Air (M5) ────────┐      GitHub slunkster/hermes-skills
│ local Hermes (TUI, launchd gw,   │      healthchecks.io
│  NO Telegram)                    │
│ Apple Notes, Mail.app (Outlook   │
│  work + student@ut.ee), Reminders,  │◄──── Windows PC "slunkpc": Hermes desktop
│  Calendar, files, Xcode, UniHub  │      (own local Hermes, see below)
│ Honcho client → VPS              │
└──────────────────────────────────┘

        ssh pc "…" (PowerShell, only when awake)            iPhone
                ▼                                     Telegram · Siri → :8642
┌──────── Windows PC "slunkpc" (Win 11) ───────┐      (Tailscale app)
│ local Hermes (Desktop app, TUI, NO Telegram) │
│ DaVinci Resolve MCP, video projects, ETS2    │
│ skills repo clone + Honcho client → VPS      │
└──────────────────────────────────────────────┘
```

Design principle: **one brain, several hands.** The VPS is the canonical 24/7 agent; the Mac (Apple-only
data) and the Windows PC (programs, local files, video) are peripherals the VPS can reach over SSH,
and each also runs a full local agent of its own. All share skills (git) and memory (Honcho).
Built-in memory files (`MEMORY.md`/`USER.md`) are per machine.

---

## 2. Machines

### VPS
| | |
|---|---|
| Provider | Contabo (hostname `vmi3703777`) |
| OS | Ubuntu 24.04 LTS, x86_64, 4 vCPU, 8 GB RAM, 96 GB disk (~11 GB used) |
| Public IP | <VPS_PUBLIC_IP> (only SSH open) |
| Tailscale | `hermes-vps` <VPS_TAILSCALE_IP> |
| Login | `ssh vps` → user `siim` (key only; root + password login disabled; passwordless sudo) |
| Timezone | Europe/Tallinn |
| Hermes | v0.22.5, `~/.hermes`, launcher `~/.local/bin/hermes` (use `bash -lc` over ssh) |
| Work dir | `~/Hermes` (rules in `~/Hermes/.hermes.md`) |
| Snapshots | Contabo panel — latest taken 29.10.2026 after full setup |

### MacBook Air (M5, macOS 27)
| | |
|---|---|
| Tailscale | `siims-macbook-air` <MAC_TAILSCALE_IP> |
| Hermes | v0.22.2 (update pending), `~/.hermes`, gateway via launchd `ai.hermes.gateway` |
| Telegram | **disabled** on the Mac (`TELEGRAM_BOT_TOKEN` commented out in `~/.hermes/.env`) |
| Reachable from VPS | Remote Login ON; VPS key in `~/.ssh/authorized_keys` restricted with `from="<VPS_TAILSCALE_IP>"` |
| Must be | awake + logged in for `ssh mac` (FileVault: unreachable after reboot until login) |
| Work dir | `~/Hermes/<topic>/` (rules `~/Hermes/.hermes.md`) |

### Windows PC (Windows 11 Pro)
| | |
|---|---|
| Tailscale | `slunkpc` <PC_TAILSCALE_IP> |
| Windows user | `Siim Alve` (**space in the name** — always quote paths) |
| Hermes | v0.22.7, data `%LOCALAPPDATA%\hermes`, launcher `%LOCALAPPDATA%\hermes\bin\hermes.exe`; Desktop app + `hermes --tui` |
| Gateway | Scheduled Task `Hermes_Gateway` (at login); **no messaging platforms** — `TELEGRAM_*` commented out in `.env` (that bot's token was already revoked) |
| Reachable from VPS | OpenSSH Server (auto-start), firewall rule `Hermes-VPS-SSH` allows port 22 **only from <VPS_TAILSCALE_IP>**; VPS key in `C:\ProgramData\ssh\administrators_authorized_keys` with `from="<VPS_TAILSCALE_IP>"`; default SSH shell = PowerShell. Set up with `infra/windows/setup-ssh.ps1` (admin PowerShell). |
| Must be | awake for `ssh pc` (turn off sleep on AC if it should always be reachable) |
| Extras | DaVinci Resolve MCP bridge `~\Downloads\davinci-resolve-mcp`, ETS2 mods, Coop Pank widget (`~\.enablebanking`) |

Remote option: the Desktop app can also use the VPS — Settings → Gateways → Remote gateway
`http://<VPS_TAILSCALE_IP>:9119`, user `siim`. Use **the IP**, not `hermes-vps` (Host-header check).

### iPhone
- **Telegram** → VPS bot (works).
- **Tailscale app** with VPN On Demand → dashboard `http://<VPS_TAILSCALE_IP>:9119` in Safari.
- **Siri shortcut "Jarvis"** → VPS API server — **⚠ NOT WORKING YET.** Status (4 Nov 2026):
  - API server is up and tested from the VPS (`curl http://<VPS_TAILSCALE_IP>:8642/health`; key in VPS `~/Hermes/iphone/api-key.txt`).
  - v1 (one `POST /v1/chat/completions`) worked for quick questions but Siri gives up on tool-heavy
    ones ("something went wrong") — e.g. "schedule tomorrow" takes ~34 s. A faster model doesn't help (time is in tools).
  - v2 (`POST /v1/runs` → poll `GET /v1/runs/<id>` every 3 s until `output` is non-empty) was built by hand on
    the phone; the requests work (Show Result showed `completed`) but the loop's If never matched.
  - Next step: `~/Hermes/iphone/Jarvis-unsigned.shortcut` (generated on the VPS, contains the key — never commit) must be
    signed on the Mac: `bash ~/Hermes/iphone/sign-and-deliver.sh` (Mac awake) → iCloud Drive `Jarvis.shortcut` →
    open on iPhone → Add Shortcut. Not yet tested on a phone. Guide: `~/Hermes/iphone/siri-shortcut.md` (copy in `infra/iphone/`).

---

## 3. Network, SSH & firewall

**Tailscale** account: siim.alve@ (Google login, 2FA). All private traffic goes over it.

**SSH aliases**
| From | Alias | Target | Key |
|---|---|---|---|
| Mac | `vps` | siim@<VPS_PUBLIC_IP> | `~/.ssh/id_ed25519` (passphrase in macOS keychain) |
| VPS | `mac` | siimalve@<MAC_TAILSCALE_IP> | `~/.ssh/mac_access` (only valid from VPS Tailscale IP) |
| VPS | `github-skills` | git@github.com | `~/.ssh/hermes_skills_deploy` (deploy key, this repo only, write) |
| VPS | `pc` | "Siim Alve"@<PC_TAILSCALE_IP> | `~/.ssh/pc_access` (only valid from VPS Tailscale IP) |
| PC | `github-skills` | git@github.com | `~\.ssh\hermes_skills_deploy` (own deploy key "slunkpc (Windows Hermes)", write) |
| PC | — | `ssh siim@<VPS_TAILSCALE_IP>` (or the public IP) | `~\.ssh\id_ed25519` |

**VPS firewall (ufw):** deny incoming except `OpenSSH`, plus on `tailscale0` only: `9119/tcp` (dashboard),
`8642/tcp` (API server for the iPhone), `8765/tcp` (SNK web preview).
Docker publishes Honcho `:8000` only on 127.0.0.1 and <VPS_TAILSCALE_IP> (verified unreachable from
the public IP). Postgres/Redis are not published at all. fail2ban active.

**SSH hardening:** `/etc/ssh/sshd_config.d/00-hardening.conf` — no passwords, no keyboard-interactive, no root.

---

## 4. Hermes configuration

### VPS (`~/.hermes/config.yaml`, change only with `hermes config set`)
| Setting | Value |
|---|---|
| Main model | `claude-opus-5-5` (Anthropic, OAuth token) |
| Title generation | DeepSeek `deepseek-flash` |
| TTS / image gen | OpenAI |
| Web search | brave-free |
| Terminal backend | local, cwd `/home/siim/Hermes` |
| `skills.create_dir` | `/home/siim/hermes-skills/skills` |
| Memory | `memory_char_limit 5000`, `user_char_limit 2500`, `memory.provider honcho` |
| Speech-to-text | `stt.provider local`, `stt.language et`, `stt.local.model /home/siim/Hermes/whisper-et/model2604/ct2`, cpu/int8 |
| MCP | `todoist` → https://ai.todoist.net/mcp (OAuth) |
| Plugins | honcho |

**Voice:** TalTech `whisper-large-v3-turbo-et-verbatim-2604` (1.6 GB, ~2–5× audio length on CPU,
104/104 words on the reference test). Writes numbers as words ("neliteist nelikümmend viis") — the
agent understands that. Switch to OpenAI if speed matters more than accuracy:
`ssh vps 'bash -lc "hermes config set stt.provider openai; hermes config set stt.openai.model gpt-transcribe"'`
(back: `stt.provider local`). OpenAI tested clearly worse on Estonian.

### Mac
Same model, `memory.provider honcho` (→ VPS Honcho), `skills.create_dir
/Users/siimalve/Hermes/hermes-skills/skills`, memory limits 5000/2500, `terminal.cwd /Users/siimalve/Hermes`.

### Windows PC
Same model (`claude-opus-5-5`), `memory.provider honcho` (→ VPS Honcho, `%LOCALAPPDATA%\hermes\honcho.json`),
`skills.create_dir C:/Users/Siim Alve/hermes-skills/skills`, memory limits 5000/2500, `timezone Europe/Tallinn`,
`delegation.provider deepseek` / `delegation.model deepseek-flash`. No Telegram.

### API server (VPS, for the iPhone)
Part of `hermes-gateway`: `API_SERVER_ENABLED=true`, `API_SERVER_HOST=<VPS_TAILSCALE_IP>`, `API_SERVER_PORT=8642`,
`API_SERVER_KEY=…` in VPS `.env` (copy of the key: `~/Hermes/iphone/api-key.txt`). Model name `hermes-agent`.
Endpoints used: `/v1/chat/completions` (blocking), `/v1/runs` + `/v1/runs/<id>` (async; `status`, `output`).
Each request is a fresh session. Changing the key → restart the gateway + update the shortcut.

### Dashboard (VPS)
`~/.config/systemd/user/hermes-dashboard.service` → `hermes dashboard --host <VPS_TAILSCALE_IP> --port 9119`.
Basic auth: user `siim`, password set with `ssh -t vps '~/bin/set-dashboard-password'`
(env vars `HERMES_DASHBOARD_BASIC_AUTH_*` in VPS `.env`).

---

## 5. Connected services

| Service | How | Where it works |
|---|---|---|
| Telegram | bot token in VPS `.env`, allowed user <TELEGRAM_USER_ID> | VPS only (Mac + PC bots disabled) |
| Gmail, Drive, Docs, Sheets, Google Calendar (incl. "Moodle" iCal, ÕIS2 timetable, Töö - SNK) | `google-workspace` skill, token `~/.hermes/google_token.json` (copied from Mac) | VPS + Mac |
| Todoist | MCP, **separate OAuth login per machine** (sharing one refresh token would log the other out) | VPS + Mac |
| Outlook work `work@example.org`, `student@ut.ee` | Mail.app via JXA (`~/Hermes/paevaulevaade/outlook_mail.js`) | Mac; VPS via `ssh mac` when awake |
| Apple Notes / Reminders / Calendar.app | `osascript -l JavaScript` | Mac; VPS via `ssh mac` |
| Exchange/UT calendars | `ekcal` (EventKit) on Mac — **fails over SSH** (no TCC grant); work events are in Google "Töö - SNK" anyway | Mac only |
| Weather | Open-Meteo (Treski/Värska, Tartu, Viljandi) + Ilmateenistus warnings XML | VPS briefing |
| DaVinci Resolve | MCP bridge (`resolve_mcp_bridge.py`) | PC; VPS via `ssh pc` when awake |
| PC programs / files / video projects | PowerShell | PC; VPS via `ssh pc` when awake |
| LLM APIs | Anthropic (main), OpenAI (TTS, images, Honcho embeddings), DeepSeek (titles, Honcho analysis, sub-agents) | all |

Useful IDs:
- Calendar "Töö - SNK": `<WORK_CALENDAR_ID>@group.calendar.google.com`; personal = `you@gmail.com`
- Google Doc "Hermes – mõtted ja ideed" (quick-capture ideas): `<SHEET_ID>`
  (the older doc "Mõtted" is a grant draft — never write there)
- Drive folder "Hermes VPS backups": `<DRIVE_FOLDER_ID>`
- Todoist projects: Inbox, Töö, HUUB, MTÜ, Välk, Ülikool; label `ostud` = shopping

---

## 6. Memory

Two layers, active on all three machines:

1. **Built-in** `~/.hermes/memories/MEMORY.md` (agent notes) + `USER.md` (about Siim) — injected into
   every prompt, **per machine, not synced**. VPS version was written for Linux (Mac-only tips removed).
2. **Honcho** (self-hosted on VPS, `~/honcho`, upstream plastic-labs/honcho) — stores conversations from
   both machines in workspace `hermes`, user peer `siim`, AI peer `hermes`; builds a profile and facts.
   - API `http://<VPS_TAILSCALE_IP>:8000`, auth on (JWT in `~/.config/honcho-jwt` on VPS, copied into each
     machine's `~/.hermes/honcho.json`). VPS `honcho.json` has `pinUserPeer: true` (Telegram user → `siim`).
   - Analysis model: **DeepSeek `deepseek-flash`** for deriver, summaries, dreams and all dialectic
     levels (`STRUCTURED_OUTPUT_MODE=json_object` — DeepSeek rejects json_schema). Embeddings stay on
     OpenAI `text-embedding-3-small` (DeepSeek has none). Non-secret settings: `infra/vps/honcho/env-nonsecret.txt`.
   - Tuning: `DERIVER_REPRESENTATION_BATCH_MAX_AGE_SECONDS=120` (new facts within ~2 min),
     `DERIVER_MODEL_CONFIG__MAX_OUTPUT_TOKENS=6000`, `DIALECTIC_LEVELS__low__MAX_TOOL_ITERATIONS=2`.
   - Verified 4 Nov 2026: the PC Hermes recalled a fact only stored in Honcho ("Väikelinna pubi") in ~1 s.
   - Speed: `honcho_search` ~0.3 s, `honcho_reasoning` ~6 s → agents are told to prefer search for facts.
   - Health: `curl http://<VPS_TAILSCALE_IP>:8000/health`; queue: `GET /v3/workspaces/hermes/queue/status`.

Sessions/chat history (`state.db`) are per machine and not shared.

---

## 7. Skills & sync

- Repo: **github.com/slunkster/hermes-skills** (private). Clones: Mac `~/Hermes/hermes-skills`, VPS `~/hermes-skills`,
  PC `C:\Users\Siim Alve\hermes-skills`.
- Only *personal* skills live here; the ~58 bundled Hermes skills come with each install.
- `skills.create_dir` points here on all machines → skills Hermes creates/patches land in the repo.
- `scripts/sync.sh` = `git add -A` → commit → `pull --rebase --autostash` → push. Runs every 15 min
  (Mac launchd `ee.siim.hermes-skills-sync`, VPS crontab). Windows: `scripts/sync.ps1`, Scheduled Task
  `HermesSkillsSync` (every 15 min, hidden via `conhost.exe --headless`).
- 4 Nov 2026: the PC's 11 own skills were moved in (davinci-resolve-editing, concert-multicam-edit,
  estonian-e-invoicing, windows-python-app-packaging, academic-coursework, car-buying-research,
  document-harmonization, ets2-mod-install, personal-bank-balance-access, source-consistency-audit,
  browser-harness). Backup: PC `%LOCALAPPDATA%\hermes\backups\skills-before-repo-20261104-0000`.
- The old local copies were removed from `~/.hermes/skills` on the Mac (they would shadow the repo).
  Backup of the pre-repo state: Mac `~/Hermes/backups/hermes-skills-before-repo-20261028.tgz`.
- `platforms: [macos]` skills (ios-app-development, macos-app-without-xcode, macos-terminal-glyph-diagnosis) are hidden on the VPS by design;
  `platforms: [linux, macos]` (hermes-vps-hosting) is hidden on Windows.

Skills added during the setup:
| Skill | What |
|---|---|
| `hermes-vps-hosting` | how this whole stack was built + pitfalls (use it when changing infra) |
| `homme` | daily briefing; VPS variant uses `~/.hermes/scripts/homme.sh` (adds weather/ice) |
| `telegram-to-drive` | send file/photo + note "Algatusruum / arved" → filed in Drive with a descriptive name (`scripts/drive ls|up`) |
| `quick-capture` | voice/text dump → Todoist tasks / `ostud` / calendar / ideas doc |

---

## 8. Scheduled jobs

| When | Where | What | Delivers |
|---|---|---|---|
| every 10 min | VPS crontab | `~/bin/hc-ping.sh` → healthchecks.io (fail ping if gateway inactive) | healthchecks.io |
| every 15 min | VPS crontab + Mac launchd + PC Scheduled Task | skills git sync | — |
| 03:30 | VPS crontab | `~/bin/hermes-backup.sh` encrypted backup → Drive, keeps 14 | log `~/Hermes/backups/backup.log` |
| ~04:00–04:10 | VPS systemd timer | `apt-daily-upgrade` security updates (override in `/etc/systemd/system/apt-daily-upgrade.timer.d/`) | — |
| 04:30 if needed | unattended-upgrades | automatic reboot (`/etc/apt/apt.conf.d/52hermes-auto-reboot`) | — |
| 08:00 | Hermes cron `49c434663fd5` | "Hommikune ülevaade" — script `homme.sh` + skill `homme` (Opus) | Telegram |
| 09:00 | Hermes cron `0bc82b85b9a6` | `healthcheck.sh`, no LLM, **silent when OK** | Telegram |

Manage Hermes cron: `ssh vps 'bash -lc "hermes cron list"'`, run now: `hermes cron run <id>`, history: `hermes cron runs <id>`.

---

## 9. Backups & restore

### What exists
| Layer | What | Where |
|---|---|---|
| Contabo snapshot | whole server | Contabo panel (manual; take one after big changes) |
| Nightly backup | Hermes state + Honcho DB + scripts | Google Drive "Hermes VPS backups", 14 newest kept, `hermes-vps-YYYY-MM-DD_HHMM.tar.gz.age` (~11 MB) |
| Skills | all personal skills | GitHub (this repo) |
| Infra scripts/config | copies, no secrets | `infra/` in this repo |

Nightly archive contents: `hermes/` (config.yaml, .env, auth.json, SOUL.md, memories, cron, sessions,
mcp-tokens, Google token + client secret, pairing, `state.db` via sqlite `.backup`, honcho.json,
honcho-jwt), `home.tar` (`~/Hermes` without the 1.6 GB speech model, `~/.ssh`, systemd user units,
`~/bin`, `.config/hc-ping-url`, `.config/honcho-jwt`, age public key), `crontab.txt`,
`honcho.sql.gz` (pg_dump), `honcho.env`, `honcho-compose.yml`.

Encrypted with **age** to the Mac's public key. The VPS cannot decrypt its own backups (on purpose).

### Decrypt (Mac, or any machine with `age` + the key from Bitwarden)
```
age -d -i ~/.config/hermes-backup/age-key.txt hermes-vps-….tar.gz.age | tar xz
```

### Restore A — roll back the VPS (fastest)
Contabo panel → restore snapshot. Then restore last night's data on top if the snapshot is old (Restore B steps 4–7).

### Restore B — rebuild on a fresh server
1. New VPS, Ubuntu 24.04. Create user `siim`, copy key, harden SSH, ufw (see `infra/vps/system/`).
2. `curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash -s -- --skip-setup --skip-computer-use`
3. `sudo apt install age sqlite3 docker.io docker-compose-v2 git curl ufw fail2ban unattended-upgrades`; Tailscale `curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up --hostname=hermes-vps`. (New Tailscale IP? Update it in: Mac `~/.ssh/authorized_keys` `from=`, both `honcho.json`, dashboard unit, Honcho compose port, healthcheck script, this README.)
4. Copy the decrypted backup up; put `hermes/*` back into `~/.hermes/`, untar `home.tar` into `~`, `crontab crontab.txt`.
5. Speech model: re-download (see `estonian-speech-transcription` skill) to `~/Hermes/whisper-et/model2604/ct2`; `hermes pm install --extra stt-whisper`.
6. Honcho: `git clone https://github.com/plastic-labs/honcho ~/honcho`, copy `honcho-compose.yml` → `docker-compose.yml`, `honcho.env` → `.env`;
   `docker compose up -d database` → `gunzip -c honcho.sql.gz | docker compose exec -T database psql -U postgres postgres` → `docker compose up -d --build`.
7. `hermes plugins install honcho`, `hermes memory setup honcho </dev/null` (just to prepare deps), `sudo loginctl enable-linger siim`, `hermes gateway install`, `systemctl --user enable --now hermes-dashboard`, apply `infra/vps/system/` timer + reboot config, `git clone git@github-skills:slunkster/hermes-skills.git ~/hermes-skills`.
8. Verify: `hermes doctor`, Telegram message, `bash ~/.hermes/scripts/healthcheck.sh` (silent = good), `ssh mac hostname`.

### Restore C — Mac lost
The VPS keeps working alone. New Mac: install Hermes, `git clone` this repo to `~/Hermes/hermes-skills`,
point `skills.create_dir` there, restore the **age key from Bitwarden** to `~/.config/hermes-backup/age-key.txt`,
re-add Tailscale, a new SSH key for `vps`, the VPS `mac_access.pub` into `authorized_keys` (`from="<VPS_TAILSCALE_IP>"`),
copy `~/.hermes/honcho.json` from the VPS. Mac memories (`MEMORY.md`) are not backed up — Honcho has the long-term memory.

---

## 10. Monitoring & alerts

| Check | Detects | Alert |
|---|---|---|
| 09:00 `healthcheck.sh` | backup missing/older than 26 h or errors in log · disk ≥85% · Google login invalid · skills sync/GitHub broken · dashboard down · Honcho down or containers missing · Hermes update available (VPS or Mac) | Telegram, only if something is wrong |
| healthchecks.io "Hermes VPS" (period 10 min, grace 20 min) | VPS down, network down, or `hermes-gateway` inactive | email (+ Telegram via @HealthchecksBot), independent of the VPS |
| fail2ban | SSH brute force | (blocks silently) |

Ping URL is in `~/.config/hc-ping-url` on the VPS (not in this repo).

---

## 11. Updates & maintenance

- **Hermes** (manual, when the 09:00 check says so):
  - VPS: `ssh vps 'bash -lc "hermes update"'` then `ssh vps 'systemctl --user restart hermes-gateway'`
  - Mac: `hermes update` then `hermes gateway restart` (closes the current chat)
- **Ubuntu security updates:** automatic ~04:00, reboot at 04:30 only when required. Reboot tested 29.10.2026: everything returns in ~1 min.
- **Honcho** (occasionally): `cd ~/honcho && git pull && sg docker -c "docker compose up -d --build"` — check the `.env` template for new variables first.
- **Contabo snapshot** after any bigger change.
- **Dashboard password:** `ssh -t vps '~/bin/set-dashboard-password'`.
- Docker group note: in scripts/cron use `sg docker -c "docker compose …"` (the systemd user session predates the group change).

---

## 12. Where secrets live

Never commit any of these. All are in the nightly encrypted backup unless noted.

| Secret | Location |
|---|---|
| Anthropic token, OpenAI, DeepSeek keys | `~/.hermes/.env` (VPS + Mac) |
| Telegram bot token | VPS `~/.hermes/.env` (Mac + PC copies commented out) |
| API server key (iPhone) | VPS `.env` `API_SERVER_KEY` + `~/Hermes/iphone/api-key.txt`; also inside `Jarvis-unsigned.shortcut` and the phone's shortcut |
| Google OAuth token + client secret | `~/.hermes/google_token.json`, `google_client_secret.json` (both machines) |
| Todoist OAuth | `~/.hermes/mcp-tokens/todoist*.json` (separate per machine) |
| Dashboard basic-auth | VPS `.env` `HERMES_DASHBOARD_BASIC_AUTH_*` |
| Honcho JWT secret + LLM keys | VPS `~/honcho/.env` |
| Honcho client token | VPS `~/.config/honcho-jwt`; `apiKey` in each `~/.hermes/honcho.json` |
| healthchecks ping URL | VPS `~/.config/hc-ping-url` |
| GitHub | Mac: `gh` login (keyring, account slunkster); VPS + PC: own deploy keys `~/.ssh/hermes_skills_deploy` |
| SSH keys | Mac `~/.ssh/id_ed25519` (passphrase in keychain); PC `~\.ssh\id_ed25519`; VPS `~/.ssh/mac_access`, `~/.ssh/pc_access` |
| PC secrets | `%LOCALAPPDATA%\hermes\.env`, `honcho.json`, `~\.enablebanking\` — **not in the nightly backup** |
| **Backup decryption key** | **Mac `~/.config/hermes-backup/age-key.txt` + Bitwarden — NOT in any backup** |

Accounts with 2FA: Contabo, GitHub, Google, Tailscale, Bitwarden.

---

## 13. Runbook — when something breaks

| Symptom | Check / fix |
|---|---|
| Bot doesn't answer on Telegram | `ssh vps 'systemctl --user status hermes-gateway'`; `tail -50 ~/.hermes/logs/gateway.log` (look for "polling conflict" → something else uses the token: only the VPS may). Restart: `ssh vps 'systemctl --user restart hermes-gateway'`. |
| "polling conflict" | A second poller: the Mac gateway (token must stay commented out) or a stray `gateway run --idle` process from `hermes chat -q` → `ps -u siim -o pid,cmd \| grep '[g]ateway run'`, kill it. |
| Briefing says Outlook unreachable / `ssh mac` fails | Mac asleep, lid closed, or rebooted with FileVault (log in once). `ssh vps 'ssh mac hostname'`. |
| Google errors / "login invalid" alert | Re-run the google-workspace setup on the Mac, then `scp ~/.hermes/google_token.json vps:.hermes/`. |
| Todoist errors on VPS | `ssh -t vps hermes mcp login todoist` (paste the redirect URL back). |
| Honcho alert / memory tools fail | `ssh vps 'cd ~/honcho && sg docker -c "docker compose ps"'` → `… up -d`; logs `docker compose logs --since 10m deriver api`. Hermes keeps working without Honcho (built-in memory still active). |
| Memory slow | expected for `honcho_reasoning` (~6 s, DeepSeek); search is ~0.3 s. Main latency is Opus itself. |
| Voice messages slow | local model ≈ 2–5× clip length. Option: switch to OpenAI (section 4) — less accurate. |
| Backup alert | `ssh vps 'tail -20 ~/Hermes/backups/backup.log'`; run `~/bin/hermes-backup.sh` by hand. |
| Skills not syncing | `~/Hermes/hermes-skills/.sync.log` (Mac), `~/hermes-skills/.sync.log` (VPS); resolve git conflicts manually, then `sh scripts/sync.sh`. |
| Windows app can't connect | URL must be exactly `http://<VPS_TAILSCALE_IP>:9119`; Tailscale running on the PC; `ssh vps 'systemctl --user status hermes-dashboard'`. |
| `ssh pc` times out | PC asleep/off, or Tailscale not running on it. `ssh vps 'ssh pc hostname'`. |
| Complex commands over `ssh pc` break | Quoting through ssh → PowerShell is fragile: write a `.ps1`, `scp` it to `AppData/Local/Temp/`, run `powershell -NoProfile -ExecutionPolicy Bypass -File …`. |
| PC: every `hermes` command says "completing source-update dependencies" | An update couldn't replace `hermes.exe` because `hermes --tui` was open. Close the TUI, run `hermes update` again. |
| Siri: "something went wrong" | Tailscale off on the phone (VPN On Demand), or the question took too long (use the polling shortcut / Telegram). Check the VPS log: `grep api_server ~/.hermes/logs/gateway.log \| tail`. |
| Agent "can't restart the gateway" | By design — run the restart command yourself in a normal Terminal. |
| Disk filling | `ssh vps 'df -h; du -sh ~/.hermes/* ~/Hermes/* | sort -h | tail'`; Docker: `sg docker -c "docker system df"`. |

---

## 14. Costs (approximate)

| Item | Cost |
|---|---|
| Contabo VPS | monthly plan (see Contabo invoice) |
| Anthropic (Opus 5.5) | the main cost; scales with use |
| DeepSeek Flash (Honcho analysis, titles) | cents–~1–2 €/month |
| OpenAI (embeddings, TTS, images) | cents/month |
| Speech-to-text | free (local) |
| Tailscale, healthchecks.io, GitHub private repo, Open-Meteo | free |

No API spending limits are set (deliberate choice).

---

## 15. Known limitations

- Mac-dependent features (Outlook/UT mail, Apple Notes, Reminders, `ekcal` calendars, Mac files) only work while the Mac is awake.
- PC-dependent features (`ssh pc`: DaVinci Resolve, local files, video projects) only work while the PC is awake.
- **Siri shortcut is not working yet** (see section 2, iPhone). Siri runs have no chat history; long tasks belong in Telegram.
- PC Hermes state (`%LOCALAPPDATA%\hermes`) is not in the nightly backup — skills are in git, memory in Honcho.
- No road-condition data (Tark Tee has no open API) — ice warnings come from weather + Ilmateenistus.
- Built-in memory files and chat history are per machine; only Honcho is shared.
- Honcho starts nearly empty; it gets useful after a week or two of conversations.
- Dashboard session writes from the Windows app may be refused while the Telegram gateway owns the profile (chatting works).
- The 09:00 check runs on the VPS itself — total VPS failure is covered by healthchecks.io instead.

---

## 16. Files in this repo

```
README.md                         this document
scripts/sync.sh                   skills git sync (Mac + VPS)
scripts/sync.ps1                  skills git sync (Windows PC, Scheduled Task HermesSkillsSync)
skills/                           personal Hermes skills (see section 7)
infra/vps/bin/                    hermes-backup.sh, hc-ping.sh, set-dashboard-password  (→ VPS ~/bin)
infra/vps/hermes-scripts/         homme.sh, healthcheck.sh                             (→ VPS ~/.hermes/scripts)
infra/vps/paevaulevaade/          collect_vps.py, calendar_all.py, todoist_mcp.py      (→ VPS ~/Hermes/paevaulevaade)
infra/vps/systemd-user/           hermes-dashboard.service                             (→ VPS ~/.config/systemd/user)
infra/vps/honcho/                 docker-compose.yml, env-nonsecret.txt                (→ VPS ~/honcho)
infra/vps/system/                 crontab + apt/ssh/timer config snapshot
infra/mac/                        ee.siim.hermes-skills-sync.plist                     (→ Mac ~/Library/LaunchAgents)
infra/windows/                    setup-ssh.ps1 (admin: OpenSSH Server for `ssh pc`)   (run once on the PC)
infra/iphone/                     siri-shortcut.md (guide, no key)
```
`infra/` holds copies for reference/restore — the live files are on the machines. After changing a
live script, copy it back here.

---

## 17. History

**28–29 Oct 2026 — initial build**
VPS rebuilt (Ubuntu 24.04), hardened (user `siim`, keys only, ufw, fail2ban, auto updates) →
Hermes installed + configured from the Mac's keys → Telegram moved from Mac to VPS → skills moved
into this repo with 15-min sync → VPS memories written → Tailscale + `ssh mac` → Google and Todoist
directly on VPS → dashboard for the Windows app → nightly encrypted backups to Drive → 08:00 briefing
→ TalTech Estonian speech model (chosen over OpenAI after tests) → 09:00 health check → memory
limits raised + self-hosted Honcho shared by both machines, analysis on DeepSeek Flash → update
notices → `telegram-to-drive` → `quick-capture` + weather/ice in briefing → healthchecks.io →
reboot tested, automatic security reboots at 04:30 → this README.

**3–4 Nov 2026 — Windows PC + iPhone**
VPS API server (`:8642`, Tailscale only) for an iPhone Siri shortcut → shortcut v1 (blocking) too slow
for tool-heavy questions → v2 polling via `/v1/runs` (built by hand, If step not matching yet) → signed
shortcut file prepared, waiting for the Mac → `ssh pc` (OpenSSH Server, VPS-only firewall rule) →
PC Hermes updated v0.21.6 → v0.22.7 → PC's 11 skills moved into this repo + own deploy key + 15-min
Scheduled Task sync → PC on shared Honcho (verified) → PC settings aligned (timezone, memory limits,
DeepSeek sub-agents) → PC Telegram bot disabled (only the VPS bot remains).
