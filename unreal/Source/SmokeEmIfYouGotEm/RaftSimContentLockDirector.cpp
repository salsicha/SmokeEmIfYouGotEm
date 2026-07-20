#include "RaftSimContentLockDirector.h"

#include "Dom/JsonObject.h"
#include "Engine/Engine.h"
#include "GenericPlatform/GenericPlatformProperties.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMemory.h"
#include "HAL/PlatformMisc.h"
#include "HAL/PlatformTime.h"
#include "HAL/IConsoleManager.h"
#include "Misc/App.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/Parse.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RenderTimer.h"
#include "DynamicRHI.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "UnrealEngine.h"

namespace
{
constexpr const TCHAR* RapidMatrixManifest = TEXT(
    "physics/data/real_world/south_fork_american_chili_bar/full_hydraulics/manifest.json");
constexpr float SolverBudgetMilliseconds = 1.6f;
constexpr float FrameBudgetMilliseconds = 1000.0f / 60.0f;
constexpr float HitchBudgetMilliseconds = 33.0f;
constexpr float MemoryBudgetMegabytes = 8192.0f;

bool LoadJson(const FString& Path, TSharedPtr<FJsonObject>& OutRoot)
{
    FString Text;
    if (!FFileHelper::LoadFileToString(Text, *Path))
    {
        return false;
    }
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Text);
    return FJsonSerializer::Deserialize(Reader, OutRoot) && OutRoot.IsValid();
}

FString SerializeJson(const TSharedRef<FJsonObject>& Root)
{
    FString Text;
    const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Text);
    FJsonSerializer::Serialize(Root, Writer);
    return Text;
}

bool EveryFeatureEnvelopePassed(const TSharedPtr<FJsonObject>& Band)
{
    const TSharedPtr<FJsonObject>* Validation = nullptr;
    const TArray<TSharedPtr<FJsonValue>>* Envelopes = nullptr;
    bool bValidationPassed = false;
    if (!Band.IsValid() ||
        !Band->TryGetObjectField(TEXT("validation"), Validation) || Validation == nullptr ||
        !(*Validation)->TryGetBoolField(TEXT("passed"), bValidationPassed) ||
        !(*Validation)->TryGetArrayField(TEXT("feature_envelopes"), Envelopes) || Envelopes == nullptr)
    {
        return false;
    }
    for (const TSharedPtr<FJsonValue>& Value : *Envelopes)
    {
        const TSharedPtr<FJsonObject> Envelope = Value->AsObject();
        bool bPassed = false;
        if (!Envelope.IsValid() || !Envelope->TryGetBoolField(TEXT("passed"), bPassed) || !bPassed)
        {
            return false;
        }
    }
    return bValidationPassed;
}

struct FFrameSeriesSummary
{
    float Mean = BIG_NUMBER;
    float P95 = BIG_NUMBER;
    float Max = BIG_NUMBER;
};

FFrameSeriesSummary SummarizeFrameSeries(TArray<float>& Samples)
{
    FFrameSeriesSummary Summary;
    if (Samples.IsEmpty())
    {
        return Summary;
    }
    Samples.Sort();
    double Total = 0.0;
    for (const float Sample : Samples)
    {
        Total += Sample;
    }
    Summary.Mean = static_cast<float>(Total / Samples.Num());
    Summary.P95 = Samples[FMath::Clamp(
        FMath::CeilToInt(Samples.Num() * 0.95f) - 1, 0, Samples.Num() - 1)];
    Summary.Max = Samples.Last();
    return Summary;
}
}

ARaftSimContentLockDirector::ARaftSimContentLockDirector()
{
    PrimaryActorTick.bCanEverTick = true;
}

bool ARaftSimContentLockDirector::IsPackagedRegressionRequested()
{
    return FParse::Param(FCommandLine::Get(), TEXT("RaftSimPackagedRegression"));
}

bool ARaftSimContentLockDirector::IsPerformanceCaptureRequested()
{
    float SoakSeconds = 0.0f;
    return FParse::Value(
        FCommandLine::Get(), TEXT("RaftSimPerformanceSoakSeconds="), SoakSeconds) &&
        SoakSeconds > 0.0f;
}

