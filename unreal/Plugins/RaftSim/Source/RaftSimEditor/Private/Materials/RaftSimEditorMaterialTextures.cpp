#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
FString GetFirstPartyMaterialTextureAssetBindingKey(const FString& RiverId, const FString& MapKey)
{
    return FString::Printf(TEXT("%s|%s"), *RiverId, *MapKey);
}

bool LoadPreviewPngBgraPixels(const FString& RelativePath, int32& OutWidth, int32& OutHeight, TArray<FColor>& OutPixels)
{
    OutWidth = 0;
    OutHeight = 0;
    OutPixels.Reset();
    if (RelativePath.IsEmpty())
    {
        return false;
    }

    const FString AbsolutePath = FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), RelativePath));
    TArray<uint8> CompressedImage;
    if (!FFileHelper::LoadFileToArray(CompressedImage, *AbsolutePath))
    {
        UE_LOG(LogRaftSimEditorEnvironment, Warning, TEXT("Failed to load first-party material PNG: %s"), *AbsolutePath);
        return false;
    }

    IImageWrapperModule& ImageWrapperModule =
        FModuleManager::LoadModuleChecked<IImageWrapperModule>(FName(TEXT("ImageWrapper")));
    TSharedPtr<IImageWrapper> ImageWrapper = ImageWrapperModule.CreateImageWrapper(EImageFormat::PNG, *AbsolutePath);
    if (!ImageWrapper.IsValid() || !ImageWrapper->SetCompressed(CompressedImage.GetData(), CompressedImage.Num()))
    {
        UE_LOG(LogRaftSimEditorEnvironment, Warning, TEXT("Failed to decode first-party material PNG header: %s"), *AbsolutePath);
        return false;
    }

    TArray<uint8> RawBgra;
    if (!ImageWrapper->GetRaw(ERGBFormat::BGRA, 8, RawBgra))
    {
        UE_LOG(LogRaftSimEditorEnvironment, Warning, TEXT("Failed to decode first-party material PNG pixels: %s"), *AbsolutePath);
        return false;
    }

    OutWidth = ImageWrapper->GetWidth();
    OutHeight = ImageWrapper->GetHeight();
    if (OutWidth <= 0 || OutHeight <= 0 || RawBgra.Num() != OutWidth * OutHeight * 4)
    {
        UE_LOG(LogRaftSimEditorEnvironment, Warning, TEXT("First-party material PNG dimensions are invalid: %s"), *AbsolutePath);
        OutWidth = 0;
        OutHeight = 0;
        return false;
    }

    OutPixels.Reserve(OutWidth * OutHeight);
    for (int32 PixelIndex = 0; PixelIndex < OutWidth * OutHeight; ++PixelIndex)
    {
        const int32 ByteIndex = PixelIndex * 4;
        OutPixels.Add(FColor(
            RawBgra[ByteIndex + 2],
            RawBgra[ByteIndex + 1],
            RawBgra[ByteIndex],
            RawBgra[ByteIndex + 3]));
    }

    return true;
}

TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> GetFirstPartyMaterialTextureAtlasAssetSpecs()
{
    struct FRiverSpec
    {
        const TCHAR* RiverId;
        const TCHAR* RiverAssetName;
    };

    const FRiverSpec RiverSpecs[] = {
        {TEXT("american_south_fork"), TEXT("AmericanSouthFork")},
        {TEXT("colorado_river"), TEXT("ColoradoRiver")},
        {TEXT("pacuare"), TEXT("Pacuare")},
        {TEXT("zambezi_batoka_gorge"), TEXT("Zambezi")},
        {TEXT("futaleufu_terminator"), TEXT("Futaleufu")},
        {TEXT("chilko_river_lava_canyon"), TEXT("Chilko")},
    };

    TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> Specs;
    for (const FRiverSpec& RiverSpec : RiverSpecs)
    {
        FRaftSimFirstPartyMaterialTextureAssetSpec Albedo;
        Albedo.RiverId = RiverSpec.RiverId;
        Albedo.RiverAssetName = RiverSpec.RiverAssetName;
        Albedo.MapKey = TEXT("AlbedoAtlas");
        Albedo.MapKind = TEXT("albedo");
        Albedo.SourceRelativePath = GetFirstPartyMaterialTextureAtlasAlbedoRelativePath(RiverSpec.RiverId);
        Albedo.CompressionSettings = TC_Default;
        Albedo.bSRGB = true;
        Albedo.LODGroup = TEXTUREGROUP_World;
        Specs.Add(Albedo);

        FRaftSimFirstPartyMaterialTextureAssetSpec Normal;
        Normal.RiverId = RiverSpec.RiverId;
        Normal.RiverAssetName = RiverSpec.RiverAssetName;
        Normal.MapKey = TEXT("NormalAtlas");
        Normal.MapKind = TEXT("normal");
        Normal.SourceRelativePath = GetFirstPartyMaterialTextureAtlasNormalRelativePath(RiverSpec.RiverId);
        Normal.CompressionSettings = TC_Normalmap;
        Normal.bSRGB = false;
        Normal.LODGroup = TEXTUREGROUP_WorldNormalMap;
        Specs.Add(Normal);

        FRaftSimFirstPartyMaterialTextureAssetSpec Packed;
        Packed.RiverId = RiverSpec.RiverId;
        Packed.RiverAssetName = RiverSpec.RiverAssetName;
        Packed.MapKey = TEXT("AORoughnessHeightAtlas");
        Packed.MapKind = TEXT("ao_roughness_height");
        Packed.SourceRelativePath = GetFirstPartyMaterialTextureAtlasPackedRelativePath(RiverSpec.RiverId);
        Packed.CompressionSettings = TC_Masks;
        Packed.bSRGB = false;
        Packed.LODGroup = TEXTUREGROUP_World;
        Specs.Add(Packed);

        FRaftSimFirstPartyMaterialTextureAssetSpec NormalDetail;
        NormalDetail.RiverId = RiverSpec.RiverId;
        NormalDetail.RiverAssetName = RiverSpec.RiverAssetName;
        NormalDetail.MapKey = TEXT("SourceConditionedNormalDetail");
        NormalDetail.MapKind = TEXT("source_conditioned_normal_detail");
        NormalDetail.SourceRelativePath =
            GetSourceConditionedMaterialMapRelativePath(RiverSpec.RiverId, NormalDetail.MapKey);
        NormalDetail.TextureAssetRootPackagePath = TEXT("/Game/RaftSim/Rendering/SourceConditionedMaterialMaps/Textures");
        NormalDetail.CompressionSettings = TC_Normalmap;
        NormalDetail.bSRGB = false;
        NormalDetail.LODGroup = TEXTUREGROUP_WorldNormalMap;
        Specs.Add(NormalDetail);
    }

    return Specs;
}

TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> GetSourceConditionedMaterialTextureAssetSpecs()
{
    struct FRiverSpec
    {
        const TCHAR* RiverId;
        const TCHAR* RiverAssetName;
    };

    const FRiverSpec RiverSpecs[] = {
        {TEXT("american_south_fork"), TEXT("AmericanSouthFork")},
        {TEXT("colorado_river"), TEXT("ColoradoRiver")},
        {TEXT("pacuare"), TEXT("Pacuare")},
        {TEXT("zambezi_batoka_gorge"), TEXT("Zambezi")},
        {TEXT("futaleufu_terminator"), TEXT("Futaleufu")},
        {TEXT("chilko_river_lava_canyon"), TEXT("Chilko")},
    };

    TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> Specs;
    for (const FRiverSpec& RiverSpec : RiverSpecs)
    {
        FRaftSimFirstPartyMaterialTextureAssetSpec MacroAlbedo;
        MacroAlbedo.RiverId = RiverSpec.RiverId;
        MacroAlbedo.RiverAssetName = RiverSpec.RiverAssetName;
        MacroAlbedo.MapKey = TEXT("SourceConditionedMacroAlbedo");
        MacroAlbedo.MapKind = TEXT("source_conditioned_macro_albedo");
        MacroAlbedo.SourceRelativePath = GetSourceConditionedMaterialMapRelativePath(RiverSpec.RiverId, MacroAlbedo.MapKey);
        MacroAlbedo.TextureAssetRootPackagePath = TEXT("/Game/RaftSim/Rendering/SourceConditionedMaterialMaps/Textures");
        MacroAlbedo.CompressionSettings = TC_Default;
        MacroAlbedo.bSRGB = true;
        MacroAlbedo.LODGroup = TEXTUREGROUP_World;
        Specs.Add(MacroAlbedo);

        FRaftSimFirstPartyMaterialTextureAssetSpec MaterialZones;
        MaterialZones.RiverId = RiverSpec.RiverId;
        MaterialZones.RiverAssetName = RiverSpec.RiverAssetName;
        MaterialZones.MapKey = TEXT("SourceConditionedMaterialZones");
        MaterialZones.MapKind = TEXT("source_conditioned_material_zones");
        MaterialZones.SourceRelativePath =
            GetSourceConditionedMaterialMapRelativePath(RiverSpec.RiverId, MaterialZones.MapKey);
        MaterialZones.TextureAssetRootPackagePath = TEXT("/Game/RaftSim/Rendering/SourceConditionedMaterialMaps/Textures");
        MaterialZones.CompressionSettings = TC_Masks;
        MaterialZones.bSRGB = false;
        MaterialZones.LODGroup = TEXTUREGROUP_World;
        Specs.Add(MaterialZones);

        FRaftSimFirstPartyMaterialTextureAssetSpec Packed;
        Packed.RiverId = RiverSpec.RiverId;
        Packed.RiverAssetName = RiverSpec.RiverAssetName;
        Packed.MapKey = TEXT("SourceConditionedAORoughnessHeight");
        Packed.MapKind = TEXT("source_conditioned_ao_roughness_height");
        Packed.SourceRelativePath = GetSourceConditionedMaterialMapRelativePath(RiverSpec.RiverId, Packed.MapKey);
        Packed.TextureAssetRootPackagePath = TEXT("/Game/RaftSim/Rendering/SourceConditionedMaterialMaps/Textures");
        Packed.CompressionSettings = TC_Masks;
        Packed.bSRGB = false;
        Packed.LODGroup = TEXTUREGROUP_World;
        Specs.Add(Packed);
    }

    struct FPhysicalCorridorTextureSpec
    {
        const TCHAR* RiverId;
        const TCHAR* RiverAssetName;
        const TCHAR* SourceRoot;
        const TCHAR* FilenamePrefix;
        const TCHAR* AlbedoSuffix;
    };
    const FPhysicalCorridorTextureSpec PhysicalCorridors[] = {
        {
            TEXT("american_south_fork"),
            TEXT("AmericanSouthFork"),
            TEXT("physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
                 "chili_bar_reach_0_2500m/derived"),
            TEXT("south_fork_chili_bar_reach"),
            TEXT("source_albedo_2048.png")
        },
        {
            TEXT("colorado_river"),
            TEXT("ColoradoRiver"),
            TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/production_corridor/"
                 "lees_ferry_reach_2200_4700m/derived"),
            TEXT("colorado_lees_ferry_reach"),
            TEXT("terrain_albedo_2048.png")
        },
        {
            TEXT("zambezi_batoka_gorge"),
            TEXT("Zambezi"),
            TEXT("physics/data/real_world/zambezi_batoka_gorge/production_corridor/"
                 "boiling_pot_to_mukuni_beach/derived"),
            TEXT("zambezi_batoka_gorge"),
            TEXT("source_albedo_2048.png")
        },
        {
            TEXT("futaleufu_terminator"),
            TEXT("Futaleufu"),
            TEXT("physics/data/real_world/futaleufu_river_chile/production_corridor/"
                 "rio_azul_swinging_bridge_to_pasarela/derived"),
            TEXT("futaleufu_terminator"),
            TEXT("source_albedo_2048.png")
        },
        {
            TEXT("chilko_river_lava_canyon"),
            TEXT("Chilko"),
            TEXT("physics/data/real_world/chilko_river_bc/production_corridor/"
                 "chilko_river_lodge_to_taseko_junction/derived"),
            TEXT("chilko_river_lava_canyon"),
            TEXT("source_albedo_2048.png")
        }
    };
    for (const FPhysicalCorridorTextureSpec& Corridor : PhysicalCorridors)
    {
        FRaftSimFirstPartyMaterialTextureAssetSpec PhysicalAlbedo;
        PhysicalAlbedo.RiverId = Corridor.RiverId;
        PhysicalAlbedo.RiverAssetName = Corridor.RiverAssetName;
        PhysicalAlbedo.MapKey = TEXT("PhysicalCorridorSourceAlbedo");
        PhysicalAlbedo.MapKind = TEXT("physical_corridor_source_albedo");
        PhysicalAlbedo.SourceRelativePath = FPaths::Combine(
            Corridor.SourceRoot,
            FString::Printf(TEXT("%s_%s"), Corridor.FilenamePrefix, Corridor.AlbedoSuffix));
        PhysicalAlbedo.TextureAssetRootPackagePath =
            TEXT("/Game/RaftSim/Rendering/PhysicalCorridor/Textures");
        PhysicalAlbedo.CompressionSettings = TC_Default;
        PhysicalAlbedo.bSRGB = true;
        PhysicalAlbedo.LODGroup = TEXTUREGROUP_World;
        PhysicalAlbedo.AddressX = TA_Clamp;
        PhysicalAlbedo.AddressY = TA_Clamp;
        Specs.Add(PhysicalAlbedo);

        FRaftSimFirstPartyMaterialTextureAssetSpec PhysicalZones = PhysicalAlbedo;
        PhysicalZones.MapKey = TEXT("PhysicalCorridorMaterialZones");
        PhysicalZones.MapKind = TEXT("physical_corridor_material_zones");
        PhysicalZones.SourceRelativePath = FPaths::Combine(
            Corridor.SourceRoot,
            FString::Printf(TEXT("%s_material_zones_2048.png"), Corridor.FilenamePrefix));
        PhysicalZones.CompressionSettings = TC_Masks;
        PhysicalZones.bSRGB = false;
        Specs.Add(PhysicalZones);

        FRaftSimFirstPartyMaterialTextureAssetSpec PhysicalNormal = PhysicalAlbedo;
        PhysicalNormal.MapKey = TEXT("PhysicalCorridorNormal");
        PhysicalNormal.MapKind = TEXT("physical_corridor_normal");
        PhysicalNormal.SourceRelativePath = FPaths::Combine(
            Corridor.SourceRoot,
            FString::Printf(TEXT("%s_normal_2048.png"), Corridor.FilenamePrefix));
        PhysicalNormal.CompressionSettings = TC_Normalmap;
        PhysicalNormal.bSRGB = false;
        PhysicalNormal.LODGroup = TEXTUREGROUP_WorldNormalMap;
        Specs.Add(PhysicalNormal);

        FRaftSimFirstPartyMaterialTextureAssetSpec PhysicalPacked = PhysicalAlbedo;
        PhysicalPacked.MapKey = TEXT("PhysicalCorridorAORoughnessHeight");
        PhysicalPacked.MapKind = TEXT("physical_corridor_ao_roughness_height");
        PhysicalPacked.SourceRelativePath = FPaths::Combine(
            Corridor.SourceRoot,
            FString::Printf(TEXT("%s_ao_roughness_height_2048.png"), Corridor.FilenamePrefix));
        PhysicalPacked.CompressionSettings = TC_Masks;
        PhysicalPacked.bSRGB = false;
        Specs.Add(PhysicalPacked);
    }

    return Specs;
}

TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> GetProductionDetailMaterialTextureAssetSpecs()
{
    struct FRiverSpec
    {
        const TCHAR* RiverId;
        const TCHAR* RiverAssetName;
    };

    const FRiverSpec RiverSpecs[] = {
        {TEXT("american_south_fork"), TEXT("AmericanSouthFork")},
        {TEXT("colorado_river"), TEXT("ColoradoRiver")},
        {TEXT("pacuare"), TEXT("Pacuare")},
        {TEXT("zambezi_batoka_gorge"), TEXT("Zambezi")},
        {TEXT("futaleufu_terminator"), TEXT("Futaleufu")},
        {TEXT("chilko_river_lava_canyon"), TEXT("Chilko")},
    };

    TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> Specs;
    for (const FRiverSpec& RiverSpec : RiverSpecs)
    {
        FRaftSimFirstPartyMaterialTextureAssetSpec Albedo;
        Albedo.RiverId = RiverSpec.RiverId;
        Albedo.RiverAssetName = RiverSpec.RiverAssetName;
        Albedo.MapKey = TEXT("TerrainDetailAlbedo");
        Albedo.MapKind = TEXT("first_party_terrain_detail_albedo");
        Albedo.SourceRelativePath = GetProductionDetailTextureRelativePath(RiverSpec.RiverId, Albedo.MapKey);
        Albedo.TextureAssetRootPackagePath = TEXT("/Game/RaftSim/Rendering/ProductionDetailTextures/Textures");
        Albedo.CompressionSettings = TC_Default;
        Albedo.bSRGB = true;
        Albedo.LODGroup = TEXTUREGROUP_World;
        Specs.Add(Albedo);

        FRaftSimFirstPartyMaterialTextureAssetSpec Normal;
        Normal.RiverId = RiverSpec.RiverId;
        Normal.RiverAssetName = RiverSpec.RiverAssetName;
        Normal.MapKey = TEXT("TerrainDetailNormal");
        Normal.MapKind = TEXT("first_party_terrain_detail_normal");
        Normal.SourceRelativePath = GetProductionDetailTextureRelativePath(RiverSpec.RiverId, Normal.MapKey);
        Normal.TextureAssetRootPackagePath = TEXT("/Game/RaftSim/Rendering/ProductionDetailTextures/Textures");
        Normal.CompressionSettings = TC_Normalmap;
        Normal.bSRGB = false;
        Normal.LODGroup = TEXTUREGROUP_WorldNormalMap;
        Specs.Add(Normal);

        FRaftSimFirstPartyMaterialTextureAssetSpec Packed;
        Packed.RiverId = RiverSpec.RiverId;
        Packed.RiverAssetName = RiverSpec.RiverAssetName;
        Packed.MapKey = TEXT("TerrainDetailAORoughnessHeight");
        Packed.MapKind = TEXT("first_party_terrain_detail_ao_roughness_height");
        Packed.SourceRelativePath = GetProductionDetailTextureRelativePath(RiverSpec.RiverId, Packed.MapKey);
        Packed.TextureAssetRootPackagePath = TEXT("/Game/RaftSim/Rendering/ProductionDetailTextures/Textures");
        Packed.CompressionSettings = TC_Masks;
        Packed.bSRGB = false;
        Packed.LODGroup = TEXTUREGROUP_World;
        Specs.Add(Packed);
    }

    return Specs;
}

TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> GetSolverVisualizationFieldTextureAssetSpecs()
{
    TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> Specs;

    FRaftSimFirstPartyMaterialTextureAssetSpec Normal;
    Normal.RiverId = TEXT("american_south_fork");
    Normal.RiverAssetName = TEXT("AmericanSouthFork");
    Normal.MapKey = TEXT("CppSolverSurfaceNormal");
    Normal.MapKind = TEXT("validated_cpp_solver_surface_normal");
    Normal.SourceRelativePath =
        TEXT("unreal/Content/RaftSim/Rendering/SolverVisualizationFields/"
             "american_south_fork_median_cpp_solver_surface_normal_v1.png");
    Normal.TextureAssetRootPackagePath = TEXT("/Game/RaftSim/Rendering/SolverVisualizationFields/Textures");
    Normal.CompressionSettings = TC_Normalmap;
    Normal.bSRGB = false;
    Normal.LODGroup = TEXTUREGROUP_WorldNormalMap;
    Normal.AddressX = TA_Clamp;
    Normal.AddressY = TA_Clamp;
    Specs.Add(Normal);

    FRaftSimFirstPartyMaterialTextureAssetSpec Packed;
    Packed.RiverId = TEXT("american_south_fork");
    Packed.RiverAssetName = TEXT("AmericanSouthFork");
    Packed.MapKey = TEXT("CppSolverDepthSpeedFroude");
    Packed.MapKind = TEXT("validated_cpp_solver_depth_speed_froude");
    Packed.SourceRelativePath =
        TEXT("unreal/Content/RaftSim/Rendering/SolverVisualizationFields/"
             "american_south_fork_median_cpp_solver_depth_speed_froude_v1.png");
    Packed.TextureAssetRootPackagePath = TEXT("/Game/RaftSim/Rendering/SolverVisualizationFields/Textures");
    Packed.CompressionSettings = TC_Masks;
    Packed.bSRGB = false;
    Packed.LODGroup = TEXTUREGROUP_World;
    Packed.AddressX = TA_Clamp;
    Packed.AddressY = TA_Clamp;
    Packed.bCompressionNoAlpha = false;
    Specs.Add(Packed);

    return Specs;
}

TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> GetFutaleufuNativeCanopyTextureAssetSpecs()
{
    static const TCHAR* SourceRoot =
        TEXT("unreal/Content/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/Textures");
    static const TCHAR* AssetRoot =
        TEXT("/Game/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/Textures");

    TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> Specs;
    auto AddSpec = [&Specs](
                       const TCHAR* MapKey,
                       const TCHAR* MapKind,
                       const TCHAR* Filename,
                       TextureCompressionSettings Compression,
                       bool bSRGB,
                       TextureGroup LODGroup,
                       TextureAddress Address,
                       bool bPreserveAlpha)
    {
        FRaftSimFirstPartyMaterialTextureAssetSpec Spec;
        Spec.RiverId = TEXT("futaleufu_native_canopy");
        Spec.RiverAssetName = TEXT("FutaleufuCoigue");
        Spec.MapKey = MapKey;
        Spec.MapKind = MapKind;
        Spec.SourceRelativePath = FPaths::Combine(SourceRoot, Filename);
        Spec.TextureAssetRootPackagePath = AssetRoot;
        Spec.CompressionSettings = Compression;
        Spec.bSRGB = bSRGB;
        Spec.LODGroup = LODGroup;
        Spec.AddressX = Address;
        Spec.AddressY = Address;
        Spec.bCompressionNoAlpha = !bPreserveAlpha;
        Specs.Add(Spec);
    };

    AddSpec(
        TEXT("BarkAlbedo"),
        TEXT("coigue_bark_albedo"),
        TEXT("coigue_bark_v1_albedo.png"),
        TC_Default,
        true,
        TEXTUREGROUP_World,
        TA_Wrap,
        false);
    AddSpec(
        TEXT("BarkNormal"),
        TEXT("coigue_bark_normal"),
        TEXT("coigue_bark_v1_normal.png"),
        TC_Normalmap,
        false,
        TEXTUREGROUP_WorldNormalMap,
        TA_Wrap,
        false);
    AddSpec(
        TEXT("BarkAORoughnessHeight"),
        TEXT("coigue_bark_ao_roughness_height"),
        TEXT("coigue_bark_v1_ao_roughness_height.png"),
        TC_Masks,
        false,
        TEXTUREGROUP_World,
        TA_Wrap,
        false);
    AddSpec(
        TEXT("LeafAlbedoOpacity"),
        TEXT("coigue_leaf_albedo_opacity"),
        TEXT("coigue_leaf_atlas_v2_albedo_opacity.png"),
        TC_Default,
        true,
        TEXTUREGROUP_World,
        TA_Clamp,
        true);
    AddSpec(
        TEXT("LeafNormal"),
        TEXT("coigue_leaf_normal"),
        TEXT("coigue_leaf_atlas_v2_normal.png"),
        TC_Normalmap,
        false,
        TEXTUREGROUP_WorldNormalMap,
        TA_Clamp,
        false);
    AddSpec(
        TEXT("LeafAORoughnessSubsurface"),
        TEXT("coigue_leaf_ao_roughness_subsurface"),
        TEXT("coigue_leaf_atlas_v2_ao_roughness_subsurface.png"),
        TC_Masks,
        false,
        TEXTUREGROUP_World,
        TA_Clamp,
        false);
    return Specs;
}

TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> GetFutaleufuCordilleraCypressTextureAssetSpecs()
{
    static const TCHAR* SourceRoot =
        TEXT("unreal/Content/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/"
             "CordilleraCypress/Textures");
    static const TCHAR* AssetRoot =
        TEXT("/Game/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/"
             "CordilleraCypress/Textures");

    TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> Specs;
    auto AddSpec = [&Specs](
                       const TCHAR* MapKey,
                       const TCHAR* MapKind,
                       const TCHAR* Filename,
                       TextureCompressionSettings Compression,
                       bool bSRGB,
                       TextureGroup LODGroup,
                       TextureAddress Address,
                       bool bPreserveAlpha)
    {
        FRaftSimFirstPartyMaterialTextureAssetSpec Spec;
        Spec.RiverId = TEXT("futaleufu_native_canopy_cypress");
        Spec.RiverAssetName = TEXT("FutaleufuCordilleraCypress");
        Spec.MapKey = MapKey;
        Spec.MapKind = MapKind;
        Spec.SourceRelativePath = FPaths::Combine(SourceRoot, Filename);
        Spec.TextureAssetRootPackagePath = AssetRoot;
        Spec.CompressionSettings = Compression;
        Spec.bSRGB = bSRGB;
        Spec.LODGroup = LODGroup;
        Spec.AddressX = Address;
        Spec.AddressY = Address;
        Spec.bCompressionNoAlpha = !bPreserveAlpha;
        Specs.Add(Spec);
    };

    AddSpec(
        TEXT("BarkAlbedo"), TEXT("cordillera_cypress_bark_albedo"),
        TEXT("cordillera_cypress_bark_v3_albedo.png"),
        TC_Default, true, TEXTUREGROUP_World, TA_Wrap, false);
    AddSpec(
        TEXT("BarkNormal"), TEXT("cordillera_cypress_bark_normal"),
        TEXT("cordillera_cypress_bark_v3_normal.png"),
        TC_Normalmap, false, TEXTUREGROUP_WorldNormalMap, TA_Wrap, false);
    AddSpec(
        TEXT("BarkAORoughnessHeight"), TEXT("cordillera_cypress_bark_ao_roughness_height"),
        TEXT("cordillera_cypress_bark_v3_ao_roughness_height.png"),
        TC_Masks, false, TEXTUREGROUP_World, TA_Wrap, false);
    AddSpec(
        TEXT("FarLeafAlbedoOpacity"), TEXT("cordillera_cypress_far_spray_albedo_opacity"),
        TEXT("cordillera_cypress_spray_v3_albedo_opacity.png"),
        TC_Default, true, TEXTUREGROUP_World, TA_Clamp, true);
    AddSpec(
        TEXT("FarLeafNormal"), TEXT("cordillera_cypress_far_spray_normal"),
        TEXT("cordillera_cypress_spray_v3_normal.png"),
        TC_Normalmap, false, TEXTUREGROUP_WorldNormalMap, TA_Clamp, false);
    AddSpec(
        TEXT("FarLeafAORoughnessSubsurface"),
        TEXT("cordillera_cypress_far_spray_ao_roughness_subsurface"),
        TEXT("cordillera_cypress_spray_v3_ao_roughness_subsurface.png"),
        TC_Masks, false, TEXTUREGROUP_World, TA_Clamp, false);
    AddSpec(
        TEXT("NearLeafAlbedoOpacity"), TEXT("cordillera_cypress_near_spray_albedo_opacity"),
        TEXT("cordillera_cypress_spray_v10_albedo_opacity.png"),
        TC_Default, true, TEXTUREGROUP_World, TA_Clamp, true);
    AddSpec(
        TEXT("NearLeafNormal"), TEXT("cordillera_cypress_near_spray_normal"),
        TEXT("cordillera_cypress_spray_v10_normal.png"),
        TC_Normalmap, false, TEXTUREGROUP_WorldNormalMap, TA_Clamp, false);
    AddSpec(
        TEXT("NearLeafAORoughnessSubsurface"),
        TEXT("cordillera_cypress_near_spray_ao_roughness_subsurface"),
        TEXT("cordillera_cypress_spray_v10_ao_roughness_subsurface.png"),
        TC_Masks, false, TEXTUREGROUP_World, TA_Clamp, false);
    AddSpec(
        TEXT("TwigLeafAlbedoOpacity"), TEXT("cordillera_cypress_twig_albedo_opacity"),
        TEXT("cordillera_cypress_twig_v18_albedo_opacity.png"),
        TC_Default, true, TEXTUREGROUP_World, TA_Clamp, true);
    AddSpec(
        TEXT("TwigLeafNormal"), TEXT("cordillera_cypress_twig_normal"),
        TEXT("cordillera_cypress_twig_v18_normal.png"),
        TC_Normalmap, false, TEXTUREGROUP_WorldNormalMap, TA_Clamp, false);
    AddSpec(
        TEXT("TwigLeafAORoughnessSubsurface"),
        TEXT("cordillera_cypress_twig_ao_roughness_subsurface"),
        TEXT("cordillera_cypress_twig_v18_ao_roughness_subsurface.png"),
        TC_Masks, false, TEXTUREGROUP_World, TA_Clamp, false);
    AddSpec(
        TEXT("ScaleLeafAlbedoOpacity"), TEXT("cordillera_cypress_scale_leaf_albedo_opacity"),
        TEXT("cordillera_cypress_scale_leaf_v19_albedo_opacity.png"),
        TC_Default, true, TEXTUREGROUP_World, TA_Clamp, true);
    AddSpec(
        TEXT("ScaleLeafNormal"), TEXT("cordillera_cypress_scale_leaf_normal"),
        TEXT("cordillera_cypress_scale_leaf_v19_normal.png"),
        TC_Normalmap, false, TEXTUREGROUP_WorldNormalMap, TA_Clamp, false);
    AddSpec(
        TEXT("ScaleLeafAORoughnessSubsurface"),
        TEXT("cordillera_cypress_scale_leaf_ao_roughness_subsurface"),
        TEXT("cordillera_cypress_scale_leaf_v19_ao_roughness_subsurface.png"),
        TC_Masks, false, TEXTUREGROUP_World, TA_Clamp, false);
    AddSpec(
        TEXT("BotanicalSprayAlbedoOpacity"),
        TEXT("cordillera_cypress_botanical_spray_albedo_opacity"),
        TEXT("cordillera_cypress_botanical_spray_v20_albedo_opacity.png"),
        TC_Default, true, TEXTUREGROUP_World, TA_Clamp, true);
    AddSpec(
        TEXT("BotanicalSprayNormal"),
        TEXT("cordillera_cypress_botanical_spray_normal"),
        TEXT("cordillera_cypress_botanical_spray_v20_normal.png"),
        TC_Normalmap, false, TEXTUREGROUP_WorldNormalMap, TA_Clamp, false);
    AddSpec(
        TEXT("BotanicalSprayAORoughnessSubsurface"),
        TEXT("cordillera_cypress_botanical_spray_ao_roughness_subsurface"),
        TEXT("cordillera_cypress_botanical_spray_v20_ao_roughness_subsurface.png"),
        TC_Masks, false, TEXTUREGROUP_World, TA_Clamp, false);
    AddSpec(
        TEXT("CompoundBranchletAlbedoOpacity"),
        TEXT("cordillera_cypress_compound_branchlet_albedo_opacity"),
        TEXT("cordillera_cypress_compound_branchlet_v21_albedo_opacity.png"),
        TC_Default, true, TEXTUREGROUP_World, TA_Clamp, true);
    AddSpec(
        TEXT("CompoundBranchletNormal"),
        TEXT("cordillera_cypress_compound_branchlet_normal"),
        TEXT("cordillera_cypress_compound_branchlet_v21_normal.png"),
        TC_Normalmap, false, TEXTUREGROUP_WorldNormalMap, TA_Clamp, false);
    AddSpec(
        TEXT("CompoundBranchletAORoughnessSubsurface"),
        TEXT("cordillera_cypress_compound_branchlet_ao_roughness_subsurface"),
        TEXT("cordillera_cypress_compound_branchlet_v21_ao_roughness_subsurface.png"),
        TC_Masks, false, TEXTUREGROUP_World, TA_Clamp, false);
    return Specs;
}

