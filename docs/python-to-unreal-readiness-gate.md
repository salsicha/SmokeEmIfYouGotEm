# Python-To-Unreal Readiness Gate

Milestone 10 generated the first Python-to-Unreal readiness gate artifacts in `physics/data/readiness/milestone_10/`.

Current decision: **approved**. The audit is complete, and production Unreal work may start with telemetry/replay playback first, followed by live custom water and then Chrono/custom raft coupling.

## Artifacts

- `scenario_suite.json`: seven audited scenarios: flat pool, uniform channel, bed step, PyClaw-compatible procedural rapid, and South Fork American low/median/high runnable flows.
- `pyclaw_reference_summary.json`: PyClaw reference run summary; all seven scenarios pass validation after exact dry cells are exported as a shallow reference shelf.
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
- Reference solver: PyClaw, using a shallow shelf for exact dry-cell reference exports until wet/dry handling is improved.
- Raft/contact candidate: Project Chrono bridge over custom water/contact samples, with custom reduced raft fallback if budgets fail.
- Unreal integration order: telemetry/replay playback first, then live custom water, then Chrono/custom raft coupling.
- Chrono::FSI remains an optional research path, not the baseline runtime dependency.

## Next Action

Create the production Unreal project and keep telemetry playback as the first integration target. Live water, Chrono/custom raft coupling, VR comfort, and native collision/contact should come after the replay path can inspect the validated physics outputs.

Regenerate the report:

```bash
python -m raftsim.examples.generate_python_to_unreal_readiness --output-dir physics/data/readiness/milestone_10 --scratch-dir /tmp/raftsim_m10_readiness_runs --cpp-solver /path/to/raftsim_water_solver
```
