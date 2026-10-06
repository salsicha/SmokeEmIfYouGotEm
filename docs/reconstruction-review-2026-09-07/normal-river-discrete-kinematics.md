# Discrete pressure/transport consistency — September 12

This turn made concrete implementation and diagnostic progress. It did not
finish or enable playable nonlinear water. The entire scene/terrain/rapid-shape,
breaking/froth, other-river/crew/release/final-commit goal remains active.
Desktop target stays 30 FPS, p95 33.333 ms, without changing quality, timestep,
solver or memory budgets. No reference playback, engine capture or FPS run.

## Identified mismatch, not a claim of a complete stability fix

The original pressure closure expanded continuous material-derivative product
rules into velocity-gradient squares and a bed Hessian. Its hydrostatic
acceleration also excluded the actual finite-volume transport/diffusion update.
Depth-weighted discrete gradient/divergence operators change with depth, and
discrete product rules do not hold identically. Therefore the solved material
acceleration need not match the acceleration actually advanced by transport.

`audit_nonlinear_kinematics.py` now measures that mismatch using the **standard
one-pole SGN** equation, actual reconstructed connectivity and actual FV mass/
momentum rates on unchanged captured states. It is not a replay or an energy
test. The two rational auxiliary pole accelerations must not each be described
as the one actual physical acceleration.

Current-arithmetic report:
`tmp/south-fork-nonlinear-kinematics-audit-v2-20260912.json`.

| Fixed input | Expanded maximum acceleration mismatch | Kinematic mismatch |
| --- | ---: | ---: |
| Captured initial state | 95.817831 m/s² | 1.050655e-6 m/s² |
| Earlier saved five-second weighted state | 214.033478 m/s² | 3.196547e-5 m/s² |

The initial expanded maximum is at (y84,x0), depth 2.150514 m, so this mismatch
is not confined to vanishing-depth cells. The unchanged 40-iteration solver
leaves a nonzero numerical residual; the new mismatch is not reported as zero.
The v1 audit remains preserved with its original arithmetic and source hashes.

## Implemented kinematic formulation

An explicit `--pressure-formulation kinematic` option now uses the actual
finite-volume mass and momentum derivatives and evaluates material identities
without a discrete spatial product-rule assumption. With D/G the paired
divergence/gradient, b = G(bed), c = u·G(u), and a = u_t + c:

- Q = (D u)² + D c - u·G(D u) - D_t u.
- C = u·G(u·b) - b·c + u·b_t.
- The pressure kinematics are q = Q - D a and bottom acceleration b·a + C.
- D_t and b_t differentiate the face weights using actual FV h_t.

For face weights h_i/(h_i+h_j), the derivative is evaluated as
`(h_t_i * weight_j - weight_i * h_t_j) / (h_i+h_j)`, avoiding a squared-depth
denominator. The reconstructed wet graph is fixed **within each rate
evaluation**; no differentiability is asserted across graph changes.

