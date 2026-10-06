# Exact normal calculation in ordinary playable water — September 14

The previous goal turn made progress by identifying the subcell geometry
mismatch and implementing exact conservative cell storage. This turn delivers
a measured performance change in the normal renderer; it does not promote that
storage primitive into an unfinished hydraulic model or close visual gates.

## Current-frame geometry, original-order sums

The existing warm CSV records 132 crest updates across 131 rows, with 131
profile changes. Reusing old profile heights would therefore be inappropriate.
Selection and current physical input are left intact, including the original
0.5 cm selection tolerance, refinement depth, geometry, update cadence and
2 cm independent shape gate.

`FRaftSimCrestNormals` now computes each triangle's normal concurrently, then
gathers a vertex's incident face normals in the **original triangle/corner
order**. No atomic or reordered floating-point reduction is used. The cached
incidence lists hold only triangle membership and fine-vertex involvement;
all positions, face normals and tangent projections are recomputed from the
current mesh. Actual index arrays, vertex count and source-prefix count control
invalidation. Degenerate faces, repeated indices, untouched source vertices,
dry meshes, changed winding and rewetting retain the original behavior.

The normal playable path enables this by default. `-RaftSimSerialCrestNormals`
retains the old control. `-RaftSimCrestNormalsAudit` compares every vertex
attribute and times both paths with alternating call order, including incidence
rebuild costs. No change to solver state, terrain, material or scenario menu.

## Build and native evidence

First build 71084 failed on the new fixture's implicit int-to-bool conversion.
The explicit comparison fixed that compile error; existing D6 damping warnings
were not hidden or edited. Candidate build 41071 passed in 15.15 seconds.
Candidate native 97169 passed all 11 tests, zero warnings/failures/not-run.
After actual-input qualification, final default build 18451 passed in 15.27
seconds and native 26918 again passed **11/11**, zero warnings/failures/not-run,
1.862683 seconds test duration. Final report:
`unreal/Saved/RaftSimValidation/crest-normals-default-v1-20260914/index.json`.

The new native test compares all attributes of 40,344 vertices over 24 changing
frames. Existing crest target-cache/memo-epoch/fine-crest, shoreline geometry and
upload, dry-rock, carrier contact, completed GPU frame, career catalog and save
migration regressions remain included. The CSV auditor adds an optional normals
scope: historical absence stays unavailable, never zero. Four paired-profile
tests plus eight original CSV tests pass; no target or footer rule is relaxed.

Final built SHA256:

- Normal helper: `fb0643ad50f63ef0741ad8812c07a333b3f80d51fe8f8928098af19a47a36fd3`.
- Shoreline crest cpp: `4a17f33f8e31646f81b291628c3eda551f8f81d636d6f38c34c58c74dc9be66f`.
- Raft DLL: `dacfb42deb24b432d00c70904fa5acc39618fd25ba972d8977a482975b503817`.

## Actual paired measurement and default gameplay

Ordinary South Fork process 19737 completed exit 0, station 8330, 1280x720.
The same-input warm window is engine frames 120–250. All **132 calls / 8,870,166
vertex comparisons** match exactly, retaining the second call at frame 250.
No call is discarded as an outlier or because topology rebuilt.

| Paired calls | Original mean ms | Parallel mean ms | Original minus parallel ms |
| --- | ---: | ---: | ---: |
| All 132 | 1.676411 | 1.047822 | 0.628589 |
| Parallel second, 67 | 1.761679 | 1.014769 | 0.746911 |
| Parallel first, 65 | 1.588520 | 1.081892 | 0.506627 |
| Reused topology, 100 | 1.629831 | 0.716114 | 0.913717 |
| Rebuilt topology, 32 | 1.821975 | 2.084410 | -0.262435 |

Rebuild-only calls are slower, explicitly retained; the whole measured workload
improves in both call orders. This scoped same-input result supports default
integration, not a sustained FPS or scene-acceptance claim. Report:
`tmp/south-fork-crest-normals-paired-v1-20260914.json`, log SHA256
`2448536446d8a0b29aaf98f501e457033db7d72ba90ec2669af358465b70eceb`.

