# Public reentry discontinuity — September25

Actual D3D12 editor-world production-raft regression now exercises successful
`RequestSelectedReentry`, rather than testing only its `RemoveSwimmerAt` helper.
The existing rotated raft, real rendered hull, crew avatars, integrator and
occupancy assertions remain. This is a native fixture, not normal-play video.

The test establishes ReadyForReentry explicitly; it does not claim to validate
the preceding user-input, thrown-line or pulling sequence. It computes the tube
target after setting the current reentry pose, then invokes the public request.

- Exact current hull distance:1.140148845m, within unchanged1.35m gate.
- Root displacement during the synchronous request:392.377744591cm.
- Elapsed simulation time during that displacement:0seconds.
- Avatar identity preserved; swimmer removed; rescue count increments once.
- Repeating the request does not board another swimmer or increment the count.
- Occupied crew mass235→310kg and integrated raft mass455→530kg, with the existing
  impulse/inertia checks passing. Other original occupancy cases also pass.

This proves a discontinuity for this fixture, not a universal3.92m jump or a
body/raft penetration measurement. `AttachAvatarToSeat` immediately selects
SeatedIdle and relocates the root; no elapsed-time boarding traversal exists on
this path. The Reentry pose alone is not a climb animation.

Initial fixture incorrectly reused a tube target calculated before later raft
and pose changes. Boarding was refused, and downstream assertions failed.
Preserved failed report: `tmp/crew-public-reentry-20260925/index.json`. It is not
evidence of a broken readiness gate. Correcting current-state setup, without
changing the gameplay gate, yields1success/0failures/0warnings/0not-run, engine0:
`tmp/crew-public-reentry-v2-20260925/index.json`. Full measurement log:
`tmp/crew-public-reentry-v2-20260925.log`. Editor builds29.52s and11.11s passed.

Next repair needs an elapsed-time boarding state and coordinated root/body/PPE
motion over the actual tube, followed by seated ownership. Preserve readiness,
distance, duplicate-request, occupancy and rescue-count protections; validate
when mass transfers and when paddling becomes available. A straight interpolation
from this target to its assigned seat could cross the hull and must not be called
a collision-safe climb. Review actual continuous rendered motion, each identity,
both sides, tilted/moving raft and interruptions/checkpoint resets.

No runtime behavior, saved asset, packaged executable or river acceptance changed.
The passing occupancy regression is explicitly not reentry-animation acceptance.

## Ready-pose ownership repair

The next production pass found `DriftSwimmers` unconditionally applying Swimming
before its hull-clearance query and again after positioning. The later rescue
update restored Reentry for the selected ready passenger. This repeatedly changed
pose ownership and reset animation phase inside each frame. Drift now selects
Reentry only for the matching ReadyForReentry target; all other swimmers retain
Swimming. The same selected pose is used for clearance and the final update.
No readiness/distance limit, hull clearance, mass or completion rule changed.

Before the runtime fix, the extended native test fails exactly eight ready-pose
assertions (`tmp/crew-ready-pose-before-20260925/index.json`). Afterward the same
test passes (`tmp/crew-ready-pose-after-20260925/index.json`). Additional checks
pass12elapsed updates at1/60s with finite body and PFD error<0.01cm, unoccupied
crew mass235kg while waiting, another passenger still swimming, and release to
Swimming when the target's phase returns to Pulling. Eight zero-step cycles
retain the ready root within0.01cm. Final D3D12 report:
`tmp/crew-ready-pose-elapsed-20260925/index.json`,1success/0failures/0warnings/
0not-run, exit0. Tests exercise production methods directly in an editor world,
not human input or an inspected continuous gameplay animation.

Editor builds11.03s (new failing regression),29.72s (runtime fix),11.03s
(elapsed checks) succeed. The ordinary Boot/menu South Fork launch exits0 with
raft speed1.367m/s,wet1,support delta0 and sampled penetration0. Separate300frame
CSV rows30–270 give mean21.763666ms,p9530.2152ms. Nonlegacy timing is confirmed
in `tmp/crew-ready-pose-normal-20260925.log`; report with CSV SHA256:
`tmp/crew-ready-pose-normal-cost-20260925.json`. This no-rescue run is a launch
regression check, not direct rescue validation or a performance improvement claim.

The392.377744591cm instantaneous boarding jump still exists and is still logged.
This fixes a competing pose owner required before a timed climb, not the climb
itself. No cap geometry, flow field, saved map, packaged stage or remote changed.

Standalone Development game target also rebuilds successfully in119.34s. Its
binary is not yet restaged or separately packaged-play qualified. The normal
editor-hosted game test above used the rebuilt production runtime without opt-in.
