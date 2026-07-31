#include "AssetRegistry/AssetRegistryModule.h"
#include "Engine/Texture2D.h"
#include "Environment/RaftSimEditorEnvironmentInternal.h"
#include "HAL/IConsoleManager.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpressionComponentMask.h"
#include "Materials/MaterialExpressionDepthFade.h"
#include "Materials/MaterialExpressionMultiply.h"
#include "Materials/MaterialExpressionParticleSubUV.h"
#include "Materials/MaterialExpressionScalarParameter.h"
#include "Materials/MaterialExpressionVertexColor.h"
#include "Misc/PackageName.h"
#include "NiagaraEmitterHandle.h"
#include "NiagaraSpriteRendererProperties.h"
#include "NiagaraSystem.h"
#include "Stateless/Modules/NiagaraStatelessModule_AddVelocity.h"
#include "Stateless/Modules/NiagaraStatelessModule_Drag.h"
#include "Stateless/Modules/NiagaraStatelessModule_GravityForce.h"
#include "Stateless/Modules/NiagaraStatelessModule_InitializeParticle.h"
#include "Stateless/Modules/NiagaraStatelessModule_ShapeLocation.h"
#include "Stateless/Modules/NiagaraStatelessModule_SubUVAnimation.h"
#include "Stateless/NiagaraStatelessEmitter.h"
#include "Stateless/NiagaraStatelessSpawnInfo.h"
#include "UObject/Package.h"
#include "UObject/SavePackage.h"
#include "UObject/UnrealType.h"

