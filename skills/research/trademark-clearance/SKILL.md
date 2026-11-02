---
name: trademark-clearance
description: "Use when checking if a name or trademark is free or taken."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Trademarks, Branding, Legal, Estonia, EU, Research]
    category: research
    related_skills: [statutory-law-research, grounded-citations]
---

# Trademark & Name Clearance (Europe / Estonia)

Freedom-to-use / freedom-to-register checks for a mark, brand or company name: "is X
taken as a trademark in Europe?", "can I name my OÜ X for activity Y?". The deliverable
is a per-office list of LIVE vs dead marks with numbers, classes, owners and statuses,
plus the legal basis (Estonian firm-name rules when a company name is at stake) and an
explicit risk summary per aspect.

## When to Use

- User asks whether a name/mark is free, taken, blocked, or safe to register (Estonian or English).
- Before founding a company, branding, buying a domain, or filing a trademark application.
- Both halves count: the trademark side (registers) and, for a company name, the
  distinctness side (äriregister) plus the trademark-consent rule (ÄS § 12 lg 3).
- Skip when the question is purely "what does the statute say" with no name at stake -> use statutory-law-research.

## Procedure

1. **Pin the target before searching.** Exact mark string(s), spelling variants (Estonian vs English —
   Meedia / Media, both word orders), territory (all-Europe vs Estonia), and the user's activity.
   Map the activity to Nice classes (EMTAK mapping in `references/estonia-firm-name-law.md`).
   Decide which question you are answering: firm-name registration, use-in-trade, or both.
2. **TMview first** for the pan-European trademark picture. Drive it by URL, never by its UI
   form (see pitfalls). Exact search (criteria=I) for the bare name; contains-search (criteria=C)
   for multiword candidates and variants — "contains" matches both words in any order and matches
   substrings, so run both spellings and check for zero phrases.
   Recipes + row extraction + office codes: `references/tmview-eu-search.md`.
3. **Estonia (Patendiamet public DB)** when EE matters: substring sweep with `#verbalElement`,
   then the exact-match checkbox to prove presence/absence of the bare mark. IRs recorded for EE
   appear here too. Mechanics: `references/estonia-checks.md`.
4. **Company-name side** (if an OÜ name is in question): äriregister substring search + the exact
   candidate string + the stem; note entities in liquidation still block identical names. Then run the official **e-äriregistri nimeotsing** (name + legal form + EMTAK) — it also cross-checks trademarks and yields a quotable verdict ('Nimi sobib suure tõenäosusega').
5. **Law**: fetch the CURRENT ÄS text from Riigi Teataja (use statutory-law-research's JSON-API
   recipe; browser innerText slicing is the fallback). Apply § 11 lg 2 (clear distinctness from all
   registered/reserved names) and § 12 lg 3 (trademark-consent rule — consent required only if a
   mark protected IN ESTONIA overlaps the company's actual activity classes; also applies to later
   activity changes). Details: `references/estonia-firm-name-law.md`.
6. **Practical layer**: `.ee` domain via `whois -h whois.tld.ee <name>.ee` (not a blocking right,
   but users care); note it separately from legal findings.
7. **Classify and answer.** Split every result set LIVE vs dead; answer each user question in the
   first lines; state explicitly which findings do/don't overlap the user's classes.

## Answer Shape (user preference)

- Mirror the user's language — Estonian for this user. CLI: plain text, no markdown symbols.
- Verdicts first (one line per question), then evidence lists.
- Evidence entries: `office/country | mark | reg/app no | Nice classes | owner | status`,
  with statuses kept verbatim (Registreeritud / Registered / Expired / Ended / Kehtiv).
- Group as LIVE (registreeritud) and dead/aegunud separately; name which classes are relevant
  to the user's field and whether they overlap.
- Close with: per-aspect risk summary (madal/keskmine/kõrge via reasons), practical notes
  (domains), "andmed seisuga <date>", a not-legal-advice caveat, and self-check links
  (tmdn.org/tmview, andmebaas.epa.ee, ariregister.rik.ee).

