# Pacuare Huacas-Pinball: evidence-based reach

September 27, 2026. **Implemented, not accepted.** `L_UpperHuacas` is now
a 2.3 km geographic reconstruction of the Pacuare from above Upper Huacas to
below Lower Pinball (OSM chainage 81.95-84.45 km). It replaced the 600 m
straight interpreted reach. Terrain, banks, the wetted channel and the
water-surface anchors are measured. The bed, the surface between anchors, and
the discharge are inferred and labelled. It is not survey-grade and not
accepted.

## Sources

The downloads were approved on 2026-09-26. They are archived with requests,
hashes, CRS and licences in
`physics/data/real_world/pacuare_river_costa_rica/huacas_sources_2026_09/manifest.json`.

| source | what it measures | epoch |
| --- | --- | --- |
| IGN Costa Rica 1:5,000 contours (10 m, SNIT WFS) | terrain; water surface where contours meet the river | 2014-2017 compilation |
| IGN 1:5,000 hydrography (D01 bank lines) | the active channel (banks) | same |
| IGN 2014-2017 orthophoto (WMTS z18, ~1 m effective) | wetted water, gravel bars, whitewater, emergent rocks | 2014-2017, flow unknown |
| OSM relation 12000489 | chainage, rapid positions (matches GoRafting river km within 0.1 km) | 2026 |
| Sentinel-2 L2A 2021-12-11 (10 m) | colour outside the orthophoto and for the backdrop | 2021 |

- **Licence:** IGN requires attribution; commercial redistribution is unclear
  and must be confirmed with IGN before shipping derived data. OSM is ODbL.
  Sentinel-2 requires attribution.
- **No bathymetry, LiDAR or discharge record exists.**

## Method

Scripts are numpy only.

1. **Frames.** `geo_frames.py` puts every source in CRTM05 (EPSG:5367). IGN
   bank lines, contours, OSM and the orthophoto register within a few metres.
2. **Evidence grid** (`build_pacuare_evidence_grid.py`, 1 m).
   - **Midline:** from facing points of the IGN bank lines. The OSM line
     leaves the channel in places, so it is used only to order the points.
   - **Active channel:** the region between the banks.
   - **Wetted water, bars and rocks:** from the orthophoto inside the channel.
     Whitewater is bright and neutral or cool. Bright components that are
     large, bank-attached and smooth are dry gravel bars. Textured bright
     patches, such as boulder gardens and single rocks, are emergent rocks.
   - **Water-surface anchors (measured).** A contour at level L runs beside
     the river only where the water is below L. So the upstream-most place
     where an L contour comes within 10 m of a bank is where the surface
     crosses L. These stations do not change for bank distances of 8-25 m.

     | OSM km | 79.79 | 82.28 | 82.99 | 83.54 | 84.48 | 86.13 |
     | --- | --- | --- | --- | --- | --- | --- |
     | elevation (m) | 190 | 180 | 170 | 160 | 150 | 140 |

   - **Surface between anchors (inferred).** Each 10 m drop is spread along
     the river in proportion to 0.04 plus the orthophoto whitewater share, so
     rapids are steep and pools flat. Huacas and Pinball then carry most of
     each drop.
   - **Terrain (interpolated between measured contours).** A harmonic solve by
     conjugate gradients, with the water edge held at the surface, then about
     4.5 m of smoothing away from the channel. A Jacobi-only fill left
     terraces between contour lines.
   - **Bed (inferred).** Discharge-consistent depth on a smooth section:
     Manning n 0.035 in pools and 0.05 in rapids, with a critical-depth
     floor. Two calibration passes (`calibrate_river_bed.py`, step-limited)
     lowered it by station towards the reference surface. The first cook ran
     high; the final cook still sits 0.1-0.4 m high (see Results). Gravel bars get a beach profile, from 0.1 m above the surface at
     the water's edge to 0.6 m over 6 m (inferred).
   - **Rocks and boulders (inferred).** Emergent rock tops sit at the surface
     plus a height scaled from the rock's size. Submerged boulders sit at the
     upstream edges of whitewater patches, as for Hance.
