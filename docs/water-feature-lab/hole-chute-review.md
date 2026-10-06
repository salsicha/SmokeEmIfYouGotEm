# Hydraulic-hole laboratory: chute prototype, 2026-09-29

Status: **prototype, not physically or visually accepted**. The first two hole
trials were flooded/weak; a third skimmed along the surface with reverse flow
underneath. The fourth changes the approach geometry, not just the foam look.

## Configuration and actual flow

Case `tmp/water-feature-lab/hole-v4-chute`, Blender 5.2.0 LTS. Fixed 6 × 1.6 ×
2.9 m domain, 80-cell longest axis, ~7.5 cm resolution, 24 fps, 240 frames.
The 0.9 m upstream bed slopes down from x=0.75 to x=2.2 m into the pool.
The source velocity setting is 2.5 m/s, depth 0.3 m, level drain z=0.55 m.
Those are configuration values, **not measured discharge or tailwater stage**.
All data, liquid mesh and secondary particles baked in 222.33 seconds.

The installed API describes the inlet velocity as an initial velocity of emitted
liquid. Flooding the emitter does not establish the intended channel current.
Therefore neither source velocity nor its calculated Froude is an acceptance
measurement. The chute provides a gravitational approach to the pool.

The new section diagnostic reads the cached velocity grid and uses 2×2
subcell quadrature against the rendered liquid mesh to estimate wet area.
It is an estimator, not the solver's exact wet-cell/face flux.

At frames 168, 192, 216 and 240 (roughly 7–10 simulated seconds), all 16
samples at x=1.95, 2.25, 2.70 and 3.30 m have:

- upstream near-surface mean flow, approximately −0.13 to −0.41 m/s;
- downstream lower-band mean flow, approximately +0.75 to +1.25 m/s.

This is evidence of the desired roller direction and its persistence across
those sampled times. It is not evidence of correct turbulence, retention,
entrainment rate, pressure distribution or calibrated natural-river behavior.

The section-flux estimates are **not yet consistent enough for conservation
acceptance**: late x=0.75 m estimates are about 0.37–0.38 m³/s, whereas downstream
values are roughly 0.5–0.6 m³/s. Mesh wet masks, grid staggering/mapping,
unsteady storage, source behavior and numerical error need separate checks.
Do not quietly normalize these values or claim the configured 1.07 m³/s.

Evidence: `sections-preview.json`, `sections-late.json`, `bake.json` in the case
directory. `unreal/Scripts/audit_water_feature_sections.py` is read-only.

## Calibration

`tmp/water-feature-lab/velocity-calibration-v2/calibration.json` repeats the
no-contact falling-sphere test and also compares the interior velocity grid to
particle readback. Gravity error 0.231%, maximum quadratic position residual
0.527 mm; grid/particle peak-normalized discrepancy 1.552%. Both checks pass
their diagnostic tolerances. The conversion factor is only valid for the
matching build, domain, resolution and time configuration.

The grid accessor's interleaved xyz layout and particle readback normalization
were inspected in Blender's primary source:
https://raw.githubusercontent.com/blender/blender/v5.0.0/source/blender/makesrna/intern/rna_fluid.cc
https://raw.githubusercontent.com/blender/blender/v5.0.0/source/blender/blenkernel/intern/particle_system.cc
The runtime calibration checks the installed 5.2 build rather than assuming
that the older source alone proves its behavior.

## Visuals

The closer camera isolates the chute toe, roller and near pool. The front wall
is an invisible physical boundary: the exposed water face is a cutaway, not a
free-standing vertical water slab. Secondary foam/bubbles/spray remain a
subgrid approximation. Native Cycles sphere points retain the cached particle
positions but replace expensive icosphere instances; radii remain explicit
render settings, not measured bubble radii. No fluid field is changed by this
renderer option. Its first frame took ~6.55 seconds including evaluation,
versus ~27 seconds for the earlier overview/instance preview; this is not a
controlled benchmark and certainly not a real-time-game performance claim.

The surface still looks too smooth and the whitewater too blanket-like. A
visible return current is progress, not photorealism or physical acceptance.
Next refinements must address entrainment structure, boundary/flux consistency,
spatial convergence and comparison with real laboratory footage.

Readback at frame 192 confirmed every cached liquid/secondary particle was
`ALIVE`; including dead/unborn particles is not the cause of the blanket in
this sample. Secondary lifetime settings currently use Blender defaults 10..25;
their conversion to physical seconds has NOT been verified (the earlier note
incorrectly labeled them seconds). Do not infer that the entire clip retains
startup particles from those raw values alone. Production/lifetime and
subgrid optical coverage require sensitivity testing, not arbitrary thinning
just to make the image prettier. The native-point radius is uniform by species
and does not yet retain the original per-particle size variation.

Follow-up renderer correction: `--point-clouds --particle-sizes` now transfers
each evaluated particle's radius as a point attribute instead of assigning
every particle the maximum radius. Frame 192 readback confirms foam/spray
radius 1.5004..2.9995 mm and bubble radius 0.6002..1.1998 mm. All cached positions
are retained; no particles are randomly discarded or fluid fields modified.
The preview in `preview-particle-sizes/frame_0192.png` was rendered and inspected.
It still looks too uniformly foamy: correcting representation alone does not
resolve emission/lifetime/air-phase fidelity. The already-delivered prototype
clip remains unchanged and uses the earlier uniform radii.

## Delivered prototype clip

`hole-prototype-v1/feature.mp4` and `feature.png` contain 36 actual rendered
frames (168..238, stride 2), played at 12 fps: three seconds at normal speed.
The interval is simulation time 6.9583..9.875 s. Every APNG frame matched its
source exactly; MP4 decoding returned all 36 frames; no adjacent duplicates.
Beginning/middle/end were visually inspected. This is not a seamless loop.
MP4 SHA256: `5dc0aa6b9f0d70df34cf9208d7c183fff8eb253b3735b8184a19786deed60666`.
Packaging does not change the unaccepted physics/visual assessment above.

## Remaining scope

Standing waves, pillows, eddies, boils, isolated foam and isolated froth/spray
remain in the active goal. Neither this hole nor the existing waterfall clip
completes those cases. No full-river work is resumed by this experiment.
