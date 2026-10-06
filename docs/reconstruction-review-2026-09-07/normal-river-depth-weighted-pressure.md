# Vanishing-depth pressure coupling — September 12

This turn made research progress toward evolving river water, not playable-scene
acceptance. It exposed a failure of the previous nonlinear pressure candidate,
kept that evidence, and tested a changed spatial discretization. No Unreal code,
shader, map, material, save, build or game capture changed. Ordinary play still
has the previous finite-depth detail model with experimental strain OFF. Its
latest measured 21.571211 FPS / p95 52.6052 ms fails the current 30 FPS target.
Terrain, geometry/contact tolerances, resolution, physics and quality gates are
unchanged. South Fork is the scenario; Troublemaker is only its rapid.

## Failure found, not hidden

The original five-second centered-interpolation replay remains live as session
2816 / PID 14124, started local 21:38:58. It has been repeatedly polled and its
CPU time increases. It has not been declared stopped or restarted because of
its duration. Its future report remains
`tmp/south-fork-nonlinear-pressure-bank-v1-20260912.json`.

A separate bounded one-second continuation from the saved one-second state
locates the problem without altering that running process. Report:
`tmp/south-fork-nonlinear-pressure-bank-second-second-v1-20260912.json`.
It completes its requested interval in 130 accepted steps and 15 retries, with
zero volume error, maximum depth 4.688619196 m and maximum speed **40.846019416
m/s**. A completed interval is not acceptance. The saved initial-state hash is
`5ef37b45210b25a8357ec5b840eb2c37d6bb9b0f6e808cc912d257348f04e4ab`.
Splitting the interval adds an explicit final remainder; this is a documented
diagnostic continuation, not a claim of bit-identical trajectory to the still-
running unsplit five-second replay.

The fastest cell is (y100,x106), bed 9.387420654 m, depth 7.051945425e-13 m,
velocity (-0.318529221,-40.844777405) m/s. Centered pressure contributes about
-3151.115116 m/s2 in y at this cell. Tiny water volumes make global energy and
residual norms insufficient to rule out severe local acceleration.

## Preconditioner trial did not solve it

Added an explicit `block` alternative to the reference's `diagonal` PCG
preconditioner. It uses each same-cell 2x2 block of the unchanged positive-
definite acceleration matrix and still permits at most 40 iterations. Dense
matrix/block tests pass, but the actual-bank result does not improve enough to
adopt it. At the saved one-second state, global relative residual is 1.6007e-5
with diagonal versus 1.6395e-5 with block. At the failing two-second state the
largest local acceleration residual remains 16.83 versus 15.66 m/s2. Default
preconditioning is still diagonal; this is retained as a rejected experiment.

Reports `tmp/south-fork-nonlinear-pressure-preconditioner-v{1,2}-20260912.json`
and `tmp/south-fork-nonlinear-pressure-preconditioner-second-second-v1-20260912.json`
preserve the earlier comparisons. The extended, hash-bound audit is
`tmp/south-fork-nonlinear-pressure-thin-bank-audit-v1-20260912.json`.

## Changed interpolation, not a cutoff or cap

New opt-in `--pressure-interpolation depth_weighted` retains the same nonlinear
SGN/rational equations, wet-face graph and 40-iteration limit, while changing
the graph's face interpolation. The default remains `centered` for comparison.

For connected neighbors i,j, face velocity is
`(h_i u_i + h_j u_j)/(h_i+h_j)` instead of `(u_i+u_j)/2`.
The pressure gradient is the negative adjoint of this divergence. On a fully
wet periodic grid, it is also the conservative divergence of the cross-weighted
face pressure `(h_j P_i + h_i P_j)/(h_i+h_j)`. Constant gradients remain zero;
pressure forces sum to zero up to roundoff. Uniform-depth linear response is
unchanged. Smooth-grid consistency still requires convergence tests.

