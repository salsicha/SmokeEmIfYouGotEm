#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "Serialization/JsonSerializer.h"
#include "Dom/JsonObject.h"
#include "RaftSimFlipTestEnvironment.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimCrewSeatLayout.h"
#include "RaftSimFlipCandidateLoads.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "RaftSimCapsizePolicy.h"
#include "RaftSimImplicitDrag.h"
#include "RaftSimContactWitnessPrune.h"
#include "RaftSimSwimmerSubmersion.h"
#include "RaftSimFlipObstacle.h"
#include "RaftSimHullPrepareCache.h"
#include "RaftSimRaftActor.h"
#include "RaftSimGroundSourceRegistry.h"
#include "RaftSimFaceOrdering.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "Misc/ScopeExit.h"
#include <limits>
#include <type_traits>

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimProductionCapturedRockPin,
    "RaftSim.Production.CapturedRockPin",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::ClientContext|EAutomationTestFlags::ProductFilter)
bool FRaftSimProductionCapturedRockPin::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Editor,false);if(!World)return false;
    ON_SCOPE_EXIT{World->DestroyWorld(false);World->RemoveFromRoot();};
    auto* Rock=World->SpawnActor<AStaticMeshActor>();auto* Cube=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube"));
    if(!Rock || !Cube)return false;
    Rock->Tags.Add(TEXT("RaftSimPhysicalGround"));Rock->GetStaticMeshComponent()->SetStaticMesh(Cube);
    Rock->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Rock->SetActorScale3D(FVector(1.2,2.4,5.5));Rock->SetActorLocation(FVector(0,0,-125));
    auto Sources=MakeShared<FRaftSimGroundSourceRegistry>(World);
    const auto Scenes=RaftSimFlipTestEnvironment::Scenes();
    const auto Scene=*Scenes.FindByPredicate([](const auto& S){return S.Name==TEXT("rock_pin_broadside");});
    const auto* Defaults=GetDefault<ARaftSimRaftActor>();
    auto* Runtime=NewObject<URaftSimChronoRuntimeAdapter>(World);
    FRaftSimRaftBodyConfig Body;Body.Runtime=ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;
    Body.MassKg=Defaults->MassKg+85.f+75.f*Defaults->PaddlerCount;
    Body.LengthMeters=Defaults->FootprintLengthM;Body.WidthMeters=Defaults->FootprintWidthM;Body.TubeRadiusMeters=Defaults->TubeRadiusM;
    const float Yaw=Body.MassKg*(Body.LengthMeters*Body.LengthMeters+Body.WidthMeters*Body.WidthMeters)/12.f;
    Body.InertiaTensorKgM2=FVector(.45f*Yaw,.45f*Yaw,Yaw);Body.BuoyancyWeightMultiple=5.2f;Body.LinearDragCoefficient=9000.f;
    FRaftSimFlexParameters Flex;Flex.MassKg=Defaults->MassKg;Flex.GuideMassKg=85.;Flex.PassengerMassKg=75.;Flex.PassengerCount=Defaults->PaddlerCount;
    Flex.LengthM=Body.LengthMeters;Flex.WidthM=Body.WidthMeters;Flex.TubeRadiusM=Body.TubeRadiusMeters;
    Runtime->ConfigureRaftBody(Body);Runtime->ConfigureFlexibleRaftModel(Flex,RaftSimCrewSeatLayout::BuildNormalSeats(Flex,false),18000.,true);
    double Seconds=0.;
    Runtime->SetWaterSurfaceSampler([&](const FVector& P,float& H){H=Scene.Surface(P,Seconds)*100.;return Scene.Wet(P);});
    Runtime->SetFlexibleWaterFieldSampler([&](const FVector& P,FRaftSimFlexUniformWater& W){W.bWet=Scene.Wet(P);W.SurfaceHeightM=Scene.Surface(P,Seconds);W.VelocityMps=Scene.Velocity(P,Seconds);return true;});
    Runtime->SetGroundSurfaceSampler([&](const FVector& P,float& Z,FVector& N){double G;if(Sources->SampleGround(P,G,N)){Z=float(G);return true;}Z=-400.f;N=FVector::UpVector;return true;});
    Runtime->SetHullGroundQuery([Sources](auto A,auto B,auto F,double Skin,double Clearance){return Sources->SweepCapturedSurface(A,B,F,Skin,Clearance);});
    bool ReferenceChecked=false;
    Runtime->SetHullGroundArcQuery([&,Sources](auto A,auto B,auto F,double Skin,double Clearance,const FRaftSimHullArcPath& Arc)
    {
        auto Fast=Sources->SweepCapturedSurface(A,B,F,Skin,Clearance,true,&Arc);
        if(!ReferenceChecked && Fast.Status==RaftSimSurfaceSweep::EStatus::Contact)
        {
            const auto ExactReference=Sources->SweepCapturedSurface(A,B,F,Skin,Clearance,false,&Arc);
            ReferenceChecked=true;
            TestEqual(TEXT("original-face hierarchy retains exhaustive contact status"),int32(Fast.Status),int32(ExactReference.Status));
            TestEqual(TEXT("original-face hierarchy retains moving face ID"),Fast.MovingFace,ExactReference.MovingFace);
            TestEqual(TEXT("original-face hierarchy retains captured ground face ID"),Fast.GroundFace,ExactReference.GroundFace);
            TestTrue(TEXT("original-face hierarchy retains contact time"),FMath::Abs(Fast.Time-ExactReference.Time)<1.e-9);
            TestTrue(TEXT("original-face hierarchy retains both exact witnesses"),
                Fast.Witness.MovingPoint.Equals(ExactReference.Witness.MovingPoint,1.e-9) &&
                Fast.Witness.GroundPoint.Equals(ExactReference.Witness.GroundPoint,1.e-9) &&
                Fast.Normal.Equals(ExactReference.Normal,1.e-9));
        }
        return Fast;
    });
    TArray<RaftSimRaftMesh::FMeshData> Rest,Prepared;
    const auto* Asset=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/RaftSim/Rafts/Production/SM_RaftSim_ProductionPaddleRaft.SM_RaftSim_ProductionPaddleRaft"));
    if(!RaftSimRaftMesh::ExtractProductionRaftRestMesh(Asset,Rest)){AddError(TEXT("Original production asset missing"));return false;}
    RaftSimRaftMesh::FProductionRaftDeformationCache DeformCache;RaftSimHullPrepareCache::FCache Exact;
    const FTransform Datum(FQuat::Identity,FVector(0,0,-Body.TubeRadiusMeters*100.));
    if(!Runtime->SetHullGeometryProvider([&](const auto& Segments,FRaftSimHullGeometry& H)
        {
            const RaftSimRaftMesh::FRaftSimRaftVisualCondition C={Runtime->GetFlexiblePressureFraction(),Runtime->GetFlexibleFabricIntegrity(),0.f};
            if(Exact.Matches(Rest,Body.TubeRadiusMeters,Segments,C,Datum)){H=Exact.Hull;return true;}
            RaftSimRaftMesh::DeformProductionRaftRestMesh(Rest,Body.TubeRadiusMeters,Segments,C,Prepared,&DeformCache,false);
            const bool Good=RaftSimRaftMesh::ExportHullGeometry(Prepared,Datum,H);
            if(Good)Exact.Remember(Rest,Body.TubeRadiusMeters,Segments,C,Datum,Prepared,H);return Good;
        },[]{}))return false;
    TestEqual(TEXT("actual full original hull triangles"),Runtime->GetHullGeometry().Faces.Num(),38344);
    const FQuat Q=FRotator(0,90,0).Quaternion();double Half=0.;
    for(const auto& V:Runtime->GetHullGeometry().VerticesM)Half=FMath::Max(Half,Q.RotateVector(V).X);
    FVector P((-.6-Half-.4)*100.,0,0);P.Z=Scene.Surface(P,0.)*100.+20.;
    FRaftSimRaftKinematicState Initial;Initial.WorldTransform=FTransform(Q,P);Initial.LinearVelocityMetersPerSecond=FVector(1.5,0,0);Runtime->SetKinematicState(Initial);
    int32 Impulses=0;double Lift=-1.,Scoop=-1.,Flip=-1.;
    for(int32 I=0;I<480;++I)
    {
        Seconds=I/120.;if(!Runtime->StepRaftDynamics(1.f/120.f)){AddError(FString::Printf(TEXT("Captured original-mesh step %d refused: %s"),I,*Runtime->GetLastHullContact().Failure));break;}
        const auto& K=Runtime->GetKinematicState();const auto R=K.WorldTransform.GetRotation();
        Impulses+=Runtime->GetLastHullContact().Impulses;
        const double Difference=R.RotateVector(FVector(0,-Body.WidthMeters,0)).Z;
        if(Lift<0. && Impulses>0 && Difference>.1 && R.GetUpVector().Z>0.)Lift=Seconds;
        const auto& Load=Runtime->GetLastSurfacePressure();
        if(Scoop<0. && R.GetUpVector().Z>0. && Load.WetUpperFaces>0 && Load.MinimumFaceOffsetM<0. &&
            FVector::DotProduct(Load.Load.TorqueNm,K.AngularVelocityRadiansPerSecond)>0.)Scoop=Seconds;
        if(Flip<0. && RaftSimCapsizePolicy::PhysicallyInverted(R,100.)){Flip=Seconds;Runtime->SetFlexibleCapsized(true);}
        if(K.WorldTransform.ContainsNaN() || K.AngularVelocityRadiansPerSecond.ContainsNaN()){AddError(TEXT("Non-finite captured-mesh pin"));break;}
    }
    TestTrue(TEXT("actual captured rock has real full-hull contact impulses"),Impulses>0);
    TestTrue(TEXT("native captured contact exercised exhaustive full-hull parity"),ReferenceChecked);
    TestTrue(TEXT("captured source lift precedes dipped upper-face scoop and physical flip"),Lift>=0. && Scoop>Lift && Flip>Scoop);
    AddInfo(FString::Printf(TEXT("PRODUCTION_CAPTURED_ROCK_PIN lift=%.9f scoop=%.9f flip=%.9f impulses=%d"),Lift,Scoop,Flip,Impulses));
    return !HasAnyErrors();
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimHullPrepareCacheTest,
    "RaftSim.Demo.RockPinExactShapeCache",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimHullPrepareCacheTest::RunTest(const FString&)
{
    // Cache invalidation fixture, not a replacement hull for a boat run.
    TArray<RaftSimRaftMesh::FMeshData> Rest;Rest.SetNum(1);auto& S=Rest[0];
    S.Vertices={FVector(0,0,0),FVector(100,0,0),FVector(0,100,0)};S.Triangles={0,1,2};
    S.Normals.Init(FVector::UpVector,3);S.UVs.Init(FVector2D::ZeroVector,3);S.Tangents.Init(FProcMeshTangent(1,0,0),3);
    TArray<FRaftSimFlexVisualSegmentState> Input;Input.AddDefaulted();Input[0].SegmentId=TEXT("fixture");
    RaftSimRaftMesh::FRaftSimRaftVisualCondition C;FTransform T=FTransform::Identity;
    FRaftSimHullGeometry H;TestTrue(TEXT("fixture export valid"),RaftSimRaftMesh::ExportHullGeometry(Rest,T,H));
    RaftSimHullPrepareCache::FCache Cache;Cache.Remember(Rest,.32f,Input,C,T,Rest,H);
    TestTrue(TEXT("exact unchanged inputs reuse full snapshot"),Cache.Matches(Rest,.32f,Input,C,T));
    for(int32 Case=0;Case<10;++Case)
    {
        auto Source=Rest;auto D=Input;auto Condition=C;auto Transform=T;float Radius=.32f;
        switch(Case)
        {
        case 0:Source[0].Vertices[0].X+=1.e-9;break;
        case 1:Swap(Source[0].Triangles[0],Source[0].Triangles[1]);break;
        case 2:Source[0].Normals[0].X+=1.e-9;break;
        case 3:Source[0].UVs[0].X+=1.e-9;break;
        case 4:Source[0].Tangents[0].bFlipTangentY=true;break;
        case 5:D[0].FreeboardLossM+=1.e-9;break;
        case 6:D[0].bRecovering=true;break;
        case 7:Condition.PressureFraction=.99f;break;
        case 8:Transform.SetTranslation(FVector(1.e-9,0,0));break;
        case 9:Radius=.33f;break;
        }
        TestFalse(FString::Printf(TEXT("same-count changed input invalidates exact cache %d"),Case),Cache.Matches(Source,Radius,D,Condition,Transform));
    }
    TestTrue(TEXT("cached export preserves every original vertex and indexed face"),Cache.Hull.VerticesM==H.VerticesM && Cache.Hull.Faces==H.Faces);
    auto SignedZero=Rest;SignedZero[0].Vertices[0].X=-0.0;SignedZero[0].UVs[0].X=-0.0;
    TestTrue(TEXT("byte-different signed zeros retain original exact value equality"),Cache.Matches(SignedZero,.32f,Input,C,T));
    auto ChangedTangent=Rest;ChangedTangent[0].Tangents[0].TangentX.Z=1.e-9;
    TestFalse(TEXT("same-count tangent direction edit invalidates bulk key"),Cache.Matches(ChangedTangent,.32f,Input,C,T));
    auto DifferentCount=Rest;DifferentCount[0].UVs.Add(FVector2D::ZeroVector);
    TestFalse(TEXT("attribute count changes invalidate bulk key"),Cache.Matches(DifferentCount,.32f,Input,C,T));
    auto Nonfinite=Rest;Nonfinite[0].Normals[0].X=std::numeric_limits<double>::quiet_NaN();
    Cache.Remember(Nonfinite,.32f,Input,C,T,Rest,H);
    TestFalse(TEXT("identical NaN bytes cannot turn unequal normal values into a cache hit"),Cache.Matches(Nonfinite,.32f,Input,C,T));
    Nonfinite=Rest;Nonfinite[0].UVs[0].X=std::numeric_limits<double>::quiet_NaN();
    Cache.Remember(Nonfinite,.32f,Input,C,T,Rest,H);
    TestFalse(TEXT("identical NaN UV bytes preserve original cache refusal"),Cache.Matches(Nonfinite,.32f,Input,C,T));
    Nonfinite=Rest;Nonfinite[0].Tangents[0].TangentX.Z=std::numeric_limits<double>::quiet_NaN();
    Cache.Remember(Nonfinite,.32f,Input,C,T,Rest,H);
    TestFalse(TEXT("identical NaN tangent bytes preserve original cache refusal"),Cache.Matches(Nonfinite,.32f,Input,C,T));
    Nonfinite=Rest;Nonfinite[0].Normals[0].X=std::numeric_limits<double>::infinity();
    Cache.Remember(Nonfinite,.32f,Input,C,T,Rest,H);
    TestTrue(TEXT("nonfinite rest attributes retain legacy equality instead of a new validity rule"),Cache.Matches(Nonfinite,.32f,Input,C,T));

    // Actual production data, not the small cache-invalidation fixture above.
    // All destination arrays remain independent, including after publication
    // buffer swaps and same-count edits. Compare EVERY attribute and range.
    TArray<RaftSimRaftMesh::FMeshData> Original;
    const auto* Asset=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/RaftSim/Rafts/Production/SM_RaftSim_ProductionPaddleRaft.SM_RaftSim_ProductionPaddleRaft"));
    if(!TestTrue(TEXT("copy controls load the original production asset"),RaftSimRaftMesh::ExtractProductionRaftRestMesh(Asset,Original)))return false;
    FRaftSimHullGeometry OriginalHull;
    if(!TestTrue(TEXT("copy controls export the actual full indexed hull"),RaftSimRaftMesh::ExportHullGeometry(Original,FTransform::Identity,OriginalHull)))return false;
    TestEqual(TEXT("copy controls retain all production vertices"),OriginalHull.VerticesM.Num(),26610);
    TestEqual(TEXT("copy controls retain all production faces"),OriginalHull.Faces.Num(),38344);
    TestEqual(TEXT("copy controls retain all five material sections"),Original.Num(),5);
    // Use the original asset's actual indexed hull for query/order costs; the
    // numerical enclosure fixture is not a substitute for this native pilot.
    FRaftSimEndpointFaceTree OrderingTree;TArray<int32> OrderingScratch;
    TArray<FVector> OrderingEnd=OriginalHull.VerticesM;
    for(int32 I=0;I<OrderingEnd.Num();++I)OrderingEnd[I]+=FVector(.02*FMath::Sin(I*.1),.03*FMath::Cos(I*.07),.01);
    if(!TestTrue(TEXT("actual full production endpoint tree refits for ordering control"),
        OrderingTree.Refit(OriginalHull.VerticesM,OrderingEnd,OriginalHull.Faces,.00001,true)))return false;
    FRandomStream OrderingRandom(20261005);
    for(int32 SizeClass=0;SizeClass<4;++SizeClass)
    {
        double ReferenceSeconds=0.,RadixSeconds=0.;int64 CandidateSum=0;int32 Comparisons=0;
        TArray<TArray<int32>> Inputs;
        for(int32 Query=0;Query<64;++Query)
        {
            const FVector Center=OriginalHull.VerticesM[OrderingRandom.RandRange(0,OriginalHull.VerticesM.Num()-1)];
            const double Extent=SizeClass==0?.015:SizeClass==1?.15:SizeClass==2?.75:10.;
            TArray<int32> Unordered;OrderingTree.GatherCandidates(FBox(Center-FVector(Extent),Center+FVector(Extent)),Unordered);
            Inputs.Add(MoveTemp(Unordered));
        }
        for(int32 Pair=0;Pair<256;++Pair)
        {
            const auto& InputIds=Inputs[Pair%Inputs.Num()];CandidateSum+=InputIds.Num();
            auto ReferenceIds=InputIds,RadixIds=InputIds;
            const auto Run=[&](bool Reference)
            {
                const double Begin=FPlatformTime::Seconds();
                if(Reference)ReferenceIds.Sort();else RaftSimFaceOrdering::Radix(RadixIds,OrderingScratch);
                const double Elapsed=FPlatformTime::Seconds()-Begin;
                if(Reference)ReferenceSeconds+=Elapsed;else RadixSeconds+=Elapsed;
            };
            Run(Pair%2!=0);Run(Pair%2==0);
            TestTrue(TEXT("actual original-hull query face IDs and tie order match without tolerance"),ReferenceIds==RadixIds);
            ++Comparisons;
        }
        AddInfo(FString::Printf(TEXT("PRODUCTION_FACE_ORDER_PAIRS class=%d pairs=%d alternating_order=1 vertices=%d faces=%d mean_candidates=%.3f reference_mean_ms=%.9f radix_mean_ms=%.9f exact=1 fps_acceptance=0"),
            SizeClass,Comparisons,OriginalHull.VerticesM.Num(),OriginalHull.Faces.Num(),double(CandidateSum)/Comparisons,
            1000.*ReferenceSeconds/Comparisons,1000.*RadixSeconds/Comparisons));
    }
    if(!TestTrue(TEXT("production first section has every attribute"),!Original.IsEmpty() &&
        !Original[0].Vertices.IsEmpty() && !Original[0].Triangles.IsEmpty() && !Original[0].Normals.IsEmpty() &&
        !Original[0].UVs.IsEmpty() && !Original[0].Tangents.IsEmpty()))return false;
    using FImmutableRest=RaftSimRaftMesh::FImmutableProductionRestMesh;
    static_assert(!std::is_copy_assignable_v<FImmutableRest> && !std::is_move_assignable_v<FImmutableRest>);
    static_assert(std::is_same_v<decltype(std::declval<const FImmutableRest&>().GetSections()),
        const TArray<RaftSimRaftMesh::FMeshData>&>);
    auto Import=Original;
    const RaftSimHullPrepareCache::FRestOwner Owner=MakeShared<const FImmutableRest>(Import);
    RaftSimHullPrepareCache::FCache Sealed;Sealed.Remember(Owner,.32f,Input,C,T,Original,OriginalHull);
    bool DeepOwned=true;
    for(int32 I=0;I<Import.Num();++I)
    {
        const auto& A=Import[I];const auto& B=Owner->GetSections()[I];
        DeepOwned &= RaftSimHullPrepareCache::SameBytes(A.Vertices,B.Vertices) &&
            RaftSimHullPrepareCache::SameBytes(A.Triangles,B.Triangles) &&
            RaftSimHullPrepareCache::SameBytes(A.Normals,B.Normals) &&
            RaftSimHullPrepareCache::SameBytes(A.UVs,B.UVs) &&
            RaftSimHullPrepareCache::SameBytes(A.Tangents,B.Tangents) &&
            A.Vertices.GetData()!=B.Vertices.GetData() && A.Triangles.GetData()!=B.Triangles.GetData() &&
            A.Normals.GetData()!=B.Normals.GetData() && A.UVs.GetData()!=B.UVs.GetData() &&
            A.Tangents.GetData()!=B.Tangents.GetData();
    }
    TestTrue(TEXT("sealed original rest owns all five attributes without importer aliases"),DeepOwned);
    Import[0].Vertices[0].X+=1.;Import[0].Triangles[0]=Import[0].Triangles[1];
    Import[0].Normals[0].X+=1.;Import[0].UVs[0].X+=1.;Import[0].Tangents[0].bFlipTangentY=!Import[0].Tangents[0].bFlipTangentY;
    Import.Reset();
    TestTrue(TEXT("mutating and freeing the importer cannot alter sealed production geometry"),
        Sealed.HasSealedRestKey(Owner) && Sealed.Matches(Owner,.32f,Input,C,T) && Sealed.Matches(Owner,.32f,Input,C,T,true));
    for(int32 Case=0;Case<24;++Case)
    {
        auto Source=Original;auto D=Input;auto Condition=C;auto Transform=T;float Radius=.32f;
        switch(Case)
        {
        case 0:Source[0].Vertices[0].X+=1.e-9;break;
        case 1:Swap(Source[0].Triangles[0],Source[0].Triangles[1]);break;
        case 2:Source[0].Normals[0].X+=1.e-9;break;
        case 3:Source[0].UVs[0].X+=1.e-9;break;
        case 4:Source[0].Tangents[0].TangentX.Z+=1.e-9;break;
        case 5:Source[0].Tangents[0].bFlipTangentY=!Source[0].Tangents[0].bFlipTangentY;break;
        case 6:Source[0].UVs.Add(FVector2D::ZeroVector);break;
        case 7:Source.AddDefaulted();break;
        case 8:D[0].SegmentId=TEXT("changed");break;
        case 9:D[0].LocalPositionM.X+=1.e-9;break;
        case 10:D[0].ContactNormalLocal.Y+=1.e-9;break;
        case 11:D[0].CompressionM+=1.e-9;break;
        case 12:D[0].FreeboardLossM+=1.e-9;break;
        case 13:D[0].IndentationM+=1.e-9;break;
        case 14:D[0].bWrapping=!D[0].bWrapping;break;
        case 15:D[0].bPinned=!D[0].bPinned;break;
        case 16:D[0].bRecovering=!D[0].bRecovering;break;
        case 17:D.AddDefaulted();break;
        case 18:Condition.PressureFraction=.99f;break;
        case 19:Condition.Integrity=.99f;break;
        case 20:Condition.CreaseAmplitudeM+=1.e-9f;break;
        case 21:Transform.SetTranslation(FVector(1.e-9,0,0));break;
        case 22:Transform.SetRotation(FQuat(FVector::UpVector,.01));break;
        case 23:Radius=.33f;break;
        }
        const RaftSimHullPrepareCache::FRestOwner ChangedOwner=Case<8 ? MakeShared<const FImmutableRest>(Source) : Owner;
        TestFalse(FString::Printf(TEXT("sealed input still rejects every source and dynamics change %d"),Case),Sealed.Matches(ChangedOwner,Radius,D,Condition,Transform));
        TestEqual(FString::Printf(TEXT("sealed and original key decisions agree %d"),Case),
            Sealed.Matches(ChangedOwner,Radius,D,Condition,Transform),Sealed.Matches(ChangedOwner,Radius,D,Condition,Transform,true));
    }
    auto Scaled=T;Scaled.SetScale3D(FVector(1.01,1,1));
    TestFalse(TEXT("sealed key still validates component scale"),Sealed.Matches(Owner,.32f,Input,C,Scaled));
    for(int32 Case=0;Case<5;++Case)
    {
        auto Invalid=Original;
        switch(Case)
        {
        case 0:Invalid[0].Vertices[0].X=std::numeric_limits<double>::quiet_NaN();break;
        case 1:Invalid[0].Normals[0].X=std::numeric_limits<double>::quiet_NaN();break;
        case 2:Invalid[0].UVs[0].X=std::numeric_limits<double>::quiet_NaN();break;
        case 3:Invalid[0].Tangents[0].TangentX.X=std::numeric_limits<double>::quiet_NaN();break;
        case 4:Invalid[0].Normals[0].X=std::numeric_limits<double>::infinity();break;
        }
        const RaftSimHullPrepareCache::FRestOwner InvalidOwner=MakeShared<const FImmutableRest>(Invalid);
        RaftSimHullPrepareCache::FCache InvalidCache;InvalidCache.Remember(InvalidOwner,.32f,Input,C,T,Original,OriginalHull);
        TestFalse(TEXT("nonfinite rest never takes sealed finite shortcut"),InvalidCache.HasSealedRestKey(InvalidOwner));
        TestEqual(TEXT("nonfinite sealed keys preserve legacy refusal and infinity equality"),
            InvalidCache.Matches(InvalidOwner,.32f,Input,C,T),Case==4);
        TestEqual(TEXT("nonfinite reference and sealed decisions identical"),InvalidCache.Matches(InvalidOwner,.32f,Input,C,T),
            InvalidCache.Matches(InvalidOwner,.32f,Input,C,T,true));
    }
    const RaftSimHullPrepareCache::FRestOwner Replacement=MakeShared<const FImmutableRest>(Original);
    TestFalse(TEXT("distinct import cannot inherit old owner identity proof"),Sealed.HasSealedRestKey(Replacement));
    TestTrue(TEXT("equal replacement retains original exact-key semantics"),Sealed.Matches(Replacement,.32f,Input,C,T));
    auto ZeroRest=Original;ZeroRest[0].UVs[0].X=0.;
    const RaftSimHullPrepareCache::FRestOwner ZeroOwner=MakeShared<const FImmutableRest>(ZeroRest);
    RaftSimHullPrepareCache::FCache ZeroCache;ZeroCache.Remember(ZeroOwner,.32f,Input,C,T,Original,OriginalHull);
    ZeroRest[0].UVs[0].X=-0.;
    const RaftSimHullPrepareCache::FRestOwner NegativeOwner=MakeShared<const FImmutableRest>(ZeroRest);
    TestTrue(TEXT("replacement signed zero still uses original value equality"),ZeroCache.Matches(NegativeOwner,.32f,Input,C,T));
    Sealed.Remember(Original,.32f,Input,C,T,Original,OriginalHull);
    TestFalse(TEXT("mutable Remember clears the sealed identity proof"),Sealed.HasSealedRestKey(Owner));
    Sealed.Remember(Owner,.32f,Input,C,T,Original,OriginalHull);
    double ReferenceKeySeconds=0.,SealedKeySeconds=0.;int32 KeyHits=0;
    for(int32 Pair=0;Pair<512;++Pair)
    {
        const auto RunKey=[&](bool Reference)
        {
            const double Begin=FPlatformTime::Seconds();
            const bool Hit=Sealed.Matches(Owner,.32f,Input,C,T,Reference);
            const double Elapsed=FPlatformTime::Seconds()-Begin;
            if(Reference)ReferenceKeySeconds+=Elapsed;else SealedKeySeconds+=Elapsed;
            KeyHits+=int32(Hit);
        };
        RunKey(Pair%2!=0);RunKey(Pair%2==0);
    }
    TestEqual(TEXT("all same-input production sealed/reference pairs agree"),KeyHits,1024);
    TestTrue(TEXT("sealed reuse retains original full hull and all prepared sections"),
        Sealed.Hull.VerticesM==OriginalHull.VerticesM && Sealed.Hull.Faces==OriginalHull.Faces && Sealed.Prepared.Num()==5);
    AddInfo(FString::Printf(TEXT("PRODUCTION_REST_KEY_PAIRS pairs=512 alternating_order=1 vertices=%d faces=%d sections=%d reference_mean_ms=%.9f sealed_mean_ms=%.9f exact=1 fps_acceptance=0"),
        OriginalHull.VerticesM.Num(),OriginalHull.Faces.Num(),Original.Num(),1000.*ReferenceKeySeconds/512.,1000.*SealedKeySeconds/512.));
    TArray<RaftSimRaftMesh::FMeshData> Destination;FRaftSimHullGeometry DestinationHull;
    const auto Equal=[&]()
    {
        using namespace RaftSimHullPrepareCache;
        if(Destination.Num()!=Original.Num() || !SameBytes(OriginalHull.VerticesM,DestinationHull.VerticesM) ||
            !SameBytes(OriginalHull.Faces,DestinationHull.Faces) || !SameBytes(OriginalHull.Sections,DestinationHull.Sections))return false;
        for(int32 I=0;I<Original.Num();++I)
        {
            const auto& A=Original[I];const auto& B=Destination[I];
            if(!SameBytes(A.Vertices,B.Vertices) || !SameBytes(A.Triangles,B.Triangles) ||
                !SameBytes(A.Normals,B.Normals) || !SameBytes(A.UVs,B.UVs) || !SameBytes(A.Tangents,B.Tangents))return false;
            if((!A.Vertices.IsEmpty() && A.Vertices.GetData()==B.Vertices.GetData()) ||
                (!A.Triangles.IsEmpty() && A.Triangles.GetData()==B.Triangles.GetData()) ||
                (!A.Normals.IsEmpty() && A.Normals.GetData()==B.Normals.GetData()) ||
                (!A.UVs.IsEmpty() && A.UVs.GetData()==B.UVs.GetData()) ||
                (!A.Tangents.IsEmpty() && A.Tangents.GetData()==B.Tangents.GetData()))return false;
        }
        return OriginalHull.VerticesM.GetData()!=DestinationHull.VerticesM.GetData() &&
            OriginalHull.Faces.GetData()!=DestinationHull.Faces.GetData() &&
            OriginalHull.Sections.GetData()!=DestinationHull.Sections.GetData();
    };
    const auto Restore=[&]()
    {
        RaftSimHullPrepareCache::FCopyCounts Counts;
        RaftSimHullPrepareCache::CopyPreparedIfChanged(Original,Destination,Counts);
        RaftSimHullPrepareCache::CopyHullIfChanged(OriginalHull,DestinationHull,Counts);
        return Counts;
    };
    auto Copies=Restore();
    TestTrue(TEXT("first full snapshot is deeply assigned with no shared mutable arrays"),Copies.Assigned>0 && Equal());
    const auto* HeldVertices=DestinationHull.VerticesM.GetData();const auto* HeldPrepared=Destination[0].Vertices.GetData();
    Copies=Restore();
    TestEqual(TEXT("byte-identical owned production buffers need no assignment"),Copies.Assigned,0);
    TestEqual(TEXT("every original hull and render attribute is compared"),Copies.Retained,5*Original.Num()+3);
    TestTrue(TEXT("identical copy elision preserves both buffer allocations"),HeldVertices==DestinationHull.VerticesM.GetData() && HeldPrepared==Destination[0].Vertices.GetData() && Equal());
    for(int32 Case=0;Case<10;++Case)
    {
        switch(Case)
        {
        case 0:Destination[0].Vertices[0].X+=1.e-9;break;
        case 1:Swap(Destination[0].Triangles[0],Destination[0].Triangles[1]);break;
        case 2:Destination[0].Normals[0].X+=1.e-9;break;
        case 3:Destination[0].UVs[0].X+=1.e-9;break;
        case 4:Destination[0].Tangents[0].bFlipTangentY=!Destination[0].Tangents[0].bFlipTangentY;break;
        case 5:DestinationHull.VerticesM[0].X+=1.e-9;break;
        case 6:Swap(DestinationHull.Faces[0].X,DestinationHull.Faces[0].Y);break;
        case 7:--DestinationHull.Sections[0].VertexCount;break;
        case 8:Destination[0].UVs.Add(FVector2D::ZeroVector);break;
        case 9:DestinationHull.VerticesM[0].X=std::numeric_limits<double>::quiet_NaN();break;
        }
        Copies=Restore();
        TestEqual(FString::Printf(TEXT("only the changed original array is assigned %d"),Case),Copies.Assigned,1);
        TestTrue(FString::Printf(TEXT("all original attributes and independent ownership restored %d"),Case),Equal() && DestinationHull.IsValid());
    }
    TArray<RaftSimRaftMesh::FMeshData> Published=Destination;
    Swap(Published,Destination);Copies=Restore();
    TestTrue(TEXT("publication buffer swap cannot invalidate byte-identity proof"),Copies.Assigned==0 && Equal());
    Destination.SetNum(Original.Num()+1);Copies=Restore();
    TestTrue(TEXT("extra material section is removed, never silently retained"),Equal());
    Destination.Reset();Copies=Restore();
    TestTrue(TEXT("empty destination regains all original sections"),Copies.Assigned>0 && Equal());
    // Same original production arrays in both execution orders. This narrow
    // operation timing is not whole-frame or packaged-game FPS acceptance.
    auto ReferencePrepared=Original;auto ReferenceHull=OriginalHull;
    double ReferenceSeconds=0.,CandidateSeconds=0.;int32 RetainedArrays=0;
    for(int32 Pair=0;Pair<64;++Pair)
    {
        const auto Run=[&](bool Candidate)
        {
            const double Begin=FPlatformTime::Seconds();
            if(Candidate)
            {
                const auto Counts=Restore();RetainedArrays+=Counts.Retained;
                CandidateSeconds+=FPlatformTime::Seconds()-Begin;
            }
            else
            {
                ReferencePrepared=Original;ReferenceHull=OriginalHull;
                ReferenceSeconds+=FPlatformTime::Seconds()-Begin;
            }
        };
        Run(Pair%2!=0);Run(Pair%2==0);
        TestTrue(FString::Printf(TEXT("same-input copy pair preserves every actual attribute %d"),Pair),Equal());
        bool ReferenceExact=ReferencePrepared.Num()==Original.Num() &&
            RaftSimHullPrepareCache::SameBytes(ReferenceHull.VerticesM,OriginalHull.VerticesM) &&
            RaftSimHullPrepareCache::SameBytes(ReferenceHull.Faces,OriginalHull.Faces) &&
            RaftSimHullPrepareCache::SameBytes(ReferenceHull.Sections,OriginalHull.Sections);
        for(int32 I=0;ReferenceExact && I<Original.Num();++I)
        {
            const auto& A=Original[I];const auto& B=ReferencePrepared[I];
            ReferenceExact=RaftSimHullPrepareCache::SameBytes(A.Vertices,B.Vertices) &&
                RaftSimHullPrepareCache::SameBytes(A.Triangles,B.Triangles) &&
                RaftSimHullPrepareCache::SameBytes(A.Normals,B.Normals) &&
                RaftSimHullPrepareCache::SameBytes(A.UVs,B.UVs) &&
                RaftSimHullPrepareCache::SameBytes(A.Tangents,B.Tangents);
        }
        TestTrue(FString::Printf(TEXT("reference copy pair preserves every actual attribute %d"),Pair),ReferenceExact);
    }
    TestEqual(TEXT("all same-input production pairs retain every exact array"),RetainedArrays,64*(5*Original.Num()+3));
    AddInfo(FString::Printf(TEXT("PRODUCTION_SNAPSHOT_COPY_PAIRS pairs=64 alternating_order=1 vertices=%d faces=%d sections=%d reference_mean_ms=%.9f candidate_mean_ms=%.9f retained_arrays=%d exact=1 fps_acceptance=0"),
        OriginalHull.VerticesM.Num(),OriginalHull.Faces.Num(),Original.Num(),1000.*ReferenceSeconds/64.,1000.*CandidateSeconds/64.,RetainedArrays));
    TArray<FVector> PositiveZero={FVector(0.,0.,0.)},NegativeZero={FVector(-0.,0.,0.)};
    RaftSimHullPrepareCache::FCopyCounts ZeroCopies;
    RaftSimHullPrepareCache::CopyArrayIfChanged(PositiveZero,NegativeZero,ZeroCopies);
    TestTrue(TEXT("signed-zero byte difference takes original assignment"),ZeroCopies.Assigned==1 && RaftSimHullPrepareCache::SameBytes(PositiveZero,NegativeZero));
    RaftSimHullPrepareCache::FCopyCounts ClearCopies;
    const TArray<RaftSimRaftMesh::FMeshData> EmptyPrepared;const FRaftSimHullGeometry EmptyHull;
    RaftSimHullPrepareCache::CopyPreparedIfChanged(EmptyPrepared,Destination,ClearCopies);
    RaftSimHullPrepareCache::CopyHullIfChanged(EmptyHull,DestinationHull,ClearCopies);
    TestTrue(TEXT("empty source clears every old section and hull array, preserving validity refusal"),Destination.IsEmpty() &&
        DestinationHull.VerticesM.IsEmpty() && DestinationHull.Faces.IsEmpty() && DestinationHull.Sections.IsEmpty() && !DestinationHull.IsValid());
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRockPinContactReplay,
    "RaftSim.Demo.RockPinContactReplay",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::ClientContext|EAutomationTestFlags::ProductFilter)
