#include "RaftSimDetailPresentationFrame.h"
#include "RaftSimDetailWaterGPU.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include "RHICommandList.h"
#include "Misc/AutomationTest.h"
#include "HAL/PlatformProcess.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRegisteredFoamClockTest,
    "RaftSim.WaterDetail.RegisteredFoamClockGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimRegisteredFoamClockTest::RunTest(const FString&)
{
    if(GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    {AddError(TEXT("A real SM5 GPU is required"));return false;}
    constexpr int32 N=33;
    const auto Split=[](double T){const float H=float(T);return FVector2f(H,float(T-double(H)));};
    struct FCase {double GPU,CPU;float Marker;uint32 Mode;float Origin;};
    const FCase Cases[]={
        {1.99,2.01,3,1,1234}, {1.99,130.125,3,1,1234}, // held GPU, advancing CPU
        {2.01,2.03,3,1,1242}, // completed next frame with moved registration
        {100000000.99,100000001.01,3,1,1234}, // phase survives coarse float high part
        {1.99,2.01,2,1,1234}, // GPU-owned timestamp
        {1.99,2.01,1,1,1234}, // old repeated registration is NOT a timestamp
        {1.99,2.01,3,2,1234}}; // disabled detail uses CPU only
    float MaxError=0;
    for(const auto& C:Cases)
    {
        FRaftSimDetailPresentationFrame Frame;Frame.Size=FIntPoint(N,N);Frame.Sequence=1;
        Frame.SimulationSeconds=C.GPU;Frame.ElapsedSeconds=999;
        Frame.Pixels.Init(FVector4f(.01f,.02f,.03f,.4f),N*(N+1));
        Frame.Pixels[N*N]=FVector4f(C.Origin,-6789,.5f,1);
        TestTrue(TEXT("host clock inserts without changing data"),Frame.WriteHostClockMetadata());
        for(int32 I=0;I<N*N;++I)
            if(Frame.Pixels[I]!=FVector4f(.01f,.02f,.03f,.4f)){AddError(TEXT("Clock changed water data"));return false;}
        auto Bad=Frame;Bad.SimulationSeconds+=.1;
        TestFalse(TEXT("timestamp and captured host payload must agree"),Bad.Validate());
        Frame.Pixels[N*N+1].W=C.Marker;
        if(C.Marker==2)
        {
            TestTrue(TEXT("GPU clock adopted"),Frame.AdoptGPUClock());
            TestFalse(TEXT("host cannot overwrite GPU clock"),Frame.WriteHostClockMetadata());
        }
        TArray<FVector4f> Queries;TArray<float> Expected;
        const auto CPU=Split(C.CPU);
        for(float X:{-1.f,0.f,2.f,4.f,8.f,14.f,16.f,17.f})
        {
            Queries.Add(FVector4f(C.Origin+X,-6781,CPU.X,CPU.Y));
            const double Edge=FMath::Min(double(X),16.-X);
            const double T=FMath::Clamp(Edge/4.,0.,1.);
            const double Weight=(C.Marker==2 || C.Marker==3) && C.Mode==1 ? T*T*(3.-2.*T):0.;
            const double Time=C.CPU+Weight*(C.GPU-C.CPU);
            Expected.Add(float(Time-FMath::FloorToDouble(Time)));
        }
        auto Read=MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("RegisteredFoamClock"));
        bool OK=false;FString Error;
        ENQUEUE_RENDER_COMMAND(RaftSimFoamClockFixture)([&](FRHICommandListImmediate& Cmd)
        {
            auto Texture=Cmd.CreateTexture(FRHITextureCreateDesc::Create2D(TEXT("FoamClockFrame"),N,N+1,PF_A32B32G32R32F)
                .SetFlags(ETextureCreateFlags::ShaderResource).SetInitialState(ERHIAccess::CopyDest));
            Cmd.UpdateTexture2D(Texture,0,FUpdateTextureRegion2D(0,0,0,0,N,N+1),N*sizeof(FVector4f),reinterpret_cast<const uint8*>(Frame.Pixels.GetData()));
            Cmd.Transition(FRHITransitionInfo(Texture,ERHIAccess::CopyDest,ERHIAccess::SRVMask));
            OK=RaftSimValidateRegisteredDetailSamplingGPU(Cmd,Texture,Queries,&Read.Get(),Error,C.Mode);
        });
        FlushRenderingCommands();
        if(!OK){AddError(Error);return false;}
        const double Deadline=FPlatformTime::Seconds()+5;
        while(!Read->IsReady() && FPlatformTime::Seconds()<Deadline)FPlatformProcess::Sleep(.001f);
        if(!TestTrue(TEXT("GPU clock result ready"),Read->IsReady()))return false;
        bool ReadOK=false;
        ENQUEUE_RENDER_COMMAND(RaftSimFoamClockCompare)([&](FRHICommandListImmediate&)
        {
            const auto* Values=static_cast<const FVector4f*>(Read->Lock(Queries.Num()*sizeof(FVector4f)));
            if(!Values)return;
            ReadOK=true;
            for(int32 I=0;I<Queries.Num();++I)
            {
                const float Difference=FMath::Abs(Values[I].X-Expected[I]);
                if(FMath::Min(Difference,FMath::Abs(1.f-Difference))>=2.e-5f)
                    AddInfo(FString::Printf(TEXT("Clock mismatch gpu=%.12g cpu=%.12g mode=%u marker=%.0f x=%.3f actual=%.9g expected=%.9g"),C.GPU,C.CPU,C.Mode,C.Marker,Queries[I].X-C.Origin,Values[I].X,Expected[I]));
                if(!FMath::IsFinite(Difference))ReadOK=false;
                MaxError=FMath::Max(MaxError,FMath::Min(Difference,FMath::Abs(1.f-Difference)));
            }
            Read->Unlock();
        });
        FlushRenderingCommands();
        TestTrue(TEXT("finite registered phase matches full-double clock reference"),ReadOK && MaxError<2.e-5f);
    }
    AddInfo(FString::Printf(TEXT("56 actual GPU clock queries: held/completed/moved frame, boundary wrap, disabled/legacy/GPU clocks, 100-million-second phase; max circular error %.9g"),MaxError));
    return !HasAnyErrors();
}
#endif
