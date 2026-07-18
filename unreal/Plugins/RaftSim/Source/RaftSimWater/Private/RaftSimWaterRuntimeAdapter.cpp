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
        // World position arrives in centimeters; the solver window is meters.
        const FRaftSimLiveWaterSampleResult Live =
            LiveWindow->Sample(FVector2D(WorldPosition.X / 100.0, WorldPosition.Y / 100.0));
        if (Live.bValid)
        {
            OutSample.SurfaceHeightMeters = Live.SurfaceHeightM;
            OutSample.BedHeightMeters = Live.BedHeightM;
            OutSample.DepthMeters = Live.DepthM;
            OutSample.VelocityMetersPerSecond =
                FVector(Live.VelocityMps.X, Live.VelocityMps.Y, 0.0f);
            OutSample.SurfaceNormal = Live.SurfaceNormal;
            OutSample.bWet = Live.bWet;
            return true;
        }
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
    if (Status == ERaftSimWaterRuntimeStatus::Uninitialized)
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
