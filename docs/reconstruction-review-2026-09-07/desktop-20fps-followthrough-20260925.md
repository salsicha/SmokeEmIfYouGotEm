# Desktop 20 FPS target follow-through — September 25, 2026

The user's target revision changes desktop acceptance to 20 FPS: 50 ms p95
frame budget and 100 ms two-frame hitch threshold. It does not cap gameplay,
change simulation frequency, lower visual quality, or relax geometry/contact,
solver or memory requirements. Existing reports retain their original targets.

Updated the runtime-budget JSON, desktop environment profile, native quality
default and content-lock director, CSV audit defaults and profiling metadata,
and the active plan authority. VR, handheld and debug-replay profiles are unchanged.
Engine CSV source confirms `csv.TargetFrameRateOverride` selects capture target
metadata, not `t.MaxFPS` or the frame limiter.

## Regression repair and checks

The profiling identity test had required a literal one-line station guard with
hard-coded 8330 m. The existing production script now selects a recorded optional
station and formats it with invariant culture. Both mismatching forms existed in
HEAD before this work; the FPS change did not introduce the mismatch.

The repaired check evaluates the real station-selection assignment and guarded
argument builder. It checks normal start (no station), the unchanged 8330 m
diagnostic default, explicit zero and 1234.125 m, under en-US and fr-FR cultures.
It also requires explicit-station/normal-start conflicts to fail before launch.
No production launch behavior or assertion threshold was relaxed.

All nine profiling-script check groups pass. Fourteen CSV unit tests and both
runtime-budget checks pass; the environment-profile JSON also retains the exact
20/90/30 desktop/VR/debug-replay targets. Pytest itself was unavailable in the
local dependency path, so the two standalone runtime-budget assertion functions
were executed directly; the CSV tests ran with unittest.

The editor target rebuilt successfully in 58.85 seconds; standalone Development
rebuilt in 117.82 seconds. This target change and regression repair do not
establish river or release acceptance. No packaged executable was restaged.

## Fresh normal-launch measurement

With both builds terminal, the rebuilt editor-hosted game launched normally
through Boot/menu `south_fork_full_descent` into `L_SouthForkAmerican_FullReach`.
D3D12 offscreen, 1280x720, ephemeral profile, 1200 post-travel CSV frames; exit0.
No review station, solver, boarding, calf-fit, resolution/cadence reduction or
other experimental gameplay flags. No source geometry or cooked fields changed.

Log: `tmp/south-fork-20fps-normal-20260925.log`. It confirms Boot/menu travel,
`csv.UseLegacyFrameTime=false` and `targetframerate=20` capture metadata.
CSV: `unreal/Saved/Profiling/CSV/Profile(20260925_151103).csv`, SHA256
`838e78ede77c8dbfb56bd10a554d3a267e7425b5f039e6540553466e7ce73687`.
Report: `tmp/south-fork-20fps-normal-cost-20260925.json`.
Analyzer uses its new default target, rows30–1170 inclusive, required water
scopes and explicitly established scope offset1; no existing report overwritten.

1141 selected frames: mean23.781307ms (42.049833 elapsed FPS),
p95=32.0096ms, maximum47.5985ms. The selected p95 passes50ms. Zero frames exceed
100ms in either the selected interval or all1200 captured frames; all-frame
maximum is also47.5985ms. Mean game-thread23.587015ms, render-thread13.023926ms,
GPU9.193510ms. This unpaired run is not evidence of an optimization or that
changing the acceptance target improved runtime speed.

Three sampled drift entries show raft speeds1.367/1.186/1.124m/s and water
speeds1.135/1.034/1.069m/s; all report wet1, support delta0cm and ground
penetration0m, with changing raft positions. These samples establish motion,
not continuous collision/shoreline correctness or full-route traversal.
No screenshots were captured in this timing run. Long-duration, packaged,
visual, geographic and hydraulic acceptance remain open; later rivers stay queued.
