# Single-carrier lighting experiment

The live material uses volumetric non-directional translucency because it was
originally an overlay above an authored Single Layer Water surface. The isolated
survey scene instead uses it as its only visible carrier, with no volume core.
The old approach capture is nearly black, with little readable shape.

`review_south_fork_surface_lighting.py` duplicates that material into the review
asset folder and changes only its translucency lighting mode to Surface Forward
Shading. A preplaced water actor selects it; the raft's existing startup logic
does not spawn a second actor when one already exists. No geometric overrides,
physics, cooked fields, production maps or shared material were changed. The
shared material hash is unchanged. The review map's exact prior file is backed
up at `tmp/project-cleanup/SouthForkSurveyPlayable-before-surface-lighting.umap`.
The script refuses to overwrite an existing experiment or backup.

Actual 1280×720 game captures were inspected:

- `unreal/Saved/Screenshots/SurveyGuideFixed20260907_001.png`: previous lighting,
  roughly the same approach position and camera.
- `unreal/Saved/Screenshots/SurveySurfaceLit20260907_001.png` and `_002.png`:
  water is now illuminated, with visible small normal detail.
- `unreal/Saved/Screenshots/SurveySurfaceLitCrux20260907_001.png`: downstream
  surface remains broadly smooth. This is **not** realistic breaking whitewater.

The correction demonstrates the lighting mismatch, not adequate foam, wave
geometry, transmission or photographic likeness. The diagnostic source terrain
is still plain gray and its supported-rock outlines are coarse. The separated
rock-gap candidate was **not** loaded for this lighting comparison. Do not mix
that candidate's settling results with this scene's screenshots.

The clean 20-second, no-screenshot benchmark after 5-second warmup samples 1,029
frames: mean 19.446 ms / p95 26.381 ms; GPU mean 6.840 ms; solver mean 10.835 ms.
The preceding face-cache run was 19.783 / 27.209 ms, GPU 6.955 ms. This is one
engineering run per state, not statistically significant acceleration. Both
fail the 16.67 ms frame budget and 1.6 ms solver budget. Resolution is 1280×720,
screen percentage 87, NVIDIA RTX 3060 Laptop GPU. See
`survey_performance_surface_lit.json`.

The capture logs retain preexisting game-mode Python startup errors for missing
editor-only `AgentSkill` / `PythonTestRunner` and the render-thread
`r.MotionVectorSimulation` warning. Captures and normal process exit succeeded;
those warnings were not hidden. The experiment remains review-only and will
be replaced by the standard scene generator unless deliberately selected again.

The subsequent actual-engine captured-ground contact and registered replay
regressions both pass (2/2, `engine-tests-surface-lit/index.json`). This does not
supersede the separate failed natural free-drift outlet criterion.
