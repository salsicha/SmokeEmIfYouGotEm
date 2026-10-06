# Ordinary water upload optimization — September 14

This heartbeat advances the normal playable South Fork renderer without enabling
the known broken research solver. It is a performance-only delivery, not a new
terrain, wave, breaking or froth appearance. The previous goal turn made progress
on the mass/energy obstruction; that required coupled correction remains open.

## Implemented in the rebuilt normal renderer

`RaftSimShorelineMeshComponent` previously rebuilt the source-to-dense vertex
mapping on every dynamic upload: clear a reserve-sized remap and revisit every
triangle corner, even when index order was unchanged. It now caches only the
ordered source membership. On a value-only update it converts every currently
referenced vertex afresh, preserving position, packed tangents/normals, color
and all four UV channels. It does not cache stale vertex values, weld coincident
vertices, remove geometry, reduce update frequency or change the water solver.

Topology ownership already compares actual index arrays. Its pending-index flag
invalidates the mapping on topology changes, including dry/rewet transitions.
The scene-proxy constructor still creates its own exact first-occurrence mapping;
the dynamic cache uses the same order. `-RaftSimOriginalUploadRemap` retains the
old per-update remapping control. Default operation needs no opt-in.
Added the `RaftSimShoreline/GameThread/RenderPacket` timing scope.

Build60870 succeeded in154.23s. Native27225 terminated exit0:10 tests succeeded,
zero test warnings/failures/not-run,1.974087s test duration. The expanded compact
upload test verifies changed attributes, coincident but distinct source nodes,
exact triangle/winding order, retained topology, empty/dry and reordered rewet
states. Existing fan, shoreline, crest support, completed-detail GPU, catalog
and save-migration checks also pass. Troublemaker remains absent as a standalone
scenario. Report: `unreal/Saved/RaftSimValidation/upload-remap-native-v1-20260914`.

Built source SHA256:

- cpp: `7fdb07e48a647edb83d92793ece326e9730202331bda08ab0a84945013e2065d`
- header: `09c4f24400948fe770bf271c9266301b87e1c43b8603db85886c8a7893692c1a`
- RaftSimRaft DLL: `53a8761a2050f2686753e179c930017ceb2dd3df4c64f7c8304378a381c344d0`

## Actual ordinary-scene cost, not isolated performance acceptance

Both runs used the same rebuilt engine, ordinary full-reach South Fork scenario,
station8330,1280x720,300 CSV rows, unchanged desktop30FPS target and warm sample
indices120–250. Default29314 and old-control86176 both terminated exit0.
Strict full CSV/footer/required-water-scope audits passed:
`tmp/south-fork-upload-cache-{default,control}-performance-v1-20260914.json`.

The RenderPacket column has131 finite positive warm samples in each run:

| Run | Packet mean / p95 ms | Overall FPS | Frame p95 ms |
| --- | --- | --- | --- |
| Default cached mapping | 1.365147 / 2.7055 | 9.771154 | 122.8184 |
| Original remapping control | 2.463862 / 3.2335 | 9.304758 | 128.3225 |

These separate runs have different trajectories/timing and shared original-job
load. The observed1.099ms packet-mean difference is not a paired same-input causal
benchmark, sustained gain or proof of the overall FPS difference. Both still
FAIL30FPS/p9533.333ms. No physics budget, quality setting or acceptance gate was
relaxed. Existing original histories and the cook were not stopped or suspended.

## Actual motion and contact after default integration

Normal game32537 terminated exit0. Its log records149 uploads,112 retaining
topology and37 rebuilding it, with25,192–26,252 referenced vertices. At frame145,
for example,25,197 current vertices are uploaded from77,824 reserved vertices
and145,443 triangle corners with no index update. This verifies that retained
and changed topology both occur on the ordinary path, not only in unit fixtures.

Actual support audit:2,020 wet points,zero dry/unavailable,max support/carrier
error4.763088884374156e-5cm;927 points include detail. Same-sequence86 GPU audit
passes4,226 queries,maxRGBA error2.9802322387695312e-8 against the unchanged1e-6
gate. Separate shape capture sequence108 has21,092 nearby triangles,none above
60degrees,gradient-decomposition error1.884225116427843e-12. The shape and contact
captures are different sequences; do not combine them into one exposure.
Reports use `tmp/south-fork-upload-cache-motion-{contact,detail,shape}-v1-20260914.json`.

Recording `unreal/Saved/VideoCaptures/RaftSim_20260914-105530.mp4` fully decodes197
encoded frames from46 source frames over6.573s. The unmodified extracted1s frame
was inspected: the same large gray rocks, steep smooth green faces and broad
blurred white froth remain. **Visual realism still fails.** Image changes establish
changing pixels, not correct breaking dynamics or real-time pacing. The recording
is not a30FPS gameplay measurement and no comparison to newly accessed reference
footage is claimed. Analysis and frame are in `detail-motion/` under the
`south-fork-upload-cache-motion-v1-20260914` label.

## Cook checkpoint and remaining scope

COMPLETE9400/local28000 passes BOTH state and artificial-bank audits:5,382,400
finite cells and86,720 artificial-bank cells exactly dry. Outflow102.1181741
versus inflow45.3069545m3/s remains unsettled. See
[the expanded checkpoint](full-river-expanded-checkpoint.md). Next COMPLETE9500/
local30000 requires BOTH audits. All five original handles were directly checked
live; no reset, source replacement, restart or suspension.

Keep delivering safe normal-scene improvements incrementally, while completing
the joint mass/pressure work replacement and its required wet/dry/history tests.
South Fork geography, collision, hydraulics, waves/froth and actual30FPS acceptance
remain open, then Colorado, Pacuare, Futaleufu, other-river/crew reviews,
normalization, regressions, release and final commit. This small upload delivery
does not complete or shrink any of those requirements.
