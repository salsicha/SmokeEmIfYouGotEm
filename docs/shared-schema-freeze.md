# Shared Schema Freeze

Milestone 7 freezes the first schema set shared by Python modeling, C++ runtime experiments, and future Unreal telemetry/replay tooling.

## Frozen Schemas

| Schema | Version | File |
| --- | --- | --- |
| 2.5D scenario package | `raftsim.scenario2_5d.v0` | `physics/schemas/scenario2_5d.schema.json` |
| Force telemetry CSV | `raftsim.telemetry_forces.v0` | `physics/schemas/telemetry_forces.schema.json` |
| Deterministic replay JSON | `raftsim.replay.v0` | `physics/schemas/replay.schema.json` |
| Parameter candidate JSON | `raftsim.parameters.v0` | `physics/schemas/parameters.schema.json` |
| Analytic fixture manifest | `raftsim.analytic_fixture_manifest.v0` | `physics/schemas/analytic_fixture_manifest.schema.json` |
| Feature-forcing manifest | `raftsim.feature_forcing.v0` | `physics/schemas/feature_forcing.schema.json` |

The schema set is indexed by `physics/schemas/shared_schemas_manifest.json` with version `raftsim.shared_schemas.v0`.

## Change Rules

- Additive optional fields may be added under the same version when old readers can ignore them.
- Required field removals, type changes, unit changes, renamed columns, or changed coordinate conventions require a new schema version.
- Telemetry CSV column order is frozen because tools may stream rows without header remapping.
- Replay files must preserve fixed-step timing and enough raft state to drive Unreal playback and debug visualization.
- Parameter candidate files must preserve both water-solver knobs and raft-force/contact knobs so tuning reports remain reproducible.
- Analytic fixture manifests must preserve provenance, benchmark-family notes, expected behavior, tolerance tiers, and a no-vendored-external-data flag until SWASHES licensing and maintenance are decided.
- Feature-forcing manifests must preserve low defaults, flow-response curves, solver-state effects, raft-coupling effects, visual-only parameters, GeoClaw comparison requirements, and conservation-failure guards.
