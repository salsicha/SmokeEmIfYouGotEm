// Headless visual-verification helper (P4 photoreal track). Registers
// `RaftSim.CaptureAfter <seconds> [label] [x y z pitch yaw]`. After letting the
// live water and terrain build for a few in-game seconds it optionally places a
// camera (when the 5 pose args are supplied) and makes it the view target, then
// screenshots the viewport backbuffer and requests exit. Uses FScreenshotRequest
// (the automation path) rather than the HighResShot console command, which does
// not write offscreen on Metal. Driven via a single -ExecCmds command to avoid
// the multi-command no-op pitfall.

#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/MeshComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/DirectionalLight.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformMisc.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Misc/Paths.h"
#include "NiagaraComponent.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRockObstacleActor.h"
#include "RaftSimCameraPresentation.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimWaterSurfaceActor.h"
#include "RaftSimWaterVfxActor.h"
#include "TimerManager.h"
#include "UnrealClient.h"

namespace RaftSimCaptureCommand
{

static void LogVisibleWaterPresentationInventory(UWorld* World)
{
    if (World == nullptr)
    {
        return;
    }
    int32 MatchingComponentCount = 0;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (Actor == nullptr)
        {
            continue;
        }
        TInlineComponentArray<UPrimitiveComponent*> Components(Actor);
        for (UPrimitiveComponent* Component : Components)
        {
            if (Component == nullptr)
            {
                continue;
            }
            FString MaterialList;
            bool bWaterNamed =
                Actor->GetName().Contains(TEXT("Water"), ESearchCase::IgnoreCase) ||
                Actor->GetName().Contains(TEXT("River"), ESearchCase::IgnoreCase) ||
                Component->GetName().Contains(TEXT("Water"), ESearchCase::IgnoreCase) ||
                Component->GetName().Contains(TEXT("River"), ESearchCase::IgnoreCase) ||
                Component->GetName().Contains(TEXT("Foam"), ESearchCase::IgnoreCase);
            for (int32 MaterialIndex = 0;
                 MaterialIndex < Component->GetNumMaterials(); ++MaterialIndex)
            {
                const UMaterialInterface* Material =
                    Component->GetMaterial(MaterialIndex);
                if (Material == nullptr)
                {
                    continue;
                }
                const FString MaterialPath = Material->GetPathName();
                bWaterNamed |=
                    MaterialPath.Contains(TEXT("Water"), ESearchCase::IgnoreCase) ||
                    MaterialPath.Contains(TEXT("River"), ESearchCase::IgnoreCase) ||
                    MaterialPath.Contains(TEXT("Foam"), ESearchCase::IgnoreCase);
                if (!MaterialList.IsEmpty())
                {
                    MaterialList += TEXT(",");
                }
                MaterialList += MaterialPath;
            }
            if (!bWaterNamed)
            {
                continue;
            }
            ++MatchingComponentCount;
            const FBox Bounds = Component->Bounds.GetBox();
            FString TagList;
            for (const FName& Tag : Actor->Tags)
            {
                if (!TagList.IsEmpty())
                {
                    TagList += TEXT(",");
                }
                TagList += Tag.ToString();
            }
            UE_LOG(
                LogTemp,
                Display,
                TEXT("RaftSim water presentation inventory: actor=%s class=%s "
                     "component=%s visible=%d shouldRender=%d actorHidden=%d "
                     "center=%s size=%s tags=[%s] materials=[%s]"),
                *Actor->GetName(),
                *Actor->GetClass()->GetName(),
                *Component->GetName(),
                Component->IsVisible() ? 1 : 0,
                Component->ShouldRender() ? 1 : 0,
                Actor->IsHidden() ? 1 : 0,
                *Bounds.GetCenter().ToCompactString(),
                *Bounds.GetSize().ToCompactString(),
                *TagList,
                *MaterialList);
        }
    }
    UE_LOG(
        LogTemp,
        Display,
        TEXT("RaftSim water presentation inventory: matchingComponents=%d"),
        MatchingComponentCount);
}

static ARaftSimRaftActor* FindRaft(UWorld* World)
{
    if (World != nullptr)
    {
        if (TActorIterator<ARaftSimRaftActor> It(World); It)
        {
            return *It;
        }
    }
    return nullptr;
}

static void ResolveRapidEvidenceCameraPose(
    const ARaftSimRaftActor& Raft,
    const FString& CameraPreset,
    FVector& OutLocation,
    FRotator& OutRotation)
{
    FVector CameraOffset(-400.0f, -380.0f, 290.0f);
    FVector LookAtOffset(20.0f, -10.0f, 35.0f);
    if (CameraPreset == TEXT("upstream_left"))
    {
        CameraOffset = FVector(400.0f, 380.0f, 290.0f);
    }
    else if (CameraPreset == TEXT("downstream_left"))
    {
        CameraOffset = FVector(-400.0f, 380.0f, 290.0f);
    }
    else if (CameraPreset == TEXT("upstream_right"))
    {
        CameraOffset = FVector(400.0f, -380.0f, 290.0f);
    }
    else if (CameraPreset == TEXT("contact_port"))
    {
        // Lower port-side review angle aimed at the bounded Meat Grinder D4
        // interface. This is camera composition only; the obstacle and raft
        // retain their live solver-derived world transforms.
        CameraOffset = FVector(-100.0f, -520.0f, 330.0f);
        LookAtOffset = FVector(-80.0f, -130.0f, 60.0f);
    }
    else if (CameraPreset == TEXT("contact_starboard"))
    {
        // Mirrored close review angle for seat-side paddle, crew, and contact
        // checks that cannot be judged reliably through the port-side crew.
        CameraOffset = FVector(-100.0f, 520.0f, 330.0f);
        LookAtOffset = FVector(-80.0f, 130.0f, 60.0f);
    }
    else if (CameraPreset == TEXT("particle_macro"))
    {
        // Capture-only inspection of the real D4 contact emitter volume. The
        // camera is close enough to resolve production-scale 2-6 cm spray and
        // sub-3 cm droplets without scaling particles or staging new events.
        CameraOffset = FVector(-100.0f, -300.0f, 145.0f);
        LookAtOffset = FVector(-100.0f, -130.0f, 10.0f);
    }
    else if (CameraPreset == TEXT("wrap_hero"))
    {
        // Release-review composition: retain the upstream-right view of the
        // real D4 contact while filling the frame with raft deformation, crew
        // response, and the obstacle instead of the distant shoreline.
        CameraOffset = FVector(360.0f, -350.0f, 275.0f);
        LookAtOffset = FVector(15.0f, -20.0f, 35.0f);
    }
    else if (CameraPreset == TEXT("river_action"))
    {
        // Guide-height contextual action view: the authentic D4 contact stays
        // in the foreground while the active channel, banks, terrain, and
        // downstream line remain legible. This is the release-media companion
        // to the close technical wrap_hero frame, not a staged simulation.
        CameraOffset = FVector(-680.0f, -520.0f, 245.0f);
        LookAtOffset = FVector(260.0f, 0.0f, 55.0f);
    }
    // Follow downstream yaw, but never inherit the wrapped raft's roll/pitch:
    // local +Z can point below the water once a real contact rotates the hull.
    const FVector FlatForward = Raft.GetActorForwardVector().GetSafeNormal2D();
    const FTransform LevelCameraBasis(
        FlatForward.IsNearlyZero()
            ? FRotator::ZeroRotator
            : FlatForward.Rotation(),
        Raft.GetActorLocation());
    OutLocation = LevelCameraBasis.TransformPosition(CameraOffset);
    const FVector LookAt = LevelCameraBasis.TransformPosition(LookAtOffset);
    OutRotation = (LookAt - OutLocation).Rotation();
}

static bool ResolveBreakingWaterEvidenceCameraPose(
    UWorld* World,
    const ARaftSimRaftActor& Raft,
    const FString& CameraPreset,
    FVector& OutLocation,
    FRotator& OutRotation)
{
    if (World == nullptr)
    {
        return false;
    }
    TArray<ARaftSimWaterSurfaceActor::FBreakingSite> Sites;
    if (TActorIterator<ARaftSimWaterSurfaceActor> It(World); It)
    {
        It->GetBreakingSites(Sites);
    }
    if (Sites.IsEmpty())
    {
        return false;
    }

    // Sites are already sorted strongest first by the live surface. Target
    // that genuine jump so material/geometry review does not mistake a weak
    // fringe response for the authored production bound.
    const ARaftSimWaterSurfaceActor::FBreakingSite* SelectedSite = &Sites[0];
    const float DistanceToRaftSquared = FVector::DistSquared2D(
        Raft.GetActorLocation(), SelectedSite->WorldPositionCm);
    FVector Downstream = SelectedSite->WorldVelocityMps.GetSafeNormal2D();
    if (Downstream.IsNearlyZero())
    {
        Downstream = Raft.GetActorForwardVector().GetSafeNormal2D();
    }
    if (Downstream.IsNearlyZero())
    {
        Downstream = FVector::ForwardVector;
    }
    const FVector Across(-Downstream.Y, Downstream.X, 0.0f);
    FVector LookAt = SelectedSite->WorldPositionCm -
        Downstream * 40.0f + FVector::UpVector * 35.0f;
    if (CameraPreset == TEXT("breaking_water_side"))
    {
        OutLocation = SelectedSite->WorldPositionCm -
            Downstream * 260.0f - Across * 650.0f + FVector::UpVector * 270.0f;
        LookAt = SelectedSite->WorldPositionCm +
            Downstream * 110.0f + FVector::UpVector * 45.0f;
    }
    else if (CameraPreset == TEXT("breaking_water_opposite"))
    {
        OutLocation = SelectedSite->WorldPositionCm -
            Downstream * 180.0f + Across * 600.0f + FVector::UpVector * 255.0f;
        LookAt = SelectedSite->WorldPositionCm +
            Downstream * 100.0f + FVector::UpVector * 40.0f;
    }
    else
    {
        // Default: review the breaking face from downstream and mostly along
        // channel, keeping the river corridor rather than a bank cut behind it.
        OutLocation = SelectedSite->WorldPositionCm +
            Downstream * 650.0f - Across * 160.0f + FVector::UpVector * 220.0f;
    }
    OutRotation = (LookAt - OutLocation).Rotation();
    const FName DressingTag(TEXT("RaftSimFullReachDressing"));
    const FName FarFieldDressingTag(TEXT("RaftSimFullReachFarFieldDressing"));
    for (TActorIterator<AActor> ActorIt(World); ActorIt; ++ActorIt)
    {
        AActor* Actor = *ActorIt;
        if (!Actor ||
            (!Actor->ActorHasTag(DressingTag) &&
             !Actor->ActorHasTag(FarFieldDressingTag)))
        {
            continue;
        }
        TInlineComponentArray<UHierarchicalInstancedStaticMeshComponent*>
            Components(Actor);
        for (UHierarchicalInstancedStaticMeshComponent* Component : Components)
        {
            if (!Component)
            {
                continue;
            }
            UStaticMesh* Mesh = Component->GetStaticMesh();
            for (int32 InstanceIndex = 0;
                 Mesh && InstanceIndex < Component->GetInstanceCount();
                 ++InstanceIndex)
            {
                FTransform InstanceTransform;
                if (!Component->GetInstanceTransform(
                        InstanceIndex, InstanceTransform, true))
                {
                    continue;
                }
                const float DistanceToSiteCm = FVector::Dist2D(
                    InstanceTransform.GetLocation(), SelectedSite->WorldPositionCm);
                if (DistanceToSiteCm > 3000.0f)
                {
                    continue;
                }
                const FBoxSphereBounds WorldBounds =
                    Mesh->GetBounds().TransformBy(InstanceTransform);
                const bool bRockComponent =
                    Component->GetName().Contains(TEXT("Boulder")) ||
                    Component->GetName().Contains(TEXT("Rock"));
                if (!bRockComponent && WorldBounds.BoxExtent.GetMax() < 50.0f)
                {
                    continue;
                }
                UE_LOG(
                    LogTemp,
                    Display,
                    TEXT("RaftSim.CaptureRapidWrapTest: nearbyDressingRock "
                         "component=%s mesh=%s instance=%d distanceToSiteCm=%.1f "
                         "location=%s scale=%s extent=%s"),
                    *Component->GetName(),
                    *Mesh->GetPathName(),
                    InstanceIndex,
                    DistanceToSiteCm,
                    *InstanceTransform.GetLocation().ToCompactString(),
                    *InstanceTransform.GetScale3D().ToCompactString(),
                    *WorldBounds.BoxExtent.ToCompactString());
            }
        }
    }
    UE_LOG(
        LogTemp,
        Display,
        TEXT("RaftSim.CaptureRapidWrapTest: breakingWaterCamera site=%s "
             "riverStationM=%.1f riverLateralM=%.1f "
             "intensity=%.3f presentationCoverage=%.3f "
             "presentationEdgeClearanceM=%.1f distanceToRaftCm=%.1f"),
        *SelectedSite->WorldPositionCm.ToCompactString(),
        SelectedSite->RiverCoordinatesMeters.X,
        SelectedSite->RiverCoordinatesMeters.Y,
        SelectedSite->Intensity,
        SelectedSite->PresentationCoverage,
        SelectedSite->PresentationEdgeClearanceMeters,
        FMath::Sqrt(DistanceToRaftSquared));
    return true;
}

