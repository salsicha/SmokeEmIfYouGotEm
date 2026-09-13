# Normal South Fork integration — September 12, 14:51 UTC

Latest September12 18:43UTC: aligned-mesh normal game capture inspected; crest
v9 passes2cm at1.428008269cm. Guided segment still fails97.40/120m and10.10/5m
route deviation, but all ground queries succeed with numerical-zero sampled
penetration and one visible Cartesian carrier. Progress snapshot also needs
timing diagnosis. [Evidence/next work](normal-river-contact-and-source.md).
Map/source alignment is saved; traversal, froth/scenery and performance remain open.

Latest September 12 18:36 UTC: [streamed contact and actual rapid-source mismatch fixed](normal-river-contact-and-source.md).
Full-river mesh now uses the same8bdf geometry revision as hydraulics, replacing
the stale4b0d actor reference. 14,257 placed source probes pass and reload verifies;
one actor reference changed, original map/actor backed up, other packages intact.
New map SHA3d52dd5bdfdf4fb9a3e0c57fa728e437cef16ccc0bf827892458e55ee8eade77.
Ground cache fix passes34 native tests; prior-mesh normal guided segment clears
ground and reaches120m/90.68s, but route tolerance still fails. Post-swap actual
capture/guided test next; full scene, froth motion and performance unaccepted.

Latest September 12 18:15 UTC: serial packing is rebuilt, 33 native/D3D12
tests pass; same-binary serial capture 21.4291 FPS still fails 60 FPS.
The actual rapid log confirms one grounded support after movement, not a
proven spawn fault. A new normal-map, crew-only guided segment test is being
built because the old isolated survey test does not cover this map/mesh/axis.
[Current evidence](normal-water-performance.md). Complete 1400 s offline
flow passes state and dry banks but is unsettled; runtime remains audited 600 s.

Latest September 12 18:01 UTC: normal-map crest v8 passes 2 cm (1.4281 cm),
and 33 native/D3D12 tests pass. Actual screenshot inspected: whitewater is
visible, but bare scenery, abrupt rock cuts and apparent raft contact remain.
No natural-traversal or convincing foam-motion acceptance. Parallel packing
benchmark regressed; source default restored to serial pending rebuild.
[Same-frame timing and geometry evidence](normal-water-performance.md).
Menu/catalog and old-save migration verified: no Troublemaker menu entry.

Latest September 12 17:32 UTC: exact batch-local crest query reuse passes
32 native/D3D12 tests and actual normal-map crest error 1.4186 cm. Short
isolated capture 22.9379 FPS still fails 60 FPS; scenery, moving froth,
raft/rock contact and natural traversal remain unaccepted. No map/profile/
source/material changes. [Current evidence](normal-water-performance.md).
Troublemaker has no menu entry. The 1300 s source cook failed an artificial
bank; a source-exact extension and verified replacement continue separately.
Normal river data remains the audited 600 s atlas, with no new promotion.

Latest September 12 17:12 UTC: compact CPU shoreline now carries only actual
bank edges into fine refinement, with all original grid vertices retained.
32 native/D3D12 tests pass including old/compact exact fine-corner attributes
and identical raster membership. Actual normal-map crest error 1.4210 cm passes
the unchanged 2 cm gate. [Current evidence](normal-water-performance.md).
Separate isolated short benchmark reaches 21.8123 FPS (45.8457 ms mean), still
not accepted playable performance. Scenery, froth motion and raft/rock contact
remain open. No map/profile/source/material change; Troublemaker stays in South
Fork and does not appear as a menu scenario.

