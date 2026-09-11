# Compatible pressure projection — September 8, 2026

Status: isolated unsaved candidate, **not a completed scene or production fix**.
The full ordered reconstruction queue remains active.

## Numerical reference

`physics/scripts/liquid_compatible_projection.py` retains the collocated grid
and solves the actual masked composition `-D M G`, with cell dimensions
32.8125, 32.8125, and 33.3333 cm. M fixes the same velocity components as the
binary terrain/river boundary. Pressure is zero on nonfluid cells. This is not
a MAC solver or a cut-cell solver and makes no production performance claim.

On the retained `liquid-terrain-pressure-160/terrain_0720_grids` snapshot, the
matrix-free preconditioned conjugate-gradient reference converges in 84
iterations: fluid-cell divergence RMS 0.1585966/s becomes 1.5003e-8/s, relative
pressure residual 9.4598e-8. Fixed velocity components are unchanged. Output is
in `liquid-compatible-projection-reference/report.json`.

## Engine implementation

The `compatible-projection` transient variant includes driven native-face
boundaries, exact shared terrain contact, wet initialization and the grid halo.
It replaces divergence with constrained-velocity divergence, the pressure
matrix with the matching wide stencil, red/black dispatch with a two-cell
coloring, and only the scalar pressure gradient with its anisotropic version.
Original P2G/G2P sampling is still collocated. Existing unrelated graph branches
are preserved. New code is in `RaftSimCompatibleProjection.h`.

The actual Niagara custom HLSL has alternate scalar/vector gradients,
Jacobi/red-black pressure, and several extrapolation implementations. Integration
failures are retained rather than treated as simulation results: V4/V5 rejected
the vector-magnitude gradient; V6 hit a dynamic-input sentinel ordering assertion;
V7 failed GPU compilation because its token parser did not separate the modulo
operator from `IterationIndex`. V7's verified assistant-owned offscreen process
was stopped. No saved scene or Niagara asset was modified by these runs.

## First completed GPU candidate: V8

`liquid-terrain-compatible-projection-v8` completes 720 steps / 12 simulated
seconds in 27.35 seconds of capture wall time. This includes offscreen capture
and blocking GPU readback, **not a gameplay frame-rate measurement**.

Actual compiled GPU HLSL includes the new D, pressure, coloring and gradient.
There are 98,376 probed particles, no nonfinite positions or velocities, and no
detected bed penetration. Mean speed is 70.54 cm/s; upstream/centre/downstream
quarter mean downstream speeds are 61.00/45.89/84.15 cm/s.

The new masked-operator audit finds divergence before projection 0.20305/s,
pressure residual times dt 0.01685/s, but final velocity divergence 0.08123/s.
The predicted-versus-final discrepancy is 0.07944/s. Inspection identifies a
subsequent extrapolation stage that overwrites corrected nonfluid velocities,
including prescribed solid velocities. This is not accepted. The old nearest-
neighbor Poisson residual is not the appropriate metric for this new matrix.

The initial opacity-zero capture is nearly black. The opacity-one diagnostic
shows a pale, opaque surface with grooves; neither is realistic water. No
visual acceptance is claimed.

## Follow-up in progress

Preserve projected components used by a fluid cell's divergence stencil, and
solid velocities, through post-projection extrapolation. Continue extrapolating
outside that support for particle sampling. V9–V11 are retained installation
failures from alternate inactive extrapolation branches; no physical results.
Repeat actual GPU readback, engine regressions, long-run storage/transport, and
visual checks before considering promotion. Outgoing stage coupling, calibrated
water volume, optics, raft coupling, and real-time performance remain open.

## Completed full-update check: V12

The active named-attribute extrapolation branch now preserves solid velocities
and the component values used by adjacent fluid pressure cells. Earlier indexed
and integer-grid branches remain unchanged. Actual GPU compiled code contains
`CompatiblePreserveProjectedSupport` only in post-projection extrapolation.

At 12s, 30,736 fluid cells have pre-projection divergence RMS 0.2167685/s;
the matching pressure residual times dt is 0.0168260/s and final divergence
0.0168287/s. Predicted-versus-final discrepancy is 0.0004105/s, consistent with
the half-float velocity/divergence storage. Fixed-component error on pressure
support is at most 0.0625 cm/s. Outside that support, extrapolation can still
change constrained components; the unscoped maximum is 130.75 cm/s and is
reported separately, not hidden.

There are 103,403 exact bed probes, zero missing probes, zero nonfinite states,
and zero detected penetration. Mean speed is 61.857 cm/s; quarter downstream
means 50.326/37.389/66.704 cm/s. Capture wall time is 30.157s, not an FPS test.
The change has not established acceptable throughput/storage or realistic optics.

All eight engine liquid-fixture tests pass without warnings in 17.243s, including
the new eighth variant within the transfer test. Seventeen `test_liquid*.py`
tests pass, including negative-adjoint consistency, projected-field audit and
full 68-cell wide-stencil dispatch coverage. Saved source assets remain unchanged.

## Iteration diagnostic, not a production setting change

`liquid-compatible-projection-pressure-160` also completes 12s. With 160
diagnostic iterations the matching pressure residual times dt is 9.7893e-7/s;
actual final divergence is 0.0004206/s, versus 0.21873/s before projection.
Predicted-versus-final discrepancy is 0.0004206/s, at half-float velocity storage
precision. This differs from the earlier stock result where converged pressure
still left substantial divergence. The runs evolve different states, so this is
not a same-snapshot convergence trace. Default iterations have not been raised.

## One-minute run at default iterations

`liquid-compatible-projection-60s` completes 3,600 steps with 123,484 exact bed
probes, zero missing probes, zero nonfinite states and zero detected penetration.
Mean speed is 56.828 cm/s; upstream/centre/downstream means are
41.000/39.269/57.736 cm/s. The marker count increase is **not** a water-volume
measurement. Storage and source/exit conservation still need calibrated checks.

At 60s, pre-projection divergence is 0.23664/s and final divergence 0.017244/s,
matching the predicted residual 0.017239/s within 0.0004412/s. Pressure-support
fixed velocity error remains at most 0.0625 cm/s. Capture wall time is 87.478s,
including manual simulation and blocking diagnostics, not real-time FPS.

The opacity-one image remains excessively pale and homogeneous, with a visible
rectangular fixture boundary. No realistic-water acceptance or scene promotion.

The installation command now waits for actual GPU compilation and rejects
failed enabled-emitter shaders before installing a candidate. Disabled emitters
are excluded because they have no compiled resource. The first gate regression
caught that distinction; after correction all eight engine tests pass without
warnings in 16.403s (`engine-liquid-compatible-gpu-gate-v2`). Latest focused
Python run: 17 tests pass in 1.054s. No production assets or commits changed.
