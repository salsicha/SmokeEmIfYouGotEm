# Whole-support particle density correction — September 11

Previous goal turn made real progress: native inlet and exterior fixes were
implemented and verified. This continuation addresses the still-failing South
Fork density distribution. The full reconstruction/realism/crew/cleanup/commit
goal remains active. No native shader or playable scene is changed in this pass.

## Implementation

- `liquid_particle_density.py`: exact centered-tent density objective and its
  particle-coordinate derivative, including the actual fixed bed-kernel
  fraction on every grid node. No fluid/solid/air phase can mask excess density.
  Positive excess drives repulsion; underfilled free-surface support is not
  attracted. Volumes remain unchanged and full stencils are required.
- `liquid_particle_contacts.py`: separable three-dimensional convex contact
  projections, enumerating active sets of up to three independent normals.
  Every original inequality is checked; no diagonal regularization, discarded
  rock plane, particle merging, mass removal or terrain change.
- `solve_liquid_particle_density.py`: original native positions and identities,
  phase-independent density descent, exact triangle-path constraints, a common
  step-size line search and saved intermediate states. This alternative uses
  particle position unknowns, NOT the prior shared-field pressure equality.
  It is not native physical-time integration or a renderer-coupled method.
- `audit_liquid_particle_density.py`: independently deposits saved positions
  with the separate volume-scatter code, reports every original native phase,
  checks unchanged IDs/volume, exact bed, original survey outer bounds and
  prospective float32 storage. Intermediate saved states allow full piecewise
  path verification; a good final endpoint cannot hide a bad intermediate step.

Tests verify finite-difference gradients and the Gauss–Newton diagonal on
anisotropic partly solid support, conserved scatter volume, absence of surface
attraction, off-grid rejection, actual ridge crossings, outer-box constraints,
nearly parallel normals, redundant planes and infeasible contact rejection.
Full liquid suite: **505 tests pass** (4.959 s latest test time).

## Input provenance

Native capture `liquid-native-residual-600-v1`, all726905 particles. Stages SHA:
`cf016de8b61dd325f01fe76313f6241fac4f924730137e0d3a63777d95ab2a8e`.
Reused only the static bed-kernel data from
`tmp/south-fork-liquid-density-projection-refined-v2-20260911`, after checking
identical captured mesh, grid dimensions, metric, origin and frame. The old
capture's fluid density, pressure solution and phase are NOT reused.
Bed-kernel SHA:
`d124d59f0164243b65c6752059294e4b873191147581fe06ba2a035e050792cb`.
Quadrature is successively converged to .001, not a certified integral.

All output packages below are under `tmp/`, prefixed
`south-fork-liquid-particle-density-descent-` and suffixed `-20260911`.

## Trials retained, including failures

- **v1** / session30264: exit1,87.52s. Cyclic contact projections stalled at
  nearly parallel constraints. Zero accepted changes; original state retained.
- **v2** / session99516: exit1,61.74s. New active-set contacts allow one step:
  energy3623.2761→3255.5075, peakdensity12.36124→8.17593. Independent
  `liquid-particle-density-independent-v2.json` rejects one original-survey
  outside endpoint. Local-frame arithmetic alone was insufficient. Prospective
  native float32 storage also violates the preserved skin on3141 particles.
- **v3** / session38177: exit0,154.21s, four steps accepted by the local-frame
  checks. Energy2688.0777, peakdensity5.25416. Independent
  `liquid-particle-density-independent-v3.json` finds one survey violation in
  each of the first two steps despite a valid final endpoint. This is NOT full
  geometry acceptance. All exact bed paths pass the existing1e-6cm skin gate;
  no below-bed particles. One coincident pair appears in the final state,
  explicitly reported (no particle was removed). Prospective float32 storage
  has3032 skin violations and one survey outside point. Not native-ready.
- **v4** / session21130: exit0,156.91s, adds the original-survey comparison to
  each line-search trial. Four steps accepted, each at shared alpha .5 (maximum
  move .125 cells per step). Independent session96535 completed exit0; report
  `liquid-particle-density-independent-v4.json` verifies all saved intermediate
  paths, exact bed/skin and original survey exterior. No tolerance was added to
  the survey boundary. All726905 identities and distinct positions remain;
  deposited and nominal volume both15143.85461798869m3.

### Independent v4 result and remaining failures

| Whole-grid metric | Original | Saved float64 candidate |
| --- | ---: | ---: |
| Positive density-excess energy | 3623.276100 | 2571.988521 |
| Maximum particle density | 12.361243 | 4.857435 |
| Maximum particle density on native solid-labelled support | 4.325248 | 3.902991 |
| Squared excess on native solid-labelled support | 593.841315 | 522.725388 |
| Maximum density on native air-labelled support | 2.133636 | 2.177433 |
| Particles outside fixed-isovalue surface candidate | 6759 | 6633 |
| Particle-occupied columns without candidate water | 673 | 700 |

The solid-labelled concentration decreases, unlike the previous fluid-only
pressure correction. Nevertheless density is far from nominal; air-labelled
peak rises and missing-water columns worsen. Phase names describe original
native grid labels, not removed fluid or particles relabelled as spray.
Whole-grid scatter uses all halo support; its candidate counts differ from the
earlier physical-owner-only native volume report for that reason.

All four exact saved paths have zero bed penetration, zero preserved-skin
violations under the unchanged1e-6cm geometric gate, and zero survey exterior
violations. Minimum raw skin residual is -2.01503e-11cm and remains reported;
this is not rounded into a claim of exact nonnegative skin everywhere.

**Prospective native float32 storage fails**:2034 preserved-skin violations,
worst margin -0.00951688cm, although no actual below-bed or survey exterior
point and no coincident positions. Directly importing the candidate is not
authorized by these checks. The next step must address representation-aware
contact constraints and then native density/interface coupling; do not waive
the skin gate, independently push out/merge points after the solve, or promote
the current fixed-isovalue surface. A GPU implementation also needs measured
cost, not an FPS claim based on this156.91s CPU reference.

All owned jobs are terminal. No Unreal or build was launched in this pass.
Saved playable map SHA256 remains
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
Scoped diff whitespace checks pass. No promotion, final commit or scene completion.

The method is promising but unresolved. Even after energy reduction it is not
incompressible, all-phase peak statistics and interface coverage still matter,
native position quantization needs explicit treatment, and no reconstructed
surface or raft support has been coupled. CPU seconds are not gameplay FPS.
All later rivers, crew, normalization and final commit remain queued.
