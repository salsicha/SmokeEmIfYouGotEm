# Troublemaker: discharge-based inferred bed candidate

September27,2026. Physical candidate under test, not a visible delivered change
or reconstruction acceptance. Normal playable v5 remains untouched.

## Why this changes the next action

The completed v5 crest check found four persistent waves with zero modeled
spilling, while the actual submitted mesh approximated its crest target within
8.25mm at the sampled instant. More tessellation is not the supported first fix.
The full-river v2 bed builder explicitly protects Troublemaker's registered
rectangle, retaining its old shore-distance depth prior after the earlier
uncalibrated shelf/plunge ablation. Neither v2 nor the450s v5 field update
replaces that local inferred bathymetry.

At the four diagnosed hydraulic XY locations, route progress is approximately
8310,8330,8330 and8359m. The v2 design's UNBIASED normal depth is0.448..0.690m;
pool weights are0..0.001874. Its fitted centreline depths reach the0.25m lower
clip here. This candidate deliberately does not use that simulated bias or
claim the unsteady flow used to fit it was settled.

## Source-preserving construction

`physics/scripts/prepare_troublemaker_conveyance_bed.py` extends the existing
strip-conveyance depth inference into the registered rapid. The authored
45.3069545472m3/s scenario flow, captured surface slope, effective width,
Manning n0.035, bank-shape length and2.2m pool prior come from the existing
full-river design. The flight-time discharge remains unknown. These assumptions
are NOT surveyed underwater shape or a calibrated reconstruction of the hole.

Only authority2 vertices change. All captured ground/rock, inferred rock
flanks, source surface, XY, connectivity, return indices and the registered
seam boundary remain exact. A30m smooth taper retains the boundary; no original
source file is overwritten. The same registered-triangle sampler validates
both mesh and hydraulic input. New tests reject unknown authority, invalid
designs, extrapolation and above-surface editable beds.

Candidate: `tmp/troublemaker-conveyance-bed-v1-20260927`.
Mesh SHA-256: `3fd9eef54ff243c09fe7c33aa69129a3496387d7d603012a543457fb1cf14542`.
Parent mesh SHA-256: `8edf8a7fbfb675a22ac6736db600a3300f018f1c9037b1c0674bc1c376cfcca7`.
Changed62,985 inferred vertices; height change min/median/max
-0.425195/+0.672117/+1.941739m. The amount of change is substantial: a fresh
flow solve and matching terrain/collision are mandatory, not optional.

The rock union is retained exactly. This does not resolve the separate
interpreted rock-envelope versus hydraulic-roof uncertainty. The new
`--geometry` argument in `prepare_south_fork_discharge_bed_cook.py` permits an
explicit registered revision while retaining the existing default unchanged.
The normal v2 coarse terrain is then applied everywhere it previously owned.

## Completed preparation and tests

Union preparation `tmp/troublemaker-conveyance-union-v1-20260927` checks all841
cores/5,382,400 cells and retains masks, captured stages and physical endpoint
faces. Its16,383 changed cells are relative to pre-union geometry, NOT v5.

The independent [comparison to current v2](runtime450-evidence/conveyance-input-comparison.json)
instead finds16,064 changed hydraulic cells in11 cores, all inside the
registered rapid. Every grid, timestep, roughness and physical boundary is
identical across all841 packages. This is source/input parity, not settled
hydraulics or actual native collision qualification.

Full-river fresh input:
`tmp/troublemaker-conveyance-full-input-v1-20260927/full/manifest.json`.
SHA-256: `b9c8cabadff5f72b396b389cd77b94193a530138d07a9dc1c5c5cbd96d26a0b9`.
Preparation session3094 completed with exit0. No old-bed evolved state was
transferred. Initial water uses the captured surface and inferred conveyance
velocity, so initial transients are expected and must not be called improvement.

Six new unit tests pass; the combined new/terrain-revision/rock-union suite
passes46 in3.48s. Fresh test directory:
`tmp/troublemaker-conveyance-tests-20260927`. Tests are not visual acceptance.

