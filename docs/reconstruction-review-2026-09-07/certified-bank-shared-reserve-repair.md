# Shared-edge geometric reserve and longer changing-depth replay

September28 UTC. Supporting candidate repair only; normal v27 is unchanged.

## Implemented without widening the band

The canonical shared-edge policy reserves half the remaining geometric band
toward the wet endpoint after accounting for one full GPU coordinate step.
Both cells use identical semantic wet/dry endpoints and original bed/depth
donors. The stored point must still pass the original nonnegative-depth and
1mm retreat proofs; thin wet spans clamp to their original wet endpoint.
Storage now passes the same requested physical width as the actual edge
builder, avoiding a slightly different reconstructed width in edge identity.
No physical donor, bed, depth floor or acceptance limit changes.

An exact lattice investigation of partition-live-v2 frames189/source33168 and
214/source33610 found no certified first-row connection among the tested
signed/radial-band candidates using the nearest-wet crossing. With the shared
reserve, first-row whole-segment candidates exist for both. This is evidence
about these maps and tested coordinates, not a global impossibility theorem.

Native shared-reserve-v1 passes20 regressions, all19 original partition-live-v2
rejected updates,258 synthetic near-corner probes across both captured cells,
the earlier65-sample sweep and builder/cache/attribute checks. Synthetic probes
are not measured hydraulics or proof of a continuous parameter interval.
Independent exact audits pass13 complete stored contours and48 shared crossings;
15 audit rejection controls also pass. Original geometric width, whole wet
triangles, dry fans, shared identity and partition gates are unchanged.

Receipt:tmp/certified-bank-shared-reserve-v1-20260928-process.json.
Stored export SHA256:
6e3453f1275634418992ed5852b6b3b3175fca82615459c0cb6d6959fb7d3f38.
Exact contour audit SHA256:
db1c13d1ccbb20d452ea3b671388a3cbab44a6f319426a690fe3ce3f38039304.
The two new positive captures have14/16 and21/23 segments/triangles.
All frozen inputs were unchanged through the replay.

## Longer actual replay still FAILED

Extended from40 to90 motion samples.452 accepted updates and62 rejections;
8311.820..8400.785m (88.965m). No recurrence of the old source33168/33610
rejections in this bounded replay, but this does not establish full traversal.

[All62 new original rejection records](certified-bank-shared-reserve-live-rejections.json)
are bound to log SHA256:
9b8e68b71b25ef793b4cda668593dc82d73731475e09962c893dc5ee7188d1f3.
There are14 source23259 and48 source19466 records. These source IDs refer to the
same physical cell with dry corner(-545800,-358900)cm, before/after a render-grid
origin change from(-554200,-348600) to(-557400,-350300)cm. Bind both map and donors.

Two independently distinguished failures:
- frame342/source23259: actual endpoints share a GPU row. The complete segment
  is wet, but exact radial determinant=-19/104857600: ordering truly reverses.
- frame414/source19466: ordering is positive and endpoints are wet, but the
  connecting segment contains dry space.129 exact samples include numerator
  approximately-1.77458122e-7; the whole-segment certificate also rejects it.
  Sorting alone cannot fix this second failure.

Receipt:tmp/certified-bank-shared-reserve-live-v1-20260928-process.json.
Process exit0 does not override runtime errors. Candidate remains OFF. The
prepared isolated profiler was NOT run because live qualification failed.

## Actual views, contact and diagnostic cost

Video:unreal/Saved/VideoCaptures/RaftSim_20260928-102553.mp4.
SHA256:1f6e2b75121cd5817cdca6f34b7a8e4b27b35eb89ea1ee5936d678549407fda0.
Decoded all2890 frames,0..96.3s,1280x720,267 adjacent duplicates. Viewed6/30/60/90s:
forward motion/gross alignment remain, but extensive flat white foam, weak
breaking/recirculation, coarse banks/rocks and crew/paddle fit remain unaccepted.
Record rate and decoded frames do not establish game FPS or full animation/
shoreline continuity, especially with rejected updates.
Report:tmp/certified-bank-shared-reserve-live-v1-20260928-decoded/report.json.

Contact at world10.1105777s, before later failures:1896 wet probes,161
ground-occluded dry probes,zero unavailable/ground-occluded wet probes;
maximum support/carrier error4.7665506258454116e-5cm. No GPU parity requested.
This is not later-state contact, independent collision or full-traversal acceptance.

Successful diagnostic topology calls:median56.5788505ms,mean75.3837692ms,
range5.209599..500.013798ms;379/452 exceed50ms. Different duration, startup,
near/far components, recording and capture overhead preclude a causal comparison
with previous runs or isolated FPS acceptance.20FPS/50ms p95,zero>100ms and
bridge clock-debt gates are unchanged and not newly qualified.

## Next work and delivery boundary

Develop a general stored contour/band construction for the shallow transition,
rather than repeatedly tuning a few endpoint offsets. Row ordering and the
actual dry endcap require distinct treatment. Investigate whether radial-only
inner witnesses are unnecessarily restrictive compared with the existing
physical1mm bound; any alternative must preserve complete dry/wet partition,
non-overlap, canonical shared identity and exact width proofs. Do not simply
relax an ordering/sign/width predicate or assume a different origin solves it.
Retain both render origins and changing depths in future verification.

Then replay actual motion/contact/shoreline and measure isolated cost before
promotion to a fresh normal build. No default solver, cook, new normal package,
captured-source deletion, push or river acceptance. All owners terminal.
South Fork and the full ordered river/crew/release goal remain unfinished.
