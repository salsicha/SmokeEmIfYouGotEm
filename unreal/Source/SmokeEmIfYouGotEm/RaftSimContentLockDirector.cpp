#include "RaftSimContentLockDirector.h"

#include "Dom/JsonObject.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "EngineUtils.h"
#include "GenericPlatform/GenericPlatformProperties.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMemory.h"
#include "HAL/PlatformMisc.h"
#include "HAL/PlatformTime.h"
#include "HAL/IConsoleManager.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/App.h"
#include "Misc/Base64.h"
#include "Misc/CommandLine.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/Parse.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimSaveSubsystem.h"
#include "RaftSimWaterVfxActor.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RenderTimer.h"
#include "DynamicRHI.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "UnrealEngine.h"

#include <cstdio>

namespace
{
constexpr const TCHAR* RapidMatrixManifest = TEXT(
    "physics/data/real_world/south_fork_american_chili_bar/full_hydraulics/manifest.json");
constexpr const TCHAR* FullReachTransitFields = TEXT(
    "physics/data/real_world/south_fork_american_chili_bar/"
    "full_hydraulics/full_reach_transit_seed");
constexpr const TCHAR* ReleaseVersion = TEXT("1.0.0-rc1");
constexpr float SolverBudgetMilliseconds = 1.6f;
constexpr float FrameBudgetMilliseconds = 1000.0f / 60.0f;
constexpr float HitchBudgetMilliseconds = 33.0f;
constexpr float MemoryBudgetMegabytes = 8192.0f;
constexpr float MinimumGpuTimingCeilingMilliseconds = 1000.0f;
constexpr float GpuToWallClockPlausibilityRatio = 16.0f;
constexpr int32 MinimumInvalidGpuTimingSampleBudget = 3;
constexpr const TCHAR* ValidationStdoutMarker = TEXT("RAFTSIM_VALIDATION_JSON_BASE64=");

void EmitValidationReportToStdout(const FString& Report)
{
    if (!FParse::Param(FCommandLine::Get(), TEXT("RaftSimValidationStdout")))
    {
        return;
    }
    const FTCHARToUTF8 Utf8(*Report);
    const FString Encoded = FBase64::Encode(
        reinterpret_cast<const uint8*>(Utf8.Get()), Utf8.Length());
    const FTCHARToUTF8 MarkerUtf8(ValidationStdoutMarker);
    const FTCHARToUTF8 EncodedUtf8(*Encoded);
    std::fprintf(stdout, "%s%s\n", MarkerUtf8.Get(), EncodedUtf8.Get());
    std::fflush(stdout);
}

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

bool RunInputMatrixGate(TSharedRef<FJsonObject> OutGate)
{
    const UInputMappingContext* Context = LoadObject<UInputMappingContext>(
        nullptr, TEXT("/Game/RaftSim/Input/IMC_RaftSimDefault.IMC_RaftSimDefault"));
    const TArray<FString> RequiredActions = {
        TEXT("PaddleStroke"), TEXT("PaddleDraw"), TEXT("Look"), TEXT("HighSide"),
        TEXT("Pause"), TEXT("GuideCommandForwardPaddle"),
        TEXT("GuideCommandBackPaddle"), TEXT("GuideCommandLeftPaddle"),
        TEXT("GuideCommandRightPaddle"), TEXT("GuideCommandStop"),
        TEXT("RescueTargetSelect"), TEXT("RescueReachGrab"),
        TEXT("RescueThrowLine"), TEXT("ReseatCrew")};
    TMap<FString, uint8> DeviceCoverage;
    TArray<TSharedPtr<FJsonValue>> MappingReports;
    if (Context != nullptr)
    {
        for (const FEnhancedActionKeyMapping& Mapping : Context->GetMappings())
        {
            if (Mapping.Action == nullptr || !Mapping.Key.IsValid())
            {
                continue;
            }
            FString ActionId = Mapping.Action->GetName();
            ActionId.RemoveFromStart(TEXT("IA_"));
            const bool bGamepad = Mapping.Key.IsGamepadKey();
            DeviceCoverage.FindOrAdd(ActionId) |= bGamepad ? 2 : 1;

            TSharedRef<FJsonObject> MappingReport = MakeShared<FJsonObject>();
            MappingReport->SetStringField(TEXT("action"), ActionId);
            MappingReport->SetStringField(TEXT("key"), Mapping.Key.GetFName().ToString());
            MappingReport->SetStringField(
                TEXT("device"), bGamepad ? TEXT("gamepad") : TEXT("keyboard_mouse"));
            MappingReports.Add(MakeShared<FJsonValueObject>(MappingReport));
        }
    }

    TArray<TSharedPtr<FJsonValue>> ActionReports;
    int32 CompleteActionCount = 0;
    for (const FString& ActionId : RequiredActions)
    {
        const uint8 Coverage = DeviceCoverage.FindRef(ActionId);
        const bool bKeyboardMouse = (Coverage & 1) != 0;
        const bool bGamepad = (Coverage & 2) != 0;
        if (bKeyboardMouse && bGamepad)
        {
            ++CompleteActionCount;
        }
        TSharedRef<FJsonObject> ActionReport = MakeShared<FJsonObject>();
        ActionReport->SetStringField(TEXT("action"), ActionId);
        ActionReport->SetBoolField(TEXT("keyboard_mouse"), bKeyboardMouse);
        ActionReport->SetBoolField(TEXT("gamepad"), bGamepad);
        ActionReport->SetBoolField(TEXT("passed"), bKeyboardMouse && bGamepad);
        ActionReports.Add(MakeShared<FJsonValueObject>(ActionReport));
    }
    const bool bPassed = Context != nullptr && CompleteActionCount == RequiredActions.Num();
    OutGate->SetStringField(
        TEXT("mapping_context"), TEXT("/Game/RaftSim/Input/IMC_RaftSimDefault"));
    OutGate->SetNumberField(TEXT("required_action_count"), RequiredActions.Num());
    OutGate->SetNumberField(TEXT("complete_action_count"), CompleteActionCount);
    OutGate->SetNumberField(TEXT("mapping_count"), MappingReports.Num());
    OutGate->SetArrayField(TEXT("actions"), ActionReports);
    OutGate->SetArrayField(TEXT("mappings"), MappingReports);
    OutGate->SetBoolField(TEXT("passed"), bPassed);
    return bPassed;
}

bool RunSaveMigrationGate(TSharedRef<FJsonObject> OutGate)
{
    URaftSimVerticalSliceSaveGame* Legacy =
        NewObject<URaftSimVerticalSliceSaveGame>(GetTransientPackage());
    Legacy->SaveVersion = 0;
    Legacy->CompletedScenarioIds.Add(TEXT("legacy_rapid"));
    Legacy->BestSafetyScore = 0.82f;
    Legacy->BestOverallScore = 0.78f;
    Legacy->Settings.UiScale = 9.0f;
    Legacy->Settings.MotionIntensity = -4.0f;
    const bool bLegacyWritable = URaftSimSaveSubsystem::NormalizeSave(Legacy);
    const bool bLegacyPassed = bLegacyWritable &&
        Legacy->SaveVersion == URaftSimSaveSubsystem::CurrentSaveVersion &&
        Legacy->CompletedScenarioIds.Contains(TEXT("legacy_rapid")) &&
        Legacy->Settings.UiScale == 1.5f && Legacy->Settings.MotionIntensity == 0.0f &&
        Legacy->InputBindings.Contains(TEXT("Pause")) &&
        Legacy->InputBindings.Contains(TEXT("PaddleStroke")) &&
        Legacy->InputBindings.Contains(TEXT("RescueThrowLine"));

    URaftSimVerticalSliceSaveGame* Future =
        NewObject<URaftSimVerticalSliceSaveGame>(GetTransientPackage());
    Future->SaveVersion = URaftSimSaveSubsystem::CurrentSaveVersion + 7;
    Future->CompletedScenarioIds.Add(TEXT("future_build_progress"));
    Future->Settings.UiScale = 7.0f;
    const int32 FutureVersionBefore = Future->SaveVersion;
    const float FutureScaleBefore = Future->Settings.UiScale;
    const bool bFutureWritable = URaftSimSaveSubsystem::NormalizeSave(Future);
    const bool bFuturePassed = !bFutureWritable &&
        Future->SaveVersion == FutureVersionBefore &&
        Future->Settings.UiScale == FutureScaleBefore &&
        Future->CompletedScenarioIds.Contains(TEXT("future_build_progress"));

    const bool bPassed = bLegacyPassed && bFuturePassed;
    OutGate->SetNumberField(
        TEXT("current_save_version"), URaftSimSaveSubsystem::CurrentSaveVersion);
    OutGate->SetBoolField(TEXT("legacy_additive_migration"), bLegacyPassed);
    OutGate->SetBoolField(TEXT("future_save_rejected_as_read_only"), bFuturePassed);
    OutGate->SetBoolField(TEXT("default_bindings_seeded"),
        Legacy->InputBindings.Num() >= 9);
    OutGate->SetBoolField(TEXT("passed"), bPassed);
    return bPassed;
}

bool RunFullReachThreeFlowGate(TSharedRef<FJsonObject> OutGate)
{
    const TArray<FString> FlowBands = {
        TEXT("low_runnable"), TEXT("median_runnable"), TEXT("high_runnable")};
    const TArray<double> StationsM = {
        120.0, 2500.0, 5200.0, 10000.0, 14500.0, 18500.0, 24000.0,
        28500.0, 33000.0, 37500.0, 41500.0, 45500.0, 48900.0};
    TArray<TSharedPtr<FJsonValue>> Cases;
    int32 PassedCaseCount = 0;
    float MaximumAverageSolverMs = 0.0f;

#if RAFTSIM_HAS_LIVE_SOLVER
    for (const FString& FlowBand : FlowBands)
    {
        for (const double StationM : StationsM)
        {
            FRaftSimWaterRuntimeConfig Config;
            Config.bRequireAcceptedReportManifest = false;
            Config.bEnableDeterministicCapture = false;
            URaftSimWaterRuntimeAdapter* Adapter =
                NewObject<URaftSimWaterRuntimeAdapter>(GetTransientPackage());
            Adapter->Configure(Config);
            bool bStepped = Adapter->ConfigureRiverWindow(
                FullReachTransitFields, FlowBand, FVector2D(StationM, 0.0),
                FVector2D(240.0, 80.0));
            FRaftSimWaterLiveWindowStats Seeded;
            bStepped = bStepped && Adapter->GetLiveWindowStats(Seeded) &&
                !Seeded.bHasNonFinite && Seeded.TotalWaterVolumeM3 > 0.0f;
            for (int32 StepIndex = 0; bStepped && StepIndex < 8; ++StepIndex)
            {
                bStepped = Adapter->StepWater(1.0f / 60.0f);
            }
            FRaftSimWaterLiveWindowStats Stepped;
            bStepped = bStepped && Adapter->GetLiveWindowStats(Stepped);
            const bool bStable = bStepped && !Stepped.bHasNonFinite &&
                Stepped.TotalWaterVolumeM3 > 0.0f &&
                FMath::Abs(Stepped.WetFraction - Seeded.SeedWetFraction) <=
                    0.15f * Seeded.SeedWetFraction;

            URaftSimWaterRuntimeAdapter* Replay =
                NewObject<URaftSimWaterRuntimeAdapter>(GetTransientPackage());
            Replay->Configure(Config);
            bool bReplay = Replay->ConfigureRiverWindow(
                FullReachTransitFields, FlowBand, FVector2D(StationM, 0.0),
                FVector2D(240.0, 80.0));
            for (int32 StepIndex = 0; bReplay && StepIndex < 8; ++StepIndex)
            {
                bReplay = Replay->StepWater(1.0f / 60.0f);
            }
            FRaftSimWaterLiveWindowStats ReplayStats;
            bReplay = bReplay && Replay->GetLiveWindowStats(ReplayStats);
            const bool bDeterministic = bReplay &&
                FMath::IsNearlyEqual(
                    Stepped.TotalWaterVolumeM3, ReplayStats.TotalWaterVolumeM3, 1.0e-4f) &&
                FMath::IsNearlyEqual(
                    Stepped.WetFraction, ReplayStats.WetFraction, 1.0e-6f);
            const bool bWithinSolverBudget =
                Stepped.AverageSolverStepMilliseconds <= SolverBudgetMilliseconds;
            const bool bCasePassed = bStable && bDeterministic && bWithinSolverBudget;
            if (bCasePassed)
            {
                ++PassedCaseCount;
            }
            MaximumAverageSolverMs = FMath::Max(
                MaximumAverageSolverMs, Stepped.AverageSolverStepMilliseconds);

            TSharedRef<FJsonObject> Case = MakeShared<FJsonObject>();
            Case->SetStringField(TEXT("flow_band"), FlowBand);
            Case->SetNumberField(TEXT("station_m"), StationM);
            Case->SetBoolField(TEXT("finite_and_mass_stable"), bStable);
            Case->SetBoolField(TEXT("deterministic_replay"), bDeterministic);
            Case->SetNumberField(
                TEXT("average_solver_step_ms"), Stepped.AverageSolverStepMilliseconds);
            Case->SetBoolField(TEXT("within_solver_budget"), bWithinSolverBudget);
            Case->SetBoolField(TEXT("passed"), bCasePassed);
            Cases.Add(MakeShared<FJsonValueObject>(Case));
        }
    }
#endif

    const int32 ExpectedCases = FlowBands.Num() * StationsM.Num();
    const bool bPassed = RAFTSIM_HAS_LIVE_SOLVER != 0 &&
        Cases.Num() == ExpectedCases && PassedCaseCount == ExpectedCases &&
        MaximumAverageSolverMs <= SolverBudgetMilliseconds;
    OutGate->SetStringField(TEXT("runtime_data"), FullReachTransitFields);
    OutGate->SetNumberField(TEXT("flow_band_count"), FlowBands.Num());
    OutGate->SetNumberField(TEXT("station_count"), StationsM.Num());
    OutGate->SetNumberField(TEXT("case_count"), Cases.Num());
    OutGate->SetNumberField(TEXT("passed_case_count"), PassedCaseCount);
    OutGate->SetNumberField(TEXT("solver_budget_ms"), SolverBudgetMilliseconds);
    OutGate->SetNumberField(TEXT("max_case_average_solver_ms"), MaximumAverageSolverMs);
    OutGate->SetArrayField(TEXT("cases"), Cases);
    OutGate->SetBoolField(TEXT("passed"), bPassed);
    return bPassed;
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

bool ARaftSimContentLockDirector::IsReleaseCandidateQARequested()
{
    return FParse::Param(FCommandLine::Get(), TEXT("RaftSimReleaseCandidateQA"));
}

bool ARaftSimContentLockDirector::IsFreshProfileQARequested()
{
    return FParse::Param(FCommandLine::Get(), TEXT("RaftSimFreshProfileQA"));
}

bool ARaftSimContentLockDirector::IsPerformanceCaptureRequested()
{
    float SoakSeconds = 0.0f;
    return FParse::Value(
        FCommandLine::Get(), TEXT("RaftSimPerformanceSoakSeconds="), SoakSeconds) &&
        SoakSeconds > 0.0f;
}

bool ARaftSimContentLockDirector::IsGpuTimingSamplePlausible(
    float GpuMilliseconds, float WallClockMilliseconds)
{
    if (!FMath::IsFinite(GpuMilliseconds) || GpuMilliseconds < 0.0f ||
        !FMath::IsFinite(WallClockMilliseconds) || WallClockMilliseconds < 0.0f)
    {
        return false;
    }
    const float PlausibleCeiling = FMath::Max(
        MinimumGpuTimingCeilingMilliseconds,
        WallClockMilliseconds * GpuToWallClockPlausibilityRatio);
    return GpuMilliseconds <= PlausibleCeiling;
}

void ARaftSimContentLockDirector::BeginPlay()
{
    Super::BeginPlay();
    if (IsFreshProfileQARequested())
    {
        FString Report;
        const bool bPassed = RunFreshProfileFirstRunQA(GetGameInstance(), Report);
        const FString OutputPath = ResolveOutputPath(
            FString(), TEXT("m9_fresh_profile_first_run.json"));
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(OutputPath), true);
        const bool bSaved = FFileHelper::SaveStringToFile(Report, *OutputPath);
        EmitValidationReportToStdout(Report);
        UE_LOG(LogTemp, Display,
            TEXT("RAFTSIM_M9_FRESH_PROFILE_QA passed=%d saved=%d report=%s"),
            bPassed ? 1 : 0, bSaved ? 1 : 0, *OutputPath);
        FPlatformMisc::RequestExitWithStatus(false, bPassed && bSaved ? 0 : 11);
        return;
    }
    if (IsReleaseCandidateQARequested())
    {
        FString Report;
        const bool bPassed = RunReleaseCandidateQA(Report);
        const FString OutputPath = ResolveOutputPath(
            FString(), TEXT("m9_release_candidate_qa.json"));
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(OutputPath), true);
        const bool bSaved = FFileHelper::SaveStringToFile(Report, *OutputPath);
        EmitValidationReportToStdout(Report);
        UE_LOG(LogTemp, Display,
            TEXT("RAFTSIM_M9_RELEASE_QA passed=%d saved=%d report=%s"),
            bPassed ? 1 : 0, bSaved ? 1 : 0, *OutputPath);
        FPlatformMisc::RequestExitWithStatus(false, bPassed && bSaved ? 0 : 10);
        return;
    }
    if (IsPackagedRegressionRequested())
    {
        FString Report;
        const bool bPassed = RunRapidMatrixRegression(Report);
        const FString OutputPath = ResolveOutputPath(
            FString(), TEXT("m8_packaged_rapid_regression.json"));
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(OutputPath), true);
        const bool bSaved = FFileHelper::SaveStringToFile(Report, *OutputPath);
        EmitValidationReportToStdout(Report);
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
                // Record the budget verdict explicitly: it is part of
                // bCasePassed, and a case whose every other flag is true would
                // otherwise fail without the report naming the failing check.
                Case->SetBoolField(TEXT("within_solver_budget"), bWithinSolverBudget);
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

bool ARaftSimContentLockDirector::RunReleaseCandidateQA(FString& OutReportJson)
{
    FString ProjectVersion;
    const bool bHasVersion = GConfig != nullptr && GConfig->GetString(
        TEXT("/Script/EngineSettings.GeneralProjectSettings"),
        TEXT("ProjectVersion"), ProjectVersion, GGameIni);
    const bool bVersionPassed = bHasVersion && ProjectVersion == ReleaseVersion;
    const bool bRuntimeRequest = IsReleaseCandidateQARequested();
    const bool bPackagedBuild = FPlatformProperties::RequiresCookedData();
    const bool bShippingBuild = FApp::GetBuildConfiguration() == EBuildConfiguration::Shipping;
    const bool bPackageModePassed = !bRuntimeRequest || (bPackagedBuild && bShippingBuild);

    TSharedRef<FJsonObject> InputGate = MakeShared<FJsonObject>();
    const bool bInputPassed = RunInputMatrixGate(InputGate);
    TSharedRef<FJsonObject> SaveGate = MakeShared<FJsonObject>();
    const bool bSavePassed = RunSaveMigrationGate(SaveGate);
    TSharedRef<FJsonObject> FullReachGate = MakeShared<FJsonObject>();
    const bool bFullReachPassed = RunFullReachThreeFlowGate(FullReachGate);

    FString RapidReportJson;
    const bool bRapidPassed = RunRapidMatrixRegression(RapidReportJson);
    TSharedPtr<FJsonObject> RapidReport;
    const TSharedRef<TJsonReader<>> RapidReader =
        TJsonReaderFactory<>::Create(RapidReportJson);
    const bool bRapidReportParsed =
        FJsonSerializer::Deserialize(RapidReader, RapidReport) && RapidReport.IsValid();

    const bool bPassed = bVersionPassed && bPackageModePassed &&
        RAFTSIM_HAS_LIVE_SOLVER != 0 && bInputPassed && bSavePassed &&
        bFullReachPassed && bRapidPassed && bRapidReportParsed;
    TSharedRef<FJsonObject> Gates = MakeShared<FJsonObject>();
    Gates->SetBoolField(TEXT("version_lock"), bVersionPassed);
    Gates->SetBoolField(TEXT("packaged_shipping_when_commanded"), bPackageModePassed);
    Gates->SetBoolField(TEXT("live_solver_compiled"), RAFTSIM_HAS_LIVE_SOLVER != 0);
    Gates->SetObjectField(TEXT("keyboard_gamepad_matrix"), InputGate);
    Gates->SetObjectField(TEXT("save_migration_and_forward_protection"), SaveGate);
    Gates->SetObjectField(TEXT("three_flow_full_reach_matrix"), FullReachGate);
    if (bRapidReportParsed)
    {
        Gates->SetObjectField(TEXT("twenty_rapid_matrix"), RapidReport.ToSharedRef());
    }

    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(TEXT("schema"), TEXT("raftsim.m9.release_candidate_qa.v1"));
    Report->SetStringField(TEXT("release_version_expected"), ReleaseVersion);
    Report->SetStringField(TEXT("project_version"), ProjectVersion);
    Report->SetStringField(
        TEXT("platform"), ANSI_TO_TCHAR(FPlatformProperties::IniPlatformName()));
    Report->SetStringField(TEXT("build_configuration"), LexToString(FApp::GetBuildConfiguration()));
    Report->SetBoolField(TEXT("running_from_packaged_build"), bPackagedBuild);
    Report->SetBoolField(TEXT("command_line_release_qa"), bRuntimeRequest);
    Report->SetObjectField(TEXT("gates"), Gates);
    Report->SetArrayField(TEXT("external_constraints"), {
        MakeShared<FJsonValueString>(TEXT("Windows Authenticode requires the Windows release runner.")),
        MakeShared<FJsonValueString>(TEXT("Proton requires the signed Windows artifact and Linux Steam runner.")),
        MakeShared<FJsonValueString>(TEXT("Apple notarization requires Developer ID credentials."))});
    Report->SetBoolField(TEXT("passed"), bPassed);
    OutReportJson = SerializeJson(Report);
    return bPassed;
}

bool ARaftSimContentLockDirector::RunFreshProfileFirstRunQA(
    UGameInstance* GameInstance, FString& OutReportJson)
{
    URaftSimSaveSubsystem* SaveSubsystem = GameInstance != nullptr
        ? GameInstance->GetSubsystem<URaftSimSaveSubsystem>()
        : nullptr;
    URaftSimVerticalSliceSaveGame* Save = SaveSubsystem != nullptr
        ? SaveSubsystem->GetSave()
        : nullptr;
    const bool bPackagedShipping = FPlatformProperties::RequiresCookedData() &&
        FApp::GetBuildConfiguration() == EBuildConfiguration::Shipping;
    const bool bFreshCreated = SaveSubsystem != nullptr &&
        SaveSubsystem->WasFreshProfileCreatedThisSession();
    const bool bWritable = SaveSubsystem != nullptr &&
        SaveSubsystem->IsCurrentSaveWritable();
    const bool bVersionCurrent = Save != nullptr &&
        Save->SaveVersion == URaftSimSaveSubsystem::CurrentSaveVersion;
    const bool bPristineProgress = Save != nullptr &&
        Save->CompletedScenarioIds.IsEmpty() && Save->ScenarioProgress.IsEmpty() &&
        Save->CompletedTrainingDrillIds.IsEmpty() &&
        Save->CompletedCareerSectionIds.IsEmpty() &&
        Save->CareerStats.TotalRuns == 0 && Save->CareerStats.CompletedRuns == 0 &&
        Save->CareerXp == 0 && Save->LicenseTier == ERaftSimLicenseTier::Trainee;
    const bool bDefaultsReady = Save != nullptr && Save->InputBindings.Num() >= 9 &&
        Save->InputBindings.Contains(TEXT("Pause")) &&
        Save->InputBindings.Contains(TEXT("PaddleStroke")) &&
        Save->InputBindings.Contains(TEXT("RescueThrowLine")) &&
        Save->UnlockedScenarioIds.Contains(TEXT("training_eddy_basics")) &&
        Save->UnlockedScenarioIds.Contains(TEXT("south_fork_upper"));
    const bool bInitialSlotPersisted =
        UGameplayStatics::DoesSaveGameExist(URaftSimSaveSubsystem::SlotName, 0);

    const FName FirstSessionScenario(TEXT("south_fork_full_descent"));
    const bool bSessionStarted = SaveSubsystem != nullptr &&
        SaveSubsystem->BeginSession(ERaftSimGameMode::FreeRun, FirstSessionScenario);
    URaftSimVerticalSliceSaveGame* Reloaded = Cast<URaftSimVerticalSliceSaveGame>(
        UGameplayStatics::LoadGameFromSlot(URaftSimSaveSubsystem::SlotName, 0));
    const bool bRoundTripPersisted = Reloaded != nullptr &&
        Reloaded->SaveVersion == URaftSimSaveSubsystem::CurrentSaveVersion &&
        Reloaded->ActiveGameMode == ERaftSimGameMode::FreeRun &&
        Reloaded->Selection.ScenarioId == FirstSessionScenario;

    const bool bPassed = bPackagedShipping && bFreshCreated && bWritable &&
        bVersionCurrent && bPristineProgress && bDefaultsReady &&
        bInitialSlotPersisted && bSessionStarted && bRoundTripPersisted;
    TSharedRef<FJsonObject> Gates = MakeShared<FJsonObject>();
    Gates->SetBoolField(TEXT("packaged_shipping"), bPackagedShipping);
    Gates->SetBoolField(TEXT("no_existing_slot_at_startup"), bFreshCreated);
    Gates->SetBoolField(TEXT("current_save_writable"), bWritable);
    Gates->SetBoolField(TEXT("current_schema_version"), bVersionCurrent);
    Gates->SetBoolField(TEXT("pristine_progression"), bPristineProgress);
    Gates->SetBoolField(TEXT("default_bindings_and_unlocks"), bDefaultsReady);
    Gates->SetBoolField(TEXT("initial_slot_persisted"), bInitialSlotPersisted);
    Gates->SetBoolField(TEXT("first_session_started"), bSessionStarted);
    Gates->SetBoolField(TEXT("disk_round_trip_persisted"), bRoundTripPersisted);

    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(
        TEXT("schema"), TEXT("raftsim.m9.fresh_profile_first_run.v1"));
    Report->SetStringField(
        TEXT("platform"), ANSI_TO_TCHAR(FPlatformProperties::IniPlatformName()));
    Report->SetStringField(
        TEXT("build_configuration"), LexToString(FApp::GetBuildConfiguration()));
    Report->SetNumberField(
        TEXT("save_version"), Save != nullptr ? Save->SaveVersion : -1);
    Report->SetNumberField(
        TEXT("default_binding_count"), Save != nullptr ? Save->InputBindings.Num() : 0);
    Report->SetObjectField(TEXT("gates"), Gates);
    Report->SetBoolField(TEXT("passed"), bPassed);
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
    InvalidGpuTimingSampleCount = 0;
    LastGameDeltaMilliseconds = 0.0f;
    LastPerformanceTickSeconds = FPlatformTime::Seconds();

    float RequestedScreenPercentage = 0.0f;
    if (FParse::Value(
            FCommandLine::Get(), TEXT("RaftSimPerformanceScreenPercentage="),
            RequestedScreenPercentage) &&
        RequestedScreenPercentage >= 25.0f && RequestedScreenPercentage <= 100.0f)
    {
        if (IConsoleVariable* ScreenPercentage =
                IConsoleManager::Get().FindConsoleVariable(TEXT("r.ScreenPercentage")))
        {
            // Apply after map travel and GameUserSettings initialization;
            // startup ExecCmds can otherwise be overwritten back to the saved
            // resolution scale before the measured frames begin.
            ScreenPercentage->Set(
                RequestedScreenPercentage, ECVF_SetByCommandline);
        }
    }

    // Performance comparisons must apply renderer controls after map travel
    // and GameUserSettings initialization, for the same reason as screen
    // percentage above. These opt-in controls are diagnostic only; ordinary
    // gameplay continues to use the project's authored scalability policy.
    auto ApplyBoundedIntegerConsoleVariable = [](
        const TCHAR* CommandLineKey, const TCHAR* ConsoleVariableName,
        int32 MinimumValue, int32 MaximumValue)
    {
        int32 RequestedValue = 0;
        if (FParse::Value(FCommandLine::Get(), CommandLineKey, RequestedValue) &&
            RequestedValue >= MinimumValue && RequestedValue <= MaximumValue)
        {
            if (IConsoleVariable* Variable =
                    IConsoleManager::Get().FindConsoleVariable(ConsoleVariableName))
            {
                Variable->Set(RequestedValue, ECVF_SetByCommandline);
            }
        }
    };
    ApplyBoundedIntegerConsoleVariable(
        TEXT("RaftSimPerformanceAntiAliasingMethod="),
        TEXT("r.AntiAliasingMethod"), 0, 4);
    ApplyBoundedIntegerConsoleVariable(
        TEXT("RaftSimPerformanceBloomQuality="),
        TEXT("r.BloomQuality"), 0, 5);
    ApplyBoundedIntegerConsoleVariable(
        TEXT("RaftSimPerformanceSkeletalMeshLodBias="),
        TEXT("r.SkeletalMeshLODBias"), -1, 8);
    ApplyBoundedIntegerConsoleVariable(
        TEXT("RaftSimPerformanceViewDistanceQuality="),
        TEXT("sg.ViewDistanceQuality"), 0, 4);
    ApplyBoundedIntegerConsoleVariable(
        TEXT("RaftSimPerformanceAntiAliasingQuality="),
        TEXT("sg.AntiAliasingQuality"), 0, 4);
    ApplyBoundedIntegerConsoleVariable(
        TEXT("RaftSimPerformanceGlobalIlluminationQuality="),
        TEXT("sg.GlobalIlluminationQuality"), 0, 4);
    ApplyBoundedIntegerConsoleVariable(
        TEXT("RaftSimPerformanceReflectionQuality="),
        TEXT("sg.ReflectionQuality"), 0, 4);
    ApplyBoundedIntegerConsoleVariable(
        TEXT("RaftSimPerformanceShadowQuality="),
        TEXT("sg.ShadowQuality"), 0, 4);
    ApplyBoundedIntegerConsoleVariable(
        TEXT("RaftSimPerformancePostProcessQuality="),
        TEXT("sg.PostProcessQuality"), 0, 4);
    ApplyBoundedIntegerConsoleVariable(
        TEXT("RaftSimPerformanceEffectsQuality="),
        TEXT("sg.EffectsQuality"), 0, 4);
    ApplyBoundedIntegerConsoleVariable(
        TEXT("RaftSimPerformanceFoliageQuality="),
        TEXT("sg.FoliageQuality"), 0, 4);
    ApplyBoundedIntegerConsoleVariable(
        TEXT("RaftSimPerformanceTextureQuality="),
        TEXT("sg.TextureQuality"), 0, 4);
    ApplyBoundedIntegerConsoleVariable(
        TEXT("RaftSimPerformanceShadingQuality="),
        TEXT("sg.ShadingQuality"), 0, 4);
    ApplyBoundedIntegerConsoleVariable(
        TEXT("RaftSimPerformanceLumenTranslucencyRadianceCacheEnabled="),
        TEXT("r.Lumen.TranslucencyReflections.RadianceCache"), 0, 1);
    ApplyBoundedIntegerConsoleVariable(
        TEXT("RaftSimPerformanceNaniteEnabled="), TEXT("r.Nanite"), 0, 1);
    ApplyBoundedIntegerConsoleVariable(
        TEXT("RaftSimPerformanceVolumetricCloudEnabled="),
        TEXT("r.VolumetricCloud"), 0, 1);
    if (FParse::Param(
            FCommandLine::Get(), TEXT("RaftSimPerformanceDisableSkeletalMeshes")) &&
        GEngine != nullptr && GEngine->GameViewport != nullptr)
    {
        GEngine->GameViewport->EngineShowFlags.SetSkeletalMeshes(false);
    }
    if (FParse::Param(
            FCommandLine::Get(),
            TEXT("RaftSimPerformanceCharacterBodyOnlyShadows")))
    {
        if (UWorld* World = GetWorld())
        {
            for (TActorIterator<ARaftSimCrewAvatarActor> It(World); It; ++It)
            {
                It->SetProductionBodyOnlyShadowMode(true);
            }
        }
    }
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
    const float WallClockMilliseconds = WallDeltaSeconds * 1000.0f;
    const float GpuMilliseconds = FPlatformTime::ToMilliseconds(RHIGetGPUFrameCycles());
    CapturedWallClockFrameMilliseconds.Add(WallClockMilliseconds);
    CapturedGameThreadMilliseconds.Add(GameThreadMilliseconds);
    CapturedRenderThreadMilliseconds.Add(RenderThreadMilliseconds);
    float WorkloadMilliseconds = FMath::Max(
        GameThreadMilliseconds, RenderThreadMilliseconds);
    if (IsGpuTimingSamplePlausible(GpuMilliseconds, WallClockMilliseconds))
    {
        CapturedGpuMilliseconds.Add(GpuMilliseconds);
        WorkloadMilliseconds = FMath::Max(WorkloadMilliseconds, GpuMilliseconds);
    }
    else
    {
        ++InvalidGpuTimingSampleCount;
    }
    CapturedWorkloadFrameMilliseconds.Add(WorkloadMilliseconds);
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
    const FString MapName = GetWorld() != nullptr ? GetWorld()->GetMapName() : FString();
    FString RequiredMapName;
    FParse::Value(
        FCommandLine::Get(), TEXT("RaftSimPerformanceRequiredMap="), RequiredMapName);
    const bool bMapPass = RequiredMapName.IsEmpty() || MapName.EndsWith(RequiredMapName);
    // Workload time follows Unreal's max(game, render, GPU) FPS-chart model, but
    // omits provably stale/uninitialized RHI GPU samples. Wall-clock cadence is
    // never filtered and remains the hitch authority, so a genuine long stall
    // still fails even if its delayed GPU timer is rejected on a later frame.
    const bool bFramePass = Workload.P95 <= FrameBudgetMilliseconds &&
        PerformanceHitchCount == 0;
    const bool bSolverPass = bHasWaterStats &&
        WaterStats.AverageSolverStepMilliseconds <= SolverBudgetMilliseconds;
    const bool bMemoryPass = PeakMemoryMb <= MemoryBudgetMegabytes;
    const int32 InvalidGpuTimingSampleBudget = FMath::Max(
        MinimumInvalidGpuTimingSampleBudget,
        FMath::CeilToInt(FrameCount * 0.001f));
    const bool bGpuTimingPass = InvalidGpuTimingSampleCount <= InvalidGpuTimingSampleBudget;

    // Startup ExecCmds are intentionally not accepted as proof of the release
    // presentation profile: GameUserSettings can restore a prior player's
    // scalability state after startup. Every command-line requirement is
    // applied after map travel above, then verified against the live CVar here.
    auto ConsoleVariableMatchesRequestedInteger = [](
        const TCHAR* CommandLineKey, const TCHAR* ConsoleVariableName)
    {
        int32 RequestedValue = 0;
        if (!FParse::Value(FCommandLine::Get(), CommandLineKey, RequestedValue))
        {
            return true;
        }
        const IConsoleVariable* Variable =
            IConsoleManager::Get().FindConsoleVariable(ConsoleVariableName);
        return Variable != nullptr && Variable->GetInt() == RequestedValue;
    };
    bool bPresentationProfilePass = true;
    float RequiredScreenPercentage = 0.0f;
    if (FParse::Value(
            FCommandLine::Get(), TEXT("RaftSimPerformanceScreenPercentage="),
            RequiredScreenPercentage))
    {
        const IConsoleVariable* ScreenPercentage =
            IConsoleManager::Get().FindConsoleVariable(TEXT("r.ScreenPercentage"));
        bPresentationProfilePass = ScreenPercentage != nullptr &&
            FMath::IsNearlyEqual(
                ScreenPercentage->GetFloat(), RequiredScreenPercentage, 0.01f);
    }
    const TPair<const TCHAR*, const TCHAR*> PresentationProfileRequirements[] = {
        {TEXT("RaftSimPerformanceAntiAliasingMethod="), TEXT("r.AntiAliasingMethod")},
        {TEXT("RaftSimPerformanceBloomQuality="), TEXT("r.BloomQuality")},
        {TEXT("RaftSimPerformanceSkeletalMeshLodBias="), TEXT("r.SkeletalMeshLODBias")},
        {TEXT("RaftSimPerformanceViewDistanceQuality="), TEXT("sg.ViewDistanceQuality")},
        {TEXT("RaftSimPerformanceAntiAliasingQuality="), TEXT("sg.AntiAliasingQuality")},
        {TEXT("RaftSimPerformanceGlobalIlluminationQuality="), TEXT("sg.GlobalIlluminationQuality")},
        {TEXT("RaftSimPerformanceReflectionQuality="), TEXT("sg.ReflectionQuality")},
        {TEXT("RaftSimPerformanceShadowQuality="), TEXT("sg.ShadowQuality")},
        {TEXT("RaftSimPerformancePostProcessQuality="), TEXT("sg.PostProcessQuality")},
        {TEXT("RaftSimPerformanceEffectsQuality="), TEXT("sg.EffectsQuality")},
        {TEXT("RaftSimPerformanceFoliageQuality="), TEXT("sg.FoliageQuality")},
        {TEXT("RaftSimPerformanceTextureQuality="), TEXT("sg.TextureQuality")},
        {TEXT("RaftSimPerformanceShadingQuality="), TEXT("sg.ShadingQuality")},
        {TEXT("RaftSimPerformanceLumenTranslucencyRadianceCacheEnabled="),
         TEXT("r.Lumen.TranslucencyReflections.RadianceCache")},
        {TEXT("RaftSimPerformanceNaniteEnabled="), TEXT("r.Nanite")},
        {TEXT("RaftSimPerformanceVolumetricCloudEnabled="), TEXT("r.VolumetricCloud")}};
    for (const TPair<const TCHAR*, const TCHAR*>& Requirement :
         PresentationProfileRequirements)
    {
        bPresentationProfilePass = bPresentationProfilePass &&
            ConsoleVariableMatchesRequestedInteger(
                Requirement.Key, Requirement.Value);
    }
    bPerformanceCapturePassed =
        bMapPass && bFramePass && bSolverPass && bMemoryPass && bGpuTimingPass &&
        bPresentationProfilePass;
    bPerformanceCaptureComplete = true;

    const bool bRunningFromPackagedBuild =
        FPlatformProperties::RequiresCookedData();
    const bool bRenderOffscreen =
        FParse::Param(FCommandLine::Get(), TEXT("RenderOffScreen"));
    const bool bReleasePerformanceQualificationEligible =
        bRunningFromPackagedBuild &&
        FApp::GetBuildConfiguration() == EBuildConfiguration::Shipping &&
        !bRenderOffscreen;
    const bool bReleasePerformanceQualified =
        bPerformanceCapturePassed && bReleasePerformanceQualificationEligible;

    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(TEXT("schema"), TEXT("raftsim.m8.full_reach_performance_soak.v3"));
    Report->SetStringField(
        TEXT("platform"), ANSI_TO_TCHAR(FPlatformProperties::IniPlatformName()));
    Report->SetStringField(TEXT("build_configuration"), LexToString(FApp::GetBuildConfiguration()));
    Report->SetStringField(TEXT("cpu_brand"), FPlatformMisc::GetCPUBrand());
    Report->SetStringField(TEXT("gpu_brand"), FPlatformMisc::GetPrimaryGPUBrand());
    Report->SetBoolField(
        TEXT("running_from_packaged_build"), bRunningFromPackagedBuild);
    Report->SetBoolField(TEXT("render_offscreen"), bRenderOffscreen);
    Report->SetStringField(
        TEXT("performance_protocol"),
        bRenderOffscreen
            ? TEXT("offscreen_engineering_diagnostic")
            : TEXT("normal_windowed_player_presentation"));
    Report->SetBoolField(
        TEXT("release_performance_qualification_eligible"),
        bReleasePerformanceQualificationEligible);
    Report->SetBoolField(
        TEXT("release_performance_qualified"),
        bReleasePerformanceQualified);
    Report->SetBoolField(TEXT("application_has_focus"), FApp::HasFocus());
    Report->SetBoolField(TEXT("unattended"), FApp::IsUnattended());
    Report->SetStringField(TEXT("map_name"), MapName);
    Report->SetStringField(TEXT("required_map_name"), RequiredMapName);
    Report->SetBoolField(TEXT("map_requirement_passed"), bMapPass);
    Report->SetBoolField(
        TEXT("performance_profile_requirement_passed"),
        bPresentationProfilePass);
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
        TEXT("frame_time_definition"),
        TEXT("max(game_thread,render_thread,plausible_gpu)"));
    Report->SetStringField(
        TEXT("gpu_timing_filter"),
        TEXT("finite nonnegative GPU samples <= max(1000ms,16x wall-clock frame); "
             "wall-clock hitches are never filtered"));
    Report->SetNumberField(
        TEXT("gpu_timing_sample_count"), CapturedGpuMilliseconds.Num());
    Report->SetNumberField(
        TEXT("invalid_gpu_timing_sample_count"), InvalidGpuTimingSampleCount);
    Report->SetNumberField(
        TEXT("invalid_gpu_timing_sample_budget"), InvalidGpuTimingSampleBudget);
    Report->SetNumberField(TEXT("mean_frame_ms"), Workload.Mean);
    Report->SetNumberField(TEXT("p95_frame_ms"), Workload.P95);
    Report->SetNumberField(TEXT("max_frame_ms"), Workload.Max);
    Report->SetNumberField(TEXT("mean_wall_clock_frame_ms"), WallClock.Mean);
    Report->SetNumberField(TEXT("p95_wall_clock_frame_ms"), WallClock.P95);
    Report->SetNumberField(TEXT("max_wall_clock_frame_ms"), WallClock.Max);
    Report->SetNumberField(TEXT("p95_game_thread_ms"), GameThread.P95);
    Report->SetNumberField(TEXT("p95_render_thread_ms"), RenderThread.P95);
    Report->SetNumberField(TEXT("p95_gpu_ms"), Gpu.P95);
    Report->SetNumberField(TEXT("mean_game_thread_ms"), GameThread.Mean);
    Report->SetNumberField(TEXT("mean_render_thread_ms"), RenderThread.Mean);
    Report->SetNumberField(TEXT("mean_gpu_ms"), Gpu.Mean);
    Report->SetNumberField(TEXT("hitches_over_33ms"), PerformanceHitchCount);
    auto RecordConsoleVariable = [&Report](
        const TCHAR* FieldName, const TCHAR* ConsoleVariableName)
    {
        if (const IConsoleVariable* Variable =
                IConsoleManager::Get().FindConsoleVariable(ConsoleVariableName))
        {
            Report->SetNumberField(FieldName, Variable->GetFloat());
        }
    };
    RecordConsoleVariable(
        TEXT("niagara_components_enabled"),
        TEXT("fx.NiagaraComponentsEnabled"));
    RecordConsoleVariable(
        TEXT("global_illumination_quality"),
        TEXT("sg.GlobalIlluminationQuality"));
    RecordConsoleVariable(
        TEXT("reflection_quality"), TEXT("sg.ReflectionQuality"));
    RecordConsoleVariable(
        TEXT("shadow_quality"), TEXT("sg.ShadowQuality"));
    RecordConsoleVariable(
        TEXT("post_process_quality"), TEXT("sg.PostProcessQuality"));
    RecordConsoleVariable(
        TEXT("effects_quality"), TEXT("sg.EffectsQuality"));
    RecordConsoleVariable(
        TEXT("foliage_quality"), TEXT("sg.FoliageQuality"));
    RecordConsoleVariable(
        TEXT("view_distance_quality"), TEXT("sg.ViewDistanceQuality"));
    RecordConsoleVariable(
        TEXT("anti_aliasing_quality"), TEXT("sg.AntiAliasingQuality"));
    RecordConsoleVariable(
        TEXT("texture_quality"), TEXT("sg.TextureQuality"));
    RecordConsoleVariable(
        TEXT("shading_quality"), TEXT("sg.ShadingQuality"));
    RecordConsoleVariable(
        TEXT("anti_aliasing_method"), TEXT("r.AntiAliasingMethod"));
    RecordConsoleVariable(TEXT("bloom_quality"), TEXT("r.BloomQuality"));
    RecordConsoleVariable(
        TEXT("skeletal_mesh_lod_bias"), TEXT("r.SkeletalMeshLODBias"));
    RecordConsoleVariable(
        TEXT("lumen_final_gather_method"), TEXT("r.Lumen.FinalGatherMethod"));
    RecordConsoleVariable(
        TEXT("lumen_translucency_radiance_cache_enabled"),
        TEXT("r.Lumen.TranslucencyReflections.RadianceCache"));
    RecordConsoleVariable(
        TEXT("translucency_lighting_volume_mark_voxels_enabled"),
        TEXT("r.TranslucencyLightingVolume.MarkVoxels"));
    RecordConsoleVariable(TEXT("nanite_enabled"), TEXT("r.Nanite"));
    RecordConsoleVariable(
        TEXT("volumetric_cloud_enabled"), TEXT("r.VolumetricCloud"));
    Report->SetBoolField(
        TEXT("skeletal_meshes_rendered"),
        GEngine == nullptr || GEngine->GameViewport == nullptr ||
            GEngine->GameViewport->EngineShowFlags.SkeletalMeshes);
    Report->SetBoolField(
        TEXT("character_body_only_shadows"),
        FParse::Param(
            FCommandLine::Get(),
            TEXT("RaftSimPerformanceCharacterBodyOnlyShadows")));