Latest September 12 16:59 UTC: actual normal-map parallel source sampling matches
serial results exactly across 50,625 vertices; native/D3D12 32 tests pass and
crest target is within 1.4206 cm. [Evidence](normal-water-performance.md).
Same-binary full-frame mean with cook paused is 53.1846 ms (18.8024 FPS), compared
with 92.7781 ms while cooking. Performance remains unaccepted. Inspected actual
capture has terrain, breaking crests and froth but unfinished scenery and
unverified raft/rock contact. No map/profile/material modifications this increment;
no separate Troublemaker scenario. The 1200 s flow failed a bank check and was
expanded source-exactly; normal runtime is still the audited 600 s atlas.

Latest September12 16:32UTC:
[normal-river performance and crest audit](normal-water-performance.md).
Shared fine crests now modify this actual full-river Cartesian single surface;
current crest-target error1.4293cm passes the unchanged2cm gate, without moving
original source vertices.32 native/D3D12 regressions pass. Parallel selection
preserves serial topology; compact uploads preserve every rendered corner.
Separate full-frame mean107.45→95.36ms andp95131.09→115.16ms remain far above
the60FPS budget. Source/CPU cost, fully shaded motion, scenery and traversal
are still unaccepted. No new map/profile/source/material edits in this increment.

## Current result: normal launch works; performance and realism unaccepted

The normal South Fork scene now launches on its reconstructed terrain and real
Cartesian water, including the retained Troublemaker rapid. No separate rapid
scenario exists. The saved map plus external packages, source-based route,
session contracts and checkpoint history are integrated. This is meaningful
playable-entry progress, **not completion of the river or broader goal**.

The carrier-startup build exits0 (225.17s). Final native/D3D12 report
`unreal/Saved/RaftSimValidation/south-fork-normal-carrier-final-v1-20260912/index.json`
has33 successes, zero warnings/failures/unrun. Actual-game crew/scoring/save
report `south-fork-normal-carrier-game-v1-20260912/index.json` has two successes,
zero warnings/failures/unrun, process exit0. Installed experimental-plugin
Python startup errors remain distinct from passing automation assertions.

`verify_south_fork_normal_assembly.py` explicitly modifies/sets the two root
components' serialized location/rotation, then switches maps and reloads from
disk. Verified launch is(-11242.795117,2400.000000,6081.207886)cm, yaw180deg.
All other external packages remain byte-identical to the assembly report.
Reload report `south-fork-normal-reload-v1-20260912.json`, SHA256
`d3e8ddada1027ac1215fe1239bab7c9c013001ea777fe506903eb942de6dd342`.
Current map SHA256
`09dcd41fd37013cbb2fc0d4e94de952ca45731937b517aad0e518d8922afec2d`.
The profile SHA256 remains
`181d1e570485d1ec3139aec4e1d9b56d0a420fd107ce5a94218368324207f5b1`.
Do not rerun the original assembler: its preflight deliberately expects the
old map. Future corrections must verify the current map/external package state.

Actual D3D12 normal-game observations (1280x720, ephemeral profiles):

- Corrected put-in:12 frames
  `unreal/Saved/Screenshots/south-fork-normal-put-in-v2-20260912_*.png` and
  `unreal/Saved/VideoCaptures/RaftSim_20260912-074638.mp4`. Raft/camera move on
  the correctly aligned visible river. No authored-water initialization error.
- Troublemaker inside the same normal map:12 frames
  `unreal/Saved/Screenshots/south-fork-normal-troublemaker-v1-20260912_*.png` and
  `unreal/Saved/VideoCaptures/RaftSim_20260912-074741.mp4`. An ephemeral8330m
  checkpoint start selects the actual source packet; normal production crest/
  material configuration is unchanged (no breaking-review opt-in). Captures
  show flowing water/froth, raft movement and the retained rapid terrain.
  Capture-log fields named raft_station/lateral are hydraulic east/north in
  this mode, NOT scoring chainage; run manager uses the separate route axis.
