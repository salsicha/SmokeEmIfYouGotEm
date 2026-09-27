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
  emitter threshold.
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
  - Vegetation structure and rock heights are inferred.
  - IGN commercial redistribution is unconfirmed.

  See the [review](../reconstruction-review-2026-09-07/pacuare-huacas-evidence.md).
  Futaleufu has sources downloaded but no reconstruction yet.
