#include "RaftSimRunManager.h"
#include "RaftSimCheckpointStreaming.h"

#include "Components/BoxComponent.h"
#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "RaftSimEncounterVolume.h"
#include "RaftSimRaftActor.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRiverWaterConfig.h"
#include "RaftSimCartesianWaterRegions.h"
#include "RaftSimRouteGhostActor.h"
#include "RaftSimSaveSubsystem.h"
#include "RaftSimWaterRuntimeAdapter.h"

ARaftSimRunManager::ARaftSimRunManager()
{
    PrimaryActorTick.bCanEverTick = true;
}

void ARaftSimRunManager::BeginPlay()
{
    Super::BeginPlay();

    ConfigureProgressCoordinateMap(ProgressCoordinateMapPath);

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
        Raft->SetCheckpointPreparation(FRaftSimCheckpointPreparation::CreateUObject(
            this,&ARaftSimRunManager::PrepareCheckpointReset));
        LastSwimmerCount = Raft->GetSwimmerCount();
    }

    if (URaftSimSaveSubsystem* Save = GetGameInstance()
            ? GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>() : nullptr)
    {
        if (Save->GetSave() != nullptr)
        {
            FRaftSimCareerScenarioDefinition Scenario;
            if (URaftSimProgressionLibrary::FindScenario(
                    Save->GetSave()->Selection.ScenarioId, Scenario))
            {
                ConfigureSession(Scenario, Save->GetSave()->ActiveGameMode);
            }
            FRaftSimScenarioProgress Progress;
            if (Save->GetScenarioProgress(ScenarioId, Progress) &&
                Progress.CoordinateMapPath == ProgressCoordinateMapPath)
            {
                BestGhostRoute = Progress.BestGhostRoute;
            }
            const FRaftSimVerticalSliceUserSettings& Settings = Save->GetSave()->Settings;
            bAssistUsed = Settings.AssistLevel != ERaftSimAssistLevel::Authentic ||
                Settings.bRouteAssistEnabled;
            if (Settings.bGhostEnabled && BestGhostRoute.Num() >= 2)
            {
                if (ARaftSimRouteGhostActor* Ghost = GetWorld()->SpawnActor<ARaftSimRouteGhostActor>(
                        ARaftSimRouteGhostActor::StaticClass(), FTransform::Identity))
                {
                    Ghost->SetRoute(BestGhostRoute);
                }
            }
        }
    }
}

void ARaftSimRunManager::ConfigureSession(
    const FRaftSimCareerScenarioDefinition& Scenario, ERaftSimGameMode InGameMode)
{
    LastProgressSample.bValid = false;
    ScenarioId = Scenario.ScenarioId;
    GameModeKind = InGameMode;
    StartStationM = Scenario.StartStationM;
    FinishStationM = Scenario.FinishStationM;
    bCheckpointRestorePending = StartStationM > 200.0f && !Scenario.bFullDescent;
    // GameMode configures this again after BeginPlay, so apply the ephemeral
    // review start here. Never modify the selected scenario or saved checkpoint.
    float ReviewStationM = -1.0f;
    FRaftSimCareerScenarioDefinition FullRiver;
    const bool bHasFullRiver = URaftSimProgressionLibrary::FindScenario(TEXT("south_fork_full_descent"),FullRiver);
    float ReviewMinimumM = 0.f, ReviewMaximumM = bHasFullRiver ? FullRiver.FinishStationM : FinishStationM;
    if (ProgressCoordinates) ProgressCoordinates->GetRiverStationRangeM(ReviewMinimumM,ReviewMaximumM);
    if (GetWorld() && GetWorld()->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach")) &&
        FParse::Value(FCommandLine::Get(), TEXT("RaftSimWaterReviewStation="), ReviewStationM) &&
        FMath::IsFinite(ReviewStationM) && ReviewStationM >= ReviewMinimumM && ReviewStationM <= ReviewMaximumM)
    {
        ScenarioId = TEXT("south_fork_full_descent");
        GameModeKind = ERaftSimGameMode::FreeRun;
        StartStationM = ReviewStationM;
        FinishStationM = ReviewMaximumM;
        bCheckpointRestorePending = true;
    }
}

