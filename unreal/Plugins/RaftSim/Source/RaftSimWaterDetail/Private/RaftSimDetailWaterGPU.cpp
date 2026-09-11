#include "RaftSimDetailWaterGPU.h"
#include "GlobalShader.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/Paths.h"
#include "Modules/ModuleManager.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "RHIGPUReadback.h"
#include "ShaderParameterStruct.h"

class FRaftSimDetailWaterModule : public IModuleInterface
{
    virtual void StartupModule() override
    {
        const auto Plugin=IPluginManager::Get().FindPlugin(TEXT("RaftSim"));
        check(Plugin.IsValid());
        AddShaderSourceDirectoryMapping(TEXT("/Plugin/RaftSimWaterDetail"),
            FPaths::Combine(Plugin->GetBaseDir(),TEXT("Shaders")));
    }
};
IMPLEMENT_MODULE(FRaftSimDetailWaterModule,RaftSimWaterDetail)

class FRaftSimDetailWaterCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimDetailWaterCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimDetailWaterCS,FGlobalShader);
    class FActivityMemory : SHADER_PERMUTATION_BOOL("RAFTSIM_ACTIVITY_MEMORY");
    using FPermutationDomain = TShaderPermutationDomain<FActivityMemory>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(FIntPoint,GridSize)
        SHADER_PARAMETER(float,CellMeters)
        SHADER_PARAMETER(float,StepSeconds)
        SHADER_PARAMETER(float,MomentumDamping)
        SHADER_PARAMETER(float,FoamDecay)
        SHADER_PARAMETER(float,FoamSource)
        SHADER_PARAMETER(uint32,Periodic)
        SHADER_PARAMETER(uint32,SecondOrder)
        SHADER_PARAMETER(uint32,RKStage)
        SHADER_PARAMETER(FVector2f,OriginMeters)
        SHADER_PARAMETER(float,TurbulentHeadMeters)
        SHADER_PARAMETER(float,SimulationSeconds)
        SHADER_PARAMETER(float,ActivitySource)
        SHADER_PARAMETER(float,ActivityDecay)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float>,PreviousActivity)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float>,StepInitialActivity)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float>,NextActivity)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,MeanFlow)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,PreviousState)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,StepInitialState)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,NextState)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& Parameters)
    { return IsFeatureLevelSupported(Parameters.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimDetailWaterCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimDetailWater.usf","MainCS",SF_Compute);

class FRaftSimDetailResolveCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimDetailResolveCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimDetailResolveCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(FIntPoint,GridSize)
        SHADER_PARAMETER(float,CellMeters)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,MeanFlow)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,DetailState)
        SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture2D<float4>,SurfaceOutput)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& Parameters)
    { return IsFeatureLevelSupported(Parameters.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimDetailResolveCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimDetailResolve.usf","MainCS",SF_Compute);

class FRaftSimMacroSampleTestCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimMacroSampleTestCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimMacroSampleTestCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(FIntPoint,GridSize)
        SHADER_PARAMETER(uint32,QueryCount)
        SHADER_PARAMETER(uint32,ReconstructCrest)
        SHADER_PARAMETER_RDG_TEXTURE(Texture2D<float4>,Atlas)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,Queries)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Results)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimMacroSampleTestCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimMacroSampleTest.usf","MainCS",SF_Compute);

