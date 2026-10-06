# Crest length and reference check — September 25 UTC

Supporting evidence, no playable change or river acceptance.

Using ordinary browser playback, revisited Qweniden's video titled
[Trouble Maker South Fork American River 7/15/2022 — Raft California](https://www.youtube.com/watch?v=2XTbOCNDcZQ).
Inspected separate states during playback from0:02 through paused0:18 of3:24:
localized steep whitewater fronts, intervening darker water, a raft entering
whitewater and a later downstream view. These are sampled observations, not
continuous frame analysis, surveyed wave dimensions, calibrated discharge or
proof of reuse licensing. No video downloaded or incorporated into assets.
The existing staged game frame `staged-troublemaker-motion-20260924_004.png`
still shows broad pale smooth faces; viewpoints differ, so this is qualitative.

Current source computes crest length as clamp(3*depth,2,7)m and uses static
asymmetric crest/toe/tail envelopes. Stateful detail retains0.06m turbulent
pressure head. These remain presentation/closure choices, not measurements.
Earlier foam-only changes are already rejected; do not repeat them.

A new staged normal Boot/menu FullReach run, requesting review station8330,
completed exit0. Existing crest sampling audit at about10s reports5sites:
lengths2.640558,3.151823,3.699129,2.000000,4.023316m. Only1/5hits the lower
bound; the strongest height0.618268m belongs to the2.640558m site. It alone
has positive spilling fraction0.0731303; the other four report zero. Changing
the2m minimum is therefore not supported as a blanket fix for these sites.

The old regular-grid comparison reports0.139462m error, but the actual submitted
Cartesian-mesh audit reports1.107960cm target error across1,161,612samples,
0.001819cm fine-correction tracking error, and zero source-vertex change.
Do not misreport the coarse comparison as the actual renderer's error or
increase tessellation to hide missing physical crest dynamics.

Evidence: `tmp/troublemaker-crest-length-20260925.log`, corresponding `.json`
and `.json.cartesian-mesh.json`. Capture uses the retained v7staged executable;
no full-hull solver or experimental water mode enabled. Timing from this
diagnostic is not a performance comparison.

The initial log ambiguously says no checkpoint near8330m and starts the section.
Follow-up source inspection established that a review deliberately bypasses
saved checkpoints and constructs its pose at the requested StartStationM; this
was not a fallback to the river beginning. The message now distinguishes these
paths and reports the applied pose only after successful streaming/wetness and
raft restore. No relocation, hydraulic or collision logic changed.

Editor build succeeded32.31s. New normal Boot/menu FullReach120post-travel-frame
run exited0; `tmp/review-start-applied-20260925.log` reports requested and
sampled station8330.000m, sampled=1, world centimetres
(-541798.327843,-359800.000000,715.413513), destination error0cm. Thus the new
run verifies this review-start path. It does not retrospectively supply missing
pose telemetry for old captures, register the video camera, validate complete
traversal, or establish the wave geometry as measured. No bed, rock, material,
solver or captured-source edits.

Native follow-up:3/3successes,0test warnings/errors/not-run, engine exit0:
`RunProgressDistinctFromRapidHydraulics`, `ReviewCameraUsesScenarioDownstream`,
`ReviewStartUsesScenarioRange`. Report:
`tmp/review-start-regressions-20260925/index.json`.
These cover coordinate separation, camera frame and review bounds; the actual
normal-menu run above separately verifies successful applied relocation.

## Breaking-onset interpretation follow-up

The current `smoothstep(1.28,1.7,upstream_Froude)` spilling fraction is a
presentation closure, not a site measurement. The primary experimental abstract
of [Ohtsu, Yasuda and Gotoh (2001)](https://www.tandfonline.com/doi/abs/10.1080/00221680109499821)
reports dependence on inflow boundary-layer development: limiting Froude values
range from 1.3 to 2.3 for developing inflow, versus approximately 1.7 for fully
developed inflow in their smooth rectangular channels. Those conditions are not
established for this natural rapid. Therefore neither this paper nor the five
runtime sites establishes that a zero spilling fraction is a software error;
lowering the threshold to whiten every crest would be unsupported.

Next physical calibration needs registered local flow/depth, crest and approach
geometry plus an appropriate breaking criterion, not more tessellation or a
uniform foam multiplier. This literature check supplies no new measured South
Fork coordinates, bathymetry, discharge or license to redistribute paper/video
assets. It does not change the playable water or qualify its appearance.
