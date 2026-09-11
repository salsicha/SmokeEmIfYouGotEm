# Native particle segments before exterior retirement

2026-09-10. South Fork remains incomplete; no map promotion or visual/FPS claim.

The regional post-spawn particle stage now assigns the position-typed
`Particles.RiverStepStartPosition` from the actual `Particles.Position` before
FLIP/PIC advection and terrain contact. It is retained in native particle storage,
not reconstructed from velocity, a region origin, or a previous CPU sample.
Full-state native transfers copy this additional float3 without conversions.
Packet setup discovers its compiled component offset and refuses a missing or
inconsistent regional layout. Snapshot records declare `route_step_start_offset`.

`audit_liquid_native_segments.py` first requires the existing complete native
handoff/birth/RHI audit. It then matches immutable integer birth identities across
consecutive snapshots: each particle's next-step origin must bitwise equal its
previous committed position, without unaccounted owner changes or missing keys.
At the retained pre-advection P2G snapshot, origin must also equal current position
for every live particle, including the new births. No tolerance can hide a stale
origin, current/end-position substitution, or velocity-derived approximation.

## Evidence

- Build5599 succeeds with the new attribute and snapshot ABI.
- `liquid-native-segments-v1` completes with clean RHI validation: seven consecutive
  step pairs,84 native particle segments, all84 moving. All18 particles at the
  P2G snapshot have refreshed origins. The same eighteen-particle birth/handoff
  audit passes. Raw P2G and reduction also pass unchanged: volume
  0.375001023347977 m3 versus0.3750000111758709 m3 expected, declared bound
  0.004773083203743487 m3;84 nonzero shared cells,zero reduction mismatches.
- `engine-liquid-segments-v1` failed one test, specifically its shader-string
  assertion. Generated code actually routes the correct position through a
  GUID-named `SetVariables` module. The test now checks both links, invocation
  and persistent native loading. This is not suppression of a missing attribute.
  The independently measured live segments above pass the exact bitwise check.
- Rebuild70120 succeeds. Final engine regression `engine-liquid-segments-v2`
  finishes with all ten tests successful (nine clean, one with an unrelated
  Google connectivity-probe HTTP timeout warning), zero test failures and no
  RHI errors. Its process exits0. No owned build/Unreal process remains running.
- 261 liquid-specific Python tests pass. New cases reject stale, fabricated,
  nonfinite, missing, duplicated and wrong-owner origins; reordered compaction
  and independently accounted new births are supported.

Saved geographic map remains unchanged, SHA256
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.

## Next integration

Exterior particles are still rejected by the existing transaction (bit2). No
retirement has been enabled. Use the proven native segment with the validated
physical parent face profile to classify real outward crossings. A region cut
is not an outlet; the bed/solid banks and domain floor/roof cannot silently drain.
Retire only an explicitly accepted open-face crossing, retaining its birth key,
full state and volume in an exit ledger, atomically with the survivor commit.
Then verify sustained inflow/outflow balance, reset/generation and allocation
lifetime before dense regional fluid, surface/foam, raft and visual/FPS acceptance.
