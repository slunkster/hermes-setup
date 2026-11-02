# Seto language sources (all verified working)

## Seto Instituut — free learning materials
Index page: https://www.setoinstituut.ee/mis-on-tehtud/seto-keel/
On it: Seto aabits + töölehed (worksheets), "Aabitsa tüüraamat oppajalõ" (teacher guide), "Väike eesti-seto koolisõnastik" (two editions), "Seto keele teejuht", "Seto keele arõnguplaan".
Audio companion (juttõ ja laulõ): https://www.setoinstituut.ee/jutto-ja-laulo-seto-aabitsa-mano/
Printed copies: https://setokaubamaja.ee

### Download mechanics (WordPress Download Manager)
1. Save the download page: `curl -sL "<download page url>" -o page.html`
2. Extract the real link: `grep -oE 'https://www.setoinstituut.ee/download/[^"]*wpdmdl=[0-9]+&refresh=[a-z0-9]+' page.html`
3. Fetch it: `curl -sL -o file.pdf "<full link from step 2>"`

### Väike eesti-seto koolisõnastik (SA Seto Instituut, 2020)
Entry shape: eesti märksõna – seto nominatiiv, genitiiv, partitiiv. Estonian→Seto only.
- Thematic edition: https://www.setoinstituut.ee/download/vaike-eesti-seto-koolisonastik-teemavaldkondade-kaupa/ (~31 lk; themes: Aed ja aiasaadused, Aeg-nädalapäevad-kuud, Asesõnad-sidesõnad, Ilm, Keha ja kehaosad, Kool, Kunst ja muusika, Käsitöö, Mets-puud-taimed-seened, Linnud, Metsloomad-putukad, Kalad-kalastus, Koduloomad, Linn ja linnaelu, Maja-sisustus-hooned, Olulisemad küsimused, Ost ja müük, Perekond-sugulased, Arvsõnad, Rõivad-ehted-jalanõud, Sport, Toit, Transport, Elukutsed, Tegevused, Värvid)
- Alphabetical edition: https://www.setoinstituut.ee/download/vaike-eesti-seto-koolisonastik-tahestikuline/ (~19 lk)
- Teejuht PDF (Hagu & Pajusalu; school dictionary included as a section): https://www.umakultuur.ee/_uploads/materjal/seto_keele_teejuht.pdf

### Seto aabitsa töölehed (worksheets)
Download page: https://www.setoinstituut.ee/download/seto-aabitsa-toolehed/ (~38 lk; pypdf extract_text works, layout clean). Readymade Seto exercise phrasing and vocabulary — the source to copy when an instruction, worksheet or activity name must be in Seto (e.g. „PANÕQ ÕGA PILDI MANO ÕIGÕ NUMMÕR“, „VIAQ ÕIGÕ SÕNA ÕIGÕ AS´A MANO“).

## EKI online Seto dictionaries (arhiiv.eki.ee)
- Seto sõnastik: https://arhiiv.eki.ee/dict/setosonastik/ — query `https://arhiiv.eki.ee/dict/setosonastik/index.cgi?Q=<sõna>`; answer line "Leitud N artiklit"; phonetic headword + usage examples (Se = seto, V = võro, Kos, Sa, Kov). Book PDF linked from the page.
- Seto eripäraste sõnade sõnaraamat: https://arhiiv.eki.ee/dict/setoeri/ — same cgi interface.
- Search modes: "Märksõna" (headword) default; "Kirjakeelne vaste" searches by the standard-Estonian equivalent.

## Võro cross-checks (do not pass off as Seto)
- https://synaq.org — võro-eesti-võro sõnaraamat
- https://wi.ee — Võru Instituut (corpora, publications); "Kuidas võro ja seto keelel vahet teha?": https://umakiil.eu/artikliq/37-kuidas-voru-ja-setu-keele-vahet-teha-laeteq-sirp

## News / community
- Setomaa portal: https://kogukond.setomaa.ee
- ERR Seto news: https://vikerraadio.err.ee/1191790/setukeelsed-uudised
