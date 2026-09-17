# Exact indexed crest edges installed — performance remains open

2026-09-17. The prior commit-only turn confirmed a clean tree but did not advance
the gameplay goal. This continuation implements and installs an exact-output
CPU optimization. It does not accept South Fork physics, appearance or release.

## Change and exactness

Refinement assembly now uses a direct lower-vertex index to find canonical
edges. Each chain has at most eight entries; higher-degree/nonmanifold fans use
the original hash map for overflow. There is no mesh-degree-dependent unbounded
linear scan. Both maps retain the original triangle traversal and insertion
order. No height, sampling tolerance, topology, normal, ownership, film depth,
wave detail, refresh frequency or visual setting is reduced.

The shoreline enables the qualified path by default. `-RaftSimLegacyCrestEdges`
retains the original assembly lookup as a same-build control. Other standalone
refinement callers retain their existing default. This does not change physical
ground, collision, hydraulic assets or the captured-ground rendering correction.

`RaftSimCrestIndexedEdgeAudit` compares 64 changed actual-game inputs after two
warm builds, alternating call order. Both sides use the current prepared range
bound and independent memo/topology histories. Timings include map construction
and the whole adaptive build. Ordered parents, triangles, original owners,
expanded coordinates and the actual production topology must all match.

| Capture | Compared vertices | Legacy build ms | Indexed build ms | Legacy assembly ms | Indexed assembly ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| pairs-v1 | 4,310,278 | 8.381602 | 7.674349 | 1.900418 | 1.188557 |
| pairs-v2 | 4,328,725 | 7.434027 | 6.874956 | 1.585124 | 1.008387 |

Both captures are exact and faster in **both** execution-order groups, not merely
their combined average. The second capture also enables the candidate in the
playable surface. These are local CPU comparisons, not ordinary FPS evidence.
All 128 pairs and 8,639,003 expanded vertices are retained, not cherry-picked.

Native input reports: `tmp/crest-indexed-edges-pairs-v{1,2}-20260917.json`, SHA256:

- v1 `bf59260d31727c3d77f9f3d14ef6c385cb3f59cf3a9905ea3e5ed47317d20e14`
- v2 `4c19779136583f388a8adc645ecb9b6888bdcfe1c3070cc88c79dbc32c29f3fb`

Reproduce summaries with `physics/scripts/audit_crest_indexed_edge_pair.py` and
fresh `--report` paths. It reuses the unchanged complete-pair, finite-value,
exactness and both-order gates; generated summaries remain ignored.

## Native tests, installation and actual appearance

Opt-in and default-enabled builds each pass all 24 shoreline/crest native tests,
zero failures, warnings, not-run or in-process tests. The extended regression
compares 24 moving profiles/crops/windings/detail windows against original and
serial assembly, plus 70,000 high-degree edges, updates, misses and self edges.
The 29 Python comparison/audit regressions pass, including rejection of
wrong-candidate/mixed-label input reports. No tolerances were changed.
The initial link attempt used the wrong working directory and failed LNK1181;
linking from Engine/Source succeeded. Initial pytest dependency lookup failed;
using the existing local dependency directories succeeded. The full compilation
retains the unrelated existing C4701 warning in DetailSourceFootprintTest.cpp.

Default-enabled native report:
`tmp/crest-indexed-edges-native-v2-20260917/index.json`, SHA256
`bb8173f9070888e506a07f53d6321818d0e836a3035d7b23e2f945342f58aebd`.
All five gameplay translation units were rebuilt for the changed refinement
type; the default-enable-only revision rebuilt its shoreline translation unit.
This is not a full packaged release build or all-project regression pass.

Installed gameplay DLL:
`67ef0aa789708c26f9bc55070bbfecf108395886b7216c8b68212512271763eb`.
Installed PDB:
`0079cb9bfc5eeeeeb537adac2389ebf387d43c094352652316c253b3135d82a8`.
Verified original DLL/PDB and installation manifest remain in
`tmp/indexed-edges-installed-backup-v1-20260917/`. Original DLL is
`e3b13f50993efda77683f9fb8ea9fff676b2a4325dadcfe01f80165ac376a8a6`.
The project Git object still matches HEAD; captured-ground asset and water-detail
DLL retain hashes `687d05c5...174b` and `650f80ca...b37` respectively.

