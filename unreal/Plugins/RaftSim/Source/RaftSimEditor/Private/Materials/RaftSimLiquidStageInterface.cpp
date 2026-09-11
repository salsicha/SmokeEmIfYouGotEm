#include "RaftSimLiquidStageInterface.h"
#include "NiagaraCompileHashVisitor.h"
#include "NiagaraShaderParametersBuilder.h"
#include "NiagaraGPUSystemTick.h"
#include "NiagaraSimStageData.h"
#include "RenderGraphBuilder.h"

struct FRaftSimLiquidPendingGroup
{
    TArray<FRaftSimLiquidCompletedStage> Records;
    uint32 Ordinal=0;
};
RDG_REGISTER_BLACKBOARD_STRUCT(FRaftSimLiquidPendingGroup);

namespace
{
BEGIN_SHADER_PARAMETER_STRUCT(FLiquidStageParameters,)
    SHADER_PARAMETER(uint32,Ready)
END_SHADER_PARAMETER_STRUCT()

struct FLiquidStageProxy final : FNiagaraDataInterfaceProxy
{
    virtual int32 PerInstanceDataPassedToRenderThreadSize() const override { return 0; }
    virtual void PreStage(const FNDIGpuComputePreStageContext& Context) override
    { URaftSimLiquidStageInterface::PreStageEvent().Broadcast(Context); }
    virtual bool RequiresPostStageFinalize() const override
    { return URaftSimLiquidStageInterface::PostGroupEvent().IsBound(); }
    virtual void PostStage(const FNDIGpuComputePostStageContext& Context) override
    {
        if (!URaftSimLiquidStageInterface::PostGroupEvent().IsBound()) return;
        const auto& Stage=Context.GetSimStageData();
        FRaftSimLiquidCompletedStage Record;
        Record.SystemId=Context.GetSystemInstanceID();Record.Context=Context.GetComputeInstanceData().Context;
        Record.StageName=Stage.StageMetaData->SimulationStageName;
        Record.StageIndex=Stage.StageIndex;Record.Iteration=Stage.IterationIndex;Record.Iterations=Stage.NumIterations;
        Record.Loop=Stage.LoopIndex;Record.Loops=Stage.NumLoops;
        Record.First=Stage.bFirstStage;Record.Last=Stage.bLastStage;Record.Reset=Context.GetComputeInstanceData().bResetData;
        Record.RateSpawns=Context.GetComputeInstanceData().SpawnInfo.SpawnRateInstances;
        Record.EventSpawns=Context.GetComputeInstanceData().SpawnInfo.EventSpawnTotal;
        Context.GetGraphBuilder().Blackboard.GetOrCreate<FRaftSimLiquidPendingGroup>().Records.Add(Record);
    }
    virtual void FinalizePostStage(FRDGBuilder& Graph,const FNiagaraGpuComputeDispatchInterface&) override
    {
        auto& Pending=Graph.Blackboard.GetOrCreate<FRaftSimLiquidPendingGroup>();
        if (Pending.Records.IsEmpty()) return;
        // Unreal calls all PostStage functions before ANY FinalizePostStage.
        // Whichever participating proxy finalizes first drains the complete
        // group once. Other proxies find it empty. Never defer to the next frame.
        TArray<FRaftSimLiquidCompletedStage> Records=MoveTemp(Pending.Records);
        URaftSimLiquidStageInterface::PostGroupEvent().Broadcast(Graph,Pending.Ordinal++,Records);
    }
};
}

FRaftSimLiquidPreStage& URaftSimLiquidStageInterface::PreStageEvent()
{ static FRaftSimLiquidPreStage Event;return Event; }

FRaftSimLiquidPostGroup& URaftSimLiquidStageInterface::PostGroupEvent()
{ static FRaftSimLiquidPostGroup Event;return Event; }

FNiagaraVariable URaftSimLiquidStageInterface::Variable()
{ return FNiagaraVariable(FNiagaraTypeDefinition(StaticClass()),TEXT("User.RiverCurrentSurfaceStage")); }

URaftSimLiquidStageInterface::URaftSimLiquidStageInterface(const FObjectInitializer& Initializer):Super(Initializer)
{ Proxy.Reset(new FLiquidStageProxy()); }

void URaftSimLiquidStageInterface::PostInitProperties()
{
    Super::PostInitProperties();
    if (HasAnyFlags(RF_ClassDefaultObject))
        FNiagaraTypeRegistry::Register(FNiagaraTypeDefinition(GetClass()),ENiagaraTypeRegistryFlags::AllowAnyVariable | ENiagaraTypeRegistryFlags::AllowParameter);
}

void URaftSimLiquidStageInterface::BuildShaderParameters(FNiagaraShaderParametersBuilder& Builder) const
{ Builder.AddNestedStruct<FLiquidStageParameters>(); }

void URaftSimLiquidStageInterface::SetShaderParameters(const FNiagaraDataInterfaceSetShaderParametersContext& Context) const
{ Context.GetParameterNestedStruct<FLiquidStageParameters>()->Ready=1; }

#if WITH_EDITORONLY_DATA
void URaftSimLiquidStageInterface::GetFunctionsInternal(TArray<FNiagaraFunctionSignature>& Functions) const
{
    FNiagaraFunctionSignature Function;Function.Name=TEXT("ReadReady");
    Function.bMemberFunction=true;Function.bRequiresContext=false;
    Function.bSupportsCPU=false;Function.bSupportsGPU=true;
    Function.Inputs.Add(FNiagaraVariable(FNiagaraTypeDefinition(GetClass()),TEXT("Stage")));
    Function.Outputs.Add(FNiagaraVariable(FNiagaraTypeDefinition::GetIntDef(),TEXT("Ready")));
    Functions.Add(Function);
}
bool URaftSimLiquidStageInterface::AppendCompileHash(FNiagaraCompileHashVisitor* Visitor) const
{
    if (!Super::AppendCompileHash(Visitor)) return false;
    Visitor->UpdateShaderParameters<FLiquidStageParameters>();
    return Visitor->UpdateString(TEXT("RiverCurrentSurfaceStageVersion"),TEXT("1"));
}
void URaftSimLiquidStageInterface::GetParameterDefinitionHLSL(const FNiagaraDataInterfaceGPUParamInfo& Info,FString& Code)
{ Code+=FString::Printf(TEXT("uint %s_Ready;\n"),*Info.DataInterfaceHLSLSymbol); }
bool URaftSimLiquidStageInterface::GetFunctionHLSL(const FNiagaraDataInterfaceGPUParamInfo& Info,const FNiagaraDataInterfaceGeneratedFunction& Function,int,FString& Code)
{
    if (Function.DefinitionName!=TEXT("ReadReady")) return false;
    Code+=FString::Printf(TEXT("void %s(out int Ready) { Ready=(int)%s_Ready; }\n"),*Function.InstanceName,*Info.DataInterfaceHLSLSymbol);
    return true;
}
#endif
