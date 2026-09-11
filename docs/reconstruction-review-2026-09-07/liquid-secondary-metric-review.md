# Secondary whitewater: metric motion and optical review

September 9. South Fork is still incomplete. These are unsaved, bounded GPU
fixture changes, not production promotion or photographic acceptance.

## Corrected source and motion

The owned native secondary modules now use actual per-axis cell dimensions for
curl, including the previously incorrect X-minus velocity lookup. Emission uses
elapsed simulation time and a wet-band surface-area approximation, not a fixed
per-frame probability. Its 120 particles/m²/s rate and vorticity response are
empirical candidates, not footage-calibrated entrainment. Velocity is rotated
from grid into world space without applying grid scale. Foam follows flow;
spray uses ballistic gravity; bubbles use a time-integrated buoyancy/relaxation
model. Paused particles retain position and velocity.

The active native module previously failed to persist its returned state.
Particles.State now records foam, spray or bubble transitions. Boundary checks
read the actual SolidVelocity_Boundary vector attribute along five points of
the proposed path; this avoids the obsolete scalar attribute and reduces
escapes, but is not exact triangle collision.

The first two new captures failed during setup: UObject allocation under a hash
iteration lock, then a Niagara input pin appended after the dynamic Add pin.
Both failures remain recorded. The installer now collects objects before
editing and validates ordered signature pins before compilation.

## Actual GPU evidence

`liquid-secondary-vector-contact-12s` completes with secondary populations
65/333/531/264/251/245 at frames 6/30/60/240/480/720, compared with at most one
particle before the metric source correction. No GPU spawn batches were
rejected. The current-foam audit passes with max coverage discrepancy
0.000732421875 and exact paused history. Live reconstruction records 750 updates
and 30 distinct images. This is diagnostic motion evidence only.

`liquid-secondary-render-state-12s` records actual sprite size and classification.
At frame 720 its 264 particles comprise 232 foam, 16 spray and 16 bubbles.
Sprite dimensions are 5–8 cm with no nonpositive sizes. Material dynamic XYZ
are zero and W contains the state. Thus zero sprite size does not explain weak
visibility. The capture still includes a 14.877 cm below-bed sample and ten
out-of-domain samples at frame 240; terrain contact is not accepted.

Particles still use native SDF support, whereas the visible surface is the live
reconstructed SDF. In the earlier metric-input-order capture, sampling the
rendered SDF at final particle positions found a median signed distance of
-2.419 cm and some deeper particles. Surface alignment remains to be fixed;
increasing sprite size or lifting all particles is not a physical remedy.

The latest near-surface foam field is weak too: within |SDF| < 16.7 cm, median
coverage is 0.0005827, p90 0.06470, p99 0.20989 and maximum 0.33813. Only 6.32%
of these sampled cells exceed 0.1 coverage. This band statistic includes all
surface orientations, not a camera-visible coverage measurement.

The 101 numerical tests pass, including six independent metric-curl, source-time
and motion-integrator cases. `engine-liquid-secondary-metric` passes all 13
engine tests without warnings. These do not prove real-GPU time-step convergence
or full-scene performance.

## Optical source evidence and next correction

Read-only `liquid-secondary-whitewater-material.json` shows the native sprite
material uses a blue Color default (0.633382, 0.819171, 0.942708), a scalar value
1000 connected to Specular, and a tangent-space normal texture connected to a
material marked world-space-normal. Opacity is a lifetime/noise/disk product;
the zero dynamic XYZ only affect texture-coordinate offsets, not a zero-alpha
gate. The inspection engine run also passes the current-foam GPU test.

An owned optical candidate now preserves that lifetime/opacity graph but uses
neutral near-white lit color, roughness 0.65, specular 0.25 and a smooth aggregate
normal in the sprite tangent frame. The 5–8 cm geometry and simulation are
unchanged. These are sub-resolution billboard aggregates, not resolved fluid
volume or a second water surface.

The first optics build caught a const/non-const pointer mismatch in the new
regression; the corrected build succeeds. `engine-liquid-secondary-optics`
passes all 14 tests without warnings. `liquid-secondary-neutral-optics-12s`
completes with runtime assertions confirming roughness/specular 0.65/0.25 on
the active sprite material, 750 live updates, 30 distinct motion images, no
engine errors or rejected spawn batches, and exact paused particle state.
Independent current-foam and live-input audits pass. The final image still
looks glossy cyan, not realistic whitewater. The material correction alone
does not fix the lack of froth. Three sampled below-bed particles remain
(maximum 13.311 cm across those captures); collision is not accepted.

The new reproducible paused alignment audit quantifies the mismatch on that
same capture. Of 213 final foam particles, median native SDF distance is
+0.032 cm, but median rendered SDF distance is -3.388 cm; 98 have opposite
signs between the fields. Of 20 spray particles, 12 lie outside native water
but inside rendered water. This proves inconsistent surface support, not the
exact fraction hidden by the camera/depth buffer. The native and rendered
fields must agree for secondary classification and surface following; a
constant upward sprite offset would hide rather than resolve the discrepancy.
The top-crossing foam audit reports mean coverage 0.0039275 and only 0.0266%
of sampled columns above 0.1 coverage. That is not camera-visible coverage,
but reinforces the lack of actual surface foam. Numerical suite now passes
103 tests, including anisotropic/local-origin surface alignment and empty-state
handling. Geometry, material and appearance evidence remain separately scoped.

Next: couple secondary support to the same rendered surface and improve physically supported
entrainment. Realistic breaking relief/froth, continuous whole-scene shores,
raft integration, reference calibration and performance remain open.
