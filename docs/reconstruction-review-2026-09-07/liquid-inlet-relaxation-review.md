# Bounded inlet relaxation candidate — not scene acceptance

September 10, 2026 (engine log timestamps are UTC September 11).

The preceding user-status turn was no implementation progress. This continuation
implements a candidate upstream reservoir coupling for the measured failure in
[the same-run inlet neighborhood](liquid-inlet-neighborhood-review.md).

## Physical treatment and limitations

The old correction acted only at a submerged inlet-plane crossing. The actual
first-failure particle was 36.43 cm above the prescribed stage, and the retained
neighborhood did not establish detached spray. Deleting or reclassifying that
particle would not resolve the primary-fluid boundary inconsistency.

The transient registered-terrain installer now adds a compact normal-velocity
relaxation band at the physical parent inlet, never at internal regional cuts.
Width is four normal grid cells, capped at one quarter of the physical extent
(2 m for the current parent). Only rows with strictly positive prescribed inward
velocity and a wet stage above the original pointwise triangle bed qualify.
Primary water above that stage is included; stage and particle heights are not
clamped. Nearest-face ties, dry rows, invalid origins, roof/floor crossings and
all outgoing rows are untouched by this band. Vertical and tangential motion
are unchanged. The prior submerged plane condition remains as a final inlet
boundary constraint; the exit, identity, mass and whole-commit gates are intact.

For distance d, width L and original boundary depth h, q=clamp(1-d/L,0,1),
sigma=4 sqrt(g h)/L q²(3-2q). Normal velocity obeys du/dt=sigma(U-u), with
the coefficient held constant over each native substep. Endpoint attenuation
exp(-sigma dt) updates velocity; its integrated average updates displacement.
The average uses a small-argument expansion in HLSL and independent expm1 in
the float64 reference. Native predictor displacement and FLIP velocity are
distinct inputs and each retains its own unforced normal component.

This is external boundary momentum, not internal momentum conservation. The
coefficient 4 and four-cell band are experimental, not measured South Fork
properties. A passing exit gate cannot establish absorption, correct discharge,
stage, pressure behavior or realistic rapid motion. Actual boundary impulses,
storage, outgoing discharge, reflected disturbances and visible motion still
need measurement before promotion. No map, production system or captured
geometry was rewritten by this candidate.

The technique is informed by the primary [DualSPHysics relaxation-zone
documentation](https://github.com/DualSPHysics/DualSPHysics/wiki/3.-SPH-formulation#3132-relaxation-zone-rz),
which describes velocity relaxation over a region with smooth weighting and
horizontal-only or horizontal/vertical control. That implementation is SPH;
it does not validate this FLIP implementation or its selected parameters.

## Verification so far

- 334 liquid Python regressions pass, including seven added relaxation cases
  and three uncancelled-arithmetic envelope tests.
  The above-stage test intentionally still exits under a sufficiently strong
  disturbance: no new permission silently turns it into an approved exit.
- The captured step67 regression now checks integrated relaxation that prevents
  its crossing, and separately retains its original plane-only reference result.
- Build session90893 succeeded in43.97s.
- Engine regression session5622 is terminal0:14 clean passes and one pass with
  an unrelated Google connectivity timeout warning, no test failures.
- The full native audit selects every particle starting within the candidate
  band, including zero response markers, to detect missed treatment. Old reports
  retain plane-only reference semantics through explicit version selection.
- The stage probe records the actual bound inlet spatial scales and rejects a
  dense source with nonzero unregistered jitter. This was not inferred from the
  construction script alone. The actual600-step capture confirms all12 scales
  are exactly[0,0,0].

## Actual full-field result — rejected

`liquid-native-inlet-relaxation-flow` (session87787 terminal0) retains598
continuous handoff controls over600 native steps with the same diagnostic seed
173193 and all719335 original initial particles. First failure is step501,
not the previous approximately368. This is not an accepted flow run.

The first rejection latch identifies owner4, birth4/89015, west inlet row69.
The original row has inward velocity0.67285478cm/s, stage876.47693cm and actual
hit bed863.18188cm. Particle hitZ892.95054cm is16.47cm above stage. Its response
marker is1, so the relaxation actually executed. The particle still crossed:
local normal start0.16852cm, end-0.02762cm. The velocity changed from
[31.43548,-7.65970,-3.46379] to[30.49221,-8.03250,-3.46379]cm/s. No vertical
change, no hidden deletion; unchanged non-outgoing exit reason8 rejects the
whole commit with error64.

There are499 valid commits throughstep500. Exact count bookkeeping before the
failure is719335+18764births-44577exits=693522survivors, a nominal storage change
of-537.77083m³. Eight full one-second intervals have inflow about47m³/s and
outflow117.27,123.90,118.83,117.42,112.50,108.52,104.44,96.69m³/s. The transient
is still draining; neither steady discharge nor correct stage is established.

The fullstep500 replay, `liquid-native-inlet-relaxation-step500`, is terminal0
(session59535). This generation fails slightly earlier at498, same owner4
birth4/89015 and westrow69; fullstep500 is therefore AFTER a failed commit and
must not be presented as the immediate valid pre-failure state. The first latch
still preserves that generation's actual first trajectory.

The retained step500 remains useful for checking the executed operation, not
for accepting the failed fluid trajectory. `inlet-advection-audit.json`
(audit53491 terminal0) selects19385 candidates, verifies7256 unobstructed
responses and defers362 responses near subsequent terrain contact. All response
markers match the independent reference, including zero-marker candidates.
Max position difference is0.00049825cm; max velocity difference is
0.00004933cm/s. Those deferred contact responses are NOT verified here.

The first audit attempt exposed an incomplete arithmetic bound: it scaled
roundoff from the small final velocity while the actual relaxation used a
102.15878cm/s target before cancellation. The bound now uses the uncancelled
v+n*(U-dot(v,n))*weight operation magnitudes; the existing gamma32 is unchanged.
The plane-only historical capture model and all physical/exit/mass gates remain
unchanged. Regression tests cover cancellation and coordinate sign reversal.
This arithmetic comparison is not a physical parameter-error allowance.

Using nominal1/48m³ particles and assumed water density1000kg/m³, the verified
subset's reference impulses total[-807.68674,-319.21864,0]kg·m/s for this step.
That is supplied boundary momentum, not a claim of total solver momentum
conservation. Deferred contacts and pressure contributions are not included.
All build/UE/audit processes are terminal; the final process check found none.

The candidate demonstrates that finite damping alone is not a complete inlet
condition, particularly at nearly stagnant shallow margins. Do not simply crank
up damping until the gate turns green or turn above-stage crossings into exits.
The next physical implementation must reconcile reservoir/buffer state and
free-surface support with pressure, velocity and signed exchange accounting.
The primary [open-boundary description](https://github.com/DualSPHysics/DualSPHysics/wiki/3.-SPH-formulation#315-open-boundary-conditions)
supports explicit fluid/buffer transitions, including backflow and water-depth
changes. Our current system has no such exterior particle reservoir; a normal
velocity sponge must not be presented as that algorithm.

South Fork, all later rivers, crew work, normalization, release checks and final
commit remain incomplete. No photorealism or playable-performance acceptance.
