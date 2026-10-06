# Certified near-axis storage: bounded repair and failed longer replay

September28 UTC. Candidate-only supporting work; v27 remains the normal game.

## Implemented and proved scope

FStorage now searches on the actual stored row or column for proposals in the
first two float steps from a canonical axis. A point close to an axis can
otherwise acquire a much larger off-axis coordinate when converted to the GPU
buffer. The resulting root proposal is not itself acceptance: the unchanged
whole wet-triangle, omitted-dry-fan, radial partition and1mm width proofs still
gate the complete stored polygon. Canonical shared crossings are unchanged.

Axis-v1/v2's conditional correction reproduced reversed order on a single
GPU row. The final consistent-row choice removes that captured reversal.
Original proposal-live-v1 frame186/source33168 now has13 segments/15 triangles,
complete native certificates for both radial search policies, real builder/cache/
attribute comparisons and independent exact stored-polygon certification.
It is a positive ninth case bound to the original raw log, not modified donors.
The earlier dry vertex remains a negative sign control. Captured data are
simulation inputs, not new surveyed bathymetry or measured reconstruction.

Final native receipt: tmp/certified-bank-axis-v4-20260928-process.json:
20 regressions,15 independent audit controls,nine exact exported cases pass.
Export SHA256 c747c4b1264b05cc3a157e3dc266cb2c8eddc7bba82c3d9a6147e8c4c84b7fce.
Exact audit SHA256 3dd34cdbc5256413b4e9249a7f9b247de59f713c46da150bb498af22c805c4eb.
All frozen inputs and the protected automation test are unchanged. Two new
changed-state tests described below are EXPLICIT NEGATIVE controls, not extra
accepted geometry cases. They must become independently certified positives.

## Actual engine replay: FAILED

One longer FullReach8310 replay with candidate flag, normal render rebase,
40 screenshot requests and video recording used the unchanged implementation.
275 updates accepted and37 rejected.40 motion samples span8312.180..8356.468m
(44.288m). Process exit zero and motion are not runtime-health acceptance.
No unchanged rerun was started. Engine/native/decoder owners are terminal.

Receipt: tmp/certified-bank-axis-live-v1-20260928-process.json.
Log SHA256 57820e57efb0f813f7a0058f4563bf162db1d8403fc0f3b96e35be82d9a36322.
[Captured original failing states](certified-bank-axis-live-rejections.json):

- frame183/source33168 has changed depths: both failed endpoints are wet,
  but their connecting segment crosses dry space. Exact33-point sampling
  finds a negative numerator approximately-2.06113816e-9, and the full exact
  segment certificate rejects it. Per-point wetness is insufficient.
- frame292/source23259 reverses radial order on a constant GPU row farther
  than the current two-row correction. Its exact determinant is
  -19/655360000. The ordering gate correctly rejects it.

The implementation remains disabled in normal play. These failures need a
general stored-contour/endcap construction with complete segment and ordering
proofs, not a wider band, depth tolerance or acceptance of retained old meshes.

## Motion, appearance, contact and cost

Original engine video:
unreal/Saved/VideoCaptures/RaftSim_20260928-094624.mp4.
SHA256 ce3d3a1fe2380f9b88cf7c16f925c0b3960787370d4608dc076e6ce45fe4b43e.
Decoder report: tmp/certified-bank-axis-live-v1-20260928-decoded/report.json.
All1309 frames decoded,0..43.6s,1280x720;76 adjacent duplicates. Recorded rate
is not game FPS. Extracted6/20/30/42s frames were visually inspected: forward
movement and gross raft/water alignment are visible, but broad flat white
foam, weak breaking/recirculation, coarse banks/rocks and crew fit remain
unaccepted. Sampled frames do not establish full animation or shoreline
continuity, particularly during rejected updates.

The world10.0097s contact snapshot, BEFORE the later failures, has1873 wet
probes,135 ground-occluded dry probes,zero unavailable/occluded wet probes and
maximum support/carrier error4.7683715e-5cm. This does not establish later
contact, full traversal, independent collision acceptance or GPU parity.

Accepted topology calls: median44.895899ms,mean57.102065ms,
range4.288301..303.059399ms;39/275 exceed50ms. Startup, near/far components,
audit, video and screenshot work are included. These are NOT isolated frame
timings or a causal FPS comparison. The existing20FPS and bridge-clock gates
remain unmet. The radial evaluation counter excludes the new fixed-row search;
whole-construction timings, not that counter alone, must assess its cost.

## Next work

Repair full-segment endcap selection across changing depths and constant-row
ordering beyond the two-row case, retaining all exact proof gates. Recheck
the original and new captured states, then repeat actual motion/shoreline/
post-crest/contact and isolated frame/clock measurements. Enable a bounded
improvement in a fresh normal build only when qualified. Physical breaking,
holes, recirculation and the full ordered river/crew/release queue remain open.
No cook, package, solver activation, source deletion, river acceptance or push.
