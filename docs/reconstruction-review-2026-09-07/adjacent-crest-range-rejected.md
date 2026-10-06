# Adjacent crest range cache rejected for ordinary play

September 17, 2026. No playable improvement is claimed by this experiment.
The installed surface, water material, terrain and solver remain unchanged.

## Evidence and implementation

The preceding installed 300-frame capture, samples60..240, is CPU-bound:
mean game-thread32.05ms versus GPU10.98ms; inclusive water Tick19.72ms and
crest selection3.00ms. These nested times must not be added together.
A fresh installed `south-fork-current-stage-cost-v1-20260917` capture with
`-RaftSimWaterStageTimings` confirms selection sampling is a major rebuild cost:
for example frame194 has total crest13.2680ms, selection8.4757ms,
selection-sampling6.7395ms, assembly0.3869ms. Instrumented captures are not
ordinary FPS acceptance. Log SHA256:
`9cfd8886ed6ffb61ef386688a1d467cb68a852e58b6041bd84af4c43ff568013`.

The candidate caches only the last exact range-query box per selection batch.
Adjacent source triangles often share a box. Each cache belongs to one batch,
not a worker thread; levels join before resizing, and all caches expire when
the immutable-profile build returns. No approximate keys, rounded coordinates,
cross-profile reuse, changed selection tolerance, reduced geometry or slower
refresh is introduced. Invalid range values still follow the original fallback.
The new optional argument does not change refinement object layout.

The opt-in `-RaftSimAdjacentCrestRanges` remains diagnostic-only. The paired
`-RaftSimCrestAdjacentRangeAudit=...` compares complete adaptive builds and the
actual production topology: ordered parents, triangles, owners and expanded
coordinates. Allocation/destruction is inside timing. Two warm pairs precede
64 numbered pairs with alternating execution order; no failed/slower rows are
removed. The strict analyzer rejects missing/wrong schemas, incomplete histories,
wrong ordering, invalid timings/counts and implicit truthy exactness.

## Actual in-game results: do not enable

Both captures use the candidate in the actual South Fork surface, with the
existing material/terrain. They request1200 frames and complete exit0 without
timeouts. Exact cook suspend/resume succeeds for both. Candidate DLL SHA256:
`d088127be42cd9cb735c398da95aca743436f342fdb97e6387ca449bfd008686`.

| Capture | Exact expanded vertices | Reference mean ms | Candidate mean ms | Both orders faster |
| --- | ---: | ---: | ---: | --- |
| pairs-v1 | 4,317,314 | 7.220640 | 7.182545 | Yes, but only32/64 individual pairs |
| pairs-v2 | 4,319,406 | 7.235559 | 7.210639 | **No** |

In v2, reference-first worsens7.081922->7.244828ms; candidate-first improves
7.389197->7.176450ms. Thus the tiny mean improvement is not a reliable win.
Do not promote it or repeatedly tune this cache to chase the favorable mean.
The larger profile-evaluation/selection cost remains the next CPU target.

Actual reports `tmp/crest-adjacent-range-pairs-v{1,2}-20260917.json` SHA256:

- v1: `bbc7bd146c33ed64a039c139d6880eb9e2d96dd5f4379fb74000ffc6798e4e67`.
- v2: `2fb870a3181164b9e043c4a70bff8ce680e42260c39ceeaff159e6dd0df26af0`.

Summaries use the same stems plus`-audit.json`. Native v1 passes29 tests with
zero warnings/failures/unrun tests. New coverage includes one-ULP box changes,
48 moving/cropped/winding/changing-profile fixtures, serial/parallel contexts,
detail windows and absent/nonfinite bounds. A first test compilation failed
because `<cmath>` was missing; fixed before the passing build. Final native v2
also passes29 with zero warnings/failures/unrun tests,2.678734s; report
`tmp/crest-adjacent-range-native-v2-20260917/index.json`. Python timing/30FPS
regressions initially37 PASS; the expanded timing/carrier/source-provenance
suite passes74 in1.28s. These overlapping suites are not summed.

## Installed game control remains below target

Fresh ordinary no-override/no-instrumentation capture:
`south-fork-adjacent-range-installed-control-v1-20260917`, exit0,300 frames,
1280x720/D3D12, original inclusive samples60..240. Elapsed-frame25.907729FPS,
mean38.598520ms, p9544.7123ms: **FAIL** unchanged30FPS/p95<=33.333333ms.
This slower control is retained; there is no claim that the candidate caused
it or that a short capture establishes sustained performance.
CSV SHA256`eab11277d8d857dc95c32d4eb53ee45f9a59f838b6667b6ad9420e4f1a677f38`;
report`tmp/adjacent-range-installed-control-v1-20260917-audit.json`.

Installed gameplay DLL remains
`89b171f1a2031beb88b0e0a275a928b9acc1c9580b92616e7c4e64890302e410`.
Project DLL, water-detail DLL and water material hashes also match the preceding
review. No new visual/reference-video inspection or motion acceptance this turn.
The previous broad froth/mean-face evidence remains unresolved.

## Hydraulic continuation and remaining work

Same PID17516/start2026-09-17T12:52:03.0749210Z is directly verified live, not
restarted. Complete3950s/local7000 passes state/conservation AND all86,720
exactly dry artificial-bank cells on5,382,400 cells. Maximum depth3.981553829m,
speed5.361164592m/s, volume2,897,414.200574m3, maximum step residual
1.521822357e-8m3. Outflow91.263301156 versus inflow45.306954547m3/s:
**NOT settled, NOT promoted**. Next4000/local8000 needs a completed snapshot
and BOTH audits. h SHA256:
`da72f85aa075993e179c9efa8c56283d912559aa173b3849b5a0c240fd732609`.
Reports`tmp/control-ablation-3950s-{state,banks}-v1-20260917.json`.

Physical source-consistent breaking/froth and nonlinear pressure stability still
need work; this cost experiment does not solve them. Continue South Fork
terrain/boulders/collision/hydraulic consistency, shared rendered/contact water,
real-reference motion and30FPS qualification, then Colorado -> Pacuare ->
Futaleufu, Chilko/Zambezi/all-scene water, crew, normalization, regressions and
release. Troublemaker remains a rapid within South Fork, never a menu scenario.
