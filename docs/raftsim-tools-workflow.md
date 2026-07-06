# RaftSim Tools Workflow

Open `unreal/SmokeEmIfYouGotEm.uproject` in Unreal Editor 5.8 and use the `RaftSim Tools` menu as the entry point for tooling review.

## Replay + Debug Viewer

Use this first. It loads the Milestone 10 replay package, timeline bookmarks, force telemetry, and live-water debug overlay definitions. Review depth, velocity, Froude, wet/dry, feature tags, conservation deltas, raft trajectory, contact probes, and runtime budget overlays before allowing live physics to drive the same view.

## Rapid/River Editor

Use this for South Fork annotation review. Check station pins, reach/drop spans, polygons, raft lines, guide notes, evidence references, rights/provenance, confidence, and expected surf/flush/pin/release/flip outcomes. Do not promote an export while blocking validation messages remain.

## Feature Tuning Editor

Use this for flow-dependent feature forcing and presentation tuning. Keep physics-facing gains conservative. Solver-state and raft-coupling edits must remain manifest-recorded, GeoClaw-compared, conservation-guarded, and unable to hide conservation failures. Visual-only and audio-only controls must not affect solver or raft state.

## Validation Actions

Use the validation actions as the standard review buttons:

- Validate Source
- Export Deterministically
- Regenerate Solver Package
- Validate Stitched Window
- Run Live-Water Smoke
- Run Round Trip
- Open Latest Report

Each action names its required evidence and report target in `unreal/Content/RaftSim/Tools/tool_validation_actions.json`.

## Vertical Slice Launcher

Use this after the replay/debug and validation paths are clean. Launch the selected South Fork vertical-slice scenario, then capture replay/debug evidence for the acceptance gate.