static void HandleCaptureAfter(const TArray<FString>& Args, UWorld* World)
{
    if (World == nullptr)
    {
        return;
    }
    const float Delay = Args.Num() > 0 ? FMath::Max(FCString::Atof(*Args[0]), 0.1f) : 3.0f;
    const FString Label = Args.Num() > 1 ? Args[1] : TEXT("RaftSimCapture");
    const FString OutPath =
        FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Screenshots"), Label + TEXT(".png"));

    // Optional camera pose: x y z pitch yaw (world cm / degrees).
    bool bHasCamera = false;
    FVector CamLoc = FVector::ZeroVector;
    FRotator CamRot = FRotator::ZeroRotator;
    if (Args.Num() >= 7)
    {
        CamLoc = FVector(FCString::Atof(*Args[2]), FCString::Atof(*Args[3]), FCString::Atof(*Args[4]));
        CamRot = FRotator(FCString::Atof(*Args[5]), FCString::Atof(*Args[6]), 0.0f);
        bHasCamera = true;
    }

    TWeakObjectPtr<UWorld> WeakWorld(World);
    FTimerHandle Handle;
    World->GetTimerManager().SetTimer(
        Handle,
        FTimerDelegate::CreateLambda([WeakWorld, OutPath, bHasCamera, CamLoc, CamRot]()
        {
            UWorld* W = WeakWorld.Get();
            if (W != nullptr && bHasCamera)
            {
                ACameraActor* Cam = W->SpawnActor<ACameraActor>(
                    ACameraActor::StaticClass(), CamLoc, CamRot);
                if (Cam != nullptr)
                {
                    if (APlayerController* PC = W->GetFirstPlayerController())
                    {
                        PC->SetViewTarget(Cam);
                    }
                }
            }
            FScreenshotRequest::RequestScreenshot(
                OutPath, /*bShowUI=*/false, /*bAddFilenameSuffix=*/false);
            UE_LOG(LogTemp, Display, TEXT("RaftSim.CaptureAfter: requested screenshot -> %s"),
                   *OutPath);

            if (W != nullptr)
            {
                FTimerHandle ExitHandle;
                W->GetTimerManager().SetTimer(
                    ExitHandle,
                    FTimerDelegate::CreateLambda([]() { FPlatformMisc::RequestExit(false); }),
                    4.0f, false);
            }
        }),
        Delay, false);

    UE_LOG(LogTemp, Display, TEXT("RaftSim.CaptureAfter: capturing in %.1fs -> %s (camera=%d)"),
           Delay, *OutPath, bHasCamera ? 1 : 0);
}

static FAutoConsoleCommandWithWorldAndArgs GCaptureAfterCommand(
    TEXT("RaftSim.CaptureAfter"),
    TEXT("After N in-game seconds, optionally place a camera (x y z pitch yaw), "
         "screenshot the viewport and exit. "
         "Usage: RaftSim.CaptureAfter <seconds> [label] [x y z pitch yaw]"),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&HandleCaptureAfter));

