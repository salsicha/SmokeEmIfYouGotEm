#include "RaftSimWaterRuntimeAdapter.h"

#include "RaftSimLiveWaterWindow.h"

URaftSimWaterRuntimeAdapter::~URaftSimWaterRuntimeAdapter() = default;

#include "Dom/JsonObject.h"
#include "HAL/FileManager.h"
#include "Misc/Crc.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

void URaftSimWaterRuntimeAdapter::Configure(const FRaftSimWaterRuntimeConfig& InConfig)
{
    Config = InConfig;
    CaptureState = FRaftSimWaterDeterministicCaptureState();
    CaptureState.CapturePath = Config.DeterministicCapturePath;
    CaptureState.bEnabled = Config.bEnableDeterministicCapture;
    CommittedWaterFrame = 0;
    SimTimeSeconds = 0.0;
    LastHandoffTransferredCellCount = 0;
    MovingWindowHandoffCount = 0;
    bLastHandoffPreservedState = false;
    RiverCoordinatePoints.Reset();
    RiverSpatialHash.Reset();
    RiverVerticalDatumM = 0.0f;
    RiverCoordinateMapPath.Reset();

    bool bManifestReady = !Config.bRequireAcceptedReportManifest;
    if (!Config.AcceptedReportSetManifestPath.IsEmpty())
    {
        bManifestReady = LoadAcceptedReportManifest(Config.AcceptedReportSetManifestPath);
    }

    Status = (!Config.ScenarioPackagePath.IsEmpty() && bManifestReady)
        ? ERaftSimWaterRuntimeStatus::ScenarioBound
        : ERaftSimWaterRuntimeStatus::Uninitialized;
}

bool URaftSimWaterRuntimeAdapter::LoadAcceptedReportManifest(const FString& ManifestPath)
{
    ReportManifestState = FRaftSimWaterReportManifestState();
    ReportManifestState.ManifestPath = ManifestPath;

    FString ManifestText;
    const FString FullPath = ResolveRepoRelativePath(ManifestPath);
    if (!FFileHelper::LoadFileToString(ManifestText, *FullPath))
    {
        Status = ERaftSimWaterRuntimeStatus::Faulted;
        return false;
    }

    TSharedPtr<FJsonObject> Root;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ManifestText);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        Status = ERaftSimWaterRuntimeStatus::Faulted;
        return false;
    }

    FString Schema;
    const bool bSchemaOk = Root->TryGetStringField(TEXT("schema"), Schema)
        && Schema == TEXT("raftsim.milestone20.report_set_lock.v1");
    bool bPassed = false;
    Root->TryGetBoolField(TEXT("passed"), bPassed);

    const TSharedPtr<FJsonObject>* LockObject = nullptr;
    if (Root->TryGetObjectField(TEXT("lock"), LockObject)
        && LockObject != nullptr
        && LockObject->IsValid())
    {
        (*LockObject)->TryGetStringField(TEXT("lock_hash"), ReportManifestState.LockHash);
        ReportManifestState.LockedArtifactCount = (*LockObject)->GetIntegerField(TEXT("artifact_count"));
    }

    const TSharedPtr<FJsonObject>* ProductionUse = nullptr;
    bool bLiveWaterBridgeUnblocked = false;
    if (Root->TryGetObjectField(TEXT("production_use"), ProductionUse)
        && ProductionUse != nullptr
        && ProductionUse->IsValid())
    {
        (*ProductionUse)->TryGetBoolField(
            TEXT("live_water_unreal_bridge_foundation_unblocked"),
            bLiveWaterBridgeUnblocked
        );
    }

    const bool bLockMatches = Config.ExpectedReportSetLockHash.IsEmpty()
        || Config.ExpectedReportSetLockHash == ReportManifestState.LockHash;
    ReportManifestState.bLoaded = true;
    ReportManifestState.bAccepted = bSchemaOk && bPassed && bLockMatches;
    ReportManifestState.bLiveWaterBridgeUnblocked =
        ReportManifestState.bAccepted && bLiveWaterBridgeUnblocked;
    return ReportManifestState.bLiveWaterBridgeUnblocked;
}

