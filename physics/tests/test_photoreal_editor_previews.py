# ruff: noqa: F405

from photoreal_test_support import *  # noqa: F401,F403


def test_unreal_editor_preview_capture_records_procedural_asset_plan():
    editor_source = EDITOR_MODULE_PATH.read_text(encoding="utf-8")
    water_review = json.loads(WATER_MATERIAL_REVIEW_PATH.read_text(encoding="utf-8"))

    assert "GetFirstPartyProceduralEnvironmentAssetPlanRelativePath" in editor_source
    assert "GetFirstPartyProceduralMaterialRecipePlanRelativePath" in editor_source
    assert "GetFirstPartyMaterialInstanceCandidateManifestRelativePath" in editor_source
    assert "GetFirstPartyMaterialTextureAtlasAlbedoRelativePath" in editor_source
    assert "GetFirstPartyMaterialTextureAtlasNormalRelativePath" in editor_source
    assert "GetFirstPartyMaterialTextureAtlasPackedRelativePath" in editor_source
    assert "GetProductionGeospatialAttachmentLedgerRelativePath" in editor_source
    assert "GetPhotorealFlowVariantCapturePlanRelativePath" in editor_source
    assert "GetEnvironmentPreviewFlowVariantSpecs" in editor_source
    assert "MakeFlowVariantPreviewMapPackagePath" in editor_source
    assert "GetPreviewFlowVariantCaptureRelativePath" in editor_source
    assert "flow_variant_capture_manifest.json" in editor_source
    assert (
        "docs/environment-captures/photoreal_river_previews/flow_variants"
        in editor_source
    )
    assert "captured_band_named_flow_variant_preview_renders" in editor_source
    assert "BuildPreviewMapForSpec(VariantSpec" in editor_source
    assert (
        "all_band_named_flow_variant_previews_captured_not_lifelike_approved"
        in editor_source
    )
    assert "low_runnable" in editor_source
    assert "high_runnable" in editor_source
    assert "low_release_planning" in editor_source
    assert "high_release_planning" in editor_source
    assert "clear_season_low_planning" in editor_source
    assert "flash_response_review_only" in editor_source
    assert "SampleFirstPartyMaterialAtlasTile" in editor_source
    assert "ApplyFirstPartyMaterialAtlasTint" in editor_source
    assert "ApplyFirstPartyMaterialAtlasSurfaceResponse" in editor_source
    assert "GetFirstPartyMaterialAtlasMicroReliefCm" in editor_source
    assert "TerrainBankLayeredMaterialTile" in editor_source
    assert "FlowDependentWaterSurfaceMaterialTile" in editor_source
    assert "WetBoulderContactMaterialTile" in editor_source
    assert "BiomeFoliageGroundcoverMaterialTile" in editor_source
    assert "RaftForegroundReviewMaterialTile" in editor_source
    assert "AddPreviewSurfaceAtmosphereAndSprayDetail" in editor_source
    assert "RaftSim_SurfaceGlint" in editor_source
    assert "RaftSim_FoamFleck" in editor_source
    assert "RaftSim_RainforestSprayMist" in editor_source
    assert "RaftSim_BoulderContactFoam" in editor_source
    assert "RaftSim_FlowAwareWaterlinePebble" in editor_source
    assert "WaterlinePebbleCount" in editor_source
    assert "AddPreviewIrregularRockActor" in editor_source
    assert "RaftSim_SourceAwareBoulder" in editor_source
    assert "AddPreviewBoulderSurfaceVariationDetail" in editor_source
    assert "RaftSim_BoulderWetSheenFacet" in editor_source
    assert "RaftSim_BoulderAbrasionFacet" in editor_source
    assert "RaftSim_BoulderTopHighlightFacet" in editor_source
    assert "RaftSim_BoulderMossSedimentFacet" in editor_source
    assert "RaftSim_BoulderCreviceShadowFacet" in editor_source
    assert "BoulderBaseColor" in editor_source
    assert "bNearCameraReviewBoulder" in editor_source
    assert "ReviewClearanceSide" in editor_source
    assert "NearCameraFacetScale" in editor_source
    assert "RaftSim_ProceduralTalusPebble" in editor_source
    assert "AddPreviewSourceAwareBankBreakupDetail" in editor_source
    assert "RaftSim_SourceAwareBankBreakupPatch" in editor_source
    assert "AddPreviewTerrainMaterialLayerDetail" in editor_source
    assert "RaftSim_TerrainMaterialLayerFacet" in editor_source
    assert "AddPreviewLandscapeNaniteMaterialScaffoldDetail" in editor_source
    assert "RaftSim_LandscapeNaniteMaterialScaffoldFacet" in editor_source
    assert "RaftSim_LandscapeNaniteStrataMicroBand" in editor_source
    assert "RaftSim_LandscapeNaniteSlopeOcclusionPatch" in editor_source
    assert "LoadOrCreatePreviewTerrainVertexColorMaterial" in editor_source
    assert "M_RaftSim_TerrainVertexColorLitPreview" in editor_source
    assert "EditorOnlyData->Roughness" in editor_source
    assert "NormalizePreviewTerrainProxyPatchColor" in editor_source
    assert "GetPreviewSoftTerrainPatchCoverage" in editor_source
    assert "BlendPreviewSoftTerrainPatchColor" in editor_source
    assert "ApplyPreviewSourceAwareTerrainPhotoMottle" in editor_source
    assert "SourceAwareTerrainPhotoMottleReliefCm" in editor_source
    assert "TerrainConstantIndex" in editor_source
    assert "SetCastShadow(false)" in editor_source
    assert "AddPreviewFlowBandTextureDetail" in editor_source
    assert "RaftSim_FlowTextureRibbon" in editor_source
    assert "NearFrameWaterRibbonDemotion" in editor_source
    assert "bNearFrameWaterRibbon" in editor_source
    assert "BaseWaveAmplitudeCm" in editor_source
    assert "StandingWaveAmplitudeCm" in editor_source
    assert "FlowCurrentCueScale" in editor_source
    assert "FlowCuedWaterFoamMottleColor" in editor_source
    assert "FlowCuedWaterSlickMottleT" in editor_source
    assert "FlowCuedWaterMottleRippleCm" in editor_source
    assert "AddPreviewWaterSurfaceChopAndTurbidityDetail" in editor_source
    assert "AddPreviewWaterTurbidityPatch" in editor_source
    assert "RaftSim_FlowSurfaceChopCrest" in editor_source
    assert "RaftSim_FlowTurbidityDepthPatch" in editor_source
    assert "const float TurbidityDepthPatchArtifactDemotion = 0.0f" in editor_source
    assert "AddPreviewWaterMicroRippleGlintDetail" in editor_source
    assert "RaftSim_WaterMicroRippleGlint" in editor_source
    assert "const float DarkMicroRippleArtifactDemotion = 0.0f" in editor_source
    assert "AddPreviewWaterShaderDepthReflectionScaffoldDetail" in editor_source
    assert "RaftSim_WaterShaderDepthReflectionScaffold" in editor_source
    assert "FirstPartyLitWaterNormalResponseEmissiveFill" in editor_source
    assert "FirstPartyLitWaterNormalResponseRoughness" in editor_source
    assert "FirstPartyLitWaterNormalResponseSpecular" in editor_source
    assert "NearCameraWaterScaffoldClearanceMinX" in editor_source
    assert (
        "const float NearCameraWaterScaffoldClearanceMinX = 25200.0f" in editor_source
    )
    assert "CentralWaterScaffoldPlateDemotion" in editor_source
    assert "RemainingWaterOverlaySlabDemotion" in editor_source
    assert "WaterOverlaySlabOpacityDemotion" in editor_source
    assert "CurrentStreakLengthScale" in editor_source
    assert "remaining water overlay slab demotion" in editor_source
    assert "LongDarkWaterStreakDemotion" in editor_source
    assert "WaterLineArtifactColorReblend" in editor_source
    assert "long dark water streak demotion" in editor_source
    assert "BaseWaterCenterGuideStripeDemotion" in editor_source
    assert "BaseWaterEdgeRailArtifactDemotion" in editor_source
    assert "BaseWaterEdgeRailLumaCeiling" in editor_source
    assert "CenterGuideRibbonDemotion" in editor_source
    assert "CenterGuideRibbonDemotion <= 0.16f" in editor_source
    assert "CenterGuideStripeT" in editor_source
    assert "CenterStripeBreakupT" in editor_source
    assert "CenterLaneEraseColor" in editor_source
    assert "CenterLaneBroadEraseT" in editor_source
    assert "constexpr int32 CrossSteps = 81" in editor_source
    assert "base-water center guide-stripe breakup" in editor_source
    assert "BaseWaterCrossChannelBreakupNoise" in editor_source
    assert "BaseWaterCrossChannelBreakupT" in editor_source
    assert "BaseWaterCrossChannelHighlightT" in editor_source
    assert "BaseWaterCrossChannelReliefCm" in editor_source
    assert "BaseWaterCenterSeamDiffusionT" in editor_source
    assert "base-water cross-channel breakup" in editor_source
    assert "FirstPartyPostSeamWaterSurfaceGrainNoise" in editor_source
    assert "FirstPartyPostSeamWaterSurfaceGrainT" in editor_source
    assert "BaseWaterResidualDarkStreakLumaFloor" in editor_source
    assert "FirstPartyAtlasReviewEmissiveFillScale" in editor_source
    assert (
        "const float FirstPartyLitWaterNormalResponseSpecular = 0.0f" in editor_source
    )
    assert "SetFogInscatteringColor" in editor_source
    assert "RiverEyeCenterCoverForegroundLumaFloor" in editor_source
    assert "CurrentStreakArtifactDemotion" in editor_source
    assert "CurrentStreakNearFrameStartX" in editor_source
    assert "const float CurrentStreakArtifactDemotion = 0.0f" in editor_source
    assert "WaterlineRailArtifactDemotion" in editor_source
    assert "FlowTextureRailArtifactDemotion" in editor_source
    assert "ShallowEdgeRailArtifactDemotion" in editor_source
    assert "current streak and waterline rail artifact demotion" in editor_source
    assert "central water scaffold plate demotion" in editor_source
    assert "RaftSim_WaterShaderFresnelBankReflection" in editor_source
    assert "RaftSim_WaterShaderRefractionSeam" in editor_source
    assert "AddPreviewRiverAtmosphericBackdropDetail" in editor_source
    assert "RaftSim_RiverSpecificCloudHaze" in editor_source
    assert "RaftSim_RiverSpecificHorizonVeil" in editor_source
    assert "AddPreviewSourceAwareSkyGradientLayer" in editor_source
    assert "RaftSim_SourceAwareSkyGradientBand" in editor_source
    assert "RaftSim_SourceAwareSunWarmthVeil" in editor_source
    assert "RaftSim_SourceAwareAtmosphereDepthSheet" in editor_source
    assert "AddPreviewWaterfallAndPlungeMistDetail" in editor_source
    assert "RaftSim_PacuareWaterfallCurtain" in editor_source
    assert "RaftSim_PacuareWaterfallPlungeMist" in editor_source
    assert "RaftSim_PacuareWaterfallRunout" in editor_source
    assert "RaftSim_PacuareWaterfallWetCliff" in editor_source
    assert "AddPreviewSourceMaskedBankBarMicrogeometryDetail" in editor_source
    assert "RaftSim_SourceMaskedExposedBarMicroPebble" in editor_source
    assert "RaftSim_SourceMaskedBankSlopeMaterialFlake" in editor_source
    assert "AddPreviewSourceMaskedShorelineLipOverhangDetail" in editor_source
    assert "RaftSim_SourceMaskedShorelineLipOverhang" in editor_source
    assert "DisablePreviewProceduralMeshCollision" in editor_source
    assert "AddPreviewBiomeBankEcologyDetail" in editor_source
    assert "RaftSim_BiomeDeadfallLog" in editor_source
    assert "FirstPartyOrganicDeadfallCylinderReplacement" in editor_source
    assert "RaftSim_BiomeBankGrassCard" in editor_source
    assert "RaftSim_BiomeRootRunner" in editor_source
    assert "FirstPartyOrganicRootRunnerCylinderReplacement" in editor_source
    assert "AddPreviewBiomeFoliageSilhouetteDetail" in editor_source
    assert "RaftSim_OrganicFoliageSilhouetteBranch" in editor_source
    assert "RaftSim_RainforestVineCurtain" in editor_source
    assert "RaftSim_RiparianBranchCluster" in editor_source
    assert "RaftSim_DesertScrubSilhouette" in editor_source
    assert "AddPreviewDenseBiomeFoliageLayerDetail" in editor_source
    assert "RaftSim_DenseBiomeOrganicBranchFrondCanopy" in editor_source
    assert "RaftSim_DenseBiomeOrganicBranchFrondUnderstory" in editor_source
    assert "RaftSim_DenseBiomeFoliageTrunkCluster" in editor_source
    assert "RaftSim_DenseBiomeOrganicPalmFrondLattice" in editor_source
    assert "RaftSim_DenseBiomeFoliageDesertThicket" in editor_source
    assert "UInstancedStaticMeshComponent" in editor_source
    assert "AddPreviewInstancedProceduralFoliageEquivalentDetail" in editor_source
    assert "RaftSim_InstancedProceduralFoliageCanopyLibrary" in editor_source
    assert "RaftSim_InstancedProceduralFoliageTrunkLibrary" in editor_source
    assert "RaftSim_InstancedProceduralFoliageUnderstoryLibrary" in editor_source
    assert "RemainingInstancedSphereFoliageBlobCull = 0.0f" in editor_source
    assert "AddPreviewProceduralLeafClusterActor" in editor_source
    assert "RaftSim_ProceduralLeafClusterSupplement" in editor_source
    assert "AddPreviewOrganicLeafSprayActor" in editor_source
    assert "RaftSim_OrganicCanopyLeafSpray" in editor_source
    assert "AddPreviewOrganicBranchFrondActor" in editor_source
    assert "RaftSim_OrganicBranchFrondSupplement" in editor_source
    assert "RaftSim_DenseBiomeOrganicBranchFrondCanopy" in editor_source
    assert "AddPreviewFineTwigCanopyLaceActor" in editor_source
    assert "RaftSim_FineTwigCanopyLace" in editor_source
    assert "RaftSim_DenseBiomeFineTwigCanopyLace" in editor_source
    assert "const int32 TwigCount = bRainforest ? 20 : 14" in editor_source
    assert "const int32 LeafletsPerTwig = bRainforest ? 5 : 4" in editor_source
    assert "AddPreviewFoliageCrownDepthAndLeafletBreakupDetail" in editor_source
    assert "RaftSim_FoliageCrownDepthAndLeafletBreakup" in editor_source
    assert (
        "const int32 LeafletsPerCrown = Spec.bDesertCanyon ? 3 : (bRainforest ? 7 : 5)"
        in editor_source
    )
    assert "bUseFirstPartyProceduralFoliageOnly" in editor_source
    assert "bUseFirstPartyProceduralFoliageOnly = true" in editor_source
    assert "PCG/SampleContent/SimpleForest" in editor_source
    assert (
        "first-party procedural-only foliage review path with stylized PCG sample tree meshes disabled"
        in editor_source
    )
    assert "FirstPartyProceduralCanopyHeightCm" in editor_source
    assert "FirstPartyProceduralCanopyWidthScale" in editor_source
    assert "FirstPartyProceduralTrunkHeightCm" in editor_source
    assert "first-party procedural canopy height and massing profile" in editor_source
    assert "FirstPartyProceduralCanopyToneAnchor" in editor_source
    assert "FirstPartyProceduralCanopyToneCompression" in editor_source
    assert "FirstPartyProceduralCanopyShadowColor" in editor_source
    assert (
        "first-party procedural canopy tone compression and shadow profile"
        in editor_source
    )
    assert "FirstPartyProceduralCanopyBlobDemotion" in editor_source
    assert "FoliageCardSilhouetteDemotion" in editor_source
    assert "FoliageCardVisibilityBreakupT" in editor_source
    assert "first-party foliage card/canopy artifact demotion" in editor_source
    assert "remaining square card cull" in editor_source
    assert "RemainingSquareSourceCardCull" in editor_source
    assert "RemainingSquareFoliageCardCull" in editor_source
    assert "RemainingSquareCardOpacityDemotion" in editor_source
    assert "RemainingAtmosphericCardCull" in editor_source
    assert "RemainingBlockyFoliageProxyCull" in editor_source
    assert (
        "first_party_blocky_bank_ecology_and_sphere_foliage_cull"
        in ASSET_PLAN_PATH.read_text(encoding="utf-8")
    )
    assert "SquareFoliageSourceCardArtifactDemotion" in editor_source
    assert "SquareFoliageCardArtifactDemotion" in editor_source
    assert "const int32 CardsPerSide = Spec.bDesertCanyon ? 14" in editor_source
    assert "const int32 GrassCardCount = Spec.bDesertCanyon ? 10" in editor_source
    assert "const int32 SilhouetteCount = Spec.bDesertCanyon ? 8" in editor_source
    assert "square foliage/source-card artifact demotion" in editor_source
    assert "RaftSim_MaskAwareCanopyCardOrganicCull" in editor_source
    assert "RaftSim_BiomeBankGrassOrganicCull" in editor_source
    assert "RaftSim_RainforestVineCurtainOrganicCull" in editor_source
    assert "RaftSim_DesertScrubSilhouetteOrganicCull" in editor_source
    assert "RaftSim_OrganicFoliageSilhouetteBranch" in editor_source
    assert (
        "SouthFork.FoliageColor = FLinearColor(0.16f, 0.29f, 0.105f)" in editor_source
    )
    assert "Pacuare.FoliageColor = FLinearColor(0.035f, 0.20f, 0.055f)" in editor_source
    assert "Specular->R = 0.16f" in editor_source
    assert "EmissiveScale->R = 0.22f" in editor_source
    assert "Constant->R = 0.22f" in editor_source
    assert "const float MinLuma = Spec.bDesertCanyon ? 0.300f" in editor_source
    assert "const float MaxLuma = Spec.bDesertCanyon ? 0.38f" in editor_source
    assert "const float MaxFeatureBlend = Spec.bDesertCanyon ? 0.14f" in editor_source
    assert "constexpr int32 XSteps = 560" in editor_source
    assert "constexpr int32 YSteps = 224" in editor_source
    assert "BaseTerrainSourceAwareMaterialGrainT" in editor_source
    assert "BaseTerrainMaterialBreakupT" in editor_source
    assert "BaseTerrainMicroReliefCm" in editor_source
    assert "ApplyPreviewSourceAwareTerrainSurfaceGranularity" in editor_source
    assert "FirstPartySourceAwareTerrainGranularityCell" in editor_source
    assert "FirstPartyTerrainSurfaceGranularityReliefCm" in editor_source
    assert "ApplyPreviewSourceConditionedFarBankAlbedoCalibration" in editor_source
    assert "SourceConditionedFarBankAlbedoT" in editor_source
    assert "FarBankSourceDrapeGain" in editor_source
    assert "SourceConditionedFarBankMicroReliefCm" in editor_source
    assert "SourceConditionedTerrainLumaTarget" in editor_source
    assert "GetSourceConditionedMaterialMapManifestRelativePath" in editor_source
    assert "CreateSourceConditionedMaterialTextureAssets" in editor_source
    assert "SourceConditionedMacroAlbedo" in editor_source
    assert "SourceConditionedMaterialZones" in editor_source
    assert "SourceConditionedAORoughnessHeight" in editor_source
    assert "SourceConditionedNormalDetail" in editor_source
    assert "SourceConditionedZoneWeights" in editor_source
    assert "SourceConditionedMacroAlbedoWeight" in editor_source
    assert "SourceConditionedSurfaceResponseWeight" in editor_source
    assert "SourceConditionedNormalDetailWeight" in editor_source
    assert "SourceConditionedMaterialAssignmentReviewOnlyNotLifelike" in editor_source
    assert "ApplyPreviewBroadSlopeTerrainExposureFill" in editor_source
    assert "BroadSlopeTerrainExposureFillT" in editor_source
    assert "BroadSlopeTerrainLumaTarget" in editor_source
    assert "BroadSlopeTerrainLowFrequencyReliefCm" in editor_source
    assert "BroadSlopeSourceDrapeT" in editor_source
    assert "broad-slope terrain exposure fill and relief" in editor_source
    assert "SourceAwareMacroTerrainRidgeFacetT" in editor_source
    assert "SourceAwareMacroTerrainRidgeNoise" in editor_source
    assert "SourceAwareMacroTerrainRidgeReliefCm" in editor_source
    assert "MacroTerrainRidgeShadowT" in editor_source
    assert "MacroTerrainRidgeHighlightT" in editor_source
    assert "source-aware macro terrain ridge/facet relief" in editor_source
    assert "ApplyPreviewSourceAwareTerrainSlopeFacetTexture" in editor_source
    assert "SourceAwareTerrainSlopeFacetTextureT" in editor_source
    assert "SourceAwareTerrainSlopeFacetNoise" in editor_source
    assert "SourceAwareTerrainSlopeFacetReliefCm" in editor_source
    assert "ApplyPreviewSourceAwareRiparianCanopyMassTexture" in editor_source
    assert "SourceAwareRiparianCanopyMassTextureT" in editor_source
    assert "SourceAwareRiparianCanopyMassNoise" in editor_source
    assert "SourceAwareRiparianCanopyMassReliefCm" in editor_source
    assert "source-aware riparian canopy mass texture" in editor_source
    assert "BaseWaterFlowThreadTextureT" in editor_source
    assert "BaseWaterFlowThreadNoise" in editor_source
    assert "BaseWaterFlowThreadReliefCm" in editor_source
    assert "BaseWaterFlowThreadFoamGlintT" in editor_source
    assert "FirstPartyWaterPaletteSeed" in editor_source
    assert "FirstPartyWaterLongBandNoise" in editor_source
    assert "FirstPartyWaterLongReflectionColor" in editor_source
    assert "base-water flow-thread texture" in editor_source
    assert "constexpr int32 Segments = 72" in editor_source
    assert "constexpr int32 CrossSteps = 3" in editor_source
    assert "NearFrameShorelineRibbonDemotion" in editor_source
    assert "PaleShorelineSlashArtifactDemotion" in editor_source
    assert "GraphicWaterlineRibbonDemotion" in editor_source
    assert "RibbonContinuityBreakupT" in editor_source
    assert "SegmentFade *" in editor_source
    assert "FMath::Lerp(0.002f, 0.012f" in editor_source
    assert "NearFrameShallowWaterBandDemotion" in editor_source
    assert "ShallowWaterEdgeBandDemotion" in editor_source
    assert "NearFrameBubbleDemotion" in editor_source
    assert "PaleFoamSlashArtifactDemotion" in editor_source
    assert "FoamRailContinuityBreakupT" in editor_source
    assert "LoadOrCreatePreviewWaterVertexColorMaterial()" in editor_source
    assert "BandInnerEdge" in editor_source
    assert "Side * (ActiveRiverHalfWidth + 66.0f * WetBankScale)" in editor_source
    assert "(Spec.bDesertCanyon ? 44.0f : 32.0f) * WetBankScale" in editor_source
    assert "(Spec.bDesertCanyon ? 52.0f : 38.0f) * WetBankScale" in editor_source
    assert "const int32 BandCount = 0" in editor_source
    assert "const float BandWidth = Spec.bDesertCanyon ? 54.0f" in editor_source
    assert "constexpr int32 XTiles = 44" in editor_source
    assert "constexpr int32 YTiles = 16" in editor_source
    assert "const int32 RillCount = Spec.bDesertCanyon ? 30" in editor_source
    assert "const int32 PatchCount = Spec.bDesertCanyon ? 48" in editor_source
    assert "const int32 LayerCount = Spec.bDesertCanyon ? 26" in editor_source
    assert "const int32 FacetCount = Spec.bDesertCanyon ? 30" in editor_source
    assert "const int32 BandPerSide = Spec.bDesertCanyon ? 4" in editor_source
    assert "const int32 OcclusionCount = Spec.bDesertCanyon ? 9" in editor_source
    assert "SourceOverlayPlateArtifactDemotion" in editor_source
    assert "DemotedSourceAerialMicrotileWeight" in editor_source
    assert "SourceOverlayMicrotileEdgeLiftCm" in editor_source
    assert "const float SourceOverlayPlateArtifactDemotion = 0.72f" in editor_source
    assert "const float TileZOffset = 56.0f" in editor_source
    assert "PaleBankMaterialSlashDemotion" in editor_source
    assert "TerrainMaterialOverlayPlateDemotion" in editor_source
    assert "PaleLandscapeScaffoldSlashDemotion" in editor_source
    assert "LandscapeNaniteOverlayPlateDemotion" in editor_source
    assert "SourceNormal.Z < 0.0f" in editor_source
    assert "GetPreviewTerrainNormalSofteningBlend" in editor_source
    assert "SoftenPreviewTerrainNormals" in editor_source
    assert "SampleLumaBilinear" in editor_source
    assert "HeightfieldLocalReliefAmplitudeCm" in editor_source
    assert "HeightfieldSeamFeatherUv" in editor_source
    assert "TerrainNormalSofteningBlend" in editor_source
    assert "SourceLocalRelief" in editor_source
    assert "source_terrain_macro_amplitude_cm" in editor_source
    assert "source_terrain_local_relief_amplitude_cm" in editor_source
    assert "source_terrain_seam_feather_uv" in editor_source
    assert "source_terrain_normal_softening_blend" in editor_source
    assert "GetPreviewWaterMaterialResponse" in editor_source
    assert "MeshNormalUpBlend" in editor_source
    assert "Normals = ComputePreviewMeshNormals(Vertices, Triangles);" in editor_source
    assert 'FMaterialParameterInfo(TEXT("EmissiveFillScale"))' in editor_source
    assert 'FMaterialParameterInfo(TEXT("SpecularLevel"))' in editor_source
    assert "UMaterialExpressionFrac" in editor_source
    assert "AtlasNormalSeamBlend" in editor_source
    assert "HalfPeriodOffset->R = 0.5f" in editor_source
    assert "SeamContinuousNormal" in editor_source
    assert "water_material_emissive_fill_scale" in editor_source
    assert "water_material_roughness_scale" in editor_source
    assert "water_material_roughness_floor" in editor_source
    assert "water_material_specular_level" in editor_source
    assert "water_material_normal_intensity" in editor_source
    assert "water_mesh_normal_up_blend" in editor_source
    assert "Constant->R = 0.22f" in editor_source
    assert "Constant->R = 0.10f" in editor_source
    assert "AddPreviewShallowWaterClarityAndAerationDetail" in editor_source
    assert "RaftSim_ShallowWaterClarityBand" in editor_source
    assert "RaftSim_ShallowWaterAerationBubbleLace" in editor_source
    assert "AddPreviewFlowDependentHydraulicAerationAndSprayDetail" in editor_source
    assert "RaftSim_FlowDependentHydraulicAerationMat" in editor_source
    assert "RaftSim_FlowDependentWaveTrainFoamLace" in editor_source
    assert "RaftSim_FlowDependentSprayBead" in editor_source
    assert "HazardReadabilityOpacityLimit" in editor_source
    assert "FirstPartyLitWaterNormalResponseEmissiveFill = 0.38f" in editor_source
    assert "FRaftSimPhotographicCaptureSettings" in editor_source
    assert "GetPhotographicCaptureSettings" in editor_source
    assert "CaptureSettings.SunIntensity" in editor_source
    assert "CaptureSettings.SkyLightIntensity" in editor_source
    assert "CaptureSettings.FogDensity" in editor_source
    assert "CaptureSettings.ExposureBias" in editor_source
    assert "CaptureSettings.Saturation" in editor_source
    assert "CaptureSettings.Contrast" in editor_source
    assert "float FilmGrainIntensity = 0.0f" in editor_source
    assert "bOverride_FilmGrainIntensity" in editor_source
    assert "GEngine->DefaultFilmGrainTexture" not in editor_source
    assert "bApplyFirstPartyCaptureFilmGrainDither" in editor_source
    assert "const bool bApplyFirstPartyCaptureFilmGrainDither = false" in editor_source
    assert "FirstPartyCaptureFilmGrainDitherSeed" in editor_source
    assert "FirstPartyCaptureFilmGrainDitherStrength" in editor_source
    assert "Settings.ExposureBias = -0.12f" in editor_source
    assert "Settings.ExposureBias = -0.18f" in editor_source
    assert "constexpr int32 XSteps = 640" in editor_source
    assert "constexpr int32 CrossSteps = 81" in editor_source
    assert "FirstPartyCaptureQualityWaterTextureCell" in editor_source
    assert "FirstPartyCaptureQualityWaterMicroReliefCm" in editor_source
    assert "RiverEyeCenterCoverCaptureQualityTextureCell" in editor_source
    assert "RiverEyeCenterCoverCaptureQualityMicroReliefCm" in editor_source
    assert "AddPreviewNearFieldPhotorealReviewDressing" in editor_source
    assert "RaftSim_NearFieldCaptureQualityWaterTexture" in editor_source
    assert "RaftSim_NearFieldCaptureQualityFoamLace" in editor_source
    assert "RaftSim_NearFieldRiverbedPebbleDressing" in editor_source
    assert "RaftSim_NearFieldRiverbedDebrisDressing" in editor_source
    assert "DisablePreviewProceduralMeshCollision" in editor_source
    assert "RaftSim_MidFieldSourceColorBankDrape" in editor_source
    assert "RaftSim_CaptureQualityBankTextureFlecks" in editor_source
    assert "bUseSeparateCaptureQualityWaterFleckCards = false" in editor_source
    assert "RaftSim_CaptureQualityWaterTextureFlecks" in editor_source
    assert "IntegratedWaterFleckCell" in editor_source
    assert "IntegratedWaterFleckColor" in editor_source
    assert "IntegratedWaterEntropyEdgeCell" in editor_source
    assert "ApplyPreviewIntegratedTerrainCorridorTexture" in editor_source
    assert "IntegratedTerrainCorridorTextureCell" in editor_source
    assert "NearCameraWaterEntropyCell" in editor_source
    assert "IntegratedBankEntropyPatchSeed" in editor_source
    assert (
        "const bool bUseTemporaryRiverEyeCenterArtifactCover = false" in editor_source
    )
    assert (
        "river_specific_recorded_capture_photometry_no_camera_film_grain"
        in editor_source
    )
    assert "CaptureComponent->PostProcessBlendWeight = 1.0f" in editor_source
    assert (
        "bUseSeparateSourceAwareWaterChromaMicrobreakupGeometry = false"
        in editor_source
    )
    assert "RaftSim_SourceAwareWaterChromaMicrobreakup" in editor_source
    assert "IntegratedWaterShaderChromaCell" in editor_source
    assert "IntegratedWaterShaderChromaReliefCm" in editor_source
    assert "NearFieldWaterPatchTileBreakupDemotionT" in editor_source
    assert "ContinuousNearFieldWaterCurrentBlendT" in editor_source
    assert "ContinuousNearFieldCurrentThread" in editor_source
    assert "ContinuousNearFieldCurrentColor" in editor_source
    assert "ContinuousNearFieldWaterFineChromaThread" in editor_source
    assert "ContinuousFineCurrentColor" in editor_source
    assert "river water keeps generated vertex-current color" in editor_source
    assert "review-material atlas/source texture weights culled" in editor_source
    assert "NearFieldCurrentOliveMottle" in editor_source
    assert "NearFieldWaterSurfaceGrainT" in editor_source
    assert "NearFieldFineRippleAmplitudeCm" in editor_source
    assert "NearFieldDarkSlick" in editor_source
    assert "NearCameraWaterMacroRippleMottleT" in editor_source
    assert "bUsePhysicalCandidateShading ? 0.0f : 0.48f" in editor_source
    assert "NearCameraWaterMacroRippleReliefT" in editor_source
    assert "NearCameraWaterMacroRippleShadow" in editor_source
    assert "NearCameraWaterMacroRippleHighlight" in editor_source
    assert "NearCameraWaterMacroRippleSeamGuardT" in editor_source
    assert "RiverEyeCenterCoverMacroRippleMottleT" in editor_source
    assert "RiverEyeCenterCoverPaletteSeed" in editor_source
    assert "RiverEyeCenterCoverLongBandNoise" in editor_source
    assert "RiverEyeCenterCoverLongBandColor" in editor_source
    assert "const float LongDarkWaterStreakDemotion = 0.0f" in editor_source
    assert "BaseWaterDepthCurrentGradingT" in editor_source
    assert "BaseWaterCurrentTongueT" in editor_source
    assert "BaseWaterSedimentThreadT" in editor_source
    assert "BaseWaterSkyThreadT" in editor_source
    assert "BaseWaterResidualCenterSeamEraseT" in editor_source
    assert "BaseWaterResidualCenterSeamReliefDampingT" in editor_source
    assert "BaseWaterResidualDarkStreakLumaFloor" in editor_source
    assert "DarkMicroRippleArtifactDemotion" in editor_source
    assert "ResidualCenterFlowTextureRibbonCullT" in editor_source
    assert "CenterHydraulicLaneMinimum" in editor_source
    assert "ResidualCenterWaterShaderPlateDemotion" in editor_source
    assert "ResidualCenterShaderScaffoldEraseT" in editor_source
    assert "base-water residual center-seam erase" in editor_source
    assert (
        "const float NearCameraWaterScaffoldClearanceMinX = 25200.0f" in editor_source
    )
    assert "const int32 RefractionSeamCount = 0" in editor_source
    assert "constexpr int32 CrossSteps = 13" in editor_source
    assert "AddPreviewIrregularShorelineEdgeBreakupDetail" in editor_source
    assert "RaftSim_IrregularShorelineEdgeBreakup" in editor_source
    assert "AddPreviewTerrainErosionRillDetail" in editor_source
    assert "RaftSim_TerrainErosionRill" in editor_source
    assert "AddPreviewRaftForeground" in editor_source
    assert "FForegroundRaftProxyHiddenState" in editor_source
    assert "FComponentHiddenState" in editor_source
    assert "CaptureComponent->HideComponent(PrimitiveComponent)" in editor_source
    assert "PrimitiveComponent->SetVisibility(false, true)" in editor_source
    assert "PrimitiveComponent->SetHiddenInGame(true, true)" in editor_source
    assert "AddPreviewRiverEyeCenterArtifactCover" in editor_source
    assert "RaftSim_RiverEyeCenterArtifactCover" in editor_source
    assert "RiverEyeCenterlineFollowingYawDeg" in editor_source
    assert "RiverEyeTargetX" in editor_source
    assert "RiverEyeTexturedCenterCoverT" in editor_source
    assert "RiverEyeCenterCoverFlowMottleGain" in editor_source
    assert "RiverEyeCenterCoverDeepCurrentColor" in editor_source
    assert "RiverEyeCenterCoverSkyHighlightColor" in editor_source
    assert "constexpr int32 CrossSteps = 48" in editor_source
    assert "DestroyRiverEyeCenterArtifactCover" in editor_source
    assert "SetActorHiddenInGame(true)" in editor_source
    assert "SetIsTemporarilyHiddenInEditor(true)" in editor_source
    assert "RestoreForegroundRaftProxyVisibility" in editor_source
    assert "RaftSim_ForegroundRaft_OarShaft" in editor_source
    assert "RaftSim_ForegroundRaft_OarShaftRounded" in editor_source
    assert "RaftSim_ForegroundRaft_OarBlade" in editor_source
    assert "RaftSim_ForegroundRaft_BowLine" in editor_source
    assert "RaftSim_ForegroundRaft_BowLineRounded" in editor_source
    assert "RaftSim_ForegroundRaft_TubeSeam" in editor_source
    assert "RaftSim_ForegroundRaft_BowRounded" in editor_source
    assert "RaftSim_ForegroundRaft_FrameBarRounded" in editor_source
    assert "TubeHighlightColor" in editor_source
    assert "HideActorComponents" in editor_source
    assert "Actor->Tags.AddUnique(ForegroundRaftProxyTag)" in editor_source
    assert "Actor->ActorHasTag(ForegroundRaftProxyTag)" in editor_source
    assert "CaptureComponent->HiddenActors.AddUnique(Actor)" in editor_source
    assert "bCullReviewOnlyForegroundRaftForGuideSeatCaptures = true" in editor_source
    assert (
        "bCullReviewOnlyForegroundRaftForFlowVariantGuideSeatCaptures = true"
        in editor_source
    )
    assert (
        "bCreateReviewOnlyForegroundRaftProxyInLifelikeCandidateMaps = false"
        in editor_source
    )
    assert "Skipped review-only foreground raft/oar proxy generation" in editor_source
    assert (
        "lifelike-candidate maps skip placeholder raft/oar proxy generation"
        in editor_source
    )
    assert "RaftSim_RiverEye_DownstreamCaptureCamera" in editor_source
    assert 'TEXT("RaftSim_RiverEye_DownstreamCaptureCamera")' in editor_source
    assert "NearFieldWaterSourceTileDemotionT" in editor_source
    assert "NearCameraBottomCenterWaterWedgeDemotionT" in editor_source
    assert "NearCameraBottomCenterWaterWedgeLongitudinalT" in editor_source
    assert "NearCameraBottomCenterWaterWedgeLateralT" in editor_source
    assert "NearCameraBottomCenterWaterWedgeArtifactDemotion" in editor_source
    assert "NearCameraBottomCenterWaterWedgeLumaFloor" in editor_source
    assert "NearCameraUpstreamWaterApronMinX" in editor_source
    assert "NearFieldCaptureQualityWaterApronMinX" in editor_source
    assert "HasReviewOnlyForegroundToken" in editor_source
    assert "ComponentUsesReviewOnlyForegroundMaterial" in editor_source
    assert "CulledReviewOnlyForegroundComponentCount" in editor_source
    assert "RaftForegroundReview" in editor_source
    assert "NearFieldInboardBankShelfCullT" in editor_source
    assert "ContinuousNearFieldBankShelfRailDemotion" in editor_source
    assert "NearCameraInWaterDebrisOcclusionCullT" in editor_source
    assert "AddPreviewProceduralBankTextureCards" in editor_source
    assert "RaftSim_MaskAwareGroundCover" in editor_source
    assert "RaftSim_MaskAwareCanopyCard" in editor_source
    assert "FoliageT" in editor_source
    assert "lit water variation" in editor_source
    assert "SourceDrapeColor" in editor_source
    assert "DrapeWeight" in editor_source
    assert "NormalizePreviewSourceDrapeAlbedo" in editor_source
    assert "MicrotileSubdivisions = 8" in editor_source
    assert "RaftSim_SourceAerialDrapeMicroTile" in editor_source
    assert "ColorStrataNoise" in editor_source
    assert "RiverSurfacePatchSeed" in editor_source
    assert "MaterialStrataNoise" in editor_source
    assert "CanyonStrataColor" in editor_source
    assert "GradientBandCount = Spec.bDesertCanyon ? 6" in editor_source
    assert "RemainingAtmosphericCardCull = 0.16f" in editor_source
    assert "SamplePreviewBankUndercutShelfReliefCm" in editor_source
    assert "ContactFoamStrength" in editor_source
    assert "Editor.CheckForWorldGCLeaksAreFatal" in editor_source
    assert "first_party_procedural_environment_assets.json" in editor_source
    assert "first_party_procedural_material_recipes.json" in editor_source
    assert "first_party_material_texture_atlas_manifest.json" in editor_source
    assert "first_party_material_instance_candidates.json" in editor_source
    assert "first_party_production_detail_texture_manifest.json" in editor_source
    assert "CreateProductionDetailMaterialTextureAssets" in editor_source
    assert "TerrainDetailAlbedo" in editor_source
    assert "TerrainDetailNormal" in editor_source
    assert "TerrainDetailAORoughnessHeight" in editor_source
    assert "TerrainDetailUvScale" in editor_source
    assert "TerrainDetailUvOffset" in editor_source
    assert "AtlasTileOrigin" in editor_source
    assert "AtlasTileScale" in editor_source
    assert (
        "const bool bCreateLegacyTerrainOverlayProxyGeometry = false" in editor_source
    )
    assert "const bool bCreateLegacyWaterOverlayProxyGeometry = false" in editor_source
    assert "RaftSimSkipPhotorealFlowVariantCaptures" in editor_source
    assert "production_geospatial_attachment_ledger.json" in editor_source
    assert "procedural_asset_plan" in editor_source
    assert "procedural_material_recipe_plan" in editor_source
    assert "first_party_material_texture_atlas_manifest" in editor_source
    assert "first_party_material_instance_candidate_manifest" in editor_source
    assert "first_party_material_texture_asset_root" in editor_source
    assert "first_party_material_texture_asset_status" in editor_source
    assert "first_party_atlas_sampler_review_material" in editor_source
    assert "first_party_atlas_sampler_review_material_status" in editor_source
    assert "first_party_material_instance_review_asset_root" in editor_source
    assert "first_party_material_instance_review_asset_status" in editor_source
    assert "first_party_material_instance_scene_assignment_status" in editor_source
    assert "UTexture2D" in editor_source
    assert "CreateFirstPartyMaterialTextureAtlasAssets" in editor_source
    assert "T_RaftSim_%s_%s" in editor_source
    assert "TC_Normalmap" in editor_source
    assert "TC_Masks" in editor_source
    assert "TEXTUREGROUP_WorldNormalMap" in editor_source
    assert "UMaterialInstanceConstant" in editor_source
    assert "M_RaftSim_AtlasSampleReview" in editor_source
    assert "LoadOrCreateFirstPartyAtlasSampleReviewMaterial" in editor_source
    assert "UMaterialExpressionTextureSampleParameter2D" in editor_source
    assert "UMaterialExpressionTextureCoordinate" in editor_source
    assert "UMaterialExpressionLinearInterpolate" in editor_source
    assert "UMaterialExpressionComponentMask" in editor_source
    assert "PixelDepthOffset" in editor_source
    assert "AmbientOcclusion" in editor_source
    assert "CreateFirstPartyMaterialInstanceCandidateAssets" in editor_source
    assert "MI_RaftSim_%s_%s_AtlasCandidate" in editor_source
    assert "SetParentEditorOnly" in editor_source
    assert "SetTextureParameterValueEditorOnly" in editor_source
    assert "AlbedoAtlas" in editor_source
    assert "NormalAtlas" in editor_source
    assert "AORoughnessHeightAtlas" in editor_source
    assert "AtlasTileOriginScale" in editor_source
    assert "ReviewAssetOnlyNotLifelike" in editor_source
    assert "PreviewColor" in editor_source
    assert "VertexColorWeight" in editor_source
    assert "RoughnessFloor" in editor_source
    assert "AssignFirstPartyMaterialInstancesToPreviewScene" in editor_source
    assert "geospatial_attachment_ledger" in editor_source
    assert "Missing first-party procedural environment asset plan" in editor_source
    assert "Missing first-party procedural material recipe plan" in editor_source
    assert "Missing first-party material texture atlas manifest" in editor_source
    assert "Missing first-party material instance candidate manifest" in editor_source
    assert "Missing production geospatial attachment ledger" in editor_source
    assert water_review["schema"] == "raftsim.unreal.water_material_candidate_review.v1"
    assert water_review["status"] == (
        "solver_surface_default_lit_landscape_candidate_captured_review_only"
    )
    assert (
        water_review["active_decision"]["active_material"]
        == "/Game/RaftSim/Materials/M_RaftSim_VertexColorWaterPreview"
    )
    assert water_review["active_decision"]["landscape_candidate_material"] == (
        "/Game/RaftSim/Materials/LandscapeCandidates/M_RaftSim_SolverSurfaceWaterCandidate"
    )
    assert (
        "Opaque DefaultLit surface shading"
        in water_review["active_decision"]["solver_surface_water_contract"]
    )
    assert "accepted whole-window median finite-volume C++ frame" in (
        water_review["active_decision"]["solver_surface_water_contract"]
    )
    assert (
        "procedural ribbon mesh is continuous"
        in water_review["active_decision"]["observed_result"]
    )
    assert water_review["single_layer_depth_split_failure"]["decision"].startswith(
        "Keep Single Layer Water assets inactive"
    )
    assert water_review["test_run"]["clean_start_material_compile_failures"] == 0
    assert water_review["test_run"]["photoreal_asset_tests"] == "26 passed"
    assert water_review["test_run"]["solver_visualization_manifest"] == str(
        SOLVER_VISUALIZATION_FIELD_MANIFEST_RELATIVE_PATH
    )
    assert "near-black river surface" in water_review["observed_failure"]["summary"]
