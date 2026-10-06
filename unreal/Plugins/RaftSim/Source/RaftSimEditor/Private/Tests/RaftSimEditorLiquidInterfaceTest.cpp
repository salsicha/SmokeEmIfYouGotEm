#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "RaftSimLiquidInterfaceGPU.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include "../Materials/RaftSimLiquidDataset.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidInterfaceTransportTest,"RaftSim.Editor.LiquidInterfaceTransportGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidInterfaceTransportTest::RunTest(const FString&)
{
    if(GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM6)
    { AddError(TEXT("Actual SM6 GPU required for explicit interface transport"));return false; }
    const bool Compact=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalUnifiedTransport"));
    const FString Directory=FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()/(Compact?
        TEXT("../tmp/south-fork-liquid-interface-compact-cases-20260911"):TEXT("../tmp/south-fork-liquid-interface-transport-cases-20260911")));
    const auto Manifest=FRaftSimLiquidDataset::Read(Directory/TEXT("manifest.json"));
    if(!Manifest || Manifest->GetStringField(TEXT("schema"))!=TEXT("raftsim.liquid_interface_transport_cases.v1") ||
        Manifest->GetArrayField(TEXT("cases")).Num()!=15 || Manifest->GetNumberField(TEXT("gpu_error_tolerance_cm"))!=.02)
    { AddError(TEXT("Missing or unexpected actual-river transport cases; run preparation script"));return false; }
    bool CaseCompact=false;Manifest->TryGetBoolField(TEXT("compact_transport"),CaseCompact);
    if(CaseCompact!=Compact) { AddError(TEXT("Transport case interpolation differs from requested shader mode"));return false; }
    auto Int3=[](const TSharedPtr<FJsonObject>& J,const TCHAR* Key)
    {
        const auto& A=J->GetArrayField(Key);
        return A.Num()==3?FIntVector(int32(A[0]->AsNumber()),int32(A[1]->AsNumber()),int32(A[2]->AsNumber())):FIntVector(-1);
    };
    double MaximumError=0;uint64 Compared=0;
    for(const auto& Entry:Manifest->GetArrayField(TEXT("cases")))
    {
        const auto C=Entry->AsObject();const FString Name=C->GetStringField(TEXT("name"));
        const FIntVector Size=Int3(C,TEXT("cells")),Lo=Int3(C,TEXT("update_min")),Hi=Int3(C,TEXT("update_max"));
        const auto& H=C->GetArrayField(TEXT("spacing_cm"));
        if(Size.GetMin()<5 || int64(Size.X)*Size.Y*Size.Z>4000000 || H.Num()!=3)
        { AddError(TEXT("Invalid transport case dimensions"));return false; }
        const FVector3f Cell(float(H[0]->AsNumber()),float(H[1]->AsNumber()),float(H[2]->AsNumber()));
        const float Dt=float(C->GetNumberField(TEXT("dt")));const int32 Count=Size.X*Size.Y*Size.Z;
        TArray<uint8> Phi,Velocity,Expected;
        auto Load=[&](const TCHAR* Key,TArray<uint8>& Bytes,int32 BytesPerCell)
        {
            const auto File=C->GetObjectField(TEXT("files"))->GetObjectField(Key);
            const FString Local=File->GetStringField(TEXT("file"));
            return FPaths::GetCleanFilename(Local)==Local &&
                FRaftSimLiquidDataset::Hash(Directory/Local)==File->GetStringField(TEXT("sha256")) &&
                FFileHelper::LoadFileToArray(Bytes,*(Directory/Local)) && Bytes.Num()==Count*BytesPerCell;
        };
        if(!Load(TEXT("phi"),Phi,4) || !Load(TEXT("velocity"),Velocity,8) || !Load(TEXT("expected"),Expected,4))
        { AddError(TEXT("Changed/truncated transport case input or CPU reference"));return false; }
        TArray<float> Actual;uint32 Status[3]={MAX_uint32,MAX_uint32,MAX_uint32};bool Ran=false,Rejected=false;FString Error;
        ENQUEUE_RENDER_COMMAND(RaftSimInterfaceTransportTest)([&](FRHICommandListImmediate& Cmd)
        {
            auto Upload=[&](const TCHAR* Label,EPixelFormat Format,const TArray<uint8>& Bytes,int32 Stride)
            {
                auto T=Cmd.CreateTexture(FRHITextureCreateDesc::Create3D(Label,Size.X,Size.Y,Size.Z,Format)
                    .SetFlags(TexCreate_ShaderResource|TexCreate_UAV).SetInitialState(ERHIAccess::CopyDest));
                Cmd.UpdateTexture3D(T,0,FUpdateTextureRegion3D(0,0,0,0,0,0,Size.X,Size.Y,Size.Z),Size.X*Stride,Size.X*Size.Y*Stride,Bytes.GetData());
                Cmd.Transition(FRHITransitionInfo(T,ERHIAccess::CopyDest,ERHIAccess::SRVCompute));return T;
            };
            const auto S=Upload(TEXT("InterfaceScalarTest"),PF_R32_FLOAT,Phi,4);
            const auto V=Upload(TEXT("InterfaceVelocityTest"),PF_FloatRGBA,Velocity,8);
            FRDGBuilder Graph(Cmd);
            auto Source=Graph.RegisterExternalTexture(CreateRenderTarget(S,TEXT("InterfaceSource")));
            auto Flow=Graph.RegisterExternalTexture(CreateRenderTarget(V,TEXT("InterfaceFlow")));
            const auto Step=RaftSimAdvectLiquidInterface(Graph,Source,Flow,Cell,Dt,Lo,Hi,Error,Compact);
            if(!Step.Scalar) { Graph.Execute();return; }
            FString InvalidError;
            Rejected=!RaftSimAdvectLiquidInterface(Graph,Source,Source,Cell,Dt,Lo,Hi,InvalidError).Scalar &&
                !RaftSimAdvectLiquidInterface(Graph,Source,Flow,FVector3f(0,1,1),Dt,Lo,Hi,InvalidError).Scalar &&
                !RaftSimAdvectLiquidInterface(Graph,Source,Flow,Cell,-1,Lo,Hi,InvalidError).Scalar &&
                !RaftSimAdvectLiquidInterface(Graph,Source,Flow,Cell,Dt,Lo,Size+FIntVector(1),InvalidError).Scalar;
            TRefCountPtr<IPooledRenderTarget> Retained;Graph.QueueTextureExtraction(Step.Scalar,&Retained);
            FRHIGPUBufferReadback Counters(TEXT("InterfaceTransportStatus"));
            AddEnqueueCopyPass(Graph,&Counters,Step.Diagnostics,sizeof(Status));
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            const void* CounterData=Counters.Lock(sizeof(Status));
            if(!CounterData) { Error=TEXT("Missing interface diagnostics readback");return; }
            FMemory::Memcpy(Status,CounterData,sizeof(Status));Counters.Unlock();
            Actual.SetNumUninitialized(Count);
            Cmd.Transition(FRHITransitionInfo(Retained->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
            for(int32 Z=0;Z<Size.Z;++Z)
            {
                FRHIGPUTextureReadback R(TEXT("InterfaceScalarReadback"));
                R.EnqueueCopy(Cmd,Retained->GetRHI(),FIntVector(0,0,Z),0,FIntVector(Size.X,Size.Y,1));Cmd.SubmitAndBlockUntilGPUIdle();
                int32 Pitch=0;const auto* Data=static_cast<const float*>(R.Lock(Pitch));
                if(!Data || Pitch<Size.X) { Error=TEXT("Incomplete interface scalar readback");return; }
                for(int32 Y=0;Y<Size.Y;++Y) FMemory::Memcpy(Actual.GetData()+(Z*Size.Y+Y)*Size.X,Data+Y*Pitch,Size.X*sizeof(float));
                R.Unlock();
            }
            Ran=true;
        });
        FlushRenderingCommands();
        if(!Ran) { AddError(Name+TEXT(": ")+Error);return false; }
        TestTrue(TEXT("Interface rejects aliasing, invalid metric, timestep and update range"),Rejected);
        TestEqual(Name+TEXT(" updated cells"),Status[0],uint32(C->GetNumberField(TEXT("updated_cells"))));
        TestEqual(Name+TEXT(" out-of-domain trace diagnostics"),Status[1],uint32(C->GetNumberField(TEXT("rejected_trace_cells"))));
        TestEqual(Name+TEXT(" nonfinite diagnostics"),Status[2],0u);
        const auto* Reference=reinterpret_cast<const float*>(Expected.GetData());
        const auto* Input=reinterpret_cast<const float*>(Phi.GetData());
        for(int32 Z=0;Z<Size.Z;++Z) for(int32 Y=0;Y<Size.Y;++Y) for(int32 X=0;X<Size.X;++X)
        {
            const int32 I=(Z*Size.Y+Y)*Size.X+X;const double Delta=FMath::Abs(double(Actual[I])-Reference[I]);
            if(!FMath::IsFinite(Actual[I]) || Delta>.02)
            { AddError(FString::Printf(TEXT("%s scalar mismatch at%d: GPU%g CPU%g error%gcm"),*Name,I,Actual[I],Reference[I],Delta));return false; }
            if((X<Lo.X || X>=Hi.X || Y<Lo.Y || Y>=Hi.Y || Z<Lo.Z || Z>=Hi.Z) && Actual[I]!=Input[I])
            { AddError(TEXT("Transport overwrote caller-owned halo/boundary scalar"));return false; }
            MaximumError=FMath::Max(MaximumError,Delta);++Compared;
        }
    }
    AddInfo(FString::Printf(TEXT("Explicit interface GPU operator: %llu samples, max CPU difference %.9g cm; twelve actual river field cases and three analytic cases. Not a coupled river trajectory."),Compared,MaximumError));
    return true;
}