bool FRaftSimRockPinContactReplay::RunTest(const FString& SecondaryPath)
{
    FString Path=SecondaryPath;
    if(Path.IsEmpty() && !FParse::Value(FCommandLine::Get(),TEXT("RaftSimRockPinReplay="),Path))
    {AddInfo(TEXT("No recorded full-hull pinning failure selected; replay not exercised"));return true;}
    FString Json;TSharedPtr<FJsonObject> J;
    if(!TestTrue(TEXT("actual native snapshot reads"),FFileHelper::LoadFileToString(Json,*Path) &&
        FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json),J) && J.IsValid()))return false;
    if(!TestEqual(TEXT("native failure snapshot schema"),J->GetStringField(TEXT("schema")),FString(TEXT("raftsim.full_hull_native_failure.v1"))))return false;
    const auto Vec=[](const TArray<TSharedPtr<FJsonValue>>& V){return FVector(V[0]->AsNumber(),V[1]->AsNumber(),V[2]->AsNumber());};
    const auto Body=[&](const TSharedPtr<FJsonObject>& B)
    {FRaftSimFlexRigidState S;S.Position=Vec(B->GetArrayField(TEXT("position")));S.LinearVelocity=Vec(B->GetArrayField(TEXT("velocity")));
     S.AngularVelocity=Vec(B->GetArrayField(TEXT("omega")));const auto& Q=B->GetArrayField(TEXT("quaternion"));
     S.Orientation=FQuat(Q[0]->AsNumber(),Q[1]->AsNumber(),Q[2]->AsNumber(),Q[3]->AsNumber());return S;};
    FRaftSimHullGeometry Before,After;
    for(const auto& V:J->GetArrayField(TEXT("before_vertices")))Before.VerticesM.Add(Vec(V->AsArray()));
    for(const auto& V:J->GetArrayField(TEXT("after_vertices")))After.VerticesM.Add(Vec(V->AsArray()));
    for(const auto& F:J->GetArrayField(TEXT("faces"))){const auto V=Vec(F->AsArray());Before.Faces.Add(FIntVector(V.X,V.Y,V.Z));}
    After.Faces=Before.Faces;Before.Sections={{0,Before.VerticesM.Num(),0,Before.Faces.Num()}};After.Sections=Before.Sections;
    if(!TestTrue(TEXT("replay retains actual full production hull, not a proxy"),Before.VerticesM.Num()==26610 && Before.Faces.Num()==38344 && Before.IsValid() && After.IsValid()))return false;
    const auto Previous=Body(J->GetObjectField(TEXT("previous")));auto State=Body(J->GetObjectField(TEXT("predicted")));
    FRaftSimHullGroundArcQuery ArcQuery;
    if(FParse::Param(FCommandLine::Get(),TEXT("RaftSimRockPinArcCandidate")))
        ArcQuery=[](auto A,auto B,auto F,double Skin,double Clearance,const FRaftSimHullArcPath& Arc)
        {return RaftSimFlipObstacle::Sweep(A,B,F,Skin,Clearance,false,true,&Arc);};
    const auto R=RaftSimHullContact::Integrate(State,Previous,Before,After,J->GetNumberField(TEXT("mass_kg")),
        Vec(J->GetArrayField(TEXT("inertia"))),J->GetNumberField(TEXT("dt")),
        [](auto A,auto B,auto F,double Skin,double Clearance){return RaftSimFlipObstacle::Sweep(A,B,F,Skin,Clearance,false,true);},ArcQuery);
    AddInfo(FString::Printf(TEXT("ROCK_PIN_REPLAY completed=%d failure=%s consumed=%.17g queries=%d impulses=%d shape_work=%.17g dissipated=%.17g kinetic_change=%.17g"),
        int32(R.bCompleted),*R.Failure,R.ConsumedSeconds,R.Queries,R.Impulses,R.PrescribedShapeWorkJ,R.DissipatedJ,R.KineticChangeJ));
    if(FParse::Param(FCommandLine::Get(),TEXT("RaftSimRockPinRequireComplete")))
    {
        TestTrue(TEXT("recorded contact substep completes under unchanged limits"),R.bCompleted);
        TestTrue(TEXT("whole native substep is consumed"),FMath::Abs(R.ConsumedSeconds-J->GetNumberField(TEXT("dt")))<1.e-12);
        if(ArcQuery)
        {
            auto Reference=Body(J->GetObjectField(TEXT("predicted")));
            const FRaftSimHullGroundArcQuery Exhaustive=[](auto A,auto B,auto F,double Skin,double Clearance,const FRaftSimHullArcPath& Arc)
                {return RaftSimFlipObstacle::Sweep(A,B,F,Skin,Clearance,false,true,&Arc,false);};
            const auto Slow=RaftSimHullContact::Integrate(Reference,Previous,Before,After,J->GetNumberField(TEXT("mass_kg")),
                Vec(J->GetArrayField(TEXT("inertia"))),J->GetNumberField(TEXT("dt")),
                [](auto A,auto B,auto F,double Skin,double Clearance){return RaftSimFlipObstacle::Sweep(A,B,F,Skin,Clearance,false,true);},Exhaustive,false);
            TestTrue(TEXT("exhaustive original triangles without clear-flight shortcut also complete"),Slow.bCompleted);
            TestTrue(TEXT("accelerated original hull agrees with exhaustive contact pose"),
                State.Position.Equals(Reference.Position,1.e-9) && State.Orientation.Equals(Reference.Orientation,1.e-9));
            TestTrue(TEXT("accelerated original hull agrees with exhaustive velocities"),
                State.LinearVelocity.Equals(Reference.LinearVelocity,1.e-9) && State.AngularVelocity.Equals(Reference.AngularVelocity,1.e-9));
            TestEqual(TEXT("actual contact impulses unchanged by acceleration"),R.Impulses,Slow.Impulses);
            TestTrue(TEXT("dissipated work unchanged by acceleration"),FMath::Abs(R.DissipatedJ-Slow.DissipatedJ)<1.e-9);
        }
    }
    else TestTrue(TEXT("recorded baseline contact refusal reproduces"),!R.bCompleted && R.Failure==J->GetStringField(TEXT("failure")));
    FString Other;
    if(!HasAnyErrors() && SecondaryPath.IsEmpty() && FParse::Value(FCommandLine::Get(),TEXT("RaftSimRockPinReplay2="),Other))
        return RunTest(Other);
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRockPillowLoads,
    "RaftSim.Demo.RockPillowLoads",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::ClientContext|EAutomationTestFlags::ProductFilter)
