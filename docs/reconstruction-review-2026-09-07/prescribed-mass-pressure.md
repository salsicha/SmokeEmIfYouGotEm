# Conservative prescribed mass/pressure pair - September 28 UTC

Supporting physics progress only. Normal playable v24 is unchanged; no new
engine build, cook, frame-time measurement or visible wave improvement is
claimed here. South Fork remains unfinished. Nonlinear gameplay stays OFF.

## Construction and scope

`physics/scripts/subcell_prescribed_mass_pressure.py` adds
`PrescribedMassPressurePair` without changing the existing source replay's
loaded modules. Pressure-jet velocity divergence is not conservative volume
transport: using it as the mass map fails the original fan's volume rates.

For each shared face, integrated physical momentum p divided by owner volume
V gives layer velocity u. Transport uses the actual depth-column normal dotted
with the mean of the two layer velocities, plus an explicit prescribed profile
lift. The lift is the original exact fan flux minus the mean-velocity flux of
the original integrated momentum. The same signed flux debits one owner and
credits its neighbor. Every original exterior flux coordinate q is retained.
Dry owners keep their original identity, without flooring positive tiny water.

With shared-face matrix R, exterior incidence E and profile outflow ell:

    Vdot = -R p - E q - ell
    p = B v + O q
    A_p = B R^T phi
    A_q = O^T R^T phi + E^T phi
    phi.Vdot + v.A_p + q.A_q + phi.ell = 0

Here v is canonical velocity, not layer velocity. B and O come from the
unchanged original two pressure poles and weights. Their transpose is applied
directly, not fitted from a global energy residual. The potential covector phi
is supplied by the caller: it is NOT asserted to be the full gravity plus
kinetic geometry derivative. Exterior-coordinate and profile-lift work are
generally nonzero and remain explicit.

This is a frozen-geometry, prescribed-profile component, not a complete force
law or total-energy solver. Evolving reconstruction, the full gravity/kinetic
shape derivative, moving metric work, physical momentum/bed ledgers, natural
inlet/outlet states, interacting fronts, finite-time stability, breaking and
native performance remain unresolved. A stationary FLAT lake test does not
establish variable-bed well-balancing. No captured geometry or licensing
classification changes are made by this component.

## Verification

Fifteen new cases pass, including exact original fan volume rates; independent
pointwise edge quadrature; direct face-by-face assembly; original-pole physical
force; velocity AND boundary-coordinate directional derivatives; constant
potential/datum invariance; winding and face subdivision; dry-owner identity;
positive subfloat volume; malformed inputs; six differently oriented/moving
fans; and a stationary flat lake. Negative controls reject pressure-jet mass
transport and omission of the original subcell-profile lift.

The combined run passes **75 tests in 124.78 seconds**, with zero errors,
failures or skips. Ten frozen input hashes were verified again after terminal
completion. Existing pressure/transport and provenance tests are included.

- Recipe: `tmp/verify-prescribed-mass-pressure-v3-20260928.ps1`
- Receipt: `tmp/prescribed-mass-pressure-v3-20260928-process.json`
- Log/XML: `tmp/prescribed-mass-pressure-v3-20260928.{log,xml}`
- Completed: `2026-09-28T11:11:17.8806124Z`, exit code 0.
- Module SHA256: `4362efe6a9240888722f45a79d8e27f43b166f63230f8fa58d0be13f4a0a9a93`
- Test SHA256: `c113a7bffc997b1277284f9fc5b2d26b825c5f07ee32cef0ccfb5e990bb00fa6`

No captured-source acceptance is inferred from these fixtures. The SAME
physical-transport replay Python33152 remains live (index0 checked, index1
started; CPU advancing, no error-log content). Do not duplicate it or edit its
frozen inputs. Its pending terminal/report/hash checks remain prerequisites for
isolated game timing. This new module is not used by that running replay.

Next physics work must derive and test the missing coupled energy/geometry
terms, not enable this incomplete component in gameplay. In parallel with that
dependency, the known three-wet finite-chord shoreline defect remains eligible
for bounded normal-playable work. The 20 FPS and full visual gates stay open.