void ARaftSimContentLockDirector::BeginPlay()
{
    Super::BeginPlay();
    if (IsPackagedRegressionRequested())
    {
        FString Report;
        const bool bPassed = RunRapidMatrixRegression(Report);
        const FString OutputPath = ResolveOutputPath(
            FString(), TEXT("m8_packaged_rapid_regression.json"));
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(OutputPath), true);
        const bool bSaved = FFileHelper::SaveStringToFile(Report, *OutputPath);
        UE_LOG(LogTemp, Display,
            TEXT("RAFTSIM_M8_PACKAGED_REGRESSION passed=%d saved=%d report=%s"),
            bPassed ? 1 : 0, bSaved ? 1 : 0, *OutputPath);
        FPlatformMisc::RequestExitWithStatus(false, bPassed && bSaved ? 0 : 8);
        return;
    }

    float SoakSeconds = 0.0f;
    if (FParse::Value(
            FCommandLine::Get(), TEXT("RaftSimPerformanceSoakSeconds="), SoakSeconds) &&
        SoakSeconds > 0.0f)
    {
        float WarmupSeconds = 5.0f;
        FParse::Value(
            FCommandLine::Get(), TEXT("RaftSimPerformanceWarmupSeconds="), WarmupSeconds);
        StartPerformanceCapture(SoakSeconds, WarmupSeconds, FString(), true);
    }
}

FString ARaftSimContentLockDirector::ResolveOutputPath(
    const FString& RequestedPath, const TCHAR* DefaultName) const
{
    if (!RequestedPath.IsEmpty())
    {
        return FPaths::ConvertRelativePathToFull(RequestedPath);
    }
    FString CommandLineOutput;
    if (FParse::Value(
            FCommandLine::Get(), TEXT("RaftSimValidationOutput="), CommandLineOutput) &&
        !CommandLineOutput.IsEmpty())
    {
        return FPaths::ConvertRelativePathToFull(CommandLineOutput);
    }
    return FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Validation"), DefaultName);
}

