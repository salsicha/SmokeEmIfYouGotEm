# Current-surface foam transport — September 9

Implemented persistent GPU foam history against the current reconstructed SDF,
not the inherited Niagara SDF. RK2 backtracing uses the current solver velocity
and GPU-carried simulation age delta. Zero-delta rendering copies coverage
exactly; initialization and reset clear it. Curl/compression-driven source and
decay remain empirical appearance controls, not calibrated air entrainment.
Output modifies G on the existing single surface, preserving distance and clock.
No solver/particle state or saved production assets are changed.

## Retained failure and correction

`liquid-current-surface-foam-12s/current_foam_audit.json` failed with coverage
error 0.16235. GPU reciprocal rounding included the exactly 50 cm support
boundary while the float64 reference excluded it. The support cutoff now uses
the same half-representable distance as the stored SDF. A separate audit bug
compared four storage channels against three velocity components; padding is
now excluded from that comparison. Neither numerical tolerance was widened.

`liquid-current-foam-cutoff-12s/current_foam_audit.json` passes the predeclared
0.001 absolute coverage/source/interpolation gates:

- Active simulation delta: 0.0166015625 s; max coverage error 0.000732422.
- Source-rate error 0.000769272/s; advected coverage error 0.000624164.
- Current velocity XYZ and boundary exactly match independent grid readback.
- Paused coverage is bit-for-bit identical to previous history; no decay or
  extra transport occurs on render-only callbacks.
- R/B/A metadata preserved exactly; zero GPU diagnostics and engine errors.
- 28,093 source cells, 136,904 nonzero coverage cells, maximum coverage 0.34058.

Separate live, occupancy, and clock audits pass: 750 updates, 70,963 particles,
30 distinct motion images, zero new water in non-fluid parent cells and no
distance-sign mismatch. Captures are blocking diagnostics, not frame-rate tests.
90 numerical liquid tests pass (3.406 s). The actual-engine suite in
`engine-liquid-current-foam-cutoff/index.json` has 13 successes, no failures or
warnings, including nine foam cases: advection, pause, reset, decay, shear
source, solids, invalid delta, missing history and the support boundary.

## Cost

`liquid-current-foam-benchmark/benchmark_audit.json` verifies 480 uninterrupted
editor fixture intervals: mean 22.6605 ms, p95 25.1525 ms. Its 471 post-warmup
GPU samples measure 5.4838 ms density/occupancy, 0.5774 ms distance, and
0.11194 ms foam plus copy, totaling 6.1731 ms. These do not measure packaged
game FPS or accept full-scene performance. No readbacks occurred in the timed
window. The native foam stage still executes and can be eliminated later once
the current-surface path is integrated and equivalence is verified.

## Appearance remains incomplete

Actual `motion_029.png` still looks cyan/plastic, with weak white coverage and
visible rectangular fixture boundaries. It is not photorealistic. The current
21 m window still has unverified rapid identity and inferred submerged bed.
No scene promotion, new river cook, or commit occurred. Actual Niagara reset
integration, long-duration transport, coherent visible froth, spray, proper
whole-scene shores/raft coupling, physical flux/volume acceptance and the later
river queue remain open.

Next inspect/adjust the optical response to the transported coverage on this
same surface, compare actual motion to the supplied whitewater reference, and
retain the transport regression. Epic's [Single Layer Water documentation](https://dev.epicgames.com/documentation/unreal-engine/single-layer-water-shading-model-in-unreal-engine)
explains that material opacity balances surface reflection against volume
scattering. This supports testing a matte surface contribution for foam, not
adding another white sheet. Artistic optical controls are not measured bubble
density or calibration.

## Subsequent rejected experiments

`liquid-current-foam-optical-controls` compares strength 0/1/4 on a frozen
surface. It remains mostly glossy cyan. Highest upward SDF crossings (not
visible image pixels) have mean coverage 0.00392, median 0.000749 and p99 0.0537.
This distinguishes low exposed-surface coverage from the much higher volume
maximum. The supplied real whitewater image has bright opaque froth separated
by dark water troughs and airborne spray; this fixture does not reproduce it.

`liquid-current-foam-precise-hit` tested a 0.25 cm ray-hit cap. Runtime material
readback shows the instance already has Tolerance 0.005 and Voxel Size 16.40625
cm, i.e. about 0.082 cm tolerance, unlike the engine material default. The cap
does not address the current problem and was removed. Material controls now log
actual applied values. An initial diagnostic lookup omitted the space in
`Voxel Size`; that logging typo is fixed, not evidence of a zero-sized grid.

