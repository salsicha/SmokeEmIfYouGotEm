# Captured rock XY correction — not visual acceptance

September 7, 2026. This is a separate, unaccepted South Fork candidate. It does
not replace the production scene or the previous playable survey baseline.

## Finding and implementation

The fixed-bank view with `raftsim.HideLiveOverlay 1` retains the stepped gray
foreground edge (`SurveyShoreNoCarrier_000.png`). That edge is terrain/rock
geometry, not whole water quads being culled. The source builder retained the
lowest supported LiDAR return's height but moved it to a regular raster-cell
centre. This discarded up to half a cell of measured horizontal registration.

`register_captured_rock_vertices.py` now produces a **mesh-only** candidate with
the same selected original returns at their actual XY. It does not invent new
boulder measurements or smooth the terrain. All recorded Z values and all
non-rock vertices are byte-identical to the preceding candidate. Interpolated
faces and the submerged bed remain explicitly inferred.

- 4,226 original rock returns: mean XY correction 0.197892 m, maximum 0.350932 m.
- 403,200 vertices / 803,842 triangles, no added presentation tessellation.
- 119 quad diagonal changes prevent folded triangles after registration.
- Minimum projected triangle area: 0.000702149 m². These thin triangles remain
  valid, but are not evidence of measured continuous vertical rock faces.
- Full-mesh barycentric audit: zero vertex error; maximum tested triangle error
  2.05e-12 m, including every triangle's centroid, asymmetric point and edge.
- 1,268 one-metre hydraulic cells change by more than 1e-7 m. Local bed changes
  range from -1.297829 to +1.542420 m on steep faces, so old flow is not reused.

`south_fork_geometry_source.py` and `south_fork_registered_mesh.py` explicitly
distinguish this irregular mesh from a raster. FBX export, hydraulic cooking
and runtime-package export use the same mesh identity and triangle topology.
Raster sampling is rejected for registered XY; legacy raster experiments keep
their original sampling and identity gates. Changed triangle connectivity is
included in the new mesh hash.

## Evidence and identities

Candidate: `tmp/south-fork-rock-return-xy-candidate-v2-20260907`.
Mesh SHA256: `4b0dfeac342607c118e91b2182fced676b4fc0c9ea08c2ff70e2166818255d40`.
The earlier `south-fork-rock-return-xy-candidate-20260907` is retained evidence;
it predates explicit nominal-axis metadata and must not be used by the sampler.

Fresh run:
`tmp/south-fork-survey-hydraulics/1m-mixed-inlet-registered-rock-xy-20260907`.
It uses the same bounded hydrostatic core, 1 m grid, 0.1 s timestep, CFL 0.2,
Manning 0.035, mixed inlet and uncalibrated 1600 cfs forcing as the baseline.
600 simulated seconds took 224.838 seconds wall time; 13 saved frames pass the
survey sanity screen. Maximum final exported depth is 2.465753 m. This is not
spatial convergence or calibration against instantaneous reference-video flow.

Mean-flow checks all pass: maximum tail section error 1.811%; three interval
storage derivatives +0.090769, -0.096506, +0.003576 m³/s; regional median stage
changes less than 1 cm. Numerical flux audit also passes: net +0.038501587 m³/s,
measured volume derivative +0.038500730 m³/s, no side-boundary leakage.
Reports are in the September 6 evidence directory under the unique suffix
`registered-rock-xy-20260907`; this is the existing review tool's output root,
not the date of the experiment.

FBX: `unreal/SourceArt/RaftSim/SouthForkRockRegisteredCandidate20260907`.
New map: `/Game/RaftSim/Maps/Review/SouthForkRegisteredRockPlayable`.
Map SHA256: `81f31bec7ba8683e3a7479f17333419b6d32eeb277de5630f098d41fdf705ad7`.
Mesh asset: `/Game/RaftSim/Environment/SouthForkRockRegisteredCandidate20260907/SM_TroublemakerSurveyCandidate`.
All 803,842 collision triangles are retained. 254 engine probes pass, including
interiors of all changed triangles; maximum height error 0.0020833 cm.
See `registered-rock-engine-integration.json` and `rock-xy-mesh-audit.json`.

Original map SHA256 remains
`2c53df655cd7fa83a232f40f951c4babcdc34adbd3fb7aafda8db270b64969bd`.
Native archive remains
`d91b779b83c6b32d25518d4a284ed757d175758e2342a3b3649367b925a64155`.
Focused pipeline regressions: 44 tests and 33 subtests pass; one pre-existing
affine/matrix PendingDeprecationWarning. See `registered-rock-pipeline-tests.xml`.
Built-engine `SouthForkRegisteredRockCandidateReplay` and unchanged baseline
`SouthForkDepthLimitedCandidateReplay` both pass without test warnings. See
`engine-registered-rock-replay/index.json`. These are two-second bounded runtime
replays under NullRHI, not rendered motion, traversal, or performance acceptance.

## Actual engine comparison and limitations

The generic `EditorAssetLibrary.duplicate_asset` approach crashed UE's old-world
GC check before the candidate was saved/imported. Original map hash unchanged;
no candidate map/mesh file remained. `StageRegisteredRockReview.log` retains
the failure. Staging now uses `LevelEditorSubsystem.new_level_from_template`;
the successful attempt is `StageRegisteredRockReviewTemplate.log`.

First game captures `SurveyRegisteredRockBank_000.png`–`011.png` had unmatched
presentation: the opt-in breaking review recognized only the original map and
its old field packages. Do not treat those images as a shader/geometry A/B.
The explicit map/package allowlist now includes the new registered-rock pair;
no default or production map is enabled by this change. Both builds succeeded.

Matched captures: `SurveyRegisteredRockMatchedBank_000.png`–`011.png`, at fixed
station/lateral (0,0), requested 0.1-second intervals after 10-second warmup.
Frames 0 and 11 were actually viewed, alongside baseline
`SurveyCurrentNormalV2Bank_000.png`; this is not continuous playback acceptance.
The log verifies the V2 current-normal material, shared relief, lit foam and
one surface carrier (10,465 vertices, 1.5 m spacing, 3 m analysis spacing).
Maximum sampled shared relief is 0.4012 m, not measured breaking-wave height.

**The local rock edge changes but still has an angular outline. Foam remains
too smooth. Neither shoreline nor water realism is accepted.** Registration
alone does not supply missing submerged rock contours, actual crest geometry,
or a stateful breaking-fluid layer. New-map guided traversal and settled
performance have not been tested. Existing frame/solver-budget failures and
the previous guide's 5.10 m route-error failure remain open.

No production promotion, final commit or queue completion is claimed.
