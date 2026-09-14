# Explicit exterior water and foam transport — September 13

Implemented the missing exterior Riemann faces in the total-depth CPU reference
and native GPU transport. This is an integration dependency, **not** a claim that
the new evolution is enabled in normal play or that waves leave without reflection.
The existing relative-detail solver remains the normal owner. Desktop acceptance
remains 30 FPS with p95 33.333 ms; no quality or physics-timestep change.

## Contract and implementation

Optional paired exterior buffers supply ghost-cell centres one cell outside the
local window, in west Ny / east Ny / south Nx / north Nx order. Each supplies
actual h, east/north momentum and conserved foam, plus independent physical bed.
The caller owns their provenance and time. These are boundary flux inputs, not
values copied over the evolving interior. No depth floor, velocity cap, mass
repair, foam production, clipping or relaxation was introduced.

The existing hydrostatic reconstruction and factored Rusanov arithmetic are used
at those faces. Endpoint normal slopes remain zero; the supplied ghost polynomial
is constant. This retains first-order boundary reconstruction while interior MC
remains available. It is not a characteristic radiation boundary. Physical bed
slopes use the ghost centres; a one-cell-wide dimension uses both exterior sides.
Foam uses the exact shared water flux and its upwind donor, dividing water flux
by donor depth before multiplying foam to avoid overflowing foam/h.

`BoundaryFlux` returns positive-coordinate-axis water/momentum/foam flux in the
same packed order. Negate west and south for outward flux. It includes normal
hydrostatic pressure, so flat-bed momentum can be balanced against the exterior;
general variable-bed momentum additionally has bed sources. Water and foam obey
the full exterior flux ledger. A 1x1 domain validates all four ghost entries.
Invalid ghost values set diagnostics and CFL zero; malformed descriptors and
periodic/exterior combinations are rejected before dispatch.

Closed/periodic GPU modes compile without exterior resources and retain their
existing allocation/dispatch count. Exterior mode adds two supplied input buffers
(20 bytes per boundary entry) and one returned ledger (16 bytes per entry), with
no extra dispatch. At 128x128 this is 512 entries, 10,240 input bytes plus 8,192
ledger bytes, excluding allocator overhead. This is accounting, not performance
qualification of the 1.6 ms water budget.

The wet graph still contains only interior neighbours. **Open nonhydrostatic
pressure closure is not implemented.** CPU `rate` explicitly refuses exterior
plus dispersive pressure. The native exterior transport API is standalone; the
current RK/advance owner cannot pass exterior buffers. Do not silently connect
this to the existing closed pressure operator and call the result open-river
integration. Normal ghost-source acquisition, temporal boundary policy,
persistent state/window ownership and evolved wet material/contact eligibility
remain required, followed by actual breaking-wave/foam and performance checks.

## Verification

Build62661 succeeded in 28.65 s. Native D3D12 session22236 closed with exit0:
76 passes, zero automation warnings/failures/unrun, 16.821411 s. Existing engine
startup warnings are retained in the log; this is not a warning-free engine or
packaged release qualification.

Report: `tmp/south-fork-exterior-transport-native-v1-20260913/index.json`.
Log: `unreal/Saved/Logs/south-fork-exterior-transport-native-v1-20260913.log`.
The new `RaftSim.WaterDetail.TotalDepthExteriorTransportGPU` exercises 22 cases:
four throughflow directions, stepped/dry lake, dry domain, 1e-30 m film, random
wet/dry state and 1xN/Nx1/1x1 grids, each first order and MC. Six additional invalid
ghost cases have zero CFL; five invalid descriptor combinations are refused.
Uniform flow, resting lake and dry domain rates are exactly zero on GPU.

Maximum rate component difference from the represented-input CPU reference is
1.52587891e-5; maximum boundary-flux difference is 1.90734863e-6. Bed slopes match
exactly in these fixtures. Largest logged absolute water/foam balance residuals
are 1.60025229e-6 / 2.95974314e-6, against flux magnitudes 453.404345 / 476.260201.
Existing relative2e-5/max1e-3 rate limits and relative2e-6 conservation limits were
not relaxed. The old closed/periodic transport, pressure, RK, frame/source,
geometry/contact and scenario catalog/migration regressions also pass.

CPU initial targeted run: 50 passes in 5.75 s. Broader 16-file run85642:
182 passes in 33.51 s. After adding two flat-bed momentum-ledger tests, final
16-file rerun5791 CLOSED exit0 with 184 passes in 33.00 s. CPU foam-pulse tests
perform 400 SSP-RK2 steps in each direction, leave less than 1% of initial foam,
balance the stage-integrated exterior ledger within 1e-12 and retain the uniform
water state exactly. These are passive transport tests, **not** evidence for
nonreflecting dispersive waves or convincing rendered froth.

Fixture: `tmp/south-fork-exterior-transport-fixtures-v1-20260913.bin`,
SHA256 `77887d123896ced07cb74dead009b1a3df57ef7128407528d868f87b4afea3ba`.
Generate with `physics/scripts/export_total_depth_exterior_fixtures.py OUTPUT`;
pass `-RaftSimExteriorFixture=ABSOLUTE_OUTPUT` to native automation alongside the
existing pressure, transport and foam-step fixtures. No historical fixture was
replaced. All exterior scenarios are manufactured, not measured South Fork data.

GPU shader SHA256 `17204efa1e84fd2fc0469863843d7533c3ec1798872b328fd0c84d8c2b0ea10f`.
WaterDetail DLL SHA256 `bba6140f063a99a3dd3b7b615d94b134040b7c789635bccdbd852f5e53ae69ad`.
Raft DLL SHA256 `7ba22fbc0e015ce130ccef19fb016df28142f3131f40f9b51dfea433729c74c4`.

## Current scope and preservation

No normal scene capture/performance run was warranted by a change to an unused
solver path. Latest actual ordinary performance remains 22.252858 FPS,
p95 51.2054 ms, failing 30 FPS; it is not a fresh measurement of these binaries.
Normal map, water material and user save hashes remain unchanged:

- Map `db3080cc87f82bafbcb5403757fead35ca6b7a5d4b52dc74c35548d5faf7abb6`.
- Material `26aa5029c579afad38fd603f96df9da304bd32ed338097d2580c9a29545ea82a`.
- Save `181d1e570485d1ec3139aec4e1d9b56d0a420fd107ce5a94218368324207f5b1`.

The 3900 s expanded-river checkpoint passes both state and artificial-bank audits
but still has more outflow than inflow; it was not promoted over runtime600s.
Cook96057 remains live, observed3940s/local38800, without restart or suspension.
4000/local40000 is next after the final complete marker and terminal confirmation.

The preceding 30-FPS confirmation turn only rechecked existing target/tests; it
was no new goal progress. This turn revalidated the specific running cook and
implemented/verified a missing integration dependency. Full scene, reference,
terrain/rapid, Colorado/Pacuare/Futaleufu, Chilko/Zambezi, crew, normalization,
release and final-commit requirements remain active. No new video access attempt
or successful video viewing is claimed. No commits were made.

A broad `git diff --check` encountered the sandbox's Git LFS temporary-write
denial on the existing corridor metadata. It did not complete and is not a release
check. Scoped tracked source/document `git diff --check` and explicit new-source
trailing-whitespace checks pass; these are not full-worktree/release qualification.