- **Performance fails**: rapid recording72 source frames/9.795s (~7.35fps),
  including capture overhead and concurrent cook. First surface refresh86.537ms
  for50,625 vertices,1m spacing,analysis stride1; first solver step11.37ms.
  These are observations, not isolated sustained cost measurements. Do not
  weaken fidelity/gates to label this accepted. Profile/cache the actual
  presentation pipeline and coupled solver, then repeat unrecorded frame-time
  and motion checks. Confirm spatial breaking/foam authority at the rapid,
  not merely the first startup log from the put-in.
- Ground material and captured geometry are present, but vegetation/context
  appearance is sparse and froth realism remains unaccepted. An actual video
  exists; no final reference-based motion/photorealistic acceptance is claimed.

Current cook remains session1541/PID31752, same immutable executable/input:
at14:51UTC local6160/908s. Latest completed audited snapshot remains800s;
next1000s is local8000. No restart. Runtime uses audited600s transient data;
self-contained production data staging, settled-flow acceptance, full traversal,
shore/support/boulder parity, performance and all later river/crew/release work
remain open. No final commit or goal completion.

## September 12, 14:29 UTC runtime and assembly checkpoint

### 14:42 UTC saved terrain; actual launch defects under repair

The normal map was saved successfully by assembly executionV4 at14:36UTC.
`unreal/Saved/RaftSimValidation/south-fork-normal-assembly-v1-20260912.json`
SHA256 `38f92c394eb0dd004b5c4fbfe4244add22999a32569c9a8ce847fbe73c4c2f0c`
records455 saved actors,443 source terrain placements and10,210 combined
collision checks. Maximum height error0.00386556cm (unchanged0.1cm gate).
Terrain source assets/materials and the real profile are unchanged. Original
map plus308 replaced scene actors and remaining original external packages
are recoverable from
`unreal/Saved/RaftSimValidation/south-fork-pre-reconstruction-20260912.zip`,
SHA256 `79f67b1593090ba0de0bd96e75c3b48563375799edbec4f1fe80198b5c213492`.
Map SHA256 at this assembly is
`f3660a9705ede3510033c0be4dbc48eb30c3ef11b11a99ef9843ea5fa2fed26e`;
external actor packages are also essential parts of its state.

Actual normal-game captureV1 **fails**, despite the saved geometry passing.
The raft/root transform did not serialize its in-memory move, leaving it in
the old frame; new fail-closed water correctly refused that dry location.
The placed carrier also began before the raft configured the bridge and
cached a non-Cartesian grid. That capture is NOT acceptance evidence:
`south-fork-normal-put-in-v1-20260912_*.png` and
`RaftSim_20260912-073729.mp4` show this failure.

Fixes in progress: explicitly mark/edit root-component transform properties,
use named Python Rotator fields, and reload from disk to check position/yaw;
defer carrier initialization until a real live water field exists. The new
verification script is `unreal/Scripts/verify_south_fork_normal_assembly.py`.
Do not claim playable integration complete until corrected launch succeeds.

Historical execution issues:V1 checked a nonexistent public sample.valid
property and saved nothing;V2 exhausted commit/video memory compiling all
obsolete water distance fields alongside new terrain, also saving nothing.
V3 used bounded retirement and NullRHI, reached collision validation but
caught a rapid probe-frame error: old export probes precede Y reflection.
V4 uses the verified reflected geographic probes, preserving the same
collision threshold, and saves successfully. Assembly NullRHI is a geometry/
collision operation only; normal-game D3D12 testing remains required.

Compiled normal-launch changes (`south-fork-normal-launch-build-v1-20260912.log`,
281.07 s, exit0). Native/D3D12 report
`unreal/Saved/RaftSimValidation/south-fork-normal-launch-v1-20260912/index.json`
has33 successes, zero warnings/failures/unrun. This extends the prior32-pass
checkpoint suite and two actual-game crew/scoring/save passes. The latest
gameplay pair must be repeated after the scene is saved.

- Cartesian launches and section restores now share geographic region
  selection, manifest roughness/extent and transactional wet-point validation.
  Dry/invalid destinations preserve the existing water state and raft position.
  A failed authored-river load disables the raft, never substitutes a flat tank.
