# Foam provenance and the remaining drift coat

September7,2026 local time. Registered South Fork candidate only. Full goal
active; no scene acceptance, promotion or commit. Prior turn was progress:
paired live GPU measurements established genuinely small added perturbations.

## What the white region represents

`-RaftSimCoverageAudit` selects an isolated unlit diagnostic copied from the
current crest material. Same WPO root and two previous-frame switches, no second
surface. RGB displays final foam coverage, old coarse final coverage, and GPU
resolved foam respectively. `create_coverage_audit_material.py` preserves the
original52194d11...858438f material hash. Setup60530 exit0; build58343 exit0,
4actions25.97s. Diagnostic material/report `coverage-audit-material.json`.

Actual engine capture67960 exit0, log confirms the diagnostic MID and active GPU
detail. `unreal/Saved/Screenshots/FinalFoamCoverageAudit_000.png` inspected. The
broad face is strongly magenta/pink: final red and GPU blue both contribute.
Thus the broad white lit face is substantially simulated foam, not simply a
reflection. Green elsewhere is the old coarse coverage, not the extra drift
coat described below. Display tone mapping means RGB is not a linear coverage
measurement. This is a provenance view, not a realism candidate.

## Remaining independent optical path

Fresh saved-graph walk `audit_foam_consumers.py` / `foam-consumer-graph.json`
confirmed the final foam node controls the main color/roughness branch. However,
an independent scrolling drift signal still drives `LiveDriftFoamOpacity`,
`LiveDriftFoamRoughness` and `LiveDriftFoamSurfaceGlow`. The prior claim of one
complete optical foam authority was therefore too broad. The earlier pair of
GPU additive coats had been bypassed, but this older drift coat remained.

Emissive parameters are already set to zero by the currently used
`RaftSimSurveyLitFoamReview` runtime branch; their nonzero saved defaults do NOT
prove the actual scene is self-lit. Do not repeat that as a new diagnosis.
Audit24170 returned1 despite producing a valid report; qualified, not clean
process success. Follow-up graph inspections15779/20727 returned0.

## Bounded correction

New opt-in `-RaftSimUnifiedFoamOpticsReview` selects
`M_RaftSim_LiveRiverSurface_StatefulCrestReview_OpticsReview`, SHA
**25c159d5d5c5193c04a7d101dd50b63e95baf2257e802853a2ab38f525cc894b**.
Inside the GPU-owned window the independent drift coat becomes zero; outside
it remains unchanged, using the SAME border/4m fade equation and world/basis/
domain/enable inputs as final foam ownership. The authoritative simulated foam
is not perforated, brightened or repainted. Geometry, normal and opacity graphs
are unchanged. Source material and all particle/solver settings remain intact.

The initial edit14215 correctly refused an unexpected fourth consumer; process
returned0 despite Python error, and no candidate file was saved. Additional
inspection found `LinearInterpolate_43.Alpha` outside the live color, roughness
and glow trees. It is preserved, not globally rewritten. Saved refraction root
is null; no claim about that node's unrelated purpose. The scoped edit changes
only three reachable optical parents123/124/125, preserving the original exact
three-consumer constraint within its actual scope.

Build44372 exit0,4actions24.51s. Scoped setup20304 returned1 despite successful
save and valid invariant report `unified-foam-optics-setup.json`; qualification
retained. Fresh-load audit47267 exited0 and passed:
`unified-foam-optics-audit.json` verifies exact ownership-equation equivalence,
shared inputs, precisely the three intended consumers, unchanged WPO/normal/
opacity subgraphs and2previous-frame switches. This is graph verification, not
a fresh full engine automation-suite run or a realism pass.

## Actual motion and performance

Engine76423 exited0, `UnifiedFoamOpticsMotion.log` confirms the candidate MID.
Video `unreal/Saved/VideoCaptures/RaftSim_20260907-203651.mp4`:
696captured source frames,23.930s,718decoded frames. Existing local decoder
exited0, saved unmodified1/8/16/23s frames and full-stream numerical metrics under
`detail-motion/UnifiedFoamOpticsMotion*`. Frames8/23 visually inspected.

The independent drifting flecks are absent, but the white face is STILLsmooth
and the surrounding water now exposes more of its underlying smoothness. Spray
still looks puffy. No photographic improvement or complete natural flow is
accepted. Foam-face image spatial-gradient mean0.74654 versus prior0.99312;
dark-water frame-change mean0.05777 versus1.59645. These reductions reflect
removed visual patterns, not measured fluid speed, less turbulence or an FPS
improvement. Tone mapping/temporal effects and nonidentical particle states are
confounders. Numeric decoding does not mean every frame was watched visually.

Isolated process3583 exit0, no simultaneous recorder/build/decoder:
`survey_performance_unified_foam_optics.json`, same1280x720/87%,RTX3060Laptop,
Development offscreen5s warmup/20s measurement. Mean16.200989ms,p9521.699499ms,
GPUmean6.904269ms,solvermean9.573585ms,onewallhitch; final detailbacklog0.007232s.
This run is WORSE than the prior19.112ms p95; original16.667msframe/1.6mssolver
budgets still FAIL. Do not infer that the material caused the whole CPU increase
or claim a speedup. No repeated run until lucky, promotion or release pass.

## Next work

Do not repeat the foam-versus-reflection diagnosis or glow-default hypothesis.
The mask is present, the tiny perturbation is correctly resolved, and the old
extra coat was hiding some smoothness with unrelated moving flecks. Next work
must implement persistent churning relief/foam and surface-coupled spray using
the actual liquid motion, with bounded energy/forcing and raft support, rather
than more whitening or a second sheet. Keep the optical correction opt-in until
that integrated appearance and performance are validated. CPU cost, geographic
identity/rock shape, traversal and the full ordered remaining queue stay open.
All owned processes in this pass are terminal; no later-river start or commit.
