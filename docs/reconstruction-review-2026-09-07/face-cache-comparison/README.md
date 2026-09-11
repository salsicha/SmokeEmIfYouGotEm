# Solver face-reuse comparison

Three alternating baseline/candidate pairs, 100 steps each, same one-metre
survey scenario and solver settings. Every saved CSV is bit-for-bit identical
in every pair. The median wall time including output is 9.636 s baseline and
9.133 s candidate (5.2% lower); this is a small native benchmark, not engine
FPS, convergence or physical/visual acceptance.

The report and process logs retain the exact commands originally run. To keep
large generated frame exports out of documentation, their six output folders
were subsequently moved without alteration to
`tmp/south-fork-face-cache-20260907/{0,1,2}-{baseline,candidate}`. Nothing was
deleted. The baseline binary and source are preserved in that same scratch
directory. Reproduce using `physics/scripts/compare_south_fork_solver_optimization.py`
with a fresh scratch output directory; the script refuses to overwrite one.

The engine build initially reported success with zero build actions despite a
newer static solver archive. Its water DLL was still dated 19:10, versus the
archive at 21:14 local time. An archive content hash is now a public module
compile definition, in addition to `ExternalDependencies`, so all consuming
modules recompile and relink when that archive actually changes. This prevents
an old linked solver from masquerading as a successful optimization build.