- Save schema4 retains exact previous coordinate-frame checkpoint/ghost/time/
  distance records in `HistoricalRouteProgress`, while retaining career awards
  and aggregates. Active checkpoints/ghosts cannot cross coordinate frames or
  unrelated river levels. In-memory serialization/migration is tested; the
  user's actual save is not written by verification.
- Explicit `bEnableLiveSharedBreakingRelief` activates the common spatial
  carrier/support relief without review flags or a retired rapid-map identity.
  It does not enable the old rapid-origin-only refinement grid. Actual froth,
  motion and full-frame cost remain unaccepted.
- The menu catalog now matches the reconstructed source contracts: playable
  start120m, finish33280m inside33334.146m source route. Provisional career
  boundaries use guide mileage rather than scaling the old49km frame. Their
  landmark georeferencing is explicitly unaccepted. See
  `physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/playable_route/session_contracts.json`.
  Troublemaker remains part of South Fork and has no menu scenario.

Current exact input manifest is
`tmp/south-fork-full-scene-assembly-600s-v4-20260912.json`, SHA256
`c141cf60334eae244c0727ef0275cb6de44e4801880aad5c94d0a56bf672aba8`.
Five Python preflight rejection tests pass, including a finish outside the
captured route. `unreal/Scripts/assemble_south_fork_full_reach.py` revalidates
these inputs, archives the exact original map/profile/external packages, loads
all partition descriptors, replaces only the308 obsolete terrain/water/rock/
dressing/reflection actors and checks combined terrain collision before saving.
At this checkpoint execution is in progress; **do not infer a saved map until
the successful assembly report and post-save runtime checks exist**.

The unchanged live cook reached the completed800s snapshot (local4000).
Independent state audit passes, and all86,720 artificial bank-face cells remain
exactly dry. Outlet58.0064 versus inlet45.3070 m3/s is not settled acceptance.
Reports `tmp/south-fork-expanded-800s-state-v1-20260912.json` and
`tmp/south-fork-expanded-800s-banks-v1-20260912.json`. Session1541/PID31752 is
still the same cook; no restart or live-input mutation was performed.

## Historical preflight checkpoint

Status: exact inputs joined and runtime-tested; **normal map not yet replaced**.
This is progress toward the existing South Fork scenario, not an alternate rapid
scenario, visual acceptance, settled-flow acceptance or a completed delivery.

## Actual saved map inventory

`unreal/Scripts/audit_south_fork_full_reach_integration.py` reads the normal map
without saving assets or profiles. Loaded actors alone are incomplete: there
are135 loaded actors but318 saved World Partition descriptors, including161
static meshes,113 legacy rock/contact actors,21 dressing actors and lighting/
launch infrastructure. All318 external actor package hashes are recorded.
The stable numeric inventory is
`unreal/Saved/RaftSimValidation/south-fork-normal-integration-inventory-v3-20260912.json`,
SHA256 `9b38702ff0293b2c1268ec28ce0b518f8e20828adc3272c060843d082f7b2c04`.
V3 editor execution exits0 without Python exceptions. Earlier inventory files
remain historical evidence; V1 did not include unloaded terrain descriptors.

The real config still uses `full_hydraulics/full_reach_transit_seed`, the old
production corridor coordinate map and old streaming manifest. The surface
and run manager are spawned at runtime rather than placed in this map. Old
terrain, bank dressing, bridge, reflection captures and contact proxies cannot
be assumed to align with the reconstructed UTM frame. Preserve/reposition or
replace their exact targets as part of the coherent scene operation; do not
delete unrelated assets or infer absence from an unloaded actor.

## Latest runtime state

`tmp/south-fork-runtime-atlas-600s-v1-20260912` exports836 tiles and799 source
packets from the independently audited terminal600s snapshot.41,987,038 bed
intersections are exact. All799 captured bed/mask packets reuse741,172,375
verified bytes; state remains an immutable dependency of the completed cook.