bool FRaftSimRockPillowLoads::RunTest(const FString&)
{
    const auto Scenes=RaftSimFlipTestEnvironment::Scenes();
    const auto& Pillow=*Scenes.FindByPredicate([](const auto& S){return S.Name==TEXT("rock_pillow_broadside");});
    TestTrue(TEXT("rock control starts without imposed roll or spin"),Pillow.InitialRollDegrees==0. && Pillow.InitialRollRateRadS==0.);
    TArray<FVector> V;TArray<FIntVector> Faces;RaftSimFlipObstacle::Geometry(V,Faces,false,true);
    TestTrue(TEXT("bed-connected wedge has the same twelve rendered/contact triangles"),V.Num()==8 && Faces.Num()==12);
    const FVector Normal=RaftSimFlipObstacle::TopNormal(true);
    for(int32 I=4;I<8;++I)TestEqual(TEXT("top mesh vertices match ground height sampler"),V[I].Z,RaftSimFlipObstacle::TopCm(V[I].X,false,true));
    TestTrue(TEXT("sloped rock supports upstream and upward, not a vertical wall"),Normal.X<0. && Normal.Z>0.);
    TestTrue(TEXT("top collision/render plane has the sampled normal"),FMath::Abs(FVector::DotProduct(V[5]-V[4],Normal))<1.e-9);
    for(double X=-3.;X<-.6;X+=.2)
    {
        FVector P(X*100.,0,0);P.Z=Pillow.Surface(P,0.)*100.;
        const FVector Flow=Pillow.Velocity(P,0.);
        const double Hx=(Pillow.Surface(P+FVector(.1,0,0),0.)-Pillow.Surface(P-FVector(.1,0,0),0.))/.002;
        TestTrue(TEXT("pillow flow is finite and tangent to visible stationary surface"),!Flow.ContainsNaN() && FMath::Abs(Flow.Z-Flow.X*Hx)<1.e-7);
        TestTrue(TEXT("pillow bed has no vertical flux"),FMath::Abs(Pillow.Velocity(FVector(X*100.,0,-200.),0.).Z)<1.e-9);
    }
    TestTrue(TEXT("no water velocity inside solid footprint"),Pillow.Velocity(FVector::ZeroVector,0.).IsZero());
    TArray<FVector> PinV;TArray<FIntVector> PinF;RaftSimFlipObstacle::Geometry(PinV,PinF,true,true);
    for(int32 I=4;I<8;++I)TestEqual(TEXT("pinned pillow control has the same tall rendered/contact top"),PinV[I].Z,150.);
    TestTrue(TEXT("pinned ground sampler uses the flat tall top, not the low ramp normal"),RaftSimFlipObstacle::TopNormal(true,true)==FVector::UpVector);
    FRaftSimFlexSegmentOverwash Wet;Wet.bWet=true;Wet.bUpstreamExposed=true;
    Wet.OvertoppingDepthM=.35;Wet.LocalPosition=FVector(0,1.,0);
    FRaftSimFlexTubeSegment Tube;Tube.TributaryLengthM=1.;
    // Local +Y is upstream after yaw 90. Negative local X roll lifts the
    // downstream side and dips upstream. No integrator pose is set here.
    const FQuat Q=FQuat(FVector::UpVector,PI*.5)*FQuat(FVector::ForwardVector,-PI/6.);
    const FVector Current(4.,0,0);
    const auto Scoop=RaftSimOverwashLoads::ScoopingFace(Wet,Tube,Q,.32,Current);
    TestTrue(TEXT("dipped upstream face receives downward and downstream pressure"),Scoop.ForceN.Z<0. && Scoop.ForceN.X>0.);
    TestTrue(TEXT("scoop torque reinforces upstream dip about raft longitudinal axis"),FVector::DotProduct(Scoop.TorqueNm,Q.GetForwardVector())<0.);
    TestTrue(TEXT("scoop transfers momentum from relative water, not a roll target"),FVector::DotProduct(Scoop.ForceN,Current)>0.);
    TestTrue(TEXT("outgoing relative flow creates no suction load"),RaftSimOverwashLoads::ScoopingFace(Wet,Tube,Q,.32,-Current).ForceN.IsZero());
    TestTrue(TEXT("tangential water creates no scoop pressure"),RaftSimOverwashLoads::ScoopingFace(Wet,Tube,Q,.32,Q.GetForwardVector()*4.).ForceN.IsNearlyZero(1.e-9));
    Wet.OvertoppingDepthM=0.;
    TestTrue(TEXT("non-overtopped tube cannot scoop"),RaftSimOverwashLoads::ScoopingFace(Wet,Tube,Q,.32,Current).ForceN.IsZero());
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimFlipLoadsAndPolicy,
    "RaftSim.Demo.FlipLoadsAndPolicy",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::ClientContext|EAutomationTestFlags::ProductFilter)
