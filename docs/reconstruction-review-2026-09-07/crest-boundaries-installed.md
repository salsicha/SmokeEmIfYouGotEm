# Exact crest boundary classification installed

September 17, 2026. This is a CPU optimization on the existing playable surface,
not a wave-detail reduction or acceptance of physical/visual/performance gates.
The [integer optical-normal correction](integer-optical-normal-installed.md)
remains installed and unchanged.

## Angular face: captured evidence, not a smoothing prescription

`south-fork-integer-hash-angular-boundary-v1-20260917` captures the ordinary
South Fork scenario with the indexed shape exporter, without candidate terrain
or material overrides. Game exit0,24 PNGs, exact cook resume0. PNG022 SHA256:
`560a6efaa498e9fc71caaf3c95783fe4ccee3c612a26489678bdedc44df207db`.
Its carrier/camera export shares game frame155, world11.276242s, detail sequence152.
Independent report `tmp/south-fork-angular-boundary-rays-v1-20260917.json` retains
all seven probes and source hashes, not selected successful hits only.

| Screenshot probe | Cached-source slope | Submitted base slope | CPU displayed slope |
| --- | ---: | ---: | ---: |
| (640,650) | 42.505185deg | 45.835096deg | 45.722614deg |
| (960,690) | 42.939334deg | 48.545468deg | 46.418201deg |

Both source cells are fully wet, with recorded corner depths0.61..2.36m.
At(640,650), crest/detail gradient magnitudes are0.002701/0.007599 versus a
roughly unit base gradient. At(960,690), they are0.141891/0.037670. The submitted
base-minus-target gradient components are at most0.000158 at these two probes.
The large face is already represented in the cached mean stage plus existing
base shaping; it is not justified to flatten fine crests to conceal it.

These are nearest exported CPU triangles with vertex-sampled presented detail,
NOT GPU pixel visibility, terrain occlusion, a GPU fence or measured river
geometry. No terrain-ray list was requested in this capture. Base is a residual
including hydraulic/other shaping; cached bed+depth is not a new live solver
query. Current source still uses inferred submerged geometry and the existing
runtime field. The source-consistent reconstruction/coupled breaking/motion
work remains required; this diagnosis does not accept the sharp face or froth.

## Exact boundary lookup change

The original boundary classification built a general edge-count map and a
separate boundary set on every changed refinement topology. The new path uses
the existing bounded indexed-edge lookup for both root counts and propagated
boundary markers. Consumed edges become zero; the same ordered parent edges
create the same two boundary children. Chains remain bounded to eight entries,
with the original map fallback for high-degree/nonmanifold cases.

The frozen reference algorithm remains callable with
`-RaftSimLegacyCrestBoundaries`. No coordinates, heights, profiles, tolerances,
selection, topology, interpolation, normals, refresh rate, wet membership,
collision, hydraulic state or material changes. Boundary state is reconstructed
from current topology, never reused from an older topology/profile.

Native `RaftSim.M4.CrestBoundaries` checks empty input, consumed/repeated edges,
descendants, duplicate/nonmanifold faces, self edges,36 moving/cropped/winding/
refinement fixtures and a70,000-edge fan. Added FindOrAdd tests exercise both
indexed and overflow storage without replacing existing values.

## Actual-input qualification

The native audit compares all boundary flags against the reference AND the
actual production flags, including counting, allocation and propagation cost.
Two warm calls precede64 numbered comparisons with alternating execution order.
The analyzer rejects incomplete histories, invalid counts/timings, reordered
frames, implicit truthy results and improvement in only one execution order.
These timings are classification cost, not complete crest-update or frame time.

| Capture | Midpoint flags | Reference mean ms | Indexed mean ms | Both orders faster |
| --- | ---: | ---: | ---: | --- |
| pairs-v2 | 982,472 | 2.269283 | 0.807441 | Yes, all64 individual pairs faster |
| pairs-v3, candidate active in gameplay | 983,992 | 2.302197 | 0.823850 | Yes, all64 individual pairs faster |

All1,966,464 flags are exact. v2 reference-first2.293451->0.801697ms and
indexed-first2.245116->0.813184ms; v3 reference-first2.331603->0.820391ms and
indexed-first2.272791->0.827309ms. No unfavorable pair was removed.
Reports `tmp/crest-boundaries-pairs-v{2,3}-20260917.json`, SHA256 respectively:

- `d97d70caded05c3146b0c827b95729f305fe5c2301d69249702a89f287aa1656`
- `c4f96b55b0175383e62540b571ef8de391752b70bef137d9315a2b00671f4ceb`

Summaries use the same stems plus `-audit.json`, produced by
`physics/scripts/audit_crest_boundary_pair.py`.