## Pitfalls

- **TMview's home-page typeahead ignores programmatic input.** Native-setter dispatch and CDP
  insertText both leave its React state empty; clicking SEARCH then flags "Required field".
  Do not debug the form — navigate the results hash URL directly (params below).
- **TMview criteria codes are non-obvious and silent when wrong:** C = Contains, I = Is (exact).
  Other codes are unverified (E is NOT exact and yields a different set) — verify any run by
  reading the count line and the first rows before trusting it.
- **"Contains" is raw substring matching:** "talk" also hits Stalker, Netalko, Vitalkomplex.
  Classify live/dead and read Nice classes before drawing conclusions; never count substring hits
  as conflicts.
- **An exact-hit list is not the risk list.** For use-in-trade similarity also scan near names
  (doubled-word brands, "+media/meedia" composites) by contains-searching the distinctive word
  and filtering by classes.
- **"Registered" is territorial.** EE firm name -> only EE national marks + EUTMs + IRs designating
  EE/EU can trigger the consent rule. Operating in country X -> X's marks matter. Say which
  territory each finding blocks.
- **IR (WIPO) rows carry no designated-country list in TMview.** Check WIPO Madrid Monitor,
  EUIPO eSearch, or the national DB (EPA lists IRs recorded for EE) before claiming EE/EU scope.
- **Statute numbering moved across redactions** (the firm-name/trademark provisions were
  renumbered). Cite the current redaction and quote the fetched text.
- **EPA form: programmatic insert APPENDS** to a populated `#verbalElement`. Clear the field first
  or reload the form. Results display can be capped ("esimesed N") — the "Leiti M" count is
  authoritative.
- **Äriregister phrase searches can return 0** while the stem has many hits — search the full
  candidate, the stem, and check liquidation status separately.
- **Compare counts before concluding:** TMview's "1-100 of N" line vs rows actually collected;
  with many pages, append rows to a workspace file and aggregate in Python, not by eye.
- **TMview can be fully blocked** — EUIPO WAF (BigIP) answers 302 → /error/revise.html for both
  curl and real browsers ('Our website has detected a problem…'). Do not retry-loop; pivot to
  EUIPO eSearch for EUTMs/IRs (recipe in `references/tmview-eu-search.md`) — for an EE firm name
  EPA + eSearch already cover every EE-protected mark.
- **eSearch quotes are not phrases** and a multiword query can silently return the previous result
  set — prove absence of composites by scanning the contains-set for the second word instead.
- **RIK nimeotsing needs all three fields** (nimi; õiguslik vorm — Osaühing = value 5; EMTAK
  tegevusala) or it errors 'Väli on kohustuslik'; the EMTAK typeahead commits only on a REAL mouse
  click (click_at_xy) on the `.typeahead.dropdown-menu` item — JS-dispatched events leave the
  hidden input empty.

## Verification

- Every result set: count line matches the number of rows collected (no silent truncation).
- Every "live" claim reads status Registered/Kehtiv in the fetched row.
- "0 results" claims come from an exact search, not a substring one.
- EE-law claims quote the ÄS subsection as fetched in this session (current redaction).
- The answer states which territory each finding affects and the not-legal-advice caveat.
- Company-name answers quote the nimeotsing verdict line and the fetched ÄS § 15¹ reservation rule
  (one reservation per person, 6 months + one 3-month extension) when advising on reservation.

## References

- `references/tmview-eu-search.md` — TMview URL recipes (criteria/office/page params), DOM row extraction, count interpretation.
- `references/estonia-checks.md` — EPA trademark DB mechanics, äriregister search, Riigi Teataja text extraction, .ee whois.
- `references/estonia-firm-name-law.md` — ÄS §§ 9/11/12 rules, consent gate logic, EMTAK-to-Nice mapping, answer logic for "can I name my OÜ X".
