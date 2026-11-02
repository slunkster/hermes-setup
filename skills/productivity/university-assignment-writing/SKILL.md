---
name: university-assignment-writing
description: "Use when drafting a university assignment from a rubric."
---

# University assignment writing (Estonian, rubric-driven)

For the user's Tartu Ülikool course tasks such as "pick a problem in your community, find ≥4 sources, write ≤1 A4 incl. personal connection, format and cite correctly". Language: Estonian. Pair with `grounded-citations` for source verification and `estonian-proofreading` for the final pass.

## Procedure

1. **Read the brief and the rubric image first.** List the scored criteria (number/fit of sources, personal connection, depth of problem description, formatting/APA). Map every section of the draft to one; personal connection and description carry the most points.
2. **Propose 1 main topic + 2 alternatives, ranked by source availability** (peer-reviewed + official). Run a quick search per candidate before recommending; say plainly which topics have only grey literature. Re-offer alternatives if the user rejects the main topic (e.g. wants it unrelated to a given theme).
3. **Honour the user's source constraints** (e.g. year ≥ 2021, mainly one named document such as the municipality's latest development plan). Apply the year filter to every source; flag any exempt classic (e.g. a book the brief itself cites) as such.
4. **Source hunt in parallel** (subagents by source type, see `grounded-citations`), then pull the primary document to disk and grep it for the user's requested angles; cite with page numbers.
5. **Draft to `~/Hermes/<topic>/mustand.md`**: problem statement + theory anchor, source list in APA 7, body with inline (Author, year, lk n) citations. Measure the body only (exclude headings and the source list) with a short Python count; report the total and the per-paragraph counts. You cannot verify a printed A4 fit — say so and let the user check in Word. For "make it ~N% shorter", cut whole sub-claims from the longest paragraphs, keep every source still cited in the text, and report the percentage achieved.
6. **Personal connection is the user's to write.** Insert explicit `[LISA: …]` placeholders asking for concrete examples; fill in only facts the user stated (home region, workplace/role). Never invent anecdotes or feelings.
7. **Mark own inference vs source claim.** When the user wants an angle the source does not state (e.g. "schools may close", "community leaders are ageing"), write it as the author's hedged reasoning and cite only the facts that support it. Tell the user which of their hypotheses the sources contradict or only partly support.
8. **Pre-submit checklist to the user:** items not checked at source (classic book publisher, DOIs, figures read from tables/images), draft status of cited documents — use the reference form the user asked for (see Pitfalls) and keep the "eelnõu"/adoption caveat in your chat summary, registers that disagree (state source + date for every figure; never mix series), then offer .docx/PDF export.

## Pitfalls

- Do not state which way a trend goes from a search snippet; read the table (see `grounded-citations`). Municipal data may show growth in one indicator and decline in another — present both.
- A requested but undocumented claim (e.g. leader ages, unemployment when the document only says labour shortage/low pay) must be reworded to what the source actually says.
- Sources the user excluded by year stay out; list older ones separately as optional rather than including them silently.
- Keep chat replies compact; put the full text in the file and summarise verified vs unverified.
- Render and visually inspect the submitted PDF before flagging broken paragraphs, split references, duplicated headings, or broken URLs: extraction can insert false paragraph boundaries and truncate detected links. A line-wrapped URL is not automatically malformed. Check page dimensions rather than assuming the paper is A4, and distinguish missing PDF link annotations from an invalid URL. Under APA 7, check italicised standalone titles and hanging indents; do not demand publisher locations or page numbers for every paraphrase.
- Never assert a requirement the rubric does not state (voice, section order, length, allowed source types). Read the criteria rows; when the user asks whether something is required, quote the row. Claiming a non-requirement makes the user rework text that was already in line with the brief.
- Follow the user's reference form for a named document. If they want "arengukavas" rather than "arengukava eelnõus", write their wording in the deliverable and keep the adoption-status caveat in your summary — do not silently re-add the qualifier they removed.
- When the user supplies their personal facts mid-task, write the personal section from those facts only, and in your reply mark which sentences are your formulation rather than their experience so they can adjust. Say that the concrete example the rubric rewards still has to come from them.
- Reading Estonian plans and statistics for the body of the text: see `estonian-municipal-documents`.
