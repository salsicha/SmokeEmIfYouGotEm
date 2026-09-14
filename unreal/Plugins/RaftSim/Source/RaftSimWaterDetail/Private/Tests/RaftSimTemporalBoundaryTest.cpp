#include "Misc/AutomationTest.h"
#include "RaftSimTemporalBoundaryGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTemporalBoundaryTest,"RaftSim.WaterDetail.TemporalBoundaryGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FTemporalBoundaryTest::RunTest(const FString&)
{
    if(GUsingNullRHI){AddError(TEXT("Actual GPU required"));return false;}
    bool Passed=true;FString Error;TArray<FString> Records;
    ENQUEUE_RENDER_COMMAND(TemporalBoundaryVerification)([&](FRHICommandListImmediate& Cmd)
    {
        const FIntPoint Size(17,13);const int32 N=2*(Size.X+Size.Y);const double Start=1048576.03125,Span=.125;
        for(int32 Case=0;Case<14;++Case)
        {
            const bool PreviousPassed=Passed;Passed=true;
            TArray<FVector4f> A,B,Clock,Info;TArray<float> ZA,ZB,UA,UB;
            for(int32 I=0;I<N;++I)
            {
                A.Add(FVector4f(1+I*.125f,.5f,-.25f,.125f));B.Add(FVector4f(2+I*.125f,1.5f,.25f,.5f));
                ZA.Add((I-30)*.25f);ZB.Add(ZA.Last());UA.Add((I-30)*.0625f);UB.Add(UA.Last()+.125f);
            }
            const bool Second=Case==3 || Case==4 || Case==6 || Case==12;
            float Offset=Case==0?0:Case==1?.125f:.03125f,Dt=Second?.015625f:0;
            if(Case==4)Dt=.09375f;
            if(Case==5)Offset=-.0009765625f;
            if(Case==6)Dt=.125f;
            if(Case==7)B.Last().X=-1;
            if(Case==8)ZB.Last()+=1;
            if(Case==9)UB.Last()=std::numeric_limits<float>::infinity();
            if(Case==10){A.Last()=FVector4f(1e-30f,1e-30f,0,0);B.Last()=FVector4f(2e-30f,2e-30f,0,0);}
            if(Case==11)Offset=std::numeric_limits<float>::quiet_NaN();
            if(Case==12)Dt=-.0078125f;
            if(Case==13){A.Last()=FVector4f(0,0,0,0);B.Last()=FVector4f(0,0,0,0);}
            Clock.Add(FVector4f(1048576,.03125f+Offset,.02f,1.f/120.f));Info.Add(FVector4f(0,Dt,0,0));
            FRDGBuilder Graph(Cmd);auto Upload=[&](const auto& V,const TCHAR* Name){return CreateStructuredBuffer(Graph,Name,MakeArrayView(V));};
            const FRaftSimTemporalBoundaryEndpoint First{Upload(A,TEXT("TemporalTest.A")),Upload(ZA,TEXT("TemporalTest.ZA")),Upload(UA,TEXT("TemporalTest.UA")),Start};
            const FRaftSimTemporalBoundaryEndpoint Last{Upload(B,TEXT("TemporalTest.B")),Upload(ZB,TEXT("TemporalTest.ZB")),Upload(UB,TEXT("TemporalTest.UB")),Start+Span};
            auto P=Upload(Clock,TEXT("TemporalTest.Clock")),T=Upload(Info,TEXT("TemporalTest.Info"));
            if(Case==0)
            {
                for(int32 Fault=0;Fault<6;++Fault)
                {
                    auto Bad=Last;auto Shape=Size;auto BadP=P;
                    if(Fault==0)Bad.Seconds=Start;
                    if(Fault==1)Bad.Seconds=std::numeric_limits<double>::infinity();
                    if(Fault==2)Bad.FaceNormalVelocity=nullptr;
                    if(Fault==3)Bad.State=First.Bed;
                    if(Fault==4)Shape.X=0;
                    if(Fault==5)BadP=First.State;
                    FString E;const auto Invalid=RaftSimSampleTemporalBoundaryGPU(Graph,First,Bad,BadP,nullptr,Shape,E);
                    Passed &= !Invalid.Diagnostics && !E.IsEmpty();
                }
            }
            const auto R=RaftSimSampleTemporalBoundaryGPU(Graph,First,Last,P,Second?T:nullptr,Size,Error);
            if(!R.Diagnostics){Passed=false;Graph.Execute();return;}
            FRHIGPUBufferReadback SR(TEXT("TemporalTest.SR")),BR(TEXT("TemporalTest.BR")),TR(TEXT("TemporalTest.TR")),DR(TEXT("TemporalTest.DR"));
            AddEnqueueCopyPass(Graph,&SR,R.Input.ExteriorState,N*16);AddEnqueueCopyPass(Graph,&BR,R.Input.ExteriorBed,N*4);
            AddEnqueueCopyPass(Graph,&TR,R.Input.FaceVelocity,N*8);AddEnqueueCopyPass(Graph,&DR,R.Diagnostics,16);
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            const auto* S=static_cast<const FVector4f*>(SR.Lock(N*16));const auto* Z=static_cast<const float*>(BR.Lock(N*4));
            const auto* U=static_cast<const FVector2f*>(TR.Lock(N*8));const auto* D=static_cast<const uint32*>(DR.Lock(16));
            if(!S || !Z || !U || !D){Passed=false;return;}
            const bool BadTime=Case==5 || Case==6 || Case==11 || Case==12;
            Passed &= D[0]==(BadTime?1u:0u);
            if(Case==7)Passed &= D[1]>0 && !FMath::IsFinite(S[N-1].X);
            else if(Case==8)Passed &= D[2]>0 && !FMath::IsFinite(Z[N-1]);
            else if(Case==9)Passed &= D[3]>0 && !FMath::IsFinite(U[N-1].X);
            else if(BadTime)for(int32 I=0;I<N;++I)Passed &= !FMath::IsFinite(S[I].X) && !FMath::IsFinite(Z[I]) && !FMath::IsFinite(U[I].X);
            else
            {
                Passed &= (D[0]|D[1]|D[2]|D[3])==0;
                const double Alpha=(double(Clock[0].Y)-.03125+double(Dt))/Span;
                for(int32 I=0;I<N;++I)
                {
                    for(int32 K=0;K<4;++K)
                    {
                        const double Expected=(1-Alpha)*double(A[I][K])+Alpha*double(B[I][K]);
                        Passed &= FMath::Abs(double(S[I][K])-Expected)<=1e-6*FMath::Max(1e-30,FMath::Abs(Expected));
                    }
                    Passed &= Z[I]==ZA[I] && FMath::Abs(U[I].X-((1-Alpha)*UA[I]+Alpha*UB[I]))<1e-7 && U[I].Y==1.f;
                }
                if(Alpha==0)Passed &= FMemory::Memcmp(S,A.GetData(),N*16)==0;
                if(Alpha==1)Passed &= FMemory::Memcmp(S,B.GetData(),N*16)==0;
            }
            Records.Add(FString::Printf(TEXT("temporal boundary case%d passed%d diagnostics%u/%u/%u/%u; actual compensated stage time"),Case,Passed,D[0],D[1],D[2],D[3]));
            SR.Unlock();BR.Unlock();TR.Unlock();DR.Unlock();Passed &= PreviousPassed;
        }

        // A stage2 request beyond the observation bracket must roll back. The
        // retry samples the SAME origin clock plus the actual halved trial dt.
        const FIntPoint Tiny(1,1);TArray<FVector4f> Initial={FVector4f(1,.75f,0,.25f)},GhostA,GhostB,Clock;
        GhostA.Init(Initial[0],4);GhostB.Init(FVector4f(1,.75f,0,.5f),4);
        TArray<float> Bed={0},ExtBed={0,0,0,0},Velocity={.75f,.75f,0,0},Fraction={1};
        Clock.Add(FVector4f(1048576,.03125f,.02f,1.f/128.f));
        TRefCountPtr<FRDGPooledBuffer> PriorState,PriorClock;
        for(int32 Trial=0;Trial<2;++Trial)
        {
            FRDGBuilder Graph(Cmd);auto Upload=[&](const auto& V,const TCHAR* Name){return CreateStructuredBuffer(Graph,Name,MakeArrayView(V));};
            auto S=PriorState?Graph.RegisterExternalBuffer(PriorState):Upload(Initial,TEXT("TemporalRetry.Initial"));
            auto P=PriorClock?Graph.RegisterExternalBuffer(PriorClock):Upload(Clock,TEXT("TemporalRetry.Clock"));
            auto F=Upload(Fraction,TEXT("TemporalRetry.Fraction"));
            const FRaftSimTemporalBoundaryEndpoint A{Upload(GhostA,TEXT("TemporalRetry.A")),Upload(ExtBed,TEXT("TemporalRetry.ZA")),Upload(Velocity,TEXT("TemporalRetry.UA")),Start};
            const FRaftSimTemporalBoundaryEndpoint B{Upload(GhostB,TEXT("TemporalRetry.B")),Upload(ExtBed,TEXT("TemporalRetry.ZB")),Upload(Velocity,TEXT("TemporalRetry.UB")),Start+1./256.};
            FRaftSimTotalDepthBoundaryProvider Provider=[&](FRDGBuilder& G,FRDGBufferRef,FRDGBufferRef C,FRDGBufferRef I)
            {return RaftSimSampleTemporalBoundaryGPU(G,A,B,C,I,Tiny,Error).Input;};
            auto Select=[&](FRDGBuilder&,FRDGBufferRef,const FRaftSimTotalDepthTransportResult&){return F;};
            const auto R=RaftSimTryTotalDepthStepGPU(Graph,S,Upload(Bed,TEXT("TemporalRetry.Bed")),P,Tiny,.5f,false,true,Select,Error,Provider);
            if(!R.State){Passed=false;Graph.Execute();return;}
            FRHIGPUBufferReadback SR(TEXT("TemporalRetry.SR")),PR(TEXT("TemporalRetry.PR")),DR(TEXT("TemporalRetry.DR")),VR(TEXT("TemporalRetry.VR"));
            AddEnqueueCopyPass(Graph,&SR,R.State,16);AddEnqueueCopyPass(Graph,&PR,R.Progress,16);AddEnqueueCopyPass(Graph,&DR,R.Diagnostics,16);
            AddEnqueueCopyPass(Graph,&VR,R.BoundaryVolume,64);Graph.QueueBufferExtraction(R.State,&PriorState);Graph.QueueBufferExtraction(R.Progress,&PriorClock);
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            const auto* Next=static_cast<const FVector4f*>(SR.Lock(16));const auto* C=static_cast<const FVector4f*>(PR.Lock(16));
            const auto* D=static_cast<const uint32*>(DR.Lock(16));const auto* V=static_cast<const FVector4f*>(VR.Lock(64));
            if(!Next || !C || !D || !V){Passed=false;return;}
            if(Trial==0)
            {
                Passed &= D[0]==0 && D[1]!=0 && D[3]==0 && *Next==Initial[0] && C->X==Clock[0].X && C->Y==Clock[0].Y && C->Z==Clock[0].Z && C->W==1.f/256.f;
                for(int32 I=0;I<4;++I)Passed &= V[I]==FVector4f(0,0,0,0);
            }
            else Passed &= D[0]==0 && D[1]==0 && D[2]==0 && D[3]==1 && C->X==Clock[0].X && C->Y==Clock[0].Y+1.f/256.f && Next->W>Initial[0].W;
            Records.Add(FString::Printf(TEXT("temporal retry%d accepted%u clock%.9g/%.9g proposed%.9g foam%.9g"),Trial,D[3],C->X,C->Y,C->W,Next->W));
            SR.Unlock();PR.Unlock();DR.Unlock();VR.Unlock();
        }
    });
    FlushRenderingCommands();TestTrue(TEXT("Temporal observations respect compensated stage time, immutable bed, finite state and retry rollback"),Passed);
    for(const auto& R:Records)AddInfo(R);if(!Error.IsEmpty())AddError(Error);return !HasAnyErrors();
}
#endif
