# Exact shoreline crest-weight storage

The corrected distant-view baseline remains mean22.084942ms/p9533.7009ms,
failing the33.333333ms gate. This increment removes per-publication allocation
of the two crest-input float arrays and avoids zeroing the source prefix just
before overwriting it. It does not change hydraulic data, wetness, shoreline
crossings, topology, crest targets, refinement, collision or rendering policy.

`FRaftSimShorelineCrestWeights` retains capacity only. Every source float is
copied exactly; every reserve float is reset to positive zero each publication;
each current edge inherits its wet vertex's weights as before. Shrinking or
losing an edge cannot leave a stale weight. No input or output is quantized.

The editor build succeeds in125.57s. Native suites ShorelineCrestWeights,
ReferencedWaterVertices, ReferencedWaterComponent and ShorelineFineCrest all
pass (4success,0failure,0warning) in
`tmp/crest-weight-scratch-native-v1-20260924/index.json`. The new independent
scalar-reference test compares every float bit, including negative zero,
across32 growing/shrinking publications and varying edge membership. Existing
component/refinement comparisons also exercise the normal publication method.

Game rebuild succeeds in164.13s. The actual corrected-view900-frame run
`south-fork-crest-weight-storage-cost-v1-20260924` exits0 without timeout;
the original cook's exact-identity suspend/resume guard succeeds. CSV mode
confirmation is nonlegacy, scope offset1; audited rows60–840 give mean21.933685ms,
p9533.0047ms (PASS this short33.333333ms gate), maximum46.4453ms. CSV SHA256:
`8bfb07a55a9867b16322b5d1bc6eea1ad9106c6bd9b1aee676c379b32c52086b`.
Report: `tmp/crest-weight-storage-frame-v1-20260924.json`. The earlier failing
baseline is retained. Variable trajectory and machine load mean this single
comparison does not establish causal speedup or sustained/full-route acceptance.

Motion run `south-fork-crest-weight-storage-motion-v1-20260924` also exits0,
without timeout, and resumes the cook. Actual recording
`unreal/Saved/VideoCaptures/RaftSim_20260923-211921.mp4` has SHA256
`c801fc28c0d90911de492c1041bfd5f23783d03762b6d1f716cb593c2c33a444`.
It fully decodes466frames through15.5s, with27 adjacent duplicates; encoded
frame rate is not game FPS. Original3s/6s/11s frames were inspected: downstream
seated crew/water remain visible, route station advances25.43→25.45km and the
previous ridge gaps/foreground obstruction are absent in those views. This
is sampled image inspection, not proof that every frame is flicker-free or
that water/terrain realism is accepted. Decoder report/stills:
`tmp/crest-weight-storage-motion-decoded-v1-20260924/`.

No visual improvement or river acceptance is claimed. Whole-route realism,
normal-start/reentry coverage of this build, repeated performance and the
ordered river queue remain open; installed4950s fields and nonlinear OFF are
unchanged. Next examine remaining measured shoreline/publication cost while
retaining all geometry, then extend actual gameplay qualification.