void ApplyFirstPartyMaterialTextureImportSettings(
    UTexture2D* Texture,
    const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec)
{
    if (!Texture)
    {
        return;
    }

    Texture->SRGB = Spec.bSRGB;
    Texture->CompressionSettings = Spec.CompressionSettings;
    const bool bNativeCanopyLeafTexture =
        Spec.RiverId.StartsWith(TEXT("futaleufu_native_canopy")) &&
        (Spec.MapKey.Contains(TEXT("Leaf")) ||
         Spec.MapKey.StartsWith(TEXT("BotanicalSpray")) ||
         Spec.MapKey.StartsWith(TEXT("CompoundBranchlet")));
    const bool bSouthForkGeneratedCanopyTexture =
        Spec.RiverId == TEXT("south_fork_generated_canopy") &&
        Spec.MapKey == TEXT("BillboardAlbedoOpacity");
    const bool bMaskedCanopyTexture =
        bNativeCanopyLeafTexture || bSouthForkGeneratedCanopyTexture;
    Texture->MipGenSettings = bMaskedCanopyTexture ? TMGS_Sharpen5 : TMGS_FromTextureGroup;
    Texture->LODGroup = Spec.LODGroup;
    Texture->AddressX = Spec.AddressX;
    Texture->AddressY = Spec.AddressY;
    Texture->CompressionNoAlpha = Spec.bCompressionNoAlpha;
    Texture->DeferCompression = false;
    Texture->VirtualTextureStreaming = false;
    Texture->NeverStream = bMaskedCanopyTexture;
    const bool bMaskedLeafAlbedo = bSouthForkGeneratedCanopyTexture ||
        (bNativeCanopyLeafTexture &&
         (Spec.MapKey.EndsWith(TEXT("LeafAlbedoOpacity")) ||
          Spec.MapKey == TEXT("BotanicalSprayAlbedoOpacity") ||
          Spec.MapKey == TEXT("CompoundBranchletAlbedoOpacity")));
    Texture->bDoScaleMipsForAlphaCoverage = bMaskedLeafAlbedo;
    const float AlphaCoverageThreshold =
        (Spec.MapKey == TEXT("BotanicalSprayAlbedoOpacity") ||
         Spec.MapKey == TEXT("CompoundBranchletAlbedoOpacity"))
            ? 0.42f
            : 0.50f;
    Texture->AlphaCoverageThresholds = bMaskedLeafAlbedo
        ? FVector4(0.0f, 0.0f, 0.0f, AlphaCoverageThreshold)
        : FVector4(0.0f, 0.0f, 0.0f, 0.0f);
    Texture->SetModernSettingsForNewOrChangedTexture();
}

bool UpdateFirstPartyMaterialTextureSource(
    UTexture2D* Texture,
    const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec,
    int32 Width,
    int32 Height,
    const TArray<FColor>& Pixels)
{
    if (!Texture || Width <= 0 || Height <= 0 || Pixels.Num() != Width * Height)
    {
        return false;
    }

    Texture->Modify();
    Texture->PreEditChange(nullptr);
    // Empty cached platform data can retain a matching DDC key and bypass source rebuilding.
    Texture->ReleaseResource();
    FlushRenderingCommands();
    Texture->SetPlatformData(nullptr);
    Texture->Source.Init(Width, Height, 1, 1, TSF_BGRA8);
    uint8* MipData = Texture->Source.LockMip(0);
    for (int32 Y = 0; Y < Height; ++Y)
    {
        uint8* DestPtr = &MipData[static_cast<int64>(Y) * Width * sizeof(FColor)];
        const FColor* SrcPtr = &Pixels[static_cast<int64>(Y) * Width];
        for (int32 X = 0; X < Width; ++X)
        {
            *DestPtr++ = SrcPtr->B;
            *DestPtr++ = SrcPtr->G;
            *DestPtr++ = SrcPtr->R;
            *DestPtr++ = SrcPtr->A;
            ++SrcPtr;
        }
    }
    Texture->Source.UnlockMip(0);
    ApplyFirstPartyMaterialTextureImportSettings(Texture, Spec);
    Texture->PostEditChange();
    return true;
}

bool RebuildAndValidateFirstPartyTexturePlatformData(
    UTexture2D* Texture,
    const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec,
    FString& OutSummary)
{
    if (!Texture)
    {
        return false;
    }

    Texture->BlockOnAnyAsyncBuild();
    const UTexture::EUpdateResourceFlags RebuildFlags =
        static_cast<UTexture::EUpdateResourceFlags>(
            static_cast<uint32>(UTexture::EUpdateResourceFlags::ForceRebuild) |
            static_cast<uint32>(UTexture::EUpdateResourceFlags::Synchronous));
    Texture->UpdateResourceWithParams(RebuildFlags);
    Texture->BlockOnAnyAsyncBuild();
    FlushRenderingCommands();

    const FTexturePlatformData* PlatformData = Texture->GetPlatformData();
    const int32 MipCount = PlatformData ? PlatformData->Mips.Num() : 0;
    const bool bValid =
        Texture->Source.IsValid() &&
        PlatformData &&
        MipCount > 0 &&
        PlatformData->SizeX == Texture->Source.GetSizeX() &&
        PlatformData->SizeY == Texture->Source.GetSizeY();
    OutSummary += FString::Printf(
        TEXT("%s rebuilt running-platform data for %s/%s: source=%dx%d platform=%dx%d mips=%d.\n"),
        bValid ? TEXT("Validated") : TEXT("Rejected"),
        *Spec.RiverId,
        *Spec.MapKey,
        Texture->Source.GetSizeX(),
        Texture->Source.GetSizeY(),
        PlatformData ? PlatformData->SizeX : 0,
        PlatformData ? PlatformData->SizeY : 0,
        MipCount);
    return bValid;
}

UTexture2D* CreateOrUpdateFirstPartyMaterialTextureAsset(
    const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec,
    FString& OutSummary,
    bool& bOutSaved)
{
    bOutSaved = false;

    int32 Width = 0;
    int32 Height = 0;
    TArray<FColor> Pixels;
    if (!LoadPreviewPngBgraPixels(Spec.SourceRelativePath, Width, Height, Pixels))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to load first-party material texture source %s for %s/%s\n"),
            *Spec.SourceRelativePath,
            *Spec.RiverId,
            *Spec.MapKey);
        return nullptr;
    }

    const FString PackagePath = Spec.GetTextureAssetPath();
    const FString AssetName = FPackageName::GetLongPackageAssetName(PackagePath);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, *AssetName);

    UPackage* Package = CreatePackage(*PackagePath);
    if (!Package)
    {
        OutSummary += FString::Printf(TEXT("Failed to create texture package %s\n"), *PackagePath);
        return nullptr;
    }

    UObject* ExistingObject = StaticLoadObject(UObject::StaticClass(), nullptr, *ObjectPath);
    UTexture2D* Texture = Cast<UTexture2D>(ExistingObject);
    if (!Texture)
    {
        Texture = FindObject<UTexture2D>(Package, *AssetName);
    }
    if (!Texture && ExistingObject)
    {
        OutSummary += FString::Printf(TEXT("Existing first-party material texture asset is not a Texture2D: %s\n"), *ObjectPath);
        return nullptr;
    }
    if (!Texture)
    {
        Texture = NewObject<UTexture2D>(Package, *AssetName, RF_Public | RF_Standalone | RF_Transactional);
        FAssetRegistryModule::AssetCreated(Texture);
    }
    if (!Texture)
    {
        OutSummary += FString::Printf(TEXT("Failed to create first-party material texture asset %s\n"), *ObjectPath);
        return nullptr;
    }

    if (!UpdateFirstPartyMaterialTextureSource(Texture, Spec, Width, Height, Pixels))
    {
        OutSummary += FString::Printf(TEXT("Failed to update first-party material texture source %s\n"), *ObjectPath);
        return nullptr;
    }
    if (Spec.RiverId.StartsWith(TEXT("futaleufu_native_canopy")))
    {
        if (!RebuildAndValidateFirstPartyTexturePlatformData(Texture, Spec, OutSummary))
        {
            OutSummary += FString::Printf(
                TEXT("Failed to build renderable first-party material texture platform data %s\n"),
                *ObjectPath);
            return nullptr;
        }
    }

    Package->MarkPackageDirty();
    const FString Filename =
        FPackageName::LongPackageNameToFilename(PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);

    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;

    bOutSaved = UPackage::SavePackage(Package, Texture, *Filename, SaveArgs);
    OutSummary += FString::Printf(
        TEXT("%s first-party material Texture2D review asset %s (%s/%s) from %s -> %s\n"),
        bOutSaved ? TEXT("Saved") : TEXT("Failed"),
        *ObjectPath,
        *Spec.RiverId,
        *Spec.MapKey,
        *Spec.SourceRelativePath,
        *Filename);
    return bOutSaved ? Texture : nullptr;
}

bool CreateFirstPartyMaterialTextureAtlasAssets(
    TMap<FString, UTexture2D*>& OutTextureAssetsByKey,
    FString& OutSummary,
    const FString& RiverIdFilter)
{
    bool bAllSaved = true;
    OutTextureAssetsByKey.Reset();

    for (const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec : GetFirstPartyMaterialTextureAtlasAssetSpecs())
    {
        if (!RiverIdFilter.IsEmpty() && Spec.RiverId != RiverIdFilter)
        {
            continue;
        }
        bool bSaved = false;
        UTexture2D* Texture = CreateOrUpdateFirstPartyMaterialTextureAsset(Spec, OutSummary, bSaved);
        bAllSaved &= bSaved && Texture != nullptr;
        if (Texture)
        {
            OutTextureAssetsByKey.Add(GetFirstPartyMaterialTextureAssetBindingKey(Spec.RiverId, Spec.MapKey), Texture);
        }
    }

    return bAllSaved;
}

bool CreateSourceConditionedMaterialTextureAssets(
    TMap<FString, UTexture2D*>& InOutTextureAssetsByKey,
    FString& OutSummary,
    const FString& RiverIdFilter)
{
    bool bAllSaved = true;

    for (const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec : GetSourceConditionedMaterialTextureAssetSpecs())
    {
        if (!RiverIdFilter.IsEmpty() && Spec.RiverId != RiverIdFilter)
        {
            continue;
        }
        bool bSaved = false;
        UTexture2D* Texture = CreateOrUpdateFirstPartyMaterialTextureAsset(Spec, OutSummary, bSaved);
        bAllSaved &= bSaved && Texture != nullptr;
        if (Texture)
        {
            InOutTextureAssetsByKey.Add(GetFirstPartyMaterialTextureAssetBindingKey(Spec.RiverId, Spec.MapKey), Texture);
        }
    }

    return bAllSaved;
}

bool CreateProductionDetailMaterialTextureAssets(
    TMap<FString, UTexture2D*>& InOutTextureAssetsByKey,
    FString& OutSummary,
    const FString& RiverIdFilter)
{
    bool bAllSaved = true;

    for (const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec : GetProductionDetailMaterialTextureAssetSpecs())
    {
        if (!RiverIdFilter.IsEmpty() && Spec.RiverId != RiverIdFilter)
        {
            continue;
        }
        bool bSaved = false;
        UTexture2D* Texture = CreateOrUpdateFirstPartyMaterialTextureAsset(Spec, OutSummary, bSaved);
        bAllSaved &= bSaved && Texture != nullptr;
        if (Texture)
        {
            InOutTextureAssetsByKey.Add(GetFirstPartyMaterialTextureAssetBindingKey(Spec.RiverId, Spec.MapKey), Texture);
        }
    }

    return bAllSaved;
}

