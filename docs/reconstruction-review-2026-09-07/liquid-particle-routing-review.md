# Native full-state particle routing — September 10, 2026

South Fork remains incomplete. This pass verifies **GPU routing candidates**, not
native ownership handoff, sustained water flow, photorealism, or frame rate.

## Implemented

Fixed the pending routing build errors (const structured-buffer array views and
signed byte-size comparisons). Added an actual GPU regression test and an
independent audit of native snapshots.

The routing kernel preserves every native float/int component as uint32 bits in
an immutable, component-major packet. It chooses a physical owner in the common
river frame, independently of computational halos. Internal boundaries are
half-open; the outer maximum edge belongs to the final physical cell. Exterior,
invalid-position, and over-capacity records are explicitly counted, not silently
removed. The current native ABI has no half components; unsupported half layouts
are rejected. No native particle buffer, live count, or ID table is modified.

The native probe stages all twelve owners after the selected aligned P2G group.
The fixture uses three actual prepared seed positions in each of owners 0, 1, 4,
and 5, with four-times diagnostic packet velocity to cross physical boundaries
within three native steps. This velocity is a test input, not river calibration.

## Evidence

- Final Unreal Editor development build succeeded; build session 39669 terminal.
- `engine-liquid-routing-v1/index.json`: seven tests succeeded, zero test warnings
  or failures. Covers routing, identity, regional contact/exterior, raw transfer,
  normalized transfer, and boundary exchange with actual GPU/RHI validation.
- Routing GPU test preserves all word bits, including signed zero, NaN auxiliary
  payloads, large signed IDs, padded input strides and inactive capacity. Checks
  all four owners, internal/outer edges, exterior and invalid positions, empty and
  over-capacity counts, and rejection of overlapping owners/unsupported ABI.
- `liquid-native-routes-step3-v1/capture.json`: complete, no exchange error.
  Capture took 29.0690728 seconds including blocking diagnostic readbacks;
  **this is not a frame-time measurement**.
- `routes_audit.json`: all twelve owners accounted for, twelve live particles,
  six actual physical-boundary crossings. Owner 1's three particles and owner 5's
  three particles route to physical owner 0. Remaining particles stay in 0/4.
  Destinations agree with an independent float64 canonical station/lateral
  bounds calculation, not a copy of the GPU routing table. Captured position,
  velocity, and birth/native identity planes are bit-exact; all inactive words
  are zero and route counts match every live record.
- `identity_audit.json`: all twelve birth identities persist from first to third
  step in the same uninterrupted native generation. **Native owner changes remain
  zero**, as expected while routing is staged but not committed.
- `native_transfer_audit.json`: raw P2G matches the independent numeric reference,
  zero reduction-component mismatches, 72 nonzero shared-column cells. Physical
  volume 0.2500010108342394 m3 versus nominal 0.2500000074505806 m3, within the
  previously declared floating-point envelope 0.002685700202736215 m3. This
  short packet check is not dense-flow or sustained conservation acceptance.
- 236 `test_liquid*.py` unittest tests pass. Scoped `git diff --check` passes.

The first routing audit invocation exposed that prepared canonical axes are XY
pairs, not XYZ triples. The reference now accepts both horizontal representations
and has regression coverage for the actual two-component schema. No engine or
capture changes were needed for this audit correction.

Prepared manifest SHA256 remains
`11ec3a4e36c4cf1a7a395ac269bab8ffad6653ae50009ad5faa3b436d6f5a0b3`.
Saved playable map SHA256 remains
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
No saved scene was promoted; no visual evidence was fabricated; no commit/push.

## Remaining work / native integration constraints

Next is bounded destination assembly and actual native import/export, preserving
full particle state and birth tags while rebuilding local persistent handles,
live counters and free-ID tables. It must run without blocking GPU readbacks.

Engine source inspection shows that `PrepareTicksForProxy` derives dispatch and
spawn counts from CPU upper bounds before native stage execution. Simply raising
that bound to the maximum suppresses new births; changing it after preparation
does not resize that frame's dispatch. `AllocateGPU` can recreate buffers without
preserving their contents and clears the count offset, so it must not be used to
blindly enlarge live imported state. Empty owners also need valid allocated
source state/counts before native simulation. Any production handoff must account
for these constraints, plus queued ticks, reset/generation and sequence lifetime.

Routing candidates do not solve those requirements. Once actual handoff passes,
continue regional affine/dense wet transport, continuous surface and foam,
raft/terrain/rock checks, reference comparison and measured performance. Then
complete the remaining rivers and the full original project queue.

All owned processes are terminal: engine tests 19822, native replay 1584. The
goal remains active; no external blocker.
