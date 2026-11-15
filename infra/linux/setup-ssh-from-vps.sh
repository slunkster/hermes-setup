#!/usr/bin/env bash
# Run once with sudo on the Linux desktop: lets ONLY the VPS (Tailscale <VPS_TAILSCALE_IP>) ssh in
# as siimalve with a key (VPS key ~/.ssh/linux_access, `ssh linux` on the VPS).
# The key itself is in ~/.ssh/authorized_keys with from="<VPS_TAILSCALE_IP>".
set -euo pipefail
VPS_IP=<VPS_TAILSCALE_IP>
USER_NAME=siimalve
cat > /etc/ssh/sshd_config.d/00-hermes-hardening.conf <<CONF
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
AllowUsers ${USER_NAME}@${VPS_IP}
CONF
sshd -t
ufw allow in on tailscale0 from ${VPS_IP} to any port 22 proto tcp comment 'Hermes VPS ssh'
systemctl enable --now sshd
systemctl reload sshd
echo "OK — test on the VPS:  ssh linux hostname"
