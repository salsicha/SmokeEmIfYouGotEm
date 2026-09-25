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
