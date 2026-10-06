# Downstream review frame and the broad foreground face

September 15, 2026. Camera/evidence correction, **not terrain, water realism,
traversal, or performance acceptance**. Previous goal work improved source
packing; the intervening commit-only turn found a clean tree. This turn changes
the review frame and obtains evidence that changes the next terrain action.

## Confirmed coordinate bug and fix

The Cartesian hydraulic adapter correctly returns geographic east/north axes.
Its `WorldToRiverCoordinates` tangent is world +X, not downstream. The old
`shore_left/right` and low presets mistakenly used that tangent and left normal
as a river frame. South Fork already owns a separate downstream progress axis.

`IRaftSimRunCoordinateProvider` exposes the existing run manager's read-only
map and exact nearest-polyline projection to the raft plugin. It adds no reverse
game-module dependency, cache, tick, physics state, or terrain edit. Review
queries reject invalid/ambiguous providers and unsupported positions. Only
no-provider legacy worlds can fall back to a non-Cartesian hydraulic ribbon.

- Both shoreline heights/banks use the authored downstream tangent and
  reflected river-left, retaining the original offsets/exposure/FOV.
- `legacy_hydraulic_frame` explicitly reproduces the old shoreline camera;
  its log says `NOT_downstream`. Original captures remain untouched.
- `river_station*` resolves focus through the progress map, then samples
  hydraulic water at that WORLD position. `station=` walking also uses the
  progress map instead of treating easting as chainage.
- A requested camera that cannot be resolved or installed refuses a fallback
  capture. Named options without a preset retain the gameplay camera.
- Each request records actual camera position, pitch/yaw/roll, FOV, and an
  explicit `scenario_downstream` raft-coordinate declaration. The parser
  rejects mixed/malformed metadata and contradictory hydraulic relabeling;
  old logs retain their explicit legacy interpretation path.

This fixes evidence-camera placement only. It does not change the original
hydraulic API, the player's normal camera, or the geometry of any water/ground.

## Actual normal-map captures

All use the playable `/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach`, scenario
`south_fork_full_descent`, review start 8330 m, D3D12, 1280x720, normal water,
ephemeral profile, 12-second warmup, three screenshots at requested 1-second
intervals and actual recording. No saved selection or assets changed.

Commands after the common engine/map flags:

```text
RaftSim.CaptureSeries 12 3 1 downstream-camera-shore-v1-20260915 shore_left record
RaftSim.CaptureSeries 12 3 1 downstream-camera-legacy-v1-20260915 shore_left legacy_hydraulic_frame record
RaftSim.CaptureSeries 12 3 1 downstream-camera-fixed-v1-20260915 river_station_downstream focusstation=8350 focuslateral=0 record
```

Logs: `tmp/<label>.log`. Stills: `unreal/Saved/Screenshots/<label>_NNN.png`.
All three `_001` originals were inspected, plus corrected shore decoded 05s.
The two shoreline clips were completely decoded (not continuously watched):
104 source frames each, durations 5.927/5.934 s, 178 decoded frames each through
PTS 5.9 s. Fixed-station clip records 94 source frames over 6.028 s. Encoder
30 Hz is not playable FPS. ROI names inherited from the old decoder do NOT
identify matching physical regions after changing the view.

| View | Fixed world camera cm | Yaw | Request-time downstream range m |
| --- | --- | --- | --- |
| Corrected shore-left | -543488.36, -360723.19, 1058.02 | 157.011283° | 8352.158–8356.372 |
| Explicit old axes | -544076.74, -360823.15, 1056.98 | -41.423666° | 8352.209–8356.427 |
| Fixed 8350 m, looking upstream | -544502.16, -360700.72, 996.15 | 18.43° | 8352.158–8356.151 |

FOV is 90°. All three capture audits confirm zero camera displacement/angle
change and three distinct PNGs. These are separately evolved runs, not exact
same-state A/B captures. Corrected shore shows the opposite/downstream stretch
instead of the dominant foreground face. It still has a broad smooth crest,
blanket-like froth and an incomplete-looking distant landscape. The fixed
upstream view also shows large smooth water faces and inadequate crest breakup.
Neither constitutes convincing whitewater. No new FPS run was warranted for
this capture-only change; last ordinary run remains **24.225877 FPS / p95
47.78 ms**, failing the 30 FPS / 33.333333 ms gate.

## References accessible again

Read-only in-app browser review; no remote video download or source upload:

