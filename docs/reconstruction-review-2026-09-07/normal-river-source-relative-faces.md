# Source-relative faces and pressure columns

September 14, 2026. Further integration of exact source geometry into existing
physical kernels; **not native water, full evolving physics or scene acceptance**.

The previous source representation retained exact polygons and positive areas,
but its numerical storage used a local zero datum. Passing that storage to an
old face or connectivity consumer as if zero were its actual elevation gives
the wrong water support. Reconstructing global float coordinates first also
loses positive face intervals and differences between nearby exact datums.

## Explicit relative face interface

`SourceFaceSection` retains rational tangent/elevation endpoints, exact source
level differences and positive interval lengths. It verifies neighboring
source heights at their combined exact knots, without a welding tolerance.
Lengths and depths are formed before conversion to numerical kernel inputs.
The float projection is for inspection, not the authoritative geometry.

The existing hydrostatic moments, Rusanov donor flux, paired pressure-secant
flux and dry-front flux now consume a face depth-interval interface. The same
kernel implementations can therefore evaluate original source-relative faces
without subtracting rounded absolute heights. Surface differences involving
exact datums preserve those datum differences before numerical conversion.
Both XY momentum components and the original physical flux formulas remain.

Harmonic pressure columns and their analytic stage derivatives use the same
interface. Piecewise exact source sections are supported as well as the old
single-segment arrays. The original pressure poles, solver iteration limits,
residual checks and physical energy requirements are not changed.

Source-topology connectivity now reads an exact storage's retained source datum
instead of treating its local numerical zero as global elevation. Original
source vertex IDs and positive shared wet-edge predicates still determine
connectivity; there is no proximity welding or point-contact bridge.

## Independent requirements

Controls include positive widths that collapse in a float projection, distinct
datums with identical float elevations, a face that must remain dry despite a
rounded projection indicating water, translated-frame flux equivalence,
dry-front energy and direct force, exact source-edge agreement, source
connectivity, partial-lake bed/pressure balance, and harmonic column derivatives.
These are physical/representation controls, not visual realism measurements.

Two further tests first failed: nonzero depths below represented range were
silently classified as zero, and the inherited bed query converted exact
tangent coordinates to floats too early. Neither behavior is an acceptable
fallback for exact geometry.
The final implementation rejects a nonzero depth that would convert to zero
(on either the wet or dry side) and rejects unrepresentable positive bed spans.
Exact tangent queries interpolate the retained original segment before the
final elevation conversion. All three initially failing controls now pass.

The actual first audit also recovered the same 258 wet components over 255
positive cells, verified all 480 neighboring Cartesian faces exactly, and
evaluated 458 positive shared harmonic columns. Original source-frame boundary
moments agree with independent rational line integrals within 2.52e-16 scaled
error. Per-cell partial-lake bed/pressure balance has maximum residual
2.13163e-14. These are original-state controls, not 480 independent accepted
pressure graph connections or an evolved river.

Final actual run completed with exit 1 (the retained history failure):

```powershell
python -B physics/scripts/audit_south_fork_subcell_kinetic_geometry.py --atlas tmp/south-fork-runtime-atlas-600s-v1-20260912/atlas/manifest.json --report tmp/south-fork-source-relative-faces-v2-20260914.json --source-representation --pool-history-steps 20 --pool-history-scheme coupled-donor
```

Report SHA256:
`725369fc4b024d7a9d68809e309af840c69507e3cc0f5d2dc4dd3c8ac917c742`.
All 38 report source hashes match the final code and data. The final exact-frame
controls reproduce the figures above. The existing static 258-pool pressure
controls pass with both original poles and 40 iterations; that graph still
uses the old storage representation, not the new source-relative face objects.

The entire serialized successive-state history is identical to the preceding
matched-front-pressure history. Seventeen candidate steps reach 0.34 seconds
and 420 regions. Step 18 rejects three zero solved volumes; one of those regions
has nonzero incoming transfer. No timestep reduction, tiny-region deletion or
energy adjustment is applied. The audit correctly retains overall acceptance
as false. This rerun is a non-regression check, not new finite-time acceptance.

## Remaining integration scope

Final focused selection: **211 passed, 1 failed**; the existing old
storage/face equality test is unchanged and still fails.
`tmp/subcell-source-relative-faces-tests-v2-20260914.xml` (14.304 seconds in XML).
Retained original energy selection: **25 passed, 12 failed**.
`tmp/subcell-source-relative-faces-retained-v1-20260914.xml` (7.953 seconds in XML).
No skip, expected-failure marker, tolerance change or replacement requirement
was used. All 464 protected source/capture/map/profile/actor hashes were
rechecked unchanged. There are no native/map/state or rendering changes.

The evolving `WetPoolPartition` still builds old float-vertex storage and old
face traces. It has not been relabeled as exact or silently switched. Its
region subset construction, exact datum transfers, internal source-edge
sections, pressure graph traces and one-sided topology events still need
consistent integration. Conservative drying/extinction remains a separate
unmet requirement, including regions with coupled inflow.

This work does not establish the full rational transport/pressure/bed-force
model, qualified finite-time/open-boundary/refinement behavior, or playable
breaking/froth. South Fork visual and 30 FPS validation, subsequent Colorado,
Pacuare and Futaleufu work, Chilko/Zambezi reviews, crew, normalization,
regressions and release checks remain open. Troublemaker remains a rapid in
South Fork, never a standalone menu scenario. Full goal remains active.
