# Colorado Hance: evidence-based reach

September 26, 2026. **Playable delivery: `L_Hance` is now a 2.5 km geographic
reconstruction of Hance Rapid** (Grand Canyon river mile ~76.7) instead of the
600 m straight interpreted reach. Banks, emergent rocks and pools are measured;
the bed inside the rapid is inferred and labelled; the water is cooked at the
flow the measurements were taken at. Not survey-grade and not accepted as
photoreal (see Limits).

## Sources (downloaded with the user's permission)

Archived with hashes, DOIs and datums in
`physics/data/real_world/colorado_river_grand_canyon_rowing/hance_sources_2026_09/manifest.json`
(all U.S. public domain; NAD83(2011) / Arizona Central EPSG:6404, ellipsoid heights):

| source | what it measures | epoch |
| --- | --- | --- |
| USGS/GCMRC channel mapping, river miles 61-88 (doi:10.5066/P99SSSU6) | pool bathymetry (multibeam/singlebeam) and total-station banks, 1 m | May 2014 |
| USGS corridor DEM, zone 5 (doi:10.5066/P93Y4FMJ), 1 m crop | ground, emergent rocks, water-surface texture | May-June 2021, steady ~8,000 cfs |
| USGS corridor imagery (ImageServer, 0.5 m and 0.2 m exports) | water outline, whitewater, colour | same flights as the DEM |
| USGS 3DEP seamless DEM, 10 m export of a 6.5 km window (added 2026-09-27) | terrain beyond the corridor DEM | NAVD88 heights |

The 2021 imagery replaced the 2013 mosaic in the approved list: same provider
and resolution, same epoch and flow as the DEM. The rapid itself (about 900 m)
has **no sonar coverage**; the corridor DEM reaches only 200-250 m from the
channel.

## Method

Scripts (numpy only) in `physics/scripts/`:

1. `build_hance_evidence_grid.py`: 1 m grid of dry ground (2021 DEM),
   measured bed (2014 sonar, 95,415 cells), emergent rock tops (2021 DEM, 1,274
   cells), and a **discharge-consistent inferred bed** where there is no sonar
   (87,330 cells): Manning strip depth for Q = 226.5 m3/s (8,000 cfs),
   n = 0.040 in the rapid, never shallower than critical depth, blended into
   the measured pools. The water-surface target uses only surfaces with their
   own texture. The DEM metadata says it is less accurate on water, and over
   calm clear water it reads the bed. So the target is DEM over imagery
   whitewater, plus the waterline between a dry 2021 DEM cell and its wet
   neighbour's 2014 bed, fitted with a non-increasing profile.
2. **Inferred boulders (class 4, 141):** whitewater forms just downstream of an
   obstacle, so each ≥ 4 m2 imagery whitewater patch over inferred bed places a
   boulder at its upstream edge (one per 3 m lateral cluster, radius from the
   patch width). Crest 0.25 m below the reference surface (pour-over
   assumption); height p50 1.19 m. Location evidence is measured; height is not.
3. `build_hance_curvilinear_scenario.py`: 2 m station/lateral solver grid
   (1,257 x 81) on the channel centreline smoothed to a 282 m minimum radius,
   plus the runtime coordinate map (`world_y_sign -1`, datum 740 m).
4. Cook: `raftsim_water_solver` (finite volume, HLL, MUSCL, bed slope on,
   uncalibrated), 1,800 s, discharge-profile inlet, reference-stage outlet.
5. `compare_hance_cook.py` / `calibrate_hance_bed.py`: two calibration steps
   lowered or raised **only the inferred bed** (cumulative -1.39 to +0.85 m).
   The measured bed never changed.

| cook | change | textured-surface error median / median abs | calm stations in bounds | wet IoU | Fr > 0.8 share vs imagery foam, main / lower rapid |
| --- | --- | ---: | ---: | ---: | --- |
| v0 | smooth inferred bed, n 0.058 | +0.24 / 0.46 m | 58% | 0.94 | 0.4% / 1.2% vs 14% / 7.9% |
| v2 | + boulders, n 0.040 | +0.34 / 0.52 m | 56% | 0.94 | 11.3% / 8.5% |
| v3 | + textured reference, corrected outlet | +0.39 / 0.44 m | 52% | 0.95 | 9.1% / 1.2% |
| v5 (shipped) | two bed calibration steps | **+0.04 / 0.18 m** | **68%** | **0.95** | 10.4% / 1.7% |

