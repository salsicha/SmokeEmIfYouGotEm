#include "Misc/AutomationTest.h"
#include "RaftSimLiquidParticleExitGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidExitTest,"RaftSim.Editor.LiquidParticleExitGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidExitTest::RunTest(const FString&)
{
    if(GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Actual GPU required for physical exit classification"));return false; }
    bool Passed=false;
    ENQUEUE_RENDER_COMMAND(RaftSimLiquidExitTest)([&](FRHICommandListImmediate& Cmd)
    {
        constexpr uint32 Capacity=16,NF=7,NI=2;
        const FVector Lower(1000,2000,100),X(0,1,0),Y(-1,0,0);
        const FVector3f Starts[Capacity]={{190,25,50},{390,25,50},{10,25,50},{390,125,50},
            {390,175,50},{390,225,50},{390,25,10},{390,25,190},{390,390,50},
            {410,25,50},{100,25,50},{390,25,50},{25,390,50},{390,300,50},{100,25,50},{100,25,50}};
        const FVector3f Ends[Capacity]={{210,25,50},{410,25,50},{-10,25,50},{410,125,50},
            {410,175,50},{410,225,50},{410,25,-30},{410,25,230},{410,410,50},
            {420,25,50},{110,25,50},{400,25,50},{25,410,50},{450,500,50},{110,25,50},{110,25,50}};
        TArray<uint32> Words;Words.SetNumZeroed(Capacity*(NF+NI));TArray<FUintVector4> Routes;
        for(uint32 I=0;I<Capacity;++I)
        {
            for(uint32 Phase=0;Phase<2;++Phase)
            {
                const auto Local=Phase?Starts[I]:Ends[I];
                const FVector3f World=FVector3f(Lower+X*Local.X+Y*Local.Y+FVector(0,0,Local.Z));
                for(uint32 A=0;A<3;++A) { const float Value=World[A];FMemory::Memcpy(&Words[(3*Phase+A)*Capacity+I],&Value,4); }
            }
            const bool Inside=Ends[I].X>=0 && Ends[I].X<=400 && Ends[I].Y>=0 && Ends[I].Y<=400;
            Routes.Emplace(Inside?3u:MAX_uint32,I==14?1u:0u,I,Inside?1u:2u);
            Words[6*Capacity+I]=0x7fc01234u+I; // Non-position payload must remain untouched.
            Words[7*Capacity+I]=16777217u+I;Words[8*Capacity+I]=0x80000000u+I;
        }
        Words[3*Capacity+10]=0x7fc01234u; // Invalid previous endpoint.
        FRDGBuilder Graph(Cmd);FString Error;
        const TArray<FIntRect> Regions={{0,0,4,4},{4,0,8,4},{0,4,4,8},{4,4,8,8}};
        auto Routing=RaftSimBuildLiquidParticleRoutePlan(Graph,{8,8},Regions,Lower,X,Y,{50,50},Error);
        TArray<FVector3f> Rows;Rows.Init({120,200,-100},32);
        for(uint32 I=0;I<8;++I) Rows[I].Z=100; // West is an inlet, not an outgoing pressure face.
        Rows[10]={160,150,-100};Rows[11]={170,200,-100};Rows[12]={120,140,-100};
        auto Plan=RaftSimBuildLiquidParticleExitPlan(Graph,Routing,200,Rows,Error);
        if(!Plan.FaceRows) { Graph.Execute();return; }
        FRaftSimLiquidFaceBed Bed;
        for(int32 Face=0;Face<4;++Face)
        {
            Bed.Offsets[Face]=Bed.Knots.Num();
            if(Face==1) Bed.Knots.Append({{0,120},{125,160},{150,170},{175,140},{200,155},{225,160},{250,120},{400,120}});
            else Bed.Knots.Append({{0,120},{400,120}});
            Bed.Counts[Face]=Bed.Knots.Num()-Bed.Offsets[Face];
        }
        auto ExactRows=Rows;ExactRows[12].Y=200; // Row wet, but particle genuinely below pointwise bed.
        auto ExactPlan=RaftSimBuildLiquidParticleExitPlan(Graph,Routing,200,ExactRows,Error,&Bed);
        if(!ExactPlan.FaceRows) { Graph.Execute();return; }
        for(int32 InvalidCase=0;InvalidCase<4;++InvalidCase)
        {
            auto BadBed=Bed;
            if(InvalidCase==0) BadBed.Knots[1].X=399;
            if(InvalidCase==1) BadBed.Offsets[1]+=1;
            if(InvalidCase==2) BadBed.Knots[Bed.Offsets[1]+1].X=0;
            if(InvalidCase==3) BadBed.Counts[3]=1;
            if(RaftSimBuildLiquidParticleExitPlan(Graph,Routing,200,Rows,Error,&BadBed).FaceRows)
            { Graph.Execute();return; }
        }
        auto BadRows=Rows;BadRows.Pop();
        if(RaftSimBuildLiquidParticleExitPlan(Graph,Routing,200,BadRows,Error).FaceRows ||
            RaftSimBuildLiquidParticleExitPlan(Graph,Routing,0,Rows,Error).FaceRows)
        { Graph.Execute();return; }
        const uint32 NaN=0x7fc01234u;FMemory::Memcpy(&BadRows[0].X,&NaN,4);BadRows.Add(Rows.Last());
        if(RaftSimBuildLiquidParticleExitPlan(Graph,Routing,200,BadRows,Error).FaceRows)
        { Graph.Execute();return; }
        auto WordsDesc=FRDGBufferDesc::CreateStructuredDesc(4,Words.Num());WordsDesc.Usage|=BUF_SourceCopy;
        auto NativeWords=Graph.CreateBuffer(WordsDesc,TEXT("ExitTest.FullNativeWords"));
        Graph.QueueBufferUpload(NativeWords,Words.GetData(),Words.Num()*4,ERDGInitialDataFlags::None);
        auto NativeRoutes=CreateStructuredBuffer(Graph,TEXT("ExitTest.NativeRoutes"),TConstArrayView<FUintVector4>(Routes));
        auto TraceDesc=FRDGBufferDesc::CreateStructuredDesc(4,RaftSimLiquidExitTraceWords);TraceDesc.Usage|=BUF_SourceCopy;
        auto Trace=Graph.CreateBuffer(TraceDesc,TEXT("ExitTest.FirstRejection"));AddClearUAVPass(Graph,Graph.CreateUAV(Trace),0);
        Plan.FirstRejectionTrace=Trace;ExactPlan.FirstRejectionTrace=Trace;
        TRefCountPtr<FRDGPooledBuffer> TraceResult;
        Graph.QueueBufferExtraction(Trace,&TraceResult);
        TRefCountPtr<FRDGPooledBuffer> Records[4],Counts[4],Original;
        Graph.QueueBufferExtraction(NativeWords,&Original);
        const uint32 Live[4]={15,0,17,15};
        for(uint32 Case=0;Case<4;++Case)
        {
            Plan.NativeStep=37+Case;ExactPlan.NativeStep=37+Case;
            // Source routing counts are independently checked by assembly. This
            // classifier always preserves the full native live count, including overflow.
            TArray<uint32> SourceCounts;SourceCounts.Init(0,7);SourceCounts[6]=Live[Case];
            FRaftSimLiquidParticleRoutePacket Packet;
            Packet.Capacity=Capacity;Packet.FloatComponents=NF;Packet.IntComponents=NI;
            Packet.Words=NativeWords;Packet.Routes=NativeRoutes;
            Packet.Counts=CreateStructuredBuffer(Graph,TEXT("ExitTest.SourceCounts"),TConstArrayView<uint32>(SourceCounts));
            if(RaftSimClassifyLiquidParticleExits(Graph,Plan,Packet,0,0,0,1.f/48,Error).Records ||
                RaftSimClassifyLiquidParticleExits(Graph,Plan,Packet,4,0,3,1.f/48,Error).Records ||
                RaftSimClassifyLiquidParticleExits(Graph,Plan,Packet,0,0,5,1.f/48,Error).Records ||
                RaftSimClassifyLiquidParticleExits(Graph,Plan,Packet,0,0,3,0,Error).Records)
            { Graph.Execute();return; }
            const auto Out=RaftSimClassifyLiquidParticleExits(Graph,Case==3?ExactPlan:Plan,Packet,0,0,3,1.f/48,Error);
            if(!Out.Records || !Error.IsEmpty()) { Graph.Execute();return; }
            Graph.QueueBufferExtraction(Out.Records,&Records[Case]);Graph.QueueBufferExtraction(Out.Counts,&Counts[Case]);
        }
        Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
        const uint32 Status[Capacity]={1,2,4,4,4,2,4,4,4,8,8,1,2,2,8,1};
        const uint32 Faces[Capacity]={MAX_uint32,1,0,1,1,1,4,5,1,MAX_uint32,MAX_uint32,MAX_uint32,3,1,MAX_uint32,MAX_uint32};
        const uint32 FaceRow[Capacity]={MAX_uint32,8,0,10,11,12,MAX_uint32,MAX_uint32,MAX_uint32,MAX_uint32,MAX_uint32,MAX_uint32,24,14,MAX_uint32,MAX_uint32};
        const uint32 Expected[4][8]={{2,0,3,0,1,6,3,15},{0,0,0,0,0,0,0,0},{3,0,3,0,1,6,4,17},{2,0,3,0,1,6,3,15}};
        for(uint32 Case=0;Case<4;++Case)
        {
            FRHIGPUBufferReadback A(TEXT("ExitTest.Candidates")),B(TEXT("ExitTest.Counts"));
            for(auto* Buffer:{Records[Case].GetReference(),Counts[Case].GetReference()})
                Cmd.Transition(FRHITransitionInfo(Buffer->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
            A.EnqueueCopy(Cmd,Records[Case]->GetRHI(),Capacity*16);B.EnqueueCopy(Cmd,Counts[Case]->GetRHI(),32);
            Cmd.SubmitAndBlockUntilGPUIdle();
            const auto* R=static_cast<const FUintVector4*>(A.Lock(Capacity*16));
            const auto* C=static_cast<const uint32*>(B.Lock(32));if(!R || !C) return;
            bool Exact=FMemory::Memcmp(C,Expected[Case],32)==0;
            if(!Exact) for(uint32 I=0;I<8;++I)
                if(C[I]!=Expected[Case][I]) UE_LOG(LogTemp,Error,TEXT("Exit case%u count%u got%u expected%u"),Case,I,C[I],Expected[Case][I]);
            for(uint32 I=0;I<Capacity;++I)
            {
                const bool Active=I<Live[Case];
                const uint32 ExpectedStatus=Case==3 && I==4?2:Case==3 && I==5?4:Status[I];
                const bool RecordOK=R[I].X==(Active?ExpectedStatus:0) && R[I].Y==(Active?Faces[I]:MAX_uint32) && R[I].Z==(Active?FaceRow[I]:MAX_uint32);
                if(!RecordOK) UE_LOG(LogTemp,Error,TEXT("Exit case%u particle%u got status/face/row %u/%u/%u"),Case,I,R[I].X,R[I].Y,R[I].Z);
                Exact &= RecordOK;
                if(Active && ExpectedStatus==2)
                {
                    float Fraction=0;FMemory::Memcpy(&Fraction,&R[I].W,4);
                    Exact &= FMath::IsNearlyEqual(Fraction,I==13?1.f/6.f:.5f,1e-6f);
                }
            }
            A.Unlock();B.Unlock();if(!Exact) return;
        }
        FRHIGPUBufferReadback Read(TEXT("ExitTest.UnchangedNativeWords"));
        Cmd.Transition(FRHITransitionInfo(Original->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
        Read.EnqueueCopy(Cmd,Original->GetRHI(),Words.Num()*4);Cmd.SubmitAndBlockUntilGPUIdle();
        const auto* Data=Read.Lock(Words.Num()*4);if(!Data) return;
        Passed=FMemory::Memcmp(Data,Words.GetData(),Words.Num()*4)==0;Read.Unlock();
        FRHIGPUBufferReadback TraceRead(TEXT("ExitTest.FirstRejectionContents"));
        Cmd.Transition(FRHITransitionInfo(TraceResult->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
        TraceRead.EnqueueCopy(Cmd,TraceResult->GetRHI(),RaftSimLiquidExitTraceWords*4);Cmd.SubmitAndBlockUntilGPUIdle();
        const auto* T=static_cast<const uint32*>(TraceRead.Lock(RaftSimLiquidExitTraceWords*4));
        if(!T) { Passed=false;return; }
        // The winning rejected index is intentionally unspecified, but must
        // belong to the FIRST dispatch and preserve its complete raw payload.
        const uint32 I=T[3];
        Passed &= T[0]==37 && T[1]==1 && T[2]==0 && I<15 && T[5]==NF && T[6]==NI && T[7]==0 && T[8]==3 && T[13]==15;
        if(I<15)
        {
            Passed &= (Status[I]==4 || Status[I]==8) && T[14]==Status[I] && T[9]==Faces[I] && T[10]==FaceRow[I];
            for(uint32 K=0;K<NF+NI;++K) Passed &= T[64+K]==Words[K*Capacity+I];
        }
        TraceRead.Unlock();
    });
    FlushRenderingCommands();
    TestTrue(TEXT("Rotated physical exits, internal cuts, wet/dry/bed rows, above-stage spray, first floor/roof/corner hit, invalid origins/routes, empty/overflow accounting and unchanged full payload"),Passed);
    return Passed;
}
