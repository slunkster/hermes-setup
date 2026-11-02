#!/bin/bash
# Daily VPS health check (Hermes cron, --no-agent). Prints NOTHING when all is fine;
# any output is delivered to Telegram as an alert.
P=$(ls -td ~/.hermes/installs/*/environments/*/venv 2>/dev/null | head -1)/bin/python
G=~/.hermes/skills/productivity/google-workspace/scripts/google_api.py
FOLDER_ID=<DRIVE_FOLDER_ID>
problems=()

# 1. Last night's backup exists on Google Drive (newer than 26 h)
latest=$("$P" "$G" drive search "'$FOLDER_ID' in parents and trashed = false and name contains 'hermes-vps-'" --raw-query --max 50 2>/dev/null \
  | python3 -c "import sys,json; f=json.load(sys.stdin); print(max(x['name'] for x in f) if f else '')" 2>/dev/null)
if [ -z "$latest" ]; then
  problems+=("Varukoopia: Google Drive'ist ei leitud ühtegi koopiat (või Drive'i päring ebaõnnestus).")
else
  ts=$(echo "$latest" | sed -E 's/hermes-vps-([0-9-]+)_([0-9]{2})([0-9]{2}).*/\1 \2:\3/')
  age_h=$(( ( $(date +%s) - $(date -d "$ts" +%s) ) / 3600 ))
  [ "$age_h" -gt 26 ] && problems+=("Varukoopia: viimane koopia on ${age_h} h vana ($latest). Vaata ~/Hermes/backups/backup.log.")
fi
tail -n 20 ~/Hermes/backups/backup.log 2>/dev/null | grep -qiE "error|traceback|failed" && \
  problems+=("Varukoopia logis on viga: $(grep -iE 'error|failed' ~/Hermes/backups/backup.log | tail -1 | cut -c1-150)")

# 2. Disk space
use=$(df --output=pcent / | tail -1 | tr -dc 0-9)
[ "$use" -ge 85 ] && problems+=("Ketas on ${use}% täis.")

# 3. Google login still valid (briefing, Gmail, Drive, backups depend on it)
"$P" ~/.hermes/skills/productivity/google-workspace/scripts/setup.py --check 2>&1 | grep -q AUTHENTICATED || \
  problems+=("Google'i sisselogimine ei kehti enam — Gmail/Drive/kalender/varukoopiad ei tööta.")

# 4. Skills sync with GitHub (last successful sync within 2 h)
cd ~/hermes-skills 2>/dev/null && git fetch -q origin 2>/dev/null || problems+=("Skillide sünk: GitHubi ei saa kätte (deploy key?).")
if [ -d ~/hermes-skills/.git ]; then
  last=$(stat -c %Y ~/hermes-skills/.git/FETCH_HEAD 2>/dev/null || echo 0)
  ahead=$(git -C ~/hermes-skills rev-list --count origin/main..main 2>/dev/null || echo 0)
  [ "$ahead" -gt 0 ] && problems+=("Skillide sünk: $ahead commit'i on GitHubi lükkamata.")
fi

# 5. Services
systemctl --user is-active -q hermes-dashboard || problems+=("Hermes dashboard (Windowsi/desktop ühendus) ei tööta.")
curl -sf -m 10 http://<VPS_TAILSCALE_IP>:8000/health >/dev/null || problems+=("Honcho mälu (Docker, ~/honcho) ei vasta — jagatud mälu ei tööta.")
if [ -d ~/honcho ]; then
  down=$(cd ~/honcho && sg docker -c "docker compose ps --services --status running" 2>/dev/null | sort | tr '\n' ' ')
  [ "$down" != "api database deriver redis " ] && problems+=("Honcho konteinerid: töötavad ainult: ${down:-mitte ükski}")
fi

# 6. Hermes updates (info only; never installs)
up=$(bash -lc "hermes update --check" 2>/dev/null | grep -oE "release available: [^ ]+ v[0-9.]+" | sed 's/release available: //')
[ -n "$up" ] && problems+=("Uuendus VPS-il saadaval: $up → ssh vps 'hermes update', siis ssh vps 'systemctl --user restart hermes-gateway'")
mup=$(ssh -o BatchMode=yes -o ConnectTimeout=8 mac 'bash -lc "hermes update --check"' 2>/dev/null | grep -oE "release available: [^ ]+ v[0-9.]+" | sed 's/release available: //')
[ -n "$mup" ] && problems+=("Uuendus Macil saadaval: $mup → Macis 'hermes update', siis 'hermes gateway restart'")

if [ ${#problems[@]} -gt 0 ]; then
  echo "⚠️ VPS-i tervisekontroll ($(date '+%d.%m %H:%M'))"
  for p in "${problems[@]}"; do echo "• $p"; done
fi
exit 0
