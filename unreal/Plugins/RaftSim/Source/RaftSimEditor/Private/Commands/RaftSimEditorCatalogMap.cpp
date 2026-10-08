// Source-registered catalog reaches. No cloned map, Hance drape/backdrop,
// analytic channel burn, invented collision proxy or provisional flow field.
#include "Environment/RaftSimEditorEnvironmentInternal.h"
#include "Environment/RaftSimContinuousRiverSpec.h"
#include "Environment/RaftSimContinuousCollisionProbes.h"
#include "Materials/RaftSimLiquidDataset.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/WorldSettings.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRiverWaterConfig.h"
#include "RaftSimRapidChallengeProfiles.h"
#include "RaftSimGeographicTakeout.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "RaftSimRescueStreamingComponent.h"
#include "LandscapeSubsystem.h"
#include "LandscapeInfo.h"
#include "LandscapeStreamingProxy.h"
#include "LandscapeDataAccess.h"
#include "LandscapeEditTypes.h"
#include "WorldPartition/WorldPartition.h"
#include "WorldPartition/ActorDescContainerInstance.h"
#include "WorldPartition/WorldPartitionActorDescInstance.h"
#include "WorldPartition/WorldPartitionHandle.h"
#include "WorldPartition/LoaderAdapter/LoaderAdapterActorList.h"
#include "UObject/GarbageCollection.h"
#include "UObject/StrongObjectPtr.h"
#include "Misc/ScopeExit.h"
#include "Materials/MaterialExpressionDivide.h"
#include "FileHelpers.h"

namespace RaftSimCatalogMap
{
using namespace RaftSimEditorEnvironment;

static bool RelativeFile(const FString& Name, FString& Absolute)
{
    if (Name.IsEmpty() || !FPaths::IsRelative(Name) || Name.Contains(TEXT(".."))) return false;
    Absolute = FPaths::ConvertRelativePathToFull(GetRepoRoot() / Name);
    return FPaths::FileExists(Absolute);
}

// Reuse only small-scale Colorado material detail, never a geographic drape.
static UMaterial* TerrainMaterial(const RaftSimContinuousRiver::FSpec* River=nullptr)
{
    const bool Chilko=River && River->bChilko;
    // A new asset version preserves already-saved maps. World-XY projection
    // stretches a texel vertically over an entire cliff; use the same detail
    // texture on three world planes without modifying any terrain geometry.
    const FString ObjectName = Chilko ? TEXT("M_ChilkoContinuousGroundV2") : TEXT("M_ColoradoCatalogGroundV2");
    const FString PackageName = TEXT("/Game/RaftSim/Materials/Catalog/")+ObjectName;
    if (UMaterial* Existing = LoadObject<UMaterial>(nullptr, *(PackageName+TEXT(".")+ObjectName))) return Existing;
    const FString TextureName=TEXT("T_RaftSim_")+(Chilko ? FString(TEXT("Chilko")) : FString(TEXT("ColoradoRiver")))+TEXT("_TerrainDetailAlbedo");
    UTexture2D* Albedo = LoadObject<UTexture2D>(nullptr,
        *(TEXT("/Game/RaftSim/Rendering/ProductionDetailTextures/Textures/")+TextureName+TEXT(".")+TextureName));
    if (!Albedo) return nullptr;
    UPackage* Package = CreatePackage(*PackageName);
    UMaterial* M = NewObject<UMaterial>(Package,*ObjectName,RF_Public|RF_Standalone);
    M->SetShadingModel(MSM_DefaultLit);
    auto* Position = NewObject<UMaterialExpressionWorldPosition>(M);
    auto* Scale = NewObject<UMaterialExpressionMultiply>(M);
    Scale->A.Expression=Position; Scale->ConstB=1.0f/350.0f;
    auto* Normal=NewObject<UMaterialExpressionVertexNormalWS>(M);
    auto* SquaredNormal=NewObject<UMaterialExpressionMultiply>(M);
    SquaredNormal->A.Expression=Normal; SquaredNormal->B.Expression=Normal;
    for(UMaterialExpression* E:TArray<UMaterialExpression*>{Position,Scale,Normal,SquaredNormal})
        M->GetExpressionCollection().AddExpression(E);
    UMaterialExpression* ColorSum=nullptr;
    UMaterialExpression* WeightSum=nullptr;
    for(int32 Axis=0;Axis<3;++Axis)
    {
        auto* UV=NewObject<UMaterialExpressionComponentMask>(M);
        UV->Input.Expression=Scale;
        // X normal -> YZ, Y normal -> XZ, Z normal -> XY.
        UV->R=Axis!=0; UV->G=Axis!=1; UV->B=Axis!=2; UV->A=false;
        auto* Weight=NewObject<UMaterialExpressionComponentMask>(M);
        Weight->Input.Expression=SquaredNormal;
        Weight->R=Axis==0; Weight->G=Axis==1; Weight->B=Axis==2; Weight->A=false;
        auto* Sample=NewObject<UMaterialExpressionTextureSampleParameter2D>(M);
        Sample->ParameterName=Chilko ? TEXT("ChilkoGroundDetail") : TEXT("ColoradoGroundDetail");
        Sample->Texture=Albedo; Sample->Coordinates.Expression=UV; Sample->SamplerType=SAMPLERTYPE_Color;
        auto* Weighted=NewObject<UMaterialExpressionMultiply>(M);
        Weighted->A.Expression=Sample; Weighted->B.Expression=Weight;
        for(UMaterialExpression* E:TArray<UMaterialExpression*>{UV,Weight,Sample,Weighted})
            M->GetExpressionCollection().AddExpression(E);
        if(!ColorSum){ColorSum=Weighted;WeightSum=Weight;}
        else
        {
            auto* AddColor=NewObject<UMaterialExpressionAdd>(M);
            AddColor->A.Expression=ColorSum; AddColor->B.Expression=Weighted;
            auto* AddWeight=NewObject<UMaterialExpressionAdd>(M);
            AddWeight->A.Expression=WeightSum; AddWeight->B.Expression=Weight;
            M->GetExpressionCollection().AddExpression(AddColor);
            M->GetExpressionCollection().AddExpression(AddWeight);
            ColorSum=AddColor;WeightSum=AddWeight;
        }
    }
    auto* Blend=NewObject<UMaterialExpressionDivide>(M);
    Blend->A.Expression=ColorSum; Blend->B.Expression=WeightSum;
    M->GetExpressionCollection().AddExpression(Blend);
    auto* Roughness=NewObject<UMaterialExpressionConstant>(M); Roughness->R=.86f;
    M->GetExpressionCollection().AddExpression(Roughness);
    M->GetEditorOnlyData()->BaseColor.Expression=Blend;
    M->GetEditorOnlyData()->Roughness.Expression=Roughness;
    M->PostEditChange(); FAssetRegistryModule::AssetCreated(M); Package->MarkPackageDirty();
    const FString Filename=FPackageName::LongPackageNameToFilename(PackageName,FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename),true);
    FSavePackageArgs SaveArgs; SaveArgs.TopLevelFlags=RF_Public|RF_Standalone; SaveArgs.SaveFlags=SAVE_NoError;
    return UPackage::SavePackage(Package,M,*Filename,SaveArgs) ? M : nullptr;
}

static bool RegisterRapidProfiles(ARaftSimRiverWaterConfig& Water,const TSharedPtr<FJsonObject>& J,FString& Error)
{
    const TArray<TSharedPtr<FJsonValue>>* Sources=nullptr;
    if(!J->HasField(TEXT("rapid_profile_sources")))return true;
    if(!J->TryGetArrayField(TEXT("rapid_profile_sources"),Sources) || !Sources || Sources->IsEmpty())
    {Error=TEXT("Empty or malformed rapid registration sources");return false;}
    const auto Files=J->GetObjectField(TEXT("files_sha256"));
    FString TargetPath;
    if(!RelativeFile(Water.CoordinateMapPath,TargetPath))return false;
    const auto TargetJSON=FRaftSimLiquidDataset::Read(TargetPath);
    RaftSimContinuousRiver::FSpec River;
    if(!RaftSimContinuousRiver::Resolve(J,River,Error))return false;
    auto* Target=NewObject<URaftSimWaterRuntimeAdapter>();
    if(!TargetJSON || !Target->ConfigureRiverCoordinateMap(TargetPath))return false;
    TSet<FString> Seen;
    TArray<FRaftSimRapidFeature> All;
    for(const auto& V:*Sources)
    {
        const auto Source=V->AsObject(); if(!Source)return false;
        const FString Map=Source->GetStringField(TEXT("map"));
        const FString Chart=Source->GetStringField(TEXT("coordinate_map"));
        FString Path;
        if(Seen.Contains(Map) || !RaftSimRapidChallengeProfiles::HasProfile(Map) ||
            !Files->HasField(Chart) || !RelativeFile(Chart,Path) ||
            !FRaftSimLiquidDataset::Hash(Path).Equals(Files->GetStringField(Chart),ESearchCase::IgnoreCase))
        {Error=TEXT("Unknown, duplicate or changed rapid source");return false;}
        Seen.Add(Map);
        const auto S=FRaftSimLiquidDataset::Read(Path);
        if(!S)return false;
        // Source charts must already share the river's reviewed geographic frame.
        for(const TCHAR* Key:{TEXT("world_y_sign"),TEXT("vertical_datum_m")})
            if(S->GetNumberField(Key)!=TargetJSON->GetNumberField(Key))
            {Error=TEXT("Rapid source uses another world frame");return false;}
        FVector2D SO,TO;double SD=0,TD=0;
        if(!RaftSimContinuousRiver::Frame(S,River,SO,SD,Error) ||
            !RaftSimContinuousRiver::Frame(TargetJSON,River,TO,TD,Error) || SO!=TO || SD!=TD)
        {Error=TEXT("Rapid source has no matching geographic origin/datum");return false;}
        auto* Adapter=NewObject<URaftSimWaterRuntimeAdapter>();
        TArray<FRaftSimRapidFeature> Registered;
        if(!Adapter->ConfigureRiverCoordinateMap(Path) || !RaftSimRapidChallengeProfiles::Register(
            *Adapter,*Target,RaftSimRapidChallengeProfiles::Features(Map),Registered,Error))return false;
        UE_LOG(LogTemp,Display,TEXT("Registered rapid profile %s: %d sites in continuous chart; authored dimensions unchanged"),*Map,Registered.Num());
        All.Append(Registered);
    }
    Water.RegisteredRapidFeatures=MoveTemp(All);
    Water.RegisteredRapidChartFingerprint=Target->GetRiverCoordinateMapFingerprint();
    TArray<FRaftSimRapidFeature> Validated;
    return Water.ResolveRapidFeatures(TEXT(""),*Target,Validated,Error);
}

