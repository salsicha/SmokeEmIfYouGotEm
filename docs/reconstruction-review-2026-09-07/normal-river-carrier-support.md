# Submitted carrier support — September 12

## Measured mismatch

The normal South Fork scenario previously reconstructed raft-support relief
independently of the submitted water geometry. The renderer uses four-pass
hydraulic analysis, temporal easing, shoreline clipping/weights and refined
triangles; the adapter's analytic support is not that same surface.

An opt-in actual-game audit samples independent barycentric points on submitted
triangles (weights .2/.3/.5), then calls the world-space raft support API. It
removes the actual configured render lift once. This excludes material GPU
displacement and render-thread latency; it is not total contact acceptance.

Diagnostic build49961 succeeded in48.00s. Baseline game95617 exited0:
2,021 wet points, maximum difference45.534718cm, RMS6.172433cm, zero unavailable
or dry points at10.0634s. Evidence is preserved at
`tmp/south-fork-carrier-contact-before-v1-20260912.json` and
`unreal/Saved/Logs/south-fork-carrier-contact-before-v1-20260912.log`.

## Integration

The normal single Cartesian carrier registers a weak-owner, game-thread-only
support provider with the water adapter. Its existing spatially indexed query
samples only the submitted wet triangles, including current fine-crest and
temporal geometry. No second mesh, new spatial cache or GPU stall is introduced.

The adapter first requires authoritative live, wet solver data. An available
carrier replaces support height once; a clipped-dry point rejects hull support.
An unavailable/hidden/off-grid or invalid provider falls back to the existing
analytic support. Owner-specific removal and weak lifetime checks prevent
destroyed surfaces being called or old owners unbinding replacements.
Hydraulic depth, bed, velocity, normal and raw wetness remain unchanged; D3 and
overwash still use their existing field. Non-Cartesian support is unchanged.

This is CPU carrier coupling, not GPU detail coupling. The latter still needs
timestamped, world-registered evidence and a bounded-latency integration; a
current CPU triangle cannot prove contact with a displaced GPU vertex.

## Verification status

Integration build11123 succeeds261.61s, with two existing double/float warnings
in the unchanged Chaos helper. Test1669 exits0 but its REPORT is56pass/1fail:
the owner-lifetime fixture attempted to instantiate abstract UObject. Its
ensure is retained in the v1 report, not hidden by the successful process exit.
The actual actor/shoreline integration test passes. The fixture now uses a
concrete inert adapter as its owner. Rebuild87422 succeeds17.79s; full rerun
69421 exits0 and the v2 REPORT confirms57pass, zero warnings/failures/unrun:
`unreal/Saved/RaftSimValidation/south-fork-carrier-support-regressions-v2-20260912/index.json`.
RaftDLL `fed24ca5bd732068c791bf213cb680fdc7b48e2099ae38fea050665e3ca2d71d`;
WaterDLL `396aac31550e87e491fed8ce60823c029c8b8f4874a3e2741462c13981b189d8`;
mainDLL `97361951b4e96ec05ecffb59d8be41c09bee89d71b64b982abede7772af1a2e6`.

Actual post-change game14754 exits0. At10.009772s, the same2,021 barycentric
wet points have maximum support/CPU-carrier error0.000047590093cm and
RMS0.000023842251cm; no dry or unavailable points. This is floating-point
agreement with the submitted geometry, not proof of GPU contact:
`tmp/south-fork-carrier-contact-after-v1-20260912.json`.

Shared-crest audit retains the unchanged2cm gate:1,550,016 samples,
max0.600746734cm, fine correction tracking0.000209093cm, refinement source
change0. UV3 transport and UV1 bulk errors both0. Reports:
`tmp/south-fork-carrier-support-crest-v1-20260912.json.cartesian-mesh.json`,
`tmp/south-fork-carrier-support-transport-v1-20260912.json`.
Mapdb3080cc…, materiale4e9b2f3… and save181d1e57… independently rehashed,
unchanged. Terrain/bathymetry, solver and menu settings were not changed.

Capture frames000 and039 actually inspected: central wave remains too smooth
and froth thin/linear. This support correction is NOT a claimed visual fix.
At10/20s drift telemetry records zero dry/ground points, but those two samples
are not a traversal/grounding acceptance test. Heavy capture detail backlog
4.947168s over26.556s. Movie170930 has87 source frames over16.782s; it has not
been continuously viewed and is not an FPS measurement. Its SHA256 is
`faedb32a900ae0d6f0ddc668e096be43de5b0cf126e713925dfdbded54636a72`.
Motion audit confirms40 unique PNGs over12.076 game seconds, stationary camera:
`tmp/south-fork-carrier-support-motion-v1-20260912.json`.

Isolated profile66574 exits0; cook29104 suspend/resume both0, no timeout.
Rows100..250: mean54.766342ms,18.259390FPS,p9575.29ms, still FAIL60FPS.
Prior native-stage sample19.625987FPS; variable trajectories and refresh counts
mean this is not a controlled attribution to the provider alone. GPU14.882748ms,
crest update18.283279ms, source preparation1.409053ms/update. Ordinary detail
backlog7.037ms,4 exact remaps,0 teleports,34.033335 simulated seconds.
`tmp/south-fork-carrier-support-performance-v1-20260912.json`; CSV SHA256
`ee96f066574712ccbe8fa73df23d036b48681f97fa0d71b5615ebfa441aed04a`.
At20s this unsteered profile records1 ground point/0.001m penetration, unlike
its10/30s samples; no clean traversal claim. This is not itself proof of a new
collision regression or a comparison along identical trajectories.

NEXT: GPU detail contact with explicit sampling/time registration, unnecessary
CPU optical passes (native mean stage currently discards most optical work),
crest cost, convincing physical breaking/entrainment/froth, and guided
terrain/collision traversal. No gates have been lowered. Breaking/froth realism,
total contact, full-river hydraulics/traversal, later rivers, crew and release
remain incomplete; the complete goal remains active.
