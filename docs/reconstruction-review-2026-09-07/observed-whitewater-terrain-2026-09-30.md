# Expected whitewater, terrain and vegetation on the five international rivers

September 30, 2026. **Implemented, not accepted.** This continues
[observed-rapids-2026-09-29.md](observed-rapids-2026-09-29.md), which built
observed-rapid catalogues for the five short evidence reaches. Three gaps
were left open, and this pass closes them:

1. The 30 km `L_Zambezi` run (Boiling Pot to Mukuni Beach) was not covered.
   - Its 25 rapids sat at stations digitised from a stylised outfitter map.
   - Its procedural water broke weakly at most of them.
2. The calibrated whitewater display gain (0.25) was never applied.
3. The Zambezi upper gorge's walls were a 6 m step and a flat 60 m shelf.
   They were not the observed basalt cliffs.

Section 7 (October 1) then fixes five gaps found in this pass:
- the upper gorge's invisible observed whitewater;
- `L_Zambezi`'s bank-to-bank lace, tan walls and missing waterline fringe;
- the sparse Pacuare forest;
- the mossy-tan rock;
- the upper gorge's green October trees.

The brief is unchanged. Bathymetry is unavailable, so every rapid is
reconstructed from observations: imagery, guidebooks, outfitters, trip
reports and video.

## 1. Zambezi reference run: all 25 rapids at their observed stations

### What was wrong

The run's rapid stations came from digitising
`victoria-falls-rapids-map.pdf`. The pin spacing was scaled to a 17-mile run.
That map is stylised and not georeferenced. The observations place most rapids
elsewhere:

| rapid | digitised (m) | observed (m) | moved (m) | confidence |
| --- | --- | --- | --- | --- |
| 1 Against the Wall | 0 | 160 (control; span 221-353) | +160 | medium-high |
| 2 The Bridge (Between Two Worlds) | 693 | 418 | -275 | medium-high |
| 3 Rapid 3 | 1,360 | 616 | -744 | medium-high |
| 4 Morning Glory | 1,704 | 1,609 | -95 | medium-high |
| 5 Stairway to Heaven | 2,882 | 3,136 | +255 | medium-high |
| 6 Devil's Toilet Bowl | 4,751 | 4,710 | -41 | medium |
| 7 Gulliver's Travels | 6,490 | 6,140 | -350 | medium |
| 8 Midnight Diner | 7,562 | 7,770 | +208 | medium |
| 9 Commercial Suicide | 8,411 | 8,590 | +179 | medium-high |
| 10 Gnashing Jaws of Death | 9,241 | 9,310 | +69 | medium |
| 11 Overland Truck Eater | 10,288 | 10,560 | +272 | medium |
| 12 Three Ugly Sisters | 11,932 | 12,040 | +108 | low |
| 13 The Mother | 12,414 | 12,710 | +296 | low-medium |
| 14 Surprise Surprise | 14,343 | 13,640 | -703 | low-medium |
| 15 The Washing Machine | 16,146 | 15,820 | -326 | low |
| 16 The Terminators | 16,921 | 16,120 | -801 | low-medium |
| 17 Double Trouble | 17,573 | 17,170 | -403 | medium |
| 18 Oblivion | 18,776 | 18,370 | -406 | medium |
| 19 Rapid 19 | 21,274 | 22,470 | +1,196 | low |
| 20 Rapid 20 | 21,879 | 22,950 | +1,071 | low |
| 21 Rapid 21 | 22,448 | 23,960 | +1,512 | low |
| 22 Morning Shave | 24,009 | 24,470 | +461 | low-medium |
| 23 Morning Shower | 24,811 | 25,250 | +439 | low |
| 24 Rapid 24 | 25,635 | 27,450 | +1,815 | low |
| 25 Rapid 25 | 27,359 | 28,270 | +911 | low |

- **The run ended too early.** The digitised end of the run was 27,359 m.
  Rapid 25 is at about 28.3 km, and Mukuni Beach (the take-out) is at
  28.85-29.0 km on river left. The scenario now finishes at 28,950 m.
- **Stairway to Heaven.** The 2026-09-28 audit tied it to persistent
  Sentinel-2 whitewater at 2.7-2.8 km. That whitewater is the ZESCO
  power-station tailrace cascade (route 2,673 m). Projecting the upper-gorge
  observations onto the route puts Stairway's lip at about 3,145 m, where
  Sentinel-2 also shows whitewater (3.15-3.25 km).
