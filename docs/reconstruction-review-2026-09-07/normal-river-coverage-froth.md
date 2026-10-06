# Preserve transported foam coverage — September 12

The preceding turn made verified progress: completed GPU detail and actual
raft support use the same registered frame. It did not fix the visible smooth
wave/thin froth. This pass addresses an optical loss in the playable parent.

## Measured implementation problem

The detail resolve already converts persistent density to bounded coverage.
The registered material authority inverts that coverage into optical-density
units. The old coverage consumer then clamps density to one and multiplies
the recovered opacity by a second sparse, density-dependent lace threshold.
This suppresses the field again, despite its comment saying not to do so.

The unchanged project-owned procedural lace is1024x1024 grayscale, linear red
mean0.1552058425604128; SHA256
`5aeea75dc41b0441314064494ba440f85a80f3b5bd4726e77918ca7eab0d9576`.
At12% inputcoverage, the old minimum-antialias-width formula gives mean
1.458457541% on this texture. That is a source-texture calculation, NOT a
measurement of every shaded pixel: actual derivatives, compression, local
flow warp and correlation with the spatial foam field also matter.

## Correction

Recover coverage without clamping the inverse density to one. For source mean
mu, apply bounded affine contrast:
`coverage + min(coverage/mu, (1-coverage)/(1-mu)) * (lace-mu)`.
This is the greatest contrast remaining in[0,1] without clipping bias. It
keeps zero foam absent, full foam full, and the same expected mean through
both phase samples and linear mip averaging. It does not add source density,
mass, geometry, bubbles or a second visible surface. Optical calibration is
not measured void fraction or proof of physical aeration.

The exact HLSL helper is shared by a new real-GPU regression and the material
custom code. The editor refresh reads that same helper, preventing a later
refresh from restoring the sparse gate. A guarded installer backs up the
current exact-hash material and changes only coverage code, retaining all
four optical consumers and every other node. WPO/normals/wet mask, registered
frame authority, terrain/collision and saved progress are protected.

## Evidence so far

Build51746 succeeds41.89s. Source analysis
`tmp/south-fork-coverage-froth-source-v1-20260912.json` passes110cases across
all11 exact box mip levels: expected coverage preserved within1e-12 and range
bounded. At12%, new mean12%, extrema0..0.773166770. This is uncompressed
source evidence; runtime compressed/local-area means are not established.
Native60-test run57638 exits0:60pass, zero failed/warnings/unrun/inprocess.
`unreal/Saved/RaftSimValidation/south-fork-coverage-froth-regressions-v1-20260912/index.json`.
SharedGPUhelper192queries referenceerror8.91610146e-8, expectedcoverageerror
4.23925222e-8. WaterDetailDLL SHA256
`d983a2ac0f6cd5b38b13c7e422f258167316034428bc105b3e4ab523120a15f5`.
Raftc8a9d9b3…, Water73b9b542…, mainb2b68080… unchanged.

Guardedinstall83032 exits0, all other nodes exact, four optical consumers
retained,459protected map/actor/ground/save files unchanged. Existing lace is
linear(sRGBfalse),TC_MASKS. Material SHA256
`9935cd7006b6176d64b1f1f15b2664894112da27ad756ad47110cd50c7c05e28`.
Report `unreal/Saved/RaftSimValidation/south-fork-coverage-froth-install-v1-20260912.json`;
same stem `.backup.zip` preserves previous materiale4e9b2f3…, archiveSHA256
`e044651f46e3fb50ecae3cdad49d1fa4ab41b8a07c7f9926bf89e2d0053ec4e4`.
No source texture was changed or replaced. Fresh-process and actual engine
motion/visual/performance verification remain pending.

## Affine appearance rejected; replacement in progress

Fresh33703 wrote exact all-six-graph parity/hash evidence, but process exits1
despite no logged Python assertion/error; retained, not called a clean process
pass. Actualgame17841 exits0. Frames000/039 inspected: the affine mapping makes
a broad WHITE BLANKET, not convincing froth. This is a visual rejection, not
acceptance based on coverage arithmetic. At high p the affine map's minimum
is high, so it cannot preserve dark water pockets. Do not tune down simulated
density merely to compensate for this optical flaw.

Actual contact remains paired:sequence114 in both reports,955of2,021points
with detail,max4.373765cm, contacterror.000047663cm; GPU4,226queries maxRGBA
5.960464478e-8. Reports `tmp/south-fork-coverage-froth-{contact,gpu}-v1-20260912.json`.
Heavycapture204commits/1hold, maxqueueage.4s, PDEbacklog4.274173s,
3exactremaps/0teleports. Movie180959 has90sourceframes/16.444s, not continuously
viewed or FPS. No profile acceptance of this rejected appearance.

The replacement uses smooth random CORNER OCCUPANCIES, thresholded by the
transported coverage before convex interpolation. Each independent corner
has expectation p; spatial filtering, two scales and advected phase blending
retain that expectation without the affine high-density floor. Hash anchors
are fixed in world space and carried by the existing two-phase UV3 backtrace,
not regenerated per frame. Subpixel clumps resolve to expected coverage.
This remains presentation, not physical bubbles, foam mass or measured void
fraction. Finite area/flow/coverage correlations are not exact conservation.
Shared HLSL and extended GPU/CPU statistical fixture are building15570.
The affine helper/test remain as retained evidence, not the desired material.

## Advected clumps installed; actual visual check pending

