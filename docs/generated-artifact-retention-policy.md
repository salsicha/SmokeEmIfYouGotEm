# Generated Artifact Retention Policy

Written July 15, 2026. Revised July 17, 2026.

> **July 17, 2026 owner instruction (given directly in chat) supersedes the July 16 no-prune decision.** Generated preview/candidate maps are no longer versioned; repository trimming, history rewrite, and LFS pruning are authorized and executed per `docs/release-1.0-plan.md` §3 (Phase 0). A full pre-rewrite mirror archive is created before any history surgery, and GitHub-side purge of orphaned LFS storage remains an owner-handoff step. The paragraphs below record the superseded July 16 policy and the original audit for historical reference.

Historical (superseded) decision of July 16, 2026: the owner chose to keep versioning generated maps and not prune Git LFS; no LFS dry run, prune, server deletion, history rewrite, `git rm --cached`, retention-configuration change, or ignore-rule change was authorized at that time.

## Current audit

| Item | Measured state |
| --- | --- |
| Primary remote | `origin`, GitHub over SSH |
| Secondary remote | `gitlab`, GitLab over HTTPS |
| Active LFS endpoint/prune remote | GitHub `origin` |
| Local `.git/lfs` | 8.6 GB |
| Local `.git/objects` | 3.7 GB |
| Working tree | 28 GB |
| Tracked LFS files | 961 |
| Current tracked LFS payload | approximately 8.86 GiB |
| Tracked `.umap` files in LFS | 49 files, approximately 6.37 GiB |
| `EnvironmentPreviews` LFS payload | 21 files, approximately 6.36 GiB |
| Commits touching `EnvironmentPreviews` | 169 |

The remediation-plan snapshot reported a 291 GB local LFS store. The current measured store is 8.6 GB. This audit does not infer or claim that a prior prune occurred because no matching retention log was found. The smaller current store does not solve hosted LFS growth or prevent future local accumulation.

Git LFS currently uses its defaults: recent refs for 7 days, zero additional recent-commit days, a 3-day prune offset, remote refs included, and `origin` as the remote checked by prune. No repository-specific retention settings are configured.

## Largest current candidates

| Generated map | Current size |
| --- | ---: |
| `L_ZambeziBatokaGorge_PhysicalCorridorCandidate.umap` | 1.70 GiB |
| `L_ChilkoRiver_PhysicalCorridorCandidate.umap` | 1.20 GiB |
| `L_FutaleufuTerminator_PhysicalCorridorCandidate.umap` | 705 MiB |
| `L_ColoradoGrandCanyon_PhysicalCorridorCandidate.umap` | 346 MiB |
| `L_SouthForkAmerican_PhysicalCorridorCandidate.umap` | 262 MiB |
| Pacuare base and four flow-review maps | 167 MiB each |
| South Fork base and three flow-review maps | 139 MiB each |
| Colorado base and three flow-review maps | 127 MiB each |

These are review candidates under `unreal/Content/RaftSim/Maps/EnvironmentPreviews/`, not promoted shipping maps. Re-saving one produces a new immutable LFS object even when the logical map name is unchanged.

## Retention classes

### Keep in git and LFS

- source geospatial, imagery, hydrology, and rights-reviewed inputs that cannot be deterministically reacquired without provider/version drift;
- promoted shipping maps and a deliberately small set of milestone-locked integration maps;
- licensed source assets when their license permits repository storage and collaborator access;
- small review evidence, manifests, hashes, source records, generator code, and accepted report locks;
- generated binary assets only when their exact bytes are an accepted release or validation dependency and regeneration is not sufficiently deterministic.

### Regenerate locally

- unpromoted `EnvironmentPreviews/LandscapeCandidates` maps;
- unpromoted flow-variant and ordinary photoreal preview maps;
- transient capture worlds, local PVE review assets, derived candidate meshes, and shader-review packages;
- any candidate whose complete inputs, command, engine version, plugin set, and output hashes are recorded.

### Preserve as evidence, not live code

- review JSONs, compact metric reports, contact sheets, promotion/rejection decisions, and source manifests;
- the latest accepted generator for an active asset line;
- git history for superseded implementation details after the separate generator-retirement policy is approved.

## Regeneration contracts

The physical Landscape candidates are regenerated through the source-controlled editor command:

```bash
"/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd" \
  "$PWD/unreal/SmokeEmIfYouGotEm.uproject" \
  -unattended -nop4 -nosplash -NoSound -RenderOffscreen \
  -RaftSimCreateLandscapeImportCandidateMaps \
  -RaftSimExitAfterEnvironmentAutomation
```

The base and flow-variant preview maps are regenerated through:

```bash
"/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd" \
  "$PWD/unreal/SmokeEmIfYouGotEm.uproject" \
  -unattended -nop4 -nosplash -NoSound -RenderOffscreen \
  -RaftSimCreatePhotorealEnvironmentPreviewMaps \
  -RaftSimCapturePhotorealEnvironmentPreviews \
  -RaftSimExitAfterEnvironmentAutomation
```

Before any candidate is removed from tracking, its manifest must record the exact generator command, Unreal association/build, enabled project plugins, source hashes, river/flow selection, output package path, and review status. Regeneration must reproduce the required logical package and validation evidence; volatile binary hashes need not match unless a gate explicitly declares byte identity.

## Owner decision: no LFS pruning

The owner rejected local and hosted LFS pruning. The repository keeps the existing Git LFS configuration and retains all currently reachable local and hosted objects. The previously proposed 30-day recent-ref and recent-commit window with a 7-day prune offset is not adopted.

Do not run `git lfs prune`, including a dry run, as part of this remediation. Do not alter repository-specific LFS retention settings. Future reconsideration requires a new explicit owner decision and a new impact review.

The decision applies to both the GitHub origin and GitLab mirror. No server-side LFS deletion or history rewrite is planned.

## Owner decision: keep versioning maps

Generated preview and candidate maps remain tracked in Git LFS, including maps under `unreal/Content/RaftSim/Maps/EnvironmentPreviews/`. The proposed volatile-map untracking and narrow ignore rules are rejected. Regeneration contracts remain documented because they are useful for recovery and validation, but they do not replace versioned map packages.

This accepts continued repository and hosted-LFS growth as the cost of retaining exact generated map revisions. The audit measurements remain the baseline for observing that growth; observation does not authorize cleanup.

## Owner gates

The following remain prohibited without a new explicit approval that reverses or narrows the July 16, 2026 decision:

- running `git lfs prune --dry-run`;
- running any non-dry `git lfs prune`;
- changing repository-specific LFS retention configuration;
- deleting hosted GitHub or GitLab LFS objects;
- untracking or ignoring current candidate maps;
- rewriting history to remove old LFS pointers or objects.

Finding 3.1 is closed by owner decision: keep versioning maps and do not prune. No destructive action was performed.
