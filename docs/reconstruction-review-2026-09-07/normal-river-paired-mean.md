# Paired bed/mean capture and difficult-bank control - September 12

Previous goal turn: progress (exact indexed crest implementation, native/game
checks, CSV-reader correction and2700 hydraulic audit). The entire remaining
goal stays active; neither that optimization nor these controls finish water.

## Captured geometry, not an invented flat bed

`SampleWaterFieldAtRiverCoordinates` already returns bed, mean surface, depth
and wetness from the live hydraulic sample. Explicit detail snapshots now retain
these values BEFORE the existing1cm wet/depth mask, resampling on the SAME
65-to-128 grid as the uploaded flow (and the same optional finer-grid resampling).
Both heights use the river vertical datum. This is captured simulation geometry,
with the existing reconstruction's measured/inferred provenance, NOT a new
bathymetric measurement or a claim that submerged geometry is surveyed.

Snapshot v2 adds `.mean_geometry.f32` with channels bed_m, sampled_surface_m,
unmasked_depth_m, wet_fraction, and records the mean sample time. The geometry
and flow are copied together into the same render command before the state
advance/readback; geometry is not resampled at later readback completion.
The reader hashes all three input arrays, checks exact sizes/channel/datum/time
metadata and still accepts old v1 snapshots. Ordinary play allocates no geometry
record and requests no extra GPU readback; this does not enable a new solver.

Initial build75848 failed on moving a const lambda capture. Corrected to an
explicit immutable copy; build35887 succeeded14.29s. The in-place edit failed,
so apply_patch moved the component to a scoped temporary sibling and back; no
ACL change or temporary source remains.56 focused Python tests pass, including
6 paired-reader and3 total-depth-control tests. The first lake test exposed a
final floating-point time remainder; that remainder is now integrated, not
dropped, while a CFL-imposed sub1e-9s step still fails.

## Actual difficult state, not an easier replacement

Ordinary capture81587 completes with8PNGs and3 paired v2 snapshots under
`tmp/south-fork-paired-mean-input-v1-20260912/`.007 inspected: existing rounded
crests/merged froth remain unfinished. Contact sequence108,2,021 wet points/959
detail-affected, support error4.764820244e-5cm; paired GPU4,226queries maxRGBA
5.960464478e-8 passes. Both frozen-mean and total-depth controls complete5s from
this ordinary15s state. It therefore does NOT discriminate the old failure.
Reports `tmp/south-fork-total-depth-bank-v1-20260912.json` and
`tmp/south-fork-paired-frozen-bank-v1-20260912.json` preserve that result.

Explicit opt-in strain trial30277 then reproduces the difficult state, without
changing normal defaults. Its10/15/20s max|eta| is0.216195/0.316829/2.491167m;
20s has4 nonpositive total-depth cells, minimum-0.203516662m. The trial remains
REJECTED. Paired inputs and hash-bound analysis:
`tmp/south-fork-paired-strain-input-v1-20260912/` and
`tmp/south-fork-paired-strain-input-audit-v1-20260912.json`.

Both following controls start from its SAME still-admissible15s state:

| Model | Requested / completed | Depth/mass result |
| --- | --- | --- |
| Frozen-mean nonlinear/dispersive hybrid | 5s / FAIL at1.197982951s | dt8.270624685e-10s; min h7.441058057e-7m; max speed1385.83m/s |
| Total-depth hydrostatic control | 5s /5s,600steps,0 retries | min h0; max h3.643887352m; max speed5.990488850m/s; measured volume error0m3 |

Failure cell(x49,y96), origin(-5466,3570.5)m, cell size.5m, maps to
(-5441.5,3618.5)m: the SAME geographic bank location as the prior failed
v1 state(x61,y80), origin(-5472,3578.5)m. No old state was paired with newly
invented geometry. The new15s state/flow/geometry were captured together.
Its mean sample time14.983048368s precedes snapshot15.059942771s.
Max sampled surface-minus-bed-minus-depth residual1.525878906e-5m; max masked
flow-depth difference0.009961173m documents the original1cm masking operation.

Reports `tmp/south-fork-paired-frozen-strain-bank-v1-20260912.json` and
`tmp/south-fork-total-depth-strain-bank-v1-20260912.json` retain hashes and final
or failed states. The already-invalid20s input is explicitly REJECTED by the
total-depth control, not repaired; see `tmp/south-fork-total-depth-invalid-input-v1-20260912.json`.

## What the control proves and does not prove

`total_depth_bank_replay.py` evolves h,hu,hv with bed-aware hydrostatic face
reconstruction, Rusanov flux and SSP-RK2. It uses actual captured bed and initial
total momentum h*U+q. Face depth reconstruction does not clamp conserved cell
heights. Its reflecting-box boundaries conserve mass. The formulation follows
[Audusse et al., equations2.9-2.16](https://publications.imp.fu-berlin.de/478/1/file_2004_siam.pdf),
also used by the existing C++ hydraulic solver's face treatment.

This is first-order in space and omits dispersion, forcing, damping, foam and
moving-domain/mean updates. It is NOT an acceptable lower-quality production
substitute. The two-cell counterexample isolates the old flux issue; the actual
river comparison changes multiple model terms and does not assign all of the
improvement to a single term. It establishes a useful admissibility control for
the SAME failing bank, not realistic breaking, calibrated momentum, or release
performance. Next work must retain high-order wave accuracy and finite-depth
behavior while coupling evolving total depth, bed pressure, mean changes,
source-driven crests, moving-window state and the shared rendered/contact field.

Final native27986 passes65/65,0warnings/failures/unrun, with strain OFF:
`unreal/Saved/RaftSimValidation/south-fork-paired-mean-regressions-v1-20260912/index.json`.
Current Raft DLL ebd2936315c832530d1ebb32a25ee77b78f07ce3a0600c7eb893aa2ae5c1b3f6;
Water48f9caf9..., Detail615b55aa..., mainbdf4bcba... unchanged. No fresh FPS
qualification: the last measured prior build is21.571211FPS/p9552.6052ms, FAIL30.
No new reference-video playback. Cook29104 live at local15060/time2753s;
2700 remains last both audited,2800/local16000 next, runtime600s unchanged.
All terrain/boulder/collision, other rivers in order, crew, normalization,
release and final-commit requirements remain active.
