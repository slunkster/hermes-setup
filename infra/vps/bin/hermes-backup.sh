#!/bin/bash
# Nightly encrypted backup of the VPS Hermes -> Google Drive "Hermes VPS backups".
# Encrypted with age to the Mac's public key; decrypt on the Mac with
#   age -d -i ~/.config/hermes-backup/age-key.txt FILE.tar.gz.age | tar xz
# Cron: 30 3 * * *  (log: ~/Hermes/backups/backup.log)
set -euo pipefail
FOLDER_ID=<DRIVE_FOLDER_ID>
KEEP=14
PUB=$(cat ~/.config/hermes-backup.age.pub)
P=$(ls -td ~/.hermes/installs/*/environments/*/venv | head -1)/bin/python
G=~/.hermes/skills/productivity/google-workspace/scripts/google_api.py
STAMP=$(date +%Y-%m-%d_%H%M)
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
S=$W/hermes-vps-$STAMP; mkdir -p "$S/hermes"

# Consistent copy of the session database
[ -f ~/.hermes/state.db ] && sqlite3 ~/.hermes/state.db ".backup '$S/hermes/state.db'"
# Hermes state (no code, caches, toolchains or bundled skills)
cd ~/.hermes
for x in config.yaml .env auth.json SOUL.md memories cron sessions mcp-tokens google_token.json google_client_secret.json pairing; do
  [ -e "$x" ] && cp -a "$x" "$S/hermes/"
done
# Workspace (without the 1.6 GB speech model), ssh keys, cron + systemd units
tar -C ~ --exclude='Hermes/whisper-et/model*' --exclude='Hermes/backups' -cf "$S/home.tar" Hermes .ssh .config/systemd/user .config/hermes-backup.age.pub .config/hc-ping-url .config/honcho-jwt bin 2>/dev/null || true
crontab -l > "$S/crontab.txt" 2>/dev/null || true
# Honcho memory (Postgres dump + config)
if [ -d ~/honcho ]; then
  (cd ~/honcho && sg docker -c "docker compose exec -T database pg_dump -U postgres postgres" | gzip > "$S/honcho.sql.gz")
  cp ~/honcho/.env "$S/honcho.env"; cp ~/honcho/docker-compose.yml "$S/honcho-compose.yml"
  cp ~/.config/honcho-jwt ~/.hermes/honcho.json "$S/hermes/" 2>/dev/null || true
fi

OUT=$W/hermes-vps-$STAMP.tar.gz.age
tar -C "$W" -czf - "hermes-vps-$STAMP" | age -r "$PUB" -o "$OUT"
"$P" "$G" drive upload "$OUT" --parent "$FOLDER_ID" >/dev/null
echo "$(date '+%F %T') uploaded $(basename "$OUT") $(du -h "$OUT" | cut -f1)"

# Retention: keep newest $KEEP, move older to Drive trash
"$P" "$G" drive search "'$FOLDER_ID' in parents and trashed = false and name contains 'hermes-vps-'" --raw-query --max 100 \
 | python3 -c "
import sys, json
files = sorted(json.load(sys.stdin), key=lambda f: f['name'], reverse=True)
for f in files[$KEEP:]: print(f['id'])" \
 | while read -r id; do "$P" "$G" drive delete "$id" >/dev/null && echo "trashed old backup $id"; done
