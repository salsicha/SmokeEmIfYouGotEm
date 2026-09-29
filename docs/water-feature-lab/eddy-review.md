# Bank-spur eddy prototype

## Setup and evidence

`tmp/water-feature-lab/eddy-v1` is a separate synthetic 6 m flume, not a river
reconstruction. Its bank-attached rectangular spur occupies x=2.45..3.00 m,
y=0.05..0.95 m, z=-0.20..1.10 m. Visible geometry and collision use the same
mesh, and a Boolean excludes the obstacle from the initial water volume.
The approach height is 0.45 m, newly emitted inlet speed 2 m/s, inlet depth
0.35 m, and artificial level-drain threshold 0.30 m. This is not a prescribed
discharge or a true fixed downstream water elevation.

The 80-resolution, 288-frame bake finished in 229.50 seconds. Fractional
obstacles remain off; the boulder comparison did not justify promoting that
option. Mesh, liquid and secondary-particle caches are present.

`eddy-late.json` measures predefined regions with the matching 80-resolution
free-fall velocity calibration. At frames 240, 264 and 288:

- Main-current mean downstream velocity: 1.50, 1.58, 1.72 m/s.
- Bank-return mean downstream velocity: -0.96, -0.99, -1.03 m/s.
- Behind-spur lateral velocity: -0.29, -0.34, -0.31 m/s (away from the bank).
- Downstream-turn lateral velocity: +0.045, +0.106, +0.190 m/s (toward bank).

No primary particles were found deep inside the spur in the five sampled
frames. This is not a millimetre-scale collision clearance check. Earlier
frame 192 still has positive bank-region mean velocity: the flow is evolving.
These narrow-band particle means are not volume averages or tracked paths.
Counterflow alone does not prove sustained circulation or a closed trajectory.

## Visual review and remaining work

The high-oblique frame-240 preview exposes the sheltered return without hiding
the collider. The liquid shape is visible but excessive, sheet-like whitewater
coverage persists. Spray uses dielectric water; foam and bubbles still use
unvalidated white scattering approximations and rendering radii.

The first 36-frame motion sequence (frames 216..286, stride 2) is delivered
in `docs/water-feature-lab/eddy-prototype-v1/feature.mp4` and `feature.png`.
Playback is 12 fps, three seconds at normal simulation speed. All APNG frames
match the rendered sources exactly; the MP4 decodes 36 frames with zero
adjacent duplicate source images. First/middle/last frames were visually
inspected. Playback repeats but is not a seamless simulation loop.
MP4 SHA256: `8a7eda48b4b4592dda038d0db4cb130e94f1afca037cef86b30c4bf7aab8e906`.
Render session 73831 and encoder 72826 are terminal.
Circulating paths, seam exchange, longer-time persistence, boundary sensitivity,
mass balance and whitewater appearance remain unaccepted. No game integration
or real-time FPS claim is made.

## Reconstructed pathline check

`pathlines-v1.json` reconstructs 48 seeded paths from frames 168..288, using
inverse-distance interpolation of up to 12 calibrated primary-particle velocity
samples within 0.15 m. It requires at least four neighbors. The velocity field
is interpolated between consecutive cached frames; midpoint integration is
repeated at four and eight substeps per frame. These are not persistent FLIP
particle identities, and no missing path is clamped or projected into water.

At eight substeps, 31 paths stop for insufficient local/midpoint support,
16 leave bed/domain/drain bounds, and only one lasts all five seconds. That
survivor travels downstream rather than demonstrating a closed loop. Median
step-halving difference over common supported samples is 0.86 mm; the maximum
is 49.76 mm. Thus the reconstruction is not strong evidence of persistent
eddy circulation. Sparse narrow-band support is a diagnostic limitation,
not proof that the underlying solver has no eddy. A better-supported velocity
field and a longer settled interval are required; do not repeatedly rerun this
unchanged pathline test expecting acceptance.

`test_water_feature_pathlines.py` passes all five checks: constant velocity,
linear time interpolation, circular motion with second-order step refinement,
missing support, and solid entry. These verify the integrator, not the fluid.
