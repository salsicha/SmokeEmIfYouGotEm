# Atomic survivor and exit ledger transaction

2026-09-10. South Fork remains incomplete; no scene, sustained-flow or FPS acceptance.

## Implemented

Destination assembly accepts optional, source-bound exit evidence. Without it,
the previous exterior rejection (bit2) is unchanged. Evidence must reference the
same immutable word/route/count buffers it classified and carry a finite positive
native particle volume. Classification still uses physical parent face rows and
the actual pre-advection segment.

The preflight checks complete source counts against inside/approved/rejected/
invalid exit counts. Any rejected exit or mismatch invalidates the transaction
(bit64). The append stage checks each route/candidate pair, then copies every
full-word payload either into a destination survivor range or a source-indexed
exit range. Exits retain exact source/index references, crossing face/row/fraction
and immutable identity words. Per-source counters track four faces plus total
retired; native particle-volume metadata accompanies each source. Final accounting
must reconcile both outputs before handle preparation/native commit can proceed.

Existing native commit uses the same transaction gate. A failure discovered even
after partial staging cancels **all native writes**. Valid all-exit owners receive
zero live count and rebuilt empty ID lookup/free lists. No CPU readback is needed
during the transaction. The combined survivor/exit payload has an explicit512MiB
staging limit, never a silent particle clamp.

`FRaftSimNativeParticleHandoff::Issue` now optionally builds exit evidence from
the actual native source snapshots and invokes this path. Its retained assembly
sample saves the exact exit words, references, records, five-count rows, source
capacities and native volumes after simulation stops, including empty ledgers.
The diagnostic flag `-RaftSimRegionalParticleRetirement` selects it and binds the
validated parent profile. This flag does not itself change the existing inner-
corner seed fixture into an outlet fixture, or enable parent boundary forcing.

The closed-population handoff auditor explicitly refuses retirement captures:
they require a dedicated survivor/exit ledger auditor. This prevents ignoring the
new ledger and mistakenly reporting outflow verification from an old count gate.

## Evidence

- Build99275 succeeds. `engine-liquid-retirement-v1` runs all twelve engine tests
  successfully with zero warnings/failures and no RHI errors; process exits0.
- The new actual GPU retirement test covers mixed exits/survivors with inter-owner
  handoffs, all particles retiring from both native owners, and exact complete
  source partition/payload/identity preservation. Native counts, ID lookup and free
  counts agree with survivors. Source volume metadata is preserved separately.
- Forbidden boundary rows, dishonest exit totals and a per-particle corruption
  discovered after preflight leave native counts, floats, integers and ID tables
  byte-for-byte unchanged. Evidence from another source buffer is rejected before
  graph dispatch. Existing closed/exterior-rejecting assembly tests remain green.
- Final build91837 adds retained ledger/native handoff integration and succeeds.
- `liquid-retirement-closed-regression-v1` is a live **non-retiring** emission
  regression with this build: all18 particles survive the original eight commits;
  seven consecutive pairs prove84 moving segments; all18 P2G origins refresh.
  Raw P2G/reduction pass unchanged,84 nonzero shared cells,zero reduction mismatches,
  0.375001023347977 m3 versus0.3750000111758709 m3 expected, original bound
  0.004773083203743487 m3. This proves no regression, not actual outlet retirement.
  Its engine process finishes with exit0.
- 261 liquid-specific Python tests pass. Saved geographic map remains unchanged.

## Next required work

Create a bounded live outlet packet using actual prepared wet seeds near a
validated outgoing parent face. Add the independent ledger auditor: reclassify
exit segments against original parent geometry, verify exact source partition,
identity uniqueness, per-face volume and actual native survivor counts/payloads,
then observe continued native motion/births with emptied owners. Do not treat a
zero-exit inner-corner run as outflow acceptance. Parent forcing/fixture selection
must remain explicit; neither unobserved exits nor supplied flags are evidence.

After actual live retirement: reset/generation/lifetime and allocation policy,
dense sustained inflow/outflow, single surface/foam, raft, reference/FPS acceptance,
then all remaining rivers/crew/cleanup/release and final commit.
