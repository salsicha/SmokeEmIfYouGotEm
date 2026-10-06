# Complete frame profiling and exact crest-history lookup — September 14

Profiler shutdown correction verified; build14058 TERMINAL exit0,
289.12s, existing D6 damping warnings retained. All five native checks15637 pass:
CrestHistory, ExactCoordinateMap, ShorelineCrestTargetCache, ShorelineFineCrest,
PlayableCrestReconstruction. History compares694534vertices over36frames,
including25dense calls and original-map duplicate/crop/reset/boundary/alpha rules.
Actual paired gameplay3138 TERMINAL exit0. Candidate timing benefit was too weak
and order-dependent; original TMap history is restored as the normal default.
Restoration build66527 TERMINAL exit0,265.11s. Enhanced four-path native checks
64548 TERMINAL exit0: all five tests pass,0.739602s total test duration.
Fresh final-build paired gameplay99144 TERMINAL exit0 with all bytes exact.
Previous goal turn made progress through isolated scalar-gradient controls and
a separate full requested replay, not a playable physics promotion.

## Profile completion is owned by the profiler

The earlier capture exited at151frames before its300frame CSV finalized, leaving
zero bytes. `profile_south_fork_current_map.ps1` now uses the engine's existing
`-ExitAfterCsvProfiling`, removes the competing timed screenshot exit, and rejects
an empty/missing CSV even when the process exits0. PowerShell AST parses cleanly.
The existing full footer/frame parser remains required; nonempty alone is not
performance acceptance. The native performance-director branch is unchanged.

Actual verification used a direct engine invocation WITHOUT that script's cook
suspension. All original jobs stayed running; this is explicitly shared load.
Normal South Fork full-descent/reviewstation8330, ephemeral player profile,
Development/D3D12/WindowsEditor,1280x720, raytracing0, target30FPS.
Session44495 TERMINAL exit0 and actual profiler-owned shutdown. CSV630261bytes,
300 complete samples, valid final header/metadata, SHA
`9cf94a6de6d56d8935c568447b4e6c772b2b3bae8c25e11b243d054b25615c8f`.
Strict audit passes `tmp/south-fork-frame-complete-profile-audit-v1-20260914.json`.
Samples100–250: mean111.290488ms, p95137.2469ms,8.985494FPS. FAIL30FPS;
this shared-load diagnostic does not replace the prior isolated benchmark.
Water Tick73.923658ms, Refresh32.426393ms, CartesianPublish40.115164ms,
CrestUpdate29.074370ms, CrestSelection14.709819ms. Nested/inclusive scopes:
do NOT sum these or overlapping CPU/GPU thread timings.

## Retain multiple actual updates in one frame

Detailed-stage profile88589 TERMINAL exit0 with300frames. Existing stage parser
rejects repeated cartesian_publish atframe250; it is not a missing-data pass.
New `unreal/Scripts/audit_crest_history_profile.py` preserves every call and
reports both per-call and per-frame sums within the SAME scope.4parser tests
pass, including repeated calls, missing frames and equality/order failures.
No frozen physics audit script was modified.

`tmp/south-fork-crest-stage-calls-v1-20260914.json` covers152crest calls across
all151requested frames100–250, including BOTH frame250 calls. Mean per-frame
crest total28.500823ms, selection17.294156ms, vertices/history5.811948ms,
normals2.337648ms. Log SHA
`513c1cd1b0121d12b4f18bf87ab474980d5a6f203e77c87143f17429fe484b98`.

## Exact-coordinate history candidate

The history lookup still used the engine general-purpose coordinate CRC while
profile memos already use the project's exact two-word coordinate hash. The
candidate reuses `TRaftSimCoordinateMap<int32>` for history ownership, retaining
complete double coordinates, exact equality, duplicate last-writer behavior,
all targets/alpha arithmetic, lookup lifetime and dense-history behavior.
No source or midpoint is removed; no cache quantization or stale profile values.

