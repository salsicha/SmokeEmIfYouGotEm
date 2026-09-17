# South Fork spray source attachment

2026-09-17. Narrow presentation correction, not final water-realism acceptance.
Normal South Fork now selects the visible-carrier, horizontal-source-plane mode.
The existing map-name guard remains; no other river or scenario catalog changes.
Troublemaker remains a rapid within South Fork, never a menu scenario.

The ordinary path had still selected legacy elevated/tilted spray, even after
source-matched terrain and water were installed. The correction uses the same
rendered carrier query as the opt-in review. It retains the six-site pool,
particle assets, spawn-rate budgets, physical solver and wetness requirements.
The alternate falling-particle assets remain opt-in. Setting
`raftsim.SouthForkCrestSpray=0` retains the legacy comparison path.

## Evidence and scope

Two actual 1280x720 FullReach gameplay recordings, at review station 8330,
completed with exit zero, no timeout, and verified cook suspension/resumption.
The same executable used explicit CVar 0/1 and source auditing; neither used the
ballistic-asset review flag. Labels under `unreal/Saved/Logs` and corresponding
process reports under `unreal/Saved/RaftSimValidation`:

- `south-fork-spray-legacy-motion-v1-20260917`
- `south-fork-spray-attached-motion-v1-20260917`

At the one-time ten-second audit, all five candidate sites were visible, wet,
enabled, and horizontal. Their source-anchor heights exactly matched the queried
visible centre, with 6/3/3 cm aerosol/roller/spray offsets. Legacy centre-relative
spray gaps ranged from -1.692710 to 45.583406 cm; source planes were tilted.
These are **centre-relative** gaps, not terrain/particle contact measurements at
each horizontally shifted emitter. The log explicitly identifies whether a
footprint was checked. Invalid/unavailable records are not contact evidence.

Recordings `RaftSim_20260917-161227.mp4` and
`RaftSim_20260917-161323.mp4` were fully decoded: 467 and 475 encoded frames,
respectively, with sampled images at 1/3/6/9/11/13 seconds. Decode reports:
`tmp/spray-{legacy,attached}-decoded-v1-20260917/report.json`.
Source SHA256s:

- legacy: `efb4cd47ed332dfd8ee24e2bea8d1cf7df25731d777d3c7d3e425b2bbe8e9ed6`
- attached: `e08a2eaf04ff504c56d9d77f9b6ec0a8c997e53f509776d31e1714a7ddb6699b`

Inspected 6/11-second images show smaller, lower spray tufts in the candidate.
Trajectories/timing are not identical, so this is not a pixel-exact comparison.
The broad blurred foam, smooth mean wave and coarse bank/vegetation remain
unaccepted. Decoded frame rate is not game FPS.

The [Qweniden reference](https://www.youtube.com/watch?v=2XTbOCNDcZQ) was accessed
again in Chrome after the normal ads. Actual bank-view frames at 0:02 and 0:10
show irregular breaking edges, dark trough gaps, angular rocks and turbulent
foam. These sparse observations are qualitative, not a calibrated height,
velocity or whole-video motion measurement. No remote footage was downloaded.

## Footprint correction before default integration

The original nine probes were flow-oriented but extended only 0.8 m along flow.
The aerosol's 0.48 m half-length at maximum 1.35 scale plus 0.35 m offset reaches
0.998 m. Keep all original probes and add +/-1.05 m rows, for fifteen probes
total; +/-1.5 m across flow covers the 1.4175 m maximum aerosol half-width.
Native tests reject each missing/dry probe independently in four orientations.
This finite sampling is **not** continuous footprint or per-particle collision.
It does not make the horizontal plane conform to every slope beneath it.

## Installed validation

Editor Development build succeeded. Five native tests pass without warnings:
SpraySourceFootprint, RapidSourcePlane, SouthForkSprayReviewMap,
VisibleSprayCarrier, WaterVfxClassifierUsesHydraulicsAndContacts.
Report: `tmp/spray-source-installed-native-v1-20260917/index.json`.
All 28 targeted Python water-presentation/scenario tests pass. Other previously
recorded physical and legacy source-contract failures are not closed by this set.

`south-fork-spray-installed-motion-v1-20260917` uses the ordinary default, with
no CVar or ballistic override. All five audited sites are enabled, horizontal,
wet-footprint checked and exactly anchored to the visible centre. The run exits
zero with all 24 screenshots and verified cook resumption. Its video is
`unreal/Saved/VideoCaptures/RaftSim_20260917-162311.mp4`, SHA256
`72d7555aad3eaaa2b75521a3bc685dad13fc170eea853a1a92f7251052b08db1`.
All 474 encoded frames decode; report:
`tmp/spray-installed-decoded-v1-20260917/report.json`.
Inspected 11/13-second frames retain the lower source placement, but detached
tuft-like particle shapes and the broad soft foam remain visibly unconvincing.
This fixes emission placement, not the particle shapes or full breaking model.

Separate audit-free `south-fork-spray-installed-profile-v1-20260917` completes
300 frames, exit zero, no timeout, cook CPU unchanged during suspension and
resume status zero. Unchanged audit rows30-90 give **28.573702 FPS / p95
41.4636 ms: FAIL30**. CSV SHA256:
`42f9a483238aa8a24c64da2e18613ae11212895106055dd7709ccefbf37f32d4`.
Report: `tmp/spray-installed-profile-v1-20260917.json`.
This is not a controlled speed improvement/regression claim or sustained
full-route qualification. No quality, simulation rate or gate was reduced.

Standalone Development build also succeeds (161.38 seconds), log
`tmp/spray-source-installed-game-build-v1-20260917.log`. It reports the existing
C4701 warning in `RaftSimDetailSourceFootprintTest.cpp:105`, not a clean-warning
build. Old cooked packages do not inherit these builds; no packaged validation
is claimed. Full reconstruction and the ordered Colorado,
Pacuare, Futaleufu, all-scene water, crew, regression and release queue remain open.
