# Chaos And Jolt Runtime Evaluation

## Decision

Use a split/hybrid plan for now:

- Custom C++ remains authoritative for water state, water queries, and GeoClaw-validated shallow-water behavior.
- Unreal Chaos is the default Unreal-integrated physics path for visual ragdolls, physical animation, loose props, debris, breakables, editor-authored physics assets, and non-scoring set dressing.
- Jolt becomes the leading specialized candidate for a portable authoritative raft/contact/swimmer gameplay island if it beats Chaos on fixed-step replay, contact quality, and runtime cost.
- Project Chrono remains a high-fidelity research/reference backend for multibody, compliant contact, and FSI experiments. It is no longer the only runtime path under consideration for raft/contact authority.

No engine can own scoring-critical raft, crew, swimmer, pin, release, rescue, or flip outcomes until it passes the shared fixture suite in `unreal/Content/RaftSim/Physics/chaos_jolt_runtime_evaluation.json`.

This evaluation follows the Milestone 18 custom-water validation closure and regenerated readiness gate. Until the C++ water solver is approved for live Unreal use, Chaos/Jolt fixtures may use frozen water snapshots and telemetry for runtime comparison, but they must not imply that live custom water has passed the GeoClaw/C++ gate.

## Why This Split

Chaos is already inside Unreal, which makes it the practical default for animation-driven gameplay, visual ragdolls, physical assets, debugging, VR/editor iteration, props, ropes, paddles, bags, and shore clutter.

Jolt is attractive for the small deterministic gameplay-physics island: raft impacts, scrape/bounce/pin/release, swimmer bodies, character/contact constraints, fixed-step replay, and headless tests outside Unreal. If Jolt wins, Unreal still renders and authors content; Jolt would own only the selected scoring-critical runtime state.

Chrono still matters, but mostly as a high-fidelity reference and research tool. The raft game needs a shipping runtime that is fast, debuggable, deterministic enough for replay, and easy to integrate with Unreal and the custom water solver.

## Shared Fixture Suite

Both Chaos and Jolt must run the same six fixtures with the same water snapshots, collision geometry, material presets, fixed-step schedule, and telemetry schema:

1. `raft_rock_angle_sweep`
   Raft hits a rounded rock at multiple speeds and angles. Measures contact impulse, deflection, scrape/bounce/pin outcome, roll, recovery time, and CPU cost.

2. `shallow_shelf_grounding`
   Raft grounds on a shallow shelf. Measures grounding duration, bed penetration, scrape impulse, yaw pivot, release/stick outcome, and CPU cost.

3. `pin_release_wrap_proxy`
   Raft pins between offset rocks and then releases with scripted high-side timing. Measures pin force, duration, release timing, flip/release outcome, and crew weight-shift effect.

4. `crew_ejection_swimmer_transition`
   Crew member transitions from seated to falling/ejected to swimming. Measures explicit gameplay state changes, swimmer position, ragdoll/character stability, and replayable safety state.

5. `fixed_step_replay_determinism`
   Runtime repeats 1000 fixed steps with identical inputs. Measures determinism hashes, pose drift, contact event sequence mismatches, and outcome mismatches.

6. `runtime_cost_crowded_scene`
   One raft, eight crew, fifty rocks, and twenty loose props. Measures mean/p95/max CPU per step, contact count, island count, telemetry cost, and desktop/VR budget compliance.

## Acceptance Rules

- Chaos remains the default for visual/non-authoritative physics while the evaluation is pending.
- Jolt cannot become authoritative until it has a native smoke harness and passes the six fixtures.
- Chaos cannot become authoritative for scoring-critical raft/contact outcomes merely because it is already in Unreal; it must pass the same fixtures.
- Loose Chaos props may not change scoring-critical raft or swimmer outcomes unless they emit deterministic hazard events into the authoritative bridge.
- Neither Chaos nor Jolt may mutate authoritative water state. Both consume custom-water snapshots through the same water query API.
- Chaos/Jolt authority selection cannot override a blocked custom-water readiness report.
- The selected runtime must export telemetry and replay data compatible with the existing raft/contact schemas.

## Implementation Steps

1. Wait for Milestone 18 water-validation closure, or explicitly mark fixtures as snapshot-only runtime comparisons while live water remains blocked.
2. Build Chaos automation fixtures in Unreal using `chaos_jolt_runtime_evaluation.json`.
3. Build a Jolt native smoke harness or Unreal plugin path that loads the same fixture definitions.
4. Export matching JSON summaries and fixed-step replay files for both runtimes.
5. Add a comparison report that ranks Chaos and Jolt per fixture by determinism, runtime cost, contact quality, and gameplay outcome stability.
6. Keep Chrono comparison optional for high-fidelity reference cases after the Chaos/Jolt fixture loop is working.

## Current Artifacts

- Chaos automation fixture export: `unreal/Content/RaftSim/Physics/chaos_automation_fixtures.json`.
- Chaos fixture summary: `physics/reports/milestone19/chaos/summary.json` and `.md`.
- Chaos replay summaries: `physics/reports/milestone19/chaos/replays/*.replay_summary.json`.
- Jolt native smoke harness manifest: `physics/cpp/tests/jolt_smoke_harness_manifest.json`.
- Jolt fixture summary: `physics/reports/milestone19/jolt/summary.json` and `.md`.
- Jolt replay summaries: `physics/reports/milestone19/jolt/replays/*.replay_summary.json`.
- Chaos-vs-Jolt comparison report: `physics/reports/milestone19/chaos_vs_jolt_comparison.json` and `.md`.
- Runtime authority selection report: `physics/reports/milestone19/runtime_authority_selection.json` and `.md`.

The Chaos and Jolt files are automation-ready fixture exports, not authority evidence. Unreal/Chaos and the native Jolt harness still need to execute the generated fixtures and replace schema placeholder frames with measured telemetry before either runtime can be ranked or selected.

## Current Recommendation

Keep Chaos as the production default for Unreal-authored visual physics, keep Jolt as the leading portable candidate, and use `CustomReducedRigidBody` as the first vertical-slice raft/contact/swimmer authority fallback until measured Chaos/Jolt telemetry allows a stronger selection. Do not make Chaos or Jolt authoritative for scoring-critical outcomes until the fixture suite has measured evidence.
