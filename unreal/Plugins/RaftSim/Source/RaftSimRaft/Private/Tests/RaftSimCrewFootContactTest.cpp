#include "Components/PoseableMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "UObject/Script.h"
#include "RaftSimCC0CrewVisualActor.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimRaftActor.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrewFootContactTest,
    "RaftSim.Crew.PlantedFeetShareBodyTargets",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimCrewFootContactTest::RunTest(const FString&)
{
    // Production adapters dispatch BlueprintNativeEvents. Editor automation
    // must allow that dispatch just as the editor scripting capture does.
    FEditorScriptExecutionGuard ScriptGuard;
    UWorld* World = nullptr;
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
        if (Context.WorldType == EWorldType::Editor) { World = Context.World(); break; }
    if (!TestNotNull(TEXT("registered editor world for actual child-body resources"), World)) return false;
    auto* Raft = World->SpawnActor<ARaftSimRaftActor>();
    if (!TestNotNull(TEXT("production raft"), Raft)) return false;
    ON_SCOPE_EXIT {
        TArray<AActor*> Owned;
        for (TActorIterator<ARaftSimCrewAvatarActor> It(World); It; ++It)
            if (It->GetOwner() == Raft) Owned.Add(*It);
        for (AActor* Host : Owned) World->DestroyActor(Host);
        World->DestroyActor(Raft);
    };
    Raft->InitializeCrewSeatingForValidation();
    int32 Crews = 0, Samples = 0;
    for (TActorIterator<ARaftSimCrewAvatarActor> It(World); It; ++It)
    {
        auto* Host = *It;
        if (Host->GetOwner() != Raft) continue;
        ++Crews;
        auto* Visual = Host->GetProductionVisualActor();
        auto* CC0 = Cast<ARaftSimCC0CrewVisualActor>(Visual);
        if (!TestTrue(TEXT("actual production body initialized"), CC0 && CC0->IsBodyReady())) continue;
        auto* Body = Visual ? Visual->FindComponentByClass<UPoseableMeshComponent>() : nullptr;
        if (!TestNotNull(TEXT("owned rendered body"), Body)) continue;
        TArray<UStaticMeshComponent*> Boots;
        TInlineComponentArray<UStaticMeshComponent*> Components(Host);
        for (auto* Component : Components)
            if (Component->GetName() == TEXT("ProductionLeftBoot") || Component->GetName() == TEXT("ProductionRightBoot"))
                Boots.Add(Component);
        if (!TestEqual(TEXT("both actual boots"), Boots.Num(), 2)) continue;
        for (int32 Action = 0; Action <= static_cast<int32>(ERaftSimCrewAvatarAction::HighSideStarboard); ++Action)
        {
            // Non-unit intensity also checks that the body no longer evaluates
            // a differently time-scaled copy of the host's solved pose.
            Host->SetAvatarAction(static_cast<ERaftSimCrewAvatarAction>(Action), Action % 2 ? 1.4f : 0.6f);
            TArray<FTransform> Planted;
            for (auto* Boot : Boots) Planted.Add(Boot->GetRelativeTransform());
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
                    TestTrue(FString::Printf(TEXT("body foot and boot share target (%s %s delta=%s)"),
                        *Host->GetName(),*Bone.ToString(),*(BodyTarget-Target).ToString()), Target.Equals(BodyTarget,0.05));
                    TestTrue(FString::Printf(TEXT("grounded boot stays planted (%s action=%d step=%d %s initial=%s current=%s)"),
                        *Host->GetName(),Action,Step,*Bone.ToString(),*Planted[Foot].ToString(),
                        *Boot->GetRelativeTransform().ToString()),
                        Boot->GetRelativeTransform().Equals(Planted[Foot],0.01));
                }
                ++Samples;
            }
        }
        Host->SetAvatarAction(ERaftSimCrewAvatarAction::SeatedIdle);
        TestTrue(TEXT("fitting feet preserves actual glute contact"),
            FMath::Abs(Raft->GetCrewSeatContactClearanceCm(Host)+1.0f) < 0.05f);
        const FVector Seat = Host->GetRootComponent()->GetRelativeLocation();
        TArray<FVector> Before;
        for (auto* Boot : Boots) Before.Add(Boot->GetComponentLocation());
        for (double Lift : {1.0,0.0})
        {
            Host->SetActorRelativeLocation(Seat+FVector(0,0,Lift));
            Host->SetAvatarAction(ERaftSimCrewAvatarAction::SeatedIdle);
            for (int32 Foot = 0; Foot < Boots.Num(); ++Foot)
                TestTrue(TEXT("relative-seat changes invalidate cached support"),
                    Boots[Foot]->GetComponentLocation().Equals(Before[Foot],0.01));
        }
    }
    TestEqual(TEXT("all production seats tested"),Crews,5);
    TestEqual(TEXT("five identities, eight actions, eight time steps"),Samples,320);
    const uint64 BeforeRebuild = Raft->GetCrewSupportGeometryRevision();
    Raft->InitializeCrewSeatingForValidation();
    TestTrue(TEXT("uploaded geometry rebuild advances support revision"),
        Raft->GetCrewSupportGeometryRevision() > BeforeRebuild);
    return true;
}
#endif
