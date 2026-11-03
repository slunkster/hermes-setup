# Sync Hermes skills with GitHub on Windows (Scheduled Task "HermesSkillsSync", every 15 min).
$ErrorActionPreference = 'Continue'
Set-Location (Split-Path $PSScriptRoot -Parent)
git add -A
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) { git commit -q -m "sync from $env:COMPUTERNAME $(Get-Date -Format 'yyyy-MM-dd HH:mm')" }
git pull -q --rebase --autostash origin main
git push -q origin main 2>$null
