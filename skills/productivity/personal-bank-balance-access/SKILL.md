---
name: personal-bank-balance-access
description: Use when user wants own bank balance in a widget/script.
---

# Personal bank balance access

User: Estonian, iPhone only (no Android), Coop Pank customer; answer in Estonian. Goal was a home-screen balance widget. Routes to PSD2 aggregators (Enable Banking) over scraping or reverse engineering.

## Decision order (recommend in this order)
1. **Ready-made app with bank sync** (e.g. MoneyCoach: iPhone widgets + GoCardless sync, read-only; Buxfer; Synci -> YNAB/Actual/Sheets). Zero build. Plans/pricing/regions vary - tell the user to verify.
2. **Own PSD2 client via Enable Banking** (free restricted production mode for own accounts, non-commercial). Steps below.
3. **iPhone Shortcuts: screenshot + Extract Text from Image + regex**, result to iCloud file read by a Scriptable widget. Manual trigger (Back Tap/Action Button) is most reliable; a "When app is opened" automation needs a wait for login and a sanity check that the parsed value is a number.
4. Not recommended: reverse engineering the bank app / accessibility scraping. Explain why (pinning, device-bound biometrics, Smart-ID challenge cannot be replayed so 2FA stays, full-access tokens, ToS, breaks on updates) and do NOT give pinning-bypass or emulator-hiding steps; point back to PSD2.

Platform facts to state accurately: iOS cannot read other apps' notifications or screen in the background; Android-only tricks (Tasker notification listener, Accessibility) are not options for an iPhone user. Bank push notifications often carry amounts but not balance.

## Enable Banking flow (verified against the live API)
Template: `templates/eb_client.py` (JWT RS256 client). Install `pyjwt cryptography requests` into the Hermes python.
1. User signs in at enablebanking.com (email magic link), Control Panel -> API applications -> register app with **Environment = Production** (Sandbox returns fake data), keeps generated key; browser downloads `<APP_ID>.pem` to Downloads.
2. Activate: "Activate by linking accounts" (restricted mode, only linked accounts readable). Check `GET /application` -> `"active": true`, `environment: PRODUCTION`. Activation does NOT authorise API access; step 4 is still needed.
3. `GET /aspsps?country=EE` to get the exact bank name and `maximum_consent_validity` (Coop Pank personal: REDIRECT, 180 days; `psu-ip-address` listed as required header).
4. `POST /auth` with `access.valid_until`, `aspsp{name,country}`, `state`, `redirect_url` (must exactly match one registered on the app), `psu_type: personal` -> returns a `tilisy.enablebanking.com/ais/start?...` URL. User opens it and confirms with Smart-ID/Mobile-ID.
5. User copies the full address from the redirect (`?code=...`); the code is single-use and short-lived, so ask for it immediately. Then `POST /sessions {code}` -> account uids; then `GET /accounts/{uid}/balances`. Both VERIFIED live: `POST /sessions` returns `session_id`, `accounts[]` (uid, account_id.iban, currency) and `access.valid_until`; balances come as `balances[]` with `balance_type` (CLBD = closing booked) and `balance_amount.amount` string. The `psu-ip-address` header was NOT needed for these calls. Check the `state` in the pasted callback URL against the one you sent before exchanging; the redirect host may differ from the registered URL (e.g. localhost port) - the code still works. Store session.json next to the client and a `get_balance.py` that caches `balance.json` (amount, fetched_at, consent_valid_until).
6. Re-run steps 4-5 before consent expires; banks cap unattended balance polls (~4/day), so cache the last value + timestamp for the widget.

## Widget hosting (Cloudflare Worker + Scriptable) - built and verified
Worker (`~/.enablebanking/worker/`): signs RS256 JWT with WebCrypto (key in secret `EB_PRIVATE_KEY`, token in `WIDGET_TOKEN`), caches balance in KV `BAL` (cron 4x/day, no stale on-demand fetch), serves `/balance?t=` (cache), `/refresh?t=` (user-present bank call), `/widget.js?t=` (widget source with BASE/TOKEN injected) and public `/logo/{light,dark}.png`. Scriptable loader on the phone just fetches `/widget.js` and runs it via AsyncFunction, caching the source for offline; widget edits need only `wrangler deploy`, no re-paste on the phone. Starting files: `templates/worker.js`, `templates/wrangler.toml`, `templates/coop_widget.js` (design + refresh limits: `references/widget-design-and-refresh.md`).
- wrangler: `wrangler login` runs as background process (opens browser); first `wrangler deploy` may need a workers.dev subdomain - the dashboard `/workers/onboarding` URL can 404; deploying again (or in a pty) worked and the account already had a subdomain. Secrets: `cat key.pem | npx wrangler secret put NAME` (never print them).
- New workers.dev hostnames give TLS errors (curl 000 / SEC_E_ILLEGAL_MESSAGE) for ~1-2 min after first deploy - retry.
- Scriptable cannot use real Liquid Glass (SwiftUI only): fake it with white-gradient translucent stacks + 1px border; say so. Use only fonts known to exist (boldRoundedSystemFont etc.). Smoke-test widget code in Node with Scriptable stubs per widgetFamily (small/medium/large/extraLarge/accessory*).
- Design: the user rejected the card-art background and wanted the real bank logo top-left on a plain light/dark-adaptive background - see the reference before designing; do not start with decorative backgrounds.