bool ARaftSimContentLockDirector::RunRapidMatrixRegression(FString& OutReportJson)
{
    const FString ManifestPath =
        URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(RapidMatrixManifest);
    TSharedPtr<FJsonObject> Manifest;
    TArray<TSharedPtr<FJsonValue>> CaseReports;
    int32 RapidCount = 0;
    int32 CaseCount = 0;
    int32 PassedCaseCount = 0;
    float MaximumAverageSolverMs = 0.0f;
    float MaximumSingleSolverMs = 0.0f;
    bool bManifestReady = LoadJson(ManifestPath, Manifest);

    const TArray<TSharedPtr<FJsonValue>>* Rapids = nullptr;
    if (bManifestReady)
    {
        bManifestReady = Manifest->TryGetArrayField(TEXT("rapids"), Rapids) && Rapids != nullptr;
    }
    if (bManifestReady)
    {
        RapidCount = Rapids->Num();
        for (const TSharedPtr<FJsonValue>& RapidValue : *Rapids)
        {
            const TSharedPtr<FJsonObject> Rapid = RapidValue->AsObject();
            if (!Rapid.IsValid())
            {
                continue;
            }
            FString RapidName;
            FString CookedManifestRelative;
            Rapid->TryGetStringField(TEXT("rapid_name"), RapidName);
            Rapid->TryGetStringField(TEXT("cooked_fields_manifest"), CookedManifestRelative);
            const FString CookedManifestPath =
                URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(CookedManifestRelative);
            TSharedPtr<FJsonObject> Cooked;
            const bool bCookedReady = LoadJson(CookedManifestPath, Cooked);
            const TSharedPtr<FJsonObject>* Grid = nullptr;
            const TArray<TSharedPtr<FJsonValue>>* Bands = nullptr;
            if (!bCookedReady || !Cooked->TryGetObjectField(TEXT("grid"), Grid) || Grid == nullptr ||
                !Cooked->TryGetArrayField(TEXT("bands"), Bands) || Bands == nullptr)
            {
                continue;
            }

            const int32 Nx = (*Grid)->GetIntegerField(TEXT("nx"));
            const int32 Ny = (*Grid)->GetIntegerField(TEXT("ny"));
            const double Dx = (*Grid)->GetNumberField(TEXT("dx_m"));
            const double Dy = (*Grid)->GetNumberField(TEXT("dy_m"));
            const double OriginX = (*Grid)->GetNumberField(TEXT("origin_x_m"));
            const double OriginY = (*Grid)->GetNumberField(TEXT("origin_y_m"));
            const FVector2D Center(
                OriginX + Dx * static_cast<double>(Nx - 1) * 0.5,
                OriginY + Dy * static_cast<double>(Ny - 1) * 0.5);
            const FVector2D Extent(Dx * Nx, Dy * Ny);
            const FString CookedDir = FPaths::GetPath(CookedManifestRelative);

            for (const TSharedPtr<FJsonValue>& BandValue : *Bands)
            {
                ++CaseCount;
                const TSharedPtr<FJsonObject> Band = BandValue->AsObject();
                FString BandId;
                if (Band.IsValid())
                {
                    Band->TryGetStringField(TEXT("band_id"), BandId);
                }
                const bool bEnvelopePassed = EveryFeatureEnvelopePassed(Band);
                URaftSimWaterRuntimeAdapter* Adapter =
                    NewObject<URaftSimWaterRuntimeAdapter>(GetTransientPackage());
                FRaftSimWaterRuntimeConfig Config;
                Config.bRequireAcceptedReportManifest = false;
                Config.bEnableDeterministicCapture = false;
                Adapter->Configure(Config);
                const bool bConfigured = Adapter->ConfigureRiverWindow(
                    CookedDir, BandId, Center, Extent);

                FRaftSimWaterLiveWindowStats Seeded;
                bool bStepped = bConfigured && Adapter->GetLiveWindowStats(Seeded) &&
                    !Seeded.bHasNonFinite && Seeded.TotalWaterVolumeM3 > 0.0f &&
                    Seeded.SeedWetFraction > 0.0f;
                for (int32 StepIndex = 0; bStepped && StepIndex < 12; ++StepIndex)
                {
                    bStepped = Adapter->StepWater(1.0f / 60.0f);
                }
                FRaftSimWaterLiveWindowStats Stepped;
                bStepped = bStepped && Adapter->GetLiveWindowStats(Stepped);
                const bool bStable = bStepped && !Stepped.bHasNonFinite &&
                    Stepped.TotalWaterVolumeM3 > 0.0f &&
                    FMath::Abs(Stepped.WetFraction - Seeded.SeedWetFraction) <=
                        0.12f * Seeded.SeedWetFraction;
                const bool bWithinSolverBudget = bStable &&
                    Stepped.AverageSolverStepMilliseconds <= SolverBudgetMilliseconds;

                URaftSimWaterRuntimeAdapter* Replay =
                    NewObject<URaftSimWaterRuntimeAdapter>(GetTransientPackage());
                Replay->Configure(Config);
                bool bReplay = Replay->ConfigureRiverWindow(CookedDir, BandId, Center, Extent);
                for (int32 StepIndex = 0; bReplay && StepIndex < 12; ++StepIndex)
                {
                    bReplay = Replay->StepWater(1.0f / 60.0f);
                }
                FRaftSimWaterLiveWindowStats ReplayStats;
                bReplay = bReplay && Replay->GetLiveWindowStats(ReplayStats);
                const bool bDeterministic = bReplay &&
                    FMath::IsNearlyEqual(
                        Stepped.TotalWaterVolumeM3, ReplayStats.TotalWaterVolumeM3, 1.0e-4f) &&
                    FMath::IsNearlyEqual(Stepped.WetFraction, ReplayStats.WetFraction, 1.0e-6f);
                const bool bCasePassed = bEnvelopePassed && bConfigured && bStable &&
                    bWithinSolverBudget && bDeterministic;
                if (bCasePassed)
                {
                    ++PassedCaseCount;
                }
                MaximumAverageSolverMs = FMath::Max(
                    MaximumAverageSolverMs, Stepped.AverageSolverStepMilliseconds);
                MaximumSingleSolverMs = FMath::Max(
                    MaximumSingleSolverMs, Stepped.MaxSolverStepMilliseconds);

                TSharedRef<FJsonObject> Case = MakeShared<FJsonObject>();
                Case->SetStringField(TEXT("rapid"), RapidName);
                Case->SetStringField(TEXT("flow_band"), BandId);
                Case->SetBoolField(TEXT("hash_verified_fields_loaded"), bConfigured);
                Case->SetBoolField(TEXT("feature_envelopes_passed"), bEnvelopePassed);
                Case->SetBoolField(TEXT("finite_and_mass_stable"), bStable);
                Case->SetBoolField(TEXT("deterministic_replay"), bDeterministic);
                Case->SetNumberField(
                    TEXT("average_solver_step_ms"), Stepped.AverageSolverStepMilliseconds);
                Case->SetNumberField(TEXT("max_solver_step_ms"), Stepped.MaxSolverStepMilliseconds);
                Case->SetBoolField(TEXT("passed"), bCasePassed);
                CaseReports.Add(MakeShared<FJsonValueObject>(Case));
            }
        }
    }

    const bool bPassed = bManifestReady && RapidCount == 20 && CaseCount == 60 &&
        PassedCaseCount == CaseCount && MaximumAverageSolverMs <= SolverBudgetMilliseconds;
    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(TEXT("schema"), TEXT("raftsim.m8.packaged_rapid_regression.v1"));
    Report->SetStringField(
        TEXT("platform"), ANSI_TO_TCHAR(FPlatformProperties::IniPlatformName()));
    Report->SetStringField(TEXT("build_configuration"), LexToString(FApp::GetBuildConfiguration()));
    Report->SetStringField(TEXT("runtime_data_manifest"), ManifestPath);
    Report->SetBoolField(TEXT("running_from_packaged_build"), FPlatformProperties::RequiresCookedData());
    Report->SetBoolField(TEXT("live_solver_compiled"), RAFTSIM_HAS_LIVE_SOLVER != 0);
    Report->SetNumberField(TEXT("rapid_count"), RapidCount);
    Report->SetNumberField(TEXT("case_count"), CaseCount);
    Report->SetNumberField(TEXT("passed_case_count"), PassedCaseCount);
    Report->SetNumberField(TEXT("solver_budget_ms"), SolverBudgetMilliseconds);
    Report->SetNumberField(TEXT("max_case_average_solver_ms"), MaximumAverageSolverMs);
    Report->SetNumberField(TEXT("max_single_solver_step_ms"), MaximumSingleSolverMs);
    Report->SetBoolField(TEXT("passed"), bPassed);
    Report->SetArrayField(TEXT("cases"), CaseReports);
    OutReportJson = SerializeJson(Report);
    return bPassed;
}

