# Exact-coordinate crest lookup — September 13, 2026

The normal South Fork FullReach path now uses a direct full-precision coordinate
hash for its parallel crest-selection memo tables. Same-input selection is about
7% cheaper; **whole-game improvement and 30 FPS are not established**. The latest
ordinary capture is12.674492 FPS/p9586.7254ms with growing fixed-step backlog.
The same-build original-lookup run is13.140796 FPS/p9584.5586ms. Those different
trajectories/workloads cannot establish a causal whole-frame gain.

## Change and exactness

The engine's default FVector2D hash calls a general memory CRC. The replacement
mixes its two double-precision words directly. It keeps full keys and exact
FVector2D equality; signed zeroes share a hash. There is no coordinate rounding,
welding, height interpolation, changed sampling tolerance or persisted hash.
Collision resolution remains the map's exact equality check. Every new build
still invalidates sampled heights through the existing epoch, even when retained
coordinate slots are reused. Each parallel batch exclusively owns its map.
Three refinement levels and the0.5cm selection threshold remain unchanged.

`-RaftSimLegacyCrestCoordinateHash` retains the original parallel lookup as a
same-build control. Serial reference selection remains independent. Physics
timesteps, four-tick frame work limit, debt retention, water/detail clock handling,
solver budgets, mesh density and quality are unchanged. The experimental total-
depth PDE is not promoted by this lookup change.

New native `RaftSim.M4.ExactCoordinateMap` covers27,650 distinct keys including
adjacent representable doubles and subnormals, last-writer semantics, signed
zeroes and reset. The existing28-frame `CrestMemoEpoch` fixture now compares
current profiles/crops against BOTH independent serial and legacy parallel
selection:37,187 expanded vertices, exact parent arrays, triangle order and
ownership. No old profile value is retained across an epoch.

Build48170 CLOSED0 in151.98s. Native30622 CLOSED0,84 clean passes21.125994s.
Adding optional diagnostics initially failed build59425 because a UE_LOG macro
needed braces around its conditional; fixed, not suppressed. Final build36854
CLOSED0 in17.47s. Final native56267 CLOSED0, **84 clean passes**, zero warnings,
failures or unrun tests,20.592167s:
`tmp/south-fork-coordinate-hash-native-v2-20260913/index.json`.
All six previous GPU fixtures supplied unchanged. The two existing D6 damping
double-to-float compiler warnings remain in the broader rebuild output; these
are distinct from the clean native automation result. No CPU solver equations
changed; the preceding261-test CPU result is historical, not rerun here.

Initial runtime Raft DLL SHA256:
`b68ceede9a2eeb6dc54f59ab374c78dff25897262e88f2a136a3e1ef29294b9d`.
Final, optional-diagnostics Raft DLL SHA256:
`3da788a90f0ee6ef2b3d248ff5e14ede63e02f4b5e175c4965d9b26c3069fbc2`.

## Actual same-input comparison

`tmp/south-fork-coordinate-hash-paired-v1-20260913.json` passes. Actual game
frame120 supplies52,047 source vertices and18,946 triangles; both paths generate
the same16,074 midpoint parents. Two warmup pairs precede eight measured pairs
with alternating execution order. Every pair has exact parents, triangle arrays
and source ownership. The immutable height callback and coordinates are identical.

| Pair | Direct hash ms | Original CRC ms |
| --- | ---: | ---: |
| 0 | 12.182198 | 12.880199 |
| 1 | 12.316398 | 12.880102 |
| 2 | 11.811201 | 12.822799 |
| 3 | 12.054898 | 12.898598 |
| 4 | 11.863701 | 13.035502 |
| 5 | 11.837099 | 12.955200 |
| 6 | 11.885300 | 13.078801 |
| 7 | 12.154501 | 12.718502 |
| Mean | 12.013162 | 12.908713 |

All eight are lower, mean reduction0.895551ms/~6.94%. Sampling means are
11.362624/12.217000ms; assembly0.437126/0.475450ms. These repeated identical
inputs reuse topology after warmup. This is not changing-topology performance,
whole-frame performance, GPU solver capacity or release qualification.

The additional optional stage breakdown in ordinary changing frames60–240,
excluding benchmark frame120, shows180 samples: selection-scope13.704372ms,
sampling10.771742ms, assembly1.524397ms, input preparation0.190689ms. The enclosing
scope also includes setup/telemetry overhead. Vertex work3.713238ms and normals
1.200922ms are separately measured. Sampling, not assembly, remains the main
crest target. An earlier detailed pre-change capture separately measures surface
foam/publish5.144812ms; that combined stage needs a narrower timing before
attributing all its cost to foam transport.

