#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "RaftSimRaftMesh.h"
#include "RaftSimGroundSourceRegistry.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimAuthoredHullSurfaceSweepTest,"RaftSim.M1.AuthoredHullSurfaceSweep",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimAuthoredHullSurfaceSweepTest::RunTest(const FString&)
{
    using namespace RaftSimRaftMesh;
    using namespace RaftSimSurfaceSweep;
    const auto* Asset=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/RaftSim/Rafts/Production/SM_RaftSim_ProductionPaddleRaft.SM_RaftSim_ProductionPaddleRaft"));
    TArray<FMeshData> Rest,Deformed;FProductionRaftDeformationCache Cache;
    if(!ExtractProductionRaftRestMesh(Asset,Rest)){AddError(TEXT("original authored hull unavailable"));return false;}
    UWorld* World=UWorld::CreateWorld(EWorldType::Editor,false);if(!World)return false;
    ON_SCOPE_EXIT{World->DestroyWorld(false);World->RemoveFromRoot();};
    auto* Ground=World->SpawnActor<AStaticMeshActor>();
    auto* Cube=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube"));
    if(!Ground || !Cube)return false;
    Ground->Tags.Add(TEXT("RaftSimPhysicalGround"));Ground->GetStaticMeshComponent()->SetStaticMesh(Cube);
    Ground->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Ground->SetActorScale3D(FVector(20,20,.2)); // analytic top is z=0.1 m
    FRaftSimGroundSourceRegistry Registry(World);
    TArray<FVector> NominalVertices;
    for(int32 Phase=0;Phase<3;++Phase)
    {
        TArray<FRaftSimFlexVisualSegmentState> Segments;FRaftSimRaftVisualCondition Condition;
        if(Phase)
        {
            FRaftSimFlexVisualSegmentState S;S.LocalPositionM=FVector(0,-.73,0);
            S.IndentationM=.12;S.FreeboardLossM=.04;S.CompressionM=.09;
            S.ContactNormalLocal=FVector(1,0,0);S.bPinned=true;Segments.Add(S);
            Condition.PressureFraction=.62f;Condition.Integrity=.7f;Condition.CreaseAmplitudeM=.03f;
        }
        DeformProductionRaftRestMesh(Rest,.28f,Segments,Condition,Deformed,&Cache);
        FRaftSimHullGeometry Hull;
        if(!ExportHullGeometry(Deformed,FTransform(FVector(0,0,-28)),Hull))return false;
        TestEqual(TEXT("all authored vertices swept"),Hull.VerticesM.Num(),26610);
        TestEqual(TEXT("all authored triangles swept"),Hull.Faces.Num(),38344);
        TestEqual(TEXT("all authored material sections included"),Hull.Sections.Num(),5);
        if(Phase==0)NominalVertices=Hull.VerticesM;
        TArray<FVector> Start,End;double Expected=1.;
        for(int32 I=0;I<Hull.VerticesM.Num();++I)
        {
            const auto& V=Hull.VerticesM[I];
            // Third case changes the entire authored shape during the sweep,
            // not just a rigid translation of an already deformed endpoint.
            const FVector A=(Phase==2?NominalVertices[I]:V)+FVector(0,0,2);
            const FVector B=V-FVector(0,0,2);
            Start.Add(A*100.);End.Add(B*100.);
            Expected=FMath::Min(Expected,(A.Z-.1-1.e-5)/(A.Z-B.Z));
        }
        const double Started=FPlatformTime::Seconds();
        const auto Result=Registry.SweepCapturedSurface(Start,End,Hull.Faces,.001);
        const double ElapsedMs=(FPlatformTime::Seconds()-Started)*1000.;
        TestTrue(FString::Printf(TEXT("entire production hull finds first ground contact, status=%d"),int32(Result.Status)),Result.Status==EStatus::Contact);
        TestTrue(TEXT("TOI matches independent minimum over every authored vertex"),FMath::Abs(Result.Time-Expected)<1.e-9);
        TestTrue(TEXT("contact retains original authored/source faces"),Hull.Faces.IsValidIndex(Result.MovingFace) && Result.GroundFace!=INDEX_NONE);
        TestTrue(TEXT("contact normal points out of ground"),Result.Normal.Z>1.-1.e-9);
        AddInfo(FString::Printf(TEXT("full authored surface phase=%d vertices=%d triangles=%d pairs=%llu toi=%.17g expected=%.17g query_ms=%.6f moving_face=%d ground_face=%d iterations=%d distance=%.17g; not rigid/deforming integration or FPS acceptance"),
            Phase,Hull.VerticesM.Num(),Hull.Faces.Num(),Result.TrianglePairs,Result.Time,Expected,ElapsedMs,
            Result.MovingFace,Result.GroundFace,Result.Iterations,FMath::Sqrt(Result.Witness.Squared)));
    }
    return true;
}
#endif
