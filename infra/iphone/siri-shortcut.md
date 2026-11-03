# "Ask Hermes" – Siri Shortcut (iPhone → VPS Hermes)

Base URL: `http://<VPS_TAILSCALE_IP>:8642` (Tailscale only; the API server runs inside hermes-gateway on the VPS).
Key: `~/Hermes/iphone/api-key.txt` on the VPS.

## Prerequisite (once)
1. Install **Tailscale** from the App Store, sign in with siim.alve@ (same account as the Mac/PC).
2. Tailscale → Settings → **VPN On Demand** → On.

## Why the runs version
`/v1/chat/completions` keeps one request open until Hermes is done. Questions that need tools
(calendar, mail, web) take 30–65 s → Siri gives up ("Something went wrong").
`/v1/runs` starts the job instantly and the shortcut checks every 3 s, so no single request is long.

## Build the shortcut (v2, polling)
1. **Dictate Text** (Stop listening: After Pause).
2. **Text**: `Answer briefly for reading aloud, in the language of the question, no markdown. Question: ` + *Dictated Text*
3. **Get Contents of URL**
   - URL: `http://<VPS_TAILSCALE_IP>:8642/v1/runs`
   - Method **POST**; Headers `Authorization` = `Bearer <key>`, `Content-Type` = `application/json`
   - Request Body **JSON**: `model` = `hermes-agent`, `input` = *Text* (from step 2)
4. **Get Dictionary Value** `run_id` from *Contents of URL* → **Set Variable** `RunID`
5. **Speak Text** `Okay, thinking.` (optional; tells you it started)
6. **Repeat 30 times**:
   1. **Wait** 3 seconds
   2. **Get Contents of URL** `http://<VPS_TAILSCALE_IP>:8642/v1/runs/` + *RunID* — Method **GET**, same `Authorization` header
   3. **Get Dictionary Value** `status` → **If** *Dictionary Value* **is** `completed`:
      - **Get Dictionary Value** `output` from *Contents of URL* (the one inside the loop)
      - **Speak Text** *Dictionary Value*
      - **Stop This Shortcut**
   4. **End If**
7. **End Repeat** → **Speak Text** `Hermes is still working. Ask again in a minute.`

## Measured response times (03.11.2026, Opus)
- simple answer: 8–15 s; weather: 10–15 s; "schedule tomorrow" (calendar tools): ~34 s.
- Faster model does not help much: Sonnet 34 s, Haiku 65 s (more tool calls). Time is in tools, not the model.

## Notes
- Each run is a fresh session (no chat history).
- Rotate the key: new `API_SERVER_KEY` on the VPS → `systemctl --user restart hermes-gateway` → update both headers in the shortcut.
- Test from the VPS: `curl -s http://<VPS_TAILSCALE_IP>:8642/health`
