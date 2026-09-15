# Coupled draining events and conservative momentum mixing

September 14, 2026. Experimental wet-pool integration, not complete nonlinear
rational dynamics, native gameplay, visual realism or 30 FPS acceptance.

## Actual failure topology

The original step-18 failure report now records incident transfers, source
regions, states, force parts and outside-neighborhood flow. It does not label
an inflowing pool as isolated. The four failed regions form a directed chain:
157 -> 306 -> 323 -> 349, with branches to lower receiving regions. None of
these four has incoming transfer from outside the chain. Neighboring receivers
do have outside connections; their complete river state cannot be replaced by
this small incident graph.

Incident report: `tmp/south-fork-drying-neighborhood-v1-20260914.json`, SHA-256
`12552c74a9a1e57d35abad487e3a450c2addb3819112a58cee0ad076e557d83c`.
It records nine neighboring regions and twelve aggregated directed transfers.

The failed volumes are approximately 2.1890e-247, 2.0951e-249, 9.4497e-253 and
1.0039e-254. The smallest positive branch flux, 323 -> 339, is about 1.5154e-210
and is retained. Source datums and volume-derived stages remain distinct;
report elevations are float projections of the original exact geometry.

## Explicit model change, not a repaired backward-Euler result

`coupled-events` selects a different finite-step mass approximation. It
integrates a frozen constant-capacity transfer network with water availability
events. This is NOT an exact solution of depth-dependent Rusanov evolution.
It is not obtained by clipping negative/underflowed solved volumes.

Positive reservoirs discharge at the original rates. At exact exhaustion, an
empty reservoir can pass supplied inflow in its original outlet proportions.
The empty-node routing solve includes cycles; unsupplied empty cycles cannot
circulate imaginary water. Its finite policy iteration only reduces unavailable
outflow. Exact rational arithmetic on the supplied float data determines event
times, edge-transfer integrals and remaining volumes. A zero-volume result is
an exhausted incident ledger, not a small-depth test. Positive final volumes
that cannot be represented still reject.

This changes the mass time integration from frozen proportional donor rates
to frozen capacities with availability-limited flux. It must not be described
as leaving the finite-time equations unchanged. Both schemes retain their
original instantaneous-rate controls and remain separately selectable.

Momentum uses conservative implicit mixing of the integrated transfers. The
row amount is `Vold + incoming = Vnew + outgoing`; zero final volume therefore
does not require division by zero. Only exactly zero volume AND zero stored
momentum permit source-region release. No velocity cap or global rescaling is
applied. Body forces are linearized in source volume and integrated using
event volume exposure. Side-owned pressure uses its donor's integrated active
time, matching the frozen mass-transfer capacity. Interior pressure impulses
remain equal/opposite. The global momentum check uses the explicitly
integrated external impulse, not an unchanged full-step force after drainage.
Dry-front nonadvective impulse instead uses the exact integrated active time
of the emitted mass, preserving its impulse per parcel even when its owner
receives substantially more water during the interval.
Both finite-energy gates and the 1e-10 conservation/residual gates remain.

