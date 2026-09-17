# Exact physical crest sampling: installed speed qualification rejected

2026-09-17. The candidate remains diagnostic-only. Its temporary installation
was rolled back after ordinary installed A/B failed whole-frame repeatability.
This is not new water geometry, breaking physics or accepted froth. The target remains 30 FPS with frame
p95 <= 33.333333 ms. Do not turn an average-FPS pass into full acceptance.

## Change and correctness

The validated physical-only 8 m index can now evaluate the unchanged crest
formula at its call site, specialized for height-only or height-plus-foam
queries. This removes the cross-module general-evaluator call and legacy-path
work from adaptive sampling. Float conversions, arithmetic order, exponentials,
support cutoffs, site order, local/global caps and refinement tolerances remain
unchanged. Legacy, invalid and over-capacity inputs retain the original evaluator.
No profile interpolation, stale-height reuse, reduced geometry, reduced update
frequency or solver change is introduced. The helper is independently checked
against the existing general evaluator, not used as its own reference.

The candidate's native suite passes 30 tests with zero warnings/failures/unrun
tests (3.192476 s). The new test includes 233,275 bit-exact height/foam queries,
24 adaptive topologies, support/index boundaries, non-unit/rotated directions,
zero-height spilling, local/global caps and fallback cases.
Report `tmp/inline-physical-crest-native-v1-20260917/index.json`, SHA256
`4981293614513c15cd76201c9bad24f5040a53d8ef36edda239ec4c43ae0ae92`.
Nine frame-auditor tests and the existing PowerShell profile-identity checks
also pass. No acceptance gate was relaxed.

An actual 1,200-frame South Fork audit compares EVERY query through the
immutable adaptive profile, including parallel workers. All 615 retained
profile epochs total 125,497,187 queries with zero mismatches. The process exits
0 without timeout; exact cook suspension/resumption succeeds.
Log `unreal/Saved/Logs/south-fork-inline-physical-audit-v1-20260917.log`, SHA256
`806164e53711488a08cae9dadc906991aabf8baa03cfae7e9901532d9ac1b197`.
This instrumented run is not FPS evidence. Candidate DLL SHA256:
`f99a7bdefec19ceabbc9dca769cdf0ea63f22c80553754c9d8e46fc217e4667a`.

## Audit-free actual frame comparison

Same isolated binary, original South Fork map/materials, 1280x720/D3D12,
300 frames per capture, inclusive samples 60..240 (181 samples). Actual query
auditing is disabled. Only the candidate runs enable the specialized evaluator.
All process reports confirm clean exit, no timeout and successful cook resume.

| Run | FPS | Mean frame ms | p95 frame ms | Mean crest update ms |
| --- | ---: | ---: | ---: | ---: |
| reference-a v1 | 28.011581 | 35.699520 | 41.2501 | 7.768360 |
| candidate-a v1 | 30.851695 | 32.413130 | 39.9733 | 6.929306 |
| candidate-b v2 | 29.329415 | 34.095463 | 39.0080 | 7.284256 |
| reference-b v2 | 28.623384 | 34.936471 | 41.7953 | 7.631463 |

Both isolated execution orders improve mean frame time, p95 and crest-update
cost. That initially supported an installation trial, but the ordinary
installed comparison below OVERRODE it. Nested timing scopes must not be added
together. Neither candidate p95 meets 30 FPS.
Report `tmp/inline-physical-abba-v2-20260917-audit.json` retains all four CSV
hashes and metadata; SHA256
`af71ed36597d6c7c415d255f0dcb1f5c79d851daa4f09e27e76fe5a4e62a3290`.
Capture names begin `south-fork-inline-physical-`.

The original reverse pair is also retained. Candidate-b v1 reports 30.309353
FPS, mean 32.993116 ms, p95 40.7644 ms and crest 7.031051 ms. Reference-b v1 has
duplicate `ShadowCacheUsageMB` and `LightCount/UpdatedShadowMaps` CSV columns;
the unchanged strict parser rejects it. BOTH reverse-order runs were repeated
as v2, not just the reference. No malformed measurement is used for promotion.

## Actual installed delivery trial: reject and roll back

All five current gameplay-module translation units were rebuilt in isolation.
The build retains one existing C4701 test warning about `Current` in
`RaftSimDetailSourceFootprintTest.cpp:105`; no compiler error. The rebuilt
default-enabled module passes the same 30 native tests with zero test
warnings/failures/unrun tests (3.442394 s). Report
`tmp/inline-physical-crest-native-v2-20260917/index.json`, SHA256
`71187e862e1eaff81fd8e976886ad78c3c21bd84c222bfaab0a70086b06a6b9f`.

The trial DLL SHA256 is
`d522facb8131e80b11ec89e00c0a573d40ceb94598a20e6f44b2f75cd7d73d9e`.
It was temporarily installed with verified original DLL/PDB rollback copies.
An ordinary no-plugin/no-candidate-flag launch confirmed the specialization
active, but measured only 25.303554 FPS, mean 39.520141 ms and p95 44.883 ms.
This slower result is retained, not discarded as warmup or relabeled as a pass.
Report `tmp/inline-physical-installed-v1-20260917-audit.json`.

A complete no-plugin reference/default/default/reference comparison then used
the same installed binary and unchanged frame settings/indices. Only reference
runs passed `-RaftSimReferencePhysicalCrests`; default runs needed no option.

| Installed run | FPS | Mean frame ms | p95 frame ms | Mean crest update ms |
| --- | ---: | ---: | ---: | ---: |
| reference-a | 28.507590 | 35.078378 | 41.0565 | 7.892343 |
| default-a | 27.800739 | 35.970267 | 42.1015 | 7.642058 |
| default-b | 27.918171 | 35.818966 | 41.3688 | 7.665048 |
| reference-b | 27.575797 | 36.263684 | 41.1926 | 7.850962 |

