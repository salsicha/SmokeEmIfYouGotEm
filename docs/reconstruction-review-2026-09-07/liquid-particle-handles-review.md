# Receiving persistent handles — September 10, 2026

South Fork is still incomplete. This pass prepares collision-free persistent
handles for the [receiving assembly](liquid-particle-assembly-review.md), without
modifying Niagara's live particles or counters.

## Implemented

Four GPU phases preserve each staying particle's local ID index/acquire tag,
construct unused destination indices, assign incoming particles distinct indices,
and finalize handle accounting. The ID-to-particle lookup and remaining free-ID
prefix are complete and disjoint. Incoming IDs pop from the tail of the free
list, so the remaining prefix contains only genuinely unused indices.

Birth identities and all assembled word planes remain unchanged; proposed local
handles are separate until a native commit. Invalid or duplicate staying IDs
invalidate the transaction with error bit16. Destination ranges come from the
assembly's own stored capacities rather than a second caller-provided partition.

Incoming acquire tags use a caller-supplied positive epoch with the high bit set.
Native tags must currently be below that namespace. Zero/terminal transfer epochs
and high-bit native tags are rejected. This is an explicit **one-generation
preparation contract**, not a complete runtime lifetime policy: the coordinator
must prevent epoch reuse/wrap and native namespace crossing before simulation,
and invalidate stale references correctly on reset. Do not claim those policies
are implemented simply because the current API rejects invalid inputs.

Native `TickCounter` is public in the engine header but not DLL-exported. The
capture uses `GetIDAcquireTag()` on actual current native data buffers instead.
Engine source shows `DispatchStage` writes that metadata from the native tick
counter. No engine sources or import libraries were modified.

## Evidence

- Final development build 51197 succeeded.
- `engine-liquid-handles-v1`: numerical checks succeeded, but the test failed RHI
  validation because two test input/readback buffers lacked `BUF_SourceCopy`.
  Corrected creation flags. An intermediate link failed on the unexported
  `TickCounter`; `engine-liquid-handles-v2` consequently exercised the old binary
  and repeated the same RHI errors. It is not validation of the corrected code.
- `engine-liquid-handles-v3/index.json`: final successfully linked code, all nine
  tests succeed, zero warnings/failures. Covers handles, assembly, routing,
  identities, contact, exterior, boundary exchange and P2G reduction/resolve.
- New GPU tests check preservation of staying indices and positive/negative
  acquire tags, colliding incoming source IDs, a previously empty destination,
  invalid/duplicate staying IDs, complete used/free partition, untouched full
  input payload, empty receiving buffers and acquire-tag namespace rejection.
- `liquid-native-handles-step3-v1/capture.json`: complete, no exchange error;
  28.8606042 seconds with blocking diagnostic readbacks, **not frame time**.
- `handles_audit.json`: six staying handles unchanged, six imported handles
  distinct and correctly mapped, complete/disjoint free-ID lists for all twelve
  prepared receiving owners. These are receiving capacities of 24 IDs each,
  **not proof of sufficient native destination allocation**.
- `assembly_audit.json`: all twelve particles preserved once each, all 11 float
  and 6 integer component planes bit-exact; six physical cross-owner destinations.
- `identity_audit.json`: twelve native birth identities preserved over first to
  third step; actual native ownership changes still zero (no native commit yet).
- `native_transfer_audit.json`: raw P2G and exact reduction pass, zero reduced
  component mismatches, 72 nonzero shared-column cells; physical volume
  0.2500010108342394 m3 versus nominal 0.2500000074505806 m3, within the previously
  declared numerical envelope. Not a dense/sustained flow acceptance test.
- 243 `test_liquid*.py` unittest tests pass. Scoped `git diff --check` passes.

Saved playable map remains SHA256
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
No saved-map promotion, visual/FPS acceptance, commit or push.

## Next: commit and subsequent native steps

The next implementation must actually apply the assembled word planes, override
only local ID/index tag planes with the prepared handles, update the destination
ID lookup and GPU count, then observe those particles on subsequent native steps.
Keep transaction-wide capacity/handle failure gating so one destination cannot
commit while another silently drops water. Match RHI transitions to native
buffer usage; no blocking CPU handoff.

Native free-ID recomputation occurs after the post-group finalization callback,
so a correctly ordered final-group commit can supply the updated ID-to-index
table before that recomputation. Do not inject mid-step where the already-built
neighbor grid would still describe old particle indices. Subsequent-step native
dispatch bounds and allocations must reserve incoming capacity before tick
preparation; modifying GPU counts alone is insufficient. Reserve spawn headroom,
handle empty receivers and reset ticks, and account for native asynchronous
dead-count readbacks. Avoid reallocating live buffers without preserving data.

For the bounded initial proof, all twelve particles fit within a known reservation
and no post-burst sources emit. That can establish real native handoff before
extending to births/exits, empty receivers, reset/lifetime and full dense flow;
it cannot certify those later cases. The prepared receiver currently has nine
particles for owner0 and three for owner4, while sources still contain three each
in 0/1/4/5. Next-step native snapshots must demonstrate the actual owner change,
not merely repeat staged destinations. Preserve the stricter original visual,
geographic, raft and performance acceptance work afterward, then the other rivers.

Previous goal turn was progress; this turn adds actual GPU/native handle evidence.
All owned processes terminal: final build51197, engine8098, native31587. Goal
active, no external blocker.
