# Changing-volume pressure on exact wet pools

September 14, 2026. **Research derivative verified; playable scene not accepted.**

The previous commit supplied independent-volume probes within the original
source-topology interval. This work supplies the analytic pressure-matrix,
dual-energy and physical-momentum directions those probes can verify. A changing
pool's wet-face area, local kinetic geometry, divergence weights and BOTH mass
normalization factors must change together. Differentiating just the local
terrain tensor would omit real work from the transport equation.

No native solver, map, water state, captured geometry, material, scenario or
quality setting changed. There is no new motion capture or FPS result. The latest
ordinary South Fork visual review and 30 FPS / p95 33.333333 ms gate still fail.

## Implementation and independent checks

`physics/scripts/subcell_wet_pool_pressure_rate.py` adds:

- An analytic shared-harmonic-column directional integral. For lower wet depth
  `t` and stage difference `d`, its stage partials are
  `0.5 * (1 +/- d/(2*t+d))^2`. The integral includes partial wet faces; a moving
  shoreline contributes no boundary term because the harmonic column is zero
  there. A convergent small-argument series preserves tiny upper-stage partials.
  Equal stages and flat faces have explicit stable expressions. Level-dry events
  are not assigned an arbitrary two-sided derivative.
- `WetPoolPressureRate`, differentiating the same physical-velocity divergence
  and transpose, exact source-triangle Gram tensors and `sqrt(volume)` factors.
  For `jet=(D*u,u)` and `u=q/sqrt(V)`, it includes `D_dot*u + D*u_dot`, the local
  `G_dot*jet + G*jet_dot`, the differentiated transpose and output normalization.
  It computes `A_dot*q` at **fixed normalized q**, not at fixed physical velocity.
- `dual_direction`, differentiating BOTH original pressure poles with the same
  40-CG budget and 2e-5 true-residual gate. For `z=A^-1*q`, it solves
  `z_dot=A^-1*(q_dot-A_dot*z)`. It then differentiates the dual kinetic energy
  and physical momentum, and adds the exact pool hydrostatic potential direction.
  Caller-specified volume/velocity directions are not inferred fluxes or motion.

The new tests cover both poles, periodic flat variable depth, sloping bed,
disconnected pools with shared faces and reflecting walls, zero/linear
directions, symmetry, independent perturbed-state solves, dual energy and
physical momentum, topology rejection and datum-relative depths down to 1e-150.
A bounded sloping fixture shows the centered probe error reducing by more than
3.9 per step halving before roundoff; this is not a time-evolution accuracy test.

## Real-source failure found and corrected

The first actual-source run failed in the coverage oracle introduced with volume
probes. Source triangles clipped independently can overlap by a few float units
at face endpoints. One example was the interval
`[0.016861181564617966, 0.016861181564618022]` within pool 170.
A separate overlap between pools 239 and 240 lay entirely above both water
stages on a dry ridge. Neither constitutes a new wet connection.

The independent knot-sweep coverage oracle now includes shoreline knots, checks
interval containment without requiring a representable midpoint, excludes dry
trace portions, and unions compatible same-pool overlaps only for its reference
area. It retains the existing 1e-9 source-face height agreement tolerance and
rejects incompatible or multiply owned **wet** intervals. The actual source
coordinates, face assembly and pressure matrix are unchanged; their aggregate
area error is still measured against the union-area oracle. Regression tests
retain a one-ULP overlap and reject distinct wet owners and conflicting heights.

## Actual South Fork evidence

Final report: `tmp/south-fork-pool-direction-v3-20260914.json`

SHA256: `294783cb9751eac545fde36e749fa58625acfd970ffe56c02bedb4ab72cf396b`

The audit uses the original 600-second atlas, exact registered source mesh,
original 256-cell patch and original volume/velocity arrays. It checks source
hashes before and after. The three split cells still require 258 positive pools
across 255 wet cells. Cell 158 remains dry and has no invented pressure unknown.

The controlled volume direction is proportional to volume and a deterministic
pool-index pattern, with its volume-weighted mean removed. Its sum is
-5.10702591327572e-15 m3 in floating-point arithmetic. Relative directions range
from -0.20068570657741755 to 0.19930086437301017. Prescribed velocity directions
are also nonzero. This is a directional probe, **not an actual mass update**.

| Quantity | Final evidence |
| --- | --- |
| First original pole / directional solve true residual | 4.4020e-13 / 3.4035e-13 |
| Second original pole / directional solve true residual | 2.4649e-16 / 2.4622e-16 |
| Iteration budget | 40, unchanged |
| Maximum pool-scaled matrix-direction discrepancy across probes | 3.4965e-10 |
| Maximum physical momentum-direction discrepancy divided by each pool's volume | 6.3777e-10 |
| Maximum scaled total-energy directional discrepancy | 1.8538e-8 |
| Static pressure dense-solution discrepancy | <=6.7314e-13, unchanged |
| Shared/wall column partition discrepancy | <=6.4194e-16 / 4.4314e-16 |

Verification perturbations are 1e-4, 5e-5 and 2.5e-5. The energy differences are
already affected by subtraction roundoff at these scales; they do not establish
a refinement rate. All are within the explicit 1e-6 differential-consistency
gate, which is separate from and does not replace the existing nonlinear
conservation gates. No topology-interval step shrinking was needed on this run.

The analytic total energy direction is -12.833911294742329, deliberately not
zero: the chosen direction is not a conservative dynamical solution. Its
negative sign is not evidence of physical dissipation or breaking waves.

Final subcell/triangle suite: **98 passed**, including 26 new direction tests,
in 8.62 seconds. Report:
`tmp/subcell-pool-direction-tests-v2-20260914.xml`.

Retained pressure/stress/constant-velocity suite: **34 passed, 12 failed**,
exit 1, in 8.79 seconds. All eight paired-base nonlinear energy failures and four
legacy constant-velocity failures remain visible and unwaived. Report:
`tmp/subcell-pool-direction-retained-gates-v2-20260914.xml`.

All 464 protected source/capture/map/profile/actor hashes were checked and remain
unchanged. Mixed source vertex authority is preserved. Inferred submerged beds,
connecting flanks and interpolated gaps have not become measured bathymetry.

## Still required

Next, use this complete changing-volume metric work in compatible pool mass,
advection and exact bed-force equations. Resolve flux into currently unowned dry
regions and source-topology events explicitly; restricting all transport to
common-wet pressure connections would silently prevent real wetting. Then verify
finite-time behavior, wet fronts, open/refinement boundaries, the full nonlinear
gates, native/shared-surface integration and actual motion/performance.

South Fork remains first; Colorado, Pacuare and Futaleufu follow in that order.
Chilko/Zambezi and other all-scene water reviews, crew realism/fit/animation,
normalization, regressions and release qualification remain open. Troublemaker
remains a rapid inside South Fork, not a menu scenario. The full goal is active.
