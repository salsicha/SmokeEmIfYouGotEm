# Pacuare evidence-based reconstruction

Requested 2026-09-06. Queued after completion and validation of Colorado,
which follows South Fork. Implemented 2026-09-27 as the geographic
`L_UpperHuacas` (Upper Huacas to Lower Pinball). Not accepted; see
`docs/reconstruction-review-2026-09-07/pacuare-huacas-evidence.md`.

## Objective

Reconstruct the Pacuare run's rapids, including boulder positions, rock islands,
channel bends, constrictions, drops and banks, as closely as available online
evidence permits. Then make the water physics and geometry consistent with
the reconstructed environment.

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

Only begin after Colorado's playable reconstruction and physics are validated;
downloaded sources and unintegrated terrain candidates do not satisfy that
prerequisite. Public footage remains reference-only unless licensed for use
in the game. This reconstruction is not river-navigation guidance.

## User-requested next river

On 2026-09-06 the user queued Futaleufu after Pacuare is completed and
validated. See `futaleufu-evidence-reconstruction.md`. Finish Pacuare's playable
scene, collision and water-physics validation before starting Futaleufu.

## Scene audit and source research (2026-09-26)

Audit (step 1, repository only): `L_UpperHuacas` is an interpreted 600 m
straight reach. Its 600 x 78 m solver strip and visual infill are
"review-gated reach-local visual and collision infill, not survey or
production terrain authority". Its only elevation is Copernicus GLO-30 (30 m),
and its imagery is NASA GIBS MODIS (250 m); neither resolves a 30-80 m channel.

Sources (step 2, read from public pages and service metadata; nothing
downloaded):

- **Rapid positions.** OpenStreetMap (ODbL, attribution for a rendered game)
  has Lower Huacas ("Huacas Abajo", grade 4) at 10.01257 N, -83.50557 W
  (node 13805040110), Dos Montañas at 10.06808, -83.49670, and the river
  centreline (relation 12000489). GoRafting river kilometres: Upper Huacas
  12.85, Lower Huacas 13.33, Upper/Lower Pinball 14.18/14.40, Dos Montañas
  22.67. So Upper Huacas lies about 480 m above the Lower Huacas node.
- **Costa Rica IGN 1:5,000 vectors (SNIT WFS `geos.snitcr.go.cr/be/IGN_5/wfs`).**
  Layers are `curvas_5000` (10 m contours), `hidrografia_5000` and
  `forestal2017_5k`, in EPSG:5367. Access constraints and fees are "NONE" and
  no account is needed. Coverage of the Huacas reach is confirmed: 7,419
  contour and 237 hydrography features.
- **2014-2017 1:5,000 orthophoto (SNIT WMS/WMTS `Ortofoto2017`).** The mosaic
  covers 85% of the country. Its ground sample distance is unstated and gorge
  coverage is unverified.
- **Licence.** IGN data is free to use with attribution. Commercial
  redistribution is not explicitly addressed, so it is treated as unclear
  (contact: IGN).
- **No national LiDAR, bathymetry or discharge gauge was found.** The only
  flow reference is a painted rock at km 9.67.
- **Sentinel-2 (10 m, open with attribution) is the fallback imagery.**
  FABDEM is non-commercial and excluded. AW3D30 needs an account. TanDEM-X 90
  is science-only.

Assessment: Hance quality is not reachable. The contours and orthophoto can
fix the gorge walls, planform and banks where the canopy allows. The channel
bed and cross-section must remain inferred.

### Downloaded (2026-09-26, with the user's permission)

Archived with hashes, requests, CRS and licences in
`physics/data/real_world/pacuare_river_costa_rica/huacas_sources_2026_09/manifest.json`:

- **IGN_5 vectors** (EPSG:5367): 4,051 contour lines at a 10 m interval
  (vertices every 11 m), 139 hydrography lines and 23 tree-cover polygons
  for 9.985-10.045 N, 83.475-83.545 W.
