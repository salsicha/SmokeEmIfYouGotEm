#include "Misc/AutomationTest.h"
#include "RaftSimLiquidCompactAdjointGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidCompactAdjointTest,"RaftSim.Editor.LiquidCompactAdjointGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidCompactAdjointTest::RunTest(const FString&)
{
    if(GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Actual GPU required for shared compact-adjoint verification"));return false; }
    constexpr uint32 Capacity=6,Live=5,Cases=7;const FIntVector Cells(9,8,7);const FVector3f H(.8f,1.1f,1.3f);
    const uint32 Nodes=Cells.X*Cells.Y*Cells.Z;
    const TArray<FVector4f> Points={FVector4f(3.12f,3.84f,4.17f,1),FVector4f(3.23f,3.91f,4.29f,1),
        FVector4f(3.31f,3.73f,4.21f,1),FVector4f(1.6f,2.2f,2.6f,1),FVector4f(5.52f,6.38f,6.7f,1),FVector4f(0,0,0,0)};
    const TArray<FVector4f> Gradients={FVector4f(2,-3,1,1),FVector4f(-1,2,5,1),FVector4f(4,1,-2,1),
        FVector4f(.25f,-.5f,2,1),FVector4f(-2,3,.75f,1),FVector4f(0,0,0,0)};
    TArray<uint32> Mobility;Mobility.SetNum(Nodes);for(uint32 I=0;I<Nodes;++I) Mobility[I]=I%8;
    TArray<FVector> Expected;Expected.Init(FVector::ZeroVector,Nodes);
    auto B2=[](double R){const double A=FMath::Abs(R),Tail=FMath::Max(1.5-A,0.);return A<.5?.75-R*R:.5*Tail*Tail;};
    for(uint32 I=0;I<Nodes;++I)
    {
        FVector Node(I%Cells.X,(I/Cells.X)%Cells.Y,I/(Cells.X*Cells.Y));
        for(uint32 P=0;P<Live;++P)
        {
            const FVector R=Node-(FVector(FVector3f(Points[P]))/FVector(H)-FVector(.5));
            FVector T,N;for(int32 A=0;A<3;++A) { T[A]=FMath::Max(1-FMath::Abs(R[A]),0.);N[A]=.5*(B2(R[A]-.5)+B2(R[A]+.5)); }
            Expected[I]+=FVector(FVector3f(Gradients[P]))*FVector(N.X*T.Y*T.Z,T.X*N.Y*T.Z,T.X*T.Y*N.Z);
        }
        for(int32 A=0;A<3;++A) if((Mobility[I]&(1u<<A))==0) Expected[I][A]=0;
    }
    bool Passed=false;
    ENQUEUE_RENDER_COMMAND(RaftSimCompactAdjointTest)([&](FRHICommandListImmediate& Cmd)
    {
        FRDGBuilder Graph(Cmd);FString Error;TRefCountPtr<FRDGPooledBuffer> Fields[Cases],Diagnostics[Cases];
        for(uint32 Case=0;Case<Cases;++Case)
        {
            auto P=Points,G=Gradients;auto M=Mobility;
            if(Case==3) P[0]=FVector4f(0,0,0,1);
            if(Case==4) G[0].W=0;
            if(Case==5) M[4]=8;
            if(Case==6) { const uint32 NaN=0x7fc01234u;FMemory::Memcpy(&G[0].X,&NaN,4); }
            TArray<uint32> N={Case==1?0u:Case==2?Capacity+1:Live};
            auto PB=CreateStructuredBuffer(Graph,TEXT("AdjointTest.Positions"),TConstArrayView<FVector4f>(P));
            auto GB=CreateStructuredBuffer(Graph,TEXT("AdjointTest.Gradient"),TConstArrayView<FVector4f>(G));
            auto MB=CreateStructuredBuffer(Graph,TEXT("AdjointTest.Mobility"),TConstArrayView<uint32>(M));
            auto NB=CreateStructuredBuffer(Graph,TEXT("AdjointTest.Count"),TConstArrayView<uint32>(N));
            auto Result=RaftSimLiquidCompactAdjointGPU(Graph,PB,GB,NB,Capacity,MB,Cells,H,Error);
            if(!Result.Field || !Error.IsEmpty()) { Graph.Execute();return; }
            Graph.QueueBufferExtraction(Result.Field,&Fields[Case]);Graph.QueueBufferExtraction(Result.Diagnostics,&Diagnostics[Case]);
            if(Case==0 && (RaftSimLiquidCompactAdjointGPU(Graph,PB,GB,NB,Capacity+1,MB,Cells,H,Error).Field ||
                RaftSimLiquidCompactAdjointGPU(Graph,PB,GB,NB,Capacity,MB,Cells,{0,1,1},Error).Field ||
                RaftSimLiquidCompactAdjointGPU(Graph,PB,GB,NB,Capacity,MB,{MAX_int32,MAX_int32,MAX_int32},H,Error).Field ||
                RaftSimLiquidCompactAdjointGPU(Graph,PB,GB,NB,Capacity,MB,{8,8,7},H,Error).Field))
            { Graph.Execute();return; }
        }
        Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();Passed=true;
        for(uint32 Case=0;Case<Cases;++Case)
        {
            FRHIGPUBufferReadback Field(TEXT("AdjointTest.Field")),Diag(TEXT("AdjointTest.Diagnostics"));
            for(auto* B:{Fields[Case].GetReference(),Diagnostics[Case].GetReference()})
                Cmd.Transition(FRHITransitionInfo(B->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
            Field.EnqueueCopy(Cmd,Fields[Case]->GetRHI(),Nodes*16);Diag.EnqueueCopy(Cmd,Diagnostics[Case]->GetRHI(),24);
            Cmd.SubmitAndBlockUntilGPUIdle();
            const auto* F=static_cast<const FVector4f*>(Field.Lock(Nodes*16));const auto* D=static_cast<const uint32*>(Diag.Lock(24));
            if(!F || !D) { Passed=false;return; }
            const uint32 ExpectedDiagnostics[Cases][6]={{0,0,0,Live,Nodes,0},{0,0,0,0,Nodes,0},{1,0,0,0,0,0},
                {0,1,0,Live-1,0,0},{1,0,0,Live-1,0,0},{0,0,1,Live,Nodes-1,0},{1,0,0,Live-1,0,0}};
            Passed &= FMemory::Memcmp(D,ExpectedDiagnostics[Case],24)==0;
            for(uint32 I=0;I<Nodes;++I)
            {
                const bool Written=(Case==0 || Case==1 || (Case==5 && I!=4));
                const FVector ExpectedValue=(Case==0 || (Case==5 && I!=4))?Expected[I]:FVector::ZeroVector;
                Passed &= FVector(FVector3f(F[I])).Equals(ExpectedValue,2e-5) && F[I].W==(Written?1.f:0.f);
            }
            Field.Unlock();Diag.Unlock();
        }
    });
    FlushRenderingCommands();
    TestTrue(TEXT("Compact adjoint matches double reference at every anisotropic node with component mobility, zero/overflow counts, incomplete support and invalid fields"),Passed);
    return Passed;
}
#endif