bool URaftSimWaterRuntimeAdapter::StepWater(float DeltaSeconds)
{
    if (Status == ERaftSimWaterRuntimeStatus::Uninitialized || DeltaSeconds <= 0.0f)
    {
        return false;
    }

    if (Config.bRequireAcceptedReportManifest && !ReportManifestState.bLiveWaterBridgeUnblocked)
    {
        Status = ERaftSimWaterRuntimeStatus::Faulted;
        return false;
    }

    Status = ERaftSimWaterRuntimeStatus::Running;
#if RAFTSIM_HAS_LIVE_SOLVER
    if (LiveWindow.IsValid())
    {
        LiveWindow->Step(DeltaSeconds);
    }
#endif
    SimTimeSeconds += DeltaSeconds;
    ++CommittedWaterFrame;
    AppendDeterministicCaptureFrame();
    return true;
}

bool URaftSimWaterRuntimeAdapter::SampleWaterAtWorldPosition(
    const FVector& WorldPosition,
    FRaftSimWaterSample& OutSample
) const
{
    if (Status == ERaftSimWaterRuntimeStatus::Uninitialized)
    {
        return false;
    }

    OutSample.WorldPosition = WorldPosition;
#if RAFTSIM_HAS_LIVE_SOLVER
    if (LiveWindow.IsValid())
    {
        FVector2D SolverPositionM(WorldPosition.X / 100.0, WorldPosition.Y / 100.0);
        FVector WorldTangent = FVector::ForwardVector;
        FVector WorldLeftNormal = FVector::RightVector;
        if (HasRiverCoordinateMap() &&
            !WorldToRiverCoordinates(
                WorldPosition, SolverPositionM, WorldTangent, WorldLeftNormal))
        {
            return false;
        }
        const FRaftSimLiveWaterSampleResult Live = LiveWindow->Sample(SolverPositionM);
        if (Live.bValid)
        {
            OutSample.SurfaceHeightMeters = Live.SurfaceHeightM - RiverVerticalDatumM;
            OutSample.BedHeightMeters = Live.BedHeightM - RiverVerticalDatumM;
            OutSample.DepthMeters = Live.DepthM;
            OutSample.VelocityMetersPerSecond =
                WorldTangent * Live.VelocityMps.X +
                WorldLeftNormal * Live.VelocityMps.Y;
            OutSample.SurfaceNormal = (
                WorldTangent * Live.SurfaceNormal.X +
                WorldLeftNormal * Live.SurfaceNormal.Y +
                FVector::UpVector * Live.SurfaceNormal.Z).GetSafeNormal();
            OutSample.bWet = Live.bWet;
            return true;
        }
        // A live window is authoritative over its finite crop. Outside that
        // crop there is no fallback sheet of water.
        return false;
    }
#endif
    OutSample.SurfaceHeightMeters = WorldPosition.Z;
    OutSample.BedHeightMeters = WorldPosition.Z - 1.0f;
    OutSample.DepthMeters = 1.0f;
    OutSample.VelocityMetersPerSecond = FVector::ZeroVector;
    OutSample.SurfaceNormal = FVector::UpVector;
    OutSample.bWet = true;
    return true;
}

FIntPoint URaftSimWaterRuntimeAdapter::RiverSpatialHashKey(
    const FVector2D& PositionM) const
{
    return FIntPoint(
        FMath::FloorToInt(PositionM.X / RiverSpatialHashCellM),
        FMath::FloorToInt(PositionM.Y / RiverSpatialHashCellM));
}

void URaftSimWaterRuntimeAdapter::RebuildRiverSpatialHash()
{
    RiverSpatialHash.Reset();
    for (int32 PointIndex = 0; PointIndex < RiverCoordinatePoints.Num(); ++PointIndex)
    {
        RiverSpatialHash.FindOrAdd(
            RiverSpatialHashKey(RiverCoordinatePoints[PointIndex].LocalPositionM)).Add(PointIndex);
    }
}