- **Orthophoto 2014-2017**: the service is a tile cache (WMS GetMap fails
  unless tile-aligned), so it is read through WMTS on the EPSG:3857 grid.
  - 148 zoom-18 tiles (0.59 m/px) cover 400 m either side of the OSM
    centreline, OSM chainage 81.8-85.0 km. The coverage is complete.
  - Channel, gravel bars, emergent boulders and whitewater are visible.
  - The effective resolution is about 0.8-1 m: z19 and z20 are
    interpolated from z18.
  - The exact flight date is not published.
- **OSM** (ODbL): relation 12000489 joined into a 141.35 km centreline, with
  chainage. The chainage agrees with GoRafting: Lower Huacas to Dos Montañas
  is 9.44 km on OSM against 9.34 km from GoRafting. GoRafting's km 0 is
  about 4.07 km above the Linda Vista put-in, so Upper Huacas (GoRafting
  12.85) sits at OSM 82.56 km and Lower Pinball (GoRafting 14.40) at OSM
  84.11 km.
- **Sentinel-2 L2A** (10 m; blue, green, red, NIR and SCL; tile 17PKM):
  2018-04-01, 2021-12-11 and 2025-01-19. I screened 22 candidate scenes by
  the scene-classification (SCL) layer inside the window; these three have
  no cloud or shadow over the reach.

Tools (numpy only): `fetch_wmts_corridor.py`, `fetch_sentinel2_window.py`
(windowed COG range reads), `extract_osm_river_centreline.py`,
`png_numpy.py`.

### Registration check (2026-09-27)

All sources were brought into CRTM05 (EPSG:5367) with
`physics/scripts/geo_frames.py`: generic transverse Mercator, plus Web
Mercator for the orthophoto tiles. Findings:

- **Registration.** The IGN river-bank lines (hydrography layer D01, drawn as
  double lines) follow the orthophoto water edges within a few metres, and
  the OSM centreline runs inside the channel. The 1:5,000 cartography was
  evidently compiled from the same 2014-2017 photographs, so the bank lines
  give the wetted extent at the photo flow.
- **Water-surface evidence.** The 10 m contours stop at the banks. Each
  contour end on a bank fixes the water surface at that point to within the
  contour's accuracy, which gives a stepwise surface profile along the reach.
  The D01 `elevacion` attribute is unusable (−38,252 to 11,459 m). D03
  features are small ponds outside the reach.
- **Orthophoto.** The photo shows the rapids' whitewater, pools, gravel bars
  and emergent boulders at about 1 m. It can supply a wetted mask, a
  whitewater mask (for the observed-whitewater field used at Hance) and
  emergent-rock positions.
- **Discharge.** No gauge is attached. The cook will use the existing 45 m³/s
  runnable-planning band, labelled as not measured.

Next, following the Hance pipeline:
1. Contour-to-DEM interpolation, with the banks held at the surface profile.
2. A discharge-consistent inferred bed.
3. Orthophoto-derived rocks and whitewater.
4. The curvilinear scenario and cook, then runtime export as a geographic
   `L_UpperHuacas` replacement.

### Reconstruction (2026-09-27)

Done, following the steps above. The review doc holds the method, results,
validation, performance and limits. The corrections to the registration
findings:

- **Banks.** The D01 bank lines enclose the gravel bars. They give the active
  channel, not the wetted width. The wetted water, bars and rocks come from
  the orthophoto instead.
- **Water-surface anchors.** Contour ends alone are ambiguous. The anchor is
  where an L contour first comes within 10 m of a bank going downstream: the
  water crosses L there. Stations are stable for bank distances of 8-25 m.
- **Midline.** The OSM centreline leaves the channel in places. The midline is
  built from facing bank points, and OSM only orders them.

Open against the acceptance steps above:
- **Step 3.** Rocks are orthophoto-located with inferred heights.
  Rapid-by-rapid confidence is recorded only as the measured and inferred
  split.
- **Step 4.** The lower rapids are hydraulically milder than their
  photographed whitewater. At 45 m³/s the water covers bars the photo shows
  dry.
- **Step 5.** No in-engine comparison with licensed reference footage yet.
  The views were checked against the orthophoto only.
