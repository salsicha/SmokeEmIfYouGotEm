# Landscape foliage source split

Recorded 2026-09-17 UTC. This is source normalization, not scene or release acceptance.

The 8,897-line foliage implementation is now five focused CPP files and one
private header, each below the existing 3,000-line limit. Asset helpers,
preparation, common placement, Pacuare placement, and Zambezi placement remain
in their original execution order. Six compile-time checks preserve the exact
return types of shared placement callbacks. No assets were regenerated and no
installed editor or gameplay module was replaced.

The twelve existing biome test readers now read an explicit six-file source
set. Their 1,234 assertion ASTs are unchanged. Ten new tests cover exact member
selection, missing-member failure, encoding, file bounds, and placement/type
contracts; all ten pass. All five CPP units compiled independently and the
isolated editor module linked successfully. The final standard-library type
guards were recompiled and linked successfully as well.

The broader source/historical suite reports 91 passed and 25 failed, with no
skips. It is not a clean regression run. Its overall source-bound test still
fails on the existing MaterialsBase and PhotorealMaterials limits, although
the foliage files now satisfy the original bound. Historical hashes and
runtime-water assertions were not weakened to manufacture passes.

Local evidence remains under ignored `tmp/`: the extraction preservation and
assertion reports, `landscape-foliage-source-suite-v1-20260917.xml`, and
`landscape-foliage-split-v1-20260917/` compile/link outputs. Trailing whitespace
was removed before commit; no binaries, temporary captures, or credentials
are included. Existing ignore rules already cover these outputs.

## Background results at this checkpoint

The standalone six-phase transport compile completed successfully. All 18
original transport fixtures pass on hardware and WARP; the 13 actual harness
tests pass with no skips. This does not qualify pressure or the full RK2 step.
The original engine SM5 replay remains live and its inputs remain untouched.

The original hydraulic continuation completed at 1,800 seconds. State and
86,720 dry-bank checks pass, but settling is not accepted: outflow is
92.233295 m3/s versus inflow 45.306955 m3/s. No snapshot was promoted and no
further continuation was started. Last ordinary performance remains
27.068531 FPS / p95 43.391 ms, failing the 30 FPS target. Terrain, convincing
wave/froth integration, all-scene qualification, crew, and release remain open.
Troublemaker remains a rapid within South Fork, not a separate menu scenario.
