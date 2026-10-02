# Isolated water-feature laboratory

User goal changed on 2026-09-29: build small standalone environments and show
short animations of individual water features. Full-river acceptance work is
not the current objective. Preserve the existing river builds and source work.

## Delivery and acceptance

Each case has physical dimensions, boundary conditions, fixed camera, explicit
simulation time, reproducible settings, a short rendered clip and an honest
assessment. Beauty renders must be accompanied by geometry/flow checks. A
solver label alone is not validation. Offline rendering speed is not game FPS.
No claim of real-time integration is made by these initial Blender scenes.

Use 3D liquid geometry for overturning, waterfalls and rollers. A heightfield
cannot represent an overhang or the submerged return leg of a roller. Keep
surface foam, entrained bubbles and airborne spray distinct. Secondary-particle
rendering is a subgrid approximation, not resolved individual bubble physics.

## Cases

| Feature | Tiny environment | Required evidence before acceptance |
|---|---|---|
| Waterfall | Ledge, falling sheet, plunge pool | Gravity acceleration, thinning sheet, impact/cavity/splash, mass balance |
| Hydraulic hole | Drop into controlled tailwater | Upstream surface return and downstream submerged current, persistent roller, entrainment |
| Standing wave | Short bump flume | Stationary crest with water moving through it, wavelength/height and Froude checks |
| Boulder pillow | Single obstacle | Upstream pressure mound, split flow, wake, no water through rock |
| Eddy | Single bank obstruction | Circulating trajectories, shear seam, exchange with main current |
| Boil | Local upwelling | Radial surface divergence, evolving dome and outward foam transport |
| Surface foam | Small current/shear tray | Advection, deformation, gathering/breakup, persistence; no texture sliding |
| Aerated froth/spray | Local breaking/impact patch | Volume versus surface versus ballistic phase, correct depth and scale cues |

## First iteration

`unreal/Scripts/build_water_feature_lab.py` creates fresh, independent waterfall
and hole cases; never overwrites existing output. Waterfall is the first bake.
Use actual Mantaflow liquid evolution, metric units and gravity 9.80665 m/s².
Initial low-resolution bake is a pipeline/shape prototype, not calibrated CFD.
Refine spatial and temporal resolution and assess boundary sensitivity before
physical acceptance. Clips must identify startup transients and not imply a
seamless loop. Do not fabricate whitewater by coloring all fast flow white.

### Current handoff

October 1 continuation (general curved material transport calibration): new
continuous P2 3D geometry/velocity, full material kinetic mass and local DG P1
pressure advance a nonuniform free surface with fixed slip-wall/bed contact.
The retained continuous-pressure control fails local density (bound up to
2.899x initial) despite excellent global conservation; rejected, NOT animated.
All three local controls pass unchanged preliminary 1% bounded-density gates.
Independent different spatial/time quadratures check ALL 600 saved steps,
original pressure rows, fresh momentum, kinematics, global/local volume,
energy, wall coordinates and positive curved maps. Finest density bound
deviation 0.5648%; this is not exact local incompressibility or pressure
stability. Two time steps/two meshes and independent curved Eulerian surface
integration: modal differences 9.61e-7 m temporal, 3.24e-4 m spatial. Initial
interpolated surfaces differ; no full-period/frequency/convergence acceptance.
Delivered 21-view actual engine animation and embedded playback at
`docs/water-feature-lab/moving-tank-calibration-v1/`: CALIBRATION, not accepted
standing wave. Physical 0.4 s shown 5x slow + end hold; diagnostic orange
material-node markers NOT foam; illuminated bed is authored apparatus.
Finest boundary only (no easier fallback), 3,458 welded vertices/6,912
triangles, chord volume error 5.93e-6 m3. No geometry expansion/amplitude
exaggeration/smoothing modifier, clamp, density reset or hidden fluid domain.
Fresh read-only Blender reopens delivered file; ALL 21 poses/markers match
within 2.98e-8/2.92e-8 m. First dark/cropped previews preserved separately.
240 numerical tests / 15 strict compiles pass (eight Blender-context modules
not claimed from stock Python). Physics finest 623.87 s for 0.4 s, independent
readback 81.83 s, 21 engine renders 349.66 s: not gameplay FPS. Large arrays
remain local, no duplicate fields or source/cache deletions.
Final 415-file pin verification plus three old eddy artifacts passes with no
hash conflicts or mismatches. All owned physics/qualifier/render/playback
workers terminal 0; no Blender/UnrealEditor process remains live. Scoped diff
whitespace check passes. Delivered animation panel queued for this chat.
Next full-period motion/further refinement/pressure conditioning, conservative
solid-contact/inlet chronology and topology handling, then accepted actual
feature views. No through-flow/impact/breaking/foam/froth, engine river update,
native-cache repair, Git writes, automation mutation or 20 FPS claim. Preserve
all prior receipts/source fields/animations; goal remains active, all eight
features and later playable river integration unfinished.

Previous continuation:

October 1 continuation (conforming liquid gravity/pressure and transport
calibration): new bounded RT0/P0 tetrahedral reference couples the FULL kinetic
matrix, physical face flux, pressure, gravity and explicit liquid boundaries.
No area/dual substitution, mass lumping, buried-center ghost or source fitting.
Twelve controls at three refinements independently qualify every tetrahedron,
face, mass matrix, normal trace, pressure/gravity equation and projection-energy
identity. Inclined-bed hydrostatics and all-free gravity match exact references;
tilted-interface flow and inlet/free-boundary ledger are represented. These
controls remain fixed geometry and nonhydrostatic refinement is not accepted.
Retained 10 ms trial fails its unchanged Courant gate; 4 ms on ALL meshes passes.
New free-flight parcel advances 4,000 gravity/pressure impulses with uniform
translation transport, independently checked at 21 saved poses. Gravity-control
rendering/animation is a CALIBRATION, not waterfall/impact/splash acceptance:
zero capillarity, no air drag, no collision or emission. Conforming tank/parcel
meshes are NEW authored geometry, NOT a repair of the old native eddy checkpoint.
Evidence at `docs/water-feature-lab/rt0-coupled-impulse-v1/`. Next conservative
general interface transport, solid contact/source chronology and refinement,
then actual feature animations. Preserve all source data/failed controls.
Delivered 21-view annotated gravity calibration and embedded Blender playback;
fresh read-only Blender reopens the delivered file and matches all computed
poses within 5.64e-8 m. Physical 0.4 s shown 5x slow with end hold. Numerical
224 tests / 10 strict compiles pass; Blender-only legacy tests are not claimed
from stock Python. Full-field/pressure/old-animation preservation hashes pass;
owned render/check workers terminal 0. No actual waterfall/eddy acceptance,
native cache repair, impact/contact/emission delivery or gameplay/FPS claim.
All eight features and later normal playable 20 FPS remain unfinished.

Previous continuation:

Latest continuation (October 1, full shared phase support): actual solid/phase
fields implemented across ALL 117,180 cells, 359,412 N+1 physical faces and
34,919 possibly-wet duals at TWO guarded refinements. Independent qualifier
recomputes every declared bound (max cell/dual difference 2.71e-19 m3;
liquid-area difference 8.67e-19 m2). Evidence delivered in
`docs/water-feature-lab/eddy-shared-phase-support-v1/`. Supporting fields/audits
ONLY: no new pressure/physical step, cache/playback, animation or game/FPS.
12,398 cells definitely wet, 12,625 possibly wet; 227 unresolved cells retained.
1,201 old empty cells have positive lower liquid volume in actual open regions;
no old fluid cell proved dry. No definitely-wet face lacks positive lower dual
support. Direct interval UNION face areas resolve another 60 positive-roundoff
representations without an area cutoff; old arrays/source geometry unchanged.
Total reconstructed volume bounds narrow to [3.918710,4.044877] m3: not mass
conservation or CFD convergence. Common wet-area Cartesian flux audit exposes
old-reference zero-excluding intervals in 1,257 definitely-wet cells, max
0.0230665 m3/s; internal free-surface motion and source/removal absent, so do
NOT call this full incompressibility residual or mass drift. Three receipts
copied with hash equality; 212 tests / 7 strict compiles pass.
Final 142-file hash verification plus prior animation/both playbacks pass;
all new workers terminal 0; no Blender/UnrealEditor job remains live.
Construction 391.48 s / 32.5 MB; independent full-bound check 1,430.82 s,
not game FPS.
Next derive matching pressure/kinetic inertia/velocity/free-surface/source
chronology and transport on shared phase support, including uncertainty and
internal boundaries; do NOT blindly substitute volume for area weights or
force Cartesian cut-cell flux to zero. Matched physical-step/contact/budget/
refinement acceptance still required before new bake. All 8 features and
later normal playable 20 FPS delivery remain unfinished; keep goal active.

