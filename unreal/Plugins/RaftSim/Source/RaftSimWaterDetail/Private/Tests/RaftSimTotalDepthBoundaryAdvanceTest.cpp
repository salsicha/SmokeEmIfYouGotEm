#include "Misc/AutomationTest.h"
#include "RaftSimTotalDepthAdvanceGPU.h"
#include "RaftSimTotalDepthFrameGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
// Preserve the complete stress matrix without submitting all thirteen cases
// into one editor frame's descriptor arena. Yield through normal automation
// frames; never force an RHI frame boundary or increase a resource budget.
class FBoundaryAdvanceCases final : public IAutomationLatentCommand
{
    TFunction<void(int32)> Work;TFunction<void()> Finish;int32 Case=0;uint64 LastFrame=MAX_uint64;
public:
    FBoundaryAdvanceCases(TFunction<void(int32)> InWork,TFunction<void()> InFinish)
        :Work(MoveTemp(InWork)),Finish(MoveTemp(InFinish)){}
    bool Update() override
    {
        if(LastFrame==GFrameCounter)return false;
        LastFrame=GFrameCounter;
        if(Case<13){Work(Case++);return false;}
        Finish();return true;
    }
};
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTotalDepthBoundaryAdvanceTest,"RaftSim.WaterDetail.TotalDepthBoundaryAdvanceGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FTotalDepthBoundaryAdvanceTest::RunTest(const FString&)
{
    if(GUsingNullRHI){AddError(TEXT("Actual GPU required"));return false;}
    struct FRunData{bool Passed=true;FString Error;TArray<FString> Records;};
    const auto Data=MakeShared<FRunData>();
    auto Work=[Data](int32 OnlyCase)
    {
    auto& Passed=Data->Passed;auto& Error=Data->Error;auto& Records=Data->Records;
    Records.Add(FString::Printf(TEXT("boundary case%d scheduled editor frame%llu"),OnlyCase,GFrameCounter));
    ENQUEUE_RENDER_COMMAND(BoundaryAdvanceVerification)([&,OnlyCase](FRHICommandListImmediate& Cmd)
    {
        const FIntPoint Size(17,13);const int32 N=Size.X*Size.Y,NB=2*(Size.X+Size.Y);
        TArray<FVector4f> Initial,Exterior;Initial.Init(FVector4f(1,.75f,0,.25f),N);Exterior.Init(Initial[0],NB);
        TArray<float> Bed,ExteriorBed,Fraction;Bed.Init(0,N);ExteriorBed.Init(0,NB);Fraction.Init(1,N);
        TArray<FVector2f> Trace;for(int32 I=0;I<NB;++I)Trace.Add(FVector2f(I<2*Size.Y?.75f:0,0));
        struct FResult{TArray<FVector4f> State,Volume;FVector4f Progress=FVector4f(0,0,0,0);uint32 Summary[4]{},Diagnostics[4]{};};
        for(int32 Case=OnlyCase;Case<OnlyCase+1;++Case)
        {
            const bool PreviousPassed=Passed;Passed=true;
            Initial[N/2].W=Case==7 || Case==8 || Case==12?.5f:.25f;
            TArray<FVector4f> InitialProgress={FVector4f(1048576.f,.03125f,(Case==0 || Case==6 || Case==12)?.02f:.004f,.004f)};
            if(Case==3){InitialProgress[0].Z=.02f;InitialProgress[0].W=.001f;}
            if(Case==4){InitialProgress[0].Z=0;InitialProgress[0].W=0;}
            const bool Seed=Case>=7 && Case<=11;TArray<FVector4f> InitialVolume;InitialVolume.Init(FVector4f(0,0,0,0),NB);
            if(Case==7 || Case==11)InitialVolume.Last().X=std::numeric_limits<float>::quiet_NaN();
            if(Case==8)InitialVolume.Last().X=3.4e38f;
            if(Case==11)InitialProgress[0].Z=0;
            const int32 Limit=Case==3?1:Case==5?3:16;
            auto Run=[&](int32 Batch,FResult& Out,bool Cull=true)
            {
                TRefCountPtr<FRDGPooledBuffer> State,Progress,Summary,Diagnostics,Volume;int32 Calls=0;
                for(int32 GraphIndex=0;GraphIndex<4/Batch+1;++GraphIndex)
                {
                    const bool Last=GraphIndex==4/Batch;FRDGBuilder Graph(Cmd);
                    auto Upload=[&](const auto& A,const TCHAR* Name){return CreateStructuredBuffer(Graph,Name,MakeArrayView(A));};
                    auto S=State?Graph.RegisterExternalBuffer(State):Upload(Initial,TEXT("BoundaryAdvance.State"));
                    auto P=Progress?Graph.RegisterExternalBuffer(Progress):Upload(InitialProgress,TEXT("BoundaryAdvance.Clock"));
                    FRDGBufferRef C=Summary?Graph.RegisterExternalBuffer(Summary):nullptr,D=Diagnostics?Graph.RegisterExternalBuffer(Diagnostics):nullptr;
                    FRDGBufferRef V=Volume?Graph.RegisterExternalBuffer(Volume):nullptr;
                    if(Seed && !Summary)
                    {
                        TArray<uint32> Counts={Case==11?3u:1u,Case==11?3u:1u,Case==11?1u:0u,Case==10?0u:1u};
                        TArray<uint32> Diag={0,0,0,1};C=Upload(Counts,TEXT("BoundaryAdvance.SeededSummary"));D=Upload(Diag,TEXT("BoundaryAdvance.SeededDiagnostics"));
                        V=Upload(InitialVolume,TEXT("BoundaryAdvance.SeededVolume"));
                    }
                    auto B=Upload(Bed,TEXT("BoundaryAdvance.Bed")),F=Upload(Fraction,TEXT("BoundaryAdvance.Fraction"));
                    auto SelectFraction=[&](FRDGBuilder& G,FRDGBufferRef,const FRaftSimTotalDepthTransportResult& FV)
                    {
                        // Test-only finite flux fault exercises cumulative overflow;
                        // no physical solution or performance claim is made from it.
                        if(Case==8)AddClearUAVFloatPass(G,G.CreateUAV(FV.BoundaryFlux),3e38f);
                        return F;
                    };
                    FRaftSimTotalDepthBoundaryProvider Provider=[&](FRDGBuilder&,FRDGBufferRef,FRDGBufferRef,FRDGBufferRef)
                    {
                        ++Calls;auto T=Trace;
                        if((Case==1 && Calls==2) || (Case==2 && Calls==1) || (Case==5 && Calls%2==0) || (Case==6 && Calls==3))
                            T.Last().Y=std::numeric_limits<float>::quiet_NaN();
                        return FRaftSimTotalDepthBoundaryInput{Upload(Exterior,TEXT("BoundaryAdvance.Exterior")),
                            Upload(ExteriorBed,TEXT("BoundaryAdvance.ExteriorBed")),Upload(T,TEXT("BoundaryAdvance.Trace"))};
                    };
                    if(Case==9)Provider={}; // Dropping both arguments must still fail the GPU mode tag.
                    auto R=RaftSimAdvanceTotalDepthGPU(Graph,S,B,P,C,D,Size,.5f,false,true,Last?1:Batch,Limit,
                        SelectFraction,Error,Provider,Case==9?nullptr:V,Cull);
                    if(!R.State || !Error.IsEmpty()){Passed=false;Graph.Execute();return;}
                    if(Case==9)Passed &= R.BoundaryVolume==nullptr;
                    else Passed &= R.BoundaryVolume!=nullptr;
                    auto ReadVolume=R.BoundaryVolume?R.BoundaryVolume:V;
                    FRHIGPUBufferReadback SR(TEXT("BoundaryAdvance.SR")),PR(TEXT("BoundaryAdvance.PR")),
                        CR(TEXT("BoundaryAdvance.CR")),DR(TEXT("BoundaryAdvance.DR")),VR(TEXT("BoundaryAdvance.VR"));
                    FRHIGPUBufferReadback GoodFrame(TEXT("BoundaryAdvance.GoodFrame")),MissingFrame(TEXT("BoundaryAdvance.MissingFrame")),BadFrame(TEXT("BoundaryAdvance.BadFrame"));
                    if(Last && Case==0)
                    {
                        TArray<FVector2f> References;References.Init(FVector2f(0,1),N);auto Reference=Upload(References,TEXT("BoundaryAdvance.Reference"));
                        auto Valid=RaftSimResolveTotalDepthFrameGPU(Graph,R,Reference,Size,FVector2f(0,0),.5f,Error);
                        auto Without=R;Without.BoundaryVolume=nullptr;
                        auto Missing=RaftSimResolveTotalDepthFrameGPU(Graph,Without,Reference,Size,FVector2f(0,0),.5f,Error);
                        auto Corrupt=R;auto BadVolume=InitialVolume;BadVolume.Last().X=std::numeric_limits<float>::quiet_NaN();
                        Corrupt.BoundaryVolume=Upload(BadVolume,TEXT("BoundaryAdvance.BadFrameVolume"));
                        auto Bad=RaftSimResolveTotalDepthFrameGPU(Graph,Corrupt,Reference,Size,FVector2f(0,0),.5f,Error);
                        if(!Valid.Diagnostics || !Missing.Diagnostics || !Bad.Diagnostics){Passed=false;Graph.Execute();return;}
                        AddEnqueueCopyPass(Graph,&GoodFrame,Valid.Diagnostics,16);AddEnqueueCopyPass(Graph,&MissingFrame,Missing.Diagnostics,16);
                        AddEnqueueCopyPass(Graph,&BadFrame,Bad.Diagnostics,16);
                    }
                    if(Last || Case==0)
                    {
                        AddEnqueueCopyPass(Graph,&SR,R.State,N*16);AddEnqueueCopyPass(Graph,&PR,R.Progress,16);
                        AddEnqueueCopyPass(Graph,&CR,R.Summary,16);AddEnqueueCopyPass(Graph,&DR,R.Diagnostics,16);
                        AddEnqueueCopyPass(Graph,&VR,ReadVolume,NB*16);
                    }
                    Graph.QueueBufferExtraction(R.State,&State);Graph.QueueBufferExtraction(R.Progress,&Progress);
                    Graph.QueueBufferExtraction(R.Summary,&Summary);Graph.QueueBufferExtraction(R.Diagnostics,&Diagnostics);
                    Graph.QueueBufferExtraction(ReadVolume,&Volume);Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
                    if(!Last && Case==0)
                    {
                        const auto* Inventory=static_cast<const FVector4f*>(VR.Lock(NB*16));
                        const auto* Counts=static_cast<const uint32*>(CR.Lock(16));
                        Records.Add(FString::Printf(TEXT("boundary graph batch%d graph%d inventory%.12g/%.12g/%.12g/%.12g counts%u/%u/%u"),
                            Batch,GraphIndex,Inventory[0].X,Inventory[0].Y,Inventory[0].Z,Inventory[0].W,Counts[0],Counts[1],Counts[2]));
                        VR.Unlock();CR.Unlock();
                    }
                    if(Last)
                    {
                        if(Case==0)
                        {
                            const auto* Good=static_cast<const uint32*>(GoodFrame.Lock(16));
                            const auto* Missing=static_cast<const uint32*>(MissingFrame.Lock(16));
                            const auto* Bad=static_cast<const uint32*>(BadFrame.Lock(16));
                            if(!Good || !Missing || !Bad){Passed=false;return;}
                            Passed &= (Good[0]|Good[1]|Good[2]|Good[3])==0 && (Missing[3]&8u)!=0 && Bad[0]>0;
                            Records.Add(FString::Printf(TEXT("boundary frame batch%d good%u/%u/%u/%u missing%u bad%u"),
                                Batch,Good[0],Good[1],Good[2],Good[3],Missing[3],Bad[0]));
                            GoodFrame.Unlock();MissingFrame.Unlock();BadFrame.Unlock();
                        }
                        const void* A=SR.Lock(N*16);const void* Clock=PR.Lock(16);const void* Counts=CR.Lock(16);const void* Flags=DR.Lock(16);const void* Inventory=VR.Lock(NB*16);
                        if(!A || !Clock || !Counts || !Flags || !Inventory){Passed=false;return;}
                        Out.State.SetNumUninitialized(N);Out.Volume.SetNumUninitialized(NB);
                        FMemory::Memcpy(Out.State.GetData(),A,N*16);FMemory::Memcpy(Out.Volume.GetData(),Inventory,NB*16);
                        FMemory::Memcpy(&Out.Progress,Clock,16);FMemory::Memcpy(Out.Summary,Counts,16);FMemory::Memcpy(Out.Diagnostics,Flags,16);
                        SR.Unlock();PR.Unlock();CR.Unlock();DR.Unlock();VR.Unlock();
                    }
                }
            };
            FResult Split{},Batch{},Direct{};Run(1,Split);Run(4,Batch);Run(4,Direct,false);
            if(Split.State.Num()!=N || Batch.State.Num()!=N || Direct.State.Num()!=N){Passed=false;return;}
            const bool DirectExact=FMemory::Memcmp(Direct.State.GetData(),Batch.State.GetData(),N*16)==0 &&
                FMemory::Memcmp(Direct.Volume.GetData(),Batch.Volume.GetData(),NB*16)==0 &&
                FMemory::Memcmp(&Direct.Progress,&Batch.Progress,16)==0 &&
                FMemory::Memcmp(Direct.Summary,Batch.Summary,16)==0 && FMemory::Memcmp(Direct.Diagnostics,Batch.Diagnostics,16)==0;
            Passed &= DirectExact;
            Records.Add(FString::Printf(TEXT("boundary advance case%d indirect/direct five-record exact%d"),Case,DirectExact));
            Passed &= FMemory::Memcmp(Split.State.GetData(),Batch.State.GetData(),N*16)==0 &&
                FMemory::Memcmp(Split.Volume.GetData(),Batch.Volume.GetData(),NB*16)==0 &&
                FMemory::Memcmp(&Split.Progress,&Batch.Progress,16)==0 &&
                FMemory::Memcmp(Split.Summary,Batch.Summary,16)==0 && FMemory::Memcmp(Split.Diagnostics,Batch.Diagnostics,16)==0;
            if(Case==12)
            {
                Passed &= FMemory::Memcmp(Split.State.GetData(),Initial.GetData(),N*16)!=0;
                double FoamChange=0;
                for(int32 I=0;I<N;++I)
                {
                    Passed &= Split.State[I].X==Initial[I].X && Split.State[I].Y==Initial[I].Y && Split.State[I].Z==Initial[I].Z;
                    FoamChange+=double(Split.State[I].W)-Initial[I].W;
                }
                Passed &= FMath::Abs(FoamChange)<2e-7;
                Records.Add(FString::Printf(TEXT("boundary advected foam inventory change%.12g"),FoamChange));
            }
            else Passed &= FMemory::Memcmp(Split.State.GetData(),Initial.GetData(),N*16)==0;
            Records.Add(FString::Printf(TEXT("boundary partition case%d state%d volume%d clock%d summary%d diagnostics%d initial-state%d"),Case,
                FMemory::Memcmp(Split.State.GetData(),Batch.State.GetData(),N*16)==0,FMemory::Memcmp(Split.Volume.GetData(),Batch.Volume.GetData(),NB*16)==0,
                FMemory::Memcmp(&Split.Progress,&Batch.Progress,16)==0,FMemory::Memcmp(Split.Summary,Batch.Summary,16)==0,
                FMemory::Memcmp(Split.Diagnostics,Batch.Diagnostics,16)==0,FMemory::Memcmp(Split.State.GetData(),Initial.GetData(),N*16)==0));
            const uint32 Trials[]={3,3,1,1,0,3,2,2,2,1,1,3,3};
            const uint32 Accepted[]={3,2,0,1,0,0,1,1,1,1,1,3,3};
            const uint32 Status[]={1,1,2,4,1,4,2,2,2,2,2,2,1};
            Passed &= Split.Summary[0]==Trials[Case] && Split.Summary[1]==Accepted[Case] && Split.Summary[2]==Status[Case] && Split.Summary[3]==(Case==10?0u:1u);
            if(Seed)
            {
                Passed &= FMemory::Memcmp(Split.Volume.GetData(),InitialVolume.GetData(),NB*16)==0 && (Split.Diagnostics[2]&32u)!=0 && Split.Diagnostics[3]==0;
                Passed &= Split.Progress.X==InitialProgress[0].X && Split.Progress.Y==InitialProgress[0].Y && Split.Progress.Z==InitialProgress[0].Z && Split.Progress.W==0;
                Records.Add(FString::Printf(TEXT("boundary seed case%d inventory-exact%d clock %.9g/%.9g/%.9g/%.9g original %.9g/%.9g/%.9g/%.9g"),Case,
                    FMemory::Memcmp(Split.Volume.GetData(),InitialVolume.GetData(),NB*16)==0,Split.Progress.X,Split.Progress.Y,Split.Progress.Z,Split.Progress.W,
                    InitialProgress[0].X,InitialProgress[0].Y,InitialProgress[0].Z,InitialProgress[0].W));
            }
            else
            {
                const double Elapsed=double(Split.Progress.X)-InitialProgress[0].X+double(Split.Progress.Y)-InitialProgress[0].Y;
                for(int32 I=0;I<NB;++I)
                {
                    const double Expected=I<2*Size.Y?.75*Elapsed:0;
                    Passed &= FMath::Abs(Split.Volume[I].X-Expected)<2e-8 && FMath::Abs(Split.Volume[I].W-.25*Expected)<5e-9;
                    for(int32 K=0;K<4;++K)Passed &= FMath::IsFinite(Split.Volume[I][K]);
                }
                if(Accepted[Case]==0)Passed &= FMemory::Memcmp(Split.Volume.GetData(),InitialVolume.GetData(),NB*16)==0;
                Records.Add(FString::Printf(TEXT("boundary inventory case%d elapsed%.12g first-water%.12g first-foam%.12g zero-exact%d"),Case,Elapsed,
                    Split.Volume[0].X,Split.Volume[0].W,FMemory::Memcmp(Split.Volume.GetData(),InitialVolume.GetData(),NB*16)==0));
            }
            Records.Add(FString::Printf(TEXT("boundary advance case%d trials%u accepted%u status%u mode%u bits%u/%u/%u/%u; split/batch state-clock-ledger transaction"),
                Case,Split.Summary[0],Split.Summary[1],Split.Summary[2],Split.Summary[3],Split.Diagnostics[0],Split.Diagnostics[1],Split.Diagnostics[2],Split.Diagnostics[3]));
            Records.Add(FString::Printf(TEXT("boundary case%d passed%d"),Case,Passed));Passed &= PreviousPassed;
        }
        if(OnlyCase==12)
        {
        FRDGBuilder Invalid(Cmd);
        auto S=CreateStructuredBuffer(Invalid,TEXT("BoundaryAdvance.InvalidState"),Initial);
        auto B=CreateStructuredBuffer(Invalid,TEXT("BoundaryAdvance.InvalidBed"),Bed);
        TArray<FVector4f> Clock={FVector4f(0,0,.004f,.004f)},Volumes;Volumes.Init(FVector4f(0,0,0,0),NB);
        TArray<uint32> Counts={0,0,0,1},Flags={0,0,0,0};
        auto P=CreateStructuredBuffer(Invalid,TEXT("BoundaryAdvance.InvalidClock"),Clock);
        auto C=CreateStructuredBuffer(Invalid,TEXT("BoundaryAdvance.InvalidSummary"),Counts);
        auto D=CreateStructuredBuffer(Invalid,TEXT("BoundaryAdvance.InvalidDiagnostics"),Flags);
        auto V=CreateStructuredBuffer(Invalid,TEXT("BoundaryAdvance.InvalidVolume"),Volumes);
        auto F=CreateStructuredBuffer(Invalid,TEXT("BoundaryAdvance.InvalidFraction"),Fraction);
        int32 Calls=0;auto Select=[&](FRDGBuilder&,FRDGBufferRef,const FRaftSimTotalDepthTransportResult&){++Calls;return F;};
        FRaftSimTotalDepthBoundaryProvider Provider=[&](FRDGBuilder&,FRDGBufferRef,FRDGBufferRef,FRDGBufferRef)
        {++Calls;return FRaftSimTotalDepthBoundaryInput{};};
        for(int32 Fault=0;Fault<5;++Fault)
        {
            FString E;
            auto R=RaftSimAdvanceTotalDepthGPU(Invalid,S,B,P,Fault==1?nullptr:C,Fault==1?nullptr:D,Size,.5f,Fault==4,true,1,16,
                Select,E,Fault==2?FRaftSimTotalDepthBoundaryProvider{}:Provider,Fault==0?nullptr:Fault==3?F:V);
            Passed &= !R.State && !E.IsEmpty();
        }
        Passed &= Calls==0;Invalid.Execute();
        }
    });
    FlushRenderingCommands();
    };
    auto Finish=[this,Data]
    {
        TestTrue(TEXT("Boundary continuation is graph-partition invariant and rejects lost/corrupt/overflowed inventory atomically"),Data->Passed);
        for(const auto& R:Data->Records)AddInfo(R);if(!Data->Error.IsEmpty())AddError(Data->Error);
    };
    ADD_LATENT_AUTOMATION_COMMAND(FBoundaryAdvanceCases(MoveTemp(Work),MoveTemp(Finish)));
    return true;
}
#endif
