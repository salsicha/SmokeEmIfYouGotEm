#include "RaftSimWaterFlowFrame.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimWetEdgeSweepTest,"RaftSim.P2.WetEdgeSweep",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimWetEdgeSweepTest::RunTest(const FString&)
{
    using namespace RaftSimWaterFlowFrame;
    int64 Compared=0;
    const auto Verify=[&](int32 Nx,int32 Ny,const TArray<uint8>& Wet,bool Brute)
    {
        const auto Queue=WetEdgeStepsReference(Nx,Ny,Wet),Sweep=WetEdgeStepsSweep(Nx,Ny,Wet);
        if(Queue!=Sweep){AddError(TEXT("queue/sweep distance mismatch"));return false;}
        if(WetEdgeSteps(Nx,Ny,Wet)!=Sweep || WetEdgeSteps(Nx,Ny,Wet,false)!=Queue)
        {AddError(TEXT("normal/default and retained control selection mismatch"));return false;}
        if(Brute)
        {
            // Independent nearest-seed geometry, no graph traversal or sweep.
            TArray<FIntPoint> Seeds;
            for(int32 Y=0;Y<Ny;++Y)for(int32 X=0;X<Nx;++X)
            {
                bool Seed=X==0 || Y==0 || X==Nx-1 || Y==Ny-1;
                for(int32 YY=FMath::Max(Y-1,0);YY<=FMath::Min(Y+1,Ny-1);++YY)
                    for(int32 XX=FMath::Max(X-1,0);XX<=FMath::Min(X+1,Nx-1);++XX)
                        Seed|=!Wet[YY*Nx+XX];
                if(Seed)Seeds.Emplace(X,Y);
            }
            for(int32 Y=0;Y<Ny;++Y)for(int32 X=0;X<Nx;++X)
            {
                int32 Best=MAX_int32;
                for(const auto& P:Seeds)Best=FMath::Min(Best,FMath::Max(FMath::Abs(P.X-X),FMath::Abs(P.Y-Y)));
                if(Sweep[Y*Nx+X]!=Best){AddError(TEXT("independent Chebyshev seed-distance mismatch"));return false;}
            }
        }
        Compared+=Wet.Num();return true;
    };
    for(int32 Nx=1;Nx<=4;++Nx)for(int32 Ny=1;Ny<=4;++Ny)
        for(uint32 Mask=0;Mask<(1u<<(Nx*Ny));++Mask)
        {
            TArray<uint8> Wet;Wet.SetNumUninitialized(Nx*Ny);
            for(int32 I=0;I<Wet.Num();++I)Wet[I]=(Mask>>I)&1;
            if(!Verify(Nx,Ny,Wet,true))return false;
        }
    FRandomStream Random(20260915);
    for(int32 Frame=0;Frame<80;++Frame)
    {
        const int32 Nx=Frame%2 ? 47 : 31,Ny=Frame%3 ? 29 : 43;
        TArray<uint8> Wet;Wet.Init(1,Nx*Ny);
        for(int32 I=0;I<Wet.Num();++I)
            if(Frame%4==1 || (Frame%4>=2 && Random.FRand()<.07f))Wet[I]=0;
        // Moving hole and diagonal dry line, with each call rebuilding seeds.
        if(Frame%4==0)Wet[(Frame%Ny)*Nx+Frame%Nx]=0;
        if(!Verify(Nx,Ny,Wet,true))return false;
    }
    TArray<uint8> Wide;Wide.Init(1,512*152);
    if(!Verify(512,152,Wide,false))return false;
    Wide.Init(0,512*152);
    if(!Verify(512,152,Wide,false))return false;
    TestTrue(TEXT("empty grids remain empty"),WetEdgeStepsSweep(0,0,{}).IsEmpty());
    AddInfo(FString::Printf(TEXT("%lld exact integer distances; exhaustive small masks, independent nearest-seed geometry, changing asymmetric grids and full-size extremes"),Compared));
    return !HasAnyErrors();
}
#endif
