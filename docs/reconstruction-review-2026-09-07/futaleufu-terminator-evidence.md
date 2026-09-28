# Futaleufu Terminator: evidence-based reach

September 27, 2026. **Implemented, not accepted.** `L_Terminator` is now a
2.4 km geographic reconstruction of the Futaleufu around the Terminator (OSM
chainage 72.9-75.3 km). It replaces the 600 m reach-local interpreted scene.

Open data here is coarse:
- **Measured:** the wetted extent and whitewater (Sentinel-2, 10 m), terrain
  and the water-surface anchors (Copernicus GLO-30, about 30 m).
- **Inferred and labelled:** the bed, the surface between anchors, the bank
  shape, boulders and the discharge.

It is not survey-grade and not accepted.

## Sources

The downloads were approved on 2026-09-26. They are archived in
`physics/data/real_world/futaleufu_river_chile/futaleufu_sources_2026_09/manifest.json`.
The GLO-30 tiles were already in `terrain/source`.

| source | what it measures | epoch |
| --- | --- | --- |
| Sentinel-2 L2A (10 m; B, G, R, NIR) | wetted extent, whitewater, colour | 2020-02-20 (163 m³/s at La Frontera), 2024-02-19, 2026-01-04 (flows not yet retrieved) |
| Copernicus GLO-30 (1 arc-second DSM, EGM2008) | terrain (canopy included); edited water surface | TanDEM-X 2011-2015 |
| OSM relation 9751030 | chainage, rapid nodes (El Trono) | 2026 |

- **No open imagery or elevation finer than 10 m exists** for the run. SAF
  sells aerial photography.
- **Gauge records (added 2026-09-28, with permission):** DGA daily flows for
  10702002 (La Frontera, at the Argentine border, upstream of the reach) and
  10704002 (ante junta Río Malito), from the CR2 Explorador Climático copy of
  the DGA record, in `hydrometric/dga_daily_flows_cr2.json`. That copy ends
  in June 2020, so it gives only the first image date: **163.4 m³/s at La
  Frontera on 2020-02-20**. The reach adds unmeasured tributaries (Río
  Espolón and smaller). The 2024-02-19 and 2026-01-04 flows need the DGA BNA
  portal, whose search needs a reCAPTCHA that the user must complete.
- **Licence:** Copernicus data (Sentinel-2, GLO-30) require attribution. OSM
  is ODbL.

## Locating the Terminator

The Terminator has no published coordinate. GoRafting's chainage (El Trono
27.5 km, Terminator 39.25 km), with El Trono at OSM 62.40 km, predicts OSM
74.15 km. `audit_futaleufu_terminator_location.py` counts Sentinel-2
whitewater pixels in a 170 m box on the centreline for every 100 m from 55
to 84 km, on each date:

- **The strongest persistent whitewater run is at 74.0-74.2 km** (29 pixels
  on average), a second at 74.6-74.8 km. The prediction falls inside the
  strongest run.
- **The indicator fires at the OSM El Trono node** (62.3-62.5 km).

The reach is OSM 72.9-75.3 km. The report is
`scenario_terminator_evidence_2026/evidence/terminator_location_audit.json`.

## Method

Scripts are numpy only. The frame is UTM 18S (EPSG:32718); heights are
EGM2008.

1. **Evidence grid** (`build_futaleufu_evidence_grid.py`, 1 m, 2,422 x
   1,777 m):
   - **Wetted extent (measured, ±5 m edges):** water (NDWI > 0.05) or
     whitewater in at least two of the three dates, bilinear from 10 m.
   - **Whitewater (measured appearance):** bright, neutral water pixels,
     averaged over the dates.
   - **Midline:** the middle of the wetted run along OSM normals, smoothed.
     OSM only orders it.
   - **Surface anchors (measured with editing).** GLO-30 edits water bodies
     flat and monotonic. The median of channel-interior GLO-30 heights per
     50 m, forced non-increasing, gives an anchor every 200 m. Their epoch
     and flow are unknown, and they are good to about ±2 m.
   - **Surface between anchors (inferred):** each drop is spread by the
     whitewater share plus a small base weight.
   - **Terrain:** GLO-30 bicubic beyond 30 m of the water. The bank zone is
     harmonic between the water edge and GLO-30 (inferred shape). GLO-30 is a
     surface model, so forest canopy is part of it.
   - **Bed (inferred):** discharge-consistent depth for 400 m³/s, the
     existing high-runnable planning band, on a smooth section. Manning n is
     0.035 in pools and 0.05 in rapids.
   - **Submerged boulders (inferred):** at the upstream edges of whitewater
     patches. Rocks and bars cannot be resolved at 10 m.
2. **Solver grid** (`build_curvilinear_river_scenario.py`): a 2 m grid of
   1,197 x 49 cells (2.39 km x 96 m). The minimum radius is 318 m, so cells
   are within 0.94-1.10 of their true length.
3. **Cook** (`raftsim_water_solver`, finite volume, HLL, MUSCL, bed-slope
   source on, 48,000 steps) and comparison (`compare_river_cook.py`,
   discharge from the exact face flux).
