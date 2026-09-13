# Normal South Fork fixed-camera motion evidence — September 12, 19:31 UTC

20:12 UTC update: [local-current froth revision and current capture](normal-river-local-froth.md).
The evidence below is the older global-lace baseline, not the current material.

19:49 UTC update: the missing rapid-bank canopy is now integrated in South Fork,
with a [new same-camera normal-game capture](normal-river-canopy-integration.md).
The capture below remains the pre-canopy baseline; water geometry and material
were not changed by canopy integration. Uniform/granular froth remains open.

This is the playable full South Fork map, with Troublemaker inside it, not the
retired isolated rapid scenario. No new material/geometry/physics changes were
made for this capture. Review station8330 uses normal ephemeral checkpoint
initialization; no mid-run station walks, teleports or scripted raft impulses.
Water and terrain acceptance remain open.

## Actual capture

Command `RaftSim.CaptureSeries 10 60 0.1 south-fork-normal-froth-motion-v1-20260912
-543700 -359000 1800 -25 -130 record`, launched in the normal full map with
`-game -RenderOffscreen -RaftSimEphemeralProfile`,1280x720.
The explicit fixed world camera avoids the older focus-station command's
Cartesian-east/north versus river-chainage ambiguity. No material overrides,
time dilation or stopped solver during recording.

- Log: `unreal/Saved/Logs/south-fork-normal-froth-motion-v1-20260912.log`.
- Frames: `unreal/Saved/Screenshots/south-fork-normal-froth-motion-v1-20260912_000.png`
  through`_059.png`.
- Movie: `unreal/Saved/VideoCaptures/RaftSim_20260912-122648.mp4`,33,751,062bytes,
  SHA256`eda0b61adef022498ff4b65dbc0f7e57952e8ffb961a62d1223953d04cd2cc02`.
- Audit: `tmp/south-fork-normal-froth-motion-audit-v1-20260912.json`.

All60 requested PNGs exist, all hashes unique; game time10.467–28.481s,
elapsed18.014s. Requests advance render frames106–165. Intervals
min/median/max0.241/0.309/0.400s, NOT the requested0.1s. The screenshot/recording
workload perturbs cadence; this is not an FPS/performance acceptance run.
Recorded camera displacement is exactly0cm. ROI[280,260,1000,600] changes,
but changed pixels alone do not prove physically correct advection.

Recorder log:102 source frames,22.725s; encoder may repeat frames to preserve
actual capture-time duration. PyAV independently decodes H.2641280x720,
682 presentation frames,22.7333s, strictly increasing timestamps0–22.7s.
Those682 frames must NOT be presented as682 independent rendered samples or
as proof of30FPS gameplay. Movie preview requested in the app; tool returned
queued, not proof the user watched it.

## What was and was not inspected

Actual screenshots000,020,037 were inspected. Captured rock controls and banks
are visible; foam patterns change and the raft enters the fixed view. The white
patches remain conspicuously uniform/granular and the surroundings are sparse,
with unfinished broad terrain visible downriver. The previous reference review
describes irregular dark troughs, steep rock controls and localized whitewater;
this capture is NOT accepted as a photographic match or verified breaking-wave
motion. No new reference footage was watched or imported in this pass.

The currently installed material's saved graph audit confirms transported vertex
foam drives four optical consumers and one globally current-advected lace.
That connection is not proof that local eddy/stretching motion looks correct.
Next visual work should inspect local foam movement, shading and crest/trough
structure against references while preserving source geometry and shared
water/contact coordinates; do not merely increase white coverage or wave size.

## Coordinate-report correction

`audit_water_capture_series.py` now supports an explicit Cartesian frame and
labels those outputs east/north rather than scoring chainage. The actual log's
legacy `raft_station_m` values here are hydraulic eastings[-5435.779,-5429.140]m;
northings[3599.205,3605.557]m. They are NOT negative river progress. A regression
checks Cartesian names/ranges and preserves legacy curved-river output. This
does not change gameplay coordinates or the scoring system.

User save SHA181d1e57… unchanged. No editor/game/build remains live after capture.
The independent offline flow continuation71400/PID30636 remains running.