- **Names.**
  - "Between Two Worlds" is Rapid 2 in every operator source. Rapid 3 is
    unnamed.
  - "The Last Straw" (Rapid 19) is not attested anywhere; Rapid 19 is
    unnamed.
  - The stylised map's labels stay as the digitisation's `pdf_label` and as
    aliases.
- **Classes.** These are now the low-water classes the run models, from
  outfitter and guidebook sources. For example, Rapid 1 is IV, 6 is III-IV,
  16 is III and 18 is IV-V.

### Observations used

The research record is
`physics/data/real_world/zambezi_batoka_gorge/observed_rapids/batoka_run_observations_2026_09_30.json`
(and `.md`). Every fact carries its source and a confidence. Stations are on
the route (`route_stationing.json`), which the run's coordinate map follows
to within about 10 m.

- **Sentinel-2 whitewater at low water.** The scenes are 2024-10-08
  (203 m³/s) and 2025-10-03 (283 m³/s). The channel's water pixels are
  projected onto the route. The persistent runs are 0-50 (the falls),
  1.65-1.75, 2.70-2.80 (the tailrace), 3.15-3.25, 4.75-4.80, 6.15-6.40,
  6.75, 7.80-7.90, 8.60-8.80, 10.65-10.75 and 18.40-18.45 km.
- **Landmarks.**
  - OpenStreetMap side-stream confluences: Masuwe on river right at
    8.79 km, at the foot of Rapid 9; Songwe on river left at 9.78 km, below
    Rapid 10.
  - The Taita Falcon Lodge GPS fix, "above rapids 16 & 17", at route
    16,959 m.
  - The Batoka scheme's water-surface profile.
- **Outfitter kilometres.** Rapid 11 is at 10 km. Bobo Beach is at 25 km.
  Rapid 25 and Mukuni Beach are at 30 km (Sierra Rios). The whitewater
  guidebook puts Rapid 25 at mile 17.
- **Feature detail.** Outfitter, guidebook, trip-report and video
  descriptions give each rapid's holes, waves, laterals, pour-overs, sides
  and lines. The best per-rapid video is Travel to Paddle Part 2
  (`ptfhEvCf02s`), whose chapters cover Rapids 11-21.

### What was built

- **Catalogue.** `build_zambezi_run_observed_rapids.py` writes
  `observed_rapids/batoka_run_observed_rapids.json`
  (`raftsim.observed_rapid_features.v1`, scenario frame). It holds:
  - `rapid_stations`: the observed control station, span, class, confidence
    and evidence for each rapid;
  - 30 rapid spans, including 3.5, 4b, Stairway's approach, 5.5 and the
    upper-gorge reach-end rapid;
  - 78 features.
  - Rapids 1-5 are the upper-gorge catalogue, moved onto the route by
    projecting its evidence midline.
- **Procedural water.**
  - `zambezi_reference_map.py` now places each rapid's bounded procedural
    jump at its observed station. Rapid 1 keeps its control at 160 m, behind
    the calm launch apron.
  - The scenario carries the observed station, span, evidence and confidence
    for each rapid. The digitised station is kept as
    `digitised_map_station_m`.
  - All 25 transitions still satisfy the live breaking contract (upstream
    Froude about 1.8, tailwater about 0.82). The safe launch apron is
    unchanged.
- **Markers.**
  - The named-rapid registry now prefers the catalogue's stations
    (`observed_stationing_source`, station kind
    `observed_whitewater_landmarks_and_outfitter_km`).
  - The committed editor markers, the editor geometry and the
    simulator-review runs were regenerated.
  - `place_zambezi_observed_rapid_markers.py` moves the saved map's 25
    hidden markers and relabels them. That avoids regenerating the 30 km map.
- **Observed whitewater.** `export_zambezi_run_observed_whitewater.py`
  writes the curved observed-whitewater layer
  (`observed_whitewater_normal_big_water.bin`, 2 m x 4 m). It includes broken
  water across each rapid by class, a white core behind every hole and
  pour-over, crest caps along wave trains, and bands along laterals.
  - Every rapid has whitewater in the layer, with mean coverage 0.08-0.34
    by class.
  - The procedural field and its manifest are unchanged by this layer.
