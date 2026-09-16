# Retained-source playable preview and exact solver rows

September 16, 2026. Reconstruction, convincing breaking/froth, normal-play
promotion and 30 FPS remain **incomplete**. This checkpoint repairs a stale
candidate preview, verifies actual gameplay, and prepares a tested solver
optimization; it does not label either as finished scene delivery.

## Native solver optimization

Commit `d66bb23c1` validates numerical array shape AND backing storage once per
stage, keeps general Array2D access checked, and parallelizes independent
primitive/recompute rows through the existing bounded executor. Equations,
spatial order, CFL, grid resolution, boundaries and positive-film volume are
unchanged. Views never outlive the stage or survive state replacement.

All four native CTest cases pass, including malformed storage rejection,
large parallel-vs-serial exact comparisons, wet/dry shoreline, Cartesian
conservation/checkpoint continuation, lake balance and transcritical flow.
Final rerun: 4/4, 9.03 seconds; isolated Release build directory:
`tmp/solver-grid-view-candidate-v2-20260916`.

Two independent four-pair alternating-order, 600-step comparisons retain all
44 paired saved frames bitwise-identical in each comparison. Registered replay
median solve/capture time: 3.519865 -> 3.163715 seconds (10.12% reduction).
Current-source Cartesian crop: 3.635420 -> 3.372720 seconds (7.23% reduction),
all four candidates faster. Total wall-time gains are smaller because export
dominates. These are **component timings under concurrent work, not game FPS**.
The current-source crop has 226 x 226 cells, MUSCL2/HLL and source-exact 50 s
state/bed; it reproduces the loader contract but is not independently verified
as an exact native runtime export. That limitation remains explicit.

Reports:
`tmp/solver-grid-view-comparison-v2-20260916/report.json` and
`tmp/solver-grid-view-cartesian-comparison-v2-20260916/report.json`.
The earlier views-only v1 candidate was inconsistent and is NOT the qualified
timing result. Its evidence is retained.

The normal UE static-library builder succeeded after the tests. New archive
`physics/cpp/build-ue/raftsim_water.lib` SHA256:
`d2139f1b4d95814786162dd15dcb1e3509d3225d0df6f2059b95d099ca6113b9`.
Old archive retained at `tmp/solver-grid-view-ue-baseline-v1-20260916.lib`, SHA256
`b828162b849756b1c15bb1a78fc277e4fd1cec6028b2736597b3b343f2c5ec8e`.
**Editor/game relinking and actual-game qualification are still next.** No
loaded DLL or packaged executable was replaced during the active cook. The
gameplay capture below uses the existing, pre-optimization engine binary.

## Fresh preview without rewriting historical evidence

CPU-retention correctly invalidated the old mesh package hash. The new
`refresh_south_fork_joint_preview_stage.py` accepts only the versioned, exact
before/after retention revision plus independent native saved-package readback.
It checks native triangle identity/count, material assignment and package hashes,
source cap, FBX, transform, successful union/field queries, and read-only audit
status. It does not import, modify or save assets. The original stage remains
unchanged, and the preview binds the old stage and retention receipt as additional
hashed dependencies. Changed geometry/material/native evidence is rejected.

77 focused Python tests PASS across retention, rebind and joint-preview checks.
Fresh stage: `tmp/landward-cpu-retained-stage-v1-20260916.json`.
Fresh descriptor: `tmp/landward-cpu-retained-preview-v1-20260916.json`, SHA256
`d8afce8dd51350f0bb79ed325bb4c584f3d51dfdd7b65ebf6e5c57ecffe837d8`.
All 3,258 dependencies match after gameplay. Of 464 historically protected
files, 462 are unchanged and two have only the already proven CPU-retention
revisions; map, 456 actor packages and profile remain unchanged.

## Actual engine motion and reference

