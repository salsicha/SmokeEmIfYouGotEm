#include "Misc/AutomationTest.h"
#include "RaftSimLiquidInterfaceHighOrderGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include "../Materials/RaftSimLiquidDataset.h"
#include <limits>

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidInterfaceHighOrderTest,"RaftSim.Editor.LiquidInterfaceHighOrderGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidInterfaceHighOrderTest::RunTest(const FString&)
{
    if(GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM6)
    { AddError(TEXT("Actual SM6 GPU required for higher-order interface verification"));return false; }
    const FString Directory=FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()/TEXT("../tmp/south-fork-liquid-interface-highorder-cases-20260911"));
    const auto Manifest=FRaftSimLiquidDataset::Read(Directory/TEXT("manifest.json"));
    if(!Manifest || Manifest->GetStringField(TEXT("schema"))!=TEXT("raftsim.interface_highorder_cases.v1") ||
        Manifest->GetArrayField(TEXT("cases")).Num()!=12 || !Manifest->GetBoolField(TEXT("sources_unchanged")) ||
        Manifest->GetNumberField(TEXT("scalar_arithmetic_gpu_tolerance_cm"))!=.02 ||
        FRaftSimLiquidDataset::Hash(Manifest->GetStringField(TEXT("capture"))/TEXT("stages.json"))!=Manifest->GetStringField(TEXT("native_stages_sha256")))
    { AddError(TEXT("Intact actual twelve-owner higher-order cases required"));return false; }
    const FString AnalyticDirectory=FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()/TEXT("../tmp/south-fork-liquid-interface-highorder-analytic-20260911"));
    const auto Analytic=FRaftSimLiquidDataset::Read(AnalyticDirectory/TEXT("manifest.json"));
    if(!Analytic || Analytic->GetStringField(TEXT("schema"))!=TEXT("raftsim.interface_highorder_analytic.v1") ||
        Analytic->GetArrayField(TEXT("cases")).Num()!=5)
    { AddError(TEXT("Five repeated-step/failure high-order fixtures required"));return false; }
    auto Cases=Manifest->GetArrayField(TEXT("cases"));Cases.Append(Analytic->GetArrayField(TEXT("cases")));
    uint64 Compared=0;double MaximumError=0;
    for(const auto& Entry:Cases)
    {
        const auto C=Entry->AsObject();const int32 Owner=int32(C->GetNumberField(TEXT("region_id")));
        const FString CaseDirectory=Owner>=100?AnalyticDirectory:Directory;
        double StepValue=1;C->TryGetNumberField(TEXT("steps"),StepValue);const int32 Steps=int32(StepValue);
        if(Steps<1 || Steps>24) { AddError(TEXT("Invalid bounded high-order fixture step count"));return false; }
        const auto& N=C->GetArrayField(TEXT("cells"));const auto& H=C->GetArrayField(TEXT("spacing_cm"));
        if(N.Num()!=3 || H.Num()!=3) { AddError(TEXT("Invalid high-order case dimensions"));return false; }
        const FIntVector Size(int32(N[0]->AsNumber()),int32(N[1]->AsNumber()),int32(N[2]->AsNumber()));
        if(Size.GetMin()<5 || Size.GetMax()>1024 || int64(Size.X)*Size.Y*Size.Z>4000000)
        { AddError(TEXT("High-order case exceeds test bounds"));return false; }
        const int32 Count=Size.X*Size.Y*Size.Z;const FIntVector Lo(2),Hi=Size-FIntVector(2);
        const FVector3f Cell(float(H[0]->AsNumber()),float(H[1]->AsNumber()),float(H[2]->AsNumber()));
        const float Dt=float(C->GetNumberField(TEXT("dt")));
        TArray<uint8> Phi,Velocity,Solid,Expected,NativeBoundary;
        auto Load=[&](const TCHAR* Key,TArray<uint8>& Data,int32 Stride,bool Local)
        {
            const FString Name=C->GetStringField(FString(Key)+TEXT("_file"));
            if(Local && FPaths::GetCleanFilename(Name)!=Name) return false;
            const FString Path=Local?CaseDirectory/Name:Name;
            return FRaftSimLiquidDataset::Hash(Path)==C->GetStringField(FString(Key)+TEXT("_sha256")) &&
                FFileHelper::LoadFileToArray(Data,*Path) && Data.Num()==Count*Stride;
        };
        if(!Load(TEXT("phi"),Phi,4,false) || !Load(TEXT("velocity"),Velocity,8,false) ||
            !Load(TEXT("solid"),Solid,4,true) || !Load(TEXT("expected"),Expected,4,true))
        { AddError(TEXT("Changed/truncated higher-order source or expected field"));return false; }
        if(Owner<100 && !Load(TEXT("boundary"),NativeBoundary,8,false))
        { AddError(TEXT("Changed native higher-order solid boundary"));return false; }
        TArray<float> Actual;uint32 Status[8];for(auto& Value:Status) Value=MAX_uint32;
        bool Ran=false,Rejected=false,InvalidPhaseRejected=Owner!=0;FString Error;
        ENQUEUE_RENDER_COMMAND(RaftSimInterfaceHighOrderTest)([&](FRHICommandListImmediate& Cmd)
        {
            auto Upload=[&](const TCHAR* Name,EPixelFormat Format,const TArray<uint8>& Data,int Stride)
            {
                auto Texture=Cmd.CreateTexture(FRHITextureCreateDesc::Create3D(Name,Size.X,Size.Y,Size.Z,Format)
                    .SetFlags(TexCreate_ShaderResource|TexCreate_UAV).SetInitialState(ERHIAccess::CopyDest));
                Cmd.UpdateTexture3D(Texture,0,FUpdateTextureRegion3D(0,0,0,0,0,0,Size.X,Size.Y,Size.Z),
                    Size.X*Stride,Size.X*Size.Y*Stride,Data.GetData());
                Cmd.Transition(FRHITransitionInfo(Texture,ERHIAccess::CopyDest,ERHIAccess::SRVCompute));return Texture;
            };
            auto S=Upload(TEXT("HighOrder.Source"),PF_R32_FLOAT,Phi,4);
            auto V=Upload(TEXT("HighOrder.Velocity"),PF_FloatRGBA,Velocity,8);
            auto B=Owner<100?Upload(TEXT("HighOrder.NativeBoundary"),PF_FloatRGBA,NativeBoundary,8):
                Upload(TEXT("HighOrder.Solid"),PF_R32_UINT,Solid,4);
            FRDGBuilder Graph(Cmd);
            auto Source=Graph.RegisterExternalTexture(CreateRenderTarget(S,TEXT("HighOrder.Source")));
            auto Flow=Graph.RegisterExternalTexture(CreateRenderTarget(V,TEXT("HighOrder.Flow")));
            auto Boundary=Graph.RegisterExternalTexture(CreateRenderTarget(B,TEXT("HighOrder.Boundary")));
            FRaftSimLiquidInterfaceHighOrderStep Step;auto Current=Source;
            for(int32 Iteration=0;Iteration<Steps;++Iteration)
            {
                Step=RaftSimAdvectLiquidInterfaceHighOrder(Graph,Current,Flow,Boundary,Cell,Dt,Lo,Hi,Error,true);
                if(!Step.Scalar) { Graph.Execute();return; }
                Current=Step.Scalar;
            }
            FString Invalid;
            Rejected=!RaftSimAdvectLiquidInterfaceHighOrder(Graph,Source,Source,Boundary,Cell,Dt,Lo,Hi,Invalid).Scalar &&
                !RaftSimAdvectLiquidInterfaceHighOrder(Graph,Source,Flow,Source,Cell,Dt,Lo,Hi,Invalid).Scalar &&
                !RaftSimAdvectLiquidInterfaceHighOrder(Graph,Source,Flow,Boundary,Cell,-1,Lo,Hi,Invalid).Scalar &&
                !RaftSimAdvectLiquidInterfaceHighOrder(Graph,Source,Flow,Boundary,FVector3f(0,1,1),Dt,Lo,Hi,Invalid).Scalar &&
                !RaftSimAdvectLiquidInterfaceHighOrder(Graph,Source,Flow,Boundary,Cell,Dt,Lo,Size+FIntVector(1),Invalid).Scalar;
            TRefCountPtr<IPooledRenderTarget> Retained;Graph.QueueTextureExtraction(Step.Scalar,&Retained);
            FRHIGPUBufferReadback Counters(TEXT("HighOrder.Status"));AddEnqueueCopyPass(Graph,&Counters,Step.Diagnostics,sizeof(Status));
            FRHIGPUBufferReadback InvalidCounters(TEXT("HighOrder.InvalidNativePhase"));
            if(Owner==0)
            {
                auto Bad=NativeBoundary;
                auto* Phases=reinterpret_cast<FFloat16Color*>(Bad.GetData());
                Phases[0].A=FFloat16(4.f);
                Phases[1].A=FFloat16(std::numeric_limits<float>::quiet_NaN());
                auto BadTexture=Upload(TEXT("HighOrder.InvalidBoundary"),PF_FloatRGBA,Bad,8);
                auto BadGrid=Graph.RegisterExternalTexture(CreateRenderTarget(BadTexture,TEXT("HighOrder.InvalidBoundary")));
                auto Failed=RaftSimAdvectLiquidInterfaceHighOrder(Graph,Source,Flow,BadGrid,Cell,Dt,Lo,Hi,Error,true);
                if(!Failed.Diagnostics) { Graph.Execute();return; }
                AddEnqueueCopyPass(Graph,&InvalidCounters,Failed.Diagnostics,32);
            }
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            if(Owner==0)
            {
                const auto* InvalidData=static_cast<const uint32*>(InvalidCounters.Lock(32));
                if(!InvalidData) { Error=TEXT("Missing invalid native phase diagnostics");return; }
                InvalidPhaseRejected=InvalidData[2]==10u;InvalidCounters.Unlock();
            }
            const void* Data=Counters.Lock(sizeof(Status));if(!Data) { Error=TEXT("No high-order counter readback");return; }
            FMemory::Memcpy(Status,Data,sizeof(Status));Counters.Unlock();Actual.SetNumUninitialized(Count);
            Cmd.Transition(FRHITransitionInfo(Retained->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
            for(int32 Z=0;Z<Size.Z;++Z)
            {
                FRHIGPUTextureReadback Readback(TEXT("HighOrder.ScalarReadback"));
                Readback.EnqueueCopy(Cmd,Retained->GetRHI(),FIntVector(0,0,Z),0,FIntVector(Size.X,Size.Y,1));Cmd.SubmitAndBlockUntilGPUIdle();
                int32 Pitch=0;const auto* Values=static_cast<const float*>(Readback.Lock(Pitch));
                if(!Values || Pitch<Size.X) { Error=TEXT("Incomplete high-order scalar readback");return; }
                for(int32 Y=0;Y<Size.Y;++Y) FMemory::Memcpy(Actual.GetData()+(Z*Size.Y+Y)*Size.X,Values+Y*Pitch,Size.X*4);
                Readback.Unlock();
            }
            Ran=true;
        });
        FlushRenderingCommands();if(!Ran) { AddError(Error);return false; }
        TestTrue(TEXT("High-order rejects invalid metric, layout, alias, timestep and owned box"),Rejected);
        TestTrue(TEXT("Nonfinite and unrecognized native phases invalidate every stage, including exterior cells"),InvalidPhaseRejected);
        const auto ExpectedStatus=C->GetObjectField(TEXT("limited_transport"));
        TestEqual(TEXT("All owned forward cells updated"),Status[0],uint32(ExpectedStatus->GetNumberField(TEXT("updated_cells"))));
        const uint32 ExpectedFailures=uint32(ExpectedStatus->GetNumberField(TEXT("rejected_forward_trace_cells")));
        TestEqual(TEXT("Forward failures are reported, not masked"),Status[1],ExpectedFailures);TestEqual(TEXT("No nonfinite corrections"),Status[2],0u);
        TestEqual(TEXT("Reverse trace diagnostics"),Status[6],uint32(ExpectedStatus->GetNumberField(TEXT("reverse_trace_failures"))));
        TestEqual(TEXT("Third-forward failures are not hidden"),Status[7],ExpectedFailures);
        TestEqual(TEXT("All valid cells accounted as high-order or explicit fallback"),Status[3]+Status[5],Status[0]);
        TestEqual(TEXT("High-order use or explicit full fallback matches fixture"),Status[3]>0,ExpectedStatus->GetNumberField(TEXT("second_order_cells"))>0);
        const auto* Reference=reinterpret_cast<const float*>(Expected.GetData());const auto* Input=reinterpret_cast<const float*>(Phi.GetData());
        for(int Z=0;Z<Size.Z;++Z) for(int Y=0;Y<Size.Y;++Y) for(int X=0;X<Size.X;++X)
        {
            const int I=(Z*Size.Y+Y)*Size.X+X;const double Delta=FMath::Abs(double(Actual[I])-Reference[I]);
            if(!FMath::IsFinite(Actual[I]) || Delta>.02)
            { AddError(FString::Printf(TEXT("Owner%d high-order mismatch at%d: GPU%g CPU%g error%gcm"),Owner,I,Actual[I],Reference[I],Delta));return false; }
            if((X<2 || Y<2 || Z<2 || X>=Hi.X || Y>=Hi.Y || Z>=Hi.Z) && Actual[I]!=Input[I])
            { AddError(TEXT("High-order modified caller-owned halo/boundary"));return false; }
            MaximumError=FMath::Max(MaximumError,Delta);++Compared;
        }
        AddInfo(FString::Printf(TEXT("Owner%d high-order used%u limited%u fallback%u (CPU used%d limited%d)"),Owner,
            Status[3],Status[4],Status[5],int(ExpectedStatus->GetNumberField(TEXT("second_order_cells"))),int(ExpectedStatus->GetNumberField(TEXT("extrema_limited_cells")))));
    }
    AddInfo(FString::Printf(TEXT("Limited BFECC: %llu samples across twelve river fields and five analytic/failure fixtures, maximum CPU difference %.9gcm. Includes 24 persistent GPU steps, not a coupled river trajectory or FPS benchmark."),Compared,MaximumError));
    return true;
}
