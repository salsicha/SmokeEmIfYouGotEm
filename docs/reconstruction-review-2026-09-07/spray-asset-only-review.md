# South Fork particle-only comparison

2026-09-18 UTC. **Not promoted; normal-play appearance is unchanged.**
The existing falling-particle pair does not establish a clear enough improvement
over the attached production spray. Broad blurred foam, smooth crests, isolated
spray patches and coarse banks/vegetation remain unaccepted. This is evidence
for the next change, not completion of South Fork or the ordered scene queue.

## Remove the confounded comparison

`-RaftSimSouthForkBallisticSpray` previously changed both Niagara assets AND
source selection/density from PresentationWeight to PersistenceWeight, forced
attachment even when its CVar was disabled, and implicitly enabled logging.
It now selects only the two pre-existing assets. Both runs use the ordinary
PresentationWeight, source attachment CVar, fifteen wet-footprint probes,
six-site pool, spawn formulas and horizontal source planes. Diagnostics require
the separate `-RaftSimSpraySourceAudit` flag. No asset, source data, material,
normal default, simulation step, quality setting or acceptance gate changed.
The non-South-Fork support-height branch is unchanged in effect; its obsolete
South-Fork-only conditional and misleading comment are removed.

Three negative controls reject changed presence, changed density and forced
attachment. These source checks do not prove visual quality or physics.

## Actual recordings

Both use the existing actual-game wrapper, FullReach/full descent station8330,
1280x720 D3D12, 24 startup PNGs and the ordinary moving gameplay camera. They
are separate runs, not bit-identical trajectories or synchronized particle seeds.

| Mode | Capture label suffix (prefix `south-fork-spray-asset-`) | Video in `unreal/Saved/VideoCaptures` | Decoded frames |
| --- | --- | --- | ---: |
| Ordinary attached spray | `baseline-v1-20260918` | `RaftSim_20260917-174250.mp4` | 469 |
| Existing falling pair | `ballistic-v1-20260918` | `RaftSim_20260917-174349.mp4` | 479 |

Baseline video SHA256:
`ce69a26d2145b5ccaac4574b2d043d0df48df5775ea2e034558d0a6fc1d61bd6`.
Candidate video SHA256:
`5a8c306f663d794f7bb39d7d0d3122f1f7ba4b8f1592c4cd108bce6efda7b204`.
Full decode reports: `tmp/spray-asset-{baseline,ballistic}-decoded-v1-20260918/report.json`.
Both decode completely through 15.6/15.933333s; encoded frame rate is NOT game FPS.
6/13-second decoded images and screenshot021 were visually inspected in both.
The candidate has smaller particle patches, but remains visibly tuft-like; this
does not resolve crest breakup or convincing surface froth. No default promotion.

Both process reports record exit 0, no timeout, successful cook suspension and
resumption. Baseline cook CPU advanced 0.140625s across the suspension boundary;
candidate CPU was unchanged. Decoder work overlapped candidate recording: these
are visual observations, not controlled timing evidence. No new FPS claim.
All five observed sites in each run are visible, wet-footprint checked, enabled,
horizontal and exactly anchored to their own visible centre, with 6/3/3cm emitter
offsets. Runtime geometry/intensity differ slightly between runs; no exact replay
claim. Centre offsets do not prove clearance under every source-plane point or
per-particle collision. Log confirms the candidate pair was actually selected.

## Reference and motion-space check

The [Qweniden bank-view reference](https://www.youtube.com/watch?v=2XTbOCNDcZQ)
was accessed in Chrome after normal ads. Inspected opening, 0:10 and 0:52 frames
show irregular white breaking edges, dark trough gaps, angular rocks and foam
moving through the reach. Playback advanced between observations; these sparse
samples are not continuous motion tracking, calibrated heights or bathymetry.
No remote footage was downloaded. The computer-use skill supplied the browser
inspection workflow. Reference footage remains qualitative provenance.

UE 5.8's installed `NiagaraStatelessModule_SolveVelocitiesAndForces.cpp` explicitly
transforms GravityScale/GravityBias from World space. Thus component launch
rotation does not rotate gravity sideways. The shared authored atlas inspected
locally contains multi-lobe clump images; the existing variant retains the same
atlas/frame selection. This suggests particle shape/source distribution need
attention, but is not proof that the atlas alone causes the visible tufts.
Next visual work must address crest breakup and advected foam structure, not
repeat this gravity/size-only swap or increase emission density to conceal them.

## Verification and limits

- Editor Development build succeeds in 170.90s:
  `tmp/spray-asset-only-build-v1-20260918.log`; existing C4701 warning at
  `RaftSimDetailSourceFootprintTest.cpp:105` remains.
- 73 Python checks PASS, including three new negative controls and rapid/menu
  separation: `tmp/spray-asset-only-tests-v2-20260918.xml`.
- Five native source/placement checks PASS, zero warnings/failures/not-run:
  `tmp/spray-asset-only-native-v1-20260918/index.json`.
- Two asset-readiness tests FAIL under NullRHI (only readiness assertions),
  preserved in `tmp/spray-asset-binding-native-v1-20260918/index.json`.
  The SAME tests PASS with D3D12, zero warnings/failures/not-run:
  `tmp/spray-asset-binding-native-d3d12-v1-20260918/index.json`.
  No assertions were removed. Exit 0 alone was not treated as passing.

No standalone rebuild, packaged/full-route qualification, new performance
measurement, full-physics acceptance or release acceptance is claimed. The last
ordinary profile remains 34.854890 FPS / p95 38.0726ms: FAIL30. Thirteen documented
physical-suite failures remain open. 6100/6150 hydraulic state AND dry-bank audits
pass but are NOT settled; normal water stays at 4950s. Colorado then Pacuare then
Futaleufu, all-scene water, crew, normalization, regressions and release remain open.
