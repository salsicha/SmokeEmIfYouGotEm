#pragma once

#include "NiagaraDataInterface.h"
#include "RenderGraphFwd.h"
#include "RaftSimLiquidStageInterface.generated.h"

// Unsaved editor-review DI. The proxy hook orders reconstruction before the
// existing secondary emitter; it never changes the engine or particle buffers.
DECLARE_MULTICAST_DELEGATE_OneParam(FRaftSimLiquidPreStage,const FNDIGpuComputePreStageContext&);

struct FNiagaraComputeExecutionContext;
struct FRaftSimLiquidCompletedStage
{
    uint64 SystemId=0;
    FNiagaraComputeExecutionContext* Context=nullptr;
    FName StageName;
    uint32 StageIndex=0,Iteration=0,Iterations=0,Loop=0,Loops=0;
    uint32 RateSpawns=0,EventSpawns=0;
    // Valid only during the synchronous group callback. This is the immutable
    // tick upload, not the GT parameter store that may already hold a later tick.
    const uint8* ExternalParameters=nullptr;
    uint32 ExternalParameterBytes=0;
    float EngineDeltaSeconds=-1;
    bool First=false,Last=false,Reset=false;
};
// Synchronous render-thread notification after every dispatch/DI post-stage in
// the group. Records cover only emitters carrying this DI, not arbitrary engine
// work. Consumers must verify complete participant/stage/tick alignment before
// coupling. Scheduling after a group alone does not establish conservation.
DECLARE_MULTICAST_DELEGATE_ThreeParams(FRaftSimLiquidPostGroup,FRDGBuilder&,uint32,TConstArrayView<FRaftSimLiquidCompletedStage>);
// Read-only binding of the current explicit interface during graph construction.
// The owning simulation retains and exchanges it; this DI never advances it.
DECLARE_MULTICAST_DELEGATE_ThreeParams(FRaftSimLiquidSurfaceBinding,FRDGBuilder&,uint64,FRDGTextureRef&);

UCLASS(EditInlineNew)
class URaftSimLiquidStageInterface : public UNiagaraDataInterface
{
    GENERATED_BODY()
public:
    URaftSimLiquidStageInterface(const FObjectInitializer& Initializer);
    virtual void PostInitProperties() override;
    virtual bool CanExecuteOnTarget(ENiagaraSimTarget Target) const override { return Target==ENiagaraSimTarget::GPUComputeSim; }
    virtual void BuildShaderParameters(FNiagaraShaderParametersBuilder& Builder) const override;
    virtual void SetShaderParameters(const FNiagaraDataInterfaceSetShaderParametersContext& Context) const override;
#if WITH_EDITORONLY_DATA
    virtual void GetFunctionsInternal(TArray<FNiagaraFunctionSignature>& Functions) const override;
    virtual bool AppendCompileHash(FNiagaraCompileHashVisitor* Visitor) const override;
    virtual void GetParameterDefinitionHLSL(const FNiagaraDataInterfaceGPUParamInfo& Info,FString& Code) override;
    virtual bool GetFunctionHLSL(const FNiagaraDataInterfaceGPUParamInfo& Info,const FNiagaraDataInterfaceGeneratedFunction& Function,int FunctionIndex,FString& Code) override;
#endif
    // Bind/unbind and broadcast only on the render thread.
    static FRaftSimLiquidPreStage& PreStageEvent();
    static FRaftSimLiquidPostGroup& PostGroupEvent();
    static FRaftSimLiquidSurfaceBinding& SurfaceBindingEvent();
    static FNiagaraVariable Variable();
};