// Over-the-shoulder capture: order the crew to paddle downstream so the raft
// runs into the rapid, then place the camera behind the raft's live position
// (it is physics-driven, so it cannot be teleported) looking downstream.
static void HandleCaptureRaft(const TArray<FString>& Args, UWorld* World)
{
    if (World == nullptr)
    {
        return;
    }
    const float Delay = Args.Num() > 0 ? FMath::Max(FCString::Atof(*Args[0]), 0.5f) : 14.0f;
    const FString Label = Args.Num() > 1 ? Args[1] : TEXT("RaftSimRaft");
    const float BackM = Args.Num() > 2 ? FCString::Atof(*Args[2]) : 8.0f;
    const float UpM = Args.Num() > 3 ? FCString::Atof(*Args[3]) : 4.0f;
    const float AheadM = Args.Num() > 4 ? FCString::Atof(*Args[4]) : 22.0f;
    auto DiagnosticFloat = [&Args](const TCHAR* Prefix, float DefaultValue)
    {
        const FString PrefixString(Prefix);
        for (int32 Index = 5; Index < Args.Num(); ++Index)
        {
            if (Args[Index].StartsWith(PrefixString, ESearchCase::IgnoreCase))
            {
                return FCString::Atof(*Args[Index].RightChop(PrefixString.Len()));
            }
        }
        return DefaultValue;
    };
    auto HasDiagnosticMode = [&Args](const TCHAR* Mode)
    {
        for (int32 Index = 5; Index < Args.Num(); ++Index)
        {
            if (Args[Index].Equals(Mode, ESearchCase::IgnoreCase))
            {
                return true;
            }
        }
        return false;
    };
    const float WaterRoughnessDiagnostic = FMath::Clamp(
        DiagnosticFloat(TEXT("waterroughness="), -1.0f), -1.0f, 1.0f);
    const float WaterSpecularDiagnostic = FMath::Clamp(
        DiagnosticFloat(TEXT("waterspecular="), -1.0f), -1.0f, 1.0f);
    const float WaterNormalDiagnostic = FMath::Clamp(
        DiagnosticFloat(TEXT("waternormal="), -1.0f), -1.0f, 1.5f);
    const float WaterReflectionDiagnostic = FMath::Clamp(
        DiagnosticFloat(TEXT("waterreflection="), -1.0f), -1.0f, 1.0f);
    const float WaterEmissiveDiagnostic = FMath::Clamp(
        DiagnosticFloat(TEXT("wateremissive="), -1.0f), -1.0f, 0.5f);
    const float WaterVariationDiagnostic = FMath::Clamp(
        DiagnosticFloat(TEXT("watervariation="), -1.0f), -1.0f, 1.0f);
    const float WaterOpacityDiagnostic = FMath::Clamp(
        DiagnosticFloat(TEXT("wateropacity="), -1.0f), -1.0f, 1.0f);
    const float SunPitchDiagnostic = FMath::Clamp(
        DiagnosticFloat(TEXT("sunpitch="), 999.0f), -89.0f, 999.0f);
    const float SunYawDiagnostic = FMath::Clamp(
        DiagnosticFloat(TEXT("sunyaw="), 999.0f), -360.0f, 999.0f);
    const bool bWaterInventoryDiagnostic =
        HasDiagnosticMode(TEXT("waterinventory"));
    const FString OutPath =
        FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Screenshots"), Label + TEXT(".png"));

    TWeakObjectPtr<UWorld> WeakWorld(World);

    // Start the crew paddling downstream once the raft has spawned.
    FTimerHandle PaddleHandle;
    World->GetTimerManager().SetTimer(
        PaddleHandle,
        FTimerDelegate::CreateLambda([WeakWorld]()
        {
            if (ARaftSimRaftActor* Raft = FindRaft(WeakWorld.Get()))
            {
                Raft->IssueCrewCommand(ERaftSimCrewCommand::AllForward);
            }
        }),
        1.0f, false);

    FTimerHandle ShotHandle;
    World->GetTimerManager().SetTimer(
        ShotHandle,
        FTimerDelegate::CreateLambda(
            [WeakWorld, OutPath, BackM, UpM, AheadM,
             WaterRoughnessDiagnostic, WaterSpecularDiagnostic,
             WaterNormalDiagnostic, WaterReflectionDiagnostic,
             WaterEmissiveDiagnostic, WaterVariationDiagnostic,
             WaterOpacityDiagnostic, SunPitchDiagnostic, SunYawDiagnostic,
             bWaterInventoryDiagnostic]()
        {
            UWorld* W = WeakWorld.Get();
            if (W != nullptr &&
                (SunPitchDiagnostic < 900.0f || SunYawDiagnostic < 900.0f))
            {
                for (TActorIterator<ADirectionalLight> It(W); It; ++It)
                {
                    ADirectionalLight* Sun = *It;
                    if (!Sun)
                    {
                        continue;
                    }
                    FRotator Rotation = Sun->GetActorRotation();
                    if (SunPitchDiagnostic < 900.0f)
                    {
                        Rotation.Pitch = SunPitchDiagnostic;
                    }
                    if (SunYawDiagnostic < 900.0f)
                    {
                        Rotation.Yaw = SunYawDiagnostic;
                    }
                    Sun->SetActorRotation(Rotation);
                    UE_LOG(
                        LogTemp,
                        Display,
                        TEXT("RaftSim.CaptureRaft: sun diagnostic pitch=%.1f yaw=%.1f"),
                        Rotation.Pitch,
                        Rotation.Yaw);
                    break;
                }
            }
            if (W != nullptr &&
                (WaterRoughnessDiagnostic >= 0.0f ||
                 WaterSpecularDiagnostic >= 0.0f ||
                 WaterNormalDiagnostic >= 0.0f ||
                 WaterReflectionDiagnostic >= 0.0f ||
                 WaterEmissiveDiagnostic >= 0.0f ||
                 WaterVariationDiagnostic >= 0.0f ||
                 WaterOpacityDiagnostic >= 0.0f))
            {
                int32 OverrideComponentCount = 0;
                const FName PhysicalWaterTag(TEXT("RaftSimPhysicalCorridorWater"));
                for (TActorIterator<AActor> It(W); It; ++It)
                {
                    AActor* Actor = *It;
                    if (!Actor || !Actor->ActorHasTag(PhysicalWaterTag))
                    {
                        continue;
                    }
                    TInlineComponentArray<UMeshComponent*> Components(Actor);
                    for (UMeshComponent* Component : Components)
                    {
                        if (!Component || Component->GetNumMaterials() == 0)
                        {
                            continue;
                        }
                        UMaterialInstanceDynamic* Material =
                            Component->CreateDynamicMaterialInstance(0);
                        if (!Material)
                        {
                            continue;
                        }
                        auto SetIfRequested = [Material](
                            const TCHAR* ParameterName, float Value)
                        {
                            if (Value >= 0.0f)
                            {
                                Material->SetScalarParameterValue(
                                    ParameterName, Value);
                            }
                        };
                        SetIfRequested(TEXT("Roughness"), WaterRoughnessDiagnostic);
                        SetIfRequested(TEXT("Specular"), WaterSpecularDiagnostic);
                        SetIfRequested(TEXT("NormalIntensity"), WaterNormalDiagnostic);
                        SetIfRequested(
                            TEXT("ReflectionFillIntensity"),
                            WaterReflectionDiagnostic);
                        SetIfRequested(
                            TEXT("EmissiveFillScale"), WaterEmissiveDiagnostic);
                        SetIfRequested(
                            TEXT("SurfaceVariationStrength"),
                            WaterVariationDiagnostic);
                        SetIfRequested(TEXT("Opacity"), WaterOpacityDiagnostic);
                        ++OverrideComponentCount;
                    }
                }
                UE_LOG(
                    LogTemp,
                    Display,
                    TEXT("RaftSim.CaptureRaft: physical-water diagnostic "
                         "components=%d roughness=%.3f specular=%.3f "
                         "normal=%.3f reflection=%.3f emissive=%.3f "
                         "variation=%.3f opacity=%.3f"),
                    OverrideComponentCount,
                    WaterRoughnessDiagnostic,
                    WaterSpecularDiagnostic,
                    WaterNormalDiagnostic,
                    WaterReflectionDiagnostic,
                    WaterEmissiveDiagnostic,
                    WaterVariationDiagnostic,
                    WaterOpacityDiagnostic);
            }
            if (W != nullptr && bWaterInventoryDiagnostic)
            {
                LogVisibleWaterPresentationInventory(W);
            }
            if (ARaftSimRaftActor* Raft = FindRaft(W))
            {
                const FVector RaftLoc = Raft->GetActorLocation();
                FVector Fwd = Raft->GetActorForwardVector();
                Fwd.Z = 0.0f;
                Fwd = Fwd.GetSafeNormal();
                if (Fwd.IsNearlyZero())
                {
                    Fwd = FVector(1.0f, 0.0f, 0.0f);
                }
                const FVector CamLoc =
                    RaftLoc - Fwd * (BackM * 100.0f) + FVector(0.0f, 0.0f, UpM * 100.0f);
                const FVector LookAt =
                    RaftLoc + Fwd * (AheadM * 100.0f) - FVector(0.0f, 0.0f, 150.0f);
                const FRotator CamRot = (LookAt - CamLoc).Rotation();
                if (ACameraActor* Cam = W->SpawnActor<ACameraActor>(
                        ACameraActor::StaticClass(), CamLoc, CamRot))
                {
                    if (APlayerController* PC = W->GetFirstPlayerController())
                    {
                        PC->SetViewTarget(Cam);
                    }
                }
                UE_LOG(LogTemp, Display, TEXT("RaftSim.CaptureRaft: raft at %s"), *RaftLoc.ToString());
            }
            FScreenshotRequest::RequestScreenshot(OutPath, false, false);

            if (W != nullptr)
            {
                FTimerHandle ExitHandle;
                W->GetTimerManager().SetTimer(
                    ExitHandle,
                    FTimerDelegate::CreateLambda([]() { FPlatformMisc::RequestExit(false); }),
                    4.0f, false);
            }
        }),
        Delay, false);

    UE_LOG(LogTemp, Display, TEXT("RaftSim.CaptureRaft: paddling then shooting in %.1fs -> %s"),
           Delay, *OutPath);
}

static FAutoConsoleCommandWithWorldAndArgs GCaptureRaftCommand(
    TEXT("RaftSim.CaptureRaft"),
    TEXT("Paddle the raft downstream into the rapid, then screenshot over its "
         "shoulder. Usage: RaftSim.CaptureRaft <seconds> [label] [backM] [upM] "
         "[aheadM] [waterroughness=N] [waterspecular=N] [waternormal=N] "
         "[waterreflection=N] [wateremissive=N] [watervariation=N] "
         "[wateropacity=N] [waterinventory] [sunpitch=N] [sunyaw=N]"),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&HandleCaptureRaft));

// Deterministic close-up for M1: place an authoritative D4 rock against the
// port tube, let the fixed-step solve and dynamic mesh settle for a few frames,
// then photograph the actual contact. This is a review/capture hook only; it
// never runs unless explicitly invoked from the console.
static void HandleCaptureWrapTest(const TArray<FString>& Args, UWorld* World)
{
    if (World == nullptr)
    {
        return;
    }
    const FString Label = Args.Num() > 0 ? Args[0] : TEXT("M1_FlexibleRaftWrap");
    const FString OutPath =
        FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Screenshots"), Label + TEXT(".png"));
    TWeakObjectPtr<UWorld> WeakWorld(World);

    FTimerHandle ContactHandle;
    World->GetTimerManager().SetTimer(
        ContactHandle,
        FTimerDelegate::CreateLambda([WeakWorld]()
        {
            UWorld* W = WeakWorld.Get();
            ARaftSimRaftActor* Raft = FindRaft(W);
            if (W == nullptr || Raft == nullptr)
            {
                return;
            }
            const FVector RockWorld = Raft->GetActorTransform().TransformPosition(
                FVector(0.0f, -100.0f, -20.0f));
            if (ARaftSimRockObstacleActor* Rock = W->SpawnActor<ARaftSimRockObstacleActor>(
                    ARaftSimRockObstacleActor::StaticClass(), RockWorld, FRotator::ZeroRotator))
            {
                Rock->ConfigureContact(1.4f, 0.78f);
            }
        }),
        1.0f,
        false);

    FTimerHandle ShotHandle;
    World->GetTimerManager().SetTimer(
        ShotHandle,
        FTimerDelegate::CreateLambda([WeakWorld, OutPath]()
        {
            UWorld* W = WeakWorld.Get();
            if (ARaftSimRaftActor* Raft = FindRaft(W))
            {
                const FVector CamLoc = Raft->GetActorTransform().TransformPosition(
                    FVector(-420.0f, -520.0f, 300.0f));
                const FVector LookAt = Raft->GetActorLocation() + FVector(0.0f, 0.0f, 25.0f);
                if (ACameraActor* Cam = W->SpawnActor<ACameraActor>(
                        ACameraActor::StaticClass(), CamLoc, (LookAt - CamLoc).Rotation()))
                {
                    if (APlayerController* PC = W->GetFirstPlayerController())
                    {
                        PC->SetViewTarget(Cam);
                    }
                }
            }
            if (W != nullptr)
            {
                // Settle eye adaptation, water material history, and dynamic
                // lighting after the rapid teleport and camera cut. Capturing
                // in the same frame as SetViewTarget records a black exposure
                // transient that a player never sees.
                FTimerHandle CaptureHandle;
                W->GetTimerManager().SetTimer(
                    CaptureHandle,
                    FTimerDelegate::CreateLambda([WeakWorld, OutPath]()
                    {
                        if (UWorld* DiagnosticWorld = WeakWorld.Get())
                        {
                            TActorIterator<ARaftSimWaterVfxActor> VfxIt(DiagnosticWorld);
                            const APlayerController* PC =
                                DiagnosticWorld->GetFirstPlayerController();
                            const APlayerCameraManager* Camera =
                                PC ? PC->PlayerCameraManager : nullptr;
                            UE_LOG(
                                LogTemp,
                                Display,
                                TEXT("RaftSim.CaptureWrapTest: captureCamera=%s "
                                     "underwater=%.3f blend=%.3f"),
                                Camera
                                    ? *Camera->GetCameraLocation().ToCompactString()
                                    : TEXT("unavailable"),
                                VfxIt ? VfxIt->GetLastPresentationState().Underwater : -1.0f,
                                VfxIt ? VfxIt->GetUnderwaterBlendWeight() : -1.0f);
                        }
                        FScreenshotRequest::RequestScreenshot(OutPath, false, false);
                        if (UWorld* CaptureWorld = WeakWorld.Get())
                        {
                            FTimerHandle ExitHandle;
                            CaptureWorld->GetTimerManager().SetTimer(
                                ExitHandle,
                                FTimerDelegate::CreateLambda([]()
                                {
                                    FPlatformMisc::RequestExit(false);
                                }),
                                4.0f,
                                false);
                        }
                    }),
                    1.0f,
                    false);
            }
        }),
        1.2f,
        false);
}

static FAutoConsoleCommandWithWorldAndArgs GCaptureWrapTestCommand(
    TEXT("RaftSim.CaptureWrapTest"),
    TEXT("Place an authoritative D4 rock against the raft and capture the visibly "
         "deformed tube. Usage: RaftSim.CaptureWrapTest [label]"),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&HandleCaptureWrapTest));

