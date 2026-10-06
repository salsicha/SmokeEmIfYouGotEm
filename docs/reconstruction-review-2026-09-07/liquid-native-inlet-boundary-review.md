# Native inlet sampling and outer-boundary residuals — September 11

South Fork is still incomplete. This is native simulation implementation and
diagnostic evidence, not photographic, geographic, sustained-flow or FPS acceptance.
The full queue in `../plans/remaining-work.md` remains active.

## Native inlet change

`RaftSimLiquidStratifiedSource.h` installs a weighted stratified selector only on
the unused transient regional Niagara clones when `-RaftSimRegionalStratifiedSource`
is supplied. It retains source positions, velocities, rates, initial seeds,
particle volume, and every positive source weight. Integer particle identities
and actual spawn-group counts seed a shared batch offset; a float CDF binary
search selects each site. Collapsed positive CDF weights are rejected.

Actual GPU source-index attributes are retained in exact particle word planes.
The independent audit uses immutable birth identity, actual stage-journal birth
counts and the original source profile. It does not use current storage owner
as birth owner or infer source sites from a screenshot.

Verified captures:

- `liquid-native-stratified-12-v1`: complete, process exit 0; 729672 particles,
  412 retained incoming particles, all 37 current births, no source-index
  mismatch or same-batch repeated sites.
- `liquid-native-stratified-600-v1`: complete, process exit 0; 726906 particles,
  22531 retained incoming particles, all 37 current births, no source-index
  mismatch or same-batch repeated sites. No coincident groups remain in the
  final state (the previous baseline had 89 pairs). Retired particles' full
  birth history is not directly retained and is not claimed verified here.

Reports: `liquid-native-stratified-source-12-audit-v1.json`,
`liquid-native-stratified-source-600-audit-v1.json`,
`liquid-native-stratified-coincident-v1.json`.
600-step stages SHA256:
`d4e0cdafc44a998f99c6744f057b96404116b51497a81adf2cc532572ab3f803`.

The 600-step advection replay passes all 726906 positions, maximum error
.0038327364 cm; compact-grid positions max .00048857081 cm. Interface audit
passes 2178720 paired samples, max error .0005162205 cm. Neither report certifies
volume stability, density, whitewater shape, rendering, or gameplay performance.
The diagnostic run's 69.22 s wall time is not a game FPS measurement.

## A strict exterior failure remains in that capture

`liquid-native-stratified-exterior-v1.json` identifies original particle identity
[11,15188,15188,15188] at world cm
[-13401.5703125,-2411.96533203125,493.69671630859375]. It is outside the original
survey bound by 7.7866133e-6 cm. Its uploaded-frame station is
24700.00002545841 cm, but demotion gives exactly 24700 cm, hiding the exit.
The whole dense audit raises `Native storage frame cannot expand physical
survey exterior`; `liquid-native-stratified-dense-v1.json` was NOT produced.
The source-selection result does not waive this failure.

## Residual-preserving native candidate

`-RaftSimRegionalResidualBoundary` selects the explicitly reported
`double-float-residual-outer-v2` contract on transient regional tests. The
physical-box checks and first outward intersection retain DoubleFloat
residuals; rounded internal storage-cut ownership is unchanged. This introduces
no boundary epsilon, moved terrain, particle clamp, payload edit or unledgered
deletion. Exit records retain the first-crossing face, row and fraction. The
bounded first-rejection latch now records the selected mode in word 15.

The independent storage audit reconstructs the uploaded frame and also keeps
the strict original survey check. A test explicitly verifies that retaining
arithmetic residuals does not excuse inaccuracies in the uploaded frame itself.
Captures retain and hash all seven boundary implementation files separately
from existing transport and inlet source snapshots.

Validation so far:

- 494 Python liquid tests pass, including the actual failing particle,
  preserved internal-cut ownership, and non-waived survey-frame disagreement.
