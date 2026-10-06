#include "Misc/AutomationTest.h"
#include "RaftSimCrestBoundaries.h"
#include "RaftSimSurfaceRefinement.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestBoundaryTest,
    "RaftSim.M4.CrestBoundaries",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestBoundaryTest::RunTest(const FString&)
{
    const auto Compare=[&](const TArray<int32>& Triangles,const TArray<FIntPoint>& Parents,int32 Sources)
    {
        TArray<uint8> A,B;
        RaftSimCrestBoundaries::Reference(Triangles,Parents,Sources,A);
        RaftSimCrestBoundaries::Indexed(Triangles,Parents,Sources,B);
        TestTrue(TEXT("Every ordered boundary flag exactly matches reference"),A==B && B.Num()==Parents.Num());
    };
    Compare({}, {},0);
    Compare({0,1,2},{{0,1},{0,3},{3,1},{0,1},{0,2}},3); // Consumed edge and descendants.
    Compare({0,1,2,0,1,2,0,1,2},{{0,1},{1,2},{0,2}},3); // Nonmanifold/repeated.
    Compare({0,0,1,0,1,2},{{0,0},{0,1},{1,2}},3); // Same-index edge.
    for(int32 Pass=0;Pass<36;++Pass)
    {
        TArray<FVector2D> XY;TArray<int32> Triangles;
        for(int32 Y=0;Y<6;++Y)for(int32 X=0;X<8;++X)XY.Emplace(X*100.+Pass*.17,Y*100.-Pass*.21);
        for(int32 Y=0;Y<5;++Y)for(int32 X=0;X<7;++X)
        {
            if((X+Y+Pass)%7==0)continue;const int32 I=Y*8+X;
            Triangles.Append({I,I+8,I+9,I,I+9,I+1});
        }
        if(Pass%2)for(int32 I=0;I<Triangles.Num();I+=3)Swap(Triangles[I+1],Triangles[I+2]);
        FRaftSimSurfaceRefinement Refinement;
        TestTrue(TEXT("Conforming topology fixture builds"),Refinement.Build(XY,Triangles,FBox2D(FVector2D(70,70),FVector2D(610,410)),Pass%4));
        Compare(Triangles,Refinement.MidpointParents,XY.Num());
    }
    TArray<int32> Fan;TArray<FIntPoint> Parents;
    for(int32 I=1;I<70000;++I){Fan.Append({0,I,I+1});Parents.Emplace(0,I);}
    Compare(Fan,Parents,70001); // Exercises bounded-chain overflow, including interior fan edges.
    FRaftSimIndexedEdgeMap Map(2);
    for(int32 I=1;I<70000;++I)++Map.FindOrAdd(uint64(I),4);
    for(int32 I=1;I<70000;++I)TestTrue(TEXT("FindOrAdd preserves existing indexed/overflow value"),Map.FindOrAdd(uint64(I),99)==5);
    return !HasAnyErrors();
}
#endif
