# Futaleufu evidence-based reconstruction

Requested 2026-09-06. Queued after completion and validation of Pacuare.
Order: South Fork, Colorado Grand Canyon, Pacuare, Futaleufu.
Implemented 2026-09-27 as the geographic `L_Terminator` (OSM 72.9-75.3 km).
Not accepted; see
`docs/reconstruction-review-2026-09-07/futaleufu-terminator-evidence.md`.

## Objective

Reconstruct the Futaleufu run's rapids, including boulder positions, rock
islands, channel bends, constrictions, drops and banks, as closely as available
online evidence permits. Then make the water physics and geometry consistent
with the reconstructed environment.

## Work and acceptance

1. Audit the playable reach, geographic origin, rapid locations, coordinate
   units and existing terrain provenance against independent geographic data.
2. Research available captured elevation, aerial imagery, LiDAR, river surveys,
   photographs and footage. Verify actual coverage, dates, resolution, datums,
   units and licensing; do not assume detailed LiDAR or bathymetry exists.
3. Reconstruct rapids individually using fixed landmarks and georeferenced
   evidence. Record confidence and source provenance per feature. Distinguish
   measured exposed rocks from estimated submerged shapes and artistic detail;
   do not substitute random boulder scatter for evidence-based placement.
4. Derive visible terrain/rocks, collisions, riverbed and hydraulic boundaries
   from the same reconstruction. Re-cook water fields against that geometry.
   Check discharge/storage balance, wet/dry banks, recirculation, wave/crest
   locations and raft interaction, with flow-dependent uncertainty recorded.
5. Compare actual in-engine overhead and boat-height views and animated runs
   with reference evidence. Validate shoreline stability, single-surface
   continuity, collisions and measured performance before acceptance.

Only begin after Pacuare's playable reconstruction and physics are validated;
downloaded sources and unintegrated terrain candidates do not satisfy that
prerequisite. Public footage remains reference-only unless licensed for use
in the game. This reconstruction is not river-navigation guidance.

## Scene audit and source research (2026-09-26)

Audit (step 1, repository only): `L_Terminator` is a 600 x 600 m reach-local
scene. It combines Copernicus GLO-30 with an interpreted solver strip, "not
survey or production terrain authority".

Sources (step 2, read only; nothing downloaded):

- **Rapid positions.** OpenStreetMap nodes: Zeta -43.28210, -71.92045;
  Throne Room -43.29351, -71.93766; Roller Coaster -43.30071, -71.95076;
  Wild Mile -43.30393, -71.96777; the Infierno group near -43.214, -71.855;
  and the Ruta 231 bridge -43.39925, -72.09376. The centreline is relation
  9751030.
- **Terminator itself has no published coordinate.** GoRafting puts it at
  river km 39.25, within the km 32.5-42.5 Terminator section. It must be
  placed by chainage along the OSM centreline, anchored on Throne Room
  (km 27.5) and the bridge.
- **No open data finer than about 10 m was found.** The run is entirely in
  Chile, so Argentina's 5 m MDE-Ar does not apply. IDE Chile's 12.5 m ALOS
  PALSAR DEM is resampled 30 m SRTM. No open DGA LiDAR or orthophoto exists;
  SAF sells aerial photography. OpenAerialMap has nothing.
- **Sentinel-2 (10 m) is the best open imagery.** The turquoise 50-100 m
  channel is clearly visible in it.
- **Flow.** DGA real-time stations 10702002-0 (at the border, upstream of
  the run) and 10704002-1 (above the Río Malito), plus the Argentine dam's
  daily turbine releases. A typical flow is about 15,000 cfs (425 m3/s).

Assessment: Hance quality is not reachable with open data. The planform and
wetted width can come from Sentinel-2. Banks, boulders and the Terminator
geometry stay largely inferred unless commercial imagery or elevation is
purchased.

### Downloaded (2026-09-26, with the user's permission)

Archived in `physics/data/real_world/futaleufu_river_chile/futaleufu_sources_2026_09/manifest.json`:

- **OSM** (ODbL): relation 9751030 joined into a 104.87 km centreline, with
  chainage. The rapid nodes run from Initiation (44.07 km) to La Cosa
  (65.65 km). El Trono (Throne Room) is at 62.40 km against GoRafting's
  km 27.5, an offset of 34.9 km. That puts the Terminator (GoRafting 39.25)
  near OSM 74.2 km, to be checked against the imagery.
- **Sentinel-2 L2A** (10 m; blue, green, red, NIR and SCL): 2020-02-20,
  2024-02-19 and 2026-01-04, over 43.18-43.42 S, 71.82-72.12 W.
  - Tile 18GYT is mosaicked with the same-datatake 18GYS for the southern
    1.5 km. Both are on one UTM 18S 10 m grid.
  - None of the three mosaics has cloud or shadow.

### Reconstruction (2026-09-27)

Done at the resolution the open data allows. The review doc holds the
method, results, validation, performance and limits.

- **Terminator located.** `audit_futaleufu_terminator_location.py` finds the
  strongest persistent Sentinel-2 whitewater at OSM 74.0-74.2 km. The
  GoRafting chainage predicts 74.15 km, and the indicator also fires at El
  Trono.
- **Surface.** GLO-30's edited water surface gives anchors every 200 m (about
  ±2 m, epoch flow unknown). The cook meets them within -0.34 to +1.14 m
  after two bed calibrations.

Open against the acceptance steps:
- **Step 3.** No rock or feature is resolvable at 10 m; boulders are
  inferred from whitewater.
- **Step 4.** The rapid's supercritical flow is under-produced (5 % of cells
  above Froude 0.8 against 25 % photographed whitewater). The image-date
  flows are unknown, since the DGA records need download permission.
- **Step 5.** No licensed footage comparison yet.
