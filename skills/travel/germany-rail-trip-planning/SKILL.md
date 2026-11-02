---
name: germany-rail-trip-planning
description: "Use when planning a Germany rail trip. DB routes & fares."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [travel, trains, germany, deutsche-bahn, trip-planning]
    related_skills: []
---

# Germany rail trip planning (Deutsche Bahn)

## When to Use
Use when planning or checking a Germany trip built around trains: finding direct ICE/IC connections and durations, estimating fares and seat reservations, checking whether DB sells tickets for given dates, choosing entry/exit airports for open-jaw itineraries, or checking German holiday and attraction timing.

## Core workflow
1. **Flights first** (open-jaw beats round-trip for multi-city routes): list direct routes from candidate airports via flightsfrom.com/<IATA> and flightconnections.com; then get schedules/prices from Google Flights with the q-parameter URL:
   `https://www.google.com/travel/flights?curr=EUR&hl=en&q=flights%20from%20XXX%20to%20YYY%20on%20YYYY-MM-DD%20oneway`
2. **Trains via DB's own API** (works from inside int.bahn.de; far more reliable than v6/v5.db.transport.rest, which can be down for weeks — was 503 on 11 Oct 2026). From the bahn.de page context (cdp Runtime.evaluate, awaitPromise=true):
   - Stations: `GET /web/api/reiseloesung/orte?suchbegriff=<name>&typ=ALL` → use `[0].id` (e.g. `A=1@O=München Hbf@X=...@L=8000261@...`).
   - Journeys: `POST /web/api/reiseloesung/verbindungen` with JSON body:
     `{abfahrtsHalt, ankunftsHalt, anfrageZeitpunkt:'YYYY-MM-DDTHH:MM:SS', ankunftSuche:'ABFAHRT', klasse:'KLASSENLOS', produktgattungen:['ICE','EC_IC','IR','REGIONAL','SBAHN','BUS','SCHIFF','UBAHN','TRAM','ANRUFPFLICHTIG'], reisende:[{typ:'ERWACHSENER', ermaessigungen:[{art:'KEINE_ERMAESSIGUNG',klasse:'KLASSENLOS'}], alter:[], anzahl:1}], schnelleVerbindungen:true, sitzplatzOnly:false, bikeCarriage:false, reservierungsKontingenteVorhanden:false, deutschlandTicketVorhanden:false, nurDeutschlandTicketVerbindungen:false}`
   - Response: array; per connection `verbindungsAbschnitte[]` with `startHalt.abfahrt.sollzeit`, `zielHalt.ankunft.sollzeit`, `verkehrsmittel.name` (e.g. "ICE 1008").
   - **HTTP 500 + empty body for far-out dates = data horizon, NOT a bad schema** (near dates return 201 with the same body). If April is rejected but November works, use a representative near weekday for durations/frequency; construction reroutes can inflate times (test a second date if numbers look off).
3. **Indicative fares quickly:** DB SEO pages `https://www.bahn.de/reisen/view/verbindung/<from>/<to>.shtml` (e.g. muenchen/nuernberg) list sample connections + "ab X €"; Trainline `thetrainline.com/de/bahn-fahrplan/<a>-nach-<b>` also shows "ab X €".

## bahn.de UI quirks (fallback for horizon-blocked dates)
- The SPA **ignores URL prefills** (hash `#so=..&zo=..&hd=..` and query params) — fill the form manually: `input[name="quickFinderBasic-von"]` / `-nach`.
- Autocomplete: first suggestion may be a **hotel** (e.g. "B & B Hotel Nürnberg-Hbf") — do NOT press Enter blindly; find the element with exact textContent of the station and click it (clicks bubble from spans/divs).
- Date picker is a **multi-month scroll list**: use "Switch to <Month>" buttons; a naive day-cell query hits the first match in DOM (another month!) — scope to between the target month header and the next month header, then verify the control text shows e.g. "7. Apr" before searching.
- Search = the big red button; results page can take >10 s; scripted interactions sometimes 404 — reload and retry.

## Fare facts (2026)
- Seat reservation €5.50 (2nd) / €6.90 (1st); Flexpreis 1st includes reservation; Sparpreis fares rise closer to travel — book months ahead (national sales window up to ~6–12 months).
- Deutschlandticket excludes ICE/IC — irrelevant for ICE itineraries.
- Popular ICE corridors & typical times: München–Nürnberg 1 h 11 (300 km/h), Nürnberg–Berlin 2 h 44–48 (300 km/h via Erfurt), Berlin–Hamburg 1 h 45–50 (hourly), Köln–Berlin ~4 h 15, Frankfurt–Köln 1 h 05 (300 km/h).

## Seasonal / attraction facts that keep mattering
- German school holidays: KMK Ferienkalender (kmk.org) / mehr-schulferien.de. Easter 2027 = 28 Mar; late March = Osterferien peak.
- Rhine KD cruise season ~end of March/early April → late Oct (k-d.com Fahrplan).
- Pergamonmuseum Berlin: reopens 4 Jun 2027; south wing closed until ~2037.
- Elbphilharmonie Plaza: PAID since 5 Oct 2026 (~€5 online; reduced €3).
- Deutsches Museum Munich: half-open during renovation until 2028, €16, daily 9–17.
- Dokuzentrum Nuremberg: reopened May 2026 (new exhibition), €7.50, Mon–Fri 9–18 / Sat–Sun 10–18.
- Bonn cherry blossom (Heerstraße) peak ≈ mid-April.

## Common pitfalls
- Google Flights fresh profile → consent wall; click "Accept all" via JS then RE-RUN the query, otherwise "no nonstop" readings are false negatives. Results load async — wait ~5–8 s and scroll before reading. airBaltic routes are not always daily — always check the specific weekday (e.g. HAM–TLL lacks Sunday service; HAM–RIX has a Sun 19:30 nonstop).
- When a page shows a spinner/"fetching results", wait 10–15 s and re-read innerText before concluding "no flights/services".
- Verify a click actually took effect (read back the control/field value) before proceeding — DB pickers silently keep old values.