    int32 WaterVfxActorCount = 0;
    int32 ProductionNiagaraComponentCount = 0;
    int32 ActiveRapidAerosolCount = 0;
    int32 ActiveRapidRollerCount = 0;
    bool bProductionNiagaraReady = false;
    if (UWorld* World = GetWorld())
    {
        for (TActorIterator<ARaftSimWaterVfxActor> It(World); It; ++It)
        {
            ++WaterVfxActorCount;
            bProductionNiagaraReady =
                bProductionNiagaraReady || It->IsProductionNiagaraReady();
            ProductionNiagaraComponentCount +=
                It->GetProductionNiagaraComponentCount();
            ActiveRapidAerosolCount +=
                It->GetActiveRapidAerosolNiagaraCount();
            ActiveRapidRollerCount +=
                It->GetActiveRapidRollerNiagaraCount();
        }
    }
    Report->SetNumberField(TEXT("water_vfx_actor_count"), WaterVfxActorCount);
    Report->SetBoolField(
        TEXT("production_niagara_ready"), bProductionNiagaraReady);
    Report->SetNumberField(
        TEXT("production_niagara_component_count"),
        ProductionNiagaraComponentCount);
    Report->SetNumberField(
        TEXT("active_rapid_aerosol_niagara_count"),
        ActiveRapidAerosolCount);
    Report->SetNumberField(
        TEXT("active_rapid_roller_niagara_count"),
        ActiveRapidRollerCount);
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
    Report->SetBoolField(TEXT("gpu_timing_measurement_passed"), bGpuTimingPass);
    Report->SetBoolField(TEXT("passed"), bPerformanceCapturePassed);
    const FString Json = SerializeJson(Report);
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(PerformanceOutputPath), true);
    const bool bSaved = FFileHelper::SaveStringToFile(Json, *PerformanceOutputPath);
    EmitValidationReportToStdout(Json);
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