// Named-rapid production evidence: reset the live solver to the authoritative
// Meat Grinder crop, place the real raft at the sampled free surface, then let
// a D4-authoritative contact boulder drive the normal contact path. Its visible
// shell prefers the rights-reviewed CC0 scan used by the South Fork corridor and
// retains a project-owned procedural fallback. Nothing here fabricates mesh
// deformation or VFX state; the command only stages a bounded, reproducible
// review scenario that is never active during ordinary gameplay.
static int32 HideBreakingWaterPresentationComponents(
    UWorld* World,
    bool bHideLip,
    bool bHideRoller)
{
    if (World == nullptr || (!bHideLip && !bHideRoller))
    {
        return 0;
    }
    int32 HiddenComponentCount = 0;
    for (TActorIterator<ARaftSimWaterSurfaceActor> It(World); It; ++It)
    {
        TInlineComponentArray<UProceduralMeshComponent*> Components(*It);
        for (UProceduralMeshComponent* Component : Components)
        {
            const bool bHideLipComponent = Component && bHideLip &&
                Component->GetName() == TEXT("BreakingLipMesh");
            const bool bHideRollerComponent = Component && bHideRoller &&
                Component->GetName() == TEXT("BreakingRollerVolumeMesh");
            if (bHideLipComponent || bHideRollerComponent)
            {
                Component->SetVisibility(false, true);
                ++HiddenComponentCount;
            }
        }
    }
    return HiddenComponentCount;
}

static int32 HideRapidNiagaraPresentationComponents(
    UWorld* World,
    bool bHideAerosol,
    bool bHideRoller)
{
    if (World == nullptr || (!bHideAerosol && !bHideRoller))
    {
        return 0;
    }
    int32 HiddenComponentCount = 0;
    for (TActorIterator<ARaftSimWaterVfxActor> It(World); It; ++It)
    {
        TInlineComponentArray<UPrimitiveComponent*> Components(*It);
        for (UPrimitiveComponent* Component : Components)
        {
            const bool bHideAerosolComponent = Component && bHideAerosol &&
                Component->GetName().StartsWith(TEXT("ProductionRapidAerosol_"));
            const bool bHideRollerComponent = Component && bHideRoller &&
                Component->GetName().StartsWith(TEXT("ProductionRapidRoller_"));
            if (bHideAerosolComponent || bHideRollerComponent)
            {
                Component->SetVisibility(false, true);
                ++HiddenComponentCount;
            }
        }
    }
    return HiddenComponentCount;
}