- **Finish.** The frontend scenario finishes at Mukuni Beach (28,950 m).

## 2. Display gain applied

`kObservedWhitewaterDisplayGain = 0.25` is now the gain on all six maps. That
covers the five evidence reaches and `L_Zambezi`. The 2026-09-29 overhead
renders measured 0.25 as matching the photographed white share; the former
0.9 rendered large rapids as one white sheet. The saved maps' water configs
were set with `set_observed_whitewater_gain.py` (and the Zambezi marker
script), and the editor builder writes the same constant.

## 3. Zambezi upper gorge: basalt walls reconstructed from observations

### What was wrong

GLO-30 (30 m radar, with water edited) cannot resolve the gorge. Over the
reach it is flat at water level for 40-60 m beside the Sentinel-2 water,
then rises smoothly 85-115 m to the rim. To stop the cook flooding, the
evidence grid raised a 6 m wall at the wet edge. That left a flat 60 m shelf
at +6 m along both banks, under smooth radar slopes.

The observations describe:
- near-vertical black to dark-grey basalt walls about 100-120 m high, banded
  by stacked lava flows;
- a bare, scoured band of basalt and boulders at the waterline;
- talus aprons carrying woodland;
- a few small pale beaches.

### Method

`reconstruct_zambezi_gorge_walls.py` keeps what GLO-30 still measures. That
is the rim height (the gorge depth D) and where the smeared wall crosses
mid-height (d_mid); a blurred step keeps its mid-height position. Both are
measured per 25 m of station and side and smoothed over 150 m.

| | depth D, p10 / p50 / p90 | d_mid from the water, p10 / p50 / p90 |
| --- | --- | --- |
| river left (Zambia) | 51 / 88 / 105 m | 27 / 64 / 84 m |
| river right (Zimbabwe) | 40 / 67 / 101 m | 19 / 70 / 103 m |

For each dry cell, the new profile, moving away from the water, is:
- **The cook's 6 m bank band:** unchanged, so the cook and runtime atlas stay
  valid.