`liquid-projected-foam-history-12s` tested two closest-point projections through
the previous SDF before history sampling. A rising-plane GPU test passed and
the full engine suite had 13 successes, but actual live parity failed by
0.13391 coverage and top-surface mean fell to 0.00205. The live runtime projection
was removed rather than accepted on the synthetic case. The optional float64
reference remains only to reproduce this retained rejected capture. No
tolerance was widened; `current-surface-v1` is again the runtime transport.

The next implementation is an opt-in native secondary spray/foam emitter in
the same owned transient system, with a 2048-particle per-frame spawn cap and
the existing single liquid surface. The first `liquid-native-secondary-12s`
capture finished but had an uninitialized `None` secondary emitter and zero
secondary particles; it is a FAILED setup, not a visual pass. The script now
requires an initialized secondary emitter in its actual particle report.
The follow-up `liquid-native-secondary-owned-12s` failed the new initialization
assertion at frame 6. Source inspection then established the actual cause:
this fixture derives from Hose, not Splash, and already has a disabled secondary
emitter. The attempted installer required one emitter and returned before any
addition or version handling. The `None` report entry was the existing disabled
slot. The temporary copy/add code was removed. The current command enables the
owned existing emitter and its second sprite renderer, preserving reader links;
it is still awaiting actual emission/motion/terrain/cost verification.

The enabled-emitter runs `liquid-existing-secondary-12s` and
`liquid-secondary-distance-only-12s` failed Niagara grid-reader initialization:
the producer packed SDF plus RiverFoam, while the reader expected a one-attribute
RGBA SDF. Removing assignment targets after installation did not remove all
compiled field references. Both failed processes were stopped; neither is a
completed capture. Global RGBA disabling was not used because the live velocity
and boundary bridge relies on those layouts.

The new `surface-foam` construction mode never adds the redundant native foam
attribute. It retains RGBA SimRT and the actual emitter clock; the independent
GPU foam pass still owns persistent history. `liquid-secondary-single-sdf-12s`
initialized the secondary emitter without the grid error, but failed at frame 6:
recompilation restored the stock optical material. It is another retained failed
setup, not a visual pass. Setup now enables secondary first, then installs the
optical override on the primary emitter only. Runtime grid readback asserts
single-attribute RGBA SDF and no native RiverFoam. The compiled-shader regression
also covers this new variant. Numerical liquid tests: 92 pass (2.862 s).

`liquid-secondary-optical-order-12s` completed with initialized secondary and
correct optics; actual SDF readback is one-attribute RGBA. Live, occupancy, clock
and foam audits pass. All 13 engine regressions pass, including the compiled
clock-only variant (`engine-liquid-single-sdf`). However secondary population
was zero. The capture had repeated spawn-limit warnings, not initialization
errors: Niagara rejects a 10000-particle request above a 2048 safety ceiling
instead of truncating it. The emission-trace capture confirms this in both the
actual compiled system shader and engine implementation.

The installer now sets the actual `Emitter.MaxSecondaryParticlesPerFrame`
assignment to 2048 as well as its safety ceiling. `liquid-secondary-bounded-request-12s`
verifies that compiled constant and no rejection warnings, but the frame-30
capture failed because telemetry required primary-only contact attributes on
newly present spray particles. Telemetry now records secondary UniqueID/position/
velocity separately, uses source index -1 (no native-face source ID), and keeps
the primary contact checks intact.

`liquid-secondary-particle-records-12s` completes: 750 live updates, 30 distinct
motion frames, zero engine errors or rejected spawn batches. Foam transport
passes (active max coverage error 0.00048828125; paused history exact). Secondary
counts at frames 6/30/60/240/480/720 are 0/1/1/1/0/0. One tracked particle moves
64.98 cm between frames 30 and 60. This is too little to make visible froth, not
a spray/terrain/realism pass. Initial secondary audit's `terrain_contact_acceptable`
wording was too broad for those samples; the corrected audit explicitly leaves
terrain verification false. Numerical liquid suite now has 95 passing tests.

Next: correct the native secondary source math before calibration. Active GPU
HLSL uses vorticity thresholds 5..20, not the stock template's 600..1000. It also
reads Vy_left from X+1 (same as Vy_right), and uses one scalar cell width for
all axes. The emission probability does not use its SimDt argument. A separate
metric curl calculation on the recorded surface-band fluid cells gives median
0.622/s, p90 2.345/s, p99 4.014/s, max 5.882/s (32 of 15704 cells above 5/s).
Those are diagnostic current-field values, not reference-rapid calibration.
Spray velocity/world-frame consistency and coupling to the reconstructed SDF
also remain unverified. The image is still glossy cyan with rectangular fixture
edges; no production asset or scene has been promoted.
