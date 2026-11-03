---
name: car-buying-research
description: "Use when buying a car: shortlist auto24 used-car ads."
---

# Car buying research

For finding and comparing cars to buy (mainly used, Estonian market). The user is
in Estonia (Setomaa), replies in Estonian, and asks blunt cost/risk questions.

## Procedure

1. **Model advice first, briefly.** Clarify new vs used only if it changes the
   answer (under ~20 k € with modern equipment = used). Give 4–6 candidate models
   with the year ranges where the wanted equipment is actually present (e.g. VAG
   digital cluster was optional before ~2020). Then ask only for missing hard filters:
   fuel, gearbox, max mileage, body type.
2. **Search live listings on auto24.ee** with URL filters, including the site's own
   equipment filters (codes and URL in `references/auto24.md`). auto24 is behind
   Cloudflare: attach to the user's real Brave via `BU_CDP_WS` from the start (see
   browser-harness `references/windows-cdp-setup.md`); the headless fallback is
   blocked and invisible to the user.
3. **Collect all result pages** (100 per page) into a JSON file, then drop
   SUVs/crossovers by model name when the user asked for a wagon — auto24's
   "universaal" body filter includes them.
4. **Open every remaining ad's detail page** (~0.8 s/page, ~110 ads in under 10 min,
   save to JSON every 10) and parse: price (take min of Hind/Soodushind), first
   registration, mileage, annual tax + registration fee, braked-trailer kg, and
   equipment keywords. Recipe in `references/auto24.md`.
5. **Shortlist 5–8 cars** with a one-line reason each, plus a short "skip" list
   (expensive tax, reserved, suspiciously cheap). Export the full matching set to
   CSV (`;` separator, utf-8-sig so Excel opens it) in `~/Documents/`, and give the path.

## Rules

- Seller-ticked equipment is unreliable: say which candidates need the digital
  cluster/ACC verified from photos (pre-facelift models where it was optional).
- Always show annual car tax (mootorsõidukimaks) and registration fee from the ad's
  auto24 calculator — they differ 50 € vs 300 €/yr between candidates and matter to
  this user.
- Show towing capacity when a hitch is requested; flag hybrids with low limits.
- Match tow-hitch on real terms only (`veokonks|haakekonks|haagisekonks|kärukonks|haakeseade`);
  bare `konks` false-matches "kaubakinnituse konksud" (bag hooks) in the boot.
- Plain text output (CLI, no markdown), Estonian, links as full URLs.
- Offer a closer look at a specific ad (photos, history report) at the end.
