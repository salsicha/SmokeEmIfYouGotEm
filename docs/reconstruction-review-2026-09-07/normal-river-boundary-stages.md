# Boundary-aware water integration stages — September 13, 2026

CPU evolution and a GPU single trial now compose exterior finite-volume (FV)
transport with explicit face-velocity pressure. **Not enabled in normal play**:
the temporal source owner, multi-trial boundary inventory, outgoing-wave policy,
and full nonlinear/visual/performance qualification remain unfinished.

## Implemented

CPU `rate` accepts `pressure_boundary` only with explicit exterior state/bed,
nonperiodic nonlinear depth-weighted kinematic pressure and physical bed slopes.
No face trace is inferred from an arbitrary ghost-centre velocity. Missing traces
still reject exterior+dispersive composition. Boundary pressure residuals above
2e-5 or nonfinite residuals are refused. No solver iterations or tolerances relaxed.

Physical bed slopes use the actual ghost-centre elevations, including1xN/Nx1/1x1,
instead of the former closed-edge one-sided derivative. Existing closed/periodic
calls retain their prior behavior. Variable-state CPU coupling tests verify the
same-stage hydro rate, final wet graph, fixed bed slope and explicit trace.

CPU `advance` calls `boundary_at_time(elapsed_seconds, readonly_stage)` at both
SSP-RK2 stages. A rejected trial resamples its second-stage time after halving dt.
The read-only stage permits mixed reflecting-wall policies without an interior
reset. Only accepted trapezoidal FV flux contributes to cumulative water inventory.
Final, progress, accepted-step, failure and exhaustion diagnostics preserve that
ledger. Historical `volume_error_m3` remains the inventory change; for an open
system, `mass_balance_error_m3 = change + boundary_outward_volume_m3` is the
conservation residual. No state repair or concealed boundary supply is applied.

GPU `RaftSimTryTotalDepthStepGPU` has an optional stage provider returning all
three buffers: exterior state, exterior bed, and face velocity/time derivative.
It receives the actual stage and original compensated clock; on stage two it
also receives the GPU trial-info buffer containing the actual CFL-limited dt.
A future temporal provider must consume this time, not guess from proposed dt.
Partial inputs and periodic composition reject rather than silently becoming closed.

An optional per-face `BoundaryVolume` stores accepted dt times trapezoidal FV
flux, positive-axis oriented and per unit face length. Multiply by cell width
and outward signs for water/foam inventory. It is EXACTLY zero on rejection,
including invalid stage-two ghost data; zero is selected without multiplying
invalid flux by zero. Momentum also has pressure/bed volume sources, so this
ledger is not a claim of a complete momentum or energy balance.

Default closed/periodic calls add no boundary allocation or ledger dispatch.
The new provider/ledger is not yet propagated through `RaftSimAdvanceTotalDepthGPU`.
Native tests supply constant boundaries and validate the stage/clock hooks;
time-varying GPU source interpolation is not implemented or tested yet.

## Verification

- Final affected18-file CPU suite: **248 passed in35.36s**, session19392 exit0.
  Earlier244/246 runs are retained, not added to this total. New38-test module
  covers composition, geometry, stage times, rejection accounting, read-only
  interiors, reflecting sides, residual rejection and retained failure budgets.
- Build46138: succeeded in23.25s. Native D3D12 run45281 exited0:
  **77 tests passed in16.43102646s**, zero automation errors/warnings/unrun.
  Report `tmp/south-fork-boundary-stage-native-v1-20260913/index.json`.
- New native `TotalDepthBoundaryStepGPU` exercises16 uniform throughflows
  (four directions, four shapes), four invalid-boundary stage transactions,
  and missing/periodic descriptor rejection. Uniform h/momentum/foam remain
  bit-exact, actual accepted dt is.0078125, compensated time is correct, and
  each face's accepted water/foam flux is exact. Rejected state/time/flux remain
  unchanged/zero. This is not nonlinear moving-bank or long-run GPU acceptance.
- Old pressure, transport, step, advance, frame, source/contact/geometry and
  South Fork catalog/migration regressions remain covered by that native run.

