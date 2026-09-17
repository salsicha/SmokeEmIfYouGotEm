# Current solver whole-program optimization: not promoted

Recorded 2026-09-17 UTC. This is a measured rejection, not a runtime improvement
or 30 FPS acceptance. No source equations, solver settings, installed archive,
engine DLLs, scenario assets or gameplay behavior changed.

## Candidate and unchanged inputs

The ordinary South Fork capture still has mean game-thread time35.428940ms,
GPU12.233090ms and solver5.953484ms. Crest selection remains the largest spike.
Existing row/CFL optimizations are already present in the editor definitions
through archive identity2ce80e6f2c5d13ca75123deb16326bdee21a9048d6558de4703a0db138c8bdfe;
there was no unlinked row-optimization shortcut to assume.

An isolated MSVC19.44 Release build uses CMake's standard
`CMAKE_INTERPROCEDURAL_OPTIMIZATION=ON`. It changes compiler visibility across
translation units, not equations or timestep/grid/dry/roughness settings. All
four native CTest fixtures pass in8.86s. Baseline is the unchanged current
CFL-row solver, not the older unoptimized solver from historical comparisons.

The earlier September7 LTO experiment was also not adopted; this fresh trial
tests the substantially changed current row-parallel solver. Do not repeat
either compiler trial as a new performance idea without a different mechanism.

- Candidate: `tmp/solver-lto-v1-20260917/raftsim_water_solver.exe`, SHA256
  `c2c86ecc81b0673342beb5202c59d71d65efd13f23d6ca252693e441140a8aab`.
- Baseline: `tmp/solver-cfl-rows-v1-20260916/raftsim_water_solver.exe`, SHA256
  `47fc97aa7585923253442f3a7c451537f715bcce5f6c3437f50b8ee252513c73`.
- CTest: `tmp/solver-lto-v1-20260917/Testing/Temporary/LastTest.log`, SHA256
  `05600057d55d964c61f4e1dffbcc74d2ea0aaad0c094f679c7602c7bf862c381`.

## Paired evidence and rejection

Each input runs four alternating-order pairs of600 steps with11 saved frames
per process. All44 saved frame pairs per input are byte-identical, including
derived fields and dry masks. All16 processes exit0. The Cartesian recipe
retains its explicit limitation: native runtime-export identity is not proven.
Its equivalence does not qualify physical inputs or engine performance.

Mean solve-and-capture seconds, excluding separately reported CSV export:

| Input / order | Baseline | Candidate | Reduction |
| --- | ---: | ---: | ---: |
| Cartesian / baseline first | 2.833470 | 2.844470 | -0.3882% |
| Cartesian / candidate first | 2.904140 | 2.814105 | 3.1002% |
| Registered / baseline first | 2.851010 | 2.789700 | 2.1505% |
| Registered / candidate first | 2.789440 | 2.701760 | 3.1433% |

The Cartesian baseline-first result is slower. Thus the candidate fails the
unchanged requirement for an improvement in both execution orders, despite
the combined median reductions of2.4148% Cartesian and3.0228% registered.
Background work continued during these component comparisons; they are not
uncontended engine FPS evidence. `passed=true` in their reports means state
equivalence and process success only, not accepted timing or promotion.

- Cartesian report: `tmp/solver-lto-cartesian-pairs-v1-20260917/report.json`, SHA256
  `2d823e444f415acf7de8471529ab6ff8a5b8fe02101b8f780fbda1c4547fe63f`.
- Registered report: `tmp/solver-lto-registered-pairs-v1-20260917/report.json`, SHA256
  `36ad94e743c26137eb3d43d64d2c7afd0c831e09569216677cfc47281fe31980`.

No engine integration or ordinary FPS claim follows this failed performance
candidate. The production library builder and CMake defaults are unchanged.
Keep the ignored build and reports as evidence; do not replace the live cook.
Further performance work needs reduced runtime work in the measured crest or
solver paths, not another invocation of the same compiler optimization.

## Hydraulic continuation and full remaining scope

Same cook51728/PID36872 reaches2300s/local10000. Both state and all86,720 exactly
dry artificial-bank checks PASS across5,382,400 cells. Maximum depth4.1839926513m,
speed7.0136217217m/s, volume2,971,894.1251475746m3 and maximum step conservation
residual1.6470207420e-8m3. Outflow96.5509769210m3/s versus45.3069545472m3/s in:
**not settled, calibrated or promoted**. Next2350/local11000 requires both audits.

- State: `tmp/control-ablation-2300s-state-v1-20260917.json`, SHA256
  `fc9c9a1505b22767d86d7ffec392cbbf32480d271e966d78f9460d9aeb0e68fc`.
- Banks: `tmp/control-ablation-2300s-banks-v1-20260917.json`, SHA256
  `8d724834112e29e8784e8ef42fecf1e649ecb915230310cfbfbdaa5253c8c2f7`.

Original native SM5 replay55459/editor36412 and worker37836 remain live on
transport permutations4/21; shader inputs remain frozen. This is not a pass.
The last ordinary28.057157FPS/p9541.2354ms still fails30FPS. Last physical
regression remains599 PASS/13 unchanged FAIL, not rerun for this compiler-only
trial. Source-face transport still needs compatible pressure/curvature/bed
forces, donor evolution and branch transitions before runtime integration.

Evidence-based terrain/boulders/collision, moving breaking/froth, normal South
Fork integration, Colorado->Pacuare->Futaleufu, Chilko/Zambezi/all-scene water,
crew, normalization, outstanding regressions and release remain open.
Troublemaker is only a rapid within South Fork, never its own menu scenario.