Previous continuation (October 1, geometric volume/liquid support): actual
box/roof UNION open volumes and first moments implemented for arbitrary
pressure/dual cells; independent Gaussian-column verifier checks all 117,180
cells (max difference 2.71e-19 m3, 8.67e-19 m4) and 72 local cached-liquid
bounds. Delivered supporting evidence: `docs/water-feature-lab/eddy-geometric-inertia-v1/`.
NO new animation, full step, changed pressure/cache/playback or game/FPS claim.
1,188 native fluid pressure centers lie in actual solids, but their cut cells
retain positive open volume; do not delete them. Minimum represented wet
sliver 3.16937e-16 m3 is retained. The 15.2709 m/s face's buried center says air
while its actual open dual is essentially 100% reconstructed liquid: the
10.9422 ghost response is not its open-region interface. Two other active
fast duals (9.43476 and 7.58711 m/s) contain zero reconstructed liquid at refined
bounds. Their neighboring cells remain partly wet, so cell deletion is wrong.
196 numerical tests / 4 strict compiles pass; two small receipts copied with
hash equality. Original fields/geometry/pressure/animations stay unchanged.
Final 102-file pin verification and old animation/both playback hashes pass;
no Blender/UnrealEditor job remains live, no Git/automation/evidence deletion.
Next FULL active-stencil liquid-open face/dual support and matching inertia/
pressure/transport/source handling, not buried-center/centroid relabeling or
manually replacing a few ghost coefficients. Liquid bounds are guarded values
of cached reconstruction, NOT conserved mass or accepted physical interface.
All 8 features and later playable integration remain open; goal stays active.

Previous continuation (October 1, consistent pressure): matching area/distance
matrix and velocity-gradient reference implemented, with actual native
correctVelocity and float32 RHS readbacks. Independent qualifier verifies all
359,412 faces and corrected float32 velocities. Delivered supporting evidence:
`docs/water-feature-lab/eddy-consistent-pressure-v1/`. NO new animation/cache/
playback/full fluid step/game/FPS acceptance. First flux-passing candidate has
a 303.958 m/s jet through a roundoff aperture in a fully blocked floor face:
retained and rejected. Exact containment of the unchanged 7 actual boxes closes
2,220 falsely open faces WITHOUT a small-aperture threshold, geometry changes
or velocity clamp; all unproved faces remain bit-exact. Certified consistent
pressure passes native float32 weighted-flux max 3.72529e-6 s^-1, 140 iterations,
0.262 s snapshot cost, but remaining active partial-face peak 15.2709 m/s is
physically UNQUALIFIED. Native public pressure still fails 16.6194 s^-1 maximum.
16 unsupported cells in the old native-distance input are retained/rejected,
not deleted; the prior singular fixed-flags trial is not repeated. No direct
hidden native-matrix readback. Independent source review finds fractional
matrix/ghost/outflow response inconsistency; bulk-interior residual is small.
181 numerical tests and 8 strict compiles pass. Four receipts copied/hash-
verified; 94 pinned files and old animation/both playback files reverified
unchanged; no Blender/UnrealEditor process remains live. Next exact general
coverage plus geometric partial-cell volume/inertia and liquid support, then
coupled contact/chronology/surface/refinement. Do NOT promote low flux residual
as physical velocity or animation acceptance. All 8 features remain unfinished.

Previous continuation (October 1, geometric apertures): actual closed-triangle
sections and all359,412 physical face areas are implemented, exported from the
unchanged8-solid eddy control, and independently verified against all actual
box/extruded-bed geometry (max area difference3.04e-18m2). Delivered evidence:
`docs/water-feature-lab/eddy-subcell-apertures-v1/`. Supporting geometry/native
pressure only; NO new animation/cache/playback/game/FPS acceptance. Native
distance-segment fractions are not geometric2D areas. The owned frame169
pressure-only control using geometric areas with SAME cached flags diverges:
168 geometrically closed fluid cells remain; independent recount finds87 with
no empty-neighbor ghost-fluid term, consistent with zero operator rows. The
other81 have empty neighbors: do NOT call all168 zero matrix rows. No direct
matrix readback or exclusive failure attribution yet. Do not bake it.
Rebuilding flags from areas removes those cells but changes6,027 flags and
the fluid cohort; cut-cell divergence RMS1.448->0.484s^-1 still has9.423s^-1
maximum, whole-fluid maximum16.611s^-1. No physical/convergence acceptance.
Two finite controls and the explicit native divergence failure are independently
qualified from saved readbacks. All source geometry/cache/host fields stay
unchanged, no primary particles advance. Tiny positive apertures preserved;
cell-volume/conditioning/contact/surface coupling is still unfinished. Next
inspect actual matrix/free-surface/corrected-velocity residuals and build the
shared geometric representation, not nearest-node or aperture-only promotion.
All169 tests and7 strict source compiles pass. Five reports are delivered with
copy hashes;56 qualification-pinned files and previous animation/playback
hashes reverify unchanged. All owned jobs terminal; no source-access blocker.

Previous continuation (October 1, corner mechanism): source diagnosis and twelve
matched owned native liquid-step experiments are delivered in
`docs/water-feature-lab/eddy-corner-mechanism-v1/`. Supporting physics evidence,
NOT a new animation, solver acceptance, changed playback or game delivery.
All original native controls/animation/playback stay unchanged. Three actual
late states per mode show authored-contact errors already present in the
cached obstacle field, compounded by corner interpolation. The installed
source uses26-direction volumetric ray-distance estimates; native contact
follows the interpolated field. Exact closest closed-mesh node replacement is
tested with the same native flag preparation and reconstructed uncached face
fractions in BOTH controls, exact installed liquid-step code and identical
initial cached state/clock. Pressure/contact consume the changed geometry
together; one20.833ms substep per control, not host-emission/full-frame replay.
ALL12 sampled contact gates still fail. Derived spur20.833->19.519mm and
approach10.080->9.634mm, primary spur remains up to30.305mm, and changed
geometry introduces12.501mm far-wall contact. Reject closest-node replacement
as a full repair; do not bake/promote it. An independent qualifier checks108
pinned inputs/outputs, all retained node stencils, paired initial states/code/
clocks and12 post-step volumes at8/16 quadrature. Volume quadrature changes
reach20..23litres: no conservation/convergence claim.156 tests pass; four
scripts compile. Early incomplete/asymmetric trials are preserved and explicitly
superseded. Final49-report verification rehashes6,402 unique pinned files with
zero conflicts/changes, plus unchanged animation and both playback blends.
All native jobs finish; no source-access blocker or lost prior work.
Next prototype actual subcell face/collider intersections shared by pressure,
swept contact and extraction, with budget/refinement tests; not cosmetic
clipping, clearance/radius fitting or another identical nearest-node bake.
Full all8-feature goal and later playable river integration remain active.

Previous continuation (October 1, explicit walls): the two-second paired eddy
animation and two self-contained geometry-playback Blender files are delivered
in `docs/water-feature-lab/eddy-explicit-walls-v1/`. Explicit physical planes
inside a padded computational cage repair the prior effective-width mismatch;
75 mm cell spacing and original source/floor/slope/spur geometry are retained.
Both fresh DATA and MESH controls finish 192 frames. Do not duplicate them.
All 192 cached obstacle fields agree at five fixed wall/bed stations within
float32 precision; this is sampled plane agreement, not whole-solid accuracy.
The frame-1 paired volume gap falls from 0.515263 to 0.000055 m3. Late volume
and section-flux differences remain; no conservation/convergence claim.
All 60 derived surfaces are closed and support the original 54 columns, but
ALL still fail authored contact: slope intrusion 10.080 mm, spur 20.833 mm.
Primary centers retain slope/spur intrusion too; neither solver is accepted.
48 actual rendered views and all 24 encoded frames are checked. Each saved
playback file independently reopens with 24 bit-exact poses and 96 visibility
checks; no external cache or active fluid modifier is needed. Playback is
sampled geometry, not a self-contained CFD solver or real-time game delivery.
Six rerenders visually match captures within one 8-bit channel value.
Final verification rehashes 6,331 unique pinned files across 17 new and 27
preserved prior reports with no conflicts, plus the delivered clip and blends.
All owned jobs finish; 156 numerical tests pass. No old files/caches, game,
Git or automation changes. Full eddy circulation, contact, budgets, convergence
and foam/froth/optics remain open, as do all eight features and later playable
river integration. Next repair coupled slope/spur corner discretization;
do not substitute cosmetic clipping or particle-radius fitting. See README.

