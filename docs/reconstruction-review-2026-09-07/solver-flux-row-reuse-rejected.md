# Rolling flux-row storage experiment — September25

Rejected; no normal runtime or installed archive change.

The MUSCL flux loop creates a north-face pair vector and validity mask per worker
stripe per stage. An isolated compile-time candidate reused worker-thread storage,
reset every validity flag before each stripe, and kept independent nested leases.
No flux expression, arithmetic order, boundary policy, resolution or timestep
changed. Ownership tests covered nesting, cross-thread isolation, shrink/empty/
growth and exception release. All six native CTest cases passed in7.62seconds;
receipt: `tmp/solver-flux-row-reuse-20260925/native-tests.xml`.

The first isolated build accidentally replaced default compiler flags and warned
about missing exception unwind semantics. It was not used for tests/comparisons.
The candidate was rebuilt with `/DWIN32 /D_WINDOWS /W3 /GR /EHsc` plus the candidate
macro; a same-source baseline used identical flags except macro0 instead of1.
Both final builds completed successfully. Neither replaced an installed library.

The retained Cartesian input recipe
`tmp/solver-current-cartesian-input-v1-20260916/recipe.json` ran four alternating
baseline/candidate pairs of600steps. All eight processes succeeded and every
saved field/mask CSV matched byte-for-byte. Median solve/capture time was
1.229240seconds baseline versus1.237385seconds candidate (0.663% slower).
This small difference is not proof of a systematic slowdown, but provides no
speed benefit sufficient to justify promotion. Full commands, binary identities,
individual timings and comparison results remain in
`tmp/solver-flux-row-cartesian-pairs-20260925/report.json` and adjacent outputs.

The experimental header, guarded runtime branch and added ownership test were
removed after this result. Existing solver sources/tests are restored; original
captured data and all experiment receipts remain. No duplicate cook or engine
rebuild was launched. The earlier packaged frame-budget failure remains open;
component replay equivalence is not playable motion or performance acceptance.
