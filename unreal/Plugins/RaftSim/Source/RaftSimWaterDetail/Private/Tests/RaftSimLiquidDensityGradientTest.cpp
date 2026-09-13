#include "Misc/AutomationTest.h"
#include "RaftSimLiquidDensityGradientGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidDensityGradientTest,"RaftSim.Editor.LiquidDensityGradientGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidDensityGradientTest::RunTest(const FString&)
{
    if(GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Actual GPU required for density-gradient verification"));return false; }
    constexpr uint32 Capacity=6;const FIntVector Cells(8,7,6);const FVector3f H(.8f,1.1f,1.3f);
    const TArray<FVector4f> Points={FVector4f(2.12f,3.24f,4.17f,2.1f),FVector4f(2.23f,3.11f,4.29f,2.3f),
        FVector4f(2.31f,3.33f,4.21f,2.2f),FVector4f(0,0,0,1),FVector4f(2.12f,3.24f,4.17f,0),FVector4f(4.24f,5.23f,6.17f,1)};
    TArray<FVector2f> Field;Field.Init(FVector2f::ZeroVector,Cells.X*Cells.Y*Cells.Z);
    auto Linear=[&](FIntVector I){return I.X+Cells.X*(I.Y+Cells.Y*I.Z);};
    auto Stencil=[&](const FVector4f& Particle,auto&& Visit)
    {
        const FVector Q=FVector(FVector3f(Particle))/FVector(H)-FVector(.5);
        const FIntVector Lo(FMath::FloorToInt(Q.X),FMath::FloorToInt(Q.Y),FMath::FloorToInt(Q.Z));
        const FVector T=Q-FVector(Lo);
        for(int32 Z=0;Z<2;++Z) for(int32 Y=0;Y<2;++Y) for(int32 X=0;X<2;++X)
        {
            FVector W(X?T.X:1-T.X,Y?T.Y:1-T.Y,Z?T.Z:1-T.Z);
            FVector D((2*X-1)*W.Y*W.Z/H.X,(2*Y-1)*W.X*W.Z/H.Y,(2*Z-1)*W.X*W.Y/H.Z);
            Visit(Linear(Lo+FIntVector(X,Y,Z)),W.X*W.Y*W.Z,D);
        }
    };
    for(int32 Z=2;Z<4;++Z) for(int32 Y=2;Y<4;++Y) for(int32 X=1;X<4;++X) Field[Linear({X,Y,Z})].Y=.57f;
    const double CellVolume=double(H.X)*H.Y*H.Z;
    TArray<double> Density;Density.Init(0,Field.Num());
    for(uint32 I=0;I<3;++I) Stencil(Points[I],[&](int32 Node,double W,FVector){Density[Node]+=Points[I].W/CellVolume*W;});
    for(int32 I=0;I<Field.Num();++I) Field[I].X=float(Density[I]);
    TArray<FVector> ExpectedG,ExpectedD;ExpectedG.Init(FVector::ZeroVector,Capacity);ExpectedD=ExpectedG;
    for(uint32 I=0;I<3;++I) Stencil(Points[I],[&](int32 Node,double,FVector D)
    {
        const double Excess=FMath::Max(double(Field[Node].X)+Field[Node].Y-1,0.);
        const FVector J=Points[I].W/CellVolume*D;ExpectedG[I]+=Excess*J;
        if(Excess>0) ExpectedD[I]+=J*J;
    });
    bool Passed=false;
    ENQUEUE_RENDER_COMMAND(RaftSimDensityGradientTest)([&](FRHICommandListImmediate& Cmd)
    {
        FRDGBuilder Graph(Cmd);FString Error;
        auto Positions=CreateStructuredBuffer(Graph,TEXT("DensityTest.Positions"),TConstArrayView<FVector4f>(Points));
        auto Density=CreateStructuredBuffer(Graph,TEXT("DensityTest.Field"),TConstArrayView<FVector2f>(Field));
        auto BadField=Field;const uint32 NaN=0x7fc01234u;FMemory::Memcpy(&BadField[Linear({2,2,2})].X,&NaN,4);
        auto InvalidField=CreateStructuredBuffer(Graph,TEXT("DensityTest.InvalidField"),TConstArrayView<FVector2f>(BadField));
        TRefCountPtr<FRDGPooledBuffer> Gradients[4],Diagonals[4],Diagnostics[4];
        for(uint32 Case=0;Case<4;++Case)
        {
            TArray<uint32> Counts={Case==1?0u:Case==2?Capacity+1:Capacity};
            auto Count=CreateStructuredBuffer(Graph,TEXT("DensityTest.Count"),TConstArrayView<uint32>(Counts));
            auto Result=RaftSimLiquidDensityGradientGPU(Graph,Positions,Count,Capacity,Case==3?InvalidField:Density,Cells,H,Error);
            if(!Result.Gradient || !Error.IsEmpty()) { Graph.Execute();return; }
            Graph.QueueBufferExtraction(Result.Gradient,&Gradients[Case]);Graph.QueueBufferExtraction(Result.Diagonal,&Diagonals[Case]);
            Graph.QueueBufferExtraction(Result.Diagnostics,&Diagnostics[Case]);
            if(RaftSimLiquidDensityGradientGPU(Graph,Positions,Count,Capacity+1,Density,Cells,H,Error).Gradient ||
                RaftSimLiquidDensityGradientGPU(Graph,Positions,Count,Capacity,Density,Cells,{0,1,1},Error).Gradient ||
                RaftSimLiquidDensityGradientGPU(Graph,Positions,Count,Capacity,Density,{MAX_int32,MAX_int32,MAX_int32},H,Error).Gradient ||
                RaftSimLiquidDensityGradientGPU(Graph,Positions,Count,Capacity,Density,{8,7,5},H,Error).Gradient)
            { Graph.Execute();return; }
        }
        Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();Passed=true;
        const uint32 Totals[4][4]={{1,1,0,4},{0,0,0,0},{1,0,0,0},{1,1,3,1}};
        for(uint32 Case=0;Case<4;++Case)
        {
            FRHIGPUBufferReadback G(TEXT("DensityTest.Gradient")),D(TEXT("DensityTest.Diagonal")),C(TEXT("DensityTest.Diagnostics"));
            for(auto* Buffer:{Gradients[Case].GetReference(),Diagonals[Case].GetReference(),Diagnostics[Case].GetReference()})
                Cmd.Transition(FRHITransitionInfo(Buffer->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
            G.EnqueueCopy(Cmd,Gradients[Case]->GetRHI(),Capacity*16);D.EnqueueCopy(Cmd,Diagonals[Case]->GetRHI(),Capacity*16);
            C.EnqueueCopy(Cmd,Diagnostics[Case]->GetRHI(),16);Cmd.SubmitAndBlockUntilGPUIdle();
            const auto* GG=static_cast<const FVector4f*>(G.Lock(Capacity*16));const auto* DD=static_cast<const FVector4f*>(D.Lock(Capacity*16));
            const auto* CC=static_cast<const uint32*>(C.Lock(16));
            if(!GG || !DD || !CC) { Passed=false;return; }
            Passed &= FMemory::Memcmp(CC,Totals[Case],16)==0;
            for(uint32 I=0;I<Capacity;++I)
            {
                const bool Active=(Case==0 && I<3)||((Case==0 || Case==3)&&I==5);
                const FVector EG=Active?ExpectedG[I]:FVector::ZeroVector,ED=Active?ExpectedD[I]:FVector::ZeroVector;
                Passed &= FVector(FVector3f(GG[I])).Equals(EG,2e-5) && FVector(FVector3f(DD[I])).Equals(ED,2e-5);
                Passed &= GG[I].W==(Active?1.f:0.f) && DD[I].W==(Active?1.f:0.f);
            }
            G.Unlock();D.Unlock();C.Unlock();
        }
    });
    FlushRenderingCommands();
    TestTrue(TEXT("All-node anisotropic density derivatives, partial-solid support, underfilled surface, invalid/off-grid/overflow rejection and empty batch"),Passed);
    return Passed;
}
#endif
