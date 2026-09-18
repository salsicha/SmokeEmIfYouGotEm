# Exact continuation after the 7200-second checkpoint

2026-09-18 UTC. Source-matched hydraulic settling continues; normal gameplay
still uses the installed4950 state. No new visual, breaking, contact or30FPS
acceptance is claimed. Captured surface geometry remains distinct from the
inferred submerged bed and flanks.

## Terminal checkpoint and independent audits

The prior process32728 is terminal: its process handle is absent, final local
step36000 has a complete snapshot, and `completed.json` says completed=true.
No process exit code was captured, so exit0 is not claimed. Both7150 and7200
states pass the full state audit and all86,720 exactly dry artificial-bank
checks. The7200 state contains5,382,400 original cells, maximum depth3.809049499m,
maximum speed5.340487366m/s and volume2,672,717.720963m3. Maximum step volume
residual is1.424946e-8m3. Outflow111.286852m3/s still exceeds45.306955m3/s inflow:
**not settled**, not a promoted playable-state replacement.

State/bank reports: `tmp/control-ablation-{7150,7200}s-{state,banks}-v1-20260918.json`.
Final depth SHA256:
`331bf70291a5ba83b487a1bdf397a689ed2437509d11a31940e1331efd6d19ef`.

## Stronger continuation checks

The restart auditor previously compared grid, roughness and boundaries but did
not independently compare all retained physical settings. It now compares the
entire retained scenario and manifest, excluding only explicit regenerated
restart bookkeeping. Timestep, discharge, datum, raft parameters, scenario
identity, unknown future solver fields and metadata identity cannot silently
change. Retained feature/probe files must also be byte-identical. Existing
native h/u/v, clock, source-file, geometry and volume checks remain unchanged.
False cold-start/settled/integrated claims reject. No acceptance gate is weakened.

34 tests PASS, including28 new mutation/retention controls and six existing
metadata tests. Report `tmp/restart-retained-inputs-v1-20260918.xml`, SHA256
`34ac5411a5dc27771351429b713ade529b50e8f8d7f30d4e7d539902eca15654`.
The strengthened full previous5400 restart audit also passes:
`tmp/control-ablation-5400s-strict-restart-v1-20260918.json`, SHA256
`d368546440e1ff2179372828651aa48a4786d3ac2d6f39363be2d67678124314`.

## New exact continuation

Input `tmp/control-ablation-7200to9000s-input-v1-20260918/manifest.json`, SHA256
`1c0ac9e876bf0c9b6094b91138a64f84d529234aaa7f834885fce1e113408189`.
No added context, cells or water. The native reload preserves all5,382,400
original h/u/v values bit-exactly and the exact checkpoint clock. Independent
summation differs by4.656613e-10m3, below the unchanged1e-6 gate; this is not a
state adjustment. All retained physical inputs/features/probes match.
Report `tmp/control-ablation-7200s-strict-restart-v1-20260918.json`, SHA256
`ea0694623ee210e9960b990e21c52ca69553597c12e83d84c09438727ff08231`.

Live process at this review: PID28776, startUTC
`2026-09-18T04:30:27.5746990Z`, unified session93831. Executable:
`tmp/solver-worker-limit-v1-20260917/raftsim_cartesian_cook.exe`, SHA256
`458a1fcd3f2f12391012032398d29a4b2eadb792df2e9ee09b88dff263abc8e4`.
Output: `tmp/control-ablation-7200to9000s-workers8-v1-20260918`.
It runs36000 unchanged0.05-second steps, snapshots every1000 steps, eight workers.
Revalidate the exact process identity before control; this record alone is not
proof of future liveness. Next7250/local1000 needs its completion marker and
BOTH state and artificial-bank audits. Do not restart on observation timeout.

The independent original-front pressure verifier also completed exit0:11
supported cases, two preserved unsupported records,369 original fields and631
hashes checked. See [its evidence and limits](original-front-pressure-variation.md).
Neither this derivative verification nor hydraulic settling implements the
missing nonlinear force/wetting/open-boundary law. Nonlinear runtime stays OFF.
South Fork visual/physical and30FPS gates, then Colorado, Pacuare, Futaleufu,
Chilko/Zambezi, crew, normalization,13 outstanding regressions and release remain open.
