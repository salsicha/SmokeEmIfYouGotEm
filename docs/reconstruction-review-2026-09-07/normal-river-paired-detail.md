# Paired GPU detail and raft contact — September 12

Normal moving Cartesian water now separates the simulation's candidate texture
from the existing presented texture. A three-slot nonblocking GPU readback ring
copies complete resolved frames, including their own registration row and
simulation clock. A monotonic mailbox rejects stale completions. Once per game
frame, the newest completed payload is uploaded to the existing visible water
texture and retained for CPU support. Busy slots hold the last paired frame;
they do not wait or stop the PDE. Legacy fixed-review rendering is unchanged.

Support evaluates this registered detail at each submitted triangle vertex,
then uses the same barycentric interpolation as the rendered triangle. A
bilinear detail query at a hull point would not reproduce vertex displacement.
Raw solver wetness, depth, bed, velocity and D3 are unchanged. This adds neither
a second visible water sheet nor a separate Troublemaker scenario.

The opt-in carrier contact audit records the presented sequence and requests a
GPU parity audit against the actual uploaded texture using the material's
registered sampling helper. Both reports must name the same nonzero sequence.
Agreement with CPU payload alone is not proof of GPU upload correctness.
Queue age, holds, busy-copy skips and PDE backlog are separately logged. Full
render-frame latency, clean traversal and visual realism are not established by
these numerical checks. The existing DetailSnapshot diagnostic now reads the
simulation candidate, NOT the older paired presented frame.

## Native verification

First build10512 failed on a TSharedRef/pointer mismatch in the new GPU test.
Corrected build60812 succeeds51.75s. First engine test72306 then aborts on a
render-thread assertion in the test's buffer Lock; its log and incomplete
report are preserved as failure evidence. The production ring and parity
audit already perform these operations on the render thread. The test is
corrected to do the same, with finite-value checks; rebuild3896 succeeds18.86s.
Final engine7723 exits0:59 tests pass, zero failed/warnings/unrun/inprocess.
Report `unreal/Saved/RaftSimValidation/south-fork-paired-detail-regressions-v2-20260912/index.json`.
The new real-GPU fixture compares286 queries after production-ring copy,
candidate overwrite and reupload: maximum RGBA error1.86264515e-9. It includes
registered far edge/outside coordinates, padded rows, monotonic sequence and
immutable ownership. CareerCatalog and ProgressionMigration also pass.
Actual-map, visual and performance findings follow below.

Pre-counter binary SHA256 (used for the v1 motion capture and profile):

- Raft `3c225e1fab00168196570baaa9b5aeb511e082e09f538025e769d694b26d6a4f`.
- Water `73b9b5422e83e8c8260e72a41a8b919be8836f907816bdc5be5f51aed42d15ab`
  (only explanatory comment changed in this module).
- Main `b2b68080bd72166940660a8e40a99d36ebbd7763cfab91f96ae6ee32d74b2f5a`.

Mapdb3080cc…, materiale4e9b2f3… and save181d1e57… independently rehashed
unchanged. Scoped diff whitespace check passes; no user data removed.

Previous baseline:58 tests pass, CPU-only contact error0.000047673cm;
19.212411FPS/p9569.0773ms FAIL60. Broad rounded wave and thin froth remain
visually unaccepted. Source terrain/material/map are unchanged by this work.
Hydraulic continuation96057/PID29104 remains live:2200s passes independent
state and artificial-bank checks, still unsettled, runtime600s unchanged.

Next: physical breaking/froth, larger crest/publish/GPU costs, warmed
presentation-latency measurement, terrain/collision traversal and all remaining
work. The completed checks below do not close those acceptance gates.

## Actual playable map and timing

Game14048 exits0. Carrier contact and actual uploaded-GPU reports BOTH use
sequence106.2,021wet triangle probes, zero unavailable/dry, maximum contact
error0.000047576327cm and RMS0.000023775573cm. Actual GPU4,226queries maximum
RGBAerror5.960464478e-8, maximum sampled detail4.376366615cm, passed.
Reports `tmp/south-fork-paired-detail-{contact,gpu}-v1-20260912.json`.
Additional counters explicitly report how many contact probes receive nonzero
detail (avoid mistaking an off-window-only sample for an integration pass).
Counter-only build13533 succeeds49.85s.
Final suite81225 exits0:59successes, zero warnings/failures/unrun/inprocess,
`unreal/Saved/RaftSimValidation/south-fork-paired-detail-regressions-v3-20260912/index.json`.
Final RaftDLL SHA256
`c8a9d9b3b869f02d02e144086f9520fc3ffbee6fcc3e6b2fd4bb6fdcb1d07936`.
Water/main remain the above hashes. Only opt-in audit counters changed after
the profile, not gameplay calculations.
Final actual game34431 exits0. Reports
`tmp/south-fork-paired-detail-{contact,gpu}-v2-20260912.json` BOTH use sequence107:
953of2,021wetcontactpoints receive nonzero paired detail, max3.525609326cm.
Maximumsupporterror0.000047668113cm,RMS0.000023726602cm; zero dry/unavailable.
ActualGPU4,226queries maxRGBAerror5.960464478e-8, maxsampledheight3.663621902cm,
passed. This verifies nonzero detail integration, not only off-window probes.

Crest1,550,016samples maximum0.600614003cm<=2cm, fine tracking0.000297427cm,
source vertex change0. UV3 transport/UV1bulk errors0. Reports use the same
prefix with `crest` (append `.cartesian-mesh.json`) and `transport`.
Motion report `tmp/south-fork-paired-detail-motion-v1-20260912.json` confirms
40uniquePNGs/11.779game seconds, fixed camera. Frames000/039 inspected:
smooth central wave and thin froth remain UNACCEPTED. Movie175006 has86source
frames/16.456s, not continuously viewed and not FPS. SHA256
`fc0a50e7ebf1f1232df2a8a94dd7897b1235fbfd40b9fd7b9b3cddc3a499eba8`.
Heavy capture192commits/1hold, lastsequence192,194candidates,0busy skips,
maxqueueage.4s, PDEbacklog4.777625s,3exactremaps/0teleports.

Isolated profile53952 exits0/no timeout, exact cook29104 suspended/resumed0.
1280x720,300CSVframes, warmed indices100..250:20.206351FPS,
mean49.489390ms,p9561.1501ms, GPU13.430089ms, crestupdate16.350859ms,
inclusiveCartesianpublish23.434938ms. Still FAIL60. Prior19.212411FPS;
variable trajectories and different binary prevent sole-cause improvement
claims. Report `tmp/south-fork-paired-detail-performance-v1-20260912.json`;
CSV SHA256 `71357765c9b2fcd9466f9ab298b209ce6cc47ef5cb0953903a5bfba95e41f3fa`.
Ordinary run631commits/1hold,633candidates,0busy skips; maxqueueage.4s includes
startup/final capture, not a warmed latency percentile. PDEbacklog.006724s,
7exactremaps/0teleports,34.041668sim seconds. Flow preparation1.407065ms/update.
No GPU waits were introduced, but total render-latency acceptance remains open.
