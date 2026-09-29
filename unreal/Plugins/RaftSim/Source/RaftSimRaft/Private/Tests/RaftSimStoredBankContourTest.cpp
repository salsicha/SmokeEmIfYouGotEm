#include "RaftSimStoredBankContour.h"
#include "RaftSimWaterShoreline.h"
#include "RaftSimWaterRenderFrame.h"
#include "RaftSimShorelineCrestWeights.h"
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "HAL/PlatformTime.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimStoredBankContourTest,"RaftSim.M4.ThreeWetStoredCoordinates",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimStoredBankContourTest::RunTest(const FString&)
{
    using namespace RaftSimThreeWetBankContour;
    const double Bed[]={8.711944580078125,8.45587158203125,8.5344696044921875,8.3977813720703125};
    const double H[]={0.,double(.061720576137304306f),double(.17600621283054352f),double(.16925844550132751f)};
    const auto& BaselineBed=Bed;const auto& BaselineDepth=H;
    const double CapturedBed[]={8.5700531005859375,8.471832275390625,8.05267333984375,8.407135009765625};
    const double CapturedDepth[]={0.,0.096230357885360718,0.51686644554138184,0.15903805196285248};
    const double LaterDepth[]={0.,0.096459932625293732,0.51710975170135498,0.15926313400268555};
    const double LatestDepth[]={0.,0.096567489206790924,0.51723241806030273,0.15936948359012604};
    const double TransitionBed[]={8.5975189208984375,8.420166015625,8.374542236328125,8.2484893798828125};
    const double TransitionDepth[]={0.,0.17726732790470123,0.21229608356952667,0.34734654426574707};
    const double ChangedDepth[]={0.,0.17724543809890747,0.21227142214775085,0.34732389450073242};
    const double RowBed[]={8.0471343994140625,8.0450592041015625,7.95037841796875,8.0014495849609375};
    const double RowDepth[]={0.,0.001626607496291399,0.0067639793269336224,0.01633489690721035};
    const double ReversedRowDepth[]={0.,0.0018043745076283813,0.0071192341856658459,0.016551967710256577};
    const double ShallowEndcapDepth[]={0.,0.0020726395305246115,0.0076036825776100159,0.016833245754241943};
    const double CornerDepth[]={0.,.17728912830352783,.21232075989246368,.34736922383308411};
    const double SecondCornerBed[]={8.5865020751953125,8.4203643798828125,8.4630279541015625,8.2987060546875};
    const double SecondCornerDepth[]={0.,.16613596677780151,.10671740770339966,.28282999992370605};
    FCurve C;if(!TestTrue(TEXT("original v22 donors"),C.Init(Bed,H)))return false;
    struct FMap{FVector2D O,Step,RenderOrigin;};
    const FMap Maps[]={
        {FVector2D(-542600.,-360200.),FVector2D(-100.,-100.),FVector2D(-542600.,-360200.)},
        {FVector2D(0.,0.),FVector2D(100.,100.),FVector2D(0.,0.)},
        {FVector2D(-542600.,-360200.),FVector2D(100.,-100.),FVector2D(-542600.,-360200.)},
        {FVector2D(361100.,-543000.),FVector2D(-100.,100.),FVector2D(361100.,-543000.)},
        // Original source_id26184 = row116,col84 in the225-wide captured
        // grid. ONE grid origin (not one origin per bank) preserves edges.
        {FVector2D(-542600.,-360200.),FVector2D(-100.,-100.),FVector2D(-551000.,-348600.)},
        // Actual frame34/source31556 from the retained engine rejection log.
        {FVector2D(-545400.,-362600.),FVector2D(100.,-100.),FVector2D(-551000.,-348600.)},
        // Later frame66 of the same cell, with a much smaller inner radius.
        {FVector2D(-545400.,-362600.),FVector2D(100.,-100.),FVector2D(-551000.,-348600.)},
        // Frame80: both inner vertices can collapse exactly to the origin.
        {FVector2D(-545400.,-362600.),FVector2D(100.,-100.),FVector2D(-551000.,-348600.)},
        // Original proposal-live-v1 frame186/source33168, near the X axis.
        {FVector2D(-544900.,-363300.),FVector2D(-100.,-100.),FVector2D(-554200.,-348600.)},
        // Axis-live-v1 frames183/source33168 and292/source23259.
        {FVector2D(-544900.,-363300.),FVector2D(-100.,-100.),FVector2D(-554200.,-348600.)},
        {FVector2D(-545800.,-358900.),FVector2D(100.,-100.),FVector2D(-554200.,-348600.)},
        // Partition-live-v2 frame189/source33168 and214/source33610.
        {FVector2D(-544900.,-363300.),FVector2D(-100.,-100.),FVector2D(-554200.,-348600.)},
        {FVector2D(-545700.,-363500.),FVector2D(100.,100.),FVector2D(-554200.,-348600.)},
        // Shared-reserve live frame342/source23259 and414/source19466:
        // the same physical cell before/after the render-origin shift.
        {FVector2D(-545800.,-358900.),FVector2D(100.,-100.),FVector2D(-554200.,-348600.)},
        {FVector2D(-545800.,-358900.),FVector2D(100.,-100.),FVector2D(-557400.,-350300.)}
    };
    TArray<TSharedPtr<FJsonValue>> Cases;
    const auto Pair=[](const FVector2D& P)
    {
        TArray<TSharedPtr<FJsonValue>> A;
        for(double V:{P.X,P.Y})A.Add(MakeShared<FJsonValueString>(FString::Printf(TEXT("%.17g"),V)));
        return A;
    };
    for(int32 K=0;K<UE_ARRAY_COUNT(Maps);++K)
    {
        const auto& CaseBed=K>=13 ? RowBed : K==12 ? SecondCornerBed : K==10 ? RowBed : K>=8 ? TransitionBed : K>=5 ? CapturedBed : BaselineBed;
        const auto& CaseDepth=K==14 ? ShallowEndcapDepth : K==13 ? ReversedRowDepth : K==12 ? SecondCornerDepth : K==11 ? CornerDepth : K==10 ? RowDepth : K==9 ? ChangedDepth : K==8 ? TransitionDepth : K==7 ? LatestDepth : K==6 ? LaterDepth : K==5 ? CapturedDepth : BaselineDepth;
        FCurve CaseCurve;if(!TestTrue(TEXT("unchanged case donors"),CaseCurve.Init(CaseBed,CaseDepth)))return false;
        const auto& M=Maps[K];RaftSimStoredBankContour::FStorage Storage;
        if(!TestTrue(TEXT("Cartesian GPU storage map valid"),Storage.Init(CaseCurve,M.O,
            M.O+FVector2D(M.Step.X,0.),M.O+FVector2D(0.,M.Step.Y),.1,M.RenderOrigin)))return false;
        FResult R;const uint32 Control=VectorGetControlRegister();const double Begin=FPlatformTime::Seconds();
        const bool Good=RaftSimStoredBankContour::Build(CaseCurve,Storage,R);
        const double Ms=1000.*(FPlatformTime::Seconds()-Begin);
        FResult Reference;
        const bool ReferenceGood=BuildStored(CaseCurve,Storage.Width,Reference,Storage,Storage.RootWidth,true,false);
        if(!Good || !ReferenceGood)
        {
            AddInfo(FString::Printf(TEXT("StoredBank diagnosis case=%d short=%d short_stage=%d full=%d full_stage=%d full_a=(%.17g,%.17g) full_b=(%.17g,%.17g)"),
                K,Good,R.Stats.FailedStage,ReferenceGood,Reference.Stats.FailedStage,
                Reference.Stats.FailedA.X,Reference.Stats.FailedA.Y,Reference.Stats.FailedB.X,Reference.Stats.FailedB.Y));
            const FScopedIEEE Scope;FStats Diagnostic;
            const FPoint P=Storage.Local(Storage.BufferPosition(FPoint(Reference.Stats.FailedA)));
            const FPoint Q=Storage.Local(Storage.BufferPosition(FPoint(Reference.Stats.FailedB)));
            const FPoint A=Storage.InnerPoint(P,Storage.Width),B=Storage.InnerPoint(Q,Storage.Width),O(FVector2D::ZeroVector,true);
            AddInfo(FString::Printf(TEXT("StoredBank diagnosis order=%.17g outer=%.17g inner=%.17g dry_order=%.17g wet=%d dry=%d p_value=%.17g q_value=%.17g"),
                Cross(O,P,Q).Lo,Cross(P,Q,B).Lo,Cross(P,B,A).Lo,Cross(O,A,B).Lo,
                Certificate(CaseCurve,P,Q,Q,true,Diagnostic),Certificate(CaseCurve,O,A,B,false,Diagnostic),CaseCurve.Value(P).Lo,CaseCurve.Value(Q).Lo));
        }
        if(!TestTrue(TEXT("full-search reference retains complete certificate"),ReferenceGood))return false;
        TestTrue(TEXT("bounded proposal reduces radial root evaluations"),R.Stats.RootEvaluations<Reference.Stats.RootEvaluations);
        TArray<double> BoundedTimes,ReferenceTimes;
        for(int32 Repeat=0;Repeat<3;++Repeat)for(bool Bounded:{true,false,false,true})
        {
            FResult Trial;const double TrialBegin=FPlatformTime::Seconds();
            const bool TrialGood=Bounded ? RaftSimStoredBankContour::Build(CaseCurve,Storage,Trial) :
                BuildStored(CaseCurve,Storage.Width,Trial,Storage,Storage.RootWidth,true,false);
            const double TrialMs=1000.*(FPlatformTime::Seconds()-TrialBegin);
            if(!TestTrue(TEXT("both proposal policies require complete stored certificates"),TrialGood))return false;
            (Bounded ? BoundedTimes : ReferenceTimes).Add(TrialMs);
        }
        BoundedTimes.Sort();ReferenceTimes.Sort();
        AddInfo(FString::Printf(TEXT("StoredBank proposal case=%d bounded_radial_evaluations=%d reference_radial_evaluations=%d bounded_median_ms=%.6f reference_median_ms=%.6f; not game FPS or identical geometry"),
            K,R.Stats.RootEvaluations,Reference.Stats.RootEvaluations,(BoundedTimes[2]+BoundedTimes[3])*.5,(ReferenceTimes[2]+ReferenceTimes[3])*.5));
        AddInfo(FString::Printf(TEXT("StoredBank case=%d built=%d boundary=%d triangles=%d coefficient_tests=%d construction_ms=%.6f"),
            K,int32(Good),R.Boundary.Num(),R.Triangles.Num(),R.Stats.CoefficientTests,Ms));
        if(!Good)AddInfo(FString::Printf(TEXT("StoredBank failure_stage=%d A=(%.17g,%.17g) B=(%.17g,%.17g)"),
            R.Stats.FailedStage,R.Stats.FailedA.X,R.Stats.FailedA.Y,R.Stats.FailedB.X,R.Stats.FailedB.Y));
        TestEqual(TEXT("storage proof restores floating point state"),VectorGetControlRegister(),Control);
        if(!TestTrue(TEXT("whole stored contour certified"),Good))return false;
        if(K==10)TestTrue(TEXT("captured signed-neighbor fallback exercised and final partition certified"),Storage.SignedNeighborFallbacks>0);
        TestEqual(TEXT("complete wet polygon triangulation"),R.Triangles.Num(),R.Polygon.Num()-2);
        for(const auto& P:R.Polygon)
        {
            const auto World=Storage.BufferPosition(P);
            const auto Reload=Storage.Local(World);
            TestTrue(TEXT("actual float buffer storage is idempotent"),Storage.BufferPosition(Reload)==World);
            TestTrue(TEXT("certificate bounds bind the submitted coordinate"),SamePoint(P,Reload));
        }
        TestTrue(TEXT("canonical shared crossings retained exactly"),
            Storage.BufferPosition(R.Boundary[0])==Storage.Crossings[0] && Storage.BufferPosition(R.Boundary.Last())==Storage.Crossings[1]);
        TArray<FProcMeshVertex> Source;
        TArray<float> MeshBed,MeshDepth;TArray<uint8> Wet,Available;
        for(int32 I=0;I<4;++I)
        {
            FProcMeshVertex V;
            V.Position=FVector(M.O.X+(I%2)*M.Step.X,M.O.Y+(I/2)*M.Step.Y,100.*(CaseBed[I]+CaseDepth[I]));
            V.Normal=FVector::UpVector;V.UV0=FVector2D(I%2,I/2);
            V.UV1=FVector2D(I+.25,2.*I);V.UV2=FVector2D(.3*I,.7*I);
            V.UV3=FVector2D(.9*I,.1*I);V.Color=FColor(30*I,50*I,70*I,255);
            V.Tangent=FProcMeshTangent(FVector::ForwardVector,false);
            Source.Add(V);MeshBed.Add(float(CaseBed[I]));MeshDepth.Add(float(CaseDepth[I]));Wet.Add(I!=0);Available.Add(1);
        }
        TArray<FProcMeshVertex> Mesh;TArray<uint32> MeshIndices;TArray<int32> CellOffsets;
        RaftSimWaterShoreline::FTopologyCache Cache;bool Rebuilt=false;
        for(int32 Pass=0;Pass<2;++Pass)
        {
            auto Input=Source;
            if(!TestTrue(TEXT("actual certified builder/cache accepts stored fixture"),
                Cache.Update(2,2,MoveTemp(Input),Wet,Available,MeshDepth,MeshBed,Mesh,MeshIndices,CellOffsets,
                    Rebuilt,true,true,true,true,&M.RenderOrigin)))return false;
            TestEqual(TEXT("identical donors reuse certified connectivity"),Rebuilt,Pass==0);
            if(!TestEqual(TEXT("actual triangles retain every certified ear"),MeshIndices.Num(),3*R.Triangles.Num()))return false;
            TArray<int32> ToProof;ToProof.Init(INDEX_NONE,Mesh.Num());
            const FRaftSimWaterRenderFrame Frame{FVector(M.RenderOrigin.X,M.RenderOrigin.Y,0.)};
            for(uint32 I:MeshIndices)
            {
                const FVector3f Stored=Frame.Store(Mesh[I].Position);
                const FVector2D Buffer(double(Stored.X),double(Stored.Y));
                for(int32 J=0;J<R.Polygon.Num();++J)if(Buffer==Storage.BufferPosition(R.Polygon[J])){ToProof[I]=J;break;}
                if(!TestTrue(TEXT("actual submitted XY is an independently certified stored point"),ToProof[I]!=INDEX_NONE))return false;
            }
            for(int32 I=0;I<R.Triangles.Num();++I)
            {
                const FIntVector Actual(ToProof[MeshIndices[3*I]],ToProof[MeshIndices[3*I+1]],ToProof[MeshIndices[3*I+2]]);
                const auto& E=R.Triangles[I];
                if(!TestTrue(TEXT("builder preserves certified ears except required world winding"),
                    Actual==E || Actual==FIntVector(E.X,E.Z,E.Y)))return false;
            }
            const auto& Banks=Cache.GetCurvedBanks();
            if(!TestEqual(TEXT("one certified bank"),Banks.Num(),1))return false;
            TestTrue(TEXT("variable contour metadata retained"),Banks[0].bCertified && Banks[0].IntermediateCount()==R.Boundary.Num()-2);
            const TArray<float> Coarse={0.f,1.f,2.f,3.f},Shore={0.f,.2f,.4f,.6f};
            FRaftSimShorelineCrestWeights Weights;Weights.Update(Mesh.Num(),Coarse,Shore,Cache.GetEdges(),Banks);
            double Previous=0.;
            for(int32 I=0;I<Banks[0].IntermediateCount();++I)
            {
                const auto& B=Banks[0];const double T=B.Fraction(I);const auto& V=Mesh[B.FirstNode+I];
                TestTrue(TEXT("variable attributes preserve strictly ordered physical ray fraction"),T>Previous && T<1.);Previous=T;
                TestTrue(TEXT("UV0 follows actual source-cell position"),V.UV0.Equals(B.Point(I),1.e-12));
                TestTrue(TEXT("all transported UV payloads use the same contour fraction"),
                    V.UV1==FMath::Lerp(Mesh[B.StartNode].UV1,Mesh[B.EndNode].UV1,T) &&
                    V.UV2==FMath::Lerp(Mesh[B.StartNode].UV2,Mesh[B.EndNode].UV2,T) &&
                    V.UV3==FMath::Lerp(Mesh[B.StartNode].UV3,Mesh[B.EndNode].UV3,T));
                TestEqual(TEXT("crest weight writes variable contour node"),Weights.Coarse[B.FirstNode+I],
                    FMath::Lerp(Weights.Coarse[B.StartNode],Weights.Coarse[B.EndNode],float(T)));
            }
        }
        const auto SavedMesh=Mesh;const auto SavedIndices=MeshIndices;const auto SavedOffsets=CellOffsets;
        const uint64 SavedRebuilds=Cache.GetRebuildCount(),SavedReuses=Cache.GetReuseCount();
        auto InvalidInput=Source;const FVector2D InvalidOrigin(1.e100,1.e100);
        TestFalse(TEXT("inexact frame rejects actual cache publication"),Cache.Update(2,2,MoveTemp(InvalidInput),
            Wet,Available,MeshDepth,MeshBed,Mesh,MeshIndices,CellOffsets,Rebuilt,true,true,true,true,&InvalidOrigin));
        TestTrue(TEXT("proof failure preserves the previous successful frame and cache"),
            !Rebuilt && Mesh.Num()==SavedMesh.Num() && FMemory::Memcmp(Mesh.GetData(),SavedMesh.GetData(),
                SIZE_T(Mesh.Num())*sizeof(FProcMeshVertex))==0 && MeshIndices==SavedIndices && CellOffsets==SavedOffsets &&
                Cache.GetRebuildCount()==SavedRebuilds && Cache.GetReuseCount()==SavedReuses);
        auto Retry=Source;
        TestTrue(TEXT("previous certificate remains reusable after rejected frame"),
            Cache.Update(2,2,MoveTemp(Retry),Wet,Available,MeshDepth,MeshBed,Mesh,MeshIndices,CellOffsets,
                Rebuilt,true,true,true,true,&M.RenderOrigin) && !Rebuilt);
        auto Item=MakeShared<FJsonObject>();Item->SetNumberField(TEXT("case"),K);
        Item->SetNumberField(TEXT("construction_ms"),Ms);Item->SetNumberField(TEXT("coefficient_tests"),R.Stats.CoefficientTests);
        Item->SetArrayField(TEXT("origin_cm"),Pair(M.O));Item->SetArrayField(TEXT("end_cm"),Pair(M.O+M.Step));
        Item->SetArrayField(TEXT("render_origin_cm"),Pair(Storage.RenderOrigin));
        Item->SetStringField(TEXT("width_cm"),TEXT("0.10000000000000001"));
        TArray<TSharedPtr<FJsonValue>> BValues,HValues,Boundary,Inner,Polygon,Triangles;
        for(int32 I=0;I<4;++I)
        {
            BValues.Add(MakeShared<FJsonValueString>(FString::Printf(TEXT("%.17g"),CaseBed[I])));
            HValues.Add(MakeShared<FJsonValueString>(FString::Printf(TEXT("%.17g"),CaseDepth[I])));
        }
        for(const auto& P:R.Boundary)Boundary.Add(MakeShared<FJsonValueArray>(Pair(Storage.BufferPosition(P))));
        // Inner dry proof is mathematical geometry, not another submitted surface.
        for(const auto& P:R.InnerBoundary)Inner.Add(MakeShared<FJsonValueArray>(Pair(P.XY)));
        for(const auto& P:R.Polygon)Polygon.Add(MakeShared<FJsonValueArray>(Pair(Storage.BufferPosition(P))));
        for(const auto& T:R.Triangles)
        {
            TArray<TSharedPtr<FJsonValue>> Ids;
            for(int32 I:{T.X,T.Y,T.Z})Ids.Add(MakeShared<FJsonValueNumber>(I));
            Triangles.Add(MakeShared<FJsonValueArray>(Ids));
        }
        Item->SetArrayField(TEXT("bed"),BValues);Item->SetArrayField(TEXT("depth"),HValues);
        Item->SetArrayField(TEXT("boundary_buffer_cm"),Boundary);Item->SetArrayField(TEXT("inner_local"),Inner);
        Item->SetArrayField(TEXT("polygon_buffer_cm"),Polygon);Item->SetArrayField(TEXT("triangles"),Triangles);
        Cases.Add(MakeShared<FJsonValueObject>(Item));
    }
    // Changing depths must bind fresh certificates, including all four dry
    // corners. Compare cache updates to both a fresh builder and the proof's
    // actual stored polygon, not only to a source-text topology predicate.
    int32 DynamicUpdates=0,NodeCountChanges=0,SameSizeEarChanges=0;
    for(int32 Dry=0;Dry<4;++Dry)
    {
        const auto& M=Maps[4];
        RaftSimWaterShoreline::FTopologyCache Cache;
        TArray<FProcMeshVertex> Mesh;TArray<uint32> Indices;TArray<int32> Offsets;
        int32 PreviousCount=INDEX_NONE;TArray<FIntVector> PreviousEars;
        for(double Scale:{1.,.8,.9,.999,1.})
        {
            TArray<FProcMeshVertex> Source;
            TArray<float> Depth,Beds;TArray<uint8> Wet,Available;
            double CanonicalDepth[4];
            for(int32 I=0;I<4;++I)CanonicalDepth[I]=double(float(H[I]*Scale));
            for(int32 I=0;I<4;++I)
            {
                FProcMeshVertex V;
                V.Position=FVector(M.O.X+(I%2)*M.Step.X,M.O.Y+(I/2)*M.Step.Y,
                    100.*(Bed[I^Dry]+CanonicalDepth[I^Dry]));
                V.Normal=FVector::UpVector;V.UV0=FVector2D(I%2,I/2);
                Source.Add(V);Depth.Add(float(CanonicalDepth[I^Dry]));Beds.Add(float(Bed[I^Dry]));
                Wet.Add(I!=Dry);Available.Add(1);
            }
            FCurve Curve;RaftSimStoredBankContour::FStorage Storage;FResult Proof;
            if(!TestTrue(TEXT("dynamic canonical curve"),Curve.Init(Bed,CanonicalDepth)))return false;
            if(!TestTrue(TEXT("dynamic canonical storage"),Storage.Init(Curve,FVector2D(Source[Dry].Position),
                FVector2D(Source[Dry^1].Position),FVector2D(Source[Dry^2].Position),.1,M.RenderOrigin)))return false;
            if(!TestTrue(TEXT("dynamic independent stored certificate"),RaftSimStoredBankContour::Build(Curve,Storage,Proof)))return false;
            auto Input=Source;bool Rebuilt=false;
            if(!TestTrue(TEXT("dynamic cache accepts certified donors"),Cache.Update(2,2,MoveTemp(Input),Wet,Available,Depth,Beds,
                Mesh,Indices,Offsets,Rebuilt,true,true,true,true,&M.RenderOrigin)))return false;
            TArray<FProcMeshVertex> Fresh;TArray<uint32> FreshIndices;TArray<int32> FreshOffsets;
            if(!TestTrue(TEXT("dynamic fresh builder"),RaftSimWaterShoreline::Build(2,2,MoveTemp(Source),Wet,Available,Depth,Beds,
                Fresh,FreshIndices,&FreshOffsets,nullptr,true,true,true,nullptr,&M.RenderOrigin)))return false;
            if(!TestTrue(TEXT("dynamic cache connectivity equals fresh builder"),
                Indices==FreshIndices && Offsets==FreshOffsets && Mesh.Num()==Fresh.Num()))return false;
            for(int32 I=0;I<Mesh.Num();++I)
                if(!TestTrue(TEXT("dynamic cache positions and UVs equal fresh builder"),
                    Mesh[I].Position==Fresh[I].Position && Mesh[I].UV0==Fresh[I].UV0))return false;
            if(!TestEqual(TEXT("dynamic complete certified triangulation"),Indices.Num(),3*Proof.Triangles.Num()))return false;
            TArray<int32> ToProof;ToProof.Init(INDEX_NONE,Mesh.Num());
            const FRaftSimWaterRenderFrame Frame{FVector(M.RenderOrigin.X,M.RenderOrigin.Y,0.)};
            for(uint32 I:Indices)
            {
                const FVector3f Stored=Frame.Store(Mesh[I].Position);
                for(int32 J=0;J<Proof.Polygon.Num();++J)
                    if(FVector2D(double(Stored.X),double(Stored.Y))==Storage.BufferPosition(Proof.Polygon[J])){ToProof[I]=J;break;}
                if(!TestTrue(TEXT("dynamic stored vertex belongs to current certificate"),ToProof[I]!=INDEX_NONE))return false;
            }
            for(int32 I=0;I<Proof.Triangles.Num();++I)
            {
                const FIntVector Actual(ToProof[Indices[3*I]],ToProof[Indices[3*I+1]],ToProof[Indices[3*I+2]]);
                const auto& E=Proof.Triangles[I];
                if(!TestTrue(TEXT("dynamic ears bind current proof for every dry corner"),
                    Actual==E || Actual==FIntVector(E.X,E.Z,E.Y)))return false;
            }
            if(PreviousCount!=INDEX_NONE)
            {
                const bool CountChanged=PreviousCount!=Mesh.Num();
                const bool EarsChanged=PreviousEars!=Proof.Triangles;
                NodeCountChanges+=CountChanged;SameSizeEarChanges+=!CountChanged && EarsChanged;
                if(CountChanged || EarsChanged)TestTrue(TEXT("changed certificate connectivity forces rebuild"),Rebuilt);
            }
            PreviousCount=Mesh.Num();PreviousEars=Proof.Triangles;++DynamicUpdates;
        }
    }
    AddInfo(FString::Printf(TEXT("StoredBank dynamic_updates=%d node_count_changes=%d same_size_ear_changes=%d dry_corners=4"),
        DynamicUpdates,NodeCountChanges,SameSizeEarChanges));
    TestEqual(TEXT("all changing-depth/dry-corner cases executed"),DynamicUpdates,20);
    TestTrue(TEXT("node-count rebuild exercised"),NodeCountChanges>0);
    // Original frame34/source31556 rejection must become a full certificate,
    // not disappear through a widened band or disabled partition predicate.
    const auto& RejectedBed=CapturedBed;const auto& RejectedDepth=CapturedDepth;
    FCurve RejectedCurve;RaftSimStoredBankContour::FStorage RejectedStorage;FResult RejectedResult;
    if(!TestTrue(TEXT("captured rejection curve initializes"),RejectedCurve.Init(RejectedBed,RejectedDepth)))return false;
    if(!TestTrue(TEXT("captured rejection storage initializes"),RejectedStorage.Init(RejectedCurve,
        {-545400.,-362600.},{-545300.,-362600.},{-545400.,-362700.},.1,{-551000.,-348600.})))return false;
    const bool Repaired=RaftSimStoredBankContour::Build(RejectedCurve,RejectedStorage,RejectedResult);
    AddInfo(FString::Printf(TEXT("StoredBank captured_repair=%d stage=%d coefficient_tests=%d A=(%.17g,%.17g) B=(%.17g,%.17g)"),
        Repaired,RejectedResult.Stats.FailedStage,RejectedResult.Stats.CoefficientTests,
        RejectedResult.Stats.FailedA.X,RejectedResult.Stats.FailedA.Y,RejectedResult.Stats.FailedB.X,RejectedResult.Stats.FailedB.Y));
    TestTrue(TEXT("captured live rejection repaired with complete stored certificate"),Repaired);
    for(int32 Step=0;Step<=64;++Step)
    {
        // Synthetic coverage between two original snapshots, not measured
        // intermediate hydraulics and not a proof of the continuous interval.
        double SweepDepth[4];
        for(int32 I=0;I<4;++I)SweepDepth[I]=double(float(CapturedDepth[I]+(LatestDepth[I]-CapturedDepth[I])*double(Step)/64.));
        FCurve SweepCurve;RaftSimStoredBankContour::FStorage SweepStorage;FResult SweepResult;
        if(!TestTrue(TEXT("captured-range synthetic curve"),SweepCurve.Init(CapturedBed,SweepDepth)) ||
            !TestTrue(TEXT("captured-range synthetic storage"),SweepStorage.Init(SweepCurve,
                {-545400.,-362600.},{-545300.,-362600.},{-545400.,-362700.},.1,{-551000.,-348600.})) ||
            !TestTrue(TEXT("captured-range synthetic contour fully certified"),RaftSimStoredBankContour::Build(SweepCurve,SweepStorage,SweepResult)))return false;
    }
    {
        const FScopedIEEE Scope;
        const FPoint P=RejectedStorage.Local({5600.00048828125,-14000.1494140625});
        const FPoint Q=RejectedStorage.Local({5600.,-14000.099609375});
        const FPoint A=Inner(P,RejectedStorage.Width),B=Inner(Q,RejectedStorage.Width),O(FVector2D::ZeroVector,true);
        TestTrue(TEXT("exact repeated origin has zero cross in every slot"),
            Cross(P,O,O).Zero() && Cross(O,P,O).Zero() && Cross(O,O,P).Zero());
        const FPoint Uncertain(FVector2D::ZeroVector,FBound(-1.e-20,1.e-20),FBound(-1.e-20,1.e-20));
        TestFalse(TEXT("overlapping uncertain coordinates are not exact repeated vertices"),Cross(P,O,Uncertain).Zero());
        FStats Stats;
        AddInfo(FString::Printf(TEXT("StoredBank terminal_span order_lo=%.17g outer_lo=%.17g inner_lo=%.17g wet=%d dry=%d inner_a=(%.17g,%.17g) inner_b=(%.17g,%.17g)"),
            Cross(O,P,Q).Lo,Cross(P,Q,B).Lo,Cross(P,B,A).Lo,
            Certificate(RejectedCurve,P,Q,Q,true,Stats),Certificate(RejectedCurve,O,A,B,false,Stats),A.XY.X,A.XY.Y,B.XY.X,B.XY.Y));
        TestTrue(TEXT("collapsed terminal inner fan retains certified partition"),Cross(P,B,A).Lo>=0.);
    }
    {
        // Actual proposal-live-v1 frame186/source33168, canonical dry corner1.
        // This is simulation evidence, not a surveyed terrain measurement.
        FCurve Transition;RaftSimStoredBankContour::FStorage Storage;FResult Short,Full,Selected;
        if(!TestTrue(TEXT("captured transition donors"),Transition.Init(TransitionBed,TransitionDepth)) ||
            !TestTrue(TEXT("captured transition storage"),Storage.Init(Transition,{-544900.,-363300.},
                {-545000.,-363300.},{-544900.,-363400.},.1,{-554200.,-348600.})))return false;
        const bool ShortGood=BuildStored(Transition,Storage.Width,Short,Storage,Storage.RootWidth,true,true);
        const bool FullGood=BuildStored(Transition,Storage.Width,Full,Storage,Storage.RootWidth,true,false);
        const bool SelectedGood=RaftSimStoredBankContour::Build(Transition,Storage,Selected);
        AddInfo(FString::Printf(TEXT("StoredBank transition short=%d full=%d selected=%d short_stage=%d full_stage=%d; native geometry only"),
            ShortGood,FullGood,SelectedGood,Short.Stats.FailedStage,Full.Stats.FailedStage));
        TestTrue(TEXT("transition shorter search completely certified"),ShortGood);
        TestTrue(TEXT("transition full search completely certified"),FullGood);
        TestTrue(TEXT("transition selected contour completely certified"),SelectedGood);
        const FScopedIEEE Scope;
        const FPoint StoredDry=Storage.Local({9299.9013671875,-14700.0009765625});
        TestTrue(TEXT("captured rounded point is genuinely dry, not an epsilon defect"),Transition.Value(StoredDry).Hi<0.);
    }
    {
        // Original axis-live-v1 changes now require complete certificates.
        // Preserve original frames183/source33168 and292/source23259.
        const double LiveBeds[][4]={{8.5975189208984375,8.420166015625,8.374542236328125,8.2484893798828125},
            {8.0471343994140625,8.0450592041015625,7.95037841796875,8.0014495849609375}};
        const double LiveDepths[][4]={{0.,0.17724543809890747,0.21227142214775085,0.34732389450073242},
            {0.,0.001626607496291399,0.0067639793269336224,0.01633489690721035}};
        const FVector2D LiveDry[]={{-544900.,-363300.},{-545800.,-358900.}};
        const double StepX[]={-100.,100.};
        for(int32 I=0;I<2;++I)
        {
            FCurve LiveCurve;RaftSimStoredBankContour::FStorage LiveStorage;FResult LiveResult;
            if(!TestTrue(TEXT("original changed-state donors valid"),LiveCurve.Init(LiveBeds[I],LiveDepths[I])) ||
                !TestTrue(TEXT("original changed-state storage valid"),LiveStorage.Init(LiveCurve,LiveDry[I],
                    LiveDry[I]+FVector2D(StepX[I],0.),LiveDry[I]+FVector2D(0.,-100.),.1,{-554200.,-348600.})))return false;
            const bool LiveGood=RaftSimStoredBankContour::Build(LiveCurve,LiveStorage,LiveResult);
            AddInfo(FString::Printf(TEXT("StoredBank changed_state=%d built=%d stage=%d; native geometry only"),I,LiveGood,LiveResult.Stats.FailedStage));
            TestTrue(TEXT("changed-state geometry has complete positive proof"),LiveGood);
        }
    }
    // Every original rejected update from partition-live-v2, not just a
    // selected first/last snapshot. These are simulation captures, not surveys.
    {
        struct FCapture{double Bed[4],Depth[4];FVector2D Dry,Step;};
        const FCapture Captures[]={
            {{8.5975189208984375,8.420166015625,8.374542236328125,8.2484893798828125},{0,0.17728912830352783,0.21232075989246368,0.34736922383308411},{-544900,-363300},{-100,-100}},
            {{8.5975189208984375,8.420166015625,8.374542236328125,8.2484893798828125},{0,0.17729640007019043,0.21232900023460388,0.34737679362297058},{-544900,-363300},{-100,-100}},
            {{8.5975189208984375,8.420166015625,8.374542236328125,8.2484893798828125},{0,0.17730365693569183,0.21233722567558289,0.34738436341285706},{-544900,-363300},{-100,-100}},
            {{8.5975189208984375,8.420166015625,8.374542236328125,8.2484893798828125},{0,0.17731092870235443,0.21234548091888428,0.34739193320274353},{-544900,-363300},{-100,-100}},
            {{8.5975189208984375,8.420166015625,8.374542236328125,8.2484893798828125},{0,0.17731821537017822,0.21235372126102448,0.34739947319030762},{-544900,-363300},{-100,-100}},
            {{8.5975189208984375,8.420166015625,8.374542236328125,8.2484893798828125},{0,0.17732550203800201,0.21236197650432587,0.34740704298019409},{-544900,-363300},{-100,-100}},
            {{8.5975189208984375,8.420166015625,8.374542236328125,8.2484893798828125},{0,0.177332803606987,0.21237024664878845,0.34741461277008057},{-544900,-363300},{-100,-100}},
            {{8.5975189208984375,8.420166015625,8.374542236328125,8.2484893798828125},{0,0.17734012007713318,0.21237851679325104,0.34742218255996704},{-544900,-363300},{-100,-100}},
            {{8.5865020751953125,8.4203643798828125,8.4630279541015625,8.2987060546875},{0,0.16605490446090698,0.10665461421012878,0.28275790810585022},{-545700,-363500},{100,100}},
            {{8.5865020751953125,8.4203643798828125,8.4630279541015625,8.2987060546875},{0,0.1660630851984024,0.10666102170944214,0.28276520967483521},{-545700,-363500},{100,100}},
            {{8.5865020751953125,8.4203643798828125,8.4630279541015625,8.2987060546875},{0,0.16607125103473663,0.10666739195585251,0.2827724814414978},{-545700,-363500},{100,100}},
            {{8.5865020751953125,8.4203643798828125,8.4630279541015625,8.2987060546875},{0,0.16607938706874847,0.10667373985052109,0.2827797532081604},{-545700,-363500},{100,100}},
            {{8.5865020751953125,8.4203643798828125,8.4630279541015625,8.2987060546875},{0,0.16608752310276031,0.10668005049228668,0.28278696537017822},{-545700,-363500},{100,100}},
            {{8.5865020751953125,8.4203643798828125,8.4630279541015625,8.2987060546875},{0,0.16609562933444977,0.10668633878231049,0.28279417753219604},{-545700,-363500},{100,100}},
            {{8.5865020751953125,8.4203643798828125,8.4630279541015625,8.2987060546875},{0,0.16610373556613922,0.1066926047205925,0.28280138969421387},{-545700,-363500},{100,100}},
            {{8.5865020751953125,8.4203643798828125,8.4630279541015625,8.2987060546875},{0,0.16611181199550629,0.10669884085655212,0.2828085720539093},{-545700,-363500},{100,100}},
            {{8.5865020751953125,8.4203643798828125,8.4630279541015625,8.2987060546875},{0,0.16611987352371216,0.10670505464076996,0.28281572461128235},{-545700,-363500},{100,100}},
            {{8.5865020751953125,8.4203643798828125,8.4630279541015625,8.2987060546875},{0,0.16612792015075684,0.106711246073246,0.2828228771686554},{-545700,-363500},{100,100}},
            {{8.5865020751953125,8.4203643798828125,8.4630279541015625,8.2987060546875},{0,0.16613596677780151,0.10671740770339966,0.28282999992370605},{-545700,-363500},{100,100}},
        };
        for(const FCapture& Capture:Captures)
        {
            FCurve Curve;RaftSimStoredBankContour::FStorage Storage;FResult Result;
            if(!TestTrue(TEXT("original partition-replay donors"),Curve.Init(Capture.Bed,Capture.Depth)) ||
                !TestTrue(TEXT("original partition-replay map"),Storage.Init(Curve,Capture.Dry,
                    Capture.Dry+FVector2D(Capture.Step.X,0.),Capture.Dry+FVector2D(0.,Capture.Step.Y),.1,{-554200.,-348600.})) ||
                !TestTrue(TEXT("all original rejected updates now certify"),RaftSimStoredBankContour::Build(Curve,Storage,Result)))return false;
        }
        AddInfo(TEXT("StoredBank original_partition_rejections=19 fully_certified=19"));
    }
    // Synthetic near-corner approach in BOTH captured cells. These are
    // additional changing-depth probes, not continuous-state or field proof.
    for(int32 Cell=11;Cell<=12;++Cell)for(int32 Step=0;Step<=128;++Step)
    {
        const auto& B=Cell==11 ? TransitionBed : SecondCornerBed;
        const auto& H0=Cell==11 ? CornerDepth : SecondCornerDepth;
        double Margin=1.;for(int32 I=1;I<4;++I)Margin=FMath::Min(Margin,B[0]-B[I]-H0[I]);
        double H1[4]={0.};for(int32 I=1;I<4;++I)H1[I]=double(float(H0[I]+.95*Margin*double(Step)/128.));
        FCurve Curve;RaftSimStoredBankContour::FStorage Storage;FResult Result;const auto& M=Maps[Cell];
        if(!TestTrue(TEXT("synthetic corner-approach donors"),Curve.Init(B,H1)) ||
            !TestTrue(TEXT("synthetic corner-approach map"),Storage.Init(Curve,M.O,
                M.O+FVector2D(M.Step.X,0.),M.O+FVector2D(0.,M.Step.Y),.1,M.RenderOrigin)) ||
            !TestTrue(TEXT("synthetic corner-approach complete certificate"),RaftSimStoredBankContour::Build(Curve,Storage,Result)))
        {
            AddInfo(FString::Printf(TEXT("StoredBank corner_sweep cell=%d step=%d stage=%d"),Cell,Step,Result.Stats.FailedStage));return false;
        }
    }
    AddInfo(TEXT("StoredBank synthetic_corner_approach=258 fully_certified=258"));
    RaftSimStoredBankContour::FStorage Bad;FResult R;
    RaftSimStoredBankContour::FStorage Unrebased;
    TestTrue(TEXT("unrebased captured map initializes"),Unrebased.Init(C,Maps[0].O,
        Maps[0].O+FVector2D(-100.,0.),Maps[0].O+FVector2D(0.,-100.),.1));
    TestFalse(TEXT("unrebased captured failure retained, NOT declared safe"),RaftSimStoredBankContour::Build(C,Unrebased,R));
    double Difference=0.;
    TestFalse(TEXT("inexact origin subtraction rejected"),RaftSimStoredBankContour::FStorage::ExactDifference(1.,1.e-100,Difference));
    TestFalse(TEXT("uninitialized storage cannot certify"),RaftSimStoredBankContour::Build(C,Bad,R));
    TestFalse(TEXT("sheared map rejected rather than assumed Cartesian"),Bad.Init(C,{0.,0.},{100.,1.},{0.,100.},.1));
    TestFalse(TEXT("coarse GPU coordinates reject the one millimetre budget"),Bad.Init(C,{10000000.,10000000.},
        {10000100.,10000000.},{10000000.,10000100.},.1));
    TestFalse(TEXT("invalid reinitialization cannot reuse old map"),RaftSimStoredBankContour::Build(C,Bad,R));
    FString Path;
    if(FParse::Value(FCommandLine::Get(),TEXT("RaftSimStoredBankExport="),Path))
    {
        auto Root=MakeShared<FJsonObject>();Root->SetArrayField(TEXT("cases"),Cases);
        Root->SetBoolField(TEXT("normal_renderer_integrated"),false);Root->SetBoolField(TEXT("gameplay_accepted"),false);
        FString Text;auto Writer=TJsonWriterFactory<>::Create(&Text);
        TestTrue(TEXT("stored contour export serializes"),FJsonSerializer::Serialize(Root,Writer));
        TestTrue(TEXT("stored contour export saved"),FFileHelper::SaveStringToFile(Text,*Path));
    }
    return !HasAnyErrors();
}
#endif
