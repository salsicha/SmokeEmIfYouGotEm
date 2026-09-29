# Observed rapids on the five evidence reaches

September 29, 2026. **Implemented, not accepted.** This covers the Zambezi
upper gorge, Chilko Lava Canyon, Futaleufú Terminator, Pacuare Huacas and
Colorado Hance reaches.

## Why

The user expects no bathymetry for most rivers: "most likely the only data we
will be able to find are aerial photos and videos uploaded to youtube". The
brief was to make sure every expected rapid is present, reconstructing the
missing ones from observations.

Two gaps motivated the work:
- The 10 m satellite imagery misses narrow holes and wave trains that
  outfitters, guidebooks and videos describe.
- An inferred, discharge-consistent bed smooths away the steps that make a
  rapid break, so the 2 m shallow-water solver alone does not place every
  rapid.

## What was built

1. **Observation catalogues**, one per reach, in
   `physics/data/real_world/<river>/observed_rapids/`:
   - `*_observations_2026_09_29.json` and `.md`: the research record. Named
     features, unnamed whitewater, videos and photos with times, and banks,
     terrain and vegetation, each with its sources and a confidence.
   - `*_observed_rapids.json` (schema `raftsim.observed_rapid_features.v1`):
     the rapids (station span, class, whitewater share) and the features, typed
     `ledge_hole`, `pour_over`, `boulder`, `rock_garden`, `wave_train`,
     `lateral`, `diagonal`, `drop`, `sill` and others.
   - Every feature names its sources. Positions and sizes are approximate and
     labelled as such.
   - Frames: the Zambezi catalogue uses the evidence grid's station. The four
     curved maps use the in-game (scenario) station and lateral. The
     Futaleufú rapid spans are given in the evidence frame, with
     `scenario_station_m` beside them.
   - Angle convention: a rib that leaves the river-left bank downstream
     toward the centre has a negative angle; one that leaves the river-right
     bank has a positive angle.
2. **Hydraulic reconstruction** (`observed_rapid_features.py`,
   `imprint_observed_rapids.py`): each feature is shaped into the inferred
   bed. Cells it changes get class code 5, "bed shape reconstructed from
   observations".
   - Crests are set against a previous cook's water surface and wetted width.
     They are not set against the evidence channel, which can be 2-3 times
     narrower than the water the cook carries.
   - Ledges and drops concentrate the existing fall over a short span, raising
     the bed above the step and lowering it below. Sills set a crest a
     multiple of the critical depth below the surface, for deep pools where a
     step drowns.
   - Wave trains are bed ridges with wavelength max(2πU²/g, 2π·hc, 6 m). The
     2 m solver cannot form standing waves on a flat bed.
   - Only inferred bed classes are edited: measured bathymetry, LiDAR and
     measured banks are never changed.
   - The Zambezi and Futaleufú evidence builders also take the catalogue
     (`--observed-rapids`). The drop between surface anchors is shared by
     the larger of the Sentinel-2 whitewater share and the catalogued rapid
     share, and inside catalogued rapids the inferred depth floor is 0.7 of
     the critical depth (it was 1.0, which blocked supercritical flow).
3. **Audit** with the game's breaking-site rule
   (`ARaftSimWaterSurfaceActor`): a wet cell at Froude ≤ 0.94, with a wet cell
   4 or 6 m upstream at Froude ≥ 1.12, and intensity ≥ 0.08.
   - Curvilinear cooks: `audit_observed_rapids.py` scores each catalogued
     feature's footprint, optionally against a baseline cook.
   - Cartesian cooks: `audit_cartesian_whitewater.py` scores per station bin
     and per feature.