- [Qweniden bank-side reference](https://www.youtube.com/watch?v=2XTbOCNDcZQ),
  “Trouble Maker South Fork American River 7/15/2022 - Raft California”, 3:24.
  Used the player's Skip-ad button, then inspected paused 0:08 and 0:13.
  Angular exposed boundaries, staggered local crests, dark gaps, and irregular
  aerated tongues are visible. The latter image includes raft-generated splash.
- [John Elkins raft-level reference](https://www.youtube.com/watch?v=ZEG1kvjNI30),
  “Troublemaker Rapid on the South Fork American River”, 1:08. Inspected 0:05,
  0:20 and 0:30 using ordinary player controls. The approach has dark water and
  intermittent narrow white streaks beside exposed rock, not a full-width
  homogeneous white cover.

No calibrated camera pose, matched discharge, bathymetry, new shipping rights,
or continuous-motion acceptance follows from these paused frames. The camera
correction does not make the game/reference views registered equivalents.

## Source-face probe changes the next terrain action

Preliminary pinhole rays through eight pixels of the old-axis view intersect
the unchanged registered mesh at **authority 1 (captured DEM ground)**, not
authority 5 inferred flanks. This is geometric source attribution, NOT a GPU
object-ID/depth readback: water/refraction/foliage occlusion are not modeled.

Inputs: original mesh SHA256 `8bdf1a586e7bd2536eaf25a982763efd9e5a558e7172fd7897b8ae0ecc8fe06b`,
log camera position above, pitch -8.033996°, yaw -41.423666°, 90° horizontal
FOV and 1280x720. Registered camera east/north/datum-relative Z is
(-8.9010302224, 7.7839124382, 10.5698) m. Transform world XY using the map's
origin (689236.999999999,4293073), Y sign -1 and rapid origin
(683805.1336302214,4296673.447587562); Z is already relative to 220 m NAVD88.

Construct rays from forward/right/up with screen offsets
`(2*x/1280-1, (1-2*y/720)*720/1280)`, reflect world Y into source north,
normalize, and choose the nearest positive two-sided Möller–Trumbore triangle
intersection. All three vertices of every hit below have authority 1:

| Pixel x,y | Original triangle index | Registered east,north,Z m |
| --- | --- | --- |
| 200,420 | 176501 | -6.627041,17.295865,8.665805 |
| 400,400 | 177225 | -4.344681,16.475339,8.686371 |
| 600,400 | 179387 | -1.745740,14.956060,8.492501 |
| 200,500 | 177938 | -6.957238,16.232187,7.952778 |
| 400,500 | 179380 | -5.159350,15.054557,7.741481 |
| 600,500 | 181541 | -3.234608,13.480102,7.592361 |
| 800,400 | 182270 | 1.663208,13.197564,8.206359 |
| 640,360 | 580592 | 0.066314,15.696275,8.881829 |

`build_troublemaker_captured_geometry.py` assigns authority 1 outside its water
mask and preserves the DEM. That does not establish a raw ground return at
every interpolated raster vertex. In the original classified-return NPZ,
the source rectangle east [-8,3], north [12,19] m contains 1,710 class-1
unclassified returns, 13 class-2 ground returns, four class-7 noise and five
class-9 water returns. The class-1 median height above the DEM is 1.791312 m;
this is NOT evidence that every unclassified point is rock (vegetation remains
possible). No class-2/10 return falls within 0.5 m of the first three hit points
or (-3.235,13.480). The selected broad face is not justified as a measured
continuous rock surface merely by its authority-1 raster label.

NEXT: verify that patch against fixed exposed landmarks in NAIP/reference
footage and the original classified point cloud; distinguish interpolated
DEM support from actual returns. Do not tune the unrelated flank-band prior
or relabel unclassified returns as surveyed rock. Keep original source
rasters/returns intact. Then revise only justified reconstruction, recook the
same hydraulic/collision geometry, and revisit the actual crest/froth problem.

## Verification and identities

- Final Development Editor build PASS, 16.66 s / seven actions, no warnings.
  Earlier build warning about an uninitialized output was corrected explicitly.
- Final native report: **30 PASS**, zero warnings/failures/not-run/in-process.
  Includes actual run-provider queries, Cartesian rejection, reflected banks,
  both heights, exact old-view controls, ambiguity, invalid maps and the prior
  28 shoreline/packing/crest/GPU tests. The first run had two fixture-world
  destruction warnings; fixed by giving that fixture a proper engine context.
- Focused Python: **14 PASS**. Broader presentation selection: **29 PASS /
  four FAIL**. All four also fail when executing the committed HEAD tests:
  old spray-map string assertions (two), old visible-carrier vertex string,
  old hard-coded 48900 m review bound. They remain unresolved, not waived.
  These are separate from the prior 13 retained physical regressions; no full
  physics rerun or acceptance claim this turn.
- All **464 protected source/actor hashes match**. No terrain, material,
  hydraulic assets, menus, default quality or physical tolerances changed.
  Generated recordings, reports and binaries remain ignored, not committed.

Evidence SHA256:

```text
native-v2/index.json 2d275c788543367af1480285e39aecc5e3ecb60bda9af5acef07119aa94f5c98
focused-v2.xml d9cb45f8be0246e7b4da44fffea4ebf66d6b63b1d191697f39ad906656004646
shore _001.png 444d2c294fe4fdc4efbcc7dbda608cf1520681b2213ef8ba3358bf2ad561495a
legacy _001.png 5273b18df554e502d7b48d7259675be5bffc3eb6d79230ac249bab1d9cf58e59
fixed _001.png 93fd8e0c914d526b95e51f16580413cf460e8841c006c46affa88ef07d1e1a1d
RaftSim_20260915-125325.mp4 3eb492b047d642438e6c46e6597b45392188b234f589b13f4aca0873d1c5f393
RaftSim_20260915-125534.mp4 95d2c4aecced59292fd48e831259d316078d10c84a84186e50acbf6f7a644643
RaftSim_20260915-125854.mp4 97a4cab4874a5113e919536775d63c8c6770bb182e6d5d39a074a38928a1cabe
final RaftSimRaft DLL 9f0af5abc1e5162373314195ea62480dd166b541d7d24b82027f9c00cace14c0
final game DLL db331c9ed7133704aa487df515b7155a9a63e54639ab2307051019076bc0bc95
```

The full South Fork scene remains OPEN. Colorado → Pacuare → Futaleufu,
Chilko/Zambezi/all-scene water, crew, normalization, regressions and release
remain OPEN. Troublemaker remains a rapid inside South Fork, never a menu
scenario. No gate is weakened by this evidence correction.
