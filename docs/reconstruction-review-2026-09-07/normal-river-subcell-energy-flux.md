# Joint exact-terrain mass and hydrostatic pressure — September 14

This turn advances the hydraulic coupling needed to use captured terrain in the
water solver. It does **not** deliver a new playable water surface. The preceding
goal turn rejected a lookup optimization after actual paired measurements; it
was evidence-based progress, not a delivered frame-rate improvement. No more
hash/batch variants were attempted here.

## Why mass and pressure must change together

The old donor mass rate cannot conserve nonbreaking energy with any conservative
momentum-only repair in the constant-velocity control. Instead, the new
`physics/scripts/subcell_energy_flux.py` pairs mass and pressure at each exact
shared terrain face. This is the nondispersive base, not the full two-pole model.

Energy-consistent flux/source pairing for shallow water has an established
precedent in [Fjordholm, Mishra and Tadmor (2011)](https://math.umd.edu/~tadmor/pub/TV%2Bentropy/Fjordholm_Mishra_Tadmor_JCP2011.pdf).
The following pressure-secant construction over the repository's original
piecewise-linear terrain sections is the derivation implemented and tested here;
the cited paper is not evidence that this particular subcell implementation or
its wet-front/time integration is qualified.

For cell volume V, integrated momentum P, uniform cell velocity u=P/V and stage
eta, the exact nondispersive energy gradients are:

```text
E_P = u
E_V = g eta - |u|^2/2
```

Define each shared face's wet cross-sectional area A(eta) and hydrostatic force
J(eta) directly from its original terrain segments:

```text
A(eta) = integral max(eta-bed,0) ds
J(eta) = g/2 integral max(eta-bed,0)^2 ds
A* = (J_R-J_L)/(g(eta_R-eta_L))
F_volume = mean(u_normal) A*
F_momentum = mean(u) F_volume + normal mean(J)
```

At equal stages, A* is the derivative J'/g=A, with no small-difference threshold.
The implementation does **not** subtract nearly equal pressures. It splits each
original segment at both wet levels and integrates the pressure divided
difference directly: mean depth on both-wet pieces, squared wet depth divided
by twice the stage difference on singly-wet pieces. Datum and local height remain
separate; thin representable water is not replaced by a minimum depth.

The independent exact cell bed force is retained. At constant cell stage,
`-g integral h grad(bed) dA = integral J normal ds` by the divergence theorem.
Consequently, the combined work of a shared face and its two bed-force terms is

```text
g (eta_R-eta_L) F_volume - mean(u_normal) (J_R-J_L) = 0.
```

Both owners use one flux with opposite signs. No global momentum/energy
projection, post-update rescale, terrain adjustment or pressure-residual bed
force is used to obtain this cancellation.

## Dissipation is explicit and separate

An optional shared dissipative flux subtracts `s/2 * [A, A*u]`. Its predicted
face energy rate is

```text
-s/2 * (g (eta_R-eta_L)(A_R-A_L) + mean(A)|u_R-u_L|^2) <= 0.
```

The signal bound includes twice the magnitude of mean normal velocity; this
prevents the mass flux from donating out of an exactly dry face. Reflecting
boundaries account for only the physical half of their mirrored face work.
This is an instantaneous identity, **not** a positivity timestep, a bounded
momentum update, a breaking detector, a breaking closure or an implicit solver.

A new regression deliberately demonstrates that the nondissipative central
flux alone can donate from a dry cell. Its passing energy identity therefore
does not authorize wet-front evolution. Existing thin-cell timestep, finite-step
energy and two-pole requirements remain separate and unchanged.

## Independent component checks

Ten new tests cover split Gaussian quadrature on original segments, equal/reversed
stages, distinct datums, flat and partially wet films down to 1e-150 m, 320 random
face identities in both axes and both modes, no dry-face donation in dissipative
mode, the central-flux dry-front obstruction, constant-velocity mass/energy,
rough partially wet lake/energy balance, smooth-rate refinement and invalid-state
rejection without mutation. The 16/32/64-cell flat smooth control shows second-
order consistency of the nondispersive rates; this is not two-pole dispersion or
terrain/wet-front refinement acceptance.

The full exact-terrain/source component command passes **55 tests**, 4.186 s:

```text
python -m unittest test_subcell_energy_flux test_triangle_cell_storage test_triangle_face_section test_subcell_geometry_patch test_subcell_implicit_transport test_subcell_mechanical_energy test_subcell_drain_event test_subcell_relative_stage test_captured_rock_vertex_registration test_carrier_source_epochs
```

The original two-pole stress/constant-velocity controls were also rerun, unchanged:
**14 PASS / 4 FAIL** in 2.36 s. All four required nonbreaking energy tests still
fail at absolute rates 13.48875 or 15.328125, not the required <1e-10. Report:
`tmp/subcell-energy-existing-two-pole-v1-20260914.xml`. This targeted rerun does
not supersede the broader historical 89 PASS / 29 FAIL control set.

## Actual captured terrain and source state

`physics/scripts/audit_south_fork_subcell_energy_flux.py` checks the same original
256-cell footprint and its 544 shared/wall faces, with stored lattice origin
`[-5438.999999998952,3593]` in the full-reach field frame. Input volume and momentum
come unchanged from the 600-second atlas; total initial volume is
540.7407962754788 m3. Captured-triangle/source-center bed discrepancy is
1.4210854715202e-14 m. This preserves the atlas's sub-nanometre origin offset
rather than selecting geometry on a rounded replacement grid.

All eight real-geometry lake-at-rest controls pass: four stages, both modes,
including dry cells. Worst momentum residual is 7.1054273576e-14; worst volume
rate is 2.4719256781e-14. On the actual initial state:

| Instantaneous quantity | Nondissipative | Dissipative |
| --- | ---: | ---: |
| Total volume rate, m3/s | 0 | 1.421085e-14 |
| Measured base energy rate | -1.136868e-13 | -4084.934667580508 |
| Predicted rate | 0 | -4084.934667580510 |
| Absolute identity residual | 1.136868e-13 | 2.273737e-12 |

Unit density is omitted in these energy units. These reflecting walls are a
closed control, not the river's real boundary conditions. No evolved state,
new settling claim or rapid appearance follows from an instantaneous rate.
Source hashes are checked before/after the audit, including all loaded atlas
arrays. Process completed exit 0. Report:
`tmp/south-fork-subcell-energy-flux-v1-20260914.json`, SHA256
`8bc85f7b8f42b3c992f6a60104cd7a71f3711caa22f70bfc9839c3469aa8ad0b`.

## Next required integration, not scene acceptance

This supplies a joint base flux that removes the identified mass-only energy
obstruction on exact terrain. Next derive compatible auxiliary/two-pole work
with this mass choice and qualify finite-step energy, positivity/momentum at
moving wet fronts, internal-basin connectivity, open boundaries and refinement.
Then native integration must use the same geometry and rendered/contact surface
and satisfy its measured budget. Do not promote the old dissipative frozen-
donor time update or substitute this base for the required full model.

No Unreal code, saved map, source geometry, collision, material, presentation
quality or scenario-menu setting changed in this turn. No new engine-motion or
30 FPS acceptance is claimed. South Fork's latest actual visual review remains
failed and latest ordinary p95 is 64.9716 ms. Colorado, Pacuare, Futaleufu in
order, remaining Chilko/Zambezi water, crew, normalization/regressions and release
qualification remain open. Troublemaker stays within South Fork, not a menu
scenario. The full goal remains active.
