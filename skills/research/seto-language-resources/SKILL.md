---
name: seto-language-resources
description: Use when finding or verifying Seto (seto kiil) words.
---

# Seto language: word lookup, verification, materials

Seto (seto kiil) is a South Estonian language. Võro is a close relative, useful as a cross-check but never to be passed off as Seto.

## Workflow

1. Pick the direction first. Estonian→Seto spelling and topical vocabulary come from Seto Instituut's "Väike eesti-seto koolisõnastik" (2020) — the thematic edition is fastest when the ask is topical ("words about animals"). Seto→Estonian meaning and proof that a word exists come from EKI's "Seto sõnastik". URLs, download mechanics and interface details: references/sources.md.
2. Verify every word you ship twice: existence/meaning in EKI, spelling in the school dictionary or Seto Instituut texts. For batches run scripts/check_seto_words.py <sõna> ... (prints "Leitud N" plus the headword snippet, and flags extended-search matches).
3. Deliverable conventions (this user; answer in Estonian, plain text in CLI): Seto word first, Estonian gloss after " – "; group by theme; give the list inline AND save a printable plain-text file (current working file: ~/seto_sonad/joonistamise_sonad.txt; report the absolute path); name the sources the words came from. Audience = school grades 1–9 ("klass" — the user corrected "aastased"; never write ages). Only clearly-different pairs qualify: same or near-same words (kass–kass, leib–leib; küpär–kübar, akõn–aken) get rejected. The user also rejects subjects finishable in a minute (single berries, two cherries) — prefer concrete things whose proper drawing has many parts (>5 min). Entries are referenced by number between rounds ("asenda 34, 35, 36"): replace exactly those lines in place, never renumber, and relabel a theme header when a swap no longer fits it.
4. Reuse before rebuilding: verified child-friendly vocabulary is collected in references/child-drawable-vocabulary.md. Extend that file when new words are verified instead of re-deriving lists.
5. When a term is Seto-specific culture (sõlg, tsässon, savvusann, samavar), give a one-clause explanation of what it is — these are the words most worth teaching.
6. Need a Seto-phrased instruction, worksheet or activity name? Copy attested classroom phrasing from Seto Instituut materials (aabitsa töölehed etc.) instead of translating Estonian word by word — see references/sources.md.

## Pitfalls

- setoinstituut.ee downloads sit behind WordPress Download Manager: the button href is '#', and the real URL exists only in the page HTML as /download/<slug>/?wpdmdl=<id>&refresh=<token>. Extract the full link from the HTML and fetch that (recipe in references/sources.md); a guessed ?wpdmdl value or a link stripped of &refresh fails.
- The school dictionary is selective, not exhaustive: very common words that look identical to Estonian (kala, kass, silm, muna, pall) often have no entry. Absence there is NOT evidence a word is wrong — confirm in EKI instead.
- EKI headwords are dialect-phonetic transcription (kaśs, täht́, liplõkõnõ) with usage labels (Se seto, V võro, Kos, Sa, Kov) — good for existence/meaning, never as spelling for public materials. Orthography follows the koolisõnastik / Seto Instituut texts; palatalization is written with ' (kuus', pliin', vikahtkaar').
- EKI's cgi search silently falls back to an extended search when the exact form is not a headword (marker: "?! Küsitud kujul ... kasutan laiendatud otsingut"). Read the marker before reporting a word as found.
- These dictionaries ship as PDFs that can defeat read_file's PDF auto-extract (NeedsOcrError on scanned/mixed pages). Fallback that works: `python3 -m venv .venv && .venv/bin/pip install pypdf`, then extract_text() page by page (thematic koolisõnastik ~31 lk, alphabetical ~19 lk, both layout-clean).
- Seto Instituut materials are free for private/teaching use with correct citation; redistribution for profit is not allowed. Keep the attribution line when passing materials on.
- Words missing from the school dictionary still need a written-form check: attest spelling from other Seto Instituut texts (aabitsa töölehed, aabits), not from EKI's phonetic transcription — printed materials settle things like palatalization marks (pilt/pildi appear unmarked in the töölehed).

## Files
- references/sources.md — full source inventory, exact download and query recipes.
- references/child-drawable-vocabulary.md — verified basic vocabulary for children's materials.
- scripts/check_seto_words.py — batch existence check against EKI Seto dictionaries.
