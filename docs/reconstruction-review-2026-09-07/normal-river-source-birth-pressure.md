# Original source wet-front birth geometry and pressure limit — September 15

This supplies missing **one-sided geometry and pressure-metric coefficients**.
It does not supply a conservative wet-front force, mass update, full-model time
step, native integration, or new gameplay/visual acceptance. The original bank
nonlinear stage still refuses unresolved activation; no gate is removed.

## Exact geometry at zero water

`subcell_source_birth_geometry.py` integrates the original rationally retained
source polygons before their first positive elevation knot. These rationals
retain the supplied binary geometry, not extra measurement precision.
For height `e` above the source minimum, depth moments are exact polynomials.
The leading stored-volume power is 1 for a flat start, 2 for an edge start and
3 for a point start. Edge-start cubic corrections are retained; subdivision of
a ramp rectangle cancels its two fan-triangle corrections exactly.

The class supplies exact moments, stage derivatives, the full local kinetic
Gram polynomial, the scaled-jet Gram limit, and source-face contact thresholds.
At zero, volume and Gram are zero. For a flat start, the zeroth moment is the
explicit **right-limit wet area**, not a claim that positive water exists.
Negative directions at zero and heights beyond the original birth interval
reject. There is no inverse dry mass, depth floor or added epsilon water.

The scaled jet is `(e*divergence, velocity_x, velocity_y)`. In the point case,
with original bed gradient `b`, the limiting Gram divided by volume is

```
[ 3/10       -3*b_x/4      -3*b_y/4 ]
[ -3*b_x/4    3*b_x*b_x     3*b_x*b_y ]
[ -3*b_y/4    3*b_x*b_y     3*b_y*b_y ]
```

Thus a divergence growing as `1/e` retains vertical inertia; setting the dry
Gram to zero before taking the limit would discard it. Source-face area has
its own first positive knot: subdivision by an opposing trace can introduce
an earlier face knot without changing the source storage interval. Exact face
contact also reports the volume stored before the stage reaches a higher edge;
this is not a travel time or a prescribed mass flux.

## Original two-pole pressure boundary limit

`subcell_source_birth_pressure.py` derives the single **point-birth** limit with
old volume/physical momentum fixed and bounded newborn physical velocity.
Flat/edge pressure limits are explicitly unsupported, not silently treated as
point births. No new dispersion coefficients or global iteration budgets are
introduced. Existing old-state poles retain 40 CG; the new local Schur solve
is only 2×2. Stale state and unrepresentable coefficients reject.

For one original pole, let `A=I+beta*Q`, `z=A_old^-1*q_old`. The normalized
operator's newborn principal block tends to `D`, and its old/new cross block
is `sqrt(e)*B` to leading order. Original wet faces and explicit block walls
determine these coefficients; other dry support does not become a wall.
With `v=B.T*z`, the physical kinetic-energy height slope is

```
S = -1/2 * sum_over_original_poles(
        alpha*beta * v.T*(I+beta*D)^-1*v)
E(e) - E(0) = S*e + higher-order terms
V_new(e) = c*e^3
```

This follows from the Schur complement of the original pressure operator and
the existing inverse-metric energy, not a fitted finite-difference force.
When `S` is nonzero, the fixed-old-state energy derivative with respect to new
volume is singular. The corresponding singular pressure **auxiliary** variable
is not an unbounded physical layer velocity. These are boundary properties of
the current discrete metric, not a derived physical river evolution. Coupled
front transport and its independent physical work still have to account for
them; ordinary fixed-wet Gauss stages cannot simply be enabled at zero mass.

## Actual original bank evidence

The shared source loader keeps the original registered origin arithmetic,
600.000000000002 s atlas, volume/momentum and file-hash checks. Block `[12,8]`
uses 16 original wet pools and **reflecting exterior test cuts**, not the natural
open river. The old nondispersive receiving rates only locate candidate birth
sources; they are not accepted as full-model pressure/energy fluxes.

- 24 receiving original-source regions, all point births (`V ~ e^3`).
- 24 incoming faces; 14 have no immediate contact with the source's first wet
  patch. Filling to their higher edge is a distinct contact threshold.