v5 conveys the target discharge: the solver's exact face flux
(`solver_face_discharge.py`) is 226.5 / 226.4 / 226.2 m3/s at the west / mid /
east sections against 226.5. Since 2026-09-29 the cooked manifest's
`discharge_steady_m3s` and the compare's `discharge_m3s` record that face
flux. The first export recorded the cell-centre h·u sum (229.4-231.6), which
overstates transport on wet/dry reaches (see pacuare-huacas-evidence.md); it
is kept as a labelled diagnostic. The re-export from the same v5 cook left
every cooked array, the observed-whitewater layer and the terrain
byte-identical. v5 is settled (p95 surface change 1.6 mm over the last 150 s). The v0
outlet stage came from the clear-water DEM and was 1.6 m low; it drained both
downstream pools. The waterline pairs put the scour pool at about 750.2 m;
v5 cooks it at 750.2-750.3 m. Calm-water levels are known only to about
±0.5 m (lower bound: DEM over water; upper bound: bank edge). Remaining
textured misfit: the lower-rapid crest (1,350-1,390 m) sits +0.5 to +0.9 m
high. A 2 m grid cannot reproduce the local trough behind a pour-over, and
that rapid stays under-active. A third calibration step (v6, not shipped)
improved the median absolute error by 1 cm and left that crest unchanged,
so the residual is structural, not bed calibration.

Whitewater lace and patch floors from 0.12 to 0.30 turned most of the main
rapid into one white-grey sheet, because the cooked foam field is broad. The
0.06 / 0.04 floors kept green water between filaments, but underplayed the
imagery's massed white. Concentrating the source foam was the lever, not the
material floors.

**Observed whitewater (2026-09-27).** No cooked-field quantity places the
foam where the photographs show it.
`physics/scripts/audit_hance_whitewater_indicators.py` scores 32 candidates
against the imagery foam mask in the rapids (650-1,500 m) at matched area:
- Froude and the shipped Froude-onset foam reach IoU 0.07, with precision
  0.13 against a 12% base rate.
- The best candidates (flow convergence, streamwise deceleration, Froude
  drop, advected surface slope) reach only IoU 0.13-0.14.
- The audit is archived as `evidence/whitewater_indicator_audit.json`.

A 2 m field over an inferred bed cannot resolve where individual holes and
crest caps sit. The photographs were taken at the cooked flow, so their
whitewater extent is used as **appearance evidence**:
- `export_hance_observed_whitewater.py` bakes the foam mask onto the cooked
  station/lateral grid: the fraction of 4 x 4 sub-points per cell, then one
  smoothing pass.
- It writes `observed_whitewater_steady_8000cfs_2021.bin` (RSBF v1 layout),
  recorded in the cooked manifest.
- At run time (`ARaftSimRiverWaterConfig::ObservedWhitewaterGain`, 0.9 for
  Hance) it **floors the displayed foam** and the far-field cue.