- Build 5299 failed on a const-vector test-fixture address; corrected.
- Build 32593 passed (17.07 s).
- Engine `liquid-residual-boundary-engine-v1` finished, three successes and one
  failure: the new test incorrectly used unrounded coordinates for internal
  owner expectation. That reference was corrected to the declared unchanged
  internal-cut contract; the failing report remains intact.
- Build 15926 passed (19.44 s).
- Full engine run `liquid-residual-boundary-engine-v2`, session 92062, completed
  with 20 clean successes, one success with an unrelated Google connectivity
  warning (`LiquidRegionalState`), zero failures and zero not-run tests.
- Repeated full Python suite: 494 tests pass (5.007 s test time).

## Actual residual-boundary 600-step result

`liquid-native-residual-600-v1`, session 17658, complete and process exit 0.
All inlet, boundary and transport implementation snapshots remain unchanged.
Stages SHA256:
`cf016de8b61dd325f01fe76313f6241fac4f924730137e0d3a63777d95ab2a8e`.
Diagnostic wall time 69.59 s; NOT gameplay FPS.

- `liquid-native-residual-dense-v1.json`: original 729724 particles, 22533 new
  births, 25352 retired, 726905 survivors. All 598 compact commits verified;
  strict original survey exterior preserved. Nine internal storage/survey
  owner differences remain explicitly reported, not waived outer exits.
  Compact records do not retain full per-exit trajectory history.
- `liquid-native-residual-exterior-v1.json`: zero false-inside or false-outside
  results against original survey bounds. The formerly failing particle no
  longer survives outside the boundary. No survey tolerance was introduced.
- `liquid-native-residual-sources-v1.json` and `...-coincident-v1.json`: all
  22531 retained incoming source indices match; all 37 current births present;
  zero repeated same-batch sites or final coincident groups.
- `liquid-native-residual-transfer-v1.json`: all native regional P2G words and
  reductions match independent replay; zero reduction mismatches. Deposited
  physical-box kernel volume 15130.6676 m3 versus nominal particle volume
  15143.8546 m3 is reported separately, not claimed exact surface conservation.
- `liquid-native-residual-advection-v1.json`: all 726905 positions replay,
  max .00368980 cm versus unchanged .02 cm tolerance; compact-grid positions
  max .000488609 cm. Instantaneous pressure-interior divergence RMS .000272510/s.
- `liquid-native-residual-interface-v1.json`: 2178720 paired interface samples,
  max error .000514357 cm, all internal halos and clock ledger verified.
  Renderer is NOT coupled; fixed outer XY/Z interface boundaries are provisional.

## Physical failures are still visible and next in scope

`liquid-native-residual-flow-v1.json` records -59.5 m3 nominal storage change
over 598 commits. Last interval: inflow 47.0474 m3/s, outflow 37.5215 m3/s.
This is neither steady-state nor sustained-flow acceptance.

`liquid-native-residual-volume-v1.json`: maximum native particle density
12.36117 times nominal. The fixed-density-isovalue candidate leaves 6760
particles outside its surface; 681 particle-occupied columns have no candidate
water. 463.4528 m3 of deposited kernel weight lies on native solid-labelled
nodes; that is NOT a claim that those particles penetrate terrain. Exact
particle bed-clearance samples find zero particles below the bed. The candidate
is not promoted or used to hide these defects.

Next: replace the fluid-only density correction's inadequate support near the
bed, with exact bed/path constraints and whole-grid density accounting intact;
resolve scalar/particle interface drift; verify physically sustained native
flow before renderer/raft/FPS acceptance. Previous CPU corrections moved
concentration onto solid-labelled support, so blindly repeating them is not a
valid next step. See `liquid-repeated-correction-review.md`.

All owned jobs are terminal. Saved playable map SHA256 remains
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
Scoped `git diff --check` passes (line-ending notices only).

No saved scene promotion, final commit or queue completion. Native density,
partial-solid pressure support, interface-volume drift, sustained discharge,
single visible frothy water, raft collision/support and gameplay FPS remain
unresolved before moving to Colorado, Pacuare and Futaleufu.
