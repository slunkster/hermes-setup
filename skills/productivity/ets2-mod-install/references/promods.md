# ProMods (ETS2 map overhaul)

## Where it lives

- promods.net is Cloudflare-protected; plain `curl` returns 403. Use the browser
  with the user's real profile (it passes the challenge on its own).
- The user has their own account there and may already be signed in — check the
  homepage header before assuming a login wall.
- Download entry points: `promods.net/setup.php?game=<key>`, where key is `ets`
  (Europe), `ats` (American Truck Simulator), `tgs` (The Great Steppe), `me`
  (Middle-East), `ma` (Maghreb). **`?game=ets2` is wrong** and renders
  "No mod selected".

## Check compatibility before paying

- `promods.net/compat.php` lists every release with its target ETS2 patch,
  country/city counts and DLC list.
- Only one release targets the current patch. A release built for an older patch
  will not run on a newer game, and older releases need correspondingly older
  DLC sets — so "use an older version" is usually not a way around a missing
  DLC.
- The store product page states the exact required DLCs ("THIS MOD REQUIRES TEN
  DLCS..."). Verify against the Steam depot list before the user pays.
- Do not assume a new profile is needed. Current releases update existing SCS
  profiles in place: the current mission is interrupted and the truck is
  returned to its home garage.

## The four-step flow

1. **Def file.** Step 1 of `setup.php?game=ets` requires a personalised def file;
   the generator is `promods.net/download.php?game=ets&lang=en`. Settings:
   damage (`dmg`: 0 none / 1 default / 2 double), vegetation drawing distance
   (`lod`: 1 near / 2 standard / 3 high / 4 ultra), map overlay colours, and a
   map-zoom compatibility checkbox (only for other map combinations). Choices are
   remembered server-side.
   - `dmg=1` + `lod=2` are safe defaults. `lod` really depends on the user's
     hardware, but every setting is regenerable in seconds, so take the defaults
     and tell the user which ones you chose.
   - Click GENERATE; the file downloads as `promods-eu-def-v<ver>.scs` (~3.7 MB).
     It appears in the download folder first as a GUID `.tmp` and is renamed on
     completion — re-list rather than concluding the download failed.
   - Tick the `defCheck` checkbox, then click `defNext` to continue.
2. **Choose download.** Paid vs free:
   - Paid: one file, no reassembly, fast servers. **The store total is higher
     than the figure on the promods.net page** because a gateway surcharge is
     added. Quote the store total, not the landing-page number.
   - Free: many split files (13 for Europe) on ad-supported servers with a
     multi-minute wait between each. Legal but slow — offer the choice, do not
     pick the paid tier silently.
   - Do not route around it via third-party mirrors; ProMods states that
     redistribution is illegal.
3. **Download files.** The paid tier is a single `.7z` (Europe 2.84 ~3142 MB).
4. **Install.** Extract into the ETS2 mod folder next to the def file and load
   the map files in the order ProMods publishes — load order is the usual cause
   of crashes. Legacy release downloads live under
   `store.promods.net/en-eu/collections/legacy-downloads`.

## Payment is the user's action

- The store is Shopify; checkout runs through Shop Pay, which may offer the
  user's saved cards. The Hermes vault holds nothing for this site, and card
  details are never typed by the agent.
- **Never complete the payment.** Open the checkout, report the exact total and
  which cards are offered, flag any saved card whose expiry has already passed
  (those will be declined), and stop. The user clicks Pay now.
- Download links are **single-use and expire in 48 hours** — begin the download
  as soon as the user confirms payment.