bool CreateSolverVisualizationFieldTextureAssets(FString& OutSummary)
{
    bool bAllSaved = true;
    for (const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec : GetSolverVisualizationFieldTextureAssetSpecs())
    {
        bool bSaved = false;
        UTexture2D* Texture = CreateOrUpdateFirstPartyMaterialTextureAsset(Spec, OutSummary, bSaved);
        bAllSaved &= bSaved && Texture != nullptr;
    }
    return bAllSaved;
}

bool CreateFutaleufuNativeCanopyTextureAssets(
    TMap<FString, UTexture2D*>& OutTextureAssetsByKey,
    FString& OutSummary)
{
    bool bAllSaved = true;
    OutTextureAssetsByKey.Reset();
    for (const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec : GetFutaleufuNativeCanopyTextureAssetSpecs())
    {
        bool bSaved = false;
        UTexture2D* Texture = CreateOrUpdateFirstPartyMaterialTextureAsset(Spec, OutSummary, bSaved);
        bAllSaved &= bSaved && Texture != nullptr;
        if (Texture)
        {
            OutTextureAssetsByKey.Add(Spec.MapKey, Texture);
        }
    }
    TArray<UTexture*> NativeCanopyTextures;
    for (const TPair<FString, UTexture2D*>& Pair : OutTextureAssetsByKey)
    {
        if (Pair.Value)
        {
            NativeCanopyTextures.Add(Pair.Value);
        }
    }
    FTextureCompilingManager::Get().FinishCompilation(NativeCanopyTextures);
    for (UTexture* Texture : NativeCanopyTextures)
    {
        Texture->BlockOnAnyAsyncBuild();
        Texture->SetForceMipLevelsToBeResident(120.0f);
    }
    FlushRenderingCommands();
    OutSummary += FString::Printf(
        TEXT("Finished compilation and forced residency for %d native-canopy textures before material build.\n"),
        NativeCanopyTextures.Num());
    return bAllSaved;
}

bool CreateFutaleufuCordilleraCypressTextureAssets(
    TMap<FString, UTexture2D*>& OutTextureAssetsByKey,
    FString& OutSummary)
{
    bool bAllSaved = true;
    OutTextureAssetsByKey.Reset();
    for (const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec :
         GetFutaleufuCordilleraCypressTextureAssetSpecs())
    {
        bool bSaved = false;
        UTexture2D* Texture = CreateOrUpdateFirstPartyMaterialTextureAsset(
            Spec, OutSummary, bSaved);
        bAllSaved &= bSaved && Texture != nullptr;
        if (Texture)
        {
            OutTextureAssetsByKey.Add(Spec.MapKey, Texture);
        }
    }
    TArray<UTexture*> NativeCanopyTextures;
    for (const TPair<FString, UTexture2D*>& Pair : OutTextureAssetsByKey)
    {
        if (Pair.Value)
        {
            NativeCanopyTextures.Add(Pair.Value);
        }
    }
    FTextureCompilingManager::Get().FinishCompilation(NativeCanopyTextures);
    for (UTexture* Texture : NativeCanopyTextures)
    {
        Texture->BlockOnAnyAsyncBuild();
        Texture->SetForceMipLevelsToBeResident(120.0f);
    }
    FlushRenderingCommands();
    OutSummary += FString::Printf(
        TEXT("Finished compilation and forced residency for %d cordilleran-cypress textures.\n"),
        NativeCanopyTextures.Num());
    return bAllSaved;
}

UMaterialExpression* AddComplementaryScreenDitherOpacity(
    UMaterial* Material,
    UMaterialExpression* BaseOpacity,
    int32 BaseOpacityOutputIndex,
    bool bKeepSourceSide,
    float DefaultSourceCoverage,
    int32 EditorX,
    int32 EditorY)
{
    if (!Material || !BaseOpacity)
    {
        return nullptr;
    }
    UMaterialExpressionScalarParameter* SourceCoverage =
        NewObject<UMaterialExpressionScalarParameter>(Material);
    SourceCoverage->MaterialExpressionEditorX = EditorX - 260;
    SourceCoverage->MaterialExpressionEditorY = EditorY + 120;
    SourceCoverage->ParameterName = TEXT("ComplementarySourceCoverage");
    SourceCoverage->DefaultValue = DefaultSourceCoverage;
    SourceCoverage->SliderMin = 0.0f;
    SourceCoverage->SliderMax = 1.0f;
    Material->GetExpressionCollection().AddExpression(SourceCoverage);

    UMaterialExpressionScalarParameter* PatternSize =
        NewObject<UMaterialExpressionScalarParameter>(Material);
    PatternSize->MaterialExpressionEditorX = EditorX - 260;
    PatternSize->MaterialExpressionEditorY = EditorY + 200;
    PatternSize->ParameterName = TEXT("ComplementaryPatternSize");
    PatternSize->DefaultValue = 4.0f;
    PatternSize->SliderMin = 4.0f;
    PatternSize->SliderMax = 8.0f;
    Material->GetExpressionCollection().AddExpression(PatternSize);

    UMaterialExpressionCustom* DitherMask = NewObject<UMaterialExpressionCustom>(Material);
    DitherMask->MaterialExpressionEditorX = EditorX;
    DitherMask->MaterialExpressionEditorY = EditorY;
    DitherMask->Description = bKeepSourceSide
        ? TEXT("Keep the source side of a deterministic complementary 4x4 or 8x8 screen dither")
        : TEXT("Keep the HLOD side of a deterministic complementary 4x4 or 8x8 screen dither");
    DitherMask->OutputType = CMOT_Float1;
    DitherMask->Code = bKeepSourceSide
        ? TEXT("float2 Pixel = floor(Parameters.SvPosition.xy);\n")
          TEXT("float2 Cell4 = fmod(Pixel, 4.0);\n")
          TEXT("float Rank4 = Cell4.y < 0.5 ? (Cell4.x < 0.5 ? 0.0 : (Cell4.x < 1.5 ? 8.0 : (Cell4.x < 2.5 ? 2.0 : 10.0))) :\n")
          TEXT("              Cell4.y < 1.5 ? (Cell4.x < 0.5 ? 12.0 : (Cell4.x < 1.5 ? 4.0 : (Cell4.x < 2.5 ? 14.0 : 6.0))) :\n")
          TEXT("              Cell4.y < 2.5 ? (Cell4.x < 0.5 ? 3.0 : (Cell4.x < 1.5 ? 11.0 : (Cell4.x < 2.5 ? 1.0 : 9.0))) :\n")
          TEXT("                                (Cell4.x < 0.5 ? 15.0 : (Cell4.x < 1.5 ? 7.0 : (Cell4.x < 2.5 ? 13.0 : 5.0)));\n")
          TEXT("float2 Cell8 = fmod(Pixel, 8.0);\n")
          TEXT("float X0 = fmod(Cell8.x, 2.0); float Y0 = fmod(Cell8.y, 2.0);\n")
          TEXT("float X1 = fmod(floor(Cell8.x / 2.0), 2.0); float Y1 = fmod(floor(Cell8.y / 2.0), 2.0);\n")
          TEXT("float X2 = floor(Cell8.x / 4.0); float Y2 = floor(Cell8.y / 4.0);\n")
          TEXT("float Rank8 = 16.0 * (2.0 * fmod(X2 + Y2, 2.0) + Y2) + 4.0 * (2.0 * fmod(X1 + Y1, 2.0) + Y1) + (2.0 * fmod(X0 + Y0, 2.0) + Y0);\n")
          TEXT("float Use8 = step(7.5, PatternSize);\n")
          TEXT("float Rank = lerp(Rank4, Rank8, Use8); float LevelCount = lerp(16.0, 64.0, Use8);\n")
          TEXT("float Keep = Rank < saturate(SourceCoverage) * LevelCount ? 1.0 : 0.0;\n")
          TEXT("return BaseOpacity * Keep;")
        : TEXT("float2 Pixel = floor(Parameters.SvPosition.xy);\n")
          TEXT("float2 Cell4 = fmod(Pixel, 4.0);\n")
          TEXT("float Rank4 = Cell4.y < 0.5 ? (Cell4.x < 0.5 ? 0.0 : (Cell4.x < 1.5 ? 8.0 : (Cell4.x < 2.5 ? 2.0 : 10.0))) :\n")
          TEXT("              Cell4.y < 1.5 ? (Cell4.x < 0.5 ? 12.0 : (Cell4.x < 1.5 ? 4.0 : (Cell4.x < 2.5 ? 14.0 : 6.0))) :\n")
          TEXT("              Cell4.y < 2.5 ? (Cell4.x < 0.5 ? 3.0 : (Cell4.x < 1.5 ? 11.0 : (Cell4.x < 2.5 ? 1.0 : 9.0))) :\n")
          TEXT("                                (Cell4.x < 0.5 ? 15.0 : (Cell4.x < 1.5 ? 7.0 : (Cell4.x < 2.5 ? 13.0 : 5.0)));\n")
          TEXT("float2 Cell8 = fmod(Pixel, 8.0);\n")
          TEXT("float X0 = fmod(Cell8.x, 2.0); float Y0 = fmod(Cell8.y, 2.0);\n")
          TEXT("float X1 = fmod(floor(Cell8.x / 2.0), 2.0); float Y1 = fmod(floor(Cell8.y / 2.0), 2.0);\n")
          TEXT("float X2 = floor(Cell8.x / 4.0); float Y2 = floor(Cell8.y / 4.0);\n")
          TEXT("float Rank8 = 16.0 * (2.0 * fmod(X2 + Y2, 2.0) + Y2) + 4.0 * (2.0 * fmod(X1 + Y1, 2.0) + Y1) + (2.0 * fmod(X0 + Y0, 2.0) + Y0);\n")
          TEXT("float Use8 = step(7.5, PatternSize);\n")
          TEXT("float Rank = lerp(Rank4, Rank8, Use8); float LevelCount = lerp(16.0, 64.0, Use8);\n")
          TEXT("float Keep = Rank >= saturate(SourceCoverage) * LevelCount ? 1.0 : 0.0;\n")
          TEXT("return BaseOpacity * Keep;");
    FCustomInput& BaseOpacityInput = DitherMask->Inputs.AddDefaulted_GetRef();
    BaseOpacityInput.InputName = TEXT("BaseOpacity");
    BaseOpacityInput.Input.Expression = BaseOpacity;
    BaseOpacityInput.Input.OutputIndex = BaseOpacityOutputIndex;
    FCustomInput& CoverageInput = DitherMask->Inputs.AddDefaulted_GetRef();
    CoverageInput.InputName = TEXT("SourceCoverage");
    CoverageInput.Input.Expression = SourceCoverage;
    FCustomInput& PatternSizeInput = DitherMask->Inputs.AddDefaulted_GetRef();
    PatternSizeInput.InputName = TEXT("PatternSize");
    PatternSizeInput.Input.Expression = PatternSize;
    Material->GetExpressionCollection().AddExpression(DitherMask);

    UMaterialFunctionInterface* TemporalDitherFunction =
        LoadObject<UMaterialFunctionInterface>(
            nullptr,
            TEXT("/Engine/Functions/Engine_MaterialFunctions02/Utility/"
                 "DitherTemporalAA.DitherTemporalAA"));
    UMaterialExpressionMaterialFunctionCall* TemporalDither =
        NewObject<UMaterialExpressionMaterialFunctionCall>(Material);
    if (!TemporalDitherFunction ||
        !TemporalDither->SetMaterialFunction(TemporalDitherFunction) ||
        TemporalDither->FunctionInputs.IsEmpty())
    {
        return DitherMask;
    }
    TemporalDither->MaterialExpressionEditorX = EditorX;
    TemporalDither->MaterialExpressionEditorY = EditorY + 180;
    TemporalDither->FunctionInputs[0].Input.Expression = SourceCoverage;
    Material->GetExpressionCollection().AddExpression(TemporalDither);

    UMaterialExpression* TemporalKeep = TemporalDither;
    if (!bKeepSourceSide)
    {
        UMaterialExpressionOneMinus* InverseTemporalDither =
            NewObject<UMaterialExpressionOneMinus>(Material);
        InverseTemporalDither->MaterialExpressionEditorX = EditorX + 220;
        InverseTemporalDither->MaterialExpressionEditorY = EditorY + 180;
        InverseTemporalDither->Input.Expression = TemporalDither;
        Material->GetExpressionCollection().AddExpression(InverseTemporalDither);
        TemporalKeep = InverseTemporalDither;
    }

    UMaterialExpressionMultiply* TemporalOpacity =
        NewObject<UMaterialExpressionMultiply>(Material);
    TemporalOpacity->MaterialExpressionEditorX = EditorX + 440;
    TemporalOpacity->MaterialExpressionEditorY = EditorY + 160;
    TemporalOpacity->A.Expression = BaseOpacity;
    TemporalOpacity->A.OutputIndex = BaseOpacityOutputIndex;
    TemporalOpacity->B.Expression = TemporalKeep;
    Material->GetExpressionCollection().AddExpression(TemporalOpacity);

    UMaterialExpressionScalarParameter* TransitionMode =
        NewObject<UMaterialExpressionScalarParameter>(Material);
    TransitionMode->MaterialExpressionEditorX = EditorX + 180;
    TransitionMode->MaterialExpressionEditorY = EditorY + 300;
    TransitionMode->ParameterName = TEXT("ComplementaryTransitionMode");
    TransitionMode->DefaultValue = 0.0f;
    TransitionMode->SliderMin = 0.0f;
    TransitionMode->SliderMax = 1.0f;
    Material->GetExpressionCollection().AddExpression(TransitionMode);

    UMaterialExpressionLinearInterpolate* SelectedOpacity =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    SelectedOpacity->MaterialExpressionEditorX = EditorX + 700;
    SelectedOpacity->MaterialExpressionEditorY = EditorY + 40;
    SelectedOpacity->A.Expression = DitherMask;
    SelectedOpacity->B.Expression = TemporalOpacity;
    SelectedOpacity->Alpha.Expression = TransitionMode;
    Material->GetExpressionCollection().AddExpression(SelectedOpacity);
    return SelectedOpacity;
}

