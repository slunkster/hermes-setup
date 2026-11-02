---
name: estonian-book-access
description: "Use when finding an Estonian book for free, legally."
---

# Finding an Estonian book free & legally

Estonian users often ask for a "tasuta versioon" of a course textbook. Deliver legal routes first — library borrowing is usually the fastest free option. Never give pirate links; if no legal free full text exists, say so plainly.

## Workflow
1. Identify the book: title, author, year, publisher, ISBN (Apollo/vanaraamat/ESTER listings).
2. ESTER = catalogue of all Estonian libraries:
   - URL pattern: `https://www.ester.ee/search~S1*est/?searchtype=X&searcharg=<query>&searchscope=1&SORT=D` (`searchtype=i` for ISBN). `search.ester.ee` errors in browser — use classic `www.ester.ee`, JS/browser required.
   - Record page "Eksemplarid" table = every copy in every library + status: KOHAL = on shelf, TÄHTAEG dd.mm.yy = on loan, KOHALKASUTUS = in-house only, REMONDI AJAKS PAKITUD = packed for repair, KADUNUD/MAKSTUD = lost. Extract via `js("[...document.querySelectorAll('table')].map(x=>x.innerText).join('\\n')")` — it's huge, print only tail/chunks.
   - Permalink form: `https://www.ester.ee/record=bXXXXXXX*est`.
3. Digital full text: record may link "TÄISTEKST ... ETERA" (etera.ee, TLÜ Akadeemiline Raamatukogu). Check the access label: "TLÜ/TLÜAR võrgus või sisselogides (TAAT)" = TLÜ network/login only (TAAT login page = TLÜ account) — not for other universities' students.
4. Accessible formats: veebiraamatukogu.ee (Eesti Pimedate Raamatukogu) lends DAISY audio of many Estonian books — ONLY to registered print-disabled readers (admin approves account); same content as mp3 CDs via RaRa.
5. Internet Archive: check `https://archive.org/metadata/<id>`. If collections include `internetarchivebooks`/`printdisabled` with `access-restricted-item: true`, the page often says "Borrow Unavailable — Book available to patrons with print disabilities" → NOT generally borrowable. Always read the actual borrow button, don't assume.
6. Second-hand (paid, out-of-print textbooks are scarce, ~20–60 €): osta.ee (blocks curl/bot — open in a real browser), vanaraamat.ee (ootenimekiri = notify list), kirjavara.ee, raamaturead.ee, raamatukoi.ee, yaga.ee, FB groups "Raamatud".
7. Free study aids around a textbook: annaabi.ee konspektid, Quizlet decks; suggest asking the lecturer/Moodle for scanned chapters. ESTER "Telli digikoopia" = paid digitization service.

## Notes
- TÜ students (incl. Viljandi kultuuriakadeemia) borrow from any TÜR branch free; TÜR often holds many copies (2. saal, haridusteaduste instituut, kolledžid).
- Statuses and copy counts change — always present as "hetkeseisuga".