bool URaftSimWaterRuntimeAdapter::ConfigureRiverCoordinateMap(
    const FString& CoordinateMapPath)
{
    RiverCoordinatePoints.Reset();
    RiverSpatialHash.Reset();
    RiverVerticalDatumM = 0.0f;
    RiverCoordinateMapPath.Reset();

    FString Text;
    const FString FullPath = ResolveRepoRelativePath(CoordinateMapPath);
    if (!FFileHelper::LoadFileToString(Text, *FullPath))
    {
        UE_LOG(LogTemp, Error, TEXT("RaftSim coordinate map not found: %s"), *FullPath);
        return false;
    }
    TSharedPtr<FJsonObject> Root;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Text);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("RaftSim coordinate map JSON is invalid: %s"), *FullPath);
        return false;
    }
    FString Schema;
    if (!Root->TryGetStringField(TEXT("schema"), Schema) ||
        Schema != TEXT("raftsim.curved_river_coordinate_map.v1"))
    {
        UE_LOG(LogTemp, Error, TEXT("RaftSim coordinate map schema is unsupported: %s"), *Schema);
        return false;
    }
    double VerticalDatum = 0.0;
    Root->TryGetNumberField(TEXT("vertical_datum_m"), VerticalDatum);
    RiverVerticalDatumM = static_cast<float>(VerticalDatum);

    const TArray<TSharedPtr<FJsonValue>>* Points = nullptr;
    if (!Root->TryGetArrayField(TEXT("points"), Points) || Points == nullptr || Points->Num() < 2)
    {
        UE_LOG(LogTemp, Error, TEXT("RaftSim coordinate map has fewer than two points"));
        return false;
    }
    RiverCoordinatePoints.Reserve(Points->Num());
    double PreviousStationM = -TNumericLimits<double>::Max();
    for (const TSharedPtr<FJsonValue>& PointValue : *Points)
    {
        const TArray<TSharedPtr<FJsonValue>>* Values = nullptr;
        if (!PointValue.IsValid() || !PointValue->TryGetArray(Values) ||
            Values == nullptr || Values->Num() != 5)
        {
            RiverCoordinatePoints.Reset();
            return false;
        }
        FRiverCoordinatePoint Point;
        Point.StationM = (*Values)[0]->AsNumber();
        Point.LocalPositionM = FVector2D((*Values)[1]->AsNumber(), (*Values)[2]->AsNumber());
        Point.LeftNormal = FVector2D((*Values)[3]->AsNumber(), (*Values)[4]->AsNumber()).GetSafeNormal();
        if (!FMath::IsFinite(Point.StationM) ||
            !FMath::IsFinite(Point.LocalPositionM.X) ||
            !FMath::IsFinite(Point.LocalPositionM.Y) ||
            Point.StationM <= PreviousStationM || Point.LeftNormal.IsNearlyZero())
        {
            RiverCoordinatePoints.Reset();
            return false;
        }
        PreviousStationM = Point.StationM;
        RiverCoordinatePoints.Add(Point);
    }
    double WorldLengthM = 0.0;
    for (int32 PointIndex = 1; PointIndex < RiverCoordinatePoints.Num(); ++PointIndex)
    {
        const FRiverCoordinatePoint& Previous = RiverCoordinatePoints[PointIndex - 1];
        const FRiverCoordinatePoint& Current = RiverCoordinatePoints[PointIndex];
        WorldLengthM += FVector2D::Distance(
            Previous.LocalPositionM, Current.LocalPositionM);
        constexpr float CorridorHalfWidthM = 256.0f;
        const double CorridorEdgeStepM = FMath::Max(
            FVector2D::Distance(
                Previous.LocalPositionM + Previous.LeftNormal * CorridorHalfWidthM,
                Current.LocalPositionM + Current.LeftNormal * CorridorHalfWidthM),
            FVector2D::Distance(
                Previous.LocalPositionM - Previous.LeftNormal * CorridorHalfWidthM,
                Current.LocalPositionM - Current.LeftNormal * CorridorHalfWidthM));
        if (CorridorEdgeStepM > 16.0)
        {
            UE_LOG(
                LogTemp, Error,
                TEXT("RaftSim coordinate map folds its terrain corridor at point %d "
                     "with a %.3f m edge step"),
                PointIndex, CorridorEdgeStepM);
            RiverCoordinatePoints.Reset();
            return false;
        }
    }
    const double StationLengthM =
        RiverCoordinatePoints.Last().StationM - RiverCoordinatePoints[0].StationM;
    if (StationLengthM <= 0.0 ||
        FMath::Abs(WorldLengthM - StationLengthM) / StationLengthM > 0.005)
    {
        UE_LOG(
            LogTemp, Error,
            TEXT("RaftSim coordinate map world length %.3f m does not match its %.3f m station domain"),
            WorldLengthM, StationLengthM);
        RiverCoordinatePoints.Reset();
        return false;
    }
    RebuildRiverSpatialHash();
    RiverCoordinateMapPath = CoordinateMapPath;
    UE_LOG(
        LogTemp, Display,
        TEXT("RaftSim bound curved river map %s (%d points, datum %.3f m)"),
        *CoordinateMapPath, RiverCoordinatePoints.Num(), RiverVerticalDatumM);
    return true;
}

