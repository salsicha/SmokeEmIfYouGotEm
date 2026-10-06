# Physical ground and ordinary water contact — September 14

This changes the playable South Fork contact path, not just an offline control.
The prior goal turn completed Git hygiene; it did not improve the river image.
Full terrain/water realism, 30 FPS, later rivers, crew and release remain open.

## Verified defect and shared correction

An actual submitted water triangle could provide raft buoyancy even where finer
captured rock occluded it. The hydraulic raster and rendered shoreline do not
resolve every source-mesh rock. The new native regression failed against the
original behavior: both the actor's direct query and registered raft provider
reported buried water as wet. An independent complex component trace first
proved that the test rock was above the water.

`FRaftSimGroundSourceRegistry::SampleGround` now owns the existing captured-mesh
and landscape query formerly embedded in the physics bridge. Both solid raft
contact and Cartesian water support call this implementation. It retains tagged
physical mesh precedence, component-bounds traces, overlap-hit handling, landscape
fallback and streaming-aware weak membership. The solid bridge retains its old
solver-bed fallback; water eligibility does not invent physical ground on a miss.

Water support evaluates the actual submitted triangle and its paired completed
detail at all three vertices. Only then does it reject a surface at or below
physical ground. There is no new clearance threshold, depth floor, water lift,
FV state change, terrain alteration or research-solver promotion. Positive
water columns remain supported. Cartesian spray anchors use this same position
and ground test, including the paired detail, instead of anchoring inside rock.

The regression additionally checks a positive **0.01 cm** film, disabled ground
collision, shared spray anchors, the actor/provider path and original clipped
shoreline geometry. This is not proof of exact wetting dynamics or a swept-particle
collision implementation.

## Native and independent real-terrain evidence

- Original test: session 29006, exit 1, exactly the two buried-water assertions
  fail. `unreal/Saved/RaftSimValidation/ground-contact-before-v1-20260914`.
- Correction build: session 76122, exit 0, 247.31 seconds. Two existing unrelated
  double-to-float warnings in `RaftSimD6ChaosMeasuredRunner.cpp` remain.
- Native suite: session 70790, exit 0; **12 passed**, zero failed/warned/not-run.
  `unreal/Saved/RaftSimValidation/ground-contact-after-v1-20260914`. Includes
  streamed ground, visible spray, shoreline, thin water/dry rock, crests,
  completed-frame GPU contact, career catalog and progression migration.
- Python audit/source/frame checks: **22 passed**. Missing ground, buried wet
  support, false dry support and nonfinite/displaced source measurements fail
  the audit. Historical CSVs do not invent a zero ground-query cost.

Ordinary full-reach game session 78424 completed exit 0 at requested station
8330, 1280x720, with an ephemeral profile and no experimental solver switch.
The actual contact export contains **2,020 points**, including **84 below ground**.
All 84 reject support. There are 1,933 supported wet points and three additional
raw-dry points; no unavailable points. Maximum supported carrier-height error
is **4.767661e-5 cm**. The old `raw_dry_points` aggregate now includes ground-dry
support; the new per-probe raw wet flag distinguishes them explicitly.

The independent Python sampler reconstructs the original registered triangles,
not the runtime collision query or coarser raster. All 2,020 exported points are
inside its explicitly bounded interior, with no excluded points or missing
ground. Maximum source/collision height difference is **0.000425123 cm**. There
are zero wet/dry classification disagreements, buried wet probes or incorrectly
dry clear-water probes. This audit uses a 0.001 cm source/collision comparison
tolerance, not a runtime water-depth cutoff. The initial v1 report failed JSON
serialization of a NumPy boolean; that partial file is retained. The corrected
v2 report passes, with a serialization regression test added.

Reports:

- `tmp/south-fork-ground-contact-v1-20260914.json`, SHA256
  `ccc31c52ee0d8a7cdb51a98a9ecee8705fb0641ee388b7802bd787c990b54e68`.
- `tmp/south-fork-ground-source-audit-v2-20260914.json`.
- `tmp/south-fork-ground-detail-v1-20260914.json`: same sequence **92**, 4,226 GPU
  queries, maximum RGBA error **2.980232e-8**, passes the unchanged 1e-6 gate.

The source mesh remains SHA256
`8bdf1a586e7bd2536eaf25a982763efd9e5a558e7172fd7897b8ae0ecc8fe06b`.
All 464 protected source/map/profile/actor hashes were rechecked unchanged before
gameplay. These contact results do not accept source hydraulics or whole-river
contact outside the measured footprint.

## Actual appearance and performance are still failing

