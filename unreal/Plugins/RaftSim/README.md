# RaftSim Unreal Plugin

`RaftSim` owns the simulator-specific runtime modules used by the Unreal game shell.

Production modules:

- `RaftSimCore`: shared types, versioning, deterministic identifiers, and data contracts.
- `RaftSimPhysics`: custom shallow-water, Project Chrono, replay, and bridge integration.
- `RaftSimWater`: authoritative custom C++ live-water bridge, accepted report manifest, and solver-facing contracts.
- `RaftSimRiver`: river corridor, feature, flow, season, and difficulty data.
- `RaftSimGeo`: geospatial source manifests, coordinate transforms, reach-local grids, stitched validation outputs, and Unreal corridor package contracts.
- `RaftSimRaft`: raft actors, guide seat anchors, paddles, crew seats, and boat presentation.
- `RaftSimInput`: Enhanced Input contexts and deterministic intent mapping.
- `RaftSimUI`: selection, debug, replay, settings, and scoring UI view models.
- `RaftSimDebug`: physics, audio, AI, replay, and validation debug overlays.
- `RaftSimAI`: local guide command, passenger persona, dialogue, and voice-intent interfaces.
- `RaftSimCrew`: crew safety, swimming skill, swimmer/rescue, and high-side/weight-distribution gameplay state.
- `RaftSimAudio`: interactive water/raft/crew audio, spatial presets, manifests, and validation telemetry.
- `RaftSimAutomation`: regression fixture import, live-water smoke suites, report-lock checks, and Unreal automation contracts.
- `RaftSimNetwork`: future multiplayer session, replication, prediction, voice, and scoring contracts.

The production foundation manifest lives at `unreal/Content/RaftSim/Production/production_foundation.json` and ties these modules to the UE 5.8 project lock plus the accepted Milestone 20 water report-set lock.

The plugin is intentionally source-first until Unreal Editor 5.8 is installed and can generate binary assets.
