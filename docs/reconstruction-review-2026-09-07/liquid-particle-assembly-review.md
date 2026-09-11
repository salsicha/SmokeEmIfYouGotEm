# GPU receiving-side particle assembly — September 10, 2026

South Fork remains incomplete. This builds on the verified
[routing candidates](liquid-particle-routing-review.md). It adds receiving
buffers and transactional capacity/accounting checks; **it does not commit those
buffers into Niagara's live datasets**.

## Implemented

`RaftSimAssembleLiquidParticleDestinations` accepts all 2–16 source owners with
one complete native float/int ABI and explicit destination capacities. The GPU
checks source accounting and destination capacity before copying any particle.
Overfull destinations, invalid particles, and exterior particles without an
outflow policy invalidate the whole transaction. Sources remain unchanged.

Valid transactions compact all native word planes into receiving-owner ranges,
retaining an exact source-owner/index reference per particle. Every field is
copied as integer bits; no float conversion of identities or opaque state.
Final accounting detects malformed routes and missing/extra receiving records.
An explicit 512 MiB word-buffer limit rejects oversized staging allocations;
it never clamps live counts. Slot order within an owner is not promised—identity
and payload preservation are checked independently of GPU append order.

The new native probe flag `-RaftSimRegionalParticleAssembly` requires the routing
packet probe. It snapshots the receiving buffers from the same render graph as
the actual native packet. Readbacks happen only after the diagnostic simulation
stops. Its conservative small-fixture allocation is **not** a production dispatch
budget, runtime performance result, or allocation policy for full river flow.

## Verified evidence

- Final development build succeeded, session 89304 terminal.
- `engine-liquid-assembly-v1` failed before tests: Unreal's shader parser rejected
  grouped root-parameter declarations. Splitting them into separate declarations
  fixed shader compilation; no engine files or compiler settings were changed.
- `engine-liquid-assembly-v2/index.json`: all eight engine tests succeed. One
  unrelated HTTP `google.com/generate_204` connectivity timeout warning; zero
  test failures. GPU assembly, routing, identity, contact, exterior, boundary,
  raw transfer and normalized transfer all ran with RHI validation.
- Assembly test covers lossless cross-owner compaction, receiver overflow with
  no published payload, exterior/invalid rejection, corrupted route rejection,
  empty and unallocated sources, and sixteen-owner exchange. Full-bit comparisons
  include values outside exact float integer precision. Different source ABIs
  are rejected before dispatch.
- `liquid-native-assembly-step3-v1/capture.json`: complete, no exchange error;
  28.8691444 seconds including blocking readbacks, **not FPS or frame time**.
- `assembly_audit.json`: twelve actual native particles assembled once each;
  six cross-owner particles; every native float/int word plane is bit-exact
  against its source snapshot. Independent physical routing verification runs
  as part of the assembly audit, so agreeing with a wrong destination table
  cannot pass. No stale payload in unused receiving capacity.
- `identity_audit.json`: all twelve birth identities preserved over the same
  first-to-third-step native generation; native ownership changes remain zero
  because this is staging, not a native commit.
- `native_transfer_audit.json`: raw reference P2G passes, zero reduced-component
  mismatches, 72 nonzero shared-column cells. Physical volume
  0.2500010108342394 m3 versus nominal 0.2500000074505806 m3, within the existing
  conservative numerical envelope 0.002685700202736215 m3. Not sustained-flow
  acceptance or bathymetry calibration.
- 240 `test_liquid*.py` unittest tests pass; scoped `git diff --check` passes.

Saved playable-map SHA256 unchanged:
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
Prepared-manifest SHA256 unchanged:
`11ec3a4e36c4cf1a7a395ac269bab8ffad6653ae50009ad5faa3b436d6f5a0b3`.
No saved-map promotion, beauty screenshots, visual/FPS acceptance, commit or push.

## Next: actual native handoff

The receiving assembly must be applied to native buffers with consistent live
counters, bounded dispatch/spawn capacity and valid local persistent-ID tables.
Preserve staying particles' local persistent handles; incoming particles need
unused destination handles and an acquire-tag policy that cannot collide with
native births or stale handles. Birth owner/sequence must remain unchanged.
Generation/reset and sequence lifetime remain required, not deferred acceptance.

Engine inspection reconfirmed that readback-based dead-particle subtraction can
change CPU upper counts before `PrepareTicksForProxy`, and preparation derives
spawn and dispatch sizes before GPU stages. Adjusting live counters after that
without a matching reservation contract can skip incoming particles or suppress
births. Never blindly call `AllocateGPU` on a live imported buffer: it can replace
storage and clears the count offset. Empty receiving owners require valid native
allocation and count state as well. No engine source modifications were made.

Then verify subsequent native steps, not just a successful copy; continue dense
wet transport/affine state, continuous shared surface/foam, raft/terrain/rock
consistency, real-reference comparison, and measured performance before moving
to the other rivers and original queue.

Previous goal turn was progress; this turn adds verified receiving-side GPU code
and native evidence. All processes terminal: final build 89304, engine test 94062,
native replay 94047 (confirmed by both handle completion and process inspection).
Goal active; no external blocker.
