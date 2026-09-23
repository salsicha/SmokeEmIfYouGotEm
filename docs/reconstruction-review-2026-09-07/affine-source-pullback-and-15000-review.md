# Completed source replay and 15000-second hydraulic review

Reviewed 2026-09-23. Supporting physics work, **not a visible playable update**.
South Fork remains unfinished and ahead of Colorado, Pacuare and Futaleufu.

## Completed jobs, not live process IDs

The original affine momentum replay (old PID14076/session35230) has completed.
Its 79,009,055-byte report, `tmp/south-fork-affine-moving-pressure-v1-20260919.json`,
was written at 2026-09-19T02:50:36Z. All 11 supported cases pass the original
two-pole checks; original unsupported cases2/7 remain present among13 records.
SHA256: `aaa3a412823b7b2218d459b65ad158ceba57e24a73c2cac99021966b6b43d2aa`.
This is not a completed nonlinear force, open-boundary law or game validation.

The hydraulic12000→15000 s cook (old PID12672/session79088) is also terminal.
Its native `completed.json` says completed, final local60000 is complete, and
both independent final audits pass. No OS exit-code receipt was recovered;
native completion and audited arrays are the evidence. Neither old process ID
may be reused in the retained-handle profiling helper. No duplicate cook or
original momentum replay was started.

## Saved-state derivative qualification

`physics/scripts/audit_south_fork_affine_front_variation.py` adds qualification
of the primitive energy derivatives against the completed original-source
momentum solutions. It retains original source geometry, coverage, momentum,
time rates, pressure poles and prescribed exterior flux. Every protected input
and replay implementation hash is checked before evaluation and again at the
end; the original predictor must remain in that hash chain. Unsupported records
are retained verbatim. Reports refuse overwrite.

The checker reconstructs both original pole equations and their time equations,
physical momentum/rate, boundary shifts, independent positive local-jet energy,
and the complete energy/time work in physical and canonical coordinates.
Boundary-flux work stays explicit. Saved success flags are insufficient.
It reuses saved canonical and auxiliary velocities: no repeated momentum or
auxiliary state solve. Constructing the metric still solves its geometry and
boundary shifts, so this is not a solve-free or runtime-performance claim.

All **83 focused tests pass in38.84 s**, covering the new audit, primitive
derivatives, affine moving pressure, prescribed trace and storage regions.
The22 new audit tests include lossless serialized reuse with solving forbidden,
1e-400 corruptions, source/coverage/order rejection and unsupported-record
preservation. Earlier focused45-test run also passes in24.62 s.

Test receipt `tmp/affine-pullback-audit-combined-20260923.xml` SHA256:
`2360652b9ae2009e8071383b944f540d82ed441cd44011578a8b0821d2483213`.

One source qualification was launched, PID6480/session50573, start UTC
2026-09-23T15:18:43.5347928Z.
Case0 passed in137.84 s; case1 is running at this review. Expected report:
`tmp/south-fork-affine-front-variation-v1-20260923.json`.
**No completed all-source derivative report yet.** Preserve this process and
its protected imports. Check its identity/output before doing anything else;
do not repeat expensive source solves just because a tool wait expires.

## Final hydraulic state and changed downstream trend

The [state audit](cartesian-15000-state.json) covers all5,382,400 cells at
14999.999999922 s. Volume is2,192,277.468163 m3, maximum depth3.589152 m and
maximum speed5.041169 m/s. Maximum per-step conservation residual is
1.262257e-8 m3. The [bank audit](cartesian-15000-banks.json) finds all86,720
artificial-bank sample cells exactly dry. These are final-checkpoint audits;
this review does not claim every intermediate checkpoint was independently
audited.

The reach is **not settled**: instantaneous combined outlet115.020881 versus
inlet45.306955 m3/s. Total water loss since12000 s is198,796.912327 m3.
The [regional audit](cartesian-storage-regions-15000.json) retains all cells,
original route attribution, complete markers and source hashes. Regional sums
close to time-integrated exterior volume within9.1e-10 m3 for every comparison.
These are storage rates, not measured section discharges:

| Model-time interval | Station0–9 km | Station9–26 km | Station26 km–end | Domain |
|---|---:|---:|---:|---:|
|12000–14000 s|−0.00663|−65.48654|+1.51765|−63.97553 m3/s|
|14000–14500 s|−0.00591|−52.87073|−17.68505|−70.56169 m3/s|
|14500–15000 s|−0.00605|−47.18843|−23.93555|−71.13003 m3/s|

Unlike the earlier11500–11950 s interval, the downstream region now loses
storage too. In the final500 s, median common-wet stage falls8.03 cm at23–24 km,
5.68 cm at29–30 km and3.28 cm at31–32 km. Outlet-cell median stages remain near
the authored boundary stage; this does not independently validate that stage.
The changing spatial pattern is compatible with a distributed transient, but
does not establish its cause, validate inferred bathymetry or predict a reliable
remaining settling time. Do not promote the result or tune the outlet to force
instantaneous balance. No further cook was started in this bounded review.

Original ignored-tmp audit SHA256s:

- State: `223f9a437371d44c528de8a1d2dcd5fe24aa9fd46c9c5f0aef90ccbf9152f38a`.
- Banks: `de1e74e20cdffce8780776fea37ae50925c65f41e9f4a72965999df8cdd21cdd`.
- Regions: `f8f02d819f0594441ee6d7e14709d4eac7a4486dfdf993b0d3d932cfff5006c8`.

## Next and unchanged acceptance gates

Read the single source qualification result when terminal; do not mark its
pending cases passed. Continue independent normal-play improvements while it
runs. The previous profiling helper hard-codes the two now-terminal process
identities; replace its live-job prerequisites before using it for a new
engine cost measurement. Do not launch replacement background jobs just to
satisfy the helper. Before another hydraulic continuation, retain this spatial accounting
and audit any restart bit-for-bit; do not initialize a fresh, untracked state.

Legacy storage/face consistency remains unresolved; its tolerance was not
loosened. Source-exact cap interpretation still lacks sufficient evidence.
Nonlinear gameplay remains OFF. Maps, captured data, collision and installed
4950 s fields are unchanged. No new build, engine view, motion/collision or
surface acceptance is claimed. Last normal default runs remain24.953169 and
25.497627 FPS, p9548.0971 and47.2092 ms, failing30FPS/33.333333 ms. This audit
does not supersede playable-first delivery or close any river/release gate.
