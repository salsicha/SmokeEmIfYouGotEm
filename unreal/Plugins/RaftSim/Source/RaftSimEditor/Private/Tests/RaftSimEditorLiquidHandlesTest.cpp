#include "Misc/AutomationTest.h"
#include "RaftSimLiquidParticleRoutingGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidHandlesTest,"RaftSim.Editor.LiquidParticleHandlesGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidHandlesTest::RunTest(const FString&)
{
    if(GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Actual GPU required for receiving persistent handles"));return false; }
    bool Passed=false;
    ENQUEUE_RENDER_COMMAND(RaftSimLiquidHandlesTest)([&](FRHICommandListImmediate& Cmd)
    {
        for(uint32 Mode=0;Mode<4;++Mode)
        {
            constexpr uint32 Owners=2,Slots=8,IDCount=6,NF=3,NI=4;
            TArray<uint32> Words;Words.Init(0,(NF+NI)*Slots);
            TArray<FUintVector2> Refs;Refs.Init(FUintVector2(MAX_uint32,MAX_uint32),Slots);
            // Owner0: two stayers, one incoming with colliding old index.
            // Owner1: one incoming, no stayers (previously empty receiver).
            Refs[0]={0,0};Refs[1]={1,0};Refs[2]={0,1};Refs[4]={0,2};
            const uint32 Index[4]={4,4,1,4},Tag[4]={27,29,0x80000005u,27},Position[4]={0,1,2,4};
            for(uint32 I=0;I<4;++I)
            {
                Words[(NF+1)*Slots+Position[I]]=Index[I];Words[(NF+2)*Slots+Position[I]]=Tag[I];
                Words[NF*Slots+Position[I]]=16777217+I;Words[(NF+3)*Slots+Position[I]]=0xffffffffu-I;
            }
            if(Mode==1) Words[(NF+1)*Slots+2]=4; // Duplicate staying ID.
            if(Mode==2) Words[(NF+1)*Slots]=IDCount; // Invalid staying ID.
            TArray<uint32> Counts={Mode==3?0u:3u,Mode==3?0u:1u},Gate={1,0,Mode==3?0u:4u,0};
            FRDGBuilder Graph(Cmd);FString Error;
            FRaftSimLiquidParticleAssembly A;A.TotalCapacity=Slots;A.FloatComponents=NF;A.IntComponents=NI;
            A.DestinationCapacities={4,4};
            auto UploadReadback=[&](const TCHAR* Name,const TArray<uint32>& Values)
            {
                auto Desc=FRDGBufferDesc::CreateStructuredDesc(4,Values.Num());Desc.Usage|=BUF_SourceCopy;
                auto Buffer=Graph.CreateBuffer(Desc,Name);Graph.QueueBufferUpload(Buffer,Values.GetData(),Values.Num()*4);return Buffer;
            };
            A.Words=UploadReadback(TEXT("HandlesTest.Words"),Words);
            A.References=CreateStructuredBuffer(Graph,TEXT("HandlesTest.Refs"),TConstArrayView<FUintVector2>(Refs));
            A.Counts=CreateStructuredBuffer(Graph,TEXT("HandlesTest.Counts"),TConstArrayView<uint32>(Counts));
            A.Control=UploadReadback(TEXT("HandlesTest.Control"),Gate);
            TArray<uint32> IDCapacities={IDCount,IDCount};
            auto H=RaftSimPrepareLiquidParticleHandles(Graph,A,IDCapacities,1,2,17,31,Error);
            if(!H.Handles || !Error.IsEmpty()) { Graph.Execute();return; }
            for(const uint32 Epoch:{0u,0x7fffffffu})
                if(RaftSimPrepareLiquidParticleHandles(Graph,A,IDCapacities,1,2,Epoch,31,Error).Handles)
                { Graph.Execute();return; }
            if(RaftSimPrepareLiquidParticleHandles(Graph,A,IDCapacities,1,2,17,0x80000000u,Error).Handles ||
                RaftSimPrepareLiquidParticleHandles(Graph,A,IDCapacities,1,1,17,31,Error).Handles)
            { Graph.Execute();return; }
            TRefCountPtr<FRDGPooledBuffer> Handles,Table,Free,FreeCounts,Control,Original;
            Graph.QueueBufferExtraction(H.Handles,&Handles);Graph.QueueBufferExtraction(H.IDToIndex,&Table);
            Graph.QueueBufferExtraction(H.FreeIDs,&Free);Graph.QueueBufferExtraction(H.FreeCounts,&FreeCounts);
            Graph.QueueBufferExtraction(A.Control,&Control);Graph.QueueBufferExtraction(A.Words,&Original);
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            auto Read=[&](FRDGPooledBuffer* B,uint32 Size,TArray<uint32>& Out)
            {
                FRHIGPUBufferReadback R(TEXT("HandlesTest.Readback"));
                Cmd.Transition(FRHITransitionInfo(B->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
                R.EnqueueCopy(Cmd,B->GetRHI(),Size);Cmd.SubmitAndBlockUntilGPUIdle();
                const auto* P=static_cast<const uint32*>(R.Lock(Size));if(!P) return false;
                Out.Append(P,Size/4);R.Unlock();return true;
            };
            TArray<uint32> HR,TR,FR,FC,GR,WR;
            if(!Read(Handles,Slots*8,HR) || !Read(Table,Owners*IDCount*4,TR) || !Read(Free,Owners*IDCount*4,FR) ||
                !Read(FreeCounts,Owners*4,FC) || !Read(Control,16,GR) || !Read(Original,Words.Num()*4,WR)) return;
            const bool Invalid=Mode==1 || Mode==2;
            if(GR[0]!=uint32(!Invalid) || GR[1]!=(Invalid?16u:0u) || WR!=Words) return;
            if(Invalid) continue;
            for(uint32 Owner=0;Owner<Owners;++Owner)
            {
                TSet<uint32> Used;
                for(uint32 I=0;I<Counts[Owner];++I)
                {
                    const uint32 P=Owner*4+I,IndexValue=HR[P*2],TagValue=HR[P*2+1];
                    if(IndexValue>=IDCount || Used.Contains(IndexValue) || TR[Owner*IDCount+IndexValue]!=I) return;
                    Used.Add(IndexValue);
                    if(Refs[P].X==Owner)
                    { if(IndexValue!=Words[(NF+1)*Slots+P] || TagValue!=Words[(NF+2)*Slots+P]) return; }
                    else if(TagValue!=0x80000011u) return;
                }
                if(FC[Owner]!=IDCount-Counts[Owner]) return;
                TSet<uint32> Unused;
                for(uint32 I=0;I<FC[Owner];++I)
                {
                    const uint32 IndexValue=FR[Owner*IDCount+I];
                    if(IndexValue>=IDCount || Used.Contains(IndexValue) || Unused.Contains(IndexValue) || TR[Owner*IDCount+IndexValue]!=MAX_uint32) return;
                    Unused.Add(IndexValue);
                }
                if(Used.Num()+Unused.Num()!=IDCount) return;
            }
        }
        Passed=true;
    });
    FlushRenderingCommands();
    TestTrue(TEXT("Stable staying handles, collision-free imported IDs/tags, complete disjoint free lists, untouched birth payload, invalid/duplicate IDs and namespace wrap rejection"),Passed);
    return Passed;
}