Build15570 failed on the fixture's `FMath::Log` API name; corrected to Loge.
Build93504 succeeds22.37s. Native79294 exits0,60pass/zero warnings/failures/
unrun/inprocess. Report
`unreal/Saved/RaftSimValidation/south-fork-advected-froth-regressions-v1-20260912/index.json`.
16,576GPU optical queries retain affine-reference checks. NewclumpsGPU/CPU
maximumerror0.000102475286;16,384spatialpoints mean.119268729 for .12target.
This is a finite statistical test, not exact local area or fluid conservation.
WaterDetailDLL SHA256
`f9ac11cd680bc37ca9f1134c6564020f9130e3ad3fc825d58d35fa4eed239685`.
Raft/Water/main remain unchanged from paired-contact milestone.

Guarded80488 install exits0; new material SHA256
`26aa5029c579afad38fd603f96df9da304bd32ed338097d2580c9a29545ea82a`.
Only optical coverage code and its four additional links to existing UV0,
origin,UV3flow,time nodes change; every other node is exact. Four consumers,
WPO/normals/wet mask and459protectedfiles retained. New helperSHA256
`d08d8a5c10162fe1de462f0f5edea24a3fcd01a99c67897818caea699022b765`.
`unreal/Saved/RaftSimValidation/south-fork-advected-froth-install-v1-20260912.json`
and same stem `.backup.zip` (SHAe39f5f77147c4cc7a1b0c743ec4996d3dc71e8ebeffdb0513e16006acee3e36d)
preserve the rejected affine state. The earlier backup still preserves the
original thin-foam material. No images, captured geometry or source fields
were overwritten. Fresh graph check, actual captures and timing are next.

## Final actual material and contact evidence

Fresh93349 exits0, read-only all-six-graph equality passes, material26aa5029…
unchanged: `unreal/Saved/RaftSimValidation/south-fork-advected-froth-fresh-v1-20260912.json`.
Actualgame63663 exits0. Frames000/039 inspected: separate foam patches and
green/dark water gaps replace the affine blanket. The clumps remain TOO SOFT,
and the broad underlying wave remains TOO SMOOTH. This is visible progress,
NOT convincing-froth/breaking-wave acceptance. No terrain/rapid-shape changes
were made by this optical pass.

Both contact reports use sequence101:956of2,021wetpoints with nonzero detail,
max4.080525cm, maxsupporterror.000047590896cm,RMS.000023520957cm;
zero dry/unavailable. ActualGPU4,226queries maxRGBAerror5.960464478e-8,
maxsampledheight4.221733cm. Reports
`tmp/south-fork-advected-froth-{contact,gpu}-v1-20260912.json`.
Heavycapture187commits/1hold,maxqueueage.4s,PDElag5.300957s,
3exactremaps/0teleports. Movie182859 contains86sourceframes/16.941s;
not continuously viewed and not FPS. Isolated profile4774 is pending.

Computer-use skill, guidance and confirmation instructions were read. Both
documented desktop initialization and browser fallback failed BEFORE opening
the supplied reference video: `failed to write kernel assets ... os error3`.
No UI action or new real-reference viewing occurred. This blocks that check,
not continued local implementation; the goal is not at an impasse.

Next physical work must address the smooth underlying crest, not just paint
more white onto it. The current macro support uses static asymmetric Gaussian
crest/toe/tail envelopes; moving detail pressure head is still fixed at.06m.
These implementation facts are not measured real-river waveforms or a physical
breaking acceptance. Investigate source-driven crest/entrainment dynamics,
retaining shared rendered/contact geometry and raw solver authority.

## Final measured limits

Motion audit `tmp/south-fork-advected-froth-motion-v1-20260912.json`:
40uniquePNG/12.303game seconds, stationarycamera. Movie182859 SHA256
`036f1332f86933c2994efdb18c21ba61fb47a249e789ba075d9528ba36c8da75`.
Sharedcrest1,550,016samples max.600679977cm<=2cm, finecorrectiontracking
.000220895cm, sourcechange0. UV3/UV1 errors0. Reports
`tmp/south-fork-advected-froth-crest-v1-20260912.json.cartesian-mesh.json`
and `tmp/south-fork-advected-froth-transport-v1-20260912.json`.

Isolated4774 exits0/no timeout, exactcook29104 suspended/resumed0.1280x720,
300CSVrows,warmed100..250: **17.078327FPS**,mean58.553746ms,p9584.6274ms.
Priorpaired20.206351FPS; this run REGRESSES and STILL FAILS60. GPU15.338379ms
versus13.430089, crest20.058067ms versus16.350859, inclusivepublish27.638491ms
versus23.434938. Different trajectories/scheduling mean this is not isolated
causal attribution to the new shader, nor a packaged sustained benchmark.
Report `tmp/south-fork-advected-froth-performance-v1-20260912.json`;
CSV SHA256 `1cd52138683faf11d2e1da24d40593e71d1dfc7f4a3c2ff9db84c79a5dc48dba`.
Ordinarydetail634commits/1hold,636candidates,0busy skips,maxqueueage.4s,
PDEbacklog.004988s,5remaps/0teleports,34.041668simseconds. Preparation1.411416ms.
Mapdb3080cc…,save181d1e57… rehashed unchanged; currentmaterial26aa5029….

Cook96057/PID29104 confirmedlive and resumed, observed2375.5/local7510.
2300 is latest BOTH state/bank-audited snapshot; next2400/local8000 still
requires both after completion. Runtime600s unchanged; settling unaccepted.
All physical breaking/froth, wave shape, clean traversal, latency/60FPS,
full-river/later-river/crew/normalization/release/finalcommit remain active.

Broad central wave shape, physical entrainment/breaking, full traversal,
60FPS, later rivers/crew/normalization/release/finalcommit remain incomplete.
Troublemaker remains only a rapid inside South Fork, never a menu scenario.
