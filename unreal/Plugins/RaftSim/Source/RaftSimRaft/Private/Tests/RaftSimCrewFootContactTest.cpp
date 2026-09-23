#include "Components/PoseableMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "UObject/Script.h"
#include "RaftSimCC0CrewVisualActor.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimRaftActor.h"
#include "ProceduralMeshComponent.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrewSupportIndexTest,
    "RaftSim.Crew.SupportIndexMatchesUploadedTriangles",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimCrewSupportIndexTest::RunTest(const FString&)
{
    FEditorScriptExecutionGuard ScriptGuard;
    UWorld* World=nullptr;
    for(const FWorldContext& Context:GEngine->GetWorldContexts())
        if(Context.WorldType==EWorldType::Editor){World=Context.World();break;}
    if(!TestNotNull(TEXT("editor world"),World))return false;
    auto* Raft=World->SpawnActor<ARaftSimRaftActor>();
    if(!TestNotNull(TEXT("actual raft"),Raft))return false;
    ON_SCOPE_EXIT {
        TArray<AActor*> Owned;
        for(TActorIterator<ARaftSimCrewAvatarActor> It(World);It;++It)if(It->GetOwner()==Raft)Owned.Add(*It);
        for(AActor* Host:Owned)World->DestroyActor(Host);
        World->DestroyActor(Raft);
    };
    Raft->InitializeCrewSeatingForValidation();
    UProceduralMeshComponent* Mesh=nullptr;
    TInlineComponentArray<UProceduralMeshComponent*> Components(Raft);
    for(auto* C:Components)if(C->GetName()==TEXT("RaftVisual"))Mesh=C;
    if(!TestNotNull(TEXT("uploaded raft mesh"),Mesh))return false;
    TArray<FVector> Points;
    for(int32 X=-300;X<=300;X+=5)for(int32 Y=-150;Y<=150;Y+=5)Points.Add(FVector(X,Y,0));
    // Exact vertices and points straddling bin edges complement the broad grid.
    const FProcMeshSection* Section=Mesh->GetProcMeshSection(0);
    for(int32 I=0;I<Section->ProcVertexBuffer.Num();I+=37)
        Points.Add(Mesh->GetRelativeTransform().TransformPosition(FVector(Section->ProcVertexBuffer[I].Position)));
    for(double Epsilon:{-1.e-7,0.,1.e-7})Points.Add(FVector(80.+Epsilon,20.-Epsilon,0));
    const FVector Original=Mesh->GetRelativeLocation();
    for(int32 State=0;State<3;++State)
    {
        if(State==1)Mesh->SetRelativeLocation(Original+FVector(0,0,.25));
        if(State==2){Mesh->SetRelativeLocation(Original);Raft->InitializeCrewSeatingForValidation();}
        TArray<double> Floor,Solid,ReferenceFloor,ReferenceSolid;
        const bool Actual=Raft->SampleRenderedCrewSupport(Points,Floor,Solid);
        const bool Reference=Raft->SampleRenderedCrewSupport(Points,ReferenceFloor,ReferenceSolid,true);
        TestEqual(TEXT("identical supported/missing status"),Actual,Reference);
        TestTrue(FString::Printf(TEXT("exact floor samples after lifecycle state%d"),State),Floor==ReferenceFloor);
        TestTrue(FString::Printf(TEXT("exact solid samples after lifecycle state%d"),State),Solid==ReferenceSolid);
    }
    AddInfo(FString::Printf(TEXT("Support reference equality: %d points x3 states; indexed_review=%d"),Points.Num(),
        FParse::Param(FCommandLine::Get(),TEXT("RaftSimReviewHighSideContact"))));
    return true;
}

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
            const bool bContactExpected = Action <= static_cast<int32>(ERaftSimCrewAvatarAction::Brace) ||
                FParse::Param(FCommandLine::Get(),TEXT("RaftSimReviewHighSideContact"));
            // Do not let an authored fallback satisfy the anchor-only checks.
            // Opt-in trial retains the full high-side gate; default exclusion
            // is not a passing high-side reconstruction/contact result.
            TestEqual(FString::Printf(TEXT("contact solve matches qualified scope (%s action=%d)"),*Host->GetName(),Action),
                Host->HasPlantedRenderedFeet(),bContactExpected);
            TArray<FTransform> Planted;
            for (auto* Boot : Boots) Planted.Add(Boot->GetRelativeTransform());
            for (int32 Step = 0; Step < 8; ++Step)
            {
                Host->Tick(0.1f);
                TestEqual(FString::Printf(TEXT("contact solve scope remains unchanged in motion (%s action=%d step=%d)"),*Host->GetName(),Action,Step),Host->HasPlantedRenderedFeet(),bContactExpected);
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
