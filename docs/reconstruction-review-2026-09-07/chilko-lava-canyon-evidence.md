# Chilko Lava Canyon: evidence-based reach

September 28, 2026. **Implemented, not accepted.** `L_LavaCanyon` is now a
4.0 km geographic reconstruction of the Chilko River from above Bidwell
Rapid to the head of the White Mile (BC Freshwater Atlas corridor chainage
43.9-47.9 km). It replaces the 600 m reach-local interpreted scene.

The data here are better than on the other international rivers:
- **Measured:** all terrain above the water and the water surface itself on
  the LiDAR flight days (LidarBC 2023, 1 m), the flight-day wetted extent,
  whitewater appearance at four gauged flows (Sentinel-2, 10 m), the daily
  flows (HYDAT), and the forest inventory (VRI polygons).
- **Inferred and labelled:** the bed under the water, submerged boulders, the
  roughness, the tributary gain between the lake outlet and the reach, and
  individual tree positions and sizes.

It is not survey-grade and not accepted.

## Sources

The downloads were approved on 2026-09-28 ("do the downloads Chilko and
Zambezi, and Chilean gauge records etc."). They are archived in
`physics/data/real_world/chilko_river_bc/chilko_sources_2026_09/manifest.json`.

| source | what it measures | epoch |
| --- | --- | --- |
| LidarBC 1 m bare-earth DEM (4 tiles, 1:20,000 grid) | terrain; the water surface where the river is (not hydro-flattened) | flights 2023-09-18 to 2023-10-06 (tile 092o092) |
| Sentinel-2 L2A (10 m; B, G, R, NIR, SWIR, SCL) | whitewater, colour; widths (see Limits) | 2019-08-07, 2021-07-12, 2023-08-16, 2024-09-04; plus 2023-09-15/22 and 2023-10-07 near the flights |
| HYDAT 08MA002 (lake outlet) and 08MA001 (below the Taseko) | daily flows | full record to 2024 |
| BC VRI `VEG_COMP_LYR_R1_POLY` | treed class, species shares, crown closure, height, stems/ha per polygon | reference year 2013, projected to 2025 |
| BC Freshwater Atlas route, OSM | chainage; Bidwell Creek (39.9 km), "Lava Canyon" label | 2026 |

- **Flows on the image dates** (08MA002): 113, 167, 92.7, 70.3 m³/s. The reach
  lies between the two gauges, so its flow is the lake outflow plus
  unmeasured local tributaries.
- **The LiDAR water surface** is the flight-day surface at 57 falling to 33
  m³/s (mean about 45). The flight date of each part of the reach is not in
  the DEM.
- **Only the reach is kept.** The four full tiles (~1.5 GB) were cropped. The
  1 m DEM over the evidence window (lossless at its 1 cm step) and 20 m block
  means over a 3 km surround are archived with the terrain; the tile URLs and
  hashes are in the sources manifest.
- **Licences:** LidarBC and VRI are Open Government Licence - British
  Columbia; HYDAT is Open Government Licence - Canada; Copernicus Sentinel
  data require attribution; OSM is ODbL.

## Locating Lava Canyon and Bidwell Rapid

The old scene sat about 9 km below the lodge, which is not Lava Canyon. The
guidebooks put Bidwell Rapid, the Class V entry to Lava Canyon, about 5 km
below Bidwell Creek; Bidwell Creek meets the route at 39.9 km. On the LiDAR
water surface the steepest drop in the lower corridor is 4.7 m over
44.5-44.75 km, and the only persistent Sentinel-2 whitewater in the reach is
at 44.6-44.8 km. The reach is 43.9-47.9 km: 700 m of approach, Bidwell
Rapid, and the canyon down to the head of the White Mile.

## Method

Scripts are numpy only (Blender's Python; LiDAR tiles read with its
OpenImageIO). The frame is NAD83(CSRS) / UTM 10N (EPSG:3157); heights are
CGVD2013. Sentinel-2 is WGS 84 / UTM 10N; the ~1 m datum offset is ignored.

1. **LiDAR crops** (`crop_lidarbc_dem.py`): the 1 m DEM over
   444,000-450,400 E, 5,754,200-5,759,900 N from the tiles that cover it,
   and (`--block 20`) the mean of the valid 1 m cells in each 20 m block over
   the backdrop window.
2. **Evidence grid** (`build_chilko_evidence_grid.py`, 1 m, 3,464 x 3,150 m):
   - **Water surface (measured):** the LiDAR over the channel interior,
     median per 5 m of station, forced non-increasing. Anchors every 100 m.
   - **Wetted extent (measured at the flight flow):** cells within 0.15 m of
     that surface and connected to the channel.
   - **Midline:** the middle of the wetted extent along the Freshwater Atlas
     route normals, smoothed; station is its arc length.
   - **Whitewater (measured appearance):** bright, neutral water pixels,
     averaged over the four Sentinel-2 dates.
   - **Terrain (measured):** the LiDAR everywhere above the surface,
     including emergent rocks and bars.
   - **Bed (inferred):** discharge-consistent depth below the LiDAR surface
     for 45 m³/s on a smooth section (Manning n 0.035 in pools, 0.05 in
     rapids).
   - **Submerged boulders (inferred):** at the upstream edges of whitewater
     patches.
3. **Solver grid** (`build_curvilinear_river_scenario.py`): 2 m cells, 1,990
   x 29 (3.98 km x 56 m). The minimum radius is 231 m, so cells are within
   0.97-1.07 of their true length.
4. **Bed calibration at the flight flow.** Cooks at 45 m³/s
   (`raftsim_water_solver`, finite volume, HLL, MUSCL, bed-slope source on)
   are compared with the LiDAR surface (`compare_river_cook.py`, discharge
   from the exact face flux). Step-limited passes of `calibrate_river_bed.py`
   (50 m smoothing, at most 2 m per pass) lower the inferred bed towards the
   measured surface.
5. **Runtime band.** The calibrated bed is cooked at 93 m³/s, the lake-outlet
   flow on 2023-08-16, the date of the Sentinel-2 drape.

## Runtime integration

`export_chilko_evidence_runtime.py` writes:
- the cooked field at 93 m³/s, the render-only presentation baseline and the
  observed-whitewater field (Sentinel-2 whitewater fraction, appearance
  evidence);
- the moving-window manifest (480 m crop, whole 56 m cooked width);
- a 2017² Landscape over the 3,464 x 3,150 m window (258 m of relief; 1.72 x
  1.56 m samples);
- a 2,048² Sentinel-2 drape (2023-08-16), albedo-scaled like the other
  evidence drapes. Under the flight-day water, and Sentinel-2 water within
  10 m of it, the bank colour is continued and darkened (invented bed
  colour);
- a LiDAR backdrop mesh (20 m block means, 3 km around the Landscape, bare
  earth);
- the archived LiDAR (the 1 m window and the 20 m surround).

Terrain against the solver bed in wet cells: p5/p50/p95 -0.14/0.00/+0.18 m.

`build_chilko_evidence_dressing.py` places the canopy from the BC Vegetation
Resources Inventory: 38 polygons in the window (lodgepole pine and interior
Douglas-fir, some Engelmann spruce, one aspen stand; 3-44 % crown closure;
burned 2013). Per polygon, trees = crown closure x area / mean crown area,
capped at the live stems per hectare: 80,136 trees (99.8 % conifer, heights
11/14/18 m at p10/p50/p90). Positions inside each polygon are sampled by
Sentinel-2 red-band darkness (dark conifer clumps against dry grass), so the
cover follows the inventory and the clumps follow the imagery; individual
positions, heights (projected height x N(1, 0.15)) and crown radii (0.13 x
height) are inferred. 5,713 riparian shrubs stand where Sentinel-2 NDVI
exceeds 0.45 within 25 m of the water (inferred structure).

`L_LavaCanyon` launches at station 600 m, 200 m above Bidwell Rapid. The old
scene's four interpreted D4 broach-rock contacts are gone; the inferred
boulders are in the bed. Its Chilko shoreline gravel and ground-cover layers,
authored for the 600 m scene, now span the reach from 100 m to its end with
the same instance targets.

## Results

Calibration cook (60,000 steps at 45 m³/s; `evidence/calibration_compare.json`):

| check | uncalibrated | pass 1 (relax 0.8) | pass 2 (relax 1.3) |
| --- | --- | --- | --- |
| LiDAR surface anchors (40, every 100 m) | +0.02 to +1.55 m | +0.09 to +0.91 m | **-0.14 to +0.45 m** |
| median surface error | +0.60 m | +0.29 m | **+0.015 m** |
| wet extent against the LiDAR extent, IoU | 0.865 | 0.891 | **0.917** |
| discharge, exact face flux (inlet / outlet) | 45.0 / 18.6 (still filling) | 45.0 / 44.9 | 45.0 / 44.9 |

The surface moves by about 0.6 of a bed change, hence the larger second
relaxation. The residuals above 0.2 m are local (1.5 km, 2.0-2.1 km, 3.7-3.9
km).

Runtime cook (60,000 steps at 93 m³/s; `evidence/cook_compare.json`):

| check | value |
| --- | --- |
| discharge, exact face flux | 92.9-93.0 m³/s |
| settling, p95 depth change over the last 150 s | 0.08 mm |
| surface above the 45 m³/s LiDAR surface | +0.58 to +2.04 m (median +0.84 m) |
| depth p50 / p95; speed p50 / p95 / max | 2.4 / 4.0 m; 1.7 / 2.8 / 5.5 m/s |
| cooked width (median of 250 m bins) | 24.8 m (1.19 x the LiDAR width at ~45 m³/s) |

The solver's own `validation_passed` is false for this run only because it
counts the 55 % mass gain of filling the reach from the 45 m³/s start through
open boundaries as drift; the fastest cell during filling reached 14.8 m/s,
and in the settled field it is 5.5 m/s.

- **Bidwell Rapid matches its whitewater.** At 750-1,000 m the imagery shows
  9.6 % whitewater; 8.5 % of cooked cells exceed Froude 0.8 at 93 m³/s (6.8 %
  at 45). Elsewhere whitewater is under 0.3 % and Froude > 0.8 under 7 %.
- **Sentinel-2 cannot check widths here.** Sub-pixel NIR unmixing reads 28-30
  m at every flow from 62 to 167 m³/s, and 1.42 x the LiDAR width on
  2023-09-15, three days before the flights at 62 m³/s (canyon shadows and
  mixed bank pixels). The 93 m³/s widths are therefore unchecked
  (`compare_chilko_sentinel2_widths.py`).

## Validation

- `physics/tests/test_chilko_lava_canyon_evidence.py` (9 tests) covers:
  - source hashes, and the tiles and Sentinel-2 dates the evidence used;
  - the archived LiDAR decoding back to the evidence terrain;
  - Bidwell Rapid as the reach's whitewater and steepest LiDAR drop;
  - the calibration against the LiDAR surface (anchors within 0.6 m, median
    under 0.15 m, IoU above 0.88, face flux within 3 %);
  - complete, settled cooked fields at 93 m³/s within 3 % face flux, and the
    measured and inferred labels;
  - the geographic coordinate map;
  - the VRI canopy against its inventory;
  - the catalog, backdrop and runtime constants against the export;
  - wet, steady launch water above the rapid.
- `RaftSim.P4.RiverMapLoads.L_LavaCanyon` covers the evidence package, band,
  streaming and observed-whitewater floor, one capture surface with no baked
  foam, the LiDAR backdrop, the evidence canopy (3 actors, at least 60,000
  instances), no interpreted D4 contact, and the 56 m presentation lattice
  (161 x 38, 1.5 m). Its strongest launch-window jump is at 678 m, in the
  lead-in to Bidwell Rapid: the LiDAR surface is steeper than 1 % from 625 to
  950 m against 0.3-0.5 % on the approach, and the main drop (up to 4 %) and
  the photographed whitewater sit at 775-880 m. The check uses that measured
  extent. The regenerated map carries the generator's Lava Canyon ripple and
  roughness (0.72 / 0.42), not the old map's serialized 0.55 / 0.68.
- `RaftSim.M9.FChilko*` pass. The terrain test now requires the Sentinel-2
  drape and no procedural palette.
- **Dressing on measured banks.** The old scene's shoreline gravel, meadow
  ground cover and near-bank ecology keep their instance targets and minimums.
  Two corrections were needed:
  - Their "logical" coordinate spans the whole centreline (-25 to 254 logical
    metres), so the old 2.5-597.5 m range piled the upper half of each layer
    onto the reach end. On the geographic reach the range is converted from
    real stations (100 m to 20 m before the end).
  - The LiDAR banks are basalt walls for long stretches: only about half of
    evenly spaced bank slots, and 4 % at 2.0-2.5 km, have ground under 38
    degrees within 36 m of the water. Half of each target's candidates now
    search the whole reach, with a penalty for distance from the target's
    slot, so patches stay put where the ground allows and gather on the real
    benches where it does not. Placed: gravel 7,200/7,200, ground cover
    8,253/8,400 (minimum 7,900), near-bank ecology 1,800/1,800 and waterline
    structure 1,287 (minimum 1,250).
- **In-game survey** at 600-3,800 m every 400 m: every station is wet, 1.7-4.3
  m deep, with no ground contact. The only anomaly is a 0.78 m lateral surface
  tilt over 12 m at 3,800 m, in the steep water at the head of the White Mile.

## Performance

`profile_reference_map_ps5.ps1`, 1,200 frames per station. The desktop app's
git scans held 35-48 % CPU during the runs, which can only have raised these
times:

| station | p95 | max | frames over 100 ms |
| --- | --- | --- | --- |
| 600 m (launch) | 19.2 ms | 25.5 ms | 0 |
| 850 m (Bidwell Rapid) | 21.1 ms | 33.3 ms | 0 |
| 2,200 m (canyon) | 19.3 ms | 32.4 ms | 0 |

## Limits (why this is not accepted)

- **No bathymetry.** The bed is inferred, calibrated to the measured LiDAR
  water surface at about 45 m³/s. The 93 m³/s band extrapolates from that
  calibration, and nothing measured checks its widths or stages (Sentinel-2
  cannot resolve width here).
- **The flow at the reach is the lake outflow plus unmeasured tributaries,**
  and the LiDAR flight date of each part of the reach is not in the DEM (57
  to 33 m³/s over the flights).
- **Colour is 10 m Sentinel-2.** Bank detail and rock texture come from the
  1.7 m Landscape and the procedural shoreline layers, not from imagery; the
  bed colour under the water is invented. The water reads deep blue, not the
  Chilko's glacial turquoise (appearance follow-up).
- **Tree positions, individual heights and crowns are inferred** within the
  inventory's polygons; the VRI itself is photo-interpreted (reference year
  2013).
- **Rocks and holes below the surface are not resolved.** Bidwell's two
  inferred boulders come from its whitewater patch.
