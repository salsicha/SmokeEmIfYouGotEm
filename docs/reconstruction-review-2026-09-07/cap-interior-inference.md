# Local cap outlier inference rejected as a spike repair

September 18, 2026. Supporting reconstruction work only: **no normal-play scene
change, engine build, new motion capture or performance acceptance**. South
Fork remains first in the unfinished queue. These hypotheses are not installed.

## Result tied to the actual downstream view

Tested whether isolated high unclassified returns explain the retained cap's
diagnosed spikes. The default experiment changes three interior heights; an
explicit boundary-height variant changes five heights. An independent audit
binds both to the previous native/source ray report and player-view sidecar.
**All eight diagnosed cap triangles retain exactly the same XYZ in both
variants**, including the four steep roof faces and four vertical walls.
Neither hypothesis repairs the identified geometry. No speculative cook or
cosmetic-only mesh replacement was started.

The audit also checks immutable original source XYZ/classification/IDs, roof and
solid topology, boundary XY, protected vertices and per-vertex inferred authority.
Projected coverage remains 321.544940 m². Roof area above 60 degrees changes
114.812127 → 112.857567 m² (interior) or 110.933764 m² (boundary variant).
Those reductions are not acceptance and do not outweigh the unchanged targets.

## Explicit interpretation, never a captured surface

`infer_cap_interior_surface.py` uses last/only original returns as local fit
support, not as ground/rock certification. It requires at least eight neighbors
within 0.75 m, surrounding the point without a half-plane gap, and a robust
local plane. Only high residuals exceeding max(0.3 m, 3 scaled MAD) can move
downward. These are modeling priors, not measured uncertainty. No parameter
search was used to force a favorable result.

All 549 seed vertices and all non-class-1 vertices are protected. Boundary XYZ
is protected by default; explicit boundary-height inference still fixes boundary
XY. Original XYZ is retained separately. The different schema and field names
prevent the existing original-return runtime loader from silently treating
fitted heights as captured geometry. Both hypotheses require a newly derived
physical union and fresh hydraulic qualification before any use.

The closed-solid geometry checks pass, retaining 496 inferred vertical walls.
This does not establish native collision, shoreline stability or a correct
rock interpretation. The final generator's provenance wording explicitly
distinguishes the unchanged source archive from changed inferred roof heights;
v2 manifests correct that wording without changing either generated NPZ hash.

Interior NPZ SHA256:
`1fe6ae7d857886f0194d16521f79fb0a7d2d1bbb429427aa6c2df686fb75995b`.
Boundary variant NPZ SHA256:
`f278d83c56978562ec795760af7b56b733b6db49a6f121b9a96d0b343a6b776d`.
Both remain under ignored `tmp/troublemaker-inferred-*-v2-20260918` directories.
Original captured archives are unchanged.

## Registered imagery changes the next question, not the classification

![Original aerial pixels, interpreted boundary and actual source-ray hits](cap-interior-inference/registered-overlay.png)

The original July 21, 2022 NAIP pixels show green/dark texture under much of the
western interpreted extension, unlike the broad pale eastern mass. Several
downstream ray hits lie near that transition. Vegetation or shadow mixed into
the selected class-1 surface is a plausible interpretation, **not established
classification**. The LiDAR is from 2019, image pixels are about 0.425 m and
registration uncertainty is 3 m. Neither color nor this overlay can label
individual 2019 returns or establish underwater shape. Source imagery is
retained reference evidence; no new licensing or acquisition claim is made.

Next, test coherent surface/selection alternatives against the fixed rock
landmarks and dated boat-height footage, explicitly carrying registration and
occlusion uncertainty. Do not repeat local outlier fitting, blindly remove the
green region, or tune a smoothing threshold until the spikes disappear. A
justified interpreted rock envelope must feed rendered geometry, collision,
bed and fresh water fields together, then an incremental normal-play update.

## Tests, unchanged failure and live work

103 focused Python tests PASS, including immutable source/protected geometry,
inferred authority, one-sided/sparse/invalid fit rejection and exact retained
target identification. Actual source-space audits of both generated hypotheses
pass their checks but explicitly reject visual/physical acceptance.

An unrelated exact-fraction-to-float storage clipping trial was also attempted.
It reproduced the known positive sub-ULP fragment representability failure
(31 tests pass, one affine-source clipping test fails). The trial was fully
reverted; `triangle_cell_storage.py` is unchanged. Do not repeat that conversion,
discard fragments, loosen the source-face assertion or enable the broken solver.

The existing baseline cook, PID 13584, start UTC
2026-09-18T12:17:39.4321093Z, is the only live cook. Checkpoints 10050 through
10350 (local 21000 through 27000) pass BOTH full-state and artificial-bank
audits; all 86,720 artificial-bank cells remain exactly dry. They are **not
settled**. Next unaudited checkpoint is 10400/local 28000. Candidate PID 30276
previously completed at 300 s and was not restarted; do not reuse a dual-live-
cook manifest. No cook was suspended or terminated in this run.

Installed map/4950 s water remain unchanged, nonlinear runtime remains OFF,
and latest ordinary 24.937420 FPS / p95 49.3295 ms still fails the 30 FPS target.
Troublemaker remains a rapid within South Fork, not a menu scenario. Colorado,
Pacuare and Futaleufu remain queued after South Fork acceptance.

Evidence: [cap-interior-inference](cap-interior-inference/), including both
final manifests, target audits, registered overlay, focused tests and seven
pairs of checkpoint audits. Raw NPZ/cook/build outputs remain ignored.
