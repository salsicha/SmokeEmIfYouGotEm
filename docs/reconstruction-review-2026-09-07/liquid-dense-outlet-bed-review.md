# Dense flow exposed a point-versus-cell bed mismatch

September 10, 2026. Progress, not acceptance. South Fork and the original queue
remain incomplete. No saved scene promotion, final commit, or push.

## Longer native replay

The previous goal turn fixed dense NeighborQuery storage/view growth and passed
five dense native steps. This pass expands dense **compact-only** review to at
most120 steps/118 commits while preserving the existing8192 retained stage-record
ceiling. Full payload histories remain short; one explicitly selected dense step
may retain its full before/after payload for diagnosis. The driver now saves the
failed stage report when it catches an error, without changing failure status.

Build95068 succeeded. `liquid-native-dense-flow-v1` (session7184, terminal0)
completed its capture with6424groups, but the water replay is REJECTED:
the first failed GPU transaction is native step18, control `[0,64,718578,170]`.
Bit64 is rejected/invalid exit evidence. Sixteen earlier commits through step17
passed and retired1396 actual particles; the last accepted population was718539.
The170 in the failed transaction is a candidate count, **not** accepted exits.
Later native motion continued despite the rejected commit and is not valid flow
evidence. Final neighbor failures are downstream symptoms, not a recurrence of
the repaired storage-view bug. The auditor now reports the earliest failed
transaction before those downstream symptoms.

Build51159 succeeded. `liquid-native-dense-exit-debug` (session7867, terminal0)
retains only step18's full payload. This rerun's first failed transaction was
step15, so later outside origins are not independently valid crossings. It is
not a deterministic startup/flow success. `exit-diagnostic.json` identifies a
specific independently reconstructible false below-bed rejection:

- Owner3, east boundary, profile row224.
- Crossing Z593.0981684cm; exact triangle bed591.0981717cm.
- Particle remains2cm above the same contact terrain at start, hit and end.
- Cell-centre table bed601.0784178cm, almost10cm above the actual crossing bed.
- That row is wet and outgoing (stage654.9650311cm; normal−18.4221938cm/s).

The particle follows the slope correctly. Comparing it to a single midpoint bed
height for the entire50cm boundary interval falsely labels it below terrain.
Do not relax the exit tolerance, delete the particle, or flatten the terrain.

## Prepared continuous terrain intersections

`physics/scripts/build_liquid_face_bed.py` intersects unique original mesh edges
with each physical parent face. Every triangle-edge intersection becomes a knot;
the bed is linear only within those exact triangle intervals. There is no spatial
smoothing, arbitrary knot merging, missing-coverage clamp, or changed flux/stage.

Generated review data:
`tmp/south-fork-liquid-face-bed-20260910/physical_face_bed.json`.
Four faces contain303/305/1273/1273knots. Heights at five independent points in each
interval match the original barycentric mesh sampler within1.9539925233402755e-14m.
All intervals remain strictly positive after float32 encoding (minimum across
faces0.013671875cm). The new profile gives591.0981717321645cm at the diagnosed hit.

Source mesh SHA256:
`4b0dfeac342607c118e91b2182fced676b4fc0c9ea08c2ff70e2166818255d40`.
Existing boundary SHA256:
`2bcaf0db00766c38638b95edcf82ab8e2e605aab75ce270e51ff9ff3fa9369ff`.
The derived profile retains this provenance. The contact mesh includes inferred
submerged bed; this work does **not** establish new captured bathymetry.

299 liquid Python tests pass, including rotated/aligned triangle-face profiles,
missing-coverage rejection and invalid-frame rejection. The GPU classifier is
NOT yet connected to these knots; the diagnosed exit failure remains unfixed in
runtime. Previous engine13 regression evidence predates this pass's probe-limit
and diagnostic changes. All owned build/UE processes are terminal.

## Next implementation

Validate the exact face profile against the current parent/frame and source
geometry, upload it once to the exit plan, and query its bed at the *first actual
intersection*. Keep full-box/first-face/corner/invalid-origin rejection and the
prescribed outgoing row's flow/stage conditions. Pointwise bed must also reject
actual below-terrain crossings; do not merely replace an overly high threshold
with a permissive constant. Add sloping-bed GPU and independent CPU regressions,
then repeat the original long dense replay and raw P2G/conservation checks.

Long-duration/lifetime/repopulation, visible surface/foam/raft/collision/reference
and performance acceptance, later scenes, crew, cleanup and release remain open.
