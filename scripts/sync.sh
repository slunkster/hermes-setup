#!/bin/sh
# Sync Hermes skills with GitHub: commit local changes, rebase on remote, push.
# Runs every 15 min (Mac: launchd ee.siim.hermes-skills-sync, VPS: crontab).
set -e
cd "$(dirname "$0")/.."
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
git add -A
git diff --cached --quiet || git commit -q -m "sync from $(hostname -s) $(date '+%Y-%m-%d %H:%M')"
git pull -q --rebase --autostash origin main
git push -q origin main 2>/dev/null || true