The continuum SGN equations and their variable-bed terms were checked against
the [DispersiveShallowWater.jl governing-equation documentation](https://numericalmathematics.github.io/DispersiveShallowWater.jl/stable/overview/#Serre-Green-Naghdi).
The discrete identities above are our derivation, tested by independent central
time differences. They are not a published energy-stability theorem. The
rational finite-depth extension remains experimental, not exact WGN/DtN.
The old `expanded` option stays the default control; gameplay is unchanged.

## First kinematic long replay failed; preserve it

Session 41231 / PID 40652 is **closed, failed**, not live. Report:
`tmp/south-fork-kinematic-pressure-bank-twenty-second-v1-20260912.json`.
Its pressure implementation hash is
`a51f5cb637fe3bdb5b883f19db6d2f70d597ab0f6067ed3fef9ce86fe875eeaf`.
It reaches 2.00833 s with 241 steps / zero retries, but the four-second
checkpoint retains a peak speed 3,290.722 m/s despite current speed 7.25691 m/s.
It terminates at **4.192408529 s**, 577 steps / 110 retries, on minimum-step
exhaustion. Fastest cell (y127,x6) has h = 3.54528878e-19 m and speed
31,568,013,322 m/s. Maximum depth is 4.275977 m. Hydrostatic-only energy remains
105,160.3787; that does not make the extreme shallow-cell velocity acceptable.
Terminal `.last-admissible-state.npy` SHA-256:
`e7e57a2502e5840ae08c988db4d80a6c606e61c742a34dee60294b22058df82d`.

Two accepted-time checkpoints and metadata were saved without splitting or
restarting the trajectory. New optional checkpoint callbacks receive copies;
a regression deliberately mutates the copy and proves evolution is unchanged.
All earlier centered and weighted long-replay failures remain preserved too.

## Arithmetic correction, not clipping

A separate three-cell periodic inflow stress case with depths (.2, 1e-310, .3)
and velocities (1, 0, .5) reproduced overflow while forming force/h. This input
has finite conservative fluxes; the acceleration intermediate need not fit in
floating point. The implementation now stays in sqrt(h)-normalized variables:

- Form the base normalized acceleration directly as force/sqrt(h), or
  `(FV momentum rate - u * FV mass rate)/sqrt(h) + sqrt(h) * c`.
- Factor W and its transpose into stable depth-weighted stencil coefficients,
  consistent with the previously verified GPU operator. Do not form
  normalized acceleration / sqrt(h) inside the pressure reconstruction.
- Reconstruct integrated pressure through W and depth factors directly.
- Normalize the PCG RHS to avoid dot-product overflow; evaluate the true
  residual of the returned solution with scaled norm arithmetic.
- Solve for the **pressure correction** delta, not the huge identity part of
  the transport acceleration: `A delta = -length * K base - nonlinear_rhs`,
  where `A = I + length * K`. Form K base explicitly, never `A base - base`.
  This is algebraically the same equation for base + delta; it avoids loss of
  the smaller pressure terms and a convergence norm dominated by a newly wet
  cell's identity term. It does not increase iterations or relax tolerances.

The stress case now has finite conservative rates and retains positive inflow,
mass and periodic momentum conservation. An independent derivative-form test
checks the factored W/transpose rather than merely testing the stencil against
itself. A large finite RHS test exercises the normalization. Existing small-wave,
lake, momentum, operator, thin-film and invalid-input requirements are retained.
An intermediate Boolean-mask negation typo caused 13 focused-test failures;
it was fixed, not worked around by dropping tests or changing limits.

Final focused suite session 62402: **127 passed in 30.91 s** across the same
11 unique physics/report/release test files, including the new kinematics,
checkpoint isolation, subnormal inflow and independent operator checks.

Current pressure SHA-256:
`d6011df3295206a5b8c5a1eae4a1594c7047018cd2156a712fc5bf08ceac6dae`.
Bank driver SHA-256:
`830a5a03be74e6203c2910a731eed945ab9518e0ee3dff920dc50f92334e4064`.

## Analytical evidence and live corrected replay

Before the final arithmetic refactor, report
`tmp/south-fork-kinematic-pressure-comparison-v1-20260912.json` completed.
Rational small-wave amplitudes at wavelengths 2/4/12 m were
0.98785824 / 0.99151032 / 0.99268262, with wrapped phase errors
0.00794282 / 0.00571191 / 0.00410562 cycles. All pass the existing diagnostic
criteria at 32 cells per wavelength. Short-wave stage-CFL retries are retained.
Rational-versus-SGN solitary-wave L1 differences at dx .5/.25 were
0.06824952 / 0.04639299; those are not exact-solution errors for the rational
model. Current-arithmetic v2 comparison session 54842 has now completed:
`tmp/south-fork-kinematic-pressure-comparison-v2-20260912.json`.
All three small-wave checks pass, amplitudes
0.98785824154 / 0.99151032020 / 0.99268261693 and phase errors
0.00794282319 / 0.00571190912 / 0.00410561975 cycles. Solitary-wave L1
differences are 0.06824952420 / 0.04639298926. The close match to v1 verifies
the algebraic refactor retains these resolved-wave results; it does not prove
long-bank stability. Fine rational solve still reaches 40 iterations, residual
6.34145e-9, with roundoff-scale volume/momentum changes.

Standard SGN convergence report
`tmp/south-fork-kinematic-sgn-convergence-v1-20260912.json` completed with
L1 errors 0.037100595 / 0.009545074 / 0.002355330 at dx .5/.25/.125.
Fine-grid speed error is +0.076879%; 1,279 steps and 996 stage-CFL retries,
worst pressure residual 4.66479e-6, maximum 40 iterations. This is evidence of
smooth spatial convergence, not fully converged pressure or river acceptance.
These v1 analytical reports retain their original pre-refactor hashes.

Current-arithmetic 20-second replay v2 is live as session 28187 / PID 36084,
started local 2026-09-12 22:52:43, with the same captured initial state and all
unchanged physical/numerical budgets. It saves checkpoints every 0.5 simulated
seconds. Report destination:
`tmp/south-fork-kinematic-pressure-bank-twenty-second-v2-20260912.json`.
Last observed 4.006641 s, 533 steps / 82 retries, maximum depth 4.544528 m,
current maximum speed 7.279245 m/s but peak **505.375157 m/s**, worst correction
residual 2.81943e-6. This is another unresolved transient failure, not a pass
erased by recovery. The earlier 3.501517 s checkpoint had peak 16.378013 m/s.
This is **not yet a pass**. Preserve this handle and terminal evidence; do not
restart merely because observation times out.

## Whole-river checkpoint and remaining work

Cook 96057 / PID 29104 remains live. The 3,100 s / local 22,000 checkpoint
passes BOTH state and artificial-bank audits: 5,382,400 finite cells,
maximum depth 4.187604153 m, speed 7.145899740 m/s, volume 2,934,008.701801248 m³,
driver volume error zero, maximum step residual 1.500216973e-8 m³, and all
86,720 artificial-face cells exactly dry. Inlet 45.306955 versus outlet
89.343868 m³/s means **still settling**. Runtime stays at audited 600 s;
3,200/local24,000 is next, only after its completion marker and both audits.

No Unreal source, playable mode, map, material or save was changed this turn.
The previous 67 native passes and 21.571211 FPS / p95 52.6052 ms measurement
are history, not new results. Nonlinear stability, physical breaking/froth,
conservative moving-window/mean exchange, shared rendered/contact publication,
30 FPS and all remaining full-scene requirements are still unqualified.
