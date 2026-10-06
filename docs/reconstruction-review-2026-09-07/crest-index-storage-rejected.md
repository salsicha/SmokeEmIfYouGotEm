# Crest index storage reuse rejected — September25

Tested a default-off double-buffered index array in the actual shoreline mesh
component. Each publication reset and fully rewrote the scratch indices, compared
them to the previous published indices, then swapped arrays. No topology, vertex,
height, solver, clipping, cadence or tolerance change was intended.

Editor build passed in146.58s. Initial NullRHI fine-crest test failed its actual
render-proxy assertions; this was an invalid rendering-test invocation, not a
pass. Preserved report: `tmp/crest-index-storage-native-20260925/index.json`.
The unchanged test rerun with D3D12 passed1/1, zero failures/not-run, exit0:
`tmp/crest-index-storage-native-rhi-20260925/index.json`.

Normal Boot/menu South Fork launch with compact-source reference audit recorded
64 exact comparisons and no mismatch reports, exit0. This checks complete
referenced vertex attributes, ordered triangle corners, ownership offsets and
crest corrections against the reference path, not visual realism.
Log: `tmp/crest-index-storage-live-20260925.log`.

Four separate clean launches had no paired-audit overhead. All used1280x720,
D3D12, WindowsEditor Development, ephemeral profile,300 post-travel CSV frames.
Each log confirms `csv.UseLegacyFrameTime=false`. The established analyzer uses
rows30–270 inclusive, offset1, unchanged30FPS/33.333333ms gate.

| Order | Mode | Mean frame ms | p95 ms | Mean SetMesh ms |
| --- | --- | ---: | ---: | ---: |
| 1 | Candidate | 24.040656 | 31.9658 | 5.734621 |
| 2 | Control | 23.271554 | 31.1728 | 5.403994 |
| 3 | Control | 22.353900 | 30.4828 | 5.182156 |
| 4 | Candidate | 23.746290 | 31.4982 | 5.707148 |

Report with exact CSV paths and hashes:
`tmp/crest-index-storage-abba-20260925.json`. CSV timestamps respectively
102719,102751,102821,102852 on20260925. All engine exits0. Candidate drift
samples show1.367m/s,wet1,support delta0,ground penetration0; these samples do
not prove continuous collision or full-route motion acceptance.

Both orders favor the original, including the affected mesh stage. Remove the
candidate and do not promote/repeat it unchanged. Source restored with a scoped
patch, not a worktree reset. No captured source, cooked field, packaged binary or
game asset changed. These short editor measurements do not supersede the last
packaged performance failure or establish river reconstruction acceptance.

Post-removal editor rebuild succeeded in77.27s, exit0. Both changed runtime
files have empty Git content diffs. Comparison report SHA256:
`32abd797be1d7c146e880827368e081ca7302a0f6188ea833d030a4f34ad3d09`.
