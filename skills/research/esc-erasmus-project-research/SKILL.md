---
name: esc-erasmus-project-research
description: "Use when finding all Erasmus+/ESC projects of an org."
---

# Erasmus+ / ESC project research (Estonia-focused)

Class of task: compile the complete set of European Solidarity Corps / Erasmus+ projects implemented by an organisation (or involving one) — titles, years, activities, grant sums, run dates, project codes — verified across the Estonian agency database and the EU results platforms, delivered in Estonian with a sources block. Typical asks: „leia kõik MTÜ X projektid", partner due diligence before a joint application, or a project-history list for reporting.

## Source ranking (use in this order)

1. **kaart.noored.ee** — Haridus- ja Noorteamet's map of supported projects (Erasmus+, ESC, Noortekohtumised, EMP/Norra; ~9 years, ~4 000 pin records). Primary source; most complete for Estonia.
2. **EU results platforms** — ESC: `youth.europa.eu/solidarity/projects`; Erasmus+: `erasmus-plus.ec.europa.eu/projects/search`. Content is beneficiary-submitted ⇒ only a subset of projects appears there; use for verification, never for completeness.
3. **Organisation identity** — ariregister.rik.ee / inforegister.ee / ssb.ee: registry code, former names, contacts.
4. **euroopanoored.eu** (agency news) and the organisation's own site — qualitative facts, and the real project title when the registry title looks odd.

## Workflow

1. **Resolve the organisation before searching.** Get the registry code and every former name (renames carry the project history over). Watch lookalike brands — a same-named org in another county is a different legal person; distinguish by registry code and the location field before attributing rows.
2. **Pull the full dataset instead of crawling the UI.** `curl -sL https://kaart.noored.ee/wp-json/mapData/v1/projects -o all.json` (~13 MB, all pins). Each pin's `pinContent` HTML carries domain, org, project title and tags [year, activity, programme]. Parse locally and substring-filter org+title across ALL name variants at once. Field map / snippets: `references/registry-mechanics.md`.
3. **Confirm and enumerate in the UI** so the answer matches what the user sees: open `https://kaart.noored.ee/projektid/?search=<term>&order=DESC&meta_key=aasta&paged=1`, **click the „Otsi" button** (the query param alone leaves the list unfiltered), switch to the „Nimekiri" list view, and scrape `tr.table__row` cells plus each row's `button[data-project]` id. Do not rely on the list export: the XLS download can arrive corrupt and `file=csv` just returns the HTML page.
4. **Fetch the per-project detail cards.** `https://kaart.noored.ee/projektid/arc_<id>/` builds the card via JS — wait for load, then read `document.body.innerText` from "Sulge" onward: coordinator location, dates, grant, participants, project code, description. Persist each id's text to disk as you go, so a dropped browser WS costs only the missing ids (`ensure_real_tab()` then re-run those).
5. **Verify the headline projects on the EU platform.** Load the platform landing page and submit the search through the UI input (ESC placeholder „Example employment, climate change, etc…") — deep-linking the results URL can be answered with „403 Disallowed by robots.txt" while the same search via the UI works. Cards show Host (= implementing org), dates, grant, reference; ESC detail URLs follow `/solidarity/projects/details/<code>_en`.
6. **Deliver** in Estonian as plain text for CLI: numbered list (title, year, activity, sum, run dates, project code, arc link), total grant recomputed in code, then a short NB section for data quirks, then a Sources list — build it with the grounded-citations ledger so URLs→[n] come from retrieval. Offer the xlsx/csv follow-up; this user collects these lists.

## Data-quality rules (the registries have known artifacts)

- **ESC volunteering rows („vabatahtlik teenistus") share ONE label as their „Projekti nimi" for the whole call round** — sometimes another project's name entirely; it is not the row's real project title. Attribute volunteering projects by the „Organisatsiooni nimi" column only, and verify a suspicious title against the org's own site / EU card before repeating it as their project name.
- The map lists orgs under their **current** registered name; old rows of a renamed org carry the new name.
- Absence from the EU platforms is NOT evidence a project doesn't exist (content-gated); absence from kaart.noored.ee IS meaningful for Estonian-funded projects in the covered window.
- Dates/sums can differ slightly between kaart and EU cards for the same project — report the Estonian DB values and never mix the two silently.
- „Elluviidud" = the beneficiary/coordinator column. Partner roles are not visible in either registry — state that limitation instead of guessing involvement. Rows of same-brand orgs elsewhere are not the target's projects.
- Sum grant amounts in code, and verify the delivered project count equals the number of org rows in the UI search result.
