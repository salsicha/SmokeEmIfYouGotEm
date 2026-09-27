# V12 crest height: amplitude versus spatial placement

September27. This is a focused diagnostic, not a visible improvement or water
acceptance. Current v12/450s playable fields and physics settings are unchanged.

## Evidence from the retained ordinary-camera approach

The actual ten-second height audit contains41 detector-eligible candidates
between hydraulic X=-5460 and-5400 m. These coordinates are hydraulic east/north,
not route station. Every candidate's raw/optical height correction agrees;
there are zero rise reversals and zero extra-height deficits caused by optical
filtering in this subset. Maximum candidate extra height is0.3608 m. Candidates
precede deduplication/persistence and are not41 separately rendered crests.

At the strong front near route8342.35 m, hydraulic XY=(-5428,3607), the log gives
upstream depth0.2507 m, Froude1.6657, resolved surface rise0.3593 m and additional
crest0.0470 m. Recomputing the current authored formula from rounded log inputs
gives blended target0.406359 m and additional0.047059 m; the0.20056 m depth cap
is not binding here. This explains the small extra-height number without proving
the resulting crest is spatially correct or physically realistic.

The [USACE manual's notation](https://www.publications.usace.army.mil/portals/76/publications/engineermanuals/em_1110-2-1601.pdf)
references undular height to initial depth. It does not justify blindly adding
the full theoretical height above a surface already raised by the resolved flow.
The blend, length, caps and static crest/toe/tail remain authored approximations,
not measured natural-rapid dimensions or an evolving recirculating roller.

Source log SHA256:
`2852627f04f7b025265e506ffed56b19ffb0da34fd8001da739bfb7a7d167920`.
Backward-compatible, hash-bound report:
`tmp/sf-v12-upstream-height-budget-v2-20260927.json`, SHA256
`21eb2ac340d00f8f273a77d2b5a15a48b16d45c4c09a1d15e5c1c7cad1127f9f`.
The earlier audit is preserved separately.

## Missing spatial evidence and scoped observer

The current crest is centered at the selected upstream sample, while resolved
rise uses a downstream-minus-upstream pair. Existing logs omit the downstream
coordinates and endpoint elevations. Therefore this evidence cannot determine
whether the subtraction and actual crest position account for the same rise;
do not label spatial misregistration proved, or change amplitude on that basis.

The existing one-shot `RaftSimBreakingHeightAudit` now includes both endpoint
coordinates, surface elevations and bed heights plus the upstream flow direction.
No sampling, candidate eligibility, site position, height, support, material,
time step or solver behavior changes. Normal launches without this observer do
not execute the added logging. The parser accepts complete old OR new records,
rejects partial/mixed/nonfinite/inconsistent-rise records, and hashes the exact
bytes it parsed. Physical depth is intentionally not required to include every
presentation-wave displacement: some adapter paths keep those quantities distinct.

Six focused parser regressions PASS, including legacy compatibility, independent
log rounding, invalid spatial endpoints and depth/presentation separation.
The retained v12 log remains explicitly `spatial_geometry_available=false`;
adding an observer cannot retroactively supply missing measurements.

Editor build46600 completed exit0 in59.07s, log
`tmp/crest-spatial-audit-editor-build-v1-20260927.log`. No new spatial capture
has run. Collect these fields alongside the NEXT justified normal-scene motion
review after hydraulic continuation99863 and its final audits finish; do not
repeat the unchanged v12 recording just to produce another audit. Then compare
actual paired geometry and rendered crest placement before a shape correction.
Dynamic breaking/holes and performance remain open regardless of this audit.