bool FRaftSimFlipLoadsAndPolicy::RunTest(const FString&)
{
    FRaftSimFlexSegmentOverwash Wet;Wet.bWet=true;Wet.bUpstreamExposed=true;
    Wet.OvertoppingDepthM=.5;Wet.IncomingSpeedMps=4.;Wet.LocalPosition=FVector(0,-1,0);
    FRaftSimFlexTubeSegment Tube;Tube.OutwardNormal=FVector(0,-1,0);Tube.TributaryLengthM=1.;
    const auto Port=RaftSimOverwashLoads::UpperFace(Wet,Tube,FQuat::Identity,.32);
    TestTrue(TEXT("port load follows the incoming current"),Port.ForceN.Y>0.);
    TestTrue(TEXT("upper-face force has signed overturning roll"),Port.TorqueNm.X<0.);
    Wet.LocalPosition.Y=1.;Tube.OutwardNormal.Y=1.;
    const auto Starboard=RaftSimOverwashLoads::UpperFace(Wet,Tube,FQuat::Identity,.32);
    TestTrue(TEXT("mirrored pressure force and torque reverse"),
        (Port.ForceN+Starboard.ForceN).IsNearlyZero() && (Port.TorqueNm+Starboard.TorqueNm).IsNearlyZero());
    Wet.LocalPosition=FVector(2,0,0);Tube.OutwardNormal=FVector(1,0,0);
    const auto Bow=RaftSimOverwashLoads::UpperFace(Wet,Tube,FQuat::Identity,.32);
    TestTrue(TEXT("bow pressure creates pitch, not invented roll"),FMath::Abs(Bow.TorqueNm.X)<1.e-9 && Bow.TorqueNm.Y<0.);
    const FQuat Rotation=FRotator(15,47,23).Quaternion();
    const auto Rotated=RaftSimOverwashLoads::UpperFace(Wet,Tube,Rotation,.32);
    TestTrue(TEXT("pressure load is rotation-covariant"),
        Rotated.ForceN.Equals(Rotation.RotateVector(Bow.ForceN),1.e-8) &&
        Rotated.TorqueNm.Equals(Rotation.RotateVector(Bow.TorqueNm),1.e-8));
    Wet.bWet=false;
    TestTrue(TEXT("dry faces contribute no pressure"),RaftSimOverwashLoads::UpperFace(Wet,Tube,FQuat::Identity,.32).ForceN.IsZero());
    Wet.bWet=true;Wet.IncomingSpeedMps=0.;
    TestTrue(TEXT("co-moving water contributes no pressure"),RaftSimOverwashLoads::UpperFace(Wet,Tube,FQuat::Identity,.32).ForceN.IsZero());
    TestFalse(TEXT("upright boat is not capsized"),RaftSimCapsizePolicy::PhysicallyInverted(FQuat::Identity,100.));
    TestFalse(TEXT("Euler roll 180 at physical tilt 95 is below the 100 degree gate"),
        RaftSimCapsizePolicy::PhysicallyInverted(FRotator(85,30,180).Quaternion(),100.));
    TestTrue(TEXT("physically inverted roll enters the gate"),
        RaftSimCapsizePolicy::PhysicallyInverted(FRotator(0,0,110).Quaternion(),100.));
    TestTrue(TEXT("physical pitch-over also enters the gate"),
        RaftSimCapsizePolicy::PhysicallyInverted(FRotator(110,30,0).Quaternion(),100.));
    FRaftSimSwimmerRescueFrame Released;
    Released.SwimmerWorldPositionMeters=FVector(2,3,299.3);
    Released.SwimmerDriftVelocityMetersPerSecond=FVector(1,0,-1.5);
    const auto Early=RaftSimAdvanceSubmergedSwimmer(Released,FVector::ZeroVector,300.,.1);
    TestTrue(TEXT("submerged release retains downward momentum, not surface snap"),
        Early.SwimmerWorldPositionMeters.Z<Released.SwimmerWorldPositionMeters.Z &&
        Early.SwimmerDriftVelocityMetersPerSecond.Z<0.);
    auto Swimming=Released;
    for(int32 I=0;I<1440;++I)Swimming=RaftSimAdvanceSubmergedSwimmer(Swimming,FVector::ZeroVector,300.,1./120.);
    TestTrue(TEXT("PFD candidate rises to the local surface without sinking"),
        FMath::Abs(Swimming.SwimmerWorldPositionMeters.Z-300.)<.002 &&
        FMath::Abs(Swimming.SwimmerDriftVelocityMetersPerSecond.Z)<1.e-9);
    TestTrue(TEXT("release horizontal momentum is relaxed, not erased"),Early.SwimmerWorldPositionMeters.X>2.);
    const auto Environments=RaftSimFlipTestEnvironment::Scenes();
    using namespace RaftSimContactWitnessPrune;
    TArray<FWitness> Witnesses={
        {FVector(0,0,0),FVector(0,0,0),FVector(-1,0,0),FVector::ZeroVector,3},
        {FVector(0,1,0),FVector(0,1,.2),FVector(-1,0,0),FVector::ZeroVector,3},
        {FVector(0,0,1),FVector(0,0,1.2),FVector(-1,0,0),FVector::ZeroVector,3}};
    FWitness Interior{FVector(0,.25,.25),FVector(0,.25,.35),FVector(-1,0,0),FVector::ZeroVector,3};
    TestTrue(TEXT("convex witness endpoint representation is redundant"),Redundant(Interior,Witnesses,INDEX_NONE,1.e-13));
    Interior.After.Z+=.001;
    TestFalse(TEXT("distinct deformation velocity must not be discarded"),Redundant(Interior,Witnesses,INDEX_NONE,1.e-13));
    Interior.After.Z-=.001;Interior.Ground.X=.001;
    TestFalse(TEXT("a different contact plane must not be discarded"),Redundant(Interior,Witnesses,INDEX_NONE,1.e-13));
    RaftSimImplicitDrag::FSystem Drag;
    Drag.AddPoint(FVector(1,.8,.2),FVector::ZeroVector,9000.,-6000.,FVector::ForwardVector);
    Drag.AddPoint(FVector(-1,-.8,.2),FVector::ZeroVector,9000.,0.,FVector::ForwardVector);
    FRaftSimFlexRigidState Moving;Moving.LinearVelocity=FVector(3,-2,1);Moving.AngularVelocity=FVector(4,-3,2);
    const FVector I(59,59,132);constexpr double Mass=70.;
    const auto Energy=[&](const auto& S){return .5*(Mass*S.LinearVelocity.SizeSquared()+I.X*FMath::Square(S.AngularVelocity.X)+I.Y*FMath::Square(S.AngularVelocity.Y)+I.Z*FMath::Square(S.AngularVelocity.Z));};
    const double Before=Energy(Moving);FVector Force,Torque;
    TestTrue(TEXT("empty-hull strong drag solve remains finite"),Drag.Advance(Moving,Mass,I,FVector::ZeroVector,FVector::ZeroVector,1./120.,Force,Torque));
    TestTrue(TEXT("still-water coupled drag cannot add kinetic energy"),Energy(Moving)<Before);
    RaftSimImplicitDrag::FSystem Uniform;
    Uniform.AddPoint(FVector(1,0,0),FVector(3,0,0),9000.,0.,FVector::ForwardVector);
    FRaftSimFlexRigidState Carried;Carried.LinearVelocity=FVector(3,0,0);
    TestTrue(TEXT("uniform co-moving integration succeeds"),Uniform.Advance(Carried,Mass,I,FVector::ZeroVector,FVector::ZeroVector,1./120.,Force,Torque));
    TestTrue(TEXT("co-moving current creates neither force nor rotation"),Carried.LinearVelocity.Equals(FVector(3,0,0),1.e-9) && Carried.AngularVelocity.IsNearlyZero(1.e-9));
    const auto& Hydraulic=*Environments.FindByPredicate([](const auto& S){return S.bHydraulic;});
    for(double Y=-3.;Y<=3.;Y+=.25)
    {
        const FVector SurfacePoint(0,Y*100.,Hydraulic.Surface(FVector(0,Y*100.,0),0.)*100.);
        const FVector V=Hydraulic.Velocity(SurfacePoint,0.);
        const double Hy=(Hydraulic.Surface(SurfacePoint+FVector(0,.1,0),0.)-Hydraulic.Surface(SurfacePoint-FVector(0,.1,0),0.))/.002;
        TestTrue(TEXT("hydraulic current is tangent to its stationary free surface"),FMath::Abs(V.Z-V.Y*Hy)<1.e-7);
        TestTrue(TEXT("hydraulic bed has no vertical flux"),FMath::Abs(Hydraulic.Velocity(FVector(0,Y*100.,-200),0.).Z)<1.e-9);
    }
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimFlipEnvironmentBaseline,
    "RaftSim.Demo.FlipEnvironmentBaseline",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::ClientContext|EAutomationTestFlags::ProductFilter)
