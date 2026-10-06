# Committed foam evolution and transport cost — September 13, 2026

Normal Cartesian foam now follows the adapter's successfully committed water
duration. A zero-duration refresh preserves existing foam rather than erasing
it and inventing a fallback generation interval. Spatial remapping remains
separate: newly uncovered or dry locations cannot inherit unknown exterior foam.
This fixes clock ownership, not the unresolved visual quality or 30 FPS target.

## Implementation and limits

Refresh prepares a candidate committed-water clock before changing the grid.
It publishes that clock only with the new foam field. Initial attachment starts
at the current water time, with zero elapsed duration and no historical foam
to replay. Invalid, regressed or unrepresentable duration is refused. A clock
policy transition cannot reuse a field from the other policy. The normal path
has no wall-time fallback or half-second duration clipping. Existing non-Cartesian
review paths retain their previous clock; this is not an all-scenes clock claim.

For a held clock, same-grid wet values are copied exactly. A moved field samples
only its known prior extent, including exact border nodes; outside that extent
is empty. Generation, decay and tongue/shore attenuation are not repeatedly
applied without water time advancing. Positive-duration release, attack,
suppression and shore formulas are unchanged. This remains the existing
semi-Lagrangian presentation foam, not a newly qualified conservative froth PDE.
The existing local roller/eddy velocity model is unchanged and presentation-only.

The Cartesian per-vertex loop was tested in disjoint parallel batches. It was
exact but slower than serial in actual captures, so serial remains the normal
path. `-RaftSimParallelFoamTransport` retains the experiment as opt-in;
`-RaftSimSerialFoamTransport` overrides it. Input fields/sites are immutable
during the pass; effective velocity and color outputs are per-index. The final
sum/max retain original ascending vertex order. Attack is computed once per
refresh. Both implementations use the same equations and committed clock.

Two independent opt-in reports must not be confused:

- `-RaftSimFoamEvolutionAudit=...`: selected path versus serial density,
  effective velocity, RGBA and ordered reductions, with source water time/delta.
  Pair with the parallel opt-in to validate parallel execution; serial default
  is explicitly labeled a self-check, not parallel validation.
- Existing `-RaftSimFoamTransportAudit=...`: actual submitted mesh UV3 versus
  effective CPU backtrace velocity, and unchanged bulk-flow UV1.

The new `RaftSimSurface/GameThread/FoamTransport` CSV scope is nested inside
Refresh. It is optional for old captures; absence is not reported as zero cost.
Custom `FoamWaterSeconds` and `FoamDeltaSeconds` are seconds, not CPU timings.

## Native verification

The first build10510 failed on a local diagnostic name collision. Renaming it
fixed the failure; build98416 succeeded in45.10s. Review then caught an existing
diagnostic flag collision, corrected without replacing the old transport check.
Build74575 succeeded in42.62s. Its runtime Raft DLL SHA256:
`c51dd614b662b7cce3cc16ffa3f3f29668cc80cc1cc7da007cfa0d73ff6007ad`.

The new native `RaftSim.Water.FoamCommittedEvolution` covers held/initial fields,
candidate publication, invalid/regressed clocks, untruncated0.75s duration,
positive-time formula equivalence, exact known border nodes and refused exterior
remapping. First native63954 CLOSED1:84 pass and one failure in19.159697s.
`CartesianBoulderSurface` still changed wall time to induce transport; its
wrong-north distinction correctly became zero under the new held-water policy.
The fixture now first requires bit-exact whole-field hold despite an old wall
timestamp, then executes twelve actual1/60 native water steps. Its original
direction-error gates remain unchanged. Rock relief is compared against the
same advanced water state. Build26231 succeeds in12.89s after this fixture update.
Full native31318 CLOSED0: **85 clean passes**, zero warnings/failures/unrun,
20.499918s, report `tmp/south-fork-foam-clock-native-v2-20260913/index.json`.
All six existing GPU input fixtures were supplied unchanged. Actual actor foam
transport error4.47523731961e-8; deliberately wrong north differs0.00223505321494,
above the unchanged0.001 discriminator. Whole-field held bytes also pass.
Final Raft DLL SHA256:
`b82af142c4a892a67586be701fcac87661ccc28759af4679a5dd0fcd86d79c2e`.
Eight CSV parser/budget tests pass in0.003s,
including the optional foam scope and absent historical data.

## Actual playable integration

Audit wrapper13696 CLOSED0, verified cook suspension/resume both0, no timeout.
`tmp/south-fork-foam-evolution-v1-20260913.json` passes across50,625 actual
vertices: density, effective velocity, all RGBA bytes and ordered reductions
are exact against serial at water7.666667066514492s and accepted/kernel
delta0.066666670143604279s. This is the same new clock in both paths, not a
comparison against the previous independent wall-time behavior.

The independent transport report with prefix `south-fork-foam-transport-v1`
reports complete50,625 submitted source vertices,8,752 wet, zero UV3 transport
error and zero UV1 bulk-channel error.8,454 wet vertices differ from smoothed
published bulk velocity; that difference includes the existing presentation
return model and smoothing, not measured fluid momentum.

Carrier and detail reports `tmp/south-fork-foam-{carrier,detail}-v1-20260913.json`
share frame114:2,020 wet contact points,944 affected by detail, zero unavailable,
maximum carrier error4.761698619404342e-5cm;4,226 independent GPU texture queries,
maximum RGBA error5.9604644775390625e-8, pass. They do not establish full render
latency, traversal, visual acceptance or qualification of the experimental PDE.

