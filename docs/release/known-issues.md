# 1.0.0-rc1 known issues and deferred lanes

This file is part of the release candidate, not a waiver of final acceptance.

- The current local Mac runner has an Apple Development identity but no Developer ID
  Application identity or notarization credentials. Development-signed RC packages are
  suitable for local QA only; public macOS distribution remains an M10 gate.
- A Windows/RTX runner is not present in this workspace. Windows x64 packaging,
  Authenticode, RTX 3060/4070 performance, input-device hardware, and clean-machine QA
  must run on the release workflow before the Windows artifact can pass.
- Proton compatibility requires a Linux/Steam runner and the actual Windows artifact.
- Named guide, geospatial, art-direction, and legal reviewers have not supplied final
  acceptance. Automated hydraulic, source, rights-file, material, and package checks do
  not substitute for those people.
- Where surveyed bathymetry, banks, or hazard geometry was unavailable, deterministic
  procedural infill is used and labelled. The game and its maps are not navigational
  products.
- VR/OpenXR and multiplayer are intentionally disabled for flat-screen single-player
  1.0 and remain post-launch work.

Any crash, corrupted save, progression blocker, non-finite physics state, missing runtime
data, or material fallback warning is a release-blocking defect rather than a known-issue
exception.

## Open release gates as of 2026-09-26 (blocking, not waived)

Editor-hosted Development build on the development host; no packaged-build result here.

- `RaftSim.M9.BReleaseCandidateQA` fails only its twenty-rapid regression: 57 of
  60 cases pass; the three legacy Troublemaker cases step an 801 x 161 cell field
  at 11-14 ms against the 1.6 ms per-step budget (the other nineteen rapids use
  101 x 21 fields). Play no longer uses that legacy field, but the gate is kept.
- `RaftSim.P4.RiverMapLoads.L_Zambezi` fails its start-apron spray count (0 of
  6 emitters): Zambezi's procedural field, run in real time, breaks below the
  emitter threshold. On 2026-09-27 all nine start-apron breaking sites (55-96 m
  from the camera, station 160 m) read intensity 0.00 against the 0.12
  threshold; the test now logs each site. The fix is evidence-based Zambezi
  hydraulics, not a lower threshold. The Sentinel-2 bands (four dates at
  203-2,794 m³/s Victoria Falls flows) and the ZRA daily flows are now
  archived (2026-09-28); a whitewater audit places Stairway to Heaven, Midnight
  Diner and Commercial Suicide within 250 m of their digitised stations.
- South Fork busy-rapid frame time is borderline against the 20 FPS goal (50 ms
  p95); earlier rapid-station runs ranged 42-51 ms.
- Several editor-context suites need explicit inputs or GPU fixtures
  (`RaftSim.M3.DetailFullRouteCoverage`, `DetailNativeHandoff`,
  `TerrainResidencyRoundTrip`, `RaftSim.M4.MeatGrinderLiveD3LineCalibration`).
