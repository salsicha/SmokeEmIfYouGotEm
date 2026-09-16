# Paired terrain and water in actual South Fork play

2026-09-16. Actual unsaved FullReach play now retains the revised terrain and
source-matched water together. This is not normal-menu delivery, calibrated
bathymetry, accepted breaking/froth, or a 30 FPS pass. Troublemaker remains only
a rapid within South Fork.

## Integration correction and actual evidence

The native preplay fixture repeats all 64,935 collision probes, all 803,842
directed terrain-triangle comparisons and 25,600 paired-water queries. Its
report SHA256 remains `727ed3bb99f192a9b7eebd3045e46254c58de2929d46a4a9c654b458200aa7f4`.
The actual play-world check then independently requires exactly one revised
ground actor, no original ground actor, one tagged rock solid, and the exact
paired water configuration before allowing capture.

Two integration errors prevented that comparison initially:

- `-ExecutePythonScript` closes the editor when asynchronous setup returns.
  Use `-ExecCmds="py ABSOLUTE_SCRIPT_PATH"` for the slate-callback harness.
- Calling `SetStaticMesh` without marking the external actor modified left
  World Partition free to reload its old saved mesh. UE's
  `WorldPartitionStreamingGeneration.cpp` selects dirty packages for unsaved
  PIE duplication. The harness now calls `modify()` on the verified original
  actor/component and paired configuration. It does not save them.

The v6 run explicitly found zero revised actors and one old actor and refused
capture. V7 proved the correct play-world binding but failed on JSON logging
of a native delegate handle. V8 captured all three images and a video, then
crashed during editor shutdown: its earlier capture-complete report is NOT a
successful process result. All failures remain retained.

V9 uses the supported end-play request before closing the editor, destroying
the game capture's process-exit timer with its world. Session13580 terminates
with exit0. Its report records `play_session_ended=true`; no Python error or
fatal shutdown error is logged. The source-matched 50-second atlas remains
unchanged. The new native C++ v2 loader is **not** exercised by this Python path.

Actual captures occur at world seconds15.645,25.403,35.340 and downstream
stations8341.161,8349.478,8356.479. Fixed camera(-545900,-362700,2000)cm,
pitch-35.27/yaw46.85, FOV90. Shared full-hull/render checks log maximum error0;
these bounded observations do not establish all-route contact acceptance.

Despite launch arguments1280x720, the docked PIE viewport actually rendered
1014x550. The harness now reads the PNG dimensions and explicitly records
`capture_resolution_matched=false`. No performance or resolution-matched
visual acceptance is claimed. The recorded clip has90 source frames over
20.871 seconds; decoding yields626 encoded frames with increasing timestamps.
Encoded30Hz is not game FPS. Five unmodified video frames are retained in
`tmp/control-ablation-pie-v9-motion-20260916`; 5s/15s frames were inspected.

Compared with the retained original-bed1700s image, the large central bowl is
absent from this capture. Short steep/streaked bank-side faces and broad,
smooth white coverage remain. This is not a controlled same-age/resolution
A/B or proof that removing the inferred shelf/plunge gives the correct rapid.
The earlier bank-side reference shows separated rock-controlled drops and
irregular froth; the new result still does not meet that visual target.

All456 saved actor packages match the baseline. Of eight other protected
identities, six are unchanged and two match the already verified CPU-source
retention revisions. No map, actor package, shader, DLL or executable is saved
or rebuilt by this comparison. Evidence paths are ignored, not redistributed.

149 focused regressions pass, including11 callback/report guard cases. Those
fake-engine callback tests cover mismatched ground/water, bounded streaming
waits, nonserializable handles, explicit end-play sequencing, dimension
reporting, changed/missing packages and fresh in-project evidence paths. They
do not substitute for the separately recorded actual engine run.

## Fresh full-domain checkpoints

Both100s and150s pass all5,382,400 state/conservation cells and all86,720
exact-dry artificial-bank faces, with unchanged four physical boundary faces.
At150s maximum depth3.952322866m, speed12.168753620m/s and maximum step volume
residual1.376285619e-8m3. Outflow25.204575995 versus inflow45.306954547m3/s
still precludes settling acceptance. No evolved old-bed state was transferred.

| Local evidence | SHA256 |
| --- | --- |
| `tmp/control-ablation-100s-state-v1-20260916.json` | `b0bafddc0598d8a6e0b5059ce38aca59fb746fbef679514f978e0afbbbaab572` |
| `tmp/control-ablation-100s-banks-v1-20260916.json` | `a22f5e29662feb9289dbb5f17fd884cc8eb54c0a7a9075a3c10420368e236955` |
| `tmp/control-ablation-150s-state-v1-20260916.json` | `7addbe0b649a1de4fde610402764020cf494edea01b3af2f6f3867fa66ef681c` |
| `tmp/control-ablation-150s-banks-v1-20260916.json` | `781cae473d647e715f2ebdb4f4c647d4c318231112b852dc5cff135b6d83c067` |
| `tmp/control-ablation-pie-v9-20260916.json` | `94b9abb5fb635b4d62b0269b940b924cbe8d5a12ac8657d8765c1e11c763ba00` |
| `unreal/Saved/Screenshots/control-ablation-pie-v9-20260916_002.png` | `d092caf0e85080c8bcac95e036874be86db5b1092b4e7bf6351ecc05fb05ee8d` |
| `unreal/Saved/VideoCaptures/RaftSim_20260916-102046.mp4` | `60cba573ae8b537e61cdd07bc7177a152f4a4671bfd1e70e16e9193b85890820` |

## Required next work

Preserve full solve46094/PID22940; next checkpoint4000/200s needs BOTH audits.
Preserve package83678/cook5852/shader35032, confirmed live with increasing CPU;
do not restart from the recurring compiler warning or replace its DLL/shader
inputs. After terminal completion verify archive coherence,444 non-editor
source identities and2,405 runtime files. Then link/test the new native v2
loader and1280x720 actual-game playback. In particular, verify its requirement
that the original rapid actor is loaded before `StartPlay` applies the pair:
the PIE inventory shows the actor arriving after initial game startup. Do not
weaken that guard or accept a mismatched water/terrain interval.

The full scenario still needs settled source-matched hydraulics, convincing
breaking/froth, physical traversal and uncontended30FPS/p95<=33.333ms before
normal-menu promotion. Last uncontended17.819710FPS/p9581.6343ms remains FAIL.
Colorado -> Pacuare -> Futaleufu, Chilko/Zambezi/all-scene water, crew realism,
normalization, regressions and release checks remain open.
