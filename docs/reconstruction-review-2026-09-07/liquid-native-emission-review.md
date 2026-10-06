# South Fork continuous native births and handoff

2026-09-10. The goal remains active; no scene acceptance, map promotion or commit.

## Implemented

The bounded regional probe can activate one explicit test inlet after initial
native birth. Its configured 60 particles/second is diagnostic, NOT captured
river discharge. The source uses a real wet-prior seed position and zero jitter.
The native stage records now include actual spawn-rate/event counts from Niagara's
prepared tick, so the audit checks observed births against the actual schedule.
Eight consecutive native handoffs retain before/after payload and identity
snapshots; later population growth is permitted only when independently accounted
for by recorded source births. Existing particles may not disappear, duplicate,
change their immutable birth identity or be mistaken for new births.

This mode uses a bounded 64-particle dispatch reservation/128 manual preallocation
for at most 16 initial particles and 12 measured one-particle birth steps. It is
not the dense production source/allocation or reset-lifetime policy.

Native persistent-ID capacity is now separate from particle storage capacity.
The live engine assigns IDs such as 896 while the particle capacity is 129; those
are valid within its 1024-entry ID table. Full native ID capacity is used to
preserve stayers and rebuild disjoint free-ID tables. Snapshot metadata and the
independent auditor retain both capacities rather than truncating the namespace.

## Evidence and failures retained

- `liquid-native-emission-v1`: rejected. Native births were present but several
  commits failed the handle transaction gate (bit16), because a valid high native
  ID was checked against particle capacity. No partial commit was accepted.
- `liquid-native-emission-v2`: exact birth/identity/handoff audit passes: nine
  initial plus nine planned/observed new births, eighteen retained particles,
  eight commits and fifteen owner changes. Final owner0 has15, source owner1 has3.
  Native birth counts are `[9,0,1,1,1,1,1,1,1,1,1]` through step11.
- However **v2 P2G FAILS**: 0.3541680177595481 m3 deposited versus
  0.3750000111758709 m3 expected, outside the original 0.0046879390920909585 m3
  numerical envelope. Exactly one particle's contribution is missing from owner1.
  The reduction itself is exact; source-region raw transfer has32 mismatches.
- Root cause: native NQ slot indexing uses `ExecIndex()`, which is relative to
  spawn/update. Calling its writer from both stacks overwrites slot0 when new
  births coexist with existing particles. The initial-only packet did not expose
  this collision. The fix moves neighbor insertion to one complete post-spawn
  particle simulation stage before P2G, with the update-stack writer disabled.
  No engine source change or relaxed conservation gate.
- Added the explicit NiagaraCore module dependency and used exported public node
  construction APIs; build37985 succeeds.
- `liquid-native-emission-v3`: capture completes, but the strict handoff audit
  rejects it because its first requested commit (step2) has zero owner changes.
  All nine particles move afterward; crossings begin at step3. Retained measured
  owner changes are `[0,4,9,1,1,1,1,1]`. This is NOT a passing handoff/P2G report.
- `liquid-native-emission-v4`: same implementation and unchanged audits, with
  explicit diagnostic velocity multiplier8 rather than4 to exercise an early
  crossing. Native source activation remains60 particles/s, not calibrated Q.
  Nine initial plus nine independently scheduled/observed births survive all
  eight commits: owner changes `[4,9,1,1,1,1,1,1]`, nineteen changes total;
  final owner0 has16 and source owner1 has2. Payload, identity, native free-ID
  namespace, and subsequent motion checks pass, with clean RHI validation.
  Step11 raw P2G passes for all18 particles and84 nonzero shared cells;
  reduction has zero mismatched components. Physical volume is
  0.375001023347977 m3 against0.3750000111758709 m3 expected, within the unchanged
  0.004773083203743487 m3 numerical envelope. The missing new-particle deposit
  in v2 is corrected, not tolerated by a weaker gate.
- `engine-liquid-emission-v1`: all ten engine regressions succeed, zero warnings
  or failures, no RHI errors. Includes the compiled native post-spawn NQ stage
  and rejection of spawn/update-relative NQ writes.
- 255 liquid-specific Python tests pass, including birth-loss/duplication/plan
  mismatch and separate larger native ID capacity.
- `liquid-native-neighbor-regression-v1`: non-emitting seeded regression also
  passes. Twelve particles survive three native commits (`[4,8,0]` owner changes),
  all twelve move afterward, and step6 P2G/reduction passes with94 nonzero shared
  cells. Physical0.2500002903202727 m3 versus0.2500000074505806 expected, bound
  0.0032955809513656974 m3. Clean RHI validation; engine process exits0.

## Remaining

Account for genuine exterior exits, resets/generation,
namespace lifetime and dense source allocation. Continue to connected dense
regional fluid/single surface/foam, raft and captured-reference/performance
acceptance. The authored test inlet is not evidence of calibrated river Q or
full-scene visual realism. Saved geographic map has not been modified.

Exterior implementation constraint: the current routing packet has only the
current particle position, and rejects all parent-exterior particles rather
than dropping them. Preserve that fail-closed behavior until the native ABI
retains the position before advection. Outflow needs an actual segment crossing
of a validated open parent face (not a regional cut, solid bank or floor), an
explicit exit identity/volume ledger, and atomic survivors/retirements. A mere
outside-position or outward-velocity test does not prove an authorized exit.
