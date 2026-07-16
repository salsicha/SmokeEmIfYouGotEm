# RaftSim Editor Source Inventory

Implementation files: **6**. 
Implementation lines: **46915**. 
Registered console commands: **34**.

## Source Files

| File | Lines |
| --- | ---: |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/RaftSimEditorModule.cpp` | 46188 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/RaftSimEditorToolRegistry.cpp` | 1 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/RaftSimFeatureTuningEditorShell.cpp` | 196 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/RaftSimRapidRiverEditorShell.cpp` | 90 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/RaftSimReplayDebugViewer.cpp` | 90 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/RaftSimToolValidationActions.cpp` | 350 |

## Registered Commands

| Command | Owning member | Handler |
| --- | --- | --- |
| `RaftSim.OpenTool` | `OpenToolConsoleCommand` | `HandleOpenToolCommand` |
| `RaftSim.OpenAllTools` | `OpenAllToolsConsoleCommand` | `lambda` |
| `RaftSim.CreateReviewedDataAssets` | `CreateReviewedDataAssetsConsoleCommand` | `HandleCreateReviewedDataAssetsCommand` |
| `RaftSim.CaptureToolEvidence` | `CaptureToolEvidenceConsoleCommand` | `HandleCaptureToolEvidenceCommand` |
| `RaftSim.CreatePhotorealEnvironmentPreviewMaps` | `CreatePhotorealEnvironmentPreviewMapsConsoleCommand` | `HandleCreatePhotorealEnvironmentPreviewMapsCommand` |
| `RaftSim.CapturePhotorealEnvironmentPreviews` | `CapturePhotorealEnvironmentPreviewsConsoleCommand` | `HandleCapturePhotorealEnvironmentPreviewsCommand` |
| `RaftSim.CreateLandscapeImportCandidateMaps` | `CreateLandscapeImportCandidateMapsConsoleCommand` | `HandleCreateLandscapeImportCandidateMapsCommand` |
| `RaftSim.CaptureZambeziCliffComparison` | `CaptureZambeziCliffComparisonConsoleCommand` | `HandleCaptureZambeziCliffComparisonCommand` |
| `RaftSim.CreateZambeziBatokaBasaltFamily` | `CreateZambeziBatokaBasaltFamilyConsoleCommand` | `HandleCreateZambeziBatokaBasaltFamilyCommand` |
| `RaftSim.CaptureZambeziBatokaBasaltCorridorComparison` | `CaptureZambeziBatokaBasaltCorridorComparisonConsoleCommand` | `HandleCaptureZambeziBatokaBasaltCorridorComparisonCommand` |
| `RaftSim.CaptureZambeziBatokaTerrainIntegratedComparison` | `CaptureZambeziBatokaTerrainIntegratedComparisonConsoleCommand` | `HandleCaptureZambeziBatokaTerrainIntegratedComparisonCommand` |
| `RaftSim.CaptureZambeziBatokaWorldAlignedTerrainComparison` | `CaptureZambeziBatokaWorldAlignedTerrainComparisonConsoleCommand` | `HandleCaptureZambeziBatokaWorldAlignedTerrainComparisonCommand` |
| `RaftSim.CaptureZambeziBatokaVisualMorphologyComparison` | `CaptureZambeziBatokaVisualMorphologyComparisonConsoleCommand` | `HandleCaptureZambeziBatokaVisualMorphologyComparisonCommand` |
| `RaftSim.CaptureFutaleufuNativeCanopyCorridorComparison` | `CaptureFutaleufuNativeCanopyCorridorComparisonConsoleCommand` | `HandleCaptureFutaleufuNativeCanopyCorridorComparisonCommand` |
| `RaftSim.CaptureFutaleufuDenseCanopyComparison` | `CaptureFutaleufuDenseCanopyComparisonConsoleCommand` | `HandleCaptureFutaleufuDenseCanopyComparisonCommand` |
| `RaftSim.CaptureFutaleufuAreaSampledCanopyComparison` | `CaptureFutaleufuAreaSampledCanopyComparisonConsoleCommand` | `HandleCaptureFutaleufuAreaSampledCanopyComparisonCommand` |
| `RaftSim.CaptureFutaleufuWorldStableCanopyComparison` | `CaptureFutaleufuWorldStableCanopyComparisonConsoleCommand` | `HandleCaptureFutaleufuWorldStableCanopyComparisonCommand` |
| `RaftSim.CaptureFutaleufuNativeCanopyRenderDiagnostics` | `CaptureFutaleufuNativeCanopyRenderDiagnosticsConsoleCommand` | `HandleCaptureFutaleufuNativeCanopyRenderDiagnosticsCommand` |
| `RaftSim.CaptureFutaleufuNativeCanopyOpacityDiagnostics` | `CaptureFutaleufuNativeCanopyOpacityDiagnosticsConsoleCommand` | `HandleCaptureFutaleufuNativeCanopyOpacityDiagnosticsCommand` |
| `RaftSim.CaptureFutaleufuNativeCanopyLightingDiagnostics` | `CaptureFutaleufuNativeCanopyLightingDiagnosticsConsoleCommand` | `HandleCaptureFutaleufuNativeCanopyLightingDiagnosticsCommand` |
| `RaftSim.CaptureFutaleufuNativeCanopyCorridorLightRigDiagnostics` | `CaptureFutaleufuNativeCanopyCorridorLightRigDiagnosticsConsoleCommand` | `HandleCaptureFutaleufuNativeCanopyCorridorLightRigDiagnosticsCommand` |
| `RaftSim.CaptureFutaleufuNativeCanopyReflectanceDiagnostics` | `CaptureFutaleufuNativeCanopyReflectanceDiagnosticsConsoleCommand` | `HandleCaptureFutaleufuNativeCanopyReflectanceDiagnosticsCommand` |
| `RaftSim.CaptureFutaleufuNativeCanopyShadingModelDiagnostics` | `CaptureFutaleufuNativeCanopyShadingModelDiagnosticsConsoleCommand` | `HandleCaptureFutaleufuNativeCanopyShadingModelDiagnosticsCommand` |
| `RaftSim.CaptureFutaleufuNativeCanopyMipPaddingDiagnostics` | `CaptureFutaleufuNativeCanopyMipPaddingDiagnosticsConsoleCommand` | `HandleCaptureFutaleufuNativeCanopyMipPaddingDiagnosticsCommand` |
| `RaftSim.CaptureFutaleufuNativeCanopyOpacitySelectionDiagnostics` | `CaptureFutaleufuNativeCanopyOpacitySelectionDiagnosticsConsoleCommand` | `HandleCaptureFutaleufuNativeCanopyOpacitySelectionDiagnosticsCommand` |
| `RaftSim.CaptureFutaleufuNativeCanopyBoundedShadowDiagnostics` | `CaptureFutaleufuNativeCanopyBoundedShadowDiagnosticsConsoleCommand` | `HandleCaptureFutaleufuNativeCanopyBoundedShadowDiagnosticsCommand` |
| `RaftSim.InspectProceduralVegetationSample` | `InspectProceduralVegetationSampleConsoleCommand` | `HandleInspectProceduralVegetationSampleCommand` |
| `RaftSim.EvaluateProceduralBeechCandidate` | `EvaluateProceduralBeechCandidateConsoleCommand` | `HandleEvaluateProceduralBeechCandidateCommand` |
| `RaftSim.EvaluateFutaleufuCordilleraCypressPveCandidate` | `EvaluateFutaleufuCordilleraCypressPveCandidateConsoleCommand` | `HandleEvaluateFutaleufuCordilleraCypressPveCandidateCommand` |
| `RaftSim.CreateFutaleufuNativeCanopyPrototype` | `CreateFutaleufuNativeCanopyPrototypeConsoleCommand` | `HandleCreateFutaleufuNativeCanopyPrototypeCommand` |
| `RaftSim.CreateFutaleufuCordilleraCypressFamily` | `CreateFutaleufuCordilleraCypressFamilyConsoleCommand` | `HandleCreateFutaleufuCordilleraCypressFamilyCommand` |
| `RaftSim.CreateFutaleufuCordilleraCypressOpaqueNearReview` | `CreateFutaleufuCordilleraCypressOpaqueNearReviewConsoleCommand` | `HandleCreateFutaleufuCordilleraCypressOpaqueNearReviewCommand` |
| `RaftSim.CreateFutaleufuCordilleraCypressVolumetricNearReview` | `CreateFutaleufuCordilleraCypressVolumetricNearReviewConsoleCommand` | `HandleCreateFutaleufuCordilleraCypressVolumetricNearReviewCommand` |
| `RaftSim.CreateFutaleufuCordilleraCypressDonorReview` | `CreateFutaleufuCordilleraCypressDonorReviewConsoleCommand` | `HandleCreateFutaleufuCordilleraCypressDonorReviewCommand` |

