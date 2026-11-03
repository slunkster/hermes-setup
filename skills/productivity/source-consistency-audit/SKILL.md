---
name: source-consistency-audit
description: Check that info matches across docs, pages, forms.
version: 1.0.1
author: Hermes Curator
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [documents, google-docs, audit, consistency, browser, docx]
    category: productivity
    related_skills: [docx, grounded-citations, document-to-action-items, blocked-page-recovery]
---

# Source Consistency Audit

Answer the class of question "is the same info everywhere?" when the user
hands over several links, docs, pages, forms, or screenshots that are
supposed to describe the same thing (event page + rules doc + consent
form, product description + listing + invoice, policy + FAQ + email).
The deliverable is a fact-by-fact verdict plus, when asked, one
harmonized document.

## When to Use

- "Check whether all of this says the same thing" / "kas kõikjal on sama info".
- Two or more links plus pasted or attached content that should agree.
- Follow-up: "now write me the corrected/unified version".
- Not for: single-source summarization (that is ordinary reading), or
extracting obligations from one document (`document-to-action-items`).

## Procedure

1. **Resolve every link to its real target and record the destination
   ID.** Navigate with the browser (`new_tab` / `goto_url` + `wait_for_load`
   + `page_info()`), then read the resolved URL and title. Shorteners that
   answer with JS or a meta refresh return an empty `redirect_url` from
   `curl -o /dev/null -w '%{redirect_url}'`, so the browser is the reliable
   resolver. Two links that resolve to the *same* document ID are ONE
   source — say that explicitly instead of inventing a third comparison.
2. **Cross-check the links printed inside the sources against the links
   the user gave.** A page that points to its own copy of a doc can point
   at a different, stale, or wrong file; resolving both and comparing IDs
   is a real finding, not a formality.
3. **Extract the full text of every source.** Write each one to a file in
   the workspace before comparing, so text survives context pressure and
   the diff can be done in code. Publicly shared Google Docs: load
   `https://docs.google.com/document/d/<ID>/mobilebasic` and take
   `js("document.body.innerText")` — see
   `references/google-docs-text-extraction.md` for the exact shape and the
   trap that silently returns the wrong document's text. Sign-in walls mean
   the file is not public: say so and ask, or see `blocked-page-recovery`.
4. **Treat non-link sources as full sources.** An attached screenshot of a
   page counts. Zoom into it with `vision_analyze` and a `region` crop to
   quote exact numbers, addresses and email addresses rather than
   paraphrasing them. If the screenshot's URL was not provided, verify what
   you can (search the venue/address) and state plainly that you could not
   fetch that page.
5. **Build a fact matrix, not an impression.** Rows = facts that must
   agree (date, venue *and* address, start/end times, capacity, registration
   rules, eligibility, contacts, required forms, linked documents); columns
   = sources. Fill it from the extracted text, and count occurrences in code
   when the sources are long.
6. **Classify every row:** consistent / contradiction / stated in only one
   source (omission) / cosmetic (same fact, different wording). Verify
   before calling a name difference a conflict — two different names for a
   venue are usually one building at one address; check the address (a
   quick search of `<name> <street>` settles it) and then report it as a
   wording issue with one line, not as a finding.
7. **Report in the user's language.** Answer in the language of the
   request (this user works in Estonian — Estonian reply, Estonian
   headings and table labels), grouped as: what matches everywhere → then
   each discrepancy with the concrete fix. Lead with the highest-risk
   difference (a contact address, phone, date or deadline that differs
   between the public page and the official document), because that is the
   one that actually routes people wrong.
8. **Harmonize only when asked.** When the user asks for the corrected
   document, build it with the `docx` skill (JSON spec → `docx_create.py`
   → `docx_validate.py` → `docx_read.py --text`/`--structure` to verify),
   save under the user's `Documents` folder, deliver with
   `MEDIA:<absolute path>` and also paste the full text in the reply so it
   is readable without opening the file.

## Rules and Pitfalls

- **Never resolve a conflict silently.** In the harmonized document, list
  which value you kept (which email, which name) in the reply, and leave
  unknowns as visible placeholders such as `…… (lisa link)` rather than
  inventing a URL, date, or email.
- **Additions are new policy.** Clauses you introduce while harmonizing
  (extra requirements, an explicit "no form → no entry", what to bring)
  were stated nowhere; name them as your additions so the user can keep or
  drop them instead of discovering them in the published document.
- **Different wording of the same number is not a contradiction.** Flag
  only disagreements that change meaning (different numbers, dates, times,
  addresses, requirements).
- **Omissions matter as much as conflicts.** Info living on only one
  surface (registration rules on the website but not in the rules doc) is
  the most common real problem; call out who is misled by reading each
  source alone.
- **One canonical contact per document.** Keep a single email + phone in
  the harmonized version unless the user asks for several.
- **Keep the source's numbers verbatim** (team size, capacity, quotas,
  map pool, deadlines) — never round or "tidy" them while harmonizing.
- The extracted text of a doc is the *whole* doc: before claiming
  something is missing from it, re-read the extracted file rather than
  searching your memory of it.

## Support Files

- `references/google-docs-text-extraction.md` — reading public Google
  Docs text in the browser, resolving short links, and detecting the
  silent wrong-document extraction.
