# Riigi Teataja (Estonia) - retrieving current law

`riigiteataja.ee` is the official register: every act, every redaktsioon, plus
consolidated (terviktekst) versions. The public site is an Angular app, so the raw
HTTP response is a ~51 KB shell with no law text in it. Its JSON API serves the text.

## API (verified working)

Base: `https://www.riigiteataja.ee/public-api/api/v1`

| Endpoint | Returns |
|---|---|
| `/akt/lyhendid` | JSON list of all acts: `{id, lyhend, pealkiri}` - the current id for each abbreviation |
| `/akt/{id}` | metadata for that id (`kehtivId`, `grupiId`, `lisaAadress`, ...) - treat `kehtivId` as advisory, see the version recipe below |
| `/akt/{grupiId}/redaktsioonid` | every version of an act: `{redaktsioonid: [{id, kehtivuseAlgus}...], kehtivRedaktsioon: <id>}` - the reliable current-version anchor |
| `/akt/{id}/blob-html` | full current consolidated text as HTML |
| `/akt/{id}/blob-xml` | same as XML |

`curl` needs a browser-ish UA; send `-A 'Mozilla/5.0'`. A bad id shape returns
`400 "aktId ei ole valiidne"`; an old-but-valid id silently returns that OLD
redaktsioon.

### Resolve the current id, then fetch (copy-paste)

```bash
curl -s -A 'Mozilla/5.0' 'https://www.riigiteataja.ee/public-api/api/v1/akt/lyhendid' -o /tmp/lyhendid.json
python3 -c "import json;print([a for a in json.load(open('/tmp/lyhendid.json')) if a['lyhend'] in ('LS','VTMS','KarS','KarRS')])"

ID=111072026044   # from the step above
curl -sL -A 'Mozilla/5.0' "https://www.riigiteataja.ee/public-api/api/v1/akt/$ID/blob-html" -o /tmp/act.html
```

### Any act's current version - incl. KOV määrused (no abbreviation)

Municipal (KOV) regulations carry `lyhend: null` and have no row in
`/akt/lyhendid`; find one with a search (`site:riigiteataja.ee`) and take the id
from the hit. From any id the whole version history is one call away:

```bash
# id from a search hit -> group id -> version list -> current version text
GID=$(curl -s -A 'Mozilla/5.0' "https://www.riigiteataja.ee/public-api/api/v1/akt/$ID" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['grupiId'])")
curl -s -A 'Mozilla/5.0' "https://www.riigiteataja.ee/public-api/api/v1/akt/$GID/redaktsioonid"
#   -> {"redaktsioonid": [{id, kehtivuseAlgus, ...}, ...], "kehtivRedaktsioon": <id>}
curl -sL -A 'Mozilla/5.0' "https://www.riigiteataja.ee/public-api/api/v1/akt/$KEHTIV/blob-html" -o act.html
```

- A one-entry `redaktsioonid` list means the act has never been amended.
- Do not trust the per-act `kehtivId` on an old id: it can echo the id you
  requested while a newer redaktsioon exists (a text whose successor had been in
  force for years still served as "current"). Reliable checks: `kehtivRedaktsioon`
  from the list, and the blob header line `Sõnastuse kehtivuse lõpp:` - it reads
  `hetkel kehtiv`, a past date, or `kehtetu`. A repeal-only final version may still
  be the list's `kehtivRedaktsioon`; if its body says `Kehtetu`, look up the
  replacement act rather than treating the old act as currently operative.
- Reading a dated document under the law of its time: from the same list take the
  version with the largest `kehtivuseAlgus` not after the document's date and fetch
  it by id - that is the contemporary wording of a section that has since moved.
- Finding unlisted API endpoints (how `redaktsioonid` was found): load the act page
  in a real browser and read `performance.getEntriesByType('resource')` - the SPA's
  own JSON calls are listed there.

### Turn it into greppable text

```python
import re, html
raw = open('/tmp/act.html', encoding='utf-8', errors='replace').read()
t = re.sub(r'<[^>]+>', ' ', raw)
t = html.unescape(t)
t = re.sub(r'\s+', ' ', t).replace('balance history link', ' ')
# 'balance history link' is the extractor's marker where RT injects [ RT I, ... - jõust. ... ] notes
open('/tmp/act.txt', 'w').write(t)
```

Then locate sections by string: `t[t.find('§ 106.'):][:3000]`. Superscripts degrade to
`§ 54 8`, `§ 262 1` (space + digit) - grep accordingly.

## Pitfalls specific to this source

- **Never guess the act id.** Amendment-history links, `RT I, ...` references and old
  search hits point at old redaktsioonid. Two ways to the current one: `/akt/lyhendid`
  (acts with abbreviations) or the version list `/akt/{grupiId}/redaktsioonid` (anything
  with an id, incl. KOV määrused and old ids).
- **Sanity-check currency by content**, e.g. a newly inserted section present, or a
  rate matching the latest published change; an act page whose newest `RT I,` marker
  is years old is a historical version. When a reform replaces the governing act,
  search the replacement by title (not just the old abbreviation): for example,
  the former Hädaolukorra seadus was repealed when the Kriisiolukorra ja riigikaitse
  seadus took effect; current mass-evacuation and crisis-plan rules must be located
  in the latter, not lifted from old HOS snippets.
