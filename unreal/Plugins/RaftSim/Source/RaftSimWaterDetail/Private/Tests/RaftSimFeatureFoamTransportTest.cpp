#include "RaftSimDetailWaterGPU.h"
#include "Misc/AutomationTest.h"
#include "RHIGPUReadback.h"
#include "RenderingThread.h"
#include "HAL/PlatformProcess.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimFeatureFoamTransportTest,
    "RaftSim.WaterDetail.FeatureFoamTransportGPU",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimFeatureFoamTransportTest::RunTest(const FString&)
{
    if(GUsingNullRHI){AddError(TEXT("Actual GPU required"));return false;}
    FRaftSimDetailWaterGrid Grid;Grid.Size=FIntPoint(32,16);Grid.CellMeters=.5f;
    Grid.StepSeconds=1.f/120.f;Grid.FoamDecayPerSecond=0;Grid.FoamSourcePerSecond=0;
    Grid.TurbulentHeadMeters=0;Grid.MomentumDampingPerSecond=0;
    Grid.bPeriodic=true;Grid.bSecondOrder=true;Grid.bFiniteDepthDispersion=true;
    TArray<FVector4f> Flow,FoamFlow,Initial;
    for(int32 Y=0;Y<Grid.Size.Y;++Y)for(int32 X=0;X<Grid.Size.X;++X)
    {
        Flow.Emplace(1.f,1.f,0.f,0.f);FoamFlow.Emplace(1.f,-1.f,0.f,0.f);
        const float Density=FMath::Exp(-FMath::Square((X-16.f)/2.f)-FMath::Square((Y-8.f)/2.f));
        Initial.Emplace(.01f*FMath::Cos(X*2.f*PI/Grid.Size.X),0.f,0.f,Density);
    }
    TArray<TSharedPtr<FRHIGPUBufferReadback,ESPMode::ThreadSafe>> Reads;
    for(int32 I=0;I<3;++I)Reads.Add(MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("FeatureFoamTransport")));
    bool Ran=true,RejectedOwnership=false;FString Error;
    ENQUEUE_RENDER_COMMAND(RaftSimFeatureFoamTransportTest)([&](FRHICommandListImmediate& Cmd)
    {
        for(int32 I=0;I<3;++I)
        {
            FRaftSimDetailWaterGPU Simulation;
            const auto* Transport=I==0?nullptr:(I==1?&Flow:&FoamFlow);
            Ran &= Simulation.Advance(Cmd,Grid,Flow,120,&Initial,Reads[I].Get(),Error,nullptr,nullptr,Transport);
        }
        FRaftSimDetailWaterGPU Invalid;auto Wrong=FoamFlow;Wrong[0].X=0.f;
        RejectedOwnership=!Invalid.Advance(Cmd,Grid,Flow,1,&Initial,nullptr,Error,nullptr,nullptr,&Wrong);
    });
    FlushRenderingCommands();
    if(!TestTrue(TEXT("Three native GPU batches run"),Ran)){AddError(Error);return false;}
    TestTrue(TEXT("Transport cannot change wet/depth ownership"),RejectedOwnership);
    const double Deadline=FPlatformTime::Seconds()+10.;bool Ready=false;
    do{Ready=true;for(auto& R:Reads)Ready &= R->IsReady();if(!Ready)FPlatformProcess::Sleep(.001f);}while(!Ready && FPlatformTime::Seconds()<Deadline);
    if(!TestTrue(TEXT("All actual GPU readbacks complete"),Ready))return false;
    double InitialMass=0,InitialMoment=0;
    for(int32 I=0;I<Initial.Num();++I){InitialMass+=Initial[I].W;InitialMoment+=Initial[I].W*(I%Grid.Size.X)*Grid.CellMeters;}
    TArray<TArray<FVector4f>> Results;
    ENQUEUE_RENDER_COMMAND(RaftSimFeatureFoamTransportReadback)([&](FRHICommandListImmediate&)
    {
        for(auto& Read:Reads)
        {
            const auto* Data=static_cast<const FVector4f*>(Read->Lock(Initial.Num()*sizeof(FVector4f)));
            TArray<FVector4f> Result;Result.Append(Data,Initial.Num());Results.Add(MoveTemp(Result));Read->Unlock();
        }
    });
    FlushRenderingCommands();
    double LiquidDifference=0,DefaultDifference=0;
    for(int32 I=0;I<Initial.Num();++I)
    {
        for(int32 K=0;K<3;++K)LiquidDifference=FMath::Max(LiquidDifference,double(FMath::Abs(Results[0][I][K]-Results[2][I][K])));
        for(int32 K=0;K<4;++K)DefaultDifference=FMath::Max(DefaultDifference,double(FMath::Abs(Results[0][I][K]-Results[1][I][K])));
    }
    TestTrue(TEXT("Omitted versus identical explicit transport preserves all state"),DefaultDifference==0);
    TestTrue(TEXT("Reversing foam leaves height/momentum unchanged"),LiquidDifference==0);
    for(int32 Run=0;Run<3;++Run)
    {
        double Mass=0,Moment=0;bool Nonnegative=true;
        for(int32 I=0;I<Initial.Num();++I){const auto W=Results[Run][I].W;Mass+=W;Moment+=W*(I%Grid.Size.X)*Grid.CellMeters;Nonnegative &= FMath::IsFinite(W) && W>=0;}
        const double Travel=Moment/Mass-InitialMoment/InitialMass;
        TestTrue(TEXT("Conservative foam mass"),FMath::Abs(Mass-InitialMass)<InitialMass*1e-5);
        TestTrue(TEXT("Nonnegative un-clipped density"),Nonnegative);
        TestTrue(TEXT("Centroid follows supplied foam velocity, not bulk"),FMath::Abs(Travel-(Run==2?-1.:1.))<.03);
        AddInfo(FString::Printf(TEXT("run=%d travel_m=%.9g mass_error=%.9g liquid_error=%.9g"),Run,Travel,Mass-InitialMass,LiquidDifference));
    }
    return true;
}
#endif
