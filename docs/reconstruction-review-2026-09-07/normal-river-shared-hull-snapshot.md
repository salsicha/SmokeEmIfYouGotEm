# Shared authored hull snapshot checkpoint

Reviewed 2026-09-16 UTC. This is geometry-source infrastructure, not full-hull
collision, visual acceptance, or a 30 FPS pass.

## Change

The opt-in `-RaftSimSharedHullReview` publishes the complete authored, deformed
raft surface from the same successful fixed substep used by the renderer:
five material sections, 26,610 vertices and 38,344 indexed triangles. It retains
source indexing, including seams and rigging, without welding or proxy fitting.
The review requires the production CPU mesh and unit actor scale.

Prepare and commit are separate. Invalid geometry or a later rejected contact
step cannot replace the published hull or committed renderer inputs. This is
not a rollback guarantee for every internal D4 state variable. The existing
six-sphere contact implementation is unchanged; full-surface contact is pending.

Geometry still updates every substep. Shading directions are rebuilt once per
rendered frame from committed inputs. Repeated current-segment calculations are
hoisted out of per-vertex loops, including the ordinary deformation path; there
is no temporal memoization or reduced simulation frequency.

## Verification

- Win64 Development Editor build succeeded (156.37 seconds). Existing D6
  double-to-float damping warnings remain.
- Final targeted native suite: **16 passed, zero warnings, failures or unrun
  tests**. Includes authored hull identity, snapshot transaction, flexible fabric,
  source-triangle contact, sustained support and raft dynamics regressions.
- Four authored-mesh phases compare 106,440 vertices and 153,376 faces. Position,
  normal and tangent comparisons against retained repeated-evaluation arithmetic
  are exact, including deferred shading reconstruction.
- Same-input full-shading paired timings, eight pairs in each order:
  repeated/prepared means 8.836225/6.350663 ms and 9.299849/6.534925 ms.
  These are local microbenchmarks, not gameplay frame-rate qualification.
- All 464 protected source/package hashes and the original raft FBX/asset hashes
  remain unchanged.

Local report: `tmp/shared-hull-native-v3-20260915/index.json`.
SHA-256: `505ed7b4968bcbec9bd582a9fc2ae813463c91c2aea9ebc63f4310d690f17367`.
Generated reports, logs, captures and builds remain ignored, not committed.

## Open acceptance

The earlier dense snapshot implementation completed a South Fork replay with
exact source/submitted CPU mesh agreement, but cost about 5.75 ms per fixed
substep. That replay does **not** validate the final optimized implementation's
in-game cost: a fresh optimized replay and uncontended frame profiling remain.
Full-surface continuous contact, initial overlap, packaged source availability,
normal-play promotion, terrain/water/froth appearance and the 30 FPS target are
still open. This checkpoint does not complete the remaining-work plan.
