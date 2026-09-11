# Regional water-particle birth identity — 2026-09-10

South Fork and the full goal remain incomplete. This implements and verifies a
necessary part of particle handoff, **not handoff itself**, sustained flow,
photorealism, or performance. No playable map or saved Niagara system changed.

## Implemented

Regional startup now adds `Particles.RiverBirthOwner` and
`Particles.RiverBirthSequence` as persistent **integer** particle attributes.
The owner is the region where the particle was born. The sequence is copied from
native `Particles.UniqueID` at spawn, after Niagara assigns its monotonic spawn
sequence. It is not the recyclable `Particles.ID.Index` used by native neighbor
lookup. Neither new attribute is recomputed during updates. Migration must copy
both unchanged even if destination-local engine handles change.

The pair is unique within a regional simulation generation, assuming no complete
32-bit sequence wrap in one owner. Resets start a new identity namespace. The
eventual runtime coordinator must explicitly manage that generation and enforce
the counter-lifetime contract; this diagnostic is one uninterrupted generation,
not a shipped cross-reset/global-save identity service.

`RaftSimPackLiquidIdentityGPU` reads selected planar int32 components into int4
records without float conversion. It retains the actual GPU live count (including
an invalid over-capacity value, so it cannot mask an overflow). Invalid offsets,
missing buffers, insufficient stride and overflowing addresses are rejected.
Inactive allocation slots are zero. No native particles or handles are mutated
by the snapshot helper.

The native packet probe retains integer identities at the first P2G step and the
selected later P2G step **in the same execution**. Counts are read back and checked
against the independent position snapshot. The new auditor rejects intervening
resets, duplicate/missing/relabelled identities, incorrect birth ownership or
native sequence, float records and truncated files. It does not mistake matching
IDs in two independent runs for proof of persistence.

## Verified

- `liquid-native-identity-12-step3-v1`: three real wet-prior seed positions per
  selected owner, across four owners at the shared corner; other eight owners
  empty. Diagnostic velocities remain explicitly authored, not measured flow.
- All **12 distinct birth identities** persist from first to third P2G step;
  native birth sequences include 0,1,2 per owner. No owner changes are observed
  or claimed. See `identity_audit.json` in that directory.
- Independent native raw-volume/momentum and exact reduction checks still pass:
  zero reduced-component mismatches,48 nonzero shared-column cells; physical
  volume0.25000078650191426m³ versus nominal0.2500000074505806m³. This is a tiny
  packet, not dense NQ capacity or sustained discharge conservation.
- Capture29.0531seconds includes startup/compilation/blocking readbacks, not FPS.
- `engine-liquid-identity-v1/index.json`: **all six tests succeeded**, one
  unrelated HTTP-connectivity warning in RegionalExterior, zero failures.
  Test duration18.6993seconds. The warning was a timeout fetching Google's
  connectivity endpoint, not an ignored water assertion.
- Actual GPU integer test verifies padded/reordered planes,16777217, signed
  32-bit extremes, empty and over-capacity counts, both SRV/UAV count bindings,
  and invalid input rejection. Contact/exterior compiled identity persistence,
  boundary halo, raw reduction and native resolve tests also pass.
- **232 Python liquid tests pass**, including identity reorder/local-index
  reuse, distinct birth-owner namespaces, duplicate/loss and float-data rejection.
- Saved `SouthForkRegisteredRockPlayable.umap` remains SHA256
  `36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.

## Next

Implement actual same-step regional routing/import/export. Carry all particle
state and these birth tags, preserve volume, and update local native counts,
ID-to-index and free-ID tables consistently. Dispatch/allocation bounds are
prepared before GPU execution: never just append to an unallocated empty owner
or increase its GPU count beyond prepared capacity. Enforce reset/sequence
lifetime semantics and verify face/corner crossings with real particles.

Regional affine-state integration, dense connected wet projection/flux, shared
surface/foam, full-rapid raft/collision/shoreline/reference/performance validation
and the original remaining river/crew/cleanup/release queue all remain required.
No commit or push. Final build16655/native66597/engine64295 are terminal. This
turn made implementation and verification progress; there is no external blocker.