4. **Appearance layer:** the render-only observed-whitewater floor (the
   photographed whitewater) is raised to each catalogue's expected whitewater
   (`augment_observed_whitewater.py` on curved maps,
   `export_cartesian_observed_whitewater.py` on the Cartesian Zambezi). The
   expected whitewater is:
   - broken water across each rapid, by its class;
   - a white core behind every hole and pour-over;
   - crest caps along wave trains;
   - bands along laterals.

   Every footprint is feathered (a rapid fades in and out over 20 m, the
   others over their outer quarter width). The first layers had straight
   cut lines across the river, which the survey showed at The Wall.

   It is appearance evidence only, never gameplay. The Zambezi upper gorge
   now loads the layer too: `ARaftSimWaterSurfaceActor` reads it on
   Cartesian maps whose config sets `ObservedWhitewaterGain > 0`. South Fork
   stays 0.
5. **Display gain, calibrated.** The runtime floors each vertex's displayed
   foam at gain × the layer's whitewater area fraction. At the former gain of
   0.9 the Terminator core rendered as one white sheet.

   Overhead renders there, with the layer averaging 0.71-0.74 in view,
   compared the share of 16 px blocks that are mostly white. A review-only
   `-RaftSimObservedWhitewaterGain=<g>` override allowed the comparison
   without rebuilding maps.

   | gain | blocks mostly white |
   | --- | --- |
   | none (cooked foam only) | 0.51 |
   | 0.2 | 0.71 |
   | 0.45 | 0.91 |
   | 0.9 | 0.97 |

   A gain of about 0.25 matches the photographed share and keeps the dark
   tongues between the white. **It is not applied yet.** The gain lives in
   each map's water config, so all five maps must be rebuilt. The rebuild
   failed on 2026-09-29: with C: nearly full, Windows could not grow the page
   file ("Ran out of memory ... The paging file is too small"). The maps
   and code stay at 0.9 until the rebuild runs.

## Results per reach

Breaking cells are counted with the rule above in each cook's final frame.

### Zambezi upper gorge (adopted: new cook)

Catalogue: 10 rapids, 20 features. Five sills at the heads of Rapids 1, 2, 3,
4b and 5.5, the Morning Glory bottom-hole bar, holes, laterals and wave
trains.
- The GLO-30 anchor at 1,825 m contradicted Morning Glory, so the build skips
  it (`--skip-anchor-stations 1825`). GLO-30 water in this narrow gorge is
  noisy by ±5 m.
- Cook v5: the Cartesian cook, warm-started from v4 and run for 36,000 steps.

| measure | committed (v3) | now (v5) |
| --- | --- | --- |
| surface anchors (cook - GLO-30) | -1.14 to +0.52 m (11) | -0.62 to +0.97 m (10) |
| wet IoU | 0.968 | 0.967 |
| outflow face flux | 281.0 m³/s | 281.8 m³/s |
| settling p95 abs dh | 0.016 m | 0.010 m |
| max depth | 7.2 m | 7.6 m |

Breaking cells by rapid in v5:

| rapid (station) | breaking cells |
| --- | --- |
| 1 The Wall (160-240 m) | 117, and 16 on its head bar |
| 2 The Bridge (360-440 m) | 5, and 5 on its head bar |
| 3 (560-640 m) | 2 |
| 3.5 (1,160-1,240 m) | 38 |
| 4 Morning Glory (1,480-1,600 m) | 16; top holes 4 and 9 |
| 4b (1,720-1,760 m) | 6 |
| 5 Stairway to Heaven (2,880-3,000 m) | 95 |
| 5.5 and the reach-end rapid | 0 (appearance layer only) |

- The appearance layer marks 2,686 cells (4 m) as whitewater; the photographs
  mark 435.
- **Launch:** 212.7 m, unchanged.
  - The raft's stateful water detail needs its whole 67 m source footprint
    inside one cooked live window. The export's launch rule now enforces
    that (`--detail-footprint-m`).
  - With it, 212.7 m is the most upstream valid point: 7.7 m below the Rapid
    1 head bar. A launch at 200.8 m, above the head bar, failed P4 with "No
    complete native crop for detail source footprint".
  - The inflow cut at 124 m leaves no room for a window above The Wall. The
    research places the Boiling Pot put-in at about 200 m on river left.

