# Milestone 25A Polished Tooling Slice Gate

Decision: PASS_TOOLING_CONTRACT_AND_EDITOR_BUILD_GATE

The Milestone 25A gate is source-controlled at `unreal/Content/RaftSim/Automation/polished_tooling_slice_gate.json`.

The gate verifies:

- `RaftSimEditor` and the `RaftSim Tools` menu registry exist;
- Replay + Debug Viewer, Rapid/River Editor, and Feature Tuning Editor shells have C++ config/view-model types and JSON manifests;
- sample South Fork and Milestone 10 replay data are named by the tool manifests;
- validation state, export blockers, and report/action targets are visible in source-controlled data;
- one-click validation actions are registered for source checks, deterministic export, solver regeneration, stitched-window validation, live-water smoke, round-trip validation, and report opening;
- a user-facing workflow document exists;
- the editor target builds with the tooling sources.
- `RaftSim.Milestone25A.PolishedToolingSliceGateManifest` passes under `UnrealEditor-Cmd` with `NullRHI` and exit code 0.

This closes the source-first tooling slice. The next polish layer is interactive widget work: dockable tabs, actual button execution, rendered overlays, reviewed DataAssets, and visual capture from inside Unreal Editor.