Both fractions are computed directly, not as `1 - other`, so tiny nonzero
weights survive. There is no minimum depth, momentum/height repair, speed cap,
extra damping, global dispersion disable or lowered geometry/wetness threshold.
The weighted gradient, divergence, velocity/bottom derivatives, completed-square
operator and its diagonal/block preconditioners are changed together, retaining
the adjoint and positive-definite matrix identities.

The old centered interpolation allows a vanishing-volume cell's velocity to
enter neighboring pressure gradients at one-half weight. The new pressure force
at that same captured failing cell produces y acceleration -0.003642982 m/s2
instead of -3151.115116 m/s2, without changing its depth or velocity. The maximum
local acceleration residual across the captured domain drops from 16.83 to
0.00054748 m/s2 even though the global relative residual remains about 2e-5.
This is fixed-state evidence about a discrete thin-cell pathology, **not** proof
of physical breaking, a global energy theorem or all-bank robustness.

## Fresh actual-bank evolution

`tmp/south-fork-depth-weighted-pressure-bank-two-second-v1-20260912.json`
starts from the original difficult paired 15 s input, not the failed state's
edited values. It completes two seconds / 241 steps with zero retries, zero
volume error, maximum depth 4.666208579 m and maximum/peak speed 7.063118385 m/s.
Worst reported relative pressure residual is 2.009793274e-5 at 40 iterations.
Compare the centered continuation's 40.846 m/s; no claim of full river or
long-duration acceptance follows from this short result.

The fresh full five-second weighted candidate completes in
`tmp/south-fork-depth-weighted-pressure-bank-five-second-v1-20260912.json`.
It takes 600 steps, zero retries and zero volume error; final maximum depth
4.098216607 m and speed 6.872181208 m/s. Peak accepted speed is 13.294692183 m/s,
not just the lower final value. That transient is retained for physical review,
not declared a realistic speed or discarded as negligible water. Worst pressure
relative residual is 2.363167144e-5 at 40 iterations. Session 15029 completed.
The fixed-state final audit
`tmp/south-fork-depth-weighted-pressure-five-second-residual-v1-20260912.json`
finds maximum weighted acceleration residual 0.000150414 m/s2. Switching only
the operator back to centered at this same state gives 8,900 m/s2 maximum local
residual despite a smaller global relative residual. This reinforces why the
global norm alone is insufficient, not a claim that the new model is fully
converged everywhere at every earlier stage.

A fresh 20-second weighted replay is live as session 4864 / PID 25112, started
local 22:11:29, report
`tmp/south-fork-depth-weighted-pressure-bank-twenty-second-v1-20260912.json`.
It starts from the original input and retains the 10,000-trial diagnostic budget,
with progress every two simulated seconds. Preserve its handle and the original
centered five-second replay; do not restart either because of observation timeouts.

## Analytic and regression checks

`tmp/south-fork-depth-weighted-pressure-comparison-v1-20260912.json` retains the
rational extension's small-wave response: 2/4/12 m amplitude ratios
0.981354517/0.988019727/0.991940415 and wrapped phase errors
0.00865590/0.00619405/0.00424919 cycles, at 32 cells/wavelength. All three
diagnostic checks pass. The shortest waves require stage-CFL retries; these
diagnostics do not authorize increasing the gameplay timestep.

Against the SGN solitary-wave reference (not an exact solution of the rational
extension), relative surface L1 differences at 0.5/0.25 m are
0.0685388724/0.0466344729; peak ratios 0.993901351/1.019082709 and peak-speed
differences +2.81424%/+1.46540%. Momentum changes remain below 6.2e-15 m3/s.
This does not lower existing physical acceptance criteria or claim an exact
Whitham–GN operator.

