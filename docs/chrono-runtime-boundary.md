# Native Runtime Boundary

This decision freezes the first native runtime split before Unreal production work, then adds the current Chaos/Jolt evaluation path for raft/contact authority.

See [Chaos And Jolt Runtime Evaluation](chaos-jolt-runtime-evaluation.md) for the shared fixture suite that compares Unreal Chaos and Jolt on raft impacts, grounding, pin/release, crew ejection, determinism, and runtime cost.

## Baseline Ownership

| Area | Owner | Rationale |
| --- | --- | --- |
| Reduced shallow-water / height-field solver | Custom C++ | Deterministic, portable, tunable against GeoClaw, and small enough for Unreal runtime budgets. |
| River feature forcing | Custom C++ | Holes, laterals, boils, ledges, shallows, eddy lines, and seasonal flow parameters must match the GeoClaw validation path. |
| Water query API | Custom C++ | Unreal, Chrono coupling, audio, VFX, probes, and replay need one stable water-field interface. |
| Raft rigid-body integration | Runtime selected after Chaos/Jolt evaluation; Chrono remains reference/research | The shipping runtime must pass fixed-step replay, contact quality, pin/release, crew/swimmer state, and CPU budget fixtures. |
| Rock/bed/shore collision contacts | Selected raft/contact runtime with custom water/contact inputs | The selected runtime owns collision resolution; custom code supplies water heights, bed fields, feature tags, and tuned contact coefficients. |
| Paddle/crew force intents | Custom gameplay layer feeding the selected raft/contact runtime | Voice, network, AI, and player commands become deterministic force/impulse intents applied through the native physics bridge. |
| Telemetry/replay schemas | Shared custom schemas | Python, C++, Chrono, and Unreal must emit the frozen schema set without depending on engine-specific serialization. |
| Chrono::FSI | Optional experiment/reference only | Full fluid-particle coupling is governed by [Chrono::FSI Policy](chrono-fsi-policy.md) and is not the baseline runtime dependency for UE5. |

## Integration Rule

The custom C++ water solver remains the primary Unreal runtime candidate, as frozen in [Custom Water Runtime Baseline](custom-water-runtime-baseline.md), but live custom water still depends on the Milestone 18 closure evidence being consumed by a regenerated full validation/readiness gate as described in [Custom C++ Engine Full Validation Plan](custom-cpp-engine-validation-plan.md). The selected raft/contact runtime receives sampled water/contact inputs and returns raft transforms, velocities, contacts, and force telemetry. If Chaos and Jolt both miss authority gates, the fallback is a reduced custom rigid-body integrator using the same schemas and water query API, not a replacement of the water solver.

The detailed coupling strategy is captured in [Chrono Water And Raft Coupling Plan](chrono-water-raft-coupling-plan.md). Rock contacts should use partially elastic rubber-raft collision presets, while riverbed grounding should use low-restitution, high-damping inelastic contact presets.

Project Chrono remains useful for high-fidelity reference, compliant-contact experiments, and optional FSI exploration, but it is no longer the only candidate for the shipping raft/contact runtime.

## Near-Term Runtime Work

1. Complete the Milestone 18 custom-water validation closure, or label any Chaos/Jolt runs as snapshot-only comparisons while live water remains blocked.
2. Build the Chaos automation fixtures and Jolt smoke fixtures from `chaos_jolt_runtime_evaluation.json`.
3. Feed a frozen validation snapshot into both runtime targets as buoyancy/contact samples; switch to live custom C++ water only after a future solver-parity gate approves it.
4. Add distinct material presets for elastic rock impacts and inelastic bed grounding in both targets.
5. Compare Chaos/Jolt telemetry, determinism, contact outcomes, and runtime cost against the same fixture summaries.
6. Keep Chrono::FSI isolated behind an experiment flag and out of required build/test paths.
