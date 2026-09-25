# Current normal South Fork follow-through — September25

After the crew review-code rebuilds, the current editor-hosted game was checked
through normal Boot/menu travel, not a direct map or review-only river scene.
No engine/cook job was active before launch. No experimental boarding, calf-fit,
solver or crest flags were supplied. Ephemeral profile, D3D12 offscreen,
1280x720,300 post-travel CSV frames; engine exit0.

Log: `tmp/south-fork-current-normal-20260925-2145.log` confirms
`L_RaftSimBoot` -> `L_SouthForkAmerican_FullReach` and
`csv.UseLegacyFrameTime=false`. Report:
`tmp/south-fork-current-normal-cost-20260925-2145.json`.
CSV: `unreal/Saved/Profiling/CSV/Profile(20260925_144803).csv`, SHA256
`31372a215d4d2a4f666c4efacd5b70ac4876cd87d447570e30362ce968b78a38`.
Established analyzer: rows30-270 inclusive, scope offset1, water scopes required.

Frame mean26.990518ms, p95=37.5728ms: FAIL against33.333ms. Mean game-thread
26.692312ms, render-thread14.192306ms, GPU9.356864ms. Inclusive mean water Tick
14.490037ms, CartesianPublish7.854925ms, SetMesh6.297801ms, Refresh5.980946ms,
StepWater4.460866ms and Crests3.998781ms. Do not sum nested or overlapping times.
Refresh appears in84/241 samples and averages17.159620ms on those positive rows.
This remains a water CPU-cost problem; a short unpaired run cannot attribute
the difference from older measurements to any recent edit.

Actual sampled raft motion: speed1.368m/s, water1.135m/s, wet1, support delta0cm,
ground penetration0m. These sparse telemetry values do not establish continuous
collision, shoreline/appearance acceptance, rescue motion or full-river traversal.
No images were captured in this timing run. No packaged executable was restaged.

The known batched-normal optimization remains rejected; no unchanged candidate
was rerun. Continue reducing measured water publication/refresh cost without
lowering spatial resolution, update cadence or acceptance thresholds. Geometry,
source evidence, installed cooked fields and the later-river queue are unchanged.
