# Simultaneous conditional inlet-stream separation

Recorded 2026-09-17 UTC. This closes a geometric interaction ambiguity inside
the original inlet approximation's windows. It does not implement the coupled
pressure/front law or accept playable water, source transitions or30FPS.

## Exact curved-footprint bounds

The existing conditional stream uses original edge A+sD, constant velocity u,
entry-time root r and observation-time root R. Its footprint in coordinates
X=A+sD+u*age is

    0 <= s <= k R/B,
    0 <= age <= R^3 - (B s/k)^3.

The upper curve is concave. Chords bound it from inside; tangents bound it from
outside. `subcell_inlet_stream_overlap.py` builds both rational polygons and
clips them against each other and the exact original rectangular source domain.
No sampled depth mask, approximate distance test, welded vertex, epsilon water
or float-area cutoff determines the result.

- Positive INNER intersection area proves positive overlap. Its rational
  interior witness is checked against BOTH original curved support inequalities.
- Zero OUTER intersection area proves separation, including zero-volume touches.
- Otherwise the bounded refinement continues, or returns **unresolved** with
  both area bounds. Exhausting the segment budget never means disjoint.

The source audit now records original inlet velocity and height coefficient,
so the geometry is reproducible without reconstructing a direction from the
reported area. Missing stream provenance raises. The two explicitly unsupported
receding/fan records remain listed separately, not silently filtered away.

## Same time and original window closures

The former per-stream captures have different observation times. The new audit
never intersects those mismatched snapshots: each pair first uses the earlier
of its two original valid time roots. This is pairwise evidence, not one evolved
global state.

A second comparison bounds each pair at the COMMON original window limit,
retaining source/storage knots and outward/edge branch constraints. This is a
geometric endpoint closure, not a physical step at an excluded branch equality.
Because s and age for a fixed XY point do not depend on observation time, the
condition time>(B*s/k)^3+age makes these footprints nested in time. Thus zero
upper intersection at the closure proves separation at EVERY earlier common
time, not just at sampled frames. For positive closure intersections, the code
also reports an explicitly earlier rational time at which the same witness
lies strictly inside both original supports.

## Actual South Fork result

Original registered block(12,8),600-second input water,13 immediate faces:

| Comparison | Streams | Pairs | Proven separated | Positive | Unresolved |
| --- | ---: | ---: | ---: | ---: | ---: |
| Common original observation time | 11 | 55 | 55 | 0 | 0 |
| Common original window closure | 11 | 55 | 55 | 0 | 0 |

Both comparisons retain the positive exact stream whose time/volume falls
below float range. It remains unrepresentable for physical updates. The other
two receding/fan cases have no accepted outward geometry. All55 pairs separate
already with the coarsest conservative outer polygons; a coarse polygon is not
being presented as the real water shape. Original source fragments exactly
cover the audit rectangle, and any positive witness would require an original
source owner.

The previous exact initial-wet-support result remains unchanged: three source-
ownership false positives, zero incoming overlap with actual initial water.
All10 representable stream moment partitions remain unchanged, with combined
relative uncertainty4.973799150320648e-14. All598 source/implementation hashes
and original pool volume/momentum preservation are checked by the final audit.
DEM/exposed-rock measurements remain separate from submerged priors,
interpolation and inferred flanks; exact arithmetic adds no measured precision.

This result rules out premature merging as the NEXT fix for these windows.
Next implement source-face transport and the branch transitions for the
non-horizontal incoming support, with compatible pressure/curvature and its
time variation. Do not replace that support by a minimum-centered hydrostatic
pool or extrapolate the constant-velocity law beyond its bounds. Future stream
interaction and the unsupported receding/fan regimes still require physics.

## Tests and retained artifacts

Final focused suite: **54 PASS**,4.48s. It covers independent exact incoming
area bounds, strictly interior witnesses, opposite flows touching only at an
edge, disjoint curved footprints with overlapping bounding rectangles, explicit
unresolved cases, positive sub-float intersections, exact domain clipping,
mismatched-clock rejection, both original window limits, strict earlier-time
witnesses, branch-limit rejection, source provenance, malformed domain/budget
rejection, translation/orientation and earlier wet-support/contact controls.

Broad regression: **588 PASS, 13 FAIL**, 601 tests in 199.280s, no errors or
skips. All 13 failure identities match the earlier inlet-sweep baseline; this
does not resolve the existing energy-conservation and source-geometry failures.
JUnit: `tmp/inlet-stream-overlap-full-suite-v3-20260917.xml`, SHA256
`fa809d90d4fd9b7d551617c2a2e6bcac5c0744612004ec21f7c4b76d10ee7e5c`.

- Final actual report: `tmp/south-fork-inlet-simultaneous-window-v3-20260917.json`,
  SHA256 `0e27628ad5a0b72b5d74b42d4290d1589db9eb6b2b4435792999756cc3cd1305`.
- Focused JUnit: `tmp/inlet-stream-overlap-focused-v3-20260917.xml`,
  SHA256 `57f81c732667bbf79c4dc8c314d85f659035b5954054ebe01301010404c1e472`.
- Earlier observation-only and closure reports remain in ignored `tmp`; they
  are not substituted for the final provenance/rejection-checked V3 report.

## Other live work remains open

Original native SM5 replay55459/editor36412 and worker37836 remain LIVE; all63
shader inputs are frozen. Worker32072 completed its batch normally. The last
fresh standalone54-test transport/pressure pass is not native/full-step approval.

Same hydraulic continuation51728/PID36872 reaches2200s/local8000. Both state and
86,720 exactly dry artificial-bank audits PASS on5,382,400 cells. Maximum depth
4.2414243375m, speed7.2317122163m/s, volume2,977,001.415059952m3; maximum step mass
residual1.5158152511e-8m3. Outflow96.5992060141m3/s versus45.3069545472m3/s in:
**not settled, calibrated or promoted**. Next2250/local9000 requires BOTH audits.

- State: `tmp/control-ablation-2200s-state-v1-20260917.json`,
  SHA256 `2ef41b14fe4162bd7dc8030ecc81c7e95665aeb49cd6f0e1b99576a9ce2aa67f`.
- Banks: `tmp/control-ablation-2200s-banks-v1-20260917.json`,
  SHA256 `e3c6939e1bee44056fda7198882d9c8256da971f3a876ba96d81eb72b064e353`.

No installed module, shader, material, terrain or playable behavior changed.
Last28.057157FPS/p9541.2354ms still fails30FPS. Full physical/visual/terrain/
boulder/collision work, Colorado->Pacuare->Futaleufu, Chilko/Zambezi/all-scene
water, crew, normalization/regressions and release remain open. Troublemaker
is only a South Fork rapid, never a menu scenario.
