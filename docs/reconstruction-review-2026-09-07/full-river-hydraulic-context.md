# South Fork source context and native terrain delivery preparation

Verified 2026-09-12 07:17 UTC. This is prerequisite progress, not a claim that
the normal South Fork map contains the reconstruction or that its water is solved.
South Fork remains the scenario; Troublemaker remains an embedded rapid. The
main-menu list and catalog contain no `troublemaker_challenge`. Migration retains
historical rapid results without granting full-river completion or reusing the
rapid's local checkpoint as a river start. The last built native catalog and
migration checks passed in `south-fork-global-progress-final-20260912/index.json`.

## Missing context identified and recovered

The first 320 m Cartesian geometry-region preparation failed after 14 packets:
the existing 2 m terrain clip did not contain an authoritative triangle for a
region at route station 1,120 m. The failed `hydraulic_regions/manifest.json` is
retained. Merely shifting regions within the old clip was insufficient: 7,394
original captured-water vertices could not have complete 224 m live windows
inside any 320 m source window. The old clip followed an earlier route, not the
corrected 33,334.146393644 m axis. This was missing source context, not evidence
of a hydraulic solver failure.

`extend_south_fork_source_context.py` recovered coverage from the 82 retained,
hash-verified DEM tiles, converting their source units before reprojection. No
new download or invented elevation fill was necessary. It added 207,654 source
vertices and 415,380 supplemental triangles. Every original captured-surface and
inferred-bed vertex is bit-identical; original coarse topology, the registered
rapid, and its seam remain intact. Supplemental faces are disjoint from the
original faces. Newly exposed submerged bed uses the explicitly uncalibrated
2.2 m maximum / 0.35 m shoreline prior; this is NOT measured bathymetry.

Under `physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach`:

- Original composite manifest: `c78d6d68478f885456a3556e7c61a9fdd170b76fa0b75f3ec6d7f21ea02c3b7c`.
- Additive `source_context_extension/manifest.json`: `e334162121c707e0d24baf8677f11bbd7c4454e6ee61e86250535e3b7211e1ca`.
- `hydraulic_regions_context/manifest.json`: `b56843c6579683322a3d04e178006939b4ba8da696607c5e7d00f19dcef40592`.

## Region geometry verification

799 regions contain 82,329,759 source samples on a common 1 m Cartesian lattice,
with 321 x 321 nodes per source packet. They cover all 406,823 original wet
vertices plus 52,689 route-axis / 12 m side-offset probes. The minimum complete
source margin is 117.78134464565665 m, exceeding the unchanged 112 m requirement.
Additional water revealed outside the original domain is boundary context; this
does not claim that every newly revealed water body is itself a playable run.

`audit_south_fork_hydraulic_regions.py` completed with terminal exit 0. All packet
hashes and finite values passed. All 7,726 overlapping region pairs had exactly
matching bed, captured surface, water-mask and triangle-owner values over
238,908,286 shared cells. Evidence is `hydraulic_regions_context/overlap_audit.json`.
All 14 geometry/delivery/region/context tests also passed, including exact
triangle equivalence between the 268 small and 51 larger supplemental batches.

These packets have no solved velocity/discharge state. The previous settled
461 x 321 rapid-join cook is still only a bounded join, not a whole-river solve.

## Native asset import completed

The full-editor driver `import_south_fork_terrain_and_context.py` exited cleanly
at 07:13:38 UTC; no UnrealEditor process remains. Its log is
`unreal/Saved/Logs/south-fork-terrain-and-context-20260912.log`.

| Asset group | Verified assets | Triangles | Native collision probes | Maximum error (cm) |
| --- | ---: | ---: | ---: | ---: |
| Original coarse tiles | 390 | 7,982,812 | 3,120 | 0.0016276041660603369 |
| Additive context tiles | 51 | 415,380 | 408 | 0.0032552083357586525 |

Reports are `unreal/Saved/RaftSimValidation/south-fork-composite-tiles-20260912.json`
and `south-fork-context-tiles-20260912.json`. All 441 saved asset hashes were
independently rechecked after editor exit. Native collision uses the retained
full triangle fallback; larger context batches do not simplify geometry.
Context assets use the corrected full-river material. Original tile packages
retain their verified original material; map component overrides must apply the
corrected material during integration. Material appearance is not yet accepted.

Low-disk interruptions were handled with checkpoint/resume and the 4 GiB guard.
This pass losslessly NTFS-compressed 505 files in eight terminal diagnostic
folders, verifying every path, length and SHA256 before and after; zero files
were deleted. Together with the previous pass's 1,026 files, all evidence was
preserved. Compression reports are `tmp/*-compression-20260912.json`. Observed
free space after all imports: 4,673,716,224 bytes. Do not add concurrent free-space
deltas as if they measured isolated compression savings.

## Normal-game boundary and next work

No map changed. FullReach SHA256 remains
`e77da92b73bf0a2c566fe69ee8a0ef7115d26182bb2f91648582aa1197ce13a0`;
the user save remains
`181d1e570485d1ec3139aec4e1d9b56d0a420fd107ce5a94218368324207f5b1`.
This explicitly does not resolve the user's complaint about missing visible
reconstruction progress. Held-paddle runtime delivery from the previous pass
is separate from this still-unintegrated terrain work.

Next: cook actual source-exact Cartesian hydraulic states with valid edge
conditions and verify their conservation/settling. Extend runtime source
selection and recentering to BOTH hydraulic axes, preserving shared-cell state.
The current streaming actor still chooses by hydraulic X as downstream station,
recenters only on X advancement, and fixes its crop center Y to zero. It cannot
be pointed at the new geographic Cartesian packets unchanged. Then migrate the
normal full-river map, corrected material, global RunManager axis, starts,
sections and finish coherently and inspect actual gameplay and cost. Do not
enable a known broken solver or add a rapid menu entry to bypass these tasks.
Breaking-wave/froth realism, robustness/performance, later rivers and release
acceptance remain open.
