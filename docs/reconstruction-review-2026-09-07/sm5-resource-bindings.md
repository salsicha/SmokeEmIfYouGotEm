# SM5 resource bindings and normal editor integration

September 16, 2026. The previous turn committed reviewed source/tests as
eb93e5925. This turn changes authoritative integration and compiler evidence;
it does not qualify final visuals, settled hydraulics, packaging or 30 FPS.

## Completed normal-entry observation and deployment

Replay8661/PID32124 is TERMINAL0, with its report independently passing:
5,593 fresh frames, eight post-ready handoffs and372.800019443 detail seconds.
This is the normal GameMode/observer entry point with the separately linked
modules, not the temporary terrain harness. Its startup log verifies paired
terrain activation on the original actor before BeginPlay. The report disclaims deployed normal
binaries, visuals and performance; do not reinterpret that run as deployment.

- `tmp/detail-game-module-v1-20260916/result-v3.json` SHA256
  `a92ba331dc800270bb751ff7dafbd73a457487dce60d140385d7fcf81701ca50`.
- `play-v3.log` SHA256
  `da3ae6a55059954a7cb17836f64cd0687b3091deb7051944ba2e6d115d25991f`.

After the cook was independently confirmed terminal, normal editor build20136
completed22 actions in254.92s. Incremental build23891 then compiled both binding
fixes and completed6 actions in31.52s. Both exit0. The first build retains the
route-test initialization warning and two existing damping-literal warnings.
These are normal installed project/plugin DLLs, not temporary module overrides:

| Module | SHA256 |
| --- | --- |
| RaftSimRaft | `14e578ba824b73ce9cb90c733eb4cfba2a30b8fdd04261034bbe15448f54d591` |
| RaftSimWaterDetail | `650f80cad069a08f4cba6ec18542c67b3d87f823c13aa68f86975645674bbb37` |
| SmokeEmIfYouGotEm | `4daae5dabefdc6107818c2cc4359b57366799e752d71116eedac20ef54e65af9` |

Fresh actual D3D12/SM6 GPU suite93112 completes all83 tests with zero failures,
zero not-run and zero in-process:82 clean successes and one success with an
HTTP connectivity timeout warning during `NonlinearEvolutionOwnerGPU.InitialMove`.
Its numerical/move checks pass, but the strict wrapper exits1 because it requires
83 clean successes. Preserve that warning; this is NOT a clean release pass.
Report `tmp/sm5-resource-bindings-native-sm6-v1-20260916/index.json` SHA256
`06bfa1598511f368b506f414a441afe39f12b76e28a28c91b5c3efed3b120533`.
Unchanged fixtures cover transport/exterior/shoreline, recurrence, temporal
evolution, breaking, foam and prescribed normals. No tolerances were changed.

## Terminal package failure, cause and correction

Package83678/cook5852/shader5104 is TERMINAL FAILED: UAT25, cook3 after19,034.44s.
Do not poll/restart the old job. The actual SM5 compiler reports25 errors,
including acceleration permutation26 using10 UAVs, transport10 using11,
transport15 using12, transport21 using13, and transport internal compiler errors
(including3,4,9,34). SM5 supports eight writable-buffer slots. Earlier standalone
FXC exit0 probes missed the reflected extended-UAV requirement; they were not
evidence that the engine's SM5 platform accepted those shaders.

Transport now binds13 intermediate buffers as UAVs only in their producer phase,
and as SRVs when read by later phases. The maximum actual producer outputs are
eight in exterior flux phase3; phase4 needs only its three outputs. Acceleration
phase13 reads Direction, Scratch, Partial and Control through SRVs, leaving six
outputs. Other acceleration phases retain their existing read/write behavior.
RDG receives mutually exclusive input/output views and keeps unused-resource
clearing, barriers and distinct fused control buffers. Arithmetic, ordering,
iterations, grids, fixtures and feature-level targets are unchanged.

New `audit_sm5_shader_resources.py` checks actual FXC resource reflection against
declarations and the eight-slot limit, rejecting the extended64-UAV feature flag.
It rejects the archived transport21 binary listing (13 slots) as expected.
An unchanged archived acceleration26 input with only the four input bindings
corrected compiles with original cs_5_0/O3/Zpr/Gec/Ni flags and passes reflection:
six UAVs, no extended-slot requirement. Its compiler warnings remain retained.
This is a focused compiler/resource check, not an actual SM5 GPU pass.
`tmp/sm5-acceleration26-bindings-v1-20260916/resources.json` SHA256
`fbe32a7286a5c86a99f91c72c5118883256004c3f863a16dcac720460badbb73`.
The initial audit invocation rejected FXC's indented listing; the parser now
accepts indentation with a regression case. The compiled artifact was reused.