### Futaleufú Terminator (adopted: new cook)

Catalogue: 6 rapids, 14 features, including Terminator Hole, the crux ledge
(Goal Posts), the Typewriter lateral, T2's offset holes, Khyber Pass's main
hole, China Hole and the Himalayas waves.
- Two calibration passes of `calibrate_river_bed.py` (relax 0.7) ran on
  cooks with the features.
- The Himalayas wave train was widened from 22 to 40 m. The 400 m³/s cook
  wets about 44 m there, and the 22 m train was bypassed.

| measure | committed | now (v6) |
| --- | --- | --- |
| GLO-30 anchors (cook - GLO-30) | -1.16 to +0.82 m | -0.04 to +0.85 m |
| wet IoU | 0.940 | 0.934 |
| outlet face flux | - | 399.8 m³/s |

Breaking cells by scenario station:

| rapid (scenario station) | committed | now |
| --- | --- | --- |
| Terminator Wave (500 m) | 0 | 35 |
| right bend (650-700 m) | 0 | 49 |
| Terminator core (1,000-1,300 m) | 29 | 102 (Terminator Hole 26, Typewriter 58) |
| T2 / Son of Terminator (1,380-1,500 m) | 0 | 0 |
| Khyber Pass (1,650-1,800 m) | 78 | 22 |
| Himalayas (1,850-1,950 m) | 0 | 29 |

- **T2 is not reproduced hydraulically.** At its catalogued position the
  cook is a flat pool 6-8 m deep. The GLO-30 surface there drops only 0.47 m
  in 200 m, so pour-overs are drowned and the flow goes round them.
  - The research notes that mile-marker sources put T2, Khyber and
    Himalayas about 1 km further down.
  - T2 is carried by the appearance layer (27-36 % whitewater there).
- Khyber breaks less than in the committed cook but is still present.
- Appearance layer: 12,614 cells with whitewater (9,429 raised above the
  photographed layer).
- The Landscape relief changed by 6 cm (the bed moved). The catalogue
  constants in `RaftSimEditorEnvironmentCatalog.cpp` were updated to match.

### Chilko Lava Canyon (appearance only)

All three named rapids already break in the committed 93 m³/s cook:

| rapid | breaking cells |
| --- | --- |
| Bidwell (800-950 m) | 38 |
| White Kilometre (1,500-1,650 m) | 36 |
| White Mile (3,600-3,900 m) | 36 |

- A trial cook with the 13 catalogued features (v6) changed breaking by only
  a few cells:
  - Bidwell 38 to 42;
  - White Kilometre 36 to 34;
  - White Mile 36 to 39, plus 4 below it;
  - 650-700 m, above Bidwell: 6 to 2.
- It was not adopted. Re-exporting would also need the original LiDAR crop,
  which is larger than the archived window.
- The trial found that feature sizing must use the catalogue's flow. The
  Chilko evidence grid is built at the 45 m³/s LiDAR flight flow, but the
  game cooks at 93 m³/s. `imprint_observed_rapids.py` now sizes features for
  the catalogue's discharge and records it (`sizing_discharge_m3s`).
- The LiDAR crop was rebuilt from the archived window with the correct
  decode (base + cumulative sum of the centimetre deltas along each row). The
  rebuilt bed matches the committed scenario bed exactly.
- Appearance layer: 7,802 cells with whitewater (7,248 raised).

### Pacuare Huacas (appearance only)

- A trial cook with the named rocks (Upper Huacas bottom rock, Lower Pinball
  rocks 1 and 2), the Upper Pinball boulder garden and the Guatemala waves
  changed breaking by at most one cell per feature. It was not adopted.
- The committed cook already breaks at:
  - Double Drop;
  - Upper Huacas (33 cells at its bottom rock);
  - Lower Huacas;
  - Lower Pinball.
