# Regional contact bindings — 2026-09-10

South Fork remains incomplete. This pass installs the actual captured contact
pages into regional Niagara programs and verifies their GPU terrain classification.
It does not establish wet cross-region flow, shared boundary conditions, visual
realism, or gameplay performance. Previous pressure-exchange turn was progress.

## Changes

- Added explicit canonical-world mode to the shared exact-triangle query:
  world-to-source and source-to-world reflect Y once, without consulting the
  legacy window's mutable geographic translation. Default legacy behavior remains.
- Extracted the primary particle terrain-projection installer from the existing
  review command, so regional and legacy paths share the same contact code.
- Added `RaftSimInstallRegionalLiquidContact` for unused transient regional
  allocations. Requires the matching v3 page ID and matching region origin/grid
  dimensions; rejects saved assets and assigned/live systems. Binds original
  packed triangle bytes to both primary contact and pressure classification.
- Installs rotated grid-local/centered P2G gather and disables the inherited
  placeholder solid-cell particle deletion. This is not conservative inter-region
  P2G reduction, APIC installation, or particle ownership transfer.
- Removed the pressure module's additional Landscape height fallback in the
  regional path. It could override captured triangles, and its inherited shader
  did not gate height use on the Landscape validity output. The regional terrain
  classification now has one authority: the captured triangle page. Legacy
  behavior is unchanged and was replayed after the refactor.
- Added optional `-RaftSimRegionalContact` to the native all-region stage probe,
  plus blocking native boundary-grid readbacks before owned actors are destroyed.
  `audit_liquid_regional_contact.py` compares those masks against an independent
  float32 query of the prepared source triangles. It does not compare a generated
  mask with itself or use an average-error allowance.

## Verified evidence

`liquid-regional-contact-bindings-v2` ran all twelve real regional allocations
with contact enabled and **zero initial/source water**. There were 1,518 aligned
groups and 1,160 pressure halo exchanges across all 5,960 shared columns. Every
halo address still matches the independently prepared geometry.

Its `contact_audit.json` checks **1,587,600 physical-interior cells** across all
12 regions. Every GPU solid/empty classification matches the preserved terrain,
with zero classification tolerance or mismatches; all wall velocities are zero.
All physical XY columns are checked. The two numerical Z-border layers at each
end and XY halo cells are deliberately excluded: this audit does not establish
their exterior/shared boundary behavior. It also does not execute wet primary
contact or prove sub-cell collision accuracy from a cell mask.

Final build 45675 succeeded. `engine-liquid-regional-contact-v1/index.json` has
four passing actual-RHI tests in 11.452 s: contact encoding, pressure exchange,
regional contact, and regional geometry. One unrelated connectivity timeout
warning occurred in the geometry test. The contact test compiles regions 0/5/11,
checks exact table binding and both GPU consumers, verifies no Landscape height
consumer remains, and rejects wrong pages/saved assets/live replacements. The
explicit query is independent of changes to the old window translation.
All **211 Python liquid tests** pass, including four new audit tests for exact
classification, a single erroneous cell, rotated/reflected coordinates and
nonfinite/truncated data.

The legacy moving-water replay `liquid-regional-contact-refactor-regression`
completed 720 requested steps / 12 s after the shared-code refactor. Clock,
stage-order, live-density, affine-transfer and current-surface-foam audits pass:
756 reconstruction callbacks,714positive-time/42render-only,30distinct motion
images,57267primary particles (56029 supported), max position error
1.769040e-6m and affine error3.378955e-6/s. No engine errors; existing SimCache
material-DI warnings remain. Full secondary trajectory acceptance was not rerun.
Its 90.410 s blocking capture is not FPS.

Viewed `terrain_0720.png`: the old isolated test block is still glossy/lumpy,
with exposed volume sides. It remains **visually rejected**, not an updated
photoreal whole-rapid scene. No new actual-photo match is claimed this pass.
Geographic map SHA remains
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
No saved-map/asset promotion, commit, or push.

## Continue from here

Keep the full goal active. The regional contact API is now present and exercised,
but it deliberately does not reinterpret old boundary tables as regional forcing.
Next install true external/shared boundary rules and global wide-stencil pressure
color phase (see the preceding pressure-exchange review), synchronize boundary/
divergence and conservative P2G contributions, and transfer particles/identity
between physical owners. Then shared surface/foam, actual wet birth/contact/
partial-X pressure and conservation checks, continuous surface/raft behavior,
reference motion and gameplay performance. Do not enable twelve independent
wet tanks or bypass the legacy v3 domain guard.

All owned processes are terminal: builds99779/83525/45675, contact probes3839/49515,
engine tests29408 and wet replay37321. No engine handle needs resuming.