## Playable verification and remaining limits

Five profiling wrappers6459/4460/23869/7481/16065 all CLOSED0 without timeout;
every identity-verified cook suspension/resume returns0. No heavy build/test or
replay overlapped these gameplay profiles. The paired comparison itself is
explicit diagnostic work, never used as ordinary FPS evidence. Known editor
Python startup errors for unavailable AgentSkill/PythonTestRunner remain logged.

Uninstrumented captures use1280x720, target metadata30, rows60–240 (181 samples):

- Default:12.674492 FPS/p9586.7254ms, surface52.634742ms, crest22.396291ms,
  selection13.061997ms, four water calls16.606407ms per frame.
- Original lookup:13.140796 FPS/p9584.5586ms, surface50.662846ms, crest22.000380ms,
  selection13.365510ms, four water calls16.290276ms per frame.

These scopes are nested/inclusive; do not sum them. Frame reports:
`tmp/south-fork-coordinate-hash-{default,legacy}-frame-v1-20260913.json`.
Default CSV SHA256 `9a4da980c31838a99506e6988e7e8a00cd1de23652e718fca553f30abd79405b`;
legacy CSV `e51bb26bc2a453fbfe9da0d390d541c5669b8482cc55abe47d8dcad4b2123b20`.
CSV files are under `unreal/Saved/Profiling/CSV/` with those matching run labels.

Default selected frames execute724 fixed ticks with zero failed ticks. Native,
bridge and adapter times agree at CSV precision. Debt grows1.5400to3.7423s;
end water/detail28.266668141s versus frame elapsed34.080596950s, detail backlog0.
Four exact detail remaps, zero teleports,424 frame copies and zero busy-ring
skips. Real-time capacity is still failed; no time discard was restored.

Actual geometry/contact audit7481:

- `tmp/south-fork-coordinate-hash-crest-v1-20260913.json.cartesian-mesh.json`:
  1,550,592 sevenths samples on50,525 submitted triangles, maximum target crest
  error0.593484947cm below unchanged2cm gate; correction tracking0.001626134cm,
  source vertex change0. This is not full shaded/motion acceptance.
- Carrier/detail reports with matching prefix: same frame125,2020 wet points,
  946 affected by detail, zero unavailable, maximum support error4.766563e-5cm;
  4226 GPU queries, maximum RGBA error2.980232e-8, pass.

The ordinary screenshot was inspected:
`unreal/Saved/Screenshots/south-fork-coordinate-hash-default-v1-20260913.png`, SHA256
`a9ce27ceca5a9b35e8e357baba2d0b4df8ca3570166259b84db6ee9a83b6f322`.
Broad glossy folds/blanket-like foam and unfinished terrain/vegetation/crew remain.
No visible realism improvement or reference-motion match is claimed. Protected
map, transmission material and save hashes remain unchanged. No Troublemaker
menu entry added. Reference clips remain requested; no new footage viewed.

The same cook84534/PID32144 reaches4400/local8000; BOTH finite-state and exterior-
bank audits pass (5,382,400 finite cells,86,720 artificial-face cells exactly dry).
Outlet102.245200001 versus inlet45.306954547m3/s is still unsettled. Runtime600s
unchanged; next4500/local10000 needs BOTH audits after its complete marker.

## Next work

Reduce actual current-profile sampling and remaining CPU surface work. Inspect
which profile-key fields really change the height function: current keys include
spilling fraction even though height-only evaluation does not consume it, but
do not reuse old heights unless the entire actual height function is proven
unchanged. Current geometry also moves, so simply skipping builds is invalid.
The existing per-vertex foam transport is independently writable except for its
ordered sum/max reduction; a parallel pass can preserve those reductions in
serial order and compare every actual output against a serial control.

Also finish clock integration: `RaftSimWaterSurfaceActor.cpp` still computes
legacy foam delta from `FPlatformTime::Seconds()` and clips to0.5s, independently
of committed water. Its zero-delta attack fallback also advances generation.
The previous committed-detail fix did not cover that path. Address it explicitly,
preserving first-frame/reconfigure/spatial-handoff semantics and paired transport.
Persistent total-PDE ownership, stable continued boundaries, breaking/froth,
terrain/rapid integration, later rivers, crew, release and final commit remain.
