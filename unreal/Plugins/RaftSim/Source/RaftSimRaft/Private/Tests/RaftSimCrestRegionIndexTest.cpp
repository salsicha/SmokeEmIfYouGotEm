#include "Misc/AutomationTest.h"
#include "RaftSimSurfaceRefinement.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestRegionIndexTest,"RaftSim.M4.CrestRegionIndex",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestRegionIndexTest::RunTest(const FString&)
{
    FRandomStream Random(1793);int32 Compared=0;
    for(int32 Frame=0;Frame<20;++Frame)
    {
        TArray<FBox2D> Regions;
        for(int32 I=0;I<Frame*17;++I)
        {
            const FVector2D P(Random.FRandRange(-10000,10000),Random.FRandRange(-10000,10000));
            Regions.Emplace(P,P+FVector2D(Random.FRandRange(0,1200),Random.FRandRange(0,1200)));
        }
        if(Frame==3)Regions.Add(FBox2D(ForceInit)); // Preserve original unusual-input semantics.
        FRaftSimCrestRegionIndex Index(Regions);
        for(int32 I=0;I<2000;++I)
        {
            const FVector2D P(Random.FRandRange(-11000,11000),Random.FRandRange(-11000,11000));
            FBox2D Bounds(P,P+FVector2D(Random.FRandRange(0,2400),Random.FRandRange(0,2400)));
            if(I<Regions.Num())Bounds=FBox2D(Regions[I].Max,Regions[I].Max); // Exact touching edge/corner.
            bool Expected=false;for(const auto& R:Regions)if(Bounds.Intersect(R)){Expected=true;break;}
            if(Index.Intersects(Bounds)!=Expected){AddError(TEXT("indexed union differs from original"));return false;}
            ++Compared;
        }
    }
    TArray<FVector2D> XY;TArray<int32> Triangles;
    for(int32 Y=0;Y<21;++Y)for(int32 X=0;X<21;++X)XY.Emplace(X*25.,Y*25.);
    for(int32 Y=0;Y<20;++Y)for(int32 X=0;X<20;++X)
    {const int32 A=Y*21+X;Triangles.Append({A,A+1,A+21,A+1,A+22,A+21});}
    FRaftSimSurfaceRefinement Reference,Candidate;Candidate.bIndexedRegions=true;
    for(int32 Frame=0;Frame<12;++Frame)
    {
        TArray<FBox2D> Regions={FBox2D(FVector2D(100+Frame,75),FVector2D(300,450)),
            FBox2D(FVector2D(275,0),FVector2D(425-Frame,300))};
        const auto Height=[&](const FVector2D& P)->float
        {for(const auto& R:Regions)if(R.IsInsideOrOn(P))return 13.f*FMath::Sin(P.X*.083+Frame*.03)*FMath::Cos(P.Y*.057);return 0.f;};
        FBox2D Detail(FVector2D(Frame*7.,20),FVector2D(Frame*7.+80,110));
        for(auto* Work:{&Reference,&Candidate})
            if(!Work->BuildAdaptive(XY,Triangles,Height,3,.5f,Regions,nullptr,true,true,&Detail,18,true))
            {AddError(TEXT("adaptive build failed"));return false;}
        TArray<FVector2D> A,B;Reference.Expand(XY,A);Candidate.Expand(XY,B);
        if(Reference.MidpointParents!=Candidate.MidpointParents || Reference.Triangles!=Candidate.Triangles ||
           Reference.TriangleOrigins!=Candidate.TriangleOrigins || A!=B)
        {AddError(TEXT("adaptive selection/topology differs"));return false;}
        for(auto& P:XY)P.Y+=.013;
    }
    AddInfo(FString::Printf(TEXT("Compared %d exact box-union queries and12 changing adaptive reconstructions"),Compared));
    return !HasAnyErrors();
}
#endif
