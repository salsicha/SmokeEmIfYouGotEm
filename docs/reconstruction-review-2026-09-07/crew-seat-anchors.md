# Shared normal-play horizontal seat anchors

2026-09-24 UTC. Normal physical loads now share the existing rendered seating
layout instead of applying bow passengers' weight at rear reference seats and
the stern-quarter guide's weight at the centreline. A single helper supplies
both consumers: passenger rows X=1.15,0.10m, alternating Y=−/+0.62m; guide
X=−1.55m,Y=−/+0.62m according to handedness. Additional rows retain the existing
authored spacing. No rendered body proportions or seating position was changed.

These are authored scene anchors, not newly surveyed human centres of mass.
Vertical load heights retain the existing inferred values. Articulated COM,
inertia and realistic cross-raft high-side motion remain unresolved. The
independent Python/D6 reference builder is unchanged; normal play explicitly
uses the shared layout rather than silently changing those fixtures.

## Validation

- Editor build succeeds in93.12s; Game build succeeds in90.03s:
  `tmp/crew-seat-anchors-{editor,game}-v1-20260924.log`.
  Existing unrelated detail-source `Current` warning remains.
- Native `RaftSim.Crew.+RaftSim.M5.CrewAvatarPoseProduction+RaftSim.M1.Flexible`:
  **11 succeeded,0 warnings,0 failed**,10.2827s. Report:
  `tmp/crew-seat-anchors-native-v1-20260924/index.json`.
  The extended command test compares physical XY with actual attached-avatar
  transforms, checks unchanged inferred Z/reference guide, and evaluates
  opposite nonzero guide weight moments for mirrored handedness. Existing
  command, occupancy and flexible-reference gates remain intact.
- Normal FullReach/full_descent captures use unchanged geometry, installed4950
  fields, nonlinear OFF, four solver lanes and original solver archive. No
  contact-review flag, hidden crew, alternate camera or shadow override.
  Both jobs finish exit0 and resume the exact original cook36692 successfully.
  Receipts under `unreal/Saved/RaftSimValidation/`:
  `south-fork-crew-seat-anchors-{cost,motion}-v1-20260924-process.json`.
  These are editor-hosted normal game captures; Game rebuild is separate,
  not packaged-release acceptance.

Ordinary900-frame cost, elapsed samples60–840 inclusive with confirmed scope
offset1: mean25.559523ms,p9534.7217ms,max43.6375ms. **FAILS** the unchanged
30FPS/p9533.333333ms gate. Report `tmp/crew-seat-anchors-frame-v1-20260924.json`;
CSV SHA256 `bedba8cc84e4edb3e3766b86de895f4b326fcb5d179b7cef044b78f9336a1226`.
This single run is not an isolated attribution of timing changes to seat loads;
earlier shorter-budget passes do not override this failure or prove full-route
performance. Do not restore deliberately mismatched physical positions to make
a particular timing sample pass.

High-side motion yields24 stills and
`unreal/Saved/VideoCaptures/RaftSim_20260923-185549.mp4`, SHA256
`d00740c45bde1a09e8862637f2faff22373ab569f963f9cdb6bc016b83fab7f8`.
Fully decoded462 frames through15.3667s,24 exact adjacent duplicates;
`tmp/crew-seat-anchors-motion-v1-20260924/report.json`. Original3s/9s inspected:
progress0.12→0.13km, changing water view, held crew side, zero incidents/swimmers.
No gross capsize appears in these samples, but they do not prove continuous
limb clearance, both-direction transitions, contact or full-route stability.
The awkward high-side lean/standing pose, smooth water and coarse canopy remain.
Encoded recording rate is not measured game FPS.

This delivers a normal-play load-location correction, not new terrain detail,
accepted crew realism, hydraulic settling or South Fork completion. Continue
the full ordered queue without advancing to Colorado prematurely.
