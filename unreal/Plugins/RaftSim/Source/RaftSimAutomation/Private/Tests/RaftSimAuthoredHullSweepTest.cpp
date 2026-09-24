#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "RaftSimRaftMesh.h"
#include "RaftSimGroundSourceRegistry.h"
#include "Interface_CollisionDataProviderCore.h"

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
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimHullGroupedBroadPhaseTest,"RaftSim.M1.HullGroupedBroadPhase",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimHullGroupedBroadPhaseTest::RunTest(const FString&)
{
    using namespace RaftSimRaftMesh;using namespace RaftSimSurfaceSweep;
    const auto* Asset=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/RaftSim/Rafts/Production/SM_RaftSim_ProductionPaddleRaft.SM_RaftSim_ProductionPaddleRaft"));
    TArray<FMeshData> Rest;
    FRaftSimHullGeometry Hull;
    if(!ExtractProductionRaftRestMesh(Asset,Rest) || !ExportHullGeometry(Rest,FTransform(FVector(0,0,-28)),Hull))return false;
    TestEqual(TEXT("all production faces retained"),Hull.Faces.Num(),38344);
    UWorld* World=UWorld::CreateWorld(EWorldType::Editor,false);if(!World)return false;
    ON_SCOPE_EXIT{World->DestroyWorld(false);World->RemoveFromRoot();};
    auto* Ground=World->SpawnActor<AStaticMeshActor>();if(!Ground)return false;
    Ground->Tags.Add(TEXT("RaftSimPhysicalGround"));
    for(const TCHAR* Path:{TEXT("/Engine/BasicShapes/Cube.Cube"),
        TEXT("/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround.SM_TroublemakerCapturedGround")})
    {
        auto* Mesh=LoadObject<UStaticMesh>(nullptr,Path);if(!Mesh)return false;
        FTriMeshCollisionData Data;if(!Mesh->GetPhysicsTriMeshData(&Data,false) || Data.Indices.IsEmpty())return false;
        Ground->GetStaticMeshComponent()->SetStaticMesh(Mesh);
        Ground->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
        Ground->SetActorTransform(FTransform(FRotator(0,17,0),FVector(-543186,-360044,235),FVector(1,-1,1)));
        FRaftSimGroundSourceRegistry Registry(World);
        double ReferenceMs[2]={},GroupedMs[2]={};int32 Cases=0;
        for(int32 Case=0;Case<3;++Case)
        {
            const auto& F=Data.Indices[(Data.Indices.Num()-1)*Case/2];
            const FVector Center=(FVector(Data.Vertices[F.v0])+FVector(Data.Vertices[F.v1])+FVector(Data.Vertices[F.v2]))/3.;
            TArray<FVector> Start,End;
            for(int32 I=0;I<Hull.VerticesM.Num();++I)
            {
                const FVector A=Center+Hull.VerticesM[I]*100.+FVector(0,0,500);
                // Includes clear, crossing and independent shape-change paths.
                const FVector B=A+FVector(3,5,Case==0?1.:-1000.)+FVector(0,0,Case==2?(I%7)*.1:0.);
                Start.Add(Ground->GetActorTransform().TransformPosition(A));
                End.Add(Ground->GetActorTransform().TransformPosition(B));
            }
            Registry.SweepCapturedSurface(Start,End,Hull.Faces,.001,1.e-7,false); // build outside timings
            for(int32 Order=0;Order<2;++Order)
            {
                double Ms[2]={};
                for(int32 Repeat=0;Repeat<4;++Repeat)
                {
                    FResult Pair[2];
                    for(int32 Step=0;Step<2;++Step)
                    {
                        const int32 Cached=Order==0?Step:1-Step;
                        const double Began=FPlatformTime::Seconds();
                        Pair[Cached]=Registry.SweepCapturedSurface(Start,End,Hull.Faces,.001,1.e-7,true,Cached!=0);
                        Ms[Cached]+=(FPlatformTime::Seconds()-Began)*1000.;
                    }
                    const auto& A=Pair[0];const auto& B=Pair[1];
                    TestTrue(TEXT("static face bounds preserve complete query outcome"),
                        A.Status==B.Status && A.Time==B.Time && A.TrianglePairs==B.TrianglePairs &&
                        A.Iterations==B.Iterations && A.MovingFace==B.MovingFace && A.GroundFace==B.GroundFace &&
                        A.GroundComponent==B.GroundComponent && A.Normal==B.Normal &&
                        A.Witness.MovingPoint==B.Witness.MovingPoint && A.Witness.GroundPoint==B.Witness.GroundPoint &&
                        A.Witness.MovingBary==B.Witness.MovingBary && A.Witness.GroundBary==B.Witness.GroundBary &&
                        A.Witness.Squared==B.Witness.Squared);
                }
                AddInfo(FString::Printf(TEXT("static-face-bounds source=%s case=%d order=%d uncached_ms=%.6f cached_ms=%.6f"),Path,Case,Order,Ms[0],Ms[1]));
            }
            for(int32 Order=0;Order<2;++Order)
            {
                FResult R,G;
                const auto Run=[&](bool Grouped)
                {
                    const double Began=FPlatformTime::Seconds();
                    auto X=Registry.SweepCapturedSurface(Start,End,Hull.Faces,.001,1.e-7,Grouped);
                    (Grouped?GroupedMs[Order]:ReferenceMs[Order])+=(FPlatformTime::Seconds()-Began)*1000.;return X;
                };
                if(Order==0){R=Run(false);G=Run(true);}else{G=Run(true);R=Run(false);}
                TestTrue(TEXT("grouped traversal preserves status and pair count"),R.Status==G.Status && R.TrianglePairs==G.TrianglePairs);
                TestTrue(TEXT("grouped traversal preserves exact source identity and TOI"),R.Time==G.Time && R.MovingFace==G.MovingFace && R.GroundFace==G.GroundFace && R.GroundComponent==G.GroundComponent);
                TestTrue(TEXT("grouped traversal preserves exact witnesses and normals"),R.Normal==G.Normal && R.Witness.MovingPoint==G.Witness.MovingPoint && R.Witness.GroundPoint==G.Witness.GroundPoint && R.Witness.MovingBary==G.Witness.MovingBary && R.Witness.GroundBary==G.Witness.GroundBary && R.Witness.Squared==G.Witness.Squared && R.Iterations==G.Iterations);
                TestTrue(TEXT("fixture cannot silently become invalid"),R.Status!=EStatus::Invalid);
                ++Cases;
            }
        }
        for(int32 Order=0;Order<2;++Order)
            AddInfo(FString::Printf(TEXT("full-hull grouped source=%s source_faces=%d moving_faces=%d cases=%d order=%d reference_ms=%.6f grouped_ms=%.6f; same inputs, not gameplay FPS"),Path,Data.Indices.Num(),Hull.Faces.Num(),Cases/2,Order,ReferenceMs[Order],GroupedMs[Order]));
    }
    return true;
}
#endif
