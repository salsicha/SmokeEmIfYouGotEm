#include "Misc/AutomationTest.h"
#include "RaftSimLiquidTransferGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidTransferTest,"RaftSim.Editor.LiquidTransferGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidTransferTest::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM6)
    { AddError(TEXT("Actual SM6 GPU required for conservative P2G reduction"));return false; }
    TArray<FIntVector> Sizes;for (int32 I=0;I<16;++I) Sizes.Add(FIntVector(6+2*(I%3),6+2*(I%2),4));
    TArray<FRaftSimLiquidHaloColumn> Copies;
    for (int32 I=0;I<16;++I) Copies.Add({I,(I+1)%16,{2,2},{0,2}});
    // A four-region corner, including an owner with zero local support.
    Copies.Append({{0,2,{2,2},{1,1}},{0,3,{2,2},{0,0}},
        {3,0,{3,3},{0,0}},{15,0,{3,3},{1,1}}});
    TArray<TArray<FVector4f>> Raw,Expected,Actual,ReadRaw;
    for (int32 I=0;I<Sizes.Num();++I)
    {
        auto& V=Raw.AddDefaulted_GetRef();const auto S=Sizes[I];
        for (int32 Z=0;Z<S.Z;++Z) for (int32 Y=0;Y<S.Y;++Y) for (int32 X=0;X<S.X;++X)
        {
            const float Weight=float(1+(I+X+Y)%7)/16.f;
            V.Add(I==0?FVector4f(0,0,0,0):FVector4f((100000.f+16*I+X)*Weight,(-200000.f-Y)*Weight,Z*Weight,Weight));
        }
    }
    auto Offset=[&](int32 Owner,FIntPoint P,int32 Z) { return (Z*Sizes[Owner].Y+P.Y)*Sizes[Owner].X+P.X; };
    // CPU reference groups by physical cell, never averages owner velocities.
    auto ReduceCPU=[&]()
    {
        Expected=Raw;
        for (const auto& C:Copies) for (int32 Z=0;Z<Sizes[0].Z;++Z)
            Expected[C.SourceOwner][Offset(C.SourceOwner,C.Source,Z)]+=Raw[C.DestinationOwner][Offset(C.DestinationOwner,C.Destination,Z)];
        for (const auto& C:Copies) for (int32 Z=0;Z<Sizes[0].Z;++Z)
            Expected[C.DestinationOwner][Offset(C.DestinationOwner,C.Destination,Z)]=Expected[C.SourceOwner][Offset(C.SourceOwner,C.Source,Z)];
    };
    bool Ran=false,Rejected=false;FString Error;
    ENQUEUE_RENDER_COMMAND(RaftSimTransferTest)([&](FRHICommandListImmediate& Cmd)
    {
        TArray<FTextureRHIRef> Textures;
        for (int32 I=0;I<Sizes.Num();++I)
        {
            const auto S=Sizes[I];
            auto T=Cmd.CreateTexture(FRHITextureCreateDesc::Create3D(TEXT("RawP2GTest"),S.X,S.Y,S.Z,PF_A32B32G32R32F)
                .SetFlags(TexCreate_ShaderResource|TexCreate_UAV).SetInitialState(ERHIAccess::CopyDest));
            Cmd.UpdateTexture3D(T,0,FUpdateTextureRegion3D(0,0,0,0,0,0,S.X,S.Y,S.Z),S.X*16,S.X*S.Y*16,
                reinterpret_cast<const uint8*>(Raw[I].GetData()));
            Cmd.Transition(FRHITransitionInfo(T,ERHIAccess::CopyDest,ERHIAccess::UAVCompute));Textures.Add(T);
        }
        FRDGBuilder Graph(Cmd);TArray<FRDGTextureRef> Grids,Totals,FirstTotals;
        for (const auto& T:Textures) Grids.Add(Graph.RegisterExternalTexture(CreateRenderTarget(T,TEXT("RawP2GGrid"))));
        const auto Plan=RaftSimBuildLiquidTransferPlan(Graph,Sizes,Copies,Error);
        if (!Plan.Groups || !RaftSimReduceLiquidTransfer(Graph,Plan,Grids,FirstTotals,Error)) { Graph.Execute();return; }
        // Same graph, changed input: neither the old total nor previous raw
        // snapshot may be recycled into the second reduction.
        AddClearUAVPass(Graph,Graph.CreateUAV(Grids[4]),FVector4f(-70000,90000,-3,0.5f));
        if (!RaftSimReduceLiquidTransfer(Graph,Plan,Grids,Totals,Error)) { Graph.Execute();return; }
        auto Bad=Copies;Bad.Add(Copies[0]);
        Rejected=!RaftSimBuildLiquidTransferPlan(Graph,Sizes,Bad,Error).Groups;
        Bad=Copies;Bad.Add({0,1,{2,2},{0,1}});
        Rejected &= !RaftSimBuildLiquidTransferPlan(Graph,Sizes,Bad,Error).Groups;
        auto Aliased=Grids;Aliased[1]=Grids[0];TArray<FRDGTextureRef> Invalid;
        Rejected &= !RaftSimReduceLiquidTransfer(Graph,Plan,Aliased,Invalid,Error) && Invalid.IsEmpty();
        auto Wrong=Grids;
        Wrong[0]=Graph.CreateTexture(FRDGTextureDesc::Create3D(Sizes[0],PF_FloatRGBA,FClearValueBinding::None,TexCreate_ShaderResource|TexCreate_UAV),TEXT("WrongHalfDeposit"));
        Rejected &= !RaftSimReduceLiquidTransfer(Graph,Plan,Wrong,Invalid,Error);
        TArray<TRefCountPtr<IPooledRenderTarget>> Retained;Retained.SetNum(Totals.Num());
        for (int32 I=0;I<Totals.Num();++I) Graph.QueueTextureExtraction(Totals[I],&Retained[I]);
        Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
        auto Read=[&](FRHITexture* T,FIntVector S,TArray<FVector4f>& Values)
        {
            Values.SetNumUninitialized(S.X*S.Y*S.Z);
            Cmd.Transition(FRHITransitionInfo(T,ERHIAccess::Unknown,ERHIAccess::CopySrc));
            for (int32 Z=0;Z<S.Z;++Z)
            {
                FRHIGPUTextureReadback R(TEXT("P2GFloat32"));
                R.EnqueueCopy(Cmd,T,FIntVector(0,0,Z),0,FIntVector(S.X,S.Y,1));Cmd.SubmitAndBlockUntilGPUIdle();
                int32 Pitch=0;const auto* Data=static_cast<const FVector4f*>(R.Lock(Pitch));
                if (!Data || Pitch<S.X) { Error=TEXT("Incomplete momentum/volume readback");return false; }
                for (int32 Y=0;Y<S.Y;++Y) FMemory::Memcpy(Values.GetData()+(Z*S.Y+Y)*S.X,Data+Y*Pitch,S.X*16);
                R.Unlock();
            }
            return true;
        };
        for (int32 I=0;I<Sizes.Num();++I)
            if (!Read(Retained[I]->GetRHI(),Sizes[I],Actual.AddDefaulted_GetRef()) ||
                !Read(Textures[I],Sizes[I],ReadRaw.AddDefaulted_GetRef())) return;
        Ran=true;
    });
    FlushRenderingCommands();
    if (!TestTrue(TEXT("Actual 16-owner signed full-precision P2G reduction"),Ran)) { AddError(Error);return false; }
    TestTrue(TEXT("Invalid maps, aliasing and half-precision raw data rejected"),Rejected);
    for (auto& V:Raw[4]) V=FVector4f(-70000,90000,-3,0.5f);
    ReduceCPU();
    for (int32 I=0;I<Sizes.Num();++I)
        if (Actual[I]!=Expected[I] || ReadRaw[I]!=Raw[I])
        { AddError(TEXT("Mass/momentum sum, shared copy, preserved exterior or immutable raw deposit differs"));return false; }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidTransferResolveTest,"RaftSim.Editor.LiquidTransferResolveGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidTransferResolveTest::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM6)
    { AddError(TEXT("Actual SM6 GPU required for shared P2G normalization"));return false; }
    const FIntVector Size(6,8,4);TArray<FVector4f> Deposits;
    // Includes zero support, a tiny positive volume, and raw momentum beyond
    // half range. Normalized velocities are exactly representable in half.
    const float Volumes[]={0.f,1.f/1048576.f,2.f,8192.f};
    for (int32 I=0;I<Size.X*Size.Y*Size.Z;++I)
    { const float V=Volumes[I%4];Deposits.Emplace(-10*V,20*V,5*V,V); }
    TArray<FFloat16Color> Velocity;TArray<float> Support;bool Ran=false,Rejected=false;FString Error;
    ENQUEUE_RENDER_COMMAND(RaftSimTransferResolveTest)([&](FRHICommandListImmediate& Cmd)
    {
        auto Raw=Cmd.CreateTexture(FRHITextureCreateDesc::Create3D(TEXT("TransferResolveInput"),Size.X,Size.Y,Size.Z,PF_A32B32G32R32F)
            .SetFlags(TexCreate_ShaderResource|TexCreate_UAV).SetInitialState(ERHIAccess::CopyDest));
        Cmd.UpdateTexture3D(Raw,0,FUpdateTextureRegion3D(0,0,0,0,0,0,Size.X,Size.Y,Size.Z),Size.X*16,Size.X*Size.Y*16,
            reinterpret_cast<const uint8*>(Deposits.GetData()));
        Cmd.Transition(FRHITransitionInfo(Raw,ERHIAccess::CopyDest,ERHIAccess::SRVCompute));
        FRDGBuilder Graph(Cmd);auto Input=Graph.RegisterExternalTexture(CreateRenderTarget(Raw,TEXT("ResolveRaw")));
        auto V=Graph.CreateTexture(FRDGTextureDesc::Create3D(Size,PF_FloatRGBA,FClearValueBinding::None,TexCreate_ShaderResource|TexCreate_UAV),TEXT("ResolveNativeVelocity"));
        auto S=Graph.CreateTexture(FRDGTextureDesc::Create3D(Size,PF_R32_FLOAT,FClearValueBinding::None,TexCreate_ShaderResource|TexCreate_UAV),TEXT("ResolveNativeSupport"));
        AddClearUAVPass(Graph,Graph.CreateUAV(V),FVector4f(77,77,77,77));AddClearUAVPass(Graph,Graph.CreateUAV(S),77.f);
        if (!RaftSimResolveLiquidTransfer(Graph,Input,V,S,Error)) { Graph.Execute();return; }
        Rejected=!RaftSimResolveLiquidTransfer(Graph,Input,Input,S,Error);
        TRefCountPtr<IPooledRenderTarget> ResultV,ResultS;
        Graph.QueueTextureExtraction(V,&ResultV);Graph.QueueTextureExtraction(S,&ResultS);
        Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
        Cmd.Read3DSurfaceFloatData(ResultV->GetRHI(),FIntRect(0,0,Size.X,Size.Y),FIntPoint(0,Size.Z),Velocity);
        Support.SetNumUninitialized(Deposits.Num());
        Cmd.Transition(FRHITransitionInfo(ResultS->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
        for (int32 Z=0;Z<Size.Z;++Z)
        {
            FRHIGPUTextureReadback R(TEXT("ResolveSupport"));
            R.EnqueueCopy(Cmd,ResultS->GetRHI(),FIntVector(0,0,Z),0,FIntVector(Size.X,Size.Y,1));Cmd.SubmitAndBlockUntilGPUIdle();
            int32 Pitch=0;const auto* Data=static_cast<const float*>(R.Lock(Pitch));
            if (!Data || Pitch<Size.X) { Error=TEXT("Incomplete native support readback");return; }
            for (int32 Y=0;Y<Size.Y;++Y) FMemory::Memcpy(Support.GetData()+(Z*Size.Y+Y)*Size.X,Data+Y*Pitch,Size.X*4);
            R.Unlock();
        }
        Ran=Velocity.Num()==Deposits.Num();
    });
    FlushRenderingCommands();
    if (!TestTrue(TEXT("Actual post-reduction native velocity/support resolve"),Ran)) { AddError(Error);return false; }
    TestTrue(TEXT("Resolve rejects raw/output aliasing"),Rejected);
    for (int32 I=0;I<Deposits.Num();++I)
    {
        const bool Wet=Deposits[I].W>0;
        const FFloat16Color Expected(Wet?FLinearColor(-10,20,5,0):FLinearColor(0,0,0,0));
        if (FMemory::Memcmp(&Velocity[I],&Expected,sizeof(Expected)) || Support[I]!=(Wet?3.f:0.f))
        { AddError(TEXT("Native normalization lost small support, overflowed raw momentum, or retained stale empty-cell values"));return false; }
    }
    return true;
}
