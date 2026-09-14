# Positive donor-face transport: accuracy gate still fails

September 14, 2026. Research only; no native, terrain, material, source-history
or playable-scenario changes. Desktop target remains 30 FPS / p95 33.333 ms;
physics 120 Hz and production solver 1.6 ms are unchanged. The full goal is open.

## Implemented and tested

`physics/scripts/hydrostatic_energy_transport.py` uses the original unscaled
MC depth/free-surface reconstruction and hydrostatic retained face heights.
A mass-weighted face velocity selects the donor cut height. At a frozen state,
this defines a linear velocity-to-mass-rate map T. Its transpose is assembled
from those same faces, including algebraic cancellation of owner depth in
the normalized energy adjoint. No depth floor, clamp or mass repair is used.

The donor outgoing-flux bound admits nonnegative forward-Euler mass steps.
Steps exceeding the bound are rejected. This is mass-only positivity, not
qualification of pressure at dry cells, energy through time, shock entropy,
open boundaries or wetting in the coupled model. T is a new transport, not
the original FV/Rusanov evolution. Upwind selection and weights are frozen
for the transpose identity; it is not a derivative through their state dependence.

Five focused cases pass: transpose work and normalized-adjoint equivalence
on three array shapes (including singleton/two-cell periodic aliases),
nonnegative mass and conservation, exact-dry velocity independence, a blocked
bed barrier, actual wet-to-dry inflow, resting all-dry state and invalid-step
rejections. Inputs are unchanged. The sixth, smooth refinement, FAILS.

Combined with the earlier reverse/dual-energy/bracket tests: **25 PASS / 1 FAIL**
in 7.59 s. Retained report:
`tmp/hydrostatic-energy-transport-combined-v1-20260914.xml`.
Original focused failure remains in `tmp/hydrostatic-energy-transport-v1-20260914.xml`.
This suite is not the earlier 31-test suite or the earlier 40 PASS / 8 FAIL suite;
neither historical result is superseded.

## Diagnosed failure, unchanged gate

The original smooth variable-bed probe has L1 mass-rate errors:

| Cells | L1 error |
| --- | --- |
| 32 | 0.001494454026165326 |
| 64 | 0.0005753170567170648 |
| 128 | 0.00017673557488733898 |

Ratios are **2.597618** and **3.255242**; the original test requires BOTH >3.2.
No phase, resolution, expected solution or threshold was changed.

`audit_hydrostatic_energy_transport.py` retains these probes and adds finer
grids and uncut/unlimited diagnostic expressions. Removing cuts alone still
fails the first ratio (1.54142). Removing MC limiting in the diagnostic yields
ratios 4.35790 and 4.19743 with cuts, or 4.24067 and 4.12516 without cuts.
There are four limited depth cells and four limited free-surface cells at
each tested resolution. Thus the observed coarse-grid failure is associated
with extrema reconstruction, not eliminated by dropping the bed cut. This
does not establish that the method is globally first order: original finer
ratios vary substantially (4.61639, 3.58426, 9.60025). It also does not waive
the failed original test.

Report: `tmp/south-fork-hydrostatic-energy-transport-refinement-v1-20260914.json`.
Unlimited and uncut expressions are diagnostic controls, NOT candidate
replacements: their dry-bank/positivity behavior is not accepted. The transport
has not been coupled to the variational stage, evolved or integrated in gameplay.

Next: resolve extrema reconstruction while retaining positive donor transport
and physical bed barriers, rerun the unchanged refinement and dry/mass gates,
then qualify a matching coupled energy stage and actual wetting/evolution.
Visible water, breaking/froth, terrain, native cost, later rivers and release
work remain required. An algebraic energy identity alone is not physical validation.

## Original full-river cook and histories

All five original long-job handles directly confirmed live; none restarted,
suspended or reset. Both dependency guards rechecked: 417/422 files, zero changes.
Cook 83142 passed 9000 seconds and continued to 9006 at direct check.
The complete local-20000 checkpoint passes BOTH audits:

- `tmp/south-fork-expanded-9000s-state-v1-20260914.json`: 5,382,400 finite cells,
  maximum depth 3.7765690181 m, speed 6.2207074360 m/s, volume 2,567,345.18795 m3.
  Snapshot/driver volume difference is exactly zero; maximum step conservation
  residual 1.441913611e-8 m3.
- `tmp/south-fork-expanded-9000s-banks-v1-20260914.json`: all 86,720 artificial
  bank cells exactly dry, 1,084 bank faces and 2,276 shared directed tile faces.

Depth SHA256: `04d7b3566594f6292999958659229a2831a8c297b6d42fdb32cb41dd9c9e355e`.
Outflow is 101.3846771443 m3/s versus inflow 45.3069545472 m3/s: STILL UNSETTLED,
not a normal-map integration acceptance. Next complete checkpoint 9100 seconds /
local step 22000 needs BOTH audits after its completion marker exists.

The original requested history reached accepted time 0.8753107248 s (speed
78.04173 m/s). Original observation-only history reached 0.7980092675 s
(57.46327 m/s). The old failure-clock and difference-scalar histories remain
live and unqualified. No splicing or source alteration.

## Reference access retry

Retried both supplied YouTube links, `ZEG1kvjNI30` and `2XTbOCNDcZQ`.
Direct web fetch still returns cache misses. After reading the computer-use
skill and required guidance, browser access and its native skill-runtime
initialization both fail with `failed to write kernel assets: The system cannot
find the path specified. (os error 3)`. No new frame, playback or comparison
was obtained, and no remote-media download workaround was used.