namespace
{
constexpr const TCHAR* SourceSystemPath =
    TEXT("/Niagara/DefaultAssets/Templates/Systems/FountainLightweight."
         "FountainLightweight");
constexpr const TCHAR* WaterVfxMaterialPath =
    TEXT("/Game/RaftSim/Materials/M_RaftSim_NiagaraWaterParticle."
         "M_RaftSim_NiagaraWaterParticle");
constexpr const TCHAR* WaterVfxV4ReviewMaterialPath =
    TEXT("/Game/RaftSim/VFX/Water/PhotographicSubUVV4Review/"
         "M_RaftSim_NiagaraWaterParticle_V4Review."
         "M_RaftSim_NiagaraWaterParticle_V4Review");
constexpr const TCHAR* WaterVfxV5ReviewMaterialPath =
    TEXT("/Game/RaftSim/VFX/Water/PhotographicSubUVV5Review/"
         "M_RaftSim_NiagaraWaterParticle_V5Review."
         "M_RaftSim_NiagaraWaterParticle_V5Review");
constexpr const TCHAR* UserSpawnRateName = TEXT("User.SpawnRate");
constexpr int32 ParticleAtlasGridSize = 4;
constexpr int32 ParticleAtlasFrameCount =
    ParticleAtlasGridSize * ParticleAtlasGridSize;

enum class EWaterParticleAtlasVariant : uint8
{
    Production,
    PhotographicV4Review,
    PhotographicV5Review,
};

struct FWaterNiagaraProfile
{
    const TCHAR* AssetName;
    float DefaultSpawnRate;
    FVector2f LifetimeRange;
    FVector2f SpriteMinCm;
    FVector2f SpriteMaxCm;
    FVector2f SourcePlaneCm;
    FVector2f SpeedRangeCmPerSecond;
    float ConeAngleDegrees;
    FVector3f GravityCmPerSecondSquared;
    float Drag;
    FLinearColor Color;
    bool bVelocityAligned;
    int32 FirstAtlasFrame;
    int32 LastAtlasFrame;
};

const FWaterNiagaraProfile WaterProfiles[] = {
    {
        TEXT("NS_RaftSim_SolverSpray"),
        260.0f,
        FVector2f(0.24f, 0.56f),
        FVector2f(2.0f, 3.0f),
        FVector2f(6.0f, 10.0f),
        FVector2f(52.0f, 32.0f),
        FVector2f(280.0f, 600.0f),
        34.0f,
        FVector3f(0.0f, 0.0f, -720.0f),
        0.72f,
        FLinearColor(0.68f, 0.79f, 0.82f, 0.55f),
        true,
        0,
        5,
    },
    {
        TEXT("NS_RaftSim_ContactDroplets"),
        320.0f,
        FVector2f(0.30f, 0.78f),
        FVector2f(0.6f, 0.6f),
        FVector2f(2.4f, 3.2f),
        FVector2f(56.0f, 40.0f),
        FVector2f(230.0f, 520.0f),
        38.0f,
        FVector3f(0.0f, 0.0f, -980.0f),
        0.18f,
        FLinearColor(0.70f, 0.82f, 0.86f, 0.62f),
        true,
        6,
        10,
    },
    {
        TEXT("NS_RaftSim_AeratedMist"),
        70.0f,
        FVector2f(1.10f, 2.60f),
        FVector2f(10.0f, 14.0f),
        FVector2f(30.0f, 42.0f),
        FVector2f(170.0f, 76.0f),
        FVector2f(35.0f, 85.0f),
        46.0f,
        FVector3f(0.0f, 0.0f, 18.0f),
        0.34f,
        FLinearColor(0.60f, 0.70f, 0.73f, 0.08f),
        false,
        11,
        13,
    },
    {
        TEXT("NS_RaftSim_RapidAerosol"),
        56.0f,
        FVector2f(1.35f, 3.10f),
        FVector2f(14.0f, 18.0f),
        FVector2f(44.0f, 60.0f),
        FVector2f(210.0f, 96.0f),
        FVector2f(32.0f, 86.0f),
        58.0f,
        FVector3f(0.0f, 0.0f, 12.0f),
        0.42f,
        FLinearColor(0.58f, 0.67f, 0.70f, 0.07f),
        false,
        14,
        15,
    },
    {
        TEXT("NS_RaftSim_RapidRoller"),
        220.0f,
        FVector2f(0.44f, 0.88f),
        FVector2f(8.0f, 16.0f),
        FVector2f(30.0f, 58.0f),
        FVector2f(240.0f, 70.0f),
        FVector2f(55.0f, 175.0f),
        38.0f,
        FVector3f(0.0f, 0.0f, -260.0f),
        0.55f,
        FLinearColor(0.66f, 0.75f, 0.77f, 0.30f),
        true,
        0,
        10,
    },
};

void SetVector2Range(
    FNiagaraDistributionRangeVector2& Distribution,
    const FVector2f& MinValue,
    const FVector2f& MaxValue)
{
    Distribution.Mode = ENiagaraDistributionMode::NonUniformRange;
    Distribution.Min = MinValue;
    Distribution.Max = MaxValue;
}

void SetVector3Range(
    FNiagaraDistributionRangeVector3& Distribution,
    const FVector3f& MinValue,
    const FVector3f& MaxValue)
{
    Distribution.Mode = ENiagaraDistributionMode::NonUniformRange;
    Distribution.Min = MinValue;
    Distribution.Max = MaxValue;
}

UTexture2D* BuildWaterParticleAtlasTexture(EWaterParticleAtlasVariant Variant)
{
    using namespace RaftSimEditorEnvironment;
    const bool bPhotographicV4Review =
        Variant == EWaterParticleAtlasVariant::PhotographicV4Review;
    const bool bPhotographicV5Review =
        Variant == EWaterParticleAtlasVariant::PhotographicV5Review;
    const bool bPhotographicReview =
        bPhotographicV4Review || bPhotographicV5Review;
    FRaftSimFirstPartyMaterialTextureAssetSpec TextureSpec;
    TextureSpec.RiverId = TEXT("american_south_fork");
    TextureSpec.RiverAssetName = bPhotographicV5Review
        ? TEXT("WaterParticleV5Review")
        : (bPhotographicV4Review
            ? TEXT("WaterParticleV4Review")
            : TEXT("WaterParticle"));
    TextureSpec.MapKey = TEXT("SubUV");
    TextureSpec.MapKind = bPhotographicReview
        ? TEXT("project_owned_image_generated_whitewater_particle_subuv_review")
        : TEXT("project_owned_whitewater_particle_subuv_atlas");
    TextureSpec.SourceRelativePath = bPhotographicV5Review
        ? TEXT("unreal/SourceArt/RaftSim/Water/PhotographicSubUVV5/"
               "T_RaftSim_WaterParticle_SubUV_v5_review.png")
        : (bPhotographicV4Review
            ? TEXT("unreal/SourceArt/RaftSim/Water/PhotographicSubUVV4/"
                   "T_RaftSim_WaterParticle_SubUV_v4_review.png")
            : TEXT("unreal/SourceArt/RaftSim/Water/"
                   "T_RaftSim_WaterParticle_SubUV.png"));
    TextureSpec.TextureAssetRootPackagePath = bPhotographicV5Review
        ? TEXT("/Game/RaftSim/VFX/Water/PhotographicSubUVV5Review/Textures")
        : (bPhotographicV4Review
            ? TEXT("/Game/RaftSim/VFX/Water/PhotographicSubUVV4Review/Textures")
            : TEXT("/Game/RaftSim/VFX/Water/Textures"));
    TextureSpec.CompressionSettings = TC_Masks;
    TextureSpec.bSRGB = false;
    TextureSpec.LODGroup = TEXTUREGROUP_Effects;
    TextureSpec.AddressX = TA_Clamp;
    TextureSpec.AddressY = TA_Clamp;
    TextureSpec.bCompressionNoAlpha = true;
    FString Summary;
    bool bSaved = false;
    UTexture2D* Texture = CreateOrUpdateFirstPartyMaterialTextureAsset(
        TextureSpec, Summary, bSaved);
    UE_LOG(LogTemp, Display,
        TEXT("RaftSim Niagara water VFX atlas:\n%s"), *Summary);
    return Texture != nullptr && bSaved ? Texture : nullptr;
}

bool BuildWaterParticleMaterial(
    UMaterial*& OutMaterial,
    EWaterParticleAtlasVariant Variant)
{
    UTexture2D* AtlasTexture =
        BuildWaterParticleAtlasTexture(Variant);
    if (!AtlasTexture)
    {
        UE_LOG(LogTemp, Error,
            TEXT("RaftSim Niagara water VFX: particle atlas build failed"));
        return false;
    }

    const bool bPhotographicV4Review =
        Variant == EWaterParticleAtlasVariant::PhotographicV4Review;
    const bool bPhotographicV5Review =
        Variant == EWaterParticleAtlasVariant::PhotographicV5Review;
    const TCHAR* PackagePath = bPhotographicV5Review
        ? TEXT("/Game/RaftSim/VFX/Water/PhotographicSubUVV5Review/"
               "M_RaftSim_NiagaraWaterParticle_V5Review")
        : (bPhotographicV4Review
            ? TEXT("/Game/RaftSim/VFX/Water/PhotographicSubUVV4Review/"
                   "M_RaftSim_NiagaraWaterParticle_V4Review")
            : TEXT("/Game/RaftSim/Materials/M_RaftSim_NiagaraWaterParticle"));
    const TCHAR* MaterialPath = bPhotographicV5Review
        ? WaterVfxV5ReviewMaterialPath
        : (bPhotographicV4Review
            ? WaterVfxV4ReviewMaterialPath
            : WaterVfxMaterialPath);
    const TCHAR* MaterialName = bPhotographicV5Review
        ? TEXT("M_RaftSim_NiagaraWaterParticle_V5Review")
        : (bPhotographicV4Review
            ? TEXT("M_RaftSim_NiagaraWaterParticle_V4Review")
            : TEXT("M_RaftSim_NiagaraWaterParticle"));
    UPackage* Package = CreatePackage(PackagePath);
    if (!Package)
    {
        return false;
    }
    OutMaterial = LoadObject<UMaterial>(nullptr, MaterialPath);
    if (!OutMaterial)
    {
        OutMaterial = NewObject<UMaterial>(
            Package,
            MaterialName,
            RF_Public | RF_Standalone | RF_Transactional);
        FAssetRegistryModule::AssetCreated(OutMaterial);
    }
    if (!OutMaterial)
    {
        return false;
    }
    OutMaterial->Modify();
    OutMaterial->GetExpressionCollection().Empty();
    OutMaterial->BlendMode = BLEND_Translucent;
    OutMaterial->TranslucencyLightingMode = TLM_VolumetricNonDirectional;
    OutMaterial->TwoSided = true;
    OutMaterial->SetShadingModel(MSM_DefaultLit);
    OutMaterial->SetUsageByFlag(MATUSAGE_NiagaraSprites, true);

    auto Add = [OutMaterial](UMaterialExpression* Expression)
        -> UMaterialExpression*
    {
        OutMaterial->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    auto Scalar = [&](const TCHAR* Name, float Value)
        -> UMaterialExpressionScalarParameter*
    {
        UMaterialExpressionScalarParameter* Expression =
            NewObject<UMaterialExpressionScalarParameter>(OutMaterial);
        Expression->ParameterName = Name;
        Expression->DefaultValue = Value;
        Expression->Group = TEXT("RaftSimNiagaraWaterParticle");
        return Cast<UMaterialExpressionScalarParameter>(Add(Expression));
    };
    auto Multiply = [&](UMaterialExpression* A, UMaterialExpression* B)
        -> UMaterialExpressionMultiply*
    {
        UMaterialExpressionMultiply* Expression =
            NewObject<UMaterialExpressionMultiply>(OutMaterial);
        Expression->A.Expression = A;
        Expression->B.Expression = B;
        return Cast<UMaterialExpressionMultiply>(Add(Expression));
    };

    UMaterialExpressionParticleSubUV* AtlasSample =
        NewObject<UMaterialExpressionParticleSubUV>(OutMaterial);
    AtlasSample->Texture = AtlasTexture;
    AtlasSample->SamplerType = SAMPLERTYPE_Masks;
    AtlasSample->bBlend = false;
    Add(AtlasSample);
    UMaterialExpressionComponentMask* AtlasMask =
        NewObject<UMaterialExpressionComponentMask>(OutMaterial);
    AtlasMask->Input.Expression = AtlasSample;
    AtlasMask->R = true;
    Add(AtlasMask);

    UMaterialExpressionVertexColor* ParticleColor =
        NewObject<UMaterialExpressionVertexColor>(OutMaterial);
    Add(ParticleColor);
    UMaterialExpressionMultiply* AtlasTimesParticleAlpha =
        NewObject<UMaterialExpressionMultiply>(OutMaterial);
    AtlasTimesParticleAlpha->A.Expression = AtlasMask;
    AtlasTimesParticleAlpha->B.Expression = ParticleColor;
    AtlasTimesParticleAlpha->B.OutputIndex = 4;
    Add(AtlasTimesParticleAlpha);
    UMaterialExpression* ParticleOpacity = Multiply(
        AtlasTimesParticleAlpha,
        Scalar(TEXT("ParticleOpacity"), 0.92f));

    UMaterialExpressionDepthFade* DepthFade =
        NewObject<UMaterialExpressionDepthFade>(OutMaterial);
    DepthFade->InOpacity.Expression = ParticleOpacity;
    DepthFade->FadeDistance.Expression =
        Scalar(TEXT("ParticleDepthFadeCm"), 14.0f);
    Add(DepthFade);
    UMaterialExpression* Emissive = Multiply(
        ParticleColor,
        Scalar(TEXT("ParticleEmissive"), 0.018f));

    UMaterialEditorOnlyData* EditorData = OutMaterial->GetEditorOnlyData();
    EditorData->BaseColor.Connect(0, ParticleColor);
    EditorData->Opacity.Connect(0, DepthFade);
    EditorData->Roughness.Connect(
        0, Scalar(TEXT("ParticleRoughness"), 0.42f));
    EditorData->Specular.Connect(
        0, Scalar(TEXT("ParticleSpecular"), 0.24f));
    EditorData->EmissiveColor.Connect(0, Emissive);

    OutMaterial->PostEditChange();
    Package->MarkPackageDirty();
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetAssetPackageExtension());
    return OutMaterial->GetUsageByFlag(MATUSAGE_NiagaraSprites) &&
        UPackage::SavePackage(Package, OutMaterial, *Filename, SaveArgs);
}

UNiagaraSystem* LoadOrDuplicateSystem(
    UNiagaraSystem* Source,
    const FWaterNiagaraProfile& Profile,
    EWaterParticleAtlasVariant Variant,
    bool& bOutCreated)
{
    const bool bPhotographicV4Review =
        Variant == EWaterParticleAtlasVariant::PhotographicV4Review;
    const bool bPhotographicV5Review =
        Variant == EWaterParticleAtlasVariant::PhotographicV5Review;
    const FString AssetName = bPhotographicV5Review
        ? FString::Printf(TEXT("%s_V5Review"), Profile.AssetName)
        : (bPhotographicV4Review
            ? FString::Printf(TEXT("%s_V4Review"), Profile.AssetName)
            : FString(Profile.AssetName));
    const TCHAR* PackageRoot = bPhotographicV5Review
        ? TEXT("/Game/RaftSim/VFX/Water/PhotographicSubUVV5Review")
        : (bPhotographicV4Review
            ? TEXT("/Game/RaftSim/VFX/Water/PhotographicSubUVV4Review")
            : TEXT("/Game/RaftSim/VFX/Water"));
    const FString PackagePath = FString::Printf(
        TEXT("%s/%s"),
        PackageRoot,
        *AssetName);
    const FString ObjectPath = FString::Printf(
        TEXT("%s.%s"), *PackagePath, *AssetName);
    if (UNiagaraSystem* Existing = LoadObject<UNiagaraSystem>(nullptr, *ObjectPath))
    {
        bOutCreated = false;
        return Existing;
    }

    UPackage* Package = CreatePackage(*PackagePath);
    if (!Package)
    {
        return nullptr;
    }
    UNiagaraSystem* System = Cast<UNiagaraSystem>(StaticDuplicateObject(
        Source,
        Package,
        *AssetName,
        RF_Public | RF_Standalone | RF_Transactional,
        UNiagaraSystem::StaticClass()));
    if (System)
    {
        Package->SetAssetAccessSpecifier(EAssetAccessSpecifier::Public);
        FAssetRegistryModule::AssetCreated(System);
        bOutCreated = true;
    }
    return System;
}

FNiagaraEmitterStateData* FindEmitterState(UNiagaraStatelessEmitter* Emitter)
{
    const FStructProperty* Property = FindFProperty<FStructProperty>(
        UNiagaraStatelessEmitter::StaticClass(), TEXT("EmitterState"));
    return Property
        ? Property->ContainerPtrToValuePtr<FNiagaraEmitterStateData>(Emitter)
        : nullptr;
}

bool ConfigureSystem(
    UNiagaraSystem* System,
    UMaterial* Material,
    const FWaterNiagaraProfile& Profile)
{
    if (!System || System->GetEmitterHandles().IsEmpty())
    {
        return false;
    }

    FNiagaraEmitterHandle& Handle = System->GetEmitterHandles()[0];
    UNiagaraStatelessEmitter* Emitter = Handle.GetStatelessEmitter();
    if (!Emitter)
    {
        UE_LOG(LogTemp, Error,
            TEXT("RaftSim Niagara water VFX: %s has no stateless emitter"),
            Profile.AssetName);
        return false;
    }

    System->Modify();
    Emitter->Modify();
    if (FNiagaraEmitterStateData* State = FindEmitterState(Emitter))
    {
        State->LoopBehavior = ENiagaraLoopBehavior::Infinite;
        State->LoopDuration.InitConstant(1.0f);
        State->bLoopDelayEnabled = false;
        State->bEnableDistanceCulling = true;
        State->bMaxDistanceEnabled = true;
        State->MaxDistance = 12000.0f;
    }
    else
    {
        UE_LOG(LogTemp, Error,
            TEXT("RaftSim Niagara water VFX: emitter state unavailable for %s"),
            Profile.AssetName);
        return false;
    }

    FNiagaraStatelessSpawnInfo* Spawn = Emitter->GetSpawnInfoByIndex(0);
    if (!Spawn)
    {
        Spawn = &Emitter->AddSpawnInfo();
    }
    Spawn->Type = ENiagaraStatelessSpawnInfoType::Rate;
    Spawn->bEnabled = true;
    Spawn->bSpawnProbabilityEnabled = false;
    Spawn->bLoopCountLimitEnabled = false;
    const FNiagaraVariable SpawnRateVariable(
        FNiagaraTypeDefinition::GetFloatDef(), FName(UserSpawnRateName));
    Spawn->Rate.Mode = ENiagaraDistributionMode::Binding;
    Spawn->Rate.ParameterBinding = SpawnRateVariable;
    System->GetExposedParameters().AddParameter(SpawnRateVariable);
    System->GetExposedParameters().SetParameterValue<float>(
        Profile.DefaultSpawnRate, SpawnRateVariable, true);

    UNiagaraStatelessModule_InitializeParticle* Initialize =
        Cast<UNiagaraStatelessModule_InitializeParticle>(Emitter->GetModule(
            UNiagaraStatelessModule_InitializeParticle::StaticClass()));
    UNiagaraStatelessModule_ShapeLocation* Shape =
        Cast<UNiagaraStatelessModule_ShapeLocation>(Emitter->GetModule(
            UNiagaraStatelessModule_ShapeLocation::StaticClass()));
    UNiagaraStatelessModule_AddVelocity* Velocity =
        Cast<UNiagaraStatelessModule_AddVelocity>(Emitter->GetModule(
            UNiagaraStatelessModule_AddVelocity::StaticClass()));
    UNiagaraStatelessModule_GravityForce* Gravity =
        Cast<UNiagaraStatelessModule_GravityForce>(Emitter->GetModule(
            UNiagaraStatelessModule_GravityForce::StaticClass()));
    UNiagaraStatelessModule_Drag* Drag =
        Cast<UNiagaraStatelessModule_Drag>(Emitter->GetModule(
            UNiagaraStatelessModule_Drag::StaticClass()));
    UNiagaraStatelessModule_SubUVAnimation* SubUv =
        Cast<UNiagaraStatelessModule_SubUVAnimation>(Emitter->GetModule(
            UNiagaraStatelessModule_SubUVAnimation::StaticClass()));
    if (!Initialize || !Shape || !Velocity || !Gravity || !Drag || !SubUv)
    {
        UE_LOG(LogTemp, Error,
            TEXT("RaftSim Niagara water VFX: template modules incomplete for %s"),
            Profile.AssetName);
        return false;
    }

    Initialize->LifetimeDistribution.InitRange(
        Profile.LifetimeRange.X, Profile.LifetimeRange.Y);
    SetVector2Range(
        Initialize->SpriteSizeDistribution,
        Profile.SpriteMinCm,
        Profile.SpriteMaxCm);
    Initialize->ColorDistribution.InitConstant(Profile.Color);
    if (Profile.bVelocityAligned)
    {
        Initialize->SpriteRotationDistribution.InitConstant(0.0f);
    }
    else
    {
        Initialize->SpriteRotationDistribution.InitRange(-0.5f, 0.5f);
    }
    Shape->ShapePrimitive = ENSM_ShapePrimitive::Plane;
    Shape->PlaneSize.InitConstant(Profile.SourcePlaneCm);
    Shape->bPlaneEdgesOnly = false;
    Shape->CoordinateSpace = ENiagaraCoordinateSpace::Local;
    Velocity->VelocityType = ENSM_VelocityType::InCone;
    Velocity->ConeRotationType = ENSM_ConeRotationType::Direction;
    Velocity->ConeDirection.InitConstant(FVector3f::XAxisVector);
    Velocity->ConeVelocityDistribution.InitRange(
        Profile.SpeedRangeCmPerSecond.X,
        Profile.SpeedRangeCmPerSecond.Y);
    Velocity->ConeAngle = Profile.ConeAngleDegrees;
    Velocity->InnerCone = 0.0f;
    Velocity->CoordinateSpace = ENiagaraCoordinateSpace::Local;
    Gravity->GravityDistribution.InitConstant(
        Profile.GravityCmPerSecondSquared);
    Drag->DragDistribution.InitConstant(Profile.Drag);
    SubUv->SetIsModuleEnabled(true);
    SubUv->NumFrames = ParticleAtlasFrameCount;
    SubUv->AnimationMode = ENSMSubUVAnimation_Mode::DirectSet;
    SubUv->FrameIndex.Mode = ENiagaraDistributionMode::UniformRange;
    SubUv->FrameIndex.Min = Profile.FirstAtlasFrame;
    SubUv->FrameIndex.Max = Profile.LastAtlasFrame;

    bool bConfiguredRenderer = false;
    for (UNiagaraRendererProperties* Renderer : Emitter->GetRenderers())
    {
        if (UNiagaraSpriteRendererProperties* Sprite =
                Cast<UNiagaraSpriteRendererProperties>(Renderer))
        {
            Sprite->Material = Material;
            Sprite->Alignment = Profile.bVelocityAligned
                ? ENiagaraSpriteAlignment::VelocityAligned
                : ENiagaraSpriteAlignment::Unaligned;
            Sprite->FacingMode = ENiagaraSpriteFacingMode::FaceCameraPosition;
            Sprite->SortMode = ENiagaraSortMode::ViewDepth;
            Sprite->SubImageSize = FVector2D(
                ParticleAtlasGridSize,
                ParticleAtlasGridSize);
            Sprite->bSubImageBlend = false;
            Sprite->bCastShadows = false;
            bConfiguredRenderer = true;
        }
    }
    if (!bConfiguredRenderer)
    {
        UE_LOG(LogTemp, Error,
            TEXT("RaftSim Niagara water VFX: no sprite renderer in %s"),
            Profile.AssetName);
        return false;
    }

    Emitter->PostEditChange();
    System->PostEditChange();
    System->RequestCompile(true);
    System->WaitForCompilationComplete(false, false);
    System->GetOutermost()->MarkPackageDirty();
    return true;
}

bool SaveSystem(UNiagaraSystem* System)
{
    UPackage* Package = System ? System->GetOutermost() : nullptr;
    if (!Package)
    {
        return false;
    }
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    const FString Filename = FPackageName::LongPackageNameToFilename(
        Package->GetName(), FPackageName::GetAssetPackageExtension());
    return UPackage::SavePackage(Package, System, *Filename, SaveArgs);
}

void CreateNiagaraWaterVfxSystemsImpl(EWaterParticleAtlasVariant Variant)
{
    UMaterial* Material = nullptr;
    if (!BuildWaterParticleMaterial(Material, Variant))
    {
        return;
    }
    UNiagaraSystem* Source = LoadObject<UNiagaraSystem>(nullptr, SourceSystemPath);
    if (!Source)
    {
        UE_LOG(LogTemp, Error,
            TEXT("RaftSim Niagara water VFX: missing source system %s"),
            SourceSystemPath);
        return;
    }
    Source->WaitForCompilationComplete(false, false);

    int32 SavedCount = 0;
    for (const FWaterNiagaraProfile& Profile : WaterProfiles)
    {
        FWaterNiagaraProfile AuthoredProfile = Profile;
        if (Variant == EWaterParticleAtlasVariant::PhotographicV5Review)
        {
            // V5 replaces broad procedural masks with sparse water-film
            // silhouettes. Compensate only their optical density so the same
            // production-scale sprites survive the material path; dimensions,
            // lifetimes, rates, velocities, and solver authority stay exact.
            if (Profile.FirstAtlasFrame == 11)
            {
                AuthoredProfile.Color.A = 0.16f;
            }
            else if (Profile.FirstAtlasFrame == 14)
            {
                AuthoredProfile.Color.A = 0.14f;
            }
            else if (Profile.LastAtlasFrame == 5)
            {
                AuthoredProfile.Color.A = 0.78f;
            }
            else if (Profile.FirstAtlasFrame == 6)
            {
                AuthoredProfile.Color.A = 0.88f;
            }
            else
            {
                AuthoredProfile.Color.A = 0.42f;
            }
        }
        bool bCreated = false;
        UNiagaraSystem* System = LoadOrDuplicateSystem(
            Source, AuthoredProfile, Variant, bCreated);
        const bool bConfigured = ConfigureSystem(
            System, Material, AuthoredProfile);
        const bool bSaved = bConfigured && SaveSystem(System);
        SavedCount += bSaved ? 1 : 0;
        UE_LOG(LogTemp, Display,
            TEXT("RaftSim Niagara water VFX: asset=%s created=%d saved=%d"),
            AuthoredProfile.AssetName,
            bCreated ? 1 : 0,
            bSaved ? 1 : 0);
    }
    UE_LOG(LogTemp, Display,
        TEXT("RaftSim Niagara water VFX: completed %d/%d systems mode=%s"),
        SavedCount,
        UE_ARRAY_COUNT(WaterProfiles),
        Variant == EWaterParticleAtlasVariant::PhotographicV5Review
            ? TEXT("photographic_v5_review")
            : (Variant == EWaterParticleAtlasVariant::PhotographicV4Review
                ? TEXT("photographic_v4_review")
                : TEXT("production")));
}

void CreateNiagaraWaterVfxSystems(const TArray<FString>&)
{
    CreateNiagaraWaterVfxSystemsImpl(EWaterParticleAtlasVariant::Production);
}

void CreatePhotographicV4ReviewNiagaraWaterVfxSystems(const TArray<FString>&)
{
    CreateNiagaraWaterVfxSystemsImpl(
        EWaterParticleAtlasVariant::PhotographicV4Review);
}

void CreatePhotographicV5ReviewNiagaraWaterVfxSystems(const TArray<FString>&)
{
    CreateNiagaraWaterVfxSystemsImpl(
        EWaterParticleAtlasVariant::PhotographicV5Review);
}

static FAutoConsoleCommand GCreateNiagaraWaterVfxSystemsCommand(
    TEXT("RaftSim.CreateNiagaraWaterVfxSystems"),
    TEXT("Author five project-owned solver-driven Niagara water VFX systems."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&CreateNiagaraWaterVfxSystems));

static FAutoConsoleCommand GCreatePhotographicV4ReviewNiagaraWaterVfxSystemsCommand(
    TEXT("RaftSim.CreatePhotographicV4ReviewNiagaraWaterVfxSystems"),
    TEXT("Author five isolated review-only Niagara systems using the project-owned photographic V4 atlas."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &CreatePhotographicV4ReviewNiagaraWaterVfxSystems));

static FAutoConsoleCommand GCreatePhotographicV5ReviewNiagaraWaterVfxSystemsCommand(
    TEXT("RaftSim.CreatePhotographicV5ReviewNiagaraWaterVfxSystems"),
    TEXT("Author five isolated review-only Niagara systems using the project-owned particle-scale photographic V5 atlas."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &CreatePhotographicV5ReviewNiagaraWaterVfxSystems));
}
