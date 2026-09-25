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
