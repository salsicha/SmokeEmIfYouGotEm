# Base-vertex parallel trial: rejected

2026-09-17. The committed combined source-sampling path remains installed.
An additional parallel base-vertex trial was implemented, built and measured,
then removed because it did not reliably reduce its own stage cost. No new
terrain, water state, material, geometry, physics or visual improvement results.

## Actual-state comparison

A new instrumented ordinary South Fork run identifies base-vertex work at
2.116175 ms mean per refresh, while Cartesian publication remains the larger
11.256276 ms mean per frame. These are different nested scopes and must not be
summed. Instrumented logs are diagnostic, not frame-performance acceptance.
Record: `tmp/refresh-stage-baseline-v1-20260917.json`.

The candidate moves independent vertex writes into joined tasks. All station
and diagnostic reductions remain in original vertex order. Game-thread settings
are captured before dispatch. Two separate actual-game captures compare eight
alternating serial/parallel pairs each, including allocation and reduction cost.
Every pair preserves all 50,625 vertex outputs, normals, colors, foam, Froude,
flow/shore histories, audit outputs and accumulated totals exactly. Inputs are
restored before each trial; copies and equality checks are outside timing.

| Capture | First schedule | Serial mean ms | Parallel mean ms |
| --- | --- | ---: | ---: |
| A | Serial | 1.964374 | 1.876401 |
| A | Parallel | 1.889550 | 1.910626 |
| B | Serial | 1.876725 | 1.860125 |
| B | Parallel | 1.848825 | 1.750551 |

The parallel-first group in capture A regresses. There is no robust speedup;
do not promote this trial or continue small scheduling variants on its basis.
Both 900-frame processes exit zero without timeout; the exact cook process is
suspended and resumed successfully with unchanged CPU readings in both runs.
These audit-heavy captures are not FPS qualification or 16 distinct states.

Local comparison records and SHA256:

- `tmp/base-vertex-exact-a-v1-20260917.json`:
  `d50ca47c074adbad22c810de3c7cef25d283f3594904ef0a57b47e9db977a512`.
- `tmp/base-vertex-exact-b-v1-20260917.json`:
  `01f7dca650669001a857c98696f84d6c8f7445026b0f9cbf2e95acf526340b6c`.

The candidate patch and its small contribution header are preserved under
`tmp/base-vertex-rejected-{candidate,contribution}-v1-20260917.{patch,h}`
(candidate uses `.patch`, contribution uses `.h`). Only our trial edits were
removed. The actor source is restored to the committed implementation, not an
older whole-worktree snapshot. The restored editor build succeeds; eight native
tests pass with zero failures/warnings/not-run. The candidate's focused Python
suite passed 98 tests. No broader-suite failure was removed or waived.

The final audit-free restored-path capture averages 29.219141 FPS, mean
34.224141 ms and p95 41.7484 ms: **FAIL30**. Its slower result is retained;
no causal comparison with earlier trajectories is claimed. The capture uses
1280x720 D3D12, 300 CSV frames, fixed inclusive rows60..240 and the unchanged
33.333333 ms p95 gate. It exits zero without timeout and resumes the cook;
pre-suspend/pre-resume CPU readings differ by 0.125 seconds, not zero.
Record: `tmp/base-vertex-restored-profile-v1-20260917.json`; CSV SHA256
`13e5e73c92e7e051a7fba40349901ee14e2dbe140d21fb8c2d1ee478d7a9c91a`.
Restored native report: `tmp/base-vertex-restored-native-v1-20260917/index.json`,
SHA256 `b6400a40c7ce1efa4b6c63b615beac1b81bca17e45e66ec194a721919867a5e1`.

## Physical dependency and next work

Reading the energy controls confirms that the old donor-mass/paired-stress
research candidate remains explicitly unqualified. Its constant-velocity test
demonstrates nonzero energy change even with conservative momentum. Changing
only momentum, hiding a ledger residual, or enabling the known-broken nonlinear
path is not a solution. The newer original-source affine-front predictor still
needs spatially varying inlet, slope-junction and dispersive coupling before
native/playable integration; this pass does not claim to implement that work.

Next work should address the physical breaking/froth integration and larger
publication cost, not further tiny lookup or base-vertex scheduling variations.
South Fork and the full ordered scene, crew, normalization, regression and release
queue remain open. Troublemaker is still a rapid within South Fork, never a menu
scenario. No new reference-video, rendered-motion or visual acceptance is claimed.