- Atlas SHA256:
  `95aeda87e6578d2854ecb572b7bad25631bdf8c16038b99c6e4ae4b0006303d1`.
- Use `streaming_manifest_verified.json`, SHA256:
  `4212710b844404f5bfe2ab9482799af83b3ba83b33b538943ec0af9d4d9e2051`.
  The initial catalog still needs the region0002 physical-inlet exclusion.
- Independent verified coverage audit SHA256:
  `aff9f06f3001fc3c650a5127f927c9e44f3273bbb38278f5cf683a15d2f6899b`.
  All797 continuous rectangles pass at full224m extent.406,823 original wet
  positions remain covered;3,822 centers shift, maximum102m, minimum raft
  interior margin10m (unchanged minimum8m).

Build `south-fork-atlas-600s-build-20260912.log` succeeds. Engine report
`unreal/Saved/RaftSimValidation/south-fork-atlas-600s-20260912/index.json` has
six successes and zero failures/warnings/unrun, process exit0. The actual
836-tile shared loader matches151,875 dense-reference cells across three
full224m crops and three subsequent live steps bit-exact. Source baseline
checks97,794 modeled cells,54,081 unavailable dry-context cells and zero field
error. Shoreline raster/actor and scenario/progression regressions also pass.
This is still a transient600s hydraulic state, not settled river acceptance.

## Exact scene-assembly manifest

`physics/scripts/prepare_south_fork_scene_assembly.py` joins the verified inputs
into `tmp/south-fork-full-scene-assembly-600s-v3-20260912.json`, SHA256
`66d5ef8c0cb14112364fb2a34e507b1be5de48acb4c673d4df5216ae3c687c22`.
It targets the existing `L_SouthForkAmerican_FullReach` and
`south_fork_full_descent`, never a new Troublemaker scenario.

443 placements include390 exact coarse tiles,51 context tiles, the retained
rapid mesh and its inferred join:9,205,248 triangles. Every placement has an
asset hash, source geometry/export evidence, exact transform and collision
evidence. Every ground actor explicitly overrides the old rapid-local material
with the verified full-frame `MI_SouthForkCompositeGround`. The route and
hydraulic frame must share UTM origin,220m datum and negative world Y; the
atlas must share the source-region hash and datum. All source state arrays
are hash-checked. Four rejection regressions pass for stale normal-map state,
translation/collision mismatch, mixed water datum and unrelated source terrain.

This preflight is **not** the map-writing assembler. The next integration action
must place these assets/runtime into the normal full river and verify the
combined scene, not accumulate another isolated review map. It requires:

1. Source-grounded starts, finish, career section bounds and save migration for
   the33.334146km route. Do not linearly scale the old49km station system or
   preserve bogus named section locations. The existing archived
   `review/named_rapid_station_alignment_review.json` explicitly rejected the
   old5200m Coloma seed; it is not valid reconstruction evidence.
2. Scoped replacement/repositioning of the318 legacy partition actors, with
   recoverable existing-map/package state and no unrelated asset deletion.
   Retain captured rapid vertices and test combined collision, not just each
   imported tile in an isolated tank.
3. Explicit production water/crest configuration, actual two-axis streaming,
   shore/support alignment and one visible water surface. Remove dependence
   on review-map names or retired standalone rapid launch identities.
4. Inspect normal game motion/material/froth and full frame cost; document
   rough edges honestly while improving the playable entry incrementally.
   Runtime data staging and final acceptance remain open.

The normal map/profile and external package hashes remain unchanged. No final
commit has been made. Later river/crew/normalization/release work remains in
the active goal. Current cook is session1541/PID31752, verified at708s/local2160
at13:45UTC, max step mass residual1.328721511e-8m3. Next complete snapshot is800s;
the progress line does not re-audit artificial banks. No process was restarted.
