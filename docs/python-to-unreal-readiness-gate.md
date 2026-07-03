# Python-To-Unreal Readiness Gate

Milestone 10 generated the first Python-to-Unreal readiness gate artifacts in `physics/data/readiness/milestone_10/`.

Current decision: **blocked for live custom water**. The Milestone 10 audit remains useful for telemetry/replay playback and historical regression, but the Milestone 16 GeoClaw-to-Unreal readiness report blocks live custom water until the custom C++ solver passes the full GeoClaw/C++ geometry and raft-coupling gate. Milestone 18 is the ordered closure pass for those failures: GeoClaw/C++ parity triage and fixes, geometry-family closure, raft-coupling retune, a distinct pin/release fixture, Milestone 17 analytic guardrails, and a full readiness re-run.

Production Unreal work may continue with telemetry/replay playback and non-authoritative visualization, but live water, selected raft/contact runtime coupling, and runtime tuning must wait for Milestone 18 closure and a passing regenerated GeoClaw-based readiness report.

## Artifacts

Current packaged Milestone 16 GeoClaw/C++ gate artifacts from the last full-gate generation live in `physics/data/readiness/milestone_16/`:

- `geoclaw_reference_summary.json`: 20 of 20 full GeoClaw fixed-grid reference runs passed.
- `cpp_solver_summary.json`: 40 of 40 reduced and finite-volume C++ runs completed with manifests.
- `geoclaw_cpp_comparison_summary.json`: 21 of 40 GeoClaw/C++ threshold comparisons pass, so the comparison gate blocks.
- `geometry_validation_summary.json`: 6 of 6 geometry families pass after Milestone 18 focused closure evidence is consumed by the aggregate gate.
- `raft_coupling_validation_summary.json`: 15 of 50 raft-coupling comparisons pass, so force, outcome, and transition agreement still block.
- `runtime_profile_summary.json`: 42 of 42 promoted C++ profile repetitions pass local desktop, VR, and handheld water-solver budgets, and 21 of 21 deterministic replay groups match.
- `regression_promotion_summary.json`: 44 passing artifacts were promoted as regression fixtures or manifests in the latest packaged readiness snapshot.
- `geoclaw_to_unreal_readiness_report.json` and `.md`: final Milestone 16 decision; live custom water is blocked.

Milestone 18 source reports are now consumed by the packaged readiness snapshot: `physics/reports/milestone18/remaining_geometry_closure.json` passes with six of six geometry families promotion-ready, `physics/reports/milestone18/uniform_channel_reduced_slope_profile_balance.json` closes the reduced uniform-channel aggregate row, `physics/reports/milestone18/dam_break_finite_volume_profile_calibration.json` and `physics/reports/milestone18/dam_break_reduced_profile_calibration.json` close both dam-break aggregate rows, `physics/reports/milestone18/bed_step_reduced_profile_calibration.json` closes the reduced bed-step aggregate row, `physics/reports/milestone18/constriction_finite_volume_profile_calibration.json` plus `physics/reports/milestone18/constriction_reduced_profile_calibration.json` close both constriction aggregate rows, `physics/reports/milestone18/drop_ledge_reduced_profile_calibration.json` closes the reduced drop/ledge aggregate row, and `physics/reports/milestone18/boulder_garden_reduced_profile_calibration.json` plus `physics/reports/milestone18/boulder_garden_finite_volume_profile_calibration.json` close both boulder-garden aggregate rows. `physics/reports/milestone16/geoclaw_cpp_comparisons.json` records 21 of 40 threshold comparisons passing, and `physics/reports/milestone16/raft_coupling_validation.json` has 15 of 50 raft-coupling comparisons passing. The refreshed `physics/reports/milestone16/full_cpp_validation_gate.json` and packaged GeoClaw-to-Unreal readiness report remain blocked by aggregate GeoClaw/C++ comparison and raft-coupling failures, not by the geometry-family gate.

Legacy Milestone 10 artifacts live in `physics/data/readiness/milestone_10/`:

