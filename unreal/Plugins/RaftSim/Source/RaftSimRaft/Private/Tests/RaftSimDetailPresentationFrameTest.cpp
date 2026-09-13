#include "RaftSimDetailPresentationFrame.h"
#include "../RaftSimDetailFrameReadback.h"
#include "RaftSimDetailWaterGPU.h"
#include "RenderingThread.h"
#include "Misc/AutomationTest.h"
#include "HAL/PlatformProcess.h"
#include <limits>

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimDetailPresentationFrameTest,
    "RaftSim.WaterDetail.CompletedFrameContactGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimDetailPresentationFrameTest::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("A real SM5 GPU is required"));return false; }
    constexpr int32 Nx=17,Ny=13;
    auto Expected=MakeShared<FRaftSimDetailPresentationFrame,ESPMode::ThreadSafe>();
    Expected->Size=FIntPoint(Nx,Ny);Expected->Sequence=2;Expected->ElapsedSeconds=2;Expected->SimulationSeconds=1.99;
    Expected->Pixels.Init(FVector4f(0,0,0,0),Nx*(Ny+1));
    for (int32 Y=0;Y<Ny;++Y) for (int32 X=0;X<Nx;++X)
        Expected->Pixels[Y*Nx+X]=FVector4f(.04f*FMath::Sin(X*.31f)*FMath::Cos(Y*.43f),X*.003f,Y*-.005f,(X+Y)*.02f);
    Expected->Pixels[Nx*Ny]=FVector4f(-5439,3606,.5f,1);
    auto Mailbox=MakeShared<FRaftSimDetailFrameMailbox,ESPMode::ThreadSafe>();
    auto Slot=MakeShared<FRaftSimDetailFrameReadback,ESPMode::ThreadSafe>();
    FTextureRHIRef Candidate;
    ENQUEUE_RENDER_COMMAND(RaftSimContactFrameCopy)([&](FRHICommandListImmediate& Cmd)
    {
        Candidate=Cmd.CreateTexture(FRHITextureCreateDesc::Create2D(TEXT("ContactCandidate"),Nx,Ny+1,PF_A32B32G32R32F)
            .SetFlags(ETextureCreateFlags::ShaderResource).SetInitialState(ERHIAccess::CopyDest));
        Cmd.UpdateTexture2D(Candidate,0,FUpdateTextureRegion2D(0,0,0,0,Nx,Ny+1),Nx*sizeof(FVector4f),reinterpret_cast<const uint8*>(Expected->Pixels.GetData()));
        Cmd.Transition(FRHITransitionInfo(Candidate,ERHIAccess::CopyDest,ERHIAccess::SRVMask));
        Slot->Enqueue(Cmd,Candidate,Expected->Size,Expected->Sequence,Expected->ElapsedSeconds,Expected->SimulationSeconds);
        // Simulation may overwrite its candidate while the queued copy and
        // the currently presented frame retain independent ownership.
        auto NewPixels=Expected->Pixels;NewPixels[Nx*Ny].X+=8;NewPixels[20].X+=.07f;
        Cmd.Transition(FRHITransitionInfo(Candidate,ERHIAccess::SRVMask,ERHIAccess::CopyDest));
        Cmd.UpdateTexture2D(Candidate,0,FUpdateTextureRegion2D(0,0,0,0,Nx,Ny+1),Nx*sizeof(FVector4f),reinterpret_cast<const uint8*>(NewPixels.GetData()));
        Cmd.Transition(FRHITransitionInfo(Candidate,ERHIAccess::CopyDest,ERHIAccess::SRVMask));
    });
    FlushRenderingCommands();
    TSharedPtr<const FRaftSimDetailPresentationFrame,ESPMode::ThreadSafe> Frame;
    bool PollOK=true;
    const double Deadline=FPlatformTime::Seconds()+5;
    while (!Frame && FPlatformTime::Seconds()<Deadline)
    {
        ENQUEUE_RENDER_COMMAND(RaftSimContactFramePoll)([&](FRHICommandListImmediate&) { PollOK=Slot->Poll(*Mailbox); });
        FlushRenderingCommands();Frame=Mailbox->TakeLatest();
        if (!Frame) FPlatformProcess::Sleep(.001f); // Diagnostic fixture only, never runtime.
    }
    if (!TestTrue(TEXT("production nonblocking slot returns completed registered data"),PollOK && Frame.IsValid()))return false;
    TestTrue(TEXT("padded texture rows, metadata, clock and pixels survive candidate overwrite exactly"),
        Frame->Pixels==Expected->Pixels && Frame->Sequence==2 && Frame->ElapsedSeconds==2 && Frame->SimulationSeconds==1.99);
    auto Old=MakeShared<FRaftSimDetailPresentationFrame,ESPMode::ThreadSafe>(*Expected);Old->Sequence=1;
    TestFalse(TEXT("out-of-order completion cannot regress presented sequence"),Mailbox->Publish(Old));
    auto Bad=MakeShared<FRaftSimDetailPresentationFrame,ESPMode::ThreadSafe>(*Expected);Bad->Sequence=9;
    Bad->Pixels[0].X=std::numeric_limits<float>::quiet_NaN();
    TestFalse(TEXT("nonfinite frame rejected without poisoning sequence"),Mailbox->Publish(Bad));
    auto Next=MakeShared<FRaftSimDetailPresentationFrame,ESPMode::ThreadSafe>(*Expected);Next->Sequence=3;Next->Pixels[Nx*Ny].Y+=4;
    TestTrue(TEXT("later valid registration accepted"),Mailbox->Publish(Next));
    TestTrue(TEXT("held immutable frame does not inherit newer origin"),Frame->Pixels[Nx*Ny]==Expected->Pixels[Nx*Ny]);
    TestEqual(TEXT("latest frame consumed once"),Mailbox->TakeLatest()->Sequence,uint64(3));
    TestFalse(TEXT("empty mailbox preserves held frame"),Mailbox->TakeLatest().IsValid());

    TArray<FVector4f> Queries;
    for (int32 Y=-1;Y<=Ny;++Y) for (int32 X=-1;X<=Nx;++X)
        Queries.Add(FVector4f(-5439+X*.5f+.125f,3606+Y*.5f+.375f,0,0));
    Queries.Add(FVector4f(-5439+(Nx-1)*.5f,3606+(Ny-1)*.5f,0,0));
    auto Read=MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("ContactPresentedParity"));
    bool GPUOK=false;FString Error;
    ENQUEUE_RENDER_COMMAND(RaftSimContactFramePresent)([&](FRHICommandListImmediate& Cmd)
    {
        auto Presented=Cmd.CreateTexture(FRHITextureCreateDesc::Create2D(TEXT("ContactPresented"),Nx,Ny+1,PF_A32B32G32R32F)
            .SetFlags(ETextureCreateFlags::ShaderResource).SetInitialState(ERHIAccess::CopyDest));
        Cmd.UpdateTexture2D(Presented,0,FUpdateTextureRegion2D(0,0,0,0,Nx,Ny+1),Nx*sizeof(FVector4f),reinterpret_cast<const uint8*>(Frame->Pixels.GetData()));
        Cmd.Transition(FRHITransitionInfo(Presented,ERHIAccess::CopyDest,ERHIAccess::SRVMask));
        GPUOK=RaftSimValidateRegisteredDetailSamplingGPU(Cmd,Presented,Queries,&Read.Get(),Error);
    });
    FlushRenderingCommands();
    if (!GPUOK) { AddError(Error);return false; }
    const double ReadDeadline=FPlatformTime::Seconds()+5;
    while (!Read->IsReady() && FPlatformTime::Seconds()<ReadDeadline) FPlatformProcess::Sleep(.001f);
    if (!TestTrue(TEXT("GPU parity result ready"),Read->IsReady()))return false;
    float MaxError=0;bool ReadOK=false,Finite=true;
    ENQUEUE_RENDER_COMMAND(RaftSimContactFrameCompare)([&](FRHICommandListImmediate&)
    {
        const auto* Values=static_cast<const FVector4f*>(Read->Lock(Queries.Num()*sizeof(FVector4f)));
        if (!Values) return;
        ReadOK=true;
        for (int32 I=0;I<Queries.Num();++I)
        {
            const auto CPU=Frame->SampleField(FVector2f(Queries[I].X,Queries[I].Y));
            for (int32 C=0;C<4;++C)
            { Finite &= FMath::IsFinite(Values[I][C]);MaxError=FMath::Max(MaxError,FMath::Abs(Values[I][C]-CPU[C])); }
        }
        Read->Unlock();
    });
    FlushRenderingCommands();
    TestTrue(TEXT("CPU support samples the same reuploaded registered frame as the actual GPU material helper"),ReadOK && Finite && MaxError<1.e-6f);
    AddInfo(FString::Printf(TEXT("Completed GPU frame copy/reupload/registered sampler: %d queries, max RGBA error %.9g; includes far data edge, outside and overwritten simulation candidate"),Queries.Num(),MaxError));
    return !HasAnyErrors();
}
#endif
