# Pacuare evidence-based reconstruction

Requested 2026-09-06. Queued after completion and validation of Colorado,
which follows South Fork. Not started or accepted.

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
bed and cross-section must remain inferred. Proposed downloads, awaiting the
user's permission:

1. IGN_5 contours and hydrography clipped to the Huacas-Pinball corridor
   (small vector files).
2. One orthophoto preview tile to check coverage and resolution, then the
   corridor tiles if it is usable.
3. The OSM centreline and rapid nodes.
4. A cloud-screened Sentinel-2 L2A scene from the AWS open archive (no
   account needed).
