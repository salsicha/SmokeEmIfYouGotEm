#include "Misc/AutomationTest.h"
#include "Engine/StaticMesh.h"
#include "RaftSimRaftMesh.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include <limits>

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimAuthoredHullGeometryTest,
    "RaftSim.M1.AuthoredHullGeometryIdentity",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimAuthoredHullGeometryTest::RunTest(const FString&)
{
    using namespace RaftSimRaftMesh;
    const auto* Asset=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/RaftSim/Rafts/Production/SM_RaftSim_ProductionPaddleRaft.SM_RaftSim_ProductionPaddleRaft"));
    TArray<FMeshData> Rest,Deformed,Reference,PositionsOnly;
    FProductionRaftDeformationCache Cache,ReferenceCache,PositionsCache;
    if(!ExtractProductionRaftRestMesh(Asset,Rest)){AddError(TEXT("original CPU-readable production hull missing"));return false;}
    TestEqual(TEXT("all original material sections"),Rest.Num(),5);
    FRaftSimHullGeometry Hull;int32 ComparedVertices=0,ComparedFaces=0;double MaximumDisplacement=0.;
    TArray<FVector> Nominal;double MaximumShapeChangeM=0.;
    double ReferenceMs[2]={0,0},PreparedMs[2]={0,0};int32 TimedPairs[2]={0,0};
    const FTransform BodyFromVisual(FQuat::Identity,FVector(0,0,-28));
    for(int32 Phase=0;Phase<4;++Phase)
    {
        TArray<FRaftSimFlexVisualSegmentState> Segments;
        FRaftSimRaftVisualCondition Condition;
        if(Phase==1 || Phase==2)
        {
            FRaftSimFlexVisualSegmentState S;S.SegmentId=TEXT("authored_left_chamber");
            S.LocalPositionM=FVector(0,-.73,0);S.FreeboardLossM=.04;S.CompressionM=.09;
            S.IndentationM=.12;S.ContactNormalLocal=FVector(1,0,0);S.bPinned=true;Segments.Add(S);
            for(int32 I=0;I<11;++I)
            {
                FRaftSimFlexVisualSegmentState Extra;
                const double Angle=2.*PI*I/11.;
                Extra.SegmentId=FString::Printf(TEXT("source_binding_%d"),I);
                Extra.LocalPositionM=FVector(1.5*FMath::Cos(Angle),.73*FMath::Sin(Angle),.05);
                Extra.ContactNormalLocal=FVector(.25+.03*I,1,-.2).GetSafeNormal();
                Extra.IndentationM=.002*(I+1);Extra.FreeboardLossM=.0015*I;Extra.CompressionM=.0017*I;
                Extra.bWrapping=I%2==0;Extra.bPinned=I%3==0;Extra.bRecovering=I%4==0;Segments.Add(Extra);
            }
            if(Phase==2){Condition.PressureFraction=.62f;Condition.Integrity=.7f;Condition.CreaseAmplitudeM=.03f;}
        }
        DeformProductionRaftRestMesh(Rest,.28f,Segments,Condition,Deformed,&Cache);
        DeformProductionRaftRestMesh(Rest,.28f,Segments,Condition,Reference,&ReferenceCache,true,false);
        DeformProductionRaftRestMesh(Rest,.28f,Segments,Condition,PositionsOnly,&PositionsCache,false);
        for(int32 S=0;S<Rest.Num();++S)
            if(Deformed[S].Vertices!=Reference[S].Vertices || PositionsOnly[S].Vertices!=Reference[S].Vertices)
            {AddError(TEXT("prepared or positions-only geometry differs from repeated-evaluation reference"));return false;}
        // A renderer rebuilds shading from exactly the committed source inputs.
        DeformProductionRaftRestMesh(Rest,.28f,Segments,Condition,PositionsOnly,&PositionsCache);
        for(int32 S=0;S<Rest.Num();++S)
        {
            if(Deformed[S].Vertices!=Reference[S].Vertices || Deformed[S].Normals!=Reference[S].Normals ||
               PositionsOnly[S].Vertices!=Reference[S].Vertices || PositionsOnly[S].Normals!=Reference[S].Normals)
            {AddError(TEXT("deferred shading differs from exact committed reference"));return false;}
            for(int32 V=0;V<Reference[S].Tangents.Num();++V)
                if(Deformed[S].Tangents[V].TangentX!=Reference[S].Tangents[V].TangentX ||
                   PositionsOnly[S].Tangents[V].TangentX!=Reference[S].Tangents[V].TangentX ||
                   PositionsOnly[S].Tangents[V].bFlipTangentY!=Reference[S].Tangents[V].bFlipTangentY)
                {AddError(TEXT("authored tangent frame differs from repeated reference"));return false;}
        }
        if(!Segments.IsEmpty())for(int32 Repeat=0;Repeat<8;++Repeat)
        {
            const int32 Order=Repeat%2;
            const auto RunReference=[&]()
            {const double T=FPlatformTime::Seconds();DeformProductionRaftRestMesh(Rest,.28f,Segments,Condition,Reference,&ReferenceCache,true,false);ReferenceMs[Order]+=(FPlatformTime::Seconds()-T)*1000.;};
            const auto RunPrepared=[&]()
            {const double T=FPlatformTime::Seconds();DeformProductionRaftRestMesh(Rest,.28f,Segments,Condition,Deformed,&Cache);PreparedMs[Order]+=(FPlatformTime::Seconds()-T)*1000.;};
            if(Order==0){RunReference();RunPrepared();}else{RunPrepared();RunReference();}++TimedPairs[Order];
        }
        TestTrue(TEXT("export all current deformed surfaces"),ExportHullGeometry(Deformed,BodyFromVisual,Hull));
        if(!Hull.IsValid())return false;
        if(Phase==0)Nominal=Hull.VerticesM;
        else for(int32 V=0;V<Nominal.Num();++V)
            MaximumShapeChangeM=FMath::Max(MaximumShapeChangeM,(Hull.VerticesM[V]-Nominal[V]).Length());
        if(Phase==3)TestTrue(TEXT("recovered source returns to identical nominal geometry"),Hull.VerticesM==Nominal);
        for(int32 Section=0;Section<Rest.Num();++Section)
        {
            const auto& Original=Rest[Section];const auto& Render=Deformed[Section];const auto& R=Hull.Sections[Section];
            TestEqual(TEXT("every original source vertex retained"),R.VertexCount,Original.Vertices.Num());
            TestEqual(TEXT("every original indexed face retained"),R.FaceCount*3,Original.Triangles.Num());
            for(int32 V=0;V<R.VertexCount;++V)
            {
                const FVector Expected=(Render.Vertices[V]-FVector(0,0,28))*.01;
                if(Hull.VerticesM[R.VertexStart+V]!=Expected){AddError(TEXT("source/render/body coordinate mismatch"));return false;}
                ++ComparedVertices;
                MaximumDisplacement=FMath::Max(MaximumDisplacement,(Render.Vertices[V]-Original.Vertices[V]).Length());
            }
            for(int32 F=0;F<R.FaceCount;++F)
            {
                const FIntVector Expected(R.VertexStart+Original.Triangles[F*3],R.VertexStart+Original.Triangles[F*3+1],R.VertexStart+Original.Triangles[F*3+2]);
                if(Hull.Faces[R.FaceStart+F]!=Expected){AddError(TEXT("source face identity/winding changed"));return false;}
                ++ComparedFaces;
            }
        }
    }
    TestTrue(TEXT("nontrivial pressure/contact/crease shapes exercised"),MaximumDisplacement>5.);
    TestTrue(TEXT("deformation phases change the actual hull, not only its origin"),MaximumShapeChangeM>.02);
    const FTransform Changed(FRotator(13,7,-23),FVector(9,-12,-31),FVector(1.2,-.8,1.1));
    TestTrue(TEXT("explicit reflected/nonuniform component transform supported"),ExportHullGeometry(Deformed,Changed,Hull));
    TestTrue(TEXT("component transform is applied exactly once"),Hull.VerticesM[0]==Changed.TransformPosition(Deformed[0].Vertices[0])*.01);
    // Same-count topology edits must not reuse stale indices.
    Swap(Deformed[0].Triangles[0],Deformed[0].Triangles[1]);
    TestTrue(TEXT("same-count changed indexing refreshed"),ExportHullGeometry(Deformed,BodyFromVisual,Hull) && Hull.Faces[0].X==Deformed[0].Triangles[0]);
    Deformed[0].Triangles[0]=-1;
    TestFalse(TEXT("invalid source index refused"),ExportHullGeometry(Deformed,BodyFromVisual,Hull));
    TestFalse(TEXT("invalid export cannot leave a valid stale hull"),Hull.IsValid());
    Deformed[0].Triangles[0]=0;Deformed[0].Vertices[0].X=std::numeric_limits<double>::quiet_NaN();
    TestFalse(TEXT("nonfinite source vertex refused"),ExportHullGeometry(Deformed,BodyFromVisual,Hull));
    AddInfo(FString::Printf(TEXT("original authored hull: sections=%d vertices_compared=%d faces_compared=%d phases=4 max_displacement_cm=%.9g"),
        Rest.Num(),ComparedVertices,ComparedFaces,MaximumDisplacement));
    for(int32 Order=0;Order<2;++Order)
        AddInfo(FString::Printf(TEXT("same-input full-shading paired cost order=%d pairs=%d repeated_mean_ms=%.6f prepared_mean_ms=%.6f; not gameplay FPS"),
            Order,TimedPairs[Order],ReferenceMs[Order]/TimedPairs[Order],PreparedMs[Order]/TimedPairs[Order]));
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimHullSnapshotTransactionTest,
    "RaftSim.M1.FixedStepHullSnapshotTransaction",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimHullSnapshotTransactionTest::RunTest(const FString&)
{
    auto* Subject=NewObject<URaftSimChronoRuntimeAdapter>();auto* Control=NewObject<URaftSimChronoRuntimeAdapter>();
    for(auto* Adapter:{Subject,Control})
    {
        FRaftSimRaftBodyConfig Body;Body.MassKg=220;Body.TubeRadiusMeters=.28f;Body.LengthMeters=4.3f;Body.WidthMeters=2;
        Adapter->ConfigureRaftBody(Body);
        FRaftSimFlexParameters Flex;Flex.MassKg=220;Flex.LengthM=4.3;Flex.WidthM=2;Flex.TubeRadiusM=.28;Flex.PassengerCount=0;Flex.GuideMassKg=0;
        Adapter->ConfigureFlexibleRaftModel(Flex,{});
        Adapter->SetWaterSurfaceSampler([](const FVector&,float& Z){Z=0;return true;});
        FRaftSimRaftKinematicState State;State.WorldTransform.SetTranslation(FVector(0,0,18));State.LinearVelocityMetersPerSecond=FVector(1,.3,0);
        Adapter->SetKinematicState(State);
    }
    int32 Prepared=0,Committed=0;bool Reject=false,SameStep=true;
    const auto Prepare=[&](const TArray<FRaftSimFlexVisualSegmentState>& Segments,FRaftSimHullGeometry& Out)
    {
        ++Prepared;SameStep &= &Segments==&Subject->GetFlexibleVisualSegments();
        const double Z=Segments.IsEmpty()?0:Segments[0].FreeboardLossM;
        Out.VerticesM={FVector(0,0,Z),FVector(1,0,Z),FVector(0,1,Z)};
        Out.Faces={FIntVector(0,1,2)};Out.Sections={{0,3,0,1}};return !Reject;
    };
    TestTrue(TEXT("initial source snapshot published"),Subject->SetHullGeometryProvider(Prepare,[&](){++Committed;}));
    for(int32 I=0;I<12;++I)
    {
        if(I==4){Subject->SetFlexibleConditionModifiers(.7f,.8f);Control->SetFlexibleConditionModifiers(.7f,.8f);}
        TestTrue(TEXT("shared-source step succeeds"),Subject->StepRaftDynamics(1.f/120.f));
        TestTrue(TEXT("control step succeeds"),Control->StepRaftDynamics(1.f/120.f));
        const auto& A=Subject->GetKinematicState();const auto& B=Control->GetKinematicState();
        TestTrue(TEXT("geometry source alone does not alter rigid dynamics"),A.WorldTransform.Equals(B.WorldTransform,0.) &&
            A.LinearVelocityMetersPerSecond==B.LinearVelocityMetersPerSecond && A.AngularVelocityRadiansPerSecond==B.AngularVelocityRadiansPerSecond);
    }
    TestTrue(TEXT("provider uses the current fixed substep, not a later render copy"),SameStep);
    TestEqual(TEXT("one prepare and commit for initial state plus each substep"),Prepared,13);TestEqual(TEXT("all commits"),Committed,13);
    const auto Before=Subject->GetKinematicState();const auto Geometry=Subject->GetHullGeometry();const auto Revision=Subject->GetHullGeometryRevision();
    Reject=true;AddExpectedError(TEXT("Shared hull geometry rejected:"),EAutomationExpectedErrorFlags::Contains,1);
    TestFalse(TEXT("failed source preparation refuses step"),Subject->StepRaftDynamics(1.f/120.f));
    TestTrue(TEXT("failed source cannot publish pose or geometry"),Subject->GetKinematicState().WorldTransform.Equals(Before.WorldTransform,0.) &&
        Subject->GetHullGeometryRevision()==Revision && Subject->GetHullGeometry().VerticesM==Geometry.VerticesM && Committed==13);
    Reject=false;
    Subject->SetGroundSphereSweep([](const FVector&,const FVector&,double,FHitResult& H)
    {H.Time=0;H.bStartPenetrating=true;H.PenetrationDepth=1;H.Normal=FVector::UpVector;return true;});
    AddExpectedError(TEXT("Continuous ground review rejected: initial sphere overlap"),EAutomationExpectedErrorFlags::Contains,1);
    TestFalse(TEXT("later contact refusal also refuses prepared geometry"),Subject->StepRaftDynamics(1.f/120.f));
    TestTrue(TEXT("contact failure cannot commit the candidate hull"),Subject->GetHullGeometryRevision()==Revision &&
        Subject->GetHullGeometry().VerticesM==Geometry.VerticesM && Committed==13);
    Subject->SetGroundSphereSweep({});
    TestFalse(TEXT("missing commit endpoint rejected at initialization"),Subject->SetHullGeometryProvider(Prepare,{}));
    AddExpectedError(TEXT("Shared hull geometry rejected:"),EAutomationExpectedErrorFlags::Contains,1);
    TestFalse(TEXT("missing commit endpoint cannot be called on a later step"),Subject->StepRaftDynamics(1.f/120.f));
    Subject->ConfigureRaftBody(FRaftSimRaftBodyConfig{});
    TestTrue(TEXT("body reconfiguration clears old actor source and snapshots"),Subject->GetHullGeometryRevision()==0 && !Subject->GetHullGeometry().IsValid());
    return !HasAnyErrors();
}
#endif
