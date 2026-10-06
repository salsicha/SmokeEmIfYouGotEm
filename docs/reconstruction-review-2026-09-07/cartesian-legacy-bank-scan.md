# Cartesian legacy bank scan — September25

Removed one unused full-grid presence scan from the normal Cartesian water
refresh. MinPresentY/MaxPresentY are consumed exclusively by the non-Cartesian
bank reach/collapse branch; that branch retains the original scan. The
`RaftSimLegacyCartesianBankBounds` flag restores the scan as a same-binary
control. Source samples, wetness, topology, geometry, physics, materials and
solver settings are unchanged. No cook was started.

Editor build passed50.41s; Game build passed108.06s. Four offscreen editor-game
runs used the ordinary Boot/menu StartScenario route, no direct-map override,
1280x720 and300 post-travel frames each. FrameTime mean/p95 (nearest rank):

| Order | Scan | Mean ms | p95 ms | CSV under unreal/Saved/Profiling/CSV |
|---|---|---:|---:|---|
| 1 | skipped | 26.6312 | 36.2985 | Profile(20260925_083429).csv |
| 2 | original | 24.0771 | 31.7368 | Profile(20260925_083535).csv |
| 3 | original | 22.4568 | 31.1317 | Profile(20260925_083835).csv |
| 4 | skipped | 22.0168 | 30.5564 | Profile(20260925_083923).csv |

All four processes exited0. Order-dependent warm-up variation exceeds the
likely saving; these measurements do not establish a reliable FPS improvement.
The retained source change removes provably unused calculations, not geometry
or quality. Full-route performance acceptance remains open.

The normal v7 stage executable was replaced only after preserving and verifying
its original SHA2565246445253bdca36b1076643235ab21639d5b6ba719cfb585d51e4d4e3d1ad85
as `SmokeEmIfYouGotEm-pre-bank-bounds-20260925.exe` beside it. Installed rebuilt
SHA25651325df13f47b5d33d5232a206df7c3db9a912eca5b3cc1f36a40c551d3ed39a.
Cooked content was not modified.

Packaged normal Boot/menu travel also completed300 post-travel frames. World10s
telemetry: raft1.367m/s, wet1, ground_points0, ground_penetration_m0,
support_delta_cm0. No Error:/Fatal matches. The process is absent and engine
requested exit status0; OS exit code was not captured for the GUI executable.
Log: `tmp/cartesian-bank-bounds-packaged-20260925.log`.
Stage CSV: `SmokeEmIfYouGotEm/Saved/Profiling/CSV/Profile(20260925_084053).csv`.
Packaged mean24.93ms/p9534.63ms still fails33.333333ms.

This is normal-play dead-work removal, not a visible reconstruction improvement.
No new shaded-motion comparison, crest/shoreline acceptance, full collision
traversal or real-reference geometry acceptance is claimed. South Fork remains
unfinished; later rivers remain queued.
