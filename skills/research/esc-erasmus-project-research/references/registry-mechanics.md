# Registry mechanics — kaart.noored.ee and the EU platforms

## kaart.noored.ee (Estonian agency project map)

Bulk dataset (fastest filter path):

```bash
curl -sL "https://kaart.noored.ee/wp-json/mapData/v1/projects" -o all_projects.json
```

Each item: `{id, lat, lng, permalink, pinContent, ...}`; `pinContent` is HTML with:
- domain: `map-infowindow__head` → Noortevaldkond / Haridusvaldkond
- org: `map-infowindow__subtitle`
- title: `map-infowindow__title`
- tags: `map-infowindow__tag` spans → e.g. `2024`, `solidaarsusprojektid`, `Euroopa Solidaarsuskorpus`
- project id = the pin `id`; detail page `https://kaart.noored.ee/projektid/arc_<id>/`

Python filter (all name variants at once):

```python
import json, re, html
d = json.load(open("all_projects.json"))
def parse(pin):
    c = pin["pinContent"]
    g = lambda p: html.unescape(re.sub(r'\s+', ' ', re.search(p, c, re.S).group(1)).strip()) if re.search(p, c, re.S) else None
    return {"id": pin["id"],
            "org": g(r'map-infowindow__subtitle">\s*([^<]+)'),
            "title": g(r'map-infowindow__title[^>]*>\s*([^<]+)'),
            "tags": [html.unescape(t.strip()) for t in re.findall(r'map-infowindow__tag">\s*([^<]+)', c)]}
rows = [parse(p) for p in d]
hits = [r for r in rows if any(v in (r["org"] + " " + r["title"]).lower() for v in ["huub", "edutegur"])]
```

UI search (for the user-visible row set): `?search=<term>&order=DESC&meta_key=aasta&paged=1` then click „Otsi"; toggle „Nimekiri". Rows: `tr.table__row` (cells: aasta, organisatsioon, projekti nimi, asukoht, programm, tegevus, prioriteet, summa) + `button[data-project]`.

Detail-card extraction after `arc_<id>/` load: find `Sulge` in `document.body.innerText`; fields below it in order: org, title, year, activity, programme, KOORDINAATORI ASUKOHT, TOIMUMISE AEG, TOETUSE SUMMA, OSALEJATE ARV, PROJEKTIKOOD, description, then XLS/PDF download links.

Field quirks:
- „Projekti nimi" for ESC volunteering rows = one shared label per call round (2021/22: „Vabatahtlik teenistus"; 2023 and 2024 rounds: a single unrelated project name repeated on all rows). Not a per-project title.
- The XLS list export can be a corrupt/truncated .xls (`xlrd` cannot open it; it handles legacy .xls only anyway). `file=csv` is unsupported — returns the site HTML.
- Org names appear as currently registered; no registry code column exists, so name-variant search is the only key.

## EU platforms

- ESC: `youth.europa.eu/solidarity/projects` — search only via the UI input (placeholder „Example employment, climate change, etc…"); results URL gets `&domain=esc2021&view=list&keyword=<q>`. Direct navigation to that URL may return „403 − Disallowed by robots.txt"; the in-UI submit works.
- Erasmus+: `erasmus-plus.ec.europa.eu/projects/search` (same interaction pattern, `domain=eplus2021`).
- Project card: „Project Reference", dates, EU Grant, Action, Topics, summary + „Host" block (implementing org, address, phone) — use Host to confirm attribution. Detail URL: `/solidarity/projects/details/<CODE>_en`.

## Project-code anatomy (EE, observed)

`YYYY-R-EE01-<ACTION>-<number>`; EE01 = Estonian national agency. Observed actions:
- `ESC30-SOL` — solidarity projects (2022→)
- `ESC31` — 2020 local solidarity projects
- `ESC51-VTJ` — volunteering projects
- `ESC50-QLA` — Quality Label references
- `KA347` — Erasmus+ youth participation projects („noorte osalusprojektid")

## Organisation identity

- ariregister.rik.ee gives registry code + status by code.
- inforegister.ee / ssb.ee / corpinfo show „Former names", contacts, EMTAK — use to link a former name to the same registry code before attributing old projects.
