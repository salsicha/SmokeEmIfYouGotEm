# South Fork: reject a raw density cutoff as the shared water surface

2026-09-11. The preceding user-status turn was informational (no implementation
progress). This continuation evaluates a concrete interface candidate against
the actual prepared and evolved South Fork river, rather than installing an
untested phase cutoff. No native shader, scene asset, acceptance gate, or saved
map changed. South Fork and every later queued scene remain incomplete.

## What was implemented and executed

`physics/scripts/liquid_volume_interface.py` implements a centred tent deposit
of fixed nominal particle volumes, trilinear sampling, and the candidate
implicit field `phi = 0.5 - deposited_volume / cell_volume`. Phi is explicitly
**not signed distance**. Off-grid mass is not renormalized, missing sample
stencils are reported, and there is no arbitrary occupancy repair. Seven tests
cover conservation, anisotropic metric, interpolation, domain edges, invalid
inputs, resolved bulk, and loss of a thin sheet.

`physics/scripts/diagnose_liquid_volume_interface.py` uses all twelve regions
of the successful `liquid-native-reservoir-metric-sor` capture. It checks the
versioned dataset hashes, every original birth identity/position against the
prepared source, common grid metric, paired pressure stage, consecutive compact
transactions and native final counts. SHA256s bind every consumed particle,
total and boundary binary. It rejects the longer trajectory's failed compact
transaction at step 641 rather than treating its later snapshot as valid flow.

The initial field is deposited on ONE parent lattice (498 x 170 x 24 including
XY halos), avoiding artificial internal regional surfaces. The evolved field
uses the ACTUAL native shared P2G totals and current particles at step 600;
final stop-time fields are not substituted for paired data. Classification
counts exclude duplicate XY halos. Both point-sampling sets have complete
stencils. Exact triangle terrain sampling supplies the clearance comparison;
it preserves the existing distinction between captured rock returns and an
inferred, uncalibrated submerged bed.

Authoritative result: [verified diagnosis](liquid-volume-interface-verified-diagnosis.json).
The earlier `liquid-volume-interface-diagnosis.json` and
`liquid-volume-interface-terrain-diagnosis.json` retain intermediate results;
use the verified result, which also validates all 598 compact transactions.

## Actual result

| Quantity | Prepared original river | Native step 600 |
| --- | ---: | ---: |
| Particles tested | 729,724 | 701,417 |
| Particles outside candidate zero set | 9,025 | 11,639 |
| Outside fraction | 1.237% | 1.659% |
| Particle-occupied XY columns with no wet candidate cell centre | 1,427 | 950 |
| Maximum deposited-volume / cell-volume ratio | 1.231 | 12.570 |

Of the excluded original particles, 5,426 are within 25 cm of the exact terrain
surface; another 2,797 are more than 50 cm above it. The missing coverage is not
only a river-exterior stencil issue or only terrain proximity. Original
particles represent the prepared wet volume, not newly generated spray. During
motion, some subgrid droplets could appropriately be treated separately, but
this diagnostic does not classify them as spray to excuse missing water.

The initial deposit conserves all 15,202.583786 m³ of nominal particle volume
when including the grid's outer halos. Nevertheless, conservation of a smooth
density kernel does not guarantee containment or the correct zero-set volume.
Cell-centre classification yields 15,268.0 m³ initially and 14,147.25 m³ at step
600. These are **not integrated surface volumes**, and their differences must
not be presented as a measured geometric volume error or an acceptance bound.

At step 600, the cutoff would change 37,891 current pressure-fluid cells to air.
About 493.3053 m³ of kernel weight is assigned to grid centres classified solid.
This is interpolation support crossing the wall, **not particles penetrating
the terrain**: all 701,417 sampled particle centres remain above the registered
triangle bed. A simple phase threshold loses this distinction.

## Consequence for implementation

Do not wire `Total.w > 0.5 * cellVolume` into native support/pressure and declare
the surface fixed. Do not fix the missing coverage by tuning a global threshold
to the desired image or treating deposited density as a metric distance.

The next implementation should retain an explicit moving liquid/air interface,
initialized from the actual wet-stage/terrain intersection, advected by the
same native velocity, and corrected using particle information. Pressure needs
subcell distances to that interface, while rendering must resolve the same
interface near crests and banks; unresolved droplets need an explicit separate
classification, not silent disappearance. The existing CPU ghost-fluid
operator remains a reference for consistent distance weights in BOTH the
pressure solve and velocity correction. Native installation, terrain contact,
source/backflow treatment, volume drift, animation and playable FPS still need
verification. No new performance claim follows from this CPU diagnostic.

Particle-based surface literature also distinguishes kernel density from
surface reconstruction; see the discussion of weighted-centre reconstruction
in [Zhu's thesis](https://www.cs.ubc.ca/~rbridson/docs/yzhu_msc.pdf).
That is background, not evidence that a particular reconstruction works here.

## Verification and state

- All 390 Python liquid tests pass (383 previous + 7 new).
- Actual whole-river diagnosis completes with all 598 compact commits valid.
- The failed 30-second capture is rejected at its failed transaction, step 641.
- No Unreal/build jobs were launched; process inspection found none running.
- Previous native build/19-engine-test evidence is unchanged, not rerun here.
- No production promotion, map edit, visual acceptance, final commit, or push.