bool RaftSimValidateMacroSamplingGPU(FRHICommandListImmediate& Cmd,FRHITexture* Atlas,
    FIntPoint GridSize,const TArray<FVector4f>& Queries,FRHIGPUBufferReadback* Readback,FString& Error,bool bReconstructCrest)
{
    check(IsInRenderingThread());
    if (!Atlas || !Readback || GridSize.X<2 || GridSize.Y<2 || Queries.IsEmpty() ||
        Atlas->GetDesc().Extent!=FIntPoint(GridSize.X,GridSize.Y*4+(bReconstructCrest ? 2 : 0)) || Atlas->GetDesc().Format!=PF_A32B32G32R32F)
    { Error=TEXT("Invalid macro sampling fixture");return false; }
    for (const auto& Q:Queries)
        if (!FMath::IsFinite(Q.X) || !FMath::IsFinite(Q.Y) || !FMath::IsFinite(Q.Z) || Q.Z<0 || Q.Z>=4)
        { Error=TEXT("Invalid macro sample coordinate or band");return false; }
    FRDGBuilder Graph(Cmd);auto* P=Graph.AllocParameters<FRaftSimMacroSampleTestCS::FParameters>();
    P->GridSize=GridSize;P->QueryCount=Queries.Num();
    P->ReconstructCrest=bReconstructCrest ? 1 : 0;
    P->Atlas=Graph.RegisterExternalTexture(CreateRenderTarget(Atlas,TEXT("RaftSim.Macro.TestAtlas")));
    P->Queries=Graph.CreateSRV(CreateStructuredBuffer(Graph,TEXT("RaftSim.Macro.Queries"),Queries));
    auto Output=Graph.CreateBuffer(FRDGBufferDesc::CreateStructuredDesc(sizeof(FVector4f),Queries.Num()),TEXT("RaftSim.Macro.Results"));
    P->Results=Graph.CreateUAV(Output);
    TShaderMapRef<FRaftSimMacroSampleTestCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
    FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Macro Interpolation Test"),Shader,P,FIntVector(FMath::DivideAndRoundUp(Queries.Num(),64),1,1));
    AddEnqueueCopyPass(Graph,Readback,Output,Queries.Num()*sizeof(FVector4f));Graph.Execute();return true;
}

bool FRaftSimDetailWaterGrid::Validate(TConstArrayView<FVector4f> Flow,FString& Error) const
{
    if (Size.X<2 || Size.Y<2 || Size.X>512 || Size.Y>512 || Flow.Num()!=Size.X*Size.Y ||
        !FMath::IsFinite(CellMeters) || CellMeters<=0 || !FMath::IsFinite(StepSeconds) || StepSeconds<=0 ||
        !FMath::IsFinite(MomentumDampingPerSecond) || MomentumDampingPerSecond<0 ||
        !FMath::IsFinite(FoamDecayPerSecond) || FoamDecayPerSecond<0 ||
        !FMath::IsFinite(FoamSourcePerSecond) || FoamSourcePerSecond<0 ||
        !FMath::IsFinite(ActivitySourcePerSecond) || ActivitySourcePerSecond<0 ||
        !FMath::IsFinite(ActivityDecayPerSecond) || ActivityDecayPerSecond<0 ||
        !FMath::IsFinite(TurbulentHeadMeters) || TurbulentHeadMeters<0 || TurbulentHeadMeters>0.1f ||
        !FMath::IsFinite(OriginMeters.X) || !FMath::IsFinite(OriginMeters.Y))
    { Error=TEXT("Invalid detail grid, timestep, rates or input size");return false; }
    float MaxSignal=0;
    for (const FVector4f& F:Flow)
    {
        if (!FMath::IsFinite(F.X) || !FMath::IsFinite(F.Y) || !FMath::IsFinite(F.Z) || !FMath::IsFinite(F.W) ||
            F.X<0 || F.W<0 || F.W>1)
        { Error=TEXT("Invalid mean-flow depth, velocity or aeration");return false; }
        if (F.X>0.01f) MaxSignal=FMath::Max(MaxSignal,FMath::Abs(F.Y)+FMath::Abs(F.Z)+2*FMath::Sqrt(9.81f*F.X));
    }
    if (StepSeconds*MaxSignal/CellMeters>0.45f)
    { Error=TEXT("Detail-wave two-dimensional CFL exceeds 0.45; substep instead of clipping state");return false; }
    return true;
}

void FRaftSimDetailWaterGPU::Reset()
{
    check(IsInRenderingThread());
    State.SafeRelease();MeanFlowState.SafeRelease();ActivityState.SafeRelease();StateSize=FIntPoint::ZeroValue;StateCellMeters=0;
    bStatePeriodic=false;bStateSecondOrder=false;bStateActivityMemory=false;StateOriginMeters=FVector2f::ZeroVector;SimulationSeconds=0;StepCount=0;
}

