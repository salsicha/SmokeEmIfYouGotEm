# Remaining requested work

Last reviewed 2026-09-10. This index does not convert diagnostic passes into
completed scenes. The request is to finish the work, not merely close its records.

The user explicitly activated an app goal on September 7 to complete this entire
queue and keep working until genuinely finished. The goal includes final
verification and committing completed changes; it has no user-specified token
budget. Keep it active while any required work remains. Do not replace this
scope with a single diagnostic milestone or mark unavailable measurements as
verified. Resume from the latest checkpoint after interruptions, checking for
owned running processes before launching work.

## Active reconstruction sequence

1. **South Fork — active, incomplete.** Latest:
   [pointwise bed GPU integration](../reconstruction-review-2026-09-07/liquid-exact-exit-bed-integration.md).
   Exact terrain-bed lookup and Windows source validation now execute;14engine
   regressions and301Python tests pass. Full120-step dense replay still REJECTED,
   now atstep30: one particle exits a prescribed-inflow row despite being96cm
   above the bed. Full trajectory audit confirms non-outgoing condition alone,
   not the prior midpoint-bed error. Next fix physical inlet/advection consistency
   with ghost-grid forcing; retain exit/mass gates. All build/UE processes terminal.
   No sustained-flow, scene, visual or performance acceptance. Prior:
   [dense outlet bed mismatch](../reconstruction-review-2026-09-07/liquid-dense-outlet-bed-review.md).
   Longer120-step dense replay REJECTED: step18 firstfails exit gate. Exact
   trajectory follows terrain2cmabovebed, but outlet checks higher row-midpoint
   bed. Prepared continuous exact-triangle face profiles and299Python tests pass;
   GPU integration and sloping-bed regressions are NEXT, not completed. Preserve
   all original flow/visual/raft/performance acceptance. Prior:
   [dense native neighbor storage](../reconstruction-review-2026-09-07/liquid-native-dense-neighbors-review.md).
   All719335 prepared seeds and original parent forcing now run with compact
   native handoff. Dense replay exposed/fixed stale neighbor views after slot
   allocation growth. Clean dense-nq-v3 passes719484survivors, exact owner4
   neighbor membership, all12rawP2G owners and regional reduction with original
   numeric gates.295Python tests and13engine regressions pass; both full-history
   same-process restart generations pass inlet/outlet/identity/P2G checks.
   Five dense native steps are NOT sustained flow,
   lifetime, visuals or performance acceptance; those and all original scene
   requirements remain. No map promotion. Prior:
   [native generation and same-process restart](../reconstruction-review-2026-09-07/liquid-native-restart-review.md).
   Generation tokens now gate native transfers, detect unexpected reset/duplicate
   epochs and birth namespace exhaustion. Live restart exposed/fixed reused
   transient systems and a multi-tick reset/dispatch reservation particle-loss bug.
   Both corrected generations pass12initial+10births−3exits=19survivors,117moving
   segments each and original rawP2G/reduction.285liquidPython tests and all13engine
   regressions pass (one unrelated HTTP warning, no failures/RHI errors). Dense
   allocation/repopulation/calibrated flow and all scene/reference/FPS remain open.
   No map promotion. Prior:
   [live outlet and simultaneous source emission](../reconstruction-review-2026-09-07/liquid-native-outlet-review.md).
   Actual native12initial+9births−3downstream exits=18survivors passes independent
   full-payload/identity/segment/physical-face accounting,9continuous commits and
   109moving segments. RawP2G/reduction passes unchanged;279liquidPython tests and
   all12engine regressions pass (one unrelated HTTP warning, no failures/RHI errors).
   Old combined diagnostic was rejected for stopping handoff before the capture;
   corrected continuous replay passes. Not dense flow, scene, visuals or FPS.
   Reset/generation/lifetime/repopulation/allocation and all original acceptance
   requirements remain. No map promotion. Prior:
   [atomic survivor/exit ledger](../reconstruction-review-2026-09-07/liquid-retirement-transaction-review.md).
   Optional approved exits now produce exact ledger/survivor partitions with one
   native commit gate. Twelve engine tests pass, including full retirement and
   unchanged native sinks for corrupt evidence. Native handoff/capture integration
   compiles; live non-retiring regression still passes18particles,84segments and
   rawP2G/conservation. Actual live outlet fixture/ledger audit remain required,
   along with lifetime/dense flow/surface/raft/reference/FPS acceptance. No promotion.
   Prior:
   [physical parent exit classification](../reconstruction-review-2026-09-07/liquid-exit-classification-review.md).
   GPU classifier distinguishes real outgoing parent-face crossings from internal
   cuts, dry/below-bed/floor/roof/corner leaks and invalid segments. Adapter binds
   exact validated parent rows/frame. All11engine tests pass without warnings or
   RHI errors;261liquidPython tests pass. Native retirement/exit ledger is NOT
   integrated yet; current exterior rejection remains. Sustained dense flow,
   surface/foam, raft/reference/FPS and all original acceptance remain incomplete.
   Prior:
   [native pre-advection segments](../reconstruction-review-2026-09-07/liquid-native-segments-review.md).
   Actual particle origins now persist through native transfers. Live replay
   verifies84 moving segments across7 step pairs,18 refreshed origins at P2G,
   with prior birth/handoff and rawP2G/conservation checks passing. 261liquid
   Python tests pass; all ten engine regressions succeed (one unrelated HTTP
   warning, no test failures or RHI errors). Actual open-face exit
   classification and atomic retirement, resets/lifetime/dense water and original
   visual/raft/reference/FPS acceptance remain incomplete. No map promotion.
   Prior:
   [continuous native emission](../reconstruction-review-2026-09-07/liquid-native-emission-review.md).
   Nine initial plus nine source births survive eight native commits. Fixed
   native IDs larger than particle capacity and spawn/update NQ slot collisions.
   Corrected emission-v4 passes all18 particles' raw P2G/conservation and repeated
   handoff with nineteen owner changes; ten engine regressions pass without
   warnings/failures,255liquid Python tests pass. Non-emitting live replay also
   passes twelve particles/three commits, continued motion and raw P2G.
   Exits/reset/lifetime/dense water and original scene acceptance
   still remain. No visual/performance acceptance or map promotion.
   Prior:
   [initially empty native receiver](../reconstruction-review-2026-09-07/liquid-empty-receiver-review.md).
   Empty owner 0 receives nine actual native particles; all nine survive three
   commits and move on step6, with exact payload/identity/free-list checks and
   passing native P2G, no RHI errors. Reservation now covers all empty handoff
   owners; fully seeded twelve-particle regression also passes three commits,
   continued motion and native P2G with a clean RHI log. 249 liquid Python tests pass.
   Continuous births/exits, reset/lifetime, dense water/surface and the original
   scene/reference/raft/performance acceptance remain incomplete. No map promotion.
   Prior:
   [actual native particle handoff](../reconstruction-review-2026-09-07/liquid-native-handoff-review.md).
   Actual GPU word/count/ID-lookup commit is now verified: 12 particles retained,
   6 native owner changes, all 12 move on the following completed step; native
   P2G/reduction and exact identities pass. Ten engine tests pass without warnings;
   248 liquid-specific Python tests pass. Three consecutive native commits now
   pass, with owner changes [6,3,0], all 12 particles moving afterward, exact full
   payload/ID/free-table checks and clean RHI validation. Native step 6 P2G passes.
   Initially empty receivers, births/exits, reset/lifetime, dense fluid and full
   scene/raft/reference/performance acceptance still remain. No map promotion.
   Prior:
   [receiving persistent handles](../reconstruction-review-2026-09-07/liquid-particle-handles-review.md).
   Staging preserves6staying local handles and assigns6noncolliding imported
   handles; complete free lists and full source payload verified. Nine engine
   tests pass with no warnings/failures;243Python tests pass. Still NO native
   dataset commit/subsequent-step handoff or visual/performance acceptance. Next
   real native word/count/ID-lookup commit with prior dispatch/allocation
   reservation and next-step ownership proof; then births/exits/empty receivers,
   reset/lifetime, dense water and all original scene acceptance requirements.
   Prior:
   [receiving-side particle assembly](../reconstruction-review-2026-09-07/liquid-particle-assembly-review.md).
   GPU destination capacity/accounting gate and full-state compaction verified.
   Native12particle/6cross-owner assembly preserves every word and all identities;
   raw P2G/reduction still pass. Eight engine tests succeed (one HTTP warning),
   240Python tests pass. NOT native dataset commit or subsequent-step handoff,
   sustained flow, visual/performance acceptance. Next local persistent handles,
   native count/free tables and dispatch/spawn reservation, actual import/export
   plus generation/reset/lifetime; then dense water/surface/foam and full scene.
   Prior:
   [full-state native routing candidates](../reconstruction-review-2026-09-07/liquid-particle-routing-review.md).
   Build fixed; full float/int payload GPU staging tested. Native twelve-particle
   replay has six physical-boundary crossings, all destinations independently
   verified; raw P2G and birth identity still pass. Seven engine tests pass with
   no test warnings/failures;236Python tests pass. NOT actual native handoff,
   sustained flow, visual or performance acceptance. Next destination assembly,
   native import/export/count/ID tables and bounded dispatch/spawn integration;
   then connected dense water, continuous surface/foam, raft and reference/perf.
   Prior:
   [native birth identity](../reconstruction-review-2026-09-07/liquid-particle-identity-review.md).
   Persistent integer birth-owner/sequence tags installed; actual12-particle
   same-run first-to-third-step snapshots preserve all identities, with raw
   P2G/reduction still passing. Six engine tests succeed (one HTTP-connectivity
   warning),232Python tests pass. NOT actual ownership handoff, sustained wet
   flow, visual or performance acceptance. Next bounded native routing/import/
   export, local handle/count tables and generation/sequence-lifetime contract;
   then regional affine/dense wet transport and full-rapid surface/raft checks.
   Prior:
   [native particle transfer](../reconstruction-review-2026-09-07/liquid-native-transfer-review.md).
   Actual four-particle corner snapshots independently pass native P2G on steps
   1 and3; no reduced-component mismatches, four particles survive/move, no
   phantom deposits. Fixed missing spawn-time NQ insertion and removed inherited
   21m fixture-volume deletion on regional clones. Final five engine tests pass
   with no warnings/failures;228Python tests pass. Terrain/exterior/shared
   regressions remain exact. NOT sustained flow, handoff, visual or performance
   acceptance. Next global identity/native count and particle ownership handoff,
   regional affine transport, dense/connected wet conservation, continuous
   surface/foam and full-rapid/raft/reference/performance validation.
   Prior: native raw RGBA32F momentum/
   volume publication, multi-owner conservative reduction, and normalization
   before boundary/D/P/G installed. Actual16-owner reduction and nonzero resolve
   tests pass; all12 ZERO-PARTICLE integration:30 reductions,1160 pressure and29
   boundary exchanges,1518 aligned groups. Terrain/exterior/shared readback
   regressions remain exact. Five actual-engine tests/no warnings or failures;
   224Python tests pass. NOT native wet transfer, visual or performance acceptance.
   Next nonempty native P2G audit and particle ownership handoff, connected wet
   projection, continuous surface/foam and full-rapid/raft/reference/perf checks.
   See [regional raw transfer](../reconstruction-review-2026-09-07/liquid-regional-transfer-review.md).
   Prior: validated read-only parent-face
   table installs actual exterior inflow/outlet pressure; local internal edges
   cannot become reservoirs. Final all12 ZERO-PARTICLE native run verifies898
   exact inlet velocities and6720outlet pressures, no spurious forcing/outlets;
   shared143040cell and terrain1587600cell regressions remain exact. Explicit
   nearest-even half conversion fixes observed velocity mismatches. 224Python/
   four actual-engine tests pass. NOT wet flux/visual/performance acceptance.
   Next conservative raw P2G mass/momentum and particle handoff, connected wet
   projection, continuous surface/foam and full-rapid/raft/reference/perf checks.
   See [parent exterior forcing](../reconstruction-review-2026-09-07/liquid-parent-exterior-review.md).
   Prior: native same-step RGBA16F boundary
   exchange after every complete Compute Boundary group. All12 regions:5960
   shared columns/143040 cells match physical owners bit-for-bit; terrain and
   nonzero pressure regressions remain exact. 219Python/three actual-engine tests
   pass, including16-owner signed velocity/all boundary type GPU exchange.
   Still ZERO water in native integration, NOT moving-liquid or visual/perf
   acceptance. Next explicit exterior forcing, conservative P2G/particle
   exchange, connected wet projection, shared surface/foam and full-rapid checks.
   See [shared boundary exchange](../reconstruction-review-2026-09-07/liquid-regional-boundary-exchange-review.md).
   Prior: installed regional D/P/G metric,
   globally aligned pressure phases and read-only shared pressure halos. Actual
   native first-color nonzero-marker readbacks: all 2113056 cells match exactly;
   all12 zero-water regions exchange pressure at each iteration. Terrain contact
   remains exact for1587600 cells. 215Python/three actual-engine tests pass.
   This is NOT wet cross-region flow or visual/performance acceptance. Next
   exterior/shared masks and forcing, conservative P2G/particle transfer,
   connected wet projection, shared surface/foam and full-rapid validation.
   See [regional pressure ownership](../reconstruction-review-2026-09-07/liquid-regional-projection-review.md).
   Prior: explicit canonical regional
   terrain contact installed for primary particles and pressure; removed the
   competing Landscape fallback in regional classification. Actual all12 empty
   regional GPU masks exactly match captured triangles for1587600 interior cells.
   211 Python/four actual-RHI tests pass (one connectivity warning); legacy wet
   refactor replay passes core audits but still looks glossy/lumpy. NOT wet
   cross-region flow or visual/performance acceptance. Next external/shared
   boundaries,global pressure phase,conservative P2G/particle transfer,shared
   surface/foam,and wet/full-rapid/reference/performance validation.
   See [regional contact bindings](../reconstruction-review-2026-09-07/liquid-regional-contact-bindings-review.md).
   Prior: native per-dispatch-group
   finalization hook and one-dispatch multi-owner R32F pressure halo exchange.
   Actual twelve-region ZERO-WATER run passes 1080 exchanges over all5960 shared
   columns, with every address checked against prepared geometry. Four actual-RHI
   tests pass (one connectivity warning), including exact16-owner GPU values;
   207 Python tests pass. This is NOT wet regional coupling or visual/performance
   acceptance. Next regional frame/contact/exterior bindings, global pressure
   phase, conservative P2G/particle transfer, shared surface/foam and wet checks.
   See [regional pressure exchange](../reconstruction-review-2026-09-07/liquid-regional-pressure-exchange-review.md).
   Prior: owner-scoped render-graph
   clock/foam histories and explicit rectangular reconstruction/foam/readback
   metrics installed in live reconstruction.207 Python/four actual-GPU tests
   pass, including interleaved active/paused/reset rectangular owners. Legacy
   moving-water replay passes core audits but remains glossy/lumpy. Console
   still attaches one fixture, not live coupled regions. Next regional frame/
   contact bindings and iteration-level shared pressure/conservative grid,
   particle and foam exchange, continuous surface/raft/reference/performance.
   See [reconstruction-owner review](../reconstruction-review-2026-09-07/liquid-reconstruction-owners-review.md).
   Prior: all twelve terrain contact pages
   and exact exterior/shared/diagonal halo maps, with engine boundary builder.
   Preserved original geometry and query anchor; v3 contact ABI fixes float32
   page-rebase mismatch. All719335 seed contacts exact,356320 source triangles
   checked;203 Python/four actual-RHI tests pass (one connectivity warning).
   Legacy wet replay passes core audits but still looks glossy/lumpy. Regional
   live coupling not installed; no visual/performance acceptance. Next explicit
   regional installation, isolated histories, iteration-level shared pressure
   and conservative particle/grid exchange, continuous surface/raft validation.
   See [regional geometry review](../reconstruction-review-2026-09-07/liquid-regional-geometry-review.md).
   Prior: explicit canonical regional
   engine decoder, Niagara source/seed bindings and shared initial reader added.
   Regional burst now uses exactly its seed count under the native timing gate;
   compiled code showed inherited tank allocation grows with grid dimensions.
   Five actual-RHI engine tests and 197 Python tests pass; legacy twelve-second
   wet replay passes core audits but remains glossy/lumpy. Regional water is not
   activated or coupled. Next matching contact/external/shared boundaries, actual
   regional birth/partial-X GPU checks, isolated histories, conservative exchange,
   continuous surface/raft/reference/performance validation. No v3 guard bypass.
   See [regional engine-state review](../reconstruction-review-2026-09-07/liquid-regional-engine-state-review.md).
   Prior: exact full-state partition into
   12 bounded regions/17 shared interfaces preserves all 719,335 seeds and 6,144
   inlet sites, with independent reassembly audit. Actual pressure shader now
   handles final two-cell groups without trimming extent. Exhaustive CPU coloring
   checks and actual-RHI coupled shader tests pass; 197 Python tests pass. Actual
   12 s legacy wet replay passes core audits but remains visually glossy/lumpy.
   Regional runtime exchange is NOT implemented; no full-rapid/performance/visual
   acceptance. Next strict regional engine source/seed/frame consumer, matching
   contact/boundaries, wet partial-X GPU check and conservative shared coupling.
   See [regional-state review](../reconstruction-review-2026-09-07/liquid-regional-state-review.md).
   Prior: implemented explicit native XYZ
   allocation and integrated it into the coupled halo path. Actual zero-inlet
   rectangular check verifies 68x36x24 solver / 136x72x48 render allocations and
   physical material frame. Actual coupled 12 s RHI regression passes core
   audits; six editor tests (including 14 coupling variants) and 190 Python
   tests pass. Viewed water remains glossy/lumpy, no realism or full-rapid
   acceptance. Next matching regional source/seed/frame consumers and conserved
   shared exchange, continuous surface/raft integration and reference/performance
   validation. Limits unchanged; v3 installer still guards against mismatched state.
   See [allocator review](../reconstruction-review-2026-09-07/liquid-independent-allocation-review.md).
   Prior: generalized boundary face/origin
   addressing and compatible pressure XYZ metrics. Added strict bounded v3
   decoder; fixed installer refuses mismatched allocation. 190 Python/four
   headless editor tests pass; build succeeds. Corrected 12-second RHI regression
   passes live/clock/stage/affine/foam checks, but inspected water is still glossy
   and lumpy. No full-rapid GPU, visual or performance acceptance. Next explicit
   native XYZ allocation with matching region sources/seeds and conservative
   shared exchange, then continuous surface/raft and reference validation.
   See [boundary-layout review](../reconstruction-review-2026-09-07/liquid-boundary-layout-review.md).
   Prior: whole-rapid source, initial-water,
   contact and boundary profiles generated and audited. Fixed false water in
   dry native columns and encoded-site contact precision, preserving captured
   terrain. 719,335 seeds; contact error 0.00712528 cm below unchanged 0.01 cm.
   Engine reader and primary/secondary queries now support bounded v2 contact
   tables; exact contact-region extraction added. 202 Python tests and two
   headless editor decoder/frame tests pass; build succeeds. No GPU/visual
   acceptance or scene promotion. Uniform full-domain resources exceed existing
   particle/volume caps; limits unchanged. Next conserved bounded runtime
   integration, remaining v3 consumers, single-surface raft coupling and actual
   motion/performance/reference checks.
   See [profile/reader review](../reconstruction-review-2026-09-07/liquid-whole-rapid-profile-review.md).
   Prior: prepared a source-aligned
   245x81 m whole-rapid collision/boundary domain, covering all 4,226 recovered
   rock vertices and all four reviewed rock-region polygons. Exact triangle
   clipping preserved; actual native control-volume conservation error is
   6.23e-7 m3/s under the unchanged 1e-3 gate. Native wet-face remapping fixes
   two interpolated dry-shore flux conflicts without moving terrain or inventing
   wet support. 17 focused tests pass. This is preparation, not active full-rapid
   GPU water: downstream profile/runtime generalization, continuous surface joins,
   playable physics, reference motion and performance validation remain next.
   See [whole-rapid domain review](../reconstruction-review-2026-09-07/liquid-whole-rapid-domain-review.md).
   Prior: repaired geographic registration
   of the 3D liquid. Negative actor scale collapsed Niagara's grid; the opt-in
   adapter now uses positive allocation/rotation and consistent source, boundary,
   primary and secondary contact coordinates. Actual v6 twelve-second RHI-validated
   capture passes grid/material-frame, transfer, timing, foam and sampled contact
   checks. Viewed result remains glossy/lumpy, not a realistic returning roller.
   Still an isolated 21 m patch with no recovered-rock vertices inside its physical
   bounds; no production promotion or performance acceptance. Next whole-rapid
   integration in the corrected geographic scene, not more isolated shading tuning.
   See [geographic liquid review](../reconstruction-review-2026-09-07/liquid-geographic-frame-review.md).
   Prior: fixed the bounded geographic
   review's downstream carrier cutoff with one fixed 270 by 162 m mesh at the
   unchanged 1.5 m spacing. Actual v3 traversal passes 2,428 coverage checks,
   including exact intentional hull-mask agreement, with one existing warning.
   Inspected overhead now covers downstream rock groups. Short warmed overhead
   profile: 62.39 FPS at actual 1280x720 letterboxed view / 60% resolution quality;
   not full-scene performance acceptance. Still smooth water/coarse rock faces.
   Next larger-map physical hole/crest/roller and source-aligned turn sequence;
   no production promotion. See [fixed surface coverage review](../reconstruction-review-2026-09-07/fixed-surface-coverage-review.md).
   Prior: fixed the mirrored ENU-to-Unreal
   presentation in a separate geographic registered-rock review map, including
   matched world currents, water winding/normals, terrain collision and starts.
   Actual parity test passes; 254 collision probes pass; 64.9 s guided traversal
   reaches the outlet with 604 wet samples and no missing ground (one unsuppressed
   render-thread CVar warning). New captures still show coarse rock connections
   and overly smooth water; downstream overhead water coverage also needs review.
   Continue on the corrected larger map, not the isolated liquid patch. See the
   [geographic orientation review](../reconstruction-review-2026-09-07/geographic-orientation-review.md).
   Prior: inspected the user's actual
   Troublemaker video and registered the current liquid test footprint to NAIP.
   The 21 m patch contains zero recovered-rock vertices and essentially none of
   the four reviewed rock regions; it cannot validate the whole wake/turn
   sequence. Next return to the larger matched registered-rock playable scene
   for source-aligned geometry/flow comparison before further local liquid
   tuning. No terrain moved or scene promoted. See the
   [reference coverage review](../reconstruction-review-2026-09-07/troublemaker-reference-coverage-review.md).
   Prior: compatible midpoint primary
   transport is implemented and actual GPU replay verified, but remains an
   experiment: no convincing roller, foam/secondary interpolants not yet unified,
   editor mean/p95 25.586/27.657 ms with a 93 ms spike. 180 numerical and 16
   engine tests pass (one HTTP timeout warning). Keep the particle-only surface
   fix as baseline. Next verify named-rapid landmarks and inferred submerged
   control against the captured river evidence, then native forcing and physical
   crest/roller, before playable integration. See the
   [transport review](../reconstruction-review-2026-09-07/liquid-compatible-advection-review.md).
   Prior: identified exposed grid shelves
   caused by the render-only binary occupancy floor, not solely flow shading.
   The particle-only candidate removes that floor from the visible SDF while
   keeping its audit as a control: actual grid-face crossings fall to four
   versus 7,735 in the same capture's unused floor. Quadratic transfer passes
   actual GPU moment parity but does not yet produce a returning roller.
   Twelve-second live/foam/clock/contact checks pass; rounded ripples, internal
   pockets and physical crest behavior remain unaccepted. Editor mean/p95
   25.125/27.247 ms is not whole-scene acceptance. Next: particle volume and
   source/outlet/bed consistency, then crest/roller and playable integration.
   See the [particle surface review](../reconstruction-review-2026-09-07/liquid-particle-surface-review.md).
   Prior: fixed a demonstrated hard
   reconstruction shape switch at 25 neighbors with an opt-in continuous
   weighted transition. Actual GPU continuity tests and 12 s motion checks pass;
   it affects only 383 / 51,871 sampled kernels, not the dominant dense-surface
   lumps. 165 numerical and 16 engine tests pass under RHI validation. Benchmark
   mean/p95 26.19/28.58 ms, not full-scene acceptance. Next: dense free-surface
   geometry and source/outlet/roller physics, then continuous playable integration.
   See the [kernel review](../reconstruction-review-2026-09-07/liquid-continuous-kernel-review.md).
   Prior: nine identical-state optical
   comparisons isolate the cyan cast to inherited extinction. Selected muted
   green / roughness 0.22 is verified in a separate 12 s moving capture; all 714
   GPU steps and foam/live-field checks pass. 160 numerical and 15 latest engine
   tests pass with RHI validation and no test warnings/failures. Coefficients are
   authored, not measured. The surface still has rounded fragments, regular
   ripples and coarse crests; next work is primary surface/fragment geometry,
   physical roller/source/outlet consistency and continuous playable integration.
   See the [optics review](../reconstruction-review-2026-09-07/liquid-river-optics-review.md).
   Prior: current reconstructed water now
   precedes every secondary simulation substep. RHI-validated 12/60 s captures
   verify exact dispatch/clock coverage; final sampled spray inside water is
   0 / 11,942 and foam interface-distance p95 is 0.952 cm. 157 numerical and 15
   engine tests pass (the latter before the final per-step edit; subsequent GPU
   captures exercise it). Editor benchmark mean/p95 is 26.04/28.73 ms with one
   101.76 ms spike, not full-scene performance acceptance. Cyan/glossy optics,
   physical crest/roller calibration and continuous playable integration remain
   open. No saved scene promotion. See the
   [current-surface review](../reconstruction-review-2026-09-07/liquid-current-stage-review.md).
   Prior: swept secondary terrain contact
   and physical bounds now pass sampled 12/60 s checks, but end-of-step surface
   prediction still leaves 12.2% of spray inside the rendered water at 60 s.
   Appearance remains cyan/glossy and unaccepted. Editor mean/p95 is 26.42/28.34 ms;
   149 numerical and 14 engine tests pass (one HTTP warning). No saved scene
   promotion. Next fix actual current-surface ordering, then physical crest,
   optics, single-surface playable integration and whole-scene performance; see
   the [secondary contact review](../reconstruction-review-2026-09-07/liquid-secondary-exact-endpoint-review.md).
   Prior: an isolated affine-transfer
   candidate now has verified actual GPU gradient state and passes 60 s live
   reconstruction/foam transport checks, with visible splashes, froth and some
   reverse pool flow. It is not calibrated or photorealistic. Secondary terrain
   contact and current-surface coupling still fail; editor mean/p95 is
   25.93/27.90 ms, slower than the smoother baseline. 136 numerical and 14 engine
   liquid tests pass. No saved scene promotion. Next fix exact secondary bed
   contact and surface lag, then physical crest/optics/playable integration and
   whole-scene performance; see the [affine review](../reconstruction-review-2026-09-07/liquid-affine-transfer-review.md).
   Prior: the liquid review now includes
   the hypothesized shelf and plunge pool, using a verified coordinate-only
   rebase with captured heights and hydraulic arrays unchanged. A real-GPU
   half-texture interpolation defect in foam generation is corrected; 12 s
   and 60 s transport/pause checks pass without relaxed tolerances. The 60 s
   capture still looks glossy and lacks a demonstrated returning surface
   roller in the sampled control strip. Secondary contact and whole-scene
   integration remain open. Editor mean/p95 is 23.44/25.53 ms, not performance
   acceptance. Continue with interior drop/pool circulation and pressure/stage
   coupling; see the [control-centred review](../reconstruction-review-2026-09-07/liquid-control-centered-review.md).
   Earlier pipeline history: particle covariance/density and
   distance generation are now connected directly to live Niagara GPU positions
   in the unsaved review. A twelve-second capture verifies 750 updates and 30
   distinct motion frames, with correct current particle positions and no engine
   error lines. The existing single visible texture is updated; no second mesh
   or particle-state mutation is introduced. Images still look cyan/plastic and
   expose rectangular test-window edges. Solver-fluid interior support now runs
   on the live GPU: independent audits verify current classification, CPU parity,
   removal of false interior air, no new water in non-fluid cells, and matching
   displayed surface signs. It is not physical-volume or visual acceptance.
   See the [live continuity review](../reconstruction-review-2026-09-07/liquid-live-occupancy-review.md).
   Uninterrupted editor-fixture measurements show 16.77 ms mean
   with the native surface versus 23.32 ms with reconstruction; streaming GPU
   timestamps measure 5.97 ms for reconstruction, mostly density generation.
   These are not packaged-game FPS or full-scene performance acceptance. See the
   [live cost review](../reconstruction-review-2026-09-07/liquid-live-performance-review.md).
   The continuity variant remains about 6 ms total GPU reconstruction in its
   separate benchmark. Persistent current-surface foam now uses actual GPU
   elapsed time and solver velocity; independent active/paused audits verify
   transport and exact pause stability after correcting a support-edge rounding
   defect. The foam/copy stage costs about 0.112 ms in the bounded fixture.
   Latest: 112 numerical tests pass; 14 engine regressions pass without warnings
   in `engine-liquid-surface-strain-source`. Surface coverage now uses true
   tangential compression and suppresses pure rotation sources. Live transport
   parity/pause checks pass, but appearance remains unaccepted. Offline crest
   evidence and candidate depth/speed now point to primary drop/pool and imposed
   stage review before further source-strength tuning; see the
   [surface-source review](../reconstruction-review-2026-09-07/liquid-surface-strain-source-review.md).
   The native secondary emitter now
   initializes with a single-attribute SDF grid, retains the optical override,
   and requests a bounded 2048-particle batch without GPU spawn rejection.
   Metric curl, elapsed-time emission, world-frame velocity and state persistence
   are corrected; actual populations now reach hundreds rather than one.
   Appearance remains cyan/plastic and weakly frothy, and sampled secondary bed
   penetration remains in the earlier native-support captures.
   An owned neutral/matte sprite optical correction is verified active but does
   not solve the appearance. Paused sampling finds 12 of 20 spray particles
   inside rendered water despite being outside native water. The new shared
   rendered-surface history candidate reduces that to one of 62, and p95 foam
   distance to the rendered interface is 0.954 cm. Actual GPU cache contents and
   consumed timestamps are verified; one-step lag and domain escapes remain.
   Appearance still fails. A paired editor benchmark measures 23.38 versus
   23.52 ms mean frame intervals and about 0.022 ms extra GPU copy time; this
   is not packaged FPS or full-scene performance acceptance. See the
   [shared-surface review](../reconstruction-review-2026-09-07/liquid-secondary-shared-surface-review.md);
   do not treat particle counts as visible spray. See the
   [secondary metric review](../reconstruction-review-2026-09-07/liquid-secondary-metric-review.md),
   [current foam review](../reconstruction-review-2026-09-07/liquid-current-surface-foam-review.md)
   and [clock review](../reconstruction-review-2026-09-07/liquid-gpu-clock-review.md).
   Coherent visible froth,
   whole-scene performance/shore/raft integration and
   physical/visual acceptance remain open. Continue with the
   [GPU reconstruction review](../reconstruction-review-2026-09-07/liquid-gpu-reconstruction-review.md).
   The captured Troublemaker candidate's
   new bounded3D review now consumes conservative native-face source arrays
   and actually collides with the captured terrain on the GPU. Seven engine
   regressions pass. A separate non-deleting contact candidate substantially
   reduces penetration but still accumulates water at the inlet; fixed-camera
   opacity controls reveal only a narrow liquid strip. Bed penetration and invalid-looking
   SDF presentation prevent acceptance. No production promotion. See
   [terrain source/coupling evidence](../reconstruction-review-2026-09-07/liquid-terrain-sources.md).
   Current implementation and retained failures are in the
   [contact review](../reconstruction-review-2026-09-07/liquid-terrain-contact.md).
   A motion-preserving solid-cell variant was tested and rejected: fewer shallow
   penetrations but worse deep penetrations and continued inlet accumulation.
   See [the motion/contact test](../reconstruction-review-2026-09-07/liquid-terrain-momentum.md).
   Tagged-mesh contact is now implemented in an isolated runtime candidate but
   still fails. Actual GPU queries report stationary terrain and occasional
   proposed36m particle steps, directing work to the fluid update/initialization;
   see [private-contact evidence](../reconstruction-review-2026-09-07/liquid-terrain-private-contact.md).
   The next actual-GPU audit identified a world/grid velocity-basis mismatch in
   the inherited particle transfer. An isolated correction spreads water into
   the window and reduces runaway steps substantially; eight regressions pass.
   Deep penetration, inlet crowding and unrealistic presentation remain. Full
   neighbor gathering was also tested, with mixed results, not promoted. See
   [grid-frame correction evidence](../reconstruction-review-2026-09-07/liquid-grid-frame-transfer.md).
   Registered wet-volume initialization is implemented in a transient candidate.
   The initial lateral-axis interpretation was subsequently found incorrect:
   exposed Back/Front are Y and Down/Up are Z. Current code restores the closed
   floor and open lateral faces; historical flow captures retain the wrong
   boundary settings and are not accepted. Actual GPU seeding works, with
   eight engine and twelve data regressions passing, but the filled-state run
   exposes severe terrain penetration and is not promoted. Next is consistent
   exact-topology terrain contact and pressure classification; see
   [wet-state evidence](../reconstruction-review-2026-09-07/liquid-wet-initialization.md).
   Shared registered-triangle pressure/contact queries now eliminate detected
   bed penetration in both12s and60s full-water GPU runs. Eight engine and
   thirteen data regressions pass. The60s run exposes severe inlet accumulation
   and near-stalled downstream flow; next is actual boundary-flux coupling, not
   more contact-radius tuning. Still no scene promotion; see
   [exact-terrain contact evidence](../reconstruction-review-2026-09-07/liquid-exact-terrain-contact.md).
   Full compiled boundary tracing corrected the recent axis interpretation.
   Fresh corrected-control and two-cell outer-margin captures retain zero
   sampled penetration. The margin reduces analysis-bin crowding from6,827 to70
   at12s but drains the wet state and reverses upstream flow; not accepted.
   Eight expanded engine and thirteen data tests pass. Next: driven native-face
   inflow and outgoing stage/pressure, with storage/exit accounting; see
   [boundary/margin evidence](../reconstruction-review-2026-09-07/liquid-boundary-bindings.md).
   Native-face normal-flux pressure drive is now implemented in an unsaved
   candidate. Actual12s/60s GPU runs restore downstream motion with no detected
   bed penetration, but marker count rises and storage/face flux remain
   unverified. Eight engine and seventeen data regressions pass. Outgoing
   pressure/stage coupling and realistic optics/motion still require work; see
   [driven-boundary evidence](../reconstruction-review-2026-09-07/liquid-driven-boundary.md).
   Live GPU texture readback now verifies boundary velocities and exposes a
   pressure-projection operator inconsistency: at160 diagnostic iterations the
   pressure equation converges but velocity divergence remains. No production
   iteration increase. Next correct compatible pressure/velocity operators and
   their terrain/free-surface boundary support, then repeat transport/storage
   and realism checks. Eight engine and twenty data tests pass; see
   [grid projection audit](../reconstruction-review-2026-09-07/liquid-grid-projection-audit.md).
   A compatible collocated projection now runs on the actual GPU. It also
   preserves pressure-support velocities through the later extrapolation stage.
   At12s final divergence matches the predicted pressure residual within
   half-float storage precision, with zero detected terrain penetration.
   Eight engine regressions pass. This is still an unsaved physics candidate:
   storage/throughput, outgoing stage coupling, optics and performance remain
   unaccepted. See [compatible projection](../reconstruction-review-2026-09-07/liquid-compatible-projection.md).
   A separate native outgoing-stage pressure candidate is now implemented.
   Its nonzero-pressure CPU reference and actual 12s/60s GPU runs now complete.
   All 4,142 external-stage cells match independent classification, with zero
   detected bed penetration at both final samples. Nine engine and 23 data
   regressions pass. A shader substitution retry was diagnosed and fixed;
   V4 remains a failed run. Storage/throughput, optics and visual acceptance
   remain open. See [outgoing-stage review](../reconstruction-review-2026-09-07/liquid-outlet-stage.md).
   A read-only material-graph audit then identified zero base scattering and
   two local/world coordinate errors. Unsaved optical candidates restore visible
   transparent water and correct normals; the depth-frame correction restores
   liquid in an otherwise empty oblique view. The result is still a glossy,
   bounded patch without convincing foam/breakup, not a completed river scene.
   See [optical/frame evidence](../reconstruction-review-2026-09-07/liquid-optics-world-frame.md).
   The final optical/frame engine suite has 10 clean passes; 26 focused liquid
   Python tests pass. A new actual-grid exchange audit shows excessive lateral
   exit relative to the native profile, despite the correct pressure boundary.
   The estimate is not a calibrated mass budget; flow consistency remains open.
   See [exchange-aperture evidence](../reconstruction-review-2026-09-07/liquid-exchange-aperture.md).
   A centered, rotated-grid-aware particle transfer now corrects a half-cell
   sampling bias in an isolated candidate. Matched 12s and 60s GPU tests improve
   downstream momentum and retain zero detected bed penetration; 10 clean engine
   and 34 numerical regressions pass. Pure FLIP was tested and rejected as unstable.
   Actual SDF aperture still shows excessive lateral exit, and the fresh oblique
   image remains glossy/blobby rather than whitewater. No promotion or scene
   acceptance. See [transfer evidence](../reconstruction-review-2026-09-07/liquid-centered-transfer.md)
   and [actual liquid aperture](../reconstruction-review-2026-09-07/liquid-surface-aperture.md).
   Full native-vector inflow is now verified on the GPU in another isolated
   candidate. A 160-iteration convergence A/B removes most pressure error but
   does not fix the lateral-flow mismatch. The active liquid renderer writes
   constant zero to its foam channel; explicit advected foam remains necessary.
   Ten clean engine and 38 numerical tests pass; no scene promotion. See
   [vector handoff and convergence](../reconstruction-review-2026-09-07/liquid-vector-boundary.md).
   Explicit transported foam now reaches the actual single-surface renderer in
   an isolated candidate. GPU readback caught and corrected an SDF-channel
   misbinding and inherited single-channel texture storage that discarded foam.
   A60s run preserves exact sampled bed contact and finite, bounded foam;10 clean
   engine and44 numerical regressions pass. Top-surface foam remains weak and
   the water still looks glossy/pillowy, so this is not visual acceptance or
   scene promotion. A verified two-second native-image animation is retained.
   See [foam implementation and retained failures](../reconstruction-review-2026-09-07/liquid-advected-foam.md).
   A CPU anisotropic reconstruction reference now uses the actual GPU particles,
   with render-only covariance kernels and local-density-normalized weights.
   56 numerical tests pass. Controlled tests reject center averaging for a17cm
   elevation bias. Unshifted kernels preserve prescribed crest amplitude, but
   actual main-body crossings still change11.91cm RMS under grid refinement.
   No renderer integration or resolution increase is accepted. See
   [surface reconstruction reference](../reconstruction-review-2026-09-07/liquid-anisotropic-reconstruction.md).
   A resolution-aware candidate now reaches the real renderer as an offline
   snapshot. Exact-source A/B verifies identical optics and GPU texture data;
   the water still looks rounded/plastic.63 numerical and10 engine regressions
   pass. Live reconstruction, interior consistency, foam and performance remain
   open; no scene promotion. See
   [actual-engine surface comparison](../reconstruction-review-2026-09-07/liquid-surface-snapshot.md).
   The captured Troublemaker candidate's
   reproduced shallow-bank instability is corrected in the current core; the
   600-second one-metre cook and engine replay/contact checks pass. The revised
   normal-paddle test guide has multiple bounded passes and a later 5.10 m
   route-error failure, not broad route robustness. A same-core 0.5 m cook and
   comparison are complete; two-grid convergence remains unproven and the fine
   fields are export-only. Station-labelled captures now expose the actual crux;
   shader-only ripple candidates remain opt-in, not production acceptance.
   A separate captured-XY rock candidate now preserves the original LiDAR
   horizontal positions and has matched mesh/hydraulic sampling, a fresh
   bounded 600-second solve and 254 engine collision probes. Its fixed-bank
   images still show an angular outline and smooth foam; it is not promoted.
   See [the geometry review](../reconstruction-review-2026-09-07/registered-rock-review.md).
   The new persistent GPU detail-water core passes actual-GPU transport,
   wet/dry and captured-flow tests. Its new opt-in single-carrier integration
   has fourteen successful focused tests including existing water-rendering
   regressions. Coordinate caching removes the flow-upload regression, and GPU
   interpolation now removes the stitched fine mesh's recurring CPU-update cost
   without reducing live updates. The next opt-in material now supplies separate
   previous-render-frame water textures, with a passing GPU history regression;
   quantitative motion-vector and long-animation acceptance remain open.
   A further review material replaces duplicate coarse/GPU whitening with one
   transported final-coverage input; its main crest still looks sheet-like.
   A further opt-in candidate now evaluates the same continuous support crest
   on the fine GPU vertices: the running-scene audit found an 18.4 cm maximum
   coarse interpolation error. After correcting normal decomposition, sixteen
   relevant engine tests succeed (one retained engine warning).
   This is a shape-consistency correction, not photographic acceptance;
   its 19.44 ms p95 still misses the unchanged frame-time target.
   Same-grid higher-order detail-wave transport now has analytic/conservation
   tests and two continuous24-second engine recordings. Full-frame analysis
   did not establish an improvement in the smooth foam face; it remains opt-in,
   with a19.50ms p95 and no visual/performance promotion. See
   [the motion review](../reconstruction-review-2026-09-07/detail-transport-motion.md).
   The existing falling-spray option now recognizes the registered map and its
   visible GPU carrier, instead of rejecting all sources through a hidden legacy
   mesh. Five focused tests pass; three wet source footprints emit. The new
   continuous capture still has smooth foam and detached-looking spray, and
   p95 remains19.11ms. This is not promotion or acceptance. See
   [spray integration evidence](../reconstruction-review-2026-09-07/registered-spray-carrier.md).
   A paired live GPU-state/texture audit now confirms that foam-covered detail
   cells usually have only2-3mm added height (p95 below18mm), not a lost texture
   update. Fifteen focused regressions pass; this measurement does not establish
   whitewater realism or identify every bright image pixel as foam. See
   [the height audit](../reconstruction-review-2026-09-07/detail-height-audit.md).
   A final-mask diagnostic confirms substantial simulated foam at the broad
   white face. A remaining independent scrolling coat is now removed inside
   GPU ownership in an opt-in optical candidate; saved-graph invariants pass,
   but the new motion remains smooth and p95 worsened to21.70ms. No acceptance.
   [Foam provenance and optical correction](../reconstruction-review-2026-09-07/foam-provenance-optics.md).
   An opt-in advected activity memory now keeps pressure excitation downstream
   after the local source fades. Sixteen GPU/spray regressions pass; actual
   foam-cell median added relief increases to roughly 5–6 mm, but the inspected
   scene is still smooth and puffy. The 19.44 ms p95 and 9.00 ms solver still
   fail the original gates. No promotion or scene completion. See
   [activity-memory evidence](../reconstruction-review-2026-09-07/activity-memory-review.md).
   Native stage profiling identified repeated primitive reconstruction; those
   values are now reused within each RK stage, with identical exported replay
   fields. The rebuilt engine averages 8.08 ms solver time and 19.00 ms p95
   frame time: improved, still above both gates. Broader regressions expose a
   stale guided-test default, now corrected; its actual traversal still fails
   the 5 m route-error limit at 9.94 m. Both failures are retained, not waived.
   [Native optimization and regression evidence](../reconstruction-review-2026-09-07/native-stage-profile.md).
   The driver now defaults to existing coordinated/current-aware paddle inputs.
   A first full registered-rock-map diagnostic traversal passes the unchanged
   outlet, route, sampled-contact and single-carrier checks (64.43 s, 3.80 m
   maximum route error). It retains an engine warning and is only one bounded
   run, not broad navigation or visual acceptance. Crux captures remain smooth
   and angular; all 26 runs and earlier failures are retained. See
   [registered traversal evidence](../reconstruction-review-2026-09-07/registered-traversal.md).
   A new opt-in, capped persistent secondary-water experiment now inherits the
   sampled current, integrates gravity and transitions returning fragments to
   short-lived surface foam. Eighteen focused tests pass, including a renderer
   history regression for an initial retained scene crash. The completed clip
   shows sparse flecks over a still-smooth foam face; p95 is19.35ms, so no visual
   or performance acceptance. Final GPU ripple attachment and bulk whitewater
   are still missing. See [secondary-water evidence](../reconstruction-review-2026-09-07/secondary-water-review.md).
   A same-forcing 0.25 m detail-grid experiment improves analytic GPU wave
   accuracy (19 focused tests pass), but actual foam relief remains only
   11–15 mm RMS and the inspected foam face stays smooth. Its 18.79 ms p95 and
   7.96 ms solver still fail; no promotion. Current 3D FLIP template inspection
   establishes available assets, not visible liquid or successful coupling.
   See [fine-grid and bulk-liquid evidence](../reconstruction-review-2026-09-07/fine-detail-review.md).
   A project-owned 3D FLIP/SDF fixture now shows a depth-bearing volume from
   multiple angles, with actual GPU dispatch verified after correcting an
   editor-capture scheduling problem. Its sampled Niagara compute scope is
   4.05 ms; the dark cube/jet is not river-ready. A tagged-sphere variant now
   proves primitive collision response through paired GPU particle readbacks:
   no particles enter the inner core at three samples, with shallow surface
   penetration remaining. Two configuration/ownership regressions pass.
   No river coupling, production promotion or realism acceptance is
   claimed. See [the liquid fixture review](../reconstruction-review-2026-09-07/liquid-body-fixture-review.md).
   Fine geometry still does not establish realistic
   macro crest shapes or long-run temporal acceptance. [Realism and the performance
   gates remain open](../reconstruction-review-2026-09-07/stateful-detail-water.md).
   Shoreline, crest/foam animation, robust guided collision
   traversal and frame-time budgets still need acceptance. Verify rapid
   identities and layouts, then migrate the complete 33.334 km candidate route,
   terrain, collision, hydraulic fields and starts together. Production still
   uses the previous route. Follow [the detailed checkpoint](../reconstruction-review-2026-09-07/checkpoint.md).