bool URaftSimWaterRuntimeAdapter::WorldToRiverCoordinates(
    const FVector& WorldPositionCm, FVector2D& OutStationLateralM,
    FVector& OutWorldTangent, FVector& OutWorldLeftNormal) const
{
    if (!HasRiverCoordinateMap())
    {
        OutStationLateralM = FVector2D(WorldPositionCm.X / 100.0, WorldPositionCm.Y / 100.0);
        OutWorldTangent = FVector::ForwardVector;
        OutWorldLeftNormal = FVector::RightVector;
        return true;
    }
    const FVector2D PositionM(WorldPositionCm.X / 100.0, WorldPositionCm.Y / 100.0);
    const FIntPoint CenterKey = RiverSpatialHashKey(PositionM);
    TSet<int32> CandidateSegments;
    constexpr int32 QueryRadiusCells = 3;
    for (int32 Y = -QueryRadiusCells; Y <= QueryRadiusCells; ++Y)
    {
        for (int32 X = -QueryRadiusCells; X <= QueryRadiusCells; ++X)
        {
            if (const TArray<int32>* Indices = RiverSpatialHash.Find(CenterKey + FIntPoint(X, Y)))
            {
                for (int32 PointIndex : *Indices)
                {
                    if (PointIndex > 0)
                    {
                        CandidateSegments.Add(PointIndex - 1);
                    }
                    if (PointIndex + 1 < RiverCoordinatePoints.Num())
                    {
                        CandidateSegments.Add(PointIndex);
                    }
                }
            }
        }
    }
    if (CandidateSegments.IsEmpty())
    {
        return false;
    }

    double BestDistanceSquared = TNumericLimits<double>::Max();
    int32 BestSegment = INDEX_NONE;
    double BestAlpha = 0.0;
    for (int32 SegmentIndex : CandidateSegments)
    {
        const FRiverCoordinatePoint& PointA = RiverCoordinatePoints[SegmentIndex];
        const FRiverCoordinatePoint& PointB = RiverCoordinatePoints[SegmentIndex + 1];
        const FVector2D Segment = PointB.LocalPositionM - PointA.LocalPositionM;
        const double LengthSquared = Segment.SquaredLength();
        if (LengthSquared <= UE_DOUBLE_SMALL_NUMBER)
        {
            continue;
        }

        // RiverToWorldPosition describes a ruled corridor, not a simple
        // orthogonal projection onto the centreline: its lateral axis is the
        // normalized interpolation of the two authored endpoint normals.
        // Invert that same surface here. A bounded ternary solve is stable on
        // the dense four-metre coordinate segments and makes the forward/
        // inverse pair agree to well below gameplay centimetre precision.
        auto ReconstructionDistanceSquared =
            [&PointA, &PointB, &PositionM](double Alpha)
        {
            const FVector2D Center = FMath::Lerp(
                PointA.LocalPositionM, PointB.LocalPositionM, Alpha);
            const FVector2D Left = FMath::Lerp(
                PointA.LeftNormal, PointB.LeftNormal, Alpha).GetSafeNormal();
            const double Lateral = FVector2D::DotProduct(PositionM - Center, Left);
            return (PositionM - (Center + Left * Lateral)).SquaredLength();
        };
        double LowerAlpha = 0.0;
        double UpperAlpha = 1.0;
        for (int32 Iteration = 0; Iteration < 24; ++Iteration)
        {
            const double Third = (UpperAlpha - LowerAlpha) / 3.0;
            const double LeftAlpha = LowerAlpha + Third;
            const double RightAlpha = UpperAlpha - Third;
            if (ReconstructionDistanceSquared(LeftAlpha) <=
                ReconstructionDistanceSquared(RightAlpha))
            {
                UpperAlpha = RightAlpha;
            }
            else
            {
                LowerAlpha = LeftAlpha;
            }
        }
        const double Alpha = 0.5 * (LowerAlpha + UpperAlpha);
        const double DistanceSquared = ReconstructionDistanceSquared(Alpha);
        if (DistanceSquared < BestDistanceSquared)
        {
            BestDistanceSquared = DistanceSquared;
            BestSegment = SegmentIndex;
            BestAlpha = Alpha;
        }
    }
    if (BestSegment == INDEX_NONE)
    {
        return false;
    }
    const FRiverCoordinatePoint& A = RiverCoordinatePoints[BestSegment];
    const FRiverCoordinatePoint& B = RiverCoordinatePoints[BestSegment + 1];
    const FVector2D Center = FMath::Lerp(A.LocalPositionM, B.LocalPositionM, BestAlpha);
    const FVector2D Left2D = FMath::Lerp(
        A.LeftNormal, B.LeftNormal, BestAlpha).GetSafeNormal();
    const FVector2D Tangent2D(Left2D.Y, -Left2D.X);
    OutStationLateralM.X = FMath::Lerp(A.StationM, B.StationM, BestAlpha);
    OutStationLateralM.Y = FVector2D::DotProduct(PositionM - Center, Left2D);
    OutWorldTangent = FVector(Tangent2D.X, Tangent2D.Y, 0.0);
    OutWorldLeftNormal = FVector(Left2D.X, Left2D.Y, 0.0);
    return true;
}

