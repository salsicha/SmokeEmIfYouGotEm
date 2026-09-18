# Velocity-resolved original-front transport

September 18, 2026. This is a research component, not playable-water acceptance.
The installed water, solver lane default, rendering, contact, geometry gates and
nonlinear runtime switch are unchanged. Nonlinear runtime remains OFF.

## Physical change

`FrontProfileTransport` uses the continuous original fan velocity in the shared
face integrals of `h`, `h^2` and `h^3` times normal velocity. The older
`FrontAuxiliaryTransport` retains its explicitly supplied owner-velocity model;
its tests and implementation have not been rewritten to claim the new result.
An independent quadrature test demonstrates that the two operators differ on
the same original state, rather than merely renaming the old calculation.

The spatial factor connection now uses the volume integral of
`h * (u . grad(h))` with the varying affine velocity and quadratic fan depth.
It is not the product of an owner-mean velocity and an integrated depth gradient.
All intersections and integrals retain original exact rational/quadratic-field
coordinates. No vertex welding, positive-fragment deletion or minimum depth is
introduced. Signed face moments reverse exactly and add exactly under subdivision.

The same original directed faces also provide one conservative shallow-water
mass/momentum/total-energy receipt per interface, debited and credited to its
two owners. Actual bed force and all prescribed exterior traces are retained.
The mass receipts equal the independently differentiated support-volume rates.
The original energy datum is explicit; its change contributes exactly
`-g * datum_change * mass_rate`, not an energy reset or residual correction.

Important boundary distinction: these conservative receipts describe the
prescribed **nondispersive** fan, including its exterior flux. The inherited
auxiliary pressure operator still uses reflecting outer boundaries. Their
separate passing checks are NOT a valid coupled open-boundary dispersive RHS.
Differing incident fans, slope junctions, topology evolution, finite steps,
the complete physical-momentum law and native integration remain unfinished.

## Checks

The final focused regression set passes 93 tests in seven modules, including
the unchanged original fan, pressure geometry, depth metric, auxiliary transport
and provenance-rejection tests. Independent line/volume quadrature, finite time
differences of momentum/energy, exact shared-face cancellation, hanging edges,
winding, dry owners, and a positive `1e-400`-wide front strip are covered.
Report: `tmp/front-profile-transport-regression-v1-20260918.xml`.
SHA256: `248044397bb38f2d21855a514a9753f4d9cf194bf331c714b246822ee845d19a`.

Earlier development results are retained: 31 passes before adding sub-float and
datum controls; one command with a nonexistent flux-test filename ran NO tests;
the corrected command passed 58 tests. The original-case audit first refused
changed historical hashes, then exposed the initially omitted source energy
datum. Both refusals were addressed explicitly, not by changing source records
or tolerances.

The final original-source replay exits0: all11 supported cases reproduce the
original owner volumes and mass, momentum and total-energy rates exactly. The
new profile-weighted force operators pass their exact skew and direct-ledger
checks. Unsupported records2 and7 remain unchanged and untested. Report:
`tmp/south-fork-front-profile-transport-v1-20260918.json`, SHA256
`0ff041612fe3f898791d8bcbea3fba7efee34adfd47c603304121b34b2f52c5c`.

Independent report reload rehashes all620 recorded current-source entries and
15 loaded implementation entries and verifies both unsupported records against
the source report as JSON values. Ten unused historical Python modules changed
in preceding commits; their original hashes are verified against explicit full
Git revisions, their current hashes are also recorded, and none are imported
for this computation. Measured inputs and every loaded module must match current
bytes. No original provenance hashes are overwritten or silently refreshed.

The broader pre-existing storage/face representation and block-preconditioner
regressions are not fixed by this component. No broader-suite pass is claimed.

## Hydraulic continuation

The same cook8900/startUTC2026-09-18T06:34:59.2598919Z/session68256 remains live.
The complete8050/local7000 and8100/local8000 snapshots pass BOTH full-state
and artificial-bank audits. Each retains5,382,400 cells and all86,720 artificial
bank face cells exactly dry; maximum step residual remains1.4395798775268531e-8m3.

| Time s | Max depth m | Max speed m/s | Outflow m3/s | Inflow m3/s |
|---|---:|---:|---:|---:|
|8050|3.8049520587757426|5.351137059673638|101.39956822863971|45.30695454719997|
|8100|3.8032053674404374|5.3513364566353285|104.1882917657852|45.30695454719997|

Still NOT settled. Installed4950 water remains unchanged. Reports:
`tmp/control-ablation-{8050,8100}s-{state,banks}-v1-20260918.json`.
Depth SHA256s, respectively:
`cc656ef82f65b583c852065511ae9711cfba1e9aed131e75ba3b373a79be0f55` and
`082cd2e5c88818834b905f8216406f69dfd314b76608bc897ed768a69ae154db`.
Next8150/local9000 requires its completion marker and both audits.

## Remaining delivery

Inspection of the existing publication trace places ordinary topology publishing
around0.14-0.18ms versus approximately5.4-8.5ms adaptive selection on the inspected
rebuild frames170-179. No new performance experiment or speedup is claimed.
The previous nine actual-game lane comparisons still fail the30FPS/p95 budget.

Next complete conservative physical-momentum/interface coupling, without merely
adding the incompatible reflecting and open-trace operators. Substantive surface
refresh/selection cost and actual breaking/froth appearance remain open. South
Fork is the scenario; Troublemaker is only its rapid. Colorado -> Pacuare ->
Futaleufu, Chilko/Zambezi reviews, crew, normalization, all outstanding regressions
and release requirements remain in the full goal, not replaced by these tests.
