# Shared long-term memory across machines: self-hosted Honcho on the VPS

Built-in MEMORY.md/USER.md never sync between installs. One Honcho server on the VPS, used by every Hermes (Mac + VPS), gives one shared memory. Raise the built-in limits too (`memory.memory_char_limit 5000`, `memory.user_char_limit 2500` on each machine) — cheap and removes the "memory full" churn.

## Server (VPS, Docker)

1. `sudo apt-get install -y docker.io docker-compose-v2; sudo usermod -aG docker <user>`; `git clone https://github.com/plastic-labs/honcho ~/honcho`.
2. `docker-compose.yml` from `docker-compose.yml.example`, edited: api port bound to `127.0.0.1:8000` AND `<vps-tailscale-ip>:8000`; remove the db/redis `ports:` blocks and `POSTGRES_HOST_AUTH_METHOD=trust`; drop the `mcp` service. Firewall already default-denies; nothing public.
3. `.env` from `.env.template` (chmod 600): `LLM_OPENAI_API_KEY` (embeddings always need it), `AUTH_USE_AUTH=true`, `AUTH_JWT_SECRET=$(openssl rand -hex 32)`.
4. `docker compose up -d --build` (~3 min first build; run as background process). Health: `curl http://<ts-ip>:8000/health`.
5. Token: `docker compose exec -T api /app/.venv/bin/python scripts/generate_jwt.py --workspace hermes` — output has `Scope:/Expires:/Token:` lines; store only the token in `~/.config/honcho-jwt` (600). Create the workspace once: `POST /v3/workspaces {"id":"hermes"}` with `Authorization: Bearer`.

## Cheap analysis model (DeepSeek Flash)

For every text section `DERIVER_`, `SUMMARY_`, `DREAM_DEDUCTION_`, `DREAM_INDUCTION_`, `DIALECTIC_LEVELS__{minimal,low,medium,high,max}__` append to `.env`:
`<P>_MODEL_CONFIG__TRANSPORT=openai`, `__MODEL=deepseek-flash`, `__OVERRIDES__BASE_URL=https://api.deepseek.com/v1`, `__OVERRIDES__API_KEY_ENV=DEEPSEEK_API_KEY`, `__STRUCTURED_OUTPUT_MODE=json_object` (DeepSeek rejects `json_schema`), plus `DEEPSEEK_API_KEY=`. Embeddings stay on OpenAI (DeepSeek has no embedding model). Also:
- `DERIVER_MODEL_CONFIG__MAX_OUTPUT_TOKENS=6000` — the 2500 default truncates DeepSeek's extraction (`finish_reasons=['length']`) and forces retries.
- `DERIVER_REPRESENTATION_BATCH_MAX_AGE_SECONDS=120` — default 1800 means a fact said on Telegram reaches the other machine only after 30 min.
- `DIALECTIC_LEVELS__low__MAX_TOOL_ITERATIONS=2` — default 5; each iteration is a full LLM round, the dialectic otherwise takes 7–30 s.
Apply with `docker compose up -d --force-recreate api deriver`. Verify: `GET /v3/workspaces/hermes/queue/status` drains, `POST /v3/workspaces/hermes/peers/<peer>/representation` lists observations, `POST …/peers/<peer>/chat {"query":…,"reasoning_level":"low"}` answers.

## Clients (each machine)

1. `hermes plugins install honcho`.
2. `hermes memory setup honcho </dev/null` — run ONLY to make PM prepare the `honcho-ai` dependency; it then fails at the cloud OAuth prompt and leaves honcho.json untouched. Without this step tools fail with "honcho-ai is required".
3. Write `~/.hermes/honcho.json` (600): `{baseUrl: "http://<vps-ts-ip>:8000", apiKey: <JWT>, workspace: "hermes", peerName: "<user>", hosts: {hermes: {enabled, aiPeer: "hermes", peerName, workspace, recallMode: "hybrid", contextTokens: 1500}}}`; on the gateway host add `pinUserPeer: true` so Telegram IDs map to the same user peer.
4. `hermes config set memory.provider honcho`; the user restarts each gateway (deps load only in a fresh process; `hermes chat -q` runs inside the running gateway).
5. Test across machines: tell the Telegram bot a new fact, wait ~2 min, ask a new Mac session.

## Speed

`honcho_search` (raw message search) answers in ~0.3 s; `honcho_reasoning` (dialectic) takes ~6 s and is less reliable for fresh facts (it may not have derived them yet). Put "prefer honcho_search for factual recall" into each agent's MEMORY.md. The main model (Opus) dominates remaining latency — mention a faster model as an option, don't switch it unasked.

## Pitfalls

- `baseUrl` on localhost/127.0.0.1 makes the plugin skip the API key — with auth on, use the Tailscale IP even on the VPS itself.
- `usermod -aG docker` doesn't reach the running systemd user manager or cron — call docker via `sg docker -c "…"` in scripts.
- Back it up: `sg docker -c "docker compose exec -T database pg_dump -U postgres postgres" | gzip` inside the nightly backup, plus `.env`, compose file, JWT, honcho.json.
- Containers run in UTC, so recalled observations carry UTC timestamps (shown without a zone) — convert before stating a date to the user.
- Cost note for the user: background analysis per message; with DeepSeek Flash roughly €1–2/month at personal volume.
