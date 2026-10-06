#include "Misc/AutomationTest.h"
#include "RaftSimLiquidDensityGPU.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include "Containers/ResourceArray.h"
#include "RHIUtilities.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidSparseKernelGPURegression,
    "RaftSim.Editor.LiquidFixtureSparseKernelGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidSparseKernelGPURegression::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Actual GPU required for sparse reconstruction"));return false; }
    TArray<FVector4f> Results[4];
    for (int32 Mode=0;Mode<4;++Mode)
    {
        TArray<FVector4f> Points;Points.Add(FVector4f(0,0,0,0));
        for (int32 I=0;I<24;++I)
        { const float Angle=2*PI*I/24;Points.Add(FVector4f(.35f*FMath::Cos(Angle),.35f*FMath::Sin(Angle),0,0)); }
        Points.Add(FVector4f(.8f+(Mode%2 ? 1.e-6f : -1.e-6f),0,0,0));
        FString Error;uint32 Status[4]={MAX_uint32,MAX_uint32,MAX_uint32,MAX_uint32};
        ENQUEUE_RENDER_COMMAND(RaftSimSparseKernelRegression)([&](FRHICommandListImmediate& Cmd)
        {
            FRDGBuilder Graph(Cmd);
            auto Input=CreateStructuredBuffer(Graph,TEXT("SparseKernelTestPositions"),TConstArrayView<FVector4f>(Points));
            const auto Density=RaftSimLiquidDensityGPU(Graph,Input,Points.Num(),nullptr,0,
                FVector3f(-1,-1,-1),FVector3f(2,2,2),FIntVector(32,32,32),.4f,1.f/6,Error,Mode>=2);
            if (!Density.Scalar) return;
            FRHIGPUBufferReadback Rows(TEXT("SparseKernelTestRows")),Diagnostics(TEXT("SparseKernelTestDiagnostics"));
            AddEnqueueCopyPass(Graph,&Rows,Density.KernelRows,3*sizeof(FVector4f));
            AddEnqueueCopyPass(Graph,&Diagnostics,Density.Diagnostics,4*sizeof(uint32));
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            Results[Mode].Append(static_cast<const FVector4f*>(Rows.Lock(3*sizeof(FVector4f))),3);Rows.Unlock();
            FMemory::Memcpy(Status,Diagnostics.Lock(sizeof(Status)),sizeof(Status));Diagnostics.Unlock();
        });
        FlushRenderingCommands();
        TestTrue(TEXT("Density dispatch succeeded"),Error.IsEmpty());
        for (uint32 Value:Status) TestEqual(TEXT("Density diagnostics remain clear"),Value,0u);
        if (!TestEqual(TEXT("Three actual kernel rows read"),Results[Mode].Num(),3)) return false;
        TestEqual(TEXT("Fixture crosses the actual raw neighbor threshold"),Results[Mode][1].W,Mode%2 ? 25.f : 26.f);
    }
    auto Difference=[&](int32 A,int32 B)
    {
        float Maximum=0;
        for (int32 Row=0;Row<3;++Row) for (int32 Col=0;Col<3;++Col)
            Maximum=FMath::Max(Maximum,FMath::Abs(Results[A][Row][Col]-Results[B][Row][Col]));
        return Maximum;
    };
    TestTrue(TEXT("Control exhibits the hard kernel jump"),Difference(0,1)>.5f);
    TestTrue(TEXT("Weighted transition remains continuous on the GPU"),Difference(2,3)<.001f);
    auto Volume=[&](int32 Index)
    {
        const auto& R=Results[Index];
        const float Det=R[0].X*(R[1].Y*R[2].Z-R[1].Z*R[2].Y)-
            R[0].Y*(R[1].X*R[2].Z-R[1].Z*R[2].X)+R[0].Z*(R[1].X*R[2].Y-R[1].Y*R[2].X);
        return R[0].W/Det;
    };
    TestTrue(TEXT("Transition never changes integrated quadrature weight"),FMath::Abs(Volume(0)-Volume(2))<1.e-6f);
    TestTrue(TEXT("Outside integrated quadrature weight unchanged"),FMath::Abs(Volume(1)-Volume(3))<1.e-6f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidParticlePackGPURegression,
    "RaftSim.Editor.LiquidFixtureParticlePackGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidParticlePackGPURegression::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Actual GPU required for Niagara particle packing"));return false; }
    constexpr uint32 Capacity=16,Stride=20,Offset=2;
    for (bool Uav:{false,true}) for (uint32 Count:{0u,3u,21u})
    {
        TArray<FVector4f> Actual;uint32 ActualCount=MAX_uint32,OriginalCounts[3]={};bool Dispatched=false;
        ENQUEUE_RENDER_COMMAND(RaftSimParticlePackRegression)([&](FRHICommandListImmediate& Cmd)
        {
            TResourceArray<float> Values;Values.Init(-777.f,Stride*5);
            for (uint32 I=0;I<Capacity;++I)
            { Values[(Offset+0)*Stride+I]=100+I;Values[(Offset+1)*Stride+I]=200+2*I;Values[(Offset+2)*Stride+I]=300-4*I; }
            TResourceArray<uint32> Counts;Counts.Add(99);Counts.Add(Count);Counts.Add(77);
            FRWBuffer Floats,Counter;
            Floats.Initialize(Cmd,TEXT("LiquidPackTestFloats"),sizeof(float),Stride*5,PF_R32_FLOAT,ERHIAccess::SRVMask,BUF_None,&Values);
            const auto CountState=Uav?ERHIAccess::UAVCompute:ERHIAccess::SRVMask;
            Counter.Initialize(Cmd,TEXT("LiquidPackTestCounts"),sizeof(uint32),3,PF_R32_UINT,CountState,BUF_SourceCopy,&Counts);
            FMatrix44f Transform=FMatrix44f::Identity;
            Transform.M[0][0]=0;Transform.M[0][1]=1;Transform.M[1][0]=-1;Transform.M[1][1]=0;
            Transform.M[3][0]=50;Transform.M[3][1]=-25;Transform.M[3][2]=75;
            FRDGBuilder Graph(Cmd);FRDGBufferRef PackedCount=nullptr;
            auto Packed=RaftSimPackLiquidParticlesGPU(Graph,Floats.SRV,Counter.SRV,Stride,Offset,1,Capacity,Transform,PackedCount,Uav?Counter.UAV.GetReference():nullptr);
            if (!Packed) return;
            FRHIGPUBufferReadback PositionReadback(TEXT("LiquidPackPositions")),CountReadback(TEXT("LiquidPackCount")),OriginalReadback(TEXT("LiquidPackOriginalCounter"));
            AddEnqueueCopyPass(Graph,&PositionReadback,Packed,Capacity*sizeof(FVector4f));
            AddEnqueueCopyPass(Graph,&CountReadback,PackedCount,sizeof(uint32));
            Graph.Execute();
            Cmd.Transition(FRHITransitionInfo(Counter.Buffer,CountState,ERHIAccess::CopySrc));
            OriginalReadback.EnqueueCopy(Cmd,Counter.Buffer,sizeof(OriginalCounts));
            Cmd.SubmitAndBlockUntilGPUIdle();
            Actual.Append(static_cast<const FVector4f*>(PositionReadback.Lock(Capacity*sizeof(FVector4f))),Capacity);PositionReadback.Unlock();
            FMemory::Memcpy(&ActualCount,CountReadback.Lock(sizeof(uint32)),sizeof(uint32));CountReadback.Unlock();
            FMemory::Memcpy(OriginalCounts,OriginalReadback.Lock(sizeof(OriginalCounts)),sizeof(OriginalCounts));OriginalReadback.Unlock();
            Dispatched=true;
        });
        FlushRenderingCommands();
        if (!TestTrue(TEXT("Real particle pack dispatched"),Dispatched)) return false;
        TestEqual(TEXT("Actual count retained even when greater than capacity"),ActualCount,Count);
        TestTrue(TEXT("Niagara counter remains unchanged"),OriginalCounts[0]==99 && OriginalCounts[1]==Count && OriginalCounts[2]==77);
        float Error=0;
        for (uint32 I=0;I<Capacity;++I)
        {
            const FVector4f Expected=I<Count?FVector4f((-150.f-2*I)*.01f,(75.f+I)*.01f,(375.f-4*I)*.01f,0):FVector4f(0,0,0,0);
            Error=FMath::Max(Error,(Actual[I]-Expected).Size());
        }
        TestTrue(TEXT("Offsets, stride, rotation, translation, units and inactive slots match CPU"),FMath::IsFinite(Error) && Error<1e-5f);
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidOccupancyGPURegression,
    "RaftSim.Editor.LiquidFixtureOccupancyGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidOccupancyGPURegression::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Actual SM5+ GPU required for occupancy regression"));return false; }
    constexpr int32 N=10;
    for (int32 Case=0;Case<6;++Case)
    {
        const int32 Ratio=Case<3?(1<<Case):2,R=N*Ratio,Count=R*R*R;
        TArray<FFloat16Color> Boundary;Boundary.SetNum(N*N*N);
        TArray<float> Source;Source.SetNum(Count);
        TArray<FVector2f> Actual;uint32 Status[4]={0,0,0,0};FString Error;
        const auto Index=[](int32 X,int32 Y,int32 Z){return X+N*(Y+N*Z);};
        for (int32 Z=0;Z<N;++Z)for (int32 Y=0;Y<N;++Y)for (int32 X=0;X<N;++X)
        {
            float Type=Case==3?2.f:0.f;
            if (Case<3 && (X==0 || Z==N-1 || (X==5 && Y==5 && Z==5))) Type=X==0?3:Z==N-1?2:1;
            if (Case>=4 && X==5 && Y==5 && Z==5) Type=Case==4?4.f:.25f;
            Boundary[Index(X,Y,Z)]=FFloat16Color(FLinearColor(0,0,0,Type));
        }
        for (int32 I=0;I<Count;++I) Source[I]=I%19==0?-.4f:.4f;
        bool Dispatched=false,BadDomainRejected=false;
        ENQUEUE_RENDER_COMMAND(RaftSimOccupancyRegression)([&](FRHICommandListImmediate& Cmd)
        {
            auto B=Cmd.CreateTexture(FRHITextureCreateDesc::Create3D(TEXT("OccupancyTestBoundary"),N,N,N,PF_FloatRGBA)
                .SetFlags(TexCreate_ShaderResource).SetInitialState(ERHIAccess::CopyDest));
            auto S=Cmd.CreateTexture(FRHITextureCreateDesc::Create3D(TEXT("OccupancyTestScalar"),R,R,R,PF_R32_FLOAT)
                .SetFlags(TexCreate_ShaderResource).SetInitialState(ERHIAccess::CopyDest));
            Cmd.UpdateTexture3D(B,0,FUpdateTextureRegion3D(0,0,0,0,0,0,N,N,N),N*sizeof(FFloat16Color),N*N*sizeof(FFloat16Color),reinterpret_cast<const uint8*>(Boundary.GetData()));
            Cmd.UpdateTexture3D(S,0,FUpdateTextureRegion3D(0,0,0,0,0,0,R,R,R),R*sizeof(float),R*R*sizeof(float),reinterpret_cast<const uint8*>(Source.GetData()));
            Cmd.Transition(FRHITransitionInfo(B,ERHIAccess::CopyDest,ERHIAccess::SRVMask));
            Cmd.Transition(FRHITransitionInfo(S,ERHIAccess::CopyDest,ERHIAccess::SRVMask));
            FRDGBuilder Graph(Cmd);
            auto Native=Graph.RegisterExternalTexture(CreateRenderTarget(B,TEXT("OccupancyTestBoundary")));
            auto Scalar=Graph.RegisterExternalTexture(CreateRenderTarget(S,TEXT("OccupancyTestScalar")));
            auto DiagnosticDesc=FRDGBufferDesc::CreateStructuredDesc(sizeof(uint32),4);DiagnosticDesc.Usage|=BUF_SourceCopy;
            auto Diagnostics=Graph.CreateBuffer(DiagnosticDesc,TEXT("OccupancyTestDiagnostics"));
            AddClearUAVPass(Graph,Graph.CreateUAV(Diagnostics),0);
            auto Bad=Graph.CreateTexture(FRDGTextureDesc::Create3D(FIntVector(R+1,R,R),PF_R32_FLOAT,FClearValueBinding::None,TexCreate_ShaderResource|TexCreate_UAV),TEXT("OccupancyTestBadDomain"));
            BadDomainRejected=!RaftSimLiquidOccupancyGPU(Graph,Bad,Native,Diagnostics,Error).Scalar;
            auto Result=RaftSimLiquidOccupancyGPU(Graph,Scalar,Native,Diagnostics,Error);
            if (!Result.Scalar) return;
            FRHIGPUBufferReadback Readback(TEXT("OccupancyTestAudit")),StatusReadback(TEXT("OccupancyTestStatus"));
            AddEnqueueCopyPass(Graph,&Readback,Result.Audit,Count*sizeof(FVector2f));
            AddEnqueueCopyPass(Graph,&StatusReadback,Diagnostics,sizeof(Status));
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            Actual.Append(static_cast<const FVector2f*>(Readback.Lock(Count*sizeof(FVector2f))),Count);Readback.Unlock();
            FMemory::Memcpy(Status,StatusReadback.Lock(sizeof(Status)),sizeof(Status));StatusReadback.Unlock();Dispatched=true;
        });
        FlushRenderingCommands();
        if (!TestTrue(TEXT("Real occupancy dispatched"),Dispatched)) { AddError(Error);return false; }
        TestTrue(TEXT("Nonuniform refinement rejected"),BadDomainRejected);
        if (Case>=4)
        {
            TestTrue(TEXT("Invalid category diagnosed"),Status[2]>0);
            TestTrue(TEXT("Invalid input is not a finite accepted surface"),!FMath::IsFinite(Actual[0].X));
            continue;
        }
        TestTrue(TEXT("Valid input diagnostics zero"),(Status[0]|Status[1]|Status[2]|Status[3])==0);
        TArray<float> Core;Core.Init(0,N*N*N);
        for (int32 Z=1;Z<N-1;++Z)for (int32 Y=1;Y<N-1;++Y)for (int32 X=1;X<N-1;++X)
        {
            bool Fluid=true;
            for (int32 DZ=-1;DZ<=1;++DZ)for (int32 DY=-1;DY<=1;++DY)for (int32 DX=-1;DX<=1;++DX)
                Fluid &= Boundary[Index(X+DX,Y+DY,Z+DZ)].A.GetFloat()==0;
            Core[Index(X,Y,Z)]=Fluid?1.f:0.f;
        }
        float MaxError=0;int32 FalseWet=0;bool Finite=true;
        for (int32 Z=0;Z<R;++Z)for (int32 Y=0;Y<R;++Y)for (int32 X=0;X<R;++X)
        {
            const FVector3f Position((X+.5f)/Ratio-.5f,(Y+.5f)/Ratio-.5f,(Z+.5f)/Ratio-.5f);
            const FIntVector Low(FMath::FloorToInt(Position.X),FMath::FloorToInt(Position.Y),FMath::FloorToInt(Position.Z));
            const FVector3f Fraction=Position-FVector3f(Low);float Confidence=0;
            for (int32 DZ=0;DZ<2;++DZ)for (int32 DY=0;DY<2;++DY)for (int32 DX=0;DX<2;++DX)
                Confidence+=Core[Index(FMath::Clamp(Low.X+DX,0,N-1),FMath::Clamp(Low.Y+DY,0,N-1),FMath::Clamp(Low.Z+DZ,0,N-1))]*
                    (DX?Fraction.X:1-Fraction.X)*(DY?Fraction.Y:1-Fraction.Y)*(DZ?Fraction.Z:1-Fraction.Z);
            const int32 I=X+R*(Y+R*Z);const float Expected=FMath::Min(Source[I],.5f-Confidence);
            Finite &= FMath::IsFinite(Actual[I].X) && FMath::IsFinite(Actual[I].Y);
            MaxError=FMath::Max(MaxError,FMath::Max(FMath::Abs(Actual[I].X-Expected),FMath::Abs(Actual[I].Y-Confidence)));
            if (Source[I]>0 && Actual[I].X<=0 && Boundary[Index(X/Ratio,Y/Ratio,Z/Ratio)].A.GetFloat()!=0) ++FalseWet;
        }
        TestTrue(TEXT("GPU matches independent CPU interior interpolation"),Finite && MaxError<=1e-6f);
        TestEqual(TEXT("No new liquid in nonfluid parent cells"),FalseWet,0);
    }
    return true;
}