bool URaftSimWaterRuntimeAdapter::RiverToWorldPosition(
    FVector2D StationLateralM, float ElevationM, FVector& OutWorldPositionCm) const
{
    if (!HasRiverCoordinateMap())
    {
        OutWorldPositionCm = FVector(
            StationLateralM.X * 100.0, StationLateralM.Y * 100.0,
            (ElevationM - RiverVerticalDatumM) * 100.0);
        return true;
    }
    if (StationLateralM.X < RiverCoordinatePoints[0].StationM ||
        StationLateralM.X > RiverCoordinatePoints.Last().StationM)
    {
        return false;
    }
    int32 Low = 0;
    int32 High = RiverCoordinatePoints.Num() - 1;
    while (Low + 1 < High)
    {
        const int32 Mid = Low + (High - Low) / 2;
        if (RiverCoordinatePoints[Mid].StationM <= StationLateralM.X)
        {
            Low = Mid;
        }
        else
        {
            High = Mid;
        }
    }
    const FRiverCoordinatePoint& A = RiverCoordinatePoints[Low];
    const FRiverCoordinatePoint& B = RiverCoordinatePoints[High];
    const double Alpha = FMath::Clamp(
        (StationLateralM.X - A.StationM) / FMath::Max(B.StationM - A.StationM, 1.0e-9),
        0.0, 1.0);
    const FVector2D Center = FMath::Lerp(A.LocalPositionM, B.LocalPositionM, Alpha);
    const FVector2D LeftNormal = FMath::Lerp(
        A.LeftNormal, B.LeftNormal, Alpha).GetSafeNormal();
    const FVector2D WorldXYM = Center + LeftNormal * StationLateralM.Y;
    OutWorldPositionCm = FVector(
        WorldXYM.X * 100.0, WorldXYM.Y * 100.0,
        (ElevationM - RiverVerticalDatumM) * 100.0);
    return true;
}

