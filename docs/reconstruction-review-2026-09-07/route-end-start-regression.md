# Route-end start transform — September 25

The normal run-manager start-transform function requested station + 1 m for
its heading. The coordinate adapter rejects points beyond the authored route,
so a valid start in its final metre failed before checkpoint placement. Session
range checks alone did not detect this: they never built the transform.

The function now uses a backwards, in-range chord when the forward sample is
unavailable, retaining downstream orientation. It does not clamp an invalid
start into the route or change the water-height/streaming placement rules.
Normal interior starts retain their forward chord. Null adapters, nonfinite
stations and a degenerate heading are rejected.

The existing native route-range test now calls the production transform builder
at the captured route minimum, 8330 m, maximum minus 0.5 m, and maximum. It checks
position and downstream heading, plus rejection beyond the maximum. The
original session bounds checks remain. This is production-code coverage, not
an additional review-only placement path.

Verification:

- `tmp/route-end-start-build-20260925.log`: Editor build succeeded, 36.98 s.
- `tmp/route-end-start-regressions-20260925/index.json`: three native tests
  succeeded; zero failed, unrun or test warnings. Engine process exited 0.
  Tests: `RunProgressDistinctFromRapidHydraulics`,
  `ReviewCameraUsesScenarioDownstream`, `ReviewStartUsesScenarioRange`.

No packaged game rebuild, route-end wet-water placement, rendered motion or
performance acceptance is claimed by these tests. South Fork remains first and
unfinished; this bounded change closes a route-start regression only.

The preceding boulder audit also avoided repeating an obsolete repair:
Cartesian flow-direction coupling was already fixed, and normal Cartesian
raft support first samples the submitted carrier. The independently configured
fallback footprint list still differs from the rendered exposure list; that
alone does not establish a mismatch in the normal carrier-backed query.
