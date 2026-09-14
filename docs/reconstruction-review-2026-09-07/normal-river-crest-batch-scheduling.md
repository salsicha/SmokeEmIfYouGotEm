# Crest-selection batch scheduling — September 14, 2026

IN PROGRESS. Ordinary gameplay keeps the original128-triangle batch size.
Build78752 TERMINAL exit0,290.53s. Native48264 TERMINAL exit0:13tests pass,
1.676099s, including85,110 exact expanded vertex comparisons in the new
18-frame regrouping test. Parser/budget suite20tests PASS0.74s.
First actual-game19742 TERMINAL exit0. Full120–250 audit correctly rejected
missing frame248: selection reused unchanged geometry, which the first audit
did not log. No full report was written or fabricated. The explicitly bounded
120–247 prefix showed no convincing winner:128 mean17.1373ms;32 17.9761ms;
64 17.0798ms with worse p95;256 17.3291ms;512 19.6810ms. This prefix is diagnostic
only, not a replacement for the rejected requested interval.

Added an explicit `CrestBatchAudit unchanged` record for actual geometry reuse.
The parser still requires EVERY frame to contain complete builds or explicit
unchanged records; missing records are not silently skipped, and a no-op-only
interval cannot produce timing evidence. Eight parser tests PASS0.20s.
Correction build39484 TERMINAL exit0,19.08s; full fresh repeat31155 TERMINAL exit0.

## Complete comparison: keep the original128 default

`tmp/south-fork-crest-batch-paired-v2-20260914.json` accounts for ALL131frames
120–250:131actual build groups (two at247) plus explicit unchanged frame248.
All five variants retain identical topology/ownership and8,803,547 expanded XY
positions per variant. Log SHA
`d79f71b9f93688d755abe851120c1f2a27564e50fa41da61b83dabf3e6f01898`.

| Batch triangles | Mean build ms | p95 ms | Mean memo MB (decimal) |
| --- | ---: | ---: | ---: |
| 128, original | 17.3138 | 26.7277 | 52.0 |
| 32 | 17.6735 | 28.0808 | 125.1 |
| 64 | 16.8686 | 26.1796 | 81.9 |
| 256 | 17.2665 | 25.6215 | 29.7 |
| 512 | 19.6572 | 28.4080 | 15.6 |

The64 mean benefit0.4452ms changes sign across call positions (−1.5575 to
+2.1978ms), uses substantially more memo memory and was only0.0574ms in the
earlier complete prefix.256 gives only0.0473ms mean benefit, also order-sensitive.
512 is slower in every call-position mean. No reliable latency win established;
ordinary gameplay retains128. This is a rejected scheduling optimization, not
a delivered frame-rate improvement or changed visual result.

Fresh final CSV audit succeeds with300samples and complete footer. Its4.9104FPS
includes FIVE additional reconstructions per changed-profile frame and must NOT
replace the ordinary-game baseline or be presented as a new performance regression.
Report `tmp/south-fork-crest-batch-v2-frame-audit-20260914.json`.
The previous goal turn completed profiling and rejected the history hash change
after two exact-output but weak/order-dependent timing comparisons.

## Evidence and bounded change

The complete normal shared-load profile measured crest selection at14.71ms;
the separate detailed run measured17.29ms including input work,12.09ms in the
selection substage. These are not isolated timings or30FPS acceptance. Existing
code uses128-triangle batches with exclusive per-batch profile memo tables.
The earlier shared-corner optimization was rejected; it stays disabled.

`FRaftSimSurfaceRefinement::ParallelBatchSize` exposes the scheduling size,
default128. No sample location, refinement level, half-centimeter selection
tolerance, profile arithmetic, topology assembly order or4096-entry memo cap
changes. Regrouped tables still get the current build's height epoch.

Opt-in `-RaftSimCrestBatchAudit` compares128/32/64/256/512 on every actual
profile rebuild during frames100–250. Each variant has independent retained
state; first call position rotates across all five variants. All ordered
midpoint parents, triangles, cell owners and expanded XY must compare exactly.
The diagnostic never supplies geometry to gameplay. It intentionally adds work;
its frame rate cannot be claimed as ordinary-game FPS.

The analysis interval120–250 excludes initial cold calls. The new parser retains
all five-variant groups, including repeated builds in one frame, requires every
requested frame and rejects incomplete/mismatched groups or any logged mismatch.
Six parser tests PASS0.22s. Timings include nested selection; do not sum them.
Memo allocation is not total process memory or memory-budget qualification.

New native `RaftSim.M4.CrestBatchScheduling` compares five regrouped schedules
against fresh serial selection across18 changing profiles, coordinate drift,
translation, winding changes, detail windows and disabled/re-enabled retention.
It passes in the fresh native report under
`unreal/Saved/RaftSimValidation/crest-batch-native-v1-20260914/index.json`.

## Physics remains independent

Original59896/95666/97152/83142 and candidate41566 were directly polled live.
No original process, source, pressure gate or frozen dependency was changed.
Main last0.622926049s/speed31.703605m/s; candidate last0.308333347s/speed7.224340m/s.
Neither proves the full9.066667s and both moves. Cook8328.5s; both complete8300
audits pass but remain unsettled. Next complete8400 needs both state/bank audits.

Observer second speed-doubling trial127 is independently audited in
`tmp/south-fork-observed-second-doubling-kinetic-v1-20260914.json`.
At trial-clock0.374183780s, fastest cell[100,20] has0.428948mm depth and28.330339m/s
speed, but kinetic rate−13.771237 and pressure work only+0.00031248 (density
omitted). All four fastest cells again have negative local kinetic rate.
This is not total mechanical-energy/boundary balance or stability acceptance.

Final direct poll confirms all5original/research handles LIVE. Main59896 last
0.652288684s/speed29.974111m/s; candidate41566 last0.408333351s/speed7.048642m/s.
Cook83142 now8377s; no complete8400 snapshot yet. All417 original and422
candidate guarded script hashes rechecked unchanged. Final parser/budget suite
22tests PASS0.66s. The broader candidate physical controls have THREE failures
documented in `normal-river-difference-scalar-controls.md`; no promotion.

Full terrain/hydraulics, rapid shape, physically breaking waves/froth/contact,
30FPS, crew, later rivers, release and final commit remain open. No new reference
footage access or physical solver promotion is claimed.