static bool ResolveGeographicFinish(const TSharedPtr<FJsonObject>& J,double Start,double& Finish,FString& Error)
{
    RaftSimContinuousRiver::FSpec River;
    if(!RaftSimContinuousRiver::Resolve(J,River,Error))return false;
    if(!J->HasField(TEXT("geographic_takeout")))
    {
        bool Full=false;
        if(River.RiverId==TEXT("colorado_river_grand_canyon_rowing") &&
            J->TryGetBoolField(TEXT("full_river_coverage"),Full) && Full)
        {Error=TEXT("Full Colorado run requires mapped Pearce Ferry takeout");return false;}
        return true;
    }
    const auto G=J->GetObjectField(TEXT("geographic_takeout"));
    if(!G || G->GetStringField(TEXT("schema"))!=TEXT("raftsim.native_geographic_takeout.v1") ||
        River.RiverId!=TEXT("colorado_river_grand_canyon_rowing"))return false;
    FString Path;
    if(!RelativeFile(J->GetStringField(TEXT("coordinate_map")),Path) ||
        !FRaftSimLiquidDataset::Hash(Path).Equals(G->GetStringField(TEXT("coordinate_map_sha256")),ESearchCase::IgnoreCase))
    {Error=TEXT("Takeout target chart identity changed");return false;}
    const auto& A=G->GetArrayField(TEXT("takeout_world_xy_cm"));
    const auto& B=G->GetArrayField(TEXT("downstream_rapid_world_xy_cm"));
    const auto& C=G->GetArrayField(TEXT("cooked_station_interval_m"));
    if(A.Num()!=2 || B.Num()!=2 || C.Num()!=2)return false;
    auto* Adapter=NewObject<URaftSimWaterRuntimeAdapter>();FVector2D Registered;
    if(!Adapter->ConfigureRiverCoordinateMap(Path) || !RaftSimGeographicTakeout::Resolve(*Adapter,
        {A[0]->AsNumber(),A[1]->AsNumber()},{B[0]->AsNumber(),B[1]->AsNumber()},
        {C[0]->AsNumber(),C[1]->AsNumber()},Start,Registered,Error))return false;
    Finish=Registered.X;
    UE_LOG(LogTemp,Display,TEXT("Geographic Pearce Ferry finish station=%.9f left_lateral=%.9f ramp_docking_accepted=0"),Finish,Registered.Y);
    return true;
}

static bool AddRuntime(UWorld* World, const TSharedPtr<FJsonObject>& J, FString& Error)
{
    RaftSimContinuousRiver::FSpec River;
    if (!World || !J || !J->HasField(TEXT("rig")) || !RaftSimContinuousRiver::Resolve(J,River,Error)) return false;
    const auto Launch=J->GetObjectField(TEXT("launch"));
    const auto& XYZ=Launch->GetArrayField(TEXT("location_cm"));
    const double Start=Launch->GetNumberField(TEXT("station_m"));
    double Finish=J->GetNumberField(TEXT("finish_station_m"));
    if(!ResolveGeographicFinish(J,Start,Finish,Error))return false;
    if (XYZ.Num()!=3 || !FMath::IsFinite(Start) || !FMath::IsFinite(Finish) || Finish<=Start ||
        Launch->GetNumberField(TEXT("minimum_footprint_depth_m"))<1.) return false;
    const FVector LaunchCm(XYZ[0]->AsNumber(),XYZ[1]->AsNumber(),XYZ[2]->AsNumber());
    const FRotator Rotation(0,Launch->GetNumberField(TEXT("yaw_deg")),0);
    if (LaunchCm.ContainsNaN() || Rotation.ContainsNaN()) return false;
    UClass* Mode=LoadClass<AGameModeBase>(nullptr,TEXT("/Script/SmokeEmIfYouGotEm.RaftSimVerticalSliceGameMode"));
    if (!Mode) return false;
    World->GetWorldSettings()->DefaultGameMode=Mode;
    auto* Water=World->SpawnActor<ARaftSimRiverWaterConfig>(); if (!Water) return false;
    Water->CookedFieldsDir=J->GetStringField(TEXT("cooked_fields"));
    Water->FlowBand=FName(*J->GetStringField(TEXT("flow_band")));
    Water->CoordinateMapPath=J->GetStringField(TEXT("coordinate_map"));
    if(!RegisterRapidProfiles(*Water,J,Error))return false;
    Water->StreamingManifestPath=J->GetStringField(TEXT("streaming"));
    Water->WindowCenterM=FVector2D(Start,0); Water->WindowExtentM=480;
    Water->bRecenterHydraulicCrux=false; Water->bEnableMovingWindowStreaming=true;
    Water->MovingWindowStationExtentM=480; Water->MovingWindowAdvanceM=80;
    Water->MovingWindowLateralExtentM=J->GetNumberField(TEXT("lateral_extent_m"));
    Water->LivePresentationWidthM=Water->MovingWindowLateralExtentM;
    Water->bEnableCookedFarFieldWater=true; Water->bMapProvidesTerrain=true;
    Water->bLiveSolverOwnsRuntimeRendering=true; Water->bEnableLiveSolverVolumeCore=true;
    const FString WaterFolder=TEXT("/Game/RaftSim/Environment/")+River.AssetFolder+TEXT("/Water/");
    const FString MaterialName=TEXT("MI_RaftSim_")+River.WaterStem+TEXT("_LiveVolumeWaterV2");
    const FString NormalName=TEXT("T_RaftSim_")+River.WaterStem+TEXT("WaterV1_FlowNormal");
    const FString FoamName=TEXT("T_RaftSim_")+River.WaterStem+TEXT("WaterV1_FoamLace");
    Water->LiveVolumeCoreMaterialOverride=LoadObject<UMaterialInterface>(nullptr,
        *(WaterFolder+TEXT("Materials/")+MaterialName+TEXT(".")+MaterialName));
    Water->LiveWaterFlowNormalTexture=LoadObject<UTexture2D>(nullptr,
        *(WaterFolder+TEXT("Textures/")+NormalName+TEXT(".")+NormalName));
    Water->LiveWaterFoamLaceTexture=LoadObject<UTexture2D>(nullptr,
        *(WaterFolder+TEXT("Textures/")+FoamName+TEXT(".")+FoamName));
    if (!Water->LiveVolumeCoreMaterialOverride || !Water->LiveWaterFlowNormalTexture || !Water->LiveWaterFoamLaceTexture)
    { Error=TEXT("Missing river-specific water optics: ")+River.RiverId; return false; }
    Water->LiveSurfaceCalmCoverage=.035f; Water->LiveSurfaceActiveCoverage=.14f;
    Water->LiveSurfaceRoughness=.32f; Water->LiveFoamIntensity=.55f;
    if(River.bChilko)
    {
        // Existing reviewed Chilko presentation, not Colorado optics or a
        // borrowed geographic whitewater mask. No simulation state is changed.
        Water->LiveSurfaceSpecular=.18f;Water->LiveSurfaceRoughness=.42f;
        Water->LiveSkyReflectionStrength=.05f;Water->LiveRippleStrength=.72f;
        Water->LiveFoamIntensity=.56f;
        Water->bEnableLivePresentationSurfaceSmoothing=true;
        Water->LivePresentationSurfaceSmoothingStrength=.58f;
        Water->LivePresentationStandingWaveScale=.78f;
        Water->LivePresentationHydraulicReliefScale=.78f;
        Water->LiveRapidFoamFocusStart=.12f;Water->LiveRapidFoamFocusEnd=.72f;
        Water->LiveRapidFoamCoverageGain=.90f;Water->LiveSurfaceBankBlendMeters=4.5f;
        Water->bEnableLivePresentationBankNaturalism=true;
        Water->LivePresentationBankNaturalismAmplitudeMeters=.90f;
        Water->LiveShallowSurfaceColor=FLinearColor(.069f,.075f,.080f,1);
        Water->LiveDeepSurfaceColor=FLinearColor(.012f,.020f,.021f,1);
        Water->LiveReflectedSkyColor=FLinearColor(.025f,.050f,.075f,1);
        Water->LiveWaterScattering=FLinearColor(.00015f,.00016f,.00018f,0);
        Water->LiveWaterAbsorption=FLinearColor(.0080f,.0040f,.0045f,0);
        Water->LiveRiverbedColorScale=FLinearColor(.088f,.085f,.086f,0);
        Water->LiveShallowWaterOpacity=.36f;Water->LiveOpticalDepthResponseExponent=.25f;
        Water->LiveDeepWaterOpacity=.84f;Water->LiveFoamWaterOpacity=.86f;
        Water->bEnforceTaggedDirectionalLightPresentation=true;
        Water->RuntimeDirectionalLightActorTag=TEXT("RaftSimColdWaterHighlightNaturalismV1");
        Water->RuntimeDirectionalLightIntensity=2.90f;
        Water->RuntimeDirectionalLightRotation=FRotator(-50,55,0);
        for(const TCHAR* Tag:{TEXT("RaftSimChilkoTransmittingWaterV2"),TEXT("RaftSimChilkoLocalizedReflectionWaterV3"),
            TEXT("RaftSimColdWaterHighlightNaturalismV1"),TEXT("RaftSimColdWaterDepthAttenuationV2"),
            TEXT("RaftSimColdWaterNonlinearOpticalDepthV1"),TEXT("RaftSimSolverMaskedFoamLace"),TEXT("RaftSimNoSolverStateMutation")})
            Water->Tags.AddUnique(Tag);
    }
    Water->bEnableLiveRapidSurfaceRefinement=true; Water->LiveRapidSurfaceSubdivision=2;
    Water->bEnableLiveRaftLocalFluidHeightfield=true; Water->LiveRaftLocalFluidWindowMeters=100;
    Water->LiveRaftLocalFluidHeightfieldStrength=.65f;
    Water->ObservedWhitewaterGain=0; // Never borrow Hance's geographic foam mask.
    Water->SetActorLabel(TEXT("Catalog_RuntimeWater"));
    auto* Raft=World->SpawnActor<ARaftSimRaftActor>(ARaftSimRaftActor::StaticClass(),FTransform(Rotation,LaunchCm));
    if (!Raft) return false;
    auto* Rig=FindFProperty<FEnumProperty>(Raft->GetClass(),TEXT("RaftRig"));
    if (!Rig) return false;
    Rig->GetUnderlyingProperty()->SetIntPropertyValue(Rig->ContainerPtrToValuePtr<void>(Raft),
        static_cast<int64>(River.Rig));
    Raft->SetActorLabel(TEXT("Catalog_ProductionRaft"));
    if (World->GetWorldPartition())
    {
        auto* Source=NewObject<URaftSimRescueStreamingComponent>(Raft,TEXT("RescueTerrainStreaming"),RF_Transactional);
        Raft->AddInstanceComponent(Source); Source->RegisterComponent();
        // The state holders must not unload when their initial cell is left.
        for (AActor* Actor : TArray<AActor*>{Water,Raft})
            if (Actor->CanChangeIsSpatiallyLoadedFlag()) Actor->SetIsSpatiallyLoaded(false);
    }
    if (!World->SpawnActor<APlayerStart>(APlayerStart::StaticClass(),FTransform(Rotation,LaunchCm+FVector(0,0,180)))) return false;
    UClass* RunClass=LoadClass<AActor>(nullptr,TEXT("/Script/SmokeEmIfYouGotEm.RaftSimRunManager"));
    AActor* Run=RunClass ? World->SpawnActor<AActor>(RunClass,FTransform::Identity) : nullptr;
    if (!Run) return false;
    auto* Scenario=FindFProperty<FNameProperty>(RunClass,TEXT("ScenarioId"));
    auto* StartProp=FindFProperty<FFloatProperty>(RunClass,TEXT("StartStationM"));
    auto* FinishProp=FindFProperty<FFloatProperty>(RunClass,TEXT("FinishStationM"));
    if (!Scenario || !StartProp || !FinishProp) return false;
    Scenario->SetPropertyValue_InContainer(Run,FName(*J->GetStringField(TEXT("section_id"))));
    StartProp->SetPropertyValue_InContainer(Run,Start); FinishProp->SetPropertyValue_InContainer(Run,Finish);
    if (World->GetWorldPartition() && Run->CanChangeIsSpatiallyLoadedFlag()) Run->SetIsSpatiallyLoaded(false);
    return true;
}

