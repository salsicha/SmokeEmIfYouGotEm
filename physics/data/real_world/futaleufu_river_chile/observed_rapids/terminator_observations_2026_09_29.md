# Futaleufú – Terminator reach: observation summary

Reach: OSM relation 9751030, chainage 72.9–75.3 km, stations 0–2392 m. I checked the station convention against OSM: station 0 = 72.942 km and station 1200 = 74.142 km. Lateral positions are given facing downstream. From about station 1000 the river flows west, so **river left = south bank**.

Full detail and source lists are in `futaleufu_terminator_observations.json`. This file covers 28 features, 17 videos and 7 photos.

## How the stations were placed

- **Distance-marker scaling:** I scaled GoRafting's km markers (by Steve Merrow) between two OSM anchors: the Río Azul confluence (station −5897) and the Zapata footbridge (station 4666).
  - That gives: Terminator staging eddy ~644, entrance ~886, mid-rapid scout ~1128, Son of Terminator (T2) ~1371, Khyber Pass ~1661, Himalayas ~1855, Chucao Beach ~3793.
- **Independent checks that agree with that scaling:**
  - **Approach landmarks:** GoRafting describes a tall cliff at a 90° left turn, then a rock outcrop on river left where the river bends right. The centreline has exactly this: a 90° left bend at station ~0 and a right bend at 600–800.
  - **Geotagged photo:** the Commons photo *Futa Terminator.jpg* shows a kayaker in Terminator. The camera was on the right bank at station 1304, looking south.
  - **Your Sentinel-2 data:** strongest whitewater at 1000–1500, a pool-like 3 % at 1500–1750, and 19 % at 1750–2000.
  - **OSM channel outline:** about 80 m wide at 1100–1300, pinching to about 40 m at 1400 and 1600. This matches Expediciones Chile's note that Terminator narrows toward the bottom, building big waves and strong current.
- **Conflicting source:** Whitewater Guidebook's mile markers put Terminator at about the same place (~1144). However, they put T2, Khyber and Himalayas about 1 km further down (~2380, ~2730, ~2900), which would push Khyber and Himalayas out of the reach. Each affected feature records this in its `conflicts` field.

## Features (station ± uncertainty, confidence)