- **Talus apron:** 36°, up to 35 % of the depth, with ±0.5 m blocky rubble.
- **The cliff:** lava-flow units 13 m high (±30 %), each an 84° face and a
  1.8 m ledge. Its mid-height lies at d_mid, with a bounded ±7 m wander for
  buttresses and embayments. It takes the upper 65 % of the wall ("black
  vertical cliffs sit above scree/talus slopes"). Above the talus top, a 14°
  shoulder runs to the cliff foot; the first in-game survey showed that a
  flat shelf there read as a terrace.
- **Above the rim:** the profile blends back to GLO-30 over 25 m. The cliff
  tops out at the local plateau (the GLO-30 maximum within 40 m), so it never
  stands as a lip above a lower rim.
- **Beaches:** at the observed pale patches (790 L, 2,000 L, 2,850 R and
  3,170 R), the bank slopes gently from +0.6 m instead.

All profile parameters are smoothed over 21 m of dry ground. That removes the
straight seams where the nearest water cell switches at hairpins.

Changed cells are class 6: "gorge wall reconstructed from observations". The
counts are:
- 118,289 cliff;
- 559,282 talus;
- 223,054 rim blend;
- 3,068 beach.

The terrain range is unchanged (758.9-905.0 m), so the Landscape relief, the
vertical offset and the editor constants stay the same.

### Export

`export_zambezi_gorge_wall_terrain.py` regenerates the 2017² heightfield the
same way the exporter does. It also recolours the drape on the walls, with
inferred colours:
- cliffs one dark basalt tone that varies only over tens of metres along the
  wall, with rust staining. A near-vertical face samples a 1 m strip of a
  top-down drape over its whole height, so pixel-scale noise was stretched
  into blocks down the face in the first survey; the ledges in the geometry
  carry the banding instead;
- talus 55 % grey-brown rubble over the image colour;
- beaches pale sand.

It re-lowers the GLO-30 backdrop under the new edge. The canopy was re-placed
on the new terrain with `build_zambezi_evidence_dressing.py`. The cliff zone
carries no trees (bare basalt), so there are 8,577 trees and 2,467 shrubs,
down from 8,883 and 2,811.

## 4. In-game survey of all six maps (2026-10-01)

`RaftSim.SurveyStations` (new) walks the raft to an explicit station list:
each map's rapids and landmarks. At each station it takes chase, side and a
new wide view (`RaftSim.SurveyWideShot 1`, 45 m upstream and 22 m up). All
six maps were surveyed with every station reached:

| map | stations | anomalies |
| --- | --- | --- |
| `L_Hance` | 10 | 0 |
| `L_UpperHuacas` | 11 | 1 |
| `L_Terminator` | 14 | 3 |
| `L_LavaCanyon` | 13 | 0 |
| `L_ZambeziUpperGorge` | 13 | 0 |
| `L_Zambezi` | 26 | 6 |

Findings against the observations follow.

- **Colorado (Hance).**
  - **Whitewater:** the main rapid at 700-850 m and Son of Hance at about
    1,300-1,380 m are white with dark tongues between, and the tail waves
    show at 1,050 m. At the gain of 0.25 nothing reads as one sheet.
  - **Terrain and vegetation** match the observations:
    - red Hakatai slopes and cliffs on river right;
    - the Red Canyon sand beach and fan on river left;
    - the dark Upper Granite Gorge walls downstream;
    - sparse desert scrub with a greener riparian edge above the rapid.
  - **Remaining artifact:** hard-edged dark parallelograms on some upper
    canyon walls.
- **Pacuare (Upper Huacas).**
  - **Whitewater** is present at Double Drop, Upper Huacas, Lower Huacas and
    Upper and Lower Pinball.
  - **Huacas Falls was missing.** Observed: a 30-46 m fall on river right
    between the Huacas rapids, which rafts paddle under. Added below.
  - **The forest reads sparse.** Trees are widely spaced on pale ground,
    where observers describe dense rainforest spilling down the walls. Not
    changed here.
- **Futaleufu (Terminator).**
  - **Whitewater** is present at Terminator Wave, the bend, the Terminator
    core (mostly white, as described for class V+), Khyber Pass and
    Himalayas.
  - **Vegetation:** forest runs to the water, with grassy benches.
  - **Rock was missing:** the observed top-bend cliff, the river-left
    outcrop at the right bend, the granite banks and the bank boulders.
    Added below.
- **Chilko (Lava Canyon).**
  - **Whitewater** is present at Bidwell, the White Kilometre and through the
    White Mile.
  - **Vegetation:** the forest follows the observed aspect rule (dense
    conifers river right, open slopes river left).
  - **The waterline talus was missing:** the dark basalt boulder talus and
    the rockslide fans. Added below.
- **Zambezi upper gorge.**
  - **Walls:** the reconstructed gorge walls stand where the shelf was. The
    first build's cliffs read tan with blocky dark patches and a flat bench
    along the wall; both were corrected above.
  - **Whitewater:** on this Cartesian map the layer at 0.25 shows as lace
    only, so overhead renders (`RaftSim.SurveyTopShot`, 70 m above the raft)
    were taken at Morning Glory (1,500 and 1,600 m) and Stairway to Heaven
    (2,930 and 2,990 m) at review gains of 0.25, 0.5 and 0.8.
    - The three renders are identical. The observed-whitewater floor is
      written to the carrier's vertex foam, but the Cartesian live core takes
      its foam from the GPU foam transport, so on this map the layer loads
      and has no visible effect. The 2026-09-29 note that the upper gorge
      "loads the layer" was true but its appearance was never verified.
    - The whitewater seen there is the cook's own breaking. The cook breaks
      at every catalogued rapid except 5.5 and the reach-end rapid. The
      overhead renders show it as lace through Morning Glory and Stairway,
      weaker than the photographs.
    - Making the floor reach the Cartesian core needs a change to its foam
      path or material; it is not made here.
- **Zambezi 30 km run.**
  - **Whitewater:** every rapid station is white and the Mukuni Beach finish
    is calm.
  - **Too uniform:** the class broken water filled the whole ~144 m
    procedural channel as a uniform lace, so the layer's broken water is now
    confined to the 30-60 m low-water river width with calm margins.
    - A second survey still shows lace across the full width at each rapid,
      margins included. That is the procedural field's own foam: every
      rapid's bounded jump spans the uniform 144 m channel.
    - So the layer adds each rapid's cores, holes and waves, while the
      overall look stays a generic lace. That is a limit of the seed (see
      Limits).
  - **Terrain and vegetation:** the gorge is tan and brown dry-season
    slopes, which matches the August-December imagery. The black basalt
    cliffs and the green waterline fringe are not represented (see Limits).

## 5. Added from the survey

- **Futaleufu observed rock** (`build_observed_rock_placement.py`). The six
  reviewed rock meshes are fitted to described sizes on the banks, never
  inside the cooked water, and are visual only. There are 84 rocks:
  - the top-bend cliff on river right (stations 0-170, 14 blocks, 9-15 m
    long and 9-16 m high);
  - the river-left outcrop at the right bend (580-760 m, 16 blocks, 12-20 m
    long and 8-15 m high);
  - granite banks on river left through the Terminator (980-1,460 m,
    22 blocks);
  - large boulders on river right (900-1,700 m, 18);
  - boulders on both banks at Khyber Pass and Himalayas (14).
  - 25 canopy trees inside the large blocks were removed.
- **Chilko observed rock** (1,510 boulders):
  - dark basalt boulder talus at Bidwell (300, 1.2-3.2 m);
  - the landslide cobble apron on river left above it (60);
  - boulder and cobble banks along the reach (900);
  - the rockslide fans on river right at 2,640-2,790 m (140) and at the White
    Mile head (110).
  - The first build placed 424, which the second survey showed too sparse
    to read as the observed talus banks.
- **Huacas Falls** (`add_pacuare_huacas_falls.py`).
  - At station 820 m on river right, the IGN wall rises about 40 m within
    31 m.
  - The cascade is painted into the drape along its fall line: white
    aerated water streaked down the fall, 6-10 m wide, over dark wet rock.
  - The editor places spray mist (`NS_RaftSim_AeratedMist`) at the plunge
    and on the lower cascade.
  - 6 trees and 6 shrubs were cleared from the fall line.
  - Its appearance is inferred; the terrain and water are unchanged.

The editor places both kinds of rock with the new `AddObservedRockShells`,
from `*_observed_rock_placement.json`
(`raftsim.observed_rock_placement.v1`). The P4 map tests check that the rock
uses six variants, is visual only and is placed, and that the falls have
their three mist emitters.

## 6. Verification (2026-10-01)

**Drapes need importing.** Evidence drapes reach the game only through
`unreal/Scripts/install_evidence_drape.py`, which the map rebuild does not
run.
- Until the new upper-gorge and Pacuare drapes were imported, the third
  survey still showed the old Sentinel-2 drape stretched into tan and dark
  blocks down the new cliffs, and no painted cascade at Huacas Falls.
- After the import, the fourth survey shows:
  - the upper-gorge walls as dark basalt, banded by the ledge shading;
  - Huacas Falls as a white cascade down the river-right wall into the
    river, seen from upstream at 760 and 790 m.

**Feature surveys** (`RaftSim.SurveyStations` with wide views):
- **Futaleufu:** the top-bend cliff blocks on river right, the river-left
  outcrop at 650-700 m and the granite boulders on the Terminator banks are
  all in view.
- **Chilko:** the 1-3 m talus is present but subtle in the wide views. It is
  close in tone to the banks and small at 50 m range.
- **Rock colour:** the reviewed rock material is a mossy tan. It has no tint
  parameter, so the granite (grey-white) and the basalt (dark) are not
  colour-matched.

**Automation** (`RaftSim.P4.RiverMapLoads`, `RaftSim.M6.*`, run in the
editor):
- **Pass:**
  - `L_Hance`;
  - `L_UpperHuacas`, including three mist emitters and three falling-water
    strands;
  - `L_Terminator`, with 84 observed rocks in six visual-only variants;
  - `L_LavaCanyon`, with 1,510 rocks;
  - `L_ZambeziUpperGorge`, with 11,044 canopy rows;
  - `M6.CareerCatalog` and `M6.ProgressionMigration` (the run finishes at
    Mukuni Beach).
- **Fail:** `L_Zambezi`, only on its start-apron spray emitters (0 of 6).
  This is the failure known since 2026-09-27. Its new observed-whitewater
  gain check passes.

**Python:**
- These new tests pass:
  - `test_zambezi_observed_run_and_walls.py` (the 25 observed stations, the
    procedural controls, the layer covering every rapid, the walls);
  - `test_observed_rock_and_falls.py`.
- The existing reach, catalogue and registry tests pass, except four in
  `test_zambezi_reference_map.py`. Those already failed before this work:
  they hash-lock a map and sources that changed in earlier commits, and one
  asserts a C++ line no longer in the source.

## 7. Follow-up fixes (2026-10-01)

Five gaps left open above were then fixed. Each was checked with a fresh
in-game survey (`RaftSim.SurveyStations`, chase, wide and overhead views).

### Upper gorge whitewater

- **Cause.** The Cartesian live core draws the foam of the GPU moving detail
  (`URaftSimStatefulDetailComponent`). That foam comes from the detail's own
  breaking source: the flow's entrainment potential merged with the accepted
  crest source. The observed layer only floored the carrier's vertex foam,
  which this core never draws.
- **Fix.** The river water config has a new `ObservedWhitewaterEntrainmentGain`.
  - The adapter samples gain × the observed fraction.
  - The moving detail merges that sample into its breaking source as a third
    estimate of the same source: a maximum, not added production.
  - The detail then transports and decays the foam as before.
  - Render-only; review override `-RaftSimObservedEntrainmentGain=<g>`.
- **Calibration.** Overhead and chase renders at Morning Glory (1,500 and
  1,600 m) and Stairway to Heaven (2,930 and 2,990 m), at gains 0, 0.5 and 0.9:
  - 0 is the cook's own lace;
  - 0.5 gives heavy broken water that keeps its lace texture;
  - 0.9 is one white sheet through Stairway.
  - `L_ZambeziUpperGorge` uses 0.6. The calm pool at 2,200 m stays calm.

### `L_Zambezi` (30 km run)

- **Lace.** Two causes, both in the procedural seed
  (`zambezi_reference_map.py`):
  - Each rapid's jump lane was a flat quartic about 100 m wide across the
    144 m channel.
  - The rapid's surface relief (the swell through the rapid and the jump
    profile) was a station-only profile, so the runtime's relief foam painted
    bank to bank.

  Now each rapid is a deep, fast Gaussian tongue (sigma 20 m; 26 m for
  river-wide features) between shallow boulder shelves (0.75 m, Froude 0.22)
  with slow eddies below the jump. The surface relief is carried by the
  tongue only. The centreline, and so the raft's line and every transition
  record, is unchanged. The cooked fields, their manifest hash, the streaming
  manifest and the observed layer were regenerated.

  Result: the lace is centred, with calmer green margins, at Rapid 13
  (12,020 m) and Rapid 17 (18,350 m). It still spreads bank to bank at the
  bigger rapids. The live solve evens the rapid's surface drop across the
  channel, and the relief foam follows it. A higher foam Froude onset (1.1)
  made no visible difference and was reverted. Deferred to a later water pass.