static void HandleCaptureRapidWrapTest(const TArray<FString>& Args, UWorld* World)
{
    if (World == nullptr)
    {
        return;
    }
    const FString Label = Args.Num() > 0 ? Args[0] : TEXT("M9_MeatGrinderD4Wrap");
    const float StationM = Args.Num() > 1
        ? FMath::Clamp(FCString::Atof(*Args[1]), 785.606f, 1145.606f)
        : 960.0f;
    const FString CameraPreset = Args.Num() > 2
        ? Args[2].ToLower()
        : TEXT("upstream_right");
    auto HasDiagnosticMode = [&Args](const TCHAR* Mode)
    {
        for (int32 Index = 3; Index < Args.Num(); ++Index)
        {
            if (Args[Index].Equals(Mode, ESearchCase::IgnoreCase))
            {
                return true;
            }
        }
        return false;
    };
    auto DiagnosticFloat = [&Args](const TCHAR* Prefix, float DefaultValue)
    {
        const FString PrefixString(Prefix);
        for (int32 Index = 3; Index < Args.Num(); ++Index)
        {
            if (Args[Index].StartsWith(PrefixString, ESearchCase::IgnoreCase))
            {
                return FCString::Atof(*Args[Index].RightChop(PrefixString.Len()));
            }
        }
        return DefaultValue;
    };
    auto DiagnosticString = [&Args](const TCHAR* Prefix)
    {
        const FString PrefixString(Prefix);
        for (int32 Index = 3; Index < Args.Num(); ++Index)
        {
            if (Args[Index].StartsWith(PrefixString, ESearchCase::IgnoreCase))
            {
                return Args[Index].RightChop(PrefixString.Len());
            }
        }
        return FString();
    };
    const FVector RockLocalCm(
        FMath::Clamp(DiagnosticFloat(TEXT("rockx="), -100.0f), -180.0f, 180.0f),
        FMath::Clamp(DiagnosticFloat(TEXT("rocky="), -130.0f), -180.0f, 180.0f),
        FMath::Clamp(DiagnosticFloat(TEXT("rockz="), -20.0f), -100.0f, 120.0f));
    const float CameraExposureBias = FMath::Clamp(
        DiagnosticFloat(TEXT("exposure="), 1.25f), -2.0f, 3.0f);
    const float LiveSurfaceCoverageDiagnostic = FMath::Clamp(
        DiagnosticFloat(TEXT("livecoverage="), -1.0f), -1.0f, 0.25f);
    const float LiveWaterRoughnessDiagnostic = FMath::Clamp(
        DiagnosticFloat(TEXT("livewaterroughness="), -1.0f), -1.0f, 0.80f);
    const float LiveWaterSpecularDiagnostic = FMath::Clamp(
        DiagnosticFloat(TEXT("livewaterspecular="), -1.0f), -1.0f, 1.0f);
    const bool bUnlitDiagnostic = HasDiagnosticMode(TEXT("unlit"));
    const bool bHideLiveSurfaceDiagnostic = HasDiagnosticMode(TEXT("nowater"));
    const bool bHideAuthoredWaterDiagnostic =
        HasDiagnosticMode(TEXT("noauthoredwater"));
    const bool bHideContactRockDiagnostic =
        HasDiagnosticMode(TEXT("norockvisual"));
    const bool bHideWaterVfxDiagnostic = HasDiagnosticMode(TEXT("novfx"));
    const bool bHideBreakingLipDiagnostic =
        HasDiagnosticMode(TEXT("nobreakinglip"));
    const bool bHideBreakingRollerDiagnostic =
        HasDiagnosticMode(TEXT("nobreakingroller"));
    const bool bHideRapidAerosolDiagnostic =
        HasDiagnosticMode(TEXT("norapidaerosol"));
    const bool bHideRapidRollerDiagnostic =
        HasDiagnosticMode(TEXT("norapidroller"));
    const bool bHideDetailedTerrainDiagnostic = HasDiagnosticMode(TEXT("noterrain"));
    const bool bHideFarFieldDiagnostic = HasDiagnosticMode(TEXT("nofarfield"));
    const bool bHideDressingDiagnostic = HasDiagnosticMode(TEXT("nodressing"));
    const bool bHideBoulderDressingDiagnostic =
        HasDiagnosticMode(TEXT("noboulderdressing"));
    const bool bWaterInventoryDiagnostic = HasDiagnosticMode(TEXT("waterinventory"));
    const bool bTerrainVertexMacroDiagnostic =
        HasDiagnosticMode(TEXT("terrainvertexmacro"));
    const bool bTerrainNoEdgeBlendDiagnostic =
        HasDiagnosticMode(TEXT("terrainnoedgeblend"));
    const bool bTerrainNoSpecularDiagnostic =
        HasDiagnosticMode(TEXT("terrainnospecular"));
    const float TerrainMacroInfluenceDiagnostic = FMath::Clamp(
        DiagnosticFloat(TEXT("terrainmacro="), -1.0f), -1.0f, 1.0f);
    const float AuthoredWaterDetailDiagnostic = FMath::Clamp(
        DiagnosticFloat(TEXT("waterdetail="), -1.0f), -1.0f, 0.40f);
    const float AuthoredWaterFoamDiagnostic = FMath::Clamp(
        DiagnosticFloat(TEXT("waterfoam="), -1.0f), -1.0f, 2.0f);
    const float AuthoredWaterFoamCoreDiagnostic = FMath::Clamp(
        DiagnosticFloat(TEXT("waterfoamcore="), -1.0f), -1.0f, 2.0f);
    const float AuthoredWaterFoamLaceDiagnostic = FMath::Clamp(
        DiagnosticFloat(TEXT("waterfoamlace="), -1.0f), -1.0f, 2.0f);
    const float AuthoredWaterRoughnessDiagnostic = FMath::Clamp(
        DiagnosticFloat(TEXT("waterroughness="), -1.0f), -1.0f, 0.80f);
    const float AuthoredWaterSpecularDiagnostic = FMath::Clamp(
        DiagnosticFloat(TEXT("waterspecular="), -1.0f), -1.0f, 1.0f);
    const bool bDisableAuthoredWaterShadowDiagnostic =
        HasDiagnosticMode(TEXT("noshadowwater"));
    const bool bHideRiggingDiagnostic = HasDiagnosticMode(TEXT("norigging"));
    const bool bHideRubberDiagnostic = HasDiagnosticMode(TEXT("norubber"));
    const bool bHideTubesDiagnostic = HasDiagnosticMode(TEXT("notubes"));
    const bool bHideFloorDiagnostic = HasDiagnosticMode(TEXT("nofloor"));
    const bool bHideFittingsDiagnostic = HasDiagnosticMode(TEXT("nofittings"));
    auto SetDiagnosticConsoleVariable = [](const TCHAR* Name, int32 Value)
    {
        if (IConsoleVariable* Variable =
                IConsoleManager::Get().FindConsoleVariable(Name))
        {
            // Capture-only renderer comparisons run after the world exists;
            // switching these at startup can race Metal initialization.
            Variable->Set(Value, ECVF_SetByConsole);
        }
    };
    if (HasDiagnosticMode(TEXT("taa")))
    {
        SetDiagnosticConsoleVariable(TEXT("r.AntiAliasingMethod"), 2);
    }
    if (HasDiagnosticMode(TEXT("nobloom")))
    {
        SetDiagnosticConsoleVariable(TEXT("r.BloomQuality"), 0);
    }
    if (HasDiagnosticMode(TEXT("nocloud")))
    {
        SetDiagnosticConsoleVariable(TEXT("r.VolumetricCloud"), 0);
    }
    const bool bReviewedRockDiagnostic = HasDiagnosticMode(TEXT("reviewedrock"));
    const FString ReviewedRockMeshOverridePath =
        DiagnosticString(TEXT("rockmesh="));
    const FString AuthoredWaterMaterialOverridePath =
        DiagnosticString(TEXT("watermaterial="));
    const FString TerrainMaterialOverridePath =
        DiagnosticString(TEXT("terrainmaterial="));
    if (!AuthoredWaterMaterialOverridePath.IsEmpty())
    {
        UMaterialInterface* AuthoredWaterMaterialOverride =
            LoadObject<UMaterialInterface>(
                nullptr, *AuthoredWaterMaterialOverridePath);
        if (AuthoredWaterMaterialOverride == nullptr)
        {
            UE_LOG(
                LogTemp,
                Error,
                TEXT("RaftSim.CaptureRapidWrapTest: water material override "
                     "could not be loaded: %s"),
                *AuthoredWaterMaterialOverridePath);
        }
        else
        {
            const FName AuthoredWaterTag(
                TEXT("RaftSimFlowBand_median_runnable"));
            int32 OverrideComponentCount = 0;
            for (TActorIterator<AActor> It(World); It; ++It)
            {
                AActor* Actor = *It;
                if (!Actor || !Actor->ActorHasTag(AuthoredWaterTag))
                {
                    continue;
                }
                if (UStaticMeshComponent* WaterComponent =
                        Actor->FindComponentByClass<UStaticMeshComponent>())
                {
                    WaterComponent->SetMaterial(
                        0, AuthoredWaterMaterialOverride);
                    ++OverrideComponentCount;
                }
            }
            UE_LOG(
                LogTemp,
                Display,
                TEXT("RaftSim.CaptureRapidWrapTest: waterMaterialOverride=%s "
                     "components=%d"),
                *AuthoredWaterMaterialOverride->GetPathName(),
                OverrideComponentCount);
        }
    }
    if (AuthoredWaterDetailDiagnostic >= 0.0f ||
        AuthoredWaterFoamDiagnostic >= 0.0f ||
        AuthoredWaterFoamCoreDiagnostic >= 0.0f ||
        AuthoredWaterFoamLaceDiagnostic >= 0.0f ||
        AuthoredWaterRoughnessDiagnostic >= 0.0f ||
        AuthoredWaterSpecularDiagnostic >= 0.0f)
    {
        const FName AuthoredWaterTag(TEXT("RaftSimFlowBand_median_runnable"));
        int32 OverrideComponentCount = 0;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            AActor* Actor = *It;
            if (!Actor || !Actor->ActorHasTag(AuthoredWaterTag))
            {
                continue;
            }
            if (UStaticMeshComponent* WaterComponent =
                    Actor->FindComponentByClass<UStaticMeshComponent>())
            {
                if (UMaterialInstanceDynamic* WaterMaterial =
                        WaterComponent->CreateDynamicMaterialInstance(0))
                {
                    // Render-only bracket over the existing flow-normal
                    // texture. Geometry, foam masks, depth, and solver state
                    // remain fixed while short-wave slope strength changes.
                    if (AuthoredWaterDetailDiagnostic >= 0.0f)
                    {
                        WaterMaterial->SetScalarParameterValue(
                            TEXT("CalmRippleStrength"),
                            AuthoredWaterDetailDiagnostic * 0.75f);
                        WaterMaterial->SetScalarParameterValue(
                            TEXT("FlowRippleStrength"),
                            AuthoredWaterDetailDiagnostic);
                        WaterMaterial->SetScalarParameterValue(
                            TEXT("FoamRippleStrength"),
                            AuthoredWaterDetailDiagnostic * 1.35f);
                    }
                    if (AuthoredWaterFoamDiagnostic >= 0.0f)
                    {
                        WaterMaterial->SetScalarParameterValue(
                            TEXT("HydraulicFoamIntensity"),
                            AuthoredWaterFoamDiagnostic);
                    }
                    if (AuthoredWaterFoamCoreDiagnostic >= 0.0f)
                    {
                        WaterMaterial->SetScalarParameterValue(
                            TEXT("HydraulicFoamColorCoreGain"),
                            AuthoredWaterFoamCoreDiagnostic);
                    }
                    if (AuthoredWaterFoamLaceDiagnostic >= 0.0f)
                    {
                        WaterMaterial->SetScalarParameterValue(
                            TEXT("HydraulicFoamColorBreakupGain"),
                            AuthoredWaterFoamLaceDiagnostic);
                    }
                    if (AuthoredWaterRoughnessDiagnostic >= 0.0f)
                    {
                        WaterMaterial->SetScalarParameterValue(
                            TEXT("WaterRoughness"),
                            AuthoredWaterRoughnessDiagnostic);
                    }
                    if (AuthoredWaterSpecularDiagnostic >= 0.0f)
                    {
                        WaterMaterial->SetScalarParameterValue(
                            TEXT("Specular"),
                            AuthoredWaterSpecularDiagnostic);
                    }
                    ++OverrideComponentCount;
                }
            }
        }
        UE_LOG(
            LogTemp,
            Display,
            TEXT("RaftSim.CaptureRapidWrapTest: authored water diagnostic "
                 "components=%d detail=%.3f foam=%.3f core=%.3f lace=%.3f "
                 "roughness=%.3f specular=%.3f"),
            OverrideComponentCount,
            AuthoredWaterDetailDiagnostic,
            AuthoredWaterFoamDiagnostic,
            AuthoredWaterFoamCoreDiagnostic,
            AuthoredWaterFoamLaceDiagnostic,
            AuthoredWaterRoughnessDiagnostic,
            AuthoredWaterSpecularDiagnostic);
    }
    if (!TerrainMaterialOverridePath.IsEmpty())
    {
        UMaterialInterface* TerrainMaterialOverride = LoadObject<UMaterialInterface>(
            nullptr, *TerrainMaterialOverridePath);
        if (TerrainMaterialOverride == nullptr)
        {
            UE_LOG(
                LogTemp,
                Error,
                TEXT("RaftSim.CaptureRapidWrapTest: terrain material override "
                     "could not be loaded: %s"),
                *TerrainMaterialOverridePath);
        }
        else
        {
            const FName DetailedTerrainTag(TEXT("RaftSimFullReachTerrain"));
            int32 OverrideComponentCount = 0;
            for (TActorIterator<AActor> It(World); It; ++It)
            {
                AActor* Actor = *It;
                if (!Actor || !Actor->ActorHasTag(DetailedTerrainTag))
                {
                    continue;
                }
                if (UStaticMeshComponent* TerrainComponent =
                        Actor->FindComponentByClass<UStaticMeshComponent>())
                {
                    TerrainComponent->SetMaterial(0, TerrainMaterialOverride);
                    ++OverrideComponentCount;
                }
            }
            UE_LOG(
                LogTemp,
                Display,
                TEXT("RaftSim.CaptureRapidWrapTest: terrainMaterialOverride=%s "
                     "components=%d"),
                *TerrainMaterialOverride->GetPathName(),
                OverrideComponentCount);
        }
    }
    if (bTerrainVertexMacroDiagnostic || bTerrainNoEdgeBlendDiagnostic ||
        bTerrainNoSpecularDiagnostic || TerrainMacroInfluenceDiagnostic >= 0.0f)
    {
        const FName DetailedTerrainTag(TEXT("RaftSimFullReachTerrain"));
        int32 OverrideComponentCount = 0;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            AActor* Actor = *It;
            if (!Actor || !Actor->ActorHasTag(DetailedTerrainTag))
            {
                continue;
            }
            if (UStaticMeshComponent* TerrainComponent =
                    Actor->FindComponentByClass<UStaticMeshComponent>())
            {
                if (UMaterialInstanceDynamic* TerrainMaterial =
                        TerrainComponent->CreateDynamicMaterialInstance(0))
                {
                    if (bTerrainVertexMacroDiagnostic)
                    {
                        TerrainMaterial->SetScalarParameterValue(
                            TEXT("UseSourceMacroTexture"), 0.0f);
                    }
                    if (bTerrainNoEdgeBlendDiagnostic)
                    {
                        TerrainMaterial->SetScalarParameterValue(
                            TEXT("UseCorridorEdgeBlend"), 0.0f);
                    }
                    if (bTerrainNoSpecularDiagnostic)
                    {
                        TerrainMaterial->SetScalarParameterValue(
                            TEXT("TerrainSpecular"), 0.0f);
                    }
                    if (TerrainMacroInfluenceDiagnostic >= 0.0f)
                    {
                        // Presentation A/B only: source hue and geometry stay
                        // fixed while reviewers bracket how much sub-meter
                        // ground detail survives the registered aerial blend.
                        TerrainMaterial->SetScalarParameterValue(
                            TEXT("SourceMacroInfluence"),
                            TerrainMacroInfluenceDiagnostic);
                    }
                    ++OverrideComponentCount;
                }
            }
        }
        UE_LOG(
            LogTemp,
            Display,
            TEXT("RaftSim.CaptureRapidWrapTest: terrain parameter diagnostic "
                 "components=%d vertexMacro=%d noEdgeBlend=%d noSpecular=%d "
                 "macroInfluence=%.3f"),
            OverrideComponentCount,
            bTerrainVertexMacroDiagnostic ? 1 : 0,
            bTerrainNoEdgeBlendDiagnostic ? 1 : 0,
            bTerrainNoSpecularDiagnostic ? 1 : 0,
            TerrainMacroInfluenceDiagnostic);
    }
    const FString OutPath =
        FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Screenshots"), Label + TEXT(".png"));
    TWeakObjectPtr<UWorld> WeakWorld(World);

    FTimerHandle PrepareHandle;
    World->GetTimerManager().SetTimer(
        PrepareHandle,
        FTimerDelegate::CreateLambda([WeakWorld, StationM]()
        {
            UWorld* W = WeakWorld.Get();
            ARaftSimRaftActor* Raft = FindRaft(W);
            UGameInstance* GameInstance = W ? W->GetGameInstance() : nullptr;
            URaftSimPhysicsBridgeSubsystem* Bridge = GameInstance
                ? GameInstance->GetSubsystem<URaftSimPhysicsBridgeSubsystem>()
                : nullptr;
            URaftSimWaterRuntimeAdapter* Water = Bridge ? Bridge->GetWaterRuntime() : nullptr;
            if (Raft == nullptr || Water == nullptr)
            {
                UE_LOG(LogTemp, Error, TEXT("RaftSim.CaptureRapidWrapTest: runtime unavailable"));
                return;
            }
            // Lock this evidence recipe to one shipping presentation preset.
            // The ordinary game still selects/cycles all three weather states;
            // clear morning keeps wet fabric, deformation, and contact
            // geometry legible after the authored water's reflection and
            // foam response have been bounded for the high-energy tile.
            if (GEngine != nullptr)
            {
                GEngine->Exec(W, TEXT("RaftSim.SetWeather clear_morning"));
            }
            static const FString MeatGrinderCooked = TEXT(
                "physics/data/real_world/south_fork_american_chili_bar/"
                "full_hydraulics/rapids/meat_grinder/cooked");
            if (!Water->ConfigureRiverWindow(
                    MeatGrinderCooked,
                    TEXT("median_runnable"),
                    FVector2D(StationM, 0.0f),
                    FVector2D(200.0f, 40.0f),
                    0.039f,
                    /*bRecenterHydraulicCrux=*/false))
            {
                UE_LOG(LogTemp, Error, TEXT("RaftSim.CaptureRapidWrapTest: Meat Grinder window failed"));
                return;
            }

            FVector RiverBaseCm;
            if (!Water->RiverToWorldPosition(
                    FVector2D(StationM, 0.0f), Water->GetRiverVerticalDatumM(), RiverBaseCm))
            {
                UE_LOG(LogTemp, Error, TEXT("RaftSim.CaptureRapidWrapTest: station mapping failed"));
                return;
            }
            FRaftSimWaterSample Sample;
            if (!Water->SampleWaterAtWorldPosition(RiverBaseCm, Sample) || !Sample.bWet)
            {
                UE_LOG(LogTemp, Error, TEXT("RaftSim.CaptureRapidWrapTest: station sample is dry"));
                return;
            }
            FVector2D RiverCoordinates;
            FVector Tangent;
            FVector LeftNormal;
            Water->WorldToRiverCoordinates(RiverBaseCm, RiverCoordinates, Tangent, LeftNormal);
            RiverBaseCm.Z = Sample.SurfaceHeightMeters * 100.0f + 6.0f;
            const FRotator Downstream = Tangent.GetSafeNormal2D().Rotation();
            Raft->SetCheckpointTransform(FTransform(Downstream, RiverBaseCm), true);
            Raft->ResetMotionForTesting();
            Raft->IssueCrewCommand(ERaftSimCrewCommand::HighSide);
            UE_LOG(
                LogTemp,
                Display,
                TEXT("RaftSim.CaptureRapidWrapTest: station=%.3f depth=%.3f speed=%.3f surfaceZ=%.1f"),
                StationM,
                Sample.DepthMeters,
                Sample.VelocityMetersPerSecond.Size(),
                RiverBaseCm.Z);
        }),
        0.35f,
        false);

    FTimerHandle ContactHandle;
    World->GetTimerManager().SetTimer(
        ContactHandle,
        FTimerDelegate::CreateLambda(
            [WeakWorld, RockLocalCm, bReviewedRockDiagnostic,
             ReviewedRockMeshOverridePath]()
        {
            UWorld* W = WeakWorld.Get();
            ARaftSimRaftActor* Raft = FindRaft(W);
            if (W == nullptr || Raft == nullptr)
            {
                return;
            }
            const FVector RockWorld = Raft->GetActorTransform().TransformPosition(
                RockLocalCm);
            if (ARaftSimRockObstacleActor* Rock = W->SpawnActor<ARaftSimRockObstacleActor>(
                    ARaftSimRockObstacleActor::StaticClass(), RockWorld, FRotator(8.0f, 27.0f, -5.0f)))
            {
                if (bReviewedRockDiagnostic && !ReviewedRockMeshOverridePath.IsEmpty())
                {
                    if (UStaticMesh* ReviewedRockMeshOverride =
                            LoadObject<UStaticMesh>(
                                nullptr, *ReviewedRockMeshOverridePath))
                    {
                        Rock->SetReviewedVisualMeshForDiagnostics(
                            ReviewedRockMeshOverride);
                        UE_LOG(
                            LogTemp,
                            Display,
                            TEXT("RaftSim.CaptureRapidWrapTest: "
                                 "rockMeshOverride=%s"),
                            *ReviewedRockMeshOverride->GetPathName());
                    }
                    else
                    {
                        UE_LOG(
                            LogTemp,
                            Error,
                            TEXT("RaftSim.CaptureRapidWrapTest: rock mesh "
                                 "override could not be loaded: %s"),
                            *ReviewedRockMeshOverridePath);
                    }
                }
                Rock->ConfigureContact(1.20f, 0.82f);
                Rock->SetPreferReviewedVisual(bReviewedRockDiagnostic);
                UE_LOG(
                    LogTemp,
                    Display,
                    TEXT("RaftSim.CaptureRapidWrapTest: contactLocalCm=%s"),
                    *RockLocalCm.ToCompactString());
            }
        }),
        0.75f,
        false);

    FTimerHandle ShotHandle;
    World->GetTimerManager().SetTimer(
        ShotHandle,
        FTimerDelegate::CreateLambda(
            [WeakWorld, OutPath, CameraPreset, CameraExposureBias, bUnlitDiagnostic,
             bHideLiveSurfaceDiagnostic, bHideWaterVfxDiagnostic,
             bHideAuthoredWaterDiagnostic, bHideContactRockDiagnostic,
             bHideDetailedTerrainDiagnostic, bHideFarFieldDiagnostic,
             bHideDressingDiagnostic, bHideBoulderDressingDiagnostic,
             bWaterInventoryDiagnostic,
             bDisableAuthoredWaterShadowDiagnostic,
             bHideRiggingDiagnostic, bHideRubberDiagnostic,
             bHideTubesDiagnostic, bHideFloorDiagnostic,
             bHideFittingsDiagnostic, bHideBreakingLipDiagnostic,
             bHideBreakingRollerDiagnostic, bHideRapidAerosolDiagnostic,
             bHideRapidRollerDiagnostic, LiveSurfaceCoverageDiagnostic,
             LiveWaterRoughnessDiagnostic, LiveWaterSpecularDiagnostic]()
        {
            UWorld* W = WeakWorld.Get();
            if (bUnlitDiagnostic && GEngine != nullptr && W != nullptr)
            {
                GEngine->Exec(W, TEXT("viewmode unlit"));
            }
            if (W != nullptr &&
                (bHideRapidAerosolDiagnostic || bHideRapidRollerDiagnostic))
            {
                const int32 HiddenRapidNiagaraComponentCount =
                    HideRapidNiagaraPresentationComponents(
                        W,
                        bHideRapidAerosolDiagnostic,
                        bHideRapidRollerDiagnostic);
                UE_LOG(
                    LogTemp,
                    Display,
                    TEXT("RaftSim.CaptureRapidWrapTest: hidden rapid Niagara "
                         "components=%d aerosol=%d roller=%d"),
                    HiddenRapidNiagaraComponentCount,
                    bHideRapidAerosolDiagnostic ? 1 : 0,
                    bHideRapidRollerDiagnostic ? 1 : 0);
            }
            if (W != nullptr && bHideLiveSurfaceDiagnostic)
            {
                for (TActorIterator<ARaftSimWaterSurfaceActor> It(W); It; ++It)
                {
                    It->SetActorHiddenInGame(true);
                }
            }
            if (W != nullptr && bHideAuthoredWaterDiagnostic)
            {
                int32 HiddenAuthoredWaterActors = 0;
                for (TActorIterator<AActor> It(W); It; ++It)
                {
                    AActor* Actor = *It;
                    if (!Actor)
                    {
                        continue;
                    }
                    bool bAuthoredWater = false;
                    for (const FName& Tag : Actor->Tags)
                    {
                        const FString TagString = Tag.ToString();
                        if (TagString.StartsWith(TEXT("RaftSimFlowBand_")) ||
                            Tag == TEXT("RaftSimSolverFoamOverlay"))
                        {
                            bAuthoredWater = true;
                            break;
                        }
                    }
                    if (bAuthoredWater)
                    {
                        Actor->SetActorHiddenInGame(true);
                        ++HiddenAuthoredWaterActors;
                    }
                }
                UE_LOG(
                    LogTemp,
                    Display,
                    TEXT("RaftSim.CaptureRapidWrapTest: hidden authored-water actors=%d"),
                    HiddenAuthoredWaterActors);
            }
            if (W != nullptr && bHideContactRockDiagnostic)
            {
                int32 HiddenContactRocks = 0;
                for (TActorIterator<ARaftSimRockObstacleActor> It(W); It; ++It)
                {
                    It->SetActorHiddenInGame(true);
                    ++HiddenContactRocks;
                }
                UE_LOG(
                    LogTemp,
                    Display,
                    TEXT("RaftSim.CaptureRapidWrapTest: hidden contact rocks=%d"),
                    HiddenContactRocks);
            }
            if (W != nullptr &&
                (bHideBreakingLipDiagnostic || bHideBreakingRollerDiagnostic))
            {
                const int32 HiddenBreakingComponentCount =
                    HideBreakingWaterPresentationComponents(
                        W,
                        bHideBreakingLipDiagnostic,
                        bHideBreakingRollerDiagnostic);
                UE_LOG(
                    LogTemp,
                    Display,
                    TEXT("RaftSim.CaptureRapidWrapTest: hidden breaking-water "
                         "components=%d lip=%d roller=%d"),
                    HiddenBreakingComponentCount,
                    bHideBreakingLipDiagnostic ? 1 : 0,
                    bHideBreakingRollerDiagnostic ? 1 : 0);
            }
            if (W != nullptr &&
                (LiveSurfaceCoverageDiagnostic >= 0.0f ||
                 LiveWaterRoughnessDiagnostic >= 0.0f ||
                 LiveWaterSpecularDiagnostic >= 0.0f))
            {
                int32 OverrideComponentCount = 0;
                for (TActorIterator<ARaftSimWaterSurfaceActor> It(W); It; ++It)
                {
                    TInlineComponentArray<UProceduralMeshComponent*> Components(*It);
                    for (UProceduralMeshComponent* Component : Components)
                    {
                        if (!Component ||
                            Component->GetName() != TEXT("SurfaceMesh"))
                        {
                            continue;
                        }
                        if (UMaterialInstanceDynamic* Material =
                                Cast<UMaterialInstanceDynamic>(
                                    Component->GetMaterial(0)))
                        {
                            if (LiveSurfaceCoverageDiagnostic >= 0.0f)
                            {
                                Material->SetScalarParameterValue(
                                    TEXT("ActiveLiveSurfaceCoverage"),
                                    LiveSurfaceCoverageDiagnostic);
                            }
                            if (LiveWaterRoughnessDiagnostic >= 0.0f)
                            {
                                Material->SetScalarParameterValue(
                                    TEXT("LiveWaterRoughness"),
                                    LiveWaterRoughnessDiagnostic);
                            }
                            if (LiveWaterSpecularDiagnostic >= 0.0f)
                            {
                                Material->SetScalarParameterValue(
                                    TEXT("LiveWaterSpecular"),
                                    LiveWaterSpecularDiagnostic);
                            }
                            ++OverrideComponentCount;
                        }
                    }
                }
                UE_LOG(
                    LogTemp,
                    Display,
                    TEXT("RaftSim.CaptureRapidWrapTest: live surface diagnostic "
                         "coverage=%.3f roughness=%.3f specular=%.3f "
                         "components=%d"),
                    LiveSurfaceCoverageDiagnostic,
                    LiveWaterRoughnessDiagnostic,
                    LiveWaterSpecularDiagnostic,
                    OverrideComponentCount);
            }
            if (W != nullptr && bHideWaterVfxDiagnostic)
            {
                for (TActorIterator<ARaftSimWaterVfxActor> It(W); It; ++It)
                {
                    It->SetActorHiddenInGame(true);
                }
            }
            if (W != nullptr && bHideBoulderDressingDiagnostic)
            {
                const FName DressingTag(TEXT("RaftSimFullReachDressing"));
                const FName FarFieldDressingTag(
                    TEXT("RaftSimFullReachFarFieldDressing"));
                for (TActorIterator<AActor> It(W); It; ++It)
                {
                    AActor* Actor = *It;
                    if (!Actor ||
                        (!Actor->ActorHasTag(DressingTag) &&
                         !Actor->ActorHasTag(FarFieldDressingTag)))
                    {
                        continue;
                    }
                    TInlineComponentArray<
                        UHierarchicalInstancedStaticMeshComponent*> Components(Actor);
                    for (UHierarchicalInstancedStaticMeshComponent* Component : Components)
                    {
                        if (Component &&
                            (Component->GetName().Contains(TEXT("Boulder")) ||
                             Component->GetName().Contains(TEXT("Rock"))))
                        {
                            Component->SetVisibility(false, true);
                        }
                    }
                }
            }
            if (W != nullptr &&
                (bHideDetailedTerrainDiagnostic || bHideFarFieldDiagnostic ||
                 bHideDressingDiagnostic ||
                 bDisableAuthoredWaterShadowDiagnostic))
            {
                const FName DetailedTerrainTag(TEXT("RaftSimFullReachTerrain"));
                const FName FarFieldTag(TEXT("RaftSimFullReachFarField"));
                const FName DressingTag(TEXT("RaftSimFullReachDressing"));
                const FName FarFieldDressingTag(
                    TEXT("RaftSimFullReachFarFieldDressing"));
                const FName AuthoredWaterTag(TEXT("RaftSimFlowBand_median_runnable"));
                for (TActorIterator<AActor> It(W); It; ++It)
                {
                    AActor* Actor = *It;
                    const bool bHide = Actor &&
                        ((bHideDetailedTerrainDiagnostic &&
                          Actor->ActorHasTag(DetailedTerrainTag)) ||
                         (bHideFarFieldDiagnostic &&
                          Actor->ActorHasTag(FarFieldTag)) ||
                         (bHideDressingDiagnostic &&
                          (Actor->ActorHasTag(DressingTag) ||
                           Actor->ActorHasTag(FarFieldDressingTag))));
                    if (bHide)
                    {
                        Actor->SetActorHiddenInGame(true);
                    }
                    if (Actor && bDisableAuthoredWaterShadowDiagnostic &&
                        Actor->ActorHasTag(AuthoredWaterTag))
                    {
                        if (UStaticMeshComponent* WaterComponent =
                                Actor->FindComponentByClass<UStaticMeshComponent>())
                        {
                            WaterComponent->SetCastShadow(false);
                        }
                    }
                }
            }
            if (W != nullptr && bWaterInventoryDiagnostic)
            {
                LogVisibleWaterPresentationInventory(W);
            }
            if (ARaftSimRaftActor* Raft = FindRaft(W))
            {
                if (UProceduralMeshComponent* RaftMesh =
                        Raft->FindComponentByClass<UProceduralMeshComponent>())
                {
                    RaftMesh->SetMeshSectionVisible(0, !bHideTubesDiagnostic);
                    RaftMesh->SetMeshSectionVisible(1, !bHideFloorDiagnostic);
                    RaftMesh->SetMeshSectionVisible(2, !bHideRiggingDiagnostic);
                    RaftMesh->SetMeshSectionVisible(3, !bHideFittingsDiagnostic);
                    RaftMesh->SetMeshSectionVisible(4, !bHideRubberDiagnostic);
                }
                FVector CamLoc;
                FRotator CamRot;
                ResolveRapidEvidenceCameraPose(*Raft, CameraPreset, CamLoc, CamRot);
                if (ACameraActor* Cam = W->SpawnActor<ACameraActor>(
                        ACameraActor::StaticClass(), CamLoc, CamRot))
                {
                    UCameraComponent* CameraComponent = Cam->GetCameraComponent();
                    CameraComponent->SetFieldOfView(
                        CameraPreset == TEXT("particle_macro")
                            ? 42.0f
                            : (CameraPreset == TEXT("contact_port")
                                ? 54.0f
                                : (CameraPreset == TEXT("river_action") ? 62.0f : 56.0f)));
                    RaftSimCameraPresentation::Configure(
                        CameraComponent, CameraExposureBias);
                    if (APlayerController* PC = W->GetFirstPlayerController())
                    {
                        PC->SetViewTarget(Cam);
                    }
                }
                UE_LOG(
                    LogTemp,
                    Display,
                    TEXT("RaftSim.CaptureRapidWrapTest: contacts=%d wrapping=%d "
                         "pinned=%d recovering=%d indentation=%.3f wetness=%.3f "
                         "raftZ=%.1f rotation=%s"),
                    Raft->GetActiveWaterContactCount(),
                    Raft->GetWrappingRockContactCount(),
                    Raft->GetPinnedRockObstacleCount(),
                    Raft->GetRecoveringRockContactCount(),
                    Raft->GetMaximumWaterContactIndentationM(),
                    Raft->GetSurfaceWetness(),
                    Raft->GetActorLocation().Z,
                    *Raft->GetActorRotation().ToCompactString());
                FVector DominantContactWorldCm;
                FVector DominantContactNormal;
                float DominantContactIndentationM = 0.0f;
                if (Raft->GetDominantWaterContactPresentation(
                        DominantContactWorldCm,
                        DominantContactNormal,
                        DominantContactIndentationM))
                {
                    UE_LOG(
                        LogTemp,
                        Display,
                        TEXT("RaftSim.CaptureRapidWrapTest: dominantContact localCm=%s "
                             "normalWorld=%s indentation=%.3f"),
                        *Raft->GetActorTransform().InverseTransformPosition(
                            DominantContactWorldCm).ToCompactString(),
                        *DominantContactNormal.ToCompactString(),
                        DominantContactIndentationM);
                }
            }
            if (W != nullptr)
            {
                const FName AuthoredWaterTag(
                    TEXT("RaftSimFlowBand_median_runnable"));
                int32 AuthoredWaterComponentCount = 0;
                int32 AuthoredWaterShadowCount = 0;
                for (TActorIterator<AActor> It(W); It; ++It)
                {
                    AActor* Actor = *It;
                    if (!Actor || !Actor->ActorHasTag(AuthoredWaterTag))
                    {
                        continue;
                    }
                    if (const UStaticMeshComponent* WaterComponent =
                            Actor->FindComponentByClass<UStaticMeshComponent>())
                    {
                        ++AuthoredWaterComponentCount;
                        AuthoredWaterShadowCount += WaterComponent->CastShadow ? 1 : 0;
                    }
                }
                UE_LOG(
                    LogTemp,
                    Display,
                    TEXT("RaftSim.CaptureRapidWrapTest: authoredWater=%d "
                         "shadowCasting=%d"),
                    AuthoredWaterComponentCount,
                    AuthoredWaterShadowCount);
                TActorIterator<ARaftSimWaterVfxActor> VfxIt(W);
                if (VfxIt)
                {
                    const FRaftSimWaterVfxState& Vfx = VfxIt->GetLastPresentationState();
                    UE_LOG(
                        LogTemp,
                        Display,
                        TEXT("RaftSim.CaptureRapidWrapTest: spray=%.3f mist=%.3f "
                             "sheet=%.3f droplets=%.3f instances=%d/%d/%d/%d "
                             "contactPatchTriangles=%d contactPatchVisible=%d "
                             "connectedV6Triangles=%d connectedV6Visible=%d "
                             "connectedV7Triangles=%d connectedV7Visible=%d "
                             "connectedV8Triangles=%d connectedV8Visible=%d "
                             "depthV10Triangles=%d depthV10Visible=%d "
                             "depthV10Frames=%d depthV10Frame=%d "
                             "depthV10DepthCm=%.2f "
                             "productionNiagara=%d rapidRollerEmitters=%d"),
                        Vfx.Spray,
                        Vfx.Mist,
                        Vfx.ImpactSheet,
                        Vfx.Droplets,
                        VfxIt->GetSprayInstanceCount(),
                        VfxIt->GetMistInstanceCount(),
                        VfxIt->GetImpactFoamInstanceCount(),
                        VfxIt->GetDropletInstanceCount(),
                        VfxIt->GetContactWaterPatchTriangleCount(),
                        VfxIt->IsContactWaterPatchVisible() ? 1 : 0,
                        VfxIt->GetConnectedContactWaterV6TriangleCount(),
                        VfxIt->IsConnectedContactWaterV6Visible() ? 1 : 0,
                        VfxIt->GetConnectedContactWaterV7TriangleCount(),
                        VfxIt->IsConnectedContactWaterV7Visible() ? 1 : 0,
                        VfxIt->GetConnectedContactWaterV8TriangleCount(),
                        VfxIt->IsConnectedContactWaterV8Visible() ? 1 : 0,
                        VfxIt->GetDepthBearingContactWaterV10TriangleCount(),
                        VfxIt->IsDepthBearingContactWaterV10Visible() ? 1 : 0,
                        VfxIt->GetDepthBearingContactWaterV10CachedFrameCount(),
                        VfxIt->GetDepthBearingContactWaterV10CurrentFrame(),
                        VfxIt->GetDepthBearingContactWaterV10DepthCm(),
                        VfxIt->GetProductionNiagaraComponentCount(),
                        VfxIt->GetActiveRapidRollerNiagaraCount());
                }
            }
            if (W != nullptr)
            {
                FTimerHandle CaptureHandle;
                W->GetTimerManager().SetTimer(
                    CaptureHandle,
                    FTimerDelegate::CreateLambda(
                        [WeakWorld, OutPath, CameraPreset,
                         bHideBreakingLipDiagnostic,
                         bHideBreakingRollerDiagnostic,
                         bHideRapidAerosolDiagnostic,
                         bHideRapidRollerDiagnostic]()
                    {
                        if (UWorld* DiagnosticWorld = WeakWorld.Get())
                        {
                            // The live surface rebuilds at 15 Hz and may have
                            // recreated a component after the preparation
                            // callback. Reapply the requested visibility in
                            // this exact screenshot callback so isolation
                            // evidence cannot race the presentation refresh.
                            HideBreakingWaterPresentationComponents(
                                DiagnosticWorld,
                                bHideBreakingLipDiagnostic,
                                bHideBreakingRollerDiagnostic);
                            HideRapidNiagaraPresentationComponents(
                                DiagnosticWorld,
                                bHideRapidAerosolDiagnostic,
                                bHideRapidRollerDiagnostic);
                            APlayerController* MutablePC =
                                DiagnosticWorld->GetFirstPlayerController();
                            ARaftSimRaftActor* CurrentRaft = FindRaft(DiagnosticWorld);
                            ACameraActor* EvidenceCamera = MutablePC
                                ? Cast<ACameraActor>(MutablePC->GetViewTarget())
                                : nullptr;
                            if (CurrentRaft != nullptr && EvidenceCamera != nullptr)
                            {
                                FVector CameraLocation;
                                FRotator CameraRotation;
                                ResolveRapidEvidenceCameraPose(
                                    *CurrentRaft,
                                    CameraPreset,
                                    CameraLocation,
                                    CameraRotation);
                                if (CameraPreset.StartsWith(TEXT("breaking_water")))
                                {
                                    ResolveBreakingWaterEvidenceCameraPose(
                                        DiagnosticWorld,
                                        *CurrentRaft,
                                        CameraPreset,
                                        CameraLocation,
                                        CameraRotation);
                                }
                                EvidenceCamera->SetActorLocationAndRotation(
                                    CameraLocation,
                                    CameraRotation);
                                // Timers execute after the player camera's
                                // normal update. Force the moved evidence
                                // camera through the manager before the
                                // screenshot request so the captured frame and
                                // logged pose cannot lag one tick behind.
                                if (MutablePC->PlayerCameraManager)
                                {
                                    MutablePC->PlayerCameraManager->UpdateCamera(0.0f);
                                }
                            }
                            if (CurrentRaft != nullptr)
                            {
                                UE_LOG(
                                    LogTemp,
                                    Display,
                                    TEXT("RaftSim.CaptureRapidWrapTest: finalFrame "
                                         "contacts=%d wrapping=%d pinned=%d "
                                         "recovering=%d indentation=%.3f "
                                         "wetness=%.3f raft=%s"),
                                    CurrentRaft->GetActiveWaterContactCount(),
                                    CurrentRaft->GetWrappingRockContactCount(),
                                    CurrentRaft->GetPinnedRockObstacleCount(),
                                    CurrentRaft->GetRecoveringRockContactCount(),
                                    CurrentRaft->GetMaximumWaterContactIndentationM(),
                                    CurrentRaft->GetSurfaceWetness(),
                                    *CurrentRaft->GetActorLocation().ToCompactString());
                            }
                            TActorIterator<ARaftSimWaterVfxActor> VfxIt(DiagnosticWorld);
                            const APlayerController* PC =
                                DiagnosticWorld->GetFirstPlayerController();
                            const APlayerCameraManager* Camera =
                                PC ? PC->PlayerCameraManager : nullptr;
                            UE_LOG(
                                LogTemp,
                                Display,
                                TEXT("RaftSim.CaptureRapidWrapTest: captureCamera=%s "
                                     "underwater=%.3f blend=%.3f"),
                                Camera
                                    ? *Camera->GetCameraLocation().ToCompactString()
                                    : TEXT("unavailable"),
                                VfxIt ? VfxIt->GetLastPresentationState().Underwater : -1.0f,
                                VfxIt ? VfxIt->GetUnderwaterBlendWeight() : -1.0f);
                            for (TActorIterator<ARaftSimWaterSurfaceActor> It(DiagnosticWorld); It; ++It)
                            {
                                const FBox Bounds = It->GetComponentsBoundingBox(true);
                                UE_LOG(
                                    LogTemp,
                                    Display,
                                    TEXT("RaftSim.CaptureRapidWrapTest: liveSurface center=%s "
                                         "size=%s breakingLipTriangles=%d "
                                         "breakingLipVisible=%d "
                                         "breakingRollerTriangles=%d "
                                         "breakingRollerVisible=%d"),
                                    *Bounds.GetCenter().ToCompactString(),
                                    *Bounds.GetSize().ToCompactString(),
                                    It->GetBreakingLipTriangleCount(),
                                    It->IsBreakingLipVisible() ? 1 : 0,
                                    It->GetBreakingRollerVolumeTriangleCount(),
                                    It->IsBreakingRollerVolumeVisible() ? 1 : 0);
                            }
                            for (TActorIterator<ARaftSimRockObstacleActor> It(DiagnosticWorld); It; ++It)
                            {
                                const FBox Bounds = It->GetComponentsBoundingBox(true);
                                const FVector RockRelativeToRaftCm = CurrentRaft
                                    ? CurrentRaft->GetActorTransform().InverseTransformPosition(
                                          It->GetActorLocation())
                                    : FVector::ZeroVector;
                                UE_LOG(
                                    LogTemp,
                                    Display,
                                    TEXT("RaftSim.CaptureRapidWrapTest: rock center=%s size=%s "
                                         "relativeToRaftCm=%s"),
                                    *Bounds.GetCenter().ToCompactString(),
                                    *Bounds.GetSize().ToCompactString(),
                                    *RockRelativeToRaftCm.ToCompactString());
                                if (const UProceduralMeshComponent* ProceduralRock =
                                        It->FindComponentByClass<UProceduralMeshComponent>())
                                {
                                    const UMaterialInterface* Material =
                                        ProceduralRock->GetMaterial(0);
                                    UE_LOG(
                                        LogTemp,
                                        Display,
                                        TEXT("RaftSim.CaptureRapidWrapTest: "
                                             "proceduralRock visible=%d section0=%d "
                                             "material=%s center=%s extent=%s"),
                                        ProceduralRock->IsVisible() ? 1 : 0,
                                        ProceduralRock->IsMeshSectionVisible(0) ? 1 : 0,
                                        Material
                                            ? *Material->GetPathName()
                                            : TEXT("unavailable"),
                                        *ProceduralRock->Bounds.Origin.ToCompactString(),
                                        *ProceduralRock->Bounds.BoxExtent.ToCompactString());
                                }
                                TArray<UStaticMeshComponent*> StaticRockComponents;
                                It->GetComponents(StaticRockComponents);
                                for (const UStaticMeshComponent* Component : StaticRockComponents)
                                {
                                    UE_LOG(
                                        LogTemp,
                                        Display,
                                        TEXT("RaftSim.CaptureRapidWrapTest: rockVisual=%s "
                                             "visible=%d registered=%d renderState=%d "
                                             "shouldRender=%d hiddenInGame=%d ownerHidden=%d "
                                             "materialSlots=%d center=%s extent=%s"),
                                        Component ? *Component->GetName() : TEXT("unavailable"),
                                        Component && Component->IsVisible() ? 1 : 0,
                                        Component && Component->IsRegistered() ? 1 : 0,
                                        Component && Component->IsRenderStateCreated() ? 1 : 0,
                                        Component && Component->ShouldRender() ? 1 : 0,
                                        Component && Component->bHiddenInGame ? 1 : 0,
                                        Component && Component->GetOwner() &&
                                                Component->GetOwner()->IsHidden()
                                            ? 1
                                            : 0,
                                        Component ? Component->GetNumMaterials() : 0,
                                        Component
                                            ? *Component->Bounds.Origin.ToCompactString()
                                            : TEXT("unavailable"),
                                        Component
                                            ? *Component->Bounds.BoxExtent.ToCompactString()
                                            : TEXT("unavailable"));
                                    if (Component)
                                    {
                                        for (int32 MaterialIndex = 0;
                                             MaterialIndex < Component->GetNumMaterials();
                                             ++MaterialIndex)
                                        {
                                            const UMaterialInterface* Material =
                                                Component->GetMaterial(MaterialIndex);
                                            UE_LOG(
                                                LogTemp,
                                                Display,
                                                TEXT("RaftSim.CaptureRapidWrapTest: "
                                                     "rockMaterial[%d]=%s"),
                                                MaterialIndex,
                                                Material
                                                    ? *Material->GetPathName()
                                                    : TEXT("unavailable"));
                                        }
                                    }
                                }
                            }
                        }
                        FScreenshotRequest::RequestScreenshot(OutPath, false, false);
                        if (UWorld* CaptureWorld = WeakWorld.Get())
                        {
                            FTimerHandle ExitHandle;
                            CaptureWorld->GetTimerManager().SetTimer(
                                ExitHandle,
                                FTimerDelegate::CreateLambda([]()
                                {
                                    FPlatformMisc::RequestExit(false);
                                }),
                                4.0f,
                                false);
                        }
                    }),
                    // The camera is already in the running level. Two 60 Hz
                    // frames resolve the view target without turning an active
                    // D4 wrap into a later shape-recovery screenshot.
                    0.03f,
                    false);
            }
        }),
        0.95f,
        false);
}