bool FRaftSimDetailWaterGPU::Advance(FRHICommandListImmediate& RHICmdList,
    const FRaftSimDetailWaterGrid& Grid,const TArray<FVector4f>& Flow,int32 Steps,
    const TArray<FVector4f>* InitialState,FRHIGPUBufferReadback* Readback,FString& Error,
    const TArray<float>* InitialActivity,FRHIGPUBufferReadback* ActivityReadback)
{
    check(IsInRenderingThread());
    if (!Grid.Validate(Flow,Error))return false;
    if (Steps<1 || Steps>512 || (State.IsValid() &&
        (StateSize!=Grid.Size || StateCellMeters!=Grid.CellMeters || bStatePeriodic!=Grid.bPeriodic ||
        StateOriginMeters!=Grid.OriginMeters || bStateSecondOrder!=Grid.bSecondOrder ||
        bStateActivityMemory!=Grid.bActivityMemory || InitialState || InitialActivity)))
    { Error=TEXT("Invalid batch size or implicit reset of persistent detail state");return false; }
    if (InitialState)
    {
        if (InitialState->Num()!=Flow.Num()) { Error=TEXT("Initial detail state size mismatch");return false; }
        for (const FVector4f& S:*InitialState)
            if (!FMath::IsFinite(S.X) || !FMath::IsFinite(S.Y) || !FMath::IsFinite(S.Z) || !FMath::IsFinite(S.W) || S.W<0)
            { Error=TEXT("Invalid initial detail state");return false; }
    }
    if (!Grid.bActivityMemory && (InitialActivity || ActivityReadback))
    { Error=TEXT("Activity input/readback requires explicit activity mode");return false; }
    if (InitialActivity)
    {
        if (InitialActivity->Num()!=Flow.Num()) { Error=TEXT("Initial activity size mismatch");return false; }
        for (float A:*InitialActivity)if (!FMath::IsFinite(A) || A<0 || A>1)
        { Error=TEXT("Initial activity must be finite and in [0,1]");return false; }
    }
    FRDGBuilder Graph(RHICmdList);
    FRDGBufferRef FlowBuffer=CreateStructuredBuffer(Graph,TEXT("RaftSim.Detail.MeanFlow"),Flow);
    TArray<FVector4f> Zero;
    if (!State.IsValid() && !InitialState)Zero.Init(FVector4f(0,0,0,0),Flow.Num());
    FRDGBufferRef Current=State.IsValid() ? Graph.RegisterExternalBuffer(State) :
        CreateStructuredBuffer(Graph,TEXT("RaftSim.Detail.Initial"),InitialState ? *InitialState : Zero);
    FRDGBufferRef CurrentActivity=nullptr;
    if (Grid.bActivityMemory)
    {
        TArray<float> ZeroActivity;
        if (!ActivityState.IsValid() && !InitialActivity)ZeroActivity.Init(0,Flow.Num());
        CurrentActivity=ActivityState.IsValid() ? Graph.RegisterExternalBuffer(ActivityState) :
            CreateStructuredBuffer(Graph,TEXT("RaftSim.Detail.InitialActivity"),InitialActivity ? *InitialActivity : ZeroActivity);
    }
    FRaftSimDetailWaterCS::FPermutationDomain Permutation;
    Permutation.Set<FRaftSimDetailWaterCS::FActivityMemory>(Grid.bActivityMemory);
    TShaderMapRef<FRaftSimDetailWaterCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Permutation);
    for (int32 Step=0;Step<Steps;++Step)
    {
        const FRDGBufferRef StepInitial=Current;
        const FRDGBufferRef InitialActivityForStep=CurrentActivity;
        const int32 StageCount=Grid.bSecondOrder ? 2 : 1;
        for (int32 Stage=0;Stage<StageCount;++Stage)
        {
            FRDGBufferRef Next=Graph.CreateBuffer(FRDGBufferDesc::CreateStructuredDesc(sizeof(FVector4f),Flow.Num()),TEXT("RaftSim.Detail.State"));
            auto* P=Graph.AllocParameters<FRaftSimDetailWaterCS::FParameters>();
            P->GridSize=Grid.Size;P->CellMeters=Grid.CellMeters;P->StepSeconds=Grid.StepSeconds;
            P->MomentumDamping=Grid.MomentumDampingPerSecond;P->FoamDecay=Grid.FoamDecayPerSecond;
            P->FoamSource=Grid.FoamSourcePerSecond;P->Periodic=Grid.bPeriodic ? 1u : 0u;
            P->SecondOrder=Grid.bSecondOrder ? 1u : 0u;P->RKStage=Stage;
            P->OriginMeters=Grid.OriginMeters;P->TurbulentHeadMeters=Grid.TurbulentHeadMeters;
            P->SimulationSeconds=float(SimulationSeconds+(Step+Stage)*double(Grid.StepSeconds));
            P->ActivitySource=Grid.ActivitySourcePerSecond;P->ActivityDecay=Grid.ActivityDecayPerSecond;
            P->PreviousActivity=nullptr;P->StepInitialActivity=nullptr;P->NextActivity=nullptr;
            if (Grid.bActivityMemory)
            {
                const auto NextActivity=Graph.CreateBuffer(FRDGBufferDesc::CreateStructuredDesc(sizeof(float),Flow.Num()),TEXT("RaftSim.Detail.Activity"));
                P->PreviousActivity=Graph.CreateSRV(CurrentActivity);P->StepInitialActivity=Graph.CreateSRV(InitialActivityForStep);
                P->NextActivity=Graph.CreateUAV(NextActivity);CurrentActivity=NextActivity;
            }
            P->StepInitialState=Graph.CreateSRV(StepInitial);
            P->MeanFlow=Graph.CreateSRV(FlowBuffer);P->PreviousState=Graph.CreateSRV(Current);P->NextState=Graph.CreateUAV(Next);
            FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Stateful Detail Water"),Shader,P,
                FComputeShaderUtils::GetGroupCount(Grid.Size,FIntPoint(8,8)));
            Current=Next;
        }
    }
    if (Readback)AddEnqueueCopyPass(Graph,Readback,Current,Flow.Num()*sizeof(FVector4f));
    if (ActivityReadback)AddEnqueueCopyPass(Graph,ActivityReadback,CurrentActivity,Flow.Num()*sizeof(float));
    if (Grid.bActivityMemory)Graph.QueueBufferExtraction(CurrentActivity,&ActivityState);
    Graph.QueueBufferExtraction(Current,&State);
    Graph.QueueBufferExtraction(FlowBuffer,&MeanFlowState);
    Graph.Execute();
    StateSize=Grid.Size;StateCellMeters=Grid.CellMeters;bStatePeriodic=Grid.bPeriodic;bStateSecondOrder=Grid.bSecondOrder;
    bStateActivityMemory=Grid.bActivityMemory;
    StateOriginMeters=Grid.OriginMeters;SimulationSeconds+=Steps*double(Grid.StepSeconds);StepCount+=Steps;
    return true;
}