- **Walls.** The Batoka basalt material read tan for three reasons:
  - its rock photos (AerialRocks02 and Rock037) are warm tan, and 10-22 %
    of the tan drape still blended into the basalt;
  - the runtime cameras' shared manual exposure (+1.25 EV with bilateral
    local exposure, set for South Fork) lifts any dark surface in the strong
    Zambezi sun to light grey. A probe at a sixth of the basalt value turned
    shadowed walls black but left sunlit walls light;
  - the warm haze (0.58/0.50/0.39) coloured the distant walls. Haze density
    turned out to matter little near the river: the fog thins quickly with
    height.

  Changes:
  - The basalt tint is now cool (0.20/0.235/0.30), cancelling the photo's
    tan.
  - The rust weathering accent is weaker (0.30/0.27/0.28 at 0.20).
  - Basalt coverage is at least 0.97.
  - The rock colour is desaturated 0.82 and scaled 0.62.
  - The haze is the dry season's thin grey smoke (density 0.0007, colour
    0.50/0.52/0.54).
  - `L_Zambezi` sets the new `PresentationExposureBiasOffset` to -0.5 EV,
    which the guide and survey cameras add to the shared exposure.

  Result: the walls render about 27 % darker and greyer, and black in shadow,
  but still grey-brown in direct sun. The foam no longer clips.
