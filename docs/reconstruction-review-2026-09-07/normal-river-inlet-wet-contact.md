# Inlet streams versus exact initial wet support

Recorded 2026-09-17 UTC. This corrects a source-ownership inference and adds
certified conditional contact geometry. It is not an evolving pressure/front
law, native water integration or visual/performance acceptance.

## Existing-water intersections

The earlier inlet audit tagged a piece as `initial_ownership=wet` whenever its
original source triangle belonged to a wet pool. That does not establish that
the incoming stream intersects the pool's actual wet portion. The source can
be only partially wet, with incoming water confined to its dry portion.

`InletSweep.initial_wet_support_moments` now clips the ORIGINAL source polygon
at the original pool's datum plus stage offset. This sum remains rational before
clipping, so a large elevation datum cannot erase a positive thin film. The
strictly dry constant-bed equality case is explicit. It independently integrates
incoming depth moments0-3 over the wet and dry portions, preserving both and
their certified uncertainty. These are incoming-water moments, not the old
pool's depth moments, and do not define a merged state or add water to a pool.

On the unchanged registered South Fork block(12,8), all three streams previously
described as entering already-wet regions have **exactly zero upper-bound
incoming overlap with actual initial wet support** at the audited times. Their
initially wet source ownership is still retained separately. The three paths:

- `(8,598578) -> (12,598578)`
- `(8,598578) -> (8,196657)`
- `(8,197376) -> (8,599296)`

All10 representable conditional outward streams retain their original source
pieces and four moment bounds. The one positive exact stream below float
time/volume range and the two receding/fan cases remain unresolved, not deleted
or accepted. Combined moment uncertainty remains4.973799150320648e-14 of incoming
moments; no water, geometry, registration, source ID or gradient changed.

## First contact with static initial water

For the existing conditional sweep, transform a point to

    X = A + s D + u age.

It has positive incoming depth at time t exactly when s>=0, age>=0 and

    t > (B s / k)^3 + age.

The new `subcell_inlet_contact_time.py` clips each original wet polygon into
this exact coordinate frame and minimizes the convex cubic on its edges. The
objective's age derivative is one, so no interior minimum is missed. Edge
stationary points require only a square root; exact roots remain rational and
irrational roots have integer-derived rational bounds. Unresolved time bounds
raise instead of guessing a crossing. A zero-area reachable touch is not
reported as future positive-volume overlap. The returned time is an infimum;
the contact boundary itself has zero incoming volume.

The actual audit checks EVERY initially wet source, including ones outside the
current stream footprint. All10 conditional first-contact bounds lie beyond
the respective ORIGINAL isolated geometry windows, which already retain the
storage/face-knot and outward-branch limits. These extrapolated conditional
contact times are **not physical river predictions**: existing water is held
static and the constant-velocity inlet approximation is not valid beyond its
window. They show that existing-water contact is not the first event inside
these particular windows, not that real streams never interact.

Next physical work should address the earlier source crossings, stream-stream
support and branch transitions, then the coupled pressure/curvature/time law.
Do not create minimum-centered hydrostatic pools for the non-horizontal inlet
support, merge by source ID, extrapolate the conditional velocity law or use
this separation result to waive future collisions.

## Verification and source evidence

Final focused suite: **35 PASS**,3.68s. Independent controls cover quadrature,
all four moment complements, dry/fully wet/partially wet sources, large datums,
positive sub-float films, reversed polygon orientation, exact and irrational
edge minima, independent scalar minimization, zero-volume touches, before/after
contact, and insufficient-bound rejection. No old assertion or gate changed.

Original broad suite plus wet-support tests: **562 PASS / 13 FAIL**,198.45s,
zero errors/skips, one existing JUnit warning. Exact failed identities match
the prior suite: four nonbreaking energy, eight paired nonlinear energy, and
one legacy storage/face consistency failure. The seven new contact-time tests
are additionally included in the final35-test focused run, not this earlier
broad run. Those failures remain open.

Final actual audit verifies597 source/implementation hashes and preserves all
original pool volumes/momenta. Source authority remains distinct: captured DEM
and exposed rock versus submerged priors, interpolation and inferred flanks.
Exact rational coordinates do not add surveyed precision.

- Support report: `tmp/south-fork-inlet-wet-support-v1-20260917.json`,
  SHA256 `68c234ba8afa97526889536a29b0ad0c46d4935ba8a2382fa075013aeae8ec52`.
- Final support/contact report: `tmp/south-fork-inlet-wet-contact-v2-20260917.json`,
  SHA256 `53713ffebb348386ea769ac5437104cbbfd7bd54b1cb1f77aba94e34582452c9`.
- Focused tests: `tmp/inlet-wet-contact-focused-v2-20260917.xml`,
  SHA256 `cbb7a8d57713d0009984679838ddbd71d33ac171ce14a4abe3a9133af5557cde`.
- Broad tests: `tmp/inlet-wet-support-full-suite-v1-20260917.xml`,
  SHA256 `fa6f0bd242f46f0ea4192bc761864a89506db4fc343ba7580b6d85cef76499dd`.

## Concurrent validation

Original native SM5 session55459/editor36412 remains LIVE. Worker32072 completed
its transport permutations10/9; worker37836 continues its original batch. Do
not restart on the long compiler warning. All63 shader inputs remain frozen.
The previous fresh standalone54-test pass remains valid, not native acceptance.

Same hydraulic continuation51728/PID36872 reaches2150s/local7000. Both state and
86,720 exact-dry artificial-bank audits PASS on5,382,400 cells. Maximum depth
4.2688358655m, speed7.2820692243m/s, volume2,979,554.8012722693m3 and maximum
step mass residual1.5158152511e-8m3. Outflow95.5000869283m3/s exceeds
inflow45.3069545472m3/s: **not settled or promoted**. Next2200/local8000 needs
BOTH audits after completion.

- State: `tmp/control-ablation-2150s-state-v1-20260917.json`,
  SHA256 `1ce75fa86a29f82e5fabb83c0c68a66ba01168afe9d135a11718e44f9b6c87a5`.
- Banks: `tmp/control-ablation-2150s-banks-v1-20260917.json`,
  SHA256 `2499cce4ea2dcfec2faeae1d8cf4cf1e73d797ef5edcaadbe18813064f44fd16`.

No installed module, shader, map, material or gameplay behavior changed. Last
ordinary28.057157FPS/p9541.2354ms still fails30FPS. Terrain/boulders/collision,
convincing single-surface waves/froth, Colorado then Pacuare then Futaleufu,
Chilko/Zambezi/all-scene water, crew, normalization/regressions and release remain
open. Troublemaker remains a rapid inside South Fork, never a menu scenario.
