# Exact dry kinematics and connected energy qualification

September 14, 2026. Research progress only. No native, playable, terrain,
material, source, boundary, pressure-gate or FPS-target changes.
Previous goal turn: PROGRESS (connected scalar correction, actual-source
qualification, and retained original failures). This turn rules out an
arithmetic-only fix and checks the connected proposal's remaining energy issue.

## Dry-cell error survives independent rational evaluation

New `physics/scripts/audit_exact_dry_kinematics.py` independently reconstructs
the original MC face geometry using ordered rational (value, right derivative)
pairs and directly evaluates `A=r^2*(3-2*r)`. It does not call the production
MC, hydrostatic-face or cut-pressure evaluator. The comparison target is the
original geometry action, including its directional entering limit. Original
represented h/bed arrays and the mass/momentum ray remain unchanged.

At dry core cell [3,0] of the original variable-bed fixture:

| Probe | Independent D | D squared difference from limit |
| --- | ---: | ---: |
| Analytic entering limit | 1.25 | 0 |
| 2^-8, 2^-16, 2^-24 | 3.75 | 12.5 |
| 2^-48 | 3.742828369140625 | 12.44626420084387 |
| 2^-56, 2^-64 | 1.25 | 0 |

Original and independent D actions agree to at most1.776357e-15 over every
cell at every probe. The dry-cell failure therefore is not removed by exact
arithmetic. Smaller probes reaching the limit do not waive the original gate.

At the incident x face [3,0] -> [3,1], the exact represented reconstructed
bed jump is1/72057594037927936m (2^-56m). Its rate is exactly zero; entering
height rate is1/8. Thus the tiny dry-side column is blocked below ray parameter
2^-53, whereas at the original2^-24 probe it is essentially open. The incident
y faces also retain their represented gaps. These exact values are recorded,
not snapped to an ideal affine bed or assigned a tolerance. The pressure
transfer's dependence on the joint gap/depth ratio is the issue.

Three oracle tests pass: independently known flat affine divergence, rational
MC directional ties, unchanged input arrays and reproduction of the retained
defect. Passing a reproduction test does not make the modeled defect acceptable.
Report: `tmp/south-fork-exact-dry-kinematics-v1-20260914.json`.

## Connected derivative does not supply the missing energy closure

`periodic_connected_scalar_reference.py` supplies exact periodic copies ONLY
for explicitly closed periodic, fully positive controls. It rejects open
boundaries and dry inputs. No such artificial halo is supplied to South Fork.
Original pressure D/E, adjoints, FV rates, both rational poles and residual
gates remain unchanged. Constant-null, cyclic registration and refinement
tests pass, as does restoration after an intentional exception.

`audit_connected_closed_energy.py` reuses the original eight smooth profiles
at64 and128 cells. The candidate rational energy remains the inverse frozen
linear-response metric extended nonlinearly, not an established invariant.

| Resolution | Original rational positive rates | Connected rational positive rates | SGN positive rates, both |
| --- | ---: | ---: | ---: |
| 64 | 4/8 | 4/8 | 0/8 |
| 128 | 5/8 | 5/8 | 0/8 |

All64 full FV/pressure evaluations pass their original pressure gates.
Connected seed2205 rational rate per transverse width is+0.06048061470067623
at64 cells and+0.09415229447914264 at128. These increasing positive rates do
not support assuming that the scalar correction resolves nonlinear energy.
Negative SGN samples are not a stability proof or permission to substitute SGN
for the requested two-pole model.

An independent state-space check reuses the ORIGINAL finite-difference routine,
changing only its explicit scalar context and truthfully relabeling the result.
Actual full FV plus connected two-pole directions for seeds2204/2205 at64
remain positive at all three original probes. At epsilon1e-5, absolute rate
errors are3.16866528675408e-11 and1.2717828526409569e-11. This verifies the
positive rates, not a new model invariant or proof that no other energy exists.

Reports:

- `tmp/south-fork-connected-closed-energy-64-v1-20260914.json`
- `tmp/south-fork-connected-closed-energy-128-v1-20260914.json`
- `tmp/south-fork-connected-energy-direction-v1-20260914.json`
- `tmp/exact-dry-periodic-scalar-controls-v1-20260914.xml`:5 PASS.

## Consequence for implementation

Do not promote the connected scalar proposal or launch another full-history
variant on the assumption that the physical-force ray pass fixes everything.
The earlier combined40PASS/8FAIL remains unchanged; no assertions are edited,
skipped or marked expected failures. Original histories continue unchanged.
The next formulation work must address joint cut/kinematic consistency and
the actual nonlinear two-pole energy/flux relation. Increasing precision,
snapping source beds, choosing only smaller probes, or treating the frozen
linear SPD metric as a nonlinear guarantee would not resolve these findings.

This is not a claim that the existing game is stable or realistic, nor that
no satisfactory formulation exists. Native integration still requires the
original full moving-window history, physical waves/contact/froth, actual
rendered comparison and measured performance.

## Newly complete full-river checkpoint

Original cook83142 reaches complete8900s/local18000. Both independent audits
pass:5,382,400 finite cells,86,720 exactly dry artificial-bank cells,1084 bank
faces,2276 directed shared faces. Max depth3.77731463069403m, max speed
6.220746796777652m/s, volume2572974.1440217616m3; snapshot/driver difference
-9.313226e-10m3 and maximum step residual1.441914e-8m3.
Outflow102.204022764m3/s versus inflow45.306954547m3/s remains UNSETTLED.
Reports `tmp/south-fork-expanded-8900s-{state,banks}-v1-20260914.json`.
Depth SHA `1c1235b22a4a3f944e4af17663c8742383f93d803d9c394ac231b778f40f2437`.
Next COMPLETE9000/local20000 requires BOTH audits.

Both replay implementation guards were checked:417/422 files, zero changes.
All five original jobs were directly confirmed live. No restart, suspension,
source reset, native/gameplay promotion, new FPS claim or final commit.
Desktop remains30FPS/p9533.333ms, physics120Hz. Remaining South Fork visual
and terrain work, later rivers, crew, normalization, release and full goal OPEN.
