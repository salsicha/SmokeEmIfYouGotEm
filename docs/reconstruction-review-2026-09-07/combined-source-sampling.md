# Combined South Fork source sampling

2026-09-17. Normal South Fork FullReach now combines the live sampling and
baseline handover passes. A stack-owned cache retains one baseline result per
vertex per refresh, including dry and failed results. It never survives a
refresh or source change. Other scenes retain their existing schedule;
`-RaftSimSeparateSourceHandover` provides the original comparison path.
No solver equations, timestep, quality, terrain, materials or water state changed.
Troublemaker remains a rapid within South Fork, not a menu scenario.

## Evidence and limits

Two independent actual-game captures each compare eight alternating-order pairs
on one frozen state of 50,625 samples. All 16 pairs preserve every sampled field,
mask, probe request, feather value and height exactly; all reduce this stage's
cost. Median separate/combined times are 3.427450/2.661051 ms and
3.550649/2.702100 ms, respectively. These are two states, not 16 distinct states.
Local records: `tmp/fused-source-same-input-{a,b}-v1-20260917.json`.
Diagnostic audit overhead is excluded from performance acceptance runs.

Audit-free reference/combined/combined/reference frame p95 values are
40.1357, 36.5258, 37.5363 and 37.2385 ms. The second comparison is worse overall;
there is no claim of repeatable whole-frame improvement. The component is
retained for its exact same-input stage reduction, not a global FPS result.
Record: `tmp/fused-source-abba-v1-20260917.json`.

The final default-path capture averages 37.070557 FPS, with p95 36.3204 ms:
**FAIL30**, against the unchanged 33.333333 ms limit. It uses 1280x720 D3D12,
300 CSV rows and the fixed inclusive 60..240 measurement interval. It is not
a sustained, packaged or full-traversal acceptance test. Record:
`tmp/fused-source-installed-profile-v1-20260917.json`; source CSV SHA256:
`0ccc7e7e650d0e85f5ee96dcd8da0c4453669922d8c77d70d06fb09ecf4872b7`.
On the combined path, SourceSamples includes both passes; SourceHandover times
only its already-completed guard. The auditor explains this without changing
thresholds, parsing or duplicate-header rejection.

Installed editor and standalone Development builds succeed. Eight focused
native tests and 98 Python tests pass, including cache lifetime, dry/failed
results, source packing, shoreline caches, scenario launch and runtime-contract
negative controls. Records: `tmp/fused-source-installed-native-v1-20260917/index.json`,
`tmp/fused-source-installed-python-v1-20260917.xml`, and
`tmp/fused-source-game-build-v1-20260917.log`. This does not close previously
recorded broader-suite failures or constitute a rebuilt/accepted cooked package.

The final ordinary gameplay recording was fully decoded and frames at 3 and
11 seconds inspected. Broad soft froth and insufficient rock/vegetation detail
remain unaccepted. No full-video viewing or new reference-video review is claimed.
Video: `unreal/Saved/VideoCaptures/RaftSim_20260917-152546.mp4`, SHA256
`0c6f161cbf502030f73355fbe98a3d8fbf641018f8410695e34cbe25ba1cb77f`.
Breaking-wave realism, contact/physical qualification and the ordered remaining
scene, crew, regression and release work remain open.

Generated reports, recordings, logs, binaries and native build products stay
local under existing `.gitignore` rules; this note retains the evidence summary.
