#include "Misc/AutomationTest.h"
#include "RaftSimSurfaceRefinement.h"
#include <limits>
#include <cmath>

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestAdjacentRangeTest,
    "RaftSim.M4.CrestAdjacentRange",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestAdjacentRangeTest::RunTest(const FString&)
{
    FRaftSimCrestRangeMemo Memo;int32 Calls=0;
    const FBox2D Box(FVector2D(-10,20),FVector2D(40,80));
    auto Value=[&](const FBox2D&){++Calls;return 7.f;};
    TestEqual(TEXT("First range"),Memo.Width(Box,Value),7.f);
    TestEqual(TEXT("Identical bounds reuse exact width"),Memo.Width(Box,Value),7.f);
    TestEqual(TEXT("Only one evaluation"),Calls,1);
    FBox2D Moved=Box;Moved.Max.X=std::nextafter(Moved.Max.X,std::numeric_limits<double>::infinity());
    Memo.Width(Moved,Value);TestEqual(TEXT("One representable coordinate change invalidates"),Calls,2);
    Memo.Width(Box,Value);TestEqual(TEXT("Cache holds only last box"),Calls,3);
    FRaftSimSurfaceRefinement Work[2];
    for(int32 Pass=0;Pass<48;++Pass)
    {
        TArray<FVector2D> XY;TArray<int32> Triangles;
        for(int32 Y=0;Y<7;++Y)for(int32 X=0;X<9;++X)XY.Emplace(X*100.+Pass*.17,Y*100.-Pass*.21);
        for(int32 Y=0;Y<6;++Y)for(int32 X=0;X<8;++X)
        {
            if((X+Y+Pass)%9==0)continue;const int32 I=Y*9+X;
            Triangles.Append({I,I+9,I+10,I,I+10,I+1});
        }
        if(Pass%2)for(int32 I=0;I<Triangles.Num();I+=3)Swap(Triangles[I+1],Triangles[I+2]);
        const float Amplitude=Pass%4 ? 4.f : .1f;
        const auto Height=[&](const FVector2D& P){return Amplitude*FMath::Sin(float(P.X*.02+P.Y*.01+Pass));};
        const FBox2D Detail(FVector2D(200,100),FVector2D(500,400));
        for(int32 Kind=0;Kind<2;++Kind)
        {
            auto& W=Work[Kind];W.ParallelBatchSize=Pass%3 ? 7 : 128;
            // Includes invalid bounds (which must fall through to sampling),
            // changing closures and a missing range function across builds.
            W.HeightRangeWidthCm=Pass%8==0 ? TFunction<float(const FBox2D&)>() :
                TFunction<float(const FBox2D&)>([&](const FBox2D&){return Pass%8==1 ?
                    std::numeric_limits<float>::quiet_NaN() : 2*Amplitude;});
            TestTrue(TEXT("Range-memo fixture builds"),W.BuildAdaptive(XY,Triangles,Height,3,.5f,{},nullptr,
                Pass%2==0,true,Pass%3 ? &Detail : nullptr,50.f,true,true,true,false,Kind==1));
        }
        TArray<FVector2D> A,B;Work[0].Expand(XY,A);Work[1].Expand(XY,B);
        TestTrue(TEXT("Every topology, owner and coordinate exact across moving/changing profiles"),
            Work[0].MidpointParents==Work[1].MidpointParents && Work[0].Triangles==Work[1].Triangles &&
            Work[0].TriangleOrigins==Work[1].TriangleOrigins && A==B);
    }
    return !HasAnyErrors();
}
#endif
