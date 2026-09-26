# South Fork channel canopy correction - September26 UTC

Delivered to the normal FullReach scene: removed **266 inferred tree instances**
whose roots were inside the preserved context water mask. The remaining NAIP
canopy count is **140,417**. Six external actor packages changed; terrain,
collision, water geometry, cooked fields, imagery and original placement JSON
are unchanged. This is an asset-only change used by the existing rebuilt
Editor-hosted game; no standalone executable or packaged release was restaged.

## Cause and evidence

The first 3,000-root check stored only aggregate errors, including a 220 cm
maximum. The enhanced check locates seven roots over 20 cm from the ground.
A separate fresh-editor audit loaded all static-mesh ground actors and matched
actual canopy instances by XY and placement hash. Six mesh bottoms were about
200 cm above physical ground, one 25.66 cm above it, even after the existing
20 cm root sink. This was not a missing terrain actor in the original trace.

The 220 cm source-root difference matches the terrain's inferred channel depth.
All seven roots fall in cells explicitly marked water in
`source_context_extension/unknown_submerged_bed_mask.tif`. The placement builder
used the larger context DEM but the smaller original water mask, then clipped
out-of-range lookup indices to its edge. This admitted trees in the added
channel coverage. Lowering their roots would have planted them on riverbed.

The new read-only audit checks all 140,683 original roots against the context
mask: 266 water cells, zero unknown/outside cells. Only these positively
identified water-cell instances were removed, not all trees with a height error.
The generator now uses the context mask and context origin/cell spacing,
requires matching DEM/mask shapes, rejects unknown mask coverage, and refuses
out-of-range indexing instead of clamping. The original placement is retained.

Source mask SHA256:
`7ed4f6db78b0bb86f75c6a155613b830997181347efd7b5f66897973205dac1a`.
Original placement SHA256:
`bda1ea1ff90e30d21c3c2eadbe888213eeaf8428c5e37fb170885098fce3852b`.

## Saved-scene verification

- Three numerical tests pass: grid axes/classes, outside-grid rejection, and
  retained/extended-grid coordinate equivalence.
- The repair validates every target before editing, checks the original
  placement hash, backs up all six packages, and verifies exact surviving
  transform multisets after removals (including HISM index swapping).
- A fresh editor reload confirms all six package hashes, corrected component
  counts and absence of removed XY positions. The 260 surviving instances in
  affected components remain non-colliding.
- Four explicit-camera game frames completed; frame003 was inspected. The
  center channel is clear of the removed trees; the surrounding canopy remains.
  This elevated diagnostic view is not the normal raft camera or a water-motion
  validation view. Distant coverage and bank details remain unfinished.

![Corrected channel from a diagnostic game camera](canopy-channel-repair/channel-view.png)

Receipts: [water-mask audit](canopy-channel-repair/channel-audit.json),
[repair and package hashes](canopy-channel-repair/repair.json),
[fresh-engine readback](canopy-channel-repair/fresh-verification.json).
Recoverable package backups are in
`tmp/naip-canopy-20260926/channel-repair-v1/`; source capture data was not deleted.

## Normal launch, motion and cost

Fresh `profile_south_fork_current_map.ps1 -NormalMenuLaunch -NoCookWorkload
-ProfileFrames 1200`, label `south-fork-canopy-channel-repair-20260926`:
exit0, no timeout, ordered Boot/menu/FullReach travel confirmed, D3D12 1280x720,
nonlegacy frame timing and scope offset1, required water scopes present.
CSV `Profile(20260925_220224).csv`, SHA256
`382ba5d601c4095aedd1c164ac8dc9a5a6a90cc942e2490d2d6fefc12f4c1e0e`.
Timing report: `tmp/naip-canopy-20260926/channel-repair-cost.json`.

Rows30-1170: mean49.8100ms (20.0763 elapsed FPS), **p95 74.3482ms FAILS50ms**,
maximum143.25ms; one frame exceeds100ms in both the selected and full1200
intervals. This is an unpaired shared-host run, not proof of a causal slowdown
from removing trees. The target is unchanged; average20FPS alone is not a pass.
Logged drift includes changing positions, speed1.384m/s, wet1, support delta0cm,
ground penetration0m. These are sampled motion/contact observations only.

South Fork is still unfinished. This repair does not establish two-metre
shore clearance for every remaining tree, exact surveyed trunk locations,
HLOD correctness, full-route collision/shoreline continuity, sustained
performance, or geographic/visual acceptance. Later rivers remain queued.
