# Zambezi upper gorge: evidence-based Cartesian reach

September 28, 2026. **Implemented, not accepted.** `L_ZambeziUpperGorge` is a
new map covering the Zambezi from the Boiling Pot to below Stairway to Heaven
(0.15-3.65 km along the 30 km run's route chainage).
The 30 km interpretive `L_Zambezi` stays alongside it, unchanged. The user
chose this on 2026-09-28 ("go with option B, keep the 30 km run alongside").

The data are the weakest of the international rivers:
- **Measured:**
  - the low-water wetted extent and whitewater (Sentinel-2, 10 m, at known
    flows);
  - terrain and an edited water surface (Copernicus GLO-30, 30 m);
  - the daily flow at Victoria Falls on the image days (ZRA).
- **Inferred and labelled:** the bed, the depth everywhere, the steepness of
  the gorge walls below the 30 m resolution, submerged boulders, roughness,
  and tree positions.

It is not survey-grade and not accepted.

## Why a Cartesian grid

The Batoka zigzag turns through hairpins of 25-40 m radius. The curvilinear
scenario builder smooths the centreline to a minimum radius, and then the
channel no longer follows the water at the hairpins. This reach is instead
cooked on a map-aligned (east/north) 2 m grid, the Cartesian runtime that
South Fork FullReach already uses. That solver has no metric terms, so a
north-up grid is exact.

## Sources

Archived with licences and hashes in
`physics/data/real_world/zambezi_batoka_gorge/zambezi_sources_2026_09/manifest.json`.
The downloads were approved on 2026-09-28.

| source | what it measures | epoch |
| --- | --- | --- |
| Sentinel-2 L2A, tile 35KLA (10 m; B, G, R, NIR; SWIR, SCL) | wetted extent, whitewater, colour | 2024-10-08 (203 m³/s), 2025-10-03 (283 m³/s), 2025-07-25 (904 m³/s), 2025-05-28 (vegetation) |
| ZRA daily flows at Victoria Falls | flow on the image days | archived series |
| Copernicus GLO-30 DEM | terrain; the edited (flattened) water surface | 2011-2015 acquisitions |
| OSM route, `route_stationing.json` | chainage | 2026 |
| `reference/rapid_location_audit_2026_09.json` | the digitised rapid map against Sentinel-2 whitewater | this project |

The rapid map the user supplied is stylised, not georeferenced. The audit ties
Stairway to Heaven to the persistent whitewater run at route 2.7-2.8 km, and
the reach contains it. Copernicus data require attribution; OSM is ODbL.

## Method

Scripts are numpy only. The frame is WGS 84 / UTM 35S (EPSG:32735); heights
are EGM2008. The runtime datum is 700 m.

1. **Evidence grid** (`build_zambezi_evidence_grid.py`, 1 m, 1,985 x 1,549 m):
   - **Wetted extent (measured):** Sentinel-2 water on the dates at or below
     300 m³/s, connected to the channel. The median wetted width is 30.5 m
     (p10 18.5, p90 62 m).
   - **Whitewater (measured appearance):** bright, neutral water pixels on
     the dates at or below 1000 m³/s.
   - **Water-surface anchors (measured, ±2 m):** the median of GLO-30 over the
     channel interior per 50 m, forced non-increasing and sampled every 200 m.
     GLO-30 flattens and edits water, so this is a coarse surface.
   - **Bed (inferred):** discharge-consistent depth below that surface for
     283 m³/s. Manning n is 0.035 in pools and 0.05 in rapids.
     - Depth is capped at **6.5 m**. The cook and the runtime atlas reject
       depths over 10 m, and an 8 m cap breached that while filling.
     - The channel is at least **8 m** half-width, so the 10 m imagery cannot
       dam it.
   - **Gorge walls (inferred):** the 30 m radar DEM smears the walls into
     gentle slopes that flood. The walls rise 6 m over the first 6 m beyond the
     wet edge and hold that height out to 60 m (269,602 cells). Without this the
     first cook ran +1.4 m high with a wet IoU of 0.35.
2. **Cook package** (`prepare_zambezi_cartesian_cook.py`):
   - 2 m cells in 64-cell tiles (91 tiles).
   - The lattice is aligned so that a tile edge is the inflow cut (N
     8,017,440, where the river runs south) and another is the outflow cut
     (E 378,460, where it runs west). Water beyond the cuts is excluded.
   - Dry spill tiles surround the wet ones, because the runtime atlas rejects
     wet cells on artificial exterior faces.
   - The first cook starts cold, from still water at the reference surface. A
     velocity seed along the midline tangent pointed into the walls at
     hairpins.
3. **Cook** (`raftsim_cartesian_cook`, finite volume, HLL): 283 m³/s imposed
   on the inflow faces. The runtime gates hold throughout: depth at most 10 m
   and speed at most 20 m/s.
4. **Comparison** (`compare_zambezi_cartesian_cook.py`):
   - surface anchors and the wet IoU against the Sentinel-2 extent;
   - discharge as the exact exterior face flux;
   - settling between the last two frames;
   - Froude against the photographed whitewater.
5. **Calibration:** two passes of `calibrate_river_bed.py` (relax 0.8, 50 m
   smoothing, at most 2 m per pass), each warm-started from the previous cook.

## Results

The final cook (w2) is 60,000 steps (3,000 s), warm-started:

| measure | value |
| --- | --- |
| surface anchors (cook - GLO-30) | -0.24 to +1.00 m (9 anchors) |
| per-station surface error | median +0.52 m, p90 abs 1.02 m |
| wet IoU against Sentinel-2 at 203/283 m³/s | 0.77 (8,022 false-wet, 638 missed cells) |
| outflow face flux | 283.55 m³/s (+0.2 %) |
| settling, last 6,000 steps | p95 abs dh 0.009 m (max 0.12 m) |
| mass conservation residual | 1.5e-10 m³ |
| depth | p50 4.1 m, p95 7.2 m, max 7.7 m |
| speed | p50 1.25 m/s, p95 3.8 m/s, max 6.7 m/s |
| Froude | p50 0.20, p95 0.68, share > 1 0.9 % |

- **Calibration history:**
  - Uncalibrated (walls, cold start): +1.74 m median, IoU 0.71, outflow
    279.2 m³/s.
  - Pass 1: +0.84 m and IoU 0.75, but it had not settled (outflow 302).
  - Pass 2 is the table above.
- **Depth cap:** calibration can only lower the bed where the 6.5 m cap
  allows. 9,873 cells are capped after pass 2. The highest remaining anchors
  (+0.8 to +1.0 m at stations 2025, 2425 and 3025) are where it binds.
- **Whitewater is not where the photographs show it.**
  - Per 250 m of station, the photographed whitewater share is 28 % at
    2,750 m (Stairway to Heaven), 9.5 % at 1,500 m and 7 % at the Boiling Pot
    outflow.
  - The cooked Froude > 0.8 share is instead highest at 750 m (12 %) and
    2,250 m (10 %), and only 1.7 % at 2,750 m.
  - As at Hance, an inferred bed cannot place the rapids.

## Runtime integration

`export_zambezi_evidence_runtime.py` writes, under
`scenario_upper_gorge_evidence_2025/cartesian_runtime/`:
- **the shared atlas** (`raftsim.cartesian_state_atlas.v1`): the tiles' bed
  and the settled h, u, v.
- **one source region** over every tile (`cartesian_east_north_m`), whose
  captured-water mask is the Sentinel-2 extent plus the cook's water.
- **the streaming manifest** (`raftsim.cartesian_water_streaming.v1`):
  - 224 m live windows, re-centred every 64 m;
  - 166 explicit valid-centre rectangles that keep every crop off unavailable
    cells;
  - 98.9 % of raft-depth water (> 0.3 m) is coverable.
- **the Cartesian coordinate map**, and a separate **curved progress map**
  for run progress. The progress map:
  - is the midline resampled at 0.25 m and smoothed with sigma 3 m (at most
    about 1.2 m shift), then thinned to at most 1 m;
  - exists because the 2 m midline turns one hairpin at a ~6 m radius at a
    vertex, and the loader's ±256 m corridor check rejected it (40 m edge
    step; now 12 m against the 16 m limit).