static bool Build(const TSharedPtr<FJsonObject>& J, FString& Error)
{
    if (!J || J->GetStringField(TEXT("schema"))!=TEXT("raftsim.catalog_map_import.v1") ||
        J->GetStringField(TEXT("rig"))!=TEXT("ColoradoOarRig"))
    { Error=TEXT("Unsupported catalog map contract"); return false; }
    const FString Map=J->GetStringField(TEXT("map_package"));
    if (!Map.StartsWith(TEXT("/Game/RaftSim/Maps/Catalog/L_Colorado_")) || !FPackageName::IsValidLongPackageName(Map) ||
        FPackageName::DoesPackageExist(Map))
    { Error=TEXT("Fresh catalog map required; existing maps are never overwritten"); return false; }
    const auto Files=J->GetObjectField(TEXT("files_sha256"));
    if (Files->Values.IsEmpty()) { Error=TEXT("Missing source identities"); return false; }
    for (const auto& File:Files->Values)
    {
        FString Absolute,Expected; const FString Name(*File.Key);
        if (!RelativeFile(Name,Absolute) || !File.Value->TryGetString(Expected) || Expected.Len()!=64 ||
            !FRaftSimLiquidDataset::Hash(Absolute).Equals(Expected,ESearchCase::IgnoreCase))
        { Error=TEXT("Changed or unavailable source: ")+Name; return false; }
    }
    for (const TCHAR* Key:{TEXT("heightfield"),TEXT("coordinate_map"),TEXT("streaming")})
        if (!Files->HasField(J->GetStringField(Key))) { Error=TEXT("Unhashed map dependency"); return false; }
    const FString Fields=J->GetStringField(TEXT("cooked_fields"));
    if (!Files->HasField(Fields/TEXT("manifest.json"))) { Error=TEXT("Unhashed cooked field"); return false; }
    const auto L=J->GetObjectField(TEXT("landscape"));
    const auto Launch=J->GetObjectField(TEXT("launch"));
    const int32 Size=L->GetIntegerField(TEXT("size_px"));
    const float SpanX=L->GetNumberField(TEXT("horizontal_span_x_m"))*100.0;
    const float SpanY=L->GetNumberField(TEXT("horizontal_span_y_m"))*100.0;
    const float Relief=L->GetNumberField(TEXT("target_relief_cm"));
    const float Offset=L->GetNumberField(TEXT("world_vertical_offset_cm"));
    const float Start=Launch->GetNumberField(TEXT("station_m"));
    const float Finish=J->GetNumberField(TEXT("finish_station_m"));
    const auto& XYZ=Launch->GetArrayField(TEXT("location_cm"));
    if (Size!=2017 || !FMath::IsFinite(SpanX) || !FMath::IsFinite(SpanY) ||
        !FMath::IsFinite(Relief) || !FMath::IsFinite(Offset) || SpanX<=0 || SpanY<=0 || Relief<=0 ||
        !FMath::IsFinite(Start) || !FMath::IsFinite(Finish) || Start<0 || Finish<=Start || XYZ.Num()!=3 ||
        Launch->GetNumberField(TEXT("minimum_footprint_depth_m"))<1.0)
    { Error=TEXT("Invalid landscape or launch envelope"); return false; }
    const FVector LaunchCm(XYZ[0]->AsNumber(),XYZ[1]->AsNumber(),XYZ[2]->AsNumber());
    const FRotator Rotation(0,Launch->GetNumberField(TEXT("yaw_deg")),0);
    if (LaunchCm.ContainsNaN() || Rotation.ContainsNaN()) { Error=TEXT("Nonfinite launch"); return false; }
    FString HeightPath; if (!RelativeFile(J->GetStringField(TEXT("heightfield")),HeightPath)) return false;
    auto& Editor=FModuleManager::LoadModuleChecked<ILandscapeEditorModule>(TEXT("LandscapeEditor"));
    const auto* Format=Editor.GetHeightmapFormatByExtension(TEXT(".png"));
    if (!Format) return false;
    const FLandscapeFileResolution Resolution(Size,Size);
    const auto Info=Format->Validate(*HeightPath);
    if (Info.ResultCode==ELandscapeImportResult::Error || !Info.PossibleResolutions.Contains(Resolution)) return false;
    auto Heights=Format->Import(*HeightPath,Resolution);
    if (Heights.ResultCode==ELandscapeImportResult::Error || Heights.Data.Num()!=Size*Size) return false;
    uint16 Minimum=MAX_uint16;
    for (uint16 H:Heights.Data) Minimum=FMath::Min(Minimum,H);
    if (Minimum!=0) { Error=TEXT("Catalog exporter must encode its terrain minimum at zero"); return false; }
    UMaterial* Ground=TerrainMaterial(); if (!Ground) return false;
    UWorld* World=UEditorLoadingAndSavingUtils::NewBlankMap(false); if (!World) return false;
    UClass* Mode=LoadClass<AGameModeBase>(nullptr,TEXT("/Script/SmokeEmIfYouGotEm.RaftSimVerticalSliceGameMode"));
    if (!Mode) return false;
    World->GetWorldSettings()->DefaultGameMode=Mode;
    // +Y south, with north edge at -spanY/2; the coordinate map has exactly
    // the same centred northing origin. Decode UE height units using /65536.
    ALandscape* Land=World->SpawnActor<ALandscape>(FVector(0,-SpanY*.5f,Relief*.5f+Offset),FRotator::ZeroRotator);
    if (!Land) return false;
    Land->SetActorScale3D(FVector(SpanX/(Size-1),SpanY/(Size-1),Relief/512.0f));
    Land->LandscapeMaterial=Ground; Land->MaxLODLevel=0; Land->CollisionMipLevel=0;
    Land->SimpleCollisionMipLevel=0;
    if (auto* Nanite=FindFProperty<FBoolProperty>(ALandscapeProxy::StaticClass(),TEXT("bEnableNanite")))
        Nanite->SetPropertyValue_InContainer(Land,false);
    TMap<FGuid,TArray<uint16>> HeightLayers; HeightLayers.Add(FGuid(),MoveTemp(Heights.Data));
    TMap<FGuid,TArray<FLandscapeImportLayerInfo>> MaterialLayers;
    MaterialLayers.Add(FGuid(),TArray<FLandscapeImportLayerInfo>());
    Land->Import(FGuid::NewGuid(),0,0,Size-1,Size-1,2,63,HeightLayers,*HeightPath,
        MaterialLayers,ELandscapeImportAlphamapType::Additive,TArrayView<const FLandscapeLayer>());
    Land->SetActorLabel(TEXT("Catalog_RegisteredTerrain"));
    for (ULandscapeComponent* C:Land->LandscapeComponents) if (C) { C->OverrideMaterial=Ground; C->SetForcedLOD(0); }
    Land->UpdateAllComponentMaterialInstances(true); Land->RecreateComponentsState(); Land->PostEditChange();
    // Query actual Chaos complex heightfield data, not the editable PNG or
    // the bilinear reference used to export. A missing collision sample fails.
    const auto& Probes=J->GetArrayField(TEXT("wet_bed_collision_probes_cm"));
    if (Probes.IsEmpty()) { Error=TEXT("No wet-bed collision probes"); return false; }
    double MaxCollisionErrorCm=0;
    for (const auto& Value:Probes)
    {
        const auto& P=Value->AsArray();
        if (P.Num()!=3) return false;
        const FVector Location(P[0]->AsNumber(),P[1]->AsNumber(),P[2]->AsNumber());
        if (Location.ContainsNaN()) return false;
        const TOptional<float> Z=Land->GetHeightAtLocation(Location,EHeightfieldSource::Complex);
        if (!Z.IsSet()) { Error=TEXT("Missing complex collision heightfield at wet cell"); return false; }
        MaxCollisionErrorCm=FMath::Max(MaxCollisionErrorCm,FMath::Abs(double(Z.GetValue())-Location.Z));
    }
    UE_LOG(LogTemp,Display,TEXT("Catalog wet-bed complex collision probes=%d max_error_cm=%.6f"),Probes.Num(),MaxCollisionErrorCm);
    if (MaxCollisionErrorCm>10.) { Error=TEXT("Complex collision differs from cooked wet bed by over 10 cm"); return false; }
    for (const auto& Spec:GetEnvironmentPreviewSpecs())
        if (Spec.RiverId==TEXT("colorado_river")) { AddPreviewLightRig(World,Spec); break; }
    if (!AddRuntime(World,J,Error)) return false;
    FAssetCompilingManager::Get().FinishAllCompilation();
    return SavePreviewWorld(World,Map,Error);
}

