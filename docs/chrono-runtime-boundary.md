# Chrono Runtime Boundary

This decision freezes the first native runtime split before Unreal production work.

## Baseline Ownership

| Area | Owner | Rationale |
| --- | --- | --- |
| Reduced shallow-water / height-field solver | Custom C++ | Deterministic, portable, tunable against PyClaw, and small enough for Unreal runtime budgets. |
| River feature forcing | Custom C++ | Holes, laterals, boils, ledges, shallows, eddy lines, and seasonal flow parameters must match the PyClaw validation path. |
| Water query API | Custom C++ | Unreal, Chrono coupling, audio, VFX, probes, and replay need one stable water-field interface. |
| Raft rigid-body integration | Project Chrono | Chrono is the baseline for 6DoF body dynamics, inertia, contacts, collision response, and future constraints. |
| Rock/bed/shore collision contacts | Project Chrono with custom water/contact inputs | Chrono owns collision resolution; custom code supplies water heights, bed fields, feature tags, and tuned contact coefficients. |
| Paddle/crew force intents | Custom gameplay layer feeding Chrono | Voice, network, AI, and player commands become deterministic force/impulse intents applied through the native physics bridge. |
| Telemetry/replay schemas | Shared custom schemas | Python, C++, Chrono, and Unreal must emit the frozen schema set without depending on engine-specific serialization. |
| Chrono::FSI | Optional experiment/reference only | Full fluid-particle coupling is governed by [Chrono::FSI Policy](chrono-fsi-policy.md) and is not the baseline runtime dependency for UE5. |

## Integration Rule

The custom C++ water solver remains the primary Unreal runtime candidate, as frozen in [Custom Water Runtime Baseline](custom-water-runtime-baseline.md). Chrono receives sampled water/contact inputs and returns raft transforms, velocities, contacts, and force telemetry. If Chrono integration misses runtime budgets, the fallback is a reduced custom rigid-body integrator using the same schemas and water query API, not a replacement of the water solver.

## Near-Term Milestone 8 Work

1. Build a standalone native C++ Chrono smoke test outside Unreal.
2. Feed the custom C++ water field into a Chrono raft body as buoyancy/contact samples.
3. Compare Chrono/custom-water telemetry against Python/PyClaw reference scenarios.
4. Keep Chrono::FSI isolated behind an experiment flag and out of required build/test paths.
