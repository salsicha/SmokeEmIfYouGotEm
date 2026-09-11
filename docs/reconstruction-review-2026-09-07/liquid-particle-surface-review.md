# Particle-derived surface versus solver-cell shelves — September 9, 2026

South Fork remains incomplete. These are isolated real-engine candidates, not
a promotion to the playable river or proof of photorealism.

## Quadratic transfer result

The opt-in `RaftSimLiquidQuadraticTransfer` uses matching quadratic B-spline
P2G/G2P and the APIC moment C = B D^-1, D = diag(h²/4). The existing collocated
pressure solver is unchanged; this is not a MAC-grid implementation. Complete
interior-support tests cover partition, first/second moments, affine fields,
linear/angular transfer momentum, and continuity across former tent-cell edges.
They do not prove conservation at clipped boundaries or river mass balance.

`liquid-quadratic-transfer-motion/affine_audit.json` verifies the actual compiled
P2G/G2P markers, captured sampling coordinates and GPU affine state against an
independent quadratic reconstruction: maximum error 0.000003260 /s against the
unchanged 0.001 /s tolerance. All 714 simulation dispatches/clock increments
are covered; GPU validation reports no engine errors. The engine regression
report `engine-liquid-quadratic-transfer/index.json` has 16 successes, no test
warnings or failures. That suite predates the particle-only source selection
below; the subsequent actual capture exercises that change.

Small corrugations reduce, but large regular shelves become conspicuous.
Reverse-flow fraction in the selected pool is only 0.00436 versus 0.05514 in
the preceding tent-transfer capture. These are one-time wet-cell statistics,
not evidence of a realistic returning surface roller. Do not accept the
quadratic candidate merely for being smoother.

## Identified exposed-surface error

The render-only occupancy floor takes max(particle density, interpolated binary
solver-fluid core). Although the core is eroded by one solver cell, it still
creates an exposed, grid-aligned surface when particle density is lower.
The prior synthetic enclosed-hole test did not cover this condition.

The actual quadratic capture's before/after scalar analysis finds 14,927 common
columns; 13,212 rise over 1 cm, 9,079 over 10 cm. Median rise is 13.97 cm and
maximum 1.318 m. Original density has zero top crossings on solver-cell faces;
the filled field has 7,687. The previous tent candidate also has the error:
1,968 columns rise over 10 cm and 1,517 become face-aligned. See the respective
`occupancy_surface_attribution.json` files. These are same-state scalar
comparisons, not image guesses or a claim that all ripples share one cause.

## Correction and actual motion

`RaftSimLiquidParticleSurfaceOnly` selects the original live particle scalar
for redistancing. The binary floor remains computed/read back as a diagnostic
control but is **not applied**. The single visible surface and secondary cache
use that selection. Boundary/flow data remain available to foam. Neither
primary simulation, captured terrain nor hydraulic source data is changed by
this flag. No invented fill geometry or second water plane is introduced.

`liquid-particle-surface-motion` is a new 12 s RHI-validated capture with the
quadratic transfer, continuous sparse kernels and muted-green optics. Runtime
assertions verify the requested source selection. The occupancy audit verifies
zero sign mismatches between raw particle scalar and the actual displayed SDF,
while independently checking the unused floor as a control. Only four actual
rendered top crossings coincide with solver faces, versus 7,735 in this same
capture's unused floor. The broad shelves are absent in inspected frames
000/015/029, but rounded, finely rippled water and rectangular fixture edges
remain. Interior air pockets formerly hidden by the floor are not claimed fixed.

All 714 dispatches and positive GPU clock increments are covered. Live particle
position error is 0.000001488 m; all 30 motion frames differ. Active/paused foam
transport passes unchanged tolerances. Final sampled spray inside water is
0 / 24,962; all 13,371 bubbles are inside. Foam absolute interface-distance p95
is 0.936 cm, maximum 1.120 cm. Sampled secondary terrain/domain contact is clear;
this is not exhaustive collision-trajectory or visual secondary acceptance.

## Performance and remaining work

`liquid-particle-surface-benchmark` verifies 480 uninterrupted editor-fixture
intervals: mean 25.125 ms, p95 27.247 ms, maximum 29.206 ms. Reconstruction GPU
mean is 5.164 ms (density 4.363, distance 0.582, copy/foam 0.218). This is one
run, not an isolated attribution of improvement to either change, not packaged
FPS, and not whole-scene performance acceptance. The unused occupancy-control
cost is still included. No need to repeat long stability runs while the primary
physical shape remains unaccepted.

Next: primary particle distribution/volume and source/outlet/bed consistency,
then physical crest/returning roller behavior and continuous playable integration.
The submerged bed remains an uncalibrated prior, not surveyed bathymetry; the
source discharge is numerical, not a measurement. Do not repair remaining
holes or crests by reinstating the categorical surface floor. No production
asset promotion or commit. The full multi-river/crew/release queue stays active.

Final numerical suite: 173 tests pass. The new shelf regression initially used
a clipped profile whose sampled crossing was 7.214 rather than its intended
7.3; reducing its slope keeps both bracket samples linear. The corrected test
proves the original crossing at 7.3 and the floor-created crossing at 10.0,
without relaxing its assertions. Scoped whitespace/diff checks pass.
