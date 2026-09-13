# Native-representable contact and local density retries

2026-09-11. South Fork remains incomplete. This work advances the existing full
queue; it is not scene acceptance, a visual comparison, or a gameplay FPS result.

## What changed

`liquid_particle_quantization.py` derives conservative float32 world-coordinate
rounding-error boxes from the actual position magnitude and displacement bound.
`solve_liquid_particle_density.py --native-positions` includes those bounds in
the terrain and exterior contact constraints, then tests the actual stored
float32 endpoints and complete piecewise-triangle paths. It does not move the
bed, expand the survey, reduce the required skin, or push out saved particles.

The first native-representable full-river solve was valid geometrically but
slow: four accepted iterations took 720.40 seconds and only reduced peak density
from 12.36124 to 9.67143. Global step sizes were 0.5, 1/2048, 1/16 and 1/64.
Its immutable package is
`tmp/south-fork-liquid-native-position-density-v1-20260911`, manifest SHA256
`0fcaae192c7da44a4a0b2c99f8f6debd0bd0c57910bbdc5addb84b02ff6144e6`.
Independent evidence is `liquid-native-position-density-independent-v1.json`.
All 726905 IDs, distinct final positions and 15143.85461798869 m3 were retained.
The original 1e-6 cm numerical skin gate was unchanged; raw minimum path margin
was -9.89995e-7 cm, not literally nonnegative. Fixed-isovalue coverage remained
inadequate (6717 particles outside, 672 occupied columns without candidate water).

The new read-only `diagnose_liquid_represented_pairs.py` reproduced a rejected
full-size trial from saved step 1. `liquid-represented-pairs-v1.json` identifies
two pairs whose independent bed-contact projections land at the same represented
point. Before that trial, pair separations were 0.23456 and 0.06455 cm; both were
at approximately 2 cm bed clearance. One pair's unrounded endpoints also match
to floating-point accuracy. This is non-injective contact projection at terrain
features, not merely a duplicate inlet sample or an aesthetic foam problem.

`liquid_represented_retry.py` now retries only members of a colliding trial
group at a smaller local direction scale. Each retry solves its original
terrain-contact problem again. New collision groups are rechecked. Stationary
particles stay stationary; no points are jittered, merged, deleted, independently
pushed apart or omitted. The original full-river energy, represented-coordinate,
bed/path/skin, survey and distinct-position checks still decide acceptance.
This is an opt-in numerical descent strategy (`--local-contact-retry`), not a
new physical repulsion force or a claim of physical time integration.

## Actual all-particle result

Package: `tmp/south-fork-liquid-local-contact-retry-v1-20260911`.
Manifest SHA256:
`26fb949874f54194df52eb982d596536e47602fa3588c06aefe7edc8bb6c45b9`.
Solver session 84445 exited 0; all snapshotted implementation sources were
unchanged during execution. No particles, volumes, momentum or terrain changed
except the proposed density-correction positions. Physical time was not advanced.

| Quantity | Input | Four accepted corrections |
| --- | ---: | ---: |
| Particle count / final distinct positions | 726905 | 726905 |
| Conserved volume (m3) | 15143.85461798869 | 15143.85461798869 |
| Whole-support excess energy | 3623.276100 | 1557.389838 |
| Peak particle density | 12.361243 | 3.130106 |
| Peak liquid-plus-solid-kernel density | 12.859323 | 3.669216 |
| Solid-labelled peak particle density | 4.325248 | 2.932529 |
| Solid-labelled squared excess sum | 593.841315 | 396.053183 |
| Air-labelled peak particle density | 2.133636 | 2.026177 |
| Particles outside fixed 0.5 isovalue | 6759 | 6583 |
| Occupied columns missing candidate water | 673 | 759 |

All four global steps were accepted at scale 1; 2, 10, 24 and 38 particles
respectively needed local retries. The CPU reference took 166.94 seconds versus
720.40 seconds for the previous four-step native-representable method. This is
not a controlled rendering benchmark, a real-time solver, or a gameplay speedup.
656270 markers changed position; all saved positions are exactly representable
as native float32 world centimeters despite being stored in float64 NPZ arrays.

