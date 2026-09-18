# Exact continuation after the 5400-second checkpoint

2026-09-17. This continues the source-matched hydraulic cook; normal gameplay
still uses the installed 4950-second state. No later state is promoted here.

The previous process, PID6968, is terminal: its handle was absent after its final
10000-step/5400-second completion record appeared. No exit code was captured,
so exit zero is not claimed. The final state and all 86,720 artificial bank
cells pass independent audits, with empty stderr and no failure marker.

The existing restart generator preserves all 5,382,400 original cells exactly,
including bed, roughness, boundaries and clock. It adds no cells or water.
Native continuation audit confirms zero volume error and bit-exact h/u/v.
New input: `tmp/control-ablation-5400to7200s-input-v1-20260917/manifest.json`,
SHA256 `b608b82588501af10e7149f04f884b5eac4fcd4820886ff963bbe9adc58f39aa`.
Restart audit: `tmp/control-ablation-5400s-continuation-restart-v1-20260917.json`,
SHA256 `b79f2d4d74565b4cf78470ab9f20154fb153dd77acbd9458d45b3db1db84d372`.

The new eight-lane process is PID32728, started UTC
`2026-09-17T22:01:07.6154364Z`, executable
`tmp/solver-worker-limit-v1-20260917/raftsim_cartesian_cook.exe`, SHA256
`458a1fcd3f2f12391012032398d29a4b2eadb792df2e9ee09b88dff263abc8e4`.
It runs 36,000 unchanged 0.05-second steps to 7200 seconds, writing to
`tmp/control-ablation-5400to7200s-workers8-v1-20260917`. Revalidate the live
handle/start/executable before any future control; this record is not proof
that the process remains live indefinitely.

Completed 5450, 5500, 5550 and 5600-second checkpoints pass BOTH the full state audit
and all 86,720 exactly dry artificial-bank checks. At 5550 seconds: maximum
depth 3.696207410 m, speed 5.141559302 m/s, volume 2,794,929.961240 m3 and maximum
step conservation residual 1.424946e-8 m3. Outflow is 123.494411 m3/s against
45.306955 m3/s inflow: **not settled**. Reports are
`tmp/control-ablation-{5450,5500,5550}s-{state,banks}-v1-20260917.json`.
5550-second depth SHA256:
`9c3bd05d0cf40a9ce06f58837740b0c5ad6c16b289888197a85a6f4dfa1d1e88`.

At 5600 seconds, maximum depth is 3.696135495 m, speed 5.409996469 m/s,
volume 2,791,013.887468 m3 and outflow 120.411979 m3/s versus the same inflow.
Still not settled. Both reports:
`tmp/control-ablation-5600s-{state,banks}-v1-20260917.json`; depth SHA256
`80cbfbde1ca4a56ff79731790a84fb920f598bb882c1b86cf821353ce5813c0d`.
5650 and 5700 seconds now pass both full-state and artificial-bank audits.
Reports: `tmp/control-ablation-{5650,5700}s-{state,banks}-v1-20260917.json`.
At 5700 seconds maximum depth is 3.697731395 m, speed 5.413853960 m/s,
volume 2,783,158.975307 m3 and maximum step residual 1.424946e-8 m3.
Outflow 124.765308 m3/s still exceeds inflow 45.306955 m3/s: NOT settled.
All 86,720 artificial bank cells remain exactly dry. 5700-second depth SHA256:
`c9cb6c3b1af0884ce836d0b729384550f586ef51a7db05cba6dc4b65d91848ce`.
5750 seconds/local7000 also passes BOTH audits. Maximum depth 3.699409066 m,
speed 5.461326199 m/s, volume 2,779,227.603968 m3; outflow 126.197287 m3/s
versus the same 45.306955 inflow, still NOT settled. Reports:
`tmp/control-ablation-5750s-{state,banks}-v1-20260917.json`; depth SHA256:
`57c7822afefbc64ac76bc15bfdce7117751b99160b7e6c58f933229997a842e5`.
5800/local8000 and 5850/local9000 now pass BOTH audits. At 5850 seconds,
maximum depth is 3.703972637 m, speed 5.477930826 m/s and volume
2,771,359.981574 m3. Maximum step residual remains 1.424946e-8 m3.
Outflow 122.771842 m3/s versus inflow 45.306955 m3/s is still NOT settled.
All 86,720 artificial-bank cells remain exactly dry. Reports:
`tmp/control-ablation-{5800,5850}s-{state,banks}-v1-20260917.json`.
5850-second depth SHA256:
`4588e7907f65c8c569ef3e56b8bfcc21009de74d1b778d510cfde8d28661a6d5`.
5900/local10000 also passes BOTH audits. Maximum depth 3.706955389 m,
speed 5.498792871 m/s and volume 2,767,431.274178 m3; outflow
123.516389 m3/s versus the same 45.306955 inflow, still NOT settled.
All 86,720 artificial-bank cells remain exactly dry. Reports:
`tmp/control-ablation-5900s-{state,banks}-v1-20260917.json`; depth SHA256
`5d36f1756435628150f22cc6142f71915ae8b11d00da5e04496bd524b7bfb837`.
Next 5950 seconds is local step11000 in the NEW continuation output.

Each later checkpoint requires its completion marker and both independent
audits. Bounded depth/speed, exact restart and conservation do not prove settled
flow, bathymetric truth, physical breaking, convincing froth or playable contact.
Captured terrain and inferred bed/flanks retain their separate provenance.
