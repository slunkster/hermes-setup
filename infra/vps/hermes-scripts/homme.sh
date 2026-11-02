#!/bin/bash
# Daily briefing data for the 08:00 cron job (skill homme). Read-only.
P=$(ls -td ~/.hermes/installs/*/environments/*/venv | head -1)/bin/python
exec "$P" ~/Hermes/paevaulevaade/collect_vps.py "$@"
