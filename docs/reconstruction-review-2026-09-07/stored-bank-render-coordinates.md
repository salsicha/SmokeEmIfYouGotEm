# Conservative bank contours in actual render coordinates

September28 UTC. Qualified candidate construction, **not normal playable
integration or river acceptance**. v26 remains the last delivered game and
still fails both rapid performance gates. No game package, captured source,
terrain, collision, cooked field, material or physical solver was changed.

## What this step establishes

The current normal render packet casts CPU FVector positions to FVector3f in
RaftSimShorelineMeshComponent.cpp. A certificate for ideal local or binary64
world points does not automatically survive that conversion. The new
RaftSimStoredBankContour candidate applies the storage conversion BEFORE its
whole-triangle and dry-band certificates. RaftSimThreeWetBankContour now takes
a storage policy; its original local-coordinate entry point remains available.

The policy uses an explicit render origin. Source subtraction must be exact
(error-free TwoDiff checks it), source buffer positions must be representable,
and every submitted point is binary32. The inverse-map intervals enclose the
exact stored buffer coordinate under the unchanged physical cell transform.
An independent Fraction audit reconstructs buffer + render origin exactly;
it does not trust the native rounded local inverse or native success flags.
Physical bed and depth values are never clamped, lifted or altered.

The same original captured v22 bank was checked in five frames: the original
physical location with a local storage origin, a translated control, two
reflections, and the original WHOLE-GRID origin. For the latter, dry source
26184 is row116/column84 in the225-wide captured grid. The common render origin
is(-551000,-348600)cm; the bank remains at(-542600,-360200)cm. The audit derives
that origin from the protected capture's IDs and field coordinates. This does
not independently survey the bed: these are the same cached hydraulic inputs
used by the earlier reconstruction diagnostic.

Four frames require67 boundary segments/69 wet triangles. The whole-grid frame
requires68 segments/70 triangles. Every actual stored triangle is exactly
certified wet, the omitted area outside the band is exactly certified dry,
and the band remains at most0.1cm. Exact edge incidence, radial/band ordering
and total cell partition are checked. Native ordering predicates prevent a
storage policy from accepting reversed/overlapping radial spans. Shared edge
points use the same semantic wet/dry crossing policy qualified previously.

## Retained failures and limits

The first build failed on a mixed-type auto declaration in the new test; that
declaration was corrected. Direct world-coordinate storage then failed the
whole-contour test in v2-v4; the other16 regressions passed. Those receipts and
logs remain. Rounding both coordinates outward is not generally wetward: the
captured contour has a negative X derivative near its fold. One retained
counterexample is wet at(46/1600,468/3200), but dry at(47/1600,468/3200).
The exact audit's regression retains this counterexample.

The policy now checks a bounded neighborhood of representable points, with
proved wet outer and dry inner endpoints, followed by full segment/triangle
proofs. Even that direct-world variant remains rejected on the captured bank;
it is explicitly tested as NOT safe. Rebased storage passes without widening
the band or substituting new donors. This is evidence for the rebased candidate,
not a proof that no possible direct-world algorithm could work.

Per-cell rebasing must NOT be used as the normal integration: neighbors could
round shared positions differently. The whole-grid frame test addresses the
candidate arithmetic but does not yet change the actual renderer. The renderer
must publish the SAME frame to raster, ray tracing, shoreline construction and
the corresponding inverse mapping, with explicit motion-history handling when
the frame changes. General sheared/non-Cartesian maps are rejected, not certified.

Construction is still milliseconds PER BANK, not a solved frame budget. v7's
whole-grid fixture took2.639700ms once; earlier v5 samples were about5ms. These
single native fixture timings are neither isolated game FPS nor a causal
optimization comparison. Do not enable repeated full reconstruction over
hundreds of banks every frame on the strength of these passes.

## Authoritative evidence

- Recipe: tmp/verify-stored-bank-contour-v7-20260928.ps1.
- Receipt: tmp/stored-bank-contour-v7-20260928-process.json, terminal
  native_and_exact_candidate_complete,2026-09-28T14:23:26.7269171Z.
- Editor build48.04s, exit0. Native17 tests PASS; zero warnings, failures,
  not-run or in-process tests.30 frozen implementation/proof/capture inputs
  rehash unchanged, including the protected user surface test.
- Independent exact audit: all five complete stored geometries PASS.
- Audit controls:15 tests PASS, including translation omission, GPU conversion,
  triangle/index/partition defects, band violations and the captured fold.
- Native export: tmp/stored-bank-contour-v7-20260928-stored.json;
  SHA25696b077dd4bb9d9926c8b77c84e5fc7e87c6d4ec52eee0d904fe1d5c871432a66.
- Exact audit: tmp/stored-bank-contour-v7-20260928-exact-audit.json;
  SHA2568d84e1eb80ad12352b6946bbd8b7685333598d18b7ab2796dab1646ab4375e3d.
- Original contact SHA256 remains
  bff4c53b8ad86c0003b40036862ae8c0e8e6aeb3a2e238e5e70ab0ff4dd2b74f.

## Next integration, not an acceptance waiver

1. Implement a common published render-coordinate frame, covering raster,
   ray-tracing transforms, moving-grid history and unchanged CPU support.
2. Make canonical edges, the variable bank polygon, transported attributes
   and crest weights use that same frame. Stored triangulation connectivity,
   not only node count or winding, controls cache invalidation.
3. Avoid per-frame expensive recertification only with a mathematically valid
   cache domain. For fixed bed, the physical numerator is monotone in each
   positive donor depth; a proved lower-depth wet/upper-depth dry box could
   permit exact membership checks. This is a proposed next implementation,
   not an implemented/qualified optimization or permission for stale geometry.
4. Measure actual construction frequency and whole-update cost on both rapid
   captures before normal enablement. Rebuild into a fresh stage; never cook
   into the hard-linked v25/v26 stages. Verify Boot/menu, real motion/contact,
   shoreline continuity, raster/ray consistency and isolated20FPS/bridge-clock
   gates. No diagnostic pass here supplies any of those acceptance results.
