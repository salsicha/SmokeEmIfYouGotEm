#include "RaftSimCapturedCanopyActor.h"

#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Dom/JsonObject.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Camera/PlayerCameraManager.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Misc/FileHelper.h"
#include "TimerManager.h"
#include "UObject/UObjectIterator.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

// Read-only diagnostic: which canopy instances stand above (or far below) the
// first visible ground under them in the running game world, and what that
// ground belongs to. Canopy is non-colliding, so a downward visibility trace
// from above each root finds the terrain actually rendered there.
namespace
{
void RunCanopyGroundAudit(UWorld* World, double RadiusCm, const FString& OutPath)
{
    if (!World) return;
    FVector Centre = FVector::ZeroVector;
    if (APlayerController* PC = World->GetFirstPlayerController())
    {
        // The view drives both World Partition streaming and instance culling.
        if (PC->PlayerCameraManager) Centre = PC->PlayerCameraManager->GetCameraLocation();
        else if (APawn* Pawn = PC->GetPawn()) Centre = Pawn->GetActorLocation();
    }
    FCollisionQueryParams Params(SCENE_QUERY_STAT(RaftSimCanopyGroundAudit), true);
    int32 Traced = 0, NoHit = 0, Floating = 0, Buried = 0, Culled = 0;
    TArray<double> Gaps;
    TMap<FString, int32> FloatingOwners;
    TArray<TSharedPtr<FJsonValue>> Examples;
    for (TActorIterator<ARaftSimCapturedCanopyActor> It(World); It; ++It)
    {
        for (UHierarchicalInstancedStaticMeshComponent* Comp : {It->CanopyA.Get(), It->CanopyB.Get(), It->CanopyC.Get()})
        {
            if (!Comp) continue;
            for (int32 I = 0; I < Comp->GetInstanceCount(); ++I)
            {
                FTransform T;
                if (!Comp->GetInstanceTransform(I, T, true)) continue;
                const FVector Root = T.GetLocation();
                if (FVector::DistSquared2D(Root, Centre) > RadiusCm * RadiusCm) continue;
                if (Comp->InstanceEndCullDistance > 0 &&
                    FVector::Dist(Root, Centre) > Comp->InstanceEndCullDistance)
                {
                    ++Culled; // Not drawn: cannot be seen floating.
                    continue;
                }
                ++Traced;
                TArray<FHitResult> Hits;
                World->LineTraceMultiByChannel(Hits, Root + FVector(0, 0, 30000), Root - FVector(0, 0, 30000),
                    ECC_Visibility, Params);
                const FHitResult* First = nullptr;
                for (const FHitResult& Hit : Hits)
                {
                    const AActor* Owner = Hit.GetActor();
                    const FString Label = Owner ? Owner->GetActorNameOrLabel() : FString();
                    if (Label.Contains(TEXT("Water"))) continue;
                    First = &Hit;
                    break;
                }
                const double Gap = First ? Root.Z - First->ImpactPoint.Z : TNumericLimits<double>::Max();
                if (First) Gaps.Add(Gap); else ++NoHit;
                const bool bFloating = !First || Gap > 100.0;
                Floating += bFloating;
                Buried += First && Gap < -300.0;
                if (bFloating || (First && Gap < -300.0))
                {
                    const AActor* Owner = First ? First->GetActor() : nullptr;
                    FString Key = Owner ? Owner->GetActorNameOrLabel().Left(40) : TEXT("<no hit>");
                    FloatingOwners.FindOrAdd(Key)++;
                    if (Examples.Num() < 300)
                    {
                        auto Row = MakeShared<FJsonObject>();
                        Row->SetStringField(TEXT("actor"), It->GetActorNameOrLabel());
                        Row->SetStringField(TEXT("component"), Comp->GetName());
                        Row->SetNumberField(TEXT("index"), I);
                        Row->SetNumberField(TEXT("root_x_cm"), Root.X);
                        Row->SetNumberField(TEXT("root_y_cm"), Root.Y);
                        Row->SetNumberField(TEXT("root_z_cm"), Root.Z);
                        Row->SetNumberField(TEXT("distance_m"), FVector::Dist2D(Root, Centre) / 100.0);
                        Row->SetStringField(TEXT("hit_owner"), Key);
                        if (First)
                        {
                            Row->SetNumberField(TEXT("gap_cm"), Gap);
                            FString Tags;
                            for (const FName& Tag : First->GetActor()->Tags) Tags += Tag.ToString() + TEXT(";");
                            Row->SetStringField(TEXT("hit_tags"), Tags);
                            Row->SetStringField(TEXT("hit_component"), First->GetComponent() ? First->GetComponent()->GetName() : FString());
                        }
                        Examples.Add(MakeShared<FJsonValueObject>(Row));
                    }
                }
            }
        }
    }
    Gaps.Sort();
    const auto Quantile = [&Gaps](double F) { return Gaps.Num() ? Gaps[FMath::Clamp(int32(F * (Gaps.Num() - 1)), 0, Gaps.Num() - 1)] : 0.0; };
    auto Report = MakeShared<FJsonObject>();
    Report->SetStringField(TEXT("scope"), TEXT("Game-world downward visibility traces under canopy instance roots; read-only diagnostic."));
    Report->SetNumberField(TEXT("centre_x_cm"), Centre.X);
    Report->SetNumberField(TEXT("centre_y_cm"), Centre.Y);
    Report->SetNumberField(TEXT("radius_m"), RadiusCm / 100.0);
    Report->SetNumberField(TEXT("traced"), Traced);
    Report->SetNumberField(TEXT("culled_not_drawn"), Culled);
    Report->SetNumberField(TEXT("no_hit"), NoHit);
    Report->SetNumberField(TEXT("floating_over_1m_or_no_hit"), Floating);
    Report->SetNumberField(TEXT("buried_over_3m"), Buried);
    Report->SetNumberField(TEXT("gap_cm_p01"), Quantile(.01));
    Report->SetNumberField(TEXT("gap_cm_p50"), Quantile(.5));
    Report->SetNumberField(TEXT("gap_cm_p99"), Quantile(.99));
    Report->SetNumberField(TEXT("gap_cm_max"), Gaps.Num() ? Gaps.Last() : 0.0);
    auto Owners = MakeShared<FJsonObject>();
    for (const auto& Pair : FloatingOwners) Owners->SetNumberField(Pair.Key, Pair.Value);
    Report->SetObjectField(TEXT("outlier_first_hit_owners"), Owners);
    Report->SetArrayField(TEXT("outlier_examples"), Examples);
    FString Json;
    FJsonSerializer::Serialize(Report, TJsonWriterFactory<>::Create(&Json));
    const bool bSaved = FFileHelper::SaveStringToFile(Json, *OutPath);
    UE_LOG(LogTemp, Display, TEXT("RAFTSIM_CANOPY_GROUND_AUDIT traced=%d culled=%d no_hit=%d floating=%d buried=%d p99_cm=%.1f saved=%d"),
        Traced, Culled, NoHit, Floating, Buried, Quantile(.99), bSaved ? 1 : 0);
}

void HandleCanopyGroundAudit(const TArray<FString>& Args, UWorld* World)
{
    if (!World || Args.Num() < 2)
    {
        UE_LOG(LogTemp, Error, TEXT("Usage: RaftSim.CanopyGroundAudit <radius_m> <output.json> [delay_s]"));
        return;
    }
    const double RadiusCm = FCString::Atod(*Args[0]) * 100.0;
    const FString OutPath = Args[1];
    const float DelaySeconds = Args.Num() > 2 ? FCString::Atof(*Args[2]) : 0.0f;
    if (DelaySeconds <= 0.0f)
    {
        RunCanopyGroundAudit(World, RadiusCm, OutPath);
        return;
    }
    FTimerHandle Handle;
    TWeakObjectPtr<UWorld> WeakWorld(World);
    World->GetTimerManager().SetTimer(Handle, FTimerDelegate::CreateLambda([WeakWorld, RadiusCm, OutPath]()
    {
        RunCanopyGroundAudit(WeakWorld.Get(), RadiusCm, OutPath);
    }), DelaySeconds, false);
}

FAutoConsoleCommandWithWorldAndArgs GRaftSimCanopyGroundAudit(
    TEXT("RaftSim.CanopyGroundAudit"),
    TEXT("Trace under every loaded canopy instance within <radius_m> of the player and write <output.json>, optionally after [delay_s]."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&HandleCanopyGroundAudit));
// Read-only: what instanced or static geometry lies in the current view beyond
// a distance, grouped by owner/component/mesh. Used to attribute distant
// silhouettes (for example floating tree ridges) to their generating actors.
void RunViewInventory(UWorld* World, double MinDistanceCm, const FString& OutPath)
{
    if (!World) return;
    APlayerController* PC = World->GetFirstPlayerController();
    if (!PC || !PC->PlayerCameraManager) return;
    const FVector Eye = PC->PlayerCameraManager->GetCameraLocation();
    const FVector Forward = PC->PlayerCameraManager->GetCameraRotation().Vector();
    const double HalfFovCos = FMath::Cos(FMath::DegreesToRadians(PC->PlayerCameraManager->GetFOVAngle() * 0.5 + 2.0));
    struct FGroup { int32 Count = 0; double MinD = TNumericLimits<double>::Max(), MaxD = 0, MinZ = TNumericLimits<double>::Max(), MaxZ = -TNumericLimits<double>::Max(); FString Tags; };
    TMap<FString, FGroup> Groups;
    const auto Add = [&](const FString& Key, const FVector& P, const AActor* Owner)
    {
        FGroup& G = Groups.FindOrAdd(Key);
        const double D = FVector::Dist(P, Eye);
        ++G.Count; G.MinD = FMath::Min(G.MinD, D); G.MaxD = FMath::Max(G.MaxD, D);
        G.MinZ = FMath::Min(G.MinZ, P.Z); G.MaxZ = FMath::Max(G.MaxZ, P.Z);
        if (G.Tags.IsEmpty() && Owner) for (const FName& Tag : Owner->Tags) G.Tags += Tag.ToString() + TEXT(";");
    };
    const auto InView = [&](const FVector& P)
    {
        const FVector D = P - Eye;
        const double Len = D.Size();
        return Len > MinDistanceCm && FVector::DotProduct(D / Len, Forward) > HalfFovCos;
    };
    for (TObjectIterator<UStaticMeshComponent> It; It; ++It)
    {
        UStaticMeshComponent* Comp = *It;
        if (!Comp || Comp->GetWorld() != World || !Comp->IsRegistered() || !Comp->IsVisible()) continue;
        const AActor* Owner = Comp->GetOwner();
        if (Owner && Owner->IsHidden()) continue;
        const FString Mesh = Comp->GetStaticMesh() ? Comp->GetStaticMesh()->GetName() : TEXT("<none>");
        const FString Base = (Owner ? Owner->GetClass()->GetName() + TEXT("|") + Owner->GetActorNameOrLabel().Left(48) : TEXT("<no owner>")) +
            TEXT("|") + Comp->GetName() + TEXT("|") + Mesh;
        if (UInstancedStaticMeshComponent* Ism = Cast<UInstancedStaticMeshComponent>(Comp))
        {
            for (int32 I = 0; I < Ism->GetInstanceCount(); ++I)
            {
                FTransform T;
                if (!Ism->GetInstanceTransform(I, T, true)) continue;
                const FVector P = T.GetLocation();
                if (!InView(P)) continue;
                if (Ism->InstanceEndCullDistance > 0 && FVector::Dist(P, Eye) > Ism->InstanceEndCullDistance) continue;
                Add(Base, P, Owner);
            }
        }
        else
        {
            const FVector P = Comp->Bounds.Origin;
            if (InView(P)) Add(Base, P, Owner);
        }
    }
    TArray<TPair<FString, FGroup>> Sorted;
    for (const auto& Pair : Groups) Sorted.Add(TPair<FString, FGroup>(Pair.Key, Pair.Value));
    Sorted.Sort([](const TPair<FString, FGroup>& A, const TPair<FString, FGroup>& B) { return A.Value.Count > B.Value.Count; });
    TArray<TSharedPtr<FJsonValue>> Rows;
    for (int32 I = 0; I < FMath::Min(Sorted.Num(), 400); ++I)
    {
        auto Row = MakeShared<FJsonObject>();
        Row->SetStringField(TEXT("key"), Sorted[I].Key);
        Row->SetNumberField(TEXT("count"), Sorted[I].Value.Count);
        Row->SetNumberField(TEXT("min_distance_m"), Sorted[I].Value.MinD / 100.0);
        Row->SetNumberField(TEXT("max_distance_m"), Sorted[I].Value.MaxD / 100.0);
        Row->SetNumberField(TEXT("min_z_cm"), Sorted[I].Value.MinZ);
        Row->SetNumberField(TEXT("max_z_cm"), Sorted[I].Value.MaxZ);
        Row->SetStringField(TEXT("tags"), Sorted[I].Value.Tags);
        Rows.Add(MakeShared<FJsonValueObject>(Row));
    }
    auto Report = MakeShared<FJsonObject>();
    Report->SetStringField(TEXT("scope"), TEXT("Read-only view-cone inventory of visible static/instanced mesh geometry beyond a distance."));
    Report->SetNumberField(TEXT("eye_x_cm"), Eye.X); Report->SetNumberField(TEXT("eye_y_cm"), Eye.Y); Report->SetNumberField(TEXT("eye_z_cm"), Eye.Z);
    Report->SetNumberField(TEXT("forward_x"), Forward.X); Report->SetNumberField(TEXT("forward_y"), Forward.Y); Report->SetNumberField(TEXT("forward_z"), Forward.Z);
    Report->SetNumberField(TEXT("min_distance_m"), MinDistanceCm / 100.0);
    Report->SetArrayField(TEXT("groups"), Rows);
    FString Json;
    FJsonSerializer::Serialize(Report, TJsonWriterFactory<>::Create(&Json));
    const bool bSaved = FFileHelper::SaveStringToFile(Json, *OutPath);
    UE_LOG(LogTemp, Display, TEXT("RAFTSIM_VIEW_INVENTORY groups=%d saved=%d"), Groups.Num(), bSaved ? 1 : 0);
}

void HandleViewInventory(const TArray<FString>& Args, UWorld* World)
{
    if (!World || Args.Num() < 2)
    {
        UE_LOG(LogTemp, Error, TEXT("Usage: RaftSim.ViewInventory <min_distance_m> <output.json> [delay_s]"));
        return;
    }
    const double MinCm = FCString::Atod(*Args[0]) * 100.0;
    const FString OutPath = Args[1];
    const float DelaySeconds = Args.Num() > 2 ? FCString::Atof(*Args[2]) : 0.0f;
    if (DelaySeconds <= 0.0f) { RunViewInventory(World, MinCm, OutPath); return; }
    FTimerHandle Handle;
    TWeakObjectPtr<UWorld> WeakWorld(World);
    World->GetTimerManager().SetTimer(Handle, FTimerDelegate::CreateLambda([WeakWorld, MinCm, OutPath]()
    { RunViewInventory(WeakWorld.Get(), MinCm, OutPath); }), DelaySeconds, false);
}

FAutoConsoleCommandWithWorldAndArgs GRaftSimViewInventory(
    TEXT("RaftSim.ViewInventory"),
    TEXT("List visible static/instanced geometry in the current view beyond <min_distance_m>, grouped by owner and mesh."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&HandleViewInventory));
}
