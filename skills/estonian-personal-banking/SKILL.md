---
name: estonian-personal-banking
description: "Use when comparing Estonian personal bank cards/accounts."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [estonia, banking, personal, cards, fees]
    category: research
---

# Estonian personal banking comparison (eraklient)

Goal: choose or compare a bank card / daily-banking offer for a private client (eraklient) in Estonia, including youth/student tiers. Prices change several times a year — always fetch live pages, never quote from memory. Answer in Estonian unless asked otherwise. Cite every number to the bank's page (grounded-citations ledger) and state the as-of date.

Business (OÜ) fee comparisons live in the separate user-owned skill `estonian-business-bank-fees` — never mix its business price lists into a personal answer.

## When to Use

- The user asks which bank card/account to take, or to compare Estonian personal banking offers (fees, cashback, FX, ATM limits).
- Youth/student tiers matter (age-based pricing, ISIC, student discounts).
- Any personal-banking numbers will be quoted — this skill governs how they are fetched, verified and cited.
Skip for OÜ/business fee questions — that is `estonian-business-bank-fees` (user-owned).

## Screen by AGE first

Young-client tiers differ per bank AND per product (account vs card vs package), and the wording matters: "alla 26-aastasele" = under 26; "kuni 25-aastastele (k.a)" = through age 25. Check the exact cutoff and what it applies to (card fee vs account vs whole package). Per-bank cutoffs and anchor numbers: `references/personal-cards.md`.

## Where the personal price lists are (verified 2026-09)

- LHV — /et/era-deebetkaart + /et/hinnakiri (debit-card fee 1 €/mo applies only ages 26–65 → free under 26; account + SEPA payments free)
- SEB — /eraklient/igapaevapangandus/paketid (+ /seb-noortepakett for 18–25); full list /hinnakiri
- Swedbank — /private/home/more/pricesrates?language=EST; cards /private/cards/cards/debit; packages /private/d2d/accounts/pricingAgreement
- Coop — cooppank.ee/paketid (base URL 308-redirects — use curl -L, no /et/ variant) + erakliendi PDF on res30f.cooppank.ee
- Bigbank — price list only at /dokumendid/?main=549&sec&doc=31516 (JS-rendered — read with the browser)
- Luminor — pricelist_*_private_et-ee.pdf under luminor.ee/s3fs-public/documents/ + bloom.luminor.ee
- Citadele — /et/private/c-cards/ and per-card pages (/youth/, /c-lite-virtual-card/, ...)
- Revolut — fetch via web_extract; Wise — wise.com/ee/pricing
- Inbank and Holm have no everyday consumer account+card product (loans/deposits only) — exclude from card comparisons. TBB is in liquidation.

## Method

1. Fetch each bank's page/PDF live with `scripts/fetch_pages.py` (browser-UA curl -L + tag strip; saves PDFs raw for read_file). JS-rendered pages (Bigbank documents) still come back as shells — read those in the browser.
2. Per bank record: monthly fee at the target age; what it includes (account, unlimited payments, card count, delivery); FX markup on card purchases; free ATM limits + overflow fee; bundled cards (ISIC student option); credit card + insurances; cashback/interest; promos with validity end.
3. Compare on the user's stated profile and call out which free tiers expire at which birthday (e.g. Luminor/Citadele youth tiers end at 21, SEB/LHV/Swedbank/Coop run to ~26).
4. Deliver: decisive recommendation + per-bank numbers + a "kas tasub maksta?" verdict; cite inline and end with the Sources list. Fintechs (Revolut/Wise) are travel/FX add-ons, not primary salary accounts.

## Pitfalls

- Headless extractors often time out on .ee bank sites — use `scripts/fetch_pages.py` first, the browser second, and keep search snippets only for locating URLs.
- Marketing pages and price lists disagree: trust the price list, then read the footnotes (e.g. a "0,32 € Igapäevane pakett" figure can belong to 65+, not youth).
- Quote the exact age wording per bank — "kuni X (k.a)" includes age X, and the same bank can have different cutoffs for card vs package.
- Promos are dated — always state the deadline (ISIC opening fee, Revolut trial months, savings/cashback campaigns); never present them as permanent rates.
- Reprint-safe figures: re-read every number from the fetched page before quoting it; do not quote from a search snippet.
