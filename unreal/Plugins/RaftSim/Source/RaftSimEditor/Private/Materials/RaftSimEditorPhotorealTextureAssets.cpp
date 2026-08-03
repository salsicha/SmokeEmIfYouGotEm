#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Engine/Texture2D.h"

namespace RaftSimPhotorealMaterials
{

bool BuildSouthForkWaterTextureAssets()
{
    using namespace RaftSimEditorEnvironment;
    FString Summary;
    FRaftSimFirstPartyMaterialTextureAssetSpec FlowNormalSpec;
    FlowNormalSpec.RiverId = TEXT("american_south_fork");
    FlowNormalSpec.RiverAssetName = TEXT("SouthForkWater");
    FlowNormalSpec.MapKey = TEXT("FlowNormal");
    FlowNormalSpec.MapKind = TEXT("project_owned_multiscale_river_flow_normal");
    FlowNormalSpec.SourceRelativePath =
        TEXT("unreal/SourceArt/RaftSim/Water/"
             "T_RaftSim_SouthForkWater_FlowNormal.png");
    FlowNormalSpec.TextureAssetRootPackagePath =
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/Textures");
    FlowNormalSpec.CompressionSettings = TC_Normalmap;
    FlowNormalSpec.bSRGB = false;
    FlowNormalSpec.LODGroup = TEXTUREGROUP_WorldNormalMap;
    // The generated source is visually periodic but not pixel-identical at
    // the boundary. Mirrored addressing guarantees continuous sampling at
    // every repeat without destructively filtering the authored field.
    FlowNormalSpec.AddressX = TA_Mirror;
    FlowNormalSpec.AddressY = TA_Mirror;
    FlowNormalSpec.bCompressionNoAlpha = true;
    bool bFlowNormalSaved = false;
    UTexture2D* FlowNormalTexture = CreateOrUpdateFirstPartyMaterialTextureAsset(
        FlowNormalSpec, Summary, bFlowNormalSaved);

    // A first-party flow-aligned lace texture replaces the prior world-space
    // cellular noise. It is only breakup detail: the material still multiplies
    // it by the solver-authored foam mask, so it cannot invent whitewater.
    FRaftSimFirstPartyMaterialTextureAssetSpec FoamLaceSpec;
    FoamLaceSpec.RiverId = TEXT("american_south_fork");
    FoamLaceSpec.RiverAssetName = TEXT("SouthForkWater");
    FoamLaceSpec.MapKey = TEXT("FoamLace");
    FoamLaceSpec.MapKind = TEXT("project_owned_flow_aligned_whitewater_foam_breakup");
    FoamLaceSpec.SourceRelativePath =
        TEXT("unreal/SourceArt/RaftSim/Water/"
             "T_RaftSim_SouthForkWater_FoamLace.png");
    FoamLaceSpec.TextureAssetRootPackagePath =
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/Textures");
    FoamLaceSpec.CompressionSettings = TC_Masks;
    FoamLaceSpec.bSRGB = false;
    FoamLaceSpec.LODGroup = TEXTUREGROUP_World;
    FoamLaceSpec.AddressX = TA_Mirror;
    FoamLaceSpec.AddressY = TA_Mirror;
    FoamLaceSpec.bCompressionNoAlpha = true;
    bool bFoamLaceSaved = false;
    UTexture2D* FoamLaceTexture = CreateOrUpdateFirstPartyMaterialTextureAsset(
        FoamLaceSpec, Summary, bFoamLaceSaved);

    UE_LOG(LogTemp, Display, TEXT("RaftSim South Fork water textures:\n%s"), *Summary);
    return FlowNormalTexture != nullptr && bFlowNormalSaved &&
        FoamLaceTexture != nullptr && bFoamLaceSaved;
}

bool BuildPacuareUpperHuacasWaterTextureAssets()
{
    using namespace RaftSimEditorEnvironment;
    FString Summary;

    FRaftSimFirstPartyMaterialTextureAssetSpec FlowNormalSpec;
    FlowNormalSpec.RiverId = TEXT("pacuare");
    FlowNormalSpec.RiverAssetName = TEXT("PacuareUpperHuacasWaterV1");
    FlowNormalSpec.MapKey = TEXT("FlowNormal");
    FlowNormalSpec.MapKind =
        TEXT("project_owned_pacuare_multiscale_river_flow_normal");
    FlowNormalSpec.SourceRelativePath =
        TEXT("unreal/SourceArt/RaftSim/Water/PacuareUpperHuacas/"
             "T_RaftSim_PacuareUpperHuacas_FlowNormalV1.png");
    FlowNormalSpec.TextureAssetRootPackagePath =
        TEXT("/Game/RaftSim/Environment/PacuareRun/Water/Textures");
    FlowNormalSpec.CompressionSettings = TC_Normalmap;
    FlowNormalSpec.bSRGB = false;
    FlowNormalSpec.LODGroup = TEXTUREGROUP_WorldNormalMap;
    FlowNormalSpec.AddressX = TA_Mirror;
    FlowNormalSpec.AddressY = TA_Mirror;
    FlowNormalSpec.bCompressionNoAlpha = true;
    bool bFlowNormalSaved = false;
    UTexture2D* FlowNormalTexture = CreateOrUpdateFirstPartyMaterialTextureAsset(
        FlowNormalSpec, Summary, bFlowNormalSaved);

    FRaftSimFirstPartyMaterialTextureAssetSpec FoamLaceSpec;
    FoamLaceSpec.RiverId = TEXT("pacuare");
    FoamLaceSpec.RiverAssetName = TEXT("PacuareUpperHuacasWaterV1");
    FoamLaceSpec.MapKey = TEXT("FoamLace");
    FoamLaceSpec.MapKind =
        TEXT("project_owned_pacuare_solver_masked_whitewater_lace");
    FoamLaceSpec.SourceRelativePath =
        TEXT("unreal/SourceArt/RaftSim/Water/PacuareUpperHuacas/"
             "T_RaftSim_PacuareUpperHuacas_FoamLaceV1.png");
    FoamLaceSpec.TextureAssetRootPackagePath =
        TEXT("/Game/RaftSim/Environment/PacuareRun/Water/Textures");
    FoamLaceSpec.CompressionSettings = TC_Masks;
    FoamLaceSpec.bSRGB = false;
    FoamLaceSpec.LODGroup = TEXTUREGROUP_World;
    FoamLaceSpec.AddressX = TA_Mirror;
    FoamLaceSpec.AddressY = TA_Mirror;
    FoamLaceSpec.bCompressionNoAlpha = true;
    bool bFoamLaceSaved = false;
    UTexture2D* FoamLaceTexture = CreateOrUpdateFirstPartyMaterialTextureAsset(
        FoamLaceSpec, Summary, bFoamLaceSaved);

    UE_LOG(
        LogTemp,
        Display,
        TEXT("RaftSim Pacuare Upper Huacas water textures:\n%s"),
        *Summary);
    return FlowNormalTexture != nullptr && bFlowNormalSaved &&
        FoamLaceTexture != nullptr && bFoamLaceSaved;
}

bool BuildColoradoHanceWaterTextureAssets()
{
    using namespace RaftSimEditorEnvironment;
    FString Summary;

    FRaftSimFirstPartyMaterialTextureAssetSpec FlowNormalSpec;
    FlowNormalSpec.RiverId = TEXT("colorado_river");
    FlowNormalSpec.RiverAssetName = TEXT("ColoradoHanceWaterV1");
    FlowNormalSpec.MapKey = TEXT("FlowNormal");
    FlowNormalSpec.MapKind =
        TEXT("project_owned_colorado_multiscale_river_flow_normal");
    FlowNormalSpec.SourceRelativePath =
        TEXT("unreal/SourceArt/RaftSim/Water/ColoradoHance/"
             "T_RaftSim_ColoradoHance_FlowNormalV1.png");
    FlowNormalSpec.TextureAssetRootPackagePath =
        TEXT("/Game/RaftSim/Environment/ColoradoRun/Water/Textures");
    FlowNormalSpec.CompressionSettings = TC_Normalmap;
    FlowNormalSpec.bSRGB = false;
    FlowNormalSpec.LODGroup = TEXTUREGROUP_WorldNormalMap;
    FlowNormalSpec.AddressX = TA_Mirror;
    FlowNormalSpec.AddressY = TA_Mirror;
    FlowNormalSpec.bCompressionNoAlpha = true;
    bool bFlowNormalSaved = false;
    UTexture2D* FlowNormalTexture = CreateOrUpdateFirstPartyMaterialTextureAsset(
        FlowNormalSpec, Summary, bFlowNormalSaved);

    FRaftSimFirstPartyMaterialTextureAssetSpec FoamLaceSpec;
    FoamLaceSpec.RiverId = TEXT("colorado_river");
    FoamLaceSpec.RiverAssetName = TEXT("ColoradoHanceWaterV1");
    FoamLaceSpec.MapKey = TEXT("FoamLace");
    FoamLaceSpec.MapKind =
        TEXT("project_owned_colorado_solver_masked_whitewater_lace");
    FoamLaceSpec.SourceRelativePath =
        TEXT("unreal/SourceArt/RaftSim/Water/ColoradoHance/"
             "T_RaftSim_ColoradoHance_FoamLaceV1.png");
    FoamLaceSpec.TextureAssetRootPackagePath =
        TEXT("/Game/RaftSim/Environment/ColoradoRun/Water/Textures");
    FoamLaceSpec.CompressionSettings = TC_Masks;
    FoamLaceSpec.bSRGB = false;
    FoamLaceSpec.LODGroup = TEXTUREGROUP_World;
    FoamLaceSpec.AddressX = TA_Mirror;
    FoamLaceSpec.AddressY = TA_Mirror;
    FoamLaceSpec.bCompressionNoAlpha = true;
    bool bFoamLaceSaved = false;
    UTexture2D* FoamLaceTexture = CreateOrUpdateFirstPartyMaterialTextureAsset(
        FoamLaceSpec, Summary, bFoamLaceSaved);

    UE_LOG(LogTemp, Display, TEXT("RaftSim Colorado Hance water textures:\n%s"), *Summary);
    return FlowNormalTexture != nullptr && bFlowNormalSaved &&
        FoamLaceTexture != nullptr && bFoamLaceSaved;
}

bool BuildFutaleufuTerminatorWaterTextureAssets()
{
    using namespace RaftSimEditorEnvironment;
    FString Summary;

    FRaftSimFirstPartyMaterialTextureAssetSpec FlowNormalSpec;
    FlowNormalSpec.RiverId = TEXT("futaleufu_terminator");
    FlowNormalSpec.RiverAssetName = TEXT("FutaleufuTerminatorWaterV1");
    FlowNormalSpec.MapKey = TEXT("FlowNormal");
    FlowNormalSpec.MapKind =
        TEXT("project_owned_patagonian_multiscale_river_flow_normal");
    FlowNormalSpec.SourceRelativePath =
        TEXT("unreal/SourceArt/RaftSim/Water/FutaleufuTerminator/"
             "T_RaftSim_FutaleufuTerminator_FlowNormalV1.png");
    FlowNormalSpec.TextureAssetRootPackagePath =
        TEXT("/Game/RaftSim/Environment/FutaleufuRun/Water/Textures");
    FlowNormalSpec.CompressionSettings = TC_Normalmap;
    FlowNormalSpec.bSRGB = false;
    FlowNormalSpec.LODGroup = TEXTUREGROUP_WorldNormalMap;
    // The generated project asset is visually continuous but not guaranteed
    // byte-identical at opposite borders. Mirrored addressing guarantees a
    // continuous derivative without blurring its irregular current ridges.
    FlowNormalSpec.AddressX = TA_Mirror;
    FlowNormalSpec.AddressY = TA_Mirror;
    FlowNormalSpec.bCompressionNoAlpha = true;
    bool bFlowNormalSaved = false;
    UTexture2D* FlowNormalTexture = CreateOrUpdateFirstPartyMaterialTextureAsset(
        FlowNormalSpec, Summary, bFlowNormalSaved);

    FRaftSimFirstPartyMaterialTextureAssetSpec FoamLaceSpec;
    FoamLaceSpec.RiverId = TEXT("futaleufu_terminator");
    FoamLaceSpec.RiverAssetName = TEXT("FutaleufuTerminatorWaterV1");
    FoamLaceSpec.MapKey = TEXT("FoamLace");
    FoamLaceSpec.MapKind =
        TEXT("project_owned_patagonian_solver_masked_whitewater_lace");
    FoamLaceSpec.SourceRelativePath =
        TEXT("unreal/SourceArt/RaftSim/Water/FutaleufuTerminator/"
             "T_RaftSim_FutaleufuTerminator_FoamLaceV1.png");
    FoamLaceSpec.TextureAssetRootPackagePath =
        TEXT("/Game/RaftSim/Environment/FutaleufuRun/Water/Textures");
    FoamLaceSpec.CompressionSettings = TC_Masks;
    FoamLaceSpec.bSRGB = false;
    FoamLaceSpec.LODGroup = TEXTUREGROUP_World;
    FoamLaceSpec.AddressX = TA_Mirror;
    FoamLaceSpec.AddressY = TA_Mirror;
    FoamLaceSpec.bCompressionNoAlpha = true;
    bool bFoamLaceSaved = false;
    UTexture2D* FoamLaceTexture = CreateOrUpdateFirstPartyMaterialTextureAsset(
        FoamLaceSpec, Summary, bFoamLaceSaved);

    UE_LOG(
        LogTemp,
        Display,
        TEXT("RaftSim Futaleufu water textures:\n%s"),
        *Summary);
    return FlowNormalTexture != nullptr && bFlowNormalSaved &&
        FoamLaceTexture != nullptr && bFoamLaceSaved;
}

bool BuildChilkoLavaCanyonWaterTextureAssets()
{
    using namespace RaftSimEditorEnvironment;
    FString Summary;

    FRaftSimFirstPartyMaterialTextureAssetSpec FlowNormalSpec;
    FlowNormalSpec.RiverId = TEXT("chilko_river_lava_canyon");
    FlowNormalSpec.RiverAssetName = TEXT("ChilkoLavaCanyonWaterV1");
    FlowNormalSpec.MapKey = TEXT("FlowNormal");
    FlowNormalSpec.MapKind =
        TEXT("project_owned_chilko_multiscale_river_flow_normal");
    FlowNormalSpec.SourceRelativePath =
        TEXT("unreal/SourceArt/RaftSim/Water/ChilkoLavaCanyon/"
             "T_RaftSim_ChilkoLavaCanyon_FlowNormalV1.png");
    FlowNormalSpec.TextureAssetRootPackagePath =
        TEXT("/Game/RaftSim/Environment/ChilkoRun/Water/Textures");
    FlowNormalSpec.CompressionSettings = TC_Normalmap;
    FlowNormalSpec.bSRGB = false;
    FlowNormalSpec.LODGroup = TEXTUREGROUP_WorldNormalMap;
    FlowNormalSpec.AddressX = TA_Mirror;
    FlowNormalSpec.AddressY = TA_Mirror;
    FlowNormalSpec.bCompressionNoAlpha = true;
    bool bFlowNormalSaved = false;
    UTexture2D* FlowNormalTexture = CreateOrUpdateFirstPartyMaterialTextureAsset(
        FlowNormalSpec, Summary, bFlowNormalSaved);

    FRaftSimFirstPartyMaterialTextureAssetSpec FoamLaceSpec;
    FoamLaceSpec.RiverId = TEXT("chilko_river_lava_canyon");
    FoamLaceSpec.RiverAssetName = TEXT("ChilkoLavaCanyonWaterV1");
    FoamLaceSpec.MapKey = TEXT("FoamLace");
    FoamLaceSpec.MapKind =
        TEXT("project_owned_chilko_solver_masked_whitewater_lace");
    FoamLaceSpec.SourceRelativePath =
        TEXT("unreal/SourceArt/RaftSim/Water/ChilkoLavaCanyon/"
             "T_RaftSim_ChilkoLavaCanyon_FoamLaceV1.png");
    FoamLaceSpec.TextureAssetRootPackagePath =
        TEXT("/Game/RaftSim/Environment/ChilkoRun/Water/Textures");
    FoamLaceSpec.CompressionSettings = TC_Masks;
    FoamLaceSpec.bSRGB = false;
    FoamLaceSpec.LODGroup = TEXTUREGROUP_World;
    FoamLaceSpec.AddressX = TA_Mirror;
    FoamLaceSpec.AddressY = TA_Mirror;
    FoamLaceSpec.bCompressionNoAlpha = true;
    bool bFoamLaceSaved = false;
    UTexture2D* FoamLaceTexture = CreateOrUpdateFirstPartyMaterialTextureAsset(
        FoamLaceSpec, Summary, bFoamLaceSaved);

    UE_LOG(
        LogTemp,
        Display,
        TEXT("RaftSim Chilko Lava Canyon water textures:\n%s"),
        *Summary);
    return FlowNormalTexture != nullptr && bFlowNormalSaved &&
        FoamLaceTexture != nullptr && bFoamLaceSaved;
}

bool BuildZambeziBatokaWaterTextureAssets()
{
    using namespace RaftSimEditorEnvironment;
    FString Summary;

    FRaftSimFirstPartyMaterialTextureAssetSpec FlowNormalSpec;
    FlowNormalSpec.RiverId = TEXT("zambezi_batoka_gorge");
    FlowNormalSpec.RiverAssetName = TEXT("ZambeziBatokaWaterV1");
    FlowNormalSpec.MapKey = TEXT("FlowNormal");
    FlowNormalSpec.MapKind =
        TEXT("project_owned_zambezi_multiscale_river_flow_normal");
    FlowNormalSpec.SourceRelativePath =
        TEXT("unreal/SourceArt/RaftSim/Water/ZambeziBatoka/"
             "T_RaftSim_ZambeziBatoka_FlowNormalV1.png");
    FlowNormalSpec.TextureAssetRootPackagePath =
        TEXT("/Game/RaftSim/Environment/ZambeziRun/Water/Textures");
    FlowNormalSpec.CompressionSettings = TC_Normalmap;
    FlowNormalSpec.bSRGB = false;
    FlowNormalSpec.LODGroup = TEXTUREGROUP_WorldNormalMap;
    FlowNormalSpec.AddressX = TA_Mirror;
    FlowNormalSpec.AddressY = TA_Mirror;
    FlowNormalSpec.bCompressionNoAlpha = true;
    bool bFlowNormalSaved = false;
    UTexture2D* FlowNormalTexture = CreateOrUpdateFirstPartyMaterialTextureAsset(
        FlowNormalSpec, Summary, bFlowNormalSaved);

    FRaftSimFirstPartyMaterialTextureAssetSpec FoamLaceSpec;
    FoamLaceSpec.RiverId = TEXT("zambezi_batoka_gorge");
    FoamLaceSpec.RiverAssetName = TEXT("ZambeziBatokaWaterV1");
    FoamLaceSpec.MapKey = TEXT("FoamLace");
    FoamLaceSpec.MapKind =
        TEXT("project_owned_zambezi_solver_masked_whitewater_lace");
    FoamLaceSpec.SourceRelativePath =
        TEXT("unreal/SourceArt/RaftSim/Water/ZambeziBatoka/"
             "T_RaftSim_ZambeziBatoka_FoamLaceV1.png");
    FoamLaceSpec.TextureAssetRootPackagePath =
        TEXT("/Game/RaftSim/Environment/ZambeziRun/Water/Textures");
    FoamLaceSpec.CompressionSettings = TC_Masks;
    FoamLaceSpec.bSRGB = false;
    FoamLaceSpec.LODGroup = TEXTUREGROUP_World;
    FoamLaceSpec.AddressX = TA_Mirror;
    FoamLaceSpec.AddressY = TA_Mirror;
    FoamLaceSpec.bCompressionNoAlpha = true;
    bool bFoamLaceSaved = false;
    UTexture2D* FoamLaceTexture = CreateOrUpdateFirstPartyMaterialTextureAsset(
        FoamLaceSpec, Summary, bFoamLaceSaved);

    UE_LOG(
        LogTemp,
        Display,
        TEXT("RaftSim Zambezi Batoka water textures:\n%s"),
        *Summary);
    return FlowNormalTexture != nullptr && bFlowNormalSaved &&
        FoamLaceTexture != nullptr && bFoamLaceSaved;
}

bool BuildCrewSkinTextureAssets()
{
    using namespace RaftSimEditorEnvironment;
    struct FTextureSpec
    {
        const TCHAR* MapKey;
        const TCHAR* MapKind;
        const TCHAR* SourceRelativePath;
        TextureCompressionSettings Compression;
        bool bSRGB;
        TextureGroup LODGroup;
    };
    static const FTextureSpec TextureSpecs[] = {
        {
            TEXT("MicrodetailAlbedo"),
            TEXT("neutral_skin_micro_albedo_variation"),
            TEXT("unreal/SourceArt/RaftSim/Crew/SyntheticSkin/"
                 "T_RaftSim_SyntheticSkin_MicroAlbedo.png"),
            TC_Default,
            true,
            TEXTUREGROUP_Character,
        },
        {
            TEXT("MicrodetailNormal"),
            TEXT("tangent_space_skin_micro_normal"),
            TEXT("unreal/SourceArt/RaftSim/Crew/SyntheticSkin/"
                 "T_RaftSim_SyntheticSkin_MicroNormal.png"),
            TC_Normalmap,
            false,
            TEXTUREGROUP_CharacterNormalMap,
        },
    };

    bool bAllSaved = true;
    FString Summary;
    for (const FTextureSpec& TextureSpec : TextureSpecs)
    {
        FRaftSimFirstPartyMaterialTextureAssetSpec Spec;
        Spec.RiverId = TEXT("synthetic_crew_skin");
        Spec.RiverAssetName = TEXT("CrewSkin");
        Spec.MapKey = TextureSpec.MapKey;
        Spec.MapKind = TextureSpec.MapKind;
        Spec.SourceRelativePath = TextureSpec.SourceRelativePath;
        Spec.TextureAssetRootPackagePath = TEXT("/Game/RaftSim/Characters/Textures");
        Spec.CompressionSettings = TextureSpec.Compression;
        Spec.bSRGB = TextureSpec.bSRGB;
        Spec.LODGroup = TextureSpec.LODGroup;
        Spec.AddressX = TA_Wrap;
        Spec.AddressY = TA_Wrap;
        Spec.bCompressionNoAlpha = true;
        bool bSaved = false;
        UTexture2D* Texture =
            CreateOrUpdateFirstPartyMaterialTextureAsset(Spec, Summary, bSaved);
        bAllSaved &= Texture != nullptr && bSaved;
    }
    UE_LOG(LogTemp, Display, TEXT("RaftSim crew skin textures:\n%s"), *Summary);
    return bAllSaved;
}

bool BuildEquipmentTextileTextureAssets()
{
    using namespace RaftSimEditorEnvironment;
    struct FTextureSpec
    {
        const TCHAR* TextileName;
        const TCHAR* MapKey;
        const TCHAR* MapKind;
        TextureCompressionSettings Compression;
        bool bSRGB;
        TextureGroup LODGroup;
    };
    static const FTextureSpec TextureSpecs[] = {
        {TEXT("RaftCoatedFabric"), TEXT("Albedo"), TEXT("neutral_tintable_albedo"),
         TC_Default, true, TEXTUREGROUP_World},
        {TEXT("RaftCoatedFabric"), TEXT("Normal"), TEXT("tangent_space_normal"),
         TC_Normalmap, false, TEXTUREGROUP_WorldNormalMap},
        {TEXT("RaftCoatedFabric"), TEXT("AORoughnessHeight"),
         TEXT("packed_ao_roughness_height"), TC_Masks, false, TEXTUREGROUP_WorldSpecular},
        {TEXT("PfdRipstop"), TEXT("Albedo"), TEXT("neutral_tintable_albedo"),
         TC_Default, true, TEXTUREGROUP_Character},
        {TEXT("PfdRipstop"), TEXT("Normal"), TEXT("tangent_space_normal"),
         TC_Normalmap, false, TEXTUREGROUP_CharacterNormalMap},
        {TEXT("PfdRipstop"), TEXT("AORoughnessHeight"),
         TEXT("packed_ao_roughness_height"), TC_Masks, false, TEXTUREGROUP_CharacterSpecular},
        {TEXT("WetsuitNeoprene"), TEXT("Albedo"), TEXT("neutral_tintable_albedo"),
         TC_Default, true, TEXTUREGROUP_Character},
        {TEXT("WetsuitNeoprene"), TEXT("Normal"), TEXT("tangent_space_normal"),
         TC_Normalmap, false, TEXTUREGROUP_CharacterNormalMap},
        {TEXT("WetsuitNeoprene"), TEXT("AORoughnessHeight"),
         TEXT("packed_ao_roughness_height"), TC_Masks, false, TEXTUREGROUP_CharacterSpecular},
    };

    bool bAllSaved = true;
    FString Summary;
    for (const FTextureSpec& TextureSpec : TextureSpecs)
    {
        FRaftSimFirstPartyMaterialTextureAssetSpec Spec;
        Spec.RiverId = TEXT("generated_equipment_textiles");
        Spec.RiverAssetName = TextureSpec.TextileName;
        Spec.MapKey = TextureSpec.MapKey;
        Spec.MapKind = TextureSpec.MapKind;
        Spec.SourceRelativePath = FString::Printf(
            TEXT("unreal/SourceArt/RaftSim/Equipment/GeneratedTextiles/"
                 "T_RaftSim_%s_%s.png"),
            TextureSpec.TextileName,
            TextureSpec.MapKey);
        Spec.TextureAssetRootPackagePath = TEXT("/Game/RaftSim/Equipment/Textures");
        Spec.CompressionSettings = TextureSpec.Compression;
        Spec.bSRGB = TextureSpec.bSRGB;
        Spec.LODGroup = TextureSpec.LODGroup;
        Spec.AddressX = TA_Wrap;
        Spec.AddressY = TA_Wrap;
        Spec.bCompressionNoAlpha = true;
        bool bSaved = false;
        UTexture2D* Texture =
            CreateOrUpdateFirstPartyMaterialTextureAsset(Spec, Summary, bSaved);
        bAllSaved &= Texture != nullptr && bSaved;
    }
    UE_LOG(LogTemp, Display, TEXT("RaftSim equipment textile textures:\n%s"), *Summary);
    return bAllSaved;
}

} // namespace RaftSimPhotorealMaterials
