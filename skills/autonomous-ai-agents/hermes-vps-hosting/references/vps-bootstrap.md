# VPS bootstrap recipe (Mac → fresh Ubuntu VPS → Hermes)

## 1. SSH key from the Mac

- Check first: `ls ~/.ssh/*.pub`. None → user runs `ssh-keygen -t ed25519 -C "<name>@mac"` themselves (passphrase recommended; the agent cannot type it).
- Provider form has a key field → `pbcopy < ~/.ssh/id_ed25519.pub` and paste.
- No key field (provider emails/shows a root password) → user runs `ssh-copy-id -i ~/.ssh/id_ed25519.pub root@<ip>`. After a rebuild on the same IP, clear the stale host key first: `ssh-keygen -R <ip>`.
- Passphrase-protected key: the agent's BatchMode ssh fails until the key is in the agent → user runs once `ssh-add --apple-use-keychain ~/.ssh/id_ed25519`. The agent's terminal shares the launchd `SSH_AUTH_SOCK`, so it works for the agent too.
- Write `~/.ssh/config` (chmod 600):
  ```
  Host *
    AddKeysToAgent yes
    UseKeychain yes
    IdentityFile ~/.ssh/id_ed25519
  Host vps
    HostName <ip>
    User <user>
    ServerAliveInterval 30
  ```
- Diagnose with `ssh -v -o BatchMode=yes root@<ip> true 2>&1 | grep -iE 'offering|accepts|denied'`:
  - "Offering public key" then denied → key not in the server's authorized_keys (re-run ssh-copy-id).
  - Interactive ssh asks for the *key passphrase* → server accepted the key; only the agent unlock is missing.
- Always test from the agent with `ssh -o BatchMode=yes -o ConnectTimeout=10 …` so it never hangs on a prompt.

## 2. Harden (as root, then as the new user)

```
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq && apt-get -y -qq upgrade && apt-get -y -qq install ufw fail2ban unattended-upgrades git curl
adduser --disabled-password --gecos "" <user>; usermod -aG sudo <user>
echo "<user> ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-<user>; chmod 440 /etc/sudoers.d/90-<user>; visudo -c
install -d -m 700 -o <user> -g <user> /home/<user>/.ssh
install -m 600 -o <user> -g <user> /root/.ssh/authorized_keys /home/<user>/.ssh/authorized_keys
```
Verify `ssh <user>@<ip> 'sudo -n true'` works, THEN:
```
printf "PasswordAuthentication no\nKbdInteractiveAuthentication no\nPermitRootLogin no\nPubkeyAuthentication yes\n" | sudo tee /etc/ssh/sshd_config.d/00-hardening.conf
sudo sshd -t && sudo systemctl reload ssh
sudo sshd -T | grep -E '^(passwordauthentication|permitrootlogin)'
sudo ufw default deny incoming; sudo ufw default allow outgoing; sudo ufw allow OpenSSH; sudo ufw --force enable
sudo systemctl enable --now fail2ban unattended-upgrades
```
- Name the drop-in `00-…`: sshd uses the FIRST value it reads, and cloud images ship `50-cloud-init.conf` with `PasswordAuthentication yes`, which would win over a later file. Confirm with `sshd -T`, not by reading files.
- Negative test: root login and password-only login must both return `Permission denied (publickey)`.
- Then switch the Mac's `Host vps` alias to `User <user>`.

## 3. Credentials and config without the wizard

- Inspect what the Mac uses without revealing values: `hermes auth list`, and `awk` over `.env` printing only name + length. An `ANTHROPIC_TOKEN` (oauth, long-lived setup-token) copies to another host fine; an empty `ANTHROPIC_API_KEY=` line is not a credential.
- Copy selected vars, never echoing them:
  ```
  grep -E '^(ANTHROPIC_TOKEN|DEEPSEEK_API_KEY|DEEPSEEK_BASE_URL|OPENAI_API_KEY|TELEGRAM_BOT_TOKEN|TELEGRAM_ALLOWED_USERS|TELEGRAM_HOME_CHANNEL)=' ~/.hermes/.env \
   | ssh vps 'f=~/.hermes/.env; touch $f; chmod 600 $f; cp $f $f.bak; t=$(mktemp); cat >$t; for k in $(cut -d= -f1 $t); do sed -i "/^$k=/d" $f; done; cat $t >>$f; rm $t'
  ```
  Ask the user before copying keys (clarify).
- Mirror the Mac's non-path settings with `hermes config set` (model.provider/default, auxiliary.*, tts/stt, web.backend, image_gen.*). Don't copy the whole Mac config.yaml — it contains Mac paths (terminal.cwd, skill dirs, computer_use).
