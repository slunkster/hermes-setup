---
name: estonian-municipal-documents
description: "Use when citing Estonian municipal or state documents."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Estonia, Municipal, Statistics, Sources, Citations]
    category: research
    related_skills: [grounded-citations, university-assignment-writing, estonian-grant-applications]
---

# Estonian municipal and state documents

## When to Use

Use when a claim has to come from Estonian official material rather than general
knowledge: a valla arengukava or majandusaasta aruanne, a rahuloluküsitlus, a
maakonna arengustrateegia, a ministry report, or a Statistikaamet figure — for
coursework, a grant application (KOP, Erasmus+/ESC), or community-work planning.
Also use it when someone quotes a "fact" about an Estonian region from a news
story or search snippet and it needs checking against the document.

Reading, quoting and citing that material: valla
arengukava, majandusaasta aruanne, rahuloluküsitlus, maakonna arengustrateegia,
ministry reports, Statistikaamet figures. Pair with `grounded-citations` for the
citation ledger, and with `university-assignment-writing` or
`estonian-grant-applications` when the output is that artifact.

## Where the documents are

| Need | Source |
|---|---|
| Valla arengukava (kehtiv + eelnõu), investeeringutekava, eelarvestrateegia | `https://<vald>.ee`, uploads folders; the "Arengukavad" page gives the avalik väljapanek dates and says whether the text is still an eelnõu |
| Kinnitatud aktid ja lisad | Riigi Teataja, `riigiteataja.ee/aktilisa/...` |
| Vanemad uuringud, kohalik ajaleht | `kogukond.<vald>.ee/kogukond/docs/file/...` |
| Riiklikud prognoosid ja üleriigiline planeering | `riigiplaneering.ee` |
| Ministeeriumide ülevaated (demograafia, noored, haridus, sotsiaal) | `hm.ee`, `agri.ee`, `fin.ee`, `sm.ee` |
| Eesti kohta tehtud rahvusvahelised ülevaated | `oecd.org` (Shrinking Smartly in Estonia; place-based regional development) |

## Procedure

1. **Pick the newest document that covers the angle and check its status** — eelnõu
   vs kinnitatud. The municipality hosts both; in a pending text the PDF title
   page has a blank "Kinnitatud ... määrusega nr ..." line.
2. **Pull the PDF into the workspace** (not `/tmp`) and extract it page by page
   with markers: `python scripts/pdf_pages.py extract doc.pdf > doc.txt`, then
   grep the extract. Cite the page you actually grepped; the footer
   ("Lehekülg N /137") lets you state which numbering you use.
3. **Search each theme in two places.** An arengukava states it in the SWOT and
   again in the chapter's "Arengueeldused ja probleemid" list, while the numbers
   sit in that chapter's tables (rahvastik, tööhõive, haridus, noorsootöö,
   elamumajandus). Table lines extract out of order — read the surrounding rows,
   not a single grep hit.
4. **Cross-check every figure** against a second source or series before it
   reaches prose (see Pitfalls).
5. **Record value + year + series/author + document + page** for each number.
   A municipal figure without a date and series is unusable.
6. **Keep the document's own wording for what you attribute to it** ("arengukava
   nimetab probleemina …", "mõõdikute järgi"), and put your own inference in a
   sentence of its own, clearly marked as yours.

## Pitfalls

- **Two population series, both official.** Statistikaamet counts residents with
  the residents index (≥0.7, and it accounts for unregistered migration), so it
  reads lower; the rahvastikuregister counts everyone registered there.
  Nationally ~2–3% apart, in small peripheral municipalities far more. Never
  subtract across series or across different dates — give series + date for every
  figure.
- **Scenario tables are not trends.** A national forecast lists each
  municipality once per scenario ("seniste rändesuundumuste jätkumine",
  "sisserände Eesti", …); the same municipality can lose 23% or 50% depending on
  the scenario. Name the scenario in the text. A value that repeats identically
  across scenarios may be a modelling floor — read the method chapter before
  quoting it as a projection.
- **A search snippet is not the document.** Snippets cut the condition off a
  comparative claim, so "the decline is slower in X" can hold only in one
  scenario. Read the paragraph and the table; if you already repeated the snippet
  version, correct it explicitly.
- **Prose vs its own table.** A plan's narrative and its indicator table can
  disagree ("sündimus on stabiilne" beside a record-low year). Present both and
  name the conflict instead of smoothing it. In a small municipality one year is
  noise — births can fall and recover within two years; never build a trend on a
  single value.
- **Ambiguous indicator names.** In "mõõdikud" tables an indicator can count
  people or units ("noorteaktiivide arv"). Do not guess the unit — quote the
  indicator as written or leave it out.
- **Author and status.** Ministry reports usually name the author on the title
  page; municipal PDFs usually do not, so cite the issuing body. Say in your
  summary whether a cited plan is still an eelnõu, but follow the user's
  preferred reference form in the deliverable itself.
- **Pay and service comparisons need their reference.** "Madalam palgatase" is
  meaningless without "kui Eesti / Võru maakonna keskmine"; carry the comparison
  and the year into your text.

## Supporting files

- `references/arengukava-reading.md` — structure of a development plan and which
  table holds which figure.
- `scripts/pdf_pages.py` — per-page text extraction with `=====PAGE n=====`
  markers plus line-to-page mapping for `(lk n)` citations.
