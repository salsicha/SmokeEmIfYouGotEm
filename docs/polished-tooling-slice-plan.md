# Polished Tooling Slice Plan

Milestone 25A converts the current text-first Unreal contracts into tools that can be opened and reviewed inside the Unreal Editor. The goal is not to replace source-controlled JSON; it is to give designers and reviewers a polished path for loading, inspecting, editing, validating, exporting, and replaying the same data without hand-editing files.

## Tool Surfaces

- `RaftSimEditor` module: owns menu registration, tool descriptors, shared validation status, and launch commands.
- Replay + Debug Viewer: loads the Milestone 10 replay manifest and exposes timeline scrub, bookmarks, force/contact samples, and the live-water debug overlays.
- Rapid/River Editor: presents station pins, reach/drop spans, polygons, raft lines, evidence references, guide notes, source/provenance status, confidence, and expected raft outcomes.
- Feature Tuning Editor: exposes flow-dependent forcing and presentation controls while keeping conservative defaults and manifest-recorded tuning.
- Geospatial Import/Export Validator: checks source manifests, CRS/transform metadata, reach-local grids, stitched validation exports, and deterministic solver package regeneration.
- Vertical Slice Playtest Launcher: opens the selected South Fork vertical-slice scenario and captures replay/debug evidence for the acceptance gates.

## Polish Bar

A tool is not considered polished until it:

- opens from a `RaftSim Tools` Unreal menu entry;
- loads source-controlled sample data without manual file lookup;
- presents validation errors and blocked export states clearly;
- exports deterministic JSON/GeoJSON/solver-facing artifacts when applicable;
- links every export to source manifests, report locks, and validation reports;
- has a focused automation or manifest-backed report;
- has a short workflow note for the person using it in the editor.

## Initial Implementation Order

1. Add the `RaftSimEditor` module and source-controlled tool registry.
2. Ship the Replay + Debug Viewer shell first, because it proves the visual review loop without changing river data.
3. Add the Rapid/River Editor shell once the shared registry and validation status model are stable.
4. Add the Feature Tuning Editor shell with conservative defaults and explicit physics-vs-presentation labeling.
5. Wire one-click validation actions to the existing Milestone 20, 21, 23, and 24 gate manifests.
6. Add a tooling-slice gate report and user workflow docs before rolling the work into broader Milestone 25 release hardening.
