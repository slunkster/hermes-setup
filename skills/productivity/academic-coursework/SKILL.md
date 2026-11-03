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
  accurate and concrete. Ask them in one `clarify` batch (max 5), not a chain.
- Write in the assignment's language (usually Estonian), natural academic
  register; first person ("mina-vormis") with personal observations when the
  user has a role in the organisation.
- Default deliverable: Word .docx saved to `~/Downloads`, APA-style citations,
  length as the assignment says (verify page count, see docx skill).
- Reply in chat briefly: file path, structure in a few lines, and a short
  "check before uploading" list of any inferred/uncertain facts.

## Procedure
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
   rendered page count.

## Pitfalls
- Use only facts from the user, their files, or sources actually read;
  anything inferred (e.g. a founding year computed from "3 years ago") goes
  into the check-list in the reply. Fabricated org facts are worse than gaps.
- Every grading criterion such as "terminology", "theory linked to concrete
  examples", "discussion and analysis present" needs visible text: name the
  theory terms explicitly and pair each with an org-specific example.
- Weave the user's stated priorities (e.g. which factor is most important)
  into the argument as their judgement — they asked for that emphasis.
- Deadlines are often the same day — don't over-research; one search plus
  the provided materials is usually enough.

See `references/org-environment-analysis.md` for the organisation
external-environment framework (Hatch / Roots) used in management courses.
