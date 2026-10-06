# Same-forcing finer detail grid — not accepted

The opt-in `RaftSimFineDetailReview` experiment retains the same 64 m domain,
hydraulic input, pressure-head forcing and shared support crest. It changes the
detail grid from 128² at 0.5 m to 256² at 0.25 m, and the conforming presentation
mesh from 0.375 m to 0.1875 m. The complete original flow/source field is bilinearly
upsampled; this is **not** a finer hydraulic cook or newly measured terrain.
Texture borders stay at −32.25 and 31.75 m. The material's two ownership masks
now bind the actual half-cell size; current/previous displacement paths remain.

## Verification

- `engine-fine-detail/index.json`: 19 clean engine test successes. The new actual
  GPU periodic-wave fixture uses the same 3 cm, 4 m wave, domain, time step and
  one-second duration. RMS error drops from 8.940 to 2.147 mm; retained amplitude
  rises from 17.418 to 27.878 mm. These are numerical, not photographic results.
- `fine-detail-material-audit.json`: saved graph differs only in two half-cell
  bindings and one scalar parameter. Material creation exited 1 after transient
  unconnected-pin warnings; a fresh saved-asset audit exited 0 without failed
  shader compilation. Both outcomes are retained.
- `fine-detail-snapshot/live_*`: three full GPU snapshots. Actual foam-cell
  added-height RMS is 11.22/12.27/15.06 mm, versus 10.98/9.28/11.97 mm in the
  earlier activity-memory run. Four times as many cells is not four times the
  physical area. These are single observations, not a controlled statistical
  visual comparison or the total macro-wave height.
- Actual recording `unreal/Saved/VideoCaptures/RaftSim_20260908-004029.mp4`,
  summarized under `detail-motion/FineDetailMotion*`: inspected 8 s and 23 s
  frames still show a broad smooth foam face and angular terrain. No promotion.
- Separate `survey_performance_fine_detail.json`: 13.287 ms mean frame,
  18.795 ms p95, 7.632 ms mean GPU, 7.965 ms mean solver, one >33 ms wall-clock
  hitch. The original 16.667 ms p95 and 1.6 ms solver gates still fail.

The finer mesh contains about 128,000 vertices in one section; no second water
sheet was introduced. Production map, project descriptor, original optics
material and native archive hashes remain unchanged. The secondary-particle
flag was deliberately off in this experiment. This remains an optional review
configuration, not a performance or visual fix for all scenes.

## Next bulk-liquid investigation

Read-only inspection of current Windows UE 5.8 Niagara Fluids templates is saved
in `liquid-template-inspection.json`. Splash, Hose, Pool and Coupled all load and
report ready; their graphs contain particle/grid pressure stages and surface
renderers. Enabled renderer flags alone do not establish visible liquid or an
active rendering mode. The inspector saved no assets and the project descriptor
was not changed. Its editor ignored the queued Quit command; after the report
was saved, the exact owned process was explicitly closed (exit 1), not recorded
as a clean process success.

The historical V9 trial was on Mac and rejected direct stock-template reuse in
a small contact volume because it produced no visible liquid body. It does not
prove that all project-owned FLIP rendering/coupling is infeasible. Equally,
loading these templates now does not overturn that failed trial. Inspect the
selected rendering path, then establish visible bulk liquid and bounded cost
before attempting river coupling. Do not increase particles or resolution and
call a smooth foam sheet realistic.

### Renderer binding follow-up

`liquid-template-bindings.json` now includes renderer enable/visibility bindings,
embedded graph inputs, static and ordinary rapid-iteration values, and the shared
`Grid3D_FLIP_FLUID_CONTROLS` module. Screen-space, dynamic-mesh and direct-SDF
renderers are gated respectively by `UseScreenSpaceRendering`, `UseMeshRendering`
and `UseDirectSDFRendering`. The shared module computes them from an enum selector
linked to `Module.Rendering Method`; all three are not simultaneously active
just because their renderer properties say enabled. The enum is
`/NiagaraFluids/Enums/ENiagaraFLIPRenderingMethod`. The module contains a default
`NewEnumerator0`, but its exact output-pin association and the compiled system's
selected version still need explicit verification; do not infer an active mode
from that anonymous default pin alone.

The Hose GPU script's recorded external-collision switches (mesh, Landscape,
global distance field, depth map, geometry collection and particle) are all zero.
That is further reason not to treat the stock template as river-coupled water.
No liquid system was spawned or promoted in this inspection.

The final native inspector build and selector run exited 0. Intermediate full
graph/controls runs exited 1 despite saved reports and normal shutdown; their
logs remain. Two Python reflection attempts also failed on non-exposed private
fields despite process exit 0. That short-lived helper was removed; the working
native inspector replaces it. Existing assets were not deleted or changed.
