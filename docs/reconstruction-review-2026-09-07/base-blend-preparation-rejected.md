# Per-refresh blend-factor preparation: rejected

September 27, 2026 UTC. Exact live component results, but no repeatable
whole-frame gain. Candidate removed; packaged gameplay remains unchanged.
Do not rerun this unchanged hypothesis to obtain a favorable timing result.

## Distinct hypothesis

The base-water vertex loop repeatedly evaluates two exponential response
factors from the same refresh interval: flow-history response at 4/s and
shallow-shore history at 0.8/s. The candidate calculated those same float
expressions once per refresh, inside the measured evaluation call. It retained
the original velocity-jump reset, shore-history reset, interpolation order,
all vertex work and statistics, geometry, physics and update cadence. It did
not reuse an alpha from an earlier refresh. Both paths remained serial.

Temporary switches were `RaftSimPreparedBaseBlend` (candidate, default off)
and `RaftSimBaseBlendAudit` (paired comparison). No solver override or quality
change was used. Editor build succeeded in 45.84 s.

## Actual identical-input comparison

Editor-hosted normal FullReach map, review station 11,520 m, D3D12, 1280x720,
ephemeral profile, 350-frame bound. Each pair restores the same complete
pre-state and compares all mutated vertex/normal/color arrays, flow and shore
histories, Froude/foam arrays, ordered station sums and global statistics.
Copies, restores and comparisons are outside timing; factor preparation is
inside. Original output remains authoritative. All **37 pairs** preserve exact
state across 50,625 vertices per pair; engine exit 0, no runtime errors.

| First path | Pairs | Original base evaluation ms | Prepared evaluation ms |
| --- | ---: | ---: | ---: |
| Original | 19 | 3.416405 | 3.330858 |
| Prepared | 18 | 3.572028 | 3.424194 |

Raw log: `tmp/base-blend-rapid-pairs-20260927.log`, SHA256
`7ca97465a90a7879f82d8c51b0789842a1752284ff13d431de0afdcae906287e`.
This narrow component improvement justified the separate whole-frame check,
not default promotion or a rendered-wave/collision acceptance claim.

## Whole-frame ABBA decision

Same editor binary, map, station and settings; no paired audit; 1,200 frames
each. All 1,140 rows 30..1169 retained. Actual log confirms nonlegacy frame
timing, analyzed with scope offset 1. Each launch checks for active engine,
build or cook processes; all four exit 0 without runtime errors and retain
healthy detail-presentation shutdown markers.

| Execution order | Mean frame ms | p95 ms | Maximum ms |
| --- | ---: | ---: | ---: |
| Original A | 43.164360 | 49.9339 | 94.3221 |
| Prepared A | 43.060580 | 49.5448 | 86.6475 |
| Prepared B | 44.012596 | 50.2853 | 96.3691 |
| Original B | 43.576427 | 49.6353 | 88.3683 |

The candidate is worse in both mean and p95 when run first in the second
pair; it also misses the 50 ms p95 goal there. **Promotion rejected.** The
component gain is not a repeatable gameplay gain. No frames exceeded 100 ms.
The two narrow editor control passes do not supersede the earlier packaged
rapid failure: different binary/host runs are not a matched before/after.

Reports/logs: `tmp/base-blend-{control-a,candidate-a,candidate-b,control-b}-20260927.{json,log}`.
CSV files with the same prefixes are in `unreal/Saved/Profiling/CSV/`.
CSV SHA256 identities in execution order:

```text
82e6df6079d6d44315bf50eaff64240ec1611f1b089748bb96e5431367426330
4c52e5d3eb3521a7060be01db0986125ab7508500d46053db2efd68ae581675f
26e48f1ceb05fba3c41f03568ec3f6bbdec7faf368ac7189ae511b38030eae09
7c412f1df365d5670091d6d4cb4158e8fa9fe13a7281a4beaca5ab9d34ffadaf
```

The runner initially stopped after successful Original A execution because it
requested the packaged-only duplicate-counter exception on an editor CSV
without that duplicate. The strict parser correctly refused. That same saved
CSV was analyzed without the exception; the game was not repeated, no samples
were discarded and the remaining three runs continued in their original order.

## Restoration and remaining work

The opt-in branches and audit changes were removed from
`RaftSimWaterSurfaceActor.cpp`, restoring its pre-experiment source exactly.
No scene, captured evidence, cooked field or installed packaged executable
was modified. Restored-source diff is empty (Git exit 0); restoration editor
build is terminal **SUCCESS**, 38.60 s, logged at
`tmp/base-blend-restoration-build-20260927.log`. Installed packaged executable
still has SHA256
`12d71f2830633d51d9b8851e9b4524b58fd74be33176d331092e6fd76433e523`.
No candidate-specific native fixture or new visual acceptance is claimed.
South Fork remains first and unfinished. Future performance work needs a
different hypothesis; physical rapid geometry, shoreline and collision gates
remain open independently of these timing results.
