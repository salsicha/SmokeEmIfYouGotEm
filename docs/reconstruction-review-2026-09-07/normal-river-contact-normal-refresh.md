# Actual terrain contact-normal refresh

September 16, 2026 UTC. Follow-up to `e38b1a13e`. This fixes the observed
zero-time contact refusal; it does not qualify full-hull/default contact or
complete the South Fork reconstruction.

## Captured cause, not a relaxed gate

The original replay logged 81 zero-time separating-contact refusals. Two fresh
short replays instrumented the unchanged solve. In
`tmp/swept-zero-diagnostic-v2-20260915.log` (SHA256
`e5c62b3fa00381b9ea70a266d8c11a8f804e98ba7e03725b3de1705fef8715da`),
the first failure identifies support 1 at local
`(1.8500000953674316, 0.85, 0)` m against source triangle 200254.

The cached normal is
`(0.45056610529810104, 0.8285637102069674, 0.3323738300236127)`;
the newly queried normal is
`(0.45057434020669007, 0.82856009015895249, 0.33237169094719027)`.
Point velocity is zero against the old normal, but -2.99602583137e-6 m/s
against the new one. The old deduplication discarded that new constraint
because the normals were close. It then found no impulse against its already
solved, stale normal and refused to advance. This is not permission to ignore
small closing contacts.

The fix refreshes a matching manifold entry with the newly queried normal and
contact boundary. Distinct contacts still remain separate. No source vertices,
radius, timestep, iteration cap, clearance allowance, impulse threshold or
energy gate changed. Temporary diagnostic logging is removed from runtime code.

## Exact source-bound red/green regression

`RaftSim.Physics.CapturedTerrainManifoldNormal` replays the captured original
force-updated substep, with the original mass/inertia, pose, velocities and six
supports. It loads the same actual terrain, not a fitted plane:

- Asset: `/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround`.
- Asset SHA256: `6aec899c1dad1d26b8410813637f705c4fdd2552d5b4db718bb974eb6fa51a4a`.
- Source triangles: 803,842, unchanged.
- Translation: `(-543186.63697775919, -360044.75875617936, 0)` cm;
  identity rotation and scale `(1,-1,1)`.
- Mass 605 kg; world-axis diagonal inertia
  `(510.24191284179688,510.24191284179688,1133.8709716796875)`.
- Substep 0.0083333337679505348 s; radius 0.2800000011920929 m.

Before the fix, the test reproduces the same refusal:
`tmp/swept-normal-regression-before-v1-20260915/index.json`, SHA256
`25a0c3da9d059f5192ccb1c7c3cb4fd3254b8b373d5baf5e896937c3686cb4ef`.
That failed evidence is retained.

After the fix, all 13 native tests pass without warnings, failures or unrun
cases. Report `tmp/swept-normal-refresh-native-v1-20260915/index.json`, SHA256
`ea650fd8edebcbc8e5e38dad73b2278ece5704009d4dcb30878d91dfaf2cb345`.
The exact substep applies two impulses, consumes its complete timestep with
zero measured time error and loses 1.0684305568144055 J of kinetic energy.
An independent closest-point check of every original source triangle against
all six final support centres finds minimum clearance 2.5503260851489351e-5 m,
passing the unchanged -1e-5 m limit. This is final-pose support clearance,
not exact rotating full-hull continuous collision proof.

The four 600-step flat/inclined, low/high-angular-velocity support cases also
pass their unchanged time/energy/clearance gates. Original source feature,
transformed BVH, actual mesh, streaming/read-only observation and six M1
raft/grounding regressions pass. Editor build passed.

## Actual South Fork replay

The corrected candidate ran in the existing
`/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach` game with
`south_fork_full_descent`, source-matched landward 50 s preview, and
`-RaftSimContinuousGroundReview`. No new menu scenario, saved level or material
change; Troublemaker remains a rapid within South Fork.

`tmp/swept-normal-refresh-playable-v1-20260915.log`, SHA256
`3fd8154e51f2c0379ecaf39877eeffd36ebe62a332bd89e5c635af58f4a3cc9d`:

- Zero rejected contact-step log entries; 153 impulse-bearing substep entries.
- Stations 8393.108 / 8420.773 / 8432.231 m at world times
  32.156 / 52.135 / 72.149 s respectively.
- All three source caches ready. The 803,842-triangle terrain build still takes
  3,638.445 ms: an unresolved startup hitch, not a performance pass.
- Recording finalized with 705 source frames over 64.254 s:
  `unreal/Saved/VideoCaptures/RaftSim_20260915-192302.mp4`, SHA256
  `bcffb3c9533758f478f2e67e65fc080ea520d42f912537799de454030fe2fe47`.

The whole recording decodes to 1,928 presentation frames. The original initial
still and decoded 6/8/18-second frames were inspected at the same fixed shore
camera as the earlier roof-jump control; the raft passes the rock and leaves
the fixed view instead of jumping up and staying at its roof. The old control's
8-second frame was inspected again for comparison. This is sampled visual
inspection, not a claim to have reviewed every decoded frame. Later passage
outside the camera is telemetry evidence only.

Decoded outputs are in `tmp/swept-normal-refresh-decoded-v1-20260915/`.
The decoder's legacy ROI names belong to another camera and are NOT evidence
about foam/terrain regions here. Encoded 30 Hz is NOT physical/gameplay FPS;
this run overlapped the cook and is not an ordinary performance benchmark.
Broad froth, smooth wave faces and jagged inferred rock flanks remain visibly
unaccepted. No new real-reference measurement is claimed by this contact fix.

## Hydraulic continuation and next work

The existing landward cook PID 2344 / owned session 75302 was confirmed live;
it was not restarted and received no older-geometry water. Independent snapshot
and exterior-bank audits at local steps 5000 / 6000 (absolute 300 / 350 s)
pass all 5,350,400 cells, with all 86,720 artificial bank-face cells exactly dry.
Reports: `tmp/south-fork-landward-300s-{snapshot,banks}-v1-20260915.json` and
`tmp/south-fork-landward-350s-{snapshot,banks}-v1-20260915.json`.
At 350 s, maximum depth is 4.8969690185 m, speed 12.1119517120 m/s,
maximum step mass residual 1.3647665e-8 m3. Net boundary flow remains about
+19.6421 m3/s: NOT settled. Next checkpoint audit is local 7000 / absolute 400 s.

Keep the contact candidate opt-in until full-hull/deformation coverage, initial
overlap policy, packaged collision-source access and runtime cost are qualified.
The actual authored hull/deformation producer is
`RaftSimRaftMesh::ExtractProductionRaftRestMesh` /
`DeformProductionRaftRestMesh`; full-hull work must share that geometry, not
invent connecting capsules between the six old support centres. The floor lift,
pressure contraction and D4 squash/bulge are currently visual-only and must not
silently diverge from a future collision hull.

All 464 protected hashes are rechecked before commit. Remaining source-supported
geometry, crest/froth motion, 30 FPS, physical regressions, Colorado -> Pacuare ->
Futaleufu, other-scene water, crew, normalization and release gates remain open.
