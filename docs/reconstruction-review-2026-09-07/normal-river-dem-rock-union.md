# Source-backed DEM rock candidate and shared hydraulic union

September 15, 2026. Candidate work, **not playable or visual acceptance**.
Troublemaker remains a rapid within South Fork; no menu or scenario was added.

## Source reconstruction

The preceding source-ray investigation attributed the broad foreground face
to retained DEM ground (authority 1), not the earlier inferred flank patch.
The original NAIP and local returns support an exposed-rock interpretation
outside the old water-only selection. Classification 1 is still unclassified,
not certified rock. The search polygon, return-selection rule, triangulation
and vertical sides are interpretations; they are not measured bathymetry or
a surveyed rock outline. Registration uncertainty remains 3 m.

`build_troublemaker_dem_rock_cap.py` retains exact original return XYZ and
indices. One-point-per-bin selection had created six holes despite original
returns inside them. Bounded refinement inserts additional ORIGINAL returns
from supported bins; it neither synthesizes vertices nor enlarges the 1 m
triangle-edge bound. The resulting roof has 549 original vertices and 1,021
faces. Fifty additional original points close the artificial sampling holes.
The roof covers 115.922036343112 square metres. All selected points remain
class 1, with heights 0.3117321406–3.4964984515 m above the retained parent.
There are no classified ground returns inside the cap: absence is not proof.

The closed solid has 1,098 vertices / 2,192 triangles, including 150 explicitly
inferred vertical side triangles. Its bottom lies 1 m below the minimum of the
ENTIRE retained parent terrain, not at a newly invented exposed riverbed.
Closed-edge orientation and volume are checked. Candidate volume is
871.8846673423865 m³; it is a solid volume, not displaced-water measurement.

Candidate: `tmp/troublemaker-dem-rock-cap-v4-20260915/manifest.json`.
NPZ SHA256 `4d55ef0243fdef836121b2eb38ab1446a41214927d7d207097fd32d8a4dfe67a`.
Parent SHA256 `8bdf1a586e7bd2536eaf25a982763efd9e5a558e7172fd7897b8ae0ecc8fe06b`.
Original returns SHA256 `7f0a5d903a3914c830916390820cbf99260d7cb2f2cf667c57f2a1faa1c47cfe`.

## Native import and unresolved tangent-ray gate

Background Blender exports the undeformed solid. FBX SHA256
`64cc871db66d9d9f00d572dbb36923a61244ff423436848f9aaddf0aa16d2f8b`.
Transient Unreal import uses full Nanite fallback, identical complex collision,
explicit origin/rotation and the retained terrain's Y-reflected actor frame.
No assets or levels are saved. Earlier v1 stops at the first missed probe;
v2 records all results and verifies the actor transform explicitly.

v2: 1,718 / 1,720 hits. All 1,021 roof-centroid and 150 side-centroid probes
hit. Two vertical rays through extremal ORIGINAL roof vertices miss.
Reproducing the mesh's float32 rounding makes those same source XYs lie just
outside its footprint; the original double-precision roof supports both.
Maximum original-vertex quantization is 0.0001299213212 cm.
This explains a numerical tangency issue; it does not erase the failed probes.

v3 RETAINS all earlier rays and adds one interior-cone ray through EACH exact
original vertex. All 549 new probes hit; total 2,267 / 2,269. Maximum native
3D source-point error is 0.0325033774 cm, below the UNCHANGED 0.1 cm limit.
The two original vertical misses remain in `failures`; `collision_verified`
remains FALSE. There is no full-river union/contact acceptance yet.

Reports: `unreal/Saved/RaftSimValidation/dem-rock-cap-collision-v{2,3}-20260915.json`.
Original logs and v1/v2/v3 evidence are retained, not overwritten.

## Shared full-river hydraulic geometry

`SourceRockUnion` validates every dependency hash, the original XYZ and class,
coordinate frame, buried closure and equality of the hydraulic roof and closed
collision solid. It takes the maximum of retained terrain and the supported
roof. Unsupported cap XY retains the original bed; it never fills water or
rewrites captured source data. Composite terrain owner 5 identifies this
candidate solid, NOT a measurement-authority class. Default sampling without
the explicit candidate is unchanged.

