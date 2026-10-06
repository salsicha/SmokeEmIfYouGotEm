# Remove discarded optical work — September 12

The native-stage correction retained the solver mean level but still performed
sixteen optical passes before discarding their result. Normal single Cartesian
water now executes only the original four hydraulic-analysis passes. The
stencil, wet-neighbour rejection, native-stage restoration, hydraulic amplitude,
spatial detail, topology and update cadence are unchanged.

The extracted Jacobi loop preserves separate optical and hydraulic outputs for
legacy scenes. Requested decomposition diagnostics still obtain the historical
optical output. `-RaftSimRetainDiscardedOpticalPasses` restores the old work in
the same binary without changing geometry; it is a timing control, not a new
water style. An opt-in live equality audit compares native base and hydraulic
arrays against the retained-work path on exactly the same input state.

`RaftSim.M4.NativeMeanSmoothingElision` compares the extracted loop to the
frozen original loop over a37x29 nonlinear field, irregular dry holes,
boundaries, strides1/3, strengths0/.4/1 and distinct native/crop-handover values.
It requires bit-exact four-pass hydraulic inputs and restored native base,
retains full diagnostics and checks independently requested early optical output.
Existing geometry/contact/GPU/scenario tests are retained.

Build16271 succeeds50.31s, first58-test run74606 passes. A separate nested CSV
filter timing marker was added to distinguish this work from other frame cost.
Build70524 succeeds49.74s; final run13756 exits0, report58pass and zero test
warnings/failures/unrun:
`unreal/Saved/RaftSimValidation/south-fork-smoothing-elision-regressions-v2-20260912/index.json`.
The CSV reader exposes the new scope only when present; missing old columns
are not inferred as zero. All5 parser tests pass.

Current RaftDLL SHA256
`02dc7f0d941034aff3e2c2ee7e5bbc7643258035ce3835b08facb0fb05048415`.
Water396aac31… and main97361951… are unchanged by this pass. No map, material,
terrain, solver or menu edits. Troublemaker remains a rapid inside South Fork.

Actual game81613 exits0. The same-state equality audit covers50,625 source
vertices:4 executed versus16 retained passes, ZERO different native-base or
hydraulic-analysis values. `tmp/south-fork-smoothing-elision-equality-v1-20260912.json`.
This proves the compared stage arrays, not identical scheduling or GPU state
between separate runs.

Actual CPU contact remains coupled:2,021 wet points, max error0.000047672714cm,
RMS0.000023531221cm, no unavailable/dry points. Shared crest1,550,016 samples,
max0.600607838cm against the unchanged2cm gate, fine correction tracking
0.000244915cm, refinement sourcechange0. UV3 transport/UV1 bulk errors both0.
Reports are `tmp/south-fork-smoothing-elision-contact-v1-20260912.json`,
`tmp/south-fork-smoothing-elision-crest-v1-20260912.json.cartesian-mesh.json`,
`tmp/south-fork-smoothing-elision-transport-v1-20260912.json`.

Frames000 and039 inspected: rounded broad central wave and thin froth remain
unaccepted. Motion audit confirms40 unique PNGs over11.869 game seconds with
stationary camera: `tmp/south-fork-smoothing-elision-motion-v1-20260912.json`.
Heavy capture detail backlog4.435394s,3 exact remaps,0 teleports.
Movie172301 has89 source frames/16.473s, not continuously viewed and not FPS;
SHA256 `a5d0954681fd2c381319ae7844737002f8924d85cb2bb344db6b05495f30b0fc`.
Mapdb3080cc…, materiale4e9b2f3… and save181d1e57… rehashed unchanged.

## Same-binary isolated timing

Both profiles exit0 without timeout; exact cook29104 suspended/resumed with
status0 each time. Retained36896 and optimized95031 use the same final binary,
1280x720,300 CSV samples, warmed indices100..250. Report:
`tmp/south-fork-smoothing-elision-performance-v1-20260912.json`.

| Run | Filter ms per active update | Frame mean ms | FPS | Frame p95 ms |
| --- | ---: | ---: | ---: | ---: |
| Retained16 passes | 2.593986 | 49.274801 | 20.294349 | 61.4993 |
| Optimized4 passes | 0.814487 | 52.049688 | 19.212411 | 69.0773 |

The filter is about69% cheaper per active update (77 versus82 active updates
in151 samples), but TOTAL frame rate does not improve in this pair. Crest
update rises15.771324 to17.247663ms and GPU13.646819 to14.730354ms. Different
trajectories/scheduling remain confounders: these are not deterministic replay
or sustained packaged performance measurements. Both runs STILL FAIL60FPS.
Retained CSV SHA256
`ef471b2ec1df395ba0c00e16da87870372645cca882c1f94c3f3b6d5f72f3ea1`;
optimized CSV SHA256
`e8cc08508537ebfcbc1ff946513aa941949e740b5987e0b268b0aa3920199dd5`.
Ordinary optimized detail backlog2.085ms,6 exact remaps,0 teleports,
34.058335 simulated seconds; source preparation1.410044ms/update. Retained
backlog.915ms. Do not confuse these with diagnostic recording lag.

Cook96057/PID29104 resumed, observed2183.5/local3670.2100 is still the latest
independently audited state/bank snapshot; next2200/local4000 requires both
audits. Runtime600s unchanged; hydraulic settling is not accepted.

NEXT: total GPU-detail/CPU contact with explicit frame registration and no
blocking GPU stall, larger crest/publish/GPU costs, convincing physical
breaking/entrainment/froth, guided terrain/collision traversal, full-river
hydraulic handoffs and the complete later-river/crew/release/commit queue.
No cadence, source fidelity, topology, contact or accuracy gate is reduced.
This removes dead work; it does not complete visual realism, GPU contact,
traversal, performance or the full goal.
