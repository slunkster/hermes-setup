# Panasonic VBR-battery camcorders (HC-X1500 / HC-X2000, AG-DVX200, AG-CX10, AG-UX series)

Condensed from the official HC-X1500/HC-X2000 operating instructions plus vendor spec
sheets. Numbers verified from the manual PDF, not from search snippets.

## Power supply and battery (HC-X2000 / HC-X1500)

| Item | Value |
|---|---|
| Power supply | 7.28 V (battery) / 12 V (AC adaptor) |
| Consumption | X2000 15.5 W, X1500 14.4 W (LCD monitor used); 22.9 W while charging |
| Battery | AG-VBR59, 7.28 V / 5900 mAh / 43 Wh; VW-VBD58 (7.2 V / 5800 mAh) also supported |
| Charge params | 8.4 V, up to 4000 mA (in-camera, from DC IN) |
| DC IN 12V | DC 12 V (11.4-12.6 V), EIAJ type 4; AC adaptor output 12 V 3 A |
| EIAJ-4 plug geometry | 5.5 mm OD x 3.3 mm ID x 1.0 mm center pin, center positive |

The manual lists only AG-VBR59 and VW-VBD58 as this model's batteries. The newer
AG-VBR89G (65 Wh) and AG-VBR118G (86 Wh) use the same interface but are absent from the
X2000 compatibility list — tell the user to check the fit rather than asserting support.

## Charging and recordable time (manual, "Standard charging time and recordable time")

| Battery | Charge in camera | X1500 59.94 Hz | X2000 59.94 Hz | X1500 50 Hz | X2000 50 Hz |
|---|---|---|---|---|---|
| AG-VBR59 | ~5 h 30 min | ~5 h 20 min | ~4 h 35 min | ~5 h 40 min | ~4 h 50 min |
| VW-VBD58 | ~5 h 15 min | ~5 h 15 min | ~4 h 30 min | ~5 h 35 min | ~4 h 45 min |

Conditions: factory defaults, MOV, 2160-59.94p/50.00p HEVC LongGOP 200M, LCD monitor used,
nothing connected to the input/output terminals. The X2000's 4h35 is the "industry longest
4.5 h" marketing figure — use it to sanity-check any parse of this table.

Average draw works out to ~9.4 W (43 Wh / 4.58 h), so any external source in Wh converts
to roughly `Wh x 0.85 / 9.4` hours. A 72 Wh bank is therefore ~6 h.

Behavioural facts that decide the recommendation:

- The battery does NOT charge while the camera is powered on; charging needs the camera off.
- The pack stays installed while recording on external DC power (manual: "Even when you use
  the AC adaptor for recording images, keep the battery connected").
- In-camera charging is the only OEM path for the AG-VBR59; quick charging needs the
  optional AG-BRD50 dual-bay charger (12 V in, 4 A, ~3 h 20 min). Third-party 8.4 V/800 mA
  chargers (Kastar, Watson, Jupio) take 6-7 h.

## Building the USB-C PD feed for the EIAJ-4 jack

- **Ready-made trigger cable:** PDE-12V-5533 / PDN-12V-5533 (pdqc.net, also Amazon JP),
  ~1,680-1,780 JPY. EIAJ#4 plug out (5.5 x 3.3 mm, 1.0 mm pin), 12 V fixed, 5 A max,
  USB-C *socket* input — it needs a PD/eMarker USB-C-to-USB-C cable or it falls back to
  5 V. The maker lists it as a stand-in for Panasonic camcorder AC adaptors.
- **EU-sourced, no soldering:** a 12 V PD trigger cable with a 5.5 x 2.1 mm plug
  (QUARKZMAN 36 W 12 V 3 A, RIIEYOCA 12 V 3 A on amazon.de) plus a 5.5 x 2.1 female ->
  EIAJ-04 male adapter (eBay seller "connekt" carries one).
- **DIY:** CH224-style PD decoy board with screw terminals + Lumberg 1636 04 EIAJ-4 plug
  (2.14 EUR, TME PL stocks it) + ~20 cm of wire.
- **Custom:** Alvin's Cables (Shenzhen) has already built USB-C male with 12 V PD trigger ->
  right-angle 5.5 x 3.3 mm DC male, 1.0 mm pin, center positive, regulated 12 V, for the
  HC-X1500/X2000; order through their custom configurator.

## Power banks verified to advertise 12 V/3 A

- UGREEN Nexode 20000 mAh 100 W, SKU 25188, 72 Wh — USB-C1 output 5 V/3 A, 9 V/3 A,
  12 V/3 A, 15 V/3 A, 20 V/5 A. Sold in Estonia (arvutitark.ee, photopoint.ee) and on
  eu.ugreen.com, ~60-70 EUR.
- UGREEN PB550 67 W 20000 mAh — same 12 V/3 A line.

Always re-read the bank's own spec sheet for the `12V` line before recommending it; PD 2.0
and 3.0 do not require a 12 V profile.

## V-mount alternative (only for rigged or all-day shoots)

- 98 Wh V-mount gives ~8-9 h at this camera's draw, with instant hot-swap.
- Requires a plate plus a REGULATED D-tap -> 12 V cable (IndiPRO and similar make regulated
  cables for the AG series): a raw D-tap sits at ~16.8 V off the charger and exceeds the
  camera's 11.4-12.6 V window.
- Direct-mount alternatives that skip the rig: Core SWX Nano-VBR98 (98 Wh, VBR form factor,
  D-tap out, charges only on OEM Panasonic chargers) and the Powerbase EDGE + VBR dummy
  cable, both ~4-5 h runtime class.
- Third-party VW-VBD98-class packs (~12,400 mAh, ~90 Wh) slot into the same bay for ~2x
  runtime without any rig; expect a bulge below the body and slow in-camera charging.
