# Boundary-aware bounded GPU intervals — September 13

This is solver integration work, not normal-play promotion, visual acceptance,
or a performance pass. Desktop target remains30FPS, p9533.333ms, hitch66.667ms;
quality, timestep/CFL, tolerances and existing solver/memory budgets are unchanged.
Latest ordinary gameplay remains21.496540FPS/p9554.5967ms. No new video viewing.

## Implemented transaction

`RaftSimAdvanceTotalDepthGPU` now forwards the explicit stage boundary provider
through every bounded trial and retains a cumulative float4 FV boundary inventory
per face. Values are integrated flux per unit face length in positive-axis
orientation, including water and foam. Rejected trials add nothing. State,
compensated progress, summary, diagnostics and inventory must be extracted and
continued together. No host readback is required by this API.

Summary element3 records boundary mode0/1. A new open interval starts with zero
inventory; continued open intervals require both provider and the exact inventory
descriptor. Dropping both arguments is detected by the GPU mode tag. Periodic or
partial boundary descriptors fail before callbacks run. Closed intervals retain
their prior path and allocate none of these new boundary records.

Candidate cumulative inventory is validated before committing any state/time.
Nonfinite prior inventory or cumulative overflow yields fatal status2, proposed
dt0, Diagnostics[2] bit32, and exact prior state/clock/inventory. Corrupt data is
retained as failed evidence, never repaired. Integrity failure overrides even a
previously completed status. Normal terminal results remain latched.

The counter/clock pass writes one authoritative commit record; state and inventory
selection explicitly consume it. The initial implementation recomputed a decision
in the selection pass: native tests showed accepted counters but zero inventory and
no foam movement. Diagnostic-only outputs independently showed correct candidate
flux and a true decision. Explicit branches and read-only ledger dependencies
alone did not fix that behavior. The shared commit record fixes the observed
transaction failure. The precise compiler/driver/graph mechanism is not established;
do not label it a proven driver bug. All temporary diagnostic shader outputs were
removed. Failed reports remain in tmp, including v2/v3/v4 and v5–v9 probes.

Single-step integration multiplies each finite face flux by half-dt before adding
the two RK stage contributions, avoiding an unnecessary intermediate overflow.
The equation, accepted-step policy and1/120s maximum remain unchanged. Frame
resolution checks boundary mode, descriptor and finite inventory before publishing
a completed paired render/contact frame. Missing or corrupt inventory cannot
produce a valid frame. This does not yet drive normal gameplay evolution.

## Focused verification

Build67189 exits0,13.58s; focused D3D12 run59981 exits0, one automation test
containing13 cases,1.56241155s, no automation errors/warnings/unrun:
`tmp/south-fork-boundary-advance-commit-v10-20260913/index.json`.

- Split one-slot graphs and four-slot batches are bit-identical for state,
  inventory, compensated clock, counters and diagnostics, including terminal calls.
- Uniform flow, retry, first/second-stage faults, exhausted budgets and zero interval.
- Missing inventory/provider, switched boundary mode, NaN and finite cumulative
  overflow all reject correctly; corruption is also detected after completion.
- Nonuniform foam moves on acceptance and has zero measured summed foam change.
  The same perturbed state rolls back exactly when inventory validation fails.
- Accepted20ms uniform interval has west-face water inventory0.0149999987334 and
  foam0.00374999968335; residual versus compensated elapsed time remains inside
  the existing2e-8/5e-9 test bounds. Zero-accepted intervals retain exact zero.
- Valid completed frame passes; missing inventory sets interval bit8, NaN inventory
  is counted invalid. Five host descriptor cases reject without invoking callbacks.

Eight desktop CSV target/parser tests pass in0.15s. Prior248 CPU tests are historical
from the boundary-stage turn; no broad CPU rerun is claimed for this GPU-only work.
Final build19865 exits0,20.70s. Full targeted D3D12 regression87706 exits0:
78passed,0warnings,0failed,0unrun,18.90896988s. All five existing fixture files
were supplied, including prescribed pressure and exterior transport.
Report: `tmp/south-fork-boundary-advance-native-v11-20260913/index.json`.
Startup SDK/platform messages remain in its log; these are not automation warnings.
Scoped source/doc whitespace checks pass; no whole-worktree release gate is claimed.

Final hashes:

- Advance shader: `3bac75add2c49b8f36da05ef36b23bafc2a759c409aa05c08ff7bd9e3c76e060`.
- Advance C++: `84ec381a3ec1b1d86dce6411b644abf8cf05f22f546b934029874cbd22278f78`.
- WaterDetail DLL: `315970bf7e861f241a68c45d25c12d5a941c6450451d73e2ba05d0352574d7bb`.

## Remaining integration and live cook

Actual compensated-time GPU source sampling, outgoing-wave policy, nonlinear
stability, persistent game-frame/window ownership, evolved wet render/contact
eligibility and convincing breaking/froth remain unfinished. No new total-state
solver is enabled in ordinary South Fork play. Whole-water cost remains unqualified.
The outgoing-boundary pulse discrepancy from the preceding record is unresolved.

Same live cook84534/PID32144 passes both independent4100s/local2000 state and bank
audits. All5,382,400 cells finite and86,720 artificial-face cells exactly dry.
Outlet93.265958595 versus inlet45.306954547m3/s: still settling; runtime600s unchanged.
Next4200/local4000 needs both audits after its complete marker. No restart occurred.
Map, transmission-water material and save hashes match the prior protected values.
Full remaining scene/crew/release/final-commit goal stays active.