## Live bounded solve: continue the same job

Native solver PID33592, helper session30490, start17:43:36.9708347Z onSeptember27.
Process receipt: `tmp/troublemaker-conveyance-process-v1-20260927.json`.
Output: `tmp/troublemaker-conveyance-full150-v1-20260927`.
Wrapper: `tmp/cook-troublemaker-conveyance-v1-20260927.ps1`.
Qualified executable SHA-256:
`458a1fcd3f2f12391012032398d29a4b2eadb792df2e9ee09b88dff263abc8e4`.
Bounded3000 steps at0.05s,150s target, snapshots at0/75/150s,8 offline lanes.
No competing engine/build/solver was present at guarded launch. Do not start
another cook while this one is live. The wrapper performs a final state audit
after successful native completion, but this does not replace bank/storage or
playable checks.

Independent initial snapshot checks pass5,382,400 finite nonnegative cells,
max depth2.671577m and speed6m/s. All86,720 artificial-bank cells are exactly
dry. Reports: `tmp/troublemaker-conveyance-initial-state-v1-20260927.json` and
`tmp/troublemaker-conveyance-initial-banks-v1-20260927.json`. Initial outflow
exceeds inflow: no initial equilibrium claim. The same live process reached
step2040/102s without a logged safety failure; this is not final validation.

## Matching runtime and native-ground preparation

Preparation code/tests and input comparison are committed locally as
`1e734f16c`; nothing was pushed. The normal scene/package remains v5.

The existing source-union packet builder completed in session67946:
`tmp/troublemaker-conveyance-source-packets-v1-20260927/manifest.json`, SHA-256
`3f07dbcef054ca7a1706cf3155000babd0a3f4d8b8b7747ef006507b547ba479`.
All799 source packets verify;15 packets/124,123 samples differ from the retained
pre-union source. Captured masks and stages remain exact. These counts are NOT
comparisons to current v5. Use this explicit `--source-packets` argument with
the discharge runtime exporter; its default references the older rapid bed.
The exporter now verifies the retained hydraulic manifest hash, exact terrain
union identity and coordinate frame before creating any output directory.
All13 packet-identity/composite-terrain regressions pass. Real paired old and
new inputs pass; old packets with new geometry are explicitly rejected. The
existing per-cell atlas/packet equality check remains mandatory afterward.

Blender export session98248 exits0. Exact403,200 vertices/803,842 triangles:
`unreal/SourceArt/RaftSim/TroublemakerConveyance20260927/manifest.json`.
FBX SHA-256 `8c1a0367e54863d7dcf3facbe4f43c28c982fdbccc33d76d70bfbbec0013b3cb`;
source mesh SHA-256 matches the candidate above. This is not native validation.

`prepare_troublemaker_bed_native_check.py` prepares the immediate installed
ablated mesh comparison, not the older pre-ablation ancestor used by union
lineage. Installed ground package remains SHA-256
`367c0324203b9dcc31b5a73c6082d10b04d481c5aa9c68c694273983ed758053`.
Preflight `tmp/troublemaker-conveyance-native-preflight-v1-20260927.json`, SHA-256
`3acd7a0dd09fa03adccce130610d29c696cb7b78e433ffa2470428e9473b41a0`,
covers62,985 changed vertices and129,242 changed triangle centroids.
New/preparation/source-preservation suite:18 pass; native-comparison suite:16
pass. Neither is actual engine verification.

The deferred native-check wrapper is LIVE as session77718:
`tmp/check-conveyance-ground-after-cook-20260927.ps1`.
It waits for the SAME PID33592 (exact UTC identity), checks final artificial
banks, refuses another live engine/build/solver, then runs
`unreal/Scripts/verify_troublemaker_conveyance_ground.py`. It may save only a
new verified candidate mesh. Normal actor binding and all saved scene packages
must remain unchanged. Its ground-only traces intentionally ignore rocks;
complete rock-union/runtime/playable checks remain mandatory. Expected receipt:
`tmp/troublemaker-conveyance-ground-native-v1-20260927.json`; native PID receipt
will be the adjacent `-process.json`. Do not launch a duplicate checker.
The first wrapper attempt stopped before launch because PowerShell parsed a
UTC literal into local DateTime; explicit DateTimeOffset UTC comparison fixed
the guard after independently confirming the original cook identity.

