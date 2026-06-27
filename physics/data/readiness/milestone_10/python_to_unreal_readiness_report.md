# Python-To-Unreal Readiness Report

Gate version: `raftsim.python_to_unreal_readiness.v0`

Decision: **BLOCKED**

The readiness audit completed, but one or more blocking checks failed; do not start the production Unreal project yet.

## Checks

| Check | Status | Details |
| --- | --- | --- |
| PyClaw Reference Scenarios | PASS | 7 PyClaw scenario runs completed. |
| Custom C++ Solver Scenarios | PASS | 7 C++ scenario runs completed. |
| Dual-Solver Comparison And Tuning | FAILED | Dual comparison threshold reports and a tuning report were generated; real-world median currently determines gate status. |
| 2.5D Raft Coupling Validation | PASS | Raft coupling sampled force envelopes across the readiness scenario suite. |
| First Real-World River Section Package | PASS | South Fork American preproduction corridor package is exported with manifest, flow bands, rapid candidates, and confidence metadata. |
| Adaptive Flow Parameters | PASS | Low, median, and high runnable flow presets map monotonically into solver parameters. |
| Profiling And Runtime Budget Reports | PASS | 18 profiling runs recorded. |
| Unreal Replay And Telemetry Exports | PASS | Representative replay and force telemetry files are exported for Unreal visualization. |

## Runtime Choices

- `authoritative_water_candidate`: custom C++ reduced shallow-water / height-field solver
- `reference_solver`: PyClaw, with shallow reference shelf for exact dry-cell scenarios until wet/dry reference handling is improved
- `raft_and_contact_candidate`: Project Chrono bridge over custom water/contact samples, with custom reduced raft fallback if budgets fail
- `unreal_integration_order`: replay/telemetry playback first, then live custom water, then Chrono/custom raft coupling
- `chrono_fsi`: optional research path only, not a baseline runtime dependency

## Required Next Actions

- Resolve dual_solver_comparison_and_tuning: Dual comparison threshold reports and a tuning report were generated; real-world median currently determines gate status.

## Accepted Model Limitations

- 2.5D shallow-water/height-field flow is the accepted runtime model for the first Unreal bridge; full 3D CFD is out of scope.
- PyClaw reference exports use a shallow shelf for exact dry cells to avoid Roe-solver singularities.
- The first real-world corridor remains a preproduction seed package; heavy lidar, imagery, guide references, and field media are not vendored.
- Real-world C++ matching must pass threshold reports before final river-content production.

## Risks

- Real-world hydraulic matching may need additional C++ solver terms or calibrated thresholds.
- Runtime budgets are measured on local smoke scenarios and need target hardware confirmation.
- Geospatial source licensing and attribution must be re-checked when pulling production data.
- Chrono integration is not yet verified inside Unreal or VR frame scheduling.
