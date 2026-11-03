# Risks, cost and native-app options

## Cost
- Cloudflare Workers Free plan (about 100k requests/day, KV 100k reads / 1k writes per day, cron free) is far above this use (a few hundred reads, 4 writes/day). Hitting limits makes errors, not charges; a bill needs a manual upgrade to Workers Paid. Limits can change: tell the user to check Billing shows Free with no payment method. Enable Banking restricted mode is free.

## Risk review to give when the user asks "can this cause problems"
- Key hygiene: private key may linger in Downloads, `~/.enablebanking/` and Cloudflare secrets; delete the Downloads copy. If the app was previously registered for a third-party service (e.g. the app name/description/redirect names one), assume that service may hold the key; consider a fresh Enable Banking app.
- Widget token travels in the URL query string (lands in Cloudflare logs) and is shown in chat/loader; prefer sending it in the `x-widget-token` header and rotate it (`wrangler secret put WIDGET_TOKEN`, update the phone loader) if the transcript is shared. It grants read-only balance access.
- The Scriptable loader executes whatever code the Worker serves; a compromised Cloudflare account or token means code runs on the phone. Pasting the widget code locally removes that at the cost of auto-update.
- `wrangler login` leaves a broad OAuth token on the PC; suggest `wrangler logout` when done.
- Consent expires (Coop Pank max 180 days): widget dies; re-auth needs `POST /auth` + `POST /sessions`, update `EB_ACCOUNT_UID`/`CONSENT_UNTIL` (uid may change per session) and redeploy; not doable from the phone.
- The balance returned is `CLBD` (booked closing); it may differ from the app's available balance (pending card transactions). Have the user compare with the app once.
- Only the linked account is covered. Logo is the bank's trademark: fine for personal use, do not share.

## Native iOS app (user has a Mac) - proposed, not built
- Interactive WidgetKit widget (iOS 17+): a `Button(intent:)` running an `AppIntent` can call `/refresh` in the background without opening any app and then `WidgetCenter.reloadTimelines`; this is the only reliable way to force a redraw. iOS 26 adds system Liquid Glass / `glassEffect`; API details unchecked.
- Design it so the widget extension fetches the Worker itself (no App Groups) so it also works with a free personal team. Token in Keychain/config, never in source.
- The Hermes host is Windows: Swift can be written there but not compiled or tested; expect a compile-fix round with the user pasting Xcode errors, and say so before promising.
- Distribution without the 99 EUR/yr program: free Apple ID via Xcode = signature expires after 7 days (re-run from Xcode), ~3 active apps and ~10 new App IDs/week (app + widget extension = 2 IDs); AltStore/SideStore can auto re-sign weekly while AltServer runs on a Mac/PC on the same wifi. TestFlight, App Store and EU alternative marketplaces all still require the paid membership; a PWA cannot provide a home-screen widget. Details are from memory: tell the user to verify.
- Questions to ask before starting: iOS version, paid vs free developer account, background style (plain adaptive vs card-style vs clear glass).
