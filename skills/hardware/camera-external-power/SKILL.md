---
name: camera-external-power
description: "Use when powering a camera beyond its stock battery."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [camera, camcorder, battery, power, usb-c-pd, v-mount, dummy-battery, runtime, gear]
    category: hardware
    related_skills: [pdf, grounded-citations, product-price-monitor]
---

# Camera & Camcorder External Power

Runtime, batteries, chargers, DC IN feeds, power banks and V-mounts for cameras and
camcorders — answered with the real numbers from the maker's manual and a parts list that
physically fits, not a bag of options.

## When to Use

- Runtime / battery-life questions, or spare pack vs bigger pack.
- Running a camera off mains, a USB-C PD power bank, a dummy battery, or a V-mount.
- "I don't have the charger" (often: no AC adaptor — a different problem than it sounds).
- Designing or reviewing a field power kit and its connectors.

## Procedure

1. **Pin the exact model**, then read the OFFICIAL manual PDF and cite the spec sections:
   power supply voltage, DC IN connector type and voltage window, battery part number with
   mAh/Wh, charging voltage/current/time, and the "standard charging time and recordable
   time" table. Search snippets are not enough — see the first two pitfalls. Download the
   PDF and extract locally when `web_extract` truncates it (recipe in the `pdf` skill).
2. **Report runtime as two numbers**: the manual's continuous recordable time *with its
   stated test conditions* (frame rate, file format, LCD, nothing plugged into video outs),
   and a realistic mixed-shooting figure at roughly 0.75x that. State the assumption.
3. **Turn capacity into runtime yourself**: `Wh / hours = average draw` from the manual's
   own table, then divide any candidate source's Wh by that draw. Never repeat marketing
   hours; a 43 Wh pack giving 4h35 means ~9.4 W, and every other option follows from it.
4. **Compare charge time against runtime.** The charge:use ratio is usually the binding
   constraint, not the runtime — 4h35 of use per 5h30 of charging means one pack can never
   keep up, and that, not capacity, is the case for a second source.
5. **Establish the charging topology before recommending a charger.** Many camcorders
   charge the pack in-camera from the DC IN input (the supplied AC adaptor *is* the
   charger) and refuse to charge while powered on. Ask which parts the user already has
   before pricing anything.
6. **Rank options cheapest/lightest first** (ladder below), then give ONE concrete parts
   list with connector geometry, polarity, voltage and current — not a menu.
7. **End with the pre-flight test**: with the cable on the source and nothing attached,
   measure the plug (DMM) and confirm nominal voltage and center-positive polarity before
   it ever touches the camera.

## Options Ladder

| Option | Gains | Costs / caveats |
|---|---|---|
| Spare OEM pack | Zero rig, known-good | Same slow in-camera charge; ratio stays ~1:1 |
| Bigger same-mount pack (OEM or third-party) | 1.5-2x runtime, no rig | May bulge below the body; OEM may not list it as compatible — check fit |
| USB-C PD power bank into DC IN | Cheapest per Wh, 1-2 h recharge, doubles as a field charger for the internal pack | Needs a 12 V-capable bank + correct DC plug; best for handhelds |
| Dummy battery + external supply | Continuous power, no bay needed | Powers the camera but does NOT charge the OEM pack |
| V-mount / Gold Mount + plate | Instant hot-swap, 98 Wh+ per pack | Plate + regulated cable + own charger + 400-600 g on a small camera; only for rigged/tripod work or when the user already owns V-mounts |

## Answer Shape

Verdict first, arithmetic second, ranked options with concrete parts and prices third,
pitfalls last. Once the user picks an option, deliver the parts list, the exact connector
spec and the gotchas in the same reply rather than asking a follow-up question. Plain text,
no markdown emphasis (CLI).

## Pitfalls

- **Marketing hours belong to a different model.** A "longest continuous recording time"
  claim is usually the flagship's number; the manual's table has a separate column per
  model. Quote the column that matches the user's camera.
- **Extracted spec tables lose their column order.** A battery row can carry charging time
  plus per-model, per-frequency recordable times in one line; the flattened text interleaves
  them. Corroborate the parse against the charging time stated in the battery spec section
  and against one marketing figure before trusting it.
- **"No charger" is often "no AC adaptor".** If the camera charges in-camera from DC IN,
  the adaptor is the charger and the fix is a 12 V source, not a standalone charger.
- **Batteries usually do not charge while the camera is on.** You cannot top up mid-shoot;
  the internal pack only charges with the camera powered off.
- **Keep the pack installed when running on external DC.** Panasonic manuals say so
  explicitly even while recording off the adaptor — the battery buffers current peaks.
- **DC IN voltage windows are tighter than the nominal.** An 11.4-12.6 V input must never
  see a raw battery tap: an unregulated "12 V" D-tap reads ~16.8 V fresh off the charger.
  Regulated cable, or nothing.
- **12 V is not mandatory in USB-C PD.** PD 2.0/3.0 sources may offer only 5/9/15/20 V; a
  bank without a 12 V PDO hands over 5 V and the device simply will not run. Verify the
  bank's own spec sheet lists `12V/3A` — the "PD" label proves nothing.
- **PD contracts are per-port and renegotiate.** Keep the 12 V port exclusive; adding a
  phone to the same bank can drop the contract mid-take.
- **Some banks shut off below ~100 mA idle load.** An idle camera can silently lose power;
  the workaround is unplug/replug or press the bank's button.
- **Compare in Wh, never mAh.** mAh at an unstated voltage is marketing; a 20,000 mAh bank
  at 3.6-3.7 V is ~72 Wh and its *rated* capacity at 5 V is lower still. Derate ~15% for
  conversion losses when promising hours, and stay under the 100 Wh air-travel limit.
- **Cold kills capacity.** Lithium packs are 0-40 °C rated; tell the user to keep the bank
  in an inside pocket on winter shoots.
- **A wrong-polarity or over-voltage plug can destroy the camera.** DC plugs follow a
  polarity-uniform standard (EIAJ RC-5320A classes — larger plug, higher voltage class,
  center positive). Match OD x ID x center-pin diameter exactly and measure before plugging.

## Verification

Before recommending a build, re-check three things against a source, not memory: the source
advertises the exact voltage/current the device needs (spec-sheet line), the connector
matches OD x ID x pin diameter, and the polarity is center-positive. Then state the
measurement the user should make at the plug before connecting the camera.

## References

- `references/panasonic-vbr-camcorders.md` — Panasonic HC-X1500/X2000 (and the wider
  VBR-battery AG/HC family): battery and DC IN specs, the charging/recordable-time table,
  verified 12 V/3 A power banks, and the concrete cables/plugs that fit the EIAJ-4 jack.