2. **Colorado — queued after South Fork**, per [its plan](colorado-evidence-reconstruction.md).
3. **Pacuare — queued after Colorado**, per [its plan](pacuare-evidence-reconstruction.md).
4. **Futaleufu — queued after Pacuare**, per [its plan](futaleufu-evidence-reconstruction.md).

Captured source coverage is not measured underwater bathymetry. A diagnostic
map is not the shipping map. Source acquisition, unit tests and finite solver
output alone do not establish physical, geographic or photographic acceptance.

## Other requested work that must not disappear from the queue

- **All-scene water realism:** the earlier scope includes the six shipping
  rivers, so Chilko and Zambezi still require final rendered-motion, shoreline,
  collision and performance review. The ordered four-river reconstruction
  sequence above does not silently close that broader scope.
- **Crew realism:** helmet sizing and seat contact have scoped September 6
  corrections and actual-engine evidence. They are not full character acceptance:
  continuous motion/reentry, garment/vest joins, straps and foot/thwart fit still
  need review. See [helmet fit](../reports/2026-09-06-helmet-fit.md) and
  [seat contact](../reports/2026-09-06-crew-seat-contact.md).
- **Project normalization:** obsolete prototype scene removal and catalog/CI
  ownership changes are implemented. Three Windows/POSIX packaging-fixture
  failures are now fixed with an added missing-execute-bit rejection test;
  28 focused checks pass. Other documented historical source/provenance and
  layout failures remain; do not erase evidence or weaken gates to pass.
  See [maintenance record](../maintenance/project-normalization.md).
- **Final delivery:** run relevant engine and release checks, review accumulated
  changes and captured-data licensing, then satisfy the requested final commit.
  No blanket deletion of historical evidence, source data or active dependencies.

The current pass is working on the first dependency, not claiming completion
of this list or launching later river reconstruction prematurely.
