# Source-supported constriction: full-map collision and fresh flow

Reviewed 2026-09-18 UTC. This advances the isolated candidate toward a joint
terrain/flow review; it does **not** accept the rock interpretation, navigation,
water appearance, performance, or playable integration.

## Actual engine result

A fresh Unreal process reloaded the saved candidate, installed ground and cap.
Their complete directed collision-source hashes match independent source-array
hashes exactly: 803,842 triangles for each ground, 6,404 for the retained cap.
The candidate hash is
`f45babb0dff6a6f069d8c57a9485dd686ff39d36f1d7a732dd0c35470d924109`.
It then loaded the actual FullReach map and its relevant physical-ground actors.
The installed actor was reused for a transient candidate swap, then restored.
No second ground or cap actor was added; no package or level was saved.

All **70,017** native collision queries pass the unchanged **0.1 cm** gate:

| Scope | Queries | Largest error (cm) |
| --- | ---: | ---: |
| Installed hydraulic cells | 25,600 | 0.002010 |
| Installed changed-triangle locations | 7,007 | 0.000280 |
| Candidate hydraulic cells | 25,600 | 0.002010 |
| Candidate changed-triangle locations | 7,007 | 0.003568 |
| Candidate union roof vertices, exposed or covered | 1,601 | 0.031770 |
| Candidate union roof centroids, exposed or covered | 2,954 | 0.013851 |
| Candidate union boundary midpoints | 248 | 0.000218 |

Hit ownership is checked as well as position. Covered roof targets remain in
the evidence, with the visible ground intersection tested instead of deleting
those source targets. All 474 protected files remain unchanged, including map,
external actors, installed physical-ground assets and the local candidate.
Map SHA256 remains
`c6bda5ff5f680d22b291eb30a6c902488acd909bb7f2b6177fa7103cdd40399f`.

The generic source-probe builder previously considered only changed Z and old
triangle centroids. It now includes XYZ changes, connectivity changes and both
old/new centroid locations when they differ. Height-only revisions retain their
original query set; the old fixed-XY validation contract is not weakened.
This candidate uses a separate installed-union descriptor and native verifier,
not an exception inserted into the existing height-only playable-preview gate.

The first local descriptor used unreversed cap winding. Inspection of the
actual cap exporter showed its explicit Y reflection plus reversed triangles;
independently reproducing that convention yields the retained native cap hash
`162f2e8df30570a3c57ca82bfe1dd5755e5d4adbe05ea68ce09ad6f2392253d7`.
That preparation-only v1 descriptor is retained; v2 was used for the native run.
No source coordinate rounding or tolerance change was used to obtain the match.

Native session 50656 ended normally with exit 0 and an explicit successful
report, not just a successful process code. NullRHI and platform-SDK warnings
are not a rendering/platform-release pass. Earlier isolated import verification
also reported missing FBX smoothing-group information; no visual acceptance is
inferred from these collision checks.

## Fresh physical geometry and flow

The separately validated source-extension contract composes the original
bed-only revision with the 338 original class1 returns and 432 inferred flank
vertices. The old captured XYZ, seam and source classifications stay protected.
The resulting 841-core geometry and fresh input independently verify all
5,382,400 cells, unchanged source masks/stages, physical boundaries, roughness,
0.05 s time step and 45.3069545472 m3/s inlet discharge. No evolved old-bed water
was transferred onto the changed terrain.

- Geometry manifest: `tmp/constriction-source-union-geometry-v1-20260918/manifest.json`,
  SHA256 `b2eae6085cc55246fec06137fb5bd8de617dd113c6ada353055ef7eb94f55abe`.
- Fresh input: `tmp/constriction-source-fresh-input-v1-20260918/manifest.json`,
  SHA256 `aba04d2ef3e613f7b48b8de3bf50df3295e3c516febd0e4392ec7789029cd07a`.
- Full-map probes: `tmp/constriction-full-map-union-v2-20260918/probes.json`,
  SHA256 `fa7fc367a00447335b86fe4ddda7c29dd44243fc0cdd0653df378927d908c2a9`.

