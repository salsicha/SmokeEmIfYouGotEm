# Advected activity memory — experimental, not accepted

The previous paired-state audit found persistent foam where instantaneous
entrainment was zero, with only 2–3 mm median GPU height perturbation. This
experiment retains a bounded activity scalar transported with mean current.
It is an authored entrainment-persistence closure, **not measured turbulent
kinetic energy**, a 3D fluid solver, or an energy-conserving turbulence model.

## Implementation

`-RaftSimActivityMemoryReview` enables one persistent float per detail cell.
The default-off shader permutation has no activity buffers. Grid size,
timestep/CFL, surface ownership, support crest, foam transport, and 0.06 m
pressure-head parameter are unchanged. The accepted maximum head remains
0.1 m. No new visible surface, clipping, foam source, or raft-support readback
was introduced.

Incoming first-order upwind differences advect intensive activity, preserving
constants under compression. The existing global CFL bounds their convex
weight. RK2 blends transport stages; exact bounded production/decay is applied
once afterward: `dA/dt = source*(1-A) - decay*A`, with source equal to local
entrainment times 1/s and decay 0.5/s. Pressure activity is
`instantaneous + (1-instantaneous)*A`. This preserves the head bound and allows
forcing after the local source fades. Source splitting is not a claim of
globally second-order physics. Periodic pressure forcing is unchanged.

## Verification

Initial build session 84100 failed because the test passed TSharedRef `.Get()`
references where readback pointers were required. Corrected to addresses;
subsequent Development Editor build succeeded. A logging-only test metric was
also corrected to retain the actual source/decay error.

Actual GPU automation session 51794 exited 0. Report
`engine-activity-memory/index.json`: **16 successes, zero warnings/failures**,
including the new activity fixture and existing detail/history/crest/resolve,
visible spray carrier, and map-selection regressions.

- Uniform-current activity centroid: 2.000000133 m in one second at 2 m/s.
- Integral ratio in uniform current: 1.000000263; range [0, 0.338663816].
- Constant-preservation error under compression and a dry cell: zero.
- Persistent source-then-decay error: 1.27814494e-6.
- Split graph activity and wave states: bit-identical.
- Memory-only pressure fixture: maximum height 0.0770414174 m, zero new foam.
- Implicit mode changes/reseeding and negative activity rates rejected.

These are controlled numerical checks, not photographic acceptance. The
memory-only fixture starts with activity everywhere, unlike the live scene.

## Actual scene evidence

Session 83100 exited 0, `ActivityMemoryMotion.log`, using the unchanged
registered-rock map and unified-foam optics candidate with all prior review
flags plus activity memory. Log confirms `activity_memory=1`.

Recording: `unreal/Saved/VideoCaptures/RaftSim_20260907-214112.mp4`, 695 source
frames over 23.991 seconds; 720 decoded frames. Unmodified 1/8/16/23-second
frames and full image-change measurements are in `detail-motion/ActivityMemoryMotion*`.
The 8- and 23-second images were inspected: broad foam remains smooth and
spray remains puffy/detached-looking. The candidate is **not photorealistic**.
Encoded frame count and luma differences are not game FPS or fluid velocity.

Paired GPU flow/state/resolved-texture snapshots are in `activity-snapshot/`.
The independent resolve checks passed below 1e-5, with finite arrays,
nonnegative foam, and bounded coverage. The diagnostic does not capture the
activity buffer itself. The analyzer now accepts `--directory`, preserving
the prior baseline rather than overwriting it.

| Approximate elapsed | Foamy cells | Median added height | p95 added height | RMS added height |
| --- | ---: | ---: | ---: | ---: |
| 10 s | 108 | 6.141 mm | 22.440 mm | 10.981 mm |
| 15 s | 125 | 4.629 mm | 20.833 mm | 9.275 mm |
| 20 s | 126 | 4.884 mm | 26.150 mm | 11.973 mm |

Foamy means resolved coverage >0.65 and full interior weight. Prior baseline
median heights were 2.276/2.211/2.614 mm; RMS 8.169/7.210/8.856 mm. Sparse
sampling times differ slightly. This is additional GPU perturbation only,
not total crest height, a frequency spectrum, or a same-cell energy budget.
Foam-overlap 5-second height-difference RMS is 13.049/18.161 mm.

## Performance and disposition

Separate session 84717 exited 0, with **no recording or diagnostic readbacks**.
`survey_performance_activity_memory.json`: same registered map, 1280×720 at
87%, RTX 3060 Laptop, offscreen Development, 5 s warmup/20 s measurement.

- Mean frame 14.318 ms, p95 19.436 ms, mean GPU 6.888 ms.
- Mean solver 9.000 ms; one wall-clock hitch over 33 ms.
- Unchanged frame 16.667 ms and solver 1.6 ms gates both **fail**.

The prior optics-only run had p95 21.699 ms and solver 9.574 ms. This isolated
run does not prove the new memory caused a performance improvement; CPU
variation dominates. No packaged/release qualification or repeated-until-pass
claim. Existing experimental editor-plugin startup errors remain outside the
clean automation results.

Keep this opt-in. It demonstrates downstream relief persistence but does not
solve realistic boiling foam, surface-coupled spray/landing, or the CPU budget.
Do not increase forcing arbitrarily to conceal remaining model limitations.
Geographic identity, rock shape, registered-map traversal, raft support,
later rivers, crew, cleanup, release checks, and final commit remain open.
