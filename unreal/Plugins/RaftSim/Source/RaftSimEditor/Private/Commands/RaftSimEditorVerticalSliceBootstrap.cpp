// Bootstraps the vertical-slice runtime content: Enhanced Input assets and the
// boot/test-tank maps. Registered as console commands so they run headlessly via
// UnrealEditor-Cmd -ExecCmds, following the RaftSim editor-command conventions.

#include "Camera/CameraActor.h"
#include "Components/SkyAtmosphereComponent.h"
#include "Editor.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Engine/DirectionalLight.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Engine/ExponentialHeightFog.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/SkyLight.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "FileHelpers.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/PlayerStart.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/FileManager.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "Materials/MaterialInterface.h"
#include "Misc/PackageName.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRockObstacleActor.h"
#include "RaftSimRiverWaterConfig.h"
#include "UObject/Package.h"
#include "UObject/SavePackage.h"

namespace RaftSimVerticalSliceBootstrap
{

struct FActionSpec
{
    const TCHAR* Name;
    EInputActionValueType ValueType;
};

// The 23 contracted action names (RaftSimInputActions.h) plus IA_Look for
// flat-screen camera. Value types follow GetMilestone23ManualInputContracts();
// the three uncontracted system actions use conventional types.
static const FActionSpec GActionSpecs[] = {
    {TEXT("PaddleStroke"), EInputActionValueType::Axis3D},
    {TEXT("PaddleBrace"), EInputActionValueType::Boolean},
    {TEXT("PaddleDraw"), EInputActionValueType::Axis2D},
    {TEXT("OarLeftStroke"), EInputActionValueType::Axis2D},
    {TEXT("OarRightStroke"), EInputActionValueType::Axis2D},
    {TEXT("OarFeather"), EInputActionValueType::Axis1D},
    {TEXT("GuideCommandForwardPaddle"), EInputActionValueType::Boolean},
    {TEXT("GuideCommandBackPaddle"), EInputActionValueType::Boolean},
    {TEXT("GuideCommandLeftPaddle"), EInputActionValueType::Boolean},
    {TEXT("GuideCommandRightPaddle"), EInputActionValueType::Boolean},
    {TEXT("GuideCommandStop"), EInputActionValueType::Boolean},
    {TEXT("HighSide"), EInputActionValueType::Boolean},
    {TEXT("CrewLean"), EInputActionValueType::Axis1D},
    {TEXT("HoldOn"), EInputActionValueType::Boolean},
    {TEXT("RescueTargetSelect"), EInputActionValueType::Axis1D},
    {TEXT("RescueReachGrab"), EInputActionValueType::Boolean},
    {TEXT("RescueThrowLine"), EInputActionValueType::Boolean},
    {TEXT("ReseatCrew"), EInputActionValueType::Boolean},
    {TEXT("GuideCommandPushToTalk"), EInputActionValueType::Boolean},
    {TEXT("RecenterVR"), EInputActionValueType::Boolean},
    {TEXT("Pause"), EInputActionValueType::Boolean},
    {TEXT("ReplayScrub"), EInputActionValueType::Axis1D},
    {TEXT("DebugOverlayToggle"), EInputActionValueType::Boolean},
    {TEXT("Look"), EInputActionValueType::Axis2D},
};

static bool SaveAssetPackage(UPackage* Package, UObject* Asset)
{
    const FString Filename = FPackageName::LongPackageNameToFilename(
        Package->GetName(), FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    return UPackage::SavePackage(Package, Asset, *Filename, SaveArgs);
}

static UInputAction* CreateInputActionAsset(const FActionSpec& Spec)
{
    const FString AssetName = FString::Printf(TEXT("IA_%s"), Spec.Name);
    const FString PackagePath = FString::Printf(TEXT("/Game/RaftSim/Input/%s"), *AssetName);
    UPackage* Package = CreatePackage(*PackagePath);
    UInputAction* Action = NewObject<UInputAction>(
        Package, FName(*AssetName), RF_Public | RF_Standalone);
    Action->ValueType = Spec.ValueType;
    if (!SaveAssetPackage(Package, Action))
    {
        return nullptr;
    }
    return Action;
}

static void AddKeyMapping(
    UInputMappingContext* Context, UInputAction* Action, const FKey& Key,
    bool bNegate = false, bool bSwizzleToY = false)
{
    FEnhancedActionKeyMapping& Mapping = Context->MapKey(Action, Key);
    if (bSwizzleToY)
    {
        UInputModifierSwizzleAxis* Swizzle =
            NewObject<UInputModifierSwizzleAxis>(Context, NAME_None, RF_Public);
        Swizzle->Order = EInputAxisSwizzle::YXZ;
        Mapping.Modifiers.Add(Swizzle);
    }
    if (bNegate)
    {
        UInputModifierNegate* Negate =
            NewObject<UInputModifierNegate>(Context, NAME_None, RF_Public);
        Mapping.Modifiers.Add(Negate);
    }
}

static void HandleCreateVerticalSliceInputAssets(const TArray<FString>&)
{
    TMap<FString, UInputAction*> Actions;
    for (const FActionSpec& Spec : GActionSpecs)
    {
        if (UInputAction* Action = CreateInputActionAsset(Spec))
        {
            Actions.Add(Spec.Name, Action);
        }
    }

    const FString ContextName = TEXT("IMC_RaftSimDefault");
    const FString PackagePath = FString::Printf(TEXT("/Game/RaftSim/Input/%s"), *ContextName);
    UPackage* Package = CreatePackage(*PackagePath);
    UInputMappingContext* Context = NewObject<UInputMappingContext>(
        Package, FName(*ContextName), RF_Public | RF_Standalone);

    // Keyboard + mouse.
    AddKeyMapping(Context, Actions[TEXT("PaddleStroke")], EKeys::W);
    AddKeyMapping(Context, Actions[TEXT("PaddleStroke")], EKeys::S, /*bNegate=*/true);
    AddKeyMapping(Context, Actions[TEXT("PaddleDraw")], EKeys::D);
    AddKeyMapping(Context, Actions[TEXT("PaddleDraw")], EKeys::A, /*bNegate=*/true);
    AddKeyMapping(Context, Actions[TEXT("Look")], EKeys::Mouse2D);
    AddKeyMapping(Context, Actions[TEXT("HighSide")], EKeys::SpaceBar);
    AddKeyMapping(Context, Actions[TEXT("Pause")], EKeys::Escape);
    AddKeyMapping(Context, Actions[TEXT("GuideCommandForwardPaddle")], EKeys::One);
    AddKeyMapping(Context, Actions[TEXT("GuideCommandBackPaddle")], EKeys::Two);
    AddKeyMapping(Context, Actions[TEXT("GuideCommandLeftPaddle")], EKeys::Three);
    AddKeyMapping(Context, Actions[TEXT("GuideCommandRightPaddle")], EKeys::Four);
    AddKeyMapping(Context, Actions[TEXT("GuideCommandStop")], EKeys::Five);
    AddKeyMapping(Context, Actions[TEXT("RescueTargetSelect")], EKeys::MouseWheelAxis);
    AddKeyMapping(Context, Actions[TEXT("RescueReachGrab")], EKeys::E);
    AddKeyMapping(Context, Actions[TEXT("RescueThrowLine")], EKeys::R);
    AddKeyMapping(Context, Actions[TEXT("ReseatCrew")], EKeys::F);

    // Gamepad.
    AddKeyMapping(Context, Actions[TEXT("PaddleStroke")], EKeys::Gamepad_LeftY);
    AddKeyMapping(Context, Actions[TEXT("PaddleDraw")], EKeys::Gamepad_LeftX);
    AddKeyMapping(Context, Actions[TEXT("Look")], EKeys::Gamepad_RightX);
    AddKeyMapping(
        Context, Actions[TEXT("Look")], EKeys::Gamepad_RightY, /*bNegate=*/false,
        /*bSwizzleToY=*/true);
    AddKeyMapping(Context, Actions[TEXT("HighSide")], EKeys::Gamepad_FaceButton_Left);
    AddKeyMapping(Context, Actions[TEXT("Pause")], EKeys::Gamepad_Special_Right);
    AddKeyMapping(Context, Actions[TEXT("GuideCommandForwardPaddle")], EKeys::Gamepad_DPad_Up);
    AddKeyMapping(Context, Actions[TEXT("GuideCommandBackPaddle")], EKeys::Gamepad_DPad_Down);
    AddKeyMapping(Context, Actions[TEXT("GuideCommandLeftPaddle")], EKeys::Gamepad_DPad_Left);
    AddKeyMapping(Context, Actions[TEXT("GuideCommandRightPaddle")], EKeys::Gamepad_DPad_Right);
    AddKeyMapping(Context, Actions[TEXT("GuideCommandStop")], EKeys::Gamepad_FaceButton_Top);
    AddKeyMapping(Context, Actions[TEXT("RescueTargetSelect")], EKeys::Gamepad_LeftShoulder, /*bNegate=*/true);
    AddKeyMapping(Context, Actions[TEXT("RescueTargetSelect")], EKeys::Gamepad_RightShoulder);
    AddKeyMapping(Context, Actions[TEXT("RescueReachGrab")], EKeys::Gamepad_FaceButton_Bottom);
    AddKeyMapping(Context, Actions[TEXT("RescueThrowLine")], EKeys::Gamepad_RightTrigger);
    AddKeyMapping(Context, Actions[TEXT("ReseatCrew")], EKeys::Gamepad_FaceButton_Right);

    const bool bSaved = SaveAssetPackage(Package, Context);
    UE_LOG(
        LogTemp, Display,
        TEXT("RaftSim.CreateVerticalSliceInputAssets: %d actions, context saved=%d"),
        Actions.Num(), bSaved ? 1 : 0);
}

static AActor* AddActorToWorld(UWorld* World, UClass* Class, const FTransform& Transform)
{
    return GEditor->AddActor(World->GetCurrentLevel(), Class, Transform);
}

static void AddCommonLighting(UWorld* World)
{
    // Warm mid-morning Sierra sun, angled for raking water highlights.
    if (ADirectionalLight* Sun = Cast<ADirectionalLight>(AddActorToWorld(
            World, ADirectionalLight::StaticClass(),
            FTransform(FRotator(-42.0f, 55.0f, 0.0f), FVector(0.0f, 0.0f, 1200.0f)))))
    {
        if (UDirectionalLightComponent* SunComp = Sun->GetComponent())
        {
            SunComp->SetIntensity(10.0f);
            SunComp->SetLightColor(FLinearColor(1.0f, 0.955f, 0.86f));
            SunComp->SetAtmosphereSunLight(true);
        }
    }
    if (ASkyLight* Sky = Cast<ASkyLight>(
            AddActorToWorld(World, ASkyLight::StaticClass(), FTransform(FVector(0.0f, 0.0f, 1100.0f)))))
    {
        if (USkyLightComponent* SkyComp = Sky->GetLightComponent())
        {
            SkyComp->SetMobility(EComponentMobility::Movable);
            SkyComp->bRealTimeCapture = true;
            // Lower ambient fill so the sun casts real shadows on the walls.
            SkyComp->SetIntensity(0.6f);
        }
    }
    if (UClass* SkyAtmosphereClass =
            LoadClass<AActor>(nullptr, TEXT("/Script/Engine.SkyAtmosphere")))
    {
        AddActorToWorld(World, SkyAtmosphereClass, FTransform(FVector::ZeroVector));
    }
    if (UClass* VolumetricCloudClass =
            LoadClass<AActor>(nullptr, TEXT("/Script/Engine.VolumetricCloud")))
    {
        AddActorToWorld(World, VolumetricCloudClass, FTransform(FVector::ZeroVector));
    }
    // Thin canyon haze only — the default fog density (~0.02) washes the whole
    // ~150 m gorge into milk; a light density keeps depth without the milkiness.
    if (AExponentialHeightFog* Fog = Cast<AExponentialHeightFog>(AddActorToWorld(
            World, AExponentialHeightFog::StaticClass(), FTransform(FVector(0.0f, 0.0f, -400.0f)))))
    {
        if (UExponentialHeightFogComponent* FogComp = Fog->GetComponent())
        {
            FogComp->SetFogDensity(0.0025f);
            FogComp->SetFogHeightFalloff(0.35f);
            FogComp->SetFogInscatteringColor(FLinearColor(0.55f, 0.62f, 0.72f));
            FogComp->SetStartDistance(2500.0f);
        }
    }

    // Unbound post-process: fixed exposure + subtle bloom for a photographic
    // look, and high Lumen quality for the reflective water.
    if (APostProcessVolume* PP = Cast<APostProcessVolume>(AddActorToWorld(
            World, APostProcessVolume::StaticClass(), FTransform(FVector::ZeroVector))))
    {
        PP->bUnbound = true;
        FPostProcessSettings& S = PP->Settings;
        S.bOverride_AutoExposureMethod = true;
        S.AutoExposureMethod = AEM_Manual;
        S.bOverride_AutoExposureBias = true;
        S.AutoExposureBias = 9.5f;
        S.bOverride_BloomIntensity = true;
        S.BloomIntensity = 0.35f;
        S.bOverride_LumenReflectionQuality = true;
        S.LumenReflectionQuality = 2.0f;
        S.bOverride_LumenFinalGatherQuality = true;
        S.LumenFinalGatherQuality = 2.0f;
        S.bOverride_LumenReflectionsScreenTraces = true;
        S.LumenReflectionsScreenTraces = 1;
    }
}

static void SetWorldGameMode(UWorld* World, const TCHAR* GameModeClassPath)
{
    if (UClass* GameModeClass = LoadClass<AGameModeBase>(nullptr, GameModeClassPath))
    {
        World->GetWorldSettings()->DefaultGameMode = GameModeClass;
    }
    else
    {
        UE_LOG(LogTemp, Warning, TEXT("RaftSim bootstrap: game mode not found: %s"),
               GameModeClassPath);
    }
}

static bool SaveWorldAsMap(UWorld* World, const TCHAR* PackagePath)
{
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetMapPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    return FEditorFileUtils::SaveMap(World, Filename);
}

static AStaticMeshActor* AddScaledPlane(
    UWorld* World, const FVector& Location, const FVector& Scale, const TCHAR* MaterialPath)
{
    AStaticMeshActor* PlaneActor = Cast<AStaticMeshActor>(
        AddActorToWorld(World, AStaticMeshActor::StaticClass(), FTransform(Location)));
    if (PlaneActor == nullptr)
    {
        return nullptr;
    }
    UStaticMesh* PlaneMesh =
        LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Plane.Plane"));
    PlaneActor->GetStaticMeshComponent()->SetStaticMesh(PlaneMesh);
    PlaneActor->GetStaticMeshComponent()->SetWorldScale3D(Scale);
    if (UMaterialInterface* Material = LoadObject<UMaterialInterface>(nullptr, MaterialPath))
    {
        PlaneActor->GetStaticMeshComponent()->SetMaterial(0, Material);
    }
    return PlaneActor;
}

static void HandleCreateVerticalSliceCoreMaps(const TArray<FString>&)
{
    // Boot / menu map.
    {
        UWorld* World = UEditorLoadingAndSavingUtils::NewBlankMap(false);
        AddCommonLighting(World);
        AddActorToWorld(
            World, ACameraActor::StaticClass(),
            FTransform(FRotator(-8.0f, 25.0f, 0.0f), FVector(-800.0f, 0.0f, 350.0f)));
        SetWorldGameMode(World, TEXT("/Script/SmokeEmIfYouGotEm.RaftSimBootGameMode"));
        const bool bSaved = SaveWorldAsMap(World, TEXT("/Game/RaftSim/Maps/L_RaftSimBoot"));
        UE_LOG(LogTemp, Display, TEXT("RaftSim bootstrap: L_RaftSimBoot saved=%d"), bSaved ? 1 : 0);
    }

    // Flat-water test tank.
    {
        UWorld* World = UEditorLoadingAndSavingUtils::NewBlankMap(false);
        AddCommonLighting(World);
        // The raft spawns the live procedural water surface + riverbed itself,
        // so the tank needs no static water plane (a stale one z-fought the
        // procedural surface). A bed plane 3 m down catches the eye under it.
        AddScaledPlane(
            World, FVector(0.0f, 0.0f, -300.0f), FVector(400.0f, 400.0f, 1.0f),
            TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
        AddActorToWorld(
            World, ARaftSimRaftActor::StaticClass(),
            FTransform(FVector(0.0f, 0.0f, 40.0f)));
        AddActorToWorld(
            World, APlayerStart::StaticClass(),
            FTransform(FVector(0.0f, -600.0f, 150.0f)));
        SetWorldGameMode(World, TEXT("/Script/SmokeEmIfYouGotEm.RaftSimVerticalSliceGameMode"));
        const bool bSaved = SaveWorldAsMap(World, TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"));
        UE_LOG(
            LogTemp, Display, TEXT("RaftSim bootstrap: L_RaftSimTestTank saved=%d"),
            bSaved ? 1 : 0);
    }
}

// One playable river map: signature rapid, live cooked-field water, raft.
struct FRiverMapSpec
{
    const TCHAR* MapName;
    const TCHAR* CookedFieldsDir;
    const TCHAR* FlowBand;
};

// The five runnable rivers (docs/five-river-simulation-plan.md). Each points at
// its signature rapid's cooked flow fields; a river map that has no cooked
// package yet falls back to the dev tank at runtime until its fields land.
static const FRiverMapSpec GRiverMaps[] = {
    {TEXT("L_Troublemaker"),
     TEXT("physics/data/real_world/south_fork_american_chili_bar/scenario_troublemaker/cooked_flow_fields"),
     TEXT("median_runnable")},
    {TEXT("L_Hance"),
     TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/scenario_hance/cooked_flow_fields"),
     TEXT("median_runnable")},
    {TEXT("L_UpperHuacas"),
     TEXT("physics/data/real_world/pacuare_river_costa_rica/scenario_upper_huacas/cooked_flow_fields"),
     TEXT("median_runnable")},
    {TEXT("L_Terminator"),
     TEXT("physics/data/real_world/futaleufu_river_chile/scenario_terminator/cooked_flow_fields"),
     TEXT("median_runnable")},
    {TEXT("L_LavaCanyon"),
     TEXT("physics/data/real_world/chilko_river_lava_canyon/scenario_lava_canyon/cooked_flow_fields"),
     TEXT("median_runnable")},
};

static bool BuildRiverMap(const FRiverMapSpec& Spec)
{
    UWorld* World = UEditorLoadingAndSavingUtils::NewBlankMap(false);
    AddCommonLighting(World);

    AddScaledPlane(
        World, FVector(0.0f, 0.0f, -300.0f), FVector(700.0f, 700.0f, 1.0f),
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));

    // River water config pointing at this river's cooked window — placed only
    // when the cooked package actually exists, so a river whose fields are not
    // cooked yet loads clean dev-tank water (still playable) and is regenerated
    // with live river water once its fields land.
    const FString ManifestPath = FPaths::Combine(
        FPaths::ProjectDir(), TEXT("../"), Spec.CookedFieldsDir, TEXT("manifest.json"));
    const bool bCookedFieldsExist = FPaths::FileExists(ManifestPath);
    if (bCookedFieldsExist)
    {
        if (ARaftSimRiverWaterConfig* RiverConfig = Cast<ARaftSimRiverWaterConfig>(
                AddActorToWorld(World, ARaftSimRiverWaterConfig::StaticClass(),
                                FTransform(FVector::ZeroVector))))
        {
            RiverConfig->CookedFieldsDir = Spec.CookedFieldsDir;
            RiverConfig->FlowBand = FName(Spec.FlowBand);
            // Load the whole cooked reach so the loader can re-centre the window
            // on its hydraulic crux (a huge extent clamps to the full grid for
            // any river regardless of its cooked origin).
            RiverConfig->WindowCenterM = FVector2D::ZeroVector;
            RiverConfig->WindowExtentM = 4000.0f;
        }
    }
    UE_LOG(LogTemp, Display, TEXT("RaftSim bootstrap: %s cooked_fields=%d"),
           Spec.MapName, bCookedFieldsExist ? 1 : 0);

    // Raft at the upstream scout eddy; run flows downstream (+X).
    AddActorToWorld(
        World, ARaftSimRaftActor::StaticClass(),
        FTransform(FVector(-6000.0f, 0.0f, 60.0f)));
    AddActorToWorld(
        World, APlayerStart::StaticClass(),
        FTransform(FVector(-6600.0f, 0.0f, 200.0f)));

    // Deterministic hydraulic-crux rock garden. These are runtime-authoritative
    // D4 obstacles, not decorative boulders: the raft binds their transforms,
    // radii, and friction into the same fixed-step solve that drives visible
    // deformation. Per-river authored geometry will replace/augment them as
    // M2/M3 procedural geography and rapid authoring land.
    struct FRockSpec
    {
        FVector LocationCm;
        float RadiusM;
        float Friction;
    };
    const FRockSpec RockGarden[] = {
        {FVector(-500.0f, -260.0f, -35.0f), 0.95f, 0.74f},
        {FVector(0.0f, 90.0f, -28.0f), 1.25f, 0.78f},
        {FVector(520.0f, 310.0f, -42.0f), 0.82f, 0.70f},
        {FVector(860.0f, -340.0f, -45.0f), 0.72f, 0.68f},
    };
    for (const FRockSpec& RockSpec : RockGarden)
    {
        if (ARaftSimRockObstacleActor* Rock = Cast<ARaftSimRockObstacleActor>(
                AddActorToWorld(
                    World,
                    ARaftSimRockObstacleActor::StaticClass(),
                    FTransform(RockSpec.LocationCm))))
        {
            Rock->ConfigureContact(RockSpec.RadiusM, RockSpec.Friction);
        }
    }

    SetWorldGameMode(World, TEXT("/Script/SmokeEmIfYouGotEm.RaftSimVerticalSliceGameMode"));
    const FString PackagePath = FString::Printf(TEXT("/Game/RaftSim/Maps/%s"), Spec.MapName);
    const bool bSaved = SaveWorldAsMap(World, *PackagePath);
    UE_LOG(LogTemp, Display, TEXT("RaftSim bootstrap: %s saved=%d"), Spec.MapName, bSaved ? 1 : 0);
    return bSaved;
}

static void HandleCreateRiverMaps(const TArray<FString>& Args)
{
    for (const FRiverMapSpec& Spec : GRiverMaps)
    {
        // Optional filter: build only maps whose name contains an arg token.
        if (Args.Num() > 0)
        {
            bool bMatch = false;
            for (const FString& Arg : Args)
            {
                if (FString(Spec.MapName).Contains(Arg)) { bMatch = true; }
            }
            if (!bMatch) { continue; }
        }
        BuildRiverMap(Spec);
    }
}

static FAutoConsoleCommand GCreateRiverMapsCommand(
    TEXT("RaftSim.CreateRiverMaps"),
    TEXT("Generate the five runnable river maps (L_Troublemaker, L_Hance, "
         "L_UpperHuacas, L_Terminator, L_LavaCanyon) with live cooked-field "
         "river water. Optional args filter by map-name substring."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&HandleCreateRiverMaps));

static FAutoConsoleCommand GCreateVerticalSliceInputAssetsCommand(
    TEXT("RaftSim.CreateVerticalSliceInputAssets"),
    TEXT("Generate the Enhanced Input action assets and default mapping context "
         "under /Game/RaftSim/Input."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&HandleCreateVerticalSliceInputAssets));

static FAutoConsoleCommand GCreateVerticalSliceCoreMapsCommand(
    TEXT("RaftSim.CreateVerticalSliceCoreMaps"),
    TEXT("Generate L_RaftSimBoot (menu) and L_RaftSimTestTank (flat-water raft "
         "tank) under /Game/RaftSim/Maps."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&HandleCreateVerticalSliceCoreMaps));

} // namespace RaftSimVerticalSliceBootstrap