Previous continuation (October 1): a verified two-second three-control eddy
animation is delivered in eddy-fractional-controls-v1/feature.png, 24 native
frames at normal speed. Both new fractional DATA/MESH runs complete 192
frames; do not duplicate them. Default37.5mm particle clearance eliminates
sampled primary-center contact but reduces late reconstructed volume47.6%.
Zero clearance restores much of it but retains27.545mm primary bank intrusion.
All60 new derived meshes still fail authored contact (20.833mm bank overlap),
despite passing closed-edge/exact-zero-area checks. Actual cached wall profiles
show fractional borders move105.68mm inward per side; the volume gap already
exists in frame1. Same authored geometry does NOT imply matched effective
boundaries. Neither toggle is an accepted repair. Default interface gaps at
157/159/161 are retained. Two corrected paired reports freshly reintegrate
all180 face/quadrature estimates each using physical MAC scale0.1875, not
display normalization1/80; old raw flux units are wrong15x and superseded,
volume integrals unchanged. Primary velocity matching remains raw API units.
72 actual matched transparent-water views and every decoded APNG frame are
verified; no cosmetic contact clipping, hidden rock or invented foam. Existing
156 pure tests pass and eight scripts compile. New reports/clip are copied
and hash-verified; all native caches and prior deliveries are preserved.
All owned jobs are terminal, no game/build/Git changes or20FPS claim.
Next explicit matched wall/bed/spur representation and coupled native contact
repair, then budgets/circulation/convergence and full foam/froth/optics. Keep
all eight cases and eventual river integration open under the newer isolated
feature goal, not the obsolete full-river heartbeat. See the new README.

The first actual waterfall clip is rendered, encoded and verified:
`docs/water-feature-lab/waterfall-prototype-v1/feature.mp4` (3 seconds).
See `docs/water-feature-lab/first-feature-review.md` for the physics calibration,
failed hole trials, visual limitations and precise next work. No case accepted.
The hole chute prototype clip is also delivered in
`docs/water-feature-lab/hole-prototype-v1/feature.mp4`. Its sampled surface return
and submerged downstream flow persist across 7..10 seconds, but section flux
estimates disagree and the rendered foam remains blanket-like. See
`docs/water-feature-lab/hole-chute-review.md`. All hole/waterfall bakes and renders
have finished; do not duplicate them.
Two separate standing-wave candidates have now been baked and inspected. The
first drowned its inlet; the raised-approach second version restores forward
flow and produces a small moving crest near the bump, but is not accepted.
See `docs/water-feature-lab/standing-wave-review.md`. A three-second coarse
candidate animation is now delivered in `standing-wave-prototype-v1`; its crest
is unsteady and not accepted. The finer v3-r160 bake and late audits are now
FINISHED, but not accepted: the bump-zone peak spans 0.60 m and the flow slows
before reaching the bump. Its matched calibration is finished.
The renderer can now preserve per-particle size variation rather than force
uniform maximum-size sphere points; this does not solve foam physics.
Matched early previews reveal a serious whitewater resolution dependence:
doubling resolution increased foam count 6.71x and bubble count 11.98x while
render radii stayed fixed. Do not claim the finer full render is more accurate.
The boulder-pillow v1 bake and two-second prototype clip are DONE; the clip is
in `boulder-pillow-prototype-v1`. It shows a mound and outward split, but actual
mesh intrusion reaches about 8.5 mm. A controlled fractional-obstacle comparison
is DONE. It eliminates sampled intrusion but also lowers the water volume and
pillow substantially; it is not accepted as a general fix. Do not duplicate it.
Both serial runners 26447 and 56278 are terminal. The standing-wave-v4-low-tail
bake/audits/preview are DONE: crest movement narrows to 0.20 m and fast flow
reaches the bump, but the shallow downstream flow is under-resolved. No v4
animation yet. See individual reviews for evidence and unresolved validation.
Airborne spray now uses water's dielectric material rather than opaque foam;
a matched preview was inspected. Previous delivered clips are unchanged.
Foam/bubble phase modeling and resolution-independent optical coverage remain
unaccepted. `--liquid-only` is explicitly a geometry diagnostic, not a final
replacement for the requested foam/froth appearance.
The bank-spur eddy v1 bake is DONE. Late region samples show downstream main
flow and upstream bank return with the expected lateral turns; full trajectory
and boundary checks remain open. Its verified three-second high-angle clip is
delivered in `eddy-prototype-v1`; render session 73831 is terminal. Reconstructed
tracers do not establish a full circulation loop and often lose narrow-band
support. Do not count that diagnostic as accepted trajectories. See
`docs/water-feature-lab/eddy-review.md`.
The matched 120-resolution velocity calibration PASSED (gravity error 0.42%).
The standing-wave-v5-low-tail-r120 bake and audits are DONE (sessions 39269,
74747 terminal). It does not converge to v4's hydraulic quantities; foam also
increases sharply. Do not accept or repeat it merely for a finer mesh.
The missing boil case is now implemented separately as a closed 3 m pool
with a submerged piston causing transient upwelling. Its matching velocity
calibration PASSED. The boil bake and early/late audits are DONE (89671 and
8273 terminal). It produces transient core upflow followed by radial spreading;
later flow reverses/decays. Its verified 1.5-second clip is delivered in
`boil-upwelling-prototype-v1`; render session 75854 and encoder 97772 are terminal.
It is not a measured natural boil or an accepted vortex-ring reproduction.

Six feature clips exist (waterfall, hole, standing-wave, boulder pillow, eddy,
transient upwelling); none is accepted yet. A separate surface-foam study now
exists: its smooth advected scattering patch was rendered and rejected as
featureless. A 220-cell thin-film/contact study is prepared with timestep,
non-overlap and native Blender timeline checks. Its three-second study clip
and editable animated scene are delivered in `surface-bubble-study-v1`.
Surface-bubble render 34347 and encoder 95687 are terminal.
This is an above-surface optical and
contact prototype, not complete physical foam. See
`docs/water-feature-lab/surface-foam-review.md` for exact limits and the newly
located primary bubble-geometry/capillary-migration reference.
A connected isolated cap/cavity/meniscus checkpoint is now delivered in
`bubble-geometry-study-v1`, with a static engine image, self-contained blend
and saved-mesh checks. It removes the artificial flat plane across a bubble.
However, the reduced spherical-cavity model has a 12.68% pressure residual
at Bo 0.544; it is NOT accepted equilibrium or a replacement foam animation.
Next solve nonlinear Young-Laplace geometry at fixed gas volume, then integrate
into moving foam with capillary interactions. Render 48650 and audits are
terminal. See `surface-foam-review.md`; all eight original cases remain open.
The next nonlinear isolated-bubble solution is now implemented and rendered:
fixed gas volume, cavity/exterior pressure balance, spatial/far-boundary
refinement and three bubble-size checks pass numerically. Its independent
cavity pressure residual at 1 mm is 0.000541%; this does not establish full
foam/optical accuracy. Native uniform drift is verified in the saved blend.
Render 32246 and encoder 73811 are DONE. Its three-second transport-study clip
and embedded native animation are delivered in `bubble-equilibrium-drift-v1`;
36 rendered/decoded frames and all copied file hashes passed. This is a
single-bubble uniform-advection check, not an interacting foam replacement.
Capillary raft interactions, drainage/rupture and reference appearance remain
open. No full froth bake runs; all eight original feature cases remain open.
The next incremental study adds reduced-model capillary attraction between
two solved bubbles at the reference's Bo=1, Mo=1e-4 condition (44.15 mPa s,
not ordinary water). Angular boundary sampling corrected a failed mesh-volume
gate. Geometry refinement, isolated pressure/volume checks and the saved
native animation's full/half-frame checks pass. Pair superposition is still
approximate and does not prove coupled 3D pressure balance. Builder 50689,
saved-scene audit 58420, render 91062 and encoder are all DONE. The 12-frame
MP4/APNG and self-contained native scene are delivered in
`bubble-pair-reference-v1`; all decoded frames and source/copy hashes pass.
It is a normal-speed half-second pre-contact study, not an accepted interacting
foam replacement. Water-volume range is 0.00213%; gas mesh error below 0.096%.
Actual first/middle/last engine frames were inspected. Pair deformation,
ordinary-water dynamics, film drainage/rupture and reference appearance remain
open. No full froth bake runs and no cache was deleted. All eight cases remain
open; do not duplicate terminal processes or present the pair as full foam.
The separate aerated-froth/spray environment is now prepared as a finite
plunging jet into a closed tank. Scene tests and its matched velocity
calibration are complete. V1 bake 2323, audit 29619 and preview render 99161
are DONE. Actual solver-field liquid volume grows about 19.6% after inlet
shutoff, so v1 is rejected, not a completed froth feature. V2 changes only
fractional boundary handling; bake **32634** is DONE and rejected: its liquid
volume falls 73.2% after shutoff. Final VDB audits and inspected engine previews
confirm the loss. Guard 32658, audits and preview 16560 are all terminal.
Do not duplicate them. V3 `froth-jet-v3-radius090` is prepared/tested, changing
only the primary liquid reconstruction radius to 0.9 versus nonfractional v1.
It is NOT baking: the disk preflight refused before launching (last free space
7.69 GiB). Require 11 GiB free and a 3 GiB owned-process guard before starting.
No cache was deleted; no write-access blocker occurred. Failure evidence is
preserved in `froth-jet-v2-failure`. No froth clip or acceptance yet. See
`docs/water-feature-lab/froth-review.md` for dimensions, limits and phase checks.
After disk recovery the goal resumed. The MODULAR radius-0.9 base bake 15863
is DONE (120 frames, 190.09 s, 699 MB), but its VDB audit still shows 13.4%
post-shutoff volume growth. V3 is rejected; mesh/secondary stages are unbaked.
V4 `froth-jet-v4-radius080-modular` changes only primary reconstruction radius
to 0.8; snapshot comparison and scene tests passed. Its guarded base bake
65701 and VDB audit are DONE, but still show 7.8% post-shutoff volume growth.
Both v3/v4 remain rejected, with no mesh/secondary promotion or new froth clip.
Eight copied diagnostic reports in `froth-radius-comparison-v1` are hash
verified. No Blender job remains live; do not duplicate the terminal runs.
Stop the radius sweep: next isolate drift with a matched no-inflow control
and investigate actual flux/time-step sensitivity. Full froth, not a
liquid-only diagnostic or a tuned volume metric, remains the deliverable.
See `docs/water-feature-lab/secondary-optics-review.md` for the next fixed-cache,
phase-separated optics experiment and the limits of the current white spheres.

