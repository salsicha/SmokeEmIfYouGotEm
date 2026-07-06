# Milestone 25A Polished Tooling Slice Gate

Decision: PASS_INTERACTIVE_TOOLING_SLICE_GATE

The Milestone 25A gate is source-controlled at `unreal/Content/RaftSim/Automation/polished_tooling_slice_gate.json`.

The gate verifies:

- `RaftSimEditor`, dockable Slate tab spawners, and the `RaftSim Tools` menu registry exist;
- Replay + Debug Viewer, Rapid/River Editor, and Feature Tuning Editor shells have C++ config/view-model types and JSON manifests;
- sample South Fork and Milestone 10 replay data are named by the tool manifests;
- validation state, export blockers, and report/action targets are visible in source-controlled data;
- one-click validation actions are registered and executable from the Slate buttons for source checks, deterministic export, solver regeneration, stitched-window validation, live-water smoke, round-trip validation, and report opening;
- reviewed Unreal DataAssets exist under `/Game/RaftSim/Tools/Reviewed`;
- `RaftSim.CaptureToolEvidence` captures full-panel screenshots and a manifest under `docs/tool-captures/milestone25a/`;
- a user-facing workflow document exists;
- the editor target builds with the tooling sources.
- `RaftSim.Milestone25A.PolishedToolingSliceGateManifest` passes under `UnrealEditor-Cmd` with `NullRHI` and exit code 0.

This closes the first interactive tooling slice. The next polish layer is feature-specific map/replay/curve/export widgets, deterministic export and solver-regeneration execution behind the buttons, rendered overlays, and native automated video capture or a documented reviewer recording workflow.
