# Estonian and Russian subtitle proofreading checks

Two lists: what to fix, and what looks wrong but must be left alone.

## Estonian - real errors to fix

- Impersonal/modal constructions take a **partitive** object:
  `Kas vaikivad pealtvaatajad ... võib lugeda` -> `Kas vaikivaid pealtvaatajaid ... võib lugeda`.
  Same pattern with `saab / tuleb / peaks + da-infinitiiv`.
- A quantifier must agree with a partitive object: `kõik neid pilte ... ei saa` ->
  `kõiki neid pilte ... ei saa` (negation forces the partitive object, so the
  quantifier goes partitive too). Contrast `Kõik tuleb alles hoida.`, which is
  correct: there the nominative is the subject of the modal construction.
- Doubled case marker: `samad, millega kiusamisega tegeletakse` ->
  `samad, millega kiusamise puhul tegeletakse` (one `-ga` too many).

## Estonian - looks wrong, is not

- `on` is identical in singular and plural, so `... jama on väga päris ja avaldavad
  väga päris mõju ...` is fine: the only number-marked verb agrees with the
  compound subject. Never "fix" `on` by adding plural.
- Singular verb after a numeral: `Uuringus osales 31 riiki`, `99% videotest kujutab
  naisi`, `58% ... on kogenud`, `69% ... ei tee`.
- Correlative negation: `ei mõtle ei sellest inimesest ega olukorrast` is standard.
- `kuidagi teisiti / teistmoodi` ("somehow differently") is idiomatic, not a
  pleonasm.
- Spoken-language features to leave intact: `ja ... ja ...`, resumptive word order,
  self-corrections (`pildi... vabandust`), the `sa`/`teie` switch, sentence
  fragments. Fix only what is ungrammatical, not what is merely spoken.

## Russian - real errors to fix

- `-тся` / `-ться`: check against the subject, not by eye.
- Agreement with `большинство / часть / 90%`: a plural predicate is acceptable when
  the quantifier has a plural dependent (`большинство из них сделаны`); singular is
  the book norm. Do not rewrite for style.
- Case after negation (genitive vs nominative with generic `не + verb`): both
  occur; change only clear mismatches.
- Grepping Cyrillic from the shell can raise homoglyph/Unicode warnings; expected,
  not an attack.

## Russian - looks wrong, is not

- `Молчание - тоже не согласие.` and separated `не` in `это не нормально` are
  normal colloquial contrast.
- `%` + plural verb (`97% ... пользуются`) is correct for countable nouns.
- Calques carried over from the source language (e.g. `очень реально влияют`,
  `который это видит, против этого, но не решается`, bare `пусть` for `las olla`)
  are awkward but grammatical: report them as notes, never rewrite silently.

## Cross-language fidelity

- Read the target text against the source cue by cue and report drifts
  (`tausta kohta valetama` -> `о себе`, `ei saada raha` -> `не заплатит`) as
  observations; only the user decides whether a translation should change.
- Confirm the two files' cue counts and timings are identical before reporting.
