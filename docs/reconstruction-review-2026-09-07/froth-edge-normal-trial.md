# FullReach foam-edge normal trial: not promoted

September 28 UTC. Bounded actual-play trial, not a delivered visual change or
reconstruction acceptance. The original material and author source are restored.

## Question and implementation

The normal full-river material had current-carried water ripple normals but no
normal contribution from its displayed foam contours. A trial wrapped that
existing normal with the already-used `RaftSimCapturedFrothNormal.hlsl`, driven
by the exact displayed `SouthForkTransportedFoamOpticsV1` coverage, constant-one
lace, world position, and an artistic 0.6 cm relief scale. This was lighting
only: not measured bubble height, water displacement or breaking physics.
It introduced no new coverage, noise, independent animation clock or solver.

Candidate editor build passed (55.27 seconds); five candidate regressions and
four existing local-current-normal tests passed. A guarded D3D12 installation
and independent fresh-process saved-asset audit both exited zero and passed.
All six protected non-normal material graphs and the original normal subgraph
were unchanged. These are graph checks, not GPU realism or performance passes.

## Actual playable evidence and decision

Both captures launched the normal FullReach scene with the ordinary boat camera
at station 8310, 1280x720 D3D12, no solver/quality override. Each recorded twelve
camera samples and exited zero without logged runtime errors. The candidate
raft moved from 8312.359 to 8341.623 m over samples at world times 2.437 to
13.085 seconds. Baseline samples span 8313.788 to 8344.689 m. These are moving,
non-deterministic runs, **not pixel-registered A/B frames**; differences in raft
pose or foam distribution cannot be attributed to the material change.

Inspected baseline/candidate frames 004 and 010: broad near-bank and downstream
white patches still read as flat sheets; no useful improvement in the intended
froth appearance was established. This does not prove the normal perturbation
is numerically zero. Edge-only lighting cannot create interior bubble detail
where saturated coverage has zero derivative, and it cannot create a breaking
face or overturning roller. The trial was therefore not promoted or packaged.
No new isolated cost claim is made for this rejected appearance candidate.

Retained local evidence (repository-relative):

- `tmp/froth-edge-install-v1.log`: graph pass, 0 errors / 4 existing warnings;
  SHA256 `2d0845aab5d6d1c4c3a80fd4837d3b95d370788e347f9a7cc28b4695e473906a`.
- `tmp/froth-edge-fresh-v1.log`: fresh saved-graph pass;
  SHA256 `4efd4c77f02631d37a7aefa0d9924eec05aa63152ce806dd98918221dde3aa25`.
- `tmp/south-fork-froth-edge-{installed,fresh}-v1.json`: protected graphs,
  original normal subgraph and candidate shader/asset identities.
- `tmp/sf-froth-relief-{before,after}-v1.log` and
  `unreal/Saved/Screenshots/sf-froth-relief-{before,after}-v1_000..011.png`.
- Candidate log SHA256
  `853b395e0e5e2aa49a85960566e48905668f65e80d8317ce9f98c0008f9c9353`.
- Candidate movie `unreal/Saved/VideoCaptures/RaftSim_20260927-200036.mp4`,
  SHA256 `28e775aab7e73724eb57e77922472c507116024beac33e1a05cdd1963519b6a4`.
- `tmp/froth-edge-candidate-v1/`: preserved author source, trial tests,
  guarded installer and candidate material; not part of the playable pipeline.

Restored material SHA256:
`6f235b61577289f195cbbb801ce8a83e40b961827ba4be637806178ea1dcedf9`.
Candidate SHA256:
`ae32789b1cef5302bafa07f638c1ac52f8b1032b9503b80c2472593280c70488`.
Only the trial's two new scripts were removed from active source, after copying
them into the retained candidate archive. Existing user changes were preserved.
Restored four local-current-normal regressions pass. Restoration editor build
passed in 31.63 seconds: `tmp/froth-edge-restored-build-v1.log`. Installation,
fresh audit, playable capture and restoration build owners all exited zero;
no trial work is still running.

## Remaining work

v14 remains the unchanged packaged baseline. Its rapid timing failures and
unaccepted breaking geometry, contact/shoreline and settled hydraulics remain
open. Do not repeat this exact edge-only trial or claim it shipped an improvement.
The next visual intervention needs evidence of actual breaking-face structure
or resolved interior froth detail, followed by normal-launch motion and isolated
cost validation; merely increasing this artistic edge-height scalar is not that
evidence. South Fork remains first in the queue.
