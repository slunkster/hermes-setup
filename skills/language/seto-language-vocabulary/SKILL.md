---
name: seto-language-vocabulary
description: Use when working with Seto-language words or word lists.
---

# Seto keele sõnavara

## Allikad (eelistusjärjekorras)

1. **Seto Instituudi koolisõnastik (2020)** – peamine õigekirja- ja sõnavara-allikas.
   - Kohalikud koopiad: `~/seto_sonad/koolisonastik_teemad.pdf` (teemade kaupa), `~/seto_sonad/koolisonastik_tahestik.pdf` (tähestikuline) ning ekstraktid `teemad.txt` ja `tahestik.txt`. Kirje kuju: `eesti sõna – seto vormid (nimetav, omastav, osastav)`.
   - Veebist: https://www.setoinstituut.ee/mis-on-tehtud/seto-keel/ (WordPress Download Manager – otsi lehe HTML-ist `wpdmdl` link kujul `/download/<slug>/?wpdmdl=NNNN&refresh=<token>`).
2. **EKI "Seto sõnastik"** (murdelised kirjed, märksõnaotsing): `https://arhiiv.eki.ee/dict/setosonastik/index.cgi?Q=<sõna>`
3. **EKI "Seto eripäraste sõnade sõnaraamat"**: `https://arhiiv.eki.ee/dict/setoeri/index.cgi?Q=<sõna>`

## Kontrollireeglid

- Õigekiri: järgi koolisõnastikku (seto kiräviis). Ülakoma (') tähistab peenendust, q-d ei kasutata.
- Koolisõnastik on valikuline: eesti keelega identsed sõnad (kala, kass, muna, pall, lumi, kuu, täht, leib) seal puuduvad – neid kontrolli EKI märksõnadest.
- EKI seto sõnastikus puudub palju uuemaid koolisõnastiku sõnu (nt käokiräs, savvusann, kikkasiin) – puudumine EKI-s ei tähenda, et sõna vale on.
- Kui allikad lahknevad (nt truba, kerk), eelista koolisõnastikku või jäta sõna välja.
- PDF-ide tekstiekstrakt: `read_file` annab NeedsOcrError; kasuta pypdf'i venvis `~/seto_sonad/.venv` (`.venv/bin/python`).

## Laste sõnalistid (kasutaja konventsioonid)

- Nõue: seto sõna peab selgelt erinema eesti vasteest (mitte sama ega peaaegu-sama sõna).
- Sihtrühm: kooli 1.–9. klass (mitte 1.–9. eluaastat – kasutaja on selle parandanud). Joonistus peab olema äratuntav.
- Eelista objekte, mille korralik joonistamine võtab üle 5 minuti (detailirohked: mustrid, oksad, palju osi). Liiga lihtsad asjad (üksik mari, kaks kirssi) lükatakse tagasi.
- Kasutaja itereerib sõnalisti – arvesta asendusvoorudega; asendustel säilita numeratsioon ja positsioonid, muuda vajadusel ainult kategooria pealkirja.
- Väljund: nummerdatud nimekiri teemade kaupa kujul "seto – eesti", allikad ja kontroll märgitud; salvesta .txt failina ja anna absoluutne tee.
