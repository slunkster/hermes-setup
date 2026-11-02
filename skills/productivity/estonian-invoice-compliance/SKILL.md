---
name: estonian-invoice-compliance
description: "Use when an Estonian invoice needs a compliance check."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Estonia, invoices, accounting, e-arve, VAT, arve]
    related_skills: [statutory-law-research]
---

# Estonian invoice compliance (arve nõuded)

## When to Use

- User asks whether an invoice (arve) meets requirements / "nõudeid täitev" / "nõuetekohane".
- Drafting a new invoice or reviewing a draft before sending.
- Questions about e-arve obligations, VAT fields, or invoice register data.

Use for "kas arve vastab nõuetele" checks and for drafting invoices. Cite the current
Raamatupidamise seadus (RPS) / Käibemaksuseadus (KMS) / Võlaõigusseadus (VÕS) text —
never blogs. Fetch texts via the RT JSON API recipe in the `statutory-law-research`
skill, which carries the exact endpoints and commands.

## Required content — RPS § 7 (reform in force since 01.07.2025)

- § 7 lg 2 (any source document): 1) toimumisaeg; 2) majandusliku sisu kirjeldus;
  3) arvnäitajad (kogus, hind, summa).
- § 7 lg 3 (counterparty is an accounting entity, state entity or foreign legal
  person): additionally arve number/identifier and data identifying the parties —
  verify BOTH parties' names + registry codes against ariregister.rik.ee.
- Not required but good practice: maksetähtpäev, viivis, IBAN + SWIFT, contact email.
  Non-VAT seller: note "Ei ole käibemaksukohuslane." (check register to confirm).

## E-invoice (e-arve) — the most common 2025+ gap — RPS § 7¹ + § 7 lg 5

- § 7 lg 5: algdokument MUST be machine-processable (masintöödeldav); exception only
  if the counterparty cannot handle it and building the capability would be
  disproportionately costly. A plain PDF is NOT masintöödeldav (definition § 7 lg 6).
- § 7¹ lg 3: a company wanting to receive only machine-processable invoices registers
  itself in the business register; the register card then shows "E-arvete
  vastuvõtmine: <operator>" (e.g. Billberry).
- § 7¹ lg 7: such a registered receiver MAY DEMAND an e-invoice from the seller;
  a compliant e-invoice is presumed if it follows EN 16931-1; parties may agree
  another standard. Ministry position: default is to send e-arve to registered
  receivers unless agreed otherwise.
- ALWAYS check the buyer's register card for the "E-arvete vastuvõtmine" field —
  it decides whether the seller must be able to send an e-arve.
- Cheap compliant route for tiny firms: RIK e-arveldaja (e-arveldaja.rik.ee) —
  1st year free, then from ~5 EUR+VAT/yr at low volume; board member signs with
  ID-card/Mobile-ID; connected to all Estonian operators. Alt: join any operator.

## If the seller is VAT-registered — KMS § 37

- lg 7 mandatory entries: invoice number+date; seller name/address/VAT number;
  buyer name+address; buyer VAT number where buyer has the tax obligation (reverse
  charge etc.); goods/services description; quantity/volume; supply or payment date
  if determinable and different from invoice date; price excl VAT + any discount;
  taxable amount per VAT rate together with the rates (or exempt amount); VAT amount
  in EUR. lg 8 adds case-specific markers (e.g. "pöördmaksustamine").
- VAT registration threshold: 40 000 EUR per calendar year (KMS § 19 lg 1).
- General VAT rate is 24% (since 01.07.2025, KMS § 15 lg 1) — always re-check, never
  quote from memory.

## Civil-law side notes

- A viivis rate printed on an invoice binds only if agreed; statutory default = the
  § 94 rate + 8%/yr (VÕS § 113 lg 1). Flag this, don't treat as error.
- For company invoices, the bank account should belong to the company itself —
  verify from the bank contract if available (e.g. .asice container: unzip, open PDF).

## Procedure

1. Locate the invoice file (mdfind 'Välk Meedia' style queries work well).
2. Read it: 2-column PDF text layers INTERLEAVE columns — render to PNG first
   (`sips -s format png in.pdf --out out.png`) and inspect visually; never flag field
   errors from raw text extraction alone.
3. Fetch current RPS/KMS/VÕS from RT API (ids are versioned; re-resolve from the
   abbreviation index each time — convenience ids as of 10.2026: RPS 110072025003,
   KMS 130062026129, VÕS 120062026018).
4. Verify both parties at ariregister.rik.ee/est/company/<regkood>: name, address,
   status, "ei ole käibemaksukohuslane", "E-arvete vastuvõtmine" channel.
5. Map invoice fields against the checklist; list missing/questionable items and the
   delivery-channel (e-arve) status; end with the flip cases.
6. Answer in Estonian, verdict first, with § + lg + p citations, then fixes, then
   plain source URLs.

## Pitfalls

- General VAT rate 24% since 01.07.2025; threshold 40 000 EUR since 01.01.2025 —
  re-verify before quoting.
- Register official name ("Osaühing Nordcity Center") vs invoice form ("Nordcity
  Center OÜ") is acceptable when the registry code is present — do not flag.
- "nõudeid täitev arve" = "arve, mis vastab nõuetele" (requirements-compliant).
- PDF/paper is fine only when the counterparty lacks machine-processing capability
  (or the parties agreed otherwise) — with an e-arve-registered buyer it is not.
- Sending e-arve capability and receiving e-arve registration are independent
  register fields; a company may send without being a registered receiver.