- **Waterline fringe.** The other `L_Zambezi` layers start 12-26 m back from
  the water or cover only the launch and camera windows. The new
  `AddZambeziWaterlineFringe` places patchy green riverine shrubs and riparian
  trees on the lowest dry ground within about 15 m of the water, along the
  whole run:
  - about a third of the bank is left as bare boulders between patches;
  - 5,008 shrubs and 651 trees;
  - positions and species are inferred.

### Pacuare forest

`densify_pacuare_rainforest.py` rebuilds the canopy's structure on the same
measured positions and IGN cover (structure inferred):
- **Canopy:** crown radius equal to the neighbour spacing (4.5-10 m, median
  6.6 m), so crowns overlap into a closed canopy.
  - Height 3.4 × radius + U(0, 6) m, 18-38 m (median 25 m), for the
    Caribbean-slope wet forest.
- **Sub-canopy:** 18,843 trees of 9-16 m in the gaps.
- **Understory:** two 4-8 m shrubs per canopy tree (53,507).
- **Forest floor:** the drape under the crowns is shaded (91 % of the drape)
  instead of the hazy orthophoto's pale ground.
- **Clearances:** 4 m from the cooked water and 9 m from the Huacas Falls fall
  line. Crowns beside the fall are capped so they cannot close over it.