void ARaftSimContentLockDirector::StartPerformanceCapture(
    float DurationSeconds, float WarmupSeconds, const FString& OutputPath,
    bool bExitWhenComplete)
{
    bCapturingPerformance = true;
    bPerformanceCaptureComplete = false;
    bPerformanceCapturePassed = false;
    bExitAfterPerformanceCapture = bExitWhenComplete;
    PerformanceWarmupRemaining = FMath::Max(0.0f, WarmupSeconds);
    PerformanceCaptureRemaining = FMath::Max(1.0f, DurationSeconds);
    bProfileGpuAtWarmupEnd = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimProfileGpuAtWarmupEnd"));
    PerformanceOutputPath = ResolveOutputPath(
        OutputPath, TEXT("m8_full_reach_performance_soak.json"));
    CapturedWorkloadFrameMilliseconds.Reset();
    CapturedWallClockFrameMilliseconds.Reset();
    CapturedGameThreadMilliseconds.Reset();
    CapturedRenderThreadMilliseconds.Reset();
    CapturedGpuMilliseconds.Reset();
    LastGameDeltaMilliseconds = 0.0f;
    LastPerformanceTickSeconds = FPlatformTime::Seconds();
}

void ARaftSimContentLockDirector::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!bCapturingPerformance)
    {
        return;
    }
    const double NowSeconds = FPlatformTime::Seconds();
    const float WallDeltaSeconds = static_cast<float>(FMath::Max(
        NowSeconds - LastPerformanceTickSeconds, 0.0));
    LastPerformanceTickSeconds = NowSeconds;
    LastGameDeltaMilliseconds = DeltaSeconds * 1000.0f;
    if (PerformanceWarmupRemaining > 0.0f)
    {
        PerformanceWarmupRemaining -= WallDeltaSeconds;
        if (PerformanceWarmupRemaining <= 0.0f && bProfileGpuAtWarmupEnd && GEngine != nullptr)
        {
            GEngine->Exec(GetWorld(), TEXT("ProfileGPU"));
            bProfileGpuAtWarmupEnd = false;
        }
        return;
    }
    const float GameThreadMilliseconds = FPlatformTime::ToMilliseconds(GGameThreadTime);
    const float RenderThreadMilliseconds = FPlatformTime::ToMilliseconds(GRenderThreadTime);
    const float GpuMilliseconds = FPlatformTime::ToMilliseconds(RHIGetGPUFrameCycles());
    CapturedWallClockFrameMilliseconds.Add(WallDeltaSeconds * 1000.0f);
    CapturedGameThreadMilliseconds.Add(GameThreadMilliseconds);
    CapturedRenderThreadMilliseconds.Add(RenderThreadMilliseconds);
    CapturedGpuMilliseconds.Add(GpuMilliseconds);
    CapturedWorkloadFrameMilliseconds.Add(FMath::Max3(
        GameThreadMilliseconds, RenderThreadMilliseconds, GpuMilliseconds));
    PerformanceCaptureRemaining -= WallDeltaSeconds;
    if (PerformanceCaptureRemaining <= 0.0f)
    {
        FinishPerformanceCapture();
    }
}