static void Command(const TArray<FString>& Args)
{
    FString Error=TEXT("Usage: RaftSim.ImportCatalogMap <repo-relative-contract.json>");
    FString Path;
    const bool Ok=Args.Num()==1 && RelativeFile(Args[0],Path) && Build(FRaftSimLiquidDataset::Read(Path),Error);
    UE_LOG(LogTemp,Display,TEXT("Catalog map import saved=%d: %s"),Ok?1:0,*Error);
    // This command is a single-map unattended importer. ExecCmds' early Quit
    // can be ignored during editor startup; explicitly end the owned batch
    // only after compilation and synchronous package saving have completed.
    FPlatformMisc::RequestExitWithStatus(false,Ok ? 0 : 1);
}

static FAutoConsoleCommand ImportCommand(TEXT("RaftSim.ImportCatalogMap"),
    TEXT("Build a fresh source-registered catalog map from a hash-verified contract."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&Command));

// First-party river-specific decorative cover. These instances do not become solid
// obstacles; actual rock/bank collision continues to come from the terrain.
static bool AddContinuousDressingChunk(UWorld* World,const TSharedPtr<FJsonObject>& Chunk,
    ALandscape* Land,const TArray<TStrongObjectPtr<UStaticMesh>>& Meshes,const RaftSimContinuousRiver::FSpec& River,
    int32& Count,double& MaximumGroundError,TArray<FGuid>& BatchActors,FString& Error)
{
        if(!Chunk || !Land)return false;
        AActor* Actor=World->SpawnActor<AActor>(); if (!Actor) return false;
        Actor->SetActorLabel(FString::Printf(TEXT("%sArtDirectedVegetation_%d"),*River.MapStem,Count));
        Actor->Tags.Add(TEXT("RaftSimArtDirectedVegetation"));
        auto* Root=NewObject<USceneComponent>(Actor,TEXT("Root"),RF_Transactional);
        Actor->AddInstanceComponent(Root); Actor->SetRootComponent(Root); Root->RegisterComponent();
        const auto& Instances=Chunk->GetArrayField(TEXT("instances"));
        if (Instances.IsEmpty() || !Instances[0]->AsObject()) return false;
        const auto& First=Instances[0]->AsObject()->GetArrayField(TEXT("location_cm"));
        if (First.Num()!=3) return false;
        const FVector ChunkAnchor(First[0]->AsNumber(),First[1]->AsNumber(),First[2]->AsNumber());
        if (ChunkAnchor.ContainsNaN()) return false;
        // Instance buffers use floats: keep them chunk-local even when the
        // common river world frame extends hundreds of kilometres downstream.
        Actor->SetActorLocation(ChunkAnchor);
        TArray<UHierarchicalInstancedStaticMeshComponent*> Groups;
        for (int32 I=0;I<Meshes.Num();++I)
        {
            auto* C=NewObject<UHierarchicalInstancedStaticMeshComponent>(Actor,
                *FString::Printf(TEXT("Vegetation_%d"),I),RF_Transactional);
            Actor->AddInstanceComponent(C); C->SetupAttachment(Root);
            C->SetStaticMesh(Meshes[I].Get()); C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            C->SetCanEverAffectNavigation(false); C->SetCastShadow(true);
            C->SetCullDistances(45000,65000); C->bEnableDensityScaling=false;
            C->RegisterComponent(); Groups.Add(C);
        }
        for (const auto& Value:Instances)
        {
            const auto P=Value->AsObject(); if (!P) return false;
            const auto& XYZ=P->GetArrayField(TEXT("location_cm"));
            const int32 Mesh=P->GetIntegerField(TEXT("mesh"));
            const double Scale=P->GetNumberField(TEXT("scale")),Yaw=P->GetNumberField(TEXT("yaw_deg"));
            if (XYZ.Num()!=3 || !Groups.IsValidIndex(Mesh) || !FMath::IsFinite(Scale) ||
                Scale<.65 || Scale>1.2 || !FMath::IsFinite(Yaw)) return false;
            FVector Position(XYZ[0]->AsNumber(),XYZ[1]->AsNumber(),XYZ[2]->AsNumber());
            if (Position.ContainsNaN()) return false;
            const FVector O=Land->GetActorLocation();
            if(Position.X<O.X || Position.X>O.X+25200. || Position.Y<O.Y || Position.Y>O.Y+25200.)
            {Error=TEXT("Dressing instance outside its registered terrain chunk");return false;}
            const auto Height=Land->GetHeightAtLocation(Position,EHeightfieldSource::Complex);
            if (!Height.IsSet() || FMath::Abs(double(Height.GetValue())-Position.Z)>10.)
            { Error=TEXT("Dressing does not meet actual collision ground"); return false; }
            MaximumGroundError=FMath::Max(MaximumGroundError,FMath::Abs(double(Height.GetValue())-Position.Z));
            // Account for authored mesh pivot instead of burying/levitating roots.
            Position.Z=Height.GetValue()-Meshes[Mesh]->GetBoundingBox().Min.Z*Scale;
            Groups[Mesh]->AddInstance(FTransform(FRotator(0,Yaw,0),Position,FVector(Scale)),true);
            ++Count;
        }
        if(!Actor->CanChangeIsSpatiallyLoadedFlag())return false;
        Actor->SetIsSpatiallyLoaded(true);Actor->MarkPackageDirty();BatchActors.Add(Actor->GetActorGuid());
    return true;
}

static bool ReleaseSavedSpatialActors(UWorld* World,const TArray<FGuid>& Guids,FString& Error);

