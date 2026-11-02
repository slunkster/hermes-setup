# TMview (tmdn.org) — driving the search by URL

TMview is EUIPO's pan-European aggregator: EUIPO + all EU national offices + WIPO +
many non-EU offices, updated daily, free, no login. Use as the first pass for the
trademark picture.

## URL recipes

Template (all parameters live in the hash fragment):

    https://www.tmdn.org/tmview/#/tmview/results?page=1&pageSize=100&criteria=C&basicSearch=TALK

- `criteria` — C = "Contains" (substring/word match), I = "Is" (exact mark text).
  Verified empirically: I sets the UI to "Is" and returns the exact-name set; C is orders of
  magnitude larger. Unverified codes silently return other sets — verify by reading the count
  line and first rows.
- `pageSize=100` works; verify by counting extracted rows.
- Pagination: increment `page`.
- Office filter: `fOffices=EM` (EUIPO), `fOffices=EE` (Estonia); comma-join for several.
  The left sidebar checkbox state updates to match, so the filter's effect is verifiable.
- URL-encode spaces/accents in basicSearch (`%20`). Search both spellings of multiword marks
  (e.g. TALK%20MEDIA and TALK%20MEEDIA) and remember contains-mode matches both words in
  either order plus substrings.
- First visit: click "Accept all cookies" once.

## Do not fight the home page

The homepage search box is a React typeahead that ignores programmatic input
(native-setter dispatch and CDP Input.insertText both leave React state empty; SEARCH then
flags "Required field"). Navigate result URLs directly instead — they drive the same search.

## Extracting rows

    rows = [...document.querySelectorAll('[role=row]')]

For each row join innerText lines with ' | '; drop the header row (contains
'Trade mark name') and rows shorter than ~20 chars.

Row layout: `[graphic marker '-'] | name | dd/mm/yyyy | classes ("9, 35") | status |
office ("Germany - DPMA", "EUIPO - EUIPO", "WIPO - WIPO") | app no | applicant`.

Parse per row: find the field matching `\d{2}/\d{2}/\d{4}`; the token before it is the name,
the tokens after are classes / status / office / appno / applicant.

## Count line

Read `1-100 of N` from the body text; fetch `ceil(N/100)` pages; compare the collected count
against N before trusting completeness. With many pages, append raw rows to a JSON file in the
workspace and aggregate in Python — do not count by eye.

## Interpreting

- Statuses seen: Registered / Expired / Ended / Filed (national DBs have their own vocabulary).
  Always split LIVE vs dead per result set and report which is which.
- European-office filter: substring-match the office label over a list such as: EUIPO, Estonia,
  Germany, Finland, Sweden, Denmark, France, Benelux, Greece, Malta, Portugal, Poland, Romania,
  Switzerland, Norway, Türkiye (not 'Turkey'), Ukraine, Russia, United Kingdom. Watch
  'Benelux - BOIP' (BE/NL/LU) and 'Türkiye - TURKPATENT'.
- WIPO rows are international registrations; TMview does not show their designated countries.
  For territorial scope use WIPO Madrid Monitor, EUIPO eSearch, or the national office DB
  (EPA lists IRs recorded for EE).

  ## If TMview is blocked — EUIPO eSearch fallback

  TMview sometimes serves the EUIPO WAF interstitial ('Our website has detected a problem…',
  BigIP 302 to /error/revise.html) to both curl and real browsers. Don't retry-loop; use EUIPO
  eSearch directly — for an EE firm name it plus EPA covers every EE-protected mark
  (EUTM + IR + EE national).

  - Basic search by URL: `https://euipo.europa.eu/eSearch/#basic/1+1+1+1/100+100+100+100/<query>`
    (query URL-encoded, space = %20; the 1+1…/100+100… flags are harmless). Contains-style,
    diacritic-folding: a VÄLK query also returns VALK* marks.
  - Quotes are NOT phrases ("A B" behaved like contains-A) — verify absence of composites by
    reading the full contains-set and scanning it for the second word.
  - Count line in body text: `N search result(s) in M page(s)`; zero hits show 'No results were
    found' and no count line.
  - Rows: cards at `.search-results-boxes.active div.box`; per card read the `header` title
    ('<num> - <name> + info') and the `dt`/`dd` pairs (Trade mark number, Type, Status, Nice
    Classification, Owner name, Basis…).
  - Paginate by clicking a visible 'Next' anchor; append rows to a file, dedupe by Trade mark
    number, and check the unique count against the count line.
  - Full details incl. per-class goods/services and owner address:
    `https://euipo.europa.eu/eSearch/#details/trademarks/<number>`.