The complete local clip is `unreal/Saved/VideoCaptures/RaftSim_20260914-142249.mp4`:
55 engine source frames over 6.327 seconds, 190 decoded frames. Its encoded
30 Hz timestamps are not gameplay FPS. The unmodified
[inspected frame](detail-motion/south-fork-ground-motion-v1-20260914_01s.png)
still shows broad smooth faces, bulky rocks and blurred froth. **Visual acceptance
fails**; corrected contact does not establish realistic breaking or calibrated
motion. Existing local decoding dependencies required elevated read access;
no remote media was downloaded.

Separate ordinary performance session 83728 completed exit 0 with no diagnostic
exports. All 300 CSV rows/footer validate. Warm rows 120–250 give **9.893320 FPS**,
mean **101.078299 ms**, p95 **128.556 ms**, failing 30 FPS / 33.333333 ms.
CSV SHA256 `97ec359721b0fc10db29bff8deb36184e78141bf820744cc5d55507e4cec95ef`;
report `tmp/south-fork-ground-performance-v1-20260914.json`.
The live expanded cook continued throughout. This is not an isolated causal
comparison or packaged traversal; several pre-existing water costs rose too.

Final timing build session 72285 completed exit 0 in 211.96 seconds. The same
12 native checks passed again, zero failed/warned/not-run, in
`unreal/Saved/RaftSimValidation/ground-contact-after-v2-20260914`. Sequential
native/game session 64369 completed exit 0. No runtime behavior changed after
the inspected recording; the final build adds a shared ground timing scope
and updates public comments.

The expanded cook had completed before the final game run. Its 300-row CSV
again passes the strict audit. Warm rows 120–250 give **20.803377 FPS**, mean
**48.069118 ms**, p95 **64.9716 ms**: still **FAIL 30 FPS**. The complete shared
ground query, including both pre-existing solid and new water queries, averages
**0.159887 ms/frame**, p95 **0.2059 ms**. Crest selection averages 5.921605 ms
and water stepping 10.329421 ms. These scopes overlap other inclusive timings;
do not sum them or attribute the large FPS difference solely to this patch.
This is still a short editor-hosted run, not sustained packaged acceptance.

CSV SHA256 `81004c2d4eabc09e56b140ec5ca59db32ee4ac60cdafe970d3cfaeaaa68fc3e4`;
report `tmp/south-fork-ground-performance-v2-20260914.json`.
All 464 protected hashes were rechecked unchanged after gameplay.
Final built source identities:

- Shared ground cpp: `7a0633a9eccc181bb7959eacc1c279f1d4ac11a47fb0de2516c65e0117ac00db`.
- Water actor cpp: `9629877870b4cbf6736cb6405ff8ae9df5162eaad41d252233da26984c306e2c`.
- Raft DLL: `5b0081c88e58edd6fae5354288f8e65859cd7e72689040d7cf1ceedb03d9e683`.
- Physics DLL: `c361b846387ec75631ed53fb2699aa4387096a14249259546a6d59b20b8b386a`.

## Expanded source run completed, not settled

Cook session **84168 is terminal, exit 0**, after local step 12000 / native
9999.999999995 seconds. Do not keep polling it as live. Both final audits pass:
all 5,382,400 cells finite, all 86,720 artificial-bank cells exactly dry,
maximum step conservation residual **1.412246e-8 m3**. Final volume is
2,509,603.437453 m3, maximum depth 3.833184 m, maximum speed 6.234656 m/s.
However, exterior outflow is **105.525238 m3/s**, versus **45.306955 m3/s** inflow.
The source is still unsettled and is not promoted into the normal map.
No automatic restart, terrain splice or experimental solver promotion follows
from its successful process exit.

Reports: `tmp/south-fork-expanded-10000s-{state,banks}-v1-20260914.json`.
Final h/u/v SHA256:

- `e42c891d3631c5035c4b1cbe0443cad64849196fda8835279c50d2136e351a47`
- `0d64926000b45672d6ffce837b6f223ad0d9b6c61d3b5e7c80a54b2fc885f601`
- `ae9102bb03b53ec907c1bdf34e69d7cf7086960073bc3a74e60d7e09da376c64`

Next work must address the dominant source-stage/terrain mismatch and compatible
mass/pressure coupling, then real breaking/froth and larger crest/solver runtime
costs. Ground contact is one correction, not a replacement for exact coupled
hydraulics. Retain the failed two-pole energy/wetting/refinement/native gates.
Then Colorado, Pacuare, Futaleufu in order, remaining Chilko/Zambezi water, crew,
normalization, regressions and release checks. Troublemaker remains within South
Fork, not a separate menu scenario. The full objective remains active.
