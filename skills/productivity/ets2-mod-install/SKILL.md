---
name: ets2-mod-install
description: "Use when installing ETS2 mods, maps or DLC checks."
---

# Installing ETS2 mods (Jazzycat / TrafficManiac)

## When to Use

User asks to download or install Euro Truck Simulator 2 mods, especially Jazzycat
or TrafficManiac traffic/cargo packs.

## Destination

```
C:\Users\Siim Alve\Documents\Euro Truck Simulator 2\mod
```

All mods for this user go there. Do not invent a folder in Documents.

## Verify DLC requirements before anything else

Most map mods refuse to load without a fixed list of DLCs. Establish ownership
from Steam's own records; never from a filename guess:

- ETS2 is Steam appid **227300**. Read
  `<steam>/steamapps/appmanifest_227300.acf` and take the `dlcappid` values under
  `InstalledDepots` — those are the DLCs owned *and* installed.
- Resolve an unfamiliar appid via SteamDB (`steamdb.info/app/<id>/`).
- **Do not infer ownership from an on-disk `dlc_*.scs` filename.** A DLC's file
  need not contain its display name, and the game folder also holds bundled
  paint jobs, so the file list does not map one-to-one onto DLCs. A filename
  search yields false negatives and tells the user they are missing something
  they own.
- Locate the install dir via `steamapps/libraryfolders.vdf` (`"path"` entries),
  then `steamapps/common/Euro Truck Simulator 2`.

## Source and download chain (traffic/cargo packs)

1. **ets3mods.com** mod pages read fine with plain `curl` (no Cloudflare). Get the
   pack list from `https://ets3mods.com/?s=<author>`; `/tag/<author>/` returns 404.
   Each page links exactly one `sharemods.com` URL for the real file.
2. **Ignore the "Direct Download Now" button** on ets3mods pages — it points at
   `batcrack.icu/tracker/...`, an ad redirect, not the file.
3. **sharemods.com is Cloudflare-protected.** Plain curl gets 403. Use the
   browser. With the user's real (non-headless) profile the challenge passes on
   its own — no click needed.
4. On the sharemods page click the button with `id=downloadbtn`
   ("CREATE DOWNLOAD LINK"), wait ~6-9s. The second page holds an `<a>` whose href
   contains `X-Amz-Signature`.
   - **Click it with JS `element.click()`, not `click_at_xy` coordinates.** The
     button submits a POST form; a coordinate click can miss and silently leave
     you on step 1, so the signed-URL lookup returns nothing and the download
     is silently skipped. Verify with a count of `X-Amz-Signature` anchors
     before extracting, and retry the click once if it is still 0.
5. **Download that URL with curl, not the browser** — far more reliable and
   verifiable.

## Presigned S3 URL quirks

- Expires in 1 hour. Collect URLs and download promptly; re-collect if 403.
- A `HEAD` request returns **403** even when the URL is good. Verify with a
  ranged GET: `curl -s -r 0-0 -D -` and read the `Content-Range: bytes 0-0/<total>`. Range GET returns 206.
- Total size from that `Content-Range` is the byte-exact expected file size — use
  it to verify the download, since the page's "726.8 MB" is rounded.
- Download to `<name>.part` and rename only when the byte count matches.

## Variant selection (read the mod page; archives ship no readme)

`.scs` files are SCS's own format — 7z/unzip **cannot** open them, so readmes are
only on the mod page. `.7z`/`.rar` downloads must be extracted first.

- `_jaz.scs` = for use **with** Jazzycat's AI traffic pack; `_def.scs` = default
  traffic only. If the user has Jazzycat's AI pack, install base + `_jaz`.
- `_eng.scs` / `_rus.scs` — language variants (Jazzycat). Install base + one.
- Jazzycat English setup is always **base + language file**; install both.
- Optional traffic files (e.g. `*_traffic.scs`, `*_traf.scs`) are opt-in — leave
  them out unless asked.

## Pack conflicts and multi-part packs

- **overweight_trailers_and_cargo and trailers_and_cargo must not be installed
  together** — the overweight pack is a subset of trailers_and_cargo. Install
  trailers_and_cargo and leave overweight out.
- `trailers_and_cargo_pack_by_Jazzycat` ships as **part1 + part2 + part3** — all
  three are required.

## Map mods (ProMods)

ProMods does **not** come from the file hosts above. It sits behind the user's
own promods.net account, needs a generated def file, and its fast-download tier
is a real purchase the user must complete themselves. Full flow, def-file
options, the version/DLC compatibility table and the payment handoff are in
`references/promods.md`.

## Diagnosing an ETS2 crash

