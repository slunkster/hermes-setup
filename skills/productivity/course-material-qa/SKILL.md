---
name: course-material-qa
description: Use when answering exam/study questions from course files.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [exam, study, university, estonian, course-materials]
    related_skills: [academic-coursework]
---

# Answering study/exam questions from course materials

## When to Use
User asks a question about a course (e.g. arengupsühholoogia) and has said
answers must come from the course materials, not general knowledge.

## Rules
- Answer ONLY from the course files. Cite which file (and slide/page) each
  point comes from, briefly.
- If the materials don't cover it or are ambiguous, say so plainly
  ("materjalides ma seda ei leidnud / pole kindel"). General knowledge may be
  added only if clearly labelled as not from the course.
- If sources disagree (e.g. lecturer's konspekt vs textbook), show both;
  the lecturer's own konspekt/slides take priority for the exam.
- Reply in Estonian, exam-friendly: short core answer first, then key terms.
- Multiple-choice questions: bold the chosen option first, then 1–3 bullets
  (justification with source; why each tempting wrong option is wrong), then
  "Kindlus: kindel / pigem kindel / ei tea". Keep it that short — the user
  fires questions rapidly while studying. If the materials' wording is more
  precise than the option (e.g. chromosome disorder vs "geenirike"), still
  pick the best option but note the nuance in one line. If several options
  are true or none match the materials, say so.
- When the materials give two formulations for the same concept (e.g. the
  konspekt's own label vs a theory's standard stage name), give both and a
  conditional pick: "if option X is offered choose it; otherwise Y" — the
  user sees options you don't, so a decision rule beats a single guess.

- Test questions are often near-verbatim sentences from the lecturer's
  konspekt or course handouts: search for the question's own phrase first; a
  verbatim match is the strongest evidence. Watch for distractors that swap
  two terms (e.g. ontogenees/fülogenees).

## Procedure
1. Read the course README for the file index (below).
2. `rg -i` in the `tekst/` folder with one distinctive keyword per answer
   option in a single alternation (e.g. `"turner|neerupealis|urikeem"`) —
   one search usually locates every option's passage. The scanned textbook
   OCR lacks diacritics, so also search ä→a, õ→o, ü→u, ö→o forms; search
   the stem, not the whole word (Estonian case endings vary).
3. Check the lecturer's own konspekt and slides first, then the user's own
   graded self-study answers (lecturer-set questions recur on the exam): test options are
   typically lifted near-verbatim from them, so an exact wording match is
   strong evidence. Distractors are usually real course terms from an
   adjacent topic (e.g. a Piaget stage offered as a prenatal stage, Jung's
   "alateadvus" twisted into a Freudian claim) — name that mismatch.
4. Read surrounding context (`sed -n 'A,Bp'` or read_file with offset)
   before answering; `rg` truncates long docx-paragraph lines, so print them
   with `rg -o ".{200}term.{200}"`.
5. If the question arrives without options, it is usually a sentence stem
   copied from the materials ("… on:", "… seepärast, et:") — search the
   stem's distinctive words, complete it with the materials' own wording,
   name confusable nearby alternatives, and say which option to pick.
6. If a file was added later to ~/Downloads, convert it first: soffice
   --headless --convert-to "txt:Text (encoded):UTF8" for doc/docx/rtf;
   pptx → pdf with soffice, then `pdftotext -layout`. Slide image text is not
   extracted — mention that if an answer may be on an image.

## Courses
- Arengupsühholoogia (Kalle Küttis, TÜ, 2026): ~/Hermes/arengupsuhholoogia/
  README.md + tekst/. Exam is multiple choice (user's info; the konspekt says
  written test + oral). Questions match Küttis' lühikonspekt, slides and the
  period handouts near-verbatim. Mangs & Martell textbook is required
  reading but NOT in the files.
