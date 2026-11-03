# Estonian e-invoice rules, formats and operators

## What counts as an e-invoice

A structured, machine-readable XML invoice — not a PDF. A PDF (even a "digital" one) is a
plain invoice. The domestic Estonian profile is **EVS 923:2014/AC:2017** ("Eesti e-arve
profiil"), the format used when invoices move to banks, public bodies and companies. It is the
format the regulation on machine-processable source documents points at.

For cross-border and Peppol traffic the standard is **EN 16931** (Peppol BIS Billing 3 as the
CIUS most networks use). Practical consequence for a new build: model the data on EN 16931
semantics and emit EVS 923 from that model, so the 2030 cross-border switch is an output
change, not a rewrite.

## Obligations (verify before quoting — this moves)

- Public sector (B2G): e-invoice mandatory since 2019-07-01; sellers must send e-invoices.
- B2B: no general obligation at the time of writing — but the buyer may **require** an
e-invoice, and a supplier cannot refuse. A general mandate for VAT-registered companies was
in draft for 2027; treat that date as "planned, check the current status".
- EU **ViDA**: member states transpose by end-2026; from January 2030 no buyer consent is
needed to send an e-invoice; from July 2030 intra-EU B2B becomes e-invoicing + digital
reporting by default (EN 16931, 10-day issuance, near real-time reporting); legacy domestic
systems must align by 2035.
- Retention: accounting source documents (including the original XML) for **7 years**, in the
original format. Keep the XML next to the PDF, or rely on the operator's archive deliberately.

## Operators

Estonian e-invoices travel through operators that roam with each other plus the e-invoice
receivers register. You cannot deliver into the network without an operator:

- **RIK central operator service** — aimed at accounting-software vendors: contract with RIK,
  ~0,5 €/month per end client, sending and receiving free, and no separate integration with the
  receivers register (RIK forwards it). The realistic path for "my own software delivers e-invoices".
- **Commercial operators**: Telema, Finbite, Unifiedpost/Fitek, Billberry, and banks via their
  own gateways. Pick by market (Peppol, Baltics, volume), not by API aesthetics.
- **e-arveldaja (RIK)** is also usable directly as an operator-level destination for a single
  company: free, unlimited to the public sector, connected to all Estonian operators.

## VAT and amounts

Standard rate is 24% (raised from 22% in 2025); reduced 9% (books, accommodation, medicines,
some services) and 0% (exports, intra-EU supply, reverse charge). Treat rates as data: read
them from the account's product catalogue, never hardcode a percentage that a law change will
invalidate. For an invoice line: net = qty × unit price rounded to cents; VAT per rate from the
rounded net; totals = sum of rounded values.

## Estonian reference number (viitenumber)

Weights 7, 3, 1 repeating from the rightmost digit; check digit = (10 − sum mod 10) mod 10,
appended. Strip leading zeros from the invoice number first so `0001` becomes `13`, not `00013`.
Payment description: `Arve <prefix><number>`.

## Mandatory invoice fields (checklist for the PDF and the XML)

Seller name, reg code, VAT number, address; invoice number and date; buyer name and reg code
(and VAT number for B2B); transaction date/period; description, quantity, unit price and amount
per line; VAT rate, VAT amount and total per rate; amount due; payment due date; bank account
(IBAN) and reference number. Missing any of these is what gets an invoice rejected by an
accountant, not by the API.
