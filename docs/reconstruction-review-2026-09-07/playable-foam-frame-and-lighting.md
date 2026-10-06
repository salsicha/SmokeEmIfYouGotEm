# Playable foam transport frame and surface-lit optics

September 12, 2026 UTC. Incremental normal-game delivery; not completed South
Fork reconstruction. Entry: **Troublemaker Rapid Challenge**, map
`/Game/RaftSim/Maps/L_SouthFork_Troublemaker`. Full-route migration, other rivers,
crew, remaining realism/performance work and release/final commit remain open.

## Geographic-frame bugs corrected

The persistent foam backtrace used `(-tangent.y, tangent.x)` as source-left in
world space. That is only correct for a positive world-Y convention. The
captured map reflects ENU north into Unreal −Y, so this projected cross-river
velocity with the opposite sign. The water adapter and global lace-advection
integral already used the correct reflected basis; the foam-density field did
not. A source-left current of +0.85 m/s became −0.85 m/s in that backtrace.

`RaftSimFoamTransportFrame.h` now supplies the source-left basis multiplied by
the map's world-Y sign. The actual persistent-foam callsite uses it. The same
missing sign affected conversion of station/lateral surface slopes into world
shading normals and the procedural mesh's tangent-space bitangent; both are
corrected. Reflected winding was already handled separately and remains intact.
Positive-Y maps retain their existing basis. No force, terrain, hydraulic array,
vertex-height or raft-support equation was changed by these frame corrections.

Native regression `RaftSim.Water.FoamTransportGeographicReflection` exercises
four river directions, five flow vectors and both world orientations, checking
velocity/backtrace parity, source-surface derivative normals and the UV
bitangent. The existing `RaftSim.Survey.GeographicHandedness` also passes. These
tests prove their scoped frame contracts, not hydraulic calibration.

## Shared foam optics on the normal carrier

A read-only audit of the actual saved `M_TroublemakerWater` found the inherited
overlay-era multiple foam masks, separate drift/solver optical paths and
emissive output. It was not the recently updated FullReach V4 material.

The normal captured material now uses `RaftSimCapturedFoamOptics.hlsl` to map
the already transported vertex-red foam through continuous optical extinction
and one existing current-advected lace. Color, roughness and specular share this
response. Zero foam or zero optical density produces no whitening. Speed and
depth are not additional foam sources. Emissive output is explicitly zero, so
foam receives actual scene lighting. Optical density (3), foam roughness (.72)
and foam specular (.25) are appearance choices, not measured void fraction or
fluid parameters. Original water-depth color and reflected-sky inputs remain.

The material's opacity/wet-bank/raft-hull graph, ripple-normal graph and empty
WPO root are unchanged. This statement is about the material graph: world-space
mesh normal/tangent orientation changed as described above. The map, captured
ground mesh, staged hydraulic fields and single-carrier ownership are unchanged.
No extra foam sheet, GPU liquid experiment or new physical source was enabled.

Material SHA256 changed from
`2116ce61b4aa0af240bda57b6ae62fabe146f7cbd413f39e834b2532358501f5` to
`0b13bf122ea85264b219c536c61067a6c31597e5b438e6b66e844d01a2e8a864`.
The original is retained byte-identically at
`tmp/troublemaker-foam-material-backup/2116ce61b4aa0af240bda57b6ae62fabe146f7cbd413f39e834b2532358501f5.uasset`.
The canopy map stays SHA256 `743a420632a767a78b56779705e394091c94a6f0ad2cdb04a5be3f60ca25f862`.

## Verification

- Builds 35022 and 11098 passed in 33.94 s and 33.11 s.
- Read-only actual-material audit 88992, material installation 54001 and
  fresh-load graph audit 20585 passed. Fresh audit checks the three optical
  consumers, zero emission and exact protected graph signatures.
- Native test run 21423: two successes, zero warnings/failures/not-run.
  Report: `unreal/Saved/RaftSimValidation/playable-foam-frame-tests-20260912/index.json`.
- 39 focused Python functions passed, including five new shader/zero-foam,
  monotonic-response, real-callsite and reflection-regression functions.
- Normal `-game` run produced 12 moving raft-attached captures. First/last were
  inspected: discrete foam patches and the downstream frothy patch are clearer.
  The water still has broad smooth areas and coarse patch edges; rock sides,
  tree morphology and real breaking shape are not accepted.
- Full playable traversal 52602 passed with the existing
  `r.MotionVectorSimulation` warning: 64.917 s, station −55.515→110.069 m, max
  route error 3.744 m under the unchanged 5 m limit; 568 wet samples, zero missing
  ground queries/grounded samples, minimum tube clearance 32.926 cm. All 2,272
  fixed water queries succeeded; shared carrier/support, material coverage and
  native progress held. Maximum hull-alpha submission error .001772 remains
  below 1/255. Thirteen station captures exist; frame004 at the crux was inspected
  and visibly has more froth, but does not pass real-footage physical realism.
- Separate normal-game performance run is terminal: 10 s warmup, 12 s sample,
  1280×720 at 87% screen percentage, 732 frames, no screenshot writes. Mean
  frame 16.476 ms, p95 24.018 ms, mean GPU 7.360 ms, mean solver 8.681 ms.
  **Frame and solver gates still fail**. This is an offscreen engineering
  diagnostic, not packaged release qualification. Report:
  `unreal/Saved/RaftSimValidation/troublemaker_lit_foam_perf_20260912.json`.

Primary artifacts under `unreal/Saved/RaftSimValidation/`:
`playable-troublemaker-optics-20260912.json`,
`playable-troublemaker-foam-setup-20260912.json`,
`playable-troublemaker-foam-fresh-20260912.json`,
`troublemaker-lit-foam-traversal-20260912/index.json`.
Traversal samples: `unreal/Saved/Automation/SouthForkGuidedTraversal_20260912_021428.json`.
Images under `unreal/Saved/Screenshots/`: `troublemaker_lit_foam_playable_20260912_000.png`
through 011 and `SouthForkGuidedTraversal_20260912_021428_000.png` through 012.

## Hydraulic shape remains the next priority

The first runtime breaking-site diagnostic reports a .022 m strongest crest,
but site publication multiplies height by a startup persistence envelope. This
is **not** a settled maximum or proof of the cause of missing wave shape. Do not
amplify crests based on that initial line. Use the existing ten-second
`RaftSimBreakingHeightAudit` to inspect source rise, Froude, inferred extra crest
and bank acceptance after startup; this flag only reports, it does not change
the normal gameplay configuration. Keep actual carrier/support geometry paired.

A read-only check reverified all five staged-array hashes. For wet cells at
least .05 m deep and lateral ±25 m, the initial cooked crux (stations −15..20 m)
has median/95th-percentile Froude .263/1.275, maximum 3.158, with 9.74% of those
cells supercritical. Those are model-state diagnostics, not surveyed flow or a
proof of the real rapid. They show that the source contains a localized fast
region worth tracing through the settled detector and rendered mesh. The
underwater bed remains inferred. Brighter foam does not close this work.