- `scenario_suite.json`: seven audited legacy scenarios: flat pool, uniform channel, bed step, PyClaw-compatible procedural rapid, and South Fork American low/median/high runnable flows.
- `pyclaw_reference_summary.json`: legacy PyClaw reference run summary; all seven scenarios pass validation after exact dry cells are exported as a shallow reference shelf.
- `cpp_solver_summary.json`: custom C++ reduced solver run summary; all seven scenarios pass smoke validation.
- `dual_solver_comparison_summary.json`: flat pool and South Fork American median flow pass thresholds using shallow-cell-aware velocity/Froude comparison.
- `raft_coupling_validation.json`: 2.5D raft force coupling sampled across the readiness scenario suite.
- `adaptive_flow_validation.json`: low, median, and high runnable flow presets map monotonically into solver parameters.
- `profiling_runtime_budget_report.json`: local profiling report for raft coupling, probe export, PyClaw, and C++ smoke profiles.
- `unreal_visualization/replay.json` and `unreal_visualization/telemetry_forces.csv`: representative replay and force telemetry exports for future Unreal visualization playback.
- `unreal_corridor_package_manifest.json`: preproduction corridor handoff manifest for the South Fork American seed section.
- `python_to_unreal_readiness_report.json` and `.md`: final gate decision, risks, runtime choices, and accepted model limitations.

## Runtime Decision

- Authoritative water candidate: custom C++ reduced shallow-water / height-field solver.
- Reference solver: GeoClaw after Milestone 14 transition; PyClaw artifacts are legacy regression data only.
- Raft/contact candidate: selected after the Chaos/Jolt shared fixture evaluation, with Chrono kept as high-fidelity reference/research and the custom reduced runtime as fallback if neither candidate passes.
- Unreal integration order: telemetry/replay playback first, Milestone 18 water-validation closure, live custom water approval, then selected raft/contact runtime coupling.
- Chrono::FSI remains an optional research path, not the baseline runtime dependency.

## Next Action

Keep telemetry playback as the first integration target. Live water, selected raft/contact runtime coupling, VR comfort, and native collision/contact should come after the replay path can inspect GeoClaw-validated physics outputs and after Milestone 18 closes the blocked water-solver evidence.

Milestone 18 closure actions:

- Build the failure triage matrix from the current GeoClaw/C++ comparison, geometry, raft-coupling, and full-gate reports.
- Run Milestone 17 analytic fixtures before and after every retune batch.
- Fix GeoClaw/C++ parity failures before accepting raft-outcome tuning.
- Keep both promoted bed-step rows guarded: finite-volume bed-step uses the discontinuous-bed Roe/topography lane, and reduced bed-step uses the bounded fixture-scoped GeoClaw profile calibration with `feature_strength_scale=0`.
- Preserve both constriction aggregate closures as guardrails while reduced drop/ledge and broader aggregate comparison failures remain visible.
- Preserve both drop/ledge aggregate closures and South Fork cascading whole-window closure as guardrails while broader aggregate comparison failures remain visible.
- Preserve both boulder-garden aggregate closures as guardrails while broader rapid-feature, real-world, reduced cascading, and raft-coupling failures remain visible.
- Keep wet/dry, bed-step, constriction, drop/ledge, tailwater, and stitched reach/drop geometry families closed in every future full-gate rerun.
- Use the dedicated flow-dependent pin/release fixture report separate from shallow-shelf and boulder proxy evidence.
- Re-run raft coupling over improved C++ water fields.
- Regenerate and explicitly approve or block the readiness report after each closure batch until aggregate comparison and raft coupling pass.

Regenerate the Milestone 16 GeoClaw-to-Unreal report from completed full-gate reports:

```bash
cd physics
PYTHONPATH=src python -m raftsim.examples.generate_milestone16_geoclaw_to_unreal_readiness --output-dir data/readiness/milestone_16 --report-dir reports/milestone16
```

Regenerate the legacy Milestone 10 report:

```bash
python -m raftsim.examples.generate_python_to_unreal_readiness --output-dir physics/data/readiness/milestone_10 --scratch-dir /tmp/raftsim_m10_readiness_runs --cpp-solver /path/to/raftsim_water_solver
```