bool FRaftSimDetailWaterGPU::Resolve(FRHICommandListImmediate& RHICmdList,FRHITexture* Target,FString& Error)
{
    check(IsInRenderingThread());
    if (!State.IsValid() || !MeanFlowState.IsValid() || !Target || Target->GetDesc().Extent!=StateSize ||
        Target->GetDesc().Format!=PF_A32B32G32R32F || !EnumHasAnyFlags(Target->GetDesc().Flags,ETextureCreateFlags::UAV))
    { Error=TEXT("Persistent detail resolve needs a matching float4 UAV target");return false; }
    FRDGBuilder Graph(RHICmdList);
    auto* P=Graph.AllocParameters<FRaftSimDetailResolveCS::FParameters>();
    P->GridSize=StateSize;P->CellMeters=StateCellMeters;
    P->MeanFlow=Graph.CreateSRV(Graph.RegisterExternalBuffer(MeanFlowState));
    P->DetailState=Graph.CreateSRV(Graph.RegisterExternalBuffer(State));
    auto Output=Graph.RegisterExternalTexture(CreateRenderTarget(Target,TEXT("RaftSim.Detail.Surface")));
    P->SurfaceOutput=Graph.CreateUAV(Output);
    TShaderMapRef<FRaftSimDetailResolveCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
    FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Detail Surface Resolve"),Shader,P,
        FComputeShaderUtils::GetGroupCount(StateSize,FIntPoint(8,8)));
    Graph.SetTextureAccessFinal(Output,ERHIAccess::SRVMask);
    Graph.Execute();
    return true;
}
