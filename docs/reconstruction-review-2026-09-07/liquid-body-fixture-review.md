# Project-owned 3D liquid fixture — not river-ready

This pass establishes a working Windows UE 5.8 3D FLIP/SDF rendering route.
It does **not** make South Fork photorealistic, and no production scene was
changed. The older V9 failure remains valid for its Mac/direct-template setup.

## Implemented

`RaftSim.CreateLiquidFixture` duplicates the engine Hose system into
`/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_LiquidBodySDFReview`, refuses overwrite,
and explicitly binds the fluid-control module's rendering-method enum to
**Direct SDF** (`NewEnumerator0`, resolved by its display name). Two copied graph
versions receive the override. Exactly one renderer remains enabled; its SDF
material instance belongs to the copied project package. Other sprite, mesh and
debug renderers are disabled. The engine source and material parents are not
edited. The copied liquid material has not yet been tuned for river optics.

The nominal domain is 4 × 4 × 5 m, maximum axis 64 cells, four particles per cell,
40 pressure iterations and the original 1.5 m initial water-height setting.
These are a bounded **Hose fixture**, not a hydraulic jump or measured river
boundary conditions. The renderer builds a volume from liquid particles; it
does not add another broad river plane. External terrain collisions, river
inlet/outlet conditions, entrained-air transport and raft support are absent.

The asset hash is
`f193332042962d24beccc04f338664cf4d2b1b0e97dff931b9e5b7f7332108a5`.
NiagaraFluids is mounted with a process flag only. The editor module now uses
the public NiagaraEditor authoring API; no runtime plugin dependency or project
descriptor change was made.

## Actual rendering and corrected test harness

`capture_liquid_fixture.py` creates an unsaved blank world. It requests one
1/60 s step per rendered editor frame, waits for activation, warms for 180 steps,
then records 4/5/6-second fixed-camera frames, two additional angles with the
simulation frozen, and a water-hidden control. Manual exposure and no temporal
AA are diagnostic choices, not production settings.

The initial synchronous Python launch exited before its callbacks finished.
The next asynchronous run produced no visible liquid because activation was
pending when component retry ticking was disabled. Both runs remain recorded;
neither proves a failed liquid simulation. Gating activation corrected the
missing instance. Subsequent lighting trials were dark or clipped and are not
accepted optical results.

A more important failure appeared in the first GPU profile: CPU age advanced,
but the profiled frame contained no Niagara simulation dispatch. Scene-capture
rendering alone was insufficient. The final harness explicitly enables and
invalidates a normal editor viewport as well. **Do not use the earlier age
counters or pixel differences as proof of continuously advancing GPU fluid.**

The final evidence is `liquid-body-sdf-viewport/`, with
`CaptureLiquidFixtureViewport.log` under `unreal/Saved/Logs`:

- Actual age records: 0, 3.999997, 5.000010 and 6.000023 s. The side/low/hidden
  controls hold at 6.000023 s. A sampled frame now contains the actual FLIP,
  pressure and surface-reconstruction GPU dispatches.
- The inspected main and low-angle images show a depth-bearing liquid volume
  and jet, but its shading is still too dark. It is not realistic whitewater.
- `analysis.json` compares decoded pixels, not PNG metadata: 3,925 and 3,763
  pixels differ by more than eight channel levels between successive fixed
  views; 34,057 differ between final water and hidden-water views. These are
  diagnostic measurements, not a photorealism score or long-animation proof.
- One whole editor GPU frame was 16.31 ms, including both viewport and scene
  capture. Its Niagara compute scope was 4.050 ms, of which surface rasterization
  was 2.293 ms. Forty pressure-iteration dispatches were recorded. The particle
  dispatch range was 286,455; this is **not** a measured live-particle count.
  This is not incremental river cost, a frame-time distribution, or release
  performance acceptance.

## Build and regression evidence

The first 93-action editor rebuild failed at link time: graph recompile
notification is not exported. The corrected implementation uses the exported
node synchronization API; the next build succeeds. Creation exits 0 and saves
the asset. The final ownership-test build and engine run exit 0;
`engine-liquid-fixture/index.json` contains one clean success. It checks fresh
compilation, bounded settings, exactly one active renderer and material-package
ownership. It does not validate liquid physics or visual realism.