// Shared-grid Landscape construction used by continuous runs. Each actor uses
// the same world frame and height encoding; no per-reach recenter/stretch.
static bool ImportContinuousTerrain(const TSharedPtr<FJsonObject>& J, const FString& Folder,
    const FString& Map, FString& Error, const TSharedPtr<FJsonObject>& Runtime=nullptr)
{
    RaftSimContinuousRiver::FSpec River;
    if (!J || !RaftSimContinuousRiver::Resolve(J,River,Error) ||
        (J->GetStringField(TEXT("schema"))!=TEXT("raftsim.colorado_continuous_landscape.v1") &&
         J->GetStringField(TEXT("schema"))!=TEXT("raftsim.continuous_landscape.v1")) ||
        !Map.StartsWith(TEXT("/Game/RaftSim/Maps/Continuous/L_")+River.MapStem+TEXT("_")) ||
        !FPackageName::IsValidLongPackageName(Map) || FPackageName::DoesPackageExist(Map))
    { Error=TEXT("Fresh continuous terrain map and supported source contract required"); return false; }
    FVector2D GeographicOrigin;double Datum=0;
    if(!RaftSimContinuousRiver::Frame(J,River,GeographicOrigin,Datum,Error))return false;
    if(Runtime)
    {
        RaftSimContinuousRiver::FSpec RuntimeRiver;FString ChartPath;
        FVector2D ChartOrigin;double ChartDatum=0;
        if(!RaftSimContinuousRiver::Resolve(Runtime,RuntimeRiver,Error) || RuntimeRiver.RiverId!=River.RiverId ||
            !RelativeFile(Runtime->GetStringField(TEXT("coordinate_map")),ChartPath) ||
            !RaftSimContinuousRiver::Frame(FRaftSimLiquidDataset::Read(ChartPath),River,ChartOrigin,ChartDatum,Error) ||
            GeographicOrigin!=ChartOrigin || Datum!=ChartDatum)
        {Error=TEXT("Terrain and runtime do not share the river geographic frame");return false;}
    }
    bool bNaniteTerrain=false;
    if (Runtime && Runtime->HasField(TEXT("nanite_terrain")) &&
        !Runtime->TryGetBoolField(TEXT("nanite_terrain"),bNaniteTerrain))
    { Error=TEXT("Nanite terrain selection must be boolean"); return false; }
    // The native build can request completion of a still-compiling Nanite
    // static mesh. Keep both offline build stages synchronous; this does not
    // disable Nanite, change LOD0, or alter runtime rendering.
    IConsoleVariable* BuildThreads=IConsoleManager::Get().FindConsoleVariable(TEXT("landscape.Nanite.MultithreadBuild"));
    IConsoleVariable* MeshAsync=IConsoleManager::Get().FindConsoleVariable(TEXT("Editor.AsyncStaticMeshCompilation"));
    if(bNaniteTerrain && (!BuildThreads || !MeshAsync)){Error=TEXT("Native landscape build sequencing control unavailable");return false;}
    const int32 PreviousBuildThreads=BuildThreads ? BuildThreads->GetInt() : 0;
    const int32 PreviousMeshAsync=MeshAsync ? MeshAsync->GetInt() : 0;
    if(bNaniteTerrain){BuildThreads->Set(0,ECVF_SetByCode);MeshAsync->Set(0,ECVF_SetByCode);}
    ON_SCOPE_EXIT {if(bNaniteTerrain){BuildThreads->Set(PreviousBuildThreads,ECVF_SetByCode);MeshAsync->Set(PreviousMeshAsync,ECVF_SetByCode);}};
    const auto L=J->GetObjectField(TEXT("landscape"));
    const int32 Size=L->GetIntegerField(TEXT("vertices"));
    const auto& ScaleValues=L->GetArrayField(TEXT("scale_xyz"));
    const double Base=L->GetNumberField(River.bChilko ? TEXT("height_base_m") : TEXT("height_base_ellipsoid_m"));
    const double Range=L->GetNumberField(TEXT("height_range_m"));
    const double ActorZ=L->GetNumberField(TEXT("actor_z_cm"));
    if (Size!=127 || ScaleValues.Num()!=3 ||
        L->GetNumberField(TEXT("spacing_m"))!=2. || L->GetNumberField(TEXT("span_m"))!=252. ||
        Base!=200. || Range!=2400. || !FMath::IsFinite(Datum) || !FMath::IsFinite(ActorZ) ||
        !FMath::IsNearlyEqual(ActorZ,(Base+Range*32768./65535.-Datum)*100.,.0001))
    { Error=TEXT("Invalid shared terrain encoding"); return false; }
    const FVector Scale(ScaleValues[0]->AsNumber(),ScaleValues[1]->AsNumber(),ScaleValues[2]->AsNumber());
    if (Scale.ContainsNaN() || !Scale.Equals(FVector(200,200,Range*100./512.*65536./65535.),.0001))
    { Error=TEXT("Terrain scale disagrees with encoded height"); return false; }
    const auto& Chunks=J->GetArrayField(TEXT("chunks"));
    if (Chunks.IsEmpty() || Chunks.Num()>32768) { Error=TEXT("Invalid continuous terrain extent"); return false; }
    auto& Editor=FModuleManager::LoadModuleChecked<ILandscapeEditorModule>(TEXT("LandscapeEditor"));
    const auto* Format=Editor.GetHeightmapFormatByExtension(TEXT(".png"));
    if (!Format) return false;
    const FLandscapeFileResolution Resolution(Size,Size);
    struct FChunk
    {
        FString Path;FIntPoint Index;FVector Location;TArray<uint16> Heights;
        TArray<FVector> WetProbes;TSharedPtr<FJsonObject> Dressing;
        FString WetProbePath,WetProbeHash;int64 WetProbeCount=0;
    };
    TArray<FChunk> Inputs;
    TMap<FIntPoint,int32> Indices;
    // Validate every source and shared edge before creating or saving a world.
    for (const auto& Value:Chunks)
    {
        const auto C=Value->AsObject(); if (!C) return false;
        const auto& Index=C->GetArrayField(TEXT("chunk"));
        const auto& XY=C->GetArrayField(TEXT("world_northwest_xy_cm"));
        if (Index.Num()!=2 || XY.Num()!=2) return false;
        FChunk Input; Input.Index=FIntPoint(Index[0]->AsNumber(),Index[1]->AsNumber());
        if (Indices.Contains(Input.Index) || Input.Index.X!=Index[0]->AsNumber() || Input.Index.Y!=Index[1]->AsNumber()) return false;
        Input.Location=FVector(XY[0]->AsNumber(),XY[1]->AsNumber(),ActorZ);
        if (Input.Location.ContainsNaN() ||
            !FMath::IsNearlyEqual(Input.Location.X,Input.Index.X*25200.,.0001) ||
            !FMath::IsNearlyEqual(Input.Location.Y,-(Input.Index.Y+1)*25200.,.0001))
        { Error=TEXT("Chunk shifted off shared lattice"); return false; }
        const FString Name=C->GetStringField(TEXT("heightfield"));
        if (FPaths::GetCleanFilename(Name)!=Name || Name.Contains(TEXT(".."))) return false;
        Input.Path=Folder/Name;
        if (!FRaftSimLiquidDataset::Hash(Input.Path).Equals(C->GetStringField(TEXT("sha256")),ESearchCase::IgnoreCase))
        { Error=TEXT("Changed terrain chunk: ")+Name; return false; }
        const auto Info=Format->Validate(*Input.Path);
        if (Info.ResultCode==ELandscapeImportResult::Error || !Info.PossibleResolutions.Contains(Resolution)) return false;
        auto Heights=Format->Import(*Input.Path,Resolution);
        if (Heights.ResultCode==ELandscapeImportResult::Error || Heights.Data.Num()!=Size*Size) return false;
        Input.Heights=MoveTemp(Heights.Data);
        Indices.Add(Input.Index,Inputs.Num()); Inputs.Add(MoveTemp(Input));
    }
    for (const FChunk& C:Inputs)
    {
        const int32* Left=Indices.Find(C.Index-FIntPoint(1,0));
        const int32* Below=Indices.Find(C.Index-FIntPoint(0,1));
        for (int32 I=0;I<Size;++I)
            if ((Left && C.Heights[I*Size]!=Inputs[*Left].Heights[I*Size+Size-1]) ||
                (Below && C.Heights[(Size-1)*Size+I]!=Inputs[*Below].Heights[I]))
            { Error=TEXT("Shared terrain edge mismatch"); return false; }
    }
    // Partition validation work by its actual geographic owner before loading
    // terrain. No all-river actor scan or all-river resident collision set.
    auto FindOwner=[&](const FVector& P)->int32
    {
        if(P.ContainsNaN() || FMath::Abs(P.X)>1.e9 || FMath::Abs(P.Y)>1.e9)return INDEX_NONE;
        const FIntPoint Cell(FMath::FloorToInt(P.X/25200.),FMath::FloorToInt(-P.Y/25200.));
        for(int32 DX:{0,-1})for(int32 DY:{0,-1})
            if(const int32* I=Indices.Find(Cell+FIntPoint(DX,DY)))
            {
                const FVector& O=Inputs[*I].Location;
                if(P.X>=O.X && P.X<=O.X+25200. && P.Y>=O.Y && P.Y<=O.Y+25200.)return *I;
            }
        return INDEX_NONE;
    };
    int32 ExpectedWetProbes=0,ExpectedInstances=0;
    TArray<TStrongObjectPtr<UStaticMesh>> DressingMeshes;
    if(Runtime)
    {
        if(Runtime->HasField(TEXT("wet_bed_collision_probe_chunks")))
        {
            if(Runtime->HasField(TEXT("wet_bed_collision_probes_cm")))
            {Error=TEXT("Ambiguous wet-bed probe encodings");return false;}
            const auto P=Runtime->GetObjectField(TEXT("wet_bed_collision_probe_chunks"));
            double Total=0;
            if(!P || P->GetStringField(TEXT("schema"))!=TEXT("raftsim.chunked_wet_bed_probes.v1") ||
                P->GetStringField(TEXT("encoding"))!=TEXT("xyz_cm_float64_le") ||
                !P->TryGetNumberField(TEXT("count"),Total) || !FMath::IsFinite(Total) ||
                Total<1 || Total>MAX_int32 || Total!=double(int64(Total)))
            {Error=TEXT("Invalid chunk-owned wet-bed probe contract");return false;}
            int64 Declared=0;TSet<FString> Paths;
            const auto Files=Runtime->GetObjectField(TEXT("files_sha256"));
            for(const auto& Value:P->GetArrayField(TEXT("chunks")))
            {
                const auto C=Value->AsObject();if(!C)return false;
                const auto& XY=C->GetArrayField(TEXT("chunk"));if(XY.Num()!=2)return false;
                const double X=XY[0]->AsNumber(),Y=XY[1]->AsNumber();
                if(!FMath::IsFinite(X) || !FMath::IsFinite(Y) || FMath::Abs(X)>100000 || FMath::Abs(Y)>100000)return false;
                const FIntPoint Index(X,Y);const int32* Owner=Indices.Find(Index);
                double Count=0;FString Relative,Digest,Path,Bound;
                if(!Owner || Index.X!=X || Index.Y!=Y || !Inputs[*Owner].WetProbePath.IsEmpty() ||
                    !C->TryGetNumberField(TEXT("count"),Count) || !FMath::IsFinite(Count) ||
                    Count<1 || Count>MAX_int32 || Count!=double(int64(Count)) ||
                    !C->TryGetStringField(TEXT("file"),Relative) || !RelativeFile(Relative,Path) ||
                    Paths.Contains(Path) || !C->TryGetStringField(TEXT("sha256"),Digest) ||
                    !Files->TryGetStringField(Relative,Bound) || Bound!=Digest)
                {Error=TEXT("Unknown, duplicate or unbound wet-bed probe chunk");return false;}
                Paths.Add(Path);Declared+=int64(Count);
                auto& Input=Inputs[*Owner];Input.WetProbePath=Path;Input.WetProbeHash=Digest;Input.WetProbeCount=int64(Count);
                // Validate every point before creating a world, then reread only
                // this chunk during collision checking. Never retain all points.
                if(!RaftSimContinuousCollisionProbes::VisitFile(Path,int64(Count),Digest,[&](const FVector& Position)
                    {if(FindOwner(Position)==*Owner)return true;Error=TEXT("Wet-bed probe belongs to another terrain chunk");return false;},Error))return false;
            }
            if(Declared!=int64(Total)){Error=TEXT("Incomplete chunk-owned wet-bed probes");return false;}
            ExpectedWetProbes=int32(Declared);
        }
        else
        {
        const auto& Probes=Runtime->GetArrayField(TEXT("wet_bed_collision_probes_cm"));
        if(Probes.IsEmpty()){Error=TEXT("Missing native wet-bed collision probes");return false;}
        ExpectedWetProbes=Probes.Num();
        for(const auto& Value:Probes)
        {
            const auto& P=Value->AsArray();if(P.Num()!=3)return false;
            const FVector Position(P[0]->AsNumber(),P[1]->AsNumber(),P[2]->AsNumber());
            const int32 Owner=FindOwner(Position);
            if(Owner==INDEX_NONE){Error=TEXT("Cooked wet cell has no source terrain chunk");return false;}
            Inputs[Owner].WetProbes.Add(Position);
        }
        }
        FString Relative;
        if(Runtime->TryGetStringField(TEXT("environment"),Relative))
        {
            FString Path;if(!RelativeFile(Relative,Path))return false;
            const auto D=FRaftSimLiquidDataset::Read(Path);
            if(!RaftSimContinuousRiver::Dressing(D,River,Error))return false;
            const auto& Names=D->GetArrayField(TEXT("meshes"));if(Names.Num()!=4)return false;
            for(const auto& Name:Names)
            {
                const FString Asset=Name->AsString();
                auto* Mesh=LoadObject<UStaticMesh>(nullptr,*Asset);
                if(!Mesh || Mesh->GetBounds().SphereRadius*1.2>1000.)
                {Error=TEXT("Missing or oversized river vegetation mesh");return false;}
                DressingMeshes.Emplace(Mesh);
            }
            ExpectedInstances=D->GetIntegerField(TEXT("instance_count"));
            if(ExpectedInstances<0 || ExpectedInstances>1000000)return false;
            int32 DeclaredInstances=0;
            for(const auto& Value:D->GetArrayField(TEXT("chunks")))
            {
                const auto C=Value->AsObject();if(!C)return false;
                const auto& XY=C->GetArrayField(TEXT("chunk"));if(XY.Num()!=2)return false;
                const FIntPoint Index(XY[0]->AsNumber(),XY[1]->AsNumber());
                const int32* Owner=Indices.Find(Index);
                if(!Owner || Inputs[*Owner].Dressing || Index.X!=XY[0]->AsNumber() || Index.Y!=XY[1]->AsNumber())
                {Error=TEXT("Unknown or duplicate dressing terrain chunk");return false;}
                DeclaredInstances+=C->GetArrayField(TEXT("instances")).Num();Inputs[*Owner].Dressing=C;
            }
            if(DeclaredInstances!=ExpectedInstances)return false;
        }
    }
    TStrongObjectPtr<UMaterial> Ground(TerrainMaterial(&River)); if (!Ground) return false;
    // UE 5.8 proxy splitting clears the final height texture and recomposes
    // edit layers on the GPU. NullRHI can retain valid old Chaos data while
    // saving a flat render surface, so collision probes alone are insufficient.
    if (FParse::Param(FCommandLine::Get(),TEXT("NullRHI")))
    { Error=TEXT("Continuous streaming terrain import requires a rendering RHI for landscape layer composition"); return false; }
    UWorld* World=GEditor ? GEditor->NewMap(true) : nullptr;
    if (!World || !World->GetWorldPartition())
    { Error=TEXT("Continuous terrain requires World Partition"); return false; }
    // Establish the final package before creating external terrain actors.
    World->GetWorldPartition()->SetDefaultHLODLayer(nullptr);
    if (!SavePreviewWorld(World,Map,Error)) return false;
    auto* TerrainSubsystem=World->GetSubsystem<ULandscapeSubsystem>();
    if (!TerrainSubsystem || !TerrainSubsystem->IsGridBased()) return false;
    double MaximumErrorCm=0.,WetMaximum=0.,MaximumGroundError=0.;
    int32 ProbeCount=0,StreamingProxyCount=0,WetProbeCount=0,InstanceCount=0,CompletedChunks=0,Batches=0;
    TArray<FGuid> BatchActors;TArray<ALandscapeProxy*> BatchTerrain;
    constexpr int32 BatchChunks=32;
    auto FlushBatch=[&]()->bool
    {
        FAssetCompilingManager::Get().FinishAllCompilation();
        if(bNaniteTerrain)
        {
            auto* Enabled=FindFProperty<FBoolProperty>(ALandscapeProxy::StaticClass(),TEXT("bEnableNanite"));
            auto* LOD=FindFProperty<FIntProperty>(ALandscapeProxy::StaticClass(),TEXT("NaniteLODIndex"));
            auto* Precision=FindFProperty<FIntProperty>(ALandscapeProxy::StaticClass(),TEXT("NanitePositionPrecision"));
            if(!Enabled || !LOD || !Precision){Error=TEXT("Native Nanite settings unavailable");return false;}
            for(auto* Proxy:BatchTerrain)
            {
                Enabled->SetPropertyValue_InContainer(Proxy,true);LOD->SetPropertyValue_InContainer(Proxy,0);
                Precision->SetPropertyValue_InContainer(Proxy,4);Proxy->MarkPackageDirty();
            }
            TerrainSubsystem->BuildNanite(UE::Landscape::EBuildFlags::WriteFinalLog,BatchTerrain);
            FAssetCompilingManager::Get().FinishAllCompilation();
            for(auto* Proxy:BatchTerrain)
                if(!Proxy->IsNaniteEnabled() || !Proxy->HasNaniteComponents() || !Proxy->IsNaniteMeshUpToDate())
                {Error=TEXT("Missing or stale built Nanite terrain representation");return false;}
        }
        if(!SavePreviewWorld(World,Map,Error))return false;
        // Newly constructed actors retain editor creation references that the
        // normal pin/unpin lifecycle cannot release. Reopen only this saved,
        // fresh construction world, then verify all accumulated spatial actors
        // are unloaded. No package or descriptor is removed.
        GEditor->ResetTransaction(FText::FromString(TEXT("Saved continuous terrain batch")));
        BatchTerrain.Reset();
        TArray<FGuid> SavedSpatial;
        for(FActorDescContainerInstanceCollection::TIterator<> It(World->GetWorldPartition());It;++It)
            if(It->GetIsSpatiallyLoaded())SavedSpatial.Add(It->GetGuid());
        for(const FGuid& Guid:BatchActors)
            if(!SavedSpatial.Contains(Guid)){Error=TEXT("Saved batch lost a spatial descriptor");return false;}
        const FString Filename=FPackageName::LongPackageNameToFilename(Map,FPackageName::GetMapPackageExtension());
        if(!FEditorFileUtils::LoadMap(Filename,false,false))
        {Error=TEXT("Unable to reopen saved continuous terrain batch");return false;}
        World=GEditor->GetEditorWorldContext().World();
        auto* Partition=World ? World->GetWorldPartition() : nullptr;
        auto* Container=Partition ? Partition->GetActorDescContainerInstance() : nullptr;
        TerrainSubsystem=World ? World->GetSubsystem<ULandscapeSubsystem>() : nullptr;
        if(!Container || !TerrainSubsystem || World->GetPackage()->GetName()!=Map)
        {Error=TEXT("Saved batch reopened in wrong world or without partition");return false;}
        CollectGarbage(GARBAGE_COLLECTION_KEEPFLAGS);
        for(const FGuid& Guid:SavedSpatial)
        {
            auto* Desc=Container->GetActorDescInstance(Guid);
            if(!Desc || Desc->IsLoaded())
            {Error=TEXT("Reopened batch lost or retained a spatial actor: ")+Guid.ToString();return false;}
        }
        ++Batches;
        UE_LOG(LogTemp,Display,TEXT("Continuous terrain batch=%d completed_chunks=%d released_actors=%d resident_batch_limit=%d"),Batches,CompletedChunks,BatchActors.Num(),BatchChunks);
        BatchActors.Reset();return true;
    };
    for (const FChunk& C:Inputs)
    {
        ALandscape* Land=World->SpawnActor<ALandscape>(C.Location,FRotator::ZeroRotator);
        if (!Land) return false;
        Land->SetActorScale3D(Scale); Land->LandscapeMaterial=Ground.Get();
        Land->MaxLODLevel=0; Land->CollisionMipLevel=0; Land->SimpleCollisionMipLevel=0;
        if (auto* Nanite=FindFProperty<FBoolProperty>(ALandscapeProxy::StaticClass(),TEXT("bEnableNanite")))
            Nanite->SetPropertyValue_InContainer(Land,false);
        TMap<FGuid,TArray<uint16>> HeightLayers; HeightLayers.Add(FGuid(),C.Heights);
        TMap<FGuid,TArray<FLandscapeImportLayerInfo>> Layers; Layers.Add(FGuid(),{});
        Land->Import(FGuid::NewGuid(),0,0,Size-1,Size-1,2,63,HeightLayers,*C.Path,
            Layers,ELandscapeImportAlphamapType::Additive,TArrayView<const FLandscapeLayer>());
        Land->SetActorLabel(FString::Printf(TEXT("ContinuousTerrain_%d_%d"),C.Index.X,C.Index.Y));
        for (ULandscapeComponent* Component:Land->LandscapeComponents)
            if (Component) { Component->OverrideMaterial=Ground.Get(); Component->SetForcedLOD(0); }
        Land->UpdateAllComponentMaterialInstances(true); Land->RecreateComponentsState(); Land->PostEditChange();
        // ALandscape itself is always loaded. Move its component to a spatial
        // proxy so full-river collision/render data can actually stream out.
        TerrainSubsystem->ChangeGridSize(Land->GetLandscapeInfo(),1);
        if (!Land->LandscapeComponents.IsEmpty() || !Land->CollisionComponents.IsEmpty())
        { Error=TEXT("Continuous terrain remained in an always-loaded root"); return false; }
        const auto& Proxies=Land->GetLandscapeInfo()->GetSortedStreamingProxies();
        if (Proxies.IsEmpty()) { Error=TEXT("Missing continuous terrain streaming proxy"); return false; }
        for (const auto& Weak:Proxies)
        {
            auto* Proxy=Weak.Get();
            if (!Proxy || !Proxy->CanChangeIsSpatiallyLoadedFlag()) return false;
            Proxy->SetIsSpatiallyLoaded(true); Proxy->MarkPackageDirty(); ++StreamingProxyCount;
            BatchActors.Add(Proxy->GetActorGuid());BatchTerrain.Add(Proxy);
        }
        Land->ForceLayersFullUpdate();
        FAssetCompilingManager::Get().FinishAllCompilation();
        int32 RenderVertices=0;
        for (const auto& Weak:Proxies)
            for (ULandscapeComponent* Component:Weak->LandscapeComponents)
            {
                FLandscapeComponentDataInterface RenderData(Component,0,false);
                if (!RenderData.GetRawHeightData())
                { Error=TEXT("Missing composed terrain render height data"); return false; }
                const FIntPoint Offset=Component->GetSectionBase();
                for (int32 Y=0;Y<=Component->ComponentSizeQuads;++Y)
                    for (int32 X=0;X<=Component->ComponentSizeQuads;++X)
                    {
                        const int32 Col=Offset.X+X,Row=Offset.Y+Y;
                        if (Col<0 || Row<0 || Col>=Size || Row>=Size ||
                            FMath::Abs(int32(RenderData.GetHeight(X,Y))-int32(C.Heights[Row*Size+Col]))>1)
                        { Error=TEXT("Composed streaming terrain render height differs from source"); return false; }
                        ++RenderVertices;
                    }
            }
        if (RenderVertices!=Size*Size)
        { Error=TEXT("Incomplete streaming terrain render vertex coverage"); return false; }
        // Off-vertex probes exercise the real triangle diagonal and both sides
        // of every chunk, not merely the PNG's vertex values.
        for (int32 Row:{0,31,62,94,125}) for (int32 Col:{0,31,62,94,125})
            for (const FVector2D Fraction:{FVector2D(.25,.75),FVector2D(.75,.25)})
            {
                const double X=Fraction.X,Y=Fraction.Y;
                const double A=C.Heights[Row*Size+Col],B=C.Heights[Row*Size+Col+1];
                const double D=C.Heights[(Row+1)*Size+Col],E=C.Heights[(Row+1)*Size+Col+1];
                const double Encoded=X<Y ? (1-Y)*A+X*E+(Y-X)*D : (1-X)*A+(X-Y)*B+Y*E;
                const double Expected=(Base+Encoded*Range/65535.-Datum)*100.;
                const FVector Position=C.Location+FVector((Col+X)*200.,(Row+Y)*200.,0);
                const TOptional<float> Actual=Land->GetHeightAtLocation(Position,EHeightfieldSource::Complex);
                if (!Actual.IsSet()) { Error=TEXT("Missing continuous complex collision"); return false; }
                MaximumErrorCm=FMath::Max(MaximumErrorCm,FMath::Abs(double(Actual.GetValue())-Expected)); ++ProbeCount;
            }
        if(MaximumErrorCm>10.){Error=TEXT("Continuous collision exceeds 10 cm geometry tolerance");return false;}
        auto CheckWetProbe=[&](const FVector& Position)->bool
        {
            const auto Height=Land->GetHeightAtLocation(Position,EHeightfieldSource::Complex);
            if(!Height.IsSet()){Error=TEXT("Cooked wet cell has no native collision terrain");return false;}
            WetMaximum=FMath::Max(WetMaximum,FMath::Abs(double(Height.GetValue())-Position.Z));++WetProbeCount;
            return true;
        };
        for(const FVector& Position:C.WetProbes)if(!CheckWetProbe(Position))return false;
        if(!C.WetProbePath.IsEmpty() && !RaftSimContinuousCollisionProbes::VisitFile(
            C.WetProbePath,C.WetProbeCount,C.WetProbeHash,CheckWetProbe,Error))return false;
        if(WetMaximum>10.){Error=TEXT("Continuous wet bed differs from native collision");return false;}
        if(C.Dressing && !AddContinuousDressingChunk(World,C.Dressing,Land,DressingMeshes,River,
            InstanceCount,MaximumGroundError,BatchActors,Error))return false;
        if(bNaniteTerrain)
        {
            // Keep the saved parent settings consistent with its spatial
            // proxy; reloading must not inherit a disabled Nanite parent.
            auto* Enabled=FindFProperty<FBoolProperty>(ALandscapeProxy::StaticClass(),TEXT("bEnableNanite"));
            auto* LOD=FindFProperty<FIntProperty>(ALandscapeProxy::StaticClass(),TEXT("NaniteLODIndex"));
            auto* Precision=FindFProperty<FIntProperty>(ALandscapeProxy::StaticClass(),TEXT("NanitePositionPrecision"));
            if(!Enabled || !LOD || !Precision)return false;
            Enabled->SetPropertyValue_InContainer(Land,true);LOD->SetPropertyValue_InContainer(Land,0);
            Precision->SetPropertyValue_InContainer(Land,4);Land->MarkPackageDirty();
        }
        ++CompletedChunks;
        if((CompletedChunks%BatchChunks==0 || CompletedChunks==Inputs.Num()) && !FlushBatch())return false;
    }
    UE_LOG(LogTemp,Display,TEXT("Continuous terrain chunks=%d collision_probes=%d max_error_cm=%.6f streaming_proxies=%d"),Inputs.Num(),ProbeCount,MaximumErrorCm,StreamingProxyCount);
    if(WetProbeCount!=ExpectedWetProbes || InstanceCount!=ExpectedInstances)
    {Error=TEXT("Incomplete batched wet-bed or dressing verification");return false;}
    UE_LOG(LogTemp,Display,TEXT("Continuous wet-bed probes=%d max_error_cm=%.6f"),WetProbeCount,WetMaximum);
    UE_LOG(LogTemp,Display,TEXT("Continuous dryland instances=%d ground_error_cm=%.6f artistic=1 nonblocking=1"),InstanceCount,MaximumGroundError);
    if(bNaniteTerrain)
        UE_LOG(LogTemp,Display,TEXT("Continuous Nanite terrain verified proxies=%d source_lod=0 relative_position_precision=4 collision_unchanged=1 batches=%d"),StreamingProxyCount,Batches);
    if(Runtime && !AddRuntime(World,Runtime,Error))return false;
    for (const auto& Spec:GetEnvironmentPreviewSpecs())
        if (Spec.RiverId==River.PreviewId) { AddPreviewLightRig(World,Spec); break; }
    for (TActorIterator<AActor> It(World);It;++It)
    {
        // Only terrain proxies and chunk-local vegetation are spatial; lights,
        // player starts and runtime managers retain their existing identities.
        const bool Spatial=It->IsA<ALandscapeStreamingProxy>() || It->Tags.Contains(TEXT("RaftSimArtDirectedVegetation"));
        if (It->CanChangeIsSpatiallyLoadedFlag()) It->SetIsSpatiallyLoaded(Spatial);
    }
    FAssetCompilingManager::Get().FinishAllCompilation();
    return SavePreviewWorld(World,Map,Error);
}

