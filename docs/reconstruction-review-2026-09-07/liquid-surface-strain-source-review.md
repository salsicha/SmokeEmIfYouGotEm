# Surface-aware aeration source and missing breaking-flow evidence

September 9 continuation. South Fork and the full queue remain incomplete.
No production promotion, map replacement, commit or push.

## Implemented and verified

The current-surface coverage shader previously treated every surface as
horizontal (`-(dVx/dx+dVy/dy)`) and let rigid rotation produce foam through curl.
Revision `surface-strain-v3` uses the actual rendered SDF normal and tangential
convergence `-trace((I-n*n^T)J)`. Curl is bounded by `sqrt(2 S:S)` where
`S=(J+J^T)/2`, so rigid rotation without deformation is not an aeration source.
Degenerate surface gradients cannot create foam. Six solver-scale SDF reads
are added; no particle physics, extra visible surface, decay constant, source
multiplier, or optical whiteness change is introduced. Existing source
thresholds/coefficient values remain empirical and uncalibrated.

This corrects the **surface coverage** source, not the separate Niagara
secondary-emission vorticity heuristic. That still needs crest/impact criteria.

- Build succeeded in 19.71 seconds (session 90948, terminal exit 0).
- 112 numerical liquid tests pass. New tests cover rotated tangential
  compression, rigid rotation, simple shear, degenerate/curved surfaces and
  anisotropic convex/concave crest diagnostics.
- `engine-liquid-surface-strain-source/index.json`: 14 successes, zero test
  failures/warnings. The actual GPU foam regression now exercises 13 cases,
  including rotated surfaces and pure rotation. Session 48699 exited 0.
- `liquid-surface-strain-source-12s`: 750 GPU updates, 30 distinct decoded
  motion frames, no engine error lines or rejected secondary batches.
  Session 10716 exited 0. Sim-cache warnings still say the render-target DI
  itself is not baked; direct GPU surface readbacks are the surface evidence.
- Active coverage error against float64 is 0.00048828125; maximum source-rate
  error is 0.000764904, within the unchanged 0.001 gates. Paused coverage is
  exactly identical. Surface distance and time metadata remain exact, and
  captured velocity/boundary fields match the independent Niagara readback.
- Secondary cache still exactly matches the completed surface at 715 active
  and 750 final publications. Final particles include 239 foam, 54 spray,
  49 bubbles. Three spray points are inside the current surface (maximum
  2.675 cm), and foam-interface absolute p95 is 1.108 cm. One-step coupling
  is not same-step contact acceptance; these are not visible-particle counts.

## Appearance and cost: not accepted

Actually inspected `motion_020.png` from the previous preserved-surface capture
and the new capture. Both show glossy cyan choppy water, not the white collapsing
crests/dark faces of the user's rafting photo. The finite square liquid edges
and unfinished terrain render remain obvious. This change does not solve that.

Whole sampled-top mean coverage fell from about 0.004063 to 0.002389; there are
no sampled top columns above 0.1 coverage in the new capture. Removing false
rotation sources correctly does **not** increase froth. Do not advertise this
as a visual improvement or undo it merely to get a whiter numerical result.

`liquid-surface-strain-source-benchmark/benchmark_audit.json` verifies 480
uninterrupted editor frame intervals and 471 post-warmup GPU timing samples:

- Mean frame interval 23.04365 ms; p95 25.09096 ms; maximum 30.60020 ms.
- GPU reconstruction mean 6.11124 ms: density 5.39295, distance 0.57617,
  foam/copy including secondary cache 0.14212 ms.
- Prior shared-surface foam/copy mean was 0.13424 ms. Separate runs are not
  an interleaved causal performance estimate. Overall time still misses
  16.67 ms, and these are not packaged-game or whole-scene FPS.
- Benchmark session 99633 exited 0; no UE/build process remained afterward.

## Why the next action is primary breaking flow, not a larger foam multiplier

Read section 6 and inspected the complete equation page of the author's
[Turbulent Micropolar SPH Fluids with Foam](https://dankoschier.github.io/resources/papers/BKKW18.pdf).
Its source model combines trapped-air, convex/outward crest, energy and
angular-velocity-difference potentials. The offline diagnostic here borrows
only the convex/outward criteria; it is not their SPH method or measured air
entrainment. It uses metric grid curvature and a smooth 0.6--0.8 alignment ramp,
not the paper's binary 0.6 test. No per-frame auto-normalization is applied.
It remains **offline**, not another unvalidated runtime source.

`liquid-surface-strain-source-12s/crest_hydraulic_context.json` records exact
input hashes and the following at the final completed instant, excluding a
metre beside the physical domain boundary:

- 12,388 top-surface columns; 0.961% have outward velocity alignment >0.6,
  and 0.525% also have positive convex crest activity.
- 98.854% have zero current coverage source at that instant.
- Of 12,192 columns with candidate-bed clearance greater than one solver
  Z cell, median depth is 1.86985 m and median horizontal surface speed is
  1.40482 m/s. The surface-speed / sqrt(g*depth) proxy has median 0.34166
  and maximum 0.84912. This is **not depth-averaged Froude**, an absence-of-jumps
  proof, or acceptance of the inferred depth.
- Top crossings omit overhangs and occlusion; a single instant does not measure
  impact history, entrained air, photographed coverage or periodic stability.

Rechecked the geographic source: liquid origin UTM (683805.13363,
4296673.44759), equivalent to (9.77472,-36.97393) relative to the existing
NAIP registration figure's centre. It is in the candidate constriction, not
evidence that the fixture was accidentally placed kilometres away. Its 21 m
window does not cover the entire hole/right/left sequence. The manifest
explicitly retains unverified rapid identity and uncalibrated submerged-bed
prior; exposed returns have not been moved to create a preferred screenshot.

Next: inspect the primary flow through the actual drop and its downstream
pool, including imposed stage, inferred bed depth and impact/recirculation.
Use the larger registered terrain and source references to verify the
hole/right/left controls. This evidence does not justify forcing this whole
small window white, inventing new surveyed rock heights, or claiming a
research crest heuristic alone recreates the rapid. Resume from this finding,
not another repeat of the already-passing cache or foam transport tests.