- In game the walls carry a tall, closed, layered forest. A few steep or
  bare-ground slopes stay open.

### Rock colour

`M_RaftSim_ReviewedRockTinted` (`unreal/Scripts/create_tinted_rock_materials.py`)
keeps the reviewed scan's normal and roughness. It remaps the scan's luminance
(cracks, facets and lichen pattern, without the moss hue) between two
parameter colours. Two instances are used:
- grey granite on the Futaleufu: 0.12-0.42;
- dark basalt on the Chilko: 0.026-0.125.

The editor applies them to each reach's observed rock, reviewed rock,
waterline-structure and shoreline-gravel components. The colours are
approximate, from descriptions and photographs.

### Upper gorge trees (October)

The canopy was placed inside the May 2025 woodland cover, when the whole gorge
is green. `apply_zambezi_october_leaf_state.py` sets each tree's leaf state
from the mean NDVI of the two October Sentinel-2 scenes (2024-10-08 and
2025-10-03) at the tree:

| leaf state | October NDVI | trees |
| --- | --- | --- |
| green | ≥ 0.5 (riverine and spray-fed) | 1,659 |
| a few dry ochre leaves | 0.33-0.5 | 2,708 |
| leafless | < 0.33 | 4,210 |

- Shrubs with October NDVI below 0.5 become leafless thorn scrub (2,024 of
  2,467).
- The new dry-season forms (`DrySeasonBareTree`, `DrySeasonSparseTree`,
  `DrySeasonScrub`) are procedural trunk, branch and twig geometry with grey
  bark. They are saved beside the Zambezi family; `AddEvidenceCanopy` takes
  extra tree forms and an alternate understory.
- Species and branching are inferred.

## Limits

- **Rapid stations.** These are observation-derived, not surveyed.
  - Rapids 19-25 rest on candidates (low confidence), and operators disagree
    on numbering below Rapid 21.
  - Feature laterals are described sides placed in the run's ~144 m
    procedural channel. The real river is 30-60 m wide at low water.
- **The upper gorge's observed whitewater** reaches its foam only as a
  breaking source of the GPU moving detail (section 7). The detail's
  transport and decay shape the result, so it is calibrated by eye (0.6), not
  matched to the photographed extent.
- **The 30 km run's water is still a procedural seed** with one bounded
  jump per rapid. Since section 7 each rapid is a central tongue between
  boulder shelves instead of a bank-to-bank lace. It still has no described
  holes or waves of its own, and the live solve redistributes the seed. The
  observed whitewater is render-only appearance evidence: it never reaches
  forces, contact or gameplay.
- **Rock and wall colours** (section 7) are approximate, from descriptions
  and photographs, not measured albedo. The 30 km run's walls keep the
  30 m DEM's smooth shape.
- **Vegetation structure is inferred:**
  - the Pacuare canopy, sub-canopy and understory;
  - the 30 km run's waterline fringe;
  - the upper gorge's dry-season forms.

  The upper gorge's leaf state is measured per 10 m pixel.
- **Not addressed here:**
  - the Colorado wall artifact;
  - the Zambezi upper gorge's dry channel beyond its cooked cuts.
  These remain realism gaps.
- **The gorge walls are inferred in shape.** Only the rim height and the
  wall's mid-height position are measured (GLO-30, ±2 m water).
  - The lava-flow banding is generic: 13 m units with 1.8 m ledges.
  - Cliff colour is inferred.