UMaterial* CreateOrUpdateFutaleufuNativeCanopyMaterial(
    const FString& AssetName,
    bool bLeafMaterial,
    const TMap<FString, UTexture2D*>& Textures,
    FString& OutSummary,
    bool bDefaultLitLeafDiagnostic,
    const FString& LeafTextureKeyPrefix,
    bool bFreezeWindForDeterministicReview,
    bool bEnableComplementaryTransition)
{
    const FString PackagePath = FString::Printf(
        TEXT("/Game/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/Materials/%s"),
        *AssetName);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, *AssetName);
    UMaterial* Material = LoadObject<UMaterial>(nullptr, *ObjectPath);
    UPackage* Package = Material ? Material->GetOutermost() : CreatePackage(*PackagePath);
    if (!Package)
    {
        OutSummary += FString::Printf(TEXT("Could not create native-canopy material package %s.\n"), *PackagePath);
        return nullptr;
    }
    if (!Material)
    {
        Material = NewObject<UMaterial>(Package, *AssetName, RF_Public | RF_Standalone | RF_Transactional);
        if (Material)
        {
            FAssetRegistryModule::AssetCreated(Material);
        }
    }
    if (!Material)
    {
        OutSummary += FString::Printf(TEXT("Could not create native-canopy material %s.\n"), *ObjectPath);
        return nullptr;
    }

    const bool bFlattenedSprayTexturePrefix =
        LeafTextureKeyPrefix.Equals(TEXT("BotanicalSpray"), ESearchCase::CaseSensitive) ||
        LeafTextureKeyPrefix.Equals(TEXT("CompoundBranchlet"), ESearchCase::CaseSensitive);
    const FString LeafAlbedoKey = LeafTextureKeyPrefix +
        (bFlattenedSprayTexturePrefix ? TEXT("AlbedoOpacity") : TEXT("LeafAlbedoOpacity"));
    const FString LeafNormalKey = LeafTextureKeyPrefix +
        (bFlattenedSprayTexturePrefix ? TEXT("Normal") : TEXT("LeafNormal"));
    const FString LeafPackedKey = LeafTextureKeyPrefix +
        (bFlattenedSprayTexturePrefix
             ? TEXT("AORoughnessSubsurface")
             : TEXT("LeafAORoughnessSubsurface"));
    const bool bNearCordilleraCypress =
        bLeafMaterial &&
        (LeafTextureKeyPrefix.Equals(TEXT("Near"), ESearchCase::CaseSensitive) ||
         LeafTextureKeyPrefix.Equals(TEXT("Twig"), ESearchCase::CaseSensitive) ||
         LeafTextureKeyPrefix.Equals(TEXT("Scale"), ESearchCase::CaseSensitive) ||
         LeafTextureKeyPrefix.Equals(TEXT("BotanicalSpray"), ESearchCase::CaseSensitive) ||
         LeafTextureKeyPrefix.Equals(TEXT("CompoundBranchlet"), ESearchCase::CaseSensitive));
    const bool bFarCordilleraCypress =
        bLeafMaterial && LeafTextureKeyPrefix.Equals(TEXT("Far"), ESearchCase::CaseSensitive);
    const bool bCordilleraCypressBark =
        !bLeafMaterial && AssetName.Contains(TEXT("CordilleraCypress"), ESearchCase::CaseSensitive);
    UTexture2D* Albedo = Textures.FindRef(bLeafMaterial ? LeafAlbedoKey : TEXT("BarkAlbedo"));
    UTexture2D* Normal = Textures.FindRef(bLeafMaterial ? LeafNormalKey : TEXT("BarkNormal"));
    UTexture2D* Packed = Textures.FindRef(
        bLeafMaterial ? LeafPackedKey : TEXT("BarkAORoughnessHeight"));
    if (!Albedo || !Normal || !Packed)
    {
        OutSummary += FString::Printf(TEXT("Native-canopy material %s is missing one or more textures.\n"), *AssetName);
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->SetShadingModel(
        bLeafMaterial && !bDefaultLitLeafDiagnostic
            ? MSM_TwoSidedFoliage
            : MSM_DefaultLit);
    Material->BlendMode = bLeafMaterial || bEnableComplementaryTransition
        ? BLEND_Masked
        : BLEND_Opaque;
    Material->TwoSided = bLeafMaterial;
    Material->OpacityMaskClipValue = bNearCordilleraCypress
        ? 0.42f
        : (bLeafMaterial ? 0.50f : 0.3333f);
    Material->DitheredLODTransition = bLeafMaterial || bEnableComplementaryTransition;

    auto AddExpression = [Material](auto* Expression, int32 EditorX, int32 EditorY)
    {
        Expression->MaterialExpressionEditorX = EditorX;
        Expression->MaterialExpressionEditorY = EditorY;
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    UMaterialExpressionTextureCoordinate* TexCoord =
        AddExpression(NewObject<UMaterialExpressionTextureCoordinate>(Material), -720, -120);
    UMaterialExpressionTextureSampleParameter2D* AlbedoSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -440, -260);
    AlbedoSample->ParameterName = bLeafMaterial ? TEXT("LeafAlbedoOpacity") : TEXT("BarkAlbedo");
    AlbedoSample->Texture = Albedo;
    AlbedoSample->SamplerType = SAMPLERTYPE_Color;
    AlbedoSample->Coordinates.Expression = TexCoord;
    UMaterialExpressionTextureSampleParameter2D* NormalSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -440, 20);
    NormalSample->ParameterName = bLeafMaterial ? TEXT("LeafNormal") : TEXT("BarkNormal");
    NormalSample->Texture = Normal;
    NormalSample->SamplerType = SAMPLERTYPE_Normal;
    NormalSample->Coordinates.Expression = TexCoord;
    UMaterialExpressionTextureSampleParameter2D* PackedSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -440, 280);
    PackedSample->ParameterName =
        bLeafMaterial ? TEXT("LeafAORoughnessSubsurface") : TEXT("BarkAORoughnessHeight");
    PackedSample->Texture = Packed;
    PackedSample->SamplerType = SAMPLERTYPE_Masks;
    PackedSample->Coordinates.Expression = TexCoord;

    UMaterialExpressionComponentMask* PackedAmbientOcclusion =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), -120, 260);
    PackedAmbientOcclusion->Input.Expression = PackedSample;
    PackedAmbientOcclusion->R = 1;
    UMaterialExpressionConstant* FullAmbientOcclusion =
        AddExpression(NewObject<UMaterialExpressionConstant>(Material), 100, 280);
    FullAmbientOcclusion->R = 1.0f;
    UMaterialExpressionScalarParameter* AmbientOcclusionInfluence =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 100, 380);
    AmbientOcclusionInfluence->ParameterName =
        bLeafMaterial ? TEXT("LeafAOInfluence") : TEXT("BarkAOInfluence");
    AmbientOcclusionInfluence->DefaultValue = bNearCordilleraCypress
        ? 0.08f
        : (bFarCordilleraCypress ? 0.45f : (bLeafMaterial ? 0.55f : 0.28f));
    UMaterialExpressionLinearInterpolate* ConditionedAmbientOcclusion =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 340, 300);
    ConditionedAmbientOcclusion->A.Expression = FullAmbientOcclusion;
    ConditionedAmbientOcclusion->B.Expression = PackedAmbientOcclusion;
    ConditionedAmbientOcclusion->Alpha.Expression = AmbientOcclusionInfluence;
    UMaterialExpressionComponentMask* Roughness =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), -120, 380);
    Roughness->Input.Expression = PackedSample;
    Roughness->G = 1;
    UMaterialExpressionConstant* Specular =
        AddExpression(NewObject<UMaterialExpressionConstant>(Material), -120, 520);
    Specular->R = bLeafMaterial ? 0.18f : 0.12f;

    UMaterialExpressionScalarParameter* BaseColorScale =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -120, -240);
    BaseColorScale->ParameterName =
        bLeafMaterial ? TEXT("LeafBaseColorScale") : TEXT("BarkBaseColorScale");
    BaseColorScale->DefaultValue = bNearCordilleraCypress
        ? 2.10f
        : (bFarCordilleraCypress
               ? 0.88f
               : (bLeafMaterial ? 1.18f : (bCordilleraCypressBark ? 1.20f : 1.72f)));
    UMaterialExpressionMultiply* ConditionedBaseColor =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 120, -240);
    ConditionedBaseColor->A.Expression = AlbedoSample;
    ConditionedBaseColor->B.Expression = BaseColorScale;

    UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, ConditionedBaseColor);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->AmbientOcclusion, ConditionedAmbientOcclusion);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, Roughness);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);
    if (bLeafMaterial)
    {
        UMaterialExpressionScalarParameter* OpacityScale =
            AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -120, -420);
        OpacityScale->ParameterName = TEXT("LeafOpacityScale");
        OpacityScale->DefaultValue = 1.0f;
        OpacityScale->SliderMin = 1.0f;
        OpacityScale->SliderMax = 4.0f;
        UMaterialExpressionMultiply* ScaledOpacity =
            AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 120, -420);
        ScaledOpacity->A.Expression = AlbedoSample;
        ScaledOpacity->A.OutputIndex = 4;
        ScaledOpacity->B.Expression = OpacityScale;
        UMaterialExpressionScalarParameter* OpacityOverride =
            AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -120, -500);
        OpacityOverride->ParameterName = TEXT("LeafOpacityOverride");
        OpacityOverride->DefaultValue = 0.0f;
        OpacityOverride->SliderMin = 0.0f;
        OpacityOverride->SliderMax = 1.0f;
        UMaterialExpressionConstant* FullOpacity =
            AddExpression(NewObject<UMaterialExpressionConstant>(Material), 120, -520);
        FullOpacity->R = 1.0f;
        UMaterialExpressionLinearInterpolate* DiagnosticOpacity =
            AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 360, -440);
        DiagnosticOpacity->A.Expression = ScaledOpacity;
        DiagnosticOpacity->B.Expression = FullOpacity;
        DiagnosticOpacity->Alpha.Expression = OpacityOverride;
        UMaterialExpression* FinalOpacity = DiagnosticOpacity;
        if (bEnableComplementaryTransition)
        {
            FinalOpacity = AddComplementaryScreenDitherOpacity(
                Material,
                DiagnosticOpacity,
                0,
                true,
                1.0f,
                620,
                -480);
        }
        ConnectPreviewMaterialScalarInput(EditorOnlyData->OpacityMask, FinalOpacity);

        UMaterialExpressionScalarParameter* NormalStrength =
            AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -120, 60);
        NormalStrength->ParameterName = TEXT("LeafNormalStrength");
        NormalStrength->DefaultValue = 1.0f;
        NormalStrength->SliderMin = 0.0f;
        NormalStrength->SliderMax = 1.0f;
        UMaterialExpressionConstant3Vector* FlatNormal =
            AddExpression(NewObject<UMaterialExpressionConstant3Vector>(Material), -120, 140);
        FlatNormal->Constant = FLinearColor(0.0f, 0.0f, 1.0f);
        UMaterialExpressionLinearInterpolate* ConditionedNormal =
            AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 120, 40);
        ConditionedNormal->A.Expression = FlatNormal;
        ConditionedNormal->B.Expression = NormalSample;
        ConditionedNormal->Alpha.Expression = NormalStrength;
        UMaterialExpressionTwoSidedSign* TwoSidedSign =
            AddExpression(NewObject<UMaterialExpressionTwoSidedSign>(Material), 120, 140);
        UMaterialExpressionMultiply* TwoSidedNormal =
            AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 360, 80);
        TwoSidedNormal->A.Expression = ConditionedNormal;
        TwoSidedNormal->B.Expression = TwoSidedSign;
        ConnectPreviewMaterialVectorInput(EditorOnlyData->Normal, TwoSidedNormal);

        UMaterialExpressionVectorParameter* TransmissionTint =
            AddExpression(NewObject<UMaterialExpressionVectorParameter>(Material), -120, -80);
        TransmissionTint->ParameterName = TEXT("LeafTransmissionTint");
        TransmissionTint->DefaultValue = bNearCordilleraCypress
            ? FLinearColor(0.78f, 1.0f, 0.58f)
            : (bFarCordilleraCypress
                   ? FLinearColor(0.48f, 0.72f, 0.30f)
                   : FLinearColor(0.55f, 0.78f, 0.36f));
        UMaterialExpressionMultiply* SubsurfaceColor =
            AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 120, -120);
        SubsurfaceColor->A.Expression = ConditionedBaseColor;
        SubsurfaceColor->B.Expression = TransmissionTint;
        if (!bDefaultLitLeafDiagnostic)
        {
            ConnectPreviewMaterialColorInput(EditorOnlyData->SubsurfaceColor, SubsurfaceColor);
        }

        UMaterialExpressionScalarParameter* DiagnosticEmissive =
            AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 360, -220);
        DiagnosticEmissive->ParameterName = TEXT("LeafDiagnosticEmissive");
        DiagnosticEmissive->DefaultValue = bNearCordilleraCypress
            ? 0.0f
            : (bFarCordilleraCypress ? 0.018f : 0.0f);
        DiagnosticEmissive->SliderMin = 0.0f;
        DiagnosticEmissive->SliderMax = 0.35f;
        UMaterialExpressionMultiply* DiagnosticEmissiveColor =
            AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 600, -220);
        DiagnosticEmissiveColor->A.Expression = ConditionedBaseColor;
        DiagnosticEmissiveColor->B.Expression = DiagnosticEmissive;
        ConnectPreviewMaterialColorInput(EditorOnlyData->EmissiveColor, DiagnosticEmissiveColor);

        UMaterialExpressionScalarParameter* WindIntensity =
            AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -440, 620);
        WindIntensity->ParameterName = TEXT("WindIntensity");
        WindIntensity->DefaultValue = bFreezeWindForDeterministicReview ? 0.0f : 0.16f;
        UMaterialExpressionScalarParameter* WindWeight =
            AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -440, 700);
        WindWeight->ParameterName = TEXT("WindWeight");
        WindWeight->DefaultValue = bFreezeWindForDeterministicReview ? 0.0f : 0.28f;
        UMaterialExpressionScalarParameter* WindSpeed =
            AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -440, 780);
        WindSpeed->ParameterName = TEXT("WindSpeed");
        WindSpeed->DefaultValue = bFreezeWindForDeterministicReview ? 0.0f : 0.42f;
        UMaterialExpressionConstant3Vector* AdditionalWindOffset =
            AddExpression(NewObject<UMaterialExpressionConstant3Vector>(Material), -440, 860);
        AdditionalWindOffset->Constant = FLinearColor::Black;
        UMaterialFunctionInterface* SimpleGrassWind = LoadObject<UMaterialFunctionInterface>(
            nullptr,
            TEXT("/Engine/Functions/Engine_MaterialFunctions01/WorldPositionOffset/"
                 "SimpleGrassWind.SimpleGrassWind"));
        UMaterialExpressionMaterialFunctionCall* LeafWind =
            AddExpression(NewObject<UMaterialExpressionMaterialFunctionCall>(Material), -80, 700);
        if (SimpleGrassWind && LeafWind->SetMaterialFunction(SimpleGrassWind))
        {
            for (int32 InputIndex = 0; InputIndex < LeafWind->FunctionInputs.Num(); ++InputIndex)
            {
                const FString InputName = LeafWind->GetInputName(InputIndex).ToString();
                FExpressionInput& Input = LeafWind->FunctionInputs[InputIndex].Input;
                if (InputName.Contains(TEXT("WindIntensity"), ESearchCase::IgnoreCase))
                {
                    Input.Expression = WindIntensity;
                }
                else if (InputName.Contains(TEXT("WindWeight"), ESearchCase::IgnoreCase))
                {
                    Input.Expression = WindWeight;
                }
                else if (InputName.Contains(TEXT("WindSpeed"), ESearchCase::IgnoreCase))
                {
                    Input.Expression = WindSpeed;
                }
                else if (InputName.Contains(TEXT("AdditionalWPO"), ESearchCase::IgnoreCase))
                {
                    Input.Expression = AdditionalWindOffset;
                }
            }
            EditorOnlyData->WorldPositionOffset.Expression = LeafWind;
        }
    }
    else
    {
        ConnectPreviewMaterialVectorInput(EditorOnlyData->Normal, NormalSample);
        if (bEnableComplementaryTransition)
        {
            UMaterialExpressionConstant* FullOpacity =
                AddExpression(NewObject<UMaterialExpressionConstant>(Material), 120, -460);
            FullOpacity->R = 1.0f;
            UMaterialExpression* TransitionOpacity =
                AddComplementaryScreenDitherOpacity(
                    Material,
                    FullOpacity,
                    0,
                    true,
                    1.0f,
                    360,
                    -460);
            ConnectPreviewMaterialScalarInput(EditorOnlyData->OpacityMask, TransitionOpacity);
        }
    }

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
        GShaderCompilingManager->ProcessAsyncResults(false, true);
    }
    if (!Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to enable InstancedStaticMeshes material usage for %s.\n"),
            *ObjectPath);
        return nullptr;
    }
    Material->PostEditChange();
    Material->MarkPackageDirty();
    Material->ForceRecompileForRendering();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
        GShaderCompilingManager->ProcessAsyncResults(false, true);
    }
    FMaterialResource* MaterialResource =
        Material->GetMaterialResource(GMaxRHIShaderPlatform);
    if (MaterialResource && !MaterialResource->IsGameThreadShaderMapComplete())
    {
        MaterialResource->SubmitCompileJobs_GameThread(EShaderCompileJobPriority::High);
        MaterialResource->FinishCompilation();
        if (GShaderCompilingManager)
        {
            GShaderCompilingManager->ProcessAsyncResults(false, true);
        }
    }
    MaterialResource = Material->GetMaterialResource(GMaxRHIShaderPlatform);
    if (!MaterialResource ||
        Material->IsCompilingOrHadCompileError(GMaxRHIShaderPlatform) ||
        !MaterialResource->GetCompileErrors().IsEmpty())
    {
        OutSummary += FString::Printf(
            TEXT("Native-canopy material shader gate failed for %s.\n"),
            *ObjectPath);
        return nullptr;
    }
    FlushRenderingCommands();
    const FString Filename =
        FPackageName::LongPackageNameToFilename(PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
    {
        OutSummary += FString::Printf(TEXT("Failed to save native-canopy material %s.\n"), *ObjectPath);
        return nullptr;
    }
    OutSummary += FString::Printf(
        TEXT("Saved %s native-canopy material %s.\n"),
        bLeafMaterial
            ? (bDefaultLitLeafDiagnostic
                   ? TEXT("masked DefaultLit diagnostic")
                   : TEXT("masked TwoSidedFoliage"))
            : (bEnableComplementaryTransition
                   ? TEXT("masked complementary-transition DefaultLit bark")
                   : TEXT("opaque DefaultLit bark")),
        *ObjectPath);
    return Material;
}

