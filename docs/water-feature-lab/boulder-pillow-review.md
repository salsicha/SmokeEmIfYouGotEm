# Single-boulder pillow experiment

Prepared standalone scene: `tmp/water-feature-lab/boulder-pillow-v1/feature.blend`.
It is not baked yet. Do not treat this fixture as a demonstrated pillow.

One authored ellipsoid is centered at (3, 0, 0.28) m with radii (0.45, 0.33,
0.60) m. It is a controlled synthetic obstacle, not measured natural rock.
The same mesh is visible and supplies the fluid collider. The 6 x 1.6 m flume
has a 0.45 m raised approach, 0.35 m initial inlet depth, 3 m/s emission velocity,
and 0.30 m downstream level-drain threshold. These are settings, not actual
discharge/depth measurements. No standing-wave bump is present in this case.

The initial liquid uses an applied exact Boolean difference against the rock.
The `--initial-only` obstacle audit tested 105 points inside the rock, finding
none inside the initial water; all four surrounding-water control points
were wet. `initial-check.json` records the result. This finite sampling is not
a complete collision proof. Dynamic particle, mesh and animation checks remain.

After the currently running standing-wave refinement finishes, bake this scene
once, inspect upstream surface rise and flow splitting on both sides, and use
`audit_water_feature_obstacle.py` to check deep particle intrusion and lateral
flow directions. The height-only section audit now refuses this obstacle case:
it would otherwise integrate through the rock. A full solid-aware flux audit
is still needed. Use top/oblique views as well as the side view.

Acceptance remains unproven: no motion clip, pressure validation, wake/seam
validation, mass balance or resolution convergence yet. The isolated eddy case
is distinct and must not be declared complete from this obstacle's wake.

One-shot serial runner session 26447 is now waiting for the fine standing-wave
bake (session 88203 / PID 14448) to exit successfully before starting this
prepared scene via `bake_prepared_water_feature.py`. The runner is not another
boulder bake yet; inspect its handle and do not start a duplicate. Existing cache
files/receipts/markers are refused rather than overwritten. No timer or recurring
automation was installed or changed.

## First baked result

The serial runner completed the 240-frame bake in 195.30 s; all data, mesh and
secondary-particle caches are complete. Session 26447 is terminal. At frames
168/192/216/240, left-side primary particles move leftward and right-side
particles rightward while both continue downstream. The surface samples show
upstream center water rising above the adjacent side-flow samples. This is
evidence of the intended pillow and split flow, not a measured pressure field.

No particles were deep inside the analytic ellipsoid (normalized radius <0.75).
Some are just inside its analytic boundary (minimum normalized radius about
0.9746); tessellation/voxel clearance and visible mesh overlap still need checking.
Do not turn the zero-deep-intrusion count into a full collision acceptance claim.

The higher oblique preview at frame 192 was rendered and inspected. The one
rock and upstream water mound are clearly visible, but foam coverage is still
too broad, the rock is intentionally smooth synthetic geometry, and no
resolution/pressure/mass-budget validation has passed. A 24-frame, two-second
prototype animation of frames 192..238 at stride 2 is now rendering.

The next low-tailwater standing-wave bake is independently running through
serial runner 56278; do not duplicate it. The two completed fine-wave audit
sessions and the boulder audit/one-frame preview are terminal.

The actual mesh nearest-surface check confirms maximum primary-particle
intrusion of about 8.5 mm; 148..170 particles per sampled frame are
more than 1 mm inside (see `obstacle-mesh-collision.json` for exact counts).
This is not entirely an analytic-ellipsoid/tessellation artifact. Collision
acceptance remains open even though there is no deep bulk penetration.

Controlled follow-up `boulder-pillow-v2-fractions` is now baking (session 49263,
PID 18124). Geometry, resolution, timing and flow settings match v1; the single
changed solver option is `use_fractions=True` with its default distance/threshold.
The installed API describes this as fractional-cell obstacle treatment. It is
a test, not a presumed fix: compare actual intrusion, pillow height and split
flow after completion. V1 remains intact, including its prototype animation.

## Delivered motion clip

`docs/water-feature-lab/boulder-pillow-prototype-v1/feature.mp4` and `feature.png`
contain 24 actual rendered frames, 192..238 at stride 2, played at 12 fps:
two seconds at normal speed. All APNG frames match the sources; MP4 decoding
returned all 24 frames; there are no adjacent duplicate frames. First/middle/
last rendered frames were visually inspected. Playback repeats but is not a
seamless simulation loop. No real-time performance is measured or implied.
MP4 SHA256: `9ef53d99816b54cee8736a67242d04cbcff0ed328ed6907b076887af56ec6f10`.

The mound and outward split are visible, but collision, foam density, surface
detail and quantitative hydraulic validation remain unaccepted. Clip render
session 2452 and its encoder are terminal. The only current live simulation is
the fractional-obstacle test, session 49263 / PID 18124; inspect that handle
before starting another bake. All standing-wave bakes and audits are finished.

## Fractional comparison result (supersedes live status above)

The v2 fractional-obstacle bake finished in 175.44 seconds. Its four sampled
frames contain no primary particles inside the actual boulder mesh, and the
minimum normalized ellipsoid radius is about 1.05 (extra clearance). However,
the upstream mound drops from roughly 0.61..0.67 m to 0.39..0.44 m, lateral
flow weakens, and the frame-192 reconstructed volume drops from 3.7616 to
2.4171 cubic metres. The rendered result is visibly shallower. Zero intrusion
alone is not sufficient to promote this option as a physically accurate fix.
Both boulder bakes and previews are terminal; the delivered v1 clip is intact.
