# Registered wet-state initialization and river boundary axes

September 8. South Fork and the full scene queue remain incomplete. The new
initial state runs on the GPU, but its terrain-contact result fails badly. No
production promotion, asset replacement or commit.

## Implemented

Correction after tracing the complete compiled module bindings: this run's
`open-sides` configuration was wrong. Exposed controls map Left/Right=X,
Back/Front=Y and Down/Up=Z; the internal custom-HLSL argument labels use a
different convention. The run opened the floor and closed negative Y, not the
claimed four horizontal faces. SystemSpawn constants alone did not establish
their physical axes. The current source correction restores Back=true and
Down=false; this historical capture is retained unchanged. Wet seeding,
grid-frame transfer and full-neighbor gather remain separate valid changes.

`physics/scripts/build_south_fork_liquid_initial_state.py` now constructs the
initial wet volume from the registered triangles and the existing hydraulic
stage/momentum field. It verifies source hashes and vertical/rotation frames.
Positions use exact bed samples; velocities are interpolated depth-averaged
momentum divided by interpolated source depth. Vertical velocity is explicitly
zero, not a claim of measured 3D flow. The bed remains an inferred submerged
surface, and real rapid identity remains unverified.

The 128x128 column quadrature uses 0.1640625m horizontal spacing. Deterministic
largest-remainder apportionment assigns equal nominal-volume particles to the
columns, with vertical samples strictly between bed and stage. Result:

- 77085 particles; minimum exact-bed clearance 0.0810168164m.
- Quadrature wet volume 680.8111195762m³.
- Represented nominal volume 680.8130121231m³, quantization error 0.0018925469m³.
- Same nominal particle volume as the inlet source: (21/64)³/4m³.
- Engine particle-volume calibration remains **false**. Quantization error is
  not a measurement of physical mass conservation or hydraulic accuracy.

Generated `unreal/SourceArt/RaftSim/SouthForkLiquidWindow20260908/hydraulic_initial_state.json`
SHA256: 4e34428973aa0b814e875c22d2f6157b4b3db128041b5f9cfedebeb14f33580e.

`InstallHydraulicInitialState` replaces only the initial branch of a privately
copied Grid3D_Flip_GridParticles function. It reads the registered position and
velocity arrays by initial execution index. Extra dummy candidates in the
inherited 163840-particle burst are rejected before becoming water; continuing
inlet particles retain their previous source path. The bounded table-size guard
depends on that current inherited burst. It must be revisited if the base
scalability/grid configuration changes.

The `wet-start` command variant includes corrected boundaries, grid transfer,
full gather and private swept contact. It is transient and has a distinct asset
name. Capture assertions prevent confusing it with the unchanged baseline.
Typed DI reads copy and repair the public parameter-map pin metadata, without
private editor headers. New capture metadata records the seed hash/count/nominal
volume on future wet-start captures; the first successful capture predates that
metadata addition, so its identity is established by log, compiled shader and
actual particle IDs instead.

## Actual engine evidence — failed physical acceptance

Build58641 exit0; open-sides capture45737 exit0:
`liquid-terrain-open-sides-readback`, CaptureLiquidTerrainOpenSides.log.
At12s:59184 live,79 more than one32.8125cm cell below bed, worst194.18cm,
13 outside domain. Correcting the axes alone does not fix contact or crowding.

The first wet-state build21884 failed because auto* could not deduce a
TObjectPtr graph type; explicit UNiagaraGraph* corrected it. Build5002 exit0.
Wet-state capture56403 exit0:
`liquid-terrain-wet-start-readback`, CaptureLiquidTerrainWetStart.log.
Its active GPU shader contains ReadRegisteredWetVolume and the initial-only
selector. At frame6,76821 initial seed IDs and441 continuing inlet IDs are live.
This confirms actual seeded water, not merely configured arrays.

|Time|Live particles|More than one cell below exact bed|Worst penetration cm|
|---|---:|---:|---:|
|0.1s|77262|1|142.2|
|0.5s|77367|80|286.2|
|1s|74954|332|559.5|
|4s|74577|1234|565.1|
|8s|85228|1862|565.1|
|12s|100733|2439|565.1|

At12s,24 are outside the domain and7628 first-query normals are invalid. Maximum
proposed contact step195.73cm; maximum retained speed16490cm/s. These are serious
failures, not acceptable splashing. The fixed-overhead opacity-one image was
inspected: the filled area remains pale and smooth, with invalid-looking patches.
It is not photorealistic. Blocking readback/manual simulation is not a timing
benchmark. No calibrated inflow/outflow balance or raft acceptance established.

## Regression results and next work

Build47229 exit0. Expanded engine regression12246 exit0:
`engine-liquid-wet-start/index.json`:8 clean passes,0 warnings/failures,11.73s.
The transfer test now constructs four variants, checks boundary overrides,
compiled seed lookup, array counts, source preservation and transient ownership.
Twelve focused Python liquid tests pass, including quantization, invalid input,
source hashes and independent exact-triangle checks on every generated seed.
These prove implementation properties, **not fluid-contact correctness**.

Saved contact/map/project hashes remain eefde251... /81f31bec... /01b95fff...
(complete hashes in liquid-grid-frame-transfer.md). All owned processes terminal.

Next: make pressure classification and particle contact use a consistent terrain
representation. The registered surface is a piecewise-linear heightfield with
preserved XY and known triangles; use its exact topology/accelerated queries
rather than assuming the coarse mesh SDF matches it. The seed table itself is
above the exact bed, yet the simulated particles rapidly enter it. Retain wet
initialization and the confirmed basis/boundary corrections while addressing
that failure. Real incoming/outgoing volume exchange, visual motion, spray,
raft coupling and performance still require verification before production.