UMaterial* CreateOrUpdateFutaleufuCypressNearSprayMaterial(
    const FString& AssetName,
    FString& OutSummary,
    bool bVolumetricScaleLeaves)
{
    const FString PackagePath = FString::Printf(
        TEXT("/Game/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/Materials/%s"),
        *AssetName);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, *AssetName);
    UMaterial* Material = LoadObject<UMaterial>(nullptr, *ObjectPath);
    UPackage* Package = Material ? Material->GetOutermost() : CreatePackage(*PackagePath);
    if (!Package)
    {
        OutSummary += FString::Printf(
            TEXT("Could not create cypress near-spray material package %s.\n"), *PackagePath);
        return nullptr;
    }
    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package, *AssetName, RF_Public | RF_Standalone | RF_Transactional);
        if (Material)
        {
            FAssetRegistryModule::AssetCreated(Material);
        }
    }
    if (!Material)
    {
        OutSummary += FString::Printf(
            TEXT("Could not create cypress near-spray material %s.\n"), *ObjectPath);
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->SetShadingModel(MSM_DefaultLit);
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = false;
    Material->DitheredLODTransition = true;
    auto AddExpression = [Material](auto* Expression, int32 EditorX, int32 EditorY)
    {
        Expression->MaterialExpressionEditorX = EditorX;
        Expression->MaterialExpressionEditorY = EditorY;
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    UMaterialExpressionVectorParameter* BaseColor =
        AddExpression(NewObject<UMaterialExpressionVectorParameter>(Material), -300, -120);
    BaseColor->ParameterName = TEXT("NearSprayBaseColor");
    BaseColor->DefaultValue = bVolumetricScaleLeaves
        ? FLinearColor(0.055f, 0.20f, 0.035f)
        : FLinearColor(0.16f, 0.42f, 0.08f);
    UMaterialExpressionScalarParameter* Roughness =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -300, 20);
    Roughness->ParameterName = TEXT("NearSprayRoughness");
    Roughness->DefaultValue = bVolumetricScaleLeaves ? 0.90f : 0.78f;
    UMaterialExpressionScalarParameter* Specular =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -300, 120);
    Specular->ParameterName = TEXT("NearSpraySpecular");
    Specular->DefaultValue = bVolumetricScaleLeaves ? 0.06f : 0.14f;
    UMaterialExpressionConstant* AmbientOcclusion =
        AddExpression(NewObject<UMaterialExpressionConstant>(Material), -300, 220);
    AmbientOcclusion->R = 1.0f;
    UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, BaseColor);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, Roughness);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->AmbientOcclusion, AmbientOcclusion);

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
    }
    Material->MarkPackageDirty();
    const FString Filename =
        FPackageName::LongPackageNameToFilename(PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to save cypress near-spray material %s.\n"), *ObjectPath);
        return nullptr;
    }
    OutSummary += FString::Printf(
        TEXT("Saved opaque geometric cypress near-spray material %s.\n"), *ObjectPath);
    return Material;
}

UMaterial* CreateOrUpdateFutaleufuCypressFarProxyMaterial(FString& OutSummary)
{
    static const FString AssetName = TEXT("M_RaftSim_FutaleufuCordilleraCypress_V18_FarProxy");
    const FString PackagePath = FString::Printf(
        TEXT("/Game/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/Materials/%s"),
        *AssetName);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, *AssetName);
    UMaterial* Material = LoadObject<UMaterial>(nullptr, *ObjectPath);
    UPackage* Package = Material ? Material->GetOutermost() : CreatePackage(*PackagePath);
    if (!Package)
    {
        OutSummary += FString::Printf(
            TEXT("Could not create cypress far-proxy material package %s.\n"), *PackagePath);
        return nullptr;
    }
    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package, *AssetName, RF_Public | RF_Standalone | RF_Transactional);
        if (Material)
        {
            FAssetRegistryModule::AssetCreated(Material);
        }
    }
    if (!Material)
    {
        OutSummary += FString::Printf(
            TEXT("Could not create cypress far-proxy material %s.\n"), *ObjectPath);
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->SetShadingModel(MSM_DefaultLit);
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = false;
    Material->DitheredLODTransition = true;

    UMaterialExpressionVertexColor* VertexColor =
        NewObject<UMaterialExpressionVertexColor>(Material);
    VertexColor->MaterialExpressionEditorX = -300;
    VertexColor->MaterialExpressionEditorY = -120;
    Material->GetExpressionCollection().AddExpression(VertexColor);
    UMaterialExpressionConstant* Roughness = NewObject<UMaterialExpressionConstant>(Material);
    Roughness->R = 0.94f;
    Roughness->MaterialExpressionEditorX = -300;
    Roughness->MaterialExpressionEditorY = 20;
    Material->GetExpressionCollection().AddExpression(Roughness);
    UMaterialExpressionConstant* Specular = NewObject<UMaterialExpressionConstant>(Material);
    Specular->R = 0.035f;
    Specular->MaterialExpressionEditorX = -300;
    Specular->MaterialExpressionEditorY = 120;
    Material->GetExpressionCollection().AddExpression(Specular);
    UMaterialExpressionConstant* AmbientOcclusion = NewObject<UMaterialExpressionConstant>(Material);
    AmbientOcclusion->R = 0.82f;
    AmbientOcclusion->MaterialExpressionEditorX = -300;
    AmbientOcclusion->MaterialExpressionEditorY = 220;
    Material->GetExpressionCollection().AddExpression(AmbientOcclusion);

    UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, VertexColor);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, Roughness);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->AmbientOcclusion, AmbientOcclusion);

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
    }
    Material->MarkPackageDirty();
    const FString Filename =
        FPackageName::LongPackageNameToFilename(PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to save cypress far-proxy material %s.\n"), *ObjectPath);
        return nullptr;
    }
    OutSummary += FString::Printf(
        TEXT("Saved matte vertex-color cypress far-proxy material %s.\n"), *ObjectPath);
    return Material;
}

bool EnsureFutaleufuNativeCanopyInstancedMaterialUsage(
    UMaterial* Material,
    FString& OutSummary)
{
    if (!Material)
    {
        return false;
    }
    Material->Modify();
    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (!Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes))
    {
        OutSummary += FString::Printf(
            TEXT("Could not enable InstancedStaticMeshes usage for native-canopy material %s.\n"),
            *Material->GetPathName());
        return false;
    }
    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
    }
    UPackage* Package = Material->GetOutermost();
    Package->MarkPackageDirty();
    const FString PackagePath = Package->GetName();
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath,
        FPackageName::GetAssetPackageExtension());
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    const bool bSaved = UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
    OutSummary += FString::Printf(
        TEXT("%s native-canopy InstancedStaticMeshes material usage %s -> %s.\n"),
        bSaved ? TEXT("Persisted") : TEXT("Failed to persist"),
        *Material->GetPathName(),
        *Filename);
    return bSaved;
}

