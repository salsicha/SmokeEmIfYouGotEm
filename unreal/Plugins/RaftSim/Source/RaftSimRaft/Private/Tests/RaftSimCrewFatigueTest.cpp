#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimRaftActor.h"
#include "UObject/Script.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrewFatigueTest, "RaftSim.Crew.PaddlerFatigue",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimCrewFatigueTest::RunTest(const FString&)
{
    FEditorScriptExecutionGuard ScriptGuard;
    UWorld* World = nullptr;
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
        if (Context.WorldType == EWorldType::Editor) { World = Context.World(); break; }
    if (!TestNotNull(TEXT("editor world"), World)) return false;
    auto* Raft = World->SpawnActor<ARaftSimRaftActor>();
    if (!TestNotNull(TEXT("production raft"), Raft)) return false;
    ON_SCOPE_EXIT {
        TArray<AActor*> Owned;
        for (TActorIterator<ARaftSimCrewAvatarActor> It(World); It; ++It)
            if (It->GetOwner() == Raft) Owned.Add(*It);
        for (AActor* Actor : Owned) World->DestroyActor(Actor);
        World->DestroyActor(Raft);
    };
    Raft->InitializeCrewSeatingForValidation();
    auto* Adapter = NewObject<URaftSimChronoRuntimeAdapter>(Raft);
    Raft->RaftAdapter = Adapter;
    FRaftSimRaftBodyConfig Body;
    Body.Runtime = ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;
    Adapter->ConfigureRaftBody(Body);

    const float Paddlers = float(Raft->PaddlerCount);
    TestTrue(TEXT("a fresh crew pulls exactly its configured paddlers"),
        FMath::IsNearlyEqual(Raft->GetCrewStrokeStrength(), Paddlers, 1.e-4f));
    TestTrue(TEXT("a fresh crew is at full energy"), FMath::IsNearlyEqual(Raft->GetCrewEnergy(), 1.f, 1.e-6f));

    // A minute of continuous hard paddling.
    constexpr float Dt = 1.f / 30.f;
    Raft->IssueCrewCommand(ERaftSimCrewCommand::AllForward);
    Raft->UpdateCrew(Raft->CrewReactionSeconds + .01f);
    TArray<float> Before;
    for (int32 I = 1; I <= Raft->PaddlerCount; ++I)
        Before.Add(Raft->GetCrewStamina(FName(*FString::Printf(TEXT("paddler_%d"), I))));
    for (int32 Frame = 0; Frame < 60 * 30; ++Frame) Raft->UpdateCrew(Dt);
    const float Tired = Raft->GetCrewEnergy();
    AddInfo(FString::Printf(TEXT("FATIGUE after_60s_energy=%.4f strength=%.4f"), Tired, Raft->GetCrewStrokeStrength()));
    TestTrue(TEXT("sustained paddling tires the crew"), Tired < .8f && Tired > .45f);
    TestTrue(TEXT("tired arms deliver less stroke force"), Raft->GetCrewStrokeStrength() < Paddlers * .92f);
    TestTrue(TEXT("but a tired crew still pulls"), Raft->GetCrewStrokeStrength() > Paddlers * .45f);
    for (int32 I = 1; I <= Raft->PaddlerCount; ++I)
        TestTrue(TEXT("every paddler working tires"),
            Raft->GetCrewStamina(FName(*FString::Printf(TEXT("paddler_%d"), I))) < Before[I - 1]);
    TestTrue(TEXT("the guide's fitness outlasts the guests"),
        Raft->GetCrewStamina(TEXT("guide")) > Tired);

    // Rest: recovery is real but slower than the drain that caused it.
    Raft->IssueCrewCommand(ERaftSimCrewCommand::Rest);
    Raft->UpdateCrew(Raft->CrewReactionSeconds + .01f);
    for (int32 Frame = 0; Frame < 10 * 30; ++Frame) Raft->UpdateCrew(Dt);
    const float TenSeconds = Raft->GetCrewEnergy();
    TestTrue(TEXT("rest recovers energy"), TenSeconds > Tired);
    TestTrue(TEXT("recovery is slow: ten seconds of rest is not a full reset"), TenSeconds < .9f);
    for (int32 Frame = 0; Frame < 80 * 30; ++Frame) Raft->UpdateCrew(Dt);
    const float Rested = Raft->GetCrewEnergy();
    AddInfo(FString::Printf(TEXT("FATIGUE rest_10s=%.4f rest_90s=%.4f"), TenSeconds, Rested));
    TestTrue(TEXT("a long rest restores most of the crew"), Rested > .9f && Rested < 1.f);

    // Exhaustion floor, and swimmers add nothing to the stroke.
    for (int32 I = 1; I <= Raft->PaddlerCount; ++I)
        Raft->SetCrewStaminaForTesting(FName(*FString::Printf(TEXT("paddler_%d"), I)), 0.f);
    TestTrue(TEXT("a spent crew keeps a floor of stroke force"),
        FMath::IsNearlyEqual(Raft->GetCrewStrokeStrength(), Paddlers * ARaftSimRaftActor::StrokeStrengthForStamina(0.f), 1.e-4f));
    float Weakest = 1.f;
    TestFalse(TEXT("the HUD can name the most tired paddler"), Raft->GetMostTiredPaddler(Weakest).IsNone());
    for (int32 I = 1; I <= Raft->PaddlerCount; ++I)
        Raft->SetCrewStaminaForTesting(FName(*FString::Printf(TEXT("paddler_%d"), I)), 1.f);
    Raft->ForceCrewOverboardForTesting(1);
    TestTrue(TEXT("a paddler in the water does not paddle"),
        FMath::IsNearlyEqual(Raft->GetCrewStrokeStrength(), Paddlers - 1.f, 1.e-4f));
    return true;
}
#endif
