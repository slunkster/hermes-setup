---
name: document-harmonization
description: "Use when the same info lives in several docs or pages."
version: 1.0.0
author: Hermes Curator
license: MIT
metadata:
  hermes:
    tags: [documents, google-docs, consistency, audit, docx, html, estonian]
    category: productivity
    related_skills: [docx, google-workspace, document-to-action-items]
---

# Document Harmonization

Audit the same facts across several sources (websites, Google Docs, forms), report the conflicts, then write one harmonized master document and deliver it paste-ready for Google Docs.

## When to use

- "Kas kõikjal on sama info?", "check these two links say the same thing", "do these documents agree" — the same event/rules/info spread across a website, Google Docs, consent forms.
- Requests that come straight after such an audit: "kirjuta mulle uus <document>", "make it consistent", "make it more pastable into docs".
- The deliverable usually lands in Google Docs. Documents and chat replies mirror the user's language (Estonian here), including domain terms.

## Procedure

### 1. Resolve every link to its real target before reading anything

- Short/friendly links (link2.it, bit.ly, custom redirectors): open them in the browser and read `page_info()['url']` + `title`, or `curl -sIL` — never assume a link maps to the document it "should".
- **Two different short links can point at the SAME document.** Verify by resolved URL/doc id, not by title or by which task the user attached them to.
- Build a `link → doc id → title` table; it belongs in the answer, because "the link you sent me points at doc X" is itself a finding.

### 2. Read public Google Docs without OAuth

- Best path: `https://docs.google.com/document/d/<id>/mobilebasic` in the browser, then `js("document.body.innerText")`. Returns the full body as plain text, no sign-in needed for link-shared docs.
- `.../export?format=txt` can silently NOT navigate (it triggers a download): `innerText` then still shows the *previous* page's text. If the text of "doc B" looks identical to "doc A", you never navigated. Always print the current URL next to the extracted text.
- A link preview showing a Google **Sign in** page only means the fetch was anonymous. Try `mobilebasic` before declaring a document unreadable.
- With OAuth already connected, `docs get DOC_ID` via the google-workspace skill works instead (see `references/google-docs-oauth-access.md`).

### 3. Build the fact matrix, then report in three parts

- List the ~10 comparable facts (date, venue, start/end times, contact, registration rules, age/consent rules, what's provided) and read off the value in each source.
- Report: (a) links → targets table, (b) "kattub kõikjal" — the facts that agree, (c) numbered discrepancies, each with the concrete fix.
- **Separate real conflicts from cosmetic variation.** Two different contact emails or dates = conflict. "kultuurikeskus" vs "kultuurimaja" for the same street address = naming variant; say so instead of padding the conflict list.
- **Report missing info, not just contradicting info.** The most common finding is a fact that exists in one source only (registration/team rules on the website, nothing in the rules doc) — someone reading only one source cannot act.
- Ground volatile claims (official venue name, registry data) with a quick search rather than guessing.

### 4. Write the harmonized master document

- Regenerate from scratch: one section per topic, keep original wording where it is correct, and pick ONE canonical value per conflicting fact.
- **One content format per document.** Bullet lists for rule/info items throughout; do not mix "paragraph with bold inline label" blocks with bullet lists — the user will come back with "vormista X samamoodi nagu kõik ülejäänud". Every section gets the same skeleton: heading + bullet list (numbered list only for an ordered consequence chain).
- Leave deliberate placeholders for facts only the organiser has ("Registreerimise link: lisa siia registreerimislingi aadress"), never dotted fill-in lines or invented values.
- In the chat reply, name **every clause you ADDED that no source contained** and **every value you chose** where sources disagreed (which email became canonical, which venue wording). A silent invention here is the failure mode.

### 5. Deliver paste-ready for Docs

Default when the destination is Google Docs and no OAuth connection exists — ship all three with identical text:

| File | Paste path |
| --- | --- |
| `<name>.html` | Semantic `h1/h2/ul/ol`, minimal CSS (Arial), no colors. Open in browser → Ctrl+A → Ctrl+C → paste into Docs keeps heading/bullet styles. **Recommend this one.** |
| `<name>.txt` | Plain text for Docs' "paste without formatting" (Ctrl+Shift+V). |
| `<name>.docx` | Direct upload / open in Google Docs. |

- Build the source of truth once (a JSON spec for the docx skill), then derive HTML/TXT from the same block list so the three cannot drift. `docx_create.py spec.json out.docx`, then verify with `docx_validate.py` (expect `ok: true`) and `docx_read.py --text` before replying.
- Write to `~/Documents/`, not the scratch dir — the user has to open these files. Deliver with `MEDIA:<absolute path>` lines.
- Mention that text pasted from HTML inherits the browser font; Ctrl+A → *Normal text → Arial* in Docs restores the default look.

## Pitfalls

- Don't re-ask for something the environment can find. "json on downloadsides" → `ls -t ~/Downloads | head -20` locates the file; that beats a clarification round-trip.
- Title-similar documents are not the same document. Compare resolved ids.
- A rules document and its companion form must reference each other (rules mention the consent requirement and link it; the form cites the rules). One-directional references are themselves a finding.
- When reusing an existing form, clean duplicated field lines (a repeated "parent phone" field is a typo, not a design).

## Domain notes

- `references/estonian-event-documents.md` — section skeleton and wording conventions for Estonian youth-event rules + parent consent form.
- `references/google-docs-oauth-access.md` — connecting Hermes to Drive/Docs for direct writes (narrow scopes, wrapper, what the shipped setup script actually supports).
