#include "Misc/AutomationTest.h"
#include "RaftSimSurfaceRefinement.h"
#include "RaftSimIndexedBreakingProfile.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestEdgeHashTest,
    "RaftSim.M4.CrestEdgeHashSelection",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestEdgeHashTest::RunTest(const FString&)
{
    TMap<uint64,int32> LegacyEdges;TRaftSimEdgeMap<int32> StrongEdges;
    TArray<int32> LegacyBuckets,StrongBuckets;LegacyBuckets.Init(0,4096);StrongBuckets.Init(0,4096);
    for(uint32 I=0;I<65536;++I)
    {
        const uint64 Key=(uint64(I)<<32)|uint64(I+1);
        LegacyEdges.Add(Key,int32(I));StrongEdges.Add(Key,int32(I));
        ++LegacyBuckets[GetTypeHash(Key)&4095];++StrongBuckets[RaftSimEdgeHash(Key)&4095];
    }
    bool ExactEdges=true;auto L=LegacyEdges.CreateConstIterator();auto S=StrongEdges.CreateConstIterator();
    for(;L && S;++L,++S)ExactEdges &= L.Key()==S.Key() && L.Value()==S.Value();
    ExactEdges &= !L && !S;
    int32 UsedLegacy=0,UsedStrong=0,MaxLegacy=0,MaxStrong=0;
    for(int32 I=0;I<4096;++I)
    {
        UsedLegacy+=LegacyBuckets[I]>0;UsedStrong+=StrongBuckets[I]>0;
        MaxLegacy=FMath::Max(MaxLegacy,LegacyBuckets[I]);MaxStrong=FMath::Max(MaxStrong,StrongBuckets[I]);
    }
    for(uint32 I=0;I<65536;I+=7)
    {
        const uint64 Key=(uint64(I)<<32)|uint64(I+1);
        ExactEdges &= LegacyEdges.Remove(Key)==StrongEdges.Remove(Key);
        ExactEdges &= !StrongEdges.Contains(Key);
        LegacyEdges.Add(Key,-int32(I));StrongEdges.Add(Key,-int32(I));
        ExactEdges &= *LegacyEdges.Find(Key)==*StrongEdges.Find(Key);
    }
    TestTrue(TEXT("unchanged edge identity, insertion order and updates"),ExactEdges);
    TestTrue(TEXT("decorrelates regular-grid bucket selection"),UsedStrong>4*UsedLegacy && MaxStrong<MaxLegacy/2);
    AddInfo(FString::Printf(TEXT("Manufactured 65536 neighboring edges / 4096 buckets: legacy used=%d max=%d, strong used=%d max=%d; not actual-game timing"),
        UsedLegacy,MaxLegacy,UsedStrong,MaxStrong));
    constexpr int32 N=23;
    TArray<FVector2D> XY;TArray<int32> Triangles;
    for(int32 Y=0;Y<N;++Y)for(int32 X=0;X<N;++X)
    {
        XY.Emplace(-544000.+100.*X,-360000.+100.*Y);
        if(X<N-1 && Y<N-1){const int32 A=Y*N+X;Triangles.Append({A,A+N,A+1,A+1,A+N,A+N+1});}
    }
    // Exercise empty lookup, endpoint zero/self edges, repeated updates and
    // high-degree nonmanifold fans beyond the bounded eight-entry chain.
    FRaftSimIndexedEdgeMap Indexed(70000);
    TestTrue(TEXT("indexed map starts empty"),Indexed.IsEmpty());
    bool ExactIndexed=true;
    for(uint32 I=0;I<70000;++I)Indexed.Add(uint64(I),int32(I));
    for(uint32 I=0;I<70000;++I)
    {
        const int32* Found=Indexed.Find(uint64(I));
        ExactIndexed &= Found && *Found==int32(I);
        Indexed.Add(uint64(I),-int32(I));
        ExactIndexed &= *Indexed.Find(uint64(I))==-int32(I);
    }
    ExactIndexed &= !Indexed.Contains((uint64(69999)<<32)|69999);
    TestTrue(TEXT("indexed bounded and spill lookups preserve every high-degree edge"),ExactIndexed);
    FRaftSimSurfaceRefinement Original,Candidate,Serial,Direct;
    Direct.bIndexedEdges=true;
    Candidate.bStrongEdgeHash=true;
    int64 Compared=0;
    for(int32 Frame=0;Frame<24;++Frame)
    {
        if(Frame>=4)XY[N*N/2]+=FVector2D(.173,-.241);
        if(Frame==9)for(auto& P:XY)P+=FVector2D(1900,-2300);
        if(Frame==12)for(int32 T=0;T<Triangles.Num();T+=3)Swap(Triangles[T+1],Triangles[T+2]);
        const auto Height=[&](const FVector2D& P)
        {
            const auto D=(P-XY[N*N/2])*.01;
            return float((Frame%3 ? 15.+Frame*3. : 0.)*FMath::Exp(-.3*D.X*D.X-.6*D.Y*D.Y));
        };
        const FBox2D Window(XY[N*N/2]-FVector2D(220),XY[N*N/2]+FVector2D(220));
        const FBox2D* Detail=Frame%4 ? nullptr : &Window;
        TArray<FBox2D> Regions;
        if(Frame%5==0)Regions.Add(FBox2D(XY[N*N/2]-FVector2D(1100),XY[N*N/2]+FVector2D(1100)));
        for(auto* W:{&Original,&Candidate,&Direct})
            if(!W->BuildAdaptive(XY,Triangles,Height,3,.5f,Regions,nullptr,true,true,Detail,25.f,Frame!=14))return false;
        if(!Serial.BuildAdaptive(XY,Triangles,Height,3,.5f,Regions,nullptr,false,false,Detail,25.f))return false;
        TArray<FVector2D> A,B,C,D;Original.Expand(XY,A);Candidate.Expand(XY,B);Serial.Expand(XY,C);Direct.Expand(XY,D);
        TestTrue(TEXT("indexed edges preserve ordered topology, ownership and exact expanded coordinates"),
            Original.MidpointParents==Direct.MidpointParents && Original.Triangles==Direct.Triangles &&
            Original.TriangleOrigins==Direct.TriangleOrigins && A==D);
        TestTrue(TEXT("edge hash preserves original and serial ordered topology, ownership and coordinates"),
            Original.MidpointParents==Candidate.MidpointParents && Original.Triangles==Candidate.Triangles &&
            Original.TriangleOrigins==Candidate.TriangleOrigins && A==B && B==C &&
            Original.MidpointParents==Serial.MidpointParents && Original.Triangles==Serial.Triangles &&
            Original.TriangleOrigins==Serial.TriangleOrigins);
        Compared+=A.Num();
    }
    AddInfo(FString::Printf(TEXT("Strong/default/serial exact over %lld vertices and 24 moving profiles, crops, winding, regions, detail windows and cache epochs"),Compared));
    return !HasAnyErrors();
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestTopologyStorageTest,
    "RaftSim.M4.CrestTopologyStorage",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestTopologyStorageTest::RunTest(const FString&)
{
    FRaftSimSurfaceRefinement Original,Retained,Serial;
    Original.bIndexedEdges=Retained.bIndexedEdges=true;
    Retained.bRetainTopologyStorage=true;
    int64 Compared=0;uint64 Queries[2]={};
    for(int32 Frame=0;Frame<36;++Frame)
    {
        const int32 N=Frame%6<3?17:13;
        TArray<FVector2D> XY;TArray<int32> Triangles;
        for(int32 Y=0;Y<N;++Y)for(int32 X=0;X<N;++X)
        {
            XY.Emplace(-544000.+100.*X+Frame*.173,-360000.+100.*Y-Frame*.241);
            if(X<N-1 && Y<N-1 && (Frame%5!=1 || X!=3))
            {
                const int32 A=Y*N+X;
                if(Frame%7==0)Triangles.Append({A,A+1,A+N,A+1,A+N+1,A+N});
                else Triangles.Append({A,A+N,A+1,A+1,A+N,A+N+1});
            }
        }
        const auto Height=[&](const FVector2D& P)
        {
            const auto D=(P-XY[N*N/2])*.01;
            return float(Frame%4==0?0:(10.+Frame)*FMath::Exp(-.4*D.X*D.X-.7*D.Y*D.Y));
        };
        const FBox2D Window(XY[N*N/2]-FVector2D(210),XY[N*N/2]+FVector2D(210));
        const auto* Detail=Frame%4==2?&Window:nullptr;
        const int32 Levels=Frame%9==0?0:(Frame%9==1?1:3);
        if(Frame==20){Original.InvalidateTopologyCache();Retained.InvalidateTopologyCache();}
        for(int32 Kind=0;Kind<2;++Kind)
        {
            TAtomic<uint64> Calls{0};auto& W=Kind?Retained:Original;
            const auto Counted=[&](const FVector2D& P){++Calls;return Height(P);};
            if(!W.BuildAdaptive(XY,Triangles,Counted,Levels,.5f,{},nullptr,true,true,Detail,25.f,true))return false;
            Queries[Kind]=Calls.Load();
        }
        if(!Serial.BuildAdaptive(XY,Triangles,Height,Levels,.5f,{},nullptr,false,false,Detail,25.f))return false;
        TArray<FVector2D> A,B,C;Original.Expand(XY,A);Retained.Expand(XY,B);Serial.Expand(XY,C);
        TestTrue(TEXT("storage reuse preserves every current height query, topology cache decision and output"),
            Queries[0]==Queries[1] && Original.TopologyBuildCount==Retained.TopologyBuildCount &&
            Original.TopologyReuseCount==Retained.TopologyReuseCount && A==B && B==C &&
            Original.MidpointParents==Retained.MidpointParents && Original.Triangles==Retained.Triangles &&
            Original.TriangleOrigins==Retained.TriangleOrigins && Retained.MidpointParents==Serial.MidpointParents &&
            Retained.Triangles==Serial.Triangles && Retained.TriangleOrigins==Serial.TriangleOrigins);
        Compared+=A.Num();
    }
    AddInfo(FString::Printf(TEXT("Exact topology storage reuse over36 moving/deformed roots, crops, winding, flat/nonflat profiles,0/1/3 levels and explicit invalidation: %lld vertices"),Compared));
    return !HasAnyErrors();
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestEmptyTileTest,
    "RaftSim.M4.CrestEmptyTile",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestEmptyTileTest::RunTest(const FString&)
{
    using FSite=URaftSimWaterRuntimeAdapter::FSupportBreakingSite;
    FRandomStream Random(842619);int64 Compared=0,EmptySamples=0,NonzeroSamples=0;
    for(int32 Case=0;Case<11;++Case)
    {
        TArray<FSite> Sites;
        for(int32 I=0;I<24 && Case!=8;++I)
        {
            auto& S=Sites.AddDefaulted_GetRef();
            S.RiverCoordinatesMeters=FVector2D(-5460.+(I%6)*14.,3590.+(I/6)*11.);
            S.FlowDirection=RaftSimWaterFlowFrame::FromAngle(I*.71f)*(Case==3 ? 1.31 : 1.);
            S.PhysicalCrestHeightMeters=Case==10 ? 0.f : (I==23 ? 1.7f : .12f+(I%5)*.15f);
            S.PhysicalCrestLengthMeters=1.f+(I%9);S.SpillingFraction=(I%4)*.41f;
            S.bLocalEnvelopeCap=Case==0 || (Case!=1 && I%2==0);S.Intensity=.7f;
        }
        if(Case==4)Sites[11].PhysicalCrestHeightMeters=-1.f;
        if(Case==5)Sites[8].FlowDirection=FVector2D::ZeroVector;
        if(Case==6)Sites[7].RiverCoordinatesMeters.X=1.e9;
        if(Case==7)Algo::Reverse(Sites);
        if(Case==9)Sites[7].RiverCoordinatesMeters=FVector2D(20000.,20000.);
        FRaftSimIndexedBreakingProfile Index(Sites,.35f,.7f),Copy=Index;
        const FRaftSimIndexedBreakingProfile Moved=MoveTemp(Copy);
        TestEqual(TEXT("unsupported index stays on full evaluator"),Index.IsIndexed(),Case!=4 && Case!=5 && Case!=6);
        const auto Compare=[&](const FVector2D& P)
        {
            float FullFoam=-1.f;
            const float Full=URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P,Sites,.35f,.7f,&FullFoam);
            for(bool Dense:{false,true})
            {
                float OldFoam=-1.f,FastFoam=-1.f,MovedFoam=-1.f;
                const float Old=Index.Sample(P,&OldFoam,Dense);
                const float Fast=Index.SampleWithEmptyTileSkip(P,&FastFoam,Dense,true);
                const float AfterMove=Moved.SampleWithEmptyTileSkip(P,&MovedFoam,Dense,true);
                if(Full!=Old || Full!=Fast || Full!=AfterMove || FullFoam!=OldFoam || FullFoam!=FastFoam || FullFoam!=MovedFoam ||
                    Index.Sample(P)!=Index.SampleWithEmptyTileSkip(P,nullptr,Dense,true))
                {AddError(FString::Printf(TEXT("Empty-tile mismatch case%d at %.17g,%.17g"),Case,P.X,P.Y));return false;}
            }
            EmptySamples+=Full==0 && FullFoam==0;NonzeroSamples+=Full!=0 || FullFoam!=0;
            ++Compared;return true;
        };
        for(int32 I=0;I<16000;++I)
            if(!Compare(FVector2D(Random.FRandRange(-5540.f,-5280.f),Random.FRandRange(3480.f,3740.f))))return false;
        for(const auto& Site:Sites)
        {
            const double Norm=Site.FlowDirection.SizeSquared();
            if(Norm==0 || Site.PhysicalCrestHeightMeters<0)continue;
            const float L=FMath::Clamp(Site.PhysicalCrestLengthMeters,2.f,7.f);
            for(double D:{-3.*L,0.,7.*L})for(double A:{-12.,0.,12.})for(double E:{-.00001,0.,.00001})
                if(!Compare(Site.RiverCoordinatesMeters+RaftSimWaterFlowFrame::ToField(FVector2D(D+E,A+E),Site.FlowDirection)/Norm))return false;
        }
        for(int32 I=-20;I<20;++I)for(double E:{-.00001,0.,.00001})
            if(!Compare(FVector2D(-5464.+I*8.+E,3592.+I*8.-E)))return false;
        if(!Compare(FVector2D::ZeroVector) || !Compare(FVector2D(1.e9,-1.e9)))return false;
    }
    TestTrue(TEXT("both zero and contributing samples exercised"),EmptySamples>0 && NonzeroSamples>0);
    AddInfo(FString::Printf(TEXT("Exact empty-tile/full/reference height and foam at %lld points; dense/hash, copy/move, support/tile seams, caps, zero-lift emitters and fallbacks"),Compared));
    return !HasAnyErrors();
}
#endif