- **the launch:** station 294.7 m (5.5 m deep, 2.0 m/s). This is the slowest
  valid point in the first 500 m. It lies within a live window's reach of a
  valid rectangle and is wet within 6 m. The finish is station 3,382 m.

`terrain/upper_gorge_evidence_2025/` holds:
- a 2017² heightfield (relief 146.4 m);
- the Sentinel-2 drape of 2025-10-03, with albedo median 0.10 and the water
  replaced by a darkened bank-colour continuation (an invented bed colour);
- a 20 m GLO-30 backdrop 3 km around the Landscape (287,436 triangles, no
  collision);
- the local centreline;
- 8,853 evidence canopy trees and 2,534 understory shrubs. These sit on an
  inferred 10 m lattice inside the NDVI > 0.5 cover of the 2025-05-28 image
  (29.5 % of the window). They are broadleaf, and their heights (6-18 m) are
  inferred.

The editor builds the map as the landscape candidate `zambezi_upper_gorge`:
- **Shared Zambezi assets, load-only:** it uses the Zambezi look settings,
  textures, rock set, opaque vegetation family and live-water instance, and
  only loads them, so building it never re-saves `L_Zambezi`'s assets.
- **Cartesian water:** the water config names the Cartesian coordinate map,
  the streaming manifest and the band.
