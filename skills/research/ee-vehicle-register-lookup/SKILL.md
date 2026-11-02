---
name: ee-vehicle-register-lookup
description: Use when checking an Estonian vehicle by plate or VIN.
---

# Estonian vehicle lookup by plate / VIN

Goal: find out what an Estonian-registered car really is — whether it is in the register, its CO2/mass as the state sees them, the fees that follow, and which checks must be left to the user.

## The one unauthenticated route into liiklusregister data

`GET https://apimsm.transpordiamet.ee/v2/msm/regTasu/by-vehicle-identifier?vinCode=<VIN>` (or `?regNr=<PLATE>`), no auth, JSON.

- HTTP 200 with numeric `totalPrice`/`basePrice` -> the vehicle IS in the Estonian register.
- HTTP 422 `{"errorMessage":"Vehicle not found"}` -> not in the register (or plate and VIN belong to different vehicles).
- Always run the control: change one VIN digit -> must answer 422, otherwise the endpoint is answering 200 to everything.
- A run of `X` (`vinCode=XXXXXXXXXXXXXXXXX`) answers 200 with all prices 0.00 and `ageCoef: null` — never report that as a fee or as a hit.
- Amounts are the one-off registreerimistasu / omanikuvahetustasu, not the annual mootorsõidukimaks, and no exemption is applied.

## Recover the register's CO2 and täismass by inversion

The same API has `GET /v2/msm/regTasu/by-technical-parameters?category=M1&co2wltp=&technPermMaxLadenMass=&initialRegDate=&seats=&regFeeCalcDate=`. Its formula (verified 2026-09):

- `co2Price` = 0.6 €/g up to 117 g/km, 1.2 €/g for 117–150, 3.6 €/g above 150.
- `massPrice` = 0.24 €/kg above a 2000 kg täismass.
- `basePrice` = 150 for an old vehicle, 300 for a recent one.
- Both component prices are scaled by `ageCoef/0.12`; `ageCoef` 0.12 is the oldest bracket and is hit at exactly 14 whole years of vehicle age, measured from `initialRegDate` to `regFeeCalcDate` (so 0.12 pins the first-registration date to a one-year window).

So from `by-vehicle-identifier`, invert: CO2 = solve the co2 table for `co2Price`; täismass = `massPrice/0.24 + 2000`.

Confirm the inversion before believing it: feed the solved CO2 + mass into `by-technical-parameters` and require an exact match of `totalPrice`, `co2Price`, `massPrice`, `basePrice` and `ageCoef`; neighbouring values (±1) must give different numbers. `category=M1` and `M1G` price identically (so they are indistinguishable); `N1`/`N1G` answer 400 `Invalid data`, so a priceable M1 answer does not prove the car is M1.

Label CO2/mass as derived from the register (by exact inversion), not as values the register returned.

## Walls — do not burn calls on these

- `https://eteenindus.mnt.ee/public/soidukTaustakontroll.jsf` (mileage, inspections, owners, restrictions): reCAPTCHA v3 + ID-login; a scripted submit returns `reCAPTCHA valideerimise viga`.
- `https://www.lkf.ee/et/kahjukontroll` and `/et/kindlustusekehtivus`: captcha; submitting with an unsolved captcha returns `The answer you entered for the CAPTCHA was not correct.` A scripted click on the reCAPTCHA box often does nothing at all (and the kahjukontroll one refuses clicks below the viewport edge — scroll first).

Hand these three links to the user to run in their own browser (they need ID-card/Mobiil-ID for the Transpordiamet one).

## Web-search expectations

Google and DuckDuckGo serve bot-challenge pages from this environment; Bing returns unrelated filler. A specific VIN is normally not indexed anywhere — say so plainly instead of implying a clean negative search.

## Reading a European Audi/VW VIN

`WAU` = Audi AG Germany; positions 4–8 are `ZZZ` + a type code (e.g. `8K` = A4 B8 2008–2015, also A4 allroad), so NHTSA/vPIC decodes only make, plant, model year and vehicle type — never engine or trim. Position 10 is the model year (`D` = 2013), position 11 the plant (`A` = Ingolstadt).