It is not a foam source. The photo already shows foam after it has drifted
downstream, and feeding it to the transported foam state smeared the whole
rapid into one white sheet (about 70% cover against the photo's 14%). It never
reaches forces, contact or gameplay. With the concentrated source, the generic
Froude foam returns to its default onset (Fr 0.78, ramp 1.25), and the lace
and patch floors rise to 0.30 / 0.10. The main and lower rapids now show
rounded white masses where the photo has them, with green water between.

![Imagery (left), 0.06 lace floor with Froude foam (middle), observed whitewater (right); main rapid at 800 m (top) and lower rapid at 1,320 m (bottom)](colorado-hance-evidence/whitewater-observed-800-1320m-imagery-before-after.png)

![Entering the main rapid at 700 m, chase and side views](colorado-hance-evidence/whitewater-observed-eye-700m.png)

Evidence, validation figures and the calibration file are archived in
`scenario_hance_evidence_2021/evidence/`.

## Runtime integration

- `export_hance_evidence_runtime.py` writes the cooked field, the render-only
  presentation baseline (`support_band_field_*.bin`), the moving-window
  manifest, and the terrain: a 2017² Landscape over the 2500 x 1212 m window
  (1.24 x 0.60 m samples; terrain minus solver bed p5/p50/p95
  -0.06/0.00/+0.04 m in wet cells) and a 4096 x 2048 orthophoto drape.
- `L_Hance` is rebuilt by `RaftSim.CreateLandscapeImportCandidateMaps colorado_river`
  (and `RaftSim.CreateRiverMaps` now routes `L_Hance` there instead of
  overwriting it with the legacy flat stub). Launch: station 520 m in the
  measured pool above the rapid. The solver streams a 480 x 160 m crop around
  the raft, re-centred every 80 m.
- **Mirrored curved grids faced down.** Hance is the first curved map in the
  geographic (ENU) frame. Its station runs to -X and river-left to +Y, which
  reverses the triangle winding that every curved presentation mesh assumed.
  The live surface rendered back faces, and its foam went dark. Winding now
  follows the measured world orientation of the grid, so earlier maps are
  unchanged.
- The live strip spans the full 160 m cooked width on a 1.5 m lattice
  (17,388 vertices; at 1 m it cost 19 ms of game thread per frame).
- **Curved far-field water** (`UpdateCurvedFarFieldWater`): the cooked
  baseline, drawn along the whole reach outside the live strip. It uses a
  4 m station/lateral lattice with the strip's own vertex encoding, has a
  hole under the drawn strip, and shows a whitewater cue where the cooked
  speed and Froude are high. It is render only and rebuilds in about 6 ms
  when the strip recentres.
- Foam calibration against the imagery at the same flow (first pass,
  2026-09-26): the generic aeration onset moved from Fr 0.78 (ramp 1.25) to
  Fr 0.6 (ramp 0.5), with a thin lace floor, via new
  `ARaftSimRiverWaterConfig` fields. With the old onset, the main rapid showed
  0.3% visible foam against 14% in the imagery. This pass was superseded by the
  observed whitewater field (above), which restores the default onset.
  Default values keep every other map unchanged.
- Terrain presentation:
  - The drape is scaled to albedo (median 0.11).
  - Under water, the drape uses a darkened continuation of the bank colours
    instead of the photographed water.
  - The outer 10 m of the corridor DEM is dropped. Its edge cells held
    photogrammetric spikes up to 70 m, which read as a spire from the river.
  - The procedural boulder scatter is removed. Rocks come from the DEM and
    the labelled boulder bed.
- **Measured terrain beyond the corridor (2026-09-27).** Outside the 2021
  corridor DEM (59% of the Landscape), the terrain is now USGS 3DEP 10 m
  instead of the invented rising fill.
  - Datum: 3DEP is NAVD88, so it is shifted by the median corridor-DEM-minus-3DEP
    difference over dry measured ground, −23.25 m (1.07 M cells; p10/p90
    −25.6/−18.3 m). This is the local geoid separation.
  - Seam: the remaining corridor-edge residual is extended harmonically and
    faded out over 150 m.
  - Upsampling uses Catmull-Rom; bilinear upsampling left grid-aligned slope
    creases that the lighting showed.
  - Landscape relief rises from 394 to 532 m. The water and bed inside the
    corridor are byte-identical, via the exporter's `--terrain-only` mode.
- **Terrain-conditioned colour** outside the photo footprint (57% of the
  Landscape). The photo's median albedo is computed for each bin of 10 m slope
  and height above the 3DEP river level. That colour is then applied to the
  3DEP terrain, blended over 60 m from the photo edge. The colour is still
  invented, but it follows the measured slopes and benches rather than one
  smeared tone.
- **3DEP terrain backdrop.** The builder places a render-only, always-loaded
  Nanite mesh around the Landscape.
  - Geometry: the whole 6.5 km 3DEP window at 10 m (786 k triangles).
  - Colour: a 2,048² drape with the same palette. 3DEP's hydro-flattened
    river cells take the photo's median open-water colour.
  - It has no collision, and it casts shadows (canyon walls shade the river at
    low sun).
  - Outside the Landscape it keeps the measured heights. Under the Landscape
    it sits 0.5 m below within 20 m of the edge, and 3 m below the local
    minimum further in. An earlier version lowered it outside the edge too,
    which drew a shadowed trench along the Landscape edge.
  - Pipeline: `export_hance_evidence_runtime.py --terrain-only`, then
    `unreal/Scripts/export_colorado_hance_backdrop_fbx.py` (Blender), then
    `unreal/Scripts/install_colorado_hance_backdrop.py`, then the map build.
- Packaged builds stage the cooked field, baseline, streaming manifest and
  coordinate map (`RaftSimWater.Build.cs`).

![2021 orthophoto (left) and game at the main rapid, same footprint, west up](colorado-hance-evidence/overhead-800m-imagery-vs-game.png)

![Lower rapid](colorado-hance-evidence/overhead-1320m-imagery-vs-game.png)

![Put-in pool (520 m), main rapid (795 m), calm run (1,070 m), lower rapid (1,345 m)](colorado-hance-evidence/eye-level-520-795-1070-1345m.png)

![Downstream from 520 m and 1,020 m: invented fill (left) and 3DEP terrain plus backdrop (right)](colorado-hance-evidence/eye-level-before-after-3dep-520-1020m.png)

![3DEP backdrop: oblique from 1.2 km looking south, and overhead (top = west)](colorado-hance-evidence/3dep-backdrop-oblique-and-overhead.png)

## Validation

Performance: editor-hosted game, 1,200 frames, rows 30-1169, idle host
(`unreal/Scripts/profile_reference_map_ps5.ps1`). Target: 20 FPS, i.e. 50 ms
p95 and no frame over 100 ms.

| start | mean ms | p95 ms | max ms | > 100 ms | game thread mean ms | GPU mean ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| put-in (520 m) | 15.9 | 29.4 | 33.0 | 0 | 16.8 | 7.6 |
| main rapid (740 m) | 18.3 | 36.5 | 51.3 | 0 | 19.2 | 7.8 |
| lower rapid (1,250 m) | 19.3 | 37.1 | 54.8 | 0 | 20.3 | 7.7 |

Before the 1.5 m lattice the put-in ran p95 61.3 ms. With the 3DEP terrain and
backdrop (2026-09-27, same method): put-in 17.2 / 30.7 / 40.4 ms (mean / p95 /
max), main rapid 19.1 / 36.9 / 55.2, lower rapid 19.2 / 37.1 / 57.3. There are
no frames over 100 ms, and GPU mean is 7.6-7.9 ms, so the backdrop costs
little. `RaftSim.P4.RiverMapLoads.L_Hance` now also checks that exactly one
backdrop is placed and that it does not collide. That test and
`RaftSim.M9.FColoradoHanceEvidenceTerrain` pass.

- Reach surveys (`RaftSim.SurveyReach`, 520-1,720 m): every station wet, no
  grounding, integrity 1.0, current 0.7 m/s in the pool and 2.1-3.2 m/s in
  the rapids. One 12 s-settle run flagged a 1.23 m lateral surface tilt on the
  scour-pool eddy line at 1,720 m. Two other runs with the same data had none.
- Automation:
  - Pass: `RaftSim.P4.RiverMapLoads.L_Hance` (updated for the new paths, band,
    streaming and strip), `RaftSim.M9.FColoradoHanceEvidenceTerrain`
    (replaces the organic-palette test), `RaftSim.M9.FColoradoHanceWater`,
    `RaftSim.Survey.GeographicHandedness`, and `RiverMapLoads` for L_LavaCanyon,
    L_Terminator, L_UpperHuacas and the South Fork full reach.
  - `L_Zambezi` fails its known start-apron spray gate (listed in known
    issues).
  - `L_Hance` also fails if it runs right after the M9 water tests in the same
    session: those tests rebuild the water material, and its startup shaders are
    then incomplete.
- `physics/tests/test_colorado_hance_evidence.py`: sources, cooked field,
  labels, coordinate map, catalog consistency and launch depth. All six tests
  pass here (Blender's Python, no pytest). The hash-locked reviews of the
  interpreted map are now recorded as superseded, and
  `test_colorado_hance_rapid_approach.py` is retired with it.

## Limits (open)

- **Whitewater** now takes its extent from the photographs (appearance
  evidence), so it is only valid at the photographed flow. The solver does
  not predict it, and it does not move with the raft's own disturbance. The
  2 m cooked surface has no hole or crest relief under the white.
- **Open water is too bright from overhead.** The deep pool below the main
  rapid measures 0.7% of the bank luminance in the orthophoto (the bank is
  near clipping) and 35% in the game at the same framing. Real deep clear
  water reflects about 1-3% against 20-35% for bank soil, so the game is
  several times too bright. Neither ~4x more red-weighted absorption nor
  halving the fallback sky-reflection floor changed it visibly, so the body
  colour is not the cause. The sparkle texture points to sun glints on the
  ripple normals and lit reflections. Not yet fixed. The eye-level pale teal
  is less clearly wrong, because canyon water at grazing angles reflects the
  lit walls.
- Rapid bed and boulder heights are inferred; velocities are not measured.
  The bed is 2014 and the surface 2021.
- The grid has no metric terms: cell lengths are 0.87-1.17 of true on bends.
- Terrain beyond the 2021 corridor DEM is now measured, but only at 10 m.
  Cliff lines that run diagonal to the grid alias into single-cell steps,
  which are present in the 3DEP export itself. Its colour is still invented
  (terrain-conditioned palette): no imagery beyond the corridor was
  downloaded.
- The cooked water ends 35-55 m inside the Landscape at both reach ends. From
  there to the edge the channel shows dry bed, and past the edge the backdrop
  shows 3DEP's flat river surface as coloured ground.
- The orthophoto colour includes its capture lighting. Distant slopes still
  read pale and hazy; some faceted flat-shaded patches show on the water.
- The far-field water takes its depth and speed from one encoded energy value,
  not the cooked depth.

## Observed rapids (2026-09-29)

The observed-whitewater layer is raised to the reach's observed-rapid
catalogue (`observed_rapids/hance_observed_rapids.json`: Hance main rapid and
Son of Hance; 14 features). It now covers the whole main rapid and Son of
Hance.

The cooked flow is unchanged:
- A trial cook with the features drowned the upper main rapid. The pools
  below the steps are measured 2014 bathymetry, so the features could only
  raise the inferred bed above each step.
- The lower main rapid and Son of Hance still do not break hydraulically.

See [observed-rapids-2026-09-29.md](observed-rapids-2026-09-29.md).
