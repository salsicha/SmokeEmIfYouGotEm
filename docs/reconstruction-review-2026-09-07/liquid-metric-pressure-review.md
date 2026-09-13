# South Fork: metric-aware pressure relaxation

2026-09-11. The previous goal turn added and verified paired native pressure
diagnostics. This turn changes the actual regional pressure program and measures
its result. South Fork and the rest of the reconstruction queue remain incomplete.

## Corrected numerical mismatch

The inherited Niagara estimate uses an isotropic nearest-neighbor box:
rho = mean(cos(pi/Naxis)), omega = 2/(1+sqrt(1-rho²)). The installed D M G
operator instead samples pressure at +/-2 cells with unequal XYZ spacing.
Using the inherited estimate also gave different factors at regional cuts.

`FLayout::PressureOmega` now uses the parent grid's eight parity subgrids:
Naxis = ceil(parent cells/2), weights = 1/haxis², and the weighted box estimate
rho = sum(weights*cos(pi/(Naxis+1)))/sum(weights). The common factor is embedded
in the regional GPU pressure program. No extra iterations, dispatches, water
damping, pressure cap, boundary relaxation, or particle deletion was added.

For the current 494x166x24 parent with 50x50x33.3333 cm spacing, the new factor
is 1.7010257300647977. The inherited region-0 estimate was about 1.850285.
This is a rectangular-box **estimate**, not the exact spectrum of the irregular
river or a claim that fixed iterations always converge. Actual residuals remain
required. See [Netlib's SOR discussion](https://netlib.org/linalg/html_templates/node16.html).

Independent Python tests assemble a wide-stencil Jacobi matrix and check its
numerical eigenvalues against the estimate. Native tests verify shared parent
relaxation across actual cuts and the compiled GPU marker. All 383 Python
liquid tests and all 19 engine regressions pass cleanly. Build 89097 succeeded;
engine regression session 13580 terminated with exit 0.

## Actual full-river result at the same 40 iterations

Capture `liquid-native-reservoir-metric-sor`: native session 5522 terminated with
exit 0. All twelve owners record the same new factor and same-step native
input/output pressure fields. The original geometry, seeds, boundary policies,
inlet source, and requested timestep are unchanged.

| Actual native quantity at step 600 | Previous capture | Corrected estimate |
| --- | ---: | ---: |
| Input divergence RMS, /s | 0.15663394 | 0.15456869 |
| Post-pressure divergence RMS, /s | 0.01865356 | 0.00043467 |
| Output/input divergence RMS | 11.91% | 0.281% |
| Storage change over 598 valid commits, m³ | -593.39583 | -590.5 |

The post-pressure divergence is about 43 times smaller without increasing the
iteration count. These are separate full native trajectories, not bit-identical
same-state A/B inputs. The major drainage discrepancy is largely unchanged,
so convergence alone did not explain it. No playable FPS claim follows from
these diagnostic runs or their readback-heavy wall times.

### Explicit coordinate-reference correction in the dense audit

The first independent routing audit rejected one of 701417 particles. Retained
`route-disagreement.json` identifies birth owner 7 / sequence 147725, currently
stored in owner 11, at [-8605.787109375,-874.3470458984375,467.80419921875] cm.
The original survey-double frame assigns owner 7. Reconstructing the declared
native float-upload frame independently from prepared geometry gives local
Y=6500.000127091698 cm, rounding to 6500 cm, and assigns owner 11 exactly as the
GPU does. This is an **internal storage cut**, not a terrain/collision change.

The dense auditor now verifies storage under the explicitly declared
`double-float-demote-v1` contract and retains the survey-double disagreement
count separately. It does not use GPU destinations to create expected owners,
does not introduce a distance tolerance, and rejects unknown/null contracts.
The original physical survey exterior check is retained: float-frame rounding
cannot admit a point outside the original physical extent. Exact payload,
identity, routing-count, approved-exit and neighbor checks remain unchanged.
Legacy captures without the descriptor retain their previous reference.

After that reference correction, native transfer audit 29115 passes all 701417
particles with zero reduction mismatches. `native-dense-audit.json` explicitly
reports one survey/internal-storage discrepancy and preserved physical outer
bounds. Accounting is 729724 original + 22533 births - 50840 exits = 701417.
This does not certify exact per-exit trajectories or physically correct flow.

## Longer run remains rejected

`liquid-native-reservoir-metric-sor-30s`, native session 97040, terminated with
exit 0 after collecting 1800 requested steps. The first failed commit is 641,
not a successful thirty-second flow. Only 639 commits through step 640 are
valid: 729724 + 24038 births - 53728 exits = 700034 survivors; storage change
-618.54167 m³ over 10.65 requested seconds. Do not audit the final post-failure
particle packet as a successful conserved run.

The retained first rejection is again birth owner 4 / sequence 97114, west
face row 71, reason 8 (non-outgoing face). Actual local normal position crosses
0.022796923 to -0.404965997 cm. Hit elevation is about 899.627 cm, above the
883.149719 cm prescribed stage and 871.526127 cm exact bed. Both captured-frame
and survey-frame calculations confirm an actual outward crossing, not the
earlier arithmetic false exit. The original rejection policy remains intact.

## Next

Keep the metric-aware pressure correction. Reconstruct a current liquid/air
interface consistent with the moving particles, terrain and external reservoir,
and use it for the pressure boundary and visible surface. The existing exact
interface CPU regression is not a live surface implementation. Signed reservoir
backflow and storage/discharge still need a physically consistent treatment.
Do not merely permit unexplained particle loss or reclassify failed late state
as accepted. Then verify the actual surface, foam, raft, shoreline and FPS.

All build, native, audit and engine test sessions are terminal. Saved review map
SHA256 remains 36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96.
No map promotion, beauty capture, completed scene, commit or push in this pass.