At audit shutdown foam time27.800001450s and detail27.866668120s differ by one
water interval because of refresh/tick ordering. Foam has409 refreshes,2 holds,
one initialization. Detail backlog is0, five exact window remaps, no teleports;
world elapsed34.038831405s. Source-clock ownership is corrected, but synchronous
same-frame evolution and real-time capacity are **not** established. Other
presentation/material clocks are not all unified by this change.

Initial ordinary/default wrapper42439 and same-build serial control5638 both
CLOSED0, verified suspension/resume0, no timeout. Initial default was parallel;
it is historical evidence, not the final default after the measured regression.
Frame report `tmp/south-fork-foam-clock-frame-v1-20260913.json`, rows60-240,
181 samples each,1280x720, target30:

| Initial experiment | Parallel | Serial control |
| --- | ---: | ---: |
| Mean FPS | 13.413732 | 12.902243 |
| Frame p95 ms | 80.7017 | 84.6519 |
| Foam transport mean ms | 1.549904 | 0.995331 |
| Foam transport p95 ms | 1.6452 | 1.2057 |

**Both fail30 FPS.** The opposite whole-frame trend does not establish a
parallel benefit: these trajectories/crest costs differ. Measured foam dispatch
is more expensive, so the experiment is not promoted. The serial control also
contains the committed-clock fix; it is not the prior wall-clock implementation.
Parallel capture CSV SHA256:
`f424f56ca169c9e238f04c3a861183cce8a28c0d57687cf79b91c6dfe2a5426c`;
serial control SHA256:
`84dfe7863ee6352431e19de7fcccbeac18a4a7114b7e474f1ff1559d4cec62e2`.

Initial parallel default has surface49.501609ms, crest20.610654ms, selection
12.367302ms, four water calls16.071211ms; inclusive/nested, do not sum.
All181 selected frames execute four fixed ticks,724 total, zero failures.
Bridge/adapter/native clocks agree at printed precision; debt grows1.2305 to
2.6530s. Foam4 to16s is one interval behind end-of-frame water4.0667 to16.0667s.
Shutdown foam29.466668203s, detail29.533334874s, world34.033411972s. There are
444 foam refreshes,2 holds,one initialization;3 exact detail remaps,zero
teleports,443 frame copies,zero skipped copies. This is not real-time acceptance.

Initial ordinary screenshot was viewed:
`unreal/Saved/Screenshots/south-fork-foam-clock-default-v1-20260913.png`, SHA256
`dddfb8ce3d10adde59fc99d12ac54273dc8c52b8803ce5b85ec410c6da9ebd66`.
Broad glossy folds, blanket-like foam and unfinished terrain/vegetation/crew
remain unaccepted. No reference motion was viewed. Map, material and save hashes
remain unchanged from the preceding record. South Fork is still the scenario;
no Troublemaker menu entry was added.

Serial-default build81342 succeeds in41.84s. Final diagnostic wording identifies
serial self-checks honestly; build12327 succeeds in43.40s. Final native61605
CLOSED0, **85 clean passes**, zero warnings/failures/unrun,19.286444s:
`tmp/south-fork-foam-clock-native-v3-20260913/index.json`. Final runtime Raft DLL:
`e9d5f6c5628a40cfbfe5ac05cecd2094ea8d1d231cdc2bbc8c92005294989e76`.
Final ordinary serial-default wrapper48738 CLOSED0, verified suspension/resume0,
no timeout. Actual CSV `south-fork-foam-clock-final-v1-20260913.csv`, SHA256
`ae9cf0ce513470df3c5d911d55b9daac8939df999044427e7a7cf07a7ae9b214`;
report `tmp/south-fork-foam-clock-final-frame-v1-20260913.json`. Same1280x720,
30 target,181 rows60-240: **12.764093 FPS / p9586.5670ms, FAIL**. Foam transport
1.014924ms, surface52.079404ms, crest22.029361ms, selection13.028822ms, four
water calls16.690033ms; these are inclusive/nested scopes, not additive costs.
No whole-frame optimization gain is established.

All724 fixed ticks succeed; bridge/native/adapter clocks agree at CSV precision.
Requested5.3217 to19.4288s, committed4.0667 to16.0667s, backlog1.2550 to3.3622s.
Independent decimal rounding explains at most0.0001s queue-identity difference.
Foam time4 to16s remains0.0666-0.0667s behind end-of-frame committed water.
At shutdown foam28.133334801s, detail28.200001471s, world34.059614927s;
424 refreshes,2 holds,one initialization. Detail backlog0,4 exact remaps,
zero teleports,423 completed copies,zero skipped copies. Capacity and unified
same-frame ownership remain open, not hidden by the corrected foam clock.

Final screenshot was viewed:
`unreal/Saved/Screenshots/south-fork-foam-clock-final-v1-20260913.png`, SHA256
`9ad3f3f355fd1e1fcb982a9c2751fab0fc460dc1efacc99ea580e889bfa06d67`.
The same glossy broad folds/blanket-like froth and unfinished surroundings
remain; the clock fix is not visual acceptance. Protected map/material/save
hashes are unchanged again. Scoped whitespace checks pass; no commit made.

All four gameplay wrappers resumed the same background cook successfully.
Cook84534/PID32144 remains live, last4475.5s/local9510. Latest4400/local8000
BOTH audits are still authoritative;4500/local10000 is not complete yet. Run
both audits after its marker. No cook result is promoted. Crest sampling,
remaining clocks, terrain/river motion, scene sequence, crew, release and final
commit requirements remain active.