static void ContinuousTerrainCommand(const TArray<FString>& Args)
{
    FString Error=TEXT("Usage: RaftSim.ImportContinuousTerrain <repo-relative-manifest.json> <fresh-map-package>");
    FString Path;
    const bool Ok=Args.Num()==2 && RelativeFile(Args[0],Path) &&
        ImportContinuousTerrain(FRaftSimLiquidDataset::Read(Path),FPaths::GetPath(Path),Args[1],Error);
    UE_LOG(LogTemp,Display,TEXT("Continuous terrain import saved=%d: %s"),Ok?1:0,*Error);
    FPlatformMisc::RequestExitWithStatus(false,Ok?0:1);
}
static FAutoConsoleCommand ContinuousCommand(TEXT("RaftSim.ImportContinuousTerrain"),
    TEXT("Import common-grid continuous terrain and verify native collision; does not claim a playable water run."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&ContinuousTerrainCommand));

static void ContinuousMapCommand(const TArray<FString>& Args)
{
    FString Error=TEXT("Usage: RaftSim.ImportContinuousMap <repo-relative-contract.json>");
    FString Path; bool Ok=false;
    if (Args.Num()==1 && RelativeFile(Args[0],Path))
    {
        const auto J=FRaftSimLiquidDataset::Read(Path);
        if (J && (J->GetStringField(TEXT("schema"))==TEXT("raftsim.colorado_continuous_map_import.v1") ||
                  J->GetStringField(TEXT("schema"))==TEXT("raftsim.continuous_map_import.v1")))
        {
            const auto Files=J->GetObjectField(TEXT("files_sha256"));
            bool Valid=!Files->Values.IsEmpty();
            for (const auto& File:Files->Values)
            {
                FString Absolute,Hash; const FString Name(*File.Key);
                if (!RelativeFile(Name,Absolute) || !File.Value->TryGetString(Hash) || Hash.Len()!=64 ||
                    !RaftSimContinuousCollisionProbes::Hash(Absolute).Equals(Hash,ESearchCase::IgnoreCase))
                { Valid=false; Error=TEXT("Changed continuous runtime dependency: ")+Name; break; }
            }
            for (const TCHAR* Key:{TEXT("terrain_manifest"),TEXT("coordinate_map"),TEXT("streaming")})
                Valid=Valid && Files->HasField(J->GetStringField(Key));
            Valid=Valid && Files->HasField(J->GetStringField(TEXT("cooked_fields"))/TEXT("manifest.json"));
            FString TerrainPath;
            if (Valid && RelativeFile(J->GetStringField(TEXT("terrain_manifest")),TerrainPath))
                Ok=ImportContinuousTerrain(FRaftSimLiquidDataset::Read(TerrainPath),FPaths::GetPath(TerrainPath),
                    J->GetStringField(TEXT("map_package")),Error,J);
        }
    }
    UE_LOG(LogTemp,Display,TEXT("Continuous map import saved=%d: %s"),Ok?1:0,*Error);
    FPlatformMisc::RequestExitWithStatus(false,Ok?0:1);
}
static FAutoConsoleCommand ContinuousMap(TEXT("RaftSim.ImportContinuousMap"),
    TEXT("Import screened common-grid terrain/water with production raft and native collision verification."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&ContinuousMapCommand));

