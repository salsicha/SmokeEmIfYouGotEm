#include "Misc/AutomationTest.h"
#include "RaftSimLiquidHaloGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidHaloTest,"RaftSim.Editor.LiquidPressureHaloGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidHaloTest::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM6)
    { AddError(TEXT("Actual SM6 GPU required for simultaneous pressure halo exchange"));return false; }
    TArray<FIntVector> Sizes={FIntVector(10,8,4),FIntVector(8,10,4),FIntVector(6,6,4)};
    while (Sizes.Num()<16) Sizes.Add(FIntVector(6,6,4));
    // Opposing faces plus a diagonal owner. Every source stays in the physical
    // interior, including both cells of a two-cell-wide pressure halo.
    TArray<FRaftSimLiquidHaloColumn> Copies={
        {0,1,{6,2},{0,2}},{0,1,{7,2},{1,2}},
        {1,0,{2,2},{8,2}},{1,0,{3,2},{9,2}},
        {2,0,{2,3},{9,7}},{0,2,{7,5},{0,0}},
        {1,2,{5,7},{1,0}},{2,1,{3,2},{7,9}}};
    for (int32 I=3;I<16;++I) Copies.Add({I,(I+1)%16,{2,2},{1,1}});
    TArray<TArray<float>> Expected,Actual;
    for (int32 Owner=0;Owner<Sizes.Num();++Owner)
    {
        const auto S=Sizes[Owner];auto& Values=Expected.AddDefaulted_GetRef();
        for (int32 Z=0;Z<S.Z;++Z) for (int32 Y=0;Y<S.Y;++Y) for (int32 X=0;X<S.X;++X)
            Values.Add(float(10000*Owner+100*Z+10*Y+X));
    }
    bool Ran=false,InvalidRejected=false;FString Error;
    ENQUEUE_RENDER_COMMAND(RaftSimHaloTest)([&](FRHICommandListImmediate& Cmd)
    {
        TArray<FTextureRHIRef> Textures;
        for (int32 I=0;I<Sizes.Num();++I)
        {
            const auto S=Sizes[I];
            auto T=Cmd.CreateTexture(FRHITextureCreateDesc::Create3D(TEXT("HaloTest"),S.X,S.Y,S.Z,PF_R32_FLOAT)
                .SetFlags(TexCreate_ShaderResource|TexCreate_UAV).SetInitialState(ERHIAccess::CopyDest));
            Cmd.UpdateTexture3D(T,0,FUpdateTextureRegion3D(0,0,0,0,0,0,S.X,S.Y,S.Z),S.X*4,S.X*S.Y*4,
                reinterpret_cast<const uint8*>(Expected[I].GetData()));
            Cmd.Transition(FRHITransitionInfo(T,ERHIAccess::CopyDest,ERHIAccess::UAVCompute));Textures.Add(T);
        }
        FRDGBuilder Graph(Cmd);TArray<FRDGTextureRef> Grids;
        for (const auto& T:Textures) Grids.Add(Graph.RegisterExternalTexture(CreateRenderTarget(T,TEXT("HaloTestGrid"))));
        auto Plan=RaftSimBuildLiquidHaloPlan(Graph,Sizes,Copies,Error);
        if (!Plan.Columns || !RaftSimExchangeLiquidPressureHalo(Graph,Plan,Grids,Error)) { Graph.Execute();return; }
        // A second same-graph iteration changes owner 0's current values. The
        // exchange must observe this write, not retained previous-iteration data.
        AddClearUAVPass(Graph,Graph.CreateUAV(Grids[0]),321.f);
        if (!RaftSimExchangeLiquidPressureHalo(Graph,Plan,Grids,Error)) { Graph.Execute();return; }
        auto Bad=Copies;Bad.Add(Copies[0]);
        InvalidRejected=!RaftSimBuildLiquidHaloPlan(Graph,Sizes,Bad,Error).Columns;
        Bad=Copies;Bad[0].Source=FIntPoint(0,0);
        InvalidRejected &= !RaftSimBuildLiquidHaloPlan(Graph,Sizes,Bad,Error).Columns;
        Bad=Copies;Bad[0].Destination=FIntPoint(2,2);
        InvalidRejected &= !RaftSimBuildLiquidHaloPlan(Graph,Sizes,Bad,Error).Columns;
        auto Aliased=Grids;Aliased[1]=Grids[0];
        InvalidRejected &= !RaftSimExchangeLiquidPressureHalo(Graph,Plan,Aliased,Error);
        Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
        for (int32 I=0;I<Sizes.Num();++I)
        {
            const auto S=Sizes[I];auto& Values=Actual.AddDefaulted_GetRef();Values.SetNumUninitialized(S.X*S.Y*S.Z);
            Cmd.Transition(FRHITransitionInfo(Textures[I],ERHIAccess::Unknown,ERHIAccess::CopySrc));
            for (int32 Z=0;Z<S.Z;++Z)
            {
                FRHIGPUTextureReadback Read(TEXT("HaloExactFloat32"));
                Read.EnqueueCopy(Cmd,Textures[I],FIntVector(0,0,Z),0,FIntVector(S.X,S.Y,1));Cmd.SubmitAndBlockUntilGPUIdle();
                int32 Pitch=0;const auto* Data=static_cast<const float*>(Read.Lock(Pitch));
                if (!Data || Pitch<S.X) { Error=TEXT("Incomplete pressure readback");return; }
                for (int32 Y=0;Y<S.Y;++Y) FMemory::Memcpy(Values.GetData()+(Z*S.Y+Y)*S.X,Data+Y*Pitch,S.X*4);
                Read.Unlock();
            }
        }
        Ran=true;
    });
    FlushRenderingCommands();
    if (!TestTrue(TEXT("Actual two-iteration bidirectional GPU exchange"),Ran)) { AddError(Error);return false; }
    TestTrue(TEXT("Reject duplicate writes, halo sources, physical destinations and aliases"),InvalidRejected);
    auto ExchangeCPU=[&]()
    {
        const auto Before=Expected;
        for (const auto& C:Copies) for (int32 Z=0;Z<Sizes[0].Z;++Z)
        {
            const auto S=Sizes[C.SourceOwner],D=Sizes[C.DestinationOwner];
            Expected[C.DestinationOwner][(Z*D.Y+C.Destination.Y)*D.X+C.Destination.X]=
                Before[C.SourceOwner][(Z*S.Y+C.Source.Y)*S.X+C.Source.X];
        }
    };
    ExchangeCPU();for (auto& V:Expected[0]) V=321.f;ExchangeCPU();
    for (int32 I=0;I<Sizes.Num();++I)
        if (Actual[I]!=Expected[I]) { AddError(TEXT("Full-volume pressure differs: stale copy, physical overwrite, or bad owner/address"));return false; }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidBoundaryHaloTest,"RaftSim.Editor.LiquidBoundaryHaloGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidBoundaryHaloTest::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM6)
    { AddError(TEXT("Actual SM6 GPU required for boundary halo exchange"));return false; }
    TArray<FIntVector> Sizes;for (int32 I=0;I<16;++I) Sizes.Add(FIntVector(6+2*(I%3),6+2*(I%2),4));
    TArray<FRaftSimLiquidHaloColumn> Copies;
    for (int32 I=0;I<16;++I)
    {
        Copies.Add({I,(I+1)%16,{2,2},{0,2}});
        Copies.Add({I,(I+15)%16,{Sizes[I].X-3,Sizes[I].Y-3},{1,1}});
    }
    TArray<TArray<FFloat16Color>> Expected,Actual;
    for (int32 I=0;I<Sizes.Num();++I)
    {
        auto& V=Expected.AddDefaulted_GetRef();const auto S=Sizes[I];
        for (int32 Z=0;Z<S.Z;++Z) for (int32 Y=0;Y<S.Y;++Y) for (int32 X=0;X<S.X;++X)
            V.Add(FFloat16Color(FLinearColor(float(20*I+X),float(-20*I-Y),float(Z*3+X-Y),float((I+X+Y+Z)%4))));
    }
    bool Ran=false,WrongFormatRejected=false,AliasedRejected=false;FString Error;
    ENQUEUE_RENDER_COMMAND(RaftSimBoundaryHaloTest)([&](FRHICommandListImmediate& Cmd)
    {
        TArray<FTextureRHIRef> Textures;
        for (int32 I=0;I<Sizes.Num();++I)
        {
            const auto S=Sizes[I];
            auto T=Cmd.CreateTexture(FRHITextureCreateDesc::Create3D(TEXT("BoundaryHaloTest"),S.X,S.Y,S.Z,PF_FloatRGBA)
                .SetFlags(TexCreate_ShaderResource|TexCreate_UAV).SetInitialState(ERHIAccess::CopyDest));
            Cmd.UpdateTexture3D(T,0,FUpdateTextureRegion3D(0,0,0,0,0,0,S.X,S.Y,S.Z),S.X*sizeof(FFloat16Color),S.X*S.Y*sizeof(FFloat16Color),
                reinterpret_cast<const uint8*>(Expected[I].GetData()));
            Cmd.Transition(FRHITransitionInfo(T,ERHIAccess::CopyDest,ERHIAccess::UAVCompute));Textures.Add(T);
        }
        FRDGBuilder Graph(Cmd);TArray<FRDGTextureRef> Grids;
        for (const auto& T:Textures) Grids.Add(Graph.RegisterExternalTexture(CreateRenderTarget(T,TEXT("BoundaryHaloGrid"))));
        const auto Plan=RaftSimBuildLiquidHaloPlan(Graph,Sizes,Copies,Error);
        if (!Plan.Columns || !RaftSimExchangeLiquidBoundaryHalo(Graph,Plan,Grids,Error)) { Graph.Execute();return; }
        // Second same-graph update must import the latest complete tuple, not
        // a stale type or velocity left from the previous boundary stage.
        AddClearUAVPass(Graph,Graph.CreateUAV(Grids[0]),FVector4f(-13,17,-7,3));
        if (!RaftSimExchangeLiquidBoundaryHalo(Graph,Plan,Grids,Error)) { Graph.Execute();return; }
        // The advection entry point must likewise copy current signed velocity
        // and its fourth native channel, without changing any physical owner.
        AddClearUAVPass(Graph,Graph.CreateUAV(Grids[1]),FVector4f(11,-23,5,2));
        if (!RaftSimExchangeLiquidVelocityHalo(Graph,Plan,Grids,Error)) { Graph.Execute();return; }
        WrongFormatRejected=!RaftSimExchangeLiquidPressureHalo(Graph,Plan,Grids,Error);
        auto Aliased=Grids;Aliased[1]=Grids[0];
        AliasedRejected=!RaftSimExchangeLiquidBoundaryHalo(Graph,Plan,Aliased,Error) &&
            !RaftSimExchangeLiquidVelocityHalo(Graph,Plan,Aliased,Error);
        Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
        for (int32 I=0;I<Sizes.Num();++I)
        {
            const auto S=Sizes[I];auto& V=Actual.AddDefaulted_GetRef();
            Cmd.Transition(FRHITransitionInfo(Textures[I],ERHIAccess::Unknown,ERHIAccess::CopySrc));
            Cmd.Read3DSurfaceFloatData(Textures[I],FIntRect(0,0,S.X,S.Y),FIntPoint(0,S.Z),V);
            if (V.Num()!=S.X*S.Y*S.Z) { Error=TEXT("Incomplete boundary readback");return; }
        }
        Ran=true;
    });
    FlushRenderingCommands();
    if (!TestTrue(TEXT("Actual 16-owner two-stage boundary GPU exchange"),Ran)) { AddError(Error);return false; }
    TestTrue(TEXT("Pressure shader rejects native boundary format"),WrongFormatRejected);
    TestTrue(TEXT("Aliased boundary owners rejected"),AliasedRejected);
    auto ExchangeCPU=[&]()
    {
        const auto Before=Expected;
        for (const auto& C:Copies) for (int32 Z=0;Z<Sizes[0].Z;++Z)
        {
            const auto S=Sizes[C.SourceOwner],D=Sizes[C.DestinationOwner];
            Expected[C.DestinationOwner][(Z*D.Y+C.Destination.Y)*D.X+C.Destination.X]=
                Before[C.SourceOwner][(Z*S.Y+C.Source.Y)*S.X+C.Source.X];
        }
    };
    ExchangeCPU();for (auto& V:Expected[0]) V=FFloat16Color(FLinearColor(-13,17,-7,3));ExchangeCPU();
    for (auto& V:Expected[1]) V=FFloat16Color(FLinearColor(11,-23,5,2));ExchangeCPU();
    for (int32 I=0;I<Sizes.Num();++I)
        if (FMemory::Memcmp(Actual[I].GetData(),Expected[I].GetData(),Expected[I].Num()*sizeof(FFloat16Color))!=0)
        { AddError(TEXT("Boundary type/solid velocity differs or a physical owner was overwritten"));return false; }
    return true;
}