The matched unforced radius-0.8 pool control is DONE (base bake 19844, original
VDB audit and reopened scene tests terminal). Its negative-phi outside-solid
volume is identical at sampled frames 2..120 after initial settling. Thus the
jet's 7.8% late growth is not reproduced by the unforced pool at voxel-count
resolution. Corrected staggered-face flux readback now uses Blender's engine
mapping, which differs from VDB storage spacing; native arrays and three
synthetic tests pass. Coarse below-nozzle flux substantially exceeds nominal
flux, but partial-face/source budgets and calibrated uncertainty remain open.
This is diagnostic work, not a new animation or an accepted froth replacement.
Temporal-refinement candidate `froth-jet-v5-r080-time2-modular` changes only
min/max substeps 2/8 to 4/16 and CFL 2 to 1; reopened scene tests pass. Guarded
base bake **58513**, owned PID **35748**, is DONE (392.51 s, 120 data frames).
Original VDB audit and reopened scene tests are terminal. Post-shutoff volume
growth worsens to 11.53%; v5 is rejected, with no mesh/secondary promotion.
Nine control/flux/v5 report copies are hash verified in `froth-control-flux-v1`.
No Blender job remains live; do not duplicate terminal bakes. Stop blind
radius/time sweeps. Next independently refine partial-cell volume and account
for source-region flux to distinguish reconstruction counts from liquid-budget
error. Keep all eight feature cases open and preserve every old cache.
See `froth-review.md`; no new animation or visual acceptance is claimed.

Independent partial-cell interface integration and subinterval bounds are now
implemented; five analytic/synthetic tests pass. V4's reconstructed fields
require at least 6.02% growth after shutoff even with favorable integration
bounds; whole-cell counting cannot explain it away. Refined control estimates
show small settling changes hidden by identical sign counts, not exact mass
conservation. Original v4 emission extends below/outside the nozzle. V6
`froth-jet-v6-contained-inlet-modular` fixes cylinder containment and removes
source dilation while keeping every v4 writable domain setting unchanged.
Base bake **68798**, owned PID **19704**, is DONE (208.94 s, 120 data frames).
Native tests and cached-field audits pass the sampled source containment:
zero negative inflow centers below/outside the nozzle versus 86/64 in v4.
But v6 is rejected for full froth acceptance: 7.00% post-shutoff sign-volume
growth, and refined interval bounds still require at least 5.24% growth.
No mesh/secondary promotion or new animation. Fourteen original reports are
hash-verified in `froth-interface-inlet-review-v1`; all jobs are terminal.
Next address moving-liquid reconstruction/transport and source-budget
consistency without fitting net error. Retain the contained-inlet correction,
preserve old caches, and keep all eight physical/visual deliverables open.

Next: implement/validate the foam and froth studies, improve the boil's surface
reconstruction, eddy trajectories and wave boundaries, and resolve the hole's
flux/boundary and entrainment issues. Also refine the waterfall's inlet, spatial
resolution and froth. Keep all eight cases in scope; one clip is not completion.

Latest transport check: APIC96 calibration and its independent cached-field
centroid both fail gravity (37.84%/42.71% error). V7 is rejected before a full
jet bake; the modular baker's native early-rejection guard passes without
marker/cache writes. Do not run it. Partial-face flux quadrature and eight
flux tests pass, but the corrected v6 plane discrepancy remains; nominal
area times emitter velocity is not an imposed flux boundary. Source/storage
accounting remains open. FLIP144 matched calibration passes (3.275% particle
gravity error; independent field 1.960%). V8 changes only resolution96->144,
retaining the contained inlet. Its base bake **81802**, owned PID **38880**,
is DONE (1030.09 seconds, 120 frames, 1.687 GB); native tests and audits
74387/69580/56433 are terminal. V8 is rejected: 12.13% post-shutoff sign-volume
growth; independent bounds require at least 10.76%. No mesh/secondary stage.
Stop the resolution sweep. Actual jet area narrows and mean speed increases
downstream, but section flux and interface drift remain unresolved. Four new
MAC-divergence tests pass; cached interior consistency cannot prove substep
pressure accuracy or rule out interface/boundary errors. Next isolate stage-wise
interface reconstruction/resampling and boundary budgets in controlled moving
liquid, without post-hoc volume correction or tuning errors to cancel. No Blender
job remains live; do not duplicate terminal bakes. Ten copies are hash verified in
`froth-transport-review-v1`. No new animation or acceptance; all eight cases
remain open. Seven more reports are hash verified in `froth-spatial-rejection-v1`;
original VDB hashes are unchanged. See `froth-review.md` for exact checks/limits.

Reference starting points (no external media bundled):
- Blender Mantaflow introduction: https://developer.blender.org/docs/release_notes/2.82/physics/
- Secondary particle definitions: https://docs.blender.org/manual/en/5.0/physics/fluid/type/domain/liquid/particles.html
- USBR hydraulic design/experimental reference: https://www.usbr.gov/tsc/techreferences/hydraulics_lab/pubs/EM/EM25.pdf

## Scheduler

Latest bounded continuation (October1, actual padded-bed native eddy): a new
two-second transparent-water comparison is DELIVERED in
`docs/water-feature-lab/eddy-padded-bed-comparison-v1/feature.png`.
Fresh192-frame FLIP evolution adds three computational cells BELOW the
unchanged authored bed; same75mm grid, physical geometry/sources, gravity,
2/8 timesteps and24fps. Installed-native plane controls locate loss of the
old floor interface during obstacle extrapolation when its only negative
seed is in the excluded bottom row. Actual padded cached bed zero survives
all192 frames. Three matched primary-particle checks reduce worst floor
intrusion37.288->0.604mm, not zero; slope/spur contact still fails. The stock
particle mesh STILL penetrates the bed54.726mm. Field-derived floor contact
passes sampled checks, but slope/spur mesh intrusion remains8.139/20.833mm.
Do not claim solver/contact/eddy acceptance or substitute a polished surface.
Both controls have30 extraction checks; all padded derived meshes pass
closed-edge/zero-area gates but all30 fail sampled overall contact acceptance.
One of54 columns is ambiguous at frame147 and retained. Rendering is actual
matched48 views with unchanged water IOR1.333 shader, flat triangle normals,
no fake foam/displacement/smoothing/contact clipping.24-frame APNG is verified
losslessly at12fps,1280x476; first/middle/last views inspected, motion changes
exclude captions. No retiming; not a seamless loop.12 delivery/evidence files
are copied/hash-verified; see newREADME for preserved paths, failed guarded
preparation attempts, exact scope and costs.156 pure tests pass;8 scripts
compile. DATA2263/MESH7521/audits62854,59355/particle75330,84976/render73805
are terminal0; encoder is terminal0. No live owned jobs, old cache edits,
Git writes, playable integration, gameFPS or accepted foam/froth claim.
Next resolve authored slope/spur versus cached obstacle geometry and primary
contact, then consistent meshing. All eight features and river integration
remain unfinished; keep the current isolated-feature goal active. Old hourly
full-river heartbeat prompt remains obsolete; its previous edit was denied.

Latest bounded continuation (October1, copied-field mesh extraction): a new
two-second MOVING eddy comparison is DELIVERED in
`docs/water-feature-lab/eddy-field-mesh-comparison-v1/feature.png`.
24 frames at12fps,1280x482; preserved standard FLIP evolution193..239,stride2,
same authored colliders/lights and fixed full-liquid view in both panels.
Both use opaque geometry-diagnostic shading and flat triangle normals, NOT
accepted water/foam optics. All decoded frames match composed originals
losslessly; first/middle/last native views inspected. The field-derived surface
is visibly more faceted, not an accepted visual improvement. No fake foam,
source-cache edits, radius tuning, altered solver, smoothing or retiming.

