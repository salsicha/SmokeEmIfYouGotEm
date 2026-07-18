// Bootstraps the vertical-slice runtime content: Enhanced Input assets and the
// boot/test-tank maps. Registered as console commands so they run headlessly via
// UnrealEditor-Cmd -ExecCmds, following the RaftSim editor-command conventions.

#include "Camera/CameraActor.h"
#include "Components/SkyAtmosphereComponent.h"
#include "Editor.h"
#include "Engine/DirectionalLight.h"
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
    AddActorToWorld(
        World, ADirectionalLight::StaticClass(),
        FTransform(FRotator(-38.0f, 42.0f, 0.0f), FVector(0.0f, 0.0f, 1200.0f)));
    AddActorToWorld(World, ASkyLight::StaticClass(), FTransform(FVector(0.0f, 0.0f, 1100.0f)));
    if (UClass* SkyAtmosphereClass =
            LoadClass<AActor>(nullptr, TEXT("/Script/Engine.SkyAtmosphere")))
    {
        AddActorToWorld(World, SkyAtmosphereClass, FTransform(FVector::ZeroVector));
    }
    AddActorToWorld(
        World, AExponentialHeightFog::StaticClass(), FTransform(FVector(0.0f, 0.0f, -150.0f)));
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
        // Water surface at Z=0 (matches ARaftSimRaftActor's flat-water fallback)
        // and a bed plane 3 m below.
        AddScaledPlane(
            World, FVector(0.0f, 0.0f, 0.0f), FVector(400.0f, 400.0f, 1.0f),
            TEXT("/Game/RaftSim/Rendering/M_RaftSim_SolverSurfaceWaterCandidate."
                 "M_RaftSim_SolverSurfaceWaterCandidate"));
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

static void HandleCreateTroublemakerMap(const TArray<FString>&)
{
    UWorld* World = UEditorLoadingAndSavingUtils::NewBlankMap(false);
    AddCommonLighting(World);

    // Visual ground and a river water surface at Z=0. The live solver window
    // (loaded from the river config) drives the actual surface.
    AddScaledPlane(
        World, FVector(0.0f, 0.0f, -300.0f), FVector(700.0f, 700.0f, 1.0f),
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));

    // River water config: median-flow Troublemaker cooked window centred at
    // origin, 600 m. The raft resolves this at BeginPlay.
    AActor* RiverConfig = AddActorToWorld(
        World, ARaftSimRiverWaterConfig::StaticClass(), FTransform(FVector::ZeroVector));
    (void)RiverConfig;

    // Raft at the upstream scout eddy; run flows downstream (+X). Kept within
    // the rendered surface grid and the loaded window for v1 registration.
    AddActorToWorld(
        World, ARaftSimRaftActor::StaticClass(),
        FTransform(FVector(-6000.0f, 0.0f, 60.0f)));
    AddActorToWorld(
        World, APlayerStart::StaticClass(),
        FTransform(FVector(-6600.0f, 0.0f, 200.0f)));

    SetWorldGameMode(World, TEXT("/Script/SmokeEmIfYouGotEm.RaftSimVerticalSliceGameMode"));
    const bool bSaved = SaveWorldAsMap(World, TEXT("/Game/RaftSim/Maps/L_Troublemaker"));
    UE_LOG(LogTemp, Display, TEXT("RaftSim bootstrap: L_Troublemaker saved=%d"), bSaved ? 1 : 0);
}

static FAutoConsoleCommand GCreateTroublemakerMapCommand(
    TEXT("RaftSim.CreateTroublemakerMap"),
    TEXT("Generate L_Troublemaker: the South Fork Troublemaker rapid with live "
         "cooked-field river water, raft, and player start."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&HandleCreateTroublemakerMap));

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
