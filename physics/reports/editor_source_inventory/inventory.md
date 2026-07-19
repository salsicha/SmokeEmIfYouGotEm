# RaftSim Editor Source Inventory

Implementation files: **38**.
Implementation lines: **51461**.
Registered console commands: **34**.

## Source Files

| File | Lines |
| --- | ---: |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Captures/RaftSimEditorEnvironmentCaptures.cpp` | 2274 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Captures/RaftSimEditorFutaleufuDiagnostics.cpp` | 1589 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Captures/RaftSimEditorPhotorealCaptureDirector.cpp` | 437 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Commands/RaftSimEditorEnvironmentAutomation.cpp` | 889 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Commands/RaftSimEditorVerticalSliceBootstrap.cpp` | 469 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/RaftSimEditorAtmosphereAndFoliage.cpp` | 1602 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/RaftSimEditorEnvironmentBridge.cpp` | 385 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/RaftSimEditorEnvironmentCatalog.cpp` | 1544 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/RaftSimEditorEnvironmentInternal.h` | 2109 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/RaftSimEditorNearFieldAndLighting.cpp` | 1884 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/RaftSimEditorSurfaceSampling.cpp` | 1323 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/RaftSimEditorTerrainAuthoring.cpp` | 2819 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/RaftSimEditorWaterAndBanks.cpp` | 1657 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Foliage/RaftSimEditorCanopyGeometry.cpp` | 2579 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Foliage/RaftSimEditorCanopyReviewDirector.cpp` | 2442 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Foliage/RaftSimEditorFoliageInternal.h` | 256 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Foliage/RaftSimEditorProceduralVegetation.cpp` | 2156 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Foliage/RaftSimEditorPveAtlas.cpp` | 1686 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Foliage/RaftSimEditorPveAuthoringInternal.h` | 208 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Foliage/RaftSimEditorPveEvaluation.cpp` | 4900 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Geometry/RaftSimEditorMeshPrimitives.cpp` | 569 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/RaftSimEditorLandscapeBuild.cpp` | 1124 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/RaftSimEditorLandscapeFoliage.cpp` | 1158 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/RaftSimEditorLandscapeGeometry.cpp` | 591 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/RaftSimEditorMaterialInstances.cpp` | 612 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/RaftSimEditorMaterialTextures.cpp` | 2349 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/RaftSimEditorMaterialsBase.cpp` | 2630 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/RaftSimEditorPhotorealMaterials.cpp` | 501 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/RaftSimEditorModule.cpp` | 1035 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/RaftSimEditorToolRegistry.cpp` | 1 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/RaftSimFeatureTuningEditorShell.cpp` | 196 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/RaftSimRapidRiverEditorShell.cpp` | 90 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/RaftSimReplayDebugViewer.cpp` | 90 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/RaftSimToolValidationActions.cpp` | 350 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Rivers/RaftSimEditorFutaleufuCaptureDirector.cpp` | 1497 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Rivers/RaftSimEditorRiverFeatureAuthoring.cpp` | 2137 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Rivers/RaftSimEditorZambeziDirector.cpp` | 1793 |
| `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Tools/RaftSimEditorTools.cpp` | 1530 |

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