The project descriptor and registered South Fork map hashes remain unchanged.
All owned processes are terminal. No commit or production promotion was made.

## Next work

Use this explicit renderer foundation to establish river-specific boundary flow
and terrain collision, with consistent surface/raft support and a single visible
river surface. Improve the SDF optical response and profile surface construction
before increasing domain size. The current isolated cube/jet is not suitable to
place over the existing river as an overlay. South Fork geography/rapid identity,
performance and the entire later-river/crew/cleanup queue remain open.

During the build, the original [California Creeks account](https://cacreeks.com/amer-sf.htm)
was read: its dated description places a boulder approach, a fall, a left-side
chute and Gunsight Rock in the Troublemaker sequence. It is descriptive historical
evidence, not a current survey or an independent duplicate of text credited to
the same author elsewhere. Linked photographs failed the web fetch; one loaded
in the browser, but no visual comparison was established. No new rapid identity
or boulder registration is claimed from this check.

## Tagged obstacle and actual GPU particle readback

The factory now accepts the optional `collision` argument and creates the
separate project-owned `NS_LiquidBodyCollisionReview`. Its SHA is
`6fdf53c11508e37fdde6ad7bcea46490b3140e57843c9bd5a13ec92b58f5d99b`.
Both copied boundary graph versions explicitly enable mesh collisions and
disable mesh-distance-field sampling. The copied rigid-mesh interface accepts
only the `RaftSimLiquidFixtureObstacle` actor tag, includes static objects,
uses simple collision and caps the primitive count at sixteen. This is a
primitive boundary test, not captured terrain collision. The original SDF
fixture, registered map and project descriptor remain unchanged.

`RaftSim.LiquidFixtureParticles <json>` takes a blocking GPU sim-cache snapshot
and measures particle positions and velocities. It does not save/replay a cache
or count a GPU dispatch range as live particles. Data-interface caching is
deliberately off; the engine warns that the material volume texture is not in
the cache. These snapshots are for numerical inspection, not baked rendering
or performance measurement. The first attempt passed a null cache and failed;
allocating the cache fixes that failure. It is retained in the run evidence.

Readback also corrected a fixture-space error: the fluid occupies z above zero,
not a tank centered around z=0. The first sphere at z=-60 cm barely intersected
the bottom and was not a useful collision test. The corrected sphere is at
(0,0,100) cm, radius80 cm; the visual floor top is z=0. A subsystem viewport
ensure was also corrected by establishing its named realtime override before
removing it. Later captures no longer have that ensure.

The paired final outputs are `liquid-body-obstacle-in-water/` (enabled) and
`liquid-body-obstacle-control/` (disabled). Both contain the identical visible
test sphere. `liquid-obstacle-comparison.json`, produced by
`analyze_liquid_obstacle.py`, reports all three sampled instants:

| Simulation age | Particles inside 60 cm core, disabled | Enabled | Maximum enabled penetration into 80 cm sphere |
|---|---:|---:|---:|
| 4 s | 9,472 | 0 | 4.46 cm |
| 5 s | 9,686 | 0 | 3.91 cm |
| 6 s | 9,615 | 0 | 3.76 cm |

The enabled five-second sample has252,558 fluid particles and matching velocity
records, all finite in position. The core is excluded at each sample; shallow
surface penetration remains within one7.8125 cm cell. This demonstrates actual
primitive collision response, **not exact surface exclusion**, robust complex
terrain collision, a hydraulic jump or raft coupling. The fixed/low-angle
captures still show a dark blue bounded tank and jet, not river whitewater.

All builds51483/82235/88873/66777 exit0. Creation87990 saves the collision asset;
render50839 completes but uses the old bottom-touching sphere. Readback61373
fails the null-cache check;78908 succeeds but still uses the old sphere position.
Corrected enabled41791/control83343 complete with particle reports. Final
regression62555 exits0: `engine-liquid-collision/index.json` has two clean
successes (ownership and explicit collision configuration). No production
promotion or commit. All owned processes are terminal.

Next: river inlet/outlet and stage boundary conditions, captured bed/obstacle
collision rather than a sphere, then consistent ownership and raft support.
The optical response and surface-construction cost remain unresolved; do not
add this bounded tank as a second surface in a river scene.

## Flow-through and bounded retirement (September 8)

The engine Hose emitter's inherited parent restored closed boundaries during
fresh compilation. Editing graph defaults, direct outlet bindings and stale
rapid-iteration constants alone did not establish flow. Removing the parent on
the owned duplicate did: `NS_LiquidChannelOwnedReview` has four explicit runtime
inlet bindings and regular/high-precision +X outlet bindings. Starting dry also
avoids the inherited source's negative-SDF rejection of particles emitted into
the initial pool. Neither the source rate nor its velocity is calibrated river
discharge: these are controlled-test defaults (20,000 particles/s, 250 cm/s).

Actual GPU readback then exposed unretired escaped particles. In
`liquid-channel-owned-stop`, 21,669 remained at six seconds, with minimum Z
-134.47 m despite the inlet being stopped at four seconds. Reported downstream
velocity included escaped, freely falling particles and was not a valid
in-domain current measurement. The readback now excludes particles outside the
fixed 400 x 400 x 500 cm domain from all three current-measurement regions.

`NS_LiquidChannelBoundedReview` adds the engine's KillParticlesInVolume module
at the end of particle update, inverted to preserve particles inside that
same domain. It does not replace wall collision or introduce a second surface.
All particles that leave any face are retired: this is a lifecycle guard, not
face-resolved volumetric flux accounting. The +X open boundary remains the
physical outlet. Existing assets were retained, not overwritten.

| Actual simulation age | Live particles | Outside at outlet pending next update | Maximum outlet overshoot | In-domain downstream mean Vx |
| --- | ---: | ---: | ---: | ---: |
| 4 s, inlet just stopping | 13,878 | 55 | 3.995 cm | 189.26 cm/s |
| 5 s | 10,620 | 41 | 4.099 cm | 182.01 cm/s |
| 6 s | 7,903 | 21 | 3.358 cm | 147.21 cm/s |

All three samples have zero nonfinite positions/velocities, zero particles
below the floor and zero in the obstacle's 60 cm core. Retirement precedes the
FLIP integration stage, so the final step can cross the outlet before next
update; maximum measured overshoot stays within one 7.8125 cm grid cell.
`analyze_liquid_channel.py` verifies these checks and monotonically decreasing
counts after inlet shutoff. `liquid-channel-bounded-analysis.json` records a
43.05% count reduction over two seconds, not a mass-conservation claim.

The capture procedure `liquid-channel-bounded-stop` completed. Directly viewed
image shows shallow dark-blue liquid around the sphere. PNG byte sizes match
because of the export format, but image hashes differ; equal size does not
establish a frozen renderer. No photographic or animation acceptance follows
from these diagnostic captures. No channel performance measurement yet.

Bounded asset SHA256:
`11da793eeb4e905a3bd9b45c85d5464ad95b6051c6302af209d457420ad268cd`.
Creation28979 exited1 despite saved=1 and normal shutdown; retain that nonzero
result. Fresh runtime91037 exited0 with completed readbacks. Build7047 failed
on an unexported graph helper; the following build failed on TObjectPtr loop
deduction. Both were corrected; build44268 and67128 succeeded. Earlier
`engine-liquid-channel` test failure was a wrong expectation of four saved
outlet links; the standalone asset has exactly two distinct required paths.
The first bounded suite52685 has three successes and one failure because the
test incorrectly used the suggested stack label as the saved function alias.
The corrected test resolves the actual module by its script and then checks
its exact alias, box choice, inverse setting, enable flag and domain dimensions.
Those retained failures are not clean successes or waived runtime conditions.
Final rebuild40938 succeeded; fresh suite53416 exited0 and
`engine-liquid-bounded-alias/index.json` reports four clean successes, zero
warnings/failures in 6.59 seconds. The lifecycle analyzer also exited0.

Project descriptor and registered South Fork map hashes still match the
previous checkpoint. No production promotion, commit or goal completion.
Next: calibrated inlet/stage and face-resolved outflow accounting, captured
terrain boundaries, single rendered surface and raft support, optical/foam
response and a fresh performance capture. This fixture is not South Fork.
