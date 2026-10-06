#include "Misc/AutomationTest.h"
#include "RaftSimTotalDepthFrameGPU.h"
#include "RaftSimDetailWaterGPU.h"
#include "../RaftSimDetailFrameReadback.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTotalDepthFrameTest,"RaftSim.WaterDetail.TotalDepthFrameGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FTotalDepthFrameTest::RunTest(const FString&)
{
    if(GUsingNullRHI){AddError(TEXT("Actual GPU required"));return false;}
    bool Passed=true;FString Error;TArray<FString> Records;
    ENQUEUE_RENDER_COMMAND(TotalDepthFrameVerification)([&](FRHICommandListImmediate& Cmd)
    {
        const FIntPoint Size(17,13);const int32 N=Size.X*Size.Y;const FVector2f Origin(128,-64);
        for(int32 Case=0;Case<11;++Case)
        {
            TArray<FVector4f> State,Progress;TArray<FVector2f> Reference;TArray<float> Bed,Fraction,BadFraction;
            for(int32 I=0;I<N;++I)
            {
                float H=.4f+.001f*(I%Size.X),B=.01f*(I%Size.X)+.02f*(I/Size.X);
                State.Add(FVector4f(H,.2f*H,.1f*H,.125f));Bed.Add(B);Reference.Add(FVector2f(B,B+.5f));
            }
            Fraction.Init(1,N);BadFraction.Init(std::numeric_limits<float>::quiet_NaN(),N);
            Progress.Add(FVector4f(1048576.f,0,(Case==1 || Case==3)?.02f:Case==10?0:.001f,.001f));
            FRDGBuilder Graph(Cmd);auto S=CreateStructuredBuffer(Graph,TEXT("FrameTest.State"),State);
            auto B=CreateStructuredBuffer(Graph,TEXT("FrameTest.Bed"),Bed);auto P=CreateStructuredBuffer(Graph,TEXT("FrameTest.Progress"),Progress);
            auto F=CreateStructuredBuffer(Graph,TEXT("FrameTest.Fraction"),Fraction);
            auto Bad=CreateStructuredBuffer(Graph,TEXT("FrameTest.BadFraction"),BadFraction);
            auto Select=[&](FRDGBuilder&,FRDGBufferRef,const FRaftSimTotalDepthTransportResult&){return Case==2?Bad:F;};
            auto Advanced=RaftSimAdvanceTotalDepthGPU(Graph,S,B,P,nullptr,nullptr,Size,.5f,true,true,1,Case==3?1:16,Select,Error);
            if(!Advanced.State){Passed=false;Graph.Execute();return;}
            // Explicit fixture mutations exercise publication validation after
            // the actual solver; none are production repair/override options.
            if(Case==4)Reference[0].X=std::numeric_limits<float>::quiet_NaN();
            if(Case==5){State[0].X=-1;Advanced.State=CreateStructuredBuffer(Graph,TEXT("FrameTest.InvalidState"),State);}
            if(Case==6)Reference[0]=FVector2f(3e38f,-3e38f);
            if(Case==7){State[0]=FVector4f(1e-30f,3e38f,0,.125f);Advanced.State=CreateStructuredBuffer(Graph,TEXT("FrameTest.InvalidVelocity"),State);}
            if(Case==8 || Case==9)
            {
                Progress[0]=FVector4f(1048576.f,Case==9?std::numeric_limits<float>::infinity():.001f,Case==8?.1f:0,0);
                Advanced.Progress=CreateStructuredBuffer(Graph,TEXT("FrameTest.InvalidClock"),Progress);
            }
            auto Ref=CreateStructuredBuffer(Graph,TEXT("FrameTest.Reference"),Reference);
            auto Resolved=RaftSimResolveTotalDepthFrameGPU(Graph,Advanced,Ref,Size,Origin,.5f,Error);
            if(!Resolved.Texture){Passed=false;Graph.Execute();return;}
            TRefCountPtr<IPooledRenderTarget> Texture;
            Graph.QueueTextureExtraction(Resolved.Texture,&Texture,ERHIAccess::SRVMask);
            FRHIGPUBufferReadback DR(TEXT("FrameTest.DiagnosticsRead")),SR(TEXT("FrameTest.StateRead"));
            AddEnqueueCopyPass(Graph,&DR,Resolved.Diagnostics,16);AddEnqueueCopyPass(Graph,&SR,Advanced.State,N*16);
            Graph.Execute();
            FRaftSimDetailFrameReadback Reader;FRaftSimDetailFrameMailbox Mailbox;
            // Deliberately wrong host simulation time: the shared readback path
            // must obtain the accepted clock from this exact GPU texture.
            Reader.Enqueue(Cmd,Texture->GetRHI(),Size,2,27.,77.,true);
            Cmd.SubmitAndBlockUntilGPUIdle();
            const bool PollOK=Reader.Poll(Mailbox);const auto Frame=Mailbox.TakeLatest();
            const auto* D=static_cast<const uint32*>(DR.Lock(16));const auto* A=static_cast<const FVector4f*>(SR.Lock(N*16));
            if(!D || !A){Passed=false;return;}
            const bool Expected=Case==0 || Case==10;
            Passed &= PollOK==Expected && bool(Frame)==Expected && Reader.Sequence==0;
            float MaxError=0;
            if(Expected)
            {
                Passed &= (D[0]|D[1]|D[2]|D[3])==0;
                if(Frame)
                {
                    Passed &= Frame->Validate() && Frame->bGPUClockMetadata && Frame->Sequence==2 && Frame->ElapsedSeconds==27.;
                    Passed &= Frame->SimulationSeconds==1048576.+(Case==0?double(.001f):0.);
                    auto Height=[&](int32 X,int32 Y){int32 I=Y*Size.X+X;return (Reference[I].X-Reference[I].Y)+A[I].X;};
                    for(int32 Y=0;Y<Size.Y;++Y)for(int32 X=0;X<Size.X;++X)
                    {
                        int32 I=Y*Size.X+X,L=FMath::Max(X-1,0),R=FMath::Min(X+1,Size.X-1),Bot=FMath::Max(Y-1,0),Top=FMath::Min(Y+1,Size.Y-1);
                        FVector4f Target(Height(X,Y),(Height(R,Y)-Height(L,Y))/((R-L)*.5f),
                            (Height(X,Top)-Height(X,Bot))/((Top-Bot)*.5f),1-FMath::Exp(-A[I].W));
                        for(int32 K=0;K<4;++K)MaxError=FMath::Max(MaxError,FMath::Abs(Frame->Pixels[I][K]-Target[K]));
                        Passed &= Frame->SampleField(Origin+FVector2f(.5f*X,.5f*Y))==Frame->Pixels[I];
                    }
                    // Even a finite but stale host time must invalidate the
                    // immutable frame once GPU-clock metadata is adopted.
                    auto Tampered=*Frame;Tampered.SimulationSeconds=77.;Passed &= !Tampered.Validate();
                    Tampered=*Frame;Tampered.Pixels[N+1].Z=.1f;Passed &= !Tampered.Validate();
                    // Reupload the immutable mailbox payload just as the live
                    // presenter does, then use the actual material sampler.
                    auto Presented=Cmd.CreateTexture(FRHITextureCreateDesc::Create2D(TEXT("TotalFramePresented"),Size.X,Size.Y+1,PF_A32B32G32R32F)
                        .SetFlags(ETextureCreateFlags::ShaderResource).SetInitialState(ERHIAccess::CopyDest));
                    Cmd.UpdateTexture2D(Presented,0,FUpdateTextureRegion2D(0,0,0,0,Size.X,Size.Y+1),Size.X*16,
                        reinterpret_cast<const uint8*>(Frame->Pixels.GetData()));
                    Cmd.Transition(FRHITransitionInfo(Presented,ERHIAccess::CopyDest,ERHIAccess::SRVMask));
                    TArray<FVector4f> Queries;
                    for(int32 Y=-1;Y<=Size.Y;++Y)for(int32 X=-1;X<=Size.X;++X)
                        Queries.Add(FVector4f(Origin.X+.5f*X+.125f,Origin.Y+.5f*Y+.375f,0,0));
                    Queries.Add(FVector4f(Origin.X+.5f*(Size.X-1),Origin.Y+.5f*(Size.Y-1),0,0));
                    FRHIGPUBufferReadback Samples(TEXT("TotalFramePresentedSamples"));
                    FString SampleError;
                    if(!RaftSimValidateRegisteredDetailSamplingGPU(Cmd,Presented,Queries,&Samples,SampleError))
                    {Passed=false;Error=SampleError;}
                    else
                    {
                        Cmd.SubmitAndBlockUntilGPUIdle();
                        const auto* Values=static_cast<const FVector4f*>(Samples.Lock(Queries.Num()*16));
                        if(!Values)Passed=false;
                        else
                        {
                            float SampleMaxError=0;
                            for(int32 I=0;I<Queries.Num();++I)
                            {
                                const auto Contact=Frame->SampleField(FVector2f(Queries[I].X,Queries[I].Y));
                                for(int32 K=0;K<4;++K)
                                {Passed &= FMath::IsFinite(Values[I][K]);SampleMaxError=FMath::Max(SampleMaxError,FMath::Abs(Values[I][K]-Contact[K]));}
                            }
                            Passed &= SampleMaxError<1e-6f;Samples.Unlock();
                            Records.Add(FString::Printf(TEXT("total frame case%d reuploaded material/contact queries%d error%.9g"),Case,Queries.Num(),SampleMaxError));
                        }
                    }
                }
                Passed &= MaxError<2e-6f;
            }
            else
            {
                Passed &= (D[0]|D[1]|D[2]|D[3])!=0;
                if(Case==1 || Case==3 || Case==8)Passed &= (D[3]&1u)!=0;
                if(Case==2)Passed &= (D[3]&4u)!=0;
                if(Case==4)Passed &= D[1]>0;
                if(Case==5 || Case==7)Passed &= D[0]>0;
                if(Case==6)Passed &= D[2]>0;
                if(Case==9)Passed &= (D[3]&2u)!=0;
            }
            Records.Add(FString::Printf(TEXT("total frame case%d published%d diagnostics%u/%u/%u/%u surface error%.9g"),Case,bool(Frame),D[0],D[1],D[2],D[3],MaxError));
            DR.Unlock();SR.Unlock();
        }
    });
    FlushRenderingCommands();TestTrue(TEXT("Actual GPU interval surface/clock reaches the existing paired frame mailbox; invalid or incomplete frames are refused"),Passed);
    for(const auto& R:Records)AddInfo(R);if(!Error.IsEmpty())AddError(Error);return !HasAnyErrors();
}
#endif