Native controls COMPLETE:15 affine plane/orientation/grid-phase cases plus
36 preserved flat-control cases,extraction refinements1/2/4. Original cell-center
knots are preserved; ordinary resampling was rejected for0.625mm surface shift.
Maximum plane error4.121e-7 base cells; flat queried height discrepancy <=37.02nm,
no axis-box vertex penetration. Exact-coordinate duplicate merge and EXACT
zero-area removal do not move vertices; raw native output remains preserved.
Overall geometry qualification is FALSE: calibrated f1/r2,f1/r4,f48/r4 retain
21/27/3 boundary edges. No tolerance widening or dropping failed cases.

Moving eddy audit COMPLETE:24 r2 frames plus r1/r4 at193/217/239,30 meshes,
all closed-edge/zero-degenerate checks pass. All54 query columns remain supported.
Median absolute column mesh/phi gap14.241..19.123mm in original particle meshes
versus0.0000567..0.0001062mm in copied-field meshes. These are float32-BVH
numerical query residuals, NOT submicrometre physical accuracy. Worst retained
near-contact column gap6.3768mm. ALL30 sampled authored-solid contact gates FAIL:
floor/approach penetration62.5mm; r2 bank-spur maximum20.8335mm. Matching native
phi_obstacle is not matching the actual solid geometry. No candidate promotion.
Mesh signed volumes change with extraction; they are NOT conserved liquid mass.

51-control910 inputs, moving1650 inputs/90 outputs, render48 views and clip are
hash-pinned;1793 combined inputs/outputs independently rehash unchanged after
encoding. Five new delivery files (14.08MiB) are copied/hash-verified.156 pure
tests pass; native controls30127/audit4457/render29447 and encoding/copy finish0.
No owned Blender job remains. Original/live phi fields and all old captures
remain unchanged. Offline extraction51.19s/render266.75s,NOT game20FPS.
All8 features and eventual river integration remain OPEN; full user goal active.
Next reconcile native obstacle-field boundary zeros/flags with actual authored
floor/bed/spur before a controlled physical repair; validate moving surface
transport/mass/contact and real foam/froth afterward. Do not repeat these completed
controls or hide contact with particles/materials. Full evidence and failed
attempt history:eddy-field-mesh-comparison-v1/README.md (the existing surface
review append failed; this sibling handoff is preserved). Old hourly full-river prompt is obsolete;
its attempted replacement was denied, so do not alter it without user authority.

Latest bounded continuation (September30–October1, manufactured flat-water control):
`docs/water-feature-lab/flat-equilibrium-control-v1/feature.png` is DELIVERED:
two seconds,24 native-view frames at12fps,three matched panels. Blue is an
explicit opaque geometry-diagnostic shader, NOT accepted water/foam optics;
gold marks the analytic wet-box walls and intended0.9m height. No native mesh
clipping/correction, artificial motion, foam projection or simulation retiming.
All24 decoded frames match composed originals losslessly. First/middle/last
actual views are inspected. Cropped initial preview is rejected/preserved;
final fixed camera checks every mesh bounding box with3-percent frame margin.

Three new private native controls COMPLETE: visualization-root
`flat-equilibrium-v6-stock-m2`, `stock-m8`, `flat-lattice-m2`.32x24x24 cells,
75mm spacing,closed box,zero initial velocity,no emitters,gravity/pressure ON,
same44800 zero-jitter quarter-cell particles. Exact compiled FLIP body and mesh
recipes run on owned resources, not modified live engine resources.96/384/96
fixed steps; integrated time1.999999952s,native final clock2s. First particle
union agrees with independent analytic lattice within8.924e-8 cells (fixed
allowance2e-6); initial zero-velocity phi advection bitexact. No APIC switch.

Stock first join raises the interior interface41.2108mm BEFORE pressure.
After2s,stock median height errors41.2176/41.2313mm;2-vs8-step median absolute
difference only0.04342mm. The flat-lattice radius0.718713553878169 is derived
analytically for THIS horizontal grid-phase/8-per-cell seed only. It leaves
final queried height errors -0.00413..+0.04525mm, but native mesh-minus-phi
median remains+36.7878mm; maximum vertex wall intrusion53.0657mm (stock91.2495mm).
Do NOT promote the radius as a general physical repair. Native mesh/field/wall
consistency and reconstructed volume remain FAILED. This still-water control
does not reproduce or uniquely explain the eddy's large timestep sensitivity.

All49 fields/meshes per control are independently audited; missing support is
not filled.147 meshes have zero exact degenerate triangles and closed edge
counts, NOT certified absence of self-intersection/collision. Native OBJ/raw
node/triangle coordinates and indices are verified against the exact-build
Apache2.0 source.905 audit dependencies and982 clip dependencies rehash unchanged.
145 combined pure tests pass; all owned controls/audit/render/encode jobs finish0.
Three new controls total245.77MiB; original source inputs/live-field fingerprints
and older captures/clips remain unchanged. External Unreal work was observed;
costs are unisolated offline timings, NOT20FPS. No river build/integration or
feature acceptance is claimed. All8 standalone cases and eventual integration
remain OPEN; the full isolated-feature goal stays active. Next consistent native
interface/meshing/walls and orientation/phase/spacing controls, then actual moving
foam/froth; do not repeat the completed still-water run or resume the obsolete
full-river heartbeat. Details and rejection history:surface-foam-review.md.

Latest bounded continuation (September30, native host-backed controls): a new
two-second side-by-side native eddy animation is DELIVERED in
`docs/water-feature-lab/eddy-temporal-comparison-v1/feature.png`.
24 frames,12fps,1440x348; unchanged native mesh, fixed camera, modeled studio
lighting, low-cost4-sample Cycles/denoising, no secondary particles or corrective
projection/clipping/retiming. All decoded frames match the annotated originals
losslessly; all23 adjacent LIQUID image comparisons in each panel differ (text
changes are excluded). This is a liquid-motion diagnostic, NOT accepted foam,
optical fidelity, circulation, collision, shoreline or gameFPS. Exact zero-area
native triangles remain in normal frames221/237 (2/4) and quarter frame219 (2).
Do not conceal these by reporting only the sampled frames without defects.

Three fresh serial controls, `tmp/water-feature-lab/eddy-temporal-resume-v6-m2`,
`v6-m4`, `v6-m8`, COMPLETE native data and mesh from copied resumable frame192
through193..240. Same physical scene/geometry,75mm cells,FLIP,24fps,time_scale1;
min/max timestep bounds2/8,4/16,8/32 only. Actual host source/obstacle rebuilding
runs.11 seed grids match independent VDB bitexact; primary loading succeeds.
Native compiled liquid-step entry/return is observed in the actual bake thread
with frame handlers/profiling, without replacing any solver function.96/192/384
steps are observed.48 data/config/mesh outputs plus preserved192 seed per case;
all original input/source hashes remain unchanged. These are serialized resumes,
NOT proof of identity to an uninterrupted bake; no secondary stage was baked.

Equal NOMINAL frame span is2s; each actual C01 endpoint span is1.999987793s.
Observed liquid-step dt sums are2.001926422/2.001926315/2.001926494s: the native
integrator/frame-clock discrepancy is exposed, not silently retimed away.
Independent audit retains the same54 earlier query columns and samples native
mesh/fields at193/194/204/216/228/240. At240 normal-to-half absolute vertical
base-phi differences have median52.3473mm,p95130.037mm (54 supported columns);
half-to-quarter median32.3035mm,p9589.9578mm (53/54; absent column retained).
Native mesh signed volumes at240 are3.599114/3.414310/3.429743m3, NOT particle
mass closure. Median mesh-first-upward-ray minus phi gaps are17.09/14.81/20.27mm;
ray hits may include detached droplets and are NOT qualified mesh normals or
material speeds. No convergence threshold has passed; none of the3 is promoted.

Native jobs94421/41586/54819 and render jobs4949/30773/23040 finish0. Native data
costs10.08/21.71/39.33s, mesh5.24/5.56/5.85s.24-frame render costs41.41/44.73/
42.07s. These are offline costs, NOT the20fps playable target. Fresh controls
total412.61MiB; earlier partial attempts are preserved, not recooked. Failed
v1/v2/v3 lacked a seed after RNA timestep setters invalidated the *new copied*
cache. The corrected runner redirects first, changes settings, THEN copies the
seed. This was not a broken VDB payload or new disk-capacity failure. v4 data
bake finished but old function wrappers saw0 steps after native recompilation;
its failed receipt/data are preserved and not treated as qualified controls.
One-frame v5 probe verifies actual profiling and native mesh, finish0. Do not
retry any unchanged failure or touch original caches with invalidating setters.