The availability idea is informed by the draining-time finite-volume approach
in [Bollermann, Noelle and Lukacova-Medvidova, section 4](https://arxiv.org/html/1501.03628#S4).
That paper also uses dry-depth and velocity cutoffs. Those are not adopted here;
its analysis is not proof of this new event/mixing/force implementation or of
the required full rational model. This implementation additionally routes
inflow through exhausted reservoirs during the requested global interval.

## Independent controls

An analytic chain with volumes [1, 1, 0] and transfers 0->1 at 2 and 1->2 at 3
dries at times 1/2 and 2/3, not by treating the second reservoir independently.
Final volumes are [0, 0, 2], with integrated transfers 1 and 2. The same event
times hold after scaling volumes and rates by 2^-900. Tests cover supplied and
unsupplied cycles, exact per-node mass ledgers, force exposure, constant
velocity, momentum conservation, kinetic nonincrease and original infinitesimal
rates. A replay of the actual four-region incident chain transfers every
original volume to its five receivers, including the smallest branch.

That replay tracks only parcels from this no-external-inflow chain. It is not
a full river update and cannot establish geometry, energy or gameplay validity.
The actual evolving-pool audit is the next authority for integration results.

## First actual candidate: global budgets are insufficient

The first 20-step run completed all candidate budget checks, but inspection
found a peak speed of 826.1222499451007 m/s at step 6, parent 155/source 199531,
volume 1.8905761270808315e-9. It is rejected as local stability evidence despite
negative global base/full energy changes. The final-step speed of 3.8205 m/s
must not hide that earlier failure. The run recorded 362 regional exhaustion
events and ended with 381 regions; no positive water was deleted.

Report: `tmp/south-fork-event-history-v1-20260914.json`, SHA-256
`ab24986209ab6be7a6d62de077909b251d4ec8e3205a4b1d535f47887374cf2c`.
The initially dispatched 100-step extension was deliberately stopped after
this local failure was found (owned PID 24860, terminal exit 1). It supplied
no completed report and is not a live job or accepted longer-time result.

An independent growing-owner control reproduced a front-force timing defect:
volume-exposure weighting created a 19998.2 m/s front-relative increment where
the original impulse/mass ratio is 0.2 m/s. Front force now uses the same
integrated active interval as front mass. Side pressure required a separate
check. This is a new correction, not a waiver of the spike.

The second actual run again completed 20 budget-checked steps, but retained a
160.08729274275618 m/s spike at step 6 (parent 155/source 198812). Its original
volume was 2.7673701474335462e-11, new volume 5.111465021142189e-9, and integrated
force impulse [-4.364866396120519e-7, 9.97083456767531e-7]. That result also
fails local stability. Report: `tmp/south-fork-event-history-v2-20260914.json`,
SHA-256 `7419ff270c8a027d02556258107b509a8440c74bec84ddea8537a2b627c95348`.

An independent wet-side pressure control then reproduced the same mismatch:
volume-exposure weighting supplied 0.399964 impulse where the original donor
active interval requires 0.000004. Side-owned pressure now uses the same
integrated active time as its donor mass; body-force volume exposure is kept.

Final focused tests: 260 passes, 1 retained float storage/face failure. Retained
energy selection: 25 passes, 12 existing failures, no changed tolerances.
Local records: `tmp/subcell-event-suite-v3-20260914.xml` and
`tmp/subcell-event-retained-v3-20260914.xml`. Twenty random networks also retain
exact final volume, incident transfers and volume exposure when the requested
interval is split, including rational intermediate states and empty cycles.
All 464 protected source/capture/
map/profile/actor hashes remain unchanged.

## Final 20-step actual-source result

The corrected run completes all 20 requested 20 ms candidate steps (0.4 s),
including 387 regional exhaustion events, ending with 381 regions. Maximum
stored-state speed declines every step from 5.300635546245253 to
3.8303460724177953 m/s. Neither earlier local spike recurs. Maximum per-step
mass error is 1.1368683772161603e-13 and momentum error 1.4797052472204086e-12.
Every base/full energy change remains negative; the least-negative changes
are -15.493737059867271 and -18.931258578983034 respectively.

Final report: `tmp/south-fork-event-history-v3-20260914.json`, SHA-256
`d5c0a4ffb4ab7e773b88acbbd57702f1912eb2141638c8b5332298758b889140`.
All 42 source hashes match the final implementation. This is a short,
reflecting-boundary, nondispersive candidate control, not a native solver or
complete time/refinement/nonlinear qualification. A new 100-step extension
with the corrected code is the next longer-time check; the stopped v1 job is
not reused or reported as successful.

## Delivery scope

The new path remains opt-in research code. Ordinary South Fork still uses
`L_SouthForkAmerican_FullReach`; Troublemaker is not a menu scenario. Native
water, source assets, map placement and render settings are unchanged. The
full playable terrain/water/froth, 30 FPS, later rivers, crew, normalization and
release objectives remain open. Depth-dependent transport, nonlinear pressure
work, wet-front/time/refinement/open-boundary qualification and native delivery
must not be replaced by this constant-capacity network control.
