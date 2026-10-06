# South Fork inward-retreat rotation: partial native repair

## General native transition implemented and bounded qualification passed

2026-09-28 23:34 UTC: FStorage prepares a bridge only when the first
representable row's whole-wet endcap has no radial dry witness. Original
donors and actual binary32 spacing determine the endcap, a close certified
dry witness, and a same-free-coordinate transition toward the contour.
Adaptive samples on that strip share the proved inner witness. The original
whole-cell wet/dry, orientation, shared-edge, width and triangulation checks
remain mandatory. No captured coordinate is hardcoded in the implementation.

tmp/verify-certified-bank-endcap-transition-v1-20260928.ps1 initially stopped
at its ownership guard because a separately owned Zambezi cook was live.
It created no run receipt or build before that guard. After the process exited
and all engine/compiler/cook owners were absent, the same unstarted recipe
ran once. Editor build passed in50.25s; native exit0,20/20 tests without warnings.
Both short/full searches construct case13 (82 boundary points,83 triangles)
and case14 (81 boundary points,82 triangles), with actual cache/buffer/ear
publication checks. Original19 earlier rejected snapshots,258 near-corner
synthetic probes,65 prior synthetic probes and20 changing-depth cache updates
also execute.17 whole-polygon audit controls,48 exact shared crossings and
15 independently audited whole stored polygons pass. Frozen inputs match.

Receipt: tmp/certified-bank-endcap-transition-v1-20260928-process.json.
Stored export SHA256:
6927ee60acb73cb49df5dcef795346be75dcc9e214dcadeda308e372e4af8983.
Exact audit SHA256:
badbcaee2c848c962746ae7b06d25b65e9bf1fa2a9895261a798182c61e61743.

The two partial-span controls below are not substitutes for these full polygon
checks. Likewise, these bounded native fixtures are not all-state or live
acceptance. New RaftSimStoredBankReplayTest.cpp contains all62 original
extended replay failures, generated after verifying the raw source SHA and
each record's exact membership. It checks bounded/full builders and a
persisted actual mesh cache across changing donors/render origins, including
identical-update reuse and the submitted buffer positions/triangle ears.
This expanded regression is NOT YET RUN. The prepared v2 recipe includes it
as the21st native test and freezes its new source plus the partial-span test.
A newly live raftsim_cartesian_cook process PID4460 prevents isolated execution;
do not kill or restart the other owner's work. Poll that specific owner before
starting v2; no v2 process receipt has been created.

After expanded qualification, replay the actual scene and measure isolated
cost. Existing fixture construction timers exclude FStorage::Init; the new
preparation work there MUST be included in runtime cost qualification. No
normal cook/package, solver activation, live replay, FPS/visual acceptance,
source deletion, commit or push resulted. Candidate default remains OFF.

## Subsequent constructive endcap evidence

Exact original frame414 donor analysis found that merely increasing the
canonical crossing reserve does not remove the large first-row excursion.
Fractions0.5,0.75,0.875,0.9375 of the unchanged available reserve gave
first-row whole-wet endpoint X approximately0.10419,0.08265,0.07568,0.07221.
The shared crossing policy was NOT changed.

A partial two-span construction is feasible with these actual binary32
buffer positions (render origin remains the original captured origin):

```
canonical edge E = (11600.1728515625,-8600)
first-row P      = (11610.41796875,-8600.0009765625)
vertical seam Q  = (11610.41796875,-8600.0302734375)
shared inner local witness A = (0.1034755936750478,0.0003045401247502055)
edge inner local witness     = (0.000729515625,0)
```

The E-P and P-Q spans pass exact whole-wet segment, whole-dry fan, orientation,
binary32 storage and band-distance checks using the actual rounded binary64
inner witnesses. Their maximum distances are0.0999cm and approximately
0.09988683247024055cm. P-Q uses the same inner witness at both ends; the
resulting zero-area inner fan/one band triangle are exact repeated-point
identities, not tolerance-based degeneracy. Direct E to the previously
rejected next-row point is not wholly wet and cannot simply replace P.

These controls are retained in physics/tests/test_shallow_endcap_transition.py;
both pass with Python unittest. They cover ONLY these two spans. No complete
closed polygon, native interval construction, cache integration, all62-state
coverage, in-game motion or frame-time claim follows. The next implementation
must construct the transition and compatible inner witnesses generally,
without hardcoding captured coordinates or weakening any full-cell checks.

2026-09-28 23:16 UTC. Supporting candidate work only, not a playable delivery.

## Preserved evidence and correction

The previously pending radial-only qualifications in the general neighbor,
near-axis reserve and final neighbor searches DID land. The normal-band-v3
build succeeded and constructed cases0..12, but failed case13 with19/20 tests
passing. Its receipt is tmp/certified-bank-normal-band-v3-20260928-process.json.
Earlier notes saying that three-line patch was unlanded are historical.

For original frame342/source23259, case13 switched from radial to normal
inner witnesses. This produced a negative inner-fan determinant despite
whole wet and dry sign certificates. An exact-rational check of the original
stored segment found a componentwise inward retreat within0.0999cm that
preserved strictly positive band/fan orientation and whole wet/dry signs.
That check was only a proposal, not native or whole-cell acceptance.

FStorage::InnerPoint now keeps already-certified radial witnesses unchanged.
Before the gradient-normal fallback it tries small componentwise inward
rotations of the radial retreat, reducing the smaller component first.
No wet-depth epsilon, band enlargement, changed source donors, relaxed
partition predicate or solver activation was introduced. The complete
native interval, partition, width and wet/dry tests still decide acceptance.

## Actual native result

Unique recipe: tmp/verify-certified-bank-inward-rotation-v1-20260928.ps1.
Receipt/log stem: tmp/certified-bank-inward-rotation-v1-20260928.
Editor build succeeded in84.99s. Native exit255:19 succeeded,1 failed.
Both bounded and original full searches constructed cases0..13. Case13
had82 boundary points and83 wet triangles; its cache/attribute checks were
also reached. This is fixture evidence, NOT game FPS or runtime acceptance.

Case14, original frame414/source19466, still fails stage1:

```
P=(0.10417968750000001,9.7656250000000002e-06)
Q=(0.029609375,1.953125e-05)
outer radial order lower=1.7456054687499964e-06
band triangle lower bounds=2.2053124484371412e-08,-7.5127291200691653e-05
inner fan lower=-2.6703816044988854e-05
whole wet segment=1; whole dry fan=1
```

The shallow whole-endcap connection makes a long tangential jump. Fix its
stored contour and neighboring inner correspondence together; individual
dry witness signs cannot establish a nonoverlapping partition. Do not
remove the orientation checks or rerun this unchanged failure.

The test exits before the full15-case export and subsequent independent
exact audit. The17 Python audit controls and48 exact crossing audit were
not rerun by this recipe after the native failure. All62 original extended
replay captures still require native regression coverage before another
live replay or promotion. No claims cover those unexecuted gates.

## Scope and provenance

All726 frozen source/evidence inputs matched after the failed run. No live
engine/compiler owner remained from this run. Specific elevated writes
were approved; this does not establish persistent workspace access.
Original donor captures are simulation evidence, not surveyed bathymetry.
Other river work and captured sources were preserved.

Normal v27 executable remains:
82e139184dbd93c46ebf7c0419e49da850db003d0aab4071ac35bba5dd65bcd0.
Protected WaterSurfaceTest.cpp remains:
d9abdd3643882d192e41af879eef023ed1e58f12a39d26698e42cb0f0773e8f3.
Candidate remains default OFF. No cook, package, new live engine replay,
20FPS acceptance, visual acceptance, source deletion, commit or push.
