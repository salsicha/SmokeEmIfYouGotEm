#include "Misc/AutomationTest.h"
#include "RaftSimDetailWaterGPU.h"
#include "RHIGPUReadback.h"
#include "RHICommandList.h"
#include "RenderingThread.h"
#include "HAL/PlatformProcess.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimFineSpatialWaveTest,
    "RaftSim.WaterDetail.FineSpatialWaveGPU",EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FRaftSimFineSpatialWaveTest::RunTest(const FString&)
{
    double Errors[2]={},Amplitudes[2]={};
    for (int32 Resolution=0;Resolution<2;++Resolution)
    {
        FRaftSimDetailWaterGrid G;
        G.Size=FIntPoint(128<<Resolution,16<<Resolution);
        G.CellMeters=0.5f/(1<<Resolution);G.StepSeconds=1.0f/240;
        G.bPeriodic=true;G.bSecondOrder=true;
        G.MomentumDampingPerSecond=G.FoamSourcePerSecond=G.FoamDecayPerSecond=0;
        TArray<FVector4f> Flow,Initial,Result;
        Flow.Init(FVector4f(1,1,0,0),G.Size.X*G.Size.Y);Initial.SetNumUninitialized(Flow.Num());
        const double Speed=FMath::Sqrt(9.81),WaveNumber=2*PI/4;
        for (int32 I=0;I<Initial.Num();++I)
        {
            const double Height=.03*FMath::Sin(WaveNumber*(I%G.Size.X)*G.CellMeters);
            Initial[I]=FVector4f(Height,Speed*Height,0,0);
        }
        auto Sim=MakeShared<FRaftSimDetailWaterGPU,ESPMode::ThreadSafe>();
        auto Read=MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("FineSpatialWave"));
        bool Ok=false;FString Error;
        ENQUEUE_RENDER_COMMAND(RaftSimFineWaveFixture)([&](FRHICommandListImmediate& Cmd)
        { Ok=Sim->Advance(Cmd,G,Flow,240,&Initial,&Read.Get(),Error); });
        FlushRenderingCommands();
        if (!TestTrue(TEXT("spatial-resolution wave fixture dispatches"),Ok)) {AddError(Error);return false;}
        const double Deadline=FPlatformTime::Seconds()+10;
        while (!Read->IsReady() && FPlatformTime::Seconds()<Deadline)FPlatformProcess::Sleep(.01f);
        if (!TestTrue(TEXT("spatial-resolution GPU readback ready"),Read->IsReady()))return false;
        ENQUEUE_RENDER_COMMAND(RaftSimFineWaveRead)([&](FRHICommandListImmediate&)
        {
            Result.SetNumUninitialized(Initial.Num());
            FMemory::Memcpy(Result.GetData(),Read->Lock(Result.Num()*sizeof(FVector4f)),Result.Num()*sizeof(FVector4f));Read->Unlock();
            Sim->Reset();
        });
        FlushRenderingCommands();
        double SquaredError=0,Sum=0,SinCoefficient=0,CosCoefficient=0;
        bool Finite=true;
        for (int32 I=0;I<Result.Num();++I)
        {
            const double Phase=WaveNumber*((I%G.Size.X)*G.CellMeters-(1+Speed)*240*double(G.StepSeconds));
            Finite &= FMath::IsFinite(Result[I].X) && FMath::IsFinite(Result[I].Y) && Result[I].W==0;
            SquaredError+=FMath::Square(Result[I].X-.03*FMath::Sin(Phase));Sum+=Result[I].X;
            SinCoefficient+=Result[I].X*FMath::Sin(Phase);CosCoefficient+=Result[I].X*FMath::Cos(Phase);
        }
        TestTrue(TEXT("finite wave, no invented foam or mean water-level drift"),Finite && FMath::Abs(Sum/Result.Num())<1.e-7);
        Errors[Resolution]=FMath::Sqrt(SquaredError/Result.Num());
        Amplitudes[Resolution]=2*FMath::Sqrt(SinCoefficient*SinCoefficient+CosCoefficient*CosCoefficient)/Result.Num();
    }
    TestTrue(TEXT("halving cell spacing materially reduces same-wave error"),Errors[1]<.65*Errors[0]);
    TestTrue(TEXT("fine wave retains more of the original amplitude without gain"),
        Amplitudes[1]>Amplitudes[0] && Amplitudes[1]<=.03001);
    AddInfo(FString::Printf(TEXT("same 4m wave after 1s: coarse_rms=%.9gm fine_rms=%.9gm coarse_amplitude=%.9gm fine_amplitude=%.9gm; physical forcing unchanged"),
        Errors[0],Errors[1],Amplitudes[0],Amplitudes[1]));
    return true;
}
#endif
