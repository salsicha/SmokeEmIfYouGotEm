# Prescribed boundary work through the original pressure poles

2026-09-19 UTC. Supporting physics progress, not playable water delivery.
The [prescribed kinetic trace](front-prescribed-trace.md) now has an exact
physical/canonical momentum implementation retaining the original two poles.
Normal scenes, installed hydraulic fields and the nonlinear OFF state are unchanged.

## Affine momentum and energy

For pressure kinetic functional `E_C(a) = a.C.a/2 + l.a + k`, each original
auxiliary solves `H_j a_j = M v - lambda_j l`, with `H_j = M + lambda_j C`.
Consequently physical momentum is **`p = B v + q`**, not just `B v`, where
`q = -sum_j w_j lambda_j M H_j^-1 l`. The homogeneous `B` and its derivative
come from the unchanged original moving-pressure implementation. Both exterior
mass normalizations and represented pole constants are retained.

The dual energy constant is
`h0 = sum_j w_j (lambda_j^2 l.H_j^-1.l/2 - lambda_j k)`.
The physical energy is `(p-q).B^-1.(p-q)/2 - h0`; its derivative includes
`v.p_t - v.B_t.v/2 - v.q_t - h0_t`. Dropping the affine terms changes physical
momentum and omits prescribed boundary work even when the homogeneous solve passes.

The implementation independently resolves each original pole, reconstructs
physical momentum and its time derivative, and compares the energy to
`c v.M.v/2 + sum_j w_j (a_j.M.a_j/2 + lambda_j E_C(a_j))`.
The latter is nonnegative: the complete augmented affine Gram matrix is checked
positive semidefinite, not only `C`. Its independently differentiated sum must
equal the full physical energy derivative exactly. No mass floor, shortened
pole list, iterative tolerance change or float conversion is introduced.

## Validation

**123 tests PASS**, 93.74 s, across the previous eight front/provenance modules
and both moving-pressure modules. Report:
`tmp/affine-moving-pressure-combined-20260919.xml`.

Ten new cases cover exact roundtrip and local-jet energy; an independent NumPy
pole/Legendre construction; each physical-momentum partial; refined physical
time differences; exact zero-trace recovery of the old result; three negative
controls omitting boundary shift/work; positive sub-float mass and quadratic
fields; invalid/unbounded affine forms. The first focused run had a test-fixture
TypeError (`Radical` has no exponentiation operator); repeated multiplication
corrected the fixture without changing a gate. Final focused result is 19 PASS.

The existing storage/face consistency failure remains open; this is not a
full-repository pass or evidence of a qualified nonlinear evolution law.

## Original-source replay is LIVE, not accepted

The new replay rebuilds original captured triangles and exact fan states.
It checks original owner volumes/rates and the preceding qualified affine
coefficients, then supplies the **original physical momenta and their rates**
as probes. It independently compares auxiliary energy to the local lifted jets.
Those supplied shallow-water rates are not claimed as a dispersive force law.

- Process **14076**, start UTC **2026-09-19T00:58:32.2675546Z**.
- Retained tool session **35230**. Do not launch a duplicate.
- Entry: `physics/scripts/audit_south_fork_affine_moving_pressure.py`.
- Trace input: `tmp/south-fork-front-prescribed-trace-v1-20260919.json`, SHA256
  `bc8d7b143777e54ce8757a143cf768e9f0c0b8d8f8295314264ba365f8071d15`.
- Original source: `tmp/south-fork-affine-front-flux-v1-20260917.json`.
- Pending output: `tmp/south-fork-affine-moving-pressure-v1-20260919.json`.

The complete protected current source/implementation map is checked before
starting and again at completion; no new historical exceptions or refreshed
hashes are allowed. All 13 records must remain, with unsupported 2 and 7 untested.
Index 0 has passed; index 1 has started. Process CPU advances from139.625 to
203.84375 s. The report has **not** completed or received an independent reload.
The earlier reflecting-pressure variation took about2382 s for this same slow
source case; absence of fresh output is not terminal evidence. Preserve the
running implementation until the final hash guard finishes.

## Next integration requirements

The pressure energy's primitive derivatives must now include the prescribed
flux/lift and both mass-denominator contributions. The old
`FrontPressureVariation` is reflecting-only; do **not** pass this affine metric
into it or interpret its homogeneous derivatives as valid for the new map.
Add an explicit compatibility guard once the active protected replay completes,
and qualify the affine variation separately. The new class is currently used
only by its tests and source audit, not by that old consumer or runtime.

Interacting-front conservation, nonlinear pressure force, source activation,
natural/radiating river boundaries, native iteration cost, and actual playable
render/contact integration remain required. A prescribed auxiliary trace alone
does not establish the correct natural river pressure boundary.

The existing sole hydraulic cook12672/session79088 continues unchanged.
New local3000 /12150 s passes BOTH state and artificial-bank audits, but is NOT
settled: outlet104.741632 versus inlet45.306955 m3/s; max depth3.999953 m,
max speed5.391680 m/s, per-step residual1.17982e-8 m3. All86,720 artificial-bank
sample cells stay exactly dry. Next local4000 /12200 s needs both audits.

Receipts in ignored tmp:

- `affine-pressure-hydraulic-3000-state-20260919.json`, SHA256
  `e88aa131e596217092f200ca0d9c2bd579f0f630a0bf8cd3602c13eff2aeb4bf`.
- `affine-pressure-hydraulic-3000-banks-20260919.json`, SHA256
  `e5b27539de25c89e29d339f6329f8530a7ddeb5cdd802fb5e57a715d2f80f8a0`.

No new build, motion/collision validation or FPS acceptance. Latest ordinary
25.003520 FPS /p95 48.329 ms still fails30 FPS. The cap interpretation choice
remains pending. South Fork, then Colorado, Pacuare, Futaleufu and the remaining
all-scene/crew/normalization/regression/release work remain OPEN.