`prepare_south_fork_rock_union_geometry.py` checks all 836 original cores /
5,350,400 cells against original source packets. The existing physical domain
and all four inlet/outlet faces are retained. A fresh exterior-mask audit finds
no undeclared captured-wet exterior faces. Captured masks and stages remain
identical. Exactly 118 bed samples change: nine in core_0629, 109 in core_0631.
Raises range from 0.4271187431 to 3.4719951649 m. Other cells and dependencies
are retained. This is inferred physical geometry above original ground, not
an edit relabelled as a new measurement.

Geometry: `tmp/south-fork-rock-union-geometry-v2-20260915/manifest.json`, SHA256
`09b484b10c01c50c4d03fcc28c3f215c9bb7051ed64567ab81093837140da726`.
Actual `CompositeTerrainSampler` queries match all 12,800 cells and owner codes
in the two changed cores EXACTLY (maximum height difference zero).
Report: `tmp/south-fork-rock-union-shared-sampler-v1-20260915.json`.

The v1 geometry export lacked the expanded domain's previously unverified
exterior metadata; flow preparation refused it. v2 independently checks all
exterior captured masks and supplies the missing evidence. The gate was not
defaulted to success or removed. v1 is retained.

## Fresh cook, not state clipping

The prior runtime atlas has positive water in 109 affected cells, totaling
10.24166031 m³. Its state cannot simply be retained/clipped under a visual prop.
The candidate instead uses a fresh captured-stage/conveyance initialization
over the complete existing domain. This initialization is inferred and needs
settling; it is not a conservative transfer of the old evolved state.

`audit_south_fork_rock_union_input.py` verifies every input hash, source-matched
bed, fresh depth, consistent eta/hu/hv/wet, original grid, all physical boundary
profiles, roughness and timestep. No restart or old clock is accepted.
Input: `tmp/south-fork-rock-union-cold-input-v1-20260915/manifest.json`, SHA256
`08759893e66b388d4cd345660eebedc6cc4e1aad96c70586743fa250693ce6e4`.
Audit PASS; 836 cores / 5,350,400 cells. Initial volume 3,022,078.8363165376 m³.
Imposed inlet discharge 45.30695454719999 m³/s, unchanged within 1e-12.

Bounded native pilot: `tmp/south-fork-rock-union-pilot-v1-20260915`, 20 steps /
1 simulated second, terminal exit 0. Independent snapshot audit PASS:
maximum depth 2.7121669179 m, speed 9.8756308441 m/s; maximum step conservation
residual 5.685569793e-9 m³. All 86,720 artificial bank-face cells exactly dry.
Neither a one-second pilot nor conservation proves settling or visual realism.

Long candidate cook launched separately after the pilot terminated:
`tmp/south-fork-rock-union-cook600s-v1-20260915`, session **45187**, PID **32276**,
start September 15 13:55:03 local. Target 12,000 × 0.05 s = 600 simulated
seconds, complete snapshots every 1,000 steps / 50 s. Executable:
`tmp/south-fork-checkpoint-solver-v1-20260912/raftsim_cartesian_cook.exe`, SHA256
`7d7c3be00a4eaefaba7fca67626ab4b6415f6d173ee9933459b06862734b135f`.
Confirmed live after step 70 / 3.5 s. Re-poll this handle / actual process;
do not restart on an observation timeout. Independently audit each completed
checkpoint's state and artificial banks. No settling claim before evidence.

## Verification and next required work

77 focused source/geometry/region/settling tests PASS; report
`tmp/south-fork-rock-union-suite-v1-20260915.xml`. All 464 protected source and
actor hashes match. No candidate asset saved. No native C++ changed this turn.
The 13 prior physical regressions and four prior presentation source-text
failures were not resolved by this work and remain open.

NEXT: observe the live cook; resolve/qualify the retained tangent-ray evidence
without loosening positional tolerance; verify the ACTUAL full-river render /
collision / hydraulic union, stage source-matched runtime packets, and review
real engine motion against footage before promotion. Runtime packet export
still needs explicit compound-source provenance rather than pretending the
changed roof is an unchanged old source packet. The vertical-flank hypothesis
also needs visual review. Do not install a visual-only rock over old water.

No playable asset, water state, menu, screenshot or FPS changed this turn.
Last normal-play result remains 24.225877 FPS / p95 47.78 ms, FAILING the
30 FPS / p95 33.333333 ms target. Broad smooth wave faces and broad froth remain
unaccepted. Full South Fork reconstruction, Colorado → Pacuare → Futaleufu,
Chilko/Zambezi/all-scene water, crew, normalization and release remain OPEN.