Candidate **50 s/local1000** passes the full-state and artificial-bank audits.
All 86,720 artificial-bank cells are exactly dry; maximum step volume residual
is 1.0820061180361051e-8 m3. Depth maximum 4.277084 m, speed maximum 12.166877 m/s.
Volume is 3,022,676.371744462 m3; outflow 27.973981 versus inlet 45.306955 m3/s.
This is startup flow, explicitly **not settled**.

The baseline 9300, 9350, 9400 and 9450 snapshots also pass both audits.
At 9450, depth maximum 3.788434 m, speed maximum 5.353259 m/s; outflow
105.324775 versus inlet 45.306955 m3/s. Baseline is still **not settled**.
Installed 4950 water remains unchanged.

Both exact jobs were verified live after the native run:

- Baseline PID13584, startUTC `2026-09-18T12:17:39.4321093Z`, session95293,
  output `tmp/control-ablation-9000to12000s-workers8-v1-20260918`.
  Latest observed step9230/time9461.5; next9500/local10000 needs both audits.
- Candidate PID30276, startUTC `2026-09-18T13:46:11.8084132Z`, session91191,
  output `tmp/constriction-source-fresh-300s-workers4-v1-20260918`.
  Latest observed step1080/time54; next100/local2000 needs both audits.

Both use the retained solver SHA256
`458a1fcd3f2f12391012032398d29a4b2eadb792df2e9ee09b88dff263abc8e4`.
Do not restart on an observation timeout. Any subsequent performance capture
must account for **both** live jobs; the older capture helper pauses only one.

## Reference and approach review

Using the computer-use skill, both videos were reopened without login or media
download and the actual river frames inspected:

- [Qweniden bank-side footage](https://www.youtube.com/watch?v=2XTbOCNDcZQ):
  0:11 and 0:16; visible total duration **3:24** on this access.
- [John Elkins raft-level footage](https://www.youtube.com/watch?v=ZEG1kvjNI30):
  0:06, 0:26, 0:31 and 0:36; visible total duration **1:08**.

These frames show exposed angular shelves next to a navigable chute, steep
water faces with broken white crests, and separated patches of entrained white
water downstream. They do not supply calibrated XYZ or certify individual
class1 returns. Do not inherit different video-duration notes from earlier
access attempts as current evidence. Temporary tabs were closed.

The new source-coordinate approach plot preserves the unaltered aerial and
existing progress axis. At 0.25 m station spacing from8300 to8370, **72** axis
samples put candidate terrain at or above the captured flattened source stage.
The 8330 start lies in this conflict. The stage is not solved water and the
progress axis is explicitly not a surveyed navigation line. This therefore
rules out treating the old review start as automatically safe, not navigation
through the rapid itself. The aerial/LiDAR dates differ and image registration
uncertainty remains 3 m. No route or terrain was changed to remove the conflict.

The initial approach-report invocation failed on relative-path handling before
writing output; resolving the input directory fixed it. The final figure was
visually inspected. Semantic extent review, a wet upstream review start and
actual hull passage remain required together with the matching fresh state.

## Tests, evidence and next work

Final focused group: **71 PASS**, covering XYZ/connectivity query coverage,
both partitions, unchanged height-only coverage, station/frame interpolation,
source-extension invariants, original strict bed gates, physical unions,
source selection, native hashing and export identity. This is not the full
regression/release suite.

Small durable receipts and the inspected plot are in
[constriction-union-review](constriction-union-review/). Large generated probes,
FBX, local candidate packages and cook outputs remain ignored and regenerable.

Next: use this verified physical union with matching audited full-domain flow
and native water queries; qualify the upstream start and actual hull/camera
motion. Do not use collision/source passes as semantic rock classification or
joint-preview acceptance. No normal-play map update, new visual pass or new FPS
claim is made. Latest ordinary timing remains24.937420FPS/p9549.3295ms: FAIL30.
South Fork breaking/froth/performance, then Colorado, Pacuare, Futaleufu,
Chilko/Zambezi water reviews, crew, normalization, regressions and release all
remain OPEN. Nonlinear runtime stays OFF.
