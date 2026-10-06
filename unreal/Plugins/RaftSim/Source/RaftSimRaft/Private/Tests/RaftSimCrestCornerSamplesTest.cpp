#include "Misc/AutomationTest.h"
#include "RaftSimSurfaceRefinement.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestCornerSamplesTest,"RaftSim.M4.CrestCornerSamples",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestCornerSamplesTest::RunTest(const FString&)
{
    TArray<FVector2D> XY;TArray<int32> Indices;
    constexpr int32 N=17;
    for(int32 Y=0;Y<N;++Y)for(int32 X=0;X<N;++X)
    {
        XY.Emplace(-544000.+100.*X,-360000.+100.*Y);
        if(X<N-1 && Y<N-1){const int32 I=Y*N+X;Indices.Append({I,I+N,I+1,I+1,I+N,I+N+1});}
    }
    FRaftSimSurfaceRefinement Shared,Original,Serial;
    for(int32 Frame=0;Frame<12;++Frame)
    {
        if(Frame==4)for(auto& P:XY)P+=FVector2D(.137,-.291);
        if(Frame==8)for(int32 T=0;T<Indices.Num();T+=3)Swap(Indices[T+1],Indices[T+2]);
        const FVector2D Center=XY[8*N+8]+FVector2D(Frame*13.1,-Frame*8.7);
        const TArray<FBox2D> Regions={FBox2D(Center-FVector2D(360,420),Center+FVector2D(360,420))};
        const FBox2D Detail(Center+FVector2D(250,-500),Center+FVector2D(650,100));
        const auto Height=[&](const FVector2D& P)
        {
            const FVector2D D=P-Center;
            if(FMath::Abs(D.X)>=360 || FMath::Abs(D.Y)>=420)return 0.f;
            return float((5.+Frame)*FMath::Cos(D.X/360*PI*.5)*FMath::Cos(D.Y/420*PI*.5));
        };
        const FBox2D* Window=Frame%3==0 ? nullptr : &Detail;
        if(!Shared.BuildAdaptive(XY,Indices,Height,3,.5f,Regions,nullptr,true,true,Window,25,true,true,true,true) ||
            !Original.BuildAdaptive(XY,Indices,Height,3,.5f,Regions,nullptr,true,true,Window,25,true,true,true,false) ||
            !Serial.BuildAdaptive(XY,Indices,Height,3,.5f,Regions,nullptr,false,false,Window,25))return false;
        TestTrue(TEXT("region skips and forced detail retain original exact topology and owners"),
            Shared.MidpointParents==Original.MidpointParents && Shared.Triangles==Original.Triangles &&
            Shared.TriangleOrigins==Original.TriangleOrigins && Shared.MidpointParents==Serial.MidpointParents &&
            Shared.Triangles==Serial.Triangles && Shared.TriangleOrigins==Serial.TriangleOrigins);
        TestTrue(TEXT("corner work is shared within the current build"),Shared.SharedCornerSamples>0 &&
            Shared.SharedCornerSamples<Shared.SharedCornerReads);
    }
    return !HasAnyErrors();
}
#endif