Standard-SGN weighted convergence completes in
`tmp/south-fork-depth-weighted-sgn-convergence-v1-20260912.json`.
At 0.5/0.25/0.125 m, relative L1 errors are
0.0396702958/0.0100194365/0.00245652941 (ratios 0.253/0.245). Peak ratios are
0.985120280/1.000219298/1.000374691; peak-speed errors
+1.83022%/+0.382398%/+0.103881%. The finest case has 1,285 accepted steps,
1,008 stage-CFL retries and worst pressure residual 4.13325e-6. This supports
second-order smooth-wave consistency, not a fully converged fine-grid solve,
full nonhydrostatic energy conservation or river acceptance. Session 7638 has
completed and must not be restarted or listed as still running.

114 unique focused regression tests pass in 30.73 s. Coverage includes weighted
adjoint identities, positive-definite/dense matrix agreement, exact cell-block
preconditioning, thin depths down to 1e-50 m without a cutoff, unchanged linear
response, flat-periodic coupled momentum, emergent lake at rest, transport,
paired capture geometry, frame-budget parsing and release-candidate checks.
An earlier invocation accidentally repeated one test file (111 executions at
that intermediate state); the final 114-test command has no duplicate paths.
These are Python reference tests, not native Unreal or packaged release tests.

Current bank-driver SHA-256:
`965a865c8d10bd2a5b8b92c43fa5dc1fa912251aa9db18cb4392bf3573aa4a0b`.
Pressure module:
`a9563039bce7e3b54a35d50cd7ff9fba9b61ccb1cf4b42149695e448fc8f87b8`.
Analytic driver:
`6f41b83a6bf69ed42485e7a202111f81692e216cced91512517f00c1137af3d6`.
Fixed-state audit:
`6d9fa8fff15f33ee36dee4af275e5a27bcb6ea6ca9d64ed945928472a76ca0be`.
Each earlier report retains the hashes of the implementation actually run.

## Unfinished integration and next work

Finish the live 20-second candidate; examine crest shape, local pressure error
and longer bank evolution before GPU promotion. A physical breaking treatment,
foam creation/transport, mean/source exchange, moving-window total-state
coupling and one completed render/contact surface remain required. Forty PCG
iterations are still not demonstrated equal to the GPU cost/memory of the
existing Chebyshev implementation. No GPU budget increase is implied.

Current integration code was re-inspected: `RaftSimStatefulDetailComponent.cpp`
only supplies paired bed/surface/depth records when geometry capture is enabled.
`RaftSimDetailRemap.usf` copies relative eta/q unchanged into overlapping cells
whose NEW mean depth exceeds 0.01 m, otherwise zeroing it; it does not read the
old mean. `RaftSimDetailWaterGPU.cpp` uploads the new mean separately. Those are
the old perturbation-model contracts, not conservative total-state rebasing.
For a new total-depth mode, surviving cells must preserve `h=H_old+eta_old`
and `M=h*U_old+q_old`, then encode `eta_new=h-H_new` and
`q_new=M-h*U_new`. New-domain inflow initialization and actual total-depth wet
faces need explicit treatment. Copying the existing relative state or merely
swapping the pressure shader would change water/momentum when the mean updates.
This inspection is not an implemented or tested integration change.
Those rebasing equations are mathematical identities, NOT a recommendation to
retain relative storage in finite precision. A float32 check with H=0.1 m and
h=1e-12 m gives eta=-0.1 m and decoded H+eta=0: storing tiny total depth as a
difference loses it. A total-depth GPU mode must preserve h/M internally, and
derive render offsets at its boundary, rather than round-tripping its conserved
state through eta/q whenever the mean changes. This remains implementation work.

The hydraulic cook is live as session 96057 / PID 29104, latest observed local
19,820 / 2,991 s. Last independently audited checkpoint is 2,900 s; next is
3,000 s / local 20,000 once its completion marker exists. Runtime remains 600 s.
No new reference-video playback: the previous retry failed both browser
initialization and web retrieval. Terrain/reference, remaining rivers, crew,
normalization, release qualification and final commit all remain in scope.
