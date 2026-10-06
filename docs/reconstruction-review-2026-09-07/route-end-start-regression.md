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

## Staged game follow-through

The Game target rebuilt successfully in 282.89 s after cleanup (3060 actions,
mostly runtime dependency copies). Log: `tmp/route-start-game-build-20260925.log`.
The v7 staged executable was updated after a verified backup; no cooked map,
captured geometry or hydraulic field was replaced.

- New executable SHA256:
  `f83b3dfb780191526a4c92d615fe9b44471c423635291e60bfe542ba0d60905d`.
- Old executable SHA256:
  `6194fed46b8dbf4a37c9948112cdc54052ed96dbc792ded7bfc1f8cc3bc04ddd`.
- Backup beside the staged executable:
  `SmokeEmIfYouGotEm-pre-route-start-20260925.exe`.
- Process/deployment receipt: `tmp/route-start-staged-20260925.json`.

Two sequential Boot/menu-handler launches each captured 900 post-travel frames
and exited 0. No direct-map argument was used in these checks. Both used an
ephemeral profile, D3D12, adapter 0, 1280x720, and nonlegacy CSV timing. Strict
audits retain rows 60–840 and frame-scope offset 1:

| Start | Mean frame ms | p95 ms | 33.333333 ms gate |
| --- | ---: | ---: | --- |
| Normal selected-scenario start | 36.488174 | 44.2335 | FAIL |
| Review station 8330 m through same menu path | 33.726005 | 45.0802 | FAIL |

Reports: `tmp/route-start-staged-{normal,troublemaker}-frame-20260925.json`.
The second log confirms requested/applied station 8330.000 m, sampled=1,
destination error 0 cm. Subsequent raft telemetry remains wet and moving.
These are launch qualification, not a matched optimization benchmark.

A separate direct-map rendered check exited 0 and produced four stills at
one-second intervals: staged `Saved/Screenshots/route-start-render-20260925_000..003.png`.
First and last inspected: raft/crew/terrain/water render, viewpoint and paddles
change, but broad pale smooth water and the angular nearby rock persist. This
is sampled motion evidence, not continuous animation or collision acceptance.
Log: `tmp/route-start-render-20260925.log`.

The verified code is now in the ordinary staged game, not only Editor. Actual
wet placement at the river endpoint remains untested; its geometric transform
is covered by the native test. No new water-realism, full traversal, shoreline,
30 FPS or release acceptance is claimed. All these build/run processes ended.

## Final-metre wet placement verified

The previously missing placement check completed in the rebuilt staged game
through Boot/menu startup, with an ephemeral profile and review station
33333.646 m (float/log value 33333.645 m). Engine exit 0; 120 post-travel frames.
`tmp/route-end-wet-placement-20260925.log` confirms sampled/applied station
33333.645 m and destination error 3.64e-12 cm after successful restoration.
At about ten seconds, raft telemetry remains wet with no dry support points,
raft speed 0.535 m/s and water speed 0.532 m/s. This closes the final-metre
streaming/wet-placement check left open above, not full outlet traversal,
surveyed bathymetry, rendered shoreline review or sustained performance.

Final-metre rendered follow-up, 03:31 UTC: a separate direct-map review with
the same staged executable and station produced four one-second-spaced stills
and exited 0 (`tmp/route-end-shoreline-20260925.log`). Inspected original
`route-end-shoreline-20260925_000.png` and `_003.png` in staged Saved/Screenshots:
water, raft and three crew are present; paddle poses and water pattern change.
No whole-surface disappearance or gross horizon/shoreline jump is visible in
these sampled views. Distant banks remain smooth and sparsely detailed; these
images do not establish captured bank accuracy, underwater geometry, continuous
shoreline stability or full-route traversal. Do not repeat this unchanged short
endpoint capture as further reconstruction progress.