UMaterialInterface* LoadOrCreateFirstPartyAtlasSampleReviewMaterial(
    const TMap<FString, UTexture2D*>& TextureAssetsByKey,
    FString& OutSummary)
{
    static const TCHAR* MaterialPackagePath = TEXT("/Game/RaftSim/Materials/M_RaftSim_AtlasSampleReview");
    static const TCHAR* MaterialObjectPath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_AtlasSampleReview.M_RaftSim_AtlasSampleReview");

    UMaterial* Material = Cast<UMaterial>(StaticLoadObject(UMaterial::StaticClass(), nullptr, MaterialObjectPath));
    UPackage* Package = Material ? Material->GetOutermost() : CreatePackage(MaterialPackagePath);
    if (!Package)
    {
        OutSummary += FString::Printf(TEXT("Failed to create atlas sample review material package %s\n"), MaterialPackagePath);
        return nullptr;
    }

    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package,
            TEXT("M_RaftSim_AtlasSampleReview"),
            RF_Public | RF_Standalone | RF_Transactional);
        if (!Material)
        {
            OutSummary += FString::Printf(TEXT("Failed to create atlas sample review material %s\n"), MaterialObjectPath);
            return nullptr;
        }
        FAssetRegistryModule::AssetCreated(Material);
    }

    UTexture2D* DefaultAlbedo =
        TextureAssetsByKey.FindRef(GetFirstPartyMaterialTextureAssetBindingKey(TEXT("american_south_fork"), TEXT("AlbedoAtlas")));
    UTexture2D* DefaultNormal =
        TextureAssetsByKey.FindRef(GetFirstPartyMaterialTextureAssetBindingKey(TEXT("american_south_fork"), TEXT("NormalAtlas")));
    UTexture2D* DefaultPacked = TextureAssetsByKey.FindRef(
        GetFirstPartyMaterialTextureAssetBindingKey(TEXT("american_south_fork"), TEXT("AORoughnessHeightAtlas")));
    UTexture2D* DefaultSourceMacroAlbedo = TextureAssetsByKey.FindRef(
        GetFirstPartyMaterialTextureAssetBindingKey(TEXT("american_south_fork"), TEXT("SourceConditionedMacroAlbedo")));
    UTexture2D* DefaultSourceMaterialZones = TextureAssetsByKey.FindRef(
        GetFirstPartyMaterialTextureAssetBindingKey(TEXT("american_south_fork"), TEXT("SourceConditionedMaterialZones")));
    UTexture2D* DefaultSourcePacked = TextureAssetsByKey.FindRef(
        GetFirstPartyMaterialTextureAssetBindingKey(TEXT("american_south_fork"), TEXT("SourceConditionedAORoughnessHeight")));
    UTexture2D* DefaultSourceNormalDetail = TextureAssetsByKey.FindRef(
        GetFirstPartyMaterialTextureAssetBindingKey(TEXT("american_south_fork"), TEXT("SourceConditionedNormalDetail")));
    UTexture2D* DefaultTerrainDetailAlbedo = TextureAssetsByKey.FindRef(
        GetFirstPartyMaterialTextureAssetBindingKey(TEXT("american_south_fork"), TEXT("TerrainDetailAlbedo")));
    UTexture2D* DefaultTerrainDetailNormal = TextureAssetsByKey.FindRef(
        GetFirstPartyMaterialTextureAssetBindingKey(TEXT("american_south_fork"), TEXT("TerrainDetailNormal")));
    UTexture2D* DefaultTerrainDetailPacked = TextureAssetsByKey.FindRef(
        GetFirstPartyMaterialTextureAssetBindingKey(TEXT("american_south_fork"), TEXT("TerrainDetailAORoughnessHeight")));

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->SetShadingModel(MSM_DefaultLit);
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = true;

    auto AddExpression = [Material](auto* Expression, int32 EditorX, int32 EditorY)
    {
        Expression->MaterialExpressionEditorX = EditorX;
        Expression->MaterialExpressionEditorY = EditorY;
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };

    UMaterialExpressionTextureCoordinate* TexCoord =
        AddExpression(NewObject<UMaterialExpressionTextureCoordinate>(Material), -1120, -120);

    UMaterialExpressionVectorParameter* AtlasTileOriginParameter =
        AddExpression(NewObject<UMaterialExpressionVectorParameter>(Material), -1120, 40);
    AtlasTileOriginParameter->ParameterName = TEXT("AtlasTileOrigin");
    AtlasTileOriginParameter->DefaultValue = FLinearColor(0.0f, 0.0f, 0.0f, 0.0f);

    UMaterialExpressionVectorParameter* AtlasTileScaleParameter =
        AddExpression(NewObject<UMaterialExpressionVectorParameter>(Material), -1120, 180);
    AtlasTileScaleParameter->ParameterName = TEXT("AtlasTileScale");
    AtlasTileScaleParameter->DefaultValue = FLinearColor(1.0f / 3.0f, 1.0f / 2.0f, 0.0f, 0.0f);

    UMaterialExpressionComponentMask* AtlasOrigin =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), -880, 40);
    AtlasOrigin->Input.Expression = AtlasTileOriginParameter;
    AtlasOrigin->R = 1;
    AtlasOrigin->G = 1;

    UMaterialExpressionComponentMask* AtlasScale =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), -880, 180);
    AtlasScale->Input.Expression = AtlasTileScaleParameter;
    AtlasScale->R = 1;
    AtlasScale->G = 1;

    UMaterialExpressionMultiply* ScaledUv = AddExpression(NewObject<UMaterialExpressionMultiply>(Material), -640, -40);
    ScaledUv->A.Expression = TexCoord;
    ScaledUv->B.Expression = AtlasScale;

    UMaterialExpressionAdd* AtlasUv = AddExpression(NewObject<UMaterialExpressionAdd>(Material), -420, -40);
    AtlasUv->A.Expression = ScaledUv;
    AtlasUv->B.Expression = AtlasOrigin;

    UMaterialExpressionTextureSampleParameter2D* AlbedoSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -180, -220);
    AlbedoSample->ParameterName = TEXT("AlbedoAtlas");
    AlbedoSample->Texture = DefaultAlbedo;
    AlbedoSample->SamplerType = SAMPLERTYPE_Color;
    AlbedoSample->Coordinates.Expression = AtlasUv;
    AlbedoSample->Group = TEXT("FirstPartyAtlas");
    AlbedoSample->SortPriority = 10;

    UMaterialExpressionTextureSampleParameter2D* NormalSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -180, 20);
    NormalSample->ParameterName = TEXT("NormalAtlas");
    NormalSample->Texture = DefaultNormal;
    NormalSample->SamplerType = SAMPLERTYPE_Normal;
    NormalSample->Coordinates.Expression = AtlasUv;
    NormalSample->Group = TEXT("FirstPartyAtlas");
    NormalSample->SortPriority = 20;

    UMaterialExpressionConstant3Vector* FlatNormal =
        AddExpression(NewObject<UMaterialExpressionConstant3Vector>(Material), 120, -20);
    FlatNormal->Constant = FLinearColor(0.0f, 0.0f, 1.0f);

    UMaterialExpressionScalarParameter* NormalIntensity =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 120, 100);
    NormalIntensity->ParameterName = TEXT("NormalIntensity");
    NormalIntensity->DefaultValue = 0.30f;
    NormalIntensity->Group = TEXT("FirstPartyAtlas");
    NormalIntensity->SortPriority = 45;

    UMaterialExpressionLinearInterpolate* ReviewNormal =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 360, 40);
    ReviewNormal->A.Expression = FlatNormal;
    ReviewNormal->B.Expression = NormalSample;
    ReviewNormal->Alpha.Expression = NormalIntensity;

    UMaterialExpressionTextureSampleParameter2D* PackedSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -180, 260);
    PackedSample->ParameterName = TEXT("AORoughnessHeightAtlas");
    PackedSample->Texture = DefaultPacked;
    PackedSample->SamplerType = SAMPLERTYPE_Masks;
    PackedSample->Coordinates.Expression = AtlasUv;
    PackedSample->Group = TEXT("FirstPartyAtlas");
    PackedSample->SortPriority = 30;

    UMaterialExpressionTextureSampleParameter2D* SourceMacroAlbedoSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -180, -40);
    SourceMacroAlbedoSample->ParameterName = TEXT("SourceConditionedMacroAlbedo");
    SourceMacroAlbedoSample->Texture = DefaultSourceMacroAlbedo;
    SourceMacroAlbedoSample->SamplerType = SAMPLERTYPE_Color;
    SourceMacroAlbedoSample->Coordinates.Expression = TexCoord;
    SourceMacroAlbedoSample->Group = TEXT("SourceConditionedMaps");
    SourceMacroAlbedoSample->SortPriority = 70;

    UMaterialExpressionTextureSampleParameter2D* SourceMaterialZonesSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -180, 920);
    SourceMaterialZonesSample->ParameterName = TEXT("SourceConditionedMaterialZones");
    SourceMaterialZonesSample->Texture = DefaultSourceMaterialZones;
    SourceMaterialZonesSample->SamplerType = SAMPLERTYPE_Masks;
    SourceMaterialZonesSample->Coordinates.Expression = TexCoord;
    SourceMaterialZonesSample->Group = TEXT("SourceConditionedMaps");
    SourceMaterialZonesSample->SortPriority = 80;

    UMaterialExpressionTextureSampleParameter2D* SourcePackedSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -180, 1160);
    SourcePackedSample->ParameterName = TEXT("SourceConditionedAORoughnessHeight");
    SourcePackedSample->Texture = DefaultSourcePacked;
    SourcePackedSample->SamplerType = SAMPLERTYPE_Masks;
    SourcePackedSample->Coordinates.Expression = TexCoord;
    SourcePackedSample->Group = TEXT("SourceConditionedMaps");
    SourcePackedSample->SortPriority = 90;

    UMaterialExpressionTextureSampleParameter2D* SourceNormalDetailSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -180, 1500);
    SourceNormalDetailSample->ParameterName = TEXT("SourceConditionedNormalDetail");
    SourceNormalDetailSample->Texture = DefaultSourceNormalDetail;
    SourceNormalDetailSample->SamplerType = SAMPLERTYPE_Normal;
    SourceNormalDetailSample->Coordinates.Expression = TexCoord;
    SourceNormalDetailSample->Group = TEXT("SourceConditionedMaps");
    SourceNormalDetailSample->SortPriority = 95;

    UMaterialExpressionVectorParameter* TerrainDetailUvScaleParameter =
        AddExpression(NewObject<UMaterialExpressionVectorParameter>(Material), -1120, 1780);
    TerrainDetailUvScaleParameter->ParameterName = TEXT("TerrainDetailUvScale");
    TerrainDetailUvScaleParameter->DefaultValue = FLinearColor(8.0f, 8.0f, 0.0f, 0.0f);
    TerrainDetailUvScaleParameter->Group = TEXT("FirstPartyProductionDetail");
    TerrainDetailUvScaleParameter->SortPriority = 130;

    UMaterialExpressionVectorParameter* TerrainDetailUvOffsetParameter =
        AddExpression(NewObject<UMaterialExpressionVectorParameter>(Material), -1120, 1920);
    TerrainDetailUvOffsetParameter->ParameterName = TEXT("TerrainDetailUvOffset");
    TerrainDetailUvOffsetParameter->DefaultValue = FLinearColor(0.17f, 0.31f, 0.0f, 0.0f);
    TerrainDetailUvOffsetParameter->Group = TEXT("FirstPartyProductionDetail");
    TerrainDetailUvOffsetParameter->SortPriority = 135;

    UMaterialExpressionComponentMask* TerrainDetailUvScale =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), -880, 1740);
    TerrainDetailUvScale->Input.Expression = TerrainDetailUvScaleParameter;
    TerrainDetailUvScale->R = 1;
    TerrainDetailUvScale->G = 1;

    UMaterialExpressionComponentMask* TerrainDetailUvOffset =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), -880, 1880);
    TerrainDetailUvOffset->Input.Expression = TerrainDetailUvOffsetParameter;
    TerrainDetailUvOffset->R = 1;
    TerrainDetailUvOffset->G = 1;

    UMaterialExpressionMultiply* TerrainDetailScaledUv =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), -640, 1740);
    TerrainDetailScaledUv->A.Expression = TexCoord;
    TerrainDetailScaledUv->B.Expression = TerrainDetailUvScale;

    UMaterialExpressionAdd* TerrainDetailUv =
        AddExpression(NewObject<UMaterialExpressionAdd>(Material), -420, 1780);
    TerrainDetailUv->A.Expression = TerrainDetailScaledUv;
    TerrainDetailUv->B.Expression = TerrainDetailUvOffset;

    UMaterialExpressionTextureSampleParameter2D* TerrainDetailAlbedoSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -180, 1760);
    TerrainDetailAlbedoSample->ParameterName = TEXT("TerrainDetailAlbedo");
    TerrainDetailAlbedoSample->Texture = DefaultTerrainDetailAlbedo;
    TerrainDetailAlbedoSample->SamplerType = SAMPLERTYPE_Color;
    TerrainDetailAlbedoSample->Coordinates.Expression = TerrainDetailUv;
    TerrainDetailAlbedoSample->Group = TEXT("FirstPartyProductionDetail");
    TerrainDetailAlbedoSample->SortPriority = 140;

    UMaterialExpressionTextureSampleParameter2D* TerrainDetailNormalSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -180, 1980);
    TerrainDetailNormalSample->ParameterName = TEXT("TerrainDetailNormal");
    TerrainDetailNormalSample->Texture = DefaultTerrainDetailNormal;
    TerrainDetailNormalSample->SamplerType = SAMPLERTYPE_Normal;
    TerrainDetailNormalSample->Coordinates.Expression = TerrainDetailUv;
    TerrainDetailNormalSample->Group = TEXT("FirstPartyProductionDetail");
    TerrainDetailNormalSample->SortPriority = 150;

    UMaterialExpressionTextureSampleParameter2D* TerrainDetailPackedSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -180, 2200);
    TerrainDetailPackedSample->ParameterName = TEXT("TerrainDetailAORoughnessHeight");
    TerrainDetailPackedSample->Texture = DefaultTerrainDetailPacked;
    TerrainDetailPackedSample->SamplerType = SAMPLERTYPE_Masks;
    TerrainDetailPackedSample->Coordinates.Expression = TerrainDetailUv;
    TerrainDetailPackedSample->Group = TEXT("FirstPartyProductionDetail");
    TerrainDetailPackedSample->SortPriority = 160;

    UMaterialExpressionVectorParameter* SourceZoneWeights =
        AddExpression(NewObject<UMaterialExpressionVectorParameter>(Material), -180, 700);
    SourceZoneWeights->ParameterName = TEXT("SourceConditionedZoneWeights");
    SourceZoneWeights->DefaultValue = FLinearColor(1.0f, 0.0f, 0.0f, 0.0f);
    SourceZoneWeights->Group = TEXT("SourceConditionedMaps");
    SourceZoneWeights->SortPriority = 100;

    UMaterialExpressionComponentMask* SourceZoneTerrain =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 840);
    SourceZoneTerrain->Input.Expression = SourceMaterialZonesSample;
    SourceZoneTerrain->R = 1;

    UMaterialExpressionComponentMask* SourceZoneVegetation =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 940);
    SourceZoneVegetation->Input.Expression = SourceMaterialZonesSample;
    SourceZoneVegetation->G = 1;

    UMaterialExpressionComponentMask* SourceZoneWater =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 1040);
    SourceZoneWater->Input.Expression = SourceMaterialZonesSample;
    SourceZoneWater->B = 1;

    UMaterialExpressionComponentMask* SourceZoneWeightTerrain =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 680);
    SourceZoneWeightTerrain->Input.Expression = SourceZoneWeights;
    SourceZoneWeightTerrain->R = 1;

    UMaterialExpressionComponentMask* SourceZoneWeightVegetation =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 760);
    SourceZoneWeightVegetation->Input.Expression = SourceZoneWeights;
    SourceZoneWeightVegetation->G = 1;

    UMaterialExpressionComponentMask* SourceZoneWeightWater =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 1120);
    SourceZoneWeightWater->Input.Expression = SourceZoneWeights;
    SourceZoneWeightWater->B = 1;

    UMaterialExpressionMultiply* SourceTerrainZoneWeighted =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 360, 820);
    SourceTerrainZoneWeighted->A.Expression = SourceZoneTerrain;
    SourceTerrainZoneWeighted->B.Expression = SourceZoneWeightTerrain;

    UMaterialExpressionMultiply* SourceVegetationZoneWeighted =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 360, 940);
    SourceVegetationZoneWeighted->A.Expression = SourceZoneVegetation;
    SourceVegetationZoneWeighted->B.Expression = SourceZoneWeightVegetation;

    UMaterialExpressionMultiply* SourceWaterZoneWeighted =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 360, 1060);
    SourceWaterZoneWeighted->A.Expression = SourceZoneWater;
    SourceWaterZoneWeighted->B.Expression = SourceZoneWeightWater;

    UMaterialExpressionAdd* SourceTerrainVegetationZones =
        AddExpression(NewObject<UMaterialExpressionAdd>(Material), 560, 900);
    SourceTerrainVegetationZones->A.Expression = SourceTerrainZoneWeighted;
    SourceTerrainVegetationZones->B.Expression = SourceVegetationZoneWeighted;

    UMaterialExpressionAdd* SourceWeightedZones =
        AddExpression(NewObject<UMaterialExpressionAdd>(Material), 760, 980);
    SourceWeightedZones->A.Expression = SourceTerrainVegetationZones;
    SourceWeightedZones->B.Expression = SourceWaterZoneWeighted;

    UMaterialExpressionSaturate* SourceZoneMask =
        AddExpression(NewObject<UMaterialExpressionSaturate>(Material), 960, 980);
    SourceZoneMask->Input.Expression = SourceWeightedZones;

    UMaterialExpressionScalarParameter* SourceConditionedMacroAlbedoWeight =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 120, -220);
    SourceConditionedMacroAlbedoWeight->ParameterName = TEXT("SourceConditionedMacroAlbedoWeight");
    SourceConditionedMacroAlbedoWeight->DefaultValue = 0.12f;
    SourceConditionedMacroAlbedoWeight->Group = TEXT("SourceConditionedMaps");
    SourceConditionedMacroAlbedoWeight->SortPriority = 110;

    UMaterialExpressionMultiply* SourceConditionedMacroAlbedoAlpha =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 360, -220);
    SourceConditionedMacroAlbedoAlpha->A.Expression = SourceConditionedMacroAlbedoWeight;
    SourceConditionedMacroAlbedoAlpha->B.Expression = SourceZoneMask;

    UMaterialExpressionScalarParameter* SourceConditionedSurfaceResponseWeight =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 960, 760);
    SourceConditionedSurfaceResponseWeight->ParameterName = TEXT("SourceConditionedSurfaceResponseWeight");
    SourceConditionedSurfaceResponseWeight->DefaultValue = 0.10f;
    SourceConditionedSurfaceResponseWeight->Group = TEXT("SourceConditionedMaps");
    SourceConditionedSurfaceResponseWeight->SortPriority = 120;

    UMaterialExpressionMultiply* SourceConditionedSurfaceResponseAlpha =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 1160, 900);
    SourceConditionedSurfaceResponseAlpha->A.Expression = SourceConditionedSurfaceResponseWeight;
    SourceConditionedSurfaceResponseAlpha->B.Expression = SourceZoneMask;

    UMaterialExpressionScalarParameter* SourceConditionedNormalDetailWeight =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 960, 620);
    SourceConditionedNormalDetailWeight->ParameterName = TEXT("SourceConditionedNormalDetailWeight");
    SourceConditionedNormalDetailWeight->DefaultValue = 0.08f;
    SourceConditionedNormalDetailWeight->Group = TEXT("SourceConditionedMaps");
    SourceConditionedNormalDetailWeight->SortPriority = 125;

    UMaterialExpressionMultiply* SourceConditionedNormalDetailAlpha =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 1160, 660);
    SourceConditionedNormalDetailAlpha->A.Expression = SourceConditionedNormalDetailWeight;
    SourceConditionedNormalDetailAlpha->B.Expression = SourceZoneMask;

    UMaterialExpressionVertexColor* VertexColor =
        AddExpression(NewObject<UMaterialExpressionVertexColor>(Material), -180, -560);

    UMaterialExpressionVectorParameter* PreviewColor =
        AddExpression(NewObject<UMaterialExpressionVectorParameter>(Material), -180, -420);
    PreviewColor->ParameterName = TEXT("PreviewColor");
    PreviewColor->DefaultValue = FLinearColor(0.30f, 0.31f, 0.27f);
    PreviewColor->Group = TEXT("FirstPartyAtlas");
    PreviewColor->SortPriority = 35;

    UMaterialExpressionScalarParameter* VertexColorWeight =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -180, -300);
    VertexColorWeight->ParameterName = TEXT("VertexColorWeight");
    VertexColorWeight->DefaultValue = 1.0f;
    VertexColorWeight->Group = TEXT("FirstPartyAtlas");
    VertexColorWeight->SortPriority = 38;

    UMaterialExpressionLinearInterpolate* ReviewSurfaceBaseColor =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 120, -500);
    ReviewSurfaceBaseColor->A.Expression = PreviewColor;
    ReviewSurfaceBaseColor->B.Expression = VertexColor;
    ReviewSurfaceBaseColor->Alpha.Expression = VertexColorWeight;

    UMaterialExpressionScalarParameter* AtlasBlendWeight =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -180, -360);
    AtlasBlendWeight->ParameterName = TEXT("AtlasBlendWeight");
    AtlasBlendWeight->DefaultValue = 0.16f;
    AtlasBlendWeight->Group = TEXT("FirstPartyAtlas");
    AtlasBlendWeight->SortPriority = 40;

    UMaterialExpressionLinearInterpolate* ReviewBaseColor =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 120, -320);
    ReviewBaseColor->A.Expression = ReviewSurfaceBaseColor;
    ReviewBaseColor->B.Expression = AlbedoSample;
    ReviewBaseColor->Alpha.Expression = AtlasBlendWeight;

    UMaterialExpressionLinearInterpolate* SourceConditionedBaseColor =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 560, -260);
    SourceConditionedBaseColor->A.Expression = ReviewBaseColor;
    SourceConditionedBaseColor->B.Expression = SourceMacroAlbedoSample;
    SourceConditionedBaseColor->Alpha.Expression = SourceConditionedMacroAlbedoAlpha;

    UMaterialExpressionScalarParameter* TerrainDetailAlbedoWeight =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 120, 1760);
    TerrainDetailAlbedoWeight->ParameterName = TEXT("TerrainDetailAlbedoWeight");
    TerrainDetailAlbedoWeight->DefaultValue = 0.0f;
    TerrainDetailAlbedoWeight->Group = TEXT("FirstPartyProductionDetail");
    TerrainDetailAlbedoWeight->SortPriority = 170;

    UMaterialExpressionLinearInterpolate* ProductionDetailBaseColor =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 560, -120);
    ProductionDetailBaseColor->A.Expression = SourceConditionedBaseColor;
    ProductionDetailBaseColor->B.Expression = TerrainDetailAlbedoSample;
    ProductionDetailBaseColor->Alpha.Expression = TerrainDetailAlbedoWeight;

    UMaterialExpressionConstant* FirstPartyAtlasReviewEmissiveFillScale =
        AddExpression(NewObject<UMaterialExpressionConstant>(Material), 120, -80);
    FirstPartyAtlasReviewEmissiveFillScale->R = 0.42f;

    UMaterialExpressionMultiply* EmissiveColor =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 360, -160);
    EmissiveColor->A.Expression = ProductionDetailBaseColor;
    EmissiveColor->B.Expression = FirstPartyAtlasReviewEmissiveFillScale;

    UMaterialExpressionComponentMask* AmbientOcclusionMask =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 180);
    AmbientOcclusionMask->Input.Expression = PackedSample;
    AmbientOcclusionMask->R = 1;

    UMaterialExpressionComponentMask* RoughnessMask =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 320);
    RoughnessMask->Input.Expression = PackedSample;
    RoughnessMask->G = 1;

    UMaterialExpressionScalarParameter* RoughnessScale =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 120, 460);
    RoughnessScale->ParameterName = TEXT("RoughnessScale");
    RoughnessScale->DefaultValue = 0.75f;
    RoughnessScale->Group = TEXT("FirstPartyAtlas");
    RoughnessScale->SortPriority = 50;

    UMaterialExpressionMultiply* RoughnessScaled =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 360, 360);
    RoughnessScaled->A.Expression = RoughnessMask;
    RoughnessScaled->B.Expression = RoughnessScale;

    UMaterialExpressionScalarParameter* RoughnessFloor =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 360, 500);
    RoughnessFloor->ParameterName = TEXT("RoughnessFloor");
    RoughnessFloor->DefaultValue = 0.62f;
    RoughnessFloor->Group = TEXT("FirstPartyAtlas");
    RoughnessFloor->SortPriority = 55;

    UMaterialExpressionAdd* RoughnessWithFloor =
        AddExpression(NewObject<UMaterialExpressionAdd>(Material), 560, 420);
    RoughnessWithFloor->A.Expression = RoughnessScaled;
    RoughnessWithFloor->B.Expression = RoughnessFloor;

    UMaterialExpressionSaturate* RoughnessSaturated =
        AddExpression(NewObject<UMaterialExpressionSaturate>(Material), 760, 420);
    RoughnessSaturated->Input.Expression = RoughnessWithFloor;

    UMaterialExpressionComponentMask* SourceAmbientOcclusionMask =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 1220);
    SourceAmbientOcclusionMask->Input.Expression = SourcePackedSample;
    SourceAmbientOcclusionMask->R = 1;

    UMaterialExpressionComponentMask* SourceRoughnessMask =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 1320);
    SourceRoughnessMask->Input.Expression = SourcePackedSample;
    SourceRoughnessMask->G = 1;

    UMaterialExpressionLinearInterpolate* SourceConditionedAmbientOcclusion =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 1160, 1180);
    SourceConditionedAmbientOcclusion->A.Expression = AmbientOcclusionMask;
    SourceConditionedAmbientOcclusion->B.Expression = SourceAmbientOcclusionMask;
    SourceConditionedAmbientOcclusion->Alpha.Expression = SourceConditionedSurfaceResponseAlpha;

    UMaterialExpressionLinearInterpolate* SourceConditionedRoughness =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 1160, 1320);
    SourceConditionedRoughness->A.Expression = RoughnessSaturated;
    SourceConditionedRoughness->B.Expression = SourceRoughnessMask;
    SourceConditionedRoughness->Alpha.Expression = SourceConditionedSurfaceResponseAlpha;

    UMaterialExpressionComponentMask* HeightMask =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 620);
    HeightMask->Input.Expression = PackedSample;
    HeightMask->B = 1;

    UMaterialExpressionScalarParameter* HeightScale =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 120, 760);
    HeightScale->ParameterName = TEXT("HeightScale");
    HeightScale->DefaultValue = 0.08f;
    HeightScale->Group = TEXT("FirstPartyAtlas");
    HeightScale->SortPriority = 60;

    UMaterialExpressionMultiply* HeightOffset =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 360, 680);
    HeightOffset->A.Expression = HeightMask;
    HeightOffset->B.Expression = HeightScale;

    UMaterialExpressionComponentMask* SourceHeightMask =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 1420);
    SourceHeightMask->Input.Expression = SourcePackedSample;
    SourceHeightMask->B = 1;

    UMaterialExpressionMultiply* SourceHeightOffset =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 360, 1420);
    SourceHeightOffset->A.Expression = SourceHeightMask;
    SourceHeightOffset->B.Expression = HeightScale;

    UMaterialExpressionLinearInterpolate* SourceConditionedHeightOffset =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 1160, 1440);
    SourceConditionedHeightOffset->A.Expression = HeightOffset;
    SourceConditionedHeightOffset->B.Expression = SourceHeightOffset;
    SourceConditionedHeightOffset->Alpha.Expression = SourceConditionedSurfaceResponseAlpha;

    UMaterialExpressionLinearInterpolate* SourceConditionedNormal =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 760, 80);
    SourceConditionedNormal->A.Expression = ReviewNormal;
    SourceConditionedNormal->B.Expression = SourceNormalDetailSample;
    SourceConditionedNormal->Alpha.Expression = SourceConditionedNormalDetailAlpha;

    UMaterialExpressionScalarParameter* TerrainDetailNormalWeight =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 120, 1980);
    TerrainDetailNormalWeight->ParameterName = TEXT("TerrainDetailNormalWeight");
    TerrainDetailNormalWeight->DefaultValue = 0.0f;
    TerrainDetailNormalWeight->Group = TEXT("FirstPartyProductionDetail");
    TerrainDetailNormalWeight->SortPriority = 180;

    UMaterialExpressionScalarParameter* TerrainDetailSurfaceResponseWeight =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 120, 2440);
    TerrainDetailSurfaceResponseWeight->ParameterName = TEXT("TerrainDetailSurfaceResponseWeight");
    TerrainDetailSurfaceResponseWeight->DefaultValue = 0.0f;
    TerrainDetailSurfaceResponseWeight->Group = TEXT("FirstPartyProductionDetail");
    TerrainDetailSurfaceResponseWeight->SortPriority = 190;

    UMaterialExpressionComponentMask* TerrainDetailAmbientOcclusion =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 2180);
    TerrainDetailAmbientOcclusion->Input.Expression = TerrainDetailPackedSample;
    TerrainDetailAmbientOcclusion->R = 1;

    UMaterialExpressionComponentMask* TerrainDetailRoughness =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 2280);
    TerrainDetailRoughness->Input.Expression = TerrainDetailPackedSample;
    TerrainDetailRoughness->G = 1;

    UMaterialExpressionComponentMask* TerrainDetailHeight =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 2380);
    TerrainDetailHeight->Input.Expression = TerrainDetailPackedSample;
    TerrainDetailHeight->B = 1;

    UMaterialExpressionMultiply* TerrainDetailHeightOffset =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 360, 2380);
    TerrainDetailHeightOffset->A.Expression = TerrainDetailHeight;
    TerrainDetailHeightOffset->B.Expression = HeightScale;

    UMaterialExpressionLinearInterpolate* ProductionDetailNormal =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 1460, 80);
    ProductionDetailNormal->A.Expression = SourceConditionedNormal;
    ProductionDetailNormal->B.Expression = TerrainDetailNormalSample;
    ProductionDetailNormal->Alpha.Expression = TerrainDetailNormalWeight;

    UMaterialExpressionLinearInterpolate* ProductionDetailAmbientOcclusion =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 1460, 1180);
    ProductionDetailAmbientOcclusion->A.Expression = SourceConditionedAmbientOcclusion;
    ProductionDetailAmbientOcclusion->B.Expression = TerrainDetailAmbientOcclusion;
    ProductionDetailAmbientOcclusion->Alpha.Expression = TerrainDetailSurfaceResponseWeight;

    UMaterialExpressionLinearInterpolate* ProductionDetailRoughness =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 1460, 1320);
    ProductionDetailRoughness->A.Expression = SourceConditionedRoughness;
    ProductionDetailRoughness->B.Expression = TerrainDetailRoughness;
    ProductionDetailRoughness->Alpha.Expression = TerrainDetailSurfaceResponseWeight;

    UMaterialExpressionLinearInterpolate* ProductionDetailHeightOffset =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 1460, 1440);
    ProductionDetailHeightOffset->A.Expression = SourceConditionedHeightOffset;
    ProductionDetailHeightOffset->B.Expression = TerrainDetailHeightOffset;
    ProductionDetailHeightOffset->Alpha.Expression = TerrainDetailSurfaceResponseWeight;

    UMaterialExpressionConstant* Specular = AddExpression(NewObject<UMaterialExpressionConstant>(Material), 560, 520);
    Specular->R = 0.0f;

    if (UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData())
    {
        ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, ProductionDetailBaseColor);
        ConnectPreviewMaterialColorInput(EditorOnlyData->EmissiveColor, EmissiveColor);
        ConnectPreviewMaterialVectorInput(EditorOnlyData->Normal, ProductionDetailNormal);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->AmbientOcclusion, ProductionDetailAmbientOcclusion);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, ProductionDetailRoughness);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->PixelDepthOffset, ProductionDetailHeightOffset);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);
    }

    Material->PostEditChange();
    Package->MarkPackageDirty();

    const FString Filename =
        FPackageName::LongPackageNameToFilename(MaterialPackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);

    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    const bool bSaved = UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
    OutSummary += FString::Printf(
        TEXT("%s first-party atlas sampler review material %s -> %s\n"),
        bSaved ? TEXT("Saved") : TEXT("Failed"),
        MaterialObjectPath,
        *Filename);
    return bSaved ? Material : nullptr;
}
} // namespace RaftSimEditorEnvironment