bool ARaftSimRunManager::ConfigureProgressCoordinateMap(const FString& Path)
{
    LastProgressSample.bValid = false;
    ProgressCoordinateMapPath = Path;
    ProgressCoordinates = nullptr;
    ProgressAxis.Reset();
    ProgressAxisIndex.Reset();
    if (Path.IsEmpty()) return true;
    auto* Candidate = NewObject<URaftSimWaterRuntimeAdapter>(this);
    if (!Candidate->ConfigureRiverCoordinateMap(Path) || Candidate->HasCartesianWaterCoordinates()) return false;
    // Retain the exact polyline corners for geometric descent chainage.
    // The hydraulic inverse instead solves a ruled lateral ribbon; its
    // off-axis station is not necessarily the nearest-axis station.
    FString Text;
    TSharedPtr<FJsonObject> Root;
    if (!FFileHelper::LoadFileToString(Text, *URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(Path)) ||
        !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text), Root) || !Root.IsValid()) return false;
    const TArray<TSharedPtr<FJsonValue>>* Points = nullptr;
    if (!Root->TryGetArrayField(TEXT("points"), Points) || !Points) return false;
    for (const auto& Value : *Points)
    {
        const auto& Values = Value->AsArray(); // Already validated by Candidate.
        FProgressAxisPoint Point;
        Point.StationM = Values[0]->AsNumber();
        Point.PositionM = FVector2D(Values[1]->AsNumber(), Values[2]->AsNumber());
        const int32 Index = ProgressAxis.Add(Point);
        ProgressAxisIndex.FindOrAdd(FIntPoint(FMath::FloorToInt(Point.PositionM.X / 128.),
            FMath::FloorToInt(Point.PositionM.Y / 128.))).Add(Index);
    }
    ProgressCoordinates = Candidate;
    return true;
}

const URaftSimWaterRuntimeAdapter* ARaftSimRunManager::GetProgressCoordinates(
    const URaftSimWaterRuntimeAdapter* HydraulicCoordinates) const
{
    if (!ProgressCoordinateMapPath.IsEmpty()) return ProgressCoordinates.Get();
    // Cartesian east/north is never a fallback scoring or checkpoint axis.
    return HydraulicCoordinates && !HydraulicCoordinates->HasCartesianWaterCoordinates()
        ? HydraulicCoordinates : nullptr;
}

bool ARaftSimRunManager::WorldToRunCoordinates(const FVector& WorldPositionCm,
    const URaftSimWaterRuntimeAdapter* HydraulicCoordinates,
    FVector2D& OutStationLateralM, FVector& OutTangent, FVector& OutLeft) const
{
    if (ProgressCoordinateMapPath.IsEmpty())
        return HydraulicCoordinates && HydraulicCoordinates->HasRiverCoordinateMap() &&
            !HydraulicCoordinates->HasCartesianWaterCoordinates() &&
            HydraulicCoordinates->WorldToRiverCoordinates(WorldPositionCm, OutStationLateralM, OutTangent, OutLeft);
    if (!ProgressCoordinates || ProgressAxis.Num() < 2 || WorldPositionCm.ContainsNaN()) return false;
    const double Sign = ProgressCoordinates->GetRiverWorldYSign();
    const FVector2D Position(WorldPositionCm.X / 100., Sign * WorldPositionCm.Y / 100.);
    const FIntPoint Key(FMath::FloorToInt(Position.X / 128.), FMath::FloorToInt(Position.Y / 128.));
    double BestDistance = TNumericLimits<double>::Max(), BestAlpha = 0;
    int32 BestIndex = INDEX_NONE;
    TSet<int32> Segments;
    // 256 m accepted corridor plus one cell for the validated <=16 m edges.
    // Always compare nearby segments; a warm hydraulic-ribbon cache must not
    // select a different branch of a bend for scoring or checkpoints.
    for (int32 Y = -3; Y <= 3; ++Y)
        for (int32 X = -3; X <= 3; ++X)
            if (const auto* Indices = ProgressAxisIndex.Find(Key + FIntPoint(X, Y)))
                for (int32 Index : *Indices)
                {
                    if (Index > 0) Segments.Add(Index - 1);
                    if (Index + 1 < ProgressAxis.Num()) Segments.Add(Index);
                }
    for (int32 Index : Segments)
    {
        const FVector2D Delta = ProgressAxis[Index + 1].PositionM - ProgressAxis[Index].PositionM;
        const double LengthSquared = Delta.SquaredLength();
        if (LengthSquared <= UE_DOUBLE_SMALL_NUMBER) continue;
        const double Alpha = FMath::Clamp(FVector2D::DotProduct(
            Position - ProgressAxis[Index].PositionM, Delta) / LengthSquared, 0., 1.);
        const double Distance = (Position - (ProgressAxis[Index].PositionM + Alpha * Delta)).SquaredLength();
        if (Distance < BestDistance || (Distance == BestDistance && Index < BestIndex))
        {
            BestDistance = Distance;
            BestIndex = Index;
            BestAlpha = Alpha;
        }
    }
    if (BestIndex == INDEX_NONE || BestDistance > FMath::Square(256.)) return false;
    const auto& A = ProgressAxis[BestIndex];
    const auto& B = ProgressAxis[BestIndex + 1];
    const FVector2D Tangent = (B.PositionM - A.PositionM).GetSafeNormal();
    const FVector2D Left(-Tangent.Y, Tangent.X);
    OutStationLateralM = FVector2D(FMath::Lerp(A.StationM, B.StationM, BestAlpha),
        FVector2D::DotProduct(Position - FMath::Lerp(A.PositionM, B.PositionM, BestAlpha), Left));
    OutTangent = FVector(Tangent.X, Sign * Tangent.Y, 0);
    OutLeft = FVector(Left.X, Sign * Left.Y, 0);
    return true;
}