void ARaftSimContentLockDirector::FinishPerformanceCapture()
{
    bCapturingPerformance = false;
    const int32 FrameCount = CapturedWorkloadFrameMilliseconds.Num();
    PerformanceHitchCount = 0;
    for (const float WallClockMilliseconds : CapturedWallClockFrameMilliseconds)
    {
        if (WallClockMilliseconds > HitchBudgetMilliseconds)
        {
            ++PerformanceHitchCount;
        }
    }
    const FFrameSeriesSummary Workload = SummarizeFrameSeries(CapturedWorkloadFrameMilliseconds);
    const FFrameSeriesSummary WallClock = SummarizeFrameSeries(CapturedWallClockFrameMilliseconds);
    const FFrameSeriesSummary GameThread = SummarizeFrameSeries(CapturedGameThreadMilliseconds);
    const FFrameSeriesSummary RenderThread = SummarizeFrameSeries(CapturedRenderThreadMilliseconds);
    const FFrameSeriesSummary Gpu = SummarizeFrameSeries(CapturedGpuMilliseconds);
    PerformanceP95FrameMilliseconds = Workload.P95;
    PerformanceP95WallClockMilliseconds = WallClock.P95;

    FRaftSimWaterLiveWindowStats WaterStats;
    bool bHasWaterStats = false;
    if (const UGameInstance* GI = GetGameInstance())
    {
        if (const URaftSimPhysicsBridgeSubsystem* Bridge =
                GI->GetSubsystem<URaftSimPhysicsBridgeSubsystem>())
        {
            bHasWaterStats = Bridge->GetWaterRuntime() != nullptr &&
                Bridge->GetWaterRuntime()->GetLiveWindowStats(WaterStats);
        }
    }
    const FPlatformMemoryStats Memory = FPlatformMemory::GetStats();
    const float PeakMemoryMb = static_cast<float>(Memory.PeakUsedPhysical) / (1024.0f * 1024.0f);
    // Workload time is the same max(game, render, GPU) definition used by
    // Unreal's built-in FPS charts. Wall-clock cadence is retained separately
    // for hitch detection because an unfocused macOS window can be presentation
    // throttled even when every engine pipeline stays comfortably inside 60 Hz.
    const bool bFramePass = Workload.P95 <= FrameBudgetMilliseconds &&
        PerformanceHitchCount == 0;
    const bool bSolverPass = bHasWaterStats &&
        WaterStats.AverageSolverStepMilliseconds <= SolverBudgetMilliseconds;
    const bool bMemoryPass = PeakMemoryMb <= MemoryBudgetMegabytes;
    bPerformanceCapturePassed = bFramePass && bSolverPass && bMemoryPass;
    bPerformanceCaptureComplete = true;

    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(TEXT("schema"), TEXT("raftsim.m8.full_reach_performance_soak.v1"));
    Report->SetStringField(
        TEXT("platform"), ANSI_TO_TCHAR(FPlatformProperties::IniPlatformName()));
    Report->SetStringField(TEXT("build_configuration"), LexToString(FApp::GetBuildConfiguration()));
    Report->SetStringField(TEXT("cpu_brand"), FPlatformMisc::GetCPUBrand());
    Report->SetStringField(TEXT("gpu_brand"), FPlatformMisc::GetPrimaryGPUBrand());
    Report->SetBoolField(TEXT("running_from_packaged_build"), FPlatformProperties::RequiresCookedData());
    Report->SetBoolField(TEXT("application_has_focus"), FApp::HasFocus());
    Report->SetBoolField(TEXT("unattended"), FApp::IsUnattended());
    Report->SetNumberField(
        TEXT("effective_time_dilation"),
        GetWorldSettings() != nullptr
            ? GetWorldSettings()->GetEffectiveTimeDilation()
            : 1.0f);
    Report->SetNumberField(TEXT("last_game_delta_ms"), LastGameDeltaMilliseconds);
    Report->SetNumberField(TEXT("sampled_frame_count"), FrameCount);
    Report->SetNumberField(TEXT("output_resolution_x"), GSystemResolution.ResX);
    Report->SetNumberField(TEXT("output_resolution_y"), GSystemResolution.ResY);
    if (const IConsoleVariable* ScreenPercentage =
            IConsoleManager::Get().FindConsoleVariable(TEXT("r.ScreenPercentage")))
    {
        Report->SetNumberField(TEXT("screen_percentage"), ScreenPercentage->GetFloat());
    }
    Report->SetStringField(
        TEXT("frame_time_definition"), TEXT("max(game_thread,render_thread,gpu)"));
    Report->SetNumberField(TEXT("mean_frame_ms"), Workload.Mean);
    Report->SetNumberField(TEXT("p95_frame_ms"), Workload.P95);
    Report->SetNumberField(TEXT("max_frame_ms"), Workload.Max);
    Report->SetNumberField(TEXT("mean_wall_clock_frame_ms"), WallClock.Mean);
    Report->SetNumberField(TEXT("p95_wall_clock_frame_ms"), WallClock.P95);
    Report->SetNumberField(TEXT("max_wall_clock_frame_ms"), WallClock.Max);
    Report->SetNumberField(TEXT("p95_game_thread_ms"), GameThread.P95);
    Report->SetNumberField(TEXT("p95_render_thread_ms"), RenderThread.P95);
    Report->SetNumberField(TEXT("p95_gpu_ms"), Gpu.P95);
    Report->SetNumberField(TEXT("hitches_over_33ms"), PerformanceHitchCount);
    Report->SetNumberField(TEXT("frame_budget_ms"), FrameBudgetMilliseconds);
    Report->SetNumberField(
        TEXT("average_solver_step_ms"), WaterStats.AverageSolverStepMilliseconds);
    Report->SetNumberField(TEXT("max_solver_step_ms"), WaterStats.MaxSolverStepMilliseconds);
    Report->SetNumberField(TEXT("solver_budget_ms"), SolverBudgetMilliseconds);
    Report->SetNumberField(TEXT("peak_used_physical_mb"), PeakMemoryMb);
    Report->SetNumberField(TEXT("memory_budget_mb"), MemoryBudgetMegabytes);
    Report->SetBoolField(TEXT("frame_budget_passed"), bFramePass);
    Report->SetBoolField(TEXT("solver_budget_passed"), bSolverPass);
    Report->SetBoolField(TEXT("memory_budget_passed"), bMemoryPass);
    Report->SetBoolField(TEXT("passed"), bPerformanceCapturePassed);
    const FString Json = SerializeJson(Report);
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(PerformanceOutputPath), true);
    const bool bSaved = FFileHelper::SaveStringToFile(Json, *PerformanceOutputPath);
    UE_LOG(LogTemp, Display,
        TEXT("RAFTSIM_M8_PERFORMANCE passed=%d frames=%d p95_ms=%.3f hitches=%d solver_ms=%.3f memory_mb=%.1f saved=%d report=%s"),
        bPerformanceCapturePassed ? 1 : 0, FrameCount, PerformanceP95FrameMilliseconds,
        PerformanceHitchCount, WaterStats.AverageSolverStepMilliseconds, PeakMemoryMb,
        bSaved ? 1 : 0, *PerformanceOutputPath);
    if (bExitAfterPerformanceCapture)
    {
        FPlatformMisc::RequestExitWithStatus(
            false, bPerformanceCapturePassed && bSaved ? 0 : 9);
    }
}
