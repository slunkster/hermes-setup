#!/bin/bash
# External dead-man switch for healthchecks.io. Runs every 10 min from crontab.
# Pings success only when the Hermes Telegram gateway is running; otherwise reports failure.
# If the whole VPS is down, no ping arrives and healthchecks.io alerts on its own.
URL=$(cat ~/.config/hc-ping-url 2>/dev/null) || exit 0
[ -n "$URL" ] || exit 0
export XDG_RUNTIME_DIR=/run/user/$(id -u)
if systemctl --user is-active -q hermes-gateway; then
  curl -fsS -m 10 --retry 3 -o /dev/null "$URL"
else
  curl -fsS -m 10 --retry 3 -o /dev/null --data-raw "hermes-gateway not active" "$URL/fail"
fi
