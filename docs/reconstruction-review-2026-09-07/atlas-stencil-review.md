# Query-local atlas address reuse

September 18, 2026. The target remains 30 FPS with p95 frame time at most
33.333333 ms. This work changes address lookup, not water appearance or physics.

## Implementation and scope

The immutable Cartesian presentation atlas previously repeated its tile lookup
for the four interpolation corners and the central-difference normal stencil.
The candidate retains the center's packed index and local tile coordinates for
ONE query. Neighbors within that same tile use the corresponding array offset;
cross-tile neighbors use the original lookup. Missing tiles, physical ends,
negative global coordinates, source datums, wet/dry reconstruction, weights and
the order of all floating-point interpolation operations remain unchanged.
No sample or hydraulic state is cached across queries, frames or windows.

The original sampler remains a separate compile-time specialization. The live
solver sampler and all raft-physics authority are unchanged. Runtime selection
is confined to the surface actor's presentation-baseline queries; other callers
retain their original default. No terrain, source data, map or menu is changed.

The actual-game audit runs 64 alternating pairs of the complete parallel source
sampling AND authority-handover passes on one frozen current state. It checks
every returned sample field and all wet, availability, probe-request, feather
and presentation-height arrays exactly, then restores the actual production
outputs. This is same-state evidence, NOT a multi-frame trajectory comparison.
Independent captures and a separate ordinary capture are required. No slow pair
or startup row is removed, and neither the 30 FPS nor physical gates are relaxed.

## Verification

The initial build fails on a test-only unsupported Unreal NaN constant. Replacing
it with `std::numeric_limits<double>::quiet_NaN()` corrects the test compilation;
the original failed log remains `tmp/atlas-stencil-editor-build-v1-20260918.log`.
The corrected build succeeds:
`tmp/atlas-stencil-editor-build-v2-20260918.log`.

All **11 native D3D12 tests pass**, zero warnings/failures/not-run/in-process:
`tmp/atlas-stencil-native-v1-20260918/index.json`. Coverage includes 35,643 exact
full-sampler comparisons across analytic wet, dry-island and missing-tile inputs,
concurrent calls, non-square tiles, negative and large tile keys, unavailable
neighbors, all tile boundaries and endpoints, plus the existing shared-atlas,
presentation authority, contact coupling, exact overlap, dry-rock, fine-crest
and four committed-clock checks.

The strict report validator passes **23 tests**:
`tmp/atlas-stencil-audit-tests-v1-20260918.xml`. It retains equality failures and
rejects an optimization when either execution-order mean loses, even when the
overall mean is faster. Missing pairs, malformed counts and nonfinite or
unmeasured times fail validation. It never awards release acceptance.

## Actual-game comparisons

Both independent captures preserve all fields/masks for all 64 pairs on 50,625
render-source vertices. Each row below contains 32 pairs, with no exclusions.

| Capture | First sampler | Original mean ms | Reuse mean ms | Faster pairs |
| --- | --- | ---: | ---: | ---: |
| A | Original | 2.688610 | 2.609069 | 31/32 |
| A | Reuse | 2.728522 | 2.639747 | 28/32 |
| B | Original | 2.719600 | 2.628075 | 27/32 |
| B | Reuse | 2.748306 | 2.685416 | 25/32 |

The whole-pass mean improvement is 0.084158 ms in A and 0.077208 ms in B.
This qualifies only a small component improvement, not a meaningful whole-frame
speedup or a solution to the current 30 FPS gap. These are separate frozen states
at world times 10.022166396433022 and 10.019370815658476 seconds, respectively.

Raw reports and original-byte SHA256:

- `tmp/atlas-stencil-pairs-a-v1-20260918.json`:
  `371c9763fe10b814900a9cbbc26143a05324549251548de5bc1c897c1f9b37d7`.
- `tmp/atlas-stencil-pairs-b-v1-20260918.json`:
  `0c6406fa1a85676cf3ecb3ddac23c08ac644f3d5a764a2c499533622d5f9fb64`.

Strict summaries are `tmp/atlas-stencil-pairs-{a,b}-summary-v1-20260918.json`.
Capture labels are `south-fork-atlas-stencil-pairs-{a,b}-v1-20260918`.
Both 600-frame game processes exit 0 without timeout; cook suspension/resumption
returns 0 and the four-lane setting plus unchanged solver archive are confirmed.
The instrumented CSVs are retained but excluded from FPS acceptance.

The normal FullReach surface now selects query-local address reuse; other scenes
and presentation callers retain their original selection. Same-binary
`-RaftSimReferenceAtlasStencil` restores the reference lookup. The temporary
candidate-enabling switch is removed. The default change is rebuilt and verified
before the final normal-game checks below.

The final editor build subsequently succeeds, and all 11 native D3D12 checks
pass again with zero warnings/failures/not-run/in-process. Final evidence:

- Build: `tmp/atlas-stencil-final-editor-build-v1-20260918.log`, SHA256
  `c3ac6e824490afedfac29cc8f7e2eb9eff59a41d30fdeb1cdaa5d67ad674ab53`.
- Native: `tmp/atlas-stencil-final-native-v1-20260918/index.json`, SHA256
  `a1e486df45c7e47b63766bfb71ed697a1f075b3b71d586d24a63ef66894c28cf`.