Normal installed startup capture
`south-fork-indexed-edge-installed-startup-v1-20260917` completed 24 images,
exit 0/no timeout, cook resume 0. There are no module, optical or quality overrides.
Actual captured-ground component emits its 803,842-triangle fallback log at
frame 1. Images 000 and 012 were inspected: the corrected rock bank remains,
but broad sheet-like froth and unconvincing crew remain. Sparse still images
are not continuous motion or physical acceptance. No visual pass is claimed.

## Ordinary frame measurements: still FAIL 30 FPS gate

Actual South Fork station 8330, 1280x720 D3D12, 300 CSV frames, unchanged inclusive
sample rows 60–240 (181 samples). Target remains 30 FPS and p95 <=33.333333 ms.
Neither ordinary run enables A/B auditing, screenshot export or optical controls.

| Run | FPS | Mean frame ms | p95 ms | Gate |
| --- | ---: | ---: | ---: | --- |
| Current pre-change, stage logging enabled | 29.682060 | 33.690385 | 42.4310 | FAIL |
| Default-enabled candidate module | 25.687239 | 38.929836 | 46.1073 | FAIL |
| Normal installed, no module override | 31.116381 | 32.137414 | 38.8109 | FAIL |

Labels respectively: `south-fork-exact-ground-stages-v1-20260917`,
`south-fork-indexed-edge-default-perf-v1-20260917`,
`south-fork-indexed-edge-installed-perf-v1-20260917`. All wrappers exit 0,
no timeout, cook suspend/resume 0. Short trajectory/load variation means the
whole-frame difference cannot be attributed entirely to this optimization.
Do not discard the slower candidate run or infer sustained 30 FPS from the
installed average. The exact local A/B speedup is the isolated claim.

Installed CSV SHA256:
`f547b12dc245362b0ab5962339c5a64d468af24cf227850e719220555c7239a6`.
`tmp/south-fork-indexed-edge-installed-perf-v1-20260917-audit.json` SHA256:
`e92f5e9ddc371f7c5fcbfdaa7fb1ee26fdf03980fd96f64927210b81d9df6884`.
Installed means: game thread 32.000616 ms, GPU 10.659517 ms, SetMesh 9.068110 ms,
crest update 7.082190 ms, selection 2.961852 ms (78 positive rows), StepWater
5.299302 ms. These scopes overlap/nest and must not be summed.

## Hydraulic continuation and remaining work

Same cook PID 36872/start 2026-09-17T03:10:30.0811512Z is preserved. New 3000 and
3050 snapshots each pass state conservation AND all 86,720 exactly dry exterior
bank cells. At 3050: maximum depth 4.193624249 m, speed 5.928888120 m/s, volume
2936150.014164 m3, maximum step residual 1.647020742e-8 m3. Outflow
88.320213479 vs inflow 45.306954547 m3/s: NOT settled, accepted or promoted.
State/bank report SHA256 in `tmp/control-ablation-3050s-*-v1-20260917.json`:

- state `30ec4966b18cee796396770a0ae2d13fbcd84e738dd9507bc1fee753217e0ee5`
- banks `516e3cdce6458edd033c1af2d6d2e5f6f35aee9b7690b6a9315596dc69a7b209`

Next snapshot is 3100/local26000, requiring its completion marker and both audits.
Next gameplay work remains current-profile/target CPU cost, source-consistent
subcell support and coupled front/energy/bed physics, convincing moving crests
and froth, then sustained 30 FPS. Preserve the bank correction and exact detail.
Colorado, Pacuare, Futaleufu remain ordered after South Fork; Chilko/Zambezi and
all-scene reviews, crew, normalization, outstanding regressions and release are
still open. Troublemaker remains a rapid inside South Fork, not a menu scenario.
