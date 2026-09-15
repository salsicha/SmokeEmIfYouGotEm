# Source-grid curvature and pressure conditioning

This work continues the [combined source-metric rate](normal-river-source-nonlinear-curvature.md).
It does not establish finite-time wetting, open-flow or native/playable acceptance.

## The original finer-grid candidate failed

The first 64x64 profile (seed 2843, fixed 16 m domain) terminated at the original
full-stage budget gate with the default source-block/2x2 preconditioning:

- Local physical momentum-ledger error: 1.05549037981989e-8.
- Energy rate: 5.628068109331252e-7.
- Metric-time ledger error: 1.3357370765021415e-16.
- Skew ledger error: 5.195496810550537e-16.
- Net mass rate: 2.7755575615628914e-17.
- Skew energy work: -3.913536161803677e-15.

The run exited 1 before producing a comparison report. Its terminal traceback
is retained in the task record. These errors are not accepted or attributed to
continuum discretization. The much smaller component-ledger errors suggest
pressure-solve accuracy is a limiting factor; this is an inference pending
the complete paired comparison. The audit now writes a failure record before
returning exit 1, instead of losing all report output when a stage rejects.

## Independent analytic curvature check

Analytic first and second derivatives of the prescribed smooth bed provide an
independent reference for both terms of
(-1.5 h^2 div(w) + 3 h grad(b).w) Hess(b) z. Constant w isolates the latter;
variable w also exercises the divergence coefficient. Source moments and edge
curvature are not used to construct this reference.

| Flow | 8-grid RMS error | 16-grid RMS error | 32-grid RMS error | Omitted-force RMS at 32 |
| --- | --- | --- | --- | --- |
| Constant | 0.0059237270 | 0.0019112916 | 0.0005104613 | 0.0103436563 |
| Variable | 0.0069526765 | 0.0021911292 | 0.0005839618 | 0.0132289063 |

Both refine by more than 3 per doubling; the 32-grid errors are less than one
tenth of the omitted-force control. Seven curvature tests pass, recorded in
`tmp/source-curvature-analytic-v2-20260914.xml`. This discriminates this isolated
force, not the full nonlinear momentum equation or gameplay.

## Opt-in SPD reference preconditioner

`subcell_spectral_preconditioner.py` provides an inverse constant-depth periodic
reference with Fourier eigenvalues 1 (transverse) and
1/(1+beta h0^2 |k|^2) (longitudinal). Centered-difference Nyquist modes are exact
nulls. Actual pressure actions, source slope covariance, depth moments and all
physical forces still use the original source matrix. The average reference
depth is used only in preconditioning; it never replaces source bathymetry.

Selection is explicit through `WetPoolPartition.pressure_preconditioner`.
The default remains `auto`, preserving the existing local/source-block path.
The new option requires exact-source, completely wet, one-pool-per-cell grids
with both periodic boundaries. It is not enabled for the actual closed channel
or bank blocks, and does not supply an open or wet-front preconditioner.

Focused controls verify a flat-grid inverse, positive symmetry, bit-identical
physical matrix actions on identical input states, original 40-CG convergence,
and rejection of unqualified geometry. An initial matrix-identity test rebuilt
the state from already-reassembled volumes and introduced a 4.44e-16 difference;
it was corrected to compare identical original inputs, keeping exact equality.
The seven focused tests then passed in
`tmp/source-spectral-unit-v2-20260914.xml`. A further failure-report regression
verifies that the first rejected stage is recorded, stops the audit and returns
exit 1; all eight focused tests pass in `tmp/source-spectral-unit-v3-20260914.xml`.

## Finer comparison: first profile completed, second still running

The first 64x64 profile, seed 2843, completed with the selected reference
preconditioner and unchanged physical equations and gates:

- Full-model RMS versus the independent continuum bracket: 0.0003084853350.
- Omitted-curvature control RMS: 0.0005425756821.
- Full refinement from the prior 32-grid result: 3.95120; omitted control:
  2.09244. Unlike the coarse grids, this profile now discriminates the omission.
- Energy rate: -7.105427357601002e-15; local physical momentum-ledger error:
  8.326672684688674e-16; maximum solve residual: 2.1499135926516076e-15.
- Physical/canonical round-trip error: 9.71445146547012e-17.
- 12,288 curvature edges, including 4,096 same-region edges; no unresolved
  fronts in this fully wet periodic control.

This is a completed individual measurement, **not a completed audit**. Seed
2845 is still running in the same process, session 98022 / Python PID 31956.
Its output is `tmp/source-nonlinear-model-fine-spectral-v1-20260914.json`, written
only when the audit terminates and verifies its frozen implementation hashes.
Do not restart it or edit those sources before reading its terminal result.

The focused source/triangle regression suite completed with 351 passes and the
one retained geometry failure in `tmp/source-spectral-suite-v1-20260914.xml`.
The additional failure-report regression above passed afterward. The paired
stress/constant-velocity suite retains 15 passes and 12 energy failures in
`tmp/source-spectral-retained-v1-20260914.xml`. No gate is waived.

All 464 protected scene/source/capture/actor hashes were checked and remain
unchanged. No engine capture or FPS improvement is claimed. Next are completion
of this same audit, nonlinear finite-time wet/front coupling and actual open-flow
integration. Native/shared-surface, convincing water, 30 FPS, and the ordered
later-river/crew/normalization/release scope remain open.

## Scenario-menu regression

The current menu code names South Fork as the scenario and retains Troublemaker
inside its full descent. A fresh headless engine `RaftSim.M6.CareerCatalog` run
passed (one success, zero test warnings/failures). It checks that the retired
rapid ID is absent and no catalog scenario launches the bounded Troublemaker
map. This is catalog validation, not a rendered-menu or gameplay capture.
Report: `tmp/menu-career-catalog-v1-20260914/index.json`, SHA256
`66934296e7f6bf017fb1b229fcb73691bdd240610e1f041fde39d6f429d64743`.

A separate fresh `RaftSim.M6.ProgressionMigration` engine run also passed with
zero test warnings/failures. It verifies migration of a saved retired rapid
selection to South Fork and removes the retired unlock/completion IDs.
Report: `tmp/menu-progression-migration-v1-20260914/index.json`, SHA256
`efc171869be83e4c275882185066f9cf2abfe1a35e6e9f6434aef9eae674f381`.
