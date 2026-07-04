# Python-To-Unreal Readiness Report

Gate version: `raftsim.geoclaw_to_unreal_readiness.v1`

Decision: **APPROVED**

The full Milestone 16 GeoClaw/C++/raft/runtime gate passed; live Unreal custom water can proceed after target-hardware confirmation.

## Checks

| Check | Status | Details |
| --- | --- | --- |
| Milestone 16 GeoClaw Reference Runs | PASS | 20 of 20 scenarios have full GeoClaw frames. |
| Milestone 16 C++ Solver Runs | PASS | 40 of 40 C++ runs completed with manifests. |
| Milestone 16 GeoClaw/C++ Thresholds | PASS | 40 of 40 threshold comparisons pass. |
| Milestone 16 Geometry Validation | PASS | 6 of 6 geometry families pass. |
| Milestone 16 Raft Coupling | PASS | 50 of 50 raft comparisons pass. |
| Milestone 16 Runtime Profile | PASS | 80 of 80 promoted C++ profile repetitions pass runtime budgets. |
| Milestone 16 Regression Promotion | PASS | 98 passing artifacts promoted. |

## Runtime Choices

- `authoritative_water_candidate`: custom C++ reduced or finite-volume shallow-water / height-field solver after full Milestone 16 approval
- `reference_solver`: GeoClaw offline fixed-grid output normalized into the shared telemetry schema
- `raft_and_contact_candidate`: Chaos/Jolt runtime authority evaluation over validated custom water fields, with Chrono retained as high-fidelity reference/research
- `unreal_integration_order`: telemetry/replay playback and promoted regression fixtures first; live custom water only after all Milestone 16 checks pass
- `chrono_fsi`: optional research path only, not a baseline runtime dependency

## Required Next Actions

- Lock the accepted Milestone 16 report set and regression fixtures before live-water Unreal integration.
- Repeat runtime profiling on target desktop, VR, and handheld hardware.

## Accepted Model Limitations

- 2.5D shallow-water/height-field flow remains the intended runtime model; full 3D CFD is out of scope.
- GeoClaw remains offline reference infrastructure and does not ship inside Unreal.
- The approved Milestone 16/18 gate validates the current C++ water evidence set; new authored rivers, feature-forcing defaults, and gameplay tuning must add matching regression evidence.
- Flow-dependent pin/release, crew high-side, swimmer, and rescue behavior remain dedicated gameplay fixtures layered over the approved water-field agreement gate.

## Risks

- Runtime profile passes on the local validation machine and still needs target desktop, VR, and handheld hardware confirmation.
- Real-world river source licensing, guide review, field-media validation, and level-editor annotation remain production gates.
- Chaos/Jolt raft/contact/swimmer authority must still be selected and validated over the approved custom water outputs.
- Future feature forcing must remain bounded, manifest-recorded, GeoClaw-compared, and separate from conservation fixes.