- South Fork submerged geometry is inferred (discharge-consistent bed v2), not
  measured. Colorado Hance is now an evidence-based geographic reach (2021 DEM
  and orthophoto, 2014 sonar pools, labelled inferred rapid bed and
  imagery-located inferred boulders, USGS 3DEP terrain and backdrop beyond the
  corridor; runs p95 31-37 ms with no hitches). It is not accepted:
  - Its whitewater extent comes from the photographs (appearance evidence), not
    the solver, and has no hole or crest relief.
  - Open water is several times brighter than the photo's deep pools.
  - Calm-water levels are known to about ±0.5 m.
  - Terrain colour beyond the photo footprint is invented.

  See the [review](../reconstruction-review-2026-09-07/colorado-hance-evidence.md).
  Pacuare Huacas-Pinball is now an evidence-based 2.3 km geographic reach.
  It uses IGN 1:5,000 contours and banks, the 2014-2017 orthophoto,
  contour-crossing water-surface anchors and imagery-placed canopy. It runs
  p95 24-30 ms with no hitches. It is not accepted:
  - It has no bathymetry. The bed is inferred and calibrated to three anchors
    (+0.11 to +0.31 m).
  - At the 45 m³/s planning flow the water covers bars the photo shows dry.
  - The lower rapids are hydraulically milder than their photographed
    whitewater.
  - Vegetation structure and rock heights are inferred. Since 2026-10-01 the
    forest is closed and layered:
    - canopy 18-38 m with overlapping crowns;
    - a sub-canopy;
    - two shrubs per canopy tree;
    - a shaded forest floor.

    The pale ground between lone trees is gone.
  - IGN commercial redistribution is unconfirmed.

  See the [review](../reconstruction-review-2026-09-07/pacuare-huacas-evidence.md).
  Futaleufu Terminator is now an evidence-based 2.4 km geographic reach. It
  uses Sentinel-2 10 m wetted extent and whitewater, Copernicus GLO-30
  terrain and surface anchors, and a Terminator located by persistent
  whitewater at its chainage. It runs p95 23-28 ms with no hitches. It is not
  accepted:
  - The imagery is 10 m and the elevation 30 m, so rocks, holes and banks are
    unresolved.
  - The bed and flow are inferred.
  - Since 2026-09-29 the bed carries observed rapid features from outfitter,
    guidebook and video observations. The cook breaks at the Terminator Wave,
    through the Terminator core, at Khyber Pass and at Himalayas. It does not
    break at T2 (Son of Terminator): GLO-30 shows a flat pool there, so T2
    shows only as appearance whitewater.
  - Since 2026-10-01 its observed and bank rock is grey granite, a tinted
    instance of the reviewed rock scan, not the scan's mossy tan. The colour
    is approximate.

  See the [review](../reconstruction-review-2026-09-07/futaleufu-terminator-evidence.md).
  Chilko Lava Canyon is now an evidence-based 4.0 km geographic reach from
  above Bidwell Rapid to the White Mile. Its terrain and the flight-day water
  surface are measured by LidarBC 2023 1 m LiDAR, the bed is calibrated to that
  surface (anchors -0.14 to +0.45 m), the canopy follows the BC forest
  inventory, and it runs p95 19-21 ms with no hitches. It is not accepted:
  - The bed is inferred, and the 93 m³/s runtime band extrapolates from the
    45 m³/s calibration without a width or stage check.
  - The imagery is 10 m. The water hue was fitted to Sentinel-2 on
    2026-09-29 (it had read deep blue); its brightness is unmeasured.
  - Since 2026-10-01 its talus and bank rock is dark basalt, a tinted
    instance of the reviewed rock scan. The colour is approximate.
  - Tree positions and sizes are inferred within the inventory polygons.

  See the [review](../reconstruction-review-2026-09-07/chilko-lava-canyon-evidence.md).
  The Zambezi upper gorge (`L_ZambeziUpperGorge`, Boiling Pot to below
  Stairway to Heaven) is a new evidence-based 3.5 km map beside the 30 km
  `L_Zambezi`. Its water is a map-aligned Cartesian cook at the 283 m³/s
  flow of the 2025-10-03 Sentinel-2 image. The GLO-30 surface anchors are
  -0.62 to +0.97 m and the wet IoU is 0.97. The first build left grey cones
  of raw DEM standing in the river at the hairpins; a station-projection fix
  on 2026-09-29 removed them. It is not accepted:
  - There is no bathymetry: depth is inferred and capped at 6.5 m by the
    runtime's 10 m gate.
  - The gorge walls are inferred below GLO-30's 30 m resolution.
  - Since 2026-09-29 the bed carries observed rapid features. The cook breaks
    at every named rapid except Rapid 5.5 (anchors now -0.62 to +0.97 m). It
    has no bed data.
  - Since 2026-09-30 the gorge walls are reconstructed from observations. They
    are banded basalt cliffs placed on the GLO-30 rim and wall mid-height,
    with talus aprons and the observed beaches. Their shape is inferred.
  - It runs p95 35.0, 32.8 and 44.8 ms with no hitches at the launch, the
    1.5 km whitewater and Stairway to Heaven. The last is 5.2 ms under the
    budget.
  - Beyond the cooked cuts the channel is dry, so the river ahead of the
    finish looks like a dry bed.
  - Since 2026-10-01 the woodland shows its October state, measured from the
    October Sentinel-2 NDVI:
    - 19 % of trees stay green (riverine and spray-fed);
    - 32 % hold a few dry leaves;
    - 49 % are leafless.

    Species and branching are inferred.

  See the [review](../reconstruction-review-2026-09-07/zambezi-upper-gorge-evidence.md).
- Observed-whitewater display (all six international river maps,
  2026-09-30): the render-only whitewater floor includes each reach's
  observed-rapid catalogue. It is shown at the calibrated gain of 0.25 (the
  former 0.9 rendered large rapids as one white sheet). It is appearance
  evidence, not hydraulics. The Cartesian Zambezi upper gorge's live core
  draws the GPU moving detail's foam, which ignores that floor. Since
  2026-10-01 the layer also joins the detail's breaking source there
  (`ObservedWhitewaterEntrainmentGain` 0.6, calibrated by eye), so Morning
  Glory and Stairway to Heaven break heavily and the pools stay calm. See
  [observed-rapids-2026-09-29.md](../reconstruction-review-2026-09-07/observed-rapids-2026-09-29.md)
  and
  [observed-whitewater-terrain-2026-09-30.md](../reconstruction-review-2026-09-07/observed-whitewater-terrain-2026-09-30.md).
- Zambezi 30 km reference run (`L_Zambezi`, 2026-09-30): its 25 rapids now
  sit at stations derived from observations, not the stylised map:
  - Sentinel-2 whitewater, side-stream confluences, the Taita Falcon Lodge
    fix and outfitter kilometres;
  - many rapids moved 200-1,800 m;
  - Rapids 19-25 are low confidence.
  The run now finishes at Mukuni Beach (28,950 m) and each rapid carries its
  observed whitewater. The water is still a procedural seed with one bounded
  jump per rapid; there is no rapid-specific hydraulic geometry.
  Since 2026-10-01:
  - Each rapid is a central tongue between shallow boulder shelves. The lace
    still spreads bank to bank at the bigger rapids, because the live solve
    evens the surface drop across the channel. This is deferred to a later
    water pass.
  - The walls are dark basalt in direct sun as well as in shadow. The fix was
    the world-space terrain normal, which had tilted every wall face toward
    the sky.
  - The walls carry inferred lava-flow ledges and gullies on 3.1 m render
    cells, cast shadows, and have rockfall on the ledges. The ledges are
    generic banding, not measured relief. Collision is still the smooth
    Landscape.
  - The banks are grey sand and black boulders, no longer an orange beach.
  - A patchy green fringe (5,008 shrubs and 651 riparian trees, inferred)
    lines the waterline along the whole run.
