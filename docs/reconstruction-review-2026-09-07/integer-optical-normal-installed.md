# South Fork optical normal correction installed

September 17, 2026. Continuation of [normal/reflection isolation](water-normal-reflection-isolation.md).
The optical lattice hash correction is now in the ordinary South Fork material,
not just a diagnostic map. It removes the obvious rectangular noise patches in
the inspected candidate lit/WorldNormal frames and ordinary installed approach.
This does **not** accept breaking geometry, convincing froth, crew, hydraulic
settling, reference-calibrated motion, traversal, performance or release.

## Isolation before installation

All labels in this table have prefix `south-fork-control-ablation-3350s-` and
suffix `-v1-20260917`. Each process report under `unreal/Saved/RaftSimValidation/`
records exit 0, no timeout, 24 actual 1280x720 PNGs and successful exact-process
solver resume. The same 3350s joint-preview descriptor was used; trajectories
vary with actual frame timing, so these are not pixel-registered A/B pairs.

| Label middle | Controlled change | Inspected PNG 022 result |
| --- | --- | --- |
| `no-optical-normal` | optical strength 0 | Smooth, no obvious rectangles, but removes detail; rejected as a fix. |
| `unfiltered-normal` | derivative footprint attenuation disabled | Rectangular/polygonal patches remain; rejected. |
| `full-precision-uv` | all four vertex UV channels full float, original material | Patches remain; rejected. |
| `constant-normal` | fixed nonzero tangent-space tilt | Smooth response; no obvious rectangles, but removes procedural detail; rejected. |
| `zero-flow-normal` | zero optical flow, original noise/filter/strength | Patches remain; rejected. |
| `integer-hash-normal` | integer lattice hash only | Obvious earlier rectangular patches absent; surface noise retained. |
| `integer-hash-world-normal` | same candidate, actual WorldNormal buffer | Previously affected foreground looks continuous; debug commands confirmed. |

The first controls narrow the defect to the procedural optical branch. The
integer hash changes the random gradient pattern, not the wave mesh. Floating
hash evaluation/reassociation was the working hypothesis; no compiler-level
root cause or universal absence of all normal artifacts is claimed.

The accepted scoped change replaces only the floating `frac` hash in
`RaftSimLocalCurrentNormal.hlsl` with the deterministic unsigned integer mixing
already used by the froth cells. It retains both gradient-noise spectra, flow,
source coordinates, clock/phase blend, strength and pixel-footprint filtering.
No lower-detail, flat-normal, zero-flow, full-UV or reflection override is enabled.

Candidate module `tmp/normal-filter-controls-v3-20260917/UnrealEditor-RaftSimRaft.dll`
SHA256 `a06d8570e0a04d045e76cc307f67bf3242d692e18c8106ea6843cb9220dd9eb5`.
Native report `tmp/normal-filter-controls-native-v3-20260917/index.json`:
27 carrier/shoreline/crest tests PASS, zero warnings/failures. This module was
used for isolation only; installed gameplay/project DLLs were not replaced.

Candidate lit PNG 022 SHA256:
`c6dbb7b44b92541a21b3c7e25c849d16b0529d323c1ecd08350a9d157fe82b36`.
Candidate WorldNormal PNG 022:
`676808ff1c4941ec6ab2ca1b99818483a1efc18e3d5026658838f0efbdf6490d`.

## Guarded production integration

`unreal/Scripts/install_south_fork_integer_normal_hash.py` requires the exact
pre-install material and reviewed generated candidate, verifies an exclusive
backup ZIP, and changes only the existing normal custom expression's code.
All other recorded nodes and WPO/base-color/roughness/opacity/mask graphs remain
exact. A separate fresh-editor read-only run verifies the persisted graphs and
source shader. No terrain, collision, hydraulic field, foam density or topology
was changed by this installation.

- Before material SHA256: `7164871356a26f5ad38dbde25fbde70c7d1d684e6c76ec856983415e0a4696cb`.
- Reviewed generated material: `73f27123b913fde2b10725548ce74f4f219e2e590eaf0fb6dd3ee4fcc82b84ef`.
- Installed material: `7e0f29aa41787954ef5d2156345a66c4f5d4d507f79985ae0f6a8311c6fb9038`.
- Exact rollback: `tmp/south-fork-integer-normal-hash-install-v1-20260917.backup.zip`.
- Install/reload reports: `tmp/south-fork-integer-normal-hash-{install,reload}-v1-20260917.json`.

The candidate-builder editor returned 1 after saving; the installer returned 0;
the fresh read-only editor returned 1 after producing its passing graph report.
Those nonzero process results are retained, not presented as clean editor exits.
The independent saved-file hashes/graphs and subsequent ordinary game exit 0
provide the actual persistence/runtime evidence. Game logs also retain the
engine experimental editor-toolset Python initialization errors; no claim of
an entirely error-free engine log is made.

Installed ordinary label `south-fork-integer-hash-installed-startup-v1-20260917`
uses no candidate gameplay module, material variant or joint-terrain override.
All 24 PNGs were produced, game exit 0, exact cook resume 0. PNG 022 SHA256:
`edd977699eb94ac71e90b93155616326a385ae281f6436bcb316a0f1611a69fa`.
The broad white sheet and angular foreground wave boundary are still visible;
do not mistake the optical correction for a realistic reconstructed rapid.
Troublemaker remains a rapid in South Fork, not its own scenario.

