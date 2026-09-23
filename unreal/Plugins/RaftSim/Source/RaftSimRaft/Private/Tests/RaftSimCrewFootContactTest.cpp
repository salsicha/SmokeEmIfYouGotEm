#include "Components/PoseableMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimRaftActor.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrewFootContactTest,
    "RaftSim.Crew.PlantedFeetShareBodyTargets",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimCrewFootContactTest::RunTest(const FString&)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Editor, false);
    if (!TestNotNull(TEXT("review world"), World)) return false;
    ON_SCOPE_EXIT { World->DestroyWorld(false); World->RemoveFromRoot(); };
    auto* Raft = World->SpawnActor<ARaftSimRaftActor>();
    if (!TestNotNull(TEXT("production raft"), Raft)) return false;
    Raft->InitializeCrewSeatingForValidation();
    int32 Crews = 0, Samples = 0;
    for (TActorIterator<ARaftSimCrewAvatarActor> It(World); It; ++It)
    {
        auto* Host = *It;
        if (Host->GetOwner() != Raft) continue;
        ++Crews;
        auto* Visual = Host->GetProductionVisualActor();
        auto* Body = Visual ? Visual->FindComponentByClass<UPoseableMeshComponent>() : nullptr;
        if (!TestNotNull(TEXT("owned rendered body"), Body)) continue;
        TArray<UStaticMeshComponent*> Boots;
        TInlineComponentArray<UStaticMeshComponent*> Components(Host);
        for (auto* Component : Components)
            if (Component->GetName() == TEXT("ProductionLeftBoot") || Component->GetName() == TEXT("ProductionRightBoot"))
                Boots.Add(Component);
        if (!TestEqual(TEXT("both actual boots"), Boots.Num(), 2)) continue;
        TArray<FTransform> Planted;
        for (auto* Boot : Boots) Planted.Add(Boot->GetRelativeTransform());
        for (int32 Action = 0; Action <= static_cast<int32>(ERaftSimCrewAvatarAction::HighSideStarboard); ++Action)
        {
            // Non-unit intensity also checks that the body no longer evaluates
            // a differently time-scaled copy of the host's solved pose.
            Host->SetAvatarAction(static_cast<ERaftSimCrewAvatarAction>(Action), Action % 2 ? 1.4f : 0.6f);
            for (int32 Step = 0; Step < 8; ++Step)
            {
                Host->Tick(0.1f);
                TestTrue(TEXT("all renderer transforms remain finite"), Host->HasFiniteVisualTransforms());
                for (int32 Foot = 0; Foot < Boots.Num(); ++Foot)
                {
                    auto* Boot = Boots[Foot];
                    const bool bLeft = Boot->GetName() == TEXT("ProductionLeftBoot");
                    const FName Bone = bLeft ? TEXT("foot_l") : TEXT("foot_r");
                    const double ProfileZ = Host->GetBodyProportionScale().Z;
                    const double Offset = Boot->GetStaticMesh()->GetBoundingBox().Min.Z *
                        (ProfileZ-Boot->GetRelativeScale3D().Z);
                    const FVector Target = Boot->GetComponentLocation()-Host->GetActorUpVector()*Offset;
                    const FVector BodyTarget = Body->GetBoneTransformByName(Bone, EBoneSpaces::WorldSpace).GetLocation();
                    TestTrue(TEXT("body foot and boot share the exact target"), Target.Equals(BodyTarget,0.05));
                    TestTrue(TEXT("grounded boots do not slide or yaw with torso/high-side"),
                        Boot->GetRelativeTransform().Equals(Planted[Foot],0.01));
                }
                ++Samples;
            }
        }
        Host->SetAvatarAction(ERaftSimCrewAvatarAction::SeatedIdle);
        TestTrue(TEXT("fitting feet preserves actual glute contact"),
            FMath::Abs(Raft->GetCrewSeatContactClearanceCm(Host)+1.0f) < 0.05f);
    }
    TestEqual(TEXT("all production seats tested"),Crews,5);
    TestEqual(TEXT("five identities, eight actions, eight time steps"),Samples,320);
    return true;
}
#endif