Independent audit `eddy-native-temporal-resume-20260930-v1.json` in the
visualization root:1495164bytes,SHA256
17d00ffc182dfa0a925271f5f142134309b0eaf75a611f50bbfc468398613a07.
All692 audit dependencies rehash unchanged. Clip receipt independently verifies
775 dependencies including audited caches and72 source renders; APNG SHA256
c6e79f86db5a1c2b0790c29b72e50cc5d8e26e0c82db252863bbbd9e053f13a9.
Six new pure clock/cohort tests pass;133 combined tests pass. Next isolate
source sampling/resampling from per-substep particle reconstruction in a
manufactured steady-interface control, with matched mass/flux and native mesh
checks. Do not solve timestep sensitivity by picking the prettiest variant,
enabling broken APIC, hiding defects, or projecting foam onto an unqualified
surface. All8 features and river integration remain open; full goal active.

Latest bounded continuation (September30, resumed on D:): the actual compiled
eddy liquid-step body now runs on newly owned in-memory resources, with no
live solver/grid/particle alias. Eight fields (including resumable phi and
previous fields) match independent VDB payloads bitexact before evolution;
all88450 primary positions/velocities match actual native scene API. Six
affine native advection controls pass, maximum1.095e-6cell error under the
fixed2e-5cell allowance. Eight ownership and four column-interface controls
are added;127 combined pure tests pass. Original engine phi/previous phi and
velocity/previous velocity fingerprints and all original input hashes stay
unchanged. Only fresh diagnostic arrays and receipts were written.

Three private single-step controls use20.8333/10.4167/5.20833ms from identical
cached inputs. Across the same54 prior columns, median absolute vertical
base-phi change from advection alone is2.58645/1.75921/0.888942mm; subsequent
particle reconstruction changes that interface another4.07749/3.16567/
1.59983mm. These are vertical zero crossings, NOT rendered-mesh normals or
material speeds, and unequal elapsed times are NOT temporal convergence.
All54 have one valid upward crossing; the24 earlier missing columns and35
normal-neighborhood failures are still unqualified. This directly demonstrates
an interface change beyond advection in this local native mechanism experiment;
it does not prove a unique cause of the earlier rendered-motion mismatch.

Native jobs75877/92641/8168 all finish0 with complete receipts. Analysis receipt
eddy-native-interface-reconstruction-20260930-v1.json, visualization root,
SHA2568817eb4db9c1165716a42c48814627808c01c6bbba882e0cf15a982c8626ed72.
All446 analysis dependencies and3 executed analysis modules independently
rehash unchanged. Existing caches, meshes, scenes and delivered clips are
preserved; the drive move is handled only by unsaved process cache relocation.
No native host emission/pre-step/source rebuild, mesh or secondary replay was
run; zero uncached force/solid velocity is explicitly scoped, not recovered
bake chronology.5.38..5.67s measured diagnostic costs are not gameFPS.

Next compare equal elapsed-time private evolution with the actual case's
pre-step/source boundary state and matched mesh extraction, tracking particle
reconstruction separately from advection and pressure/velocity update. Do not
fix the apparent mismatch by retiming cache fields, silently projecting foam,
or accepting a frozen/analytic control as the requested liquid-coupled feature.
This turn delivers a reproducible native evolution experiment, not a new
animation or a physically accepted feature. All8 standalone cases and eventual
realistic river integration remain unfinished; full goal remains active.

Latest bounded continuation (September30): exact case-specific stage/clock
evidence is preserved in visualization-root
eddy-cache-stage-clock-20260930-v1.json, SHA256
8e228ef7b45ded0d1a406594e4994d00a9a0baeb296c066d37a3147d97699dd1.
All288 C01 configurations parse;287 intervals are strictly increasing and
agree with24fps/time_scale1 to float32 accumulation accuracy. Stored dt is
the last adapted step, not the complete substep schedule; Blender clamps the
host total time at each frame end. The playback-loaded solver clock is zero
and is NOT a saved simulation timestamp. Exact live compiled liquid-step code
copies previous phi/velocity only at the beginning of an adaptive frame.

Seven pairs168/190/191/192/193/194/214 verify previous velocity equals the
prior frame's final velocity bitexact. Previous phi differences occur only
inside cells marked obstacle by the current final flags in those seven pairs;
this is not a measured free-surface displacement. Mesh extraction uses current
phi/primary particles; secondary evolution uses beginning-frame snapshots.
Playback loading initializes phi and previous fields rather than loading
their resumable values, so these must be loaded explicitly for a private
evolution test. No native step or cache correction was performed by this audit.

The repository moved to D:/repos/SmokeEmIfYouGotEm. Independent read-only
rehashing at that location confirms all312 original inputs and5 executed
modules match the preserved receipt, without rewriting old path provenance.
115 combined pure tests pass. Next reconstruct a private, explicitly resumed
native evolution and observe advection versus interface reconstruction, not
retime fields or project foam onto an inconsistent mesh. No new clip or
feature acceptance; all8 cases and eventual river integration remain open.

Latest bounded continuation (September30): native MAC extension provenance is
now independently reconstructed and checked against installed Blender
fbe6228777e7, not inferred from two-liquid-cell support. Eight new controls and
108 combined pure tests pass. Corrected native audits785d31/a2aaa1 finish0:
20 manufactured native comparisons plus frames168/192/214 match bitexact over
all512406 interior scalars. Boundary copy and obstacle-normal unprojection
are deliberately out of scope; all boundary provenance remains unsupported.

All54 prespecified frame192 surface stencils have native extension support.
Four trace obstacle contact: columns[32,12],[32,15],[40,12],[40,15]. This does
NOT qualify their forces/transport or repair the35 retained failed normal
neighborhoods. End-cache replay is not bitexact: serialized seed/extension
rounding is a possible contributor, not a proved unique cause. No fitted
tolerance is used to pass the independent/native interior comparisons.

The same52-query cohort retains median0.063593m/s cached versus0.063564m/s
replayed-extension normal mismatch. Maximum replay/cache normal-speed change
is0.0000976924m/s; replay does NOT reconcile moving mesh and velocity. The
50 queries without obstacle-contact lineage still have median0.061611m/s
replayed mismatch. Next establish exact case-specific stage/time provenance
and evolving-interface agreement; do not simply replace the strict sampler,
retime velocity_previous, project away mismatch or enable these values as
a foam driver. Native support is distinct from physical validity.

Final332288-byte receipt: visualization-root
eddy-native-mac-extension-20260930-v2.json,
SHA256e7b8f7aa3d157b212d00ea18b71838dec3afd2edea23bb71c372f125f4b3cbfe.
All20 captured inputs/receipts and4 executed modules independently rehash
unchanged. v1 evidence is retained. Initial bare-Manta wrapper probe failed
before extension and crashed during teardown; loading/evaluating the preserved
fluid scene initializes the missing base-grid API, and corrected cleanup
releases children before solvers. This is NOT a filesystem access blocker.
All owned jobs terminal;2.04s audit cost is not gameFPS. No original cache,
mesh, scene, delivered clip or normal game changed; no physical/visual feature
accepted. All8 cases remain open and the current isolated-feature goal active.

Latest bounded continuation (September30): moving-interface consistency is now
measured against five actual preserved meshes190..194 and calibrated native
frame192 velocity, not frozen-mesh prescribed markers. Six new analytic
kinematic controls pass;100 combined pure regressions pass. Native audits13048
and48453 finish0, all19 captured inputs/receipts unchanged, central geometry
hash preserved, native grid/RNA velocity bitexact and actual24fps/time_scale1
checked.54 prespecified prior queries retain temporal distance support;52
have both one-sided fits, two near-contact fits remain missing. The existing
24 missing prior regular columns are retained in the receipt's coverage.

Material-surface normal-speed disagreement is NOT accepted: radius2.5/3.5
median0.08340/0.09560m/s, maxima0.60212/0.66362m/s. One-frame versus two-frame
central stencil disagreement has median0.01656m/s,p950.09825,max0.15202. A raw
staggered-cache comparison still has median0.06359m/s,max0.53347 on the SAME52
query cohort; none of these raw probes has all8 strict liquid/liquid source
corners in each component. Ghost/extrapolated-face validity remains unproven;
do NOT enable raw interpolation as a surface sampler or force velocities to
match the mesh. These measurements do not identify a unique solver cause or
establish temporal convergence. Next establish matched native extrapolation/
stage provenance and shared evolving-interface/velocity agreement before
liquid-coupled interacting foam. Do not repeat the unchanged measurement or
present static facet/control animation as that missing coupling.
Receipt: visualization-root eddy-surface-kinematics-20260930-v2.json,
SHA256fc622114ddf011997995d4f4fbfcc59eda18f7e75210879a8558da7fd172a2c0.
Source/receipt writes succeed; all owned jobs terminal.43.37s measured audit
cost is NOT FPS. No geometry/cache repair, new render/clip or feature acceptance
claimed. All8 physical/visual cases remain open; full goal remains active.

