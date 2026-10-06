# Later-state South Fork playable comparison

September 16, 2026. **Visual, physical, default-scenario and 30 FPS acceptance
remain open.** This is an actual playable comparison, not a finished rapid.
No saved map, material, mesh, solver setting or acceptance threshold changed.

## Corrected hydraulic checkpoint

The same corrected-domain process (session72710 / PID4608) reached absolute
1700 seconds, local step1000. All5,382,400 cells pass finite/nonnegative state,
depth/speed and conservation checks. All86,720 artificial-bank face cells are
exactly dry; the earlier-domain1700 failure is not reused or relabelled.
Maximum step conservation residual is1.234195e-8 m3. Outflow90.210308 versus
inflow45.306955 m3/s means this is still **not settled**.

- State: `tmp/south-fork-context5-1700-snapshot-v1-20260916.json`,
  SHA256 `663acc15ea991b6afd3f9bd09379d2998945c5d8ce6def0ac93ab79e46a0fd5e`.
- Banks: `tmp/south-fork-context5-1700-banks-v1-20260916.json`,
  SHA256 `e24a04b8ef7d766c6ee66be0cc338d0f47815cf95a973c46adfcba4300544823`.

The same process continues toward1750/1800; next local2000 requires BOTH
audits. Do not restart it on an observation timeout.

## Source-matched runtime and native checks

Prepared799 compound source packets for the corrected841-tile domain. Eight
packets contain the unchanged rock union;791 are reused only after decoded
bed/mask equality checks. The export verifies42,185,039 overlapping bed samples.
All406,823 original-water probes retain a complete runtime crop, with minimum
raft margin10 m. The existing coverage repair removes an invalid center range
in region0002; it does not discard original-water probes or change the margin.

Export: `tmp/south-fork-landward-runtime-1700s-v1-20260916`.
Atlas SHA256: `5e819668b892e4cb89b5fee38ea32b74352528e418e55d5370b3776405e77616`.
Native read-only actual-map verification passes all30,403 union/collision
queries and12,800 initial-water queries; zero wet-mask mismatches. Height
errors <=7.629395e-6 m, depth error <=1.192031e-7 m, velocity errors
<=2.323139e-7 m/s. No solver advance, asset import or save occurs in this check.

Native report:
`unreal/Saved/RaftSimValidation/landward-1700s-saved-union-v1-20260916.json`,
SHA256 `abde7414f6dbd2e5a61c5c4036aa815a2f9556748605a6e5c2bee233b3da1019`.
The fresh joint preview binds3263 dependencies, unchanged saved rock and the
new state: `tmp/landward-1700s-joint-preview-v1-20260916.json`, SHA256
`d165e9cfb027b8719e0094783157d42c0ffa06406fcdaa7401b78dc7e061b3a2`.

On the same12,800 collision-cell coordinates, the50s and1700s expectation
arrays have bit-identical beds. Across3740 cells wet in either state, depth
change median is+0.238244 m, range[-0.479504,+0.743926] m; velocity-vector
change median0.521245 m/s. This comparison is source state, not game motion.

## Actual engine and reference comparison

The [Qweniden Trouble Maker bank-side video](https://www.youtube.com/watch?v=2XTbOCNDcZQ)
is accessible. Inspected paused frames0:09 and0:19 show fractured/angular rock
faces, distinct drops and darker gaps between foamy patches. Do not infer
surveyed dimensions, flow or matched camera registration from these views.
No reference video was downloaded. Arbitrary rounding of the game's rocks is
not justified by this reference; original returns and inferred walls remain
distinct provenance classes.

Actual FullReach `-game`, D3D12,1280x720, `south_fork_full_descent`, station8330,
ephemeral profile, full-hull/shared-hull flags and the fresh descriptor above.
The same camera is(-545900,-362700,2000) cm, pitch-35.27,yaw46.85,FOV90.
`RaftSim.CaptureSeries 12 3 10 landward-1700s-playable-v1-20260916 -545900 -362700 2000 -35.27 46.85 record`
records installation before BeginPlay at source1699.999999999 s. Captures at
world12.595/22.383/32.201 s reach station8354.029 m. Both logged hull/render
checks have zero position error; no contact-refusal/latch entries occur. This
short traversal does not qualify full-river contact.

Log: `tmp/landward-1700s-playable-v1-20260916.log`, SHA256
`82f2d22206d235ecd0723f4b3025a99fc2216096950e327c106a96da35fea06d`.
The detached game process finished with an orderly shutdown; its OS exit code
was not retained. A separate submitted-shape game run below did return0.
Video: `unreal/Saved/VideoCaptures/RaftSim_20260916-082243.mp4`.
All753 encoded frames decode through25.0667s;97 source frames span25.105s.
Inspected unmodified8/16s frames and screenshot002 show moving raft/foam, but
the deep green bowl, vertical streaks and broad white band persist. The later
initialization does **not** fix them. Encoding30Hz is not measured game FPS.
The decoder's inherited ROI labels do not identify physical regions for this
camera; do not interpret their named statistics as foam/terrain measurements.

## Submitted geometry, not an optical guess

**September 16 correction:** the v1 source interpolation below used the old
B-C quad diagonal, not the native shoreline fan A-C-D / A-D-B. Its source/base
split is superseded by the corrected analysis in
[control-prior comparison](control-prior-comparison.md). The original report
and numbers are retained as historical evidence, not valid interpolation-error
measurements. Actual submitted geometry and its total component split are
unchanged. Do not change temporal blending to fix this diagnostic error.

Second actual game run with `-RaftSimCarrierShapeAudit` exits0 and captures at
world13.022695s, presented detail sequence66. It contains69,340 active vertices
and53,702 triangles. The existing independent analyzer examines22,869 triangles
within30m of the raft. Among30-60 degree displayed slopes, the signed gradient
along the displayed slope is0.885787 from base residual,-0.031815 from crests
and0.008352 from detail. On the fully wet comparable subset, cached source
contributes0.682392, target-minus-source0.084669 and submitted-base-minus-target
0.129839. Three triangles exceed60 degrees, totaling0.078125 m2.

Report: `tmp/landward-1700s-carrier-shape-v1-20260916.json`, SHA256
`3b3f13a7c6742ab52898af1b41555a4b24dff911f66954fa0763cc3955376862`.
The base residual includes temporal/clipping/other shaping. This is not a
pixel-registered bowl measurement, GPU normal readback, or pure temporal-error
measurement. It narrows the next investigation toward source/base shape and
its presentation, rather than assuming coarse/fine crests alone cause it.
Next isolate the visible bowl/streaks against these actual submitted triangles,
then correct the responsible geometry/deformation and compare actual motion.
Do not conceal the defect by blanket foam attenuation or invented rock heights.

## Verification and remaining work

98 focused preview/retention/submitted-shape tests PASS in3.00s. All464
protected identities pass:462 unchanged, two proven CPU-retention-only
revisions. Existing ignored directories cover these generated artifacts.
Full package83678/cook5852 remains live with three active shader workers;
the900-second no-worker-state-change warning is not a terminal failure.
Preserve this cook's shader/DLL inputs. Archive identity,444 non-editor ground
sources, staged runtime closure and packaged gameplay remain next after cook.

No new uncontended FPS test: last17.819710FPS/p9581.6343ms still fails30FPS.
Do not promote this preview. South Fork geometry/breaking/froth/default delivery,
Colorado -> Pacuare -> Futaleufu, other-scene water including Chilko/Zambezi,
crew, normalization, outstanding regressions and release remain open.
Troublemaker remains a rapid within South Fork, never a menu scenario.
