#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "RaftSimCC0CrewVisualActor.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimRaftActor.h"
#include "UObject/Script.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimGuideEyeAnchorTest,
    "RaftSim.Crew.GuideEyeAnchorFollowsProductionRig",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimGuideEyeAnchorTest::RunTest(const FString&)
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
    auto* Guide = Raft->FindAvatar(TEXT("guide"));
    if (!TestNotNull(TEXT("actual guide avatar"), Guide)) return false;
    auto* Visual = Cast<ARaftSimCC0CrewVisualActor>(Guide->GetProductionVisualActor());
    if (!TestNotNull(TEXT("actual production skeleton"), Visual)) return false;
    Guide->ClearExternalPose();
    const ERaftSimCrewAvatarAction Actions[] = {
        ERaftSimCrewAvatarAction::SeatedIdle, ERaftSimCrewAvatarAction::ForwardStroke,
        ERaftSimCrewAvatarAction::BackStroke, ERaftSimCrewAvatarAction::TurnLeft,
        ERaftSimCrewAvatarAction::TurnRight, ERaftSimCrewAvatarAction::HighSidePort,
        ERaftSimCrewAvatarAction::HighSideStarboard, ERaftSimCrewAvatarAction::Swimming,
        ERaftSimCrewAvatarAction::ThrowLine, ERaftSimCrewAvatarAction::Reentry};
    double MaxOldEyeErrorCm = 0.;
    int32 Samples = 0;
    for (int32 Frame = 0; Frame < 2; ++Frame)
    {
        Raft->SetActorLocationAndRotation(Frame ? FVector(12400, -8730, 1920) : FVector::ZeroVector,
            Frame ? FRotator(13, -137, 21) : FRotator::ZeroRotator);
        for (const auto Action : Actions)
        {
            for (const float Phase : {0.f, .25f, .5f, .75f})
            {
                Guide->SetFirstPersonHeadHidden(false);
                Guide->SetAvatarActionPhaseForValidation(Action, Phase);
                FVector RenderedEye, ViewEye;
                if (!TestTrue(TEXT("rendered eye available"), Visual->GetRenderedEyeCenterWorld(RenderedEye)) ||
                    !TestTrue(TEXT("view eye available"), Visual->GetViewEyeCenterWorld(ViewEye))) return false;
                TestTrue(TEXT("camera anchor equals visible anatomical eyes"), ViewEye.Equals(RenderedEye, .25));
                const FVector OldEye = Guide->GetPoseHeadWorldLocationCm() +
                    Guide->GetActorForwardVector() * 9.f + Guide->GetActorUpVector() * 4.f;
                MaxOldEyeErrorCm = FMath::Max(MaxOldEyeErrorCm, FVector::Distance(OldEye, ViewEye));
                Guide->SetFirstPersonHeadHidden(true);
                Guide->SetAvatarActionPhaseForValidation(Action, Phase);
                FVector HiddenEye, RoutedEye;
                TestTrue(TEXT("hidden head retains anatomical eye"), Visual->GetViewEyeCenterWorld(HiddenEye));
                TestTrue(TEXT("hiding head cannot collapse camera into joint"), HiddenEye.Equals(ViewEye, .25));
                TestTrue(TEXT("raft camera API available"), Raft->GetGuideEyeWorldLocationCm(RoutedEye));
                TestTrue(TEXT("raft camera API uses production anchor"), RoutedEye.Equals(HiddenEye, .001));
                Guide->SetFirstPersonHeadHidden(false);
                Guide->SetAvatarActionPhaseForValidation(Action, Phase);
                TestTrue(TEXT("head restored"), Visual->GetRenderedEyeCenterWorld(RenderedEye));
                TestTrue(TEXT("eye restoration invariant"), RenderedEye.Equals(ViewEye, .25));
                ++Samples;
            }
        }
    }
    AddInfo(FString::Printf(TEXT("GUIDE_EYE samples=%d max_old_compact_eye_error_cm=%.3f"),
        Samples, MaxOldEyeErrorCm));
    TestEqual(TEXT("all posed world-frame samples exercised"), Samples, 80);
    return !HasAnyErrors();
}
#endif
