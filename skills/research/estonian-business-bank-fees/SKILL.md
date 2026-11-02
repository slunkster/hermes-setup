---
name: estonian-business-bank-fees
description: "Use when comparing Estonian bank fees for an OÜ."
version: 1.0.0
metadata:
  hermes:
    tags: [estonia, banking, fees, business]
    category: research
---

# Estonian business bank fee comparison

Goal: find the cheapest bank for an Estonian company (OÜ). Prices change often — always fetch live pages, never answer from memory. Answer in Estonian unless asked otherwise.

## Where the price lists are (verified 2026-09)

- LHV — https://www.lhv.ee/et/hinnakiri (account + SEPA payments free; business debit card 2 €/mo, virtual 0 €; card page /et/ari-deebetkaart; startup offers /et/alustav-ettevote)
- Coop Pank — https://www.cooppank.ee/ariklient/igapaevapangandus/arikliendi-paketid + PDF hinnakiri_ariklient_EST.pdf on res30f.cooppank.ee (Äripakett free: EE+EU payments, 1 debit card, banklink acceptance, cash deposit at Coop stores)
- SEB — packages https://www.seb.ee/ariklient/igapaevapangandus/paketid; full price list https://www.seb.ee/hinnakiri (JS-heavy; extract via search snippets or curl)
- Swedbank — https://www.swedbank.ee/business/d2d/start/tools/pricesrates (server-rendered; browser-UA curl + strip tags works)
- Luminor — PDFs at luminor.ee/s3fs-public/documents/ (pricelist_*_business_*.pdf); packages 3/7/13/29 € for 10/25/50/150 payments
- Citadele — https://www.citadele.ee/et/business/plans + PDF mainb_*.pdf under citadele.ee/storage/app/pdf/public/ee/ (Start 2 €/mo unlimited SEPA; promos for companies <12 months old)
- Bigbank — https://www.bigbank.ee/arikliendi-arvelduskonto (business account free, 2% interest on balance)
- Wise — https://wise.com/ee/pricing/business; Revolut Business — revolut.com/en-EE/business/business-account-plans
- TBB pank is in liquidation — do not include in comparisons.

## Pitfalls

- Swedbank: the 20 € "Arvelduskonto kuuhooldustasu" belongs ONLY to the "Teenused krediidiasutustele, -andjatele, makse- ja e-raha asutustele" section — never quote it for an ordinary OÜ. Ordinary business: no general monthly account fee; first 1000 euro payments/month free, then 0.16/0.38 €; business debit card 2 €/mo.
- LHV: standard business debit card — physical 2 €/mo, virtual 0 €. The "(sh virtuaalkaardil)" wording on the marketing page applies to gold/premium cards, not the standard one.
- Coop: the 1 €/mo account maintenance applies only without the (free) Äripakett; package clients are exempt.
- Foreign owners/beneficials trigger much higher fees (Coop 200–500 € opening, 20–1000 €/mo due-diligence fees; SEB 500 € document fee) — check the footnotes before quoting.
- Promos are dated: SEB free 1st year for new business clients; Citadele free package months for companies <12 months old (until 31.12.2026) — always state the deadline and the price list's "kehtiv alates" date.

## Method

1. Fetch each bank's price page/PDF live (browser-UA curl often beats headless extractors on .ee bank sites; PDFs may need a retry via a different extractor).
2. Per bank record: monthly fee, free/included payments, card fee, cash fees, promos + validity dates.
3. Compare on a stated usage profile (e.g. 1 account, 1 card, <1000 payments/mo) and show monthly + yearly cost; note where a package beats pay-per-payment (Luminor pays off from ~3 payments/mo).
4. Cite every number to the bank's page (grounded-citations ledger), and state the as-of date.
