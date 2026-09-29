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
See `docs/water-feature-lab/secondary-optics-review.md` for the next fixed-cache,
phase-separated optics experiment and the limits of the current white spheres.

Next: implement/validate the foam and froth studies, improve the boil's surface
reconstruction, eddy trajectories and wave boundaries, and resolve the hole's
flux/boundary and entrainment issues. Also refine the waterfall's inlet, spatial
resolution and froth. Keep all eight cases in scope; one clip is not completion.

Reference starting points (no external media bundled):
- Blender Mantaflow introduction: https://developer.blender.org/docs/release_notes/2.82/physics/
- Secondary particle definitions: https://docs.blender.org/manual/en/5.0/physics/fluid/type/domain/liquid/particles.html
- USBR hydraulic design/experimental reference: https://www.usbr.gov/tsc/techreferences/hydraulics_lab/pubs/EM/EM25.pdf

## Scheduler

The attempt to replace the old hourly reconstruction prompt was denied by the
app's approval reviewer. Await explicit user confirmation to change it; do not
work around that denial. The current goal authorizes feature-scene work here.
