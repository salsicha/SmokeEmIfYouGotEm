# Crest-target expansion: small component gain, not promoted

September27,2026 UTC. Supporting performance experiment only. No new playable
geometry, water, physics or FPS improvement is claimed; South Fork remains first
unfinished. The packaged game was not replaced.

## Distinct hypothesis

The target-update path traversed ordered midpoint parents twice to expand
coarse crest height and shoreline weight, then traversed them again to compute
the fine-profile correction. A temporary candidate combined those independent
scalar expansions and the correction into one ordered traversal. Each field
kept exactly the original parent addition, float multiplication and subtraction;
source/boundary targets remained zero. There was no reduced sampling, stale
profile reuse, changed topology, altered blend history or solver override.

This differs from the previously rejected per-refresh exponential preparation:
it operates on the crest target arrays, not the base-water vertex evaluation.

## Verification and live measurement

Editor build succeeded in158.75s. Two native regressions passed without warnings
or errors: the candidate compared337,216 nodes across40 changing, empty,
root-only, all-boundary and dependent-parent cases byte-for-byte, including
signed zero; the existing target-cache fixture compared11,225 rendered vertices
over16 changing frames. The latter exercised the unchanged authoritative path.

The guarded editor-hosted FullReach run used station11,520m, D3D12,1280x720,
ephemeral profile and a700-frame bound. It alternated execution order on the
same current input, preserving original outputs as the gameplay authority.
All64 pairs matched expanded coarse height, expanded shoreline weight and
target corrections byte-for-byte. Candidate scratch capacity was retained,
and allocations/preparation were inside each measured call; comparisons were
outside timing. All samples, including the initial allocation, are retained.

| First path | Pairs | Original target update ms | Fused target update ms |
| --- | ---: | ---: | ---: |
| Original | 32 | 0.306093483 | 0.256762607 |
| Fused | 32 | 0.277112937 | 0.248453114 |

This is a real narrow component saving of about0.029..0.049ms per update, **not
a whole-frame measurement**. The original component itself averages less than
0.31ms in these groups. It is not the large surface/selection bottleneck behind
the earlier packaged busy-rapid p9585.2731ms failure. No ABBA whole-frame trial,
normal-menu launch, visual-motion acceptance or packaged qualification was
performed for this candidate. Instrumented CSV timings are not FPS evidence.

Runtime exited0 with no Error/Fatal lines,699 paired detail commits,2 holds,
236 flow preparations,33.134s elapsed and zero PDE backlog. No competing engine,
build or cook was running when either test launched.

## Decision and evidence

Deprioritized, not rejected as numerically wrong or slower. The small measured
component gain does not justify treating this as a delivered performance fix.
Candidate code, its two switches and temporary native fixture were removed;
the original target block has no remaining source diff. Restoration build
succeeded in34.45s, recorded in
`tmp/crest-target-expansion-restored-build-20260927.log`.
Do not repeat this unchanged experiment or spend another four whole-frame
captures on it while the substantially larger bottlenecks remain open.

Existing local evidence (not duplicated into additional media/cooked files):

- `tmp/crest-target-expansion-pairs-20260927.log`, SHA256
  `d73661cdae9947b01d2f8441a571121b05e96052a6a18d809760e8a5c62549a7`.
- `tmp/crest-target-expansion-native-20260927/index.json`, SHA256
  `1564eed2a862d2c9d38d49ea3b8571f9fd2528e8678fded2ffd0a3ab75eab5df`.
- `tmp/crest-target-expansion-build-20260927.log` and the original guarded
  runner `tmp/run-crest-target-expansion-20260927.ps1` (historical; candidate
  is removed, so do not rerun it against the restored binary).

Next work should address a measured multi-millisecond surface/selection stage
or unresolved reconstructed hydraulics/geometry, not another sub-millisecond
target-loop variant. Captured source, riverbed, collision, cooked fields and
default solver settings were untouched.
