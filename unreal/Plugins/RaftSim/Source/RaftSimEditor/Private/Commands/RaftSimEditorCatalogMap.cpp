// Source-registered catalog reaches. No cloned map, Hance drape/backdrop,
// analytic channel burn, invented collision proxy or provisional flow field.
#include "Environment/RaftSimEditorEnvironmentInternal.h"
#include "Materials/RaftSimLiquidDataset.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/WorldSettings.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRiverWaterConfig.h"

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
static UMaterial* TerrainMaterial()
{
    const FString PackageName = TEXT("/Game/RaftSim/Materials/Catalog/M_ColoradoCatalogGroundV1");
    const FString ObjectName = TEXT("M_ColoradoCatalogGroundV1");
    if (UMaterial* Existing = LoadObject<UMaterial>(nullptr, *(PackageName+TEXT(".")+ObjectName))) return Existing;
    UTexture2D* Albedo = LoadObject<UTexture2D>(nullptr,
        TEXT("/Game/RaftSim/Rendering/ProductionDetailTextures/Textures/T_RaftSim_ColoradoRiver_TerrainDetailAlbedo.T_RaftSim_ColoradoRiver_TerrainDetailAlbedo"));
    if (!Albedo) return nullptr;
    UPackage* Package = CreatePackage(*PackageName);
    UMaterial* M = NewObject<UMaterial>(Package,*ObjectName,RF_Public|RF_Standalone);
    M->SetShadingModel(MSM_DefaultLit);
    auto* Position = NewObject<UMaterialExpressionWorldPosition>(M);
    auto* Coordinates = NewObject<UMaterialExpressionComponentMask>(M);
    Coordinates->Input.Expression=Position; Coordinates->R=true; Coordinates->G=true;
    auto* Scale = NewObject<UMaterialExpressionMultiply>(M);
    Scale->A.Expression=Coordinates; Scale->ConstB=1.0f/350.0f;
    auto* Sample = NewObject<UMaterialExpressionTextureSampleParameter2D>(M);
    Sample->ParameterName=TEXT("ColoradoGroundDetail"); Sample->Texture=Albedo;
    Sample->Coordinates.Expression=Scale; Sample->SamplerType=SAMPLERTYPE_Color;
    auto* Roughness=NewObject<UMaterialExpressionConstant>(M); Roughness->R=.86f;
    for (UMaterialExpression* E : TArray<UMaterialExpression*>{Position,Coordinates,Scale,Sample,Roughness})
        M->GetExpressionCollection().AddExpression(E);
    M->GetEditorOnlyData()->BaseColor.Expression=Sample;
    M->GetEditorOnlyData()->Roughness.Expression=Roughness;
    M->PostEditChange(); FAssetRegistryModule::AssetCreated(M); Package->MarkPackageDirty();
    const FString Filename=FPackageName::LongPackageNameToFilename(PackageName,FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename),true);
    FSavePackageArgs SaveArgs; SaveArgs.TopLevelFlags=RF_Public|RF_Standalone; SaveArgs.SaveFlags=SAVE_NoError;
    return UPackage::SavePackage(Package,M,*Filename,SaveArgs) ? M : nullptr;
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
    auto* Water=World->SpawnActor<ARaftSimRiverWaterConfig>(); if (!Water) return false;
    Water->CookedFieldsDir=Fields; Water->FlowBand=FName(*J->GetStringField(TEXT("flow_band")));
    Water->CoordinateMapPath=J->GetStringField(TEXT("coordinate_map"));
    Water->StreamingManifestPath=J->GetStringField(TEXT("streaming"));
    Water->WindowCenterM=FVector2D(Start,0); Water->WindowExtentM=480;
    Water->bRecenterHydraulicCrux=false; Water->bEnableMovingWindowStreaming=true;
    Water->MovingWindowStationExtentM=480; Water->MovingWindowAdvanceM=80;
    Water->MovingWindowLateralExtentM=J->GetNumberField(TEXT("lateral_extent_m"));
    Water->LivePresentationWidthM=Water->MovingWindowLateralExtentM;
    Water->bEnableCookedFarFieldWater=true; Water->bMapProvidesTerrain=true;
    Water->bLiveSolverOwnsRuntimeRendering=true; Water->bEnableLiveSolverVolumeCore=true;
    Water->LiveVolumeCoreMaterialOverride=LoadObject<UMaterialInterface>(nullptr,
        TEXT("/Game/RaftSim/Environment/ColoradoRun/Water/Materials/MI_RaftSim_ColoradoHance_LiveVolumeWaterV2.MI_RaftSim_ColoradoHance_LiveVolumeWaterV2"));
    Water->LiveWaterFlowNormalTexture=LoadObject<UTexture2D>(nullptr,
        TEXT("/Game/RaftSim/Environment/ColoradoRun/Water/Textures/T_RaftSim_ColoradoHanceWaterV1_FlowNormal.T_RaftSim_ColoradoHanceWaterV1_FlowNormal"));
    Water->LiveWaterFoamLaceTexture=LoadObject<UTexture2D>(nullptr,
        TEXT("/Game/RaftSim/Environment/ColoradoRun/Water/Textures/T_RaftSim_ColoradoHanceWaterV1_FoamLace.T_RaftSim_ColoradoHanceWaterV1_FoamLace"));
    if (!Water->LiveVolumeCoreMaterialOverride || !Water->LiveWaterFlowNormalTexture || !Water->LiveWaterFoamLaceTexture)
    { Error=TEXT("Missing shared Colorado water optics"); return false; }
    Water->LiveSurfaceCalmCoverage=.035f; Water->LiveSurfaceActiveCoverage=.14f;
    Water->LiveSurfaceRoughness=.32f; Water->LiveFoamIntensity=.55f;
    Water->bEnableLiveRapidSurfaceRefinement=true; Water->LiveRapidSurfaceSubdivision=2;
    Water->bEnableLiveRaftLocalFluidHeightfield=true; Water->LiveRaftLocalFluidWindowMeters=100;
    Water->LiveRaftLocalFluidHeightfieldStrength=.65f;
    Water->ObservedWhitewaterGain=0; // No Hance photographed foam mask on another rapid.
    Water->SetActorLabel(TEXT("Catalog_RuntimeWater"));
    auto* Raft=World->SpawnActor<ARaftSimRaftActor>(ARaftSimRaftActor::StaticClass(),FTransform(Rotation,LaunchCm));
    if (!Raft) return false;
    auto* Rig=FindFProperty<FEnumProperty>(Raft->GetClass(),TEXT("RaftRig"));
    if (!Rig) return false;
    Rig->GetUnderlyingProperty()->SetIntPropertyValue(Rig->ContainerPtrToValuePtr<void>(Raft),
        static_cast<int64>(ERaftSimRaftRig::ColoradoOarRig));
    Raft->SetActorLabel(TEXT("Catalog_ProductionRaft"));
    World->SpawnActor<APlayerStart>(APlayerStart::StaticClass(),FTransform(Rotation,LaunchCm+FVector(0,0,180)));
    UClass* RunClass=LoadClass<AActor>(nullptr,TEXT("/Script/SmokeEmIfYouGotEm.RaftSimRunManager"));
    AActor* Run=RunClass ? World->SpawnActor<AActor>(RunClass,FTransform::Identity) : nullptr;
    if (!Run) return false;
    auto* Scenario=FindFProperty<FNameProperty>(RunClass,TEXT("ScenarioId"));
    auto* StartProp=FindFProperty<FFloatProperty>(RunClass,TEXT("StartStationM"));
    auto* FinishProp=FindFProperty<FFloatProperty>(RunClass,TEXT("FinishStationM"));
    if (!Scenario || !StartProp || !FinishProp) return false;
    Scenario->SetPropertyValue_InContainer(Run,FName(*J->GetStringField(TEXT("section_id"))));
    StartProp->SetPropertyValue_InContainer(Run,Start); FinishProp->SetPropertyValue_InContainer(Run,Finish);
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
}
