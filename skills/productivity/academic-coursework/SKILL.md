---
name: academic-coursework
description: Use when writing university homework or essays.
version: 1.0.0
author: Hermes
license: MIT
metadata:
  hermes:
    tags: [homework, essay, university, moodle, citations, apa, estonian]
    related_skills: [docx, pdf, grounded-citations]
---

# Academic coursework (essays, reading assignments, analyses)

## When to Use
For tasks like "tee see kodutöö" with a Moodle screenshot: assignment text,
deadline, grading criteria, attached course PDFs, and a chosen real
organisation/topic the user is personally involved in. Clarify first,
ground in the readings, deliver a cited .docx.

## User preferences (always)
- The user wants MANY clarifying questions before writing, so the work is
  accurate and concrete. Default: one `clarify` batch (max 5). When the user
  explicitly asks for as many questions as possible, run several sequential
  batches (3–4), each informed by the previous answers (e.g. they pick only 2
  of 3 goals → ask for the third; vague "ei tea" → offer concrete handling
  options incl. omit/generalise/write-it-yourself).
- Write in the assignment's language (usually Estonian), natural academic
  register; first person ("mina-vormis") with personal observations when the
  user has a role in the organisation.
- Default deliverable: Word .docx saved to `~/Downloads`, APA-style citations,
  length as the assignment says (verify page count, see docx skill).
- Reply in chat briefly: file path, structure in a few lines, and a short
  "check before uploading" list of any inferred/uncertain facts.

## Procedure
0. Reflective tasks about the user's own studies (study plan, curriculum
   analysis, "vali ained"): fetch the real curriculum from the public ÕIS2 API
   BEFORE asking questions, so choices name actual modules/courses/EAP. Recipe:
   `references/ois2-curriculum-api.md`. Save the module/course dump to
   `~/Hermes/<teema>/` and quote names/EAP from it only.
1. Read the screenshot: deadline, required readings (with page ranges),
   grading criteria, length. Map every criterion to a section later.
2. Quick `web_search` on the organisation so questions are informed.
3. `clarify` batch covering: where the course PDFs are (usually Downloads);
   user's role in the org; org facts (legal form, owners/board, funding
   sources, staff, target group, activities) incl. what they don't know;
   which factors/angles they consider most important + concrete examples
   (multi-select with Other); format/citation/voice.
4. Extract PDFs with pymupdf (`pip install pymupdf`), dump each to a .txt in
   scratch, then `search_files` for the chapter heading. Printed book page
   numbers can differ from PDF page indices — locate the chapter by its
   heading and the printed page number in the text, then read that range.
   Also check user-provided slides/brochures for concrete facts.
5. Get bibliographic data from the title/copyright pages (year of the cited
   edition, publisher). If a course handout prescribes its own citation
   format (e.g. "(Hatch 2006, Rosenberg 2011 kaudu)"), follow it exactly.
6. Outline: intro (define the org + user's role) → theory frame from the
   readings → apply each framework layer with concrete org examples →
   discussion/analysis (not just description) → conclusion tying to the
   larger course project → references.
7. Generate the .docx with python-docx (Times New Roman 12, justified,
   hanging-indent reference list, italic titles), then verify word count and
   rendered page count. If python-docx is unavailable, write minimal OOXML
   (`[Content_Types].xml`, `_rels/.rels`, `word/document.xml`) with zipfile.
   Page count via installed Word (works headless-ish):
   `osascript -e 'tell application "Microsoft Word"' -e 'set d to open file name (POSIX file "<path>" as text)' -e 'delay 2' -e 'set n to (compute statistics d statistic statistic pages)' -e 'close d saving no' -e 'return n' -e 'end tell'`.
   A "≤1 A4" free-form reflection fits at ~330–420 body words in TNR 12,
   single spacing, 2–2.5 cm margins.

## Pitfalls
- Use only facts from the user, their files, or sources actually read;
  anything inferred (e.g. a founding year computed from "3 years ago") goes
  into the check-list in the reply. Fabricated org facts are worse than gaps.
- Every grading criterion such as "terminology", "theory linked to concrete
  examples", "discussion and analysis present" needs visible text: name the
  theory terms explicitly and pair each with an org-specific example.
- Weave the user's stated priorities (e.g. which factor is most important)
  into the argument as their judgement — they asked for that emphasis.
- When the user says "ära maini" for a part the brief asks for, omit it from
  the text (don't invent a placeholder) and flag in the reply which brief
  question is now unanswered and whether it was conditional ("kui kavatsed…")
  or mandatory — they decide the risk.
- Sensitive personal facts (health etc.): ask whether and how generally they
  may appear, offering a generic phrasing; use exactly the approved wording.
- Choices you made for the user (e.g. which electives fill a required EAP
  quota) go into the reply's check-list as your pick, with the reason.
- Deadlines are often the same day — don't over-research; one search plus
  the provided materials is usually enough.

See `references/ois2-curriculum-api.md` for pulling TÜ curricula
(modules, courses, EAP) from ÕIS2 without login.

See `references/org-environment-analysis.md` for the organisation
external-environment framework (Hatch / Roots) used in management courses.
