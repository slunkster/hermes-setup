# RIK e-arveldaja API ("e-Financials") — integration notes

Base URLs: `https://rmp-api.rik.ee` (live), `https://demo-rmp-api.rik.ee` (demo/testing);
all paths under `/v1`. Machine-readable spec: `GET /openapi.yaml` on either host
(`/api.html` is the same spec rendered, `/test.html` is RIK's request builder that shows the
header construction). JSON in, JSON out.

## Request signing

Every request needs two headers; there is no bearer token.

```
qt  = UTC now, second precision, "%Y-%m-%dT%H:%M:%S"
msg = f"{api_key_id}:{qt}:{path}"          # path = "/v1/..." — NO scheme, host or query string
sig = base64(HMAC-SHA-384(msg, api_key_secret))
X-AUTH-QUERYTIME: qt
X-AUTH-KEY:       f"{api_key_public}:{sig}"
```

- Query parameters are **not** signed (only the pathname), so pagination never invalidates a signature.
- Clock skew over ±5 minutes → 401. Negative access events (≥10 in 5 min, ≥30 in 60 min,
  ≥60 in 24 h) block the source IP until the window drains — so a retry storm after a bug
  locks you out. Fix the payload before retrying in a loop.
- API keys are managed by the company's representative in the UI; each key carries allowed IPs
  and permitted functions. A 401 with a correct key almost always means the IP is not allowlisted.

Self-check without credentials: compute the signature twice (Python `hmac` vs
`openssl dgst -sha384 -hmac <secret> -binary`) and compare base64 — catches message-format
mistakes before blaming the key.

## Endpoints used by a sending workflow

| Call | Purpose |
|---|---|
| `GET /v1/vat_info` | company VAT number + EMTA reference; also the cheapest auth probe |
| `GET /v1/invoice_info` | company invoice settings (address, e-mail template, default template id) |
| `GET /v1/templates`, `/bank_accounts`, `/invoice_series` | ids needed in the payload |
| `GET /v1/sale_articles`, `/products`, `/clients` | VAT rate per product, buyer ids |
| `POST /v1/sale_invoices` | create → `{code, created_object_id, messages}` |
| `PATCH /v1/sale_invoices/{id}/register` | confirm/register the invoice |
| `GET /v1/sale_invoices/{id}/delivery_options` | `can_send_einvoice`, `can_send_einvoice_reason`, `can_send_email`, `can_send_email_addresses` |
| `PATCH /v1/sale_invoices/{id}/deliver` | body `{send_einvoice: bool, send_email: bool, email_addresses?, email_subject?, email_body?}` — both booleans are required |
| `GET /v1/sale_invoices/{id}` | read back status, payment_status, deliveries |
| `GET /v1/sale_invoices/{id}/xml`, `/pdf_system` | the provider's own XML/PDF documents |
| `PATCH /v1/sale_invoices/{id}/invalidate`, `DELETE .../{id}` | credit/cancel paths (undocumented edge cases — test in demo) |

List responses are `{current_page, total_pages, items}` and accept only `page` and
`modified_since` — no filtering by code, name or date range. Page until `page >= total_pages`
or the batch is empty.

## `SaleInvoices` required fields

`sale_invoice_type` (`"INVOICE"`; credit invoices reference `credit_sale_invoices_id`),
`cl_templates_id`, `clients_id`, `cl_countries_id` (`"EST"`), `number_prefix`,
`number_suffix`, `create_date`, `journal_date`, `term_days`, `cl_currencies_id` (`"EUR"`),
`show_client_balance`.

Useful optional: `bank_accounts_id`, `bank_ref_number`, `payment_description`,
`invoice_info` (free text printed on the invoice), `client_name`, `client_vat_no`,
`base_*` amounts for foreign currency, `intra_community_supply`, `triangulation`,
`period_start_date`/`period_end_date`, `additional_info_content`.

Read-only and computed by the provider: `id`, `number`, `status`, `payment_status`,
`net_price`, `vat5/9/13/20_price`, `gross_price`, totals in `base_*`.

## `SaleInvoicesItems`

Required: `products_id`, `amount`, `custom_title`.
Optional: `unit`, `unit_net_price`, `total_net_price`, `discount_percent`, `discount_amount`,
`projects_*` (cost centres).
Read-only: `vat_rate`, `vat_amount`, `vat_rate_exception_20`, `sale_accounts_id`,
`cl_sale_articles_id` — **VAT comes from the product**, so the product catalogue must contain
one entry per VAT rate you invoice at.

## Clients

`POST /v1/clients` with `{name, code, is_client: true}` plus optional `invoice_vat_no`,
`email`, `address_text`, `invoice_days`. Resolve before creating: the list endpoint cannot be
searched server-side, and duplicates are easy to create by posting slightly different names.
Persist the returned `created_object_id` locally — the payload needs the numeric `clients_id`,
not the reg code.

## Offline payload validation

Download the spec, then validate your payload against the exact schema before any network call:

```python
spec = yaml.safe_load(Path("openapi.yaml").read_text(encoding="utf-8"))
schema = {"$ref": "#/components/schemas/SaleInvoices"}
validator = jsonschema.Draft202012Validator(
    schema, resolver=jsonschema.RefResolver.from_schema(spec))
errors = list(validator.iter_errors(payload))
```

This catches missing required fields, wrong types and read-only fields sent as input — far
cheaper than a 409 from the API. `RefResolver` is deprecated but still the shortest route for a
single-file spec; keep the call in a helper so a future jsonschema version bump touches one place.

## Errors

`4xx` bodies are `{code, messages}` or plain text (`Unauthorized`). Treat `409 Conflict` as a
business-rule rejection (duplicate number, closed period, bad account) and surface the message
to the user instead of retrying. `401` is auth/signature/IP/clock — see above.