The standalone Development game build also succeeds (26 actions, 242.29 s):
`tmp/atlas-stencil-standalone-build-v1-20260918.log`, SHA256
`e115274250897f0d61e764dd856b837f3ecd4e79eb0442c03113d7e31265a156`.
The rebuilt `unreal/Binaries/Win64/SmokeEmIfYouGotEm.exe` SHA256 is
`3ce4dc4322585c5d0d20ff5f3b469b72adf5f51cdf59e9f8fab094608218f0ca`.
This is a build check, not packaged-release or standalone-performance acceptance;
the game captures below use the rebuilt editor executable in `-game` mode.
The unchanged existing C4701 warning in DetailSourceFootprintTest remains.
Final report-validator rerun: 23 PASS,
`tmp/atlas-stencil-final-audit-tests-v1-20260918.xml`.

## Audit-free game performance: still FAIL30

The final same-binary ABBA sequence is optimized A, reference B, reference C,
optimized D. Each capture retains all 900 CSV rows and uses the fixed inclusive
60..840 window (781 samples), 1280x720 D3D12, ray tracing off, four solver lanes,
and the ordinary South Fork FullReach scenario at station 8330. No comparison
audit is enabled. All processes exit 0 without timeout; the identified cook is
resumed after each. CSV/log hashes, explicit FrameTime mode 0 and solver archive
confirmation are rechecked after all runs. Workload grouping uses verified
scope offset 1, not a fitted timing phase.

| Capture suffix | Sampler | Average FPS | p95 frame ms | 30 FPS gate |
| --- | --- | ---: | ---: | --- |
| normal-a | Reuse | 25.608748 | 47.4820 | FAIL |
| reference-b | Original | 26.130442 | 44.8907 | FAIL |
| reference-c | Original | 26.380410 | 45.1838 | FAIL |
| normal-d | Reuse | 26.713908 | 44.8950 | FAIL |

The first whole-game pair worsens, the reverse pair improves slightly. Variable
trajectories and refresh counts prevent attributing either outcome to a
0.08 ms component change. Do NOT claim a whole-frame speedup. Normal rendering
uses the exact, both-order-qualified source lookup, but 30 FPS and appearance
remain unaccepted. No new reference footage or rendered-motion acceptance.

Labels are `south-fork-atlas-stencil-{suffix}-v1-20260918`. The combined report is
`tmp/atlas-stencil-abba-frame-audit-v1-20260918.json`, SHA256
`da25ddee5d5bffae0ccdaa6f0af2afbd834ce5b470206017ad0c9095f9548cfb`.
CSV hashes in the same order:

- `64ddc5dab35d68034d0a4c153b21f56a33ebeb048b25a7c6d647219506bcca19`
- `dd1bee398a745c0e3916ea75114545a5bdf90e5de9b60d6a3b88d6d4ad2290c7`
- `c6c48283e024b543adf524702d1a3c9cba9f8e9084694e0adecd266e879820f0`
- `073960e2d3b08f943536e1fd15e91cc99f5a901f3f4ef9823219b8c47be9a1e3`

The native solver archive remains
`ae75e631be712a1dee7de53f2ca4b3508d406a1becf4346553806485c221b2a3`.

## Hydraulic continuation

The same live cook (PID 8900, start UTC 2026-09-18T06:34:59.2598919Z) completes
8250 s / local step 11000. Both independent state and artificial-bank audits
pass: 5,382,400 cells, all 86,720 artificial-bank cells exactly dry, maximum depth
3.797632432577762 m, maximum speed 5.351825984473297 m/s, maximum step mass residual
1.4395798775268531e-8 m3. Outflow 101.45107460861701 m3/s still exceeds inflow
45.30695454719997 m3/s: NOT settled. Installed 4950 water is unchanged.

Reports: `tmp/control-ablation-8250s-state-v1-20260918.json` and
`tmp/control-ablation-8250s-banks-v1-20260918.json`. Depth SHA256:
`19617b77cc3048975ccf2e3aaeab18ffe975ddda8d7552146e7edbb8a24f0686`.

8300 s / local 12000 also passes BOTH audits with the same cell counts and exactly
dry artificial banks. Maximum depth is 3.7957173969947178 m, maximum speed
5.351959042032907 m/s, maximum step residual 1.4754001131933592e-8 m3.
Outflow 101.17694176003345 m3/s still exceeds the same inflow: NOT settled.
Reports are `tmp/control-ablation-8300s-{state,banks}-v1-20260918.json`; depth hash
`f2d65ae983e3f5545a2e475ae5eab26c792033e9a3be4246aefc6de546985ea2`.

After all captures and builds, PID 8900 is directly reverified with the same
start time and advancing CPU time (58,325.64 s). Its progress reaches local12830 /
8341.500000018861 s. Do not restart it; next8350/local13000 requires a completed
snapshot marker and BOTH audits. Session68256 remains the original cook handle.

The old exact storage/face regression was inspected but not changed or waived:
the rounded-triangle API cannot simply discard positive fragments that collapse
under float-coordinate export. Broader physical coupling remains unfinished;
nonlinear runtime stays OFF. South Fork precedes Colorado, Pacuare and Futaleufu;
Chilko/Zambezi water reviews, crew, normalization, regressions and release remain
open. Troublemaker remains a rapid within South Fork, never its own menu item.
