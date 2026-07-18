#include "RaftSimRunManager.h"

#include "Components/BoxComponent.h"
#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "RaftSimEncounterVolume.h"
#include "RaftSimRaftActor.h"
#include "RaftSimSaveSubsystem.h"

ARaftSimRunManager::ARaftSimRunManager()
{
    PrimaryActorTick.bCanEverTick = true;
}

void ARaftSimRunManager::BeginPlay()
{
    Super::BeginPlay();

    if (TActorIterator<ARaftSimRaftActor> It(GetWorld()); It)
    {
        Raft = *It;
    }
    for (TActorIterator<ARaftSimEncounterVolume> It(GetWorld()); It; ++It)
    {
        Volumes.Add(*It);
    }
    if (Raft != nullptr)
    {
        LastSwimmerCount = Raft->GetSwimmerCount();
    }
}

void ARaftSimRunManager::StartRun()
{
    RunState = ERaftSimRunState::Running;
    RunTimeSeconds = 0.0f;
    SafetyIncidents = 0;
    SwimCount = 0;
    AngleErrorAccumDeg = 0.0f;
    AngleSampleSeconds = 0.0f;
    if (Raft != nullptr)
    {
        LastSwimmerCount = Raft->GetSwimmerCount();
    }
}

void ARaftSimRunManager::AccumulateSignals(float DeltaSeconds)
{
    if (Raft == nullptr)
    {
        return;
    }

    // A fresh batch of swimmers = a swim/flip incident.
    const int32 Swimmers = Raft->GetSwimmerCount();
    if (Swimmers > LastSwimmerCount)
    {
        ++SwimCount;
        ++SafetyIncidents;
    }
    LastSwimmerCount = Swimmers;

    // Boat-angle error: yaw away from downstream (+Y in these maps).
    const float Yaw = Raft->GetActorRotation().Yaw;
    const float DownstreamYaw = 0.0f; // +X (raft forward)
    float AngleErr = FMath::Abs(FMath::FindDeltaAngleDegrees(Yaw, DownstreamYaw));
    AngleErrorAccumDeg += AngleErr * DeltaSeconds;
    AngleSampleSeconds += DeltaSeconds;

    // Hazard overlaps (off the clean line) count as incidents, throttled by
    // being inside the volume — counted once per entry via overlap state.
    for (const TObjectPtr<ARaftSimEncounterVolume>& Volume : Volumes)
    {
        if (Volume == nullptr || Volume->Kind != ERaftSimEncounterKind::Hazard)
        {
            continue;
        }
        if (Volume->GetTrigger()->IsOverlappingActor(Raft))
        {
            // Only count the transition into a hazard, tracked by a tag.
            const FName Tag(*FString::Printf(TEXT("InHazard_%s"), *Volume->GetName()));
            if (!Raft->Tags.Contains(Tag))
            {
                Raft->Tags.Add(Tag);
                ++SafetyIncidents;
            }
        }
    }
}

void ARaftSimRunManager::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (Raft == nullptr)
    {
        return;
    }

    const float RaftX = Raft->GetActorLocation().X;

    if (RunState == ERaftSimRunState::Ready)
    {
        // Start once the raft leaves the scout eddy / passes the start line.
        if (RaftX >= StartLineX)
        {
            StartRun();
        }
        return;
    }

    if (RunState == ERaftSimRunState::Running)
    {
        RunTimeSeconds += DeltaSeconds;
        AccumulateSignals(DeltaSeconds);

        // Finish at the Finish volume if present, else the fallback line.
        bool bFinished = RaftX >= FinishLineX;
        for (const TObjectPtr<ARaftSimEncounterVolume>& Volume : Volumes)
        {
            if (Volume != nullptr && Volume->Kind == ERaftSimEncounterKind::Finish &&
                Volume->GetTrigger()->IsOverlappingActor(Raft))
            {
                bFinished = true;
            }
        }
        if (bFinished)
        {
            FinishRun();
        }
    }
}

void ARaftSimRunManager::FinishRun()
{
    RunState = ERaftSimRunState::Finished;

    FRaftSimGameplayScoringSignals Signals;
    Signals.SafetyIncidentCount = SafetyIncidents;
    Signals.SwimCount = SwimCount;
    Signals.CleanLineRatio = (SafetyIncidents == 0) ? 1.0f : FMath::Max(0.0f, 1.0f - 0.2f * SafetyIncidents);
    Signals.MeanBoatAngleErrorDegrees =
        AngleSampleSeconds > 0.0f ? AngleErrorAccumDeg / AngleSampleSeconds : 0.0f;
    Signals.RescueMethod =
        (SwimCount > 0) ? ERaftSimRescueMethod::ThrowLine : ERaftSimRescueMethod::None;

    FinalScore = URaftSimGameplayScoringLibrary::EvaluateGameplayScore(Signals);

    if (const UGameInstance* GameInstance = GetGameInstance())
    {
        if (URaftSimSaveSubsystem* Save = GameInstance->GetSubsystem<URaftSimSaveSubsystem>())
        {
            Save->MarkScenarioCompleted(
                ScenarioId, FinalScore.SafetyScore, FinalScore.TotalScore);
        }
    }
}