3. **Solver grid** (`build_curvilinear_river_scenario.py`, a generalised
   form of the Hance builder):
   - 2 m station/lateral grid, 1,165 x 49 cells (2.33 km x 96 m);
   - centreline smoothed to a minimum 122 m radius. On the tight meanders
     cells are 0.85-1.36 of their true length, because the solver has no
     metric terms.
4. **Cooks** (`raftsim_water_solver`, finite volume, HLL, MUSCL, bed-slope
   source on, 48,000 steps). The inlet is a discharge profile for 45 m³/s.
   The comparison is `compare_river_cook.py` and the calibration
   `calibrate_river_bed.py`.

## Runtime integration

`export_pacuare_evidence_runtime.py` writes:
- the cooked field;
- the render-only presentation baseline;
- the observed-whitewater field (orthophoto whitewater, appearance
  evidence);
- the moving-window manifest;
- a 2017² Landscape over the 1,452 x 1,620 m window;
- a 2,048² drape: the orthophoto, feathered over 40 m into Sentinel-2 colour
  fitted to it;
- a contour-derived backdrop mesh over the IGN download extent, coloured by
  Sentinel-2.

Terrain against the solver bed in wet cells: p50 -0.002 m, p5/p95 -0.27/+0.28 m
(Landscape sampling 0.72 x 0.80 m).

The map builder then adds the evidence dressing
(`build_pacuare_evidence_dressing.py`, written beside the terrain):
- **Canopy, 27,205 trees.** 9,949 sit on sunlit crown tops found in the
  orthophoto inside the IGN `forestal2017_5k` tree-cover polygons. 17,256
  are infill on shaded slopes where the photo resolves no crowns, and
  outside the photo footprint.
  - Positions are measured, at about 1 m.
  - Crown size (0.7 x neighbour spacing, median radius 4.6 m), heights
    (14-30 m), species and forms are inferred. The two tree forms are the
    project's opaque rainforest canopy meshes.
- **Understory, 26,863 shrubs,** one beside each tree (inferred structure).
  Without it the walls read as bare trunks.
- **Emergent-rock shells, 719.** A rights-reviewed rock mesh sits on the
  equal-area footprint ellipse of each photographed single boulder
  (2-12 m²). Without them the rocks render as faceted prisms.
  - The Landscape bumps stay the collision and the solver obstacles; the
    shells are visual only.
  - Clusters stay terrain: one mesh made them into slabs.
  - The emergent-rock heights are inferred.

The river-band dressing tuned on the 600 m reach keeps its per-metre
densities, scaled by centreline length / 600 m. Its woody slope ceiling uses
the leaf-litter ceiling (36 degrees) on the steeper real walls.

## Results

Final cook: 48,000 steps (2,400 s) at 45 m³/s. Measured against the evidence
(`evidence/cook_compare.json`):

| check | value |
| --- | --- |
| measured anchors 180 / 170 / 160 m | +0.31 / +0.11 / +0.24 m |
| reference surface (partly inferred), median | +0.38 m |
| wet extent against the photo wetted area, IoU | 0.58 (1,837 cells wet where the photo shows dry bars, 44 missed) |
| discharge, exact face flux, west / mid / east | 44.99 / 44.98 / 44.89 m³/s |
| settling, p95 depth change over the last 150 s | 0.9 mm |
| depth p50 / p95; speed p50 / p95 | 1.55 / 3.45 m; 0.82 / 1.96 m/s |