float ARaftSimRunManager::GetProgressFraction() const
{
    if (FMath::IsFinite(StartStationM) && FMath::IsFinite(FinishStationM) && FinishStationM > StartStationM)
    {
        return FMath::Clamp(
            (CurrentStationM - StartStationM) / (FinishStationM - StartStationM),
            0.0f, 1.0f);
    }
    if (FinishLineX > StartLineX && Raft != nullptr)
    {
        return FMath::Clamp(
            (Raft->GetActorLocation().X - StartLineX) / (FinishLineX - StartLineX),
            0.0f, 1.0f);
    }
    return 0.0f;
}

bool ARaftSimRunManager::SampleRiverStation(float& OutStationM, FVector* OutTangent,
    FVector* OutSamplePositionCm) const
{
    if (Raft == nullptr || GetGameInstance() == nullptr)
    {
        return false;
    }
    const URaftSimPhysicsBridgeSubsystem* Bridge =
        GetGameInstance()->GetSubsystem<URaftSimPhysicsBridgeSubsystem>();
    const URaftSimWaterRuntimeAdapter* Water = Bridge ? Bridge->GetWaterRuntime() : nullptr;
    const URaftSimWaterRuntimeAdapter* Progress = GetProgressCoordinates(Water);
    if (Progress == nullptr || !Progress->HasRiverCoordinateMap())
    {
        return false;
    }
    FVector2D StationLateral;
    FVector Tangent;
    FVector Left;
    const FVector SamplePositionCm = Raft->GetActorLocation();
    if (!WorldToRunCoordinates(SamplePositionCm, Water, StationLateral, Tangent, Left))
    {
        return false;
    }
    OutStationM = StationLateral.X;
    if (OutTangent != nullptr)
    {
        *OutTangent = Tangent;
    }
    if (!FMath::IsFinite(OutStationM)) return false;
    if (OutSamplePositionCm) *OutSamplePositionCm = SamplePositionCm;
    return true;
}

