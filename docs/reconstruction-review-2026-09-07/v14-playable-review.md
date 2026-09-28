# v14 packaged South Fork review — September28 UTC

The normal plunge-height correction is packaged in executable SHA256
`a10b03e6821373e16c22caaddd97def834c012639b234f4cf101a89f958cba6b`.
All11 frozen build inputs remain unchanged. The staged2,405-file v8 payload
closure passes without external-source fallback. Fields remain450s; the completed
1350s continuation is not settled or installed. See
[hydraulic completion](envelope900-to1350.md) and
[shape correction and build provenance](native-rise-plunge-relief.md).

## Completed isolated launch and timing checks

Validation session85971/wrapper11644 is terminal exit0. It waited for the sole
hydraulic owner and all final audits to finish, then ran three sequential
1200-frame captures on the same cooked standalone executable,1280x720 D3D12.
No quality, crest, solver or candidate console override. Normal launch exercised
Boot and the actual menu; rapid probes start within the same FullReach map.
All three exit0 with zero logged runtime errors. Their timing outcomes differ:

| Start | Mean ms | p95 ms | Maximum ms | Frames >100ms | Current timing gate |
| --- | ---: | ---: | ---: | ---: | --- |
| Normal Boot/menu | 40.0100 | 48.7699 | 69.8662 | 0 | PASS |
| Troublemaker approach8310 | 45.6256 | 63.6890 | 131.5464 | 5 | FAIL |
| Rapid11520 | 45.9799 | 52.9986 | 107.2641 | 1 | FAIL |

Each audit retains rows30..1169 inclusive. Gates remain20FPS, p95<=50ms and
no individual frame>100ms. No failed row is removed. Passing calm-start timing
does not establish rapid, sustained, full-river or release acceptance; mixed
outcomes do not establish a causal speedup from the plunge correction.

Normal-menu requested/committed backlog peaks0.016657s and ends0.014088s.
Rapid8310 starts0.8997s behind, peaks1.3446s and ends0.002533s; rapid11520 starts
0.6338s behind and ends0.003355s. All report zero failed-step flags. Catching up
by the end does not erase startup/interval lag or establish full real-time capacity.
No fixed tick, elapsed time or work cap was changed.

Frame receipts: `unreal/Saved/RaftSimValidation/sf-v14-<start>-20260928-frame-audit.json`.
Independent scope/clock receipts: `tmp/sf-v14-<start>-20260928-scopes-and-clock.json`.
Source CSV SHA256, with start names `normal-menu`, `rapid8310`, `rapid11520`:

- normal-menu: `cb47d5b1643980c528aa4a91ee46c7e06279900557e805eb6c7806539769a5ba`.
- rapid8310: `bf9014b680c2c92db84b33d700e963043f490440decaba4188f37dc51390845b`.
- rapid11520: `f3359ad853d41a77ff2ac2c6bf58775ed73c2a89a6f61b6f2619a44abbba05a5`.

## Retained-frame cadence comparison

The existing tested v2 analyzer was applied to these same completed CSVs, not
another engine run. Normal-menu has1140 counted crest calls and zero profile
changes. Rapid8310 has1144 calls/596 profile changes; rapid11520 has1141/576.
Multiple-call rows remain unresolved, not assigned an invented per-call category.
Rapid profile changes are legitimate current inputs; do not reuse a stale crest
or lower detail to make timing pass.

Normal-menu has only2 geometry-changing rows with measured Refresh work, versus
49 single-call joint rows at8310 and12 at11520. Their mean inclusive surface Tick
costs are38.087,49.706 and44.800ms respectively. Additional multiple-call refresh
rows occur4 times at8310 and once at11520, with mean Tick95.984 and82.355ms.
Even the no-refresh geometry rows at11520 average18.656ms in crest Update.
This is a workload split, not proof that one scheduling change would fix FPS.
Never sum parent/child scopes or confuse same-row scopes with elapsed FrameTime;
the independent auditor retains the verified one-row elapsed-time association.

Cadence reports: `tmp/sf-v14-<start>-crest-cadence-v2-20260928.json`.
Next performance work must address real changing-profile/refresh and publication
costs while retaining geometry/contact/history correctness and all failed gates.

## Completed packaged approach and sampled visual review

Session2149/wrapper32388 and packaged game3540 are terminal exit0. Receipt
`tmp/sf-v14-spatial-approach-20260928-process-v2.json` binds the same executable,
records the normal plunge default as verified and reports no runtime error.
All80 requested sample indices are present from station8313.254m at world2.413s
to8487.281m at81.019s:174.027m of passive travel, no paddle/camera/quality/solver
override. This is the actual playable FullReach, not a replacement review map.

Video `tmp/south-fork-playable-v14-20260928/Windows/SmokeEmIfYouGotEm/Saved/VideoCaptures/RaftSim_20260927-191536.mp4`,
SHA256 `3a1b1632e2bc5a8ff24e4d418d6d16cd5888e977f0f5adf0e7a4b50ab96676b6`.
All2,481 frames decode through82.667s at1280x720, with51 exact adjacent repeats.
Neither encoded frame rate nor duplicate count is game FPS. Decoded receipt and
selected views are under `tmp/sf-v14-spatial-decoded-v1-20260928/`.

Actually inspected6/11/20/40/60/80s. The raft passes exposed right-bank rock and
continues into quieter downstream water; those sampled views retain one visible
carrier. Near the rapid, broad white sheets/flat foam and detached-looking spray
remain. No convincing overturning/returning roller is established. Sparse view
inspection and complete decoding do not establish continuous shoreline stability,
all-frame motion, collision correctness or full-river traversal. Crew hands and
fit are not accepted by these passive views. The thresholded ground-contact report
is absent; that is not proof of zero collisions/penetration.

The packaged selected-site profile confirms `legacy_plunge_relief_requested=false`
and passes the strict datum-v2 parser for14 sites. At(-5428,3607), along1.75m and
across0, native surface8.096512m and submitted macro8.064976m preserve the corrected
rise; presented detail adds0.003985m. This is consistent with the prior rebuilt
default, not a same-clock A/B or a new measured rapid dimension. Profile SHA256:
`3d4fbfd6a0c2c615458fab9c04bdaec4291d8aed4babce2d92da101be17f6c4f`.
Actual adaptive crest topology reports1,660,824 samples, maximum target error
0.810730cm and zero source-anchor displacement. Its scope excludes macro lag,
other relief and GPU perturbation; the coarse-only8.57cm comparison is not the
actual adaptive submitted-mesh error. Neither is full rendered/contact acceptance.

The correction has therefore reached the rebuilt, normally launched game and
its actual approach capture. Do not rerun these unchanged owners looking for
a lucky pass. Continue dynamic breaking/roller work and measured rapid-cost
reduction; do not enable failed nonlinear/mean-strain experiments or fit the
inferred bed to the still-draining1350s field.

South Fork remains unfinished. Breaking/roller realism, ground collision,
shoreline/surface continuity, rapid performance and settling remain open.
Colorado, Pacuare, Futaleufu and the rest of the full objective remain queued.