- **Firecrawl-style extraction caps around 50 k characters** and may return only the
  table of contents for act pages: fine for discovering the section list, useless for
  quoting a paragraph. Use the API.
- **`/akt/{id}/blob-html` is the whole act** - jump by section string, and save it to
  disk so later greps are free.
- **PDF appendixes** (`aktilisa/...pdf`, e.g. exam-type tables) are static files and
  extract fine, but: (a) they are pinned to the amendment that introduced them - check
  the header line naming the amending regulation; (b) large ones (arengukavad, budget
  tables) exceed extractor caps, and head+tail truncation silently drops the middle -
  `curl` the PDF to disk and extract text with pypdf (`python3 -m pip install --user
  pypdf`), then grep the full text.

## Estonian sanction vocabulary (the part that decides consequence questions)

| Instrument | Procedure | Entered in karistusregister? | Notes |
|---|---|---|---|
| `rahatrahv`, `arest`, `juhtimisõiguse äravõtmine` (a real `karistus`) | kiirmenetlus / üldmenetlus / court | yes | Has further legal consequences while it is in the register. KarRS § 5: legal meaning until deletion; KarRS § 24: deleted + archived 1 year after execution of a misdemeanour fine (`väärteo rahatrahv`), 3 years for a criminal fine, etc. |
| `hoiatustrahv` | kirjalik hoiatamismenetlus (VTMS § 54-1); the substantive act fixes the rates (traffic: LS § 262) | no | Vehicle owner/responsible user is addressed; cap set by VTMS (420 EUR with the 7 EUR/km speeding rate) |
| `mõjutustrahv` | lühimenetlus (VTMS § 54-8 ... 54-12; on the spot, fixed amounts, max 160 EUR) | no | VTMS § 54-8 (6): expressly not a punishment, not registered, and cannot support recidivism or **any other legal consequence** (`õigusjärelm`). Which offences qualify and their fixed amounts live in the substantive act (traffic: LS § 262-1) |

Consequence questions therefore reduce to: which of these did the person receive?
A `mõjutustrahv` / `hoiatustrahv` never triggers the licence, register or exam
consequences that are conditioned on being "punished" or on a "valid punishment".

## Practical sources beside the register

- **Transpordiamet** (transport agency): procedure pages plus the e-service, which runs
  the legal pre-checks automatically before an application can be submitted.
- **eesti.ee** "Kui teid karistati väärteo eest": plain-language map of the misdemeanour
  procedures (hoiatamis-, lühi-, kiir-, üldmenetlus), written by PPA; good for procedure,
  verify amounts in the register.
- **RIK karistusregister FAQ** and **e-toimik.ee**: what the register contains, archiving
  deadlines, and the user's own extract - the self-check to hand the user.
- **PPA / Liiklusjärelevalvekeskus posts**: enforcement interpretation (e.g. that only
  register entries trigger exam requirements) - cite as interpretation only.
- **Riigikohus**: case law for contested readings.

## KOV (municipal) layer: decisions, protocols, old websites

- The register holds KOV **määrused** (`RT IV, ...`) but not KOV **otsused** or
  protocols: individual decisions and preparatory eelnõud live in the
  municipality's document register (Amphora: `https://atp.amphora.ee/<kov>`,
  linked from the council page as `Vallavolikogu otsused dokumendiregistris`).
  When the paper trail ends in a municipality, continue it there.
- An institution's history chain is cheapest read from its newest põhimäärus:
  its `Määruste kehtetuks tunnistamine` section names the predecessor acts it
  replaced (the merger/reorganisation footprint), and the municipality's
  `... hallatavate asutuste koosseis` decision tracks later structural changes.
- Municipal institutions have a business-register entry
  (`ariregister.rik.ee/est/company/<regkood>`): `Kehtetud nimed` = former names,
  `Kõrgemalseisev asutus` = supervising body, plus staff count and addresses.
  After a merger the surviving entity keeps ONE registration code; predecessor
  names appear as past names, not as separate live entities.
- Old municipal websites: predecessor domains look like `<vald>.kovtp.ee`; current
  sites link `Vanem info ... veebiarhiivis` into the domestic web archive (DIGAR).
  Pattern: `https://veebiarhiiv.digar.ee/a/<timestamp>/<url>` returns a frameset
  wrapper - the archived page itself is the iframe at
  `https://veebiarhiiv.digar.ee/a/<timestamp>mp_/<url>`; `curl` that `mp_` URL
  directly for raw archived HTML. Council `istungite päevakorrad ja eelnõud` pages
  through this archive yield meeting dates, agenda-item wording and presenter
  names - enough to date and sequence decisions even when the eelnõu files
  themselves were never archived. For Estonian sites, DIGAR is the direct route;
  web.archive.org is the general-purpose fallback.

## Worked combination (traffic, licence exchange)

Acts that must be read together: LS § 106 (lg 4 - licence on exchange without exams if
final-stage training is done and no punishment in the last 12 months; lg 5 - theory exam
only when a `kehtiv karistus` for a traffic-rules violation exists), the exam-procedure
regulation MKM määrus nr 50 (Lisa 1 maps which exam a purpose requires, and shows the
penalty case needs the theory exam only, not the driving exam), plus VTMS § 54-8 (6) and
KarRS § 24 for what counts as a punishment and when it stops counting.
