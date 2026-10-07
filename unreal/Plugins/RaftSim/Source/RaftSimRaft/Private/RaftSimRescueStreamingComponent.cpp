#include "RaftSimRescueStreamingComponent.h"
#include "RaftSimRaftActor.h"
#include "Engine/World.h"
#include "WorldPartition/WorldPartitionSubsystem.h"

URaftSimRescueStreamingComponent::URaftSimRescueStreamingComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void URaftSimRescueStreamingComponent::BeginPlay()
{
    Super::BeginPlay();
    if (GetWorld() && GetWorld()->GetWorldPartition())
        if (auto* Subsystem = GetWorld()->GetSubsystem<UWorldPartitionSubsystem>())
            Subsystem->RegisterStreamingSourceProvider(this);
}

void URaftSimRescueStreamingComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    if (GetWorld())
        if (auto* Subsystem = GetWorld()->GetSubsystem<UWorldPartitionSubsystem>())
            Subsystem->UnregisterStreamingSourceProvider(this);
    Super::EndPlay(Reason);
}

bool URaftSimRescueStreamingComponent::GetStreamingSources(
    TArray<FWorldPartitionStreamingSource>& Sources) const
{
    const auto* Raft = Cast<ARaftSimRaftActor>(GetOwner());
    if (!IsValid(Raft) || Raft->IsActorBeingDestroyed()) return false;
    const int32 Before = Sources.Num();
    const auto Add = [&](const FString& Suffix, const FVector& Position, float RadiusCm)
    {
        if (Position.ContainsNaN()) return;
        FWorldPartitionStreamingSource Source;
        Source.Name = FName(*(Raft->GetPathName() + TEXT("/RescueTerrain/") + Suffix));
        Source.Location = Position;
        Source.TargetState = EStreamingSourceTargetState::Activated;
        Source.Priority = EStreamingSourcePriority::High;
        Source.bBlockOnSlowLoading = true;
        Source.bForce2D = true;
        FStreamingSourceShape Shape;
        Shape.bUseGridLoadingRange = false;
        Shape.Radius = RadiusCm;
        Source.Shapes.Add(Shape);
        Sources.Add(MoveTemp(Source));
    };
    Add(TEXT("raft"), Raft->GetActorLocation(), 100000.f);
    for (const auto& Swimmer : Raft->GetSwimmerFrames())
    {
        FVector PositionCm;
        if (!Swimmer.PassengerId.IsNone() &&
            Raft->GetSwimmerWorldPosition(Swimmer.PassengerId, PositionCm))
            Add(TEXT("swimmer/") + Swimmer.PassengerId.ToString(), PositionCm, 30000.f);
    }
    return Sources.Num() > Before;
}
