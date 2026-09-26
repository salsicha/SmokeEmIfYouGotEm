# South Fork NAIP drape v2: lower gorge colour and full water mask

September 26, 2026. Follow-up to [drape and canopy](south-fork-naip-drape-canopy.md).
Playable texture update only; material, geometry, collision, water and canopy
actors are unchanged by this step.

## Defects found in the first drape

- **Near-white lower gorge.** An elevated ten-station survey showed the current
  route's last ~7 km (26.5-33.2 km) as almost white slopes. The window names use
  the retired 49 km route's stationing: the current lower gorge is covered only
  by `salmon_falls_takeout_approach_41500_49077m`, and that export contains a
  washed-out, desaturated source tile inside the image service mosaic (60% of
  the window; mean saturation 0.05 against 0.22 in the rest of the same image).
- **Water mask on the old grid.** The drape excluded the submerged bed using the
  composite mask (9,871 columns) although the terrain's context grid extends to
  10,006 columns, so the extended ends had no water exclusion. The other
  session found the same defect in the canopy placement and is repairing it.

## Changes in `physics/scripts/build_south_fork_naip_drape.py`

- The water mask is `source_context_extension/unknown_submerged_bed_mask.tif`
  on the context grid, so every terrain tile uses its own submerged-bed mask.
- The two windows named for stations beyond the retired route only fill pixels
  no other window covers (colour-matched by the median of the overlap; gains
  were 1.00/1.01/1.00). They are nevertheless the only imagery for the current
  lower gorge.
- `recolor_washed_tile`: the washed tile is detected from 64 px blocks with mean
  saturation < 0.08, refined per pixel within one block using locally smoothed
  saturation, and recoloured by luma-quantile transfer from the same window's
  normal pixels (a pixel at luma quantile q takes the median colour of normal
  pixels at quantile q). This keeps the tile's spatial structure (crowns,
  grass, roads) and assigns colours from the same acquisition's normal area.
  It is a colour correction, not new evidence.

Registration against the terrain water mask still peaks within one 4.9 m step
of zero (0.233 at zero, 0.234 best).

![Rebuilt drape overview (magenta: submerged bed and no coverage)](south-fork-naip-drape-v2/drape-overview.jpg)

`unreal/Scripts/update_south_fork_naip_drape_texture.py` re-imports the PNG over
`T_SouthForkFullReachNAIP` (receipts in `south-fork-naip-drape-v2/`).

![Lower gorge before and after (29.5 and 32.8 km)](south-fork-naip-drape-v2/lower-gorge-before-after.jpg)

## Still open

- No trees yet in the lower gorge: the canopy classifier (dark and green) could
  not see crowns in the washed tile. A canopy pass for the recoloured region is
  pending the other session's channel repair of the canopy actors.
- A dark notch at the left waterline at 29.5 km and the flat reservoir-like
  water surface ahead at 32.8 km need separate inspection.