## Recorded motion and performance

Fully decoded by `analyze_detail_motion.py`:

| Recording | Actual source frames | Duration s | Decoded frames |
| --- | ---: | ---: | ---: |
| full-precision UV control, `RaftSim_20260917-060159.mp4` | 243 | 15.424 | 463 |
| integer hash candidate, `RaftSim_20260917-062326.mp4` | 269 | 15.508 | 465 |
| ordinary installed, `RaftSim_20260917-063244.mp4` | 265 | 15.570 | 467 |

Decode evidence is under `tmp/control-ablation-optical-normal-motion-v1-20260917/`,
`tmp/control-ablation-integer-hash-motion-v1-20260917/`, and
`tmp/south-fork-integer-hash-installed-motion-v1-20260917/`. Candidate and installed
unmodified decoded 1/6/11s frames were inspected. A fully decoded file plus sparse
visual samples is not full continuous-motion/reference acceptance. The encoded
30Hz timeline may repeat frames and is not gameplay FPS.

Ordinary performance captures use no recording or joint candidate terrain.
The baseline/candidate pair uses the same isolated module; installed uses the
unchanged ordinary gameplay module. Each has 300 CSV samples, with the unchanged
inclusive 60..240 audit and required water scopes. No performance gate relaxed.

| Capture label after `south-fork-integer-hash-` | FPS | Mean frame ms | p95 ms | Mean GPU ms |
| --- | ---: | ---: | ---: | ---: |
| `baseline-perf-v1-20260917` | 30.568258 | 32.713673 | 39.1640 | 11.368515 |
| `candidate-perf-v1-20260917` | 31.068658 | 32.186778 | 39.5646 | 11.086627 |
| `installed-perf-v1-20260917` | 26.340117 | 37.964903 | 43.9981 | 12.833524 |

All FAIL the 30FPS/p95 <=33.333333ms gate. Retain the slower installed result;
these samples do not prove a robust speed change caused by the hash. Reports:
`tmp/south-fork-integer-hash-perf-v1-20260917-audit.json` and
`tmp/south-fork-integer-hash-installed-perf-v1-20260917-audit.json`.
Installed game thread averages37.649469ms. Inclusive water Tick23.359896ms,
CartesianPublish12.380343ms and crest Update8.516869ms identify remaining work;
these nested scopes must not be added. Preserve geometry/detail while reducing
the real frame cost.

## Regression correction

Initial adjacent suite: 28 PASS/1 FAIL. `test_local_froth_phase.py` expected an
obsolete inline lace blend in the C++ author. The failing test, author and froth
cell shader were unchanged from HEAD, verified before editing. The author now
loads `RaftSimFrothCells.ush` and invokes its threshold-before-interpolation
coverage/phase blend, so the old assertion did not test the current path.

The replacement checks the actual file dependency, material-code assignment,
input callsite, four thresholded corner occupancies and complementary phase
blend. Added negative controls reject missing threshold, phase blend or author
assignment; the analytic threshold/phase tests remain. Focused current-normal,
local-froth-phase, graph-signature, diagnostic and frame-CSV suite: 30 PASS.
PowerShell identity/mode/control/log checks also PASS. These are scoped checks,
not closure of all historical regressions or broad physical acceptance.

## Exact hydraulic continuation, still not settled

Old cook36872 is terminal. New cook PID17516 has exact start UTC
`2026-09-17T12:52:03.0749210Z`, executable
`tmp/solver-cfl-rows-v1-20260916/raftsim_cartesian_cook.exe`, SHA256
`b2e2834f2dadd347c0ff89d86e4a90859ee316a563f779b82a6b02767cdc2cfa`.
It continues3600..5400s into fresh `tmp/control-ablation-3600to5400s-v1-20260917/`.
Input `tmp/control-ablation-3600to5400s-input-v1-20260917/manifest.json` SHA256
`bb305e1851cb208b89808a9bf6810f4f7dc6043029e765637dedd68f153fee1d`.

`tmp/control-ablation-3600s-restart-v1-20260917.json` independently verifies all
5,382,400 original cells bit-exact, no added cells/water, unchanged bed/grid/
roughness/boundaries/time; restart volume error4.656613e-10m3. No retuning.
3650 and3700 both pass state/conservation AND all86,720 exactly dry artificial
bank cells. Reports `tmp/control-ablation-{3650,3700}s-{state,banks}-v1-20260917.json`.
At3700: max depth4.053569m, speed5.426968m/s, volume2,908,483.449052m3,
maximum step residual1.521822e-8m3. Outflow88.223760 versus inflow45.306955m3/s:
**not settled or promoted**. h SHA256
`e1164d625fbdab70b6a32c8bf95200278176c76905fca3b3a5b983914c2d2ab1`.
Same exact process verified live beyond3729s after capture/resume. Next3750s /
local3000 requires the completion marker and BOTH audits, not a progress line.

## Remaining acceptance

Continue actual breaking/crest/foam shape and motion, consistent reconstructed
terrain/collision/flow, settling/coupled physics, ordinary frame budget and
traversal/reference review. Captured source geometry is not measured underwater
bathymetry. Then Colorado -> Pacuare -> Futaleufu, plus Chilko/Zambezi water,
crew realism/fit/animation, normalization, outstanding regressions and release.
The active full objective remains open; this correction does not shrink it.
