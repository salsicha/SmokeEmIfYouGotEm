# Explicit face-velocity pressure boundary — September 13, 2026

This is a verified pressure-boundary component, not normal-play integration,
nonreflecting-wave qualification, a new FPS measurement, or visual acceptance.
South Fork remains the scenario; Troublemaker remains a rapid, off-menu.

## Implemented contract

The CPU nonlinear pressure reference and `RaftSimNonlinearPressureGPU` accept an
optional packed float2 per boundary face: prescribed normal velocity and its
time derivative. Order is west Ny, east Ny, south Nx, north Nx; velocities use
positive x/y orientation, not outward-normal signs. Count and stride must match
exactly, all entries must be finite, and periodic boundaries are incompatible.
The single-cell case validates all four entries, including the last one.

This is distinct from the normal source's exterior ghost-CENTRE state. Neither
face traces nor time derivatives are silently inferred from those observations.
The current normal source is not yet a temporal boundary-condition provider.

For the existing paired operators, write divergence as D(u) = D0(u) + B(g).
B adds -west/dx, +east/dx, -south/dx, +north/dx at boundary cells, inactive only
at exactly zero depth. Kinematic terms include both B(g) and B(g_t); the linear
velocity-correction operator and negative-adjoint pressure gradient are unchanged.
The pressure correction retains zero normal integrated-pressure gradient. This
does not establish transparent/outgoing-wave behavior, nonlinear stability,
or a complete boundary discretization for the full evolving river.

No depth or velocity cap, water repair, extra solver iterations, altered PCG
residual threshold, or changed simulation timestep was introduced. Absent the
new buffer, the old pressure permutation remains. Normal total-state ownership,
source-time interpolation, RK boundary stages, and boundary flux/pressure work
still need coherent integration before promotion.

## Evidence

- Build59123 succeeded in13.04s; final coupled-test build59961 in12.16s.
- CPU17-file affected suite: **210 passed in29.49s**, session33924 exit0.
  Includes26 boundary tests: sixteen uniform-flow cases, time derivative,
  affine pressure-work identity, finite-difference kinematic identity, invalid
  data, the old false-pressure failure, and deterministic fixture validation.
- Native first run78851 and final run38190 both exit0. Final report
  `tmp/south-fork-prescribed-pressure-native-v2-20260913/index.json`:
  **76 tests passed in16.0525074s**, zero automation errors/warnings/unrun.
  Optional engine startup SDK warnings are retained, not hidden.
- The pressure test now covers seven existing cases plus21 manufactured
  boundary cases in both legacy and fused reduction modes. Seventeen uniform
  or rest cases per mode consume the ACTUAL GPU exterior FV rate, wet graph,
  geometry and physical slope, not a substituted CPU rate. All34 compositions
  have exactly zero transport rate and zero pressure force with clean diagnostics.
- Uniform accelerating-flow force is also exactly zero on GPU. Nonuniform
  manufactured cases have force maximum absolute error at most9.31322575e-8;
  fused residual at most1.25124878e-7, below the unchanged2e-5 gate.
  Dry/thin and mixed dispersion fractions are exercised. Manufactured forcing
  is explicitly not presented as a measured or evolved river boundary.
- Invalid state/rate/fraction and last-face NaN/infinite trace derivative are
  rejected by diagnostics. Periodic, wrong count and wrong stride are rejected
  before dispatch. The40-iteration limit and existing force gates remain.

Fixture generation:

```text
python physics/scripts/export_prescribed_pressure_fixtures.py --output <fresh.bin>
```

The native pressure test now also requires
`-RaftSimPrescribedPressureFixture=<fresh.bin>`, alongside its original fixture.
The isolated pressure profiler accepts `-PrescribedPressureFixture` and records
it; PowerShell syntax was checked, but no new timing profile was run.

Final fixture is `tmp/south-fork-prescribed-pressure-fixtures-v2-20260913.bin`,
SHA256 `af7b7dc291525617c3634e989d0e5603566309d71850aa7b9cd574ad0b284ab2`.
Its sidecar records input-code hashes and per-case reference residuals.
The earlier v1 file is retained: it used an asymmetric acceleration with tiny
double cancellation residue. The final native oracle uses binary-exact symmetric
acceleration; the asymmetric time-derivative CPU regression remains unchanged.
Final WaterDetail DLL SHA256
`f28fc6457d12ec77029eee825e93c198b61dde298cc957416b5067f4a8220b11`.

## Remaining integration and full goal

`total_depth_bank_replay.rate` still refuses exterior FV plus dispersive pressure;
its explicit physical trace plumbing is not implemented yet. The GPU single-step,
advance, source-time policy and persistent normal-play owner still need this
boundary contract. Next implement and test that coherent composition, including
physical ghost-bed slopes, time-dependent traces and boundary energy/flux work;
then run outgoing-wave/reflection and long-run nonlinear tests. Do not assume
the former closed-box surge was caused only by reflection.

The latest actual gameplay measurement remains21.496540FPS/p9554.5967ms,
failing30FPS. No new screenshot or motion comparison is claimed. Terrain,
boulders/collision, wave breaking/foam, later rivers, crew, normalization, release
checks and final commit remain open in the full goal. Map/material/save hashes
were rechecked unchanged. No commit was made.

The full-river4000s cook completed and both state/bank audits pass, but remains
unsettled. A bit-exact continuation is live toward6000s; see
[checkpoint record](full-river-expanded-checkpoint.md). Playable data stays600s.
