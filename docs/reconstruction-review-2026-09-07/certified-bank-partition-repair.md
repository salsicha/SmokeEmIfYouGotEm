# Stored endcap and signed-neighbor repair: qualified captures, failed replay

September 28 UTC. Supporting candidate work only; v27 remains the normal game.

## Qualified change

The storage policy now tests complete near-axis endcap connections against the
original shared crossing, not merely endpoint signs. Where a radial proposal has
no wet/dry-certified pair among its nine neighboring GPU coordinates, it searches
on the actual stored row/column. Neither operation changes the original donors,
canonical shared crossing, 1 mm band, wet triangles, omitted dry fans or partition
proofs. The proposed sorting path was unnecessary and removed; ordinary segment
ordering remains mandatory. A native counter verifies the signed-neighbor
fallback is exercised by the captured source23259 case.

partition-v1 failed on a dry rounded point in case10. partition-v2 certified all
11 geometries, but its test incorrectly required the unused sorting path.
partition-v3 removes that path and verifies the actual fallback. Its receipt
tmp/certified-bank-partition-v3-20260928-process.json confirms:
20 native regressions, 15 audit rejection controls, 11 exact exported geometries,
unchanged frozen inputs. Original changed-state captures frame183/source33168 and
frame292/source23259 now independently certify:13 segments/15 triangles and
78 segments/80 triangles respectively. These are positive captured-state results,
not proof for all changing water states.

Stored export SHA256:
67cd3d1181711efdbaa2ed3c426deaf3d342e3e46abe6451487a3254e8e3d465.
Exact audit SHA256:
b4599eb147681607f60fb6ff81c878927f7fc6896779daf35bd9e9d045fa9065.

## Actual replay still FAILED

One FullReach8310 engine replay, with candidate flag and unchanged normal render
rebase, recorded 294 accepted updates and19 rejected updates.40 motion samples
span8312.180..8356.963m (44.783m). Process exit0 does not override runtime errors.
The candidate remains OFF by default; no new normal package or cook was made.
The normal launch path was not rerun this checkpoint because the candidate
failed qualification; retained v27 binary hash remains
82e139184dbd93c46ebf7c0419e49da850db003d0aab4071ac35bba5dd65bcd0.

Receipt:tmp/certified-bank-partition-live-v2-20260928-process.json.
Log SHA256:984f5e030a8fe274d8253d3bb2906064ec2d1ad6088e03675d8dbcde9981bd52.
[All19 original rejection records](certified-bank-partition-live-rejections.json)
preserve sources33168 and33610 across the changed depths.

First rejection frame189/source33168 has two wet endpoints, but its connecting
segment genuinely crosses dry space. Independent exact arithmetic finds a
negative numerator of approximately-1.011020934e-8 among33 samples and rejects
the whole segment certificate. Endcap selection is therefore still incomplete
as the canonical crossing approaches the corner. Do not loosen the sign or
width gate, accept retained old meshes, or rerun the unchanged failure.
Next: reconstruct this whole near-corner connection with representable interior
nodes, then certify all retained/omitted geometry and replay both source cells.

## Video, contact and cost: bounded observations only

Original engine video:unreal/Saved/VideoCaptures/RaftSim_20260928-101044.mp4.
SHA256:3b1991d4bfb53a610704796b5b0537763f00d24a7ebb59e142d5f242f47b5b0e.
All1306 frames decoded,0..43.5s,1280x720,126 identical adjacent frames.
Report:tmp/certified-bank-partition-live-v2-20260928-decoded/report.json.
Viewed6/20/30/42s and initial engine screenshot: forward movement and gross
raft/water alignment remain visible; broad flat white foam, weak breaking,
coarse rocks/banks and crew/paddle fit remain unaccepted. Frame samples and
decoding are not full animation/shoreline/collision acceptance, especially while
updates reject. Recorded rate is not measured game FPS.

Contact at world10.103263s, BEFORE the later failures:1863 wet probes,
143 ground-occluded dry probes,zero unavailable or ground-occluded wet probes;
maximum support/carrier error4.7678094233560842e-5cm. GPU parity was not requested.
This snapshot does not establish later-state contact or full traversal.

Accepted topology calls:median45.4756ms,mean57.723723ms,range4.073601..330.590401ms;
39/294 exceed50ms. These contain near/far components, startup, audit, screenshots
and video:NOT isolated frame-time acceptance or a causal speedup.20FPS/p95<=50ms,
zero>100ms and bridge-clock debt gates still require qualification. The extra
fixed-row and neighbor checks must be included in complete construction cost;
radial evaluation count alone omits that work.

All build/replay/decoder owners terminal. Protected automation test unchanged.
No solver activation, captured-source deletion, push or river acceptance.
South Fork remains first unfinished; later rivers remain queued.
