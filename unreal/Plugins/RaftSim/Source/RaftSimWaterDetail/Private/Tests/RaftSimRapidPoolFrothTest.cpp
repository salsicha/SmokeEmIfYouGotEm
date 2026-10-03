#include "RaftSimDetailWaterGPU.h"
#include "Misc/AutomationTest.h"
#include "RHIGPUReadback.h"
#include "RenderingThread.h"
#include "HAL/PlatformProcess.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRapidPoolFrothGPUTest,
    "RaftSim.WaterDetail.RapidPoolFrothGPU",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimRapidPoolFrothGPUTest::RunTest(const FString&)
{
    if(GUsingNullRHI){AddError(TEXT("Actual GPU required"));return false;}
    FRaftSimDetailWaterGrid Grid;Grid.Size=FIntPoint(8,8);Grid.CellMeters=.5f;
    Grid.StepSeconds=1.f/120.f;Grid.bPeriodic=true;Grid.bSecondOrder=true;
    TArray<FVector4f> Pool,Rapid,Initial;
    for(int32 I=0;I<64;++I)
    {
        Pool.Emplace(1.f,1.f,0.f,0.f);Rapid.Emplace(1.f,1.f,0.f,1.f);
        Initial.Emplace(.001f*FMath::Cos((I%8)*2.f*PI/8.f),0.f,0.f,1.f);
    }
    auto Invalid=Grid;Invalid.PoolFoamDecayPerSecond=-1.f;FString Error;
    TestFalse(TEXT("invalid pool release cannot enter GPU"),Invalid.Validate(Pool,Error));
    TArray<TSharedPtr<FRHIGPUBufferReadback,ESPMode::ThreadSafe>> Reads;
    for(int32 I=0;I<4;++I)Reads.Add(MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("RapidPoolFroth")));
    bool Ran=true;
    ENQUEUE_RENDER_COMMAND(RaftSimRapidPoolFroth)([&](FRHICommandListImmediate& Cmd)
    {
        for(int32 I=0;I<4;++I)
        {
            auto G=Grid;G.PoolFoamDecayPerSecond=(I%2)?8.f:0.f;
            FRaftSimDetailWaterGPU Simulation;
            Ran &= Simulation.Advance(Cmd,G,I<2?Pool:Rapid,120,&Initial,Reads[I].Get(),Error);
        }
    });
    FlushRenderingCommands();
    if(!TestTrue(TEXT("four actual shader integrations complete"),Ran)){AddError(Error);return false;}
    const double Deadline=FPlatformTime::Seconds()+10.;bool Ready=false;
    do{Ready=true;for(auto& R:Reads)Ready &= R->IsReady();if(!Ready)FPlatformProcess::Sleep(.001f);}
    while(!Ready && FPlatformTime::Seconds()<Deadline);
    if(!TestTrue(TEXT("native froth readbacks complete"),Ready))return false;
    TArray<TArray<FVector4f>> Results;
    ENQUEUE_RENDER_COMMAND(RaftSimRapidPoolFrothRead)([&](FRHICommandListImmediate&)
    {
        for(auto& Read:Reads)
        {
            const auto* Data=static_cast<const FVector4f*>(Read->Lock(64*sizeof(FVector4f)));
            TArray<FVector4f> Result;Result.Append(Data,64);Results.Add(MoveTemp(Result));Read->Unlock();
        }
    });
    FlushRenderingCommands();
    float PoolMax=0.f,LiquidDifference=0.f,RapidDifference=0.f;
    for(int32 I=0;I<64;++I)
    {
        TestTrue(TEXT("release keeps finite nonnegative froth"),FMath::IsFinite(Results[1][I].W) && Results[1][I].W>=0.f);
        PoolMax=FMath::Max(PoolMax,Results[1][I].W);
        for(int32 K=0;K<3;++K)
            LiquidDifference=FMath::Max(LiquidDifference,FMath::Abs(Results[0][I][K]-Results[1][I][K]));
        for(int32 K=0;K<4;++K)
            RapidDifference=FMath::Max(RapidDifference,FMath::Abs(Results[2][I][K]-Results[3][I][K]));
    }
    TestTrue(TEXT("rapid exit froth vanishes within one second"),PoolMax<.0004f);
    TestEqual(TEXT("pool bubbles do not change liquid motion"),LiquidDifference,0.f);
    TestEqual(TEXT("active crashing water remains unchanged"),RapidDifference,0.f);
    AddInfo(FString::Printf(TEXT("pool_froth_after_1s=%.9g liquid_error=%.9g active_rapid_error=%.9g"),PoolMax,LiquidDifference,RapidDifference));
    return true;
}
#endif
