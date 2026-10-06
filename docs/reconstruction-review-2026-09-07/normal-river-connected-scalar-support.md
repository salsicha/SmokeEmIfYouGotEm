# Connected scalar support: research progress, no gameplay promotion

September 14, 2026. Desktop target remains 30 FPS / p95 33.333 ms;
physics remains 120 Hz. This work changes neither the playable physics nor
the current map, terrain, material, shoreline fan or source capture.

The previous goal turn only reconfirmed existing 30 FPS settings (10 tests
passed); it did not improve the requested scene. This turn qualifies and
corrects the pending scalar-derivative proposal against real source support.

## Physical-force improvement and its limits

`depth_weighted_scalar_gradient.py` proposes a quadratic weighted scalar
derivative, separate from the original pressure D/E and their adjoints.
The independent least-squares and polynomial controls pass, but the original
new coarse wet-front refinement assertion remains FAILED: ratio 3.463083,
required >3.5. Finer ratios approach four; that does not waive the failure.

Original `audit_source_boundary_pressure_ray.ray` is run unchanged with both
actual rational poles, original state, bed, rates, trace, 40 CG iterations
and residual gates. The same exact-endpoint context is used for both variants.
At the original epsilon 2^-24, maximum conserved pressure-force errors are:

| Scalar derivative | Flat bed | Variable bed |
| --- | ---: | ---: |
| Original source-supported | 7.7610520974e-8 | 0.669219854321 |
| Depth weighted | 4.8280923881e-7 | 5.1190355066e-7 |
| Connected depth weighted | 3.8197356123e-7 | 3.9259557827e-7 |

The physical-force threshold remains 1e-6. Originally dry limit force is
exactly zero and both pressure residual gates pass. These are small-fixture
force results, NOT full-history, nonlinear energy, pressure-boundary or
playable acceptance. The proposed derivatives change the limit force itself:
variable-bed original SHA `9e291e235f4063cf9b0ed194f5379911a4649636e91e236a1305620238459cd0`,
both proposed limit SHA `0e067545f159e5c2942803da1cb3b41c1ceaff0018471b069ff53b5a24062ecb`.
Do not describe this as preserving all original nonlinear forcing.

Reports: `tmp/south-fork-depth-weighted-pressure-ray-v1-20260914.json` and
`tmp/south-fork-connected-depth-weighted-pressure-ray-v1-20260914.json`.

## Actual source exposes unsupported dry-gap links

Authoritative capture input is
`tmp/south-fork-pressure-stencil-temporal-v1-20260914.json.inputs.json`, SHA
`129a7a9de42d2f5559f8b0e777cfe38d36b4e7f6c43aa933d0292888ccb4d7de`.
Despite an earlier summary's 69x69/1m description, the decoder and actual
record establish **128x128 interior, 134x134 full source, 0.5m spacing**, three
real halo layers, 1,572 halo samples and 512 exactly matching legacy exterior
samples. No source resampling or modification was performed.

At each of the two captured endpoints, all 13,141 wet core cells initially
have quadratic rank in both axes. However the unconnected proposal has
14 directed x links and 14 directed y links crossing exactly dry intervening
cells. Full rank alone therefore does not establish connected fluid support.

New research-only `connected_depth_weighted_scalar_gradient.py` multiplies
two-cell weights by `4*m/(m+h_i)*m/(m+h_j)`, using actual directional ratios
when both terms vanish. At constant positive depth the multiplier is one;
as an intervening cell dries beside wet endpoints it vanishes continuously.
No Boolean near-dry threshold, depth floor or state reset is introduced.
The earlier unconnected implementation is retained for reproducibility.

Both actual endpoints now have **zero links across exactly dry cells**, all
13,141 wet cells retain quadratic rank in both axes, constant gradients are
exactly zero, and affine error is at most 1.332268e-15. This does not establish
connectivity through subcell bed barriers, nor validate evolving trajectories.
Six new tests pass: both gap directions, continuous bridge loss, independent
connected WLS, polynomial reproduction, entering mass-ray support, unchanged
source, and auditor detection (some checks share a test).

Reports:
`tmp/south-fork-depth-weighted-source-support-v1-20260914.json`,
`tmp/south-fork-connected-depth-weighted-source-support-v1-20260914.json`,
`tmp/connected-depth-weighted-gradient-v1-20260914.xml`.

## Original forcing assertions remain red

New wrapper tests call the original boundary test functions without translating
their assertions. Original file remains unchanged. Combined run finishes
**40 PASS / 8 FAIL**, exit 1, recorded in
`tmp/connected-depth-weighted-all-controls-v1-20260914.xml`:

- Original variable-bed raw forcing failure, unchanged.
- Both proposals differ from the original face-matrix scalar operator.
  This is an explicit incompatibility, not an independent WLS failure.
- Both proposals fail the original flat and variable-bed raw forcing gates.
- Original depth-weighted coarse convergence failure remains visible.

Connected refinement is also still below the coarse gate: 3.463260. Finer
ratios 3.781712, 3.902889, 3.954399 do not replace that gate.

`audit_depth_weighted_forcing_terms.py` reproduces the original test arithmetic
without adding the physical-force audit's exact-endpoint context. It independently
reassembles Q/C terms and checks array-exact equality with each variant's forcing.
At unchanged epsilon 2^-24:

| Variant | Flat raw max error | Variable raw max error | Variable wet Q error |
| --- | ---: | ---: | ---: |
| Original | 4.884787e-7 | 11.405669 | 6.250000 |
| Depth weighted | 1.740795e-6 | 14.226972 | 2.056963e-6 |
| Connected | 1.055569e-6 | 14.091705 | 1.256944e-6 |

In the original variable-bed case, the wet `-u.grad(D)` term has error
6.250000014; with connected support it is 2.446394e-6. This isolates the
large wet-side scalar coupling improvement. The connected variable-bed
remaining maximum Q error is on an originally dry cell [3,0]; its `D^2`
term alone differs by 12.5. The derivative correction does NOT repair the
underlying dry-column kinematics. The flat error 1.055569e-6 is also above
the unchanged 1e-6 threshold, however close it is. No test is waived.

Report: `tmp/south-fork-depth-weighted-forcing-terms-v1-20260914.json`.

## Next work and unchanged acceptance state

Continue with the actual dry-front kinematic/forcing defect and a consistent
nonlinear energy qualification before starting another long candidate history
or promoting it into native gameplay. Do not replace physical force with raw
scalar error, or vice versa, to manufacture acceptance. Full original moving
window history and same-instant final relocation are still required.

All five original long-job handles were directly confirmed live this turn.
Both implementation guards were rechecked: **417/422 files, zero changes**.
The next 8900s cook checkpoint was not complete at the check; do not audit a
partial frame or restart the cook. Last complete 8800s checkpoint passes both
state and bank audits but remains hydraulically unsettled.

No FPS measurement this turn; last isolated result remains 18.899245 FPS /
p95 70.33ms, FAIL. Latest ordinary shared-load result remains 8.921945 FPS /
p95 129.5326ms, also FAIL and not an isolated comparison. Breaking/froth,
broad base shape, source/terrain validation, remaining rivers, crew, release
and final commit remain open. No full-goal completion claim.
