# Exact shared pressure construction: full-rate parity, reference cost reduced

September14,2026. Same-geometry W/V reuse plus exact endpoint cuts reduces the
captured CPU reference-rate samples from~36s to~24-26s without changing any
output bits.234 combined regressions and seven full original-source rate checks
pass. This is reference-construction work, NOT native performance, full-history
physics, terrain/contact integration, playable30FPS or scene acceptance.

## Reuse only what is actually identical

New `physics/scripts/shared_pressure_construction_reference.py` builds W/V once
for the first pole, using the unchanged original constructor. W/V do not depend
on pole length or nonbreaking fraction. The second pole reuses those exact,
read-only row/column/coefficient arrays, while recomputing its diagonal and
same-cell off-diagonal in the ORIGINAL row and column insertion order. Python
coefficient scalars and multiplication/addition ordering are retained; no
vectorized summation changes the rounded preconditioner.

Reuse requires the same geometry object, current exact geometry bits, read-only
depth/bed/edge arrays and the same zero-mass projection mode. Geometry hashes are
recomputed on each call, not assumed valid forever. Pole length, fraction shape,
range/finiteness and projection type are revalidated. Fraction is copied for
each pole. Cached coefficient arrays are also checked for mutation. A changed
geometry/projection/coefficient or writable geometry forces an original rebuild,
not stale reuse. A process-scoped context retains at most one geometry and
restores the original constructor after exceptions and nesting. No stage's
geometry, state or rates are frozen. No live original module/process is changed.

Tests cover singleton/two-cell aliases, periodic and closed boundaries, varied
fractions, all coefficient/preconditioner/action/solve bits, exact dry rows,
positive films down to2^-1070, validation on cache hits, changed geometry,
projection mode, writable arrays, tampered cached coefficients and cleanup.

## Exact partial-cut basis experiment

New `physics/scripts/pressure_cut_basis_reference.py` factors the existing
pressure polynomial as `T=A*P+C*B` and its exact directional derivative. It
specializes exact endpoints and uses a bounded4096-entry cache for partial-cut
basis values, keyed by ALL exactH,R,Ht,Rt Fractions. Every scalar input and
feasible tangent is still validated before reuse. Coefficients, derivatives,
transmitted/blocked integrals remain arbitrary-precision Fractions. Exact
`P-T` retains tiny blocked slivers; it is not a rounded floating subtraction.
No pressure/rate term, including a tiny nonzero one, is discarded.

The captured rate makes14008 closed,104338 full and90830 partial calls. The
partial cache has45415 hits/45415 misses and stays at4096 entries. Exact outputs
pass900 random partial/tangent cases, extreme/near-endpoint fractions, below-
binary64 heights, huge pressure/rates, cache-key changes and invalid inputs.
However, repeated timing below does NOT establish a robust additional benefit
over endpoint/shared construction. Keep this variant opt-in, not the default
candidate merely because one sample is faster.

## Complete captured-source audit

Extended the separate `audit_pressure_cut_endpoints.py` to check original versus
both construction variants. It now also retains exact rows, columns, W/V,
diagonal and off-diagonal hashes in addition to full FV rate, CFL, both pressure
solutions, stage/pressure/boundary diagnostics and original operator/RHS fixture
payloads. Inputs are read-only; all source-module hashes present at launch must
remain unchanged through completion. Nothing is manufactured asA*x.

First complete sharing audit30565 TERMINAL exit0: original35.761510400s,
endpoint-only29.824340400s, endpoint/shared24.162866400s. All outputs exact; one
build and one reuse.202 combined regressions passed4.81s at that revision.

After adding cached-coefficient mutation protection and the partial basis,
audit26770 TERMINAL exit0: original36.190536100s, basis/shared24.839273700s.
All full-rate bits and original fixture payloads exact.234 combined regressions
pass5.34s. These include construction, geometry, tangents, nonlinear pressure,
boundary/adapter, native reader/fixture and requested ownership/history tests.
They do NOT constitute the full9.066667s captured history or native geometry.