// Only clean, already-saved spatial actors may be released. This never deletes
// an actor or package; its descriptor must survive and be loadable afterwards.
static bool ReleaseSavedSpatialActors(UWorld* World,const TArray<FGuid>& Guids,FString& Error)
{
    UWorldPartition* Partition=World ? World->GetWorldPartition() : nullptr;
    auto* Container=Partition ? Partition->GetActorDescContainerInstance() : nullptr;
    if(!Container || Guids.IsEmpty()) {Error=TEXT("No saved spatial batch");return false;}
    for(const FGuid& Guid:Guids)
    {
        auto* Desc=Container->GetActorDescInstance(Guid);
        AActor* Actor=Desc ? Desc->GetActor() : nullptr;
        UPackage* Package=Actor ? Actor->GetExternalPackage() : nullptr;
        if(!Desc || !Desc->GetIsSpatiallyLoaded() || !Actor || !Package || Package->IsDirty() ||
            !FPackageName::DoesPackageExist(Package->GetName()))
        {Error=TEXT("Refusing to release missing, unsaved or nonspatial terrain actor");return false;}
    }
    // Newly created actors can exist before a loader owns a reference to them.
    // Establish a normal loading reference, refresh their saved spatial flags,
    // then release through the same native path exercised on reopened maps.
    Partition->PinActors(Guids);
    IWorldPartitionActorLoaderInterface::RefreshLoadedState(false);
    Partition->UnpinActors(Guids);
    if(Partition->ForceLoadedActors)Partition->ForceLoadedActors->RemoveActors(Guids);
    CollectGarbage(GARBAGE_COLLECTION_KEEPFLAGS);
    for(const FGuid& Guid:Guids)
    {
        auto* Desc=Container->GetActorDescInstance(Guid);
        if(!Desc || Desc->IsLoaded())
        {Error=TEXT("Saved spatial batch still resident or descriptor lost: ")+Guid.ToString();return false;}
    }
    Error.Reset();return true;
}

