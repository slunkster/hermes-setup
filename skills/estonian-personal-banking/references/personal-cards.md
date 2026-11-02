# Estonian personal (eraklient) banking — source map, age rules, pitfalls

Depth companion to SKILL.md; same method (fetch live → record fees → compare on a profile → cite + as-of date). Verified 2026-09 — re-fetch before quoting, prices move several times a year.

## Screen by AGE first
Young-client pricing differs per bank AND per product (account vs card vs package), so read the exact wording and cutoff:

- SEB — Noortepakett applies automatically ages 0–25 (k.a); "free daily banking until the 26th birthday" includes accounts, unlimited EU payments, 1 debit card (ISIC option), credit cards, free card delivery, Baltic securities. /eraklient/igapaevapangandus/paketid/seb-noortepakett
- LHV — debit-card fee (1 €/mo) applies only ages 26–65 → free under 26; account + SEPA payments free at any age. /et/era-deebetkaart, /et/hinnakiri
- Swedbank — Põhipakett 1 €/mo, free ≤25 (k.a); includes debit card + unlimited payments. Standalone Deebetkaart Pluss: free ≤19, 0,32 €/mo ages 20–25.
- Coop — Kasulik (1% Coop-store cashback) free ≤26 (k.a), else 1,49 €/mo; Lihtne always free (virtual card). cooppank.ee/paketid
- Luminor — Debit package free ≤21, else 2,50 €/mo; separate "Luminor Bloom" (any age): free digital card, physical 2 €/mo, 3% Rimi cashback ≤30 €/mo. bloom.luminor.ee
- Citadele — C smart free ages 7–21 (its card fee doc: 1,99 €/mo after); C lite free virtual card. /et/private/c-cards/youth/
- Bigbank — no age tiers: card + account free, 2% interest on balance, ATM ≤2000 €/mo free worldwide. Price list lives only at /dokumendid/?main=549&sec&doc=31516
- Revolut — Standard free; Plus 3,99 / Premium 10,99 / Metal 17,99 €/mo; promo windows exist (e.g. 3 months Premium free). Fetch via web_extract.
- Wise — card 7 € one-time; ATM free ≤250 €/mo then 2,69%; FX from 0,2%.
- Exclude from card comparisons: Inbank and Holm (loans/deposits only, no everyday consumer account+card).

## Record per bank (comparison axes)
1. Monthly fee at the target age + what it includes (account, unlimited payments, card count, delivery)
2. FX markup on card purchases (LHV/Bigbank/Swedbank/Coop 1%; SEB 1,5%; Luminor 2%)
3. Free ATM withdrawals + overflow: own ≤2000 €/mo (LHV), own ≤750 (Luminor), any ≤1000 (Citadele), own ≤600 then 0,3% (SEB), worldwide ≤2000 (Bigbank); other banks' ATMs: 1 € flat (LHV) vs 1 € + 2,5% (SEB)
4. Bundled cards, ISIC student option, credit card + insurances, card-delivery fees
5. Cashback / interest: Coop 1% (stores), Bloom 3% (Rimi), Bigbank 2% (balance), Coop Piirideta 1%
6. Promo deadlines quoted with their validity end — never present as permanent

## Fetch pitfalls
- .ee bank pages often defeat headless extractors → use scripts/fetch_pages.py (browser-UA curl -L + tag strip; saves PDFs raw, read_file extracts PDF text).
- 308 redirect: cooppank.ee/paketid (no /et/ variant; base URL 308s) — needs curl -L. Coop erakliendi PDF: res30f.cooppank.ee/.../hinnakiri_eraklient_0101.pdf
- Swedbank private: /private/home/more/pricesrates?language=EST, /private/cards/cards/debit, /private/d2d/accounts/pricingAgreement (server-rendered — curl works).
- Bigbank price list is JS-rendered: curl returns a shell — read it with the browser (innerText); the /hinnakiri* URLs 404.
- Luminor PDFs: luminor.ee/s3fs-public/documents/pricelist_*_private_et-ee.pdf; stripped table columns jumble — cross-check cells against the product page.
- Citadele: per-card pages /et/private/c-cards/<card>/; fee info docs under /storage/app/media/files/pdf/.
- When a price list and a marketing page disagree, trust the price list, then read the footnotes (e.g. "Igapäevane pakett 0,32 €" applies to 65+, not to youth).
- Search snippets locate URLs; re-read every number from the fetched page before quoting it.
