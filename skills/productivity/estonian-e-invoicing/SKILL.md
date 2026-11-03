---
name: estonian-e-invoicing
description: "Use when building or sending Estonian e-invoices (e-arve)."
version: 1.0.0
author: Nous Research
license: MIT
platforms: [windows, macos, linux]
metadata:
  hermes:
    tags: [e-invoice, e-arve, estonia, e-arveldaja, rik, evs-923, invoicing, bookkeeping, vat]
    category: productivity
    related_skills: [pdf, personal-bank-balance-access]
---

# Estonian e-invoicing (e-arve)

## When to Use

- The user wants to create or send invoices (arved) in Estonia, wants "e-arve", or asks about an invoice tool for their own company.
- Integrating with e-arveldaja / RIK, or discussing e-invoice operators, formats, or the B2B mandate.
- Any feature where an invoice must be machine-readable, not just a PDF.

## Decide the architecture first

Answer feasibility with three tiers, cheapest first, and say which one fits their goal:

1. **PDF-only, fully local.** No account, no operator, no API. Enough for a small business that needs a printable invoice. Data, numbering, PDF, archive all local.
2. **Local data + RIK e-arveldaja API.** Recommended default when a company sends its *own* invoices: e-arveldaja is free, sending to the public sector is free and unlimited, there is no operator contract to sign, and RIK is itself the central operator, so invoices reach customers of every Estonian operator. The local app builds the payload and drives the API.
3. **Operator-level.** Only when invoicing is being sold as a product to other companies: RIK central operator service (contract with RIK, ~0,5 €/month per end client, sending/receiving free, no separate connection to the e-invoice receivers register) or a commercial operator (Telema, Finbite, Unifiedpost, Billberry).

State the hard limit plainly: **nothing running locally can deliver into the e-invoice network by itself** — delivery always passes through an operator. A self-hosted tool can email a PDF or XML; it cannot replace the operator. Do not let the user believe otherwise.

## Reference implementation on this machine

`~/earve` already implements tiers 1 and 2: `earve.py` (CLI + API client + SQLite register + reportlab PDF), `gui.py` + `gui.html` (local web UI), `build.bat`/`earve.exe` (packaged app), `data/openapi.yaml` (provider spec). Extend it rather than writing a new tool, and read its `README.md` before changing behaviour.

## Procedure (tier 2, own company)

1. **Account and key.** e-arveldaja account at e-arveldaja.rik.ee (signed by a board member or FIE). API key in Seadistused → Üldised seadistused → API võtmed yields `id`, public key and secret; the machine's external IP must be allowlisted or every call returns 401.
2. **Bootstrap from the account, don't hardcode ids.** Pull `/templates`, `/bank_accounts`, `/vat_info`, `/invoice_series`, `/sale_articles`, `/products`, `/clients` and cache them locally. These list endpoints have **no server-side filters** (only `page`), so lookup by reg code/name is done in your own store.
3. **Compose the payload** (required fields and item schema in `references/e-arveldaja-api.md`).
4. **Create → register → delivery options → deliver**, then read the invoice back: `POST /v1/sale_invoices`, `PATCH /{id}/register`, `GET /{id}/delivery_options`, `PATCH /{id}/deliver`.
5. **Verify before claiming success.** Payload validates against the provider's own `openapi.yaml`; the request signature matches `openssl dgst -sha384 -hmac`; and the flow round-trips in the demo environment (`demo-rmp-api.rik.ee`) before live.

## Pitfalls

- **VAT rate is not settable on invoice lines.** `vat_rate`, `vat_amount`, `sale_accounts_id` are read-only on `SaleInvoicesItems`; VAT is derived from the product (product → `cl_sale_articles_id` → `vat_rate`). Keep one product per rate in use (24 / 9 / 0) and map rate → `products_id`; if a rate is missing, tell the user to create that product in e-arveldaja instead of faking a rate.
- **The e-mailed PDF is the provider's template, not yours.** e-arveldaja generates and attaches its own document. A locally rendered PDF is a local copy/preview — say so, never promise visual parity.
- **`can_send_einvoice` can be false.** Always read `delivery_options` (`can_send_einvoice` + `can_send_einvoice_reason`, e.g. the buyer has no e-invoice reception) before promising delivery, and offer the e-mail fallback. Persist a distinct status such as `REGISTERED_NO_DELIVERY` instead of pretending it was sent.
- **Numbering belongs to you.** `number` is read-only; you supply `number_prefix` + `number_suffix`. Keep the sequence locally and expose "next number" in the UI so a real company can continue its existing series (a new tool that starts at 0001 silently breaks the series).
- **The invoice footer must match the document type.** A PDF-only invoice must not claim to be an EVS 923 e-invoice delivered through an operator. Branch the footer text on document type; this is the kind of detail an accountant notices.
- **Round per line, then per rate.** Round each line's net to cents, compute VAT from the rounded net per rate, then sum. Otherwise the local PDF and the provider's totals differ by a cent.
- **Old law is a trap.** Do not assert the current B2B mandate status from memory; check it (see `references/estonian-invoice-rules.md`) and say "as of <period>" or verify first.

## Rules for the invoice PDF itself

Single-page A4, Estonian labels. Header: company block left, "ARVE", number, invoice date, due date right. Buyer block below. Line table: description, kogus, ühiku hind, KM %, summa. Then per rate: `Maksumäär N%: base` and `KM N%: amount`, then `Kokku (KM-ta)`, then bold `Tasuda`. Footer block: maksja, IBAN + bank, viitenumber (`Est. Pangaühendus`-style 7-3-1 weights over the invoice-number digits with leading zeros stripped), optional note. Render it and look at it (see the `pdf` skill) before shipping.

## References

- `references/e-arveldaja-api.md` — request signing, endpoints, required payload fields, delivery semantics, error and rate-limit behaviour, offline validation.
- `references/estonian-invoice-rules.md` — EVS 923 vs EN 16931/Peppol, operators, mandate timeline, retention, VAT rates and reference-number algorithm.