static void VerifyContinuousTerrainUnload(const TArray<FString>& Args)
{
    UWorld* World=GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
    FString Error=TEXT("Run in an isolated editor on a saved continuous construction map");
    bool Ok=false;
    if(World && World->GetWorldPartition() && Args.IsEmpty() && World->GetPackage()->GetName().StartsWith(TEXT("/Game/RaftSim/Maps/Continuous/L_Colorado_")))
    {
        auto* Partition=World->GetWorldPartition();
        TArray<FGuid> SavedGuids;
        for(FActorDescContainerInstanceCollection::TIterator<ALandscapeStreamingProxy> It(Partition);It;++It)
            SavedGuids.Add(It->GetGuid());
        // Opening a World Partition map deliberately leaves spatial terrain
        // unloaded. Explicitly load this bounded fixture before testing release.
        if(SavedGuids.IsEmpty() || SavedGuids.Num()>256)
        {
            UE_LOG(LogTemp,Error,TEXT("Terrain residency fixture requires 1-256 saved proxies; got %d"),SavedGuids.Num());
            FPlatformMisc::RequestExitWithStatus(false,1);return;
        }
        Partition->PinActors(SavedGuids);
        struct FProbe {FGuid Guid;FVector Position;float Height;};
        TArray<FProbe> Probes;TArray<FGuid> Guids;
        for(TActorIterator<ALandscapeStreamingProxy> It(World);It;++It)
        {
            if(It->LandscapeComponents.Num()!=1)break;
            const FVector P=It->GetActorLocation()+FVector(12600.,12600.,0.);
            const auto Height=It->GetHeightAtLocation(P,EHeightfieldSource::Complex);
            if(!Height.IsSet())break;
            Probes.Add({It->GetActorGuid(),P,Height.GetValue()});Guids.Add(It->GetActorGuid());
        }
        int32 Total=0;for(TActorIterator<ALandscapeStreamingProxy> It(World);It;++It)++Total;
        Error=FString::Printf(TEXT("Incomplete terrain fixture: descriptors=%d loaded=%d probes=%d"),SavedGuids.Num(),Total,Probes.Num());
        if(Total==SavedGuids.Num() && Probes.Num()==Total && ReleaseSavedSpatialActors(World,Guids,Error))
        {
            Ok=true;double MaximumError=0.;
            auto* Container=World->GetWorldPartition()->GetActorDescContainerInstance();
            for(const FProbe& P:Probes)
            {
                {
                    FWorldPartitionReference Reference(Container,P.Guid);
                    auto* Desc=Container->GetActorDescInstance(P.Guid);
                    auto* Proxy=Desc ? Cast<ALandscapeStreamingProxy>(Desc->GetActor()) : nullptr;
                    const auto H=Proxy ? Proxy->GetHeightAtLocation(P.Position,EHeightfieldSource::Complex) : TOptional<float>();
                    if(!H.IsSet() || FMath::Abs(H.GetValue()-P.Height)>.01f)
                    {Ok=false;Error=TEXT("Reload changed or lost native terrain collision");break;}
                    MaximumError=FMath::Max(MaximumError,double(FMath::Abs(H.GetValue()-P.Height)));
                }
                CollectGarbage(GARBAGE_COLLECTION_KEEPFLAGS);
                if(Container->GetActorDescInstance(P.Guid)->IsLoaded())
                {Ok=false;Error=TEXT("Scoped native reload did not release terrain");break;}
            }
            UE_LOG(LogTemp,Display,TEXT("Continuous saved-terrain unload/reload verified=%d proxies=%d max_collision_change_cm=%.6f"),Ok?1:0,Total,MaximumError);
        }
    }
    if(Ok)Error.Reset();
    UE_LOG(LogTemp,Display,TEXT("Continuous terrain residency verification saved_no_packages=1 success=%d: %s"),Ok?1:0,*Error);
    FPlatformMisc::RequestExitWithStatus(false,Ok?0:1);
}
static FAutoConsoleCommand ContinuousTerrainUnload(TEXT("RaftSim.VerifyContinuousTerrainUnload"),
    TEXT("Verify clean saved spatial terrain can unload and reload without changing collision; no map writes."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&VerifyContinuousTerrainUnload));
}
