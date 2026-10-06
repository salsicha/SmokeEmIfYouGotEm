# Preserve native mean stage at the rapid — September 12

## Actual cause measured before changing geometry

The old playable Cartesian carrier used optically filtered water levels as its
base geometry. A new opt-in source decomposition exports raw stage/depth,
filtered stage, added hydraulic relief, shared crest, remaining relief and
final source target. It is before temporal rendering, wet-bank clipping and
GPU perturbations; it is NOT total rendered contact or photographic evidence.

Old-state game27358 exits0.10,823 wet targets,8 local flow-aligned profiles,
maximum component-sum residual9.239502e-8m:
`tmp/south-fork-surface-decomposition-v1-20260912.csv`,
`tmp/south-fork-surface-decomposition-analysis-v1-20260912.json`.
At the largest accepted crest, field[-5439,3606]m:

| Contribution | Metres |
| --- | ---: |
| Raw solver stage | 6.100173950 |
| Filtered base stage | 7.156731610 |
| Hydraulic relief | -0.205370188 |
| Shared crest relief | 0.512181358 |
| Remaining relief | -0.001722326 |
| Final source target | 7.461820450 |

The optical filter fills this solver trough by1.056557660m before the crest is
added. That is not a new measured bathymetry/flow claim: the underlying native
solver still uses inferred submerged geometry and the audited600s runtime.
It does explain a large, specific loss of resolved shape in presentation.
Along the same partial24m profile, raw endpoint-detrended trough is-1.429m,
filtered-0.366m. Endpoint trends are descriptive, not calibrated wave heights;
missing/dry four-corner samples are omitted, never extrapolated.

## Changes

For the normal single Cartesian carrier, retain the native sampled mean stage
as base geometry. Keep the existing filtered hydraulic-analysis input and
explicit relief/crest/pocket/detail mechanisms separate. Cartesian raft
support similarly stops replacing its mean stage with an optical average;
its separate relief analysis remains. This fixes the base-stage authority,
not every mismatch between support and the full rendered water.
No solver/grid/terrain/material or scoring/menu changes. Troublemaker remains
inside the South Fork scenario. No acceptance gate is lowered.

Also factored an exact shared physical-crest envelope so source-only queries
skip unused toe/tail geometry. The existing source test now compares22,326
samples against a frozen pre-optimization expression as well as the carrier.
This does not change forcing amplitudes or spatial profiles.

## Verification history and limits

Initial diagnostic build42364 fails17.59s due unbraced UE_LOG macro/else.
Corrected12958 succeeds47.83s; strengthened-test build23903 succeeds17.58s.
Pre-stage-change57native/GPU tests pass87189. Analyzer initially required
pytest unavailable in bundled Python, then its standalone unittest version
caught integer direction normalization. Actual capture then rejected an
assumed2cm lift: same engine log records0. Analyzer now requires that logged
lift explicitly, not a waived sum gate. Five standalone tests pass, including
consistent-but-smoothed stage rejection and existing-evidence preservation.

Native-stage build5171 succeeds52.92s. RaftDLL
`3fdbc5d4c84a211a784da76e0207c7a6f5be026597bbb343230addb258b9303d`;
WaterDLL `abc499f431000fe6188850eca521dbe10703978542fc0e9c761bbdb318a4f5f9`.
MainDLLf306c15a… unchanged. Final engine run25804 exits0:57 tests pass,
zero warnings/failures/unrun, including native Cartesian support stage and
the catalog/save migration tests. Report:
`unreal/Saved/RaftSimValidation/south-fork-native-stage-regressions-v1-20260912/index.json`.

Actual post-change game69893 exits0. Decomposition contains10,823 wet source
targets with EXACT zero base/native-stage difference and4.8046914e-8m maximum
component-sum residual. At[-5439,3606], raw/presentedbase6.10021973m,
oldfiltered7.1568141m (diagnostic only), hydraulic-.205373764m,
crest+.512217407m, other-.00170066833m, target6.4053627m. Reports:
`tmp/south-fork-native-stage-v1-20260912.csv`,
`tmp/south-fork-native-stage-analysis-v1-20260912.json`.
The audit uses the actual logged0m render lift and requires native stage.

Actual submitted crest audit:1,550,016 samples, maximum shared-crest error
.600724663cm against the unchanged2cm gate; fine correction tracking
.000322044cm, source change within refinement0. This is NOT a claim that
base geometry stayed unchanged by this correction, nor total rendered contact.
`tmp/south-fork-native-stage-crest-v1-20260912.json.cartesian-mesh.json`.
Source UV3 transport and UV1 bulk-channel errors both0:
`tmp/south-fork-native-stage-transport-v1-20260912.json`.

Motion series40 unique PNGs over12.048 game seconds, stationary camera:
`tmp/south-fork-native-stage-motion-v1-20260912.json`. Frames000 and039
actually inspected: deeper foreground depression/steeper falls, but broad
smooth central wave and thin linear froth STILL NOT accepted. Movie
`unreal/Saved/VideoCaptures/RaftSim_20260912-164520.mp4`,
SHA256 `7ac915be2c2a7758e8fe35ab61871a16caecbd99929871d9a7fffdf20602ca15`,
84 source frames over16.673s; not continuously viewed and not an FPS measure.
Heavy capture detail lag5.268910s; this does not establish correct motion pacing.

Isolated profile46035 exits0; exact cook29104 successfully suspended/resumed
(both statuses0), no timeout. Rows100..250 of300: mean50.952851ms,
19.625987FPS, p9559.1538ms: STILL FAIL60FPS. Previous sample14.917181FPS;
trajectory/update-count differences prevent attributing all improvement to
the source-only optimization. GPU13.602103ms, crest update16.288254ms;
source preparation1.374009ms/update versus1.924248 previously. Ordinary detail
backlog3.600ms, unlike the heavy recording. CSV SHA256
`4b5881abc3db0f54fddf5181650579a0416c61653bc90ed0adaeb6cc1d6a9fdb`;
`tmp/south-fork-native-stage-performance-v1-20260912.json`.

Reference image search found Dreamflows and Lake Tahoe gallery entries, but
both requested full image files returned cache misses. No new real photo or
continuous reference video was actually viewed. Search descriptions are not
visual evidence. Physical breaking/froth realism, total raft/rendered contact,
sustained60FPS, full-river hydraulics and later-river/release gates remain open.
This is a verified presentation-stage correction, not completion of the goal.
