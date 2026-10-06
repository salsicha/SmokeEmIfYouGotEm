# Physical-coordinate auxiliary transport — September 28 UTC

Physics implementation progress, not a new visible water improvement. The
normal rebuilt game remains v21; its two rapid timing gates and breaking/foam
realism remain failed. Nonlinear and isolated mean-strain gameplay stay OFF.

## Direct coupling, not an energy-residual force

The preceding prescribed auxiliary advection supplies separate mass/factor
transport actions. The new `subcell_prescribed_physical_transport.py` maps
their ORIGINAL two-pole weighted contributions back to the coordinates
conjugate to physical momentum, retaining one prescribed flux coordinate per
original exterior face. No fitted inverse poles or new dispersion constants.

At frozen geometry, y=(v,q), where v is canonical velocity, not layer velocity.
For each original pole with length lambda and weight w:

    H = M + lambda*C
    H*a = M*v - lambda*l(q)
    P*y = (a,q)
    action = c*L_mass*y + sum w*P^T*(L_mass + lambda*L_factor)*P*y

The transpose is computed directly: solve H*r=f_a, then return M*r in the
velocity coordinates and f_q-lambda*l^T*r in the exterior coordinates. The
lift and its transpose use the original local Gram forms and augmented
divergence; no global work discrepancy is redistributed into a force.
The physical-momentum RHS contribution has the MINUS sign of this spatial
action. Its canonical-velocity work plus explicit flux-coordinate work equals
the signed outward transport of the existing positive physical kinetic energy.
Incoming flux is not clipped. Dry owners are removed without discarding
positive subfloat water or flooring its inverse mass.

The time-ledger check uses the original prescribed q(t), volumes and Gram
geometry. It differentiates E(p,t) along this momentum contribution and keeps
the uncanceled geometry/port power:

    E_t + outward_kinetic_flux = geometry_time_work + flux_coordinate_work

The right side is generally NONZERO. It is reported, not canceled by a
manufactured force. It is not automatically the physical pressure-work flux.
Gravity/potential energy, the complete conservative momentum law, incoming/
radiating boundary states, moving-map connections, interacting wet fronts,
time integration, breaking dissipation and native runtime integration remain
required. This does not establish a complete local total-energy ledger or
permission to enable the rejected solver.

The [SGN structure-preserving reference](https://arxiv.org/abs/2408.02665v4)
discusses preserving mass and energy together; this frozen-fan two-pole
pullback is our component construction, not a claim to implement that paper's
complete discretization. No paper/video assets were downloaded or shipped.

## Tests and independent checks

Initial7 tests pass24.84 s. Expanded54 tests pass97.04 s, zero errors/failures/
skips, across the new8 cases and existing prescribed auxiliary advection,
connections, trace and affine moving-pressure modules. Six separate provenance
rejection tests pass1.07 s. Coverage includes:

- Original physical kinetic energy and both original pole states against the
  independent affine pressure metric; physical/canonical momentum roundtrip.
- Exact transpose work with arbitrary velocity AND exterior flux probes.
- Independent pointwise face quadrature of weighted physical kinetic flux,
  cross-state Green identity, signed incoming/outgoing contributions.
- Winding/exterior subdivision invariance, dry removal, positive subfloat
  water, stationary zero mode, malformed/nonfinite input rejection.
- Fresh-time physical-momentum energy differences converge to the analytic
  derivative while explicitly retaining nonzero remaining geometry/port power.

Reports: `tmp/prescribed-physical-transport-v1-tests-20260928.xml`,
`tmp/prescribed-physical-transport-v2-tests-20260928.xml`, and
`tmp/prescribed-physical-source-provenance-tests-20260928.xml`.
Implementation SHA256:259ceaeee7feca4d98618305bd9757e0f8db57e7618a7870e407a169db8f88b7.
Tests SHA256:95ca71b6e46c24b7d7132075fdf49f040dd60dc8ce34f9ad1a144f0c3c0a3b49.
Expanded report SHA256:5bfbb603f3dfbe7fe533f1dfc96c7c2449fa30d0933bb4e751526624f530b5ab.

## Original-source replay: terminal completion and independent reload

The first replay exited1 before any case on a correctly rejected changed
historical audit tool. Its receipt/log/error are retained under
`tmp/prescribed-physical-source-v1-*-20260928.*`. No captured inputs changed.
Resolved18 changed, UNUSED Python tools against exact full Git revisions;
their original report hashes are preserved, their current hashes also recorded.
The shared verifier rejects historical exceptions for any imported code or
captured data. All630 current protected entries were checked. Resolution:
`tmp/prescribed-physical-source-historical-tools-20260928.json`, SHA256
88cb2e0a8fb16721a4b3d73e3dd094e7f8396fc43811377bf67dace932b949ad.

Corrected source replay33152 completed exit0 at2026-09-28T12:03:19.7417947Z
(start09:06:42.7195829Z). Independent saved-report reload16732 also completed
exit0. No source solves were repeated. The reload verified631 current protected
hashes,22 implementation hashes and18 historical tools, plus the exact saved
kinetic ledgers. All13 original records remain;11 supported records were tested
and unsupported2/7 remain unchanged and untested. All11 tested records retain
NONZERO uncanceled geometry/port power. This is a component validation only.

- Recipe: `tmp/replay-prescribed-physical-source-v2-20260928.ps1`.
- Receipt: `tmp/prescribed-physical-source-v2-process-20260928.json`.
- Log/error: `tmp/prescribed-physical-source-v2-20260928.{log,err}`.
- Complete report: `tmp/south-fork-prescribed-physical-transport-v2-20260928.json`.
- Report SHA256:f7167b02639c3c5c46916f71dcf00d98ad00e0568359ef008aae0a2ea10b2854.
- Independent verifier: `tmp/verify-prescribed-physical-reload-20260928.py`.
- Reload receipt: `tmp/prescribed-physical-source-v2-reloaded-20260928.json`.
- The original process receipt's `source_replay_complete_reload_pending` phase
  is its preserved terminal snapshot; the separate successful reload receipt
  supersedes that pending status without overwriting the historical receipt.
- Audit entry: `unreal/Plugins/SEIYGECore/python/scripts/audit_south_fork_prescribed_physical_transport.py`.
- Audit SHA256:3286882a4b2aa76c7f64b46a61945068553ca1dde6626996287ecc4ce3d689ec.

The original physical momentum is mapped to canonical velocity,
not silently substituted by layer velocity; original nondispersive rates are
retained as probes, NOT reused as a qualified dispersive force law. Exact saved
interior plus port work equals outward kinetic flux; both original poles and
the kinetic chain rule are retained. Full force, natural boundaries and
gameplay acceptance remain false.

The source workload no longer blocks isolated game timing. Next finish
the remaining conservative pressure/bed/boundary coupling. Keep actual normal
scene delivery incremental, but do not enable an incomplete solver or use
stronger foam/noise to hide missing physical breaking. South Fork and the full
river/crew/normalization/regression/release queue remain unfinished. No push.
