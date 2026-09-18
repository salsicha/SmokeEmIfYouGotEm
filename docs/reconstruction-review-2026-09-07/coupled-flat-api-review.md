# Coupled flat-periodic research API

September 18, 2026. Commit `c19c2bcae` connects the already-derived full
two-dimensional metric-transport stage to the flat-periodic research entry
points. This is not a new derivation, native integration or visible water fix.
The nonlinear runtime remains OFF.

## What changed, and what did not

`stress_stage` and `stress_stage_physical` now default to `metric-transport`.
The old `donor-stress` and `paired-base` formulas remain explicitly selectable
negative controls. Their historical energy-work audit scripts explicitly select
the donor formulation, so a default change does not rewrite those experiments.

The physical/canonical bridge differentiates the existing inverse metric,
including both depth-normalization derivatives and both inverse-pole derivatives.
An independent forward coordinate derivative verifies the supplied state and
rate. It does not project, reset or rescale physical momentum or energy.
Both poles, the reconstructed pressure operator, 40-CG budget, 2e-5 solve gate
and 1e-10 conservation gates remain unchanged. The default keeps the original
patch preconditioner. Constant-velocity and original seeded fixtures are unchanged.

The four donor and eight paired-stress energy requirements now exercise this
corrected default on the SAME original states. The old formula failures remain
asserted as negative controls, including source-state hash equality for paired
profiles. Passing the new default does not qualify the failed old formulas.
It also does not resolve changing support, variable terrain, interacting fans,
open boundaries, finite-step behavior or playable breaking water.

## Independent checks

The initial focused run passes 44 tests. Seven new inverse-coordinate controls
include independent finite differences and forward round trips on horizontal
and nonhorizontal beds, both axes and genuinely two-dimensional arrays; the
coordinate identity on nonhorizontal beds does not enable that terrain in the
flat-periodic stage.

The broader directly related run has 70 passes and four failures in
`test_physical_rate_coordinate_accuracy.py` with the block preconditioner.
Loading the HEAD-before-commit module directly from Git, without modifying
working files, reproduces all four errors exactly:
3.759891287202777e-10, 2.9071478557796127e-10,
1.9769019754534156e-9 and 3.8196594498440817e-10.
Those older failures are not waived and remain outside the passing claim.
Reports: `tmp/coupled-default-commit-check-20260918.xml` and
`tmp/coupled-default-head-baseline-20260918.xml`.

The source-locked audit of all eight original profiles (seeds 2200/2202/2204/
2206 at 64 and 128) passes mass, momentum, local flux and energy gates.
Maximum absolute energy rate is 3.552713678800501e-15; maximum local flux
error is 1.0125233984581428e-13. All gameplay/full-physics acceptance flags
remain false. Report `tmp/coupled-default-original-profiles-v1-20260918.json`,
SHA256 `95d18ec73313a889306b24af5a169fcc8e942d90950899506ddc6057ba4d731c`.

The retained 67-module physical suite plus the new inverse-coordinate module
finishes with **870 passes and one unchanged failure**, 871 tests in 384.34 s.
The remaining exact storage/face representation assertion differs by
1.77635684e-15 and remains enforced without a tolerance. No fragment deletion,
vertex snapping or rounding workaround was introduced. The existing JUnit
metadata warning also remains. Report:
`tmp/coupled-default-full-suite-v1-20260918.xml`.
SHA256 `11a0b1c5baec6f000c056b3453241a29bcc0ba6da0805d38f1b7e8ee770e8ef7`.
This selected suite does not contain the four block-preconditioner tests above;
one failure here does NOT mean only one project regression remains.

## Hydraulic checks and runtime follow-up

The complete 7800/local2000 and 7850/local3000 snapshots pass both independent
state and exterior-bank audits. Each contains 5,382,400 cells and all 86,720
artificial-bank face cells are exactly dry. The 7850 snapshot has maximum depth
3.810883875603592 m, maximum speed 5.3501029499036505 m/s and maximum step mass
residual 1.3469852344627498e-8 m3. Its outflow is 103.6544297162659 m3/s against
45.30695454719997 m3/s inflow, so it is NOT settled. Installed 4950 water stays.
Reports: `tmp/control-ablation-{7800,7850}s-{state,banks}-v1-20260918.json`.
The 7850 depth SHA256 is
`d624d2b5b7ddbf2f801a8a172e2c86be463c1c3c93652d9b1589ece037a96cc3`.

The latest published timing evidence points to approximately 9.5 ms of native
stepping in the selection-only frame cohort. The standalone worker-limit API
already exists, but the game still uses its default four execution lanes.
A nonshipping startup override is being built for same-build four/eight-lane
comparisons. It configures the pool once, before solver construction, and rejects
invalid values; it never resizes an in-flight pool or changes the timestep.
Native domain tests pass independently at both four and eight lanes, including
partition/state/flux, rounding-mode, wet/dry and checkpoint controls. This is
not evidence that eight lanes is faster while rendering a game.

The archive rebuild succeeds (SHA256
`ae75e631be712a1dee7de53f2ca4b3508d406a1becf4346553806485c221b2a3`).
The dependent editor rebuild is still running as session85099 with log
`tmp/solver-lanes-editor-build-v1-20260918.log`. The new water module compiles;
whole-build/native option-test/performance completion remains unproven.
Default gameplay is unchanged. Do not promote eight lanes without actual
game measurements or call this pending comparison a visual improvement.