| Station | Feature | Lateral position | Notes | Confidence |
|---|---|---|---|---|
| 0 ± 120 | Approach cliff at the 90° left bend | cliff probably on the right (outside of the bend) | landmark | medium |
| 500 ± 200 | Terminator Wave (surf wave) | eddy on the left | III (one trip report says IV) | low–med |
| 650 ± 150 | Rock outcrop on river left at the right bend | left | landmark | medium |
| 650 ± 150 | Staging/scout eddy and upper portage trail | right | large eddy; trail goes into the trees | medium |
| 820 ± 150 | Final eddy above the entrance | left | ferry across from the right | med–low |
| 880–1700 (core 1000–1450) | **Terminator** | full width, 55–80 m | V overall (centre V+, left sneak IV/IV+); length reported as 0.5 mi to ~1 km; ~15–20 m drop (SRTM, rough) | high |
| 890 ± 150 | Entrance | multiple channels; kayaks far left, rafts in the second channel from the left | IV; horizon line at the top | medium |
| 990 ± 150 | Boulder pool / mid-rapid Scout Eddy; left-bank portage | left | about 100 m below the entrance | medium |
| 1150 ± 150 | Entry boulder with a hole that depends on flow | ~20 m out from the left edge | IV+ | med–low |
| 1150 ± 150 | Two offset holes (NYT account) | left | — | low–med |
| 1200 ± 150 | Rock garden (boulder chutes and slides) | left | — | med–low |
| 1250 ± 150 | Crux ledge / "Goal Posts" drop | left line | ~3 m ledge with a pillow rock | med–low |
| 1260 ± 150 | Crux hole below the small left boulder | just right of the left line | "surprisingly powerful" | med–low |
| 1300 ± 150 | **Typewriter** lateral | runs out from the left bank, pushes boats left to right | surfs boats along it before releasing them | medium |
| 1320 ± 150 | Pyramid Rock | left line | crux reference rock | low–med |
| 1375 ± 150 | Final chute | left-centre | — | low |
| 1230 ± 200 | **Terminator Hole** | centre to right-centre | held the 1985 raft ~30 min; very hard to exit | medium (low for station) |
| 1100–1450 | Centre-line waves | centre | biggest waves on the river; kayak-only line | medium |
| 1200 ± 200 | High-water far-left line: hole, eddy, ~2 m boof | far left | opens at high water | low–med |
| 1350–1700 | Constricted runout | full ~40 m channel | huge waves, strong current, swims up to ~1 km | med–low |
| 1400 ± 250 | **Son of Terminator (T2 / Lower Terminator)** | work left, exit left-centre | IV at 300–500 m³/s (III at low water); offset holes; boulders become pour-overs at high water | med / low–med |
| 1600 ± 150 | Pool above Khyber Pass | right | — | med–low |
| 1725 ± 250 | **Khyber Pass** (also spelled Kyburz / Keiber's) | holes on the left and left-centre; kayak sneak along the right shore | IV/IV+ | medium / low–med |
| 1750 ± 250 | China Hole | left to left-centre | recirculating; a no-go | low–med |
| 1900 ± 250 | **Himalayas** | centre | IV big-wave train; waves up to ~4.5 m ("15-foot"); pool below | medium / low–med |
| 2250 ± 200 | Pool and calmer water | full width | — | med–low |

## Named rapids outside the reach

| Rapid | Station | Section |
|---|---|---|
| Asleep at the Wheel | ~−3100 | above the reach |
| Entrada | ~4800 | Bridge-to-Bridge |
| Pillow (Cojín) | ~6250 | Bridge-to-Bridge |
| Mundaca | ~8200 | Bridge-to-Bridge |
| Más o Menos | ~11,680 | just below Puente Futaleufú (station 11,598) |
| Casa de Piedra | ~13,200 | below Puente Futaleufú |
| El Trono | −10,495 | upstream (OSM node) |

- **"Pillán":** no source found. It is probably a mix-up with Pillow.
- **"Pillow Rock" (Class III):** mentioned in one trip report before Terminator Wave; I could not locate it.

## Flow

- **Commercial range:** Earth River gives about 7,000–18,000 cfs (≈200–510 m³/s), with February the lowest month (7–14k cfs).
- **Typical flow:** Whitewater Guidebook calls about 15,000 cfs (≈425 m³/s) typical.
- **Mean flow:** about 373 m³/s at the border (Spanish Wikipedia).
- **Levels are set by the Argentine dam.** Guides describe them by turbine "tubes" (1–4) and by the stick gauge at Chucao Beach (high ≥ 70). Videos label level 90 and level 130 as high water.
- **Your 400 m³/s ≈ 14,100 cfs** is medium-high, near "typical":
  - Rafts still use the left sneak through Terminator.
  - The far-left high-water line starts coming in toward 500 m³/s.
  - T2 has more holes, and its boulders are close to pouring over.
  - The Himalayas waves are large.
- **Image day was low water.** The La Frontera gauge is upstream of the Espolón and Azul tributaries, so 163 m³/s there means low water in the reach. At that flow T2 and Himalayas probably break less than they would at 400 m³/s.

## Banks and vegetation

- **Rock:** Terminator is framed by cliffs, with a cliff at the top bend and a bedrock outcrop on the left at ~650. The channel is full of very large granite boulders, some described as black, some as white and sculpted. The NYT account describes granite rising from the banks.
- **Waterline:** forest runs to the waterline. Portage trails pass through trees, and one guide describes lush forest pressed against the banks. The NYT account mentions willows overhanging the water.
- **Left bank:** steep below the mid-rapid scout (the portage trail's final descent is steep).
- **Right bank:** a bench with pasture and hamlets 150–250 m back from the water: Arrayán at ~770, El Azul Sur at ~2890, the Bio Bio camp at ~3060. Ruta 231 runs 0.5–1 km back.
- **Species:** regional only, not documented at the rapid: coihue (*Nothofagus dombeyi*), ciprés de la cordillera (*Austrocedrus chilensis*, near its southern limit), lenga higher up, ñirre on poor or wet ground. The hamlet name "Arrayán" weakly suggests arrayán along the creeks.
- **Land use:** fires between about 1930 and 1965 cleared forest for pasture, leaving a mix of pasture and regrowth.

## Top videos (no per-rapid timestamps were available from chapters, comments or captions)

1. https://www.youtube.com/watch?v=lhnl1XFnMCA — *Futaleufu Rapids the Top Six* (Expediciones Chile, drone, narrated)
2. https://www.youtube.com/watch?v=EgI5c3BX_JY — *Futaleufu Terminator Section* (kayak: Terminator → Khyber → Himalayas)
3. https://www.youtube.com/watch?v=bNHynY1ySGo — *Rafting the Terminator* (filmed February 2020, the same month as the Sentinel-2 image)
4. https://www.youtube.com/watch?v=TOl7qu3nzzI — *Creature Crafts Running Terminator and Himalayas* (third-person footage plus commentary)
5. https://www.youtube.com/watch?v=7eNuR73hmxk — *TERMINATOR … Full high water (level 130)* (centre line)

Also worth a look: https://vimeo.com/230659488 (Expediciones Chile, *Terminator – Class V+*), whose description is the best single written account of the rapid.

## Photos

- **Commons *Futa Terminator.jpg*** (CC BY-SA 3.0): geotagged at station 1304, right bank, looking south.
- **Flickr erikmeldrum 287046771** (CC BY-NC-ND 2.0): Terminator. Licence allows reference viewing only.
- **Commons pasarela photo** (CC BY-SA 3.0): Zapata footbridge, station ~4697.
- **Dick Culbert, CC BY 2.0:** the Río Azul confluence and a suspension bridge (upstream context).
- **Bio Bio camp photo** (CC BY-SA 4.0).
