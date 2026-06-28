# Physics Runtime Budgets

These budgets gate the Python/C++ modeling phase before Unreal production begins. They are intentionally conservative first-pass targets for the reduced shallow-water solver, raft coupling, probe/export paths, and future Chrono integration.

## Budget Profiles

| Profile | Render Target | Physics Tick | Total Physics Budget | Water Solver | Raft Coupling | Probe/Telemetry |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Desktop | 60 Hz | 120 Hz | 4.00 ms/tick | 2.40 ms | 0.80 ms | 0.40 ms |
| VR | 90 Hz | 120 Hz | 3.00 ms/tick | 1.60 ms | 0.60 ms | 0.25 ms |
| Handheld | 60 Hz | 60 Hz | 5.00 ms/tick | 2.80 ms | 0.90 ms | 0.40 ms |

## Acceptance Gates

- Baseline reports must include the canonical fixtures plus one generated procedural rapid.
- C++ solver mean runtime should stay within the per-profile water-solver budget for the target platform.
- Raft coupling mean runtime should stay within the per-profile raft-coupling budget.
- Probe/export cost is a research-loop budget, not a shipping per-frame budget, but it must stay low enough for repeated GeoClaw/C++ comparison runs.
- Max runtime should remain below twice the relevant mean budget for desktop and handheld, and below 1.5x for VR.
- Any budget miss must be recorded with scenario id, profile, measured value, candidate parameters, and whether the miss blocks Unreal integration.

## Unreal Readiness Rule

Unreal production should not start until the C++ reduced solver, raft coupling, telemetry schema, and replay/export paths can produce baseline reports for the shared scenario set and show at least one desktop-passing configuration. VR and handheld budgets may remain provisional, but their misses must be understood before content scale-up.