bool FRaftSimFlipEnvironmentBaseline::RunTest(const FString&)
{
    TArray<TSharedPtr<FJsonValue>> Reports;
    const bool Candidate=false; // The production adapter owns pressure loads.
    for(const auto& Scene:RaftSimFlipTestEnvironment::Scenes())
    {
        // These moving-wave force controls intentionally exclude obstacle CCD
        // and stationary hydraulic entries, which require the live actor lab.
        if(Scene.bObstacle || Scene.bHydraulic)continue;
        auto* Runtime=NewObject<URaftSimChronoRuntimeAdapter>();
        FRaftSimRaftBodyConfig Body;Body.MassKg=605.;Body.BuoyancyWeightMultiple=5.2;
        Body.InertiaTensorKgM2=FVector(514.,514.,1142.);Body.LinearDragCoefficient=9000.;
        FRaftSimFlexParameters Flex;Flex.MassKg=70.;Flex.GuideMassKg=85.;Flex.PassengerMassKg=75.;Flex.PassengerCount=6;
        Flex.LengthM=Body.LengthMeters;Flex.WidthM=Body.WidthMeters;Flex.TubeRadiusM=Body.TubeRadiusMeters;
        Runtime->ConfigureRaftBody(Body);
        Runtime->ConfigureFlexibleRaftModel(Flex,RaftSimCrewSeatLayout::BuildNormalSeats(Flex,false),18000.,true);
        double Seconds=0.;
        Runtime->SetWaterSurfaceSampler([&](const FVector& P,float& H){H=Scene.Surface(P,Seconds)*100.;return true;});
        Runtime->SetFlexibleWaterFieldSampler([&](const FVector& P,FRaftSimFlexUniformWater& W)
            {W.bWet=true;W.SurfaceHeightM=Scene.Surface(P,Seconds);W.VelocityMps=Scene.Velocity(P,Seconds);return true;});
        FRaftSimRaftKinematicState Initial;Initial.WorldTransform.SetLocation(FVector(0,0,20));
        Initial.WorldTransform.SetRotation(FQuat(FVector::ForwardVector,FMath::DegreesToRadians(Scene.InitialRollDegrees)));
        Initial.AngularVelocityRadiansPerSecond=FVector(Scene.InitialRollRateRadS,0,0);
        Runtime->SetKinematicState(Initial);
        double MinimumUp=1.,MaximumOmega=0.,RiskSeconds=0.;TArray<TSharedPtr<FJsonValue>> Motion;
        for(int32 Step=0;Step<1440;++Step)
        {
            Seconds=Step/120.;
            if(Candidate)
            {
                const auto Load=RaftSimFlipCandidateLoads::Evaluate(*Runtime,Scene,Seconds,1./120.);
                Runtime->AddExternalImpulse(Load.ForceN/120.,Load.TorqueNm/120.);
            }
            if(!TestTrue(TEXT("production integration remains valid"),Runtime->StepRaftDynamics(1.f/120.f)))break;
            const auto& State=Runtime->GetKinematicState();const auto& Telemetry=Runtime->GetLastFlexibleStepTelemetry();
            const double Up=State.WorldTransform.GetRotation().GetUpVector().Z;
            MinimumUp=FMath::Min(MinimumUp,Up);MaximumOmega=FMath::Max(MaximumOmega,State.AngularVelocityRadiansPerSecond.Size());
            if(Telemetry.bReferenceFlipRisk)RiskSeconds+=1./120.;
            if(Step%12==0)
            {
                auto Row=MakeShared<FJsonObject>();Row->SetNumberField(TEXT("seconds"),Seconds);
                Row->SetNumberField(TEXT("up_z"),Up);Row->SetNumberField(TEXT("roll_deg"),State.WorldTransform.Rotator().Roll);
                Row->SetNumberField(TEXT("pitch_deg"),State.WorldTransform.Rotator().Pitch);
                Row->SetNumberField(TEXT("omega_rad_s"),State.AngularVelocityRadiansPerSecond.Size());
                Row->SetNumberField(TEXT("flip_margin_nm"),Telemetry.ReferenceFlipMarginNm);
                Row->SetNumberField(TEXT("dynamic_roll_nm"),Telemetry.OvertoppingDynamicRollMomentNm);
                Row->SetNumberField(TEXT("torque_x_nm"),Telemetry.AppliedTorqueNm.X);
                Motion.Add(MakeShared<FJsonValueObject>(Row));
            }
        }
        auto Report=MakeShared<FJsonObject>();Report->SetStringField(TEXT("scene"),Scene.Name);
        Report->SetStringField(TEXT("scope"),TEXT("Native production adapter forces without actor timed capsize constraint. Authored wave; representative loading; not live production mesh or calibrated hydraulic threshold."));
        Report->SetBoolField(TEXT("lab_only_candidate_pressure"),Candidate);
        Report->SetNumberField(TEXT("minimum_up_z"),MinimumUp);Report->SetNumberField(TEXT("maximum_omega_rad_s"),MaximumOmega);
        Report->SetNumberField(TEXT("risk_seconds"),RiskSeconds);Report->SetArrayField(TEXT("motion"),Motion);
        Reports.Add(MakeShared<FJsonValueObject>(Report));
        AddInfo(FString::Printf(TEXT("FLIP_BASELINE %s up_min=%.6f omega_max=%.6f risk_s=%.3f"),*Scene.Name,MinimumUp,MaximumOmega,RiskSeconds));
        if(Scene.Name==TEXT("calm"))TestTrue(TEXT("still water does not capsize"),MinimumUp>.99);
    }
    auto Root=MakeShared<FJsonObject>();Root->SetArrayField(TEXT("scenes"),Reports);
    FString Json;FJsonSerializer::Serialize(Root,TJsonWriterFactory<>::Create(&Json));
    const FString Dir=FPaths::ProjectSavedDir()/TEXT("FlipDemo");IFileManager::Get().MakeDirectory(*Dir,true);
    FString Label=TEXT("native-environments-latest");
    const bool Named=FParse::Value(FCommandLine::Get(),TEXT("RaftSimFlipEnvironmentLabel="),Label);
    if(Label.IsEmpty() || Label!=FPaths::MakeValidFileName(Label))
    {AddError(TEXT("Flip environment receipt requires a plain filename label"));return false;}
    const FString Receipt=Dir/(Label+TEXT(".json"));
    if(Named && IFileManager::Get().FileExists(*Receipt))
    {AddError(TEXT("Preserve prior flip receipt; use a fresh label"));return false;}
    TestTrue(TEXT("native flip receipt saved"),FFileHelper::SaveStringToFile(Json,*Receipt));
    return !HasAnyErrors();
}
#endif
