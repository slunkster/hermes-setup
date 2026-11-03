# Widget design and refresh limits

## Design the user asked for (iPhone Scriptable widget)
- Sizes: small, medium, large (+ extraLarge falls back to medium), lock screen accessoryInline/Circular/Rectangular.
- Plain background that follows light/dark (`Color.dynamic`: white / #1c1c1e). No decorative card art, no gradients behind the content. The first iteration with card-coloured art and fake glass panels was rejected.
- Actual bank logo top-left. Source: `https://enablebanking.com/brands/EE/<Bank%20Name>/` (PNG, e.g. 500x87; Coop Pank is blue "coop" + black "| Pank"). Black parts vanish in dark mode: render a dark variant with Pillow (pixels with r+g+b<170 -> white, keep alpha), resize to ~400px wide, serve both from the Worker, pick via `Device.isUsingDarkAppearance()`, cache in the Scriptable documents dir, fall back to text wordmark if the fetch fails. Logo image size = height x ~5.7 (aspect of the cropped asset).
- Big bold rounded amount in Estonian format (`1 234,56 €`, nbsp thousands), muted caption "Kontojääk", footer "Uuendatud HH:MM"; warning colour for: consent expiring within 14 days, data older than 8h, `consent_expired` error, offline (show last cached value).
- Large widget adds a faint tinted panel with rows: updated, access valid until, status.
- Real Liquid Glass is impossible in Scriptable (SwiftUI only) and a truly transparent widget is impossible too (needs wallpaper-crop screenshot hack or a native Xcode widget); say so up front.
- Scriptable gotchas: only use fonts that exist (`boldRoundedSystemFont`, `mediumSystemFont`, `semiboldSystemFont`, `regularSystemFont`, `lightSystemFont`); there is no `semiboldRoundedSystemFont`. Stacks only fill width if you add `addSpacer()` in a row. Smoke-test the script in Node with Scriptable stubs per family before handing over; the stub must define `Color.dynamic`, `Device`, `Size`, `addImage`.

## Refresh limits (state these accurately)
- PSD2: banks may cap unattended (user-absent) account-data requests to ~4 per 24h. Worker cron `0 6,10,14,18 * * *` (UTC, ~08-21 Estonia, nothing overnight) uses that budget; do not add more unattended polls (429 risk) and keep `/balance` cache-only.
- User-present refresh (built, HTTP 200 from Coop Pank): `/refresh` sends `psu-ip-address` (CF-Connecting-IP) + `psu-user-agent`. Still unverified: whether the bank excludes these calls from its cap.
- Widget side: `refreshAfterDate` ~30 min only requests a refresh; iOS decides the real cadence. Widget reads the Worker cache, not the bank.
- CONFIRMED limitation: a Scriptable run (in-app or via tap) updates the Worker/cache but does NOT redraw the home-screen widget; only iOS (or remove/re-add the widget) does. Scriptable has no reload API. Do not promise tap-to-refresh of the widget; the real fix is a native WidgetKit widget with an interactive AppIntent button (see `risk-cost-and-native-options.md`).
- Debugging "widget not updating": curl `/balance` and compare `fetched_at` with the widget's "Uuendatud" time. Equal = widget is current; server newer = iOS redraw delay; server old = the refresh never reached the Worker (cooldown, failure alert, or KV staleness: reads can lag a write by ~60s, so re-check after a minute before concluding).
- iOS cannot be triggered by bank push notifications, so event-driven refresh is not available.
- Consent lasts at most 180 days for Coop Pank; Worker var `CONSENT_UNTIL` and session.json must be updated after re-authorising (re-run `POST /auth` -> `POST /sessions`, update `wrangler.toml` var and redeploy).