bool URaftSimWaterRuntimeAdapter::GetRiverStationRangeM(
    float& OutMinimumStationM, float& OutMaximumStationM) const
{
    if (!HasRiverCoordinateMap())
    {
        OutMinimumStationM = 0.0f;
        OutMaximumStationM = 0.0f;
        return false;
    }
    OutMinimumStationM = static_cast<float>(RiverCoordinatePoints[0].StationM);
    OutMaximumStationM = static_cast<float>(RiverCoordinatePoints.Last().StationM);
    return true;
}

FString URaftSimWaterRuntimeAdapter::BuildDeterministicFrameHash() const
{
    const FString Payload = FString::Printf(
        TEXT("%s|%s|%s|%d|%d|%.9f|%.9f"),
        *Config.RuntimeName,
        *Config.ScenarioPackagePath,
        *ReportManifestState.LockHash,
        Config.DeterministicSeed,
        CommittedWaterFrame,
        Config.FixedStepSeconds,
        SimTimeSeconds
    );
    return FString::Printf(TEXT("%08x"), FCrc::StrCrc32(*Payload));
}

void URaftSimWaterRuntimeAdapter::AppendDeterministicCaptureFrame()
{
    if (!CaptureState.bEnabled || Config.DeterministicCapturePath.IsEmpty())
    {
        return;
    }

    CaptureState.LastFrameHash = BuildDeterministicFrameHash();
    ++CaptureState.CapturedFrameCount;

    const FString CaptureLine = FString::Printf(
        TEXT("{\"frame\":%d,\"time_seconds\":%.9f,\"runtime\":\"%s\",\"report_lock_hash\":\"%s\",\"frame_hash\":\"%s\"}\n"),
        CommittedWaterFrame,
        SimTimeSeconds,
        *Config.RuntimeName,
        *ReportManifestState.LockHash,
        *CaptureState.LastFrameHash
    );
    const FString FullPath = ResolveRepoRelativePath(Config.DeterministicCapturePath);
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(FullPath), true);
    FFileHelper::SaveStringToFile(CaptureLine, *FullPath, FFileHelper::EEncodingOptions::AutoDetect, &IFileManager::Get(), FILEWRITE_Append);
}

FString URaftSimWaterRuntimeAdapter::ResolveRepoRelativePath(const FString& Path) const
{
    if (FPaths::IsRelative(Path))
    {
        const FString RepoRelative = FPaths::ConvertRelativePathToFull(
            FPaths::Combine(FPaths::ProjectDir(), TEXT(".."), Path)
        );
        if (FPaths::FileExists(RepoRelative) || FPaths::DirectoryExists(RepoRelative)
            || Path.StartsWith(TEXT("physics/")))
        {
            return RepoRelative;
        }
        return FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectDir(), Path));
    }
    return Path;
}

bool URaftSimWaterRuntimeAdapter::ConfigureDevTankWindow(
    FVector2D WorldOriginM, float SizeXM, float SizeYM, float CellSizeM,
    float SurfaceHeightM, float DepthM)
{
#if RAFTSIM_HAS_LIVE_SOLVER
    LiveWindow = FRaftSimLiveWaterWindow::CreateFlatTank(
        WorldOriginM, SizeXM, SizeYM, CellSizeM, SurfaceHeightM, DepthM);
    LastHandoffTransferredCellCount = 0;
    bLastHandoffPreservedState = false;
    // Recover from Uninitialized or a prior failed river attempt (Faulted).
    if (Status == ERaftSimWaterRuntimeStatus::Uninitialized
        || Status == ERaftSimWaterRuntimeStatus::Faulted)
    {
        Status = ERaftSimWaterRuntimeStatus::ScenarioBound;
    }
    return LiveWindow.IsValid();
#else
    return false;
#endif
}

