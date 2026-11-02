---
name: homme
description: "Use when asked for a day overview (homme/täna)."
version: 1.0.0
---

# Homme — päevaülevaade kõigest

Kasutaja kirjutab lihtsalt `/homme` (või „homne ülevaade“, „mis mul homme on“). Ülevaade võtab kokku kõik kalendrid, Gmaili, Outlooki (töö + TÜ), Moodle'i ja Todoisti. Vasta **eesti keeles**. Vaikimisi sihtpäev = homme (Europe/Tallinn); kui kasutaja ütleb „täna“ või kuupäeva, kasuta seda. Kõik on **AINULT LUGEMINE** — ära muuda sündmusi, kirju ega ülesandeid ilma eraldi loata.

## 0. VPS-il (Linux, Telegrami Hermes) — teine kogumisskript

Kui `uname` = Linux (VPS), siis `collect.sh` ei tööta. Kasuta:
```bash
bash ~/.hermes/scripts/homme.sh [YYYY-MM-DD]   # vaikimisi täna; ~5 s; prindib kompaktse teksti otse
```
Kogub Google'i kalendrid + Moodle/ÕIS 14 p, Gmaili, Todoisti (VPS-i oma token) ja Outlooki/TÜ meili `ssh mac` kaudu. Kui väljundis on `MAC_UNREACHABLE`, ütle ühe reaga, et Outlooki/TÜ meile ei saanud lugeda (Mac magab). Exchange/TÜ kalendrid (ekcal) VPS-ist ei tööta. Igahommikune 08:00 cron-töö annab selle väljundi juba prompti — ära kogu uuesti. Hommikul kell 8 on sihtpäev = **täna**. Õhtune 22:00 cron („Õhtune homse eelvaade“, skript `homme_ohtu.sh` = homme.sh homse kuupäevaga) annab max 3-lauselise eelvaate: päeva algus + väljasõiduaeg, põhisündmused, tähtajad.

## 1. Kogu andmed ÜHE terminalikutsega paralleelselt (kiireim; agente pole vaja) — Macis

```bash
bash ~/Hermes/paevaulevaade/collect.sh YYYY-MM-DD [+02:00]   # ~5 s, kõik allikad paralleelselt
```
Teine argument = ajavöönd (vaikimisi +03:00 suveaeg; talveajal — okt viimasest pühapäevast märtsi lõpuni — anna `+02:00`). Toored väljundid tulevad `$TMPDIR/homme/`: `gcal.json` (sihtpäev + järgmise päeva hommik), `gcal14.json` (14 p — ainult Moodle'i/tähtaegade jaoks), `ekcal.json`, `outlook.txt`, `gmail.json`, `gmail_unread.json`, `todoist.json`. Loe need ühe `read_file`/execute_code partiina ja tõmba välja ainult vajalik. Terminali-tööriist keelab `&` esiplaanil — seetõttu on paralleelsus `collect.sh` sees.

- **Google-kalendrid** (`calendar_all.py`): kõik 16+ kalendrit, sh Moodle (nimi „Moodle“, iCal-import), ÕIS2 tunniplaan, Võru HUUB, Todoist, SNK.
- **Maci kalendrid** (`ekcal`, EventKit; allikas `ekcal.swift`): Exchange (töö work@example.org), student@ut.ee, iCloud. Google'i sündmused korduvad siin → arvesta ainult mitte-Google kontosid.
- **Outlooki meil** (`outlook_mail.js`, Mail.app): töö (konto „Exchange“) + ülikool („student@ut.ee“). Mail.app peab töötama — kui viga/tühi, käivita `open -g -a Mail`, oota 20 s, proovi uuesti.
- **Gmail**: you@gmail.com. Olulise kirja täistekst → `$GAPI gmail get ID` (mitmeosalise kirja sisu võib tulla tühi → loe Gmail API-ga otse).
- **Todoist**: projektid Inbox, Töö, HUUB, MTÜ, Välk, Ülikool. `todoist_mcp.py` uuendab tokenit ise.

## 2. Ülevaate vorm (lühike, tegevuspõhine)

0. **🌦 Ilm** (ainult VPS-i väljundis, sektsioon „ILM JA LIBEDUS“) — üks-kaks rida kodu (Treski/Värska) kohta: ilm, temperatuur, sademed, hommikune temperatuur. Kui real on `⚠️ LIBEDUSE OHT` või Ilmateenistusel on hoiatus → too see esile esimesena. Kui kalendris on täna üritus **Tartus** (~1 h 15 min sõitu) või **Viljandis** (~2 h 15 min, nt Posti 1 loengud), lisa selle linna ilm ja meeldetuletus, millal hiljemalt välja sõita (+15 min varu, libeduse korral +30 min). Teeolude (Tark Tee) andmeid pole — ära neid välja mõtle.

1. **📅 Kalender** — tabel kronoloogiliselt, terve päeva sündmused ees; kattuvused/tihedad üleminekud; kalendri nimi sulgudes. Järgmise päeva hommik lühidalt.
2. **🎓 Ülikool** — Moodle'i tähtajad järgmise 14 p jooksul (UTC → kohalik aeg!), ÕIS2 tunnid, TÜ meilid mis nõuavad tegevust.
3. **✅ Todoist** — homme / täna tegemata / üle tähtaja (projekt sulgudes).
4. **✉️ Meilid** — kolm postkasti koos, tähtsuse järgi: homset puudutavad → vastust vajavad (kellelt, mida, 1 rida soovitust) → info. Märgi postkast (Gmail/Töö/TÜ). Uudiskirjad ja teavitused ainult arvuna.
5. **💡 Soovitus** — kuidas vaba aega kasutada; seo meilid ülesannetega (nt Todoisti „Helista X“ ↔ vastav meililõim).
6. Kui mõni allikas ebaõnnestus, ütle see ühe reaga.

Lõpus paku 1–2 konkreetset tegevust (ülesande ümbertõstmine, vastuse mustand) — tee need alles kinnitusel.

## Pitfalls
- Kalender „Pere“ = pereühine kalender, sealsed sündmused EI OLE Siimu omad → jäta ülevaatest välja (VPS-il filtreerib `collect_vps.py` EXCLUDE_CALS juba ise).
- Moodle'i aeg tuleb UTC-s (21:59Z = 23:59 talveajal / 00:59 suveajal).
- `timeout` puudub Macil → kasuta `perl -e 'alarm N; exec @ARGV'`.
- Todoisti `reschedule-tasks` ainult kuupäevaga kaotab kellaaja — kui ülesandel oli kellaaeg, anna `YYYY-MM-DDTHH:MM:SS`.
- Todoisti `add-tasks` koos `deadlineDate`-iga jätab need ülesanded vaikselt lisamata (ilmselt plaan ei toeta) → kasuta ainult `dueString`, tähtaeg kirjeldusse; kontrolli alati `successCount`.
- Kalendrisse lisamisel: tööasjad → Google'i kalender „Töö - SNK“, muu → you@gmail.com; konkreetsed tegevused → Todoist. Moodle'i tähtaegu kalendrisse ära dubleeri (Moodle'i kalender on juba olemas).
- Todoisti filter ei toeta `deadline: next N days`; kasuta `deadline before: YYYY-MM-DD`.
- `ekcal` vajab kalendriõigust; kui `no calendar access`, anna Terminalile/Hermesele õigus (Süsteemiseaded → Privaatsus → Kalendrid).
