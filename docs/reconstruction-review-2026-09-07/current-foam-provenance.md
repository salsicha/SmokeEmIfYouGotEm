# Current South Fork foam provenance

Reviewed 2026-09-16 UTC. Diagnostic tooling only: no production material,
physics calibration, menu, or performance target changes.

The paired snapshot auditor checks transported density against resolved GPU
coverage, including depth and boundary taper, and binds the arrays with hashes.
It does not treat instantaneous source strength as accumulated foam history or
GPU coverage as final lit pixel coverage. The three normal-scene snapshots in
`tmp/south-fork-current-foam-audit-v1-20260915/foam-audit.json` pass the independent
resolve equation (maximum errors below 1.1e-7). Simulated GPU time lags elapsed
time; these captures are not a performance pass.

The read-only graph auditor targets the current playable material. The isolated
material builder duplicates that exact revision into ignored GeneratedLocalReview
content. Run with `-RaftSimCurrentFoamCoverageAudit` on the South Fork full-reach
map to display final optical coverage in red, GPU window ownership in green,
and resolved GPU coverage in blue, using the same surface carrier. Shipping
builds exclude the switch. The duplicate must be generated before using it.
Tone mapping prevents interpreting screenshot RGB as exact scalar measurements.

The first provenance run (v1) did not activate the diagnostic and is not valid
provenance evidence. The corrected v2 run explicitly logs activation and the
diagnostic material. Its inspected first capture shows GPU foam contributing to
the broad downstream band, with lower coverage on much of the upstream face.
This is not a visual improvement or realism acceptance. Previous optical
isolation findings remain relevant; deformation, breaking, and foam motion
still require work.

Verification:

- Editor build succeeded after the corrected map guard.
- 46 Unreal automation tests passed; zero failed, pending, or not run.
  Report: `tmp/south-fork-current-foam-native-v1-20260915/index.json`.
  SHA-256: `42a21bb6a3308258f5ca476b413a6224abd30437597db8437611f000cd797a70`.
- 17 Python tests passed across `test_detail_foam_snapshot.py`,
  `test_detail_mean_geometry.py`, and `test_detail_wave_regime.py`.
- All 464 protected asset hashes remain unchanged.
- Reports, snapshots, captures, builds, and generated diagnostic assets are
  already excluded by `.gitignore`; retain the reproducible tools in Git.

These selected tests do not establish whole-scene acceptance or resolve the
outstanding physical regressions. The target remains 30 FPS; no fresh ordinary
performance pass is claimed. Troublemaker remains a rapid within South Fork,
not a separate menu scenario.
