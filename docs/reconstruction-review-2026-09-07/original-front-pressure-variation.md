# Original moving-front pressure variation

2026-09-18. The current nonlinear force/time implementation handles complete
fixed wet support but rejects source activation. The original local dry-front
pressure map has now been verified separately; this change connects its exact
solved unknowns to the existing primitive energy derivative for original-case
checking. It does not invent the missing conservative wetting/force law or
enable nonlinear gameplay. Normal South Fork water and visuals are unchanged.

## Reuse unknowns, recheck the equations

`FrontPressureVariation` accepts an optional solved state. It reuses only the
canonical and two auxiliary velocities, while requiring the original represented
pole lengths, weights and order. It checks each exact original equation
`(M+lambda*C)*a=M*v` and reconstructs the supplied physical momentum from both
poles. Positive original matrices make those checks a uniqueness condition;
reported success flags and stored derivatives are never used instead.

The complete existing derivative follows unchanged, including both owner-volume
denominators, actual depth moments, directed common-face columns and bed slopes.
Both physical and canonical momentum coordinates retain their distinct gradients.
No approximate cache, rounded projection, residual redistribution, mass floor,
altered pole or new force is introduced. The original fresh-solve entry remains.

The new `audit_south_fork_front_pressure_variation.py` rebuilds each supported
case from the original registered mesh, affine plane and local fan. It compares
owners, volumes/rates, full pressure/divergence matrices and directed face data
to the qualified preceding report. Original wet/dry momenta and rates must
match. It then checks physical and canonical primitive time-work against the
previous complete energy derivative, including its momentum/geometry split
and a separate full-matrix contraction. All prior records, unsupported cases
and source hashes are preserved; imported implementation hashes must remain
unchanged through completion.

This checks a local reflecting-pressure component, not natural open river
boundaries, interacting fronts, gravity/transport closure or native40-CG costs.
Published [SGN split-form work](https://arxiv.org/abs/2408.02665) was inspected as
methodological context. Its equations are not substituted for the project's
two-pole model, and its conservation proofs are not claimed for this code.

## Verification

40 focused tests PASS in23.85s: 24 new controls plus the16 existing primitive
derivative tests. Every derivative agrees exactly with the fresh-solve path,
including carried physical/canonical work. A forbidden-solve control proves
the optional path does not call the old solve or auxiliary map. Perturbations
as small as1e-400 in velocities, pole constants, momentum, geometry and work
are rejected. Original independent complex-step and refined real-direction
derivative checks still pass. Report:
`tmp/solved-pressure-variation-focused-v2-20260918.xml`, SHA256
`47bdbe8ca87ed3d2745b43e572a02ae454c74a45ea94ce61484ee6e5f6f5534b`.

Broader physical regression completes across the same63 prior modules plus
the two new modules: **808 PASS / 13 FAIL**,821 tests, no errors/skips,
277.74s and one existing JUnit metadata warning. Failure identities match the
preceding suite exactly: four constant-velocity energy controls, eight paired
nonlinear energy controls, and the legacy storage/face consistency gate.
No failure is waived or redirected. Report:
`tmp/solved-pressure-variation-full-suite-v1-20260918.xml`, SHA256
`80e5f2762391820911088ae3b694ed069712424a2eb243dd8037cd5c155a46be`.

## Original-source job and continuation

Input: `tmp/south-fork-moving-pressure-metric-v1-20260918.json`, SHA256
`3fbd2603d037de54c6fa0ca0d921e1c1c76f8ab50815c878b3906727bb84b5ef`.
Fresh output: `tmp/south-fork-front-pressure-variation-v1-20260918.json`.
Original process21256/startUTC2026-09-18T03:20:39.1088023Z/session21082 has
completed exit0. All11 supported local cases pass; the two unsupported records
remain. The expensive case1/source601453 takes2382.3269975s. Output is202,206,834
bytes, SHA256`9ba9e4387631fddbe66ce06c4773e292095ad260c6e5a82e778a6803500948db`.
It has not been restarted. All in-job protected/imported hashes match at exit.

Independent reloader `tmp/verify-front-pressure-variation-v1-20260918.py` is
LIVE as38716/startUTC2026-09-18T04:09:43.6775796Z/session9281. It reconstructs
the original geometry and independently contracts the serialized primitive
gradients with original moment/face/momentum rates in BOTH coordinates. It
checks preserved source records and all current hashes. Case0 passes; the
expensive next contraction is running. Preserve this same process; no
independent all-case verification is claimed until it completes and produces
`tmp/front-pressure-variation-review-v1-20260918.json`. It does not repeat the
original pole solves or establish a conservative force/wetting/native/gameplay
law. All full-acceptance flags remain false.

The6850/6900 hydraulic states pass state AND dry-bank audits but are not settled;
installed4950 stays unchanged. No new native build, rendered-motion comparison,
visual improvement or FPS acceptance is supplied by this physics-only change.
Last ordinary frame p9543.1591ms still fails30FPS/33.333333ms. The nonlinear
runtime stays OFF. South Fork, then Colorado, Pacuare, Futaleufu, plus
Chilko/Zambezi, crew, normalization, regressions and release remain OPEN.
Troublemaker stays a rapid within South Fork, never a menu scenario.
