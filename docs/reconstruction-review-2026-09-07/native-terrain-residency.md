# Native paired terrain activation before play

2026-09-16. The exact new C++ paired loader now succeeds in an actual1280x720
game process through an explicitly loaded temporary test module. Existing
project/plugin DLLs remain unchanged because the package cook is still live.
This is not normal-menu delivery, shipping-package acceptance or water realism.

## Startup and residency correction

The previous v2 loader required the original rapid actor to be already loaded.
Actual PIE showed that World Partition streams that actor after initial game
startup. The correction preserves the loaded-actor gate rather than bypassing
it: after source-hash and native-geometry verification, it adds a streaming
source covering the original terrain's transformed bounds and blocks until
those cells are activated, before any paired terrain or water mutation.

The original actor, transform and material must still match. The real water
loader must still accept the exact paired atlas before terrain/water changes.
Failure destroys the local streaming registration; it does not install water
against the old terrain. Success retains this extra source until world cleanup
so unloading/reloading a runtime cell cannot silently restore the old saved
mesh. Existing player streaming sources and global loading ranges are unchanged.
No second terrain sheet is created and no map/actor package is saved.

The actual verified footprint has center(-543207.84,-360087.85,3217.72)cm and
radius22821.197cm. The provider forces horizontal coverage, activates cells,
and is released on world cleanup. Long-distance leave/return coverage and the
normal project-DLL call site still require follow-up; a short capture does not
prove every streaming lifecycle case.

## Isolated native execution, not a replacement cook input

The implementation compiles with the project's existing C++20/PCH flags into
`tmp/terrain-residency-compile-v1-20260916.obj`, with no MSVC diagnostics. A
temporary module under `tmp/native-terrain-residency-v1-20260916` links this
same object against the existing engine/project import libraries. The link
response replaces the project unity object, redirects both DLL/PDB outputs
into tmp, and never writes the normal module manifest or project descriptor.

The explicit `-PLUGIN=.../RaftSimTerrainResidencyHarness.uplugin` and
`-EnablePlugins=RaftSimTerrainResidencyHarness` arguments load only that new
test process's module. It invokes the real `Apply` function from the global
actors-initialized callback before BeginPlay. This is earlier than the normal
GameMode `StartPlay` call site, which remains a separate integration check.
All22 existing DLL/executable/module-manifest identities match the before-run
snapshot, and all464 protected source/map/actor identities remain unchanged
or match the two previously verified CPU-retention-only revisions.

Native test session77816 exits0: `RaftSim.M3.TerrainResidencyBoundsCandidate`
passes nine assertions for bounds, registered center, activation, full
footprint coverage, blocking and rejection of invalid/degenerate bounds.
Equivalent assertions were added to the repository's native contract test;
its normal project DLL has not yet been relinked.149 focused Python tests pass.

Actual game session62052 exits0. Its log explicitly records the original actor
resident, the revised mesh installed, and `ISOLATED_NATIVE_TERRAIN_PAIR passed=1
begun_play=0` before water BeginPlay. The raft's actual surface-sweep source
then builds from all803,842 terrain triangles. The source-matched50-second
atlas and unchanged rock solid are the same ones verified before the PIE run.

Three1280x720 captures occur at world12.477/22.165/32.251 seconds, downstream
stations8339.555/8348.379/8355.991. The fixed comparison camera remains
(-545900,-362700,2000)cm, pitch-35.27/yaw46.85, FOV90. Shared hull/render logs
report maximum error0. The video contains117 source frames over24.816 seconds;
all744 encoded frames decode with increasing timestamps. No game FPS is
inferred from the30Hz encoding. Unmodified5s/15s frames and screenshot002
were inspected: broad smooth froth and short bank-side streaked faces remain.
The central deep-bowl defect is reduced relative to the older1700s image,
but different flow ages still prevent controlled physical/visual acceptance.

The game log retains editor-tool Python startup errors (`AgentSkill` and
`PythonTestRunner` unavailable in game mode); native activation/capture still
completes. The null-RHI contract run also retains engine/plugin warnings.
These are not claimed as a warning-free release run.

## Evidence identities

| Local artifact | SHA256 |
| --- | --- |
| Native implementation source at test time | `87605f0a29e0bde1af6fb44d63465b3fcc16bbba0a86455508c990ce45d672b9` |
| Isolated implementation object | `5f103fc2ddea3f4e5eae8dcb7ac838ed8f91f9ee2a55f656ce90533186685168` |
| Temporary native test DLL | `c6045fb2cbd3e7b3d70d8b059d7d4ae4bbf7218122a7d03c995dc0168d0bdc99` |
| `tmp/native-terrain-residency-v1-20260916/native-play-v1.log` | `843b6d97d290957343e2d1633747998f250c5ac23a372fc9dbe9652f6e601074` |
| `unreal/Saved/Screenshots/control-ablation-native-v1-20260916_002.png` | `3909d9a8a1cc79b79db675ce8e9298446ef6d5df07c59fa4fbb91867be9274ca` |
| `unreal/Saved/VideoCaptures/RaftSim_20260916-103824.mp4` | `ba9f76df07254fe2cba2286dbbb08a2c2acbc17660f4c0b20b5ccfa294871a69` |
| `tmp/control-ablation-200s-state-v1-20260916.json` | `678d6ce872efcccb7b9dde3752c3aa2af7bca2a964719d4b21c51a2609869caa` |
| `tmp/control-ablation-200s-banks-v1-20260916.json` | `5f7ab7589f07a136521d95d6768426eaae6ac9f13b84e52eb175c223df920bda` |

## Still required

Full-domain200s passes all5,382,400 cells and86,720 exact-dry artificial-bank
faces. Maximum depth4.347480938m, speed12.111856477m/s; max step volume
residual1.376285619e-8m3. Outflow20.062054561 versus inflow45.306954547m3/s
is still unsettled. SAME solve46094/PID22940 remains live; next5000/250s needs
BOTH state and bank audits. Original-bed50s sources exist under
`tmp/south-fork-landward-runtime-50s-v1-20260915`; verify source/forcing/cap and
current retained native identities before using them for a same-age comparison.

SAME package83678/cook5852/shader35032 remains live with increasing CPU.
Preserve its inputs, then verify archive identity,444 non-editor sources and
2,405 staged runtime files. Relink the actual project DLL when safe and test
the normal v2 GameMode call site, streaming leave/return, physical traversal
and eventual normal-menu delivery. Do not replace the pending cook's binaries
with the temporary test module.

Breaking/froth realism and uncontended30FPS/p95<=33.333ms remain open; last
17.819710FPS/p9581.6343ms is FAIL. Colorado -> Pacuare -> Futaleufu, other-scene
water including Chilko/Zambezi, crew realism, normalization, regressions and
release remain open. Troublemaker is a rapid within South Fork, not a scenario.
