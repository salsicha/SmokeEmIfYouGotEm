# South Fork native particle handoff

2026-09-10. The scene and overall queue remain incomplete. This is actual native
simulation integration, not visual acceptance or a full-flow performance result.

## Implemented

`RaftSimLiquidParticleCommitGPU.cpp/.usf` writes the receiving assembly into
Niagara's actual float/int buffers, persistent-ID lookup and live GPU counters.
Every source word is retained except the explicitly remapped local ID/index tag.
Staying handles remain unchanged. A transaction-wide capacity/handle gate prevents
partial writes when any receiving owner cannot accept the assembly. Native sinks
and count slots cannot alias; unused ID-table entries are cleared.

The regional probe reserves a bounded dispatch upper count before tick preparation
and commits after the final aligned particle stage, before native free-ID rebuild.
It retains exact native before/after snapshots and a later native P2G snapshot.
This reservation currently covers already-populated owners and a no-new-birth,
single-generation packet. It is NOT the production allocation/lifetime policy.

Repeated commits now have distinct increasing transfer epochs and stable retained
snapshot storage. Each commit's full native words, identity/free tables, physical
destination and following motion are independently audited. Repeated stays do not
require artificial crossings, but still require motion and exact persistent IDs.

## Verified evidence

- `liquid-native-handoff-step4-v1/handoff_audit.json`: one actual native commit;
  12 particles retained, 6 owner changes, all 12 move afterward. Receiving owner 0
  contains 9 and owner 4 contains 3; exporting owners 1 and 5 are empty.
- The same run's `native_transfer_audit.json`: native step 4 P2G passes; zero
  reduced-component mismatches, 72 nonzero shared cells. Physical volume
  0.25000071138492785 m3 against 0.2500000074505806 m3, within the independently
  predeclared floating-point envelope (not a sustained-flow conservation test).
- Exact birth identity passes across the native commit. RHI-validated log clean.
- `liquid-native-handoff-repeat3-v3/handoff_audit.json`: three consecutive actual
  commits, with owner changes `[6, 3, 0]`; all 12 particles survive and move on
  native step 6. Final owner 0 holds all 12, with no particles duplicated in the
  exporters. All before/after native payloads, distinct epochs, unchanged staying
  handles, imported handles, free-ID accounting and intermediate motion pass.
- The repeated run's P2G audit passes with zero reduced-component mismatches and
  84 nonzero shared cells. Physical volume is 0.2500001434564183 m3 versus
  0.2500000074505806 m3; the declared numeric envelope is 0.0032955809513656974 m3.
  No RHI errors. The blocking capture's 29.32 seconds is NOT an FPS measurement.
- `engine-liquid-commit-v2/index.json` and final `engine-liquid-commit-v3/index.json`:
  10 engine tests succeed, zero warnings,
  failures or not-run tests. Commit tests include untouched sinks on invalid
  transactions, unallocated receiving capacity failure, padded word strides,
  exact float bit patterns, ID remapping and native counter updates.
  Final regression process exited 0; its RHI log is clean.
- 248 liquid-specific Python unittest tests pass. A mistakenly broad discovery
  invocation failed on unrelated missing `raftsim`/`pytest` setup; that invocation
  is not evidence for the complete physics suite.

## Rejected evidence and corrections

`liquid-native-handoff-step3-v1` could not reserve initially empty owners.
`step3-v2` changed native counts but had incorrect float/int buffer transitions,
and captured too early to prove subsequent completed motion. Neither is accepted.
`step4-v1` corrects float/int access to SRVMask and captures after completed motion.

`liquid-native-handoff-repeat3-v1` completed capture but failed RHI validation:
Niagara restores the counter to SRVMask|CopySrc at the last dispatch GROUP, which
is not necessarily the last stage of a particular simulation tick. The probe now
uses Niagara's exported count-state query, brackets native accesses with that
state, and restores it before engine readback. `repeat3-v2` removes those errors
but captured only five native steps when six were requested: editor frames do not
count completed native GPU steps. The script now polls the probe's flushed
`live-status.json` for actual packet readiness. `repeat3-v3` passes the full audit.

## Remaining

Support actual initially empty receiving owners,
continuous births/exits, reset/generation and persistent-ID namespace lifetime.
Integrate dense regional fluid/affine transport and connected reconstructed
surface/foam, then actual raft, collision, reference imagery, temporal stability,
and CPU/GPU/FPS acceptance. No map promotion, final commit or push was made.
Saved geographic map SHA256 remains
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.

The next allocation investigation has a concrete engine basis: `PrepareTicksForProxy`
uses the emitter's preallocation only when its CPU upper count is nonzero, or
`fx.NiagaraBatcher.FreeBufferEarly` is disabled. Empty owners currently receive a
one-slot allocation despite `PreAllocationCount=32`. Do not grow a live native
buffer blindly: native `AllocateGPU` may recreate it without copying particles.
Reservation must cover initial empty owners and reset ticks before an actual
empty-to-nonempty handoff test. No new-birth or reset correctness is claimed.