- **Discharge measure.** The solver's exact face mass flux
  (`solver_face_discharge.py`) is the transported discharge. The cell-centre
  sum of h·u overstates it on this steep reach with wet/dry banks by 2-34 %
  per section (median 10 %). An earlier cook scaled the inlet to fit that sum
  and delivered only 42.2 m³/s. The exporter and the test now use the face
  flux. The same bias inflates the Hance manifest's figures by 1-2 %; its
  face flux is 226.2-226.5 m³/s against the 226.5 target.
- **The photo flow is lower than 45 m³/s.** The cook wets bars that the
  photo shows dry. Cooks at 15 and 25 m³/s did not match the wetted area
  better, because the bars are part of an inferred bed calibrated to the
  anchors. The photo flow stays unknown.
- **Supercritical flow is under-produced in the lower rapids.** From 1,750 to
  2,250 m the photo shows 31-33 % whitewater, but only 3-7 % of wet cells
  exceed Froude 0.8. The observed-whitewater floor shows the photographed
  extent, but the hydraulics there are milder than the rapid.

## Validation

- `physics/tests/test_pacuare_huacas_evidence.py` (7 tests) covers:
  - source hashes;
  - complete, settled cooked fields and the face-flux discharge within 3 %;
  - the anchors within 0.5 m, and the measured and inferred labels;
  - the geographic coordinate map;
  - the catalog, backdrop and runtime constants against the export;
  - deep, calm water at the launch;
  - the dressing labels and extents.
- `RaftSim.P4.RiverMapLoads.L_UpperHuacas` covers the cooked package,
  streaming, backdrop, dressing counts, evidence canopy (3 actors, at least
  40,000 instances) and rock shells (6 variants, at least 700). It passes
  when run on its own. Run after `RaftSim.M9.FPacuareLiveTransmittingWater`
  in the same editor session, it fails with the startup water shader map
  incomplete: a harness order dependency, not a map defect.
- `RaftSim.M9.FPacuare*` (6 tests) pass. The terrain test now requires the
  orthophoto drape and no procedural palette over it.
- **In-game survey** at 280, 730, 1,180, 1,630 and 2,080 m: every station is
  wet, 1.3-3.8 m deep, and reachable.

## Performance

`profile_reference_map_ps5.ps1`, 1,200 frames per station, with no other
engine, Blender or solver job running:

| station | p95 | max | frames over 100 ms |
| --- | --- | --- | --- |
| 280 m | 23.6 ms | 27.8 ms | 0 |
| 1,050 m | 29.1 ms | 49.1 ms | 0 |
| 1,950 m | 30.1 ms | 44.8 ms | 0 |

This is within the 50 ms p95 goal. The canopy, understory and rock shells
added 0-2 ms p95 (21.6 / 29.0 / 28.1 ms before them).

## Limits (why this is not accepted)

- **No bathymetry.** The bed is discharge-consistent and calibrated to three
  anchors. Depths, velocities and hydraulic features between them are
  inferred.
- **The surface between anchors is inferred.** The anchors themselves carry
  about ±30 m of station uncertainty (on a 1.6 % slope, about ±0.5 m).
- **Photo flow and gameplay flow differ** (see Results), so bars flood at
  45 m³/s.
- **The lower rapids are too mild** (see Results).
- **Emergent-rock heights and all vegetation structure are inferred.**
- **The drape is photo colour**, unlit and baked with the 2014-2017 sun and
  haze. Steep walls stretch it. Colour outside the photo is Sentinel-2
  fitted to it.
- **Licence:** commercial redistribution of IGN-derived data must be
  confirmed with IGN before release.

## Observed rapids (2026-09-29)

The observed-whitewater layer is raised to the reach's observed-rapid
catalogue (`observed_rapids/huacas_observed_rapids.json`: 6 rapids, 5
features). The cooked flow is unchanged:
- A trial cook with the named rocks, the Upper Pinball boulder garden and
  the Guatemala waves changed breaking by at most one cell per feature.
- Guatemala sits in the reach-end pool.

See [observed-rapids-2026-09-29.md](observed-rapids-2026-09-29.md).