- 16 receiving regions have authority 3 (exposed rock); four mix 3/5 and four
  have authority 5 (inferred flank). They are not all measured bathymetry.
- 360 exact-rational independent moment/face integral comparisons; receipt
  reassembly error exactly zero. Original water is unchanged.
- 10 receiving regions have a nonzero derived pressure height slope.
- Final report: **545 source/implementation hashes match** at completion and
  in a separate post-run check.

The strongest predicted coupling was selected before finite-volume comparison:
original cell 188, source triangle 598578, authority 3. Analytic slope is
`-8.118284967998143e-5`. Independent positive-water pressure energies hold all
old V/P fixed and add the receiving volume only as a geometry probe, not a time
update. The first three heights gave 30.58%, 15.29%, and 7.65% slope error;
report v2 **FAILED** the 1% criterion and is retained.

Extending the same geometric refinement sequence to seven heights gives final
slope `-8.15709501831809e-5`, error `3.88100503199469e-7` (about **0.478%**),
with error approximately halving on every refinement. The final probe volume
is `1.290807064937463e-16 m3`; it is not a numerical minimum or gameplay water.
Original pressure residuals are at most `1.874e-16` and positive-energy
contraction error at most `1.111e-16`. Neither the 1% limit nor the original
pressure/energy gates changed.

## Verification and retained scope

New component/audit tests: **25 PASS**, including exact clipping, subdivision,
sub-ULP water, flat/edge/point limits, full positive-water pressure operator and
energy comparisons, nonzero and zero old momentum, bounded newborn velocities,
state immutability, malformed receipts and unsupported birth cones.

The original channel rate audit's **every non-hash field is identical** after
extracting the shared loader. The original bank time request still rejects
`Complete original wet support required; source activation is unresolved`, with
no returned rate or time state. This is deliberate non-promotion, not a pass.
The broader source suite completed **393 PASS / 1 retained FAIL** in 135.66 s.
The failure is the original legacy storage/face consistency test, maximum
coordinate mismatch `1.77635684e-15`; no tolerance or expectation changed.
Both channel AND bank loader reports match every previous non-hash field.
All **464 protected scene/source/capture/profile/actor hashes are unchanged**.
Fresh paired-stress/constant-velocity energy regressions completed **15 PASS /
12 retained FAIL** in 7.51 s, without waivers. These birth coefficients are not
fixes or replacements for those evolution paths.

Evidence (all generated outputs remain ignored):

- `tmp/source-birth-all-unit-v1-20260915.xml`: 25 new tests.
- `tmp/source-birth-full-suite-v1-20260915.xml`: 393 PASS / 1 retained FAIL.
- `tmp/source-birth-retained-energy-v1-20260915.xml`: 15 PASS / 12 retained FAIL.
- `tmp/south-fork-source-birth-bank-v1-20260915.json`: initial geometry-only report.
- `tmp/south-fork-source-birth-bank-v2-20260915.json`: retained coarse pressure
  failure, SHA256 `602eb880fa1d644c3db6d4052fcbcf3ed478452107be47f92cc98a133aed4c10`.
- `tmp/south-fork-source-birth-bank-v3-20260915.json`: final geometry/pressure
  report, SHA256 `e49848321d56fc16d20a0dda37381510980010014de0f90a906ecbacb52d1997`.
- `tmp/south-fork-block-loader-channel-v1-20260915.json`: exact report-field A/B,
  SHA256 `0f1be2e12ae76260799aa648e1bb33a4a8d24f092464e415a2992ea127407962`.
- `tmp/south-fork-block-loader-bank-v1-20260915.json`: retained activation rejection.

All owned numerical jobs are terminal. NEXT: couple these source birth/contact and pressure-work terms to conservative
full-metric front forces, including simultaneous regions and flat/edge cases;
then finite-time/open/native/shared-surface qualification and actual motion
comparison. No new engine/FPS/visual improvement is claimed. South Fork's last
ordinary run remains 12.257837 FPS / p95 98.2909 ms, failing 30 FPS. Colorado,
Pacuare, Futaleufu, Chilko/Zambezi water reviews, crew, normalization, retained
regressions and release remain open.