The earlier300-frame pairs-v1 capture exited normally but contained only26
post120 topology-change samples and no complete64-pair report. It is retained
as incomplete evidence, not a pass. `ProfileFrames` now permits explicit
300..2400-frame ordinary CSV histories, preserving the300-frame default,
30FPS metadata, watchdog and all native/replay gates. Nondefault lengths are
rejected for native/replay modes. Both qualified captures requested1200 frames;
the audits completed at frames627 and641. Their instrumented CSVs are not
ordinary performance measurements.

## Build and installation

Opt-in v1 and default-enabled v3 native suites each pass28 carrier/shoreline/
crest tests with zero warnings, failures, unrun or in-process tests. Reports:
`tmp/crest-boundaries-native-v{1,3}-20260917/index.json`.
Focused boundary-audit, carrier-ray/source-shape/epoch and frame-CSV Python
suite:49 PASS. PowerShell exact identity/mode/command/duration checks PASS.

One default-enable source edit failed to write while leaving the file intact;
the cause was not established. Ample disk space and intact source were verified.
The v2 build therefore still contains the opt-in version and was NOT installed.
After compilation ended the exact patch succeeded; a fresh v3 build compiled
the verified enabled source and passed its own native suite. No stale-build
qualification is inferred. Only the affected gameplay unity and standalone
test were rebuilt; no class layout changed. This is not a full release build.

Installed DLL SHA256:
`89b171f1a2031beb88b0e0a275a928b9acc1c9580b92616e7c4e64890302e410`.
PDB: `aa6518a9e38ca0aedafda6540263c6f9e752af93a3a1fb85651c974c01a9a189`.
Exact previous DLL/PDB and manifest:
`tmp/crest-boundaries-installed-backup-v1-20260917/`.
Previous DLL: `bb80e7c1222bfa027507904f368893f0ed25fb1fc5ce4e8a60889dc1b4e3442f`.
Previous PDB: `44246235f412e75b5f4d12062a7855c10c990a5983c919cc5bb44718d520a8f2`.
Both backups and installed copies were verified; no editor was live during
replacement. The project DLL, water-detail DLL and material remain unchanged.

## Hydraulic continuation

Same exact cook PID17516, UTC start2026-09-17T12:52:03.0749210Z, fresh3600..5400s
output, executable/input identities from the preceding review remain in use.
3750 and3800 snapshots pass state/conservation AND all86,720 exactly dry
artificial bank cells. Reports:
`tmp/control-ablation-{3750,3800}s-{state,banks}-v1-20260917.json`.
At3800: maximum depth4.025012m, speed5.403377m/s, volume2,904,141.695024m3,
maximum step residual1.521822e-8m3. Outflow90.091924 versus inflow45.306955m3/s:
still NOT settled or promoted. h SHA256
`b11c622c1a2cb3c2e313070953e9a7760ccde318c6d1264ee7181ee2b98bb31b`.
Next3850/local5000 needs the completion marker AND both independent audits.
No solver restart, forcing/bed retuning or missing-input extrapolation.

## Ordinary installed frame-time follow-up

Existing uninstrumented 300-frame installed and legacy-control captures were
audited over the same inclusive CSV sample indices60..240 at1280x720/D3D12.
Report: `tmp/crest-boundaries-commit-perf-20260917-audit.json`.

| Capture | Elapsed-frame FPS | Mean frame ms | p95 frame ms |
| --- | ---: | ---: | ---: |
| Installed indexed boundaries | 30.936070 | 32.324727 | 39.5813 |
| Legacy boundary control | 30.263432 | 33.043179 | 40.0262 |

CSV stems: `south-fork-crest-boundaries-{installed,legacy}-perf-v1-20260917`.
SHA256 respectively:

- `34a70846c553ab33c7691f718851c8cb35adaab87112f6e8d95b0401ec362206`
- `3148d021401a843387cdb3067653760d6e3adeb44621b30993f0a8344c6b3d13`

Both remain outside the33.333333ms p95 budget. One short pair does not establish
a repeatable whole-frame speedup, sustained30FPS or release acceptance. The
installed visual follow-up remains outstanding. The focused49 Python tests
and PowerShell identity/mode/duration checks were rerun successfully before
commit; the existing default-enabled native report records28 passes,0 failures.

## Still required

Sustained installed frame-time and visual follow-up must be evaluated separately
from the local speedup. Source-consistent terrain/collision/hydraulic geometry,
physically convincing single-surface breaking/froth and calibrated motion,
traversal,30FPS/p95<=33.333333ms remain open. Then Colorado -> Pacuare -> Futaleufu,
plus Chilko/Zambezi water, crew fit/animation/realism, normalization, regressions
and release checks. Troublemaker remains a rapid inside South Fork, never its
own menu scenario. No broad gate is closed by this exact-output optimization.