Files (in `Documents\Euro Truck Simulator 2\`):

- `game.log.txt` — **stops growing once it hits its size limit** and ends with
  "The log file exceeded its limit size, truncated". The crash moment is usually
  NOT in it, so do not expect the last line to explain the crash.
- `game.crash.txt` — build, CPU/GPU, `Exception code`, call stack. A
  `C0000025 NONCONTINUABLE_EXCEPTION` faulting in `KERNELBASE.dll` means the
  game's own error handler aborted the process (a fatal data error), not a GPU
  driver fault.
- Windows corroborates it: `powershell -NoProfile -Command "Get-WinEvent
  -FilterHashtable @{LogName='Application'; StartTime=(Get-Date).AddHours(-3)}"
  | Where Message -match eurotrucks2` gives APPCRASH + faulting module + code.

**Finding which mods are actually ENABLED:** `profile.sii` is binary/encrypted,
so it cannot be read. Instead use the game log's mount list — ETS2 mounts only
the enabled mods:

```bash
grep -oE 'Documents/Euro Truck Simulator 2/mod/[^ ]*' game.log.txt | sort -u
```

Diff that against `ls mod/` to see which files are present but *not* enabled.
Confirmed by finding exactly one file in the folder missing from the mount list.
Workshop mods mount as `workshop/content/227300/<id>/<file>`; map the hex in
`mod_workshop_package.00000000XXXXXXXX` to a decimal id to name them.

Pitfalls:
- **Do not `find` the workshop or mod folders** — one call dumped 228 KB. Scope
  every command to a specific subdirectory or filter it first.
- `mods_info.sii` is a detection record that accumulates duplicates with
  different timestamps. It is NOT the enabled list; do not report its count as
  "active mods".
- `.scs` filenames are not reliably greppable — newer SCS packs use a compressed
  directory, so a filename search can miss a file that is really there.

### Known crash causes in this user's setup

- **Weather/graphics mods stack.** Grimes season packs plus `Realistic Rain`
  (workshop 1787041596) and `Asphalt_improved` (3071067969) were all mounted at
  once, and BOTH Grimes autumn packs (Early + Late) were enabled together.
  Grimes' own instructions: only ONE season pack, all other weather/graphics mods
  off. Check the mount list for this before blaming anything else.
- **ProMods vs SCS Special Transport.** `dlc_oversize.scs` ships
  `oversize_offer_data.mod_czloko.sii` with offers pointing at base-map routes
  (`route_data.ber_szcz1`, `bre_tra1`, `kas_ham1`). ProMods rebuilds those areas,
  so the routes vanish -> `dangling pointer` `<ERROR>s`. Keep the ProMods Special
  Transport workshop add-on (2637561037) matching the installed ProMods version;
  it ships one folder per ProMods release (e.g. 2.57 … 2.83) and lags behind new
  releases.

## Grimes seasonal weather / graphics packs

Grimes (autumn, winter, spring, summer graphics + weather) publishes only on his
own site: **grimesmods.wordpress.com** — that page is curl-friendly (no
Cloudflare), and his Sharemods uploads are marked "Verified Author", so it is
the authentic source. Do not use reupload sites for these.

- Fetch the pack page with curl, then grep it: every past version's link is on
  the page, newest first. Match the `Compatibility latest version: ETS2 1.61`
  line to the `vN.N` in the page title to pick the right one.
- Two autumn variants exist and they are **mutually exclusive** — Early Autumn
  (autumnal colours, leaves still on trees) and Late Autumn/Mild Winter
  (leafless). Same for all season packs: only ONE Grimes pack may be enabled at
  a time, and other weather/graphics mods must be off or the game crashes.
- Install is a plain .scs move; give it a **high priority** in the Mod Manager.
- They work alongside ProMods (documented as compatible).

## Bulk work

Parallelise with `delegate_task` subagents (each gets its own terminal; a few
concurrent curls beat one serial loop). Put a verified downloader script in the
workspace that takes slugs, resolves sizes, and is safe to run concurrently.

## ProMods (paid, account-gated)

Separate flow from ets3mods — promods.net is Cloudflare-gated (curl 403s) and
requires a logged-in account. Use the browser; the user's real profile carries
the session.

- Europe is `setup.php?game=ets` — **not** `game=ets2` (that returns "No mod
  selected"). Others: `ats`, `tgs` (Great Steppe), `me` (Middle East), `ma`
  (Maghreb).
- Wizard: def file → choose download → download files → install.
- **Def file generator** is `download.php?game=ets&lang=en`. Options are damage
  level, vegetation draw distance, map colours, map-zoom compatibility. Defaults
  are fine; it downloads as `promods-eu-def-v284.scs` (browser shows a `.tmp`
  that renames on completion — do not treat the `.tmp` as the final file).
- Download choice: **free** = 13 split files with a 5-minute wait between each;
  **paid** = one archive. Paid is €1.25 on the ProMods page but **€1.37** at
  checkout (gateway surcharge). Two platforms: ProMods Store (Shopify,
  card/GPay/iDEAL) and Payloadz (PayPal only). Links are single-use, 48h expiry.
- **Never complete the payment yourself.** There is no card in the vault. Open
  checkout and hand it to the user. Expect expired saved cards — the page shows
  expiry dates that may be in the past; say so rather than letting them think
  the charge failed.
- The archive is ~3.4 GB and unpacks to **~14.5 GB**, so check free disk first.
- Install target is the Documents mod folder, **never** the Steam folder. Final
  state per ProMods' own guide: **6 SCS + 1 ZIP (dlcsupport) + the generated def
  = 8 files**. The `dlcsupport` zip is a mod package itself (manifest.sii,
  "ProMods DLC Support Package") and goes in as-is.
- Load order is shown by the Mod Manager's own numbering (1/8 … 8/8) — enable
  all and follow it. For multi-map combos ProMods publishes a priority list
  (CAP, TCP, Maghreb, Middle East, Europe, Great Steppe).

### Checking required map DLCs (do this before the user pays)

ProMods lists its DLC requirements on the store page. **Do not guess the DLC's
filename** — check Steam's authoritative record instead:

```bash
grep -A1 '"dlcappid"' "<steam>/steamapps/appmanifest_227300.acf"
```

Every owned+installed DLC appears as an app id. A file-based guess is wrong:
Nordic Horizons is app id **2780810** and ships **no** `dlc_nordic.scs`, so a
filename search falsely reports it missing. Gave the user a bad answer once —
use the app id.