Before another engine SM5 invocation could overwrite debug output,125 original
compiler files were copied into `tmp/sm5-cook-v2-failed-dumps-20260916`.
Its manifest SHA256 is
`50de86dc1bc34fc94fe78ba46b936f999b85434f30681c6ee2a7aa2485b528e6`.

Fresh engine SM5 suite47178/PID35584 is LIVE, using the same83 tests and fixtures
with explicit `-d3d12 -sm5`; shader workers are independently confirmed live.
Log `tmp/sm5-resource-bindings-native-sm5-v1-20260916.log`. Preserve this job and
its inputs. Shader compilation, reflected-resource coverage, actual SM5 GPU
execution and full packaging remain unproven. Do not launch a repeated full
cook before resolving this run's results. No full package/archive exists yet.

## Rejected CFL optimization

The fixed four-pair, alternating-order comparison14933 finishes0. All native
physical progress records and all h/u/v snapshots match byte-for-byte across
841 tiles; all source inputs remain unchanged. Paired solve/capture seconds:

| Pair/order | Baseline | Candidate |
| --- | ---: | ---: |
| 0 baseline first |21.7438974|21.2107721|
| 1 candidate first |22.2948801|21.1598171|
| 2 baseline first |21.5132678|22.9193550|
| 3 candidate first |31.2269537|24.9593618|

Combined medians22.01938875 versus22.06506355 do not demonstrate a consistent
gain in both orders, particularly with concurrent work. The tile-CFL production
parallelization from eb93e5925 is removed; comparison tooling and rounding-mode
tests remain. No live hydraulic executable or UE solver archive was replaced.
Report `tmp/domain-cfl-tiles-pairs-v1-20260916/report.json` SHA256
`f3074fb2d1e609cee3a3125ac11a8daf297ee8dabbcce0d0082b7a115b6d92f1`.
Fresh native rebuild/CTest29135 passes4/4 after the removal. The first invocation
lacked vcvars and failed to find standard headers; the corrected invocation
initializes the normal MSVC environment.40 focused Python checks also pass.

## Hydraulic continuation and source protection

The SAME hydraulic40601/PID11316 remains LIVE toward1800s. Both700/local2000
and750/local3000 pass full5,382,400-cell state/conservation checks and all86,720
exact-dry artificial-bank faces. Outflow56.058395 and57.043148m3/s respectively
still exceeds inflow45.306955m3/s: NOT settled. No runtime-field promotion.
NEXT completed800/local4000 requires BOTH audits.

| Report under tmp | SHA256 |
| --- | --- |
| control-ablation-700s-state-v1-20260916.json | `d7acd73381c459bbf3f8e82fe3f667b3b60e60442476047fa42e64fc82273fe3` |
| control-ablation-700s-banks-v1-20260916.json | `196a517176bfffbe1db87a3e3238dee94ead1a4fd463594ea98ae6b1545dedde` |
| control-ablation-750s-state-v1-20260916.json | `af35f07a0885a4df40b48801d85c37f45d9e2d4dae7e69399ac45de4d1ba4f19` |
| control-ablation-750s-banks-v1-20260916.json | `52c5700e3e6e16d78be5f1cc9cfc389ccce51e188747ca1513b216b0f5f9ac54` |

All464 protected identities remain462 unchanged plus two previously verified
CPU-retention-only revisions, with zero mismatches. Report
`tmp/sm5-resource-bindings-protected-v1-20260916.json` SHA256
`e7ac3291a196b350271fc24373990573d97ccd74bb3142354fb51a24fabef233`.
Normal editor DLLs were intentionally rebuilt only after the prior cook ended.

NEXT validate SM5, normal installed-module playback and full package/source
closure; finish settled actual-motion/reference comparison, breaking/froth,
contact/traversal and30FPS/p95<=33.333ms. Last ordinary17.819710FPS/p9581.6343ms
still fails. Colorado -> Pacuare -> Futaleufu, Chilko/Zambezi water, crew,
normalization/regressions and release remain open. Troublemaker is only a rapid
inside South Fork, never a separate scenario/menu entry.