// A section that starts mid-reach with no saved checkpoint (a Free Run of a
// named rapid, or a fresh profile on a later career section) begins at its
// start station instead of the map's put-in: the same window reseed and
// raft move the checkpoint restore does, with a transform built from the
// corridor (heading downstream, hull just above the local water surface).
static bool BuildStationStartTransform(
    const URaftSimWaterRuntimeAdapter* Progress, URaftSimWaterRuntimeAdapter* Water,
    float StationM, FTransform& OutTransform)
{
    FVector PointCm;
    FVector AheadCm;
    const float DatumM = Progress->GetRiverVerticalDatumM();
    if (!Progress->RiverToWorldPosition(FVector2D(StationM, 0.0f), DatumM, PointCm) ||
        !Progress->RiverToWorldPosition(FVector2D(StationM + 1.0f, 0.0f), DatumM, AheadCm))
    {
        return false;
    }
    FRaftSimWaterSample Sample;
    if (Water->SampleWaterAtWorldPosition(PointCm, Sample) && Sample.bWet)
    {
        PointCm.Z = Sample.SurfaceHeightMeters * 100.0f + 40.0f;
    }
    else
    {
        PointCm.Z += 100.0f;
    }
    OutTransform = FTransform(
        FRotator(0.0f, (AheadCm - PointCm).Rotation().Yaw, 0.0f), PointCm);
    return true;
}

bool ARaftSimRunManager::PrepareCheckpointReset(FTransform& Destination)
{
    if (!RaftSimCheckpointStreaming::Prepare(GetWorld(),Destination)) return false;
    auto* Instance=GetGameInstance();
    auto* Bridge=Instance ? Instance->GetSubsystem<URaftSimPhysicsBridgeSubsystem>() : nullptr;
    auto* Water=Bridge ? Bridge->GetWaterRuntime() : nullptr;
    ARaftSimRiverWaterConfig* Config=nullptr;
    for (TActorIterator<ARaftSimRiverWaterConfig> It(GetWorld()); It; ++It)
    {
        if (Config) return false; // Ambiguous scenario ownership is not a fallback.
        Config=*It;
    }
    if (Config && (!Water || ((!Config->StreamingManifestPath.IsEmpty() ||
        Config->bEnableMovingWindowStreaming) && !Water->HasRiverCoordinateMap()))) return false;
    // Legacy static ribbon/tank recovery is unchanged; geographic Cartesian
    // crops must select and validate the destination packet before the move.
    if (!Water || !Water->HasCartesianWaterCoordinates()) return true;
    return SeedCartesianCheckpointWater(Config,Water,Destination);
}

bool ARaftSimRunManager::SeedCartesianCheckpointWater(const ARaftSimRiverWaterConfig* Config,
    URaftSimWaterRuntimeAdapter* Water, FTransform& Checkpoint)
{
    if (!Config || !Water || !Water->HasCartesianWaterCoordinates() || !Checkpoint.IsValid()) return false;
    if (!FRaftSimCartesianWaterRegions::ConfigureAtWorldPosition(Water, Config->StreamingManifestPath,
        Config->FlowBand.ToString(), Checkpoint.GetLocation())) return false;
    FRaftSimWaterSample Sample;
    if (!Water->SampleWaterAtWorldPosition(Checkpoint.GetLocation(),Sample) || !Sample.bWet) return false;
    FVector Position = Checkpoint.GetLocation();
    Position.Z = Sample.SurfaceHeightMeters*100.f+40.f;
    Checkpoint.SetLocation(Position);
    return true;
}