At the75s snapshot, independent state and bank checks pass, with all86,720
artificial-bank cells exactly dry. Maximum depth2.913112m; maximum speed8.208481m/s.
Reports: `tmp/troublemaker-conveyance75-state-v1-20260927.json` and
`tmp/troublemaker-conveyance75-banks-v1-20260927.json`. The signed-transport
analysis is `tmp/troublemaker-conveyance75-analysis-v1-20260927/report.json`.
It reports96.64% wet coverage of the full captured mask, but local bins near
8380..8465m have roughly0.5m negative surface deviations and some reduced wet
coverage. Flight-time discharge is unknown, so this alone neither proves a
physical failure nor justifies promotion. Inspect the final local state and
regional storage before making a playable candidate. Do not apply the generated
simulated bias as measured bathymetry or call this state settled.

## Required follow-through

1. The150s solve, native ground check and runtime export are now complete; do
   not duplicate them. First repair the newly quantified installed-envelope
   versus retained-roof hydraulic mismatch below. Preserve these trial outputs.
   Do not compare fresh150s and evolved baselines as a bed-only experiment.
2. Inspect actual local drop/jump/recirculation behavior and bed continuity;
   numerical safety alone cannot justify promotion. No lower Froude/shoreline
   gates, decorative extra foam sheets or broken alternative solver.
3. If physically defensible, use this SAME registered mesh for rendered ground
   and collision, resample matching runtime packets, then incrementally install
   the normal FullReach candidate with a versioned bundle and rebuild. Inspect
   real motion, shoreline, support/collision consistency and cost; do not leave
   the candidate as the final offline-only deliverable.
4. South Fork remains first unfinished, with20FPS/p95<=50ms and no frame>100ms,
   convincing single-surface breaking water and captured-reference fidelity
   still required. All later rivers and the wider goal remain open.

## Completed150s solve and native ground check

This section supersedes the live-cook status above. Native PID33592 terminated
after writing `completed.json` with completed=true and a complete step3000
snapshot at149.99999999999986s (wall1500.396s). Stderr is empty. Its PowerShell
observer session30490 exited1 because `.ExitCode` was null after observation;
do NOT report a known native exit0 or re-run the solve. The old process receipt
therefore remains stale with completed=false. Independent final-state audit
was run directly against the finished files and passed, followed by storage
and station analysis (session44747 exit0).

Final state: `tmp/troublemaker-conveyance150-state-v1-20260927.json`.
Final banks: `tmp/troublemaker-conveyance150-banks-v1-20260927.json`.
Final storage: `tmp/troublemaker-conveyance150-storage-v1-20260927.json`.
Station analysis: `tmp/troublemaker-conveyance150-analysis-v1-20260927/report.json`.
All5,382,400 cells pass finite/nonnegative checks; maximum depth2.904861m,
speed8.208481m/s; all86,720 artificial-bank cells remain exactly dry.
Final h/u/v SHA-256 respectively:
`06f355a22e492b1f0aa03dbcd7787f2b2123375c1a9f7e7fb1543cd92e755fdd`,
`1df9689fb27a6bbe47b945768117d08ad9b49daed28708a3727e55f5e1bf431f`,
`d1027b13d923a4c39729350bb00bf9712c940bff7c8d4dcda342325466468160`.

Full storage change1184.655054m3 closes to integrated exterior flow within
4.53e-11m3. This is conservation, NOT equilibrium. Final75s net filling
11.220582m3/s hides regional gains185.556836 and losses174.336255m3/s.
The8-9km band changes from -0.496936m3/s over0..75s to -14.198846m3/s over
75..150s. Whole captured-mask wet coverage96.5898%; several8430..8465m bins
remain near -0.59m surface deviation with reduced wet coverage. Source-time
discharge is unknown; do not calibrate inferred bathymetry from these evolving
offsets or call the hole physically accepted.