static FAutoConsoleCommandWithWorldAndArgs GCaptureRapidWrapTestCommand(
    TEXT("RaftSim.CaptureRapidWrapTest"),
    TEXT("Stage the live raft in Meat Grinder, add a D4-authoritative contact boulder, "
         "and capture the solver-derived wrap, wetness, and spray. "
         "Usage: RaftSim.CaptureRapidWrapTest [label] [stationM] "
         "[downstream_right|upstream_left|downstream_left|upstream_right|contact_port|particle_macro|breaking_water] "
         "[unlit] [nowater] [noauthoredwater] [norockvisual] "
         "[novfx] [notubes] [nofloor] [norigging] "
         "[nobreakinglip] [nobreakingroller] "
         "[norapidaerosol] [norapidroller] "
         "[taa] [nobloom] [nocloud] "
         "[nofittings] [norubber] [reviewedrock] [noshadowwater] [nodressing] "
         "[noboulderdressing] [waterinventory] [terrainvertexmacro] "
         "[terrainnoedgeblend] [terrainnospecular] "
         "[terrainmacro=0..1] "
         "[waterdetail=0..0.40] "
         "[waterfoam=0..2] [waterfoamcore=0..2] [waterfoamlace=0..2] "
         "[waterroughness=0..0.80] [waterspecular=0..1] "
         "[rockx=cm] [rocky=cm] [rockz=cm] "
         "[livecoverage=0..0.25] "
         "[livewaterroughness=0..0.80] [livewaterspecular=0..1] "
         "[rockmesh=/Game/path.Asset] "
         "[watermaterial=/Game/path.Asset]"
         " [terrainmaterial=/Game/path.Asset]"),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&HandleCaptureRapidWrapTest));

} // namespace RaftSimCaptureCommand
