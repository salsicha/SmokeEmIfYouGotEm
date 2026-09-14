# Normal-play foam optical isolation — September 13, 2026

The preceding goal turn made progress by rejecting a measured-slower corner
cache, restoring the original normal-play default and verifying86 tests plus
ordinary play. Latest12.965487FPS/p9590.3953ms fails30; no visual acceptance.
This pass follows the broad white appearance through actual source/state data.
It does not repeat the rejected affine/sharpened-grid optical changes.

## Current GPU observations

Normal FullReach snapshot capture41854 CLOSED0; game0, no timeout, verified
cook suspend/resume0. No source/material changes preceded it. Three snapshots
under `tmp/south-fork-foam-source-observation-v1-20260913_00` through `_02`
contain the actual128x128 mean flow, paired geometry, persistent state and
resolved surface. All float32 arrays are finite. Simulation times8.000000417,
12.266667306 and16.666667536s; the snapshots are not all simultaneous with the
later30s screenshot and cannot be used for pixel-by-pixel visual attribution.

Exclude eight boundary cells (4m) on each side and require mean depth>.01m:

| Snapshot | Wet interior cells | Source>.1 | Coverage>.5 | Coverage>.8 | Coverage>.5 with source<.01 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 00 | 9483 | 827 | 515 | 180 | 225 |
| 01 | 9979 | 962 | 667 | 245 | 327 |
| 02 | 9968 | 955 | 682 | 249 | 339 |

Median coverage .000437737/.001384735/.002004981;95th-percentile coverage
.515001482/.572002411/.580176306. Peak density12.318006/15.195999/16.540113.
This is local data, not a claim that every visible white pixel is reflection.
Dense foam can be advected into currently source-free cells. Do not reduce
source density simply to force the screenshot to look darker.

Source tracing confirms GPU flow.W comes from wet-supported convergence/
deceleration plus a max-union with accepted spilling crests, not CPU vertex
foam. Registered material replaces CPU foam inside the detail window and
blends it only at the edge. Therefore a CPU-only generator change would not
directly fix the interior visual. Geometry, source and parent are unchanged.

## Optical knockout diagnostic

Added non-shipping, South-Fork-only `-RaftSimFoamOpticsOff` to set the existing
MID `SouthForkFoamOpticalDensity` to zero. The final optical consumer then
returns zero coverage; the registered inverse-density uses its existing safe
denominator. No saved material/map, transported density, source, WPO, normal,
carrier or contact code is changed. It disables the optical foam contributions
to color/roughness/scattering/opacity together, not just base color. It is a
diagnostic, never a proposed production appearance. Default remains unchanged.

Build59009 CLOSED0 in41.90s. First capture82587 CLOSED0 with cook resumed, but
the diagnostic DID NOT activate: its initial guard used the old full_hydraulics
cooked-field path, whereas this reconstructed map now has a different source.
It is preserved as invalid comparison evidence. The guard now checks the exact
FullReach map identity without changing the broader old path-based logic,
whose other effects include geometry/subdivision and must not be casually
enabled. Rebuild78428 CLOSED0 in42.60s.

Valid optical knockout88433 CLOSED0, game0, no timeout, cook suspend/resume0;
log confirms `FoamOpticsOff:`. The screenshot
`unreal/Saved/Screenshots/south-fork-foam-optics-off-v2-20260913.png` was inspected.
It STILL has a broad bright reflective water surface with transported foam
optics disabled. This establishes a separate water-material/reflection issue,
not that all white is reflection or that foam is correct. Raft pose/camera differ
from the previous run, so it is not an exact pixel-difference measurement.

The existing material generator adds view-dependent `FresnelSpecular` to the
specular input and blends a sky tint into base color. Single Layer Water already
composites physical reflection captures/sky/SSR; see
[Epic's Single Layer Water documentation](https://dev.epicgames.com/documentation/unreal-engine/single-layer-water-shading-model-in-unreal-engine).
The explicit `-RaftSimDielectricWaterReview` comparison retains foam and sets
Specular=.255 (Epic's documented water value), FresnelSpecular=0 and
FallbackSkyReflectionStrength=0. It changes no roughness, normal, light, source,
geometry, timestep, contact or authored assets. This is a bounded candidate,
not an accepted appearance or claim that .255 fixes grazing-angle reflection.
[Epic's physically based material inputs](https://dev.epicgames.com/documentation/unreal-engine/physically-based-materials?application_version=4.27&lang=en-US)
provide the specular calibration. Build7458 CLOSED0 in42.94s.

Dielectric capture20625 CLOSED0, game0, no timeout, cook suspend/resume0. Log
confirms the dielectric switch and does not enable the foam knockout. Screenshot
`unreal/Saved/Screenshots/south-fork-dielectric-water-v1-20260913.png` inspected:
bright broad clumps and a rounded/glossy underlying surface remain. Not accepted
as a visual improvement, NOT promoted to normal play. Both switches remain
non-shipping opt-in diagnostics. No resolution/quality/timestep/geometry/source
change and no new ordinary-play or native-gate performance claim.

Raft DLL SHA256
`98d48f8d88770a3849227d3d70946df395f7c09be161ba4981bfc00407cede4b`.
Map DB3080..., material26AA50... and save181D1E... remain byte-identical after
all captures. Native86-test rerun53639 CLOSED0:86 clean passes, no warning/
failure/unrun tests,21.836927s. Report
`tmp/south-fork-optical-isolation-native-v1-20260913/index.json`. Its existing optical fixture
retains the separate rejected filtered-froth helper, not the production clump
helper; a pass must not be presented as production-froth appearance acceptance.

Next implementation must address persistent surface deformation/breaking and
the motion of its foam, with paired rendered/contact observations. Do not repeat
the two rejected optical mappings, indiscriminately lower source density, or
infer that a mean coverage snapshot explains all white pixels in a later image.
The material's current FrothTime still comes from wall time, while density uses
committed water time; that remaining transport-phase mismatch is also open.
The full physical breaking/entrainment/motion, terrain/crew,30FPS, remaining
rivers and final release/commit goal stays active.
