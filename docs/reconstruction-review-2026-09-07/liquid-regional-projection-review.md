# Regional pressure phase and ownership — 2026-09-10

South Fork remains incomplete. This installs the regional pressure operator; it
does not promote independent wet tanks, declare photorealism, or change a saved map.

## Implemented

`RaftSimLiquidRegionalProjection.h` describes pressure ownership in the full
parent computational grid. Positive-scale Niagara Y is reflected before finding
the parent offset: `(firstX, parentNY - upperCanonicalY)`. The actual offsets in Y
are 98, 34 and 0. Eight regions therefore need the opposite local update phase.
The native wide (+/-2) stencil now updates the same global color everywhere.
The partial 110-cell X allocations keep both final parity lanes.

Imported pressure at shared face/corner halos is read-only during a regional
solve. Physical owners update their cells; the existing post-iteration GPU
exchange copies those current values to neighboring halos. True parent exterior
halos are not mistaken for shared interior cells. This is pressure ownership,
not an implementation of the remaining exterior boundary physics.

The compatible divergence, pressure and gradient programs use one explicit XYZ
centimetre metric from the region's parent. Installation rejects mismatched
allocated extents/origin/cell counts, saved or assigned systems, missing canonical
contact, and unsupported odd partition offsets. The legacy fixture path remains
unchanged; its rectangular-boundary guard is not bypassed. No region activates
automatically.

## Evidence

- Build succeeds. `engine-liquid-regional-projection-v1/index.json`: three engine
  tests pass, zero warnings/failures, 8.10 seconds. Includes actual compilation of
  three differently located regional GPU programs, pressure halo GPU regression,
  exhaustive even-X coloring, and every one of the parent's 1,905,120 physical
  cells visited once in two globally aligned phases.
- Final build 59888 succeeds after adding the allocation-extent mismatch guard.
  `engine-liquid-regional-projection-v2/index.json`: the same three engine tests
  pass, zero warnings/failures, 7.790 seconds, including rejection of a pressure
  metric that differs from the actual allocated grid. Final engine handle 94619
  and earlier build/probe handles are terminal; no editor process remains.
- `liquid-regional-projection-v1`: all twelve native zero-water regions execute
  the installed operator. 1,518 complete aligned groups, 1,160 pressure exchanges;
  all 5,960 shared column addresses match independently prepared geometry.
  `contact_audit.json` still matches all 1,587,600 non-border physical terrain
  classifications exactly. The 19.924-second capture wall time is not FPS.
- `liquid-regional-pressure-marker-v1`: initialize each native pressure grid with
  the exact nonzero value `1000 + region_id` after Compute Divergence. Capture
  every R32F voxel after the first actual native Solve Pressure color, BEFORE
  halo exchange. The zero-water boundary contains only solid/empty cells, so
  visited owned cells must clear; shared cells and the other color must retain
  their markers. The independent audit compares every one of 2,113,056 GPU values
  with zero tolerance: no mismatches. It uses prepared shared-owner maps and
  parent grid coordinates, not exported C++ expected values. 1,414 aligned groups,
  1,080 pressure exchanges; all addresses match. Its 19.487-second wall time is
  not gameplay performance.
- 215 Python liquid tests pass, including negative marker cases: all-zero data,
  opposite local phase, one corrupted shared cell, nonfinite and partial data.
  Scoped `git diff --check` passes.

The marker injection is opt-in (`-RaftSimRegionalPressureMarker`), requires the
regional projection/contact probe and is never used for real water. Readbacks
are queued in RDG before exchange and inspected only after completion. They do
not establish pressure convergence in moving liquid, conservation, or visual
acceptance. No new visual acceptance claim is made from an empty simulation.

## Next real integration work

1. Install explicit exterior forcing/outlet stage rules and shared fluid/solid
   boundary masks. A local native open boundary is not itself a shared boundary.
2. Exchange conservative P2G mass/momentum before normalization and transfer
   particle ownership without spawning or deleting water at region cuts.
3. Apply the shared boundary/velocity data in D/P/G at the correct native stages;
   verify wet pressure iterations against a connected reference problem.
4. Share live surface/foam histories, test continuous full-rapid flow and raft
   interaction, compare actual moving renders with footage, and measure gameplay
   performance. The prior isolated wet fixture is still glossy/lumpy and rejected.

Colorado, Pacuare, Futaleufu, other scene reviews, crew work, normalization and
final release/commit remain in the active full queue. No commit or push here.
The saved geographic map SHA256 is still
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
