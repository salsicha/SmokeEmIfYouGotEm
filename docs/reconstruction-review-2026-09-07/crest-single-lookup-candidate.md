# Crest assembly single-lookup candidate — September25

Current packaged baseline SHA256
`51325df13f47b5d33d5232a206df7c3db9a912eca5b3cc1f36a40c551d3ed39a`.
Normal Boot/menu travel with existing stage instrumentation completed300
post-travel frames and closed its log. No physics/scene settings changed.
The existing fail-closed analyzer requires complete ordered frames200–400
and matching vertex subdivisions:201 calls,73 rebuilt and128 retained.

Mean crest call cost4.574654ms; rebuilt8.898142ms versus retained2.108914ms.
All73 rebuilds changed XY without changing the continuous profile.
Rebuilt selection3.804411ms contains sampling0.806284ms and assembly2.155600ms
(nested scopes, not additive). Rebuilt target work1.627410ms and normals1.604916ms.
These instrumented results identify assembly as a target, not ordinary FPS.

Log `tmp/current-packaged-crest-stages-20260925.log`, SHA256
`ccf73415abadd7731586f76fa9d427b3ea6be5cb7fb3a70d7d0e95f46fed5993`.
Report `tmp/current-packaged-crest-stages-20260925.json`, SHA256
`c797c24840b09a1baeecf280c3646090c0578a26e756f8ddceeaec1808810dfb`.

The candidate uses FindOrAdd with INDEX_NONE to eliminate the duplicate lookup
for newly inserted midpoint edges. Existing vertices use nonnegative indices;
original insertion/triangle order is retained. The original Contains/Add path
remains default. Normal game code does not enable the candidate. The native
topology-cache test compares candidate indexed insertion against original
indexed insertion and serial map assembly over changing positions, heights,
selection masks, root winding and subdivision levels.

Editor build passed145.36s (two existing Chaos-runner float-conversion warnings).
Native `RaftSim.WaterDetail.RefinementTopologyCache` passes1/1, engine exit0:
38,416 current vertices compared,25 cached builds,33 reuses and58 fresh builds.
Report `tmp/crest-single-lookup-native-20260925/index.json`.

Pending qualification: alternating-order actual-input
whole-build timings including cache misses, normal frame cost and rendered
motion. No production promotion or water/river acceptance. The installed
packaged executable is unchanged by this experiment.
