# Hermes: let the VPS reach this PC over Tailscale (ssh pc)
# Run in an ADMIN PowerShell:
#   powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\setup-ssh.ps1"

$ErrorActionPreference = 'Stop'
$pub = '<VPS_PC_ACCESS_PUBLIC_KEY>'
$vpsTs = '<VPS_TAILSCALE_IP>'

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) { Write-Host 'Run this in an ADMIN PowerShell (right-click > Run as administrator).' -ForegroundColor Red; exit 1 }

Write-Host '1/5 Installing OpenSSH Server...'
$cap = Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Server*'
if ($cap.State -ne 'Installed') { Add-WindowsCapability -Online -Name $cap.Name | Out-Null }

Write-Host '2/5 Starting sshd (auto-start)...'
Set-Service -Name sshd -StartupType Automatic
Start-Service sshd

Write-Host '3/5 Firewall: SSH only from the VPS over Tailscale...'
Get-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -ErrorAction SilentlyContinue | Disable-NetFirewallRule
Get-NetFirewallRule -Name 'Hermes-VPS-SSH' -ErrorAction SilentlyContinue | Remove-NetFirewallRule
New-NetFirewallRule -Name 'Hermes-VPS-SSH' -DisplayName 'SSH from Hermes VPS (Tailscale)' -Direction Inbound -Protocol TCP -LocalPort 22 -RemoteAddress $vpsTs -Action Allow -Profile Any | Out-Null

Write-Host '4/5 Authorizing the VPS key...'
$line = "from=`"$vpsTs`" $pub"
# Admin accounts read this file (not the user's own authorized_keys)
$adminKeys = 'C:\ProgramData\ssh\administrators_authorized_keys'
if (-not (Test-Path $adminKeys) -or -not (Select-String -Path $adminKeys -SimpleMatch $pub -Quiet)) { Add-Content -Path $adminKeys -Value $line -Encoding ascii }
icacls $adminKeys /inheritance:r /grant 'Administrators:F' /grant 'SYSTEM:F' | Out-Null
# Non-admin fallback
$userSsh = Join-Path $env:USERPROFILE '.ssh'
New-Item -ItemType Directory -Force -Path $userSsh | Out-Null
$userKeys = Join-Path $userSsh 'authorized_keys'
if (-not (Test-Path $userKeys) -or -not (Select-String -Path $userKeys -SimpleMatch $pub -Quiet)) { Add-Content -Path $userKeys -Value $line -Encoding ascii }

Write-Host '5/5 Default SSH shell = PowerShell...'
New-Item -Path 'HKLM:\SOFTWARE\OpenSSH' -Force | Out-Null
New-ItemProperty -Path 'HKLM:\SOFTWARE\OpenSSH' -Name DefaultShell -Value "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -PropertyType String -Force | Out-Null
Restart-Service sshd

Write-Host ''
Write-Host "DONE. Windows username for Hermes: $env:USERNAME" -ForegroundColor Green
Write-Host 'Send that username back to Hermes.'