- The committed map also carries 719 rock shells placed from the orthophoto.
- Guatemala sits in the slack pool at the reach end (0.9 m/s); only the
  appearance layer carries it.
- Appearance layer: 15,346 cells with whitewater (7,726 raised).

### Colorado Hance (appearance only)

- A trial cook with the 14 catalogued features was **worse**.
  - The pools below the ledges and drops are 2014 sonar bathymetry, which is
    measured and never edited. So the features could only raise the inferred
    cells above each step, not lower the pool below it.
  - That lifted the whole upper reach by 0.15-0.2 m and drowned the upper
    main rapid: breaking fell from 46 to 8 cells in the Red Canyon rock
    garden, and from 10 to 0 at the centre entry pour-over.
- The committed cook breaks through the upper main rapid (680-840 m: 33, 31,
  47, 13 and 6 cells per 40 m).
- The lower main rapid and Son of Hance still do not break. There the cook
  runs 0.2-0.9 m above the 2021 DEM water surface, a structural mismatch
  against the measured bathymetry that calibration cannot remove.
- Appearance layer: 12,420 cells with whitewater (6,787 raised). It now
  covers the whole main rapid (680-920 m, including the bottom hole) and Son
  of Hance (1,280-1,400 m).

## Tool fixes found on the way

- `observed_rapid_features.Frame`: station bins without cells (gaps in a
  builder's station field, and the two ends) were averaged in as zeros. That
  pulled Hance's smoothed reference surface down to 505 m, where it should
  be about 755 m. Gaps are now interpolated and the ends edge-padded. The
  Zambezi, Futaleufú and Pacuare imprints were identical before and after.
- `augment_observed_whitewater.py`:
  - places rapids given in the evidence frame by their scenario station;
  - writes the layer beside the file and renames it (an in-place truncate
    failed while the file was mapped).
- `build_hance_curvilinear_scenario.py` sizes its grid from the channel
  extent. Rebuilds must pass `--half-width-m 80` to keep the committed
  81 x 1,257 grid.

## Terrain and vegetation

The research records bank, terrain and vegetation observations per reach
(`banks_terrain_vegetation` in each observations file). Each map was surveyed
in game (`RaftSim.SurveyReach`, chase and side views every 300-500 m) and
compared with them. Terrain and vegetation are present on every reach. The
findings follow.

- **Zambezi upper gorge:**
  - The research describes near-vertical walls of dark basalt about 120 m
    high, banded by stacked lava flows, with scoured basalt and boulder
    bands at low water and talus aprons with woodland.
  - The map shows the gorge's depth and course, but its walls are smooth
    30 m GLO-30 slopes: no cliffs, banding or talus. The inferred 6 m wall
    at the wet edge reads as a straight ledge in places.
  - The canopy follows the Sentinel-2 cover, drawn with the stylized
    broadleaf meshes on a jittered 10 m lattice.
  - Real walls would need finer terrain than GLO-30, for example stereo
    imagery or photogrammetry from the videos.
  - Beyond the 224 m live window, the cooked far-field water is paler than
    the live water.
- **Futaleufú Terminator:**
  - The research describes a benched, wider valley here, framed by cliffs
    at the top bend (station about 0) and a bedrock outcrop on river left
    (about 650 m), with old-growth forest.
  - The map shows forest down to grassy benches on both banks, consistent
    with the forest and pasture measured from Sentinel-2. The two
    cliffs are absent: they are below GLO-30's resolution.

## Limits

- Catalogued positions come from outfitter and guidebook descriptions, trip
  reports and videos, scaled onto the reach. Their stated uncertainty is tens
  of metres (T2, Khyber and Himalayas possibly about 1 km).
- Sizes are described sizes, not measurements. The Himalayas waves are
  described as up to about 4.5 m, the crux ledge as about 3 m.
- Bed features at 2 m resolution make a rapid break. They do not reproduce
  its shape wave for wave.
- The appearance layer can show whitewater where the cooked flow does not
  break. It is labelled render-only.
