# auto24.ee search and parsing

## Search URL

```
https://www.auto24.ee/kasutatud/nimekiri.php?bn=2&a=100&j[]=3&i[]=2&g2=20000&l2=200000&e[]=414&e[]=330&af=100&ae=2&ak=0
```

- `a=100` cars; `j[]` body: 1 sedaan, 2 luukpära, 3 universaal (also contains SUVs), 4 mahtuniversaal
- `i[]` gearbox: 1 manuaal, 2 automaat; `h[]` fuel: 1 bensiin, 2 diisel, 6 elekter, 5/14/15 hübriid, 16 pistikhübriid
- `p[]` drive: 1 esi, 2 taga, 3 nelik
- ranges: `f1/f2` year, `g1/g2` price, `l1/l2` mileage km, `k1/k2` power kW
- `e[]` equipment (AND-combined): 414 digitaalne näidikutepaneel, 330 ACC (distantsi hoidev püsikiiruse hoidja),
  400 Apple CarPlay, 427 CarPlay juhtmevaba, 401 Android Auto. No reliable tow-hitch code — check detail pages.
  Full list: `[...document.querySelector('select[name="e[]"]').options]` on `/kasutatud/otsing.php`.
- `af=100` per page, `ae=2` sort by price, `ak=<offset>` paging; total shown as "Kokku: N (1/3)".
- CarPlay is often not ticked as a filter field but written in the equipment text — filter it
  from detail pages instead of `e[]=400` to avoid losing ads.

## Result rows

`document.querySelectorAll('.result-row')` → link `a.row-link, .title a`, text has
model, price "12 345 €", year, "123 456 km", fuel, gearbox, body, drive.

## Detail page (`/soidukid/<id>`)

Use `document.body.innerText` (NBSP `\xa0` inside numbers — replace before regex):
- head block from `Liik\t`: `Esmane reg\t06/2022`, `Läbisõidumõõdiku näit\t131 000 km`,
  `Hind\t16 399 EUR` and optional `Soodushind\t… EUR` (sale price — take the min),
  `sisaldab KM 24%` = VAT included.
- `MOOTORSÕIDUKIMAKS\nAastamaks (YEAR)\n88,20 €\nRegistreerimistasu\n564,96 €` (sometimes absent).
- `VARUSTUS` section: equipment text; `piduriga haagis:\t1500 kg` towing limit.
- h1 = title (first line only; later lines are "Salvestatud N korda").