Independent audit: `liquid-local-contact-retry-independent-v2.json` (supersedes
v1 by also enumerating distinct positions in each saved step). Separate scatter
code independently reproduces the energy and volume. Exact complete triangle
paths preserve original surveyed bounds, actual bed clearance and the existing
required-skin gate. Worst raw path skin margin is -8.63552e-7 cm; final minimum
skin margin is -2.08403e-7 cm, one raw negative value within the unchanged
1e-6 cm numerical gate. Minimum actual final bed clearance is 1.990629 cm; some
input particles already had less than 2 cm, and their original clearance remains
the requirement. Do not describe these results as all raw margins nonnegative.

## GPU implementation and regression evidence

New `RaftSimLiquidDensityGradientGPU.{h,cpp}` and
`RaftSimLiquidDensityGradient.usf` compute the exact eight-node centered-tent
density-excess gradient and diagonal Gauss-Newton sensitivity. Every touched
node is included, including partial-solid support. There is no fluid-only phase
mask, attraction to underfilled surface nodes, or particle/count/mass update.

The GPU API rejects invalid dimensions, capacity, spacing and buffer layouts;
the shader rejects incomplete support, nonfinite or invalid field data, invalid
particle volume and overflow transactions. Grid multiplication and coordinate
conversion are guarded before integer overflow or invalid conversion.

The initial build failed on explicit FVector4f constructors and was corrected.
The subsequent hardening rebuild (session 39317) succeeded in 16.08 seconds.
Actual GPU report `liquid-density-gradient-engine-v2/index.json`: 4 clean
successes, 0 warnings, 0 failures, 0 not run; session 37512 exited 0. Tests cover
the new anisotropic/partial-solid derivative against separate CPU arithmetic,
empty/invalid/overflow cases, rotated physical-frame classification, exits and
routing. The earlier v1 engine report predates integer-range hardening.

515 `test_liquid*.py` regressions passed in 5.175 seconds. Six new retry tests
include a real piecewise V-shaped terrain contact where both independent QPs
collapse to one valley point, then verify two distinct represented endpoints and
both complete terrain paths after retry. Other cases cover stationary particles,
newly introduced collision groups, retry exhaustion and invalid source positions.

## What is still unproven or failing

- Density remains too high (3.13x liquid / 3.67x including the solid kernel).
- Fixed-isovalue coverage is not a consistent liquid surface: missing occupied
  columns increased to 759. No phase labels or missing markers are relabelled
  as spray to conceal this failure.
- The complete correction is CPU-only and position-only. The GPU derivative is
  an arithmetic building block, not an installed density/contact solver.
- Native momentum, interface, pressure, correction and source/outlet storage
  still need consistent coupling and sustained-flow evidence. Prior native
  storage/outflow failures remain open.
- No new scene rendering, animation comparison, raft/FPS validation, production
  scene promotion or final commit occurred.

Next: continue density/contact convergence without serial global shrinkage,
integrate independently verified native correction and scalar/interface coupling,
then validate sustained flow, one visible frothy 3D surface, raft collision/support
and actual gameplay performance. Preserve the full South Fork -> Colorado ->
Pacuare -> Futaleufu -> remaining scenes/crew/cleanup/release/final-commit queue.

The saved playable map is unchanged: SHA256
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`
for `unreal/Content/RaftSim/Maps/Review/Geographic/SouthForkRegisteredRockPlayable.umap`.
Captured rock-return provenance is unchanged; submerged terrain remains inferred,
not newly measured bathymetry.

All owned jobs are terminal: solver 84445, pair diagnostic 23538, independent
audits 3596 and 18025, engine 37512 and build 39317. No background solver is
pending. Scoped whitespace checks pass; no unrelated tree edits were removed.

Reproduction (from repository root, using the configured Python executable):

```text
python physics/scripts/solve_liquid_particle_density.py docs/reconstruction-review-2026-09-07/liquid-native-residual-600-v1 tmp/south-fork-liquid-density-projection-refined-v2-20260911 --output NEW_OUTPUT --iterations 4 --native-positions --local-contact-retry
python physics/scripts/audit_liquid_particle_density.py NEW_OUTPUT --output NEW_REPORT.json
python -m unittest discover -s physics/tests -p test_liquid*.py
```

Do not overwrite existing evidence directories. The full test suite uses the
existing SciPy runtime at `tmp/south-fork-density-numerics` on PYTHONPATH. Neither
solver command installs positions in the game or advances the native simulation.
