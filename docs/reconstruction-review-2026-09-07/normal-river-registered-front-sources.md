# Original terrain coverage beyond the water-state audit block

September 17, 2026. The prior ownership implementation made progress but left
one actual positive side ray without a source owner because it crossed the
4x4 water-state audit boundary. That boundary is not a terrain boundary.
This change resolves the terrain-source gap; it is NOT a finite-time physical
update, pressure fix, playable visual improvement or performance acceptance.

## Complete source search without moving the front

`RegisteredFrontSources` snapshots the validated registered mesh and checks
every original triangle's XY bounding box against the full side ray. Rational
ray bounds are rounded outward for this broad phase only. Exact original XYZ
and affine gradients then determine source ownership and flux. The outward
rounding does not change a front point, terrain vertex, bed or physical domain.
No guessed halo, raster sampling, interpolation, clamping or extrapolation.
The index owns its geometry epoch so caller mutations cannot stale its bounds.

The actual-source audit preserves its old block-clipped ownership as an exact
control and adds a separate registered-terrain ledger. Its source keys are
original triangle indices, NOT cell/pool identities. Both trace owners retain
their original vertex indices/coordinates and captured/inferred authority.
Terrain coverage does not establish outside-block water state or merge streams.

## Actual South Fork and regression evidence

Original block (12,8), registered terrain and 600s atlas: all 11 conditional
streams now have complete paired terrain-source ownership, including the
positive sub-float stream. The previously missing ray (donor `[8,600014]`,
receiver `[8,198093]`) belongs to original triangle `198093` on both sides,
with distinct conditional wet/dry domains. Its common volume-rate midpoint is
approximately 2.760274100e-26 m3/s. Its exact position is unchanged, including
the portion just outside the test block. This arithmetic is not additional
survey precision or proof that this conditional dry-front law can be evolved.

Seven original triangles cover the eleven rays: `196657`, `197375`, `198093`,
`199537`, `600015`, `601453`, `601454`. Six have exposed-rock authority code 3;
`199537` has inferred-flank code 5. Do not label the entire result measured.
Two receding/fan records remain unsupported. Original water is unchanged.
Every old record field, including the deliberately incomplete block-only
control, equals the preceding ownership report. All 614 source/implementation
hashes independently reverified. Exact partitions, common transfer ids/signs,
positive rate bounds and both source-provenance references are checked.
Report `tmp/south-fork-registered-front-source-v1-20260917.json`, SHA256
`b51d470118438c51994c28f477f3a3e548d4f1e32a8b365e5a0529e2b8e339ec`.

59 focused tests PASS in 4.31s, including 11 new cases: complete-face comparison
in four directions, actual source recovery beyond an artificial block, sub-float
positive ray, no extrapolation beyond terrain, exact vertices/gradients,
immutable epoch, invalid/unrepresentable input, and five crossed source pairs.
The initial two failures were invalid intermediate test-fixture constructions;
updating edge and velocity together fixes them without changing the branch gate.
JUnit `tmp/registered-front-source-focused-v2-20260917.xml`, SHA256
`0ea0d4f7b0d2931f4a8fb911ec0e48565221c3703b1c7daf007d3e605282e10a`.

Broader suite: 683 PASS / 13 FAIL, 696 tests, zero errors/skips, one existing
warning, 145.49s. Failure identities exactly match the previous suite: four
constant-velocity energy, eight nonlinear rational energy and one original
storage/face representation gate. No threshold or skip changes. JUnit
`tmp/registered-front-source-full-suite-v1-20260917.xml`, SHA256
`f7383c43eb5412184e1f97a52a824fb27b0c8f8162730f6df33a07c102e0a8b9`.

## Hydraulic continuation and remaining integration

Same cook PID17516/start UTC2026-09-17T12:52:03.0749210Z verified LIVE. Complete
4200s/local12000 passes state/conservation AND all 86,720 exactly dry artificial
bank cells. Maximum depth3.910051679m, speed5.497123927m/s, volume2,885,355.287352m3,
maximum step residual1.521822357e-8m3. Outflow97.460483563 vs inflow45.306954547m3/s:
NOT settled or promoted. Depth-array SHA256
`33594c0bb935904659f1e26b073fe364c20e23c55d69d333b1e6a178c3803a60`.
Reports `tmp/control-ablation-4200s-{state,banks}-v1-20260917.json`.
Next4250/local13000 requires its completion marker and BOTH audits; do not restart.

Next couple the now source-owned rates to original wet support and evolving
donor/receiver domains, including outside-block state, depth, physical momentum,
energy, bed/dispersive work and branch transitions. A neighboring cell containing
water does not prove the front point is wet; full-source ownership is not pool
ownership. No finite-time or energy-conservation gate is closed by signed rate
references alone. The nonlinear instability and all thirteen failures remain.

No installed runtime/material/terrain change, new engine motion/reference review
or FPS measurement. Installed gameplay DLL and material match their preceding
hashes. Last ordinary25.907729FPS/p9544.7123ms still FAIL30. South Fork terrain,
boulders, collision, hydraulic consistency, breaking and convincing froth remain
unaccepted, then Colorado -> Pacuare -> Futaleufu, Chilko/Zambezi/all-scene water,
crew, normalization, regressions and release. Troublemaker stays a rapid in South
Fork, never a scenario/menu entry. Generated evidence is already ignored.
