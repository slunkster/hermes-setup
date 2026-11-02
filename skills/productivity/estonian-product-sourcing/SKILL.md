---
name: estonian-product-sourcing
description: "Source or compare a product to buy from Estonian shops."
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Shopping, Estonia, Furniture, Sourcing, PriceComparison]
    related_skills: [product-price-monitor]
---

# Estonian Product Sourcing

Turn a spec from the user ("120x60, legs fold but top doesn't, stable, black, plus a cart") into a shortlist of concrete buyable products with real, comparable prices from Estonian sellers. This is the one-off "what should I buy and where" task — not ongoing price watching (that is `product-price-monitor`).

## When to Use

- "Otsi mulle X, mis vastaks nendele tingimustele." Furniture, event equipment, appliances, tools.
- Comparing the same model across Estonian dealers, or new vs used.
- The user adds a constraint mid-task (transport, cart, colour, budget) — re-run the filter, do not restart the search.

## Procedure

### 1. Convert the spec into the trade category term first

The user describes function ("klapitav laud, ainult jalad käivad kokku"); shops sell categories. Get the category right before searching — the colloquial word usually maps to a different product than intended. Decode the ambiguous ones with a spec check on a real product page, not from the search snippet.

- Done when you can name the category in Estonian and state the mechanical difference from the near-miss product.

### 2. Search the EE dealer set by category, then read pages directly

Start with a `web_search` on the category term, then open the plausible hits with `browser_exec`: `goto_url(...)`, `wait_for_load()`, then `js("document.body.innerText")` and slice the region around the model name. Search snippets regularly omit price, exact dimensions, VAT basis and stock; the page text carries them.

- Pull the full catalogue listing once (`js` on `a[href]` + `innerText`) to get every variant/size/colour of a model in one pass, instead of opening products one by one.
- Verify a suspect product still exists via the shop's own site search — dead products linger in search indexes and answer with a 404 layout.
- Done when each candidate has: model name, exact dimensions, material, colour split (top vs frame), folded thickness, weight, load rating, price, VAT basis, stock/delivery.

### 3. Normalize prices before presenting

Estonian B2B furniture shops (AJ Tooted, Ergostock, Standard, Dione) quote **ex-VAT by default** and label it "Ilma km-ta"; private buyers and non-VAT organisations pay KM. Convert with the current EE rate (24% in 2026) and say which figure you are quoting.

- Quote-only shops (Standard, and many Dione variants) show a range or nothing — mark them "küsi pakkumist" and say the number is unverified.
- The used-office channel is often 3–10× cheaper; list it as a separate line rather than mixing it into the new-price table.

### 4. Check the hard constraints, not the adjectives

Go constraint by constraint against the page data and drop candidates that fail: exact size, colour of the part the user named, load rating, folded thickness, indoor/outdoor, connectability (rows without gaps), height for chair pairing. State explicitly when a model misses a soft preference ("frame black, top birch, not black") and offer the custom/quote route for the exact match.

### 5. Include the transport/storage piece when quantity > 1

Multi-unit purchases for events, LANs, classrooms virtually always need a stacking cart. Pair each table/cart combo and verify cart capacity against unit weight × count — a "12 tables" cart rated 160 kg does not carry 12 × 13 kg tables; state the real safe count.

### 6. Deliver as a shortlist + budget table

Per option: model, shop, price (both VAT bases when relevant), 3–5 spec bullets that answer the original constraints, one link, one honest minus. End with a quantity × price budget table for the realistic counts, plus the used-market alternative. Offer the follow-up the user actually wants next: sending the quote/delivery request.

Answer in the user's language (Estonian for this user). Do not narrate the search process.

## Price data: hinnavaatlus.ee API (preferred for electronics)

hind.ee blocks curl (Cloudflare) and its search snippets are stale by 100–200 €. hinnavaatlus.ee has an undocumented, unauthenticated JSON API — use it instead (plain `curl -A "Mozilla/5.0"`):

- `https://api.hinnavaatlus.ee/search/?query=rx%209070%20xt&page=N` → `{total, data:[{id,name,sku,categoryName,price,inStore,offersCount}]}`, 24 per page; filter by `categoryName` (search is fuzzy, returns accessories too).
- `https://api.hinnavaatlus.ee/product/{id}/` → full product incl. `offers[]` (price, `dealer.name`, `inStore` now/soon/none, `availability` text, `shopUrl`, `date`, `isUsed`).
- `/search/suggest/?query=` for quick autocomplete.
- Product `price` = cheapest offer regardless of stock; compute the cheapest `inStore=="now"` offer yourself and report both.

## Cross-check German shops (electronics, PC parts)

For anything over ~300 €, compare EE prices against German shops that deliver to Estonia. From the VPS (datacenter IP) these are reachable with plain curl + desktop UA + `Accept-Language: de-DE`:

- **Amazon.de** — `https://www.amazon.de/s?k=<query>` for ASINs, then `https://www.amazon.de/dp/<ASIN>`; price = first `"priceAmount":` in the page (the `a-offscreen` spans are unreliable), stock = text after `id="availability"`, seller in `offer-display-feature-text-message`. Ships most Amazon-sold electronics to EE.
- **Alternate.de** — `https://www.alternate.de/listing.xhtml?q=<query>`; split on `productBox`, name in `product-name`, price `class="price">€ 999,00`, stock in `delivery-info`. EE orders go via the web shop as an *Angebotsanfrage* (or europe@alternate.de); UPS ~16.90 €, prepay/PayPal.
- **Blocked (403) from the VPS:** geizhals.de/.eu, PCGH Preisvergleich, idealo, proshop.de, caseking, computeruniverse, notebooksbilliger, galaxus, cyberport. Mindfactory doesn't ship abroad. Try them via `ssh mac` curl (residential IP) if the Mac is awake.
- **VAT normalisation:** DE shelf prices include 19% VAT; distance sales to EE are usually charged EE VAT (24%) → multiply by 1.24/1.19 ≈ 1.042, then add shipping. Present the adjusted "delivered to EE" figure next to the EE best price; say it's an estimate until checkout.

## Pitfalls

- "Kokkupandav laud" in EE retail almost always means the **top folds in half** (suitcase style, folded ~60x60x8 cm). The rigid-top/folding-leg product is "konverentsilaud / seminarilaud kokkupandavate jalgadega". Wrong category = every candidate rejected at the end.
- Same model, different price per dealer (155 € at one, 175 € at another) — compare by model across dealers, not by shop.
- Colour strings are "plaadi värv / raami värv" and the order differs between shops; read the detail table ("Lauaplaadile värv", "Raamile värv") instead of parsing the product name.
- Cart weight ratings are the total platform load: 12 folded tables at 13 kg each already exceed a 160 kg cart. Always do the multiplication aloud in the answer.
- Folded stack height matters for the van: 12 tables at 8 cm = ~1 m plus frame — mention it before the user buys a cart that does not fit their vehicle.
- Check both the category page and the product page for price: category listings are sometimes stale by a few euros; give the range, not a false-precise number.

## Reference

- `references/estonian-furniture-retailers.md` — who sells what (office/seminar furniture, event furniture, budget plastic, used), and their price/VAT quirks.

## Verification

- [ ] Category term decoded and matched to the real mechanism the user asked for.
- [ ] Every shortlisted product was opened and read, not quoted from a search snippet.
- [ ] Prices stated with VAT basis; quote-only and used channels labelled as such.
- [ ] Cart capacity checked against unit weight × count.
- [ ] Budget table covers the plausible quantities, and the next step (quote request) is offered.
