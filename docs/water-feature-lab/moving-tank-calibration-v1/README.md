# Moving-tank calibration (preliminary, not feature acceptance)

This is newly authored laboratory geometry, not captured river reconstruction
and not a repair of the old native eddy cache. The full isolated-feature goal
remains active; no waterfall, hole, standing wave, pillow, eddy, boil, foam or
froth/spray feature has been accepted. Normal playable river integration and
the user's **20 FPS** target remain outstanding.

The case is a 1.0 x 0.6 m closed tank with 0.5 m mean liquid depth, density
1,000 kg/m3 and gravity 9.80665 m/s2. The initial free surface is the quadratic
mesh interpolation of a 20 mm cosine displacement, with zero initial velocity.
Walls/bed impose stationary normal velocity; tangential slip is allowed. No
through-flow, viscosity, surface tension, air phase, breaking, foam or spray.
The illuminated checker bed, glass apparatus, lighting and colors are authored
diagnostic presentation, not measured optical evidence.

## Physical construction and qualification

Continuous quadratic 3D geometry and velocity, full consistent material kinetic
mass, and local discontinuous linear pressure moments. Implicit-midpoint
gravity/pressure uses the time-integrated geometry-dependent divergence. The
rendered boundary, mass, motion and wall planes derive from the same physical
positions. There is no skin expansion, height multiplier, smoothing modifier,
velocity clamp, cell deletion or density reset during transport.

Conserving total volume and energy alone is insufficient. A retained weak
continuous-pressure trial develops a whole-cell density bound as high as
2.899 times initial density despite roundoff-level global conservation. It is
**rejected** and is not the animation source. Local-pressure controls preserve
each material cell's volume and pass unchanged preliminary 1% bounded-density
gates. These are not proof of pointwise incompressibility or pressure stability.

| Trial | Steps / dt | Maximum whole-cell density bound deviation | Physics cost |
|---|---|---|---|
| Weak pressure, n=2 (rejected) | 100 / 4 ms | 189.89% | 12.90 s |
| Local pressure, n=2 | 100 / 4 ms | 0.5852% | 72.64 s |
| Local pressure, n=2 | 200 / 2 ms | 0.5854% | 209.52 s |
| Local pressure, n=3 | 200 / 2 ms | 0.5648% | 623.87 s |

Independent readback imports no construction helpers. It reassembles material
mass with different spatial quadrature, uses direct Jacobian inversion and a
different time quadrature, and checks **all 600 saved steps**, not just chosen
frames. It checks original pressure rows, free-component momentum, kinematics,
global/local volume, energy, stationary normal wall contact, positive curved
cell maps and density coefficient bounds. On the finest control, cumulative
global volume error is 2.22e-16 m3, cell volume error 1.09e-16 m3 and energy
error 2.27e-13 J. Bernstein positivity/bounds are floating-point polynomial
certificates, not outward-rounded interval or nonlocal-intersection proofs.

Independent Eulerian surface integration checks 21 matching times with two
quadratures. Maximum cosine-mode difference from halving the coarse time step
is 9.61e-7 m; the two spatial meshes differ by up to 3.24e-4 m. Initial surfaces
also differ because each interpolates the cosine on its own mesh. The finest
fundamental height mode at 0.4 s is -0.0103572 m. Comparison with the
[small-amplitude gravity-wave dispersion relation](https://web.mit.edu/fluids-modules/www/potential_flows/LecturesHTML/lec19bu/node4.html)
is a short-control sanity check, **not full-period frequency or flow-convergence
acceptance**. This closed-tank slosh is not a stationary crest with water moving
through it. The local pressure space differs from ordinary continuous
[Taylor-Hood](https://defelement.org/elements/taylor-hood.html); no stability
claim is inferred from that element's name.

## Display contract

Only the finest trial is eligible for views; all three local trials must pass
independent all-step qualification. The sampler never falls back to an easier
coarse case. The welded boundary has 3,458 vertices and 6,912 triangles. Every
vertex is an exact sample of the computed quadratic boundary. Planar display
chords differ in volume by at most 5.93e-6 m3 (about 0.002% of 0.3 m3), measured
over all 21 poses. The orange markers are four actual material nodes, not foam
or particles carrying a separate simulation. Wall/bed contact normals remain
sharp; smooth lighting normals do not move geometry.

The delivered [21-frame animation](moving-tank.png) covers actual t=0 to 0.4 s at 20 ms intervals, shown
5x slower plus an end hold. The embedded Blender playback runs discrete
samples at 50 FPS; this is **not measured simulation/game FPS**. Between-frame
shape-key interpolation is display interpolation, not an extra fluid step.
Early dark/cropped previews are preserved in the local artifact area and are
not visual acceptance evidence.

The [embedded playback](moving-tank.blend) was reopened read-only in a fresh
Blender 5.2.0 LTS process. Every one of the 21 evaluated poses matches the
computed boundary within 2.98e-8 m, and every marker within 2.92e-8 m. Closed
boundary topology, no geometry modifier, no fluid domain and no external image
dependency are checked. Engine views took 349.66 s at 760 x 520, Cycles 16
samples/adaptive sampling, 8 CPU threads. Neither this cost nor playback rate
is game FPS. The annotation assembler reads back every stored APNG frame
pixel-for-pixel. Start, middle and final views were visually inspected; motion
is subtle at the actual 20 mm scale. Refraction/shading remain diagnostic, not
final river-water visual acceptance.

240 numerical tests and 15 strict source compiles pass. Eight legacy
Blender-context test modules were excluded from the stock-Python run and are
not claimed passed. Physics, surface, observable, render, animation and
delivered-playback receipts are alongside these files.
Final combined 415-file SHA-256 check and three prior eddy animation/playback
preservation hashes pass with no conflicts or changes. No owned engine job
remains live; scoped whitespace checks pass.

## Sources, preservation and remaining work

The scripts are in `unreal/Scripts/`: `water_feature_moving_tetra.py`, its audit
and independent qualifier, `water_feature_quadratic_surface.py`, the surface
preparer/analyzer, `render_water_feature_moving_tank_v4.py`, the animation
assembler and read-only playback verifier. Receipts contain absolute paths and
SHA-256 pins. Large trajectory arrays and all retained previews remain under
the thread's local visualization root; they are not duplicated into the repo.
The eventual animation and embedded playback are standalone, while rerunning
the full evidence chain requires those pinned local inputs or a fresh solve.
No third-party captured imagery/assets have been copied into this calibration.
All earlier native fields, failed controls, source geometry and playbacks are
preserved. No Git history/branches or automation were changed.

Next qualify a complete oscillation, further spatial refinement and pressure
conditioning, and examine density/deformation over longer motion. Then add
conservative changing solid contact/inlet chronology and topology handling
needed for actual impact, rollers and breaking before feature animations can
be physically accepted. Do not use a pretty tank control as a completed river
or defer the eventual normal-playable integration until every river is perfect.