Latest bounded continuation (September30): static facet-event transport and
native playback are now verified components, NOT physical foam/flow. Eight
transport tests and five float64 nearest-distance controls are implemented;
94 combined pure regressions pass. Native audit61346 finishes0:52 of54 fresh
query paths complete; the two remaining paths stop explicitly at collider
contact, not silently lifted/continued.34 successful paths were previously
failed normal-neighborhood queries; this does NOT qualify those normals or
their fitted velocities. Constant prescribed50mm/s paths stay on the original
static facets, preserve speed and match20-step versus whole2s integration.
All52 objects retain every event key and pass97 native full/half-frame poses;
maximum readback error0.472micrometres, nearest distance0.307micrometres, with
the unchanged2micrometre native allowance. No new render or saved animation.

Three diagnosed numerical/playback failures are fixed without moving geometry:
accumulated terminal timestamps previously missed the exact requested endpoint;
float BVH omits captured thin triangle17078 and falsely reports2.450micrometres
of separation (float64 complete AABB candidates give1.57e-16m); per-event native
insertion merges11 keys into10 at0.00257frame separation, producing5.263micrometre
readback error. The failed v3 receipt is preserved. Bulk key arrays retain11/11
and reduce that path's maximum error to0.077micrometres; no contact gate relaxed.
Receipt: visualization-root eddy-facet-transport-20260930-v4.json, SHA256
99a2cae9bd19b170363d19e47d00d87788bb2b5bdf9b3b3cd169972e75767799.
Eleven original inputs/receipts and all three executed modules independently
rehashed unchanged. Prior caches, geometry and clips remain untouched. Native
owned jobs are terminal; no source/receipt write blocker. Actual elapsed15.92s
is diagnostic cost, NOT game FPS. Next evolve the shared mesh/interface and
validated liquid velocity together, then integrate interacting wet-foam forces
and phase changes before delivering actual foam motion/optics. Do not pass off
this frozen-mesh prescribed-marker audit as liquid-coupled foam or a new clip.
All8 feature cases remain physically/visually unaccepted; full goal stays active.

Latest bounded continuation (September30): actual-render mesh-interface
component is implemented and independently tested (10 new tests;81 pure
regressions pass). Native audit60293 finishes0 on preserved frames168/192/214;
all three prior render geometry hashes and ten original inputs/receipts remain
unchanged.55/54/56 of78 regular columns yield genuine shared-interface
queries, maximum residual3.34e-16m; no existing particle or mesh is shifted.
BUT fixed50-micrometre normal-neighborhood controls fail32/35/28 queries;
these receive NO velocity fit/transport qualification. Remaining fit coverage
is only22/18/26, and radius sensitivity remains unaccepted. Rounded BVH ray
hits near lattice/crease boundaries must not be treated as exact facet
queries: two initial audits30064/27713 fail, diagnostic identifies a2nm
ray/nearest mismatch and1.43micrometre normal-distance error. Revised audit
checks actual float64 triangle membership, uses its actual supported normal
and reports all missing/failed controls without relaxing their thresholds.
Receipt: visualization-root eddy-shared-mesh-interface-20260930-v1.json.
Source/receipt writes succeed; no live owned Blender job or blanket access
blocker. No new rendering/animation or feature acceptance this turn. Next
time-evolving interface/velocity support with explicit normal-reach/crease
handling before constrained interacting foam; do not animate known unsupported
queries, hide them with offsets, or reduce the objective to geometry tests.
All8 physical/visual feature deliverables remain open; full goal stays active.
See surface-foam-review for evidence and exact next limits.

Latest bounded continuation (September30): separate one-sided surface-MAC
reconstruction is implemented and tested, NOT integrated into foam or a new
animation. Nine new analytic/support tests pass;71 pure regression tests pass
with temporary files in the explicitly writable visualization root. Strict
interior DenseMacField is unchanged. Native audit49634 finishes0 on preserved
eddy frames168/192/214, all original inputs unchanged and all three rendered
geometry hashes match prior evidence. Of78 interface columns/frame,76/75/76
have fits. However native phi-zero and rendered water differ by median nearest
distance15.50/14.13/14.98mm; maximum42.79mm. Reconstruction radius sensitivity
has median0.085/0.091/0.105m/s and maximum0.598m/s. This inferred field is NOT
accepted for surface foam. No cached particle was moved/reclassified, liquid
rebaked or appearance altered. Audit receipt is saved at the explicitly
writable visualization root, eddy-surface-mac-audit-20260930-v1.json; initial
attempt9415 to save in the preserved case directory was denied AFTER all
three measurements. Do not repeat that destination failure. Source edits
succeed; do not describe this as a blanket source-access blocker. Next shared
render/constraint interface and independently bounded surface-velocity/time
support before fresh interacting foam dynamics; do not hide discrepancies
with offsets or loosen interior support. All8 features remain unaccepted;
supporting work only, no delivered visual/game/FPS improvement this turn.
See surface-foam-review for precise limitations and receipts.

Latest continuation (September30): new surface-manifold transport component
and numerical/control animation are delivered in surface-manifold-control-v1
(2s,24 native frames,12fps,800x450). This is fresh imposed-geometry marker
dynamics, NOT physical foam morphology or a liquid solve; no old eddy particle
is lifted/reclassified. Bounded normal constraint and tangent-speed retention
pass8 independent tests;62 pure numerical/regression tests pass this turn.
At equal24Hz timestep, constrained marker tangent speed is retained while an
explicit closest-point/velocity-projection baseline falls24.4%. Exact sphere
trajectory error472/117/29 micrometres at48/96/192 steps shows convergence,
not zero physical trajectory error. Initial baseline assertion31758 fails
because it reused the same old-normal constraint; corrected independent
baseline is a different integration scheme, not a Mantaflow replay.
Builder28267/render13399 and encoder are terminal0. Saved native scene is
reopened and97 full/half poses of8 markers match numerical interpolation
within7.04nm; half-frame chord interpolation misses the manifold by58.89
micrometres, explicitly open. All24 decoded APNG frames equal native renders,
no adjacent duplicates; actual first/middle/last views show motion/occlusion.
Caption/studio appearance remains a diagnostic, not accepted foam optics.
Native scene/trajectories/audit/capture copied and hash-verified; previous
eddy scene/animation unchanged. No Blender job remains live. Source/case
writes succeed; no scoped access blocker. Next justified boundary/surface
velocity sampling, then tangential wet-foam interaction/SPH and bubble
transitions; do not loosen the strict interior MAC sampler or use zero flow.
All8 cases and full isolated-feature objective remain unaccepted, including
formation/breakup/persistence, froth and optical calibration. Do not substitute
this imposed-sphere control for the requested foam animation or resume the
obsolete full-river scheduler. No game integration/20FPS claim. See surface-foam-review.

Latest continuation (September30): bounded occupancy completion is tested and
freshly baked in eddy-v4-boundary-completed, then delivered in
eddy-boundary-completed-study-v1/feature.png (24 verified frames,2s). The
independent native reference finds radius-two occupancy leaves near-boundary
fluid cells at zero; completion changes only those omitted centres before
native phase generation/transport, not cached types/positions, thresholds,
forces or liquid motion. All288 callbacks verify the native interior reference;
577,371 fluid-cell visits completed. Guard39516 finishes131.91s/4.694GB,
more expensive than the baseline. Independent mapping68342 agrees at three
frames, maximum position component error0.477 micrometres. Spray counts fall
42..57%, but 90.67..93.92% of sampled spray remains inside liquid; foam
97.56..98.46% inside. One frame214 ray is explicitly unknown (not outside),
recorded with bounds in secondary-mesh-v2.json after initial audit30146 fails.
Preview74594/full render7577 and encoder finish; viewed first/middle/last frames
still have submerged white grain and paper-like ribbons. Physical/visual
acceptance rejected. All24 liquid geometry hashes/primary counts match v3;
all frames edge-closed with0 exact-zero facets,0..4 tiny positive facets remain.
Native/pure tests72 pass; eight small receipts copied and hash-verified.
Original864 cache files, copied576 data/mesh files, source blends and sampled
audit inputs rehashed; old animation unchanged. No Blender job remains live.
Next surface-interface generation/transport with independent invariants, not
lifting particles or fitting density. Circulation/mass/flux remain open, all8
features unaccepted. Continue the current isolated-feature goal, not the
obsolete river heartbeat; no normal-game update or20FPS is claimed. See
eddy-review for source evidence, native warnings and exact correction scope.

