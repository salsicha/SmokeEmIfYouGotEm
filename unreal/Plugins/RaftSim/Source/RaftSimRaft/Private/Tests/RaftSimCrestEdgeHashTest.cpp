#include "Misc/AutomationTest.h"
#include "RaftSimSurfaceRefinement.h"

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
#endif
