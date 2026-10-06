# Source-matched preview terrain now uses its exact render surface

September 17, 2026. The 3350-second paired preview exposed a rendering-policy
gap: the normal captured-ground correction recognizes the original asset path,
but the verified ephemeral terrain replacement has a different path. Its
collision/source validation passed while its Nanite rendering still exposed a
green angular water patch beside the starting bank.

## Correction and scope

The joint-preview loader now requires the revised terrain's sole fallback LOD
to be collision LOD zero and contain the complete verified triangle count.
This is an additional preflight after the existing collision-source SHA256 and
all dependency/geometry/water checks, not a substitute for provenance. The
replacement component selects that exact fallback before paired water BeginPlay.
No global Nanite setting, ordinary asset allowlist, saved terrain, collision,
hydraulic state, water material, menu entry or scenario is changed.

The isolated project build compiles and links. Its first link used a stale
gameplay import library; relinking against the installed gameplay build resolves
the three missing checkpoint symbols. The first native fixture incorrectly
assumed the engine cube has 12 triangles: it actually has 48. Retained report
`tmp/joint-terrain-exact-render-native-v1-20260917/index.json` has 13 passes and
that one failure. The corrected fixture uses the actual captured 803,842-face
terrain, with null/zero/negative/mismatched/unrelated-source rejection checks.
No gate was relaxed. The second native run passes all 14 preview, checkpoint and
shoreline tests, with zero warnings/failures/not-run/in-process:

- `tmp/joint-terrain-exact-render-native-v2-20260917/index.json`
- SHA256 `0aba0a899cf675443a4010d5c0770769d2051f8472cd6a44bfc3729819046735`

The focused Python joint-preview, terrain-replacement, verified-playback and
startup-motion tests pass 101/101. These are scoped checks, not release acceptance.

## Actual paired source and motion evidence

The 3350-second native check is complete: 64,935 collision queries all hit within
the unchanged tolerances; 25,600 field queries pass with zero wet/dry mismatches.
Maximum bed/surface error is 7.62939453125e-6 m. Different wet query counts use
the existing 1e-6 solver and 1e-4 native-sampler thresholds, not changed gates.
All 803,842 directed source triangles are compared: 2,132 inferred vertices and
4,466 faces change; untouched corners, registered XY and winding remain bit-exact.
No saved assets/levels or water state were changed by this read-only verifier.
Report `unreal/Saved/RaftSimValidation/control-ablation-native-runtime-3350s-v1-20260917.json`,
SHA256 `a39f37f4343988e0d1d9a8a0e8b9a59bad2ba27b6575eeebaf499d939f26f0fd`.
The revised bed is still an inference, not measured underwater bathymetry.

All three captures use descriptor
`tmp/control-ablation-3350s-joint-preview-v1-20260917.json` (SHA256
`9c06666f5c0ff9dbb71c061f09bdeb0ad99fd2e6aed5080db3b2c69fc20eebab`),
the same source state/material, one visible water surface and ordinary gameplay
camera. Each writes 24 actual 1280x720 PNGs, exits 0 and resumes cook 36872 with
status 0. They are not frame-identical trajectories or calibrated optical flow.

| Capture label suffix (all prefixed `south-fork-control-ablation-3350s-`) | Video | Engine source frames / duration | Fully decoded frames |
| --- | --- | --- | --- |
| `motion-v1-20260917` | `RaftSim_20260917-043744.mp4` | 224 / 15.561 s | 467 |
| `exact-ground-v1-20260917` | `RaftSim_20260917-045448.mp4` | 235 / 15.580 s | 467 |
| `exact-ground-installed-v1-20260917` | `RaftSim_20260917-045705.mp4` | 233 / 15.482 s | 464 |

Videos live in `unreal/Saved/VideoCaptures/`. Their respective SHA256 values are:

- `1157791f90904accd4c1e14f3d2aa9fa682caca4af05218e093591ce041a8ac5`
- `2b3249703dc31323ff83d08957df2d80a868ec583f62655abfd522ca315b986d`
- `2cfb8197f100f24de8f94818d6841319938c312f72b2e8aed123ad552e90e26e`

`analyze_detail_motion.py` fully decodes each recording. Outputs are in
`tmp/control-ablation-3350s-motion-v1-20260917`,
`tmp/control-ablation-3350s-exact-ground-motion-v1-20260917`, and
`tmp/control-ablation-3350s-exact-ground-installed-motion-v1-20260917`.
The encoded 30 Hz timeline can repeat presentation frames: it is
**not game FPS evidence**. Fixed image rectangles are not water segmentation.
The wrapper's `fully_decoded=false` describes its own file/header-only check;
the independent decoder results supply the subsequent full-file check.

Inspected decoded 1/6/11-second frames before and after the isolated fix, and
1/11-second frames through normal installed-module startup. The starting green
patch is replaced by the actual rock bank. Broad smooth foam, rounded spilling
faces and detached-looking spray remain. The installed 11-second frame also
shows a sharp rectangular water transition near the lower-right edge: trace
actual window/render ownership there next, without assuming its cause from a
single image. Sparse frame inspection plus complete decoding is not continuous
physical-motion or photographic acceptance. Prior accessible reference footage
still demands irregular rock-controlled tongues and darker intervening gaps.

## Installed state and remaining work

Only the project DLL/PDB is installed; the correction runs only inside the
guarded ephemeral preview. Normal launch with the same descriptor confirms
803,842 render triangles, paired terrain/water activation and `singleSurface=1`.
The candidate terrain/hydraulics are **not** promoted to ordinary scenarios.

- Project DLL SHA256 `4d2bae9fb4e0b560ecf8a3889b927dacbd86f77e8eeccb27a5a020ae8190472e`.
- Exact old DLL/PDB and install hashes: `tmp/joint-terrain-exact-render-installed-backup-v1-20260917/`.
- Gameplay DLL remains `bb80e7c1222bfa027507904f368893f0ed25fb1fc5ce4e8a60889dc1b4e3442f`.
- Material remains `7164871356a26f5ad38dbde25fbde70c7d1d684e6c76ec856983415e0a4696cb`.

The same live cook's 3400/local32000 and 3450/local33000 snapshots pass both
state/conservation and all 86,720 exactly dry artificial-bank cells. At 3450 s,
outflow is 86.489332 versus inflow 45.306955 m3/s: still not settled. Reports are
`tmp/control-ablation-{3400,3450}s-{state,banks}-v1-20260917.json`. Next 3500/local
34000 requires a completed snapshot and both audits; do not restart the live cook.

No new ordinary performance measurement: the last installed 27.565906 FPS /
p95 42.8224 ms still fails 30 FPS / p95 33.333333 ms. Complete realistic single-
surface breaking/froth, physical/reference comparison, settling/convergence and
performance before proceeding Colorado -> Pacuare -> Futaleufu. Chilko/Zambezi,
crew, normalization, regressions and release remain open. Troublemaker remains
a rapid within South Fork, not a scenario or menu entry.
