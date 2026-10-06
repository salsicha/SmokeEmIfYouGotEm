# Source, target and submitted water shape — September 14

The preceding turn made progress: reference-video access was restored, current
frame times were measured, and the interrupted expanded cook was recovered
exactly. This turn traces the remaining broad faces; it does not add a visual
effect or claim the water is fixed.

## Same-publication observation

The opt-in `RaftSimCarrierShapeAudit` now writes schema v2. Alongside actual
submitted triangles and the already presented detail payload, it records current
pre-temporal carrier targets on the source lattice. Export checks array sizes,
finite target values and exact lattice correspondence within1e-6m. No solver
sample, detail commit, source update, smoothing reset or geometry edit occurs.

Target base subtracts the current coarse crest and render lift. It still includes
hydraulic/shore/boulder/other shaping. On fully wet source cells, the analyzer
uses the original source-triangle interpolation for both source and target, and
splits the submitted base gradient into:

1. Cached bed-plus-depth source gradient.
2. Target base minus cached source gradient.
3. Submitted base minus interpolated target base gradient.

The last term contains temporal AND refinement/interpolation differences,
including the differing crest histories. It is NOT a pure temporal-error
measurement. The decomposition is bookkeeping, not an energy/conservation law.
No dry-boundary extrapolation is permitted. Each bin reports its actual fully
wet comparison area; that denominator differs from the full submitted-mesh area.
Historical v1 files remain readable, with targets explicitly unavailable.

## Verification

Build41719 completed exit0,53.83s. Python12 tests pass0.303s, including independent
plane gradients, opposite signed source/target contributions, reflected world
coordinates, reversed winding, dry comparison exclusion, schema/finiteness,
historical compatibility and malformed/reserved-index rejection. No gates waived.

Native17937 completed exit0:10 succeeded,0 warnings/failures/not-run,
1.329369s test duration. Report:
`unreal/Saved/RaftSimValidation/target-shape-native-v2-20260914/index.json`.
Tests cover shoreline clipping/cache/upload, fine crest and support, completed
GPU contact, career catalog and migration. These are regressions, not a full
reconstruction or performance acceptance suite.

Built source SHA256:

- Audit header: `79c260efeb46be520f7d9e850dbc6046d3591114fd201ceac4cba305f8786ad8`.
- Surface actor: `f64797593dbd3b4768bc7500d33ac3bf10e67773608e75484094e18861540cad`.
- Raft DLL: `2af1e184b4f38e910488a98845eefc7e99f322d3f8ddb8430632eb708bd6cc65`.
- Analyzer: `1d4d95cd8bd5aa1d6263bcfa00fb984eec60550fac2dd5f0155282430214a8dc`.

## Actual ordinary-scene result

Game29746 completed exit0. Ordinary full-reach South Fork at station8330,
1280x720, no altered water/terrain/material/physics settings. The read-only
audit ran at world13.0803602s, presented detail sequence125. It exported21,748
nearby triangles over2362.927060m2 within30m of the raft; none exceed60degrees.

Capture: `tmp/south-fork-target-shape-v2-20260914.json` plus its vertices,
triangles and source CSVs. Analysis:
`tmp/south-fork-target-shape-v2-analysis-20260914.json` includes all input hashes.
Metadata SHA256 `4245913ef5c0f7a2ed9d307aefac9b1fc6cd18379186d05e00f30c2c2aac2c10`.
Source CSV SHA256 `dbc3ecaeac41d8ff033ef22f7e59d2292278e10f06885598ff9d37b74505ba45`.

The30–60degree bin has1058triangles/80.182781m2. Its fully wet source comparison
contains935triangles/69.875m2. On THAT common area, signed slope contributions
projected along the displayed slope are:

| Contribution | Area-weighted signed slope |
| --- | ---: |
| Cached source | 0.620884284 |
| Target minus source | 0.087440139 |
| Submitted base minus target | 0.124832419 |

The source is the largest contribution. Target shaping and submission history
add measurable slope; neither alone accounts for the broad base geometry.
The source-component sum residual is0 (an algebraic decomposition, NOT physical
validation). Full base/crest/detail gradient residual is1.015107e-11. Maximum
absolute crest and detail heights are0.509779m and0.163516m; neither was disabled.

The preserved v1 upload-cache capture was also reanalyzed without modifying it:
`tmp/south-fork-upload-cache-source-split-v1-20260914.json`. On its30–60degree
fully wet subset (759triangles/62.070313m2), source0.627551316 and remaining
base-source0.213674022 similarly show source dominance. Targets were not recorded
in that historical capture, so no target/temporal split is invented for it.
These are different trajectories/epochs, not a paired visual comparison.

## Next action and limits

Do not remove crest detail or alter only the foam mask to conceal source-driven
faces. Trace the source geometry/current evolved stage and qualify the coupled
mass/pressure replacement. Separately examine target shaping and temporal
differences without equating this residual with a pure smoothing bug. The
reference footage supplies a qualitative rapid-shape target, not measured
submerged geometry or proof that every observed source slope is wrong.

No new rendered appearance, calibrated motion, full-raft traversal or30FPS
acceptance is claimed. The diagnostic CSV includes export overhead and is not a
new ordinary-performance benchmark. Latest ordinary measurement remains11.4394FPS/
p95114.9399ms, failing30FPS/33.333ms. Physics remains120Hz. Troublemaker remains
within South Fork, not its own menu scenario. Expanded cook84168 is still live
from9400 toward10000; next COMPLETE9500/local2000 needs BOTH audits. All terrain,
hydraulics, breaking/froth, later-river, crew, regression and release scope remains
open; no known broken experimental solver was promoted.
