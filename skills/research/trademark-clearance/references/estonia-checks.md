# Estonian registers & practical checks

## Patendiamet public search — https://andmebaas.epa.ee/avalik/#/trademarks

Form controls (stable ids):

- `#verbalElement` — mark text. The neighbouring checkbox = EXACT match (verified: exact
  "BODY TALK" returns its 2 records; exact "TALK" returns 0). Without the checkbox, matching
  is raw substring ("talk" also hits STALKER, Netalko, Vitalkomplex).
- `#type` multi-select: 0 = Registreerimistaotlus, 1 = Registreeritud kaubamärk,
  2 = Rahvusvaheline registreering.
- `#goodsAndServices` (Nice class number), `#status`, `#applicantOwner`, date ranges.
- Submit: button with text "Otsi"; return via "Tagasi otsinguvormile".
- Results header: "Leiti N tulemust. Kuvatakse esimesed M." — the displayed M can be capped
  below N; the count line is authoritative.
- Columns: Registreeringu number | Taotluse number | Omanik | Kaubamärk | Staatus | klassid.

Pitfall: programmatic text insertion APPENDS to a populated `#verbalElement` — clear the field
first (native setter + input event) or reload the form before typing.

More EPA mechanics verified: the exact-match checkbox shares the id `verbalElement` with the text
input — disambiguate with `input[type=text]#verbalElement` vs `input[type=checkbox]#verbalElement`.
Set values with the native setter + input AND change events (plain fill_input sometimes leaves the
Angular model stale). Failure smell: results showing 'Leitud tulemusi on rohkem kui 1000' (or the
previous query's rows) mean the filter never applied — reload the form and redo field-by-field.
Sanity phrase for substring mode: 'VÄLK TAKSO' -> 1 row. Verify the exact-mode checkbox with an
exact 'VALK' (2 rows) before trusting any zero-results claim.

## Äriregister — https://ariregister.rik.ee/est

- Cookie banner first: click "Nõustun".
- Search input: `#company_search` (`name_or_code`); substring matching; submit with Enter.
- Results page: `/est/company_search_result/<searchId>?name_or_code=<q>`; company rows are
  `a[href*="/company/"]`; statuses (Likvideerimisel etc.) show as text near the link.
- Liquidation != gone: an entity in likvideerimine is still registered and blocks identical
  new names.
- Search the full candidate phrase ("talk meedia"), the stem ("talk") and note that a phrase
  query can return 0 while the stem returns many hits.

## e-äriregistri nimeotsing (name-suitability pre-check) — https://ariregister.rik.ee/est/name_query

Checks the candidate name against registered names AND trademarks; the verdict is a single line in
`document.body.innerText` ('Nimi sobib suure tõenäosusega' / negative variants).

- `#name` — candidate name (fill_input works).
- `#legal_form` — native select; Osaühing = value **5** (native setter + change event).
- Activity typeahead `#s__activity_emtak_search` — type the EMTAK code, then commit with a REAL
  mouse click (`click_at_xy`) on the `.typeahead.dropdown-menu` item; verify the hidden input
  `emtak_cl` holds the code.
- All three fields are required — otherwise 'Väli on kohustuslik.' and no verdict renders.
- After 'Otsi', wait ~8 s; the verdict appears below the form (green 'Nimi sobib…' or a negative).

## Riigi Teataja (statute text)

- Prefer the JSON-API recipe in the statutory-law-research skill
  (`references/estonia-riigi-teataja.md`).
- Fallback: open the akt URL in the browser and slice `document.body.innerText` around a section
  keyword (e.g. "Ärinime valiku piirangud") — web_extract truncates giant consolidated acts.
- Confirm section numbering in the current redaction before citing anything.

## .ee domains & cross-references

- `whois -h whois.tld.ee <name>.ee` — "Domain not found" = free; otherwise registrant + dates.
- Aggregator cross-reference: nimistu.ee company pages link EPA records via
  `?nr=<regNo>&ln=et`.
