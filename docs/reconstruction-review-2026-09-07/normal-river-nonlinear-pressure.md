# Nonlinear total-depth pressure reference — September 12

Research progress, not playable-scene acceptance. The previous local-depth
linear pressure approximation produced a concentrated crest and drifted in
flat-periodic momentum. This candidate adds nonlinear acceleration and bottom
reaction terms, retaining that rejected candidate as a comparison. No Unreal
source, shader, map, material, save, build or gameplay capture changed during
this work. Latest measured ordinary play remains 21.571211 FPS / p95 52.6052 ms,
below the user's 30 FPS / 33.333 ms target. Quality and physics requirements are
unchanged. South Fork remains the scenario; Troublemaker is an internal rapid.

## Formulation and limits

`physics/scripts/total_depth_nonlinear_pressure.py` supplies two research models:

- `sgn`: the standard Serre–Green–Naghdi (SGN) closure, a single pole of length
  1/3. This is the nonlinear long-wave validation control, not a replacement for
  the requested finite-depth wave behavior.
- `rational_sgn`: the existing two continued-fraction lengths and weights,
  whose weighted first moment is 1/3. This retains the finite-depth linear
  response and leading SGN nonlinear long-wave terms. It is an experimental
  rational extension, **not the exact Whitham–Green–Naghdi or Dirichlet-to-Neumann
  model** and not a validated model of river breaking.

