#!/bin/sh
# Hermes on the CachyOS/Arch Linux desktop — step 1 (run as yourself, NOT with sudo; it asks for sudo itself).
#   sh ~/Hermes/hermes-skills/infra/linux/setup-linux.sh
set -e

echo '1/4 Tailscale + age...'
sudo pacman -S --needed --noconfirm tailscale age
sudo systemctl enable --now tailscaled
sudo tailscale up --hostname=slunk-linux   # opens/prints a login URL — use the same Google account

echo '2/4 Hermes...'
command -v hermes >/dev/null 2>&1 || [ -x ~/.local/bin/hermes ] || \
  curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash -s -- --skip-setup --skip-computer-use

echo '3/4 Skills sync every 15 min (systemd user timer)...'
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/hermes-skills-sync.service <<'EOF'
[Unit]
Description=Sync Hermes skills repo with GitHub
After=network-online.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'exec /bin/sh %h/Hermes/hermes-skills/scripts/sync.sh >> %h/Hermes/hermes-skills/.sync.log 2>&1'
EOF
cat > ~/.config/systemd/user/hermes-skills-sync.timer <<'EOF'
[Unit]
Description=Sync Hermes skills every 15 min

[Timer]
OnBootSec=2min
OnUnitActiveSec=15min
Persistent=true

[Install]
WantedBy=timers.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now hermes-skills-sync.timer

echo '4/4 Done.'
tailscale ip -4
echo 'Now authorize this PC on the VPS — on the Mac run:'
echo "  ssh vps 'cat >> ~/.ssh/authorized_keys' <<< '$(cat ~/.ssh/id_ed25519.pub)'"
echo 'Then tell Claude "done".'
