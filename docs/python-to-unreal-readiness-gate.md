# Python-To-Unreal Readiness Gate

Milestone 10 generated the first Python-to-Unreal readiness gate artifacts in `physics/data/readiness/milestone_10/`.

Current decision: **blocked for live custom water**. The Milestone 10 audit remains useful for telemetry/replay playback and historical regression, but the Milestone 16 GeoClaw-to-Unreal readiness report blocks live custom water until the custom C++ solver passes the full GeoClaw/C++ geometry and raft-coupling gate.

Production Unreal work may continue with telemetry/replay playback and non-authoritative visualization, but live water, Chrono/custom raft coupling, and runtime tuning must wait for a passing regenerated GeoClaw-based readiness report.

## Artifacts

Current Milestone 16 GeoClaw/C++ gate artifacts live in `physics/data/readiness/milestone_16/`:

- `geoclaw_reference_summary.json`: 20 of 20 full GeoClaw fixed-grid reference runs passed.
- `cpp_solver_summary.json`: 40 of 40 reduced and finite-volume C++ runs completed with manifests.
- `geoclaw_cpp_comparison_summary.json`: 4 of 40 GeoClaw/C++ threshold comparisons pass, so the comparison gate blocks.
- `geometry_validation_summary.json`: 2 of 6 geometry families pass; wet/dry, bed-step, constriction, and drop/ledge/tailwater cases still block.
- `raft_coupling_validation_summary.json`: 7 of 50 raft-coupling comparisons pass, so force, outcome, and transition agreement still block.
- `runtime_profile_summary.json`: 8 of 8 promoted C++ profile repetitions pass local desktop, VR, and handheld water-solver budgets.
- `regression_promotion_summary.json`: 11 passing artifacts were promoted as regression fixtures or manifests.
- `geoclaw_to_unreal_readiness_report.json` and `.md`: final Milestone 16 decision; live custom water is blocked.

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
- Raft/contact candidate: Project Chrono bridge over custom water/contact samples, with custom reduced raft fallback if budgets fail.
- Unreal integration order: telemetry/replay playback first, then live custom water, then Chrono/custom raft coupling.
- Chrono::FSI remains an optional research path, not the baseline runtime dependency.

## Next Action

Keep telemetry playback as the first integration target. Live water, Chrono/custom raft coupling, VR comfort, and native collision/contact should come after the replay path can inspect GeoClaw-validated physics outputs.

GeoClaw transition actions:

- Export the same readiness scenarios into GeoClaw.
- Add GeoClaw fixed-grid output to the comparison schema.
- Re-run GeoClaw-vs-C++ field/probe/raft-force comparison.
- Re-profile the C++ path with GeoClaw-tuned parameters.
- Regenerate and explicitly re-approve the readiness report.

Regenerate the Milestone 16 GeoClaw-to-Unreal report from completed full-gate reports:

```bash
cd physics
PYTHONPATH=src python -m raftsim.examples.generate_milestone16_geoclaw_to_unreal_readiness --output-dir data/readiness/milestone_16 --report-dir reports/milestone16
```

Regenerate the legacy Milestone 10 report:

```bash
python -m raftsim.examples.generate_python_to_unreal_readiness --output-dir physics/data/readiness/milestone_10 --scratch-dir /tmp/raftsim_m10_readiness_runs --cpp-solver /path/to/raftsim_water_solver
```