The reference equations and bottom terms are checked against the
[SGN equation documentation](https://numericalmathematics.github.io/DispersiveShallowWater.jl/stable/overview/#Serre-Green-Naghdi).
The solitary wave is the analytic SGN solution in equation 7.1 of
[Guermond et al.](https://people.tamu.edu/~guermond/PUBLICATIONS/GKPT_WaterWaves_2022.pdf).
That infinite-domain solution is sampled in a 96 m periodic box with small
truncated tails; it is not an exact periodic solitary-wave solution.

The material-acceleration system uses normalized unknown `y = sqrt(h) a`.
With bottom gradient `b`, define
`W y = h^(3/2) div(y/sqrt(h)) - 1.5 b dot y`.
Each pole solves the symmetric positive-definite completed-square system
`[I + l W^T W + 0.75 l b b^T] y = rhs`.
The graph gradient and divergence are negative adjoints. Its wet graph is the
same final reconstructed hydrostatic-face graph used by transport; dry faces
and external wall faces are closed. A zero depth has no inverse-depth repair.

The forcing includes squared divergence, the trace of the squared velocity
Jacobian, and velocity contracted with the bottom Hessian. Reconstructing the
depth-integrated pressure and bottom traction after the acceleration solve
avoids the old approximation's variable-depth pressure-gradient momentum drift.
On a flat, fully wet periodic domain, the pressure force sums to zero regardless
of iterative residual. This is not a claim of zero momentum change in a sloped
river: physical bottom and boundary forces remain.

The maximum is 40 preconditioned conjugate-gradient iterations per pole, with
true residuals reported. **40 PCG iterations are not established to have the
same GPU cost or memory footprint as 40 Chebyshev iterations.** No GPU port or
solver/memory budget increase is authorized by these CPU results. Increasing
residuals in difficult geometry remain a qualification problem.

The coupled reference retains total h/hu/hv, MC reconstruction, hydrostatic
balance, Rusanov transport, SSPRK2, the 1/120 s maximum step and stage-CFL checks.
No speed cap, height/film repair, smoothing or empirical breaking dissipation
was added. Existing reported energy is explicitly hydrostatic only, excluding
nonhydrostatic kinetic energy; it cannot certify full SGN energy conservation.
Source, mean-flow exchange, moving-window remap, foam and single render/contact
surface integration remain unfinished.

## Completed analytic comparisons

Reports retain source hashes, exact settings and failed/control results.

`tmp/south-fork-sgn-closure-convergence-v1-20260912.json` uses amplitude/depth
0.3, depth 1.5 m and four seconds of evolution:

| Cell size | Relative surface L1 error | Peak amplitude ratio | Peak-speed error |
| --- | --- | --- | --- |
| 0.5 m | 0.0391771681 | 0.985065342 | +1.80053% |
| 0.25 m | 0.00987177924 | 1.000171761 | +0.376434% |
| 0.125 m | 0.00241945722 | 1.000362197 | +0.104305% |

Successive error ratios are approximately 0.252 and 0.245, consistent with
second-order convergence for the standard SGN control. Momentum changes are
at roundoff (maximum absolute 3.89e-15 m3/s). The finest case uses 1,285 accepted
steps and 1,008 stage-CFL retries, and its worst 40-iteration relative residual
is 4.64e-6. Do not conceal those retries or describe the fine-grid pressure solve
as fully converged. The two coarser cases take 481 steps and no retries.

`tmp/south-fork-nonlinear-pressure-comparison-v1-20260912.json` evaluates the
rational extension against the same SGN wave as a **comparison**, not an exact
solution of that extension. At 0.5 / 0.25 m, its relative surface differences
are 0.0680731767 / 0.0464983466, peak ratios 0.993972615 / 1.019030548, and
peak-speed differences +2.80157% / +1.46327%. Momentum changes remain below
1.9e-15 m3/s. This improves the old linear candidate's 0.09636 fine-grid shape
difference, 1.07065 peak ratio and +0.01028 m3/s momentum drift; it does not prove
exact SGN convergence for the rational model.

Small-wave checks at 2 / 4 / 12 m wavelength retain amplitude ratios
0.981354517 / 0.988019727 / 0.991940415 and wrapped phase errors
0.00865590 / 0.00619405 / 0.00424919 cycles. Each uses 32 cells per wavelength
and one analytic period. Wrapped phase is not an unwrapped speed measurement;
these diagnostic resolutions do not establish production-grid fidelity.

## Actual captured river bank

Input is the same difficult paired 15 s capture:
`tmp/south-fork-paired-strain-input-v1-20260912/live_01.json`, with actual captured
bed geometry and all four hashes retained in the reports. It is simulated
geometry, not a new bathymetric survey. No input repair or easier substituted
capture is used.

The quarter-second report completes 31 steps without retries, maximum depth
3.831560114 m and zero volume error. The one-second report
`tmp/south-fork-nonlinear-pressure-bank-one-second-v1-20260912.json` completes
121 steps without retries, maximum depth 4.705289775 m, final maximum speed
6.426202492 m/s, peak accepted-state speed 6.721701229 m/s and zero volume error.
Its worst pressure relative residual grows to 1.63440698e-5 at the 40-iteration
limit. Neither short result substitutes for the five-second comparison or
establishes realistic crests.

The five-second replay was started before adding optional progress observation.
It remains running as session 2816 / Python PID 14124, started local 21:38:58,
target `tmp/south-fork-nonlinear-pressure-bank-v1-20260912.json`. A live process
and increasing CPU time are verified; no result has been inferred from its
duration. Reuse its existing handle, do not restart it because observation
times out. Subsequent replay observers report accepted-state progress without
changing the numerical result (verified bit-for-bit by a regression test).

## Verification and provenance

100 focused tests pass (25.82 s): pressure operators, nonlinear momentum and
lake-at-rest invariants, uniform-slope bottom reaction, unchanged observation,
bank transport, paired geometry, finite-depth response, performance-budget
parsing and release-candidate checks. This is not an Unreal or release test run.

Current nonlinear module SHA-256:
`6c89b1ad4126c1200086c16d768e797503b6d37a4be128d63fc87add7fcbe094`.
Current bank driver SHA-256:
`33df4b85eddc8a67f8ade68f57a0b4e6e4f2e943b47553eee2b01a9efba24e2f`.
The earlier-started full-bank and analytic reports use driver
`8b9dbba2a22f640a842ead1ff722314e5ae6742d1af4914dd21f2d8385f7bbfc`;
later differences are its explanatory header and optional observation, not the
pressure/transport equations. Keep report hashes as run-time provenance.

Fresh reference-video retry: browser-control initialization and the documented
Windows fallback both fail with `failed to write kernel assets` / OS error 3.
Web retrieval of both YouTube links returns a cache miss. Neither video was
viewed; no motion or geometry conclusion is attributed to their contents.

The independent hydraulic cook remains live (session 96057 / PID 29104).
The 2,900 s / local 18,000 checkpoint passes both finite-state/conservation and
artificial-bank audits. Outflow still exceeds inflow; this is not equilibrium.
Next is 3,000 s / local 20,000 after its completion marker exists. Runtime still
uses the previously audited 600 s state. See the
[checkpoint record](full-river-expanded-checkpoint.md).

Next: inspect the completed five-second bank, pressure conditioning and
nonlinear/breaking behavior before considering GPU work. Published local
breaking closures require their own validation; a global dispersion switch,
height cap or momentum repair is not a substitute. All playable integration,
visual reference comparison, 30 FPS qualification, other rivers, crew and final
release/commit work remains active.