4. **Bed calibration:** two step-limited passes of `calibrate_river_bed.py`
   (relax 0.8, 50 m smoothing, at most 2 m per pass). They lower the
   inferred bed by station towards the reference surface. The uncalibrated
   cook ran 1.4 m high.

## Runtime integration

`export_futaleufu_evidence_runtime.py` writes:
- the cooked field;
- the render-only presentation baseline;
- the observed-whitewater field (Sentinel-2 whitewater, appearance
  evidence);
- the moving-window manifest;
- a 2017² Landscape over the 2,422 x 1,777 m window (735 m of relief);
- a 2,048² Sentinel-2 drape, albedo-scaled like the Pacuare drape;
- a GLO-30 backdrop mesh (20 m, 3 km around the Landscape).

Terrain against the solver bed in wet cells: p5/p50/p95 -0.09/0.00/+0.08 m.

`build_futaleufu_evidence_dressing.py` places the canopy:
- 41,966 trees on a 9 m lattice inside Sentinel-2 forest cover (NDVI > 0.6
  and green reflectance below 0.062; pasture is brighter);
- 13,359 understory shrubs within 200 m of the water.

At 10 m no crowns are resolved, so the positions, sizes, heights and species
are inferred; only the forest extent is measured. The shared editor helper
(`RaftSimEditorLandscapeFoliageEvidence.cpp`) places it, as for Pacuare.

`L_Terminator` launches at station 750 m, in the calmest deep water above
the rapid (mean 1.15 m/s). The Terminator's main whitewater runs from 1,000
to 1,500 m. The old scene's interpreted entry-marker boulder contact is
gone, because the inferred boulders are in the bed.

## Results

Final cook (48,000 steps at 400 m³/s; `evidence/cook_compare.json`):

| check | value |
| --- | --- |
| GLO-30 surface anchors (11, every 200 m) | -0.34 to +1.14 m (median +0.36 m) |
| reference surface (partly inferred), median | +0.23 m |
| wet extent against the Sentinel-2 extent, IoU | 0.90 (3,014 cells wet beyond it, 28 missed) |
| discharge, exact face flux | 399.6-400.0 m³/s |
| settling, p95 depth change over the last 150 s | 3.6 mm |
| depth p50 / p95; speed p50 / p95 | 3.5 / 6.7 m; 2.3 / 4.0 m/s |

- **The rapid is hydraulically milder than its whitewater.** From 1,000 to
  1,250 m the imagery shows 25 % whitewater, but only 5 % of wet cells
  exceed Froude 0.8. From 1,750 to 2,000 m it is 19 % against 4 %.
  - The observed-whitewater floor shows the photographed extent.
  - The smooth inferred bed and the 30 m surface cannot form the
    Terminator's holes and waves.
- **The flow is known on one image date only:** 163 m³/s at La Frontera on
  2020-02-20, plus unmeasured tributaries. The other dates and the GLO-30
  epoch are unknown. 400 m³/s is a planning band, well above that image-day
  flow, and the calibrated bed absorbs any difference.

## Validation

- `physics/tests/test_futaleufu_terminator_evidence.py` (7 tests) covers:
  - source hashes;
  - the location audit;
  - complete, settled cooked fields and the face-flux discharge within 3 %;
  - the anchors within 2 m, and the measured and inferred labels;
  - the geographic coordinate map;
  - the catalog, backdrop and runtime constants against the export;
  - calm launch water.
- `RaftSim.P4.RiverMapLoads.L_Terminator` covers the evidence package, band,
  streaming and observed-whitewater floor. It also checks one capture
  surface with no baked foam, the GLO-30 backdrop, the evidence canopy (3
  actors, at least 50,000 instances) and no interpreted D4 contact.
- `RaftSim.M9.FFutaleufu*` pass. The terrain test now requires the Sentinel-2
  drape and no procedural palette.
- The temperate near-bank ecology meets its 1,600 minimum (1,668 placed).
  On reaches over 1 km the search is widened rather than the minimum
  lowered.
- **In-game survey** at 750, 1,100, 1,450, 1,800 and 2,150 m: every station
  is wet, 3.0-6.7 m deep, with no ground contact.

## Performance

`profile_reference_map_ps5.ps1`, 1,200 frames per station, with no other job
running:

| station | p95 | max | frames over 100 ms |
| --- | --- | --- | --- |
| 750 m | 25.2 ms | 32.2 ms | 0 |
| 1,250 m (in the rapid) | 38.1 ms | 51.5 ms | 0 |
| 1,900 m | 26.6 ms | 46.5 ms | 0 |

## Limits (why this is not accepted)

- **The imagery is 10 m and the elevation 30 m.** Rocks, bars, holes and
  bank detail are not resolved. The Terminator's features are inferred or
  missing.
- **No bathymetry and no gauged flow.** The bed is inferred and calibrated
  to an edited DSM surface of unknown epoch flow (about ±2 m).
- **GLO-30 is a surface model**, so tree canopy is part of the terrain
  heights on the valley walls.
- **The lower and main rapids are too mild** hydraulically (see Results).
- **The canopy positions, species and heights are inferred.** Only forest
  cover is measured.
- **Finer data would need purchase** (SAF aerial photography). The
  2024-2026 gauge records need the DGA portal's reCAPTCHA, completed by the
  user.