bool URaftSimWaterRuntimeAdapter::ConfigureRiverWindow(
    const FString& CookedFieldsManifestDir, const FString& BandId,
    FVector2D WindowCenterM, FVector2D WindowExtentM, float RoughnessManning)
{
#if RAFTSIM_HAS_LIVE_SOLVER
    FString Error;
    LiveWindow = FRaftSimLiveWaterWindow::CreateFromCookedFields(
        ResolveRepoRelativePath(CookedFieldsManifestDir), BandId,
        WindowCenterM, WindowExtentM, RoughnessManning, Error);
    LastHandoffTransferredCellCount = 0;
    bLastHandoffPreservedState = false;
    if (!LiveWindow.IsValid())
    {
        UE_LOG(
            LogTemp, Error,
            TEXT("RaftSim river window '%s' failed to load from %s: %s"),
            *BandId, *CookedFieldsManifestDir, *Error);
        Status = ERaftSimWaterRuntimeStatus::Faulted;
        return false;
    }
    if (Status == ERaftSimWaterRuntimeStatus::Uninitialized
        || Status == ERaftSimWaterRuntimeStatus::Faulted)
    {
        Status = ERaftSimWaterRuntimeStatus::ScenarioBound;
    }
    return true;
#else
    return false;
#endif
}

bool URaftSimWaterRuntimeAdapter::ConfigureMovingRiverWindow(
    const FString& CookedFieldsManifestDir, const FString& BandId,
    FVector2D WindowCenterM, FVector2D WindowExtentM, float RoughnessManning)
{
#if RAFTSIM_HAS_LIVE_SOLVER
    FString Error;
    TUniquePtr<FRaftSimLiveWaterWindow> Candidate =
        FRaftSimLiveWaterWindow::CreateFromCookedFields(
            ResolveRepoRelativePath(CookedFieldsManifestDir), BandId,
            WindowCenterM, WindowExtentM, RoughnessManning, Error,
            /*bRecenterHydraulicCrux=*/false);
    if (!Candidate.IsValid())
    {
        UE_LOG(
            LogTemp, Error,
            TEXT("RaftSim moving river window '%s' failed to load from %s: %s"),
            *BandId, *CookedFieldsManifestDir, *Error);
        Status = ERaftSimWaterRuntimeStatus::Faulted;
        return false;
    }

    LastHandoffTransferredCellCount = 0;
    bLastHandoffPreservedState = false;
    if (LiveWindow.IsValid())
    {
        LastHandoffTransferredCellCount = Candidate->TransferOverlapStateFrom(*LiveWindow);
        if (LastHandoffTransferredCellCount <= 0)
        {
            UE_LOG(
                LogTemp, Error,
                TEXT("RaftSim rejected non-overlapping moving-window handoff for '%s'"),
                *BandId);
            return false;
        }
        ++MovingWindowHandoffCount;
        bLastHandoffPreservedState = true;
    }
    LiveWindow = MoveTemp(Candidate);
    if (Status == ERaftSimWaterRuntimeStatus::Uninitialized ||
        Status == ERaftSimWaterRuntimeStatus::Faulted)
    {
        Status = ERaftSimWaterRuntimeStatus::ScenarioBound;
    }
    return true;
#else
    return false;
#endif
}

bool URaftSimWaterRuntimeAdapter::GetLiveWindowStats(FRaftSimWaterLiveWindowStats& OutStats) const
{
    OutStats = FRaftSimWaterLiveWindowStats();
#if RAFTSIM_HAS_LIVE_SOLVER
    if (LiveWindow.IsValid())
    {
        OutStats.TotalWaterVolumeM3 = static_cast<float>(LiveWindow->TotalWaterVolumeM3());
        OutStats.WetFraction = static_cast<float>(LiveWindow->WetCellFraction());
        OutStats.SeedWetFraction = static_cast<float>(LiveWindow->SeedWetFraction());
        OutStats.bHasNonFinite = LiveWindow->HasNonFiniteState();
        OutStats.SimTimeSeconds = static_cast<float>(LiveWindow->SimTimeSeconds());
        OutStats.LastHandoffTransferredCellCount = LastHandoffTransferredCellCount;
        OutStats.MovingWindowHandoffCount = MovingWindowHandoffCount;
        OutStats.bLastHandoffPreservedState = bLastHandoffPreservedState;
        return true;
    }
#endif
    return false;
}

bool URaftSimWaterRuntimeAdapter::HasLiveWindow() const
{
#if RAFTSIM_HAS_LIVE_SOLVER
    return LiveWindow.IsValid();
#else
    return false;
#endif
}
