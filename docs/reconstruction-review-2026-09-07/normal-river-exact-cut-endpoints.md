# Exact pressure-cut endpoint optimization: isolated full-rate parity

September 14, 2026. The separate endpoint experiment preserves the complete
original captured FV rate, CFL, both pressure solutions, operator/RHS fixture
payloads, stages and boundary diagnostics bit-for-bit.164 regressions pass with
the candidate enabled in an isolated process. This is NOT an evolved-history,
native-cost, physical-model or playable-scene qualification. Original live
dependencies and histories remain untouched.

## Narrow algebraic change

New `physics/scripts/pressure_cut_endpoint_reference.py` validates every input
with the original exact conversion and feasibility rules. It specializes ONLY
exact rationalR=0 orR=H. Every partial cut calls the original reference.

For zero retained height, transmitted pressure and its first directional rate
are exactly zero; the blocked pressure/rate retainP/Pt. For full retained height,
transmitted pressure isP, blocked pressure is zero, and the transmitted rate is
`Pt + B*(Rt-Ht)`. The latter term is essential for a closing cut; it must not be
discarded by assuming a stationary/full-height tangent. Blocked rate remains
`Pt-transmitted_rate`. All computations are exact Fractions, with no float
cancellation, depth threshold, positive floor, model/source change or cache.

The context patches only the two imported cut-function bindings in its own
process and restores them even after exceptions/nested scopes. It does not
modify original source modules or running processes. It is not automatically
enabled by the production adapter or either ongoing replay.

## Verification, including initial audit harness failure

New tests cover exact partial/endpoint fractions, smallest positive binary64
height, rational heights below binary64 range, huge coefficients/rates,300
random exact cases, one-sided tangents, invalid inputs even when an endpoint
formula would not use them, and context cleanup/nesting.

Initial suite:67 tests pass0.73s. Audit41754 evaluated the original rate35.2008s
and candidate29.6680s with identical full-rate hashes and original fixture
payloads, but its final Python dictionary comparison failed on array-valued
boundary diagnostics (`truth value of an array ... ambiguous`). That run is
NOT recorded as a complete audit pass and wrote no success report.

Fixed only the new audit: array diagnostics are represented by exact dtype,
shape and byte SHA; float diagnostics include their binary64 bits, preserving
signed zero. Added a regression for array-valued equality/JSON serialization,
signed zero and rejection of object arrays.68 direct tests pass1.07s.

Fresh audit2877 TERMINAL exit0:

| Full captured original-source rate | Wall seconds |
| --- | ---: |
| Original reference |35.264790300|
| Exact endpoint candidate |31.280540900|

This one shared-load sample is about11.3% faster, not a stable speedup bound or
runtime-budget pass. The earlier incomplete-audit timing showed a larger change;
retain both rather than cherry-picking it. Both costs are still far from native
requirements. The independent captured source and its original boundary bracket
are unchanged, and actual nonzero dry-activation rates are retained.

The completed audit checks:

- Complete FV rate SHA for both:
  `3cb142f3dc4ede1c6cb9ff92bfb31d86117de9a8429f4293f22495f83c07ee80`.
- Exact binary64 CFL and both pressure-solution hashes; all stage, pressure and
  boundary diagnostics including array bits.
- Both original operator/RHS/expected-action/preconditioner fixture payloads
  match the independently retained original fixture manifest, not a recaptured
  replacement problem. State and bed are read-only and hashes unchanged.
- All source-module hashes present at audit launch remain unchanged at exit.

Broader isolated-context regression:164 tests pass5.01s. It includes endpoint
and original cut tests; reconstructed geometry, actual-mass tangent, boundary,
nonlinear pressure, adapter, acceleration, damped polynomial, native binary
reader and original fixture checks. Neither CPU history was hot-patched.

## Artifacts

- `tmp/south-fork-pressure-cut-endpoints-v2-20260914.json`, SHA256
  `db1aa418b465bd301dd9e29cb4c57fc727f163c57b9e939f6e2e226076ff2a95`.
- Candidate source SHA
  `48b70daa029a5b284d7f2537fc96c9a0e1aae37ccee3415fa8db953a3cd7c18f`.
- New audit source SHA
  `576e5b636aaa8c276243087beedd4ad120f2f458a0ce1cfc4b5a1dbee22593c9`.
- New test source SHA
  `e9476278fe39874f1164b399820fef7655ecdd8ba09a92392acfd3030131a5a9`.

## Next and unchanged scope

CPU construction still dominates. Next useful independent experiment: avoid
duplicating identical W/V coefficient construction for the two pole lengths
within ONE unchanged geometry/rate evaluation. Recompute length-dependent
diagonal/off-diagonal terms in the ORIGINAL accumulation order. Reuse must be
keyed to the same immutable geometry/projection mode and validated fraction;
never freeze geometry between stages. Require exact coefficient, full-rate,
fixture and regression parity before considering a separate optimized replay.

Native resident performance evidence is in
[the telemetry review](normal-river-native-cg-resident-telemetry.md): all960
solves exact, but two poles alone~7.1ms still fail the component gate. Main
original9.066667s/two-move history remains unproved; separate diagnostic prefix
is not interchangeable with it. BOTH7900 cook audits pass but flow is unsettled;
next COMPLETE8000/local40000 requires BOTH audits. Terrain/contact/wave/froth
integration, other scenes, crew,30FPS play, release and final commit remain OPEN.
