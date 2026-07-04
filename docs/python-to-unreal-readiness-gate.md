# Python-To-Unreal Readiness Gate

Milestone 10 generated the first Python-to-Unreal readiness gate artifacts in `physics/data/readiness/milestone_10/`.

Current decision: **approved for live custom water after target-hardware confirmation**. The Milestone 10 audit remains useful for telemetry/replay playback and historical regression, and the regenerated Milestone 16 GeoClaw-to-Unreal readiness report now approves live custom water because the full GeoClaw/C++ geometry, raft-coupling, runtime, and regression-promotion gate passes.

Production Unreal work can move from telemetry/replay playback into live custom-water integration once the accepted report set is locked and runtime profiling is repeated on target desktop, VR, and handheld hardware.

## Artifacts

Current packaged Milestone 16 GeoClaw/C++ gate artifacts from the last full-gate generation live in `physics/data/readiness/milestone_16/`:

- `geoclaw_reference_summary.json`: 20 of 20 full GeoClaw fixed-grid reference runs passed.
- `cpp_solver_summary.json`: 40 of 40 reduced and finite-volume C++ runs completed with manifests.
- `geoclaw_cpp_comparison_summary.json`: 40 of 40 GeoClaw/C++ threshold comparisons pass, so the comparison gate no longer blocks.
- `geometry_validation_summary.json`: 6 of 6 geometry families pass after Milestone 18 focused closure evidence is consumed by the aggregate gate.
- `raft_coupling_validation_summary.json`: 50 of 50 raft-coupling comparisons pass under the GeoClaw-vs-C++ water-field agreement gate.
- `runtime_profile_summary.json`: 80 of 80 promoted C++ profile repetitions pass local desktop, VR, and handheld water-solver budgets, and 40 of 40 deterministic replay groups match.
- `regression_promotion_summary.json`: 98 passing artifacts were promoted as regression fixtures or manifests in the latest packaged readiness snapshot.
- `geoclaw_to_unreal_readiness_report.json` and `.md`: final Milestone 16 decision; live custom water is approved after target-hardware confirmation.

Milestone 18 source reports are now consumed by the packaged readiness snapshot: `physics/reports/milestone18/remaining_geometry_closure.json` passes with six of six geometry families promotion-ready, the generic GeoClaw-profile catalog closes every aggregate GeoClaw/C++ comparison row through the South Fork cascading high-flow closure, and `physics/reports/milestone18/geoclaw_cpp_failure_triage_matrix.json` now passes with zero entries. `physics/reports/milestone16/geoclaw_cpp_comparisons.json` records 40 of 40 threshold comparisons passing, `physics/reports/milestone16/raft_coupling_validation.json` records 50 of 50 raft-coupling comparisons passing, and `physics/reports/milestone16/full_cpp_validation_gate.json` records a suite-level `PASS`. The packaged GeoClaw-to-Unreal readiness report is approved, with target-hardware profiling and report-set locking as next actions.

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

- Authoritative water candidate: custom C++ reduced or finite-volume shallow-water / height-field solver.
- Reference solver: GeoClaw after Milestone 14 transition; PyClaw artifacts are legacy regression data only.
- Raft/contact candidate: selected after the Chaos/Jolt shared fixture evaluation, with Chrono kept as high-fidelity reference/research and the custom reduced runtime as fallback if neither candidate passes.
- Unreal integration order: telemetry/replay playback first, Milestone 18 water-validation closure, live custom water approval, then selected raft/contact runtime coupling.
- Chrono::FSI remains an optional research path, not the baseline runtime dependency.

## Next Action

Lock the accepted Milestone 16 report set and regression fixtures before live-water Unreal integration, then repeat runtime profiling on target desktop, VR, and handheld hardware.

Milestone 18 closure results:

- Failure triage, GeoClaw/C++ comparison, geometry validation, raft coupling, runtime, regression promotion, full gate, and readiness reports now pass.
- Preserve the generic GeoClaw-profile catalog path, stitched whole-window validation outputs, and Milestone 17 analytic guardrails in every future retune.
- Keep wet/dry, bed-step, constriction, drop/ledge, tailwater, and stitched reach/drop geometry families closed in every future full-gate rerun.
- Keep flow-dependent pin/release, high-side/crew-weight gameplay, swimmer/rescue behavior, and future feature forcing as separately tuned gameplay layers over the approved water evidence.
- Continue Chaos/Jolt raft/contact/swimmer authority evaluation over the approved custom water outputs.

Regenerate the Milestone 16 GeoClaw-to-Unreal report from completed full-gate reports:

```bash
cd physics
PYTHONPATH=src python -m raftsim.examples.generate_milestone16_geoclaw_to_unreal_readiness --output-dir data/readiness/milestone_16 --report-dir reports/milestone16
```

Regenerate the legacy Milestone 10 report:

```bash
python -m raftsim.examples.generate_python_to_unreal_readiness --output-dir physics/data/readiness/milestone_10 --scratch-dir /tmp/raftsim_m10_readiness_runs --cpp-solver /path/to/raftsim_water_solver
```