The narrower crest scope improves in both pairs, but the first whole-frame
mean worsens and BOTH p95 comparisons worsen. All four fail 30 FPS. Therefore
do NOT promote the specialization based on the earlier isolated results.
Report `tmp/inline-installed-abba-v1-20260917-audit.json` retains all original
CSV hashes; SHA256
`2c15e8ea64c8387980535578a53095c55974b3292dd91b5b817fdae8d6e3e286`.
Capture names begin `south-fork-inline-installed-`.

The original installed DLL and PDB were restored byte-for-byte from
`tmp/inline-physical-crest-installed-backup-v1-20260917/`. Final installed DLL
SHA256 is `89b171f1a2031beb88b0e0a275a928b9acc1c9580b92616e7c4e64890302e410`;
PDB is `aa6518a9e38ca0aedafda6540263c6f9e752af93a3a1fb85651c974c01a9a189`.
Source defaults are also restored to OFF, including shipping builds. The
retained non-shipping diagnostic uses `-RaftSimInlinePhysicalCrests` or
`-RaftSimInlinePhysicalCrestAudit` only in `L_SouthForkAmerican_FullReach`.
The temporary default build's reference flag is historical, not the final API.

The final diagnostic-only source was rebuilt as v3 and revalidated: 30 native
PASS, zero warnings/failures/unrun tests, 2.974344 s. Report
`tmp/inline-physical-crest-native-v3-20260917/index.json`, SHA256
`0f61eca881aa179db72e98b75b36ec6d5422d9e39a2a7966c7cf6dc27e748b0d`.
This final candidate module is NOT installed. The production water-material
SHA256 remains `7e0f29aa41787954ef5d2156345a66c4f5d4d507f79985ae0f6a8311c6fb9038`.

## Visual evidence and outstanding regressions

The temporarily installed candidate completed an ordinary no-plugin startup
motion replay: 24 verified 1280x720 PNGs and one finalized 15.539-second MP4
with 256 source frames (the encoder may repeat frames). Two timestamps,
frames 012 and 022, were inspected using in-memory 960x540 previews after
the normal image viewer hit the Windows sandbox-helper error. They retain
broad smooth froth and an abrupt main face: NOT convincing-water acceptance.
The MP4 is retained; full-video decoding is not yet established by this record.
Process/capture evidence:
`unreal/Saved/RaftSimValidation/south-fork-inline-physical-installed-motion-v1-20260917-process.json`.
Movie `unreal/Saved/VideoCaptures/RaftSim_20260917-111125.mp4`, SHA256
`806407c002097afa71b9e86c41b88f36f79357e882d070ea2887ebb6f48ff260`.
These images belong to the temporary candidate installation, not a newly
accepted/current water surface. Production material and source data were not edited.

The broader selected Python entry/presentation suite reports 47 PASS / 5 FAIL
(52 tests). A read-only replay substitutes the unchanged HEAD actor text and
reproduces exactly the same failures: old route extent, terrain-probe source
spelling, catch-up constant, near-bank threshold and smoothing-loop spelling.
They remain unresolved source-contract failures, not waived acceptance gates.
Reports `tmp/inline-physical-playable-{regressions,baseline}-v1-20260917.xml`;
SHA256 respectively
`a2382b47984eaa8bb67670f2ed1c36de33f7eadc2fd00f92d081f88a2c19245c` and
`10c5aea662b74ca7db880f424173cb0b2af47eade486b4c17bb179863cdcef1f`.
The earlier 13 physical-water suite failures also remain open; that suite was
not rerun for this C++ calculation specialization.

## Hydraulic continuation and remaining scope

The same live cook (PID 17516, start UTC 2026-09-17T12:52:03.0749210Z) completed
4600s/local20000. State/conservation and all 86,720 artificial dry-bank checks
pass. Maximum depth 3.807764523 m, speed 5.517093065 m/s, volume
2,862,957.847253 m3, maximum step residual 1.521822357e-8 m3. Outflow
107.011833870 versus inflow 45.306954547 m3/s: NOT settled or promoted.
Reports `tmp/control-ablation-4600s-{state,banks}-v1-20260917.json`;
depth SHA256 `671951cfc3d95356755a2e652313909bc6bcc7ac5c7ae3a59f7d34aa687dea82`.
Completed 4650s/local21000 also passes BOTH audits, including all 86,720 dry
bank cells. Maximum depth 3.796897929 m, speed 5.519380609 m/s, volume
2,859,856.404217 m3; outflow 108.161861623 versus inflow 45.306954547 m3/s,
NOT settled. Maximum step residual remains 1.521822357e-8 m3.
Reports `tmp/control-ablation-4650s-{state,banks}-v1-20260917.json`;
depth SHA256 `fa20f907a0a766096aa1260893a5acc90a8f60c37e22ae45b59a5dbf33cf36ef`.
Next 4700s/local22000 needs its completion marker and BOTH audits. No restart.
The final direct process check confirms the same PID/start still live at
4681.5s/local21630; a progress row alone is not used to assert liveness.

Terrain/collision/hydraulic source consistency, the varying nonlinear inlet,
bed-junction and dispersive coupling, convincing breaking/froth and reference
motion remain unresolved. Captured exposed geometry remains distinct from
inferred underwater terrain. South Fork -> Colorado -> Pacuare -> Futaleufu,
Chilko/Zambezi/all-scene water, crew, normalization, regressions and release
remain open. Troublemaker is a rapid within South Fork, never a menu scenario.
Do not repeat tile-size or standalone inlining sweeps as a substitute for the
missing physical/visual integration. The installed trial demonstrates why
isolated-module timing alone cannot qualify the playable result.
