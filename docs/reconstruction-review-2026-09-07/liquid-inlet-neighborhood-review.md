# Actual inlet neighborhood and reproducible source diagnostics

September10,2026. This goal turn is progress, not a verified wait or scene
completion. The full South Fork and later queue remains active.

## What was actually captured

The unseeded `liquid-native-inlet-surface-step306` capture (UE32962 terminal0)
retained the complete step306 before/after native payload. It did NOT fail
through308. The same local birth sequence8/1577 was roughly4m away from its
position in the earlier failed run. An equal birth sequence across different
generations is not an equal physical trajectory; no such equivalence claimed.

Compiled source selection used unseeded `rand_int`/`rand_float`. The new optional
`-RaftSimRegionalSourceSeed=173193` sets deterministic source sampling on the
transient native emitter, with owner-specific seeds `base+7919*owner` and zero
component seed offset. Range0..1000000, dense mode only. The default randomized
mode, all prepared source weights/positions/velocities/rates and mass/exit gates
are unchanged. This is diagnostic reproducibility, not a claim that parallel
floating-point fluid solves become bitwise deterministic, and not a substitute
for passing randomized physical tests.

Build82318 succeeded32.86s. `liquid-native-seeded-inlet-flow` (UE79903 terminal0)
fails atstep367, owner8 birthsequence1638, westface0,row136, Z915.00042cm versus
prescribedstage878.86890cm. Its compiled weighted sampler uses the actual
particle UniqueID and emitter seed, not a constant same location for all births.
All12 configured owner seeds are retained in `stages.json`.

The same seeded replay with a fullstep367 snapshot,
`liquid-native-seeded-inlet-step367` (UE57028 terminal0), first fails at368.
Same birth identity, same face/row and same type of above-stage crossing; small
float differences shift the crossing one step. This is sufficient to obtain
the *actual same-run* immediate pre-failure neighborhood, not to claim exact
cross-run numerical determinism.

## Same-generation bit-exact link to the failed particle

`inlet-neighborhood-linked.json` resolves identity8/1638 in all12 native owner
payloads at367. Its final position is bit-for-bit equal to the first-rejection
latch's step368 starting position. The step367 atomic commit succeeds with
control `[1,0,699152,113]`. Thus this neighborhood precedes the first failure;
it is not a polluted later snapshot or an assumed particle storage index.

- Position `[9436.3037109375,6731.484375,915.2962646484375]`cm.
- Height36.4274cm above prescribedstage; nearest particles17.206/19.816/22.711cm.
- There are324 other particles within2m.
- A25cm distance graph links5 particles, all above prescribedstage.
- A35cm graph connects325 particles back below stage, ranging Z800.271–933.762cm.
- A50cm graph gives the same325-particle set.

These are geometric connectivity diagnostics, NOT a disconnected-spray detector.
The actual cell spacings are50/50/33.333cm. The evidence does not support merely
discarding this water as independent airborne spray. It identifies elevated
water near an artificial upstream plane that needs consistent free-surface
boundary treatment, not just an extra accepted-exit label or a reflecting wall.

The diagnostic also supports mixed full/compact histories: actual four-word
control buffers are read from validated paths for a full snapshot, rather than
silently skipping the snapshot when finding the first failure. Original
dense/P2G acceptance still rejects failed commits and does not accept mixed
full/compact captures as sustained-flow evidence.

## Physics next, not an acceptance workaround

The source construction sets sphere jitter scale to zero, but that setup code
alone does not prove every runtime bound parameter. Verify actual runtime
source scale and birth positions when investigating source geometry. The
prepared nominal face integral is approximately45.063m³/s inward and47.214m³/s
outward using its midpoint rows; exact pointwise bed/source integration differs.
The earlier112–124m³/s native startup outflow therefore must not be called
calibrated or steady discharge.

Next required implementation is a consistent bounded free-surface/open-boundary
coupling for the primary fluid, with actual incoming/outgoing mass and momentum
accounting, source/buffer support and a well-defined water-level condition.
Do not infer an isolated-spray policy from a height threshold alone. Keep the
current failure visible until the replacement physics and independent tests
justify it. A characteristic or buffer formulation is a design candidate, not
yet implemented or validated here. The
[DualSPHysics formulation](https://github.com/DualSPHysics/DualSPHysics/wiki/3.-SPH-formulation#315-open-boundary-conditions)
provides primary-source context for support-width buffers and dynamic water
levels, but does not validate this project's FLIP boundary implementation.

324 Python liquid tests pass (neighborhood connectivity and mixed full/compact
controls included). Engine18484 terminal0: all15 regressions pass with no
warnings/failures. All handles from this pass are terminal; a process check
found no UE/python/compiler running. No production scene changes, rendering
acceptance, final commit or push. Full queue and all original scene requirements
remain incomplete.
