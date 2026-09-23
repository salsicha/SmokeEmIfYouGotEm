# Installed rapid review after stage-storage integration

September23 follow-through on [default stage-storage reuse](solver-stage-storage.md).
This closes the outstanding review of the retained rapid captures, not a new
visible delivery or river acceptance. No new engine/cook job was launched for
this review. The normal-start qualification remains separate.

## Scope and measured cost

Both retained runs use the rebuilt normal modules and installed4950s fields in
`L_SouthForkAmerican_FullReach`, full-descent scenario, D3D12,1280×720, four solver
lanes. Archive SHA256 is
`63e9e59209d4cd4dc4c70f47e5f1c8fc64d8e903a86bcf9d967d0cb9f1d0365f`.
They explicitly select review station8330; neither is a normal-start launch or
packaged traversal. No candidate terrain/physics or nonlinear enablement occurs.
Both engine processes exit0; the identity-guarded cook suspension/resumption
statuses are0. Receipt CPU differences across pause acquisition are0.109375 s
and0.125 s, so these receipts do not support an exactly-zero CPU-advance claim.

Ordinary cost is measured separately from recording:900 frames, rows60–840,
781 samples, confirmed modern FrameTime scope offset1. Mean25.661350 ms,
elapsed38.969111 FPS, **p9535.4787 ms fails33.333333 ms**. This single window is
not a paired estimate of the optimization's effect. Mean game-thread25.367608 ms
exceeds render-thread12.587503 ms and GPU9.409516 ms. Water Tick14.287596 ms,
publication7.729386 ms, SetMesh6.347264 ms and solver-step3.901734 ms are inclusive
or overlapping scopes: do not sum them. RefreshSurface can itself publish;
subtracting its listed sampling children does not identify an unscoped bottleneck.
Tick interpolates before scheduled refresh, but that alone does not prove a
redundant publication: interpolation/recentering ownership must be preserved.

Cost audit: `tmp/solver-stage-rapid-cost-v1-20260923.json`.
CSV SHA256: `6a63ff2a378c14b92a93af8c96c65d3a78dc56af14bbd1ff42a6a2a1fc0e9ca0`.
Process receipts are under `unreal/Saved/RaftSimValidation/` with labels
`south-fork-stage-storage-rapid-cost-v1-20260923` and
`south-fork-stage-storage-rapid-motion-v1-20260923`, suffix`-process.json`.

## Actual views and motion limits

The retained15.597 s movie fully decodes to468 frames, with25 exact adjacent
duplicates. Encoding statistics are not game FPS. Original3,6,11 and13 s frames
were inspected: HUD station advances8.33→8.35 km; camera/raft orientation changes
around the large gray rock. The raft is very close to that rock in the early
views. Broad white/smooth water, angular rocks, repeated canopy and crew pose/
fit limitations persist. Later views show dark irregular patches beside the
raft; these images alone do not establish their cause or surface continuity.
No convincing breaking-froth, collision clearance or shoreline acceptance.

The source-union review already identifies an8330 start conflict against its
candidate geometry/stage. These runs use installed geometry, not that candidate,
but must not be reused as proof of a safe reconstructed start. Fresh matched
flow/geometry and hull-clearance qualification are required before candidate
promotion; see [the retained conflict](constriction-union-review.md).

Movie: `unreal/Saved/VideoCaptures/RaftSim_20260923-131349.mp4`, SHA256
`b106fe03a3194242855faf77c32b0f4970e315deb5b10af6f97a9663fe5924e3`.
Decode receipt and original sample frames:
`tmp/solver-stage-rapid-motion-v1-20260923/report.json`.
No captures were regenerated or source data changed. Do not repeat this unchanged
baseline or promote previously rejected performance options on these results.
South Fork remains first unfinished; all later rivers and acceptance gates stay open.
