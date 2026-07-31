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
