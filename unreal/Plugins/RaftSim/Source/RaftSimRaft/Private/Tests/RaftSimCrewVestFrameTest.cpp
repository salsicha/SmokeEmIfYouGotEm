#include "Components/PoseableMeshComponent.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "RaftSimCC0CrewVisualActor.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrewVestFrameTest,
    "RaftSim.Crew.VestFollowsTorsoNotHead",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimCrewVestFrameTest::RunTest(const FString&)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Editor, false);
    if (!TestNotNull(TEXT("review world"), World)) return false;
    ON_SCOPE_EXIT { World->DestroyWorld(false); World->RemoveFromRoot(); };
    const ERaftSimCrewAvatarAction Actions[] = {
        ERaftSimCrewAvatarAction::SeatedIdle, ERaftSimCrewAvatarAction::ForwardStroke,
        ERaftSimCrewAvatarAction::Brace, ERaftSimCrewAvatarAction::Reentry};
    int32 Checked = 0;
    for (int32 Identity = 0; Identity < 5; ++Identity)
    {
        auto* Visual = World->SpawnActor<ARaftSimCC0CrewVisualActor>();
        if (!TestNotNull(TEXT("CC0 actor"), Visual)) continue;
        Visual->ConfigureCrewAppearance_Implementation(FMath::Max(0, Identity - 1), 0, Identity == 0);
        if (!TestTrue(TEXT("actual selected body loaded"), Visual->IsBodyReady())) continue;
        auto* Body = Visual->FindComponentByClass<UPoseableMeshComponent>();
        if (!TestNotNull(TEXT("rendered poseable body"), Body)) continue;
        for (const auto Action : Actions)
        {
            for (const float Phase : {0.0f, 0.3f, 0.7f})
            {
                Visual->ApplyCrewPose_Implementation(Action, Phase, 1.0f, 0);
                FTransform Before;
                if (!TestTrue(TEXT("finite chest frame exists"), Visual->GetSolvedChestWorldTransform(Before))) continue;
                TestFalse(TEXT("chest frame finite"), Before.ContainsNaN());
                if (Action == ERaftSimCrewAvatarAction::SeatedIdle)
                {
                    TestTrue(TEXT("chest points forward, not mirrored"),
                        FVector::DotProduct(Before.GetUnitAxis(EAxis::X), Visual->GetActorForwardVector()) > 0.95);
                }
                const FTransform OriginalHead = Body->GetBoneTransformByName(TEXT("head"), EBoneSpaces::ComponentSpace);
                FTransform TurnedHead = OriginalHead;
                TurnedHead.SetRotation((FQuat(FVector::UpVector, 1.2) * OriginalHead.GetRotation()).GetNormalized());
                Body->SetBoneTransformByName(TEXT("head"), TurnedHead, EBoneSpaces::ComponentSpace);
                Body->RefreshBoneTransforms();
                TestTrue(TEXT("head perturbation actually reached the rendered rig"),
                    Body->GetBoneTransformByName(TEXT("head"), EBoneSpaces::ComponentSpace)
                        .GetRotation().AngularDistance(OriginalHead.GetRotation()) > 0.5);
                FTransform After;
                TestTrue(TEXT("chest frame survives head turn"), Visual->GetSolvedChestWorldTransform(After));
                TestTrue(TEXT("head turn cannot rotate or translate vest"), Before.Equals(After, 0.0001));
                Body->SetBoneTransformByName(TEXT("head"), OriginalHead, EBoneSpaces::ComponentSpace);
                Body->RefreshBoneTransforms();
                ++Checked;
            }
        }
        // The scoped review world owns all five actors. Let its teardown
        // release them; gameplay Destroy() requires a registered world context.
    }
    TestEqual(TEXT("five identities, four poses, three phases checked"), Checked, 60);
    return true;
}
#endif
