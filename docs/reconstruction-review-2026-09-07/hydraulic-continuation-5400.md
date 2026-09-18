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
5950/local11000 and 6000/local12000 now pass BOTH audits. At 6000 seconds,
maximum depth is 3.713839153 m, speed 5.530472125 m/s and volume
2,759,604.081552 m3. Maximum step residual remains 1.424946e-8 m3.
Outflow 125.137876 m3/s versus inflow 45.306955 m3/s is still NOT settled.
All 86,720 artificial-bank cells remain exactly dry. Reports:
`tmp/control-ablation-{5950,6000}s-{state,banks}-v1-20260918.json`.
6000-second depth SHA256:
`bf0d627a81fbc612274eeafce5af8d754418552be0be5979d5fbfd3a340b5cb9`.
6050/local13000 also passes BOTH audits. Maximum depth 3.717678177 m,
speed 5.541904894 m/s and volume 2,755,708.831876 m3; outflow
121.949972 m3/s versus the same 45.306955 inflow, still NOT settled.
All 86,720 artificial-bank cells remain exactly dry. Reports:
`tmp/control-ablation-6050s-{state,banks}-v1-20260918.json`; depth SHA256
`de8ce4e0ae56f1cbde66997ff3c1fc334cc5528a7fd18aeab267df4d176adda9`.
6100/local14000 and6150/local15000 now pass BOTH audits. At6150 seconds,
maximum depth3.726166096m, speed5.571480314m/s, volume2,747,959.126055m3,
maximum step residual1.424946e-8m3. Outflow121.202279m3/s exceeds the same
45.306955m3/s inflow: still NOT settled. All86,720 bank cells remain exactly dry.
Reports: `tmp/control-ablation-{6100,6150}s-{state,banks}-v1-20260918.json`.
6100 depth SHA256:
`36c5552b3f7b401c3d8aa02866ec2dae7fe411344ffc7a9be9fb8cd2febae4aa`.
6150 depth SHA256:
`8cc25f6293f62982f5fe8d3e5b3608a0c5b952cbcdfdc1203ad3ba3893b2d47b`.
6200/local16000 and 6250/local17000 now pass BOTH audits. At6250 seconds,
maximum depth3.735467780m, speed5.606395443m/s, volume2,740,285.842275m3,
maximum step residual1.424946e-8m3. Outflow121.520100m3/s exceeds the same
45.306955m3/s inflow: still NOT settled. All86,720 bank cells remain exactly dry.
Reports: `tmp/control-ablation-{6200,6250}s-{state,banks}-v1-20260918.json`.
6200 depth SHA256:
`c36bac008bacf8db5fca58af658ea4a08b5e63d932454bf3d78bb785eb5a9563`.
6250 depth SHA256:
`79431054821f043917713fd1b497574660cf8840f8ade842c559099453c85b90`.
Same process32728/start2026-09-17T22:01:07.6154364Z verified live beyond6250;
not restarted. Installed4950 state remains unchanged.
6300/local18000 and6350/local19000 now pass BOTH audits. At6350 seconds,
maximum depth3.745191598m, speed5.623021738m/s, volume2,732,696.186332m3,
maximum step residual1.424946e-8m3. Outflow118.862076m3/s exceeds the same
45.306955m3/s inflow: still NOT settled. All86,720 bank cells remain exactly dry.
Reports: `tmp/control-ablation-{6300,6350}s-{state,banks}-v1-20260918.json`.
6300 depth SHA256:
`016743c8e57ad54ee90580544e1698bdf754002beded96d1b18b1f0bc7bb6535`.
6350 depth SHA256:
`501068cc5814cd627ade3a3887d79d5a0cd76547edf2ddde7d7d4b59c31b7224`.
Same verified process32728 continues; installed4950 state remains unchanged.
6400/local20000 also passes BOTH audits. Maximum depth3.750116598m,
speed5.630827590m/s, volume2,728,936.087507m3; outflow119.795932m3/s versus
the same45.306955m3/s inflow, still NOT settled. All86,720 bank cells remain dry.
Reports: `tmp/control-ablation-6400s-{state,banks}-v1-20260918.json`; depth SHA256
`c5c09e00985bf1314881bfb247334ac8405b64a806c89e0b3eda3fc714bbb6ce`.
6450/local21000 and6500/local22000 now pass BOTH audits. At6500 seconds,
maximum depth3.759948636m, speed5.644894969m/s, volume2,721,497.163048m3,
maximum step residual1.424946e-8m3. Outflow120.360804m3/s exceeds the same
45.306955m3/s inflow: still NOT settled. All86,720 bank cells remain exactly dry.
Reports: `tmp/control-ablation-{6450,6500}s-{state,banks}-v1-20260918.json`.
6450 depth SHA256:
`66de6efd8194cd3516cb5866842bba1622aa0d2bc3cddc3960633fe4ac3e9f07`.
6500 depth SHA256:
`a0d27a4f1350c240587caa89c3c81539b0c74b0aa92fb9268b83fb7a0328a4c8`.
Same process32728/start2026-09-17T22:01:07.6154364Z verified live beyond6500;
not restarted. Installed4950 state remains unchanged.
6550/local23000 also passes BOTH audits. Maximum depth3.764660869m,
speed5.655179307m/s, volume2,717,820.114207m3; outflow120.607855m3/s versus
the same45.306955m3/s inflow, still NOT settled. All86,720 bank cells remain dry.
Reports: `tmp/control-ablation-6550s-{state,banks}-v1-20260918.json`; depth SHA256
`fe00ed5ea94a19448de9dc9aafbdab77c03d2d0cace0611487d758e96effb975`.
6600/local24000 also passes BOTH audits. Maximum depth3.769351354m,
speed5.293704502m/s, volume2,714,168.040094m3; outflow117.963657m3/s versus
the same45.306955m3/s inflow, still NOT settled. All86,720 bank cells remain dry.
Reports: `tmp/control-ablation-6600s-{state,banks}-v1-20260918.json`; depth SHA256
`53b285093de37501bae34716938f892291f227a1e4037f2826d42f00315c70a5`.
6650/local25000 also passes BOTH audits. Maximum depth3.773917551m,
speed5.301456196m/s, volume2,710,547.562100m3; outflow117.856683m3/s versus
the same45.306955m3/s inflow, still NOT settled. All86,720 bank cells remain dry.
Reports: `tmp/control-ablation-6650s-{state,banks}-v1-20260918.json`; depth SHA256
`e7fdef10e8a6b21b7856b3cce3d3c3f6429b609ae1b5929fa2a22b1c6c51c9d8`.
6700/local26000 and6750/local27000 now pass BOTH audits. At6750 seconds,
maximum depth3.782360143m, speed5.313829949m/s, volume2,703,392.638695m3,
maximum step residual1.424946e-8m3. Outflow116.341338m3/s exceeds the same
45.306955m3/s inflow: still NOT settled. All86,720 bank cells remain exactly dry.
Reports: `tmp/control-ablation-{6700,6750}s-{state,banks}-v1-20260918.json`.
6700 depth SHA256:
`92396a206cf42d352df9560f808d31d2bc79bd1796f6296b424f2728da396855`.
6750 depth SHA256:
`b8d350f668bdb21ca6e07a8f840b22870ab4d43b77a94949568585a96980a367`.
Same process32728 continues; installed4950 state remains unchanged.
6800/local28000 also passes BOTH audits. Maximum depth3.786300304m,
speed5.318740344m/s, volume2,699,860.312955m3; outflow112.361140m3/s versus
the same45.306955m3/s inflow, still NOT settled. All86,720 bank cells remain dry.
Reports: `tmp/control-ablation-6800s-{state,banks}-v1-20260918.json`; depth SHA256
`9ca6b8db7ac0b88e236c7413988ba6d9cb2628f479bd117d419bb70a3aa9782c`.
6850/local29000 and6900/local30000 now pass BOTH audits. At6900 seconds,
maximum depth3.793584349m, speed5.326638599m/s, volume2,692,889.488485m3,
maximum step residual1.424946e-8m3. Outflow113.274088m3/s exceeds the same
45.306955m3/s inflow: still NOT settled. All86,720 bank cells remain exactly dry.
Reports: `tmp/control-ablation-{6850,6900}s-{state,banks}-v1-20260918.json`.
6850 depth SHA256:
`812ca8032e0e11573e10a9cca91ccf8d6b52eef8a5a728332b6a128a1edb800d`.
6900 depth SHA256:
`d54ce0270d6f1693dbe38635bd89dad23941d3c4441b0dc96a11866be165085c`.
Same process32728 continues; installed4950 state remains unchanged.
6950/local31000,7000/local32000 and7050/local33000 now pass BOTH audits.
At7050 seconds maximum depth3.802514716m, speed5.334983890m/s,
volume2,682,665.187941m3 and maximum step residual1.424946e-8m3.
Outflow113.409385m3/s exceeds inflow45.306955m3/s: still NOT settled.
All86,720 artificial-bank cells remain exactly dry at each checkpoint.
Reports: `tmp/control-ablation-{6950,7000,7050}s-{state,banks}-v1-20260918.json`.
6950 depth SHA256:
`158841598866dc0500b8186667b2d1caf02b984a413ee4af0194144b6e7b3f56`.
7000 depth SHA256:
`88ce71a3e62adbaa9d88974600a2a1d956acde448cc50e79c699992f60247fb0`.
7050 depth SHA256:
`a826d36f76f8bbe5b8ee8e7fbc43981f700eaca796be4cf5c1836358117be3eb`.
Same verified process32728 continues; installed4950 water remains unchanged.
7100/local34000 also passes BOTH audits. Maximum depth3.805150618m,
speed5.337065169m/s, volume2,679,320.236017m3. Outflow113.893921m3/s
still exceeds inflow45.306955m3/s; NOT settled. All86,720 bank cells remain dry.
Reports:`tmp/control-ablation-7100s-{state,banks}-v1-20260918.json`;
depth SHA256:`b5df097f0b044cb17c31c715d2f29fe3584bc5eafd4caa5dd2b37ec6d4c01143`.
Next7150 seconds is local step35000 in the NEW continuation output.

Each later checkpoint requires its completion marker and both independent
audits. Bounded depth/speed, exact restart and conservation do not prove settled
flow, bathymetric truth, physical breaking, convincing froth or playable contact.
Captured terrain and inferred bed/flanks retain their separate provenance.