Separate ordinary default process 86667 completed exit 0 without comparison,
screenshot or contact-export overhead. Strict CSV validation passes all 300
rows and the completed footer; warm sample rows 120–250 inclusive give
**11.520818 FPS**, mean 86.799390 ms, **p95 103.8838 ms**. This still FAILS the
unchanged 30 FPS / p95 33.333333 ms target. Normals average 0.991013 ms, p95
2.0893 ms. Crest selection still averages 13.274755 ms, water stepping 17.176090
ms and inclusive water tick 58.841708 ms; nested timings must not be summed.

CSV SHA256: `648df9d5c69493ae53070658b6919ae26001bcf0f4d50739f0e42f3b13c00fa6`.
Report: `tmp/south-fork-crest-normals-default-performance-v1-20260914.json`.
The cook kept running. Different trajectories and shared-host load mean the
small FPS difference from prior runs cannot be attributed solely to this change.
This is a short Development/editor-hosted capture, not packaged traversal.

## Fresh actual motion/contact: still visually unaccepted

Ordinary default process 18613 completed exit 0 with contact/detail audits at
the same published sequence 106. Contact has 2,017 wet probes, 3 raw-dry probes,
zero unavailable probes and maximum support/carrier error **4.758245e-5 cm**;
941 points contain detail. GPU sampling passes 4,226 queries, maximum RGBA
error **2.980232e-8**, against the unchanged 1e-6 gate. These are not new physical
breaking-wave or full traversal tests. Reports:
`tmp/south-fork-crest-normals-{contact,detail}-v1-20260914.json`.

The local recording `unreal/Saved/VideoCaptures/RaftSim_20260914-125422.mp4`
contains 58 engine source frames over 6.376 seconds; full decoding yields 191
encoded frames. Encoded 30 Hz timestamps are NOT engine FPS evidence. The
[unmodified extracted frame](detail-motion/south-fork-crest-normals-motion-v1-20260914_01s.png)
was inspected: broad smooth faces, bulky aligned rock forms and smeared froth
remain. **Visual acceptance still fails.** Full decoding is not calibrated
continuous-motion comparison with the real reference footage. The optimization
preserves the current appearance rather than claiming new realism.

All 464 protected source/capture/map/profile/mesh/package files from the combined
ground audit were rehashed unchanged after gameplay. No geometry or source
provenance was rewritten to match a screenshot. Troublemaker remains a rapid
inside South Fork, not a standalone menu scenario.

## Remaining goal

The live cook was directly confirmed beyond native 9704/local 6080. COMPLETE
9700/local 6000 now passes BOTH state and artificial-bank audits: all 5,382,400
cells finite and all 86,720 artificial-bank cells exactly dry. Maximum step
conservation residual is 1.356499e-8 m3. Outflow 103.273733 m3/s versus inflow
45.306955 m3/s still does not establish settling. Reports:
`tmp/south-fork-expanded-9700s-{state,banks}-v1-20260914.json`.
The h/u/v hashes are respectively
`060dae029f486c188e84d693d846286c6fde547a308c8d2fd9ba5a85bca98708`,
`67199cb6e9b30af466bcfedc709be4bbf4f9e6895e1990d776c519b7ff5270dd`,
`45c025814b315632e46aae38fd5b48d64f069d83dcb3e923fc97644bb89e5fc1`.
Next COMPLETE 9800/local 8000 requires both audits. No restart or suspension.

Prioritize compatible source-triangle storage, intercell mass/pressure work and
shared contact/render clipping so geometry and actual waves improve; preserve
the existing dry/variable-bed/energy/refinement and original moving-source gates.
Further performance work must address the larger crest and solver costs without
stale heights or reduced quality. Then Colorado, Pacuare, Futaleufu in order;
remaining Chilko/Zambezi water, crew realism/fit/animation, normalization,
regressions and release checks. The complete objective remains active.