Latest continuation (September30): native eddy secondary phases are baked and
shown in eddy-native-phases-diagnostic-v1/feature.png (24 losslessly verified
frames,2s). This is a REJECTED phase-placement/appearance study, not acceptance.
An independent native VDB read matches all phase types, positions and velocities
at168/192/214; maximum position component error0.477 micrometres. Actual rendered
mesh tests,4096 deterministic samples/phase/frame, place94.65..95.36% of spray
and98.71..99.10% of foam inside liquid. Submerged median distances are about
41..53mm spray and46..49mm foam. The viewed clip has excessive submerged white
grain/ribbons. This is not a display-coordinate error; native classification/
transport versus the liquid interface requires investigation before a physical
correction. Do not lift particles, relabel cached types or fit radius/density
to disguise it. Original liquid motion and all24 geometry hashes are unchanged.
Independent cache copy662.85MB plus288 secondary VDBs3.942GB; original864 cache
files and copied576 liquid-data/mesh files rechecked unchanged after rendering.
Guarded bake67539,render95349,native tests85299 and preservation16827 are terminal0.
64 pure/native checks pass; six receipts copied/hash-verified. All8 features
remain open, including sustained eddy circulation/boundary budgets. No game
integration,20FPS or later-river acceptance. Do not rebake this unchanged stage.
See eddy-review for exact placement, optical and native-warning limitations.

Latest continuation (September30): a vertex-preserving mesh repair is integrated
into eddy-preserved-vertex-study-v1/feature.png,24 verified native frames/2s.
Captured frame192 polygon shows custom dominant-axis projection collapsed two
distinct endpoints; orthonormal-plane ears fix it, without moving coordinates.
Measurement correction: old float64 areas followed a float32 world transform;
new affine float64 measurements distinguish true zeros from lost separations.
Unrepaired168/192/214 has41/41/39 exact zeros; repaired has0. Keep old receipts.
Corrected six-frame contact audit94975 and all24 clip frames are edge-closed,
with0 exact-zero triangles, every distinct coordinate/existing triangle retained.
0..4 tiny positive-area facets/clip frame and34.75-micrometre bed residual stay
OPEN. Render89867/encoder terminal0; all decoded RGB frames match native PNGs.
The overall appearance remains pale/similar; foam is hidden/unbaked, circulation
and mass/flux remain unvalidated. This is extraction repair, not solver physics.
61 pure/native tests pass, not feature acceptance. Five receipts copied/hash-
verified; original blends,288 VDBs,six sampled native meshes unchanged; no live
Blender job. Next settled circulation/boundary budgets and full foam/froth phases,
not repeated unchanged tiny-facet diagnostics. All8 cases and current isolated
goal remain open. No game integration/FPS claim; preserve all old evidence.
See eddy-review for correction scopes and rejection evidence.

Latest continuation (September30): a two-second modeled-daylight eddy APNG is
delivered in eddy-daylight-study-v1/feature.png,24 losslessly verified native
frames. A matched48-sample studio control confirms broad white patches are
studio reflections; water material/geometry/cached motion are unchanged.
All24 geometry metrics and three full geometry hashes match the prior study.
Daylight is modeled, NOT captured/calibrated lighting; secondary phases remain
unbaked/hidden. Precision probe finds actual zero-area triangulation defects,
not float32 noise. Native BEAUTY cleanup still leaves66..71 tiny triangles;
strict constrained ears reject an unresolved native polygon. Neither candidate
is promoted. Keep both failures and all caches/clips. Daylight65195/control88824,
precision82409 and native tests are terminal; constrained58197 exits1 cleanly.
57 pure/native tests pass, not physical acceptance. Four receipts are copied/
hash-verified; original base blend,288 VDBs,six sampled mesh files and mesh blend
are unchanged. No Blender job remains live. Next unresolved polygon/contact
repair without moving the free surface, optical evidence, settled trajectories/
budgets and original foam/froth. All8 deliverables remain open. Keep the current
isolated-feature goal active, not the obsolete full-river heartbeat; offline
render/playback does not demonstrate playable integration or20FPS. See eddy-review.

Latest continuation: a new two-second aligned-eddy surface/contact APNG is
delivered in eddy-solid-contact-study-v1/feature.png,24 verified native frames.
Native mesh stage80091 completes288 frames in30.12s, with all base VDBs and
base blend preserved. Raw mesh contact audit64821 finds54..70mm solid overlap.
Sequential solid subtraction83186 has tiny open-edge defects; union-before-
subtraction82095 removes those defects in all6 sampled frames and all24 clip
frames. Shared solid material on new closure faces fixes the artificial dark
band; original lighting/water material is unchanged. This is surface extraction,
NOT a solver mass/contact correction. Numerical bed residual31.2 micrometres,
100..109 tiny degenerate triangles and visual/lighting calibration remain open.
Rendered white patches are reflections, not foam; secondary phases are unbaked.
Corrected render66742/encoder and49 pure/native checks are terminal0. Five small
receipts are hash-verified; all288 VDBs, base blend and6 sampled native mesh files
are checked unchanged. No Blender job is live. Next constructive mesh/contact
quality and optics, then circulation/budgets and full foam/froth phases. All8
features remain open. Keep this isolated-feature goal active; do not resume the
old full-river scheduler or infer game integration/20FPS from offline playback.
See eddy-review for rejection evidence and exact scope; preserve every old clip.

Latest continuation (September30): the new grid-aligned eddy candidate completes
its288-frame modular base bake (49.69s,546MB). All nine collider/source/studio
meshes and other physical domain settings match the preserved original.
Matched calibration passes0.2921% gravity error. Actual native data and287,134
primary positions/velocities at three frames validate75-mm field/display
coordinates; the old11.86-mm mapping discrepancy is resolved in those samples.
All121 audited VDB hashes are unchanged. New dense paths agree between mappings
within30.65 micrometres, but only1/48 lasts five seconds and no closed circulation
is established. This is supporting scene/data work, not a visible delivered
clip, mass/collision acceptance or playable integration. Mesh/secondary stages
remain unbaked; do not rerun the completed base bake. Guard37526/audits25092,
83714,95335 and regional/native tests are terminal0.34 pure plus5 native tests
pass; small receipts are hash-verified in eddy-grid-alignment-v1. No Blender
job remains live. Next controlled bed/surface sampling and budget checks, then
guarded collider-consistent meshing and a final foam-inclusive animation.
All eight features remain open; keep the current isolated-feature goal active.
See eddy-review for exact evidence and limitations. Preserve every old cache.

Latest continuation: a two-second eddy tracer diagnostic is delivered in
eddy-tracer-diagnostic-v1/feature.png (24 frames, lossless APNG verified).
All121 original eddy VDBs remain unchanged. The dense-MAC experiment's strict
face/center support still loses nearly all five-second paths, so persistent
circulation is NOT accepted. Three native particle readbacks independently
match isotropic display coordinates, not RNA's anisotropic field mapping.
Preview84286/renders88233/61088 and audits3074/61973 are terminal; no Blender
job remains live. Initial inaccurate seed-support caption is corrected in the
delivered clip; old renders are preserved. Four supporting reports are copied
and hash-verified.36 synthetic/analytic/native checks pass, not hydraulics.
Next align newly authored domain grids and independently validate field,
particle and mesh coordinates/collision, then longer settled eddy trajectories
with valid bed/surface handling; full foam/froth optics remain required.
Froth regional n16/n32 checks locate about99% of local reconstructed growth
in interior intervals, not the outer-boundary operation. Leave that operation
unchanged. Four regional reports are hash-verified; all jobs terminal, caches
unchanged. See eddy-review/froth-review for precise scopes. All eight cases
remain open. No accepted feature, game integration or real-time-FPS claim.

Latest isolated-froth progress (September30): installed-build solver export and
paired native frame-96 local-step probes finish, with every resumed primary
position/velocity/count independently matched to Blender. Displayed particles
use an isotropic object-centered mapping, distinct from RNA's rounded field
mapping; keep both explicit. Saved checkpoint refinement separates inside/outside
extrapolation and outer-boundary changes. The moving jet's n32 local reconstructed
volume increases about0.001906m3, versus0.00001046m3 in the still control; these
are fixed-field integrals, not conserved mass or a full-frame causal proof.
Resampling causes no measured volume change in this step, but its later effects
remain open. Do not disable boundary handling or fit volume to hide drift.
Latest probes79892/control inline run and audits94088/57773 are terminal0;
23 synthetic/analytic/AST tests pass. Eight small reports are hash-verified in
froth-stage-reconstruction-v1. No Blender job is live, no cache changed/deleted,
no new clip or playable integration. Next spatially locate reconstruction and
boundary changes and validate controlled transport/budgets. All eight cases
remain open; full foam/froth animation remains the deliverable. See froth-review.

The attempt to replace the old hourly reconstruction prompt was denied by the
app's approval reviewer. Await explicit user confirmation to change it; do not
work around that denial. The current goal authorizes feature-scene work here.
