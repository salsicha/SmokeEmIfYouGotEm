# Material source split — September 23

Supporting maintenance only. No geographic, visual, hydraulic or release acceptance.

The current layout failures were the material implementations, not the previously
split full-reach and foliage builders. The physical-source terrain material builder
now has its own translation unit; photoreal water builders and their private helpers
are separated from terrain, boulder and crew builders. The three water-builder
declarations share a header. Defaults and command registrations are unchanged.

The [exact relocation receipt](material-source-split-20260923.json) compares the
four resulting implementations against commit `07668688a`, allowing only the
necessary includes, declarations/linkage and relocation of default arguments.
Every existing expression-building function body is retained. Resulting sizes:
base2729, physical-source terrain824, photoreal terrain/crew2958, photoreal water2569
lines. No layout allowance was increased. No asset generator was run, and no saved
material, captured geometry, collision, hydraulic input or installed field changed.

Source-text consumers now read explicit ordered material source sets. Missing
members fail even when unrelated sources contain matching tokens; unrelated files
are not globbed into evidence. Seven new tests cover these contracts. Existing
assertions, numeric limits and historical hashes were not rewritten.

## Verification

- Source-set, unchanged size limits and regenerated inventory: **9 passed**.
- Layout comparison: before27 passed/8 failed; afterward29 passed/6 failed
  (plus four new source-set cases in that initial combined run). Only the size
  and stale-inventory failures closed. Six existing material/provenance expectations
  remain unresolved.
- Nine affected consumer suites: **43 passed/15 failed**, exactly the same failing
  test identities as a retrospective control supplying the two pre-split sources.
  This was a source-only control, not a restoration of every historical asset.
- Editor rebuild: passed in47.90s. The initial build caught include ordering and a
  terrain-only helper moved with the water block; both were corrected before this
  successful build and exact-relocation audit. No standalone game target rebuild
  or packaged qualification is claimed for this editor-module-only change.
- Real D3D12 editor career catalog: **1 passed, 0 failed, 0 warnings** in that test
  result; this does not certify every SDK or release log warning.

## Normal playable checks

The normal South Fork scenario path ran with four solver lanes, D3D12 at1280×720.
Motion capture retained24 views and a15.508s video. Full decoding produced465
frames including20 exact adjacent repeats. Actual3s and13s views were inspected:
raft/crew motion and river-distance advancement are present. Broad smooth water,
coarse repeated canopy and early crew shading limitations remain. No appearance
gain is attributed to this refactor.

A separate900-frame ordinary cost run used no capture, diagnostic or candidate
flags. Samples60–840 yield mean26.412631ms (**37.860673FPS**) and
**p9536.3412ms: FAIL** against33.333333ms. Mean GameThread26.204199ms,
GPU9.298098ms; nested water Tick14.262043ms, CartesianPublish7.751314ms,
CrestsUpdate3.462177ms and Topology1.193076ms must not be added together.
The confirmed UE5.8 frame-time scope offset is1. This first-pool window is not
the rapid-at8330 workload, a performance improvement claim or whole-river acceptance.

The sole exact-state cook was identity-guarded, suspended during profiling and
resumed successfully. Its CPU time did not advance during the ordinary cost run.
The initial identity check rejected CIM's0.4µs truncation before suspension;
the exact .NET start timestamp was then recorded without weakening the guard.
All engine/build jobs are terminal. Cook36692 remains live; checkpoint15100s
passes state/dry-bank audits but remains unsettled. Installed4950s fields and
nonlinear OFF are unchanged. South Fork and the ordered river queue remain open.

## Local evidence

These generated local artifacts are retained, not substituted for acceptance:

- `tmp/material-source-split-focused-v1-20260923.xml`
- `tmp/editor-layout-current-v1-20260923.xml`
- `tmp/editor-layout-split-v1-20260923.xml`
- `tmp/material-source-consumers-v1-20260923.xml`
- `tmp/material-source-consumers-baseline-v1-20260923.xml`
- `tmp/material-source-split-build-v2-20260923.log`
- `tmp/material-source-split-native-v1-20260923/index.json`
- `unreal/Saved/RaftSimValidation/south-fork-material-split-normal-v1-20260923-process.json`
- `unreal/Saved/RaftSimValidation/south-fork-material-split-cost-v1-20260923-process.json`
- `tmp/material-source-split-motion-v1-20260923/report.json`
- `tmp/material-source-split-cost-audit-v1-20260923.json`

Cost CSV SHA256: `c9f4c9f41bab6dc2b8b980bfd261aa62e021767b99200ee87bcb97999056d53f`.
Video SHA256: `4fc762f6cd9799cc56702b8ed221cc7a8b815844d4f9f7f9ca1207b14e19b98a`.
