#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Serialization/MemoryReader.h"
#include "RaftSimTemporalBoundaryGPU.h"
#include "RaftSimTotalDepthAdvanceGPU.h"
#include "RaftSimBreakingFrontGPU.h"
#include "RaftSimTotalDepthIntervalGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTemporalEvolutionTest,"RaftSim.WaterDetail.TemporalEvolutionGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FTemporalEvolutionTest::RunTest(const FString&)
{
    if(GUsingNullRHI){AddError(TEXT("Actual GPU required"));return false;}
    FString Path,Error;TArray<uint8> Bytes;
    if(!FParse::Value(FCommandLine::Get(),TEXT("RaftSimTemporalEvolutionFixture="),Path) || !FFileHelper::LoadFileToArray(Bytes,*Path))
    {AddError(TEXT("Run audit_live_temporal_evolution.py --fixture and pass -RaftSimTemporalEvolutionFixture=<binary>"));return false;}
    if(Bytes.Num()<36){AddError(TEXT("Truncated temporal evolution header"));return false;}
    FMemoryReader Reader(Bytes,true);uint32 Magic=0,Version=0,X=0,Y=0;float Dx=0;double FirstTime=0,SecondTime=0;
    Reader<<Magic<<Version<<X<<Y<<Dx<<FirstTime<<SecondTime;
    if(Magic!=0x52535445u || (Version!=1 && Version!=2) || X<1 || Y<1 || X>512 || Y>512 ||
        !FMath::IsFinite(Dx) || Dx<=0 || !FMath::IsFinite(FirstTime) || !FMath::IsFinite(SecondTime) || SecondTime<=FirstTime)
    {AddError(TEXT("Invalid temporal evolution fixture header"));return false;}
    uint32 BreakingMode=0;
    if(Version==2)
    {
        if(Reader.Tell()+4>Reader.TotalSize()){AddError(TEXT("Truncated temporal breaking mode"));return false;}
        Reader<<BreakingMode;
        if(BreakingMode!=1){AddError(TEXT("Unsupported temporal breaking mode"));return false;}
    }
    const FIntPoint Size(X,Y);const int32 N=X*Y,NB=2*(X+Y);
    TArray<FVector4f> Initial,ExteriorA,ExteriorB,Expected;TArray<float> Bed,ExteriorBed,FaceA,FaceB;
    auto Read=[&](auto& A,int32 Count)
    {
        const int64 Length=sizeof(A[0])*int64(Count);
        if(Reader.IsError() || Reader.Tell()+Length>Reader.TotalSize()){Reader.SetError();return;}
        A.SetNumUninitialized(Count);Reader.Serialize(A.GetData(),Length);
    };
    Read(Initial,N);Read(Bed,N);Read(ExteriorA,NB);Read(ExteriorB,NB);Read(ExteriorBed,NB);Read(FaceA,NB);Read(FaceB,NB);Read(Expected,N);
    if(Reader.IsError() || Reader.Tell()!=Reader.TotalSize()){AddError(TEXT("Truncated/trailing temporal evolution fixture"));return false;}
    const float Duration=float(SecondTime-FirstTime),Hi=float(FirstTime),Lo=float(FirstTime-double(Hi));
    if(!FMath::IsFinite(Duration) || Duration<=0){AddError(TEXT("Unrepresentable interval"));return false;}
    bool Passed=true;TArray<FString> Records;
    const bool Timing=FParse::Param(FCommandLine::Get(),TEXT("RaftSimTemporalEvolutionTiming"));
    const bool Cull=!FParse::Param(FCommandLine::Get(),TEXT("RaftSimUnculledTemporalEvolution"));
    if(Timing && !GSupportsTimestampRenderQueries){AddError(TEXT("Actual GPU timestamps required for requested timing"));return false;}
    struct FResult{TArray<FVector4f> State,Volume;FVector4f Clock=FVector4f(0,0,0,0);uint32 Summary[4]{},Diagnostics[4]{};};
    FResult Split,Batch,Chained;
    ENQUEUE_RENDER_COMMAND(TemporalEvolutionVerification)([&](FRHICommandListImmediate& Cmd)
    {
        auto Run=[&](int32 Slots,FResult& Out,int32 Sample,bool CullIterations,bool Chain=false)
        {
            TRefCountPtr<FRDGPooledBuffer> State,Progress,Summary,Diagnostics,Volume;
            FRenderQueryPoolRHIRef TimingPool;TArray<FRHIPooledRenderQuery> Queries;
            if(Sample>=0)
            {
                TimingPool=RHICreateRenderQueryPool(RQT_AbsoluteTime,8/Slots);
                for(int32 I=0;I<8/Slots;++I)Queries.Add(TimingPool->AllocateQuery());
            }
            const int32 GraphsPerInterval=4/Slots,GraphCount=GraphsPerInterval*(Chain?2:1);
            for(int32 Index=0;Index<GraphCount;++Index)
            {
                FRDGBuilder Graph(Cmd);
                auto Upload=[&](const auto& A,const TCHAR* Name){return CreateStructuredBuffer(Graph,Name,MakeArrayView(A));};
                TArray<float> Fraction;Fraction.Init(1,N);
                TArray<FVector4f> InitialClock={FVector4f(Hi,Lo,Chain?.5f*Duration:Duration,1.f/120.f)};
                auto S=State?Graph.RegisterExternalBuffer(State):Upload(Initial,TEXT("TemporalEvolution.State"));
                auto P=Progress?Graph.RegisterExternalBuffer(Progress):Upload(InitialClock,TEXT("TemporalEvolution.Clock"));
                auto B=Upload(Bed,TEXT("TemporalEvolution.Bed")),F=Upload(Fraction,TEXT("TemporalEvolution.Fraction"));
                auto EB=Upload(ExteriorBed,TEXT("TemporalEvolution.ExteriorBed"));
                FRaftSimTemporalBoundaryEndpoint A{Upload(ExteriorA,TEXT("TemporalEvolution.ExteriorA")),EB,
                    Upload(FaceA,TEXT("TemporalEvolution.FaceA")),FirstTime};
                FRaftSimTemporalBoundaryEndpoint Z{Upload(ExteriorB,TEXT("TemporalEvolution.ExteriorB")),EB,
                    Upload(FaceB,TEXT("TemporalEvolution.FaceB")),SecondTime};
                auto Select=[&](FRDGBuilder& G,FRDGBufferRef,const FRaftSimTotalDepthTransportResult& Stage)
                {return BreakingMode==1 ? RaftSimClassifyBreakingFrontGPU(G,Stage.Geometry,Stage.HydroRate,Stage.Pairs,Size,Dx,false,Error).Fraction:F;};
                FRaftSimTotalDepthBoundaryProvider Provider=[&](FRDGBuilder& G,FRDGBufferRef,FRDGBufferRef Clock,FRDGBufferRef Info)
                {return RaftSimSampleTemporalBoundaryGPU(G,A,Z,Clock,Info,Size,Error).Input;};
                if(Sample>=0)
                {
                    auto* Begin=Queries[2*Index].GetQuery();
                    Graph.AddPass(RDG_EVENT_NAME("TemporalEvolution.TimestampBegin"),ERDGPassFlags::None,
                        [Begin](FRHICommandList& List){List.EndRenderQuery(Begin);});
                }
                FRaftSimTotalDepthAdvanceResult Previous;
                Previous.State=S;Previous.Progress=P;
                Previous.Summary=Summary?Graph.RegisterExternalBuffer(Summary):nullptr;
                Previous.Diagnostics=Diagnostics?Graph.RegisterExternalBuffer(Diagnostics):nullptr;
                Previous.BoundaryVolume=Volume?Graph.RegisterExternalBuffer(Volume):nullptr;
                if(Chain && Index==GraphsPerInterval)
                {
                    Previous=RaftSimBeginNextTotalDepthIntervalGPU(Graph,Previous,Size,
                        FirstTime+.5*Duration,FirstTime+Duration,Error);
                    if(!Previous.State){Passed=false;Graph.Execute();return;}
                }
                auto R=RaftSimAdvanceTotalDepthGPU(Graph,Previous.State,B,Previous.Progress,Previous.Summary,
                    Previous.Diagnostics,Size,Dx,false,true,Slots,4096,Select,Error,Provider,Previous.BoundaryVolume,CullIterations);
                if(!R.State || !R.BoundaryVolume || !Error.IsEmpty()){Passed=false;Graph.Execute();return;}
                if(Sample>=0)
                {
                    auto* End=Queries[2*Index+1].GetQuery();
                    Graph.AddPass(RDG_EVENT_NAME("TemporalEvolution.TimestampEnd"),ERDGPassFlags::None,
                        [End](FRHICommandList& List){List.EndRenderQuery(End);});
                }
                FRHIGPUBufferReadback SR(TEXT("TemporalEvolution.SR")),PR(TEXT("TemporalEvolution.PR")),CR(TEXT("TemporalEvolution.CR")),
                    DR(TEXT("TemporalEvolution.DR")),VR(TEXT("TemporalEvolution.VR"));
                const bool Last=Index+1==GraphCount;
                if(Last)
                {
                    AddEnqueueCopyPass(Graph,&SR,R.State,N*16);AddEnqueueCopyPass(Graph,&PR,R.Progress,16);
                    AddEnqueueCopyPass(Graph,&CR,R.Summary,16);AddEnqueueCopyPass(Graph,&DR,R.Diagnostics,16);
                    AddEnqueueCopyPass(Graph,&VR,R.BoundaryVolume,NB*16);
                }
                Graph.QueueBufferExtraction(R.State,&State);Graph.QueueBufferExtraction(R.Progress,&Progress);
                Graph.QueueBufferExtraction(R.Summary,&Summary);Graph.QueueBufferExtraction(R.Diagnostics,&Diagnostics);
                Graph.QueueBufferExtraction(R.BoundaryVolume,&Volume);Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
                if(Sample>=0)
                {
                    uint64 Begin=0,End=0;
                    if(RHIGetRenderQueryResult(Queries[2*Index].GetQuery(),Begin,true) &&
                        RHIGetRenderQueryResult(Queries[2*Index+1].GetQuery(),End,true) && End>=Begin)
                        Records.Add(FString::Printf(TEXT("GPU temporal evolution sample%d graph%d slots%d cull%d %.6f ms (boundary sampling, both RK stages, pressure, commit and ledger; excludes upload/readback; not frame FPS)"),
                            Sample,Index,Slots,CullIterations,(End-Begin)/1000.));
                    else {Passed=false;Records.Add(TEXT("Requested temporal evolution timestamp unavailable"));}
                }
                if(Last)
                {
                    const void* Data=SR.Lock(N*16);const void* Clock=PR.Lock(16);const void* Counts=CR.Lock(16);
                    const void* Flags=DR.Lock(16);const void* Ledger=VR.Lock(NB*16);
                    if(!Data || !Clock || !Counts || !Flags || !Ledger){Passed=false;return;}
                    Out.State.SetNumUninitialized(N);Out.Volume.SetNumUninitialized(NB);
                    FMemory::Memcpy(Out.State.GetData(),Data,N*16);FMemory::Memcpy(&Out.Clock,Clock,16);
                    FMemory::Memcpy(Out.Summary,Counts,16);FMemory::Memcpy(Out.Diagnostics,Flags,16);
                    FMemory::Memcpy(Out.Volume.GetData(),Ledger,NB*16);
                    SR.Unlock();PR.Unlock();CR.Unlock();DR.Unlock();VR.Unlock();
                }
            }
        };
        Run(1,Split,-1,Cull);Run(4,Batch,-1,Cull);
        Run(4,Chained,-1,Cull,true);
        FResult ChainedSplit;Run(1,ChainedSplit,-1,Cull,true);
        const bool ChainExact=Chained.State.Num()==N && ChainedSplit.State.Num()==N &&
            Chained.Volume.Num()==NB && ChainedSplit.Volume.Num()==NB &&
            FMemory::Memcmp(Chained.State.GetData(),ChainedSplit.State.GetData(),N*16)==0 &&
            FMemory::Memcmp(Chained.Volume.GetData(),ChainedSplit.Volume.GetData(),NB*16)==0 &&
            FMemory::Memcmp(&Chained.Clock,&ChainedSplit.Clock,16)==0 &&
            FMemory::Memcmp(Chained.Summary,ChainedSplit.Summary,16)==0 &&
            FMemory::Memcmp(Chained.Diagnostics,ChainedSplit.Diagnostics,16)==0;
        Passed &= ChainExact;
        Records.Add(FString::Printf(TEXT("two consecutive intervals five-record graph partition exact%d"),ChainExact));
        FResult Other;Run(4,Other,-1,!Cull);
        if(Other.State.Num()!=N || Other.Volume.Num()!=NB || Batch.State.Num()!=N || Batch.Volume.Num()!=NB){Passed=false;return;}
        const bool OtherExact=FMemory::Memcmp(Other.State.GetData(),Batch.State.GetData(),N*16)==0 &&
            FMemory::Memcmp(Other.Volume.GetData(),Batch.Volume.GetData(),NB*16)==0 &&
            FMemory::Memcmp(&Other.Clock,&Batch.Clock,16)==0 && FMemory::Memcmp(Other.Summary,Batch.Summary,16)==0 &&
            FMemory::Memcmp(Other.Diagnostics,Batch.Diagnostics,16)==0;
        Passed &= OtherExact;
        Records.Add(FString::Printf(TEXT("temporal evolution indirect/direct five-record exact%d"),OtherExact));
        auto CheckTimed=[&](const FResult& Timed)
        {
            if(Timed.State.Num()!=N || Timed.Volume.Num()!=NB)return false;
            return FMemory::Memcmp(Timed.State.GetData(),Batch.State.GetData(),N*16)==0 &&
                FMemory::Memcmp(Timed.Volume.GetData(),Batch.Volume.GetData(),NB*16)==0 &&
                FMemory::Memcmp(&Timed.Clock,&Batch.Clock,16)==0 && FMemory::Memcmp(Timed.Summary,Batch.Summary,16)==0 &&
                FMemory::Memcmp(Timed.Diagnostics,Batch.Diagnostics,16)==0;
        };
        if(Timing)
        {
            // Explicit warm-up policy for this component benchmark only. Keep
            // the earlier all-sample/cold runs as evidence, not discarded data.
            for(int32 Warmup=0;Warmup<4;++Warmup)
            {
                FResult Warm;Run(2,Warm,-1,Warmup%2==0?Cull:!Cull);Passed &= CheckTimed(Warm);
            }
            Records.Add(TEXT("GPU temporal timing: four alternating warm-up intervals, then eight paired samples with alternating order; all results exact; no scene FPS claim"));
            for(int32 Sample=0;Sample<8;++Sample)for(int32 Order=0;Order<2;++Order)
            {
                FResult Timed;Run(2,Timed,Sample,(Sample+Order)%2==0?Cull:!Cull);Passed &= CheckTimed(Timed);
            }
        }
    });
    FlushRenderingCommands();
    if(Split.State.Num()!=N || Batch.State.Num()!=N){AddError(TEXT("Missing evolution result: ")+Error);return false;}
    Passed &= FMemory::Memcmp(Split.State.GetData(),Batch.State.GetData(),N*16)==0 &&
        FMemory::Memcmp(Split.Volume.GetData(),Batch.Volume.GetData(),NB*16)==0 &&
        FMemory::Memcmp(&Split.Clock,&Batch.Clock,16)==0 && FMemory::Memcmp(Split.Summary,Batch.Summary,16)==0 &&
        FMemory::Memcmp(Split.Diagnostics,Batch.Diagnostics,16)==0;
    Passed &= Split.Summary[2]==1 && Split.Summary[3]==1 && Split.Summary[1]>0 && Split.Clock.Z==0 &&
        (Split.Diagnostics[0]|Split.Diagnostics[1]|Split.Diagnostics[2])==0;
    const double EndTime=double(Split.Clock.X)+Split.Clock.Y;
    Passed &= FMath::Abs(EndTime-(FirstTime+Duration))<1e-9;
    if(Chained.State.Num()!=N || Chained.Volume.Num()!=NB){AddError(TEXT("Missing chained interval result: ")+Error);return false;}
    Passed &= Chained.Summary[2]==1 && Chained.Summary[3]==1 && Chained.Summary[1]>0 && Chained.Clock.Z==0 &&
        (Chained.Diagnostics[0]|Chained.Diagnostics[1]|Chained.Diagnostics[2])==0 &&
        FMath::Abs(double(Chained.Clock.X)+Chained.Clock.Y-(FirstTime+Duration))<1e-9;
    double ChainMaxError=0,ChainWater=0,ChainOutward=0;
    for(int32 K=0;K<4;++K)
    {
        double E2=0,N2=0;
        for(int32 I=0;I<N;++I)
        {
            const double E=double(Chained.State[I][K])-Expected[I][K];E2+=E*E;N2+=double(Expected[I][K])*Expected[I][K];
            ChainMaxError=FMath::Max(ChainMaxError,FMath::Abs(E));Passed &= FMath::IsFinite(Chained.State[I][K]);
        }
        const double Relative=N2>0?FMath::Sqrt(E2/N2):FMath::Sqrt(E2);
        Passed &= Relative<2e-5;
        Records.Add(FString::Printf(TEXT("two-interval component%d CPU-double relative%.12g"),K,Relative));
    }
    Passed &= ChainMaxError<1e-4;
    for(int32 I=0;I<N;++I)
    {
        Passed &= Chained.State[I].X>=0 && Chained.State[I].W==0;
        ChainWater+=(double(Chained.State[I].X)-Initial[I].X)*Dx*Dx;
    }
    for(int32 I=0;I<NB;++I)
    {
        for(int32 K=0;K<4;++K)Passed &= FMath::IsFinite(Chained.Volume[I][K]);
        const double Sign=I<int32(Y)?-1:I<int32(2*Y)?1:I<int32(2*Y+X)?-1:1;
        ChainOutward+=Sign*Dx*Chained.Volume[I].X;Passed &= Chained.Volume[I].W==0;
    }
    Records.Add(FString::Printf(TEXT("two-interval retained evolution end%.17g remaining%.12g status%u maxerror%.12g water-change%.12g cumulative-outward%.12g balance%.12g"),
        double(Chained.Clock.X)+Chained.Clock.Y,Chained.Clock.Z,Chained.Summary[2],ChainMaxError,ChainWater,ChainOutward,ChainWater+ChainOutward));
    double MaxError=0,WaterChange=0,Outward=0;
    for(int32 K=0;K<4;++K)
    {
        double E2=0,N2=0;
        for(int32 I=0;I<N;++I)
        {
            const double E=double(Split.State[I][K])-Expected[I][K];E2+=E*E;N2+=double(Expected[I][K])*Expected[I][K];
            MaxError=FMath::Max(MaxError,FMath::Abs(E));Passed &= FMath::IsFinite(Split.State[I][K]);
        }
        const double Relative=N2>0?FMath::Sqrt(E2/N2):FMath::Sqrt(E2);
        Passed &= Relative<2e-5;
        Records.Add(FString::Printf(TEXT("temporal evolution component%d CPU-double relative%.12g"),K,Relative));
    }
    Passed &= MaxError<1e-4;
    for(int32 I=0;I<N;++I)
    {
        Passed &= Split.State[I].X>=0 && Split.State[I].W==0;
        WaterChange+=(double(Split.State[I].X)-Initial[I].X)*Dx*Dx;
    }
    for(int32 I=0;I<NB;++I)
    {
        for(int32 K=0;K<4;++K)Passed &= FMath::IsFinite(Split.Volume[I][K]);
        const double Sign=I<int32(Y)?-1:I<int32(2*Y)?1:I<int32(2*Y+X)?-1:1;
        Outward+=Sign*Dx*Split.Volume[I].X;
        Passed &= Split.Volume[I].W==0;
    }
    // Float-storage mass residual is reported, not repaired or mistaken for the
    // double control's roundoff. Existing component/max state gates stay intact.
    Records.Add(FString::Printf(TEXT("temporal evolution trials%u accepted%u status%u mode%u bits%u/%u/%u/%u end%.17g remaining%.12g maxerror%.12g water-change%.12g outward%.12g balance%.12g"),
        Split.Summary[0],Split.Summary[1],Split.Summary[2],Split.Summary[3],Split.Diagnostics[0],Split.Diagnostics[1],Split.Diagnostics[2],Split.Diagnostics[3],
        EndTime,Split.Clock.Z,MaxError,WaterChange,Outward,WaterChange+Outward));
    AddInfo(FString::Printf(TEXT("temporal breaking mode%u (0=nonbreaking,1=both-stage GPU hybrid classification)"),BreakingMode));
    for(const auto& Record:Records)AddInfo(Record);
    TestTrue(TEXT("Full observed interval agrees with independent CPU evolution and graph partition preserves all five records"),Passed);
    if(!Error.IsEmpty())AddError(Error);return !HasAnyErrors();
}
#endif