- **Run manager:** a pre-placed `RaftSimRunManager` holds the progress map. The
  game mode's fallback has none, and a Cartesian hydraulic map is never used
  for progress.
- **Live surface:** a placed 224 m live surface at the 2 m cells, subdivided
  twice.
- **Far-field water:** `RaftSimWaterSurfaceActor` now draws the cooked
  Cartesian far field for any Cartesian map whose config sets
  `bEnableCookedFarFieldWater`; before, only South Fork did.

## Validation

- `physics/tests/test_zambezi_upper_gorge_evidence.py`, 8 tests, all pass.
  They check:
  - sources, flows and the rapid audit;
  - the cook's anchors, discharge and settling;
  - the atlas, region and streaming data against the runtime's own load
    gates;
  - the progress map against the loader's corridor check;
  - the launch;
  - that the terrain export, editor catalog, gameplay constants, frontend
    scenario and staging match.
- `RaftSim.P4.RiverMapLoads.L_ZambeziUpperGorge` passes:
  - the Cartesian map binds, and the first window handoff is at the launch
    (1409, 302 m);
  - the run manager holds the progress map (3,441 points);
  - the live carrier carries solver velocity;
  - the cooked far field is visible beyond the live window;
  - one GLO-30 backdrop and all 11,387 canopy rows are placed;
  - the raft is upright with no swimmers;
  - the presentation is 1.0 m spacing, 50,625 vertices and 100,352 triangles.
- The build re-saved no tracked asset: `L_Zambezi` and its materials, textures
  and vegetation are untouched.

## Performance

`profile_reference_map_ps5.ps1`, 1,200 frames, run with no other engine,
build, Blender or cook job live:

| station | p95 | max | frames over 100 ms | game thread mean | GPU mean |
| --- | --- | --- | --- | --- | --- |
| 294.7 m (launch) | 34.3 ms | 66.7 ms | 0 | 21.5 ms | 8.3 ms |

Downstream stations could not be profiled. `RaftSim.SurveyReach` needs a
curved hydraulic map, so on a Cartesian map it logs "no river coordinate map
bound" and leaves the raft at the launch; the two runs requested at 1,500 m
and 2,750 m measured the launch again and are not reported. The run
manager's review start (`-RaftSimWaterReviewStation`) is South Fork-only.

## Limits (why this is not accepted)

- **No bathymetry.**
  - Depth is inferred and capped at 6.5 m by the runtime's 10 m gate.
  - No depth data exist for the gorge. If its pools are deeper than the cap,
    as the calibration pushing against the cap suggests, the cooked water is
    shallower and faster than reality: 2-5 m/s along most of the midline.
- **Gorge walls are inferred.** GLO-30 cannot resolve the basalt walls, so a
  fixed 6 m wall profile replaces them near the water.
- **The surface reference is coarse:** GLO-30's edited water is good to about
  ±2 m, and the anchors are only that good.
- **Whitewater placement fails** (see Results). The rapids' real hydraulics,
  including Stairway to Heaven's, are not reproduced.
- **Far-field presentation:** other South Fork-only presentation paths stay
  South Fork-only on this map. They include foam sources, atlas stencil
  caching, the metric breaking search and shoreline fan topology.
- **Not yet done:**
  - a runtime reach survey and downstream-station timing, which need survey
    and review-start support on non-South Fork Cartesian maps;
  - review against photographs. The two landscape captures show the
    capture-only ribbon on the straight run at 430-590 m, not the live water.
