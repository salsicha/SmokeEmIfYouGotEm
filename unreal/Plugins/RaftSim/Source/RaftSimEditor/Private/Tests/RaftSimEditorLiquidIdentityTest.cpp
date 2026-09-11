#include "Misc/AutomationTest.h"
#include "RaftSimLiquidParticleIdentityGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include "Containers/ResourceArray.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidIdentityTest,"RaftSim.Editor.LiquidIdentityGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidIdentityTest::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Actual GPU required for exact integer particle identities"));return false; }
    constexpr uint32 Capacity=5,Stride=8,Components=6;
    const FIntVector4 Offsets(4,1,5,2);
    TResourceArray<int32> Input;
    Input.SetAllowCPUAccess(true); // CPU reference must survive the native upload.
    Input.SetNumZeroed(Stride*Components);
    const int32 Sequence[Capacity]={0,16777217,MAX_int32,MIN_int32,-1};
    for (uint32 I=0;I<Capacity;++I)
    {
        Input[4*Stride+I]=int32(I*997);
        Input[Stride+I]=Sequence[I];Input[5*Stride+I]=int32(uint32(Sequence[I])^0x12345678u);
        Input[2*Stride+I]=int32(Capacity-I);
    }
    bool Passed=false;
    ENQUEUE_RENDER_COMMAND(RaftSimLiquidIdentityTest)([&](FRHICommandListImmediate& Cmd)
    {
        FRWBuffer Native;
        Native.Initialize(Cmd,TEXT("IdentityNativeInts"),4,Input.Num(),PF_R32_SINT,ERHIAccess::SRVCompute,BUF_Static,&Input);
        const uint32 LiveCounts[3]={4,0,7};
        for (int32 Mode=0;Mode<2;++Mode)
        {
            TResourceArray<uint32> CountsData;CountsData.Append(LiveCounts,3);
            FRWBuffer NativeCounts;
            NativeCounts.Initialize(Cmd,TEXT("IdentityNativeCounts"),4,3,PF_R32_UINT,
                Mode?ERHIAccess::UAVCompute:ERHIAccess::SRVCompute,BUF_Static,&CountsData);
            FRDGBuilder Graph(Cmd);
            TRefCountPtr<FRDGPooledBuffer> Packed[3],Counts[3];
            for (uint32 C=0;C<3;++C)
            {
                FRDGBufferRef Count=nullptr;
                auto Result=RaftSimPackLiquidIdentityGPU(Graph,Native.SRV,NativeCounts.SRV,Mode?NativeCounts.UAV.GetReference():nullptr,
                    Stride,Components,Offsets,C,Capacity,Count);
                if (!Result || !Count) { Graph.Execute();return; }
                Graph.QueueBufferExtraction(Result,&Packed[C]);Graph.QueueBufferExtraction(Count,&Counts[C]);
            }
            FRDGBufferRef Invalid=nullptr;
            auto Bad=Offsets;Bad.X=Components;
            if (RaftSimPackLiquidIdentityGPU(Graph,Native.SRV,NativeCounts.SRV,nullptr,Stride,Components,Bad,0,Capacity,Invalid) || Invalid ||
                RaftSimPackLiquidIdentityGPU(Graph,Native.SRV,NativeCounts.SRV,nullptr,Capacity-1,Components,Offsets,0,Capacity,Invalid) ||
                RaftSimPackLiquidIdentityGPU(Graph,Native.SRV,NativeCounts.SRV,nullptr,MAX_uint32,Components,Offsets,0,Capacity,Invalid) ||
                RaftSimPackLiquidIdentityGPU(Graph,nullptr,NativeCounts.SRV,nullptr,Stride,Components,Offsets,0,Capacity,Invalid))
            { Graph.Execute();return; }
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            for (uint32 C=0;C<3;++C)
            {
                FRHIGPUBufferReadback IdRead(TEXT("IdentityExactRead")),CountRead(TEXT("IdentityCountRead"));
                Cmd.Transition(FRHITransitionInfo(Packed[C]->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
                Cmd.Transition(FRHITransitionInfo(Counts[C]->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
                IdRead.EnqueueCopy(Cmd,Packed[C]->GetRHI(),Capacity*16);CountRead.EnqueueCopy(Cmd,Counts[C]->GetRHI(),4);
                Cmd.SubmitAndBlockUntilGPUIdle();
                const auto* Ids=static_cast<const FIntVector4*>(IdRead.Lock(Capacity*16));
                const auto* Count=static_cast<const uint32*>(CountRead.Lock(4));
                if (!Ids || !Count) return;
                bool Exact=*Count==LiveCounts[C]; // Over-capacity evidence must not be clamped away.
                for (uint32 I=0;I<Capacity;++I)
                {
                    FIntVector4 Expected(0,0,0,0);
                    if (I<LiveCounts[C]) for (int32 A=0;A<4;++A) Expected[A]=Input[Offsets[A]*Stride+I];
                    Exact &= FMemory::Memcmp(&Ids[I],&Expected,16)==0;
                }
                IdRead.Unlock();CountRead.Unlock();if (!Exact) return;
            }
        }
        {
            // Native neighbor buffers have SRV access but no copy-source flag.
            // Preserve every signed bit through the shader snapshot instead.
            FRDGBuilder Graph(Cmd);
            auto Desc=FRDGBufferDesc::CreateBufferDesc(4,Input.Num());Desc.Usage&=~BUF_SourceCopy;
            auto* Source=Graph.CreateBuffer(Desc,TEXT("IdentitySnapshotNoCopySource"));
            Graph.QueueBufferUpload(Source,Input.GetData(),Input.Num()*4,ERDGInitialDataFlags::None);
            auto* View=Graph.CreateSRV(Source,PF_R32_SINT);
            auto* Copy=RaftSimSnapshotLiquidIntegersGPU(Graph,View,Input.Num());
            if (!Copy || RaftSimSnapshotLiquidIntegersGPU(Graph,nullptr,Input.Num()) ||
                RaftSimSnapshotLiquidIntegersGPU(Graph,View,0) ||
                RaftSimSnapshotLiquidIntegersGPU(Graph,View,Input.Num()+1) ||
                RaftSimSnapshotLiquidIntegersGPU(Graph,Graph.CreateSRV(Source,PF_R32_UINT),Input.Num()))
            { Graph.Execute();return; }
            TRefCountPtr<FRDGPooledBuffer> Retained;Graph.QueueBufferExtraction(Copy,&Retained);
            Graph.Execute();
            FRHIGPUBufferReadback Read(TEXT("IdentityIntegerSnapshotRead"));
            Cmd.Transition(FRHITransitionInfo(Retained->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
            Read.EnqueueCopy(Cmd,Retained->GetRHI(),Input.Num()*4);Cmd.SubmitAndBlockUntilGPUIdle();
            const void* Values=Read.Lock(Input.Num()*4);
            if (!Values) return;
            const bool Exact=FMemory::Memcmp(Values,Input.GetData(),Input.Num()*4)==0;
            Read.Unlock();if (!Exact) return;
        }
        Passed=true;
    });
    FlushRenderingCommands();
    TestTrue(TEXT("Exact signed 32-bit IDs beyond float precision, padded/reordered planes, empty and overflow counts, both native count bindings"),Passed);
    return Passed;
}