The older v2 input explicitly seeds from v1 `frame_012000`; even its150s
snapshot is not an identically initialized bed-only control. No paired-causal
improvement claim is justified. A coupled playable trial still requires the
candidate's exact ground, runtime packets and conservative quality gates.

Deferred checker session77718 and Unreal PID2284 completed with exit0. The
ground-only check compares all803,842 native directed triangles, preserves
all unmodified corners and XY/winding bit-exactly, and verifies all129,242
changed-triangle collision probes with maximum error0.001671582cm. All1,334
protected scene packages remain unchanged. Only the new candidate mesh is
saved. Package SHA-256 `d135f429a065e1d9d50391beaed0f20fc0b109fbb7a6e32d28c4b44b93062c86`;
native collision-source SHA-256 `d6a5f18ffe07c881b6dcbe40201cafa863b93d78b6f086e86c78effabdae743a`.
No engine motion/FPS or rock-union acceptance follows from this ground-only
NullRHI check. Import warnings remain (memory estimate, smoothing groups and
deprecated trace enum). See the [native receipt](runtime450-evidence/conveyance-native-ground.json).
Preparation/export guard commit is `aecf70b3b`.

Runtime export session39935 exits0: `tmp/troublemaker-conveyance-runtime150-v1-20260927`.
All799 packets/841 atlas tiles verify42,185,039 exact bed-intersection samples.
Atlas hash `3440032389ba92bdf0be8a61ae3936ee492f4d2b93fa65aa63b505cb17ec4f28`;
streaming hash `f053b3ba5554b421bb1bcdd02560e7dbc004c386b6345abd246a648331a73a82`.
[Export receipt](runtime450-evidence/conveyance-export.json). Do NOT bind this
export as a consistent normal-scene update until the mismatch below is fixed.

## Newly quantified promotion failure: current rock envelope not cooked

The installed September26 rock envelope is explicitly inferred and lower than
the old source-return roof. The source-union cook still uses the old roof.
`tmp/audit-conveyance-envelope-parity-20260927.py` independently samples the
candidate registered ground plus the CURRENT envelope, replacing the old roof
before taking a maximum. All319 hydraulic sample locations under the old roof
footprint match the old-roof cook exactly, but284 differ by more than1mm from
the rendered/collision envelope. Maximum mismatch1.546649m;10 of17 currently
wet samples differ, by up to0.067565m. Affected cores are0629 and0631.
See the [failed parity receipt](runtime450-evidence/conveyance-envelope-parity.json).
This is a quantified coupling problem, not proof that the envelope is surveyed
or that a1m raster resolves every rock face. Initial audit stopped on a missing
top-level origin key; using the hash-verified geometry manifest frame completed
the check. No geometry or fields were altered.
The current envelope mesh still matches its install hash `7071bab3248cc49f09cb1962eb527b1b13a9c2fefaaec2761dfc920926526f57`.
Its actor hash is now `0194ca78355f8488fd5166887aa8586f0a48d352ec2ecd8af475bab3c4d35ecc`,
matching the later September27 successful native installed-union receipt
`tmp/ignored-ground-installed-union-v3-20260927.json` (SHA-256
`53b11d23b48b0cf5f323b216cbf769e44c8a9a959a85066f08df998086730469`).
The older September26 installation actor hash is stale; its mismatch is not
evidence that the envelope disappeared, and no actor was reverted.

Next: introduce an explicit inferred-envelope union contract and resample the
same installed rock/registered-bed surface into hydraulic cores and packets,
preserving all original source returns. Do not relax the existing source-exact
cap validator, relabel the lowered envelope as measured, restore the old visual
spikes just for parity, or keep the old roof via a second maximum. Recompute
changed-bed flow and verify the coupled geometry before normal playable
installation and rebuilding. The ground candidate itself has now passed its
native source/collision checks; do not repeat that unchanged stage.
