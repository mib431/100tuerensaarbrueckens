# Walking route — 100 doors of Saarbrücken

Suggestion only. Verify each stretch on Google Maps / Street View before walking. Doors cluster tightly inside each district; most ground-time is between districts (use Saarbahn or bike to skip transit dead time).

## Strategy

~25 doors per day × 4 days. Walk 6-10 km/day. Group by district for variety: baroque → Gründerzeit → industrial → modernist.

Bring:
- Phone with GPS on (see `mi12.md`).
- Paper list `001..100` to tick off as shot. Prevents dupes and orientation drift later.
- Monopod or just lean on opposite wall — straight verticals save rotation work in `process.py`.

Best time: early morning, low sun, no parked cars / pedestrians blocking.
Avoid Sundays in Alt-Saarbrücken: shop shutters down → many doors hidden.

## Day 1 — St. Johann + Nauwieser Viertel (~25 doors)

Hauptbahnhof → Reichsstraße → **Bahnhofstraße** (Jugendstil facades, ~5)
→ Sulzbachstraße → **Nauwieser Viertel** (Nauwieserstraße, Cecilienstraße, Försterstraße — Gründerzeit, ornate, ~10)
→ **St. Johanner Markt** + side lanes (Saarstraße, Kappenstraße, ~8)
→ Saaruferpromenade for closing shots.

## Day 2 — Alt-Saarbrücken (~25)

Saarbrücke → **Schlossplatz** + Schlossberg
→ **Ludwigsplatz** + **Ludwigskirche** quarter (baroque, ~10)
→ Eisenbahnstraße → **Alte Brücke**
→ Talstraße / Hohenzollernstraße
→ Triererstraße (older row houses, ~8)
→ up to Spicherer Berg edge (Französische Allee, ~7).

## Day 3 — St. Arnual + Rotenbühl + Eschberg (~25)

Bus / tram to **St. Arnual Stiftskirche** → Stiftsstraße + village core (stone doorways, ~10)
→ N to **Rotenbühl** (Lessingstraße, Großherzog-Friedrich-Straße — villa quarter, ~10)
→ tram to **Eschberg** for post-war modernist contrast (~5).

## Day 4 — Malstatt + Burbach + Rußhütte (~25)

Tram to **Malstatt** → Burbacher Straße corridor (industrial-era, Werkssiedlung, ~10)
→ **Burbach Alte Kirche** quarter (~5)
→ Rußhütte residential streets (~5)
→ optionally Brebach core for variety (~5).

## Slot allocation hint

If you want districts visible as clusters when scanning the gallery, allocate slot ranges per district:

| Slots | District |
|---|---|
| 001-025 | St. Johann + Nauwieser Viertel |
| 026-050 | Alt-Saarbrücken |
| 051-075 | St. Arnual + Rotenbühl + Eschberg |
| 076-100 | Malstatt + Burbach + Rußhütte |

Not required by the pipeline (any slot can hold any photo). Just makes browsing the final grid feel ordered.

## On-the-go workflow

1. Take shot. Verify GPS in EXIF immediately (Gallery → Details → location pin shown).
2. Tick the slot number on paper. Note district + brief feature ("schmiedeeisernes Tor", "Jugendstil-Fenster").
3. At end of day: USB-transfer raws to PC, rename to `NNN.jpg`, drop into `raw/`, run `python process.py`, run `python bake.py --inject gallery.html`, eyeball the new tiles in browser, commit.

See `add_new.md` for full procedure.
