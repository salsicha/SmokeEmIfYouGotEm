#if WITH_DEV_AUTOMATION_TESTS

#include "RaftSimCrewStateContracts.h"

#include "Dom/JsonObject.h"
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace
{
TSharedPtr<FJsonObject> LoadContentJsonObject(FAutomationTestBase& Test, const FString& ContentRelativePath)
{
    const FString FullPath = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(FPaths::ProjectContentDir(), ContentRelativePath)
    );

    FString JsonText;
    if (!FFileHelper::LoadFileToString(JsonText, *FullPath))
    {
        Test.AddError(FString::Printf(TEXT("Missing JSON manifest: %s"), *FullPath));
        return nullptr;
    }

    TSharedPtr<FJsonObject> Root;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonText);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        Test.AddError(FString::Printf(TEXT("Invalid JSON manifest: %s"), *FullPath));
        return nullptr;
    }

    return Root;
}

bool TestArrayCount(
    FAutomationTestBase& Test,
    const TSharedPtr<FJsonObject>& Root,
    const TCHAR* FieldName,
    int32 ExpectedCount
)
{
    const TArray<TSharedPtr<FJsonValue>>* Values = nullptr;
    if (!Root->TryGetArrayField(FieldName, Values) || Values == nullptr)
    {
        Test.AddError(FString::Printf(TEXT("Missing array field: %s"), FieldName));
        return false;
    }

    Test.TestEqual(FString::Printf(TEXT("%s count"), FieldName), Values->Num(), ExpectedCount);
    return Values->Num() == ExpectedCount;
}

FRaftSimCrewSafetyTransition MakeSafetyTransition(
    ERaftSimCrewSafetyState PreviousState,
    ERaftSimCrewSafetyState NextState,
    const TCHAR* Reason
)
{
    FRaftSimCrewSafetyTransition Transition;
    Transition.PreviousState = PreviousState;
    Transition.NextState = NextState;
    Transition.TransitionReason = FName(Reason);
    return Transition;
}

bool TestSkillLevel(
    FAutomationTestBase& Test,
    const TCHAR* Label,
    const FRaftSimPassengerSwimmingSkillAssignment& Assignment,
    ERaftSimSwimmingSkillLevel ExpectedLevel
)
{
    return Test.TestEqual(
        Label,
        static_cast<int32>(Assignment.Profile.SkillLevel),
        static_cast<int32>(ExpectedLevel)
    );
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimMilestone11CrewSafetyGateTest,
    "RaftSim.Milestone11.CrewSafetyGate",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter
)