void ARaftSimRunManager::TryRestoreSessionCheckpoint()
{
    if (!bCheckpointRestorePending || bCheckpointRestoreAttempted || Raft == nullptr)
    {
        return;
    }
    URaftSimSaveSubsystem* Save = GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>();
    URaftSimPhysicsBridgeSubsystem* Bridge =
        GetGameInstance()->GetSubsystem<URaftSimPhysicsBridgeSubsystem>();
    URaftSimWaterRuntimeAdapter* Water = Bridge ? Bridge->GetWaterRuntime() : nullptr;
    const URaftSimWaterRuntimeAdapter* Progress = GetProgressCoordinates(Water);
    if (Save == nullptr || Water == nullptr || !Water->HasRiverCoordinateMap() ||
        Progress == nullptr || !Progress->HasRiverCoordinateMap())
    {
        return;
    }
    bCheckpointRestoreAttempted = true;
    // Only when this map is the scenario's own level and the start station
    // lies inside its corridor. Automation opens maps with whatever run the
    // save last selected; reseeding the window at a South Fork station on a
    // 600 m reference map left it dead (P4 RiverMapLoads on Hance, Lava
    // Canyon and Zambezi after the Troublemaker section landed, 2026-09-02).
    FRaftSimCareerScenarioDefinition Definition;
    float MinimumStationM = 0.0f;
    float MaximumStationM = 0.0f;
    const FString MapName = GetWorld()
        ? GetWorld()->GetMapName().Replace(*GetWorld()->StreamingLevelsPrefix, TEXT(""))
        : FString();
    const bool bOwnLevel =
        URaftSimProgressionLibrary::FindScenario(ScenarioId, Definition) &&
        !MapName.IsEmpty() &&
        Definition.LevelName.ToString().EndsWith(TEXT("/") + MapName, ESearchCase::IgnoreCase);
    const bool bInsideCorridor =
        Progress->GetRiverStationRangeM(MinimumStationM, MaximumStationM) &&
        StartStationM >= MinimumStationM && StartStationM <= MaximumStationM;
    if (!bOwnLevel || !bInsideCorridor)
    {
        bCheckpointRestorePending = false;
        return;
    }
    FTransform Checkpoint;
    const float CheckpointCeilingM =
        FinishStationM > StartStationM ? FinishStationM : TNumericLimits<float>::Max();
    float ReviewStationM = -1.0f;
    const bool bReviewStart = FParse::Value(
        FCommandLine::Get(), TEXT("RaftSimWaterReviewStation="), ReviewStationM)
        && GetWorld()->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach"))
        && FMath::IsFinite(ReviewStationM)
        && ReviewStationM >= MinimumStationM && ReviewStationM <= MaximumStationM
        && FMath::IsNearlyEqual(ReviewStationM, StartStationM);
    if (bReviewStart || !Save->FindBestCheckpoint(StartStationM - 25.0f, Checkpoint, CheckpointCeilingM,
            ProgressCoordinateMapPath,Definition.LevelName))
    {
        if (!BuildStationStartTransform(Progress, Water, StartStationM, Checkpoint))
        {
            bCheckpointRestorePending = false;
            return;
        }
        if (bReviewStart)
        {
            UE_LOG(LogTemp, Display,
                TEXT("RaftSim review start: constructing requested station %.3f m; saved checkpoint deliberately bypassed"),
                StartStationM);
        }
        else
        {
            UE_LOG(LogTemp, Display,
                TEXT("RaftSim run: no checkpoint near station %.0f m; starting the section at its start station"),
                StartStationM);
        }
    }
    // A resumed section is an intentional discontinuity. Seed a fresh live
    // window at its saved station before moving the authoritative raft body;
    // normal downstream handoffs remain overlap-preserving after this point.
    if (!RaftSimCheckpointStreaming::Prepare(GetWorld(),Checkpoint))
    {
        UE_LOG(LogTemp,Warning,TEXT("RaftSim section start rejected: destination terrain is not activated; water and raft not moved"));
        bCheckpointRestorePending = false;
        return;
    }
    bool bHydraulicRegionVerified = Progress == Water;
    if (TActorIterator<ARaftSimRiverWaterConfig> It(GetWorld()); It)
    {
        ARaftSimRiverWaterConfig* Config = *It;
        if (Water->HasCartesianWaterCoordinates())
        {
            if (!SeedCartesianCheckpointWater(Config,Water,Checkpoint))
            {
                UE_LOG(LogTemp,Warning,TEXT("RaftSim Cartesian section start rejected: no verified wet destination; raft not moved"));
                bCheckpointRestorePending = false;
                return;
            }
            bHydraulicRegionVerified = true;
        }
        else
        {
        FVector2D HydraulicCenter(StartStationM, 0.0f);
        if (Progress != Water)
        {
            FVector Tangent, Left;
            // Global descent metres are never solver-local metres. Resolve
            // through the shared world position, including lateral offset.
            if (!Water->WorldToRiverCoordinates(Checkpoint.GetLocation(), HydraulicCenter, Tangent, Left) ||
                !Water->GetRiverStationRangeM(MinimumStationM, MaximumStationM) ||
                HydraulicCenter.X < MinimumStationM || HydraulicCenter.X > MaximumStationM)
            {
                bCheckpointRestorePending = false;
                return;
            }
        }
        const bool bSeeded = Water->ConfigureRiverWindow(
            Config->CookedFieldsDir, Config->FlowBand.ToString(),
            HydraulicCenter,
            FVector2D(Config->MovingWindowStationExtentM, Config->MovingWindowLateralExtentM),
            0.041f, Config->bRecenterHydraulicCrux);
        if (Progress != Water)
        {
            FRaftSimWaterSample Sample;
            if (!bSeeded || !Water->SampleWaterAtWorldPosition(Checkpoint.GetLocation(), Sample) || !Sample.bWet)
            {
                UE_LOG(LogTemp, Warning, TEXT("RaftSim global section start has no wet hydraulic region; raft not moved"));
                bCheckpointRestorePending = false;
                return;
            }
            FVector Position = Checkpoint.GetLocation();
            Position.Z = Sample.SurfaceHeightMeters * 100.0f + 40.0f;
            Checkpoint.SetLocation(Position);
            bHydraulicRegionVerified = true;
        }
        }
    }
    if (!bHydraulicRegionVerified)
    {
        bCheckpointRestorePending = false;
        return;
    }
    if (!Raft->TryRestoreCheckpoint(Checkpoint))
    {
        bCheckpointRestorePending = false;
        return;
    }
    if (bReviewStart)
    {
        // Report the applied raft pose, not only the requested input. This
        // remains diagnostic: failed streaming/wetness/restore paths above
        // must never emit a successful review-start record.
        LastProgressSample.bValid = false;
        float AppliedStationM = 0.f;
        FVector AppliedPositionCm = Raft->GetActorLocation();
        const bool bSampled = SampleRiverStation(AppliedStationM, nullptr, &AppliedPositionCm);
        UE_LOG(LogTemp, Display,
            TEXT("RaftSim review start applied: requested_station_m=%.3f sampled=%d applied_station_m=%.3f world_cm=(%.6f,%.6f,%.6f) destination_error_cm=%.9g"),
            StartStationM, bSampled, AppliedStationM,
            AppliedPositionCm.X, AppliedPositionCm.Y, AppliedPositionCm.Z,
            FVector::Distance(AppliedPositionCm, Checkpoint.GetLocation()));
    }
    CurrentStationM = StartStationM;
    FurthestStationM = StartStationM;
    LastCheckpointStationM = StartStationM;
    bCheckpointRestorePending = false;
}