## Wave experiment: a real boundary effect remains

`audit_prescribed_boundary_wave.py` compares a40m,0.5m-cell window against padded
periodic controls. It starts an identical1mm Gaussian depth pulse with linear
right-going momentum: a manufactured input, NOT an exact nonlinear travelling
wave or measured river. Reflecting y sidewalls use current-stage mirrored state;
x exterior state and normal trace are prescribed at rest.

An initial v1 experiment incorrectly held its one-row channel's SIDE ghosts at
rest too, draining the pulse before it reached the outlet. Its report is retained
as a setup failure (`tmp/south-fork-prescribed-boundary-wave-v1-20260913.json`),
not successful transmission. It motivated the stage-aware sidewall implementation
and exact zero-side-water-flux regression.

Corrected v2 controls use80m and120m padding. All four runs finish16s in1921
accepted steps, zero rejected trials. Window mass-budget error is-3.316574446e-15m3;
worst pressure residual9.356412445e-13, at most19 of40 iterations.

| Time (s) | Maximum window/control depth difference (m) | Linearized difference energy / initial pulse energy |
| --- | --- | --- |
| 4.008333 | 3.113426024e-6 | 5.075036407e-6 |
| 8 | 3.043868068e-5 | 6.082011601e-4 |
| 12.008333 | 7.071962243e-5 | 7.531754081e-3 |
| 16 | 6.068708163e-5 | 6.484440876e-3 |

Changing padding changes the reported depth-difference metric by at most
1.554312234e-15m and energy ratio by2.483256656e-14. Both controls' outer5m have
exactly zero depth perturbation. This supports a window-boundary effect, not
control wrap contamination; it is NOT a separated reflected-wave coefficient,
a nonreflecting pass, a real-rapid comparison, or evidence that the earlier
nonlinear bank surge was caused only by reflection.

Reports and SHA256:

- `tmp/south-fork-prescribed-boundary-wave-v2-20260913.json`:
  `5b3f43fc44cd9d10838fa03098568c186ce8477ecb090139887a35fd7ccf6d03`.
- `tmp/south-fork-prescribed-boundary-wave-padding120-v2-20260913.json`:
  `9f6a4ddd5f90dbac00f192b4d2d1013b27ea616ab28d2bfed0959ce6352d0b46`.

Each report records implementation hashes captured BEFORE its run. A later CPU
edit adds accepted mass budgets to failure/progress output without changing the
equations; the final CPU suite was rerun, the16s experiments were not relabelled.

## Next and preservation

Propagate the boundary provider and accepted inventory through the bounded GPU
advance/continuation transaction; implement temporal source evaluation against
actual compensated stage time and validate changing-boundary GPU states against
the CPU. Resolve and test the outgoing-wave policy, then nonlinear moving-bank
stability, normal total-state ownership, evolved-wet render/contact eligibility,
breaking/froth motion and30FPS. Do not promote merely because uniform tests pass.

Latest actual gameplay remains21.496540FPS/p9554.5967ms on the prior capture;
no new FPS/capture/reference-video claim is made. All requested terrain/rapid,
other-river, crew, normalization, release and final-commit work remains active.
South Fork stays the scenario; Troublemaker stays off-menu as a rapid.

Cook84534/PID32144 is the same verified live4000-to6000s continuation, observed
4048.5s/local970. Next4100/local2000 needs both state and bank audits.4000s is
the latest both-audited long-run checkpoint, still unsettled; playable data stays600s.
No restart or suspension occurred this turn. No material/source assets or save
changed: protected map/material/save hashes were rechecked unchanged. No commit.

Final WaterDetail DLL SHA256
`e5d40454b27c8a3c51071e126b992e1dae389a8be59fd55eb36023c64a1731d6`;
step implementation `2eccfb3a6e0d5584b60dc658b6a9303384b6645930f9948fe5b4c05ecbdbf588`;
step shader `2afcefcf339801a28f4bf32af91f362d28e0a6b32a9bda48382eb3510dabfd07`.
Final CPU bank SHA256
`58b2e90fb5b32a489e7de0d917a75dc611eb3d80a379335b78d7190003b481a3`.