bool FRaftSimMilestone11CrewSafetyGateTest::RunTest(const FString& Parameters)
{
    const TSharedPtr<FJsonObject> Gate = LoadContentJsonObject(
        *this,
        TEXT("RaftSim/Automation/milestone11_crew_safety_gate.json")
    );
    if (!Gate.IsValid())
    {
        return false;
    }

    TestEqual(
        TEXT("gate schema"),
        Gate->GetStringField(TEXT("schema")),
        FString(TEXT("raftsim.unreal.milestone11_crew_safety_gate.v1"))
    );
    TestEqual(TEXT("gate status"), Gate->GetStringField(TEXT("status")), FString(TEXT("complete")));
    TestEqual(
        TEXT("automation test name"),
        Gate->GetStringField(TEXT("automation_test_name")),
        FString(TEXT("RaftSim.Milestone11.CrewSafetyGate"))
    );
    TestEqual(TEXT("completed task count"), Gate->GetIntegerField(TEXT("completed_task_count")), 4);
    TestArrayCount(*this, Gate, TEXT("gate_checks"), 4);
    TestArrayCount(*this, Gate, TEXT("native_runtime_checks"), 4);

    const TSharedPtr<FJsonObject>* RequiredManifests = nullptr;
    if (!Gate->TryGetObjectField(TEXT("required_manifests"), RequiredManifests)
        || RequiredManifests == nullptr
        || !RequiredManifests->IsValid())
    {
        AddError(TEXT("Milestone 11 gate must declare required_manifests."));
        return false;
    }

    const TSharedPtr<FJsonObject> SafetyStates = LoadContentJsonObject(
        *this,
        (*RequiredManifests)->GetStringField(TEXT("crew_overboard_safety_states"))
    );
    const TSharedPtr<FJsonObject> SwimmingSkills = LoadContentJsonObject(
        *this,
        (*RequiredManifests)->GetStringField(TEXT("swimming_skill_assignment"))
    );
    const TSharedPtr<FJsonObject> RescueGameplay = LoadContentJsonObject(
        *this,
        (*RequiredManifests)->GetStringField(TEXT("swimmer_rescue_gameplay"))
    );
    const TSharedPtr<FJsonObject> GameplayScoring = LoadContentJsonObject(
        *this,
        (*RequiredManifests)->GetStringField(TEXT("gameplay_telemetry_scoring"))
    );
    if (!SafetyStates.IsValid()
        || !SwimmingSkills.IsValid()
        || !RescueGameplay.IsValid()
        || !GameplayScoring.IsValid())
    {
        return false;
    }

    TestEqual(
        TEXT("safety state schema"),
        SafetyStates->GetStringField(TEXT("schema")),
        FString(TEXT("raftsim.unreal.crew_overboard_safety_states.v1"))
    );
    TestArrayCount(*this, SafetyStates, TEXT("states"), 8);
    TestArrayCount(*this, SafetyStates, TEXT("allowed_transitions"), 10);
    TestTrue(
        TEXT("failed rescue terminal policy"),
        SafetyStates->GetObjectField(TEXT("pass_policy"))->GetBoolField(TEXT("failed_rescue_is_terminal_until_reset"))
    );

    TestEqual(
        TEXT("swimming skill schema"),
        SwimmingSkills->GetStringField(TEXT("schema")),
        FString(TEXT("raftsim.unreal.swimming_skill_assignment.v1"))
    );
    TestArrayCount(*this, SwimmingSkills, TEXT("skill_levels"), 4);
    TestTrue(
        TEXT("non-swimmers cannot self-rescue policy"),
        SwimmingSkills->GetObjectField(TEXT("pass_policy"))->GetBoolField(TEXT("non_swimmers_cannot_self_rescue"))
    );

    TestEqual(
        TEXT("rescue gameplay schema"),
        RescueGameplay->GetStringField(TEXT("schema")),
        FString(TEXT("raftsim.unreal.swimmer_rescue_gameplay.v1"))
    );
    TestArrayCount(*this, RescueGameplay, TEXT("rescue_methods"), 3);
    TestTrue(
        TEXT("rescue telemetry policy"),
        RescueGameplay->GetObjectField(TEXT("pass_policy"))->GetBoolField(TEXT("pull_in_reseat_and_failed_rescue_emit_telemetry"))
    );

    TestEqual(
        TEXT("gameplay scoring schema"),
        GameplayScoring->GetStringField(TEXT("schema")),
        FString(TEXT("raftsim.unreal.gameplay_telemetry_scoring.v1"))
    );
    TestArrayCount(*this, GameplayScoring, TEXT("telemetry_categories"), 7);
    TestTrue(
        TEXT("swim and rescue scoring policy"),
        GameplayScoring->GetObjectField(TEXT("pass_policy"))->GetBoolField(TEXT("swims_rescue_method_time_in_water_and_recovery_are_scored"))
    );

    TestTrue(
        TEXT("seated can become at risk"),
        URaftSimCrewSafetyStateLibrary::CanTransitionSafetyState(
            ERaftSimCrewSafetyState::Seated,
            ERaftSimCrewSafetyState::AtRisk
        )
    );
    TestTrue(
        TEXT("swimming can target rescue"),
        URaftSimCrewSafetyStateLibrary::CanTransitionSafetyState(
            ERaftSimCrewSafetyState::Swimming,
            ERaftSimCrewSafetyState::RescueTargeted
        )
    );
    TestFalse(
        TEXT("failed rescue is terminal"),
        URaftSimCrewSafetyStateLibrary::CanTransitionSafetyState(
            ERaftSimCrewSafetyState::FailedRescue,
            ERaftSimCrewSafetyState::Seated
        )
    );

    FRaftSimCrewSafetyStateFrame SafetyFrame;
    SafetyFrame.PassengerId = FName(TEXT("passenger_a"));
    SafetyFrame.SeatId = FName(TEXT("bow_left"));
    SafetyFrame = URaftSimCrewSafetyStateLibrary::ApplySafetyTransition(
        SafetyFrame,
        MakeSafetyTransition(
            ERaftSimCrewSafetyState::Seated,
            ERaftSimCrewSafetyState::AtRisk,
            TEXT("missed_brace")
        )
    );
    SafetyFrame = URaftSimCrewSafetyStateLibrary::ApplySafetyTransition(
        SafetyFrame,
        MakeSafetyTransition(
            ERaftSimCrewSafetyState::AtRisk,
            ERaftSimCrewSafetyState::FallingEjected,
            TEXT("unseated_contact_impulse")
        )
    );
    SafetyFrame = URaftSimCrewSafetyStateLibrary::ApplySafetyTransition(
        SafetyFrame,
        MakeSafetyTransition(
            ERaftSimCrewSafetyState::FallingEjected,
            ERaftSimCrewSafetyState::Swimming,
            TEXT("water_contact_confirmed")
        )
    );
    TestEqual(
        TEXT("transition chain reaches swimming"),
        static_cast<int32>(SafetyFrame.CurrentState),
        static_cast<int32>(ERaftSimCrewSafetyState::Swimming)
    );

    const FRaftSimCrewSafetyStateFrame FailedFrame = URaftSimCrewSafetyStateLibrary::ApplySafetyTransition(
        SafetyFrame,
        MakeSafetyTransition(
            ERaftSimCrewSafetyState::Swimming,
            ERaftSimCrewSafetyState::FailedRescue,
            TEXT("rescue_window_expired")
        )
    );
    TestEqual(
        TEXT("failed rescue records state"),
        static_cast<int32>(FailedFrame.CurrentState),
        static_cast<int32>(ERaftSimCrewSafetyState::FailedRescue)
    );
    TestEqual(
        TEXT("failed rescue reason"),
        FailedFrame.FailedRescueReason.ToString(),
        FString(TEXT("rescue_window_expired"))
    );

    const FRaftSimSwimmingSkillProfile NonSwimmerProfile =
        URaftSimSwimmingSkillLibrary::MakeSwimmingSkillProfile(ERaftSimSwimmingSkillLevel::NonSwimmer);
    TestFalse(TEXT("non-swimmer self rescue disabled"), NonSwimmerProfile.bSelfRescueAllowed);
    TestTrue(TEXT("non-swimmer highest priority"), NonSwimmerProfile.RescuePriority >= 1.0f);
    TestTrue(TEXT("non-swimmer short critical window"), NonSwimmerProfile.TimeToCriticalSeconds <= 8.0f);

    TestSkillLevel(
        *this,
        TEXT("0.10 roll assigns non-swimmer"),
        URaftSimSwimmingSkillLibrary::AssignSwimmingSkillFromNormalizedValue(
            FName(TEXT("p1")),
            FName(TEXT("seat1")),
            0.10f,
            1234,
            false
        ),
        ERaftSimSwimmingSkillLevel::NonSwimmer
    );
    TestSkillLevel(
        *this,
        TEXT("0.20 roll assigns weak swimmer"),
        URaftSimSwimmingSkillLibrary::AssignSwimmingSkillFromNormalizedValue(
            FName(TEXT("p2")),
            FName(TEXT("seat2")),
            0.20f,
            1234,
            false
        ),
        ERaftSimSwimmingSkillLevel::WeakSwimmer
    );
    TestSkillLevel(
        *this,
        TEXT("0.50 roll assigns average swimmer"),
        URaftSimSwimmingSkillLibrary::AssignSwimmingSkillFromNormalizedValue(
            FName(TEXT("p3")),
            FName(TEXT("seat3")),
            0.50f,
            1234,
            false
        ),
        ERaftSimSwimmingSkillLevel::AverageSwimmer
    );
    TestSkillLevel(
        *this,
        TEXT("0.90 roll assigns strong swimmer"),
        URaftSimSwimmingSkillLibrary::AssignSwimmingSkillFromNormalizedValue(
            FName(TEXT("p4")),
            FName(TEXT("seat4")),
            0.90f,
            1234,
            false
        ),
        ERaftSimSwimmingSkillLevel::StrongSwimmer
    );

    FRaftSimSwimmerRescueFrame RescueFrame;
    RescueFrame.PassengerId = FName(TEXT("passenger_a"));
    RescueFrame.VisibilityScore = 0.8f;
    RescueFrame.CalloutPriority = 0.1f;
    RescueFrame = URaftSimSwimmerRescueLibrary::IntegrateSwimmerDrift(
        RescueFrame,
        FVector(2.0f, 0.5f, 0.0f),
        1.5f
    );
    TestTrue(TEXT("swimmer drifts downstream"), RescueFrame.SwimmerWorldPositionMeters.X > 2.9f);
    TestTrue(TEXT("swimmer side drift recorded"), RescueFrame.SwimmerWorldPositionMeters.Y > 0.7f);
    TestTrue(TEXT("time in water advances"), RescueFrame.TimeInWaterSeconds > 1.4f);
    TestTrue(TEXT("visibility degrades"), RescueFrame.VisibilityScore < 0.8f);
    TestTrue(TEXT("callout priority rises"), RescueFrame.CalloutPriority > 0.1f);

    FRaftSimRescueAttempt ThrowLineAttempt;
    ThrowLineAttempt.PassengerId = FName(TEXT("passenger_a"));
    ThrowLineAttempt.Method = ERaftSimRescueMethod::ThrowLine;
    ThrowLineAttempt.DistanceMeters = 5.0f;
    ThrowLineAttempt.bThrowLineAvailable = true;
    ThrowLineAttempt.TimeInWaterSeconds = 4.0f;
    RescueFrame.PullInProgress = 0.5f;
    const FRaftSimSwimmerRescueFrame SuccessfulRescue =
        URaftSimSwimmerRescueLibrary::EvaluateRescueAttempt(
            RescueFrame,
            ThrowLineAttempt,
            NonSwimmerProfile
        );
    TestTrue(TEXT("throw-line rescue progresses pull-in"), SuccessfulRescue.PullInProgress > 0.5f);
    TestEqual(TEXT("successful rescue clears failure reason"), SuccessfulRescue.FailedRescueReason, NAME_None);
    TestTrue(TEXT("successful rescue improves trust"), SuccessfulRescue.TrustDelta > 0.0f);

    FRaftSimRescueAttempt FailedReachAttempt;
    FailedReachAttempt.PassengerId = FName(TEXT("passenger_a"));
    FailedReachAttempt.Method = ERaftSimRescueMethod::ReachGrab;
    FailedReachAttempt.DistanceMeters = 5.0f;
    FailedReachAttempt.bThrowLineAvailable = false;
    FailedReachAttempt.TimeInWaterSeconds = 4.0f;
    const FRaftSimSwimmerRescueFrame FailedRescue =
        URaftSimSwimmerRescueLibrary::EvaluateRescueAttempt(
            RescueFrame,
            FailedReachAttempt,
            NonSwimmerProfile
        );
    TestEqual(TEXT("failed reach rescue reason"), FailedRescue.FailedRescueReason.ToString(), FString(TEXT("out_of_reach")));
    TestTrue(TEXT("failed rescue reduces trust"), FailedRescue.TrustDelta < 0.0f);

    FRaftSimGameplayScoringSignals CleanSignals;
    const FRaftSimGameplayScoreBreakdown CleanScore =
        URaftSimGameplayScoringLibrary::EvaluateGameplayScore(CleanSignals);

    FRaftSimGameplayScoringSignals UnsafeSignals;
    UnsafeSignals.SafetyIncidentCount = 1;
    UnsafeSignals.FailedRescueCount = 1;
    UnsafeSignals.SwimCount = 1;
    UnsafeSignals.TimeInWaterSeconds = 30.0f;
    UnsafeSignals.CrewRecoverySeconds = 20.0f;
    const FRaftSimGameplayScoreBreakdown UnsafeScore =
        URaftSimGameplayScoringLibrary::EvaluateGameplayScore(UnsafeSignals);

    TestTrue(TEXT("safety incident reduces safety score"), UnsafeScore.SafetyScore < CleanScore.SafetyScore);
    TestTrue(TEXT("swim time reduces swim rescue score"), UnsafeScore.SwimRescueScore < CleanScore.SwimRescueScore);
    TestTrue(TEXT("unsafe run scores lower overall"), UnsafeScore.TotalScore < CleanScore.TotalScore);

    return true;
}

#endif
