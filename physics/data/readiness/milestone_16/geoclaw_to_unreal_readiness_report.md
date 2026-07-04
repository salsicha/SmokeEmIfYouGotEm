# Python-To-Unreal Readiness Report

Gate version: `raftsim.geoclaw_to_unreal_readiness.v1`

Decision: **BLOCKED**

The full Milestone 16 gate was regenerated, but live Unreal custom water remains blocked by: Milestone 16 GeoClaw/C++ Thresholds, Milestone 16 Raft Coupling.

## Checks

| Check | Status | Details |
| --- | --- | --- |
| Milestone 16 GeoClaw Reference Runs | PASS | 20 of 20 scenarios have full GeoClaw frames. |
| Milestone 16 C++ Solver Runs | PASS | 40 of 40 C++ runs completed with manifests. |
| Milestone 16 GeoClaw/C++ Thresholds | FAILED | 27 of 40 threshold comparisons pass. |
| Milestone 16 Geometry Validation | PASS | 6 of 6 geometry families pass. |
| Milestone 16 Raft Coupling | FAILED | 16 of 50 raft comparisons pass. |
| Milestone 16 Runtime Profile | PASS | 54 of 54 promoted C++ profile repetitions pass runtime budgets. |
| Milestone 16 Regression Promotion | PASS | 51 passing artifacts promoted. |

## Runtime Choices

- `authoritative_water_candidate`: custom C++ reduced or finite-volume shallow-water / height-field solver after full Milestone 16 approval
- `reference_solver`: GeoClaw offline fixed-grid output normalized into the shared telemetry schema
- `raft_and_contact_candidate`: Project Chrono bridge or custom reduced raft fallback over validated custom water fields
- `unreal_integration_order`: telemetry/replay playback and promoted regression fixtures first; live custom water only after all Milestone 16 checks pass
- `chrono_fsi`: optional research path only, not a baseline runtime dependency

## Required Next Actions

- Fix remaining GeoClaw/C++ threshold failures outside accepted guardrail rows.
- Retune raft coupling against GeoClaw and C++ fields until force envelopes, outcomes, and transition cases pass.
- Keep the distinct Milestone 18 pin/release fixture separate from the raft-coupling water-field agreement gate.

## Accepted Model Limitations

- 2.5D shallow-water/height-field flow remains the intended runtime model; full 3D CFD is out of scope.
- GeoClaw remains offline reference infrastructure and does not ship inside Unreal.
- Promoted fixtures are passing subsets, not proof that the full live-water gate has passed.
- Dedicated pin/release evidence remains a separate Milestone 18 fixture until the full readiness gate is rerun.

## Risks

- Most GeoClaw/C++ threshold comparisons still fail outside hydrostatic/sloping cases.
- Raft force and outcome agreement is not yet stable across hydraulics, drops, and boulder gardens.
- Runtime profile passes only the promoted configurations and still needs target hardware confirmation.
- Real-world river source licensing, guide review, and field-media validation remain production gates.