## Refresh model (built and tested)
- PSD2 lets the bank cap unattended balance reads (~4/day). Cron (06/10/14/18 UTC, ~08-21 Estonia) calls without PSU headers. `/refresh` calls with `psu-ip-address` (CF-Connecting-IP) + `psu-user-agent`; tested OK against Coop Pank (HTTP 200). `/balance` stays cache-only: an on-demand stale fetch would silently exceed the cap.
- 20s cooldown in KV; HTTP 429 -> 'rate_limited' without flagging consent expired. KV reads can be stale ~60s after a write.
- Widget: `w.url = URLScheme.forRunningScript()` so a tap runs the script in-app, which calls `/refresh`. Stale-warning threshold 14h (night gap is 12h).
- Unverified: whether the bank really exempts PSU-present calls from its cap. Confirmed: the in-app/tap run refreshes the Worker data but does not redraw the home-screen widget (see references). Return the fresh record straight from `/refresh` instead of re-reading KV.
- Cost, risk checklist and native SwiftUI/AppIntent options (free Apple ID 7-day signing, AltStore): `references/risk-cost-and-native-options.md`.
- Look: plain light/dark background + real logo from enablebanking.com/brands/EE/Coop%20Pank/ (dark variant = black pixels recoloured white) replaced the card-style Pillow backgrounds.

## Native iOS app (built without compiling; user later reported it works on iOS 27 + Xcode 27 + macOS 27)
`~/.enablebanking/ios/CoopBalance/` (XcodeGen `project.yml`; App + Widget extension + Shared). Design rules: widget tap = `Button(intent: RefreshIntent())` defined only in the widget target (runs in the extension, no app launch); intent calls Worker `/refresh`, saves into the extension's own `UserDefaults.standard` (no App Group, so free Apple ID works) via `BalanceData.merged` (fresher `fetched_at` wins, because `/balance` KV can lag ~1 min), then `WidgetCenter.reloadAllTimelines()`. Look: `widgetRenderingMode == .fullColor` -> Coop blue `containerBackground` + white text/logo; `.accented` (Clear/Tinted = Liquid Glass) -> `Color.clear` background, system draws glass, logo uses `widgetAccentedRenderingMode(.monochrome)`, amount `widgetAccentable()`. Token goes in header `x-widget-token` via generated `Shared/Config.swift` (gen_config.py; gitignored). Verified only: tree-sitter syntax parse of every .swift file (`pip install tree-sitter tree-sitter-swift`), Apple's WidgetKit Liquid Glass doc (github.com/artemnovichkov/xcode-27-system-prompts). Shared types used by both targets (Color extensions etc.) must live in Shared/, not Widget/. Not verified: type-checking, iOS 27 runtime behaviour, AltStore on iOS 27 (July beta broke SideStore/AltStore for some; AltStore announced Remote AltServer on 2026-09-14).

## Pitfalls
- Handle the private key safely: copy it to `~/.enablebanking/` next to the client, never print or open it, tell the user not to share it, recommend deleting the Downloads copy.
- Windows: Hermes terminal is git-bash but the Hermes python is a native exe - pass `C:/Users/...` paths to it, not `/c/...` or `$HOME/...`, or it resolves to a bogus `C:\c\...` path.
- Redirect URL is fixed at app registration. If it points at a third-party site, the code lands there; suggest adding `https://localhost/callback` as redirect so the code stays with the user, and warn that uploading the .pem to any third-party service hands them the key.
- Read the app's `name/description/redirect_urls` from `GET /application` before assuming what the user set up.
- Docs pages: `web_extract` may lack a backend; fetching the page with curl and stripping tags works for Enable Banking docs.
- Hold back unverified claims about aggregator availability/pricing: say it is unconfirmed.
- User works in Estonian but sometimes writes English; reply in the language of the latest message when it clearly switches, otherwise Estonian. Keep answers short and list limits honestly (what is unverified); the user repeatedly asked for forced/instant refresh, so state iOS limits up front instead of promising it.
- Before telling the user an action happened (cron, refresh, consent), verify with a curl to the Worker `/balance` and quote `fetched_at`; the user checks widget times against it.
- Enable Banking's app form may ask for Privacy and Terms URLs; for personal use leave empty, else point both at a public one-paragraph Google Doc (Anyone with link -> Viewer) stating personal, read-only, non-commercial use. The Google token can be expired (`invalid_grant`): then give the user the text to paste into docs.new instead of re-running OAuth.
- `write_file` refuses to overwrite a file that was modified outside it or only read with offset/limit; read the whole file in ONE read_file call, or write the new version to a new filename and `mv -f` it in the terminal. Do not retry the same write.
- Node on Windows cannot read bash `$TMPDIR` paths; run `node --check` on files inside the project directory.
- When the user says "statement" or similar vague wording, ask whether they mean balance or transaction list before building.
