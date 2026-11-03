---
name: quick-capture
description: "Use when the user dumps a quick note/voice memo of things to do or remember."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [capture, voice, todoist, calendar, ideas, gtd]
    related_skills: [homme, telegram-to-drive]
---

# Kiirmärge → õigetesse kohtadesse

Kasutaja ütleb/kirjutab lennult mitu asja korraga (sageli häälsõnum, TalTechi mudel kirjutab
sõna-sõnalt: „neliteist nelikümmend viis“ = 14:45, „homme“ = kuupäev Europe/Tallinn järgi).
Lõhu see eraldi kirjeteks ja pane igaüks õigesse kohta. **Ära küsi kinnitust iga asja kohta** —
tee ära ja raporteeri lühidalt; küsi ainult siis, kui mõni asi on päriselt mitmeti mõistetav.

## Kuhu mis läheb

| Liik | Tunnus | Sihtkoht |
|---|---|---|
| Tegevus | „helista“, „saada“, „tee“, „vaata üle“ | **Todoist** (`add-tasks`), sobiv projekt: Töö (Setomaa kool/SNK/noortekeskus), HUUB, MTÜ (Algatusruum), Välk (Välk Meedia), Ülikool, muu → Inbox |
| Ostmine | „osta“, „vaja on …“ | **Todoist Inbox**, silt `ostud`, sisu nt „Osta: lambipirn“ |
| Kindel aeg/kohtumine | kellaaeg + koht/inimene, „ole …“, „kohtun …“ | **Google'i kalender**: tööasjad → „Töö - SNK“ (`<WORK_CALENDAR_ID>@group.calendar.google.com`), muu → `you@gmail.com`. Vaikimisi kestus 30 min, kui pole öeldud. |
| Mõte / idee | „mõte“, „idee“, „äkki võiks“, „jäta meelde, et …“ ilma tegevuseta | **Google Doc „Hermes – mõtted ja ideed“** (`<SHEET_ID>`) — lisa lõppu rida `PP.KK.AAAA — <mõte>` |
| Fakt minu kohta | eelistus, inimene, harjumus | Honcho/mälu (`honcho_conclude` või memory) — mitte Todoisti |

Tähtaeg ilma kellaajata („reedeks“) → Todoisti `dueString`, mitte kalendrisse.

## Käsud (VPS)

```bash
P=$(ls -td ~/.hermes/installs/*/environments/*/venv | head -1)/bin/python
G=~/.hermes/skills/productivity/google-workspace/scripts/google_api.py
$P -W ignore $G calendar create --summary "…" --start 2026-10-30T14:45:00+02:00 --end 2026-10-30T15:15:00+02:00 --location "…" --calendar <id>
$P -W ignore $G docs append <SHEET_ID> --text "
29.10.2026 — <mõte>"
```
Todoist: MCP-tööriist `add-tasks` (kui MCP pole laetud: `~/Hermes/paevaulevaade/todoist_mcp.py add-tasks '<json>'`).
Projekti-ID-d (säästa `find-projects` kutse): Inbox `6GXCVgVgFWhj8wcH`, Töö `6hWGX97Qg2cjQvvg`, HUUB `6hcQFmVVjQ56Q4w5`, MTÜ `6hfXgpRq5mvMWjhM`, Välk `6hfXwmpCHQ4RCqmv`, Ülikool `6hfjGqRvx8Pm7XM2`. „Pane töö alla“ = projekt Töö.
Üritus mitme ettevalmistusega („laat: plakat + Stuudium + FB event“) → üks emaülesanne ürituse nimega (kirjeldusse „Toimub PP.KK.AAAA“) + iga tegevus alamülesandeks (`parentId`); tähtaeg pane nii emale kui alamatele.

Kui `mcp__todoist__*` on kadunud (gateway logis `OAuthNonInteractiveError` → server „parked“): OAuth aegus, kasutaja peab tegema `hermes mcp login todoist`. Ära kasuta asenduseks hostitud `connectors__todoist_mcp__*` tööriistu — see on eraldi ühendus, mis nõuab uut autoriseerimist. Kui `~/.hermes/mcp-tokens/todoist.json` mtime on värske (kasutaja juba logis sisse), tee töö kohe ära `todoist_mcp.py` kaudu või otse JSON-RPC-ga (retsept: skill `hermes-vps-hosting`, fail „services-on-vps“, lõik „When an MCP OAuth login expires“); gateway võtab uue tokeni ise üles 5 min probe'iga.
Ajavöönd: suveaeg +03:00, talveaeg (okt viimasest pühapäevast märtsi lõpuni) +02:00.

## Vastus

Üks lühike plokk, iga kirje üks rida koos sihtkohaga, nt:
```
✅ 3 asja:
• 📞 Helista Martale matka asjus — Todoist / HUUB, homme
• 🛒 Osta: lambipirn — Todoist / ostud
• 📅 Värska Coop 14:45 — kalender (isiklik), N 30.10
```
Kui midagi jäi segaseks, lisa lõppu üks küsimus.

## Pitfalls
- Todoisti `add-tasks` + `deadlineDate` jätab ülesande vaikselt lisamata → kasuta ainult `dueString`; kontrolli `successCount`.
- Kellaajaga ülesande ümberajastamisel anna `YYYY-MM-DDTHH:MM:SS`, muidu kaob kellaaeg.
- Pärast südaööd (u 00–05) tähendab „homme“ tavaliselt **tänast kuupäeva** (järgmist ärkvelolekupäeva) — pane see kuupäev ja maini raportis kuupäeva selgelt (nt „R 30.10“).
- Ära lisa sama asja kahte kohta (kalendrisse JA Todoisti) — kas aeg või tegevus.
- Vana Google Doc „Mõtted“ on projektitaotluse mustand — sinna **mitte** kirjutada.
