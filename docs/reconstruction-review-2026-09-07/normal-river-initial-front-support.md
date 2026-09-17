# Original water support on conditional lateral fronts

2026-09-17. This closes the initial-water ownership gap left by the complete
terrain-source search. It is not a coupled finite-time solution or a playable
breaking/froth improvement. No installed binary, material or geometry changed.

## Implemented prerequisite

`subcell_front_initial_support.py` partitions both traces of each conditional
front at exact original-source boundaries and pool-stage/bed crossings.
Positive-depth, dry, whole zero-depth and unknown traces remain distinct.
Missing water state is never interpreted as dry. Stages are added to their
exact source datums before comparison, preserving sub-float wet intervals.
The guarded conditional-flux entry rejects wet or unknown initial support;
passing this necessary condition does not qualify evolving support, donor
depletion, multi-stream interactions, pressure work or a time integrator.

The original-source loader can now recover a requested rectangular region
inside the same recorded 16x16 atlas patch. Its existing 4x4 default and source
registration are unchanged. The actual audit reconstructs all 256 cells and
258 wet pools, then independently checks every original block fragment and
pool stage against the expanded context. No water state outside that recorded
patch is invented. Original block-only and whole-terrain controls remain.

## Actual South Fork result

All eleven outward conditional rays have known initially dry support on both
traces. The previously unresolved ray from block donor `[8,600014]` toward
`[8,198093]` belongs to original patch cell **171**, triangle **198093**, on
both sides. It is outside the small 4x4 audit block, not outside the source data.

This distinction matters: cell 171 contains **1.1970022780710805e-5 m3** of
original water, but that water belongs to triangle **598574**, not the ray's
triangle 198093. A positive cell-average depth would incorrectly classify the
ray as wet. Original source membership and exact wet support resolve it without
moving the ray, resampling the bed or extrapolating water.

The positive sub-float stream is retained. Two receding/fan records remain
unsupported. All 337 preceding front-record fields are exactly preserved;
all 616 current source/implementation hashes were independently verified.
Captured exposed-rock and inferred-flank authority remain separate; this is
not measured underwater bathymetry or extra survey precision.

Actual evidence: `tmp/south-fork-front-initial-support-v2-20260917.json`, SHA256
`98ef69d439885b3cd60783d4fe6cd3af7e890cc265fe7acdbbbcf28258d85e4b`.
The v1 block-only report remains as the unknown-state control.

Focused tests: **59 PASS**, no skips. This includes new exact shoreline,
positive sub-float, datum translation, separate trace pools, whole zero-depth,
invalid/unknown-state and guarded common-flux cases, plus existing ownership,
registered-source and wet-support tests. No tolerance changes.
JUnit: `tmp/front-initial-support-focused-v2-20260917.xml`, SHA256
`347663bd0c90ab2ebf378ba9d2914bda8458651f1553ea94961d35549387b87e`.

The same broader physical-water suite plus the new cases: **699 PASS / 13 FAIL**,
712 tests, zero errors/skips, one existing warning, 151.10 seconds. Failure
identities match the previous run exactly: four legacy constant-velocity energy,
eight nonlinear rational energy, and one original storage/face representation
gate. These remain failures, not exemptions. JUnit
`tmp/front-initial-support-full-suite-v1-20260917.xml`, SHA256
`22f6f24586b5bf537f46b13373ad1010b5f6c3258f509e571c5f28a49e605dcd`.

## Hydraulic continuation and remaining work

The same cook PID 17516 (start UTC 2026-09-17T12:52:03.0749210Z) was directly
verified live, not restarted. At 4400 seconds/local 16000, state/conservation
and all 86,720 artificial-bank dry checks pass on 5,382,400 cells. Maximum
depth 3.855999403 m, speed 5.502563681 m/s; maximum step conservation residual
1.521822357e-8 m3. Outflow 101.633454253 vs inflow 45.306954547 m3/s: **not
settled or promoted**. Reports `tmp/control-ablation-4400s-{state,banks}-v1-20260917.json`.
Depth-array SHA256: `aba55fe0803284ae7f4b27fccc72c9b0b10aee018f434c67fa76d94bf843e1a3`.

The subsequent 4450s/local17000 snapshot also passes BOTH audits, including all
86,720 dry bank cells. Maximum depth 3.843376254 m, speed 5.505339289 m/s,
volume 2,871,856.134494 m3, unchanged maximum step residual. Outflow
103.497668706 vs inflow 45.306954547 m3/s: still not settled. Reports
`tmp/control-ablation-4450s-{state,banks}-v1-20260917.json`, h SHA256
`d57abb76c4bc813fa3c96f844ab7e52c59f4add85210118e4a0a31f1bd6fa1da`.
Next 4500s/local18000 requires its completion marker and both audits.

Next couple the source-owned common rates to evolving donor/receiver domains,
mass, physical momentum, bed/dispersive energy and front branch transitions.
Initial dry support does not remain dry automatically as those domains evolve.
No rendered-motion or new FPS claim: convincing breaking/froth and 30 FPS are
still unaccepted. South Fork remains first, then Colorado, Pacuare, Futaleufu,
Chilko/Zambezi/all-scene reviews, crew, normalization, regressions and release.
Troublemaker remains a rapid within South Fork, not a menu scenario.
