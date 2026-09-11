#include "Misc/AutomationTest.h"
#include "RaftSimDetailWaterGPU.h"
#include "RHIGPUReadback.h"
#include "RHICommandList.h"
#include "RenderingThread.h"
#include "HAL/PlatformProcess.h"

#if WITH_AUTOMATION_TESTS
namespace
{
bool ReadActivity(const FRaftSimDetailWaterGrid& Grid,const TArray<FVector4f>& Flow,
    const TArray<float>& Initial,int32 Steps,TArray<float>& Result,TArray<FVector4f>& Waves,
    FString& Error,bool bSplit=false,const TArray<FVector4f>* SecondFlow=nullptr)
{
    auto Sim=MakeShared<FRaftSimDetailWaterGPU,ESPMode::ThreadSafe>();
    auto Read=MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("ActivityFixture"));
    auto WaveRead=MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("ActivityWaveFixture"));
    bool Ok=false,RejectMode=false,RejectReseed=false;
    ENQUEUE_RENDER_COMMAND(RaftSimActivityFixture)([&](FRHICommandListImmediate& Cmd)
    {
        const bool Split=bSplit || SecondFlow;
        Ok=Split ? Sim->Advance(Cmd,Grid,Flow,Steps/2,nullptr,nullptr,Error,&Initial) &&
            Sim->Advance(Cmd,Grid,SecondFlow ? *SecondFlow : Flow,Steps-Steps/2,nullptr,&WaveRead.Get(),Error,nullptr,&Read.Get()) :
            Sim->Advance(Cmd,Grid,Flow,Steps,nullptr,&WaveRead.Get(),Error,&Initial,&Read.Get());
        auto Changed=Grid;Changed.bActivityMemory=false;
        FString Rejected;
        RejectMode=!Sim->Advance(Cmd,Changed,Flow,1,nullptr,nullptr,Rejected);
        RejectReseed=!Sim->Advance(Cmd,Grid,Flow,1,nullptr,nullptr,Rejected,&Initial);
    });
    FlushRenderingCommands();
    if (!Ok || !RejectMode || !RejectReseed)return false;
    const double Deadline=FPlatformTime::Seconds()+10;
    while ((!Read->IsReady() || !WaveRead->IsReady()) && FPlatformTime::Seconds()<Deadline)FPlatformProcess::Sleep(.01f);
    if (!Read->IsReady() || !WaveRead->IsReady()) { Error=TEXT("Activity GPU readback timeout");return false; }
    ENQUEUE_RENDER_COMMAND(RaftSimActivityRead)([&](FRHICommandListImmediate&)
    {
        Result.SetNumUninitialized(Initial.Num());Waves.SetNumUninitialized(Initial.Num());
        FMemory::Memcpy(Result.GetData(),Read->Lock(Initial.Num()*sizeof(float)),Initial.Num()*sizeof(float));Read->Unlock();
        FMemory::Memcpy(Waves.GetData(),WaveRead->Lock(Initial.Num()*sizeof(FVector4f)),Initial.Num()*sizeof(FVector4f));WaveRead->Unlock();
        Sim->Reset();
    });
    FlushRenderingCommands();return true;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimActivityMemoryTest,
    "RaftSim.WaterDetail.ActivityMemoryGPU",EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FRaftSimActivityMemoryTest::RunTest(const FString&)
{
    FRaftSimDetailWaterGrid G;G.Size=FIntPoint(64,32);G.CellMeters=.5f;G.StepSeconds=1.0f/120;
    G.bPeriodic=true;G.bSecondOrder=true;G.bActivityMemory=true;
    G.ActivitySourcePerSecond=G.ActivityDecayPerSecond=0;
    TArray<FVector4f> Flow,Waves,SplitWaves;Flow.Init(FVector4f(1,2,0,0),2048);
    TArray<float> Initial,Result,Split;Initial.SetNumUninitialized(2048);
    double Mass0=0,Center0=0;
    for (int32 Y=0;Y<32;++Y)for (int32 X=0;X<64;++X)
    {
        const float A=.5f*FMath::Exp(-FMath::Square((X*.5f-10)/1.3f));
        Initial[Y*64+X]=A;Mass0+=A;Center0+=A*X*.5;
    }
    FString Error;
    if (!TestTrue(TEXT("advected activity fixture dispatches"),ReadActivity(G,Flow,Initial,120,Result,Waves,Error))) { AddError(Error);return false; }
    double Mass=0,Center=0;float Minimum=1,Maximum=0;
    for (int32 I=0;I<Result.Num();++I)
    { Mass+=Result[I];Center+=Result[I]*(I%64)*.5;Minimum=FMath::Min(Minimum,Result[I]);Maximum=FMath::Max(Maximum,Result[I]); }
    TestTrue(TEXT("uniform-current centroid follows 2m/s not wave speed"),FMath::Abs(Center/Mass-Center0/Mass0-2)<.002);
    TestTrue(TEXT("uniform-current activity integral retained"),FMath::Abs(Mass/Mass0-1)<1e-5);
    TestTrue(TEXT("no clipping needed for bounded advection"),Minimum>=-1e-7f && Maximum<=.500001f);
    if (!TestTrue(TEXT("split graph dispatches"),ReadActivity(G,Flow,Initial,120,Split,SplitWaves,Error,true)))return false;
    TestTrue(TEXT("persistent activity identical across graph batching"),FMemory::Memcmp(Result.GetData(),Split.GetData(),Result.Num()*sizeof(float))==0);
    TestTrue(TEXT("wave state identical across graph batching"),FMemory::Memcmp(Waves.GetData(),SplitWaves.GetData(),Waves.Num()*sizeof(FVector4f))==0);

    // Constant intensive activity must not pile up in convergent mean flow.
    Initial.Init(.4f,2048);
    for (int32 Y=0;Y<32;++Y)for (int32 X=0;X<64;++X)
        Flow[Y*64+X]=FVector4f(.2f+.01f*X,2*FMath::Sin(X*.1f),FMath::Cos(Y*.2f),0);
    Flow[10*64+10]=FVector4f(0,0,0,0);
    if (!TestTrue(TEXT("compression/dry fixture dispatches"),ReadActivity(G,Flow,Initial,120,Result,Waves,Error)))return false;
    float ConstantError=0;
    for (int32 I=0;I<Result.Num();++I)ConstantError=FMath::Max(ConstantError,FMath::Abs(Result[I]-(Flow[I].X>.01f ? .4f : 0)));
    TestTrue(TEXT("compression preserves intensive activity, dry cells zero"),ConstantError<1e-6f);

    Flow.Init(FVector4f(1,0,0,.8f),2048);Initial.Init(.2f,2048);
    G.ActivitySourcePerSecond=1;G.ActivityDecayPerSecond=.5f;
    TArray<FVector4f> Off;Off.Init(FVector4f(1,0,0,0),2048);
    if (!TestTrue(TEXT("source then decay across persistent batches"),ReadActivity(G,Flow,Initial,120,Result,Waves,Error,false,&Off)))return false;
    const double Half=60*double(G.StepSeconds),Equilibrium=.8/1.3;
    const double Expected=(.2*FMath::Exp(-1.3*Half)+Equilibrium*(1-FMath::Exp(-1.3*Half)))*FMath::Exp(-.5*Half);
    const double SourceDecayError=FMath::Abs(Result[100]-Expected);
    TestTrue(TEXT("activity survives source removal with independent exact decay"),SourceDecayError<1e-5);

    G.ActivitySourcePerSecond=G.ActivityDecayPerSecond=0;G.TurbulentHeadMeters=.06f;Initial.Init(1,2048);
    if (!TestTrue(TEXT("memory alone drives bounded pressure perturbation"),ReadActivity(G,Off,Initial,120,Result,Waves,Error)))return false;
    float MaxHeight=0,MaxFoam=0;
    for (const FVector4f& S:Waves) { MaxHeight=FMath::Max(MaxHeight,FMath::Abs(S.X));MaxFoam=FMath::Max(MaxFoam,FMath::Abs(S.W)); }
    TestTrue(TEXT("actual pressure-generated relief persists without local entrainment"),MaxHeight>.001f && MaxHeight<.2f);
    TestEqual(TEXT("activity is not a second foam source"),MaxFoam,0.0f);
    G.ActivitySourcePerSecond=-1;
    TestFalse(TEXT("negative activity rate rejected"),G.Validate(Off,Error));
    AddInfo(FString::Printf(TEXT("activity travel=%.9fm integral_ratio=%.9f range=[%.9f,%.9f] constant_error=%.9g source_decay_error=%.9g pressure_height=%.9gm"),
        Center/Mass-Center0/Mass0,Mass/Mass0,Minimum,Maximum,ConstantError,SourceDecayError,MaxHeight));
    return true;
}
#endif
