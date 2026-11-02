# EU VPS options near Estonia — anchors

Every number here is an anchor, not a quote: Hetzner repriced products multiple times in 2026 (memory-component crisis) and vendors run promos — re-check the vendor's site before quoting or ordering. All options are EU-based (GDPR). Latency from Tallinn: Tallinn DCs ~1–2 ms, Helsinki ~5–10 ms, Vilnius ~15–20 ms. For a chat/gateway agent latency barely matters — the model API dominates — so choose on price, support and invoicing.

## Main options

| Provider | Location | Example plan | Net price anchor (late 2026) | Notes |
|---|---|---|---|---|
| Hetzner Cloud | Helsinki, FI (also Falkenstein / Nuremberg, DE — same price) | CX22: 2 vCPU / 4 GB / 40 GB NVMe | ~€4.49/mo | 20 TB traffic incl. in EU regions; IPv4 +€0.50/mo (IPv6 free); backups +20%; hourly billing; hcloud API, snapshots, firewalls. Account creation may require ID verification. US regions cost ~3× and include only 1 TB — never pick them for an EU requirement. |
| Hetzner (bigger tiers) | same | CX32: 4 vCPU / 8 GB / 80 GB | ≈2× CX22 | For Docker sandbox / Playwright / multiple profiles. |
| Zone.ee CloudServer | Tallinn, EE | VPS III: 2 vCPU / 4 GB / 50 GB NVMe | €18.29/mo + VAT | Estonian-language support and invoicing; Equinix/Telia DCs. VPS II (1 vCPU / 2 GB / 35 GB) €9.12 + VAT — too small for Hermes. |
| GetVPS.ee (Core Hosting) | Tallinn, EE, TIER III | from 1 vCPU / 1 GB / 50 GB NVMe | from €5.75/mo | Estonian support, first month free; pick a larger tier for Hermes. |
| Time4VPS | Vilnius, LT | 2 vCPU / 4 GB / 50 GB class | ~€3–4.5/mo | Cheapest; single DC; EN/LT support; best prices on prepay promos. |

## Hetzner specifics worth remembering

- Prices are net, ex-VAT; VAT added at checkout. IPv4 is a separate paid add-on — a server is IPv6-only without it.
- June 2026 repricing hit dedicated-vCPU (CCX) lines hardest (CCX13 jumped to €42.99) and lifted ARM CAX11 to €5.99 — which is why the x86 CX22 is both cheaper and the safer default.
- Hourly billing makes a quick trial cheap; backups cost +20% of the server price.

## Sizing for Hermes

- Comfortable minimum: 2 vCPU / 4 GB RAM / 40 GB SSD — gateway + cron + a few sessions.
- Heavier (Docker sandbox backend, Playwright/browser automation, multiple profiles): 4 vCPU / 8 GB / 80 GB.
- x86_64 is the safe default; ARM works but is not cheaper than x86 on Hetzner anymore.