`TRaftSimCrestHistory` is parameterized only by map type. Both instantiations
are retained for `-RaftSimCrestHistoryHashAudit`: on the same actual incoming
vertices and independent matching prior histories, alternate call order, compare
ALL vertex bytes and correction values, and report both timings. Its reference
map is empty/unallocated in ordinary gameplay. The normal alias now uses the
original TMap; `FRaftSimFastCrestHistory` is diagnostic only. The enhanced native
history test compares both dense/mapped paths of BOTH map types with the serial
reference, including complete vertex bytes.

### Paired result: do not promote the hash candidate

`tmp/south-fork-crest-history-hash-paired-v1-20260914.json` retains152calls over
151frames100–250 (both frame249 calls),10,232,400 exact vertex visits,1dense call.
Log SHA `35a9e5104b38ee64bb6e45958a4c95db6154bfca306851519898046826a38da8`.
Fast mean2.966682ms versus legacy3.068552ms; paired mean benefit0.101870ms.
Legacy-first76calls show0.204809ms mean benefit; fast-first76 show−0.001070ms.
Per-frame p95 worsens from5.528301ms legacy to6.073900ms fast. This is not a
reliable speed win and does not justify changing the ordinary gameplay default.

Final-build repeat `tmp/south-fork-crest-history-hash-paired-v2-20260914.json`
retains152calls over151frames100–250, both frame247 calls,10,233,501 exact
vertex visits and1dense call. Log SHA
`6de64d8f2c981410d6045a91ba268e6cf317c7180454c1714af2860cb580c65d`.
Mean benefit falls to0.045278ms, median0.0083985ms; fast-first mean−0.016446ms.
Per-frame p95 again worsens:6.816700ms fast versus6.108899ms legacy.
This supports retaining the original default, not a performance success.
Its CSV has300 complete samples and passes the strict footer/column audit;
8.207918FPS with the dual-history diagnostic enabled is NOT an ordinary-game
benchmark. CSV SHA
`2cd5af1a3ae71c8a0ad6d1b81a2ec5b5e89d3d56c5c473a6ad311862c75a1df6`.
Budget/CSV/crest-parser regression suite:14tests PASS0.91s.

Experimental ordinary gameplay94733 TERMINAL exit0 before restoration. Actual
001 screenshot and decoded1s frame inspected: terrain/boulders visible, but
broad smeared froth and sheetlike crests still FAIL visual acceptance. Video
`RaftSim_20260914-035907.mp4`:49source frames over6.426s,193encoded frames fully
decoded. Encoder cadence is NOT game FPS. Fixed analysis ROIs are not calibrated
to this shore camera. This capture is from the experimental build, not the
restored final default; no new appearance or performance success is claimed.

Final ordinary gameplay30178 TERMINAL exit0 with the restored original default
and NO hash diagnostic enabled. Actual001 screenshot and decoded1s frame viewed:
terrain/rocks and water are integrated, but broad smeared foam and sheetlike
crests remain visually unaccepted. `RaftSim_20260914-040940.mp4` contains46source
frames over6.482s; all194encoded frames decoded. No new FPS claim from encoding,
no matched-camera before/after shape improvement claim, no final CSV requested.
Capture label: `south-fork-history-original-normal-v2-20260914`.

Physics41566 remains separate and unqualified, last accepted0.258333344s,
speed7.253570m/s. All417 original and422 candidate script hashes rechecked,
unchanged. Main original59896 last0.610619973s, speed36.624925m/s, below its
earlier peak but not full-history acceptance. Observer97152 last saved accepted
state0.407489756s, speed21.523404m/s. Cook8316s;
COMPLETE8300/local6000 passes BOTH independent audits but remains unsettled.
Next COMPLETE8400/local8000 needs BOTH audits. Normal terrain,
rapid/wave/froth/contact/30FPS, crew, all later rivers, release and commit remain
open. No reference-video access success or scene-realism acceptance this turn.
