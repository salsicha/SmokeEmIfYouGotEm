# Geographic liquid registration: allocation, forcing and contact

September 10, 2026. South Fork remains incomplete. This is an isolated 21 m
liquid diagnostic in the corrected geographic terrain, not whole-rapid
integration, reference accuracy, conservation or photorealistic acceptance.

## Evidence that changed the implementation

The larger fixed water carrier still looks like a smooth folded sheet. A
1.5 m lattice audit found a maximum analytic-crest interpolation error of
0.122958 m (RMS 0.003448 m, 118,175 samples), against a maximum continuous
crest of 0.486436 m. The existing fine GPU crest path preserves more shape,
but the inspected same-pose image still has a homogeneous white face. Neither
image warrants promotion. Captures are in `unreal/Saved/Screenshots` under
`troublemaker_fixed_crux_side_20260910` and
`troublemaker_fixed_crux_fine_20260910`; numeric audit is
`tmp/south-fork-fixed-crux-crest-audit.json`. That audit covers the shared
analytic crest, not all mean-surface or render-only displacement terms.

Bringing the existing 3D liquid into the corrected terrain exposed a different
bug. The source frame requires a reflection, not merely a yaw change. Applying
actor scale `(1,-1,1)` made Niagara multiply its allocation extents by the signed
scale. Its native render volume became **136 x 2 x 50**, while the custom
reconstruction expected 136 x 136 x 48. Its grid transforms use a quaternion
rotation, which cannot encode reflection. Correct actor transforms alone were
therefore insufficient. Additionally, source tables and terrain-query tables
retained their original ENU-derived coordinates.

## Correction

The transient geographic candidate now uses a positive-scale Niagara actor
with negative source yaw. It adapts coordinates at the source/query boundary:

- Incoming position offsets and velocities reflect Y; offsets are not translated
  twice because the stock source module adds the owner position.
- Initial absolute particle positions reflect Y and restore the documented
  parent-frame offset; initial velocities reflect without translation.
- Primary pressure/contact queries inverse-transform into unchanged captured
  triangle tables. Closest points and normals transform back to world space.
- Inflow face selection uses canonical coordinates; returned grid-local velocity
  changes lateral sign. Outgoing pressure-stage queries similarly distinguish
  canonical coordinates from reflected grid indices.
- Secondary swept terrain contact inverse-transforms both segment endpoints.
  Domain clipping and particle integration remain in the actual Niagara frame.
- The collision mesh retains its required reflected transform. The full
  geographic terrain is not translated to match the old isolated fixture.

The source JSON, captured returns, inferred bed, forcing magnitudes and saved
Niagara assets are not rewritten. The adapter is opt-in, requires the documented
control-centred rebase, and operates on the transient review system. Python's
camera/probe frame also uses the same float-representable yaw accepted by the
engine; the original double-precision source angle remains recorded. This fixes
a measured 0.000114 cm comparison error without relaxing the probe tolerance.

## Actual engine evidence

Final capture: [v6 report](liquid-geographic-registration-v6/capture.json),
[engine log](liquid-geographic-registration-v6.log). RHI validation enabled,
720 requested steps, 12 simulated seconds, no engine error lines. Blocking
capture wall time (83.984 s) is **not a frame-rate measurement**.

| Check | Evidence / result | Scope |
| --- | --- | --- |
| Actual grid | 68 x 68 x 24, successful native readbacks | No signed-scale collapse |
| Actual shader bindings | Positive 2231.25 x 2231.25 x 800 cm extents, expected axes and translated centre | Material/actor agreement |
| Live reconstruction | 758 updates, 30 distinct decoded motion frames, max position error 0.000001962 m, zero diagnostic counters | Data pipeline, not natural motion |
| GPU step ordering | 714 first-stage dispatches and reconstructions, 714 positive GPU time steps | Single-substep capture; no batched-history claim |
| Quadratic transfer | 57,389 actual particles, max moment error 0.000004089 against independent grid replay; unchanged 0.001 tolerance | Transfer parity, not mass conservation |
| Foam transport | Active and paused independent replays pass existing tolerances | Shared surface transport |
| Sampled secondary contact | 117,310 sampled positions, zero below-bed/missing-bed/out-of-domain cases | Captured instants, not every trajectory |
| Paused phase alignment | 0 / 24,737 spray particles inside rendered water; 13,671 / 13,671 bubbles inside; foam absolute-distance p95 0.932 cm | Sampled phase labels, not sprite appearance |

The final primary snapshot has 57,287 in-domain terrain probes with no missing
ground or penetration. **102 primary particles are outside the physical domain**
at that instant; do not misreport this as a closed mass budget or complete
open-boundary verification. The old render-target SimCache warning remains;
actual GPU volume readback, rather than cached material data, verifies the field.

Audits beside the capture: `clock_audit.json`, `stage_order_audit.json`,
`affine_audit.json`, `live_audit.json`, `current_foam_audit.json`,
`secondary_audit.json`. The live audit's conservative `secondary_motion_verified`
field remains false; the separate identity-tracking audit records emission,
motion and exact paused state, without promoting exhaustive contact or realism.

Build succeeded. `RaftSim.Editor.LiquidGeographicFrame` passes cleanly with the
geographic flags in `engine-liquid-geographic-frame/index.json`. The two Python
frame unit tests pass. Scoped `git diff --check` passes. Default-frame regression
also passes cleanly in `engine-liquid-legacy-frame/index.json` (one test, zero
warnings or failures). All build, engine and audit processes for this pass are
terminal.

## Rejected attempts and remaining work

Earlier registration attempts are retained: missing optics flag; missing fluid
plugin; float-angle comparison mismatch; v4 signed-scale grid collapse. V5 fixed
the primary grid/contact but omitted the separate secondary sweep conversion;
it is not the selected contact implementation. V6 includes that correction.

Viewed v6 `terrain_0720.png`: the water has real 3D relief but remains too glossy,
lumpy/crumpled and bounded by exposed rectangular test edges. It does **not**
establish the footage's returning breaking roller or the hole/right/left
sequence. The surrounding grey diagnostic terrain also has conspicuous dark
faceted/shadowed regions. No aesthetic pass is claimed.

Next: carry the now-registered simulation into a larger, source-aligned playable
domain covering the actual obstacles and turns, with one continuous river
surface and matched hydraulic exchange; evaluate physical overturning/return
flow against the real reference and then benchmark the actual playable scene.
Do not spend further isolated-patch shading iterations in place of this
whole-rapid requirement. The 21 m patch still contains no recovered-rock
vertices inside its physical bounds, as recorded in the reference coverage
review. Missing surveyed submerged bathymetry/discharge remains explicitly
inferred, not manufactured measurement.

No production map replaced or commit made. Geographic review map SHA256 remains
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
The full South Fork -> Colorado -> Pacuare -> Futaleufu and all-scene/crew/release
queue remains active.
