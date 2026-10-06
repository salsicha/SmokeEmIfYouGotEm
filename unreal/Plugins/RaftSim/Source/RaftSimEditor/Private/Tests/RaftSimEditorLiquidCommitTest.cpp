#include "Misc/AutomationTest.h"
#include "RaftSimLiquidParticleRoutingGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include "Containers/ResourceArray.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidCommitTest,"RaftSim.Editor.LiquidParticleCommitGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidCommitTest::RunTest(const FString&)
{
    if(GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5) { AddError(TEXT("Actual GPU required"));return false; }
    bool Passed=false;
    ENQUEUE_RENDER_COMMAND(RaftSimLiquidCommitTest)([&](FRHICommandListImmediate& Cmd)
    {
        constexpr uint32 Slots=4,Stride=4,NF=3,NI=3,Sentinel=0x13579bdf;
        for(uint32 Mode=0;Mode<3;++Mode)
        {
            FRDGBuilder Graph(Cmd);FString Error;
            TArray<uint32> Words;Words.Init(0,Slots*(NF+NI));
            for(uint32 C=0;C<NF+NI;++C) { Words[C*Slots]=0x80000000u+C;Words[C*Slots+2]=0x7fc01000u+C; }
            const TArray<uint32> Live={1,1},Gate={Mode==1?0u:1u,Mode==1?16u:0u,2,0};
            const TArray<FIntVector2> Handles={{1,MIN_int32+1},{-1,-1},{0,42},{-1,-1}};
            const TArray<int32> Lookup={-1,0,0,-1};
            FRaftSimLiquidParticleAssembly A;A.TotalCapacity=Slots;A.FloatComponents=NF;A.IntComponents=NI;A.DestinationCapacities={2,2};
            A.Words=CreateStructuredBuffer(Graph,TEXT("CommitTest.Words"),TConstArrayView<uint32>(Words));
            A.Counts=CreateStructuredBuffer(Graph,TEXT("CommitTest.Counts"),TConstArrayView<uint32>(Live));
            A.Control=CreateStructuredBuffer(Graph,TEXT("CommitTest.Control"),TConstArrayView<uint32>(Gate));
            FRaftSimLiquidParticleHandles H;H.TotalIDs=4;H.IDCapacities={2,2};
            H.Handles=CreateStructuredBuffer(Graph,TEXT("CommitTest.Handles"),TConstArrayView<FIntVector2>(Handles));
            H.IDToIndex=CreateStructuredBuffer(Graph,TEXT("CommitTest.IDLookup"),TConstArrayView<int32>(Lookup));
            FRWBuffer Floats[2],Integers[2],IDs[2],NativeCounts;
            TResourceArray<uint32> Initial;Initial.Init(Sentinel,Stride*NF);
            TResourceArray<uint32> InitialIDs;InitialIDs.Init(Sentinel,4);
            TResourceArray<uint32> InitialCounts;InitialCounts.Init(99,4);
            NativeCounts.Initialize(Cmd,TEXT("CommitTest.NativeCounts"),4,4,PF_R32_UINT,ERHIAccess::UAVCompute,BUF_Static|BUF_SourceCopy,&InitialCounts);
            TArray<FRaftSimLiquidNativeParticleTarget> Targets;
            for(uint32 O=0;O<2;++O)
            {
                Initial.Init(Sentinel,Stride*NF);InitialIDs.Init(Sentinel,4);
                Floats[O].Initialize(Cmd,TEXT("CommitTest.NativeFloats"),4,Stride*NF,PF_R32_FLOAT,ERHIAccess::SRVMask,BUF_Static|BUF_SourceCopy,&Initial);
                Initial.Init(Sentinel,Stride*NI);
                Integers[O].Initialize(Cmd,TEXT("CommitTest.NativeIntegers"),4,Stride*NI,PF_R32_SINT,ERHIAccess::SRVMask,BUF_Static|BUF_SourceCopy,&Initial);
                IDs[O].Initialize(Cmd,TEXT("CommitTest.NativeIDs"),4,4,PF_R32_SINT,ERHIAccess::SRVCompute,BUF_Static|BUF_SourceCopy,&InitialIDs);
                auto& T=Targets.AddDefaulted_GetRef();T.Capacity=2;T.FloatStride=Stride;T.IntStride=Stride;T.IDCapacity=4;T.CountOffset=1+2*O;
                T.Floats=Floats[O].UAV;T.Integers=Integers[O].UAV;T.IDToIndex=IDs[O].UAV;T.NativeCounts=NativeCounts.UAV;
            }
            auto Bad=Targets;Bad[1].CountOffset=Bad[0].CountOffset;
            if(RaftSimCommitLiquidParticleAssembly(Graph,A,H,Bad,1,2,Error)) { Graph.Execute();return; }
            if(Mode==2) Targets[1]={}; // Nonempty incoming destination has no native allocation.
            if(!RaftSimCommitLiquidParticleAssembly(Graph,A,H,Targets,1,2,Error)) { Graph.Execute();return; }
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            auto Read=[&](FRWBuffer& B,TArray<uint32>& Out)
            {
                FRHIGPUBufferReadback R(TEXT("CommitTest.Read"));
                Cmd.Transition(FRHITransitionInfo(B.Buffer,ERHIAccess::Unknown,ERHIAccess::CopySrc));
                R.EnqueueCopy(Cmd,B.Buffer,B.NumBytes);Cmd.SubmitAndBlockUntilGPUIdle();
                const auto* P=static_cast<const uint32*>(R.Lock(B.NumBytes));if(!P) return false;
                Out.Append(P,B.NumBytes/4);R.Unlock();return true;
            };
            TArray<uint32> Counter;if(!Read(NativeCounts,Counter)) return;
            for(uint32 I=0;I<4;++I) if(Counter[I]!=(Mode==0 && (I==1 || I==3)?1u:99u)) return;
            for(uint32 O=0;O<2;++O)
            {
                TArray<uint32> F,I,T;if(!Read(Floats[O],F) || !Read(Integers[O],I) || !Read(IDs[O],T)) return;
                for(uint32 C=0;C<NF;++C) for(uint32 J=0;J<Stride;++J)
                    if(F[C*Stride+J]!=(Mode==0 && J==0?Words[C*Slots+O*2]:Sentinel)) return;
                for(uint32 C=0;C<NI;++C) for(uint32 J=0;J<Stride;++J)
                {
                    uint32 Expected=Sentinel;
                    if(Mode==0 && J==0) Expected=C==1?uint32(Handles[O*2].X):C==2?uint32(Handles[O*2].Y):Words[(NF+C)*Slots+O*2];
                    if(I[C*Stride+J]!=Expected) return;
                }
                for(uint32 J=0;J<4;++J)
                    if(T[J]!=(Mode==0?(J<2?uint32(Lookup[O*2+J]):MAX_uint32):Sentinel)) return;
            }
        }
        Passed=true;
    });
    FlushRenderingCommands();TestTrue(TEXT("Native all-state/count/ID commit; unchanged sinks on invalid handles or missing destination; no counter alias or tail corruption"),Passed);return Passed;
}
