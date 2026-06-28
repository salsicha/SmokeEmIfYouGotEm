# Python-To-Unreal Readiness Report

Gate version: `raftsim.geoclaw_to_unreal_readiness.v1`

Decision: **BLOCKED**

GeoClaw transition artifacts were generated, but live Unreal water remains blocked until the failed GeoClaw validation checks pass.

## Checks

| Check | Status | Details |
| --- | --- | --- |
| GeoClaw Reference Exports | PASS | 1 GeoClaw export packages generated. |
| GeoClaw Fixed-Grid Outputs | FAILED | Normalized output mode is export_initial_state_only; full GeoClaw fgout frames are required for approval. |
| Custom C++ Solver Scenarios | FAILED | 0 C++ scenario runs completed. |
| GeoClaw/C++ Comparison | FAILED | 0 GeoClaw/C++ threshold comparisons completed. |
| GeoClaw C++ Tuning | FAILED | 0 C++ tuning candidates scored against GeoClaw. |
| GeoClaw Raft Coupling | FAILED | 0 raft coupling comparisons completed. |

## Runtime Choices

- `authoritative_water_candidate`: custom C++ reduced shallow-water / height-field solver
- `reference_solver`: GeoClaw offline fixed-grid output normalized into the shared telemetry schema
- `raft_and_contact_candidate`: Project Chrono bridge over custom water/contact samples, with custom reduced raft fallback if budgets fail
- `unreal_integration_order`: telemetry/replay playback first, then live custom water after GeoClaw revalidation, then Chrono/custom raft coupling
- `chrono_fsi`: optional research path only, not a baseline runtime dependency

## Required Next Actions

- Replace export-only normalized frames with real GeoClaw fixed-grid output for canonical, rafting, and real-world flow suites.
- Run the custom C++ solver against the same packages and pass GeoClaw/C++ thresholds.
- Re-run raft coupling against GeoClaw and C++ fields with outcome agreement.

## Accepted Model Limitations

- 2.5D shallow-water/height-field flow remains the accepted runtime model for the first Unreal bridge; full 3D CFD is out of scope.
- GeoClaw is an offline validation/reference dependency, not a shipping Unreal runtime dependency.
- Export-only normalized GeoClaw frames are setup smoke artifacts and cannot approve live water.
- Real-world C++ matching must pass GeoClaw threshold reports before final river-content production.

## Risks

- GeoClaw setup depends on local Clawpack and Fortran build tooling.
- C++ solver parameters may need retuning after full GeoClaw fgout frames are available.
- Runtime budgets are still measured on local smoke scenarios and need target hardware confirmation.
- Geospatial source licensing and attribution must be re-checked when pulling production data.
