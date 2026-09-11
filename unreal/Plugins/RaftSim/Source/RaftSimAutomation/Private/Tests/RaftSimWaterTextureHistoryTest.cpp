#include "Misc/AutomationTest.h"
#include "RaftSimWaterTextureHistory.h"
#include "RaftSimDetailWaterGPU.h"
#include "RHICommandList.h"
#include "RHIGPUReadback.h"
#include "RenderingThread.h"
#include "HAL/PlatformProcess.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimWaterTextureHistoryTest,
    "RaftSim.WaterDetail.RenderedFrameHistoryGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FRaftSimWaterTextureHistoryTest::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Real SM5+ GPU required"));return false; }
    TArray<TSharedPtr<FRHIGPUBufferReadback,ESPMode::ThreadSafe>> Reads;
    for (int32 I=0;I<6;++I)Reads.Add(MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("WaterHistoryTest")));
    bool bOK=true,bRejectedAliasing=false,bRejectedSize=false;uint64 Frames=0;FString Error;
    ENQUEUE_RENDER_COMMAND(RaftSimWaterHistoryTest)([&](FRHICommandListImmediate& Cmd)
    {
        auto MakeTexture=[&](int32 Width)
        {
            return Cmd.CreateTexture(FRHITextureCreateDesc::Create2D(TEXT("WaterHistoryTest"),Width,8,PF_A32B32G32R32F)
                .SetFlags(ETextureCreateFlags::ShaderResource).SetInitialState(ERHIAccess::CopyDest));
        };
        auto Current=MakeTexture(2),Previous=MakeTexture(2),Wrong=MakeTexture(3);
        auto Upload=[&](float Height)
        {
            TArray<FVector4f> Values;Values.Init(FVector4f(Height,Height*2,Height*3,Height*4),16);
            Cmd.Transition(FRHITransitionInfo(Current,ERHIAccess::Unknown,ERHIAccess::CopyDest));
            Cmd.UpdateTexture2D(Current,0,FUpdateTextureRegion2D(0,0,0,0,2,8),2*sizeof(FVector4f),reinterpret_cast<const uint8*>(Values.GetData()));
            Cmd.Transition(FRHITransitionInfo(Current,ERHIAccess::CopyDest,ERHIAccess::SRVMask));
        };
        auto Sample=[&](int32 I)
        {
            const TArray<FVector4f> Queries={FVector4f(0.25f,0.25f,0,0)};
            bOK &= RaftSimValidateMacroSamplingGPU(Cmd,Previous,FIntPoint(2,2),Queries,Reads[I].Get(),Error);
        };
        FRaftSimWaterTextureHistory History;
        bRejectedAliasing=!History.Start(Cmd,Current,Current);
        bRejectedSize=!History.Start(Cmd,Current,Wrong);
        Upload(1);bOK &= History.Start(Cmd,Current,Previous);Sample(0); // Bootstrap.
        Upload(2);Sample(1); // Update must not replace last-rendered history.
        Upload(3);Sample(2); // Nor may a second update in that same frame.
        History.CaptureFrame(Cmd);Sample(3); // End of rendered frame -> 3.
        History.CaptureFrame(Cmd);Sample(4); // No simulation update -> still 3.
        Upload(7);History.ResetHistory(Cmd);Sample(5); // Lattice replacement.
        Frames=History.GetCapturedFrames();History.Stop();History.Stop();
    });
    FlushRenderingCommands();
    TestTrue(TEXT("reject aliased current/previous textures"),bRejectedAliasing);
    TestTrue(TEXT("reject mismatched history dimensions"),bRejectedSize);
    TestEqual(TEXT("reset is not counted as a rendered frame"),Frames,uint64(2));
    if (!TestTrue(TEXT("history copy/sample commands succeed"),bOK)) { AddError(Error);return false; }
    const double Deadline=FPlatformTime::Seconds()+10;
    auto Ready=[&]() { for (const auto& R:Reads)if (!R->IsReady())return false;return true; };
    while (!Ready() && FPlatformTime::Seconds()<Deadline)FPlatformProcess::Sleep(0.01f);
    if (!Ready()) { AddError(TEXT("History GPU readback timeout"));return false; }
    TArray<FVector4f> Actual;
    ENQUEUE_RENDER_COMMAND(RaftSimWaterHistoryRead)([&](FRHICommandListImmediate&)
    {
        for (auto& R:Reads)
        {
            Actual.Add(*static_cast<const FVector4f*>(R->Lock(sizeof(FVector4f))));R->Unlock();
        }
    });
    FlushRenderingCommands();
    const float Expected[]={1,1,1,3,3,7};float MaxError=0;bool bFinite=true;
    for (int32 I=0;I<6;++I)for (int32 K=0;K<4;++K)
    {
        bFinite &= FMath::IsFinite(Actual[I][K]);
        MaxError=FMath::Max(MaxError,FMath::Abs(Actual[I][K]-Expected[I]*(K+1)));
    }
    TestTrue(TEXT("previous-rendered state survives zero/multiple steps and explicit topology reset"),bFinite && MaxError<1.e-6f);
    AddInfo(FString::Printf(TEXT("Rendered-frame GPU history: 6 snapshots, max RGBA error %.9g; two frame captures, explicit reset, idempotent stop"),MaxError));
    return true;
}
#endif
