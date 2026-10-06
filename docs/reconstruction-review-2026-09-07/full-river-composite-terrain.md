# Full-river composite terrain and rapid join

September 12, 2026, 06:08 UTC. Implementation progress, **not playable delivery**.
South Fork remains the scenario; Troublemaker is an embedded rapid component.
The normal FullReach map has not been migrated in this pass. Breaking waves,
convincing froth, hydraulic handoff, traversal and performance remain unfinished.

## Shared geometry

`physics/scripts/build_south_fork_composite_terrain.py` combines the original
2 m captured full-river surface with the retained registered rapid mesh. All
captured dry vertices and all original rapid arrays/topology remain unchanged.
Only the water mask receives an explicitly inferred, uncalibrated bed prior
(maximum depth 2.2 m, shore slope .35). This is not surveyed bathymetry.

The original 403,200 rapid vertices / 803,842 faces are retained byte-for-byte
in the durable data tree, not just scratch. A 3,214-vertex / 3,214-face inferred
annulus joins them to the coarse grid without smoothing source XYZ. It has
6,239.75 square metres projected area, no hole, no overlap, and one terrain
owner at each sampled position. Cartesian tiling avoids folding a wide ribbon
around the river's sharp turns. The 390 exported tiles retain all 7,982,812
coarse triangles with no simplification and original diagonals.

Canonical directory:
`physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/composite_terrain`.

Identity anchors:

- Composite manifest: `c78d6d68478f885456a3556e7c61a9fdd170b76fa0b75f3ec6d7f21ea02c3b7c`.
- Retained registered rapid: `8bdf1a586e7bd2536eaf25a982763efd9e5a558e7172fd7897b8ae0ecc8fe06b`.
- Coarse bed: `d2f860776f88f3400a63e96e332345dcfbb45bfa20e10f4330d06a5aded539c9`.
- Seam: `6e3a824e37a36bf188a3b97031a6c367349044466173e7f9fd398544eeb06bef`.

`CompositeTerrainSampler` samples the actual render triangles, not bilinear
interpolation, and refuses uncovered positions. Audit of all 403,200 original
rapid vertex heights has zero error. All 3,214 boundary vertices have zero
height gap; 6,428 seam probes have maximum error 9.438e-10 m.

## Native geometry delivery state

The new seam asset lives under
`/Game/RaftSim/Environment/SouthForkReconstruction/FullReach/SM_SouthForkTroublemakerJoin`.
Saved asset SHA256 is
`be796f33f0818ed8b51c2f8909289fdf37a31693a909aa9c543964ff7cfff75d`.
All triangles are retained in complex-as-simple collision and the Nanite
fallback. 6,428 actual engine collision probes at the full-river world
translation pass: maximum error .001546223959 cm. The test map hash is unchanged.
Report: `unreal/Saved/RaftSimValidation/south-fork-composite-seam-20260912.json`.

The initial commandlet attempt failed because StaticMeshEditorSubsystem was
unavailable; no asset was saved. Full-editor ExecutePythonScript succeeded.
Keep both logs; use the full editor for subsequent imports.

Full-river tile FBXs and their manifest are under
`unreal/SourceArt/RaftSim/SouthForkCompositeTerrain20260912/Tiles`.
`unreal/Scripts/import_south_fork_composite_tiles.py` imports, checks bounds and
triangle counts, probes native collision, saves a new asset, and checkpoints
its SHA256 before continuing. Verified assets are rehashed on resume and
skipped; unverified existing assets are never overwritten. No map is saved.

The first importer, PID9372, was deliberately stopped after 52 verified assets
when disk headroom became low. There were no unreported asset files. The
importer now pauses safely before a new asset if free space is below 4 GiB.
At 06:07 UTC it was relaunched with
`south-fork-composite-tiles-resume-20260912.log`; inspect the live report and
process before any restart. Report:
`unreal/Saved/RaftSimValidation/south-fork-composite-tiles-20260912.json`.
At 06:09 UTC PID23460 is live with 64/390 verified assets, no pause reason,
and maximum tile collision error .000996908 cm. At 06:10 UTC free disk space
is 5,206,159,360 bytes. Normal FullReach map SHA256 remains
`e77da92b73bf0a2c566fe69ee8a0ef7115d26182bb2f91648582aa1197ce13a0`.
Neither a partial import nor completed tile import establishes map integration.
The shared material's old rapid world frame also still needs correction.