### Alternating timing control, not cherry-picked samples

Audit99219 TERMINAL exit0. One original control36.895705300s followed by three
alternating-order pairs: endpoint→basis, basis→endpoint, endpoint→basis.
Every one of these seven full rates passes all original-source/bit checks.
Every candidate records exactly one original W/V build and one reuse. Timing
includes the full CPU FV rate/pressure operation, excludes subsequent fixture
encoding, and runs under shared background load.

| Pair | Endpoint/shared seconds | Basis/shared seconds |
| --- | ---: | ---: |
|0|25.944261400|26.064669100|
|1|24.855843700|24.445221000|
|2|23.386622900|22.178377600|
|Mean|24.728909333|24.229422567|

Both variants get faster later in the run. The basis mean is only~2% lower,
with overlapping ranges and one slower pair; these observations are not a
stable additional speedup claim. The simpler endpoint/shared version remains
the preferred isolated construction candidate. No option has been installed
into either running original history or the game. GPU/native component cost
still requires separate optimization and verification.

All complete-rate outputs have SHA256
`3cb142f3dc4ede1c6cb9ff92bfb31d86117de9a8429f4293f22495f83c07ee80`.
Original captured source SHA remains
`0114ce4611375f4e169e077d36747754306b867e67fa44bf7858ca5566f6bf10`;
fixture manifest SHA remains
`d81d0979f5f26c8382c6609aff7f17dd462758ad4b3530634c3e977af3b390a0`.

## Artifacts

- `tmp/south-fork-shared-pressure-construction-v1-20260914.json`, SHA
  `aafcd20ba3822aaaf3f528e019b0782550e4d43394f3e461d68c2e0572f77a14`.
- `tmp/south-fork-shared-pressure-cut-basis-v1-20260914.json`, SHA
  `8b40ac9e5f5b7cbac3700e638428178ead5305dc9f0662938d21420d32178237`.
- `tmp/south-fork-paired-pressure-construction-v1-20260914.json`, SHA
  `4f43a4779e779fbd29b7419237c57c42db27345da534c1110bfbffa5b5e2b85f`.
- Shared constructor source SHA
  `245e723e04f29683a55e2649375ca8a08b1d2d67514b5ee589eeb820f2c7a8ed`.
- Cut-basis source SHA
  `bc1838ada329501611b82d752e2cd11ae912933bf66a71ef095017123b28eb69`.
- Final comparison audit source SHA
  `f25a0f4dee9270fd64e589716a592a8dd43104080472a82d473129c9efc278bc`.
- Shared tests SHA
  `506b0ff40daf220ff459977e624a5d5ccfbb64a8ed5379536be535a74fa30725`;
  basis tests SHA
  `d8fd5b4dbcf23b91e8cba2054fb8f1183f1b60dd14681926dd4b5b7d09a6f676`.

## Remaining work and next action

The original main replay59896 and diagnostic95666 remain live with their source
dependencies unchanged. Main last observed accepted0.508850045659s, speed46.2m/s,
20 rejected trials in the current interval; this is NOT stability acceptance.
Full requested9.066667139530182s and both owner moves are still unproved.

The river cook74818 completed8000s; BOTH final state/artificial-bank audits pass,
but outflow102.5608m3/s remains above inflow45.3070m3/s. See
[the full-river checkpoint record](full-river-expanded-checkpoint.md) for the
verified continuation, not an inferred settled-state claim.

Next native performance task: qualify exact-operation-preserving phase fusion
for the GPU pressure solve, with independent original operator/true-residual
checks and sustained timing. The current325 dispatches per40CG solve remain
test-only and two poles cost~7.1ms before assembly/evolution/rendering. Do not
weaken the1.6ms component gate or change120Hz physics to claim30FPS. Native
geometry/rate assembly, full evolved ownership, outer wave/foam return coupling,
terrain/contact/playable validation, later rivers, crew, release and final
commit remain OPEN. Video retry09:08UTC failed both runtime paths and both web
opens; no new footage or visual acceptance was claimed.
