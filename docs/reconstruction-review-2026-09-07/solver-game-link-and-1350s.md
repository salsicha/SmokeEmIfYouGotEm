# Solver game integration and 1350-second hydraulic checkpoint

September 16, 2026. This advances the existing South Fork integration; it does
not establish finished reconstruction, packaged play, convincing breaking/froth,
settled hydraulics, full-hull default acceptance or 30 FPS.

## Tested solver is linked into the Game target

The Win64 Development **Game** build succeeded in 449.07 seconds, with two
compile workers. The separately loaded editor was not rebuilt: hashes of all
17 project/plugin editor DLLs match their pre-build values. The existing package
cook continued against those unchanged DLLs. The old game executable and target
receipt remain in `tmp/solver-rows-game-baseline-v1-20260916`.

Current game executable SHA256:
`23733e944338a0c013bef38f53d96a68ed63c691d5da4c52c6576e8f0d4809b1`.
Its embedded solver archive identity was independently located in the binary:
`d2139f1b4d95814786162dd15dcb1e3509d3225d0df6f2059b95d099ca6113b9`.
Target receipt SHA256 remains
`7c21a33677521da69e67d67e31b69b077f14d66e701966ffe9d759a0bcf973dd`;
receipt equality alone therefore cannot prove executable equality.

Build record: `tmp/solver-rows-game-build-v1-20260916.json`.
Build log: `tmp/solver-rows-game-build-v1-20260916.log`.
The prior native tests and two bit-exact replay comparisons are recorded in
[the solver review](retained-preview-and-solver-rows.md). The Game build does
not replace those tests with a compilation-only claim.

Fresh staged-runtime verification passes all **2,405 files / 916,906,778 bytes**,
with no external source fallback. Bundle manifest SHA256:
`73736ed3459fcbd72e5a9d583d221346662cd03fe137b6d7c2290ff0c421daa9`.
Report: `tmp/solver-rows-game-runtime-bundle-v1-20260916.json`.
This is the saved scene's existing route/hydraulic bundle, not promotion of
the newer landward candidate or the still-running hydraulic continuation.

## Fresh hydraulic evidence

The same process, PID18716 / session69416, produced local step3000 at absolute
1350 seconds. Input SHA256 remains
`189e14a252e3a9ad2f698a33129875521845ac71cc809b183ac91e2a1131ff37`.
All 5,369,600 cells pass the finite/conservation audit, and all **86,720**
artificial-bank face cells are exactly dry. No gate was relaxed.

- Maximum depth: 4.553026921 m; maximum speed: 7.134428487 m/s.
- Water volume: 3,015,606.069268 m3.
- Maximum per-step conservation residual: 1.378528425e-8 m3.
- Physical outflow: 80.573709962 m3/s; inflow: 45.306954547 m3/s.

The inflow/outflow imbalance means **settling is not accepted**. Reports:
`tmp/south-fork-context3-1350-snapshot-v1-20260916.json` and
`tmp/south-fork-context3-1350-banks-v1-20260916.json`.
At this review the same process is live at local3450 / absolute1372.5 seconds.
Next completed checkpoint: local4000 / absolute1400, both cell and bank audits.

## Package and visual work remain open

Cook PID16144 / session80881 is directly verified live. The very long original
SM5 batch completed, including one 3502.478-second shader; later debug-output
shader compilation is also advancing. Remaining shader workers were confirmed
children of that same cook. They are not abandoned workers to terminate.

After this same cook finishes, compare the archived executable with the new
Game hash above. Restage without recooking if the archive retained the old
game. Verify the archive's entire runtime bundle, then run the real non-editor
`RaftSim.AuditGroundSources` command and require all 444 distinct expected
identities and `editor_only_data=false`. Exit code alone is insufficient.
Editor relinking remains pending until its cook releases the DLLs.

The actual decoded 16-second gameplay frame was inspected again. Broad white
cover and abrupt rock flanks remain unaccepted. Source inspection confirms
the cap builder already inserts unused original returns into overlong
triangles without relaxing the one-metre adjacency prior. No claim is made
that unused points can repair all missing flanks; no source points, geometry,
material or hydraulic fields were changed in this checkpoint.

Last uncontended ordinary performance remains **17.819710 FPS / p95 81.6343 ms**,
failing the unchanged 30 FPS / p95 33.333333 ms gate. No competing-job measurement
is substituted for it. Colorado -> Pacuare -> Futaleufu, all-scene water,
crew, physical regressions and release checks remain open. Troublemaker is
still only a rapid within South Fork, not a scenario/menu entry.
