# Checkpoint terrain startup — 2026-09-17 UTC

## Installed correction and actual first frame

Ordinary South Fork now shows the nearby terrain and water in the first retained
1280x720 gameplay image. The prior water-only installed replay had visible water
but no terrain in image000; its later images acquired terrain. World Partition
initially loaded the authored put-in, then followed the camera to the restored
rapid several frames after the raft moved. This was not missing saved terrain.

Session restoration now copies the player's existing streaming-source policies
to a temporary checkpoint-location provider and completes cell activation before
hydraulic reseeding or moving the authoritative raft. It retains grid selection,
source shapes, loading ranges and priorities, requests Activated state, and
does not carry the old travel velocity into this discontinuity. Scope exit
unregisters the provider; there is no permanent full-reach residency, global
range change, geometry/material edit or player-source override. Nonpartitioned
maps retain their previous path. A failed readiness check rejects the move before
changing the hydraulic window. This is ordinary code, not a review-flag path.

The final installed replay `south-fork-checkpoint-terrain-installed-v3-20260917`
uses the ordinary map, installed modules and original24-frame capture. There are
no module overrides, paired-terrain preview, full-hull or audit flags, and no
warmup discard. It exits0 with all24 actual1280x720 frames. Frame000 was directly
inspected: terrain, water and crew colors are present. Destination activation
takes0.491672s in the first game tick; subsequent water preparation takes0.159654s.
The preceding isolated candidate took0.559821s for destination activation.
These are measured warm-cache costs, not cold-cache/loading-time guarantees.

Angular green water crests, broad smooth foam, terrain/source correspondence,
crew fit and animation are still unfinished. This does not establish physical,
geographic, photorealistic or performance acceptance. The separate in-run rescue/
restart `ARaftSimRaftActor::ResetToCheckpoint` path is not covered by this session
startup correction; its distant destination residency and water reseed still
need verification/integration. Cooked startup also remains unverified.

## Regression and build evidence

- Actual project unity unit compiled and linked (not unused standalone objects).
  Final project DLL SHA256
  `f11c1bc62511f43a36bb55ae67af3206c13e7e25066e0800e2795ce819cbdfc7`.
  All83 local source dependencies predate the compiled unity object.
- Six native tests PASS, no warned passes/failures/not-run: the new
  CheckpointDestinationSources plus StartupWaterAfterSessionRestore,
  ReconstructedSessionContracts, RunProgressDistinctFromRapidHydraulics,
  CoordinateFrameProgress and ShorelineCompactUpload. New checks verify exact
  destination pose, preservation of player policy and original source, empty
  source rejection, nonpartitioned no-op and provider registration/scope cleanup.
  Report `tmp/checkpoint-terrain-startup-native-v3-20260917/index.json`, SHA256
  `800268eeb8934d2e52173c44511571fce1bcda165486a11329327bb16392ae5b`.
- Three new source-order checks and the existing focused startup/preview/
  retention/session suite: **87 PASS**. Source checks do not prove rendering.
- Initial v1 capture/native launches omitted the temporary bootstrap's required
  gameplay-module argument. They exited during module startup before testing
  this change, followed by engine shutdown errors; no passes claimed. Terminal
  failure logs are retained. Corrected v2 launches verified the actual candidate.
- After final native success and confirming all editor processes stopped, the
  prior project DLL/PDB were backed up to
  `tmp/checkpoint-terrain-installed-backup-v3-20260917/` and replaced. Prior DLL
  SHA256 `4daae5dabefdc6107818c2cc4359b57366799e752d71116eedac20ef54e65af9`.
  The installed gameplay module remains947f5a53..., detail650f80ca...; no maps,
  source geometry, physics/editor binaries or captured assets were changed.
- Installed startup process report SHA256
  `127c56ecfca8c7a77fedbf47abc2e919c47eb8c4c244e0138fdced8ebe699b74`.
  First image SHA256
  `0787a3421e55b5e5081ed676ba54879a9ff5f957d4306a64356f60764a649749`.

## Full ordinary-map streaming replay passed its technical gate

Session58473 / PID28488, process start2026-09-17T00:25:35.7891550Z,
label `south-fork-checkpoint-terrain-installed-detail-v3-20260917`, uses installed
modules and the ordinary map without preview/full-hull/override flags. Original
120-world-second, eight post-ready handoff,100-fresh-frame,60-detail-second and
900-second observation gates are unchanged. Session58473 is now terminal0;
the engine exits0 without timeout. It records11,945 fresh presented frames,
eight post-ready handoffs and471.81669127382338 detail seconds. This proves
the technical continuity gate, not physical, visual or performance acceptance.

A fresh live process-module witness confirms installed projectf11c1bc6...,
gameplay947f5a53... and detail650f80ca... from their ordinary Binaries directories.
`tmp/checkpoint-terrain-installed-detail-v3-20260917-modules.json`, SHA256
`908cc90a79876cc7f96d465f1cf94561fc1314c0fd73817e1bf5b4273d34e657`.
The runner resumed its owned hydraulic cook11316 in its finally block (status0);
the same cook process was independently observed consuming CPU afterward.

Detail report SHA256:
`821f696da43ca830c4fd1fd485daee5b30e296b9ddab29668c55548e8daf73ba`.
Process report SHA256:
`d2bc126cb211745850e9b8b19d54573d678ddabb3eeb42712fed24e016045c0f`.
The report's conservative `normal_project_binary_deployed:false` field is not
a module audit; the independent live module witness above verifies the actual
installed paths and hashes. No binary deployment is inferred from that field.
The final handoff010 image was inspected directly: water and ground are present,
but the bare banks, crew fit and water appearance are still unaccepted.

No new FPS claim: last ordinary installed check remains26.784840FPS,
p9543.5724ms, FAIL30. Long-run rendering/contact/reentry and all physical gates
remain open independently of this startup correction.

## Hydraulic1350s checkpoint

The same841-tile,5,382,400-cell solve completes absolute1350s/local15000. Both
original audits pass; all86,720 artificial-bank-face cells remain exactly dry.
Maximum depth4.553027m, speed6.913833m/s, volume3,015,609.063m3, maximum per-step
conservation residual1.707900e-8m3. Total outflow80.573710m3/s still exceeds
inflow45.306955m3/s: **not settled**, not promoted into the ordinary scene.

- `tmp/control-ablation-1350s-state-v1-20260917.json`, SHA256
  `e2d7d27aa129c5d0049fe8f71adfedb1c3e810e2acf0f09dff1b6736f2c22250`.
- `tmp/control-ablation-1350s-banks-v1-20260917.json`, SHA256
  `c340df0e5f2ed00c633d679421a61d05a890f75a2ef0d801f0c04afc4ac85130`.

Next1400s/local16000 requires both audits. Continue the full reconstruction,
coupled nonlinear physics,30FPS, SM5/regression/source closure, later rivers,
crew and release queue. Troublemaker is only a rapid within South Fork.