The existing [Qweniden bank-side reference](https://www.youtube.com/watch?v=2XTbOCNDcZQ)
is accessible through the in-app browser. Playback advanced; sampled frames
at 0:27, 0:29 and 1:01 show distinct breaking crests and darker gaps between foam.
This is qualitative, unregistered evidence, not a measured flow, bathymetry,
camera calibration or claim to have continuously watched the whole clip.
No remote video was downloaded.

Actual FullReach `-game`, D3D12, 1280 x 720, scenario
`south_fork_full_descent`, review station 8330, ephemeral profile, joint-preview
descriptor above, and `-RaftSimFullHullGroundReview -RaftSimSharedHullReview`.
The capture command was:

```text
RaftSim.CaptureSeries 12 3 10 landward-cpu-retained-playable-v2-20260916 -545900 -362700 2000 -35.27 46.85 record
```

The first v1 invocation incorrectly split the unquoted PowerShell native argument
before `.json`; the engine refused it before BeginPlay. Its failure log remains.
Only that confirmed failed process was stopped after subsystem shutdown. The
correctly quoted v2 invocation exited 0, logged installation before BeginPlay,
the exact 50-second cap/field identity, one water surface and full-hull mode.
Three screenshots occur at world 12.405/22.150/32.134 s, advancing to station
8353.626 m. Both logged hull/render comparisons have zero position mismatch;
no contact refusal/mismatch/latch entries occur. This short run is NOT proof
of sustained downstream contact or packaged execution.

Recording: `unreal/Saved/VideoCaptures/RaftSim_20260916-020143.mp4`, 103 source
frames / 25.091 seconds. All 753 encoded frames decode through 25.0667 s.
Inspected unmodified decoded frames at 8/16 seconds: raft and foam change while
the rock remains fixed. Broad white cover, smooth green wave faces and abrupt
inferred sidewalls are still **unaccepted**. Encoded 30 Hz and repeated frames
do not establish game FPS. Decoder ROI names belong to an older camera; they
are not physical-region classifications for this camera.

Evidence: `tmp/landward-cpu-retained-playable-evidence-v1-20260916.json`, SHA256
`21b5501273cf1fb430322edeeda27c84c6fb290a2118e69fce19a88ab65184db`.
Decoded evidence: `tmp/landward-cpu-retained-motion-v1-20260916`.
Experimental editor Toolset Python exports still emit AgentSkill/PythonTestRunner
errors, so this is not a clean release run. No normal-menu promotion is claimed.

## Corrected hydraulic continuation

The preceding 1150-second restart failed its 1250-second exact-dry gate at
`core_0229` east: one cell at 1.0032464863478674e-6 m. No tolerance was relaxed.
The failed report remains `tmp/south-fork-context2-1250-banks-v1-20260916.json`.

Restart from that cook's last clean **1200-second** snapshot, adding one existing
source-exact dry context tile at UTM (675440,4296000). All 838 retained geometry
records, union, bed, roughness and physical boundaries are unchanged. Applying
the union changes zero added cells; added water is zero. Independent pilot and
actual native restart prove all 5,363,200 retained h/u/v cells bit-exact, 6,400
new source cells, unchanged clock and inventory error 4.656612873e-10 m3.
The prior PID18000 was stopped only after verifying its replacement; old files
are retained. Input SHA256:
`189e14a252e3a9ad2f698a33129875521845ac71cc809b183ac91e2a1131ff37`.

The new 1250 AND 1300-second snapshots pass finite/conservation checks and
all **86,720** artificial-bank face cells are exactly dry. At 1300 s, maximum
depth is 4.559992563 m, speed 7.141828416 m/s, volume 3,017,324.058295 m3,
maximum per-step conservation residual 1.378528425e-8 m3. Outflow still exceeds
inflow; this is NOT settled hydraulics or normal-map integration.
Reports: `tmp/south-fork-context3-{1250,1300}-{snapshot,banks}-v1-20260916.json`.

**Same live job: session69416 / PID18716**, output
`tmp/south-fork-landward-context1200to1800s-v1-20260916`, 12,000 steps x .05 s
toward 1800 s. Next completed local3000 / absolute1350 s cell AND bank audits.
Never restart on an observation timeout.

## Next delivery work

Package session80881 / cook PID16144 remains live; shader worker31852 continues
consuming CPU despite repeated 900-second no-state-change warnings. Do not
replace/restart the cook on a timeout. After SAME-job completion, verify archive
coherence, all 2,405 runtime payloads and all 444 non-editor ground sources;
then relink the tested solver, restage if needed, and qualify actual packaged
play/contact/performance before normal full-hull promotion. No cook proof yet.

Last uncontended ordinary game: **17.819710 FPS / p95 81.6343 ms**, still FAILS
30 FPS / p95 33.333333 ms. No fresh uncontended measurement under competing jobs.
Visible breaking/froth, source-supported rock shape and playable-first delivery
remain priorities, not more isolated diagnostic acceptance. Colorado -> Pacuare
-> Futaleufu, Chilko/Zambezi/all-scene water, crew, normalization, physical
regressions and release remain OPEN. Troublemaker is a rapid within South Fork,
never a menu scenario.
