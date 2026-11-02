---
name: telegram-to-drive
description: "Use when the user sends a file/photo to file into Google Drive."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [google-drive, telegram, files, receipts, invoices, filing]
    related_skills: [google-workspace, estonian-invoice-compliance]
---

# Telegram → Google Drive

Kasutaja saadab Telegrami (või muu kanali) kaudu faili/foto koos lühikese märkusega,
nt „Algatusruum / arved“, „Välk / tšekid“, „ülikool“. Pane fail õigesse Drive'i kausta
ja vasta lingiga. Vasta eesti keeles, lühidalt.

## Kust fail tuleb

Gateway salvestab iga üleslaadimise kettale (`~/.hermes/cache/documents/…`, pildid ka
`…/native-inputs/`) ja annab sõnumis faili tee. Kasuta seda teed — ära küsi faili uuesti.

## Töövoog

`DRIVE=<selle skilli kaust>/scripts/drive` (VPS: `~/hermes-skills/skills/productivity/telegram-to-drive/scripts/drive`,
Mac: `~/Hermes/hermes-skills/skills/productivity/telegram-to-drive/scripts/drive`).

1. **Sihtkaust.** Märkus → Drive'i tee (`Ülemkaust/Alamkaust`). Segmente sobitatakse
   tõstutundetult, `#` ja emojid ignoreeritakse, unikaalne osaline vaste sobib
   („Algatusruum“ → „#MTÜ Algatusruum“). Kahtluse korral: `sh $DRIVE ls` / `sh $DRIVE ls "Algatusruum"`.
2. **Failinimi.** Telegrami nimed on mõttetud (`file_123.jpg`, `photo.jpg`). Pane kirjeldav nimi
   kujul `YYYY-MM-DD <mis see on>.<laiend>`, nt `2026-10-29 Coop tšekk 23,40 €.jpg`.
   Pildi/PDF-i sisu loe ise (vision / read_file), et nimi ja kuupäev oleksid õiged.
   Arve puhul kasuta arve kuupäeva ja numbrit.
3. **Laadi üles:** `sh $DRIVE up "<fail>" "<tee>" --name "<nimi>"`.
   - Väljund `{"error":…, "candidates":[…]}` (exit 2) → vali kandidaatidest, või kui sobivat
     pole ja kasutaja nimetas selgelt uue kausta, korda `--create`-iga. Ära loo uusi
     ülemkaustu ilma kasutaja selge sõnata — küsi ühe reaga.
4. **Vasta:** „✅ Salvestatud: <nimi> → <kaust>“ + link.

## Kokkulepped

- Ilma märkuseta fail → küsi lühidalt, kuhu panna (paku 2–3 tõenäolist kausta `ls` põhjal).
- Mitu faili korraga sama märkusega → kõik samasse kausta, igaüks oma nimega.
- Arve või tšekk MTÜ/OÜ jaoks: pärast salvestamist võid ühe reaga mainida, kui midagi
  olulist puudub (nt arve number, rekvisiidid) — täiskontroll ainult küsimisel
  (skill `estonian-invoice-compliance`).
- Mitte kunagi kustuta ega teisalda olemasolevaid Drive'i faile.

## Pitfalls

- VPS-il pole `pdftotext`/`pymupdf`/`pypdf`. PDF-i (nt Adobe Scan, millel on OCR-tekstikiht) lugemiseks: `python3 -m venv $TMPDIR/pdfenv && $TMPDIR/pdfenv/bin/pip -q install pymupdf`, siis `pymupdf.open(f)[i].get_text()`. Kui tekstikihti pole, renderda `get_pixmap(dpi=150)` PNG-ks ja vaata pilti.
- „tšekk“ MTÜ jaoks → `Algatusruum/<aasta> majandusaasta/Ostuarved` (seal on alamkaustad Müügiarved/Ostuarved).

- Drive lubab sama nimega faile ühes kaustas — enne üleslaadimist ei pea kontrollima, aga
  kui kasutaja saadab sama faili uuesti, maini, et see on juba olemas.
- Skript otsib Minu Drive'ist ja jagatud draividest; „Minuga jagatud“ kaustu juurtasemel ei näe.