## River Build Paths

| River id | Candidate map | Present |
| --- | --- | --- |
| `american_south_fork` | `L_SouthForkAmerican_PhysicalCorridorCandidate` | yes |
| `colorado_river` | `L_ColoradoGrandCanyon_PhysicalCorridorCandidate` | yes |
| `pacuare` | `L_Pacuare_SourceLandscapeCandidate` | yes |
| `zambezi_batoka_gorge` | `L_ZambeziBatokaGorge_PhysicalCorridorCandidate` | yes |
| `futaleufu_terminator` | `L_FutaleufuTerminator_PhysicalCorridorCandidate` | yes |
| `chilko_river_lava_canyon` | `L_ChilkoRiver_PhysicalCorridorCandidate` | yes |

## Startup Flags

- `RaftSimCaptureFutaleufuAreaSampledCanopyComparison`
- `RaftSimCaptureFutaleufuDenseCanopyComparison`
- `RaftSimCaptureFutaleufuWorldStableCanopyComparison`
- `RaftSimCapturePhotorealEnvironmentPreviews`
- `RaftSimCaptureZambeziBatokaBasaltCorridorComparison`
- `RaftSimCaptureZambeziBatokaTerrainIntegratedComparison`
- `RaftSimCaptureZambeziBatokaVisualMorphologyComparison`
- `RaftSimCaptureZambeziBatokaWorldAlignedTerrainComparison`
- `RaftSimCreateFutaleufuCordilleraCypressDonorReview`
- `RaftSimCreateFutaleufuCordilleraCypressFamily`
- `RaftSimCreateFutaleufuCordilleraCypressOpaqueNearReview`
- `RaftSimCreateFutaleufuCordilleraCypressVolumetricNearReview`
- `RaftSimCreateLandscapeImportCandidateMaps`
- `RaftSimCreatePhotorealEnvironmentPreviewMaps`
- `RaftSimCreateZambeziBatokaBasaltFamily`
- `RaftSimExitAfterEnvironmentAutomation`
- `RaftSimExitAfterPveGeneration`
- `RaftSimSkipPhotorealFlowVariantCaptures`