## Matched join flow

`cook_south_fork_composite_join.py` cooks a 461 x 321, 1 m rigid Cartesian
window crossing both terrain joins, using this same triangle sampler. Ownership:
46,418 coarse cells, 96,787 rapid cells and 4,776 seam cells. The first wider
window preflight was rejected because the real river crossed its side wall.
The selected window has source coverage, dry side walls and real wet inlet
and outlet; no gate was weakened to accept it.

600 s / 6,000 steps completed in 382.61 s wall time using HLL/MUSCL2,
CFL .2, Manning .035 and Q45.3069545472 cubic metres/s. No initial-mass
preservation or fixture calibration is used. All 13 saved frames pass existing
finite/depth/speed sanity. Nine longitudinal sections including both joins
pass the settled-flow screen: maximum relative discharge error 3.1017% (<5%).
The last three storage rates are -.3166, -.1797 and -.0973 cubic metres/s;
the crux stage change is below .01 m. Initial open-flow volume drift is not
misrepresented as a conservation result.

The unchanged conservative face/microstep audit passes separately: net boundary
flux -.0767078812 versus measured volume derivative -.0767031452 cubic metres/s,
error approximately 4.736e-6 (<.001). North/south flux is zero. Evidence:
`tmp/south-fork-composite-join-cook-20260912/flow_review.json` and
`conservation_review.json`. Final frame SHA256:
`57eea657757d98382aed70e430812cfa5d27f00992a04090173d1e45f89e43ed`.

`export_south_fork_composite_join.py` rechecks all frames, hashes and exact
source-bed samples, then stages the fields in `full_reach/rapid_join_flow`.
Its manifest SHA256 is
`657d7e5db8d25f83b4020eeeb36d05da3a6c7b00bb85176af598f8aa2bc4b008`.
Its rigid local hydraulic coordinates are translated into the full river's
world frame and explicitly linked to the distinct full-river progress map.
These fields are not yet selected by the playable scenario. Acceptance and
normal-map-integrated flags remain false.

## Verification and storage

Five pure geometry tests and four new delivery/source-identity tests pass
(`test_south_fork_composite_terrain.py`, `test_south_fork_composite_delivery.py`).
The latter rehash all 390 source packets and FBXs, check full-river placement,
retained inference labels, field identity and distinct progress coordinates.

To recover disk headroom without losing evidence, transparent NTFS compression
was applied only to two terminal generated diagnostic folders. Every file's
path, byte length and SHA256 was checked before and after: 347 bank-spike
files plus 679 survey-hydraulic files, all unchanged, zero deletions. Reports:
`tmp/south-fork-evidence-compression-20260912.json` and
`tmp/south-fork-hydraulics-evidence-compression-20260912.json`.
Final observed headroom before restarting Unreal was 5,445,865,472 bytes.
This was not a broad repository cleanup or a source-data rewrite.

## Next playable implementation

Finish/verify the tile import, fix the material world frame, and place the
coarse terrain, exact rapid and seam consistently. Separate full-river progress
from local hydraulic-window coordinates; RunManager currently obtains its
station from the active water map and cannot safely treat local rapid station
zero as global station zero. Implement compatible regional flow and handoff.
Migrate the normal map, starts, sections and finish together from the incorrect
legacy extension to the 33.334 km geographic contract. Then inspect actual
normal-game motion, collision, traversal and cost. Do not expose Troublemaker
as a menu entry or rename a bounded rapid fixture as a whole South Fork run.

The previous guidance repeat (5.001737 m error) and performance failures remain
open. This pass does not recertify them or claim new visible water realism.
