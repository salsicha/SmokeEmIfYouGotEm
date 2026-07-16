# Python-To-Unreal Readiness Gate

Milestone 10 generated the first Python-to-Unreal readiness gate artifacts in `physics/data/readiness/milestone_10/`.

Current decision: **blocked for live custom water**. The v1 Milestone 16 comparison report separates 6 passing solver-parity rows from 34 reference-playback rows. The Milestone 10 audit and calibrated Milestone 16/18 artifacts remain useful for telemetry, frozen playback, and historical regression, but they do not approve the C++ solver as live Unreal water.

Production Unreal tooling and playback work may continue, but the blocked Milestone 20 report-set lock must keep live custom-water stepping disabled. Runtime budget evidence remains valid for the calibrated configurations; physical device captures are still required after solver approval.

## Artifacts

Current packaged Milestone 16 GeoClaw/C++ gate artifacts from the last full-gate generation live in `physics/data/readiness/milestone_16/`:

- `geoclaw_reference_summary.json`: 20 of 20 full GeoClaw fixed-grid reference runs passed.
- `cpp_solver_summary.json`: 40 of 40 reduced and finite-volume C++ runs completed with manifests.
- `geoclaw_cpp_comparison_summary.json`: 6 of 40 rows provide passing solver parity, 34 are reference playback, and all 40 raw calibrated threshold checks pass; solver approval is blocked.
- `geometry_validation_summary.json`: 6 of 6 geometry families pass after Milestone 18 focused closure evidence is consumed by the aggregate gate.
- `raft_coupling_validation_summary.json`: 50 of 50 raft-coupling comparisons pass under the GeoClaw-vs-C++ water-field agreement gate.
- `runtime_profile_summary.json`: 80 of 80 promoted C++ profile repetitions pass local desktop, VR, and handheld water-solver budgets, and 40 of 40 deterministic replay groups match.
- `regression_promotion_summary.json`: 98 passing artifacts were promoted as regression fixtures or manifests in the latest packaged readiness snapshot.
- `geoclaw_to_unreal_readiness_report.json` and `.md`: final Milestone 16 decision; live custom water is blocked by missing solver-parity evidence.

Milestone 20 locks the current blocked evidence set in `physics/reports/milestone20/report_set_lock.json` and `.md`. The lock hashes 27 artifacts so Unreal can detect the blocked state rather than loading an obsolete approval. Runtime and replay counts remain recorded, but they cannot override the solver-parity blocker.

Milestone 18 source reports are still consumed by the packaged readiness snapshot. They establish calibrated geometry, raft-coupling, runtime, and replay behavior, but the fixture profile catalog is now classified as reference playback. `physics/reports/milestone16/full_cpp_validation_gate.json` is therefore `BLOCKED`, and the packaged readiness report and report-set lock are blocked with it.

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
- Unreal integration order: telemetry/replay playback first, owner water-strategy decision and honest solver gate, then live custom water and raft/contact authority integration.
- Chrono::FSI remains an optional research path, not the baseline runtime dependency.

## Next Action

Use `physics/reports/milestone20/report_set_lock.json` as the machine-readable blocked manifest. Keep live custom water disabled, continue telemetry/frozen-playback tooling, and wait for the owner water-strategy decision before changing solver authority.

Milestone 18 closure results:

- Historical calibrated threshold, geometry, raft coupling, runtime, and regression reports pass; the honest solver-parity full gate and readiness report are blocked.
- Preserve stitched whole-window validation outputs and Milestone 17 analytic guardrails in every future solver path. Profile playback may remain diagnostic only.
- Keep wet/dry, bed-step, constriction, drop/ledge, tailwater, and stitched reach/drop geometry families closed in every future full-gate rerun.
- Keep flow-dependent pin/release, high-side/crew-weight gameplay, swimmer/rescue behavior, and future feature forcing as separately tuned gameplay layers over future approved water evidence.
- Continue Chaos/Jolt raft/contact/swimmer evaluation over frozen water snapshots until live water is approved.

Regenerate the Milestone 16 GeoClaw-to-Unreal report from completed full-gate reports:

```bash
cd physics
PYTHONPATH=src python -m raftsim.examples.generate_milestone16_geoclaw_to_unreal_readiness --output-dir data/readiness/milestone_16 --report-dir reports/milestone16
```

Regenerate the Milestone 20 report-set lock:

```bash
cd physics
PYTHONPATH=src python -m raftsim.examples.generate_milestone20_report_set_lock --repo-root ..
```

Regenerate the legacy Milestone 10 report:

```bash
python -m raftsim.examples.generate_python_to_unreal_readiness --output-dir physics/data/readiness/milestone_10 --scratch-dir /tmp/raftsim_m10_readiness_runs --cpp-solver /path/to/raftsim_water_solver
```
