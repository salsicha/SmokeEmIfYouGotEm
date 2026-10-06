#include "Misc/AutomationTest.h"
#include "RaftSimSurfaceRefinement.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimParallelCrestEmissionTest,
    "RaftSim.M4.ParallelCrestEmission",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimParallelCrestEmissionTest::RunTest(const FString&)
{
    // Every edge mask, rotation, winding and both green diagonals. Independent
    // expected children and ordered green metadata, including reused outputs.
    for(bool Short:{false,true})
    {
        TArray<int32> Source,Owners,Expected,ExpectedOwners,Out,OutOwners;
        TArray<FIntVector> ExpectedGreen,Green;TArray<uint8> ExpectedOther,Other;
        TMap<uint64,int32> Edges;
        const auto Key=[](int32 A,int32 B){return (uint64(FMath::Min(A,B))<<32)|uint32(FMath::Max(A,B));};
        for(int32 T=0;T<4096;++T)
        {
            const int32 Mask=T%8;int32 V[3]={T*3,T*3+1,T*3+2},M[3];
            if(T%3==0)Swap(V[0],V[1]);
            const int32 Owner=T%11-5;Source.Append({V[0],V[1],V[2]});Owners.Add(Owner);
            int32 Count=0;
            for(int32 E=0;E<3;++E)
            {M[E]=(Mask&(1<<E))?12288+T*3+E:INDEX_NONE;if(M[E]!=INDEX_NONE){Edges.Add(Key(V[E],V[(E+1)%3]),M[E]);++Count;}}
            const auto Add=[&](int32 A,int32 B,int32 C){Expected.Append({A,B,C});ExpectedOwners.Add(Owner);};
            if(Count==0){Add(V[0],V[1],V[2]);continue;}
            if(Count==3){Add(V[0],M[0],M[2]);Add(M[0],V[1],M[1]);Add(M[2],M[1],V[2]);Add(M[0],M[1],M[2]);continue;}
            int32 Start=0;
            if(Count==1)while(M[Start]==INDEX_NONE)++Start;
            else while(M[Start]==INDEX_NONE || M[(Start+1)%3]==INDEX_NONE)++Start;
            const int32 A=V[Start],B=V[(Start+1)%3],C=V[(Start+2)%3],AB=M[Start];
            if(Count==1){Add(A,AB,C);Add(AB,B,C);continue;}
            const int32 BC=M[(Start+1)%3];Add(B,BC,AB);
            const bool Alternate=Short && A%2==0;
            if(Short){ExpectedGreen.Emplace(A,B,C);ExpectedOther.Add(Alternate);}
            if(Alternate){Add(A,AB,BC);Add(A,BC,C);}else{Add(A,AB,C);Add(AB,BC,C);}
        }
        for(int32 Repeat=0;Repeat<2;++Repeat)
        {
            RaftSimParallelCrestEmission::Build(Source,Owners,Edges,Short,[](int32 A,int32,int32){return A%2==0;},Out,OutOwners,Green,Other);
            TestTrue(TEXT("all masks preserve ordered children, owners and green cache metadata"),
                Out==Expected && OutOwners==ExpectedOwners && Green==ExpectedGreen && Other==ExpectedOther);
        }
    }
    uint64 Exercised=0,Reused=0;int64 Compared=0;
    for(bool Retain:{false,true})for(bool Indexed:{false,true})
    {
        FRaftSimSurfaceRefinement Reference,Candidate;
        Reference.bIndexedEdges=Candidate.bIndexedEdges=Indexed;
        Reference.bRetainTopologyStorage=Candidate.bRetainTopologyStorage=Retain;
        Reference.bSelectiveDetailEdges=Candidate.bSelectiveDetailEdges=true;
        Candidate.bParallelTriangleEmission=true;
        for(int32 Frame=0;Frame<24;++Frame)
        {
            const int32 Epoch=Frame/2,N=Epoch%3==0?33:35;
            TArray<FVector2D> XY;TArray<int32> Triangles;
            for(int32 Y=0;Y<N;++Y)for(int32 X=0;X<N;++X)
            {
                XY.Emplace(-544000.+100.*X+Epoch*.173,-360000.+100.*Y-Epoch*.241);
                if(X<N-1 && Y<N-1 && (Epoch%5!=1 || X!=3))
                {
                    const int32 A=Y*N+X;
                    if(Epoch%3==0)Triangles.Append({A,A+1,A+N,A+1,A+N+1,A+N});
                    else Triangles.Append({A,A+N,A+1,A+1,A+N,A+N+1});
                }
            }
            const auto Height=[&](const FVector2D& P)
            {const auto D=(P-XY[N*N/2])*.01;return float(Epoch%4==0?0:(10.+Epoch)*FMath::Exp(-.4*D.X*D.X-.7*D.Y*D.Y));};
            const FBox2D Window(XY[N*N/2]-FVector2D(310),XY[N*N/2]+FVector2D(310));
            const FBox2D* Detail=Epoch%4==2?&Window:nullptr;
            const int32 Levels=Epoch==8?0:3;
            if(Frame==18){Reference.InvalidateTopologyCache();Candidate.InvalidateTopologyCache();}
            for(auto* W:{&Reference,&Candidate})
                if(!W->BuildAdaptive(XY,Triangles,Height,Levels,.5f,{},nullptr,true,true,Detail,25.f,true))return false;
            TArray<FVector2D> A,B;Reference.Expand(XY,A);Candidate.Expand(XY,B);
            TestTrue(TEXT("full adaptive history preserves coordinates, topology, owners and reuse decisions"),
                A==B && Reference.MidpointParents==Candidate.MidpointParents && Reference.Triangles==Candidate.Triangles &&
                Reference.TriangleOrigins==Candidate.TriangleOrigins && Reference.TopologyBuildCount==Candidate.TopologyBuildCount &&
                Reference.TopologyReuseCount==Candidate.TopologyReuseCount);
            Compared+=A.Num();
        }
        Exercised+=Candidate.ParallelEmissionLevels;Reused+=Candidate.TopologyReuseCount;
    }
    TestTrue(TEXT("parallel assembly and subsequent topology reuse actually exercised"),Exercised>40 && Reused>40);
    AddInfo(FString::Printf(TEXT("Compared %lld expanded coordinates over96 builds; parallel levels=%llu reused=%llu"),Compared,Exercised,Reused));
    return !HasAnyErrors();
}
#endif
