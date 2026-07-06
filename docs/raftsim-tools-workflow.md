# RaftSim Tools Workflow

Open `unreal/SmokeEmIfYouGotEm.uproject` in Unreal Editor 5.8 and use the `RaftSim Tools` menu as the entry point for tooling review. The menu opens dockable Slate tabs for each tool surface and includes utility commands for opening every tool, creating reviewed DataAssets, and capturing screenshot evidence.

For a step-by-step editing, playtesting, and new-river authoring guide, see `docs/editing-playtesting-and-river-authoring-walkthrough.md`.

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

The Slate buttons now run the same C++ action path used by `URaftSimToolValidationActionRunner`: required evidence is checked, an action record is written under `Saved/RaftSim/ToolValidation`, report-opening actions launch the linked report, and live-water smoke dispatches the Unreal automation command.

## Review Artifacts

Run `RaftSim.CreateReviewedDataAssets` from the Unreal console or `-ExecCmds` to generate reviewed assets under `/Game/RaftSim/Tools/Reviewed`. The current reviewed assets are `DA_RaftSimToolRegistry`, `DA_ReplayDebugViewer`, `DA_RapidRiverEditorShell`, `DA_FeatureTuningEditorShell`, and `DA_ToolValidationActions`.

Run `RaftSim.CaptureToolEvidence` to open every tool tab and write panel screenshots plus a manifest under `docs/tool-captures/milestone25a/`. The capture manifest records the screenshot sequence; native automated video capture is still a follow-up unless a reviewer records the editor screen manually.

## Vertical Slice Launcher

Use this after the replay/debug and validation paths are clean. Launch the selected South Fork vertical-slice scenario, then capture replay/debug evidence for the acceptance gate.
