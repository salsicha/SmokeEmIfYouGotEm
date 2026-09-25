# Independent layers against the retained cap

September25: supporting reconstruction evidence, not a playable correction.
Parent cap SHA256 is78f77b67c64dc98094522ad2a8362edd0bfeab422816c90dc668e2cc5dd2baeb.
Independent points come from the hash-verified local sections retained in
[the independent survey review](independent-lidar-followup.md).

The existing exact barycentric `sample_cap` function covers951of1199new local
points. The248outside the cap remain missing queries, not zero-height rock.
Raw2021heights are used; no apparent ground offset is applied.

| Subset inside roof footprint | Count | Median roof minus return m | Over1m |
| --- | ---: | ---: | ---: |
| All |951|.069184|62|
| Source class2 |81|.271372|11|
| Last returns of multi-return pulses |194|.323153|37|
| Upper first returns of multi-return pulses |27|−1.515693|0|

All27upper first returns lie ABOVE the current cap, by.386887–2.198241m.
Thus much of the retained cap already follows a lower layer. It is incorrect
to infer that the entire patch is an upper vegetation envelope or to apply a
blanket first-return deletion rule. Conversely the11ground-classified returns
over1m below it localize possible unsupported roof excursions, not automatically
measured replacement rock.

## Anchor686411's connected triangle patch

The anchor is cap vertex409, incident to faces
1137,1348,1710,1735,1736,1739,1740. Their union has1.110701927418603m2 area.
Boundary/centre source IDs are685888,685889,686118,686120,686411,686573,686574,
686654. Original heights include the high neighbour686654 at9.675794m relative
to the220m datum, as well as anchor686411 at10.109830m. Simply lowering/removing
409 would leave a high shared boundary and would not establish a coherent rock
surface. The existing extension builder deliberately preserves old roof faces;
changing only its new-extension pulse filter cannot repair these seven faces.

This exact footprint contains30original2019returns and17independent2021returns.
Every2021return is between7.99and8.83m above the220m datum, while the2019pool
contains both roughly8m support and many9–10.52m upper returns. Only one2021
point is class2; the other16are class1. Original lower interior examples are
685883(8.209703m),686117(8.191720m),686333(8.085954m). They are observations,
not automatically certified as rock or selected into a candidate.

The exact original pulse record for686411 is first/only return1/1, source322,
GPS256407849.39896291, original tile10SFH878056 point19465160. Therefore the
new survey's useful multi-return evidence does not turn a first-return filter
on the old cloud into a correction for this anchor.

Next expand the local support review across shared vertex686654 and its incident
faces. Define a connected interpreted exclusion only if supported by both lower
return structure and image evidence; preserve raw upper observations. Do not
patch just409, change measured XYZ, or hide unsupported holes with a smooth cap.
Any accepted candidate must replace render/collision/bed together and receive
fresh flow and normal-play validation. None of those steps is claimed complete.

Reproduction uses `sample_cap` with the cap's vertices_m/triangles and2021local
XYZ rebased through the retained anchor UTM/NAVD88 coordinate to
(683805.1336302214,4296673.447587562,220). The seven-face union is constructed
from cap triangles incident to409, and every original/new point is tested with
Shapely intersects_xy against that union. No coordinate or class filtering was
silently added to the retained local2021sections.

## Expanded local candidate: construction rejected

The union incident to source686411and686654 contains11triangles and
1.7172012538762729m2. Its nine boundary sources are685888,685889,686118,
686120,686122,686564,686573,686574,686578. All boundary edges remain below1m;
the old patch maximum edge is.963041568m, entire parent cap.998534253m.
The new footprint includes29independent returns spanning7.88–9.75m above220m,
including upper observations; it is not a uniformly ground-classified patch.

`build_troublemaker_local_support_candidate.py` attempts an explicitly
interpreted local revision, retaining the exact boundary and every outside
triangle. It excludes the two high anchors from the candidate only (raw data
untouched), using original lower interior returns685883,686116,686117,686330,
686331,686332,686333. Their source XYZ remains unchanged. A first three-point
selection and this seven-point selection both FAIL the unchanged1m edge gate.
The final failed triangulation contains new edges1.053634,1.083191,1.095877m.
These are not inherited long boundaries. The error prints all offending faces.

No candidate directory/archive was written: the failure occurs before output
creation, closure, parent sampling or installation. Later checks in the builder
have therefore NOT passed. Do not mistake the presence of a builder for valid
geometry, or rerun it unchanged expecting success. No cook or engine launch.

This local2019-only lower selection leaves an unsupported sampling gap near
the southern interior. Actual2021 lower returns exist there, but incorporating
them requires explicit source-epoch/index metadata and consistent horizontal/
vertical treatment; do not relabel them2019points or insert synthetic midpoints.
The next candidate should resolve that mixed-source contract, preserving the
unchanged1m gate, rather than removing more unrelated boundary rock or relaxing
the limit. The current source-exact playable cap remains installed, with its
documented semantic uncertainty and visual shortcomings unresolved.