void ARaftSimRunManager::StartRun()
{
    RunState = ERaftSimRunState::Running;
    RunTimeSeconds = 0.0f;
    SafetyIncidents = 0;
    SwimCount = 0;
    AngleErrorAccumDeg = 0.0f;
    AngleSampleSeconds = 0.0f;
    CurrentGhostRoute.Reset();
    GhostSampleRemaining = 0.0f;
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

    // Boat-angle error uses the curved river tangent when available.
    const float Yaw = Raft->GetActorRotation().Yaw;
    FVector RiverTangent;
    float Station = CurrentStationM;
    const float DownstreamYaw = SampleRiverStation(Station, &RiverTangent)
        ? RiverTangent.Rotation().Yaw : 0.0f;
    float AngleErr = FMath::Abs(FMath::FindDeltaAngleDegrees(Yaw, DownstreamYaw));
    AngleErrorAccumDeg += AngleErr * DeltaSeconds;
    AngleSampleSeconds += DeltaSeconds;

    GhostSampleRemaining -= DeltaSeconds;
    if (GhostSampleRemaining <= 0.0f)
    {
        if (CurrentGhostRoute.IsEmpty() ||
            FVector::DistSquared(CurrentGhostRoute.Last(), Raft->GetActorLocation()) > FMath::Square(2500.0f))
        {
            CurrentGhostRoute.Add(Raft->GetActorLocation());
        }
        GhostSampleRemaining = 1.0f;
    }

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
    LastProgressSample.bValid = false;
    if (Raft == nullptr)
    {
        return;
    }

    TryRestoreSessionCheckpoint();

    float SampledStation = CurrentStationM;
    FVector SamplePositionCm;
    const bool bHasStation = SampleRiverStation(SampledStation, nullptr, &SamplePositionCm);
    // An explicitly separate progress contract must not silently become an
    // X-axis distance trial when loading/projection fails.
    if (!ProgressCoordinateMapPath.IsEmpty() && !bHasStation) return;
    if (bHasStation)
    {
        CurrentStationM = SampledStation;
        LastProgressSample = { SamplePositionCm, GetWorld()->GetTimeSeconds(), SampledStation, true };
        FurthestStationM = FMath::Max(FurthestStationM, CurrentStationM);
    }

    const float RaftX = Raft->GetActorLocation().X;

    if (RunState == ERaftSimRunState::Ready)
    {
        // Start once the raft leaves the scout eddy / passes the start line.
        const bool bCrossedStart = FinishStationM > StartStationM && bHasStation
            ? CurrentStationM >= StartStationM - 10.0f
            : RaftX >= StartLineX;
        if (bCrossedStart)
        {
            StartRun();
        }
        return;
    }

    if (RunState == ERaftSimRunState::Running)
    {
        RunTimeSeconds += DeltaSeconds;
        AccumulateSignals(DeltaSeconds);
        RecordCheckpointIfNeeded();

        // Finish at the Finish volume if present, else the fallback line.
        bool bFinished = FinishStationM > StartStationM && bHasStation
            ? CurrentStationM >= FinishStationM
            : RaftX >= FinishLineX;
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

void ARaftSimRunManager::RecordCheckpointIfNeeded()
{
    if (GameModeKind != ERaftSimGameMode::GuidedDescent || StartStationM < 0.0f ||
        CurrentStationM < LastCheckpointStationM + 1000.0f || Raft == nullptr)
    {
        return;
    }
    LastCheckpointStationM = CurrentStationM;
    Raft->SetCheckpointTransform(Raft->GetActorTransform(), false);
    if (URaftSimSaveSubsystem* Save = GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>())
    {
        Save->RecordCareerCheckpoint(
            ScenarioId,
            FName(*FString::Printf(TEXT("%s_%05d"), *ScenarioId.ToString(),
                FMath::RoundToInt(CurrentStationM))),
            CurrentStationM, Raft->GetActorTransform(), ProgressCoordinateMapPath);
    }
}

void ARaftSimRunManager::RestartRun()
{
    if (Raft != nullptr && !Raft->TryResetToCheckpoint()) return;
    LastProgressSample.bValid = false;
    RunState = ERaftSimRunState::Ready;
    FinalScore = FRaftSimGameplayScoreBreakdown{};
    AwardedMedal = ERaftSimMedal::None;
    AfterActionSummary = FText::GetEmpty();
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
            FRaftSimRunResult Result;
            Result.ScenarioId = ScenarioId;
            Result.CoordinateMapPath = ProgressCoordinateMapPath;
            Result.GameMode = GameModeKind;
            Result.SafetyScore = FinalScore.SafetyScore;
            Result.OverallScore = FinalScore.TotalScore;
            Result.RunTimeSeconds = RunTimeSeconds;
            Result.SafetyIncidentCount = SafetyIncidents;
            Result.SwimCount = SwimCount;
            Result.FurthestStationM = FurthestStationM;
            Result.bAssistUsed = bAssistUsed;
            Result.GhostRoute = CurrentGhostRoute;
            AwardedMedal = Save->RecordRunResult(Result);
        }
    }
    AfterActionSummary = FText::Format(
        NSLOCTEXT("RaftSim", "AfterActionSummary",
            "{0} — score {1}, safety {2}, line {3}, angle {4}; {5} incident(s), {6} swim(s), {7}s"),
        URaftSimProgressionLibrary::MedalDisplayName(AwardedMedal),
        FText::AsNumber(FMath::RoundToInt(FinalScore.TotalScore * 100.0f)),
        FText::AsNumber(FMath::RoundToInt(FinalScore.SafetyScore * 100.0f)),
        FText::AsNumber(FMath::RoundToInt(FinalScore.LineChoiceScore * 100.0f)),
        FText::AsNumber(FMath::RoundToInt(FinalScore.BoatAngleScore * 100.0f)),
        FText::AsNumber(SafetyIncidents), FText::AsNumber(SwimCount),
        FText::AsNumber(FMath::RoundToInt(RunTimeSeconds)));
}
