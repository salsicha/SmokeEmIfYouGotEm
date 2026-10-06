# Normal installed-module performance and full replay

## Ordinary 30 FPS measurement

The normal South Fork FullReach game still fails the 30 FPS target. A complete
300-frame capture at actual 1280x720, D3D12/SM6, measured **22.560934 FPS** and
**53.9323 ms p95** over the original inclusive CSV rows 60–240 (181 samples).
The budget remains 33.333333 ms. This is a short warmed development measurement,
not sustained packaged-game acceptance or a claim that visual quality passes.

Session61858 exited0. The label is
`south-fork-normal-installed-ordinary-v1-20260916`. No temporary module,
reconstruction preview, full-hull audit, quality reduction, solver change or
resolution change was used. The old17.819710 FPS capture remains historical
evidence; differing machine load and gameplay trajectories mean this is not a
controlled claim of an optimization speedup.

The owned hydraulic cook11316, SM5 editor35584 and its workers31104/31820/34968
were identity-checked and temporarily suspended. All five suspension and resume
statuses were0, CPU time remained unchanged during this capture, and subsequent
CPU observations increased for every process. No job was restarted and no shader,
DLL, hydraulic input or checkpoint was replaced.

Mean measured times in milliseconds (inclusive scopes, **do not add them**):

| Scope | Mean ms |
| --- | ---: |
| Frame | 44.3244 |
| Game thread | 44.0753 |
| GPU | 15.1225 |
| Water actor tick | 28.9839 |
| Cartesian mesh publication | 17.0290 |
| Shoreline SetMesh | 15.5947 |
| Crest update | 10.6317 |
| Crest selection | 4.4444 |
| Crest normals | 0.7416 |
| Solver StepWater | 7.0312 |

A separate existing-stage-log capture, session72082, also exited0 and resumed
all five jobs. It is diagnostic, not the ordinary FPS result. Across engine
frames60–240, crest sampling averaged3.23 ms and vertex construction/history
2.80 ms; normals averaged0.67 ms. Those measurements direct further work toward
sampling and vertex construction, not the already-rejected normal candidates.
The ordinary capture records181 updates,91 XY/profile/coarse changes, four index
changes, two shoreline/detail-window changes and88 dense-history updates.
Changing profiles accompany the expensive rebuilds, so retaining old profile
values across frames is not a valid optimization. No reduction in fidelity,
update rate, refinement thresholds, physical gates or coverage is authorized.

## Profiling runner repair

PowerShell JSON decoding returned `System.DateTime` for manifest timestamps.
Comparing those values directly with exact timestamp strings rejected matching
live processes before any suspension. The runner now normalizes DateTime values
to their full UTC round-trip representation. String manifests still work; even
a one-tick (100 ns) identity difference remains rejected. The process-safe
PowerShell regression covers both representations, actual JSON decoding,
malformed/changed times, and conflicting validation modes. The related CSV,
history, midpoint and normals parser suite passes25 tests. The first expanded
test invocation lacked the existing pytest dependency path; restoring the
repository's test environment resolves that setup failure. No identity criterion
or test expectation was removed.

The full-replay mode delegates exit and coverage to the existing native probe:
120 world seconds, eight post-ready handoffs, 100 fresh frames and60 detail
seconds, with its unchanged900-second observation timeout. The outer960-second
watchdog only accommodates engine startup and shutdown. It cannot convert a
native failure into a pass. Full replay results are recorded separately below.

## Full installed-module replay: pass, not scene acceptance

Session59643/PID35200 exits0 with the native report `passed:true`:
5,593 observed ticks,5,593 fresh frames, eight post-ready handoffs and
372.800019443 detail seconds. The final periodic observation is at663.993 world
seconds; completion follows the next handoff. This is the full original gate,
not the earlier failed seven-handoff prefix. The900-second timeout, handoff
count, clock progression and geometry/physics settings remain unchanged.

The actual loaded Raft/WaterDetail/project module paths and hashes match the
normal installed binaries documented in the preceding rapid review. There is
no temporary module override. As before, the probe's hardcoded
`normal_project_binary_deployed:false` scope field is not a module inspection;
the independent live process witness supplies that evidence. This run uses the
explicit paired350s terrain/water preview and full shared-hull review, not a
saved/default-map promotion and not the ordinary FPS configuration above.

All five owned processes resume with status0 and subsequently increasing CPU
time, preserving their original process start identities. The same hydraulic
session40601 and SM5 session47178 are independently polled live after resumption.

Unmodified1280x720 screenshots at handoffs2,5 and8 were inspected. The initial
readiness screenshot does not yet show water; later5/8 captures show water and
raft progression but broad bare context terrain and unfinished crew appearance.
No visual, breaking/froth, initial-render readiness, calibrated terrain or
scene-completion gate is closed by the technical streaming pass. The actual
displayed-water model remains the legacy path; the nonlinear owner is still
diagnostic-only and retains unresolved physical gates.

Local replay evidence:

- Native result: `unreal/Saved/RaftSimValidation/south-fork-normal-installed-detail-isolated-v1-20260916-detail.json`, SHA256 `970335f1088f34a1fce5cab7a305266e26ca5a5d2eaec023b09716a143a43749`.
- Process recovery report SHA256 `298f3339c711e28e4d48511eccecdcc8209d93a5ef2646e54c37438486b59437`.
- Actual loaded-module witness under `tmp/normal-installed-detail-isolated-v1-20260916-modules.json`, SHA256 `b4838b0604b7e2ed37d53ce6ddb83a7f24a791b46232469a9fb51e906dd57525`.
- Complete replay log SHA256 `724f0dfbdf84b93010b42bb3e2707238221be7de94f2bc8ca7704c0f5976aba0`.
- Handoff5 screenshot SHA256 `03f5f23d22889a7fe65c9d085445a6a35ff9494e905c4fca4d47ea8a2b0442e6`.
- Handoff8 screenshot SHA256 `34df59b6d82bfd4878b88535283f62be4f720adbc9535ac2be77849979235f76`.

## 900-second hydraulic checkpoint

Both original audits pass at local step6000/absolute900 seconds: all5,382,400
cells are finite/nonnegative and all86,720 artificial-bank face cells remain
exactly dry. Maximum depth4.6595566867 m, speed9.2783864937 m/s, volume
3,027,189.131467 m3 and maximum step conservation residual1.287374e-8 m3.
Outflow61.258560 m3/s still exceeds inflow45.306955 m3/s: **not settled**.
This is not a default-scene promotion or calibrated bathymetry claim.

## Evidence identities

- Ordinary CSV SHA256 `afd74736a7431780b73262572370ef1ecb087fa9c6a19f256282df67397c2cba`.
- Ordinary frame audit SHA256 `f151937de5c881e96ab264b3815c924ed4b44b46cd6a5d4740ad8a662543984b`.
- Ordinary process report SHA256 `02fd63d6ee45e677097eda2b4b066755efd9071b7ec5706952fe321101ceb6e7`.
- Detailed stage log SHA256 `d32afed7d04a8c730017fd011039c6cf35b47566df90918d3b2ae37b7d63290a`.
- 900s state audit SHA256 `b3c58819aae0154c7433cae2441b5fa1f5b455867185ea8c0b31ac46426ec02f`.
- 900s exterior-bank audit SHA256 `6860849ffe74f3e115540b5c6736def838b3f1c4961ee2fdd3d117412feb513a`.

Actual engine visuals, integrated nonlinear physics, default-menu delivery,
sustained30 FPS, packaged-source closure and later river/crew/release work remain
open. Troublemaker remains only a rapid within South Fork, not a menu scenario.
