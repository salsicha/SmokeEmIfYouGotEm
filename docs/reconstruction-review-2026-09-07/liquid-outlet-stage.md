# Native outgoing-stage boundary — September 8, 2026

Status: isolated review candidate; not promoted or accepted as realistic water.

The previous compatible-projection candidate imposed normal velocity at every
wet exchange face, including outgoing faces. Its downstream level was therefore
not an independent pressure boundary. This candidate retains native inflow and
replaces only outgoing face columns with a prescribed hydrostatic stage.

Source remains the unchanged `grid_boundary_profile.json` generated from the
registered one-metre shallow-water field. Its stage is model-derived, not a new
survey measurement. The submerged bed remains inferred. No boulders, terrain,
native source arrays, saved scene or saved Niagara assets are moved or replaced.

For outgoing profile columns (`inward normal speed < 0`), ghost cells above the
profile bed receive classification 3: external stage, neither fluid unknown nor
solid wall. Their kinematic pressure is `980 * max(stage_cm - z_cm, 0)` in
cm²/s², using the active simulation's gravity of 980 cm/s². This includes zero
atmospheric pressure above the target level. Incoming columns retain prescribed
normal velocity. The open pressure condition does not artificially clamp the
outgoing velocity or delete additional water particles.

The existing compatible collocated `D M G` matrix includes external pressure as
a Dirichlet contribution while solving only interior fluid unknowns. Solid
velocity constraints and terrain contact remain unchanged. This is not a MAC
or cut-cell conservation claim; the binary bed/ghost support still has limits.

Implementation is in `RaftSimOutletStage.h`, the compatible pressure installer,
and the registered boundary classifier. The new console variant is `outlet-stage`
and capture flag is `-RaftSimLiquidTerrainOutletStage`. It builds only a transient
`_OutletStage_` system. The shared input helper respects Niagara's dynamic input
sentinel ordering; typed parameter reads now follow unambiguous reroute nodes.

The CPU reference accepts explicit external pressure and rejects missing stage
values. `liquid_outlet_stage.py` independently reconstructs the expected ghost
classification and pressure from the source profile. The GPU readback audit
compares them cell by cell, in addition to the final divergence/residual check.
Twenty-two focused Python tests pass, including nonzero pressure projection,
outgoing-only classification, zero pressure above stage and fixture validation.

V1–V3 are retained installation failures, not physical results: the pressure
module's boundary interface was behind `NiagaraNodeReroute_8`. V4 includes the
resolved connection but failed compilation, as recorded below.
Full South Fork acceptance, calibrated storage and exit accounting, optics,
animation, raft coupling and real-time performance remain outstanding.

The stage reference also converges on the actual V12 river grid after replacing
its outgoing boundary with the prescribed stage: 89 PCG iterations, relative
residual 9.04e-8, divergence RMS 0.016829/s to 7.03e-9/s, no fixed velocity
changes. This is an altered-boundary CPU reference, not an engine result. See
`liquid-outlet-stage-reference/report.json`.

V4's changing worker job files initially looked like compilation progress.
Subsequent output inspection established that they were repeated shader syntax
failures: case-insensitive `POSITION` substitution also replaced the suffix in
`stagePosition`, producing invalid `stagefloat3(...)` declarations. Permutations
6 and 10 retried continuously. The verified owned process was then stopped;
no physical or rendered results from V4 exist and no production assets were saved.

Substitution now explicitly uses case-sensitive matching. A new engine test
checks the generated declaration and subsequent variable references. The
two-phase graph/GPU wait and expanded outlet-variant test are built.

V5 completes 12 simulated seconds in 27.972s capture wall time. All 4,142
external-stage cells match the independent classifier, with maximum pressure
error 0.0719 cm²/s² (float32 arithmetic). The matching pressure residual times dt
is 0.022554/s and final velocity divergence 0.022555/s; the difference is
0.000394/s, consistent with half-float velocity storage. Fixed velocity error
on pressure support is at most 0.015625 cm/s. There are zero nonfinite states,
zero missing bed queries and zero penetrations among 89,564 exact bed probes.

Mean particle speed is 58.694 cm/s; upstream/centre/downstream quarter mean
downstream velocities are 52.763/32.294/29.452 cm/s. The lower downstream speed
does not establish better flow fidelity or source/exit conservation. The
opacity-one image remains too pale and homogeneous. No visual acceptance.

The 60s run also completes (`liquid-outlet-stage-60s`, 83.505s capture wall time).
All 4,142 stage cells match, with the same 0.0719 cm²/s² maximum pressure error.
Pressure-residual prediction is 0.022236/s versus actual divergence 0.022238/s;
their RMS difference is 0.000403/s. Pressure-support fixed velocity error is at
most 0.0625 cm/s. Among 98,673 exact bed probes there are no missing queries or
detected penetrations, and no nonfinite states. Mean particle speed is 56.122
cm/s; upstream/centre/downstream mean Vx is 43.972/34.148/33.630 cm/s. The image
still resembles pale homogeneous liquid, not accepted river optics or whitewater.
These blocking diagnostic runs do not measure gameplay performance or conserved
water volume. Marker counts are not mass measurements.

`engine-liquid-outlet-stage/index.json` records nine clean engine passes, zero
warnings/failures (18.122s), including generated shader substitution and all nine
transient variants. The focused Python suite now has 23 passes, including an
all-fluid/no-solid audit regression. The saved source system and shipping scene
are not promoted by any of these checks.
