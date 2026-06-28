# RaftSim Unreal Plugin

`RaftSim` owns the simulator-specific runtime modules used by the Unreal game shell.

Initial modules:

- `RaftSimCore`: shared types, versioning, deterministic identifiers, and data contracts.
- `RaftSimPhysics`: custom shallow-water, Project Chrono, replay, and bridge integration.
- `RaftSimRiver`: river corridor, feature, flow, season, and difficulty data.
- `RaftSimRaft`: raft actors, guide seat anchors, paddles, crew seats, and boat presentation.
- `RaftSimInput`: Enhanced Input contexts and deterministic intent mapping.
- `RaftSimUI`: selection, debug, replay, settings, and scoring UI view models.
- `RaftSimDebug`: physics, audio, AI, replay, and validation debug overlays.

The plugin is intentionally source-first until Unreal Editor 5.8 is installed and can generate binary assets.
