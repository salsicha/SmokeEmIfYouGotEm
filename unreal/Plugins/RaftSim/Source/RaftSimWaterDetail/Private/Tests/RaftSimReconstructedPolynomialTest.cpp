#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/DateTime.h"
#include "GlobalShader.h"
#include "ShaderParameterStruct.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include "HAL/FileManager.h"
#include <cmath>
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS && WITH_UNREAL_DEVELOPER_TOOLS
class FRaftSimReconstructedPolynomialTestCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimReconstructedPolynomialTestCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimReconstructedPolynomialTestCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,Count)
        SHADER_PARAMETER(FUintVector4,OmegaBits)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,RowOffsets)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,Columns)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint2>,Matrix)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint2>,Scaled)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint2>,InverseRoot)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint2>,RHS)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint4>,Output)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    {return IsD3DPlatform(P.Platform) && IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM6);}
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimReconstructedPolynomialTestCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimReconstructedPolynomialTest.usf","MainCS",SF_Compute);

namespace
{
struct FPolynomialFixture
{
    uint32 N=0,NNZ=0,Degree=0,Tag=0;
    double Omega=0;
    TArray<uint32> Rows,Columns;
    TArray<double> Matrix,Scaled,Inverse,RHS,Action,Precondition,ActionScale,PreconditionScale;
};
template<class T> bool ReadValues(const TArray<uint8>& Bytes,int64& Offset,TArray<T>& Values,uint32 Count)
{
    const int64 Length=int64(Count)*sizeof(T);
    if(Offset<0 || Offset+Length>Bytes.Num())return false;
    Values.SetNumUninitialized(Count);
    FMemory::Memcpy(Values.GetData(),Bytes.GetData()+Offset,Length);Offset+=Length;return true;
}
bool ReadFixture(const TArray<uint8>& Bytes,TArray<FPolynomialFixture>& Cases)
{
    if(Bytes.Num()<12)return false;
    uint32 Header[3];FMemory::Memcpy(Header,Bytes.GetData(),12);
    if(Header[0]!=0x52535044 || Header[1]!=1 || Header[2]!=6)return false;
    int64 Offset=12;
    for(uint32 Case=0;Case<Header[2];++Case)
    {
        if(Offset+24>Bytes.Num())return false;
        FPolynomialFixture F;
        FMemory::Memcpy(&F.N,Bytes.GetData()+Offset,4);FMemory::Memcpy(&F.NNZ,Bytes.GetData()+Offset+4,4);
        FMemory::Memcpy(&F.Degree,Bytes.GetData()+Offset+8,4);FMemory::Memcpy(&F.Tag,Bytes.GetData()+Offset+12,4);
        FMemory::Memcpy(&F.Omega,Bytes.GetData()+Offset+16,8);Offset+=24;
        if(F.N<1 || F.N>524288 || F.NNZ<F.N || F.NNZ>32*F.N || F.Degree!=1 || F.Tag!=Case ||
            !FMath::IsFinite(F.Omega) || F.Omega<=0 || F.Omega>1)return false;
        if(!ReadValues(Bytes,Offset,F.Rows,F.N+1) || !ReadValues(Bytes,Offset,F.Columns,F.NNZ) ||
            !ReadValues(Bytes,Offset,F.Matrix,F.NNZ) || !ReadValues(Bytes,Offset,F.Scaled,F.NNZ) ||
            !ReadValues(Bytes,Offset,F.Inverse,F.N) || !ReadValues(Bytes,Offset,F.RHS,F.N) ||
            !ReadValues(Bytes,Offset,F.Action,F.N) || !ReadValues(Bytes,Offset,F.Precondition,F.N) ||
            !ReadValues(Bytes,Offset,F.ActionScale,F.N) || !ReadValues(Bytes,Offset,F.PreconditionScale,F.N))return false;
        if(F.Rows[0]!=0 || F.Rows[F.N]!=F.NNZ)return false;
        for(uint32 I=0;I<F.N;++I)
        {
            if(F.Rows[I]>=F.Rows[I+1] || F.Rows[I+1]>F.NNZ || !FMath::IsFinite(F.Inverse[I]) || F.Inverse[I]<=0 ||
                !FMath::IsFinite(F.RHS[I]) || !FMath::IsFinite(F.Action[I]) || !FMath::IsFinite(F.Precondition[I]) ||
                !FMath::IsFinite(F.ActionScale[I]) || F.ActionScale[I]<0 ||
                !FMath::IsFinite(F.PreconditionScale[I]) || F.PreconditionScale[I]<0)return false;
            for(uint32 J=F.Rows[I];J<F.Rows[I+1];++J)
                if(F.Columns[J]>=F.N || (J>F.Rows[I] && F.Columns[J]<=F.Columns[J-1]) ||
                    !FMath::IsFinite(F.Matrix[J]) || !FMath::IsFinite(F.Scaled[J]) ||
                    (F.Matrix[J]!=0 && F.Scaled[J]==0))return false;
        }
        Cases.Add(MoveTemp(F));
    }
    return Offset==Bytes.Num();
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FReconstructedPolynomialTest,"RaftSim.WaterDetail.ReconstructedPolynomialGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FReconstructedPolynomialTest::RunTest(const FString&)
{
    FString Path;TArray<uint8> Bytes;TArray<FPolynomialFixture> Cases;
    if(GUsingNullRHI || !IsD3DPlatform(GMaxRHIShaderPlatform) || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM6 ||
        !FParse::Value(FCommandLine::Get(),TEXT("RaftSimReconstructedPolynomialFixture="),Path) ||
        !FFileHelper::LoadFileToArray(Bytes,*Path) || !ReadFixture(Bytes,Cases))
    {AddError(TEXT("Actual D3D SM6 GPU and complete original six-case FP64 fixture required"));return false;}
    // The original factored Python operator is independent of these CSR loops.
    // Componentwise roundoff scales prevent large rows from hiding lost tiny rows.
    constexpr double Roundoff=128*std::numeric_limits<double>::epsilon();
    uint32 CPUFailures=0,GPUFailures=0,Completed=0;TArray<FString> Details;
    for(const auto& F:Cases)
        for(uint32 I=0;I<F.N;++I)
        {
            double Action=0,ScaledAction=0;
            for(uint32 J=F.Rows[I];J<F.Rows[I+1];++J)
            {
                const uint32 C=F.Columns[J];Action+=F.Matrix[J]*F.RHS[C];
                ScaledAction+=F.Scaled[J]*(F.RHS[C]*F.Inverse[C]);
            }
            const double V=F.RHS[I]*F.Inverse[I];
            const double P=F.Omega*F.Inverse[I]*(V+V-F.Omega*ScaledAction);
            CPUFailures+=!FMath::IsFinite(Action) || !FMath::IsFinite(P) ||
                FMath::Abs(Action-F.Action[I])>Roundoff*F.ActionScale[I] ||
                FMath::Abs(P-F.Precondition[I])>Roundoff*F.PreconditionScale[I];
        }
    ENQUEUE_RENDER_COMMAND(ReconstructedPolynomial)([&](FRHICommandListImmediate& Cmd)
    {
        for(const auto& F:Cases)
        {
            FRDGBuilder Graph(Cmd);
            auto Rows=CreateStructuredBuffer(Graph,TEXT("Polynomial.Rows"),F.Rows);
            auto Columns=CreateStructuredBuffer(Graph,TEXT("Polynomial.Columns"),F.Columns);
            auto Matrix=CreateStructuredBuffer(Graph,TEXT("Polynomial.Matrix"),F.Matrix);
            auto Scaled=CreateStructuredBuffer(Graph,TEXT("Polynomial.Scaled"),F.Scaled);
            auto Inverse=CreateStructuredBuffer(Graph,TEXT("Polynomial.Inverse"),F.Inverse);
            auto RHS=CreateStructuredBuffer(Graph,TEXT("Polynomial.RHS"),F.RHS);
            auto Desc=FRDGBufferDesc::CreateStructuredDesc(16,F.N);Desc.Usage|=BUF_SourceCopy;
            auto Out=Graph.CreateBuffer(Desc,TEXT("Polynomial.Output"));
            auto* P=Graph.AllocParameters<FRaftSimReconstructedPolynomialTestCS::FParameters>();
            P->Count=F.N;P->OmegaBits=FUintVector4(0,0,0,0);FMemory::Memcpy(&P->OmegaBits,&F.Omega,8);
            P->RowOffsets=Graph.CreateSRV(Rows);P->Columns=Graph.CreateSRV(Columns);
            P->Matrix=Graph.CreateSRV(Matrix);P->Scaled=Graph.CreateSRV(Scaled);
            P->InverseRoot=Graph.CreateSRV(Inverse);P->RHS=Graph.CreateSRV(RHS);P->Output=Graph.CreateUAV(Out);
            TShaderMapRef<FRaftSimReconstructedPolynomialTestCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
            FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Reconstructed Original Action And Degree1 Preconditioner"),
                Shader,P,FIntVector(FMath::DivideAndRoundUp(F.N,256u),1,1));
            FRHIGPUBufferReadback Read(TEXT("Polynomial.Read"));AddEnqueueCopyPass(Graph,&Read,Out,16*F.N);
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            const auto* Values=static_cast<const uint8*>(Read.Lock(16*F.N));
            if(!Values)continue;
            ++Completed;double MaxActionScaledError=0,MaxPreconditionScaledError=0;uint32 Wrong=0;
            for(uint32 I=0;I<F.N;++I)
            {
                double Action,PValue;FMemory::Memcpy(&Action,Values+16*I,8);FMemory::Memcpy(&PValue,Values+16*I+8,8);
                const double AE=FMath::Abs(Action-F.Action[I]),PE=FMath::Abs(PValue-F.Precondition[I]);
                const bool Bad=!FMath::IsFinite(Action) || !FMath::IsFinite(PValue) ||
                    AE>Roundoff*F.ActionScale[I] || PE>Roundoff*F.PreconditionScale[I];
                if(Bad && Wrong<3)Details.Add(FString::Printf(TEXT("case%u row%u action %.17g expected %.17g precondition %.17g expected %.17g"),
                    F.Tag,I,Action,F.Action[I],PValue,F.Precondition[I]));
                Wrong+=Bad;
                if(F.ActionScale[I]>0)MaxActionScaledError=FMath::Max(MaxActionScaledError,AE/F.ActionScale[I]);
                if(F.PreconditionScale[I]>0)MaxPreconditionScaledError=FMath::Max(MaxPreconditionScaledError,PE/F.PreconditionScale[I]);
            }
            Read.Unlock();GPUFailures+=Wrong;
            Details.Add(FString::Printf(TEXT("original actual-RHS case%u unknowns%u entries%u: CPU/GPU FP64 arithmetic, GPU failures%u; max component-scaled errors action %.12g / degree1 precondition %.12g; NOT a full solve, cost or scene pass"),
                F.Tag,F.N,F.NNZ,Wrong,MaxActionScaledError,MaxPreconditionScaledError));
        }
    });
    FlushRenderingCommands();
    TestEqual(TEXT("Native CSR action/preconditioner matches original factored operator/reference"),CPUFailures,0u);
    TestEqual(TEXT("Read both original poles for all three sources"),Completed,6u);
    TestEqual(TEXT("GPU action/preconditioner passes componentwise double roundoff checks including tiny rows"),GPUFailures,0u);
    for(const auto& Detail:Details)AddInfo(Detail);
    return !HasAnyErrors();
}

class FRaftSimReconstructedCGTestCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimReconstructedCGTestCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimReconstructedCGTestCS,FGlobalShader);
    class FPhase : SHADER_PERMUTATION_INT("RAFTSIM_RECONSTRUCTED_CG_PHASE",14);
    class FParallelReductions : SHADER_PERMUTATION_BOOL("RAFTSIM_RECONSTRUCTED_CG_PARALLEL_REDUCTION");
    class FSlotMajor : SHADER_PERMUTATION_BOOL("RAFTSIM_RECONSTRUCTED_CG_SLOT_MAJOR");
    class FBatchedLoads : SHADER_PERMUTATION_BOOL("RAFTSIM_RECONSTRUCTED_CG_BATCHED_LOADS");
    class FFusedDirection : SHADER_PERMUTATION_BOOL("RAFTSIM_RECONSTRUCTED_CG_FUSED_DIRECTION");
    using FPermutationDomain=TShaderPermutationDomain<FPhase,FParallelReductions,FSlotMajor,FBatchedLoads,FFusedDirection>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,Count)
        SHADER_PARAMETER(uint32,PartialCount)
        SHADER_PARAMETER(uint32,InitializeDirection)
        SHADER_PARAMETER(FUintVector4,OmegaBits)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,RowOffsets)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,Columns)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint2>,Matrix)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint2>,Scaled)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint2>,InverseRoot)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint2>,RHS)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint2>,DirectionInput)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint2>,PartialInput)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint2>,ControlInput)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,DiagnosticInput)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint2>,X)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint2>,Residual)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint2>,Z)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint2>,Direction)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint2>,Applied)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint2>,Partials)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint2>,Control)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Diagnostics)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    {
        const FPermutationDomain Perm(P.PermutationId);
        return IsD3DPlatform(P.Platform) && IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM6) &&
            (!Perm.Get<FFusedDirection>() || (Perm.Get<FPhase>()==6 && !Perm.Get<FBatchedLoads>())) &&
            (Perm.Get<FPhase>()<11 || (Perm.Get<FParallelReductions>() && !Perm.Get<FBatchedLoads>()));
    }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimReconstructedCGTestCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimReconstructedCGTest.usf","MainCS",SF_Compute);

namespace
{
double Peak(const TArray<double>& X)
{double V=0;for(double Item:X)V=FMath::Max(V,FMath::Abs(Item));return V;}
double Dot(const TArray<double>& A,const TArray<double>& B)
{double V=0;for(int32 I=0;I<A.Num();++I)V+=A[I]*B[I];return V;}
double PowerFloor(double V)
{int Exponent=0;std::frexp(V,&Exponent);return std::ldexp(1.,Exponent-1);}
TArray<double> Apply(const FPolynomialFixture& F,const TArray<double>& X)
{
    TArray<double> Y;Y.Init(0.,F.N);
    for(uint32 I=0;I<F.N;++I)for(uint32 J=F.Rows[I];J<F.Rows[I+1];++J)Y[I]+=F.Matrix[J]*X[F.Columns[J]];
    return Y;
}
TArray<double> Precondition(const FPolynomialFixture& F,const TArray<double>& R)
{
    TArray<double> Y;Y.Init(0.,F.N);
    for(uint32 I=0;I<F.N;++I)
    {
        double Sum=0;for(uint32 J=F.Rows[I];J<F.Rows[I+1];++J)
        {const uint32 C=F.Columns[J];Sum+=F.Scaled[J]*(R[C]*F.Inverse[C]);}
        const double V=R[I]*F.Inverse[I];Y[I]=F.Omega*F.Inverse[I]*(V+V-F.Omega*Sum);
    }
    return Y;
}
bool NativeRangeCG(const FPolynomialFixture& F,TArray<double>& X,uint32& Completed)
{
    X.Init(0.,F.N);Completed=0;
    if(Peak(F.RHS)==0)return true;
    double Scale=PowerFloor(Peak(F.RHS));TArray<double> R=F.RHS;
    for(double& V:R)V/=Scale;
    TArray<double> Z=Precondition(F,R),P=Z;double RZ=Dot(R,Z);
    for(uint32 Iteration=0;Iteration<40;++Iteration)
    {
        if(RZ==0)break;
        const TArray<double> AP=Apply(F,P);const double Denominator=Dot(P,AP);
        if(!FMath::IsFinite(Denominator) || Denominator<=0)return false;
        const double Alpha=RZ/Denominator;
        for(uint32 I=0;I<F.N;++I){X[I]+=(Alpha*P[I])*Scale;R[I]-=Alpha*AP[I];}
        ++Completed;const double Maximum=Peak(R);
        if(!FMath::IsFinite(Maximum))return false;
        if(Maximum==0)break;
        const double Ratio=PowerFloor(Maximum);Scale*=Ratio;
        if(!FMath::IsFinite(Scale) || Scale==0)return false;
        for(double& V:R)V/=Ratio;
        Z=Precondition(F,R);const double Next=Dot(R,Z);
        if(!FMath::IsFinite(Next) || Next<0)return false;
        const double Beta=Ratio*Next/RZ;
        for(uint32 I=0;I<F.N;++I)P[I]=Z[I]+Beta*P[I];RZ=Next;
    }
    return true;
}
double RelativeResidual(const FPolynomialFixture& F,const TArray<double>& X)
{
    const TArray<double> AX=Apply(F,X);const double Maximum=Peak(F.RHS);
    double Error=0,Norm=0;
    for(uint32 I=0;I<F.N;++I)
    {
        if(!FMath::IsFinite(X[I]) || !FMath::IsFinite(AX[I]))return std::numeric_limits<double>::infinity();
        const double R=Maximum>0?F.RHS[I]/Maximum:0.;
        const double E=Maximum>0?AX[I]/Maximum-R:AX[I];Error+=E*E;Norm+=R*R;
    }
    return FMath::Sqrt(Error/(Norm>0?Norm:1.));
}
void AppendBytes(TArray<uint8>& Bytes,const void* Data,int32 Count)
{const int32 Offset=Bytes.AddUninitialized(Count);FMemory::Memcpy(Bytes.GetData()+Offset,Data,Count);}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FReconstructedCGTest,"RaftSim.WaterDetail.ReconstructedCGGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FReconstructedCGTest::RunTest(const FString&)
{
    FString Path,OutputPath;TArray<uint8> Bytes;TArray<FPolynomialFixture> Cases;
    if(GUsingNullRHI || !IsD3DPlatform(GMaxRHIShaderPlatform) || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM6 ||
        !FParse::Value(FCommandLine::Get(),TEXT("RaftSimReconstructedPolynomialFixture="),Path) ||
        !FParse::Value(FCommandLine::Get(),TEXT("RaftSimReconstructedCGOutput="),OutputPath) ||
        IFileManager::Get().FileExists(*OutputPath) || !FFileHelper::LoadFileToArray(Bytes,*Path) || !ReadFixture(Bytes,Cases))
    {AddError(TEXT("Actual D3D SM6 GPU, original six-case fixture and fresh output path required"));return false;}
    FString ControlCase;
    FParse::Value(FCommandLine::Get(),TEXT("RaftSimReconstructedCGControl="),ControlCase);
    const bool Synthetic=!ControlCase.IsEmpty();
    if(Synthetic && ControlCase!=TEXT("zero-rhs") && ControlCase!=TEXT("identity-range"))
    {AddError(TEXT("Unknown synthetic CG control; use zero-rhs or identity-range"));return false;}
    if(Synthetic)
    {
        // Explicit diagnostic copies only. Never mutate the captured fixture or
        // present an identity/zero-forcing check as source-physics qualification.
        constexpr int Exponents[6]={-1074,-1022,-600,0,600,1000};
        for(auto& F:Cases)
        {
            if(ControlCase==TEXT("zero-rhs")){F.RHS.Init(0.,F.N);continue;}
            F.NNZ=F.N;F.Omega=1.;F.Rows.SetNum(F.N+1);F.Columns.SetNum(F.N);
            F.Matrix.Init(1.,F.N);F.Scaled.Init(1.,F.N);F.Inverse.Init(1.,F.N);
            const double Value=std::ldexp(1.,Exponents[F.Tag]);
            for(uint32 I=0;I<F.N;++I)
            {F.Rows[I]=I;F.Columns[I]=I;F.RHS[I]=I%3==0?Value:(I%3==1?-Value:0.);}
            F.Rows[F.N]=F.N;
        }
        AddInfo(FString::Printf(TEXT("SYNTHETIC control %s: separate termination/range diagnostic, NOT original actual-RHS or physical-history acceptance"),*ControlCase));
    }
    const FString SourceLabel=Synthetic?FString::Printf(TEXT("SYNTHETIC %s"),*ControlCase):TEXT("original actual-RHS");
    uint32 Failures=0,Completed=0;TArray<FString> Details;TArray<uint8> Output;
    const bool ParallelReductions=FParse::Param(FCommandLine::Get(),TEXT("RaftSimReconstructedCGParallelReductions"));
    const bool PhaseTiming=FParse::Param(FCommandLine::Get(),TEXT("RaftSimReconstructedCGPhaseTiming"));
    const bool RequestedSlotMajor=FParse::Param(FCommandLine::Get(),TEXT("RaftSimReconstructedCGSlotMajor"));
    const bool BatchedLoads=FParse::Param(FCommandLine::Get(),TEXT("RaftSimReconstructedCGBatchedLoads"));
    const bool PairedLayouts=FParse::Param(FCommandLine::Get(),TEXT("RaftSimReconstructedCGPairedLayouts"));
    const bool RequestedFuseDirection=FParse::Param(FCommandLine::Get(),TEXT("RaftSimReconstructedCGFuseDirection"));
    const bool PairedFusion=FParse::Param(FCommandLine::Get(),TEXT("RaftSimReconstructedCGPairedFusion"));
    const bool RequestedFuseReductions=FParse::Param(FCommandLine::Get(),TEXT("RaftSimReconstructedCGFuseReductions"));
    const bool PairedReductionFusion=FParse::Param(FCommandLine::Get(),TEXT("RaftSimReconstructedCGPairedReductionFusion"));
    const bool PairedComparison=PairedLayouts || PairedFusion || PairedReductionFusion;
    const bool ResidentBurst=FParse::Param(FCommandLine::Get(),TEXT("RaftSimReconstructedCGResidentBurst"));
    const uint32 ResidentSolves=ResidentBurst?16u:1u;
    if(ResidentBurst && (PhaseTiming || !GSupportsTimestampRenderQueries))
    {AddError(TEXT("Resident burst requires outer timestamps and no per-phase query instrumentation"));return false;}
    const int32 Repeats=PairedComparison?10:1;
    if((RequestedFuseReductions || PairedReductionFusion) && (!ParallelReductions || BatchedLoads ||
        RequestedFuseDirection || PairedFusion || (PairedReductionFusion && (PairedLayouts || PhaseTiming || RequestedFuseReductions))))
    {AddError(TEXT("Reduction fusion requires parallel reductions and no direction fusion/batched loads; paired reduction control owns its schedule"));return false;}
    if((PairedFusion && (PairedLayouts || PhaseTiming || RequestedFuseDirection)) ||
        (BatchedLoads && (PairedFusion || RequestedFuseDirection)))
    {AddError(TEXT("Paired fusion chooses separate/fused schedules; omit layout pairing, phase timing, forced fusion and batched loads"));return false;}
    if(PairedLayouts && (PhaseTiming || RequestedSlotMajor || BatchedLoads))
    {AddError(TEXT("Paired layout control selects CSR/slot alternately; omit phase timing, forced layout and batched-load flags"));return false;}
    if(PhaseTiming && !GSupportsTimestampRenderQueries)
    {AddError(TEXT("Requested per-phase GPU timestamps are unavailable"));return false;}
    // Distinct magic prevents a synthetic control being fed to the original
    // factored-operator audit as if it were an actual-source native result.
    const uint32 Header[3]={Synthetic?0x52534343u:0x52534347u,1,6};AppendBytes(Output,Header,12);
    ENQUEUE_RENDER_COMMAND(ReconstructedCG)([&](FRHICommandListImmediate& Cmd)
    {
        TArray<TArray<uint8>> FirstResults;FirstResults.SetNum(6);
        for(int32 Repeat=0;Repeat<Repeats;++Repeat)
        {
        const bool SlotMajor=PairedLayouts?(Repeat%2)!=0:RequestedSlotMajor;
        const bool FuseDirection=PairedFusion?(Repeat%2)!=0:RequestedFuseDirection;
        const bool FuseReductions=PairedReductionFusion?(Repeat%2)!=0:RequestedFuseReductions;
        const bool LastRepeat=Repeat==Repeats-1;
        for(const auto& F:Cases)
        {
            TArray<double> CPU;uint32 CPUIterations=0;
            const bool CPUSuccess=NativeRangeCG(F,CPU,CPUIterations);
            // Storage-only transpose: each row keeps every original coefficient,
            // column and summation order. Padded slots are never read by a row.
            TArray<uint32> PackedColumns;TArray<double> PackedMatrix,PackedScaled;
            if(SlotMajor)
            {
                uint32 Width=0;for(uint32 I=0;I<F.N;++I)Width=FMath::Max(Width,F.Rows[I+1]-F.Rows[I]);
                const int64 Entries=int64(Width)*F.N;
                // Explicit test allocation limit, not truncation of a matrix.
                if(Entries>64*1024*1024){++Failures;Details.Add(TEXT("Slot-major test allocation exceeds bounded storage; no coefficients dropped"));continue;}
                PackedColumns.Init(0,uint32(Entries));PackedMatrix.Init(0.,uint32(Entries));PackedScaled.Init(0.,uint32(Entries));
                bool Exact=true;
                for(uint32 I=0;I<F.N;++I)for(uint32 J=F.Rows[I];J<F.Rows[I+1];++J)
                {
                    const uint32 K=(J-F.Rows[I])*F.N+I;
                    PackedColumns[K]=F.Columns[J];PackedMatrix[K]=F.Matrix[J];PackedScaled[K]=F.Scaled[J];
                    Exact &= PackedColumns[K]==F.Columns[J] && FMemory::Memcmp(&PackedMatrix[K],&F.Matrix[J],8)==0 &&
                        FMemory::Memcmp(&PackedScaled[K],&F.Scaled[J],8)==0;
                }
                if(!Exact){++Failures;continue;}
                Details.Add(FString::Printf(TEXT("original case%u slot-major width%u slots%lld original entries%u: every matrix/scaled coefficient and column exact, original row order retained"),F.Tag,Width,Entries,F.NNZ));
            }
            FRDGBuilder Graph(Cmd);
            auto Rows=CreateStructuredBuffer(Graph,TEXT("ReconstructedCG.Rows"),F.Rows);
            auto Columns=CreateStructuredBuffer(Graph,TEXT("ReconstructedCG.Columns"),SlotMajor?PackedColumns:F.Columns);
            auto Matrix=CreateStructuredBuffer(Graph,TEXT("ReconstructedCG.Matrix"),SlotMajor?PackedMatrix:F.Matrix);
            auto Scaled=CreateStructuredBuffer(Graph,TEXT("ReconstructedCG.Scaled"),SlotMajor?PackedScaled:F.Scaled);
            auto Inverse=CreateStructuredBuffer(Graph,TEXT("ReconstructedCG.Inverse"),F.Inverse);
            auto RHS=CreateStructuredBuffer(Graph,TEXT("ReconstructedCG.RHS"),F.RHS);
            const uint32 Groups=FMath::DivideAndRoundUp(F.N,256u);
            auto Make=[&](uint32 Stride,uint32 Count,const TCHAR* Name)
            {auto Desc=FRDGBufferDesc::CreateStructuredDesc(Stride,Count);Desc.Usage|=BUF_SourceCopy;return Graph.CreateBuffer(Desc,Name);};
            auto X=Make(8,F.N,TEXT("ReconstructedCG.X")),R=Make(8,F.N,TEXT("ReconstructedCG.Residual"));
            auto Z=Make(8,F.N,TEXT("ReconstructedCG.Z")),P=Make(8,F.N,TEXT("ReconstructedCG.Direction"));
            auto AlternateP=FuseDirection?Make(8,F.N,TEXT("ReconstructedCG.AlternateDirection")):nullptr;
            FRDGBufferRef CurrentP=P,PreviousP=P;
            auto AP=Make(8,F.N,TEXT("ReconstructedCG.Applied")),Partial=Make(8,Groups,TEXT("ReconstructedCG.Partials"));
            auto Control=Make(8,5,TEXT("ReconstructedCG.Control")),Diagnostic=Make(4,4,TEXT("ReconstructedCG.Diagnostics"));
            auto AlternatePartial=FuseReductions?Make(8,Groups,TEXT("ReconstructedCG.AlternatePartials")):nullptr;
            auto AlternateControl=FuseReductions?Make(8,5,TEXT("ReconstructedCG.AlternateControl")):nullptr;
            auto DiagnosticSnapshot=FuseReductions?Make(4,4,TEXT("ReconstructedCG.DiagnosticSnapshot")):Diagnostic;
            FRDGBufferRef CurrentPartial=Partial,PreviousPartial=Partial,CurrentControl=Control,PreviousControl=Control;
            auto Archive=ResidentBurst?Make(8,F.N*ResidentSolves,TEXT("ReconstructedCG.AllResidentSolutions")):nullptr;
            auto ArchiveDiagnostic=ResidentBurst?Make(4,4*ResidentSolves,TEXT("ReconstructedCG.AllResidentDiagnostics")):nullptr;
            FRenderQueryPoolRHIRef TimingPool;FRHIPooledRenderQuery Begin,End;
            TArray<FRHIPooledRenderQuery> ResidentQueries;
            TArray<FRHIPooledRenderQuery> PhaseQueries;TArray<int32> QueryPhases;
            if(GSupportsTimestampRenderQueries)
            {
                TimingPool=RHICreateRenderQueryPool(RQT_AbsoluteTime,(PhaseTiming?652:2)+(ResidentBurst?2*ResidentSolves:0));Begin=TimingPool->AllocateQuery();End=TimingPool->AllocateQuery();
                auto* Query=Begin.GetQuery();Graph.AddPass(RDG_EVENT_NAME("ReconstructedCG.Begin"),ERDGPassFlags::None,
                    [Query](FRHICommandList& List){List.EndRenderQuery(Query);});
            }
            auto Dispatch=[&](int32 Phase,bool Initialize=false,bool Fuse=false)
            {
                auto* Q=Graph.AllocParameters<FRaftSimReconstructedCGTestCS::FParameters>();
                Q->Count=F.N;Q->PartialCount=Groups;Q->InitializeDirection=Initialize;
                Q->OmegaBits=FUintVector4(0,0,0,0);FMemory::Memcpy(&Q->OmegaBits,&F.Omega,8);
                Q->RowOffsets=Graph.CreateSRV(Rows);Q->Columns=Graph.CreateSRV(Columns);
                Q->Matrix=Graph.CreateSRV(Matrix);Q->Scaled=Graph.CreateSRV(Scaled);
                Q->InverseRoot=Graph.CreateSRV(Inverse);Q->RHS=Graph.CreateSRV(RHS);
                Q->X=Graph.CreateUAV(X);Q->Residual=Graph.CreateUAV(R);Q->Z=Graph.CreateUAV(Z);
                Q->Direction=Graph.CreateUAV(CurrentP);Q->DirectionInput=Graph.CreateSRV(PreviousP);
                Q->Applied=Graph.CreateUAV(AP);Q->Partials=Graph.CreateUAV(CurrentPartial);
                Q->PartialInput=Graph.CreateSRV(PreviousPartial);Q->ControlInput=Graph.CreateSRV(PreviousControl);
                Q->DiagnosticInput=Graph.CreateSRV(DiagnosticSnapshot);
                Q->Control=Graph.CreateUAV(CurrentControl);Q->Diagnostics=Graph.CreateUAV(Diagnostic);
                FRaftSimReconstructedCGTestCS::FPermutationDomain Perm;Perm.Set<FRaftSimReconstructedCGTestCS::FPhase>(Phase);
                Perm.Set<FRaftSimReconstructedCGTestCS::FParallelReductions>(ParallelReductions);
                Perm.Set<FRaftSimReconstructedCGTestCS::FSlotMajor>(SlotMajor);
                Perm.Set<FRaftSimReconstructedCGTestCS::FBatchedLoads>(BatchedLoads);
                Perm.Set<FRaftSimReconstructedCGTestCS::FFusedDirection>(Fuse);
                TShaderMapRef<FRaftSimReconstructedCGTestCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Perm);
                ClearUnusedGraphResources(Shader,Q);
                const bool Serial=Phase==1 || Phase==4 || Phase==7 || Phase==9;
                if(PhaseTiming)
                {
                    PhaseQueries.Add(TimingPool->AllocateQuery());PhaseQueries.Add(TimingPool->AllocateQuery());QueryPhases.Add(Phase);
                    auto* Query=PhaseQueries[PhaseQueries.Num()-2].GetQuery();
                    Graph.AddPass(RDG_EVENT_NAME("ReconstructedCG.PhaseBegin%d",Phase),ERDGPassFlags::None,
                        [Query](FRHICommandList& List){List.EndRenderQuery(Query);});
                }
                FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Reconstructed Range CG phase%d",Phase),Shader,Q,FIntVector(Serial?1:Groups,1,1));
                if(PhaseTiming)
                {
                    auto* Query=PhaseQueries.Last().GetQuery();
                    Graph.AddPass(RDG_EVENT_NAME("ReconstructedCG.PhaseEnd%d",Phase),ERDGPassFlags::None,
                        [Query](FRHICommandList& List){List.EndRenderQuery(Query);});
                }
            };
            for(uint32 Burst=0;Burst<ResidentSolves;++Burst)
            {
                CurrentP=PreviousP=P;
                CurrentPartial=PreviousPartial=Partial;CurrentControl=PreviousControl=Control;
                if(ResidentBurst)
                {
                    ResidentQueries.Add(TimingPool->AllocateQuery());ResidentQueries.Add(TimingPool->AllocateQuery());
                    auto* Query=ResidentQueries[2*Burst].GetQuery();
                    Graph.AddPass(RDG_EVENT_NAME("ReconstructedCG.ResidentBegin%u",Burst),ERDGPassFlags::None,
                        [Query](FRHICommandList& List){List.EndRenderQuery(Query);});
                }
                AddClearUAVPass(Graph,Graph.CreateUAV(Diagnostic),0u);
                Dispatch(0);Dispatch(1);Dispatch(2);Dispatch(3,true);Dispatch(4,true);
                for(int32 Iteration=0;Iteration<40;++Iteration)
                {
                    const bool Fuse=FuseDirection && Iteration>0;
                    if(Fuse){PreviousP=CurrentP;CurrentP=CurrentP==P?AlternateP:P;}
                    Dispatch(6,false,Fuse);
                    if(FuseReductions)
                    {
                        // Immutable reduction input: other groups may still
                        // read p*Ap while this group writes its residual peak.
                        PreviousPartial=CurrentPartial;CurrentPartial=CurrentPartial==Partial?AlternatePartial:Partial;
                        AddCopyBufferPass(Graph,DiagnosticSnapshot,0,Diagnostic,0,16);Dispatch(12);
                        PreviousControl=CurrentControl;CurrentControl=CurrentControl==Control?AlternateControl:Control;
                        AddCopyBufferPass(Graph,DiagnosticSnapshot,0,Diagnostic,0,16);Dispatch(13);
                        Dispatch(3);
                        PreviousControl=CurrentControl;CurrentControl=CurrentControl==Control?AlternateControl:Control;
                        AddCopyBufferPass(Graph,DiagnosticSnapshot,0,Diagnostic,0,16);Dispatch(11);
                    }
                    else {Dispatch(7);Dispatch(8);Dispatch(9);Dispatch(10);Dispatch(3);Dispatch(4);}
                    // Delay each direction update into the NEXT A*P action.
                    // Keep the final otherwise-unused update and its finite
                    // diagnostic, preserving the original complete40-CG trace.
                    if(!FuseReductions && (!FuseDirection || Iteration==39))Dispatch(5);
                }
                if(ResidentBurst)
                {
                    auto* Query=ResidentQueries[2*Burst+1].GetQuery();
                    Graph.AddPass(RDG_EVENT_NAME("ReconstructedCG.ResidentEnd%u",Burst),ERDGPassFlags::None,
                        [Query](FRHICommandList& List){List.EndRenderQuery(Query);});
                    // Preserve EVERY solve so RDG cannot discard earlier work.
                    // Copies are outside per-solve timestamps; no CPU readback
                    // or reference calculation occurs between resident solves.
                    AddCopyBufferPass(Graph,Archive,uint64(Burst)*F.N*8,X,0,uint64(F.N)*8);
                    AddCopyBufferPass(Graph,ArchiveDiagnostic,uint64(Burst)*16,Diagnostic,0,16);
                }
            }
            if(TimingPool)
            {
                auto* Query=End.GetQuery();Graph.AddPass(RDG_EVENT_NAME("ReconstructedCG.End"),ERDGPassFlags::None,
                    [Query](FRHICommandList& List){List.EndRenderQuery(Query);});
            }
            FRHIGPUBufferReadback XRead(TEXT("ReconstructedCG.XRead")),DRead(TEXT("ReconstructedCG.DRead"));
            FRHIGPUBufferReadback ArchiveRead(TEXT("ReconstructedCG.ArchiveRead")),ArchiveDRead(TEXT("ReconstructedCG.ArchiveDRead"));
            AddEnqueueCopyPass(Graph,&XRead,X,8*F.N);AddEnqueueCopyPass(Graph,&DRead,Diagnostic,16);
            if(ResidentBurst)
            {AddEnqueueCopyPass(Graph,&ArchiveRead,Archive,8*F.N*ResidentSolves);AddEnqueueCopyPass(Graph,&ArchiveDRead,ArchiveDiagnostic,16*ResidentSolves);}
            const FString SubmitUTC=FDateTime::UtcNow().ToIso8601();
            const double HostBegin=FPlatformTime::Seconds();
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            const double HostMilliseconds=(FPlatformTime::Seconds()-HostBegin)*1000.;
            const FString CompleteUTC=FDateTime::UtcNow().ToIso8601();
            double GPUSecondsMs=-1.;
            if(TimingPool)
            {
                uint64 A=0,B=0;if(RHIGetRenderQueryResult(Begin.GetQuery(),A,true) && RHIGetRenderQueryResult(End.GetQuery(),B,true) && B>=A)
                    GPUSecondsMs=(B-A)/1000.;
            }
            double LastSolveMilliseconds=GPUSecondsMs;TArray<double> ResidentMilliseconds;
            if(ResidentBurst)
            {
                for(uint32 Burst=0;Burst<ResidentSolves;++Burst)
                {
                    uint64 A=0,B=0;double Ms=-1.;
                    if(RHIGetRenderQueryResult(ResidentQueries[2*Burst].GetQuery(),A,true) &&
                        RHIGetRenderQueryResult(ResidentQueries[2*Burst+1].GetQuery(),B,true) && B>=A)Ms=(B-A)/1000.;
                    else ++Failures;
                    ResidentMilliseconds.Add(Ms);
                }
                LastSolveMilliseconds=ResidentMilliseconds.Last();
            }
            if(PhaseTiming)
            {
                double PhaseMilliseconds[14]={},PhaseMaximum[14]={};uint32 PhaseCounts[14]={};
                for(int32 I=0;I<QueryPhases.Num();++I)
                {
                    uint64 A=0,B=0;const int32 Phase=QueryPhases[I];
                    if(RHIGetRenderQueryResult(PhaseQueries[2*I].GetQuery(),A,true) &&
                        RHIGetRenderQueryResult(PhaseQueries[2*I+1].GetQuery(),B,true) && B>=A)
                    {
                        const double Ms=(B-A)/1000.;PhaseMilliseconds[Phase]+=Ms;
                        PhaseMaximum[Phase]=FMath::Max(PhaseMaximum[Phase],Ms);++PhaseCounts[Phase];
                    }
                    else ++Failures;
                }
                for(int32 Phase=0;Phase<14;++Phase)
                    Details.Add(FString::Printf(TEXT("CG phase timing case%u phase%d parallel%d: intervals%u total_ms %.6f maximum_ms %.6f; timestamp-instrumented shared-load diagnostic, not production cost"),
                        F.Tag,Phase,ParallelReductions,PhaseCounts[Phase],PhaseMilliseconds[Phase],PhaseMaximum[Phase]));
            }
            const auto* XP=static_cast<const uint8*>(XRead.Lock(8*F.N));const auto* DP=static_cast<const uint32*>(DRead.Lock(16));
            if(!XP || !DP){++Failures;if(XP)XRead.Unlock();if(DP)DRead.Unlock();continue;}
            TArray<double> GPU;GPU.SetNumUninitialized(F.N);FMemory::Memcpy(GPU.GetData(),XP,8*F.N);
            if(ResidentBurst)
            {
                const auto* AllX=static_cast<const uint8*>(ArchiveRead.Lock(8*F.N*ResidentSolves));
                const auto* AllD=static_cast<const uint8*>(ArchiveDRead.Lock(16*ResidentSolves));
                if(!AllX || !AllD)++Failures;
                for(uint32 Burst=0;Burst<ResidentSolves;++Burst)
                {
                    const bool Exact=AllX && AllD && FMemory::Memcmp(AllX+uint64(Burst)*F.N*8,XP,F.N*8)==0 &&
                        FMemory::Memcmp(AllD+Burst*16,DP,16)==0;
                    Failures+=!Exact;
                    Details.Add(FString::Printf(TEXT("CG resident timing case%u sample%d slot-major%d burst%u warmup%d milliseconds %.6f all-solution-diagnostic-bits-exact%d"),
                        F.Tag,Repeat,SlotMajor,Burst,Burst<2,ResidentMilliseconds[Burst],Exact));
                }
                if(AllX)ArchiveRead.Unlock();if(AllD)ArchiveDRead.Unlock();
                Details.Add(FString::Printf(TEXT("CG resident graph case%u sample%d solves%u total_gpu_ms %.6f includes archival copies; no CPU gaps between solves"),F.Tag,Repeat,ResidentSolves,GPUSecondsMs));
            }
            const double CPUResidual=RelativeResidual(F,CPU),GPUResidual=RelativeResidual(F,GPU);
            double Difference=0,Norm=0;const double Scale=Peak(CPU);
            for(uint32 I=0;I<F.N;++I)
            {const double A=Scale>0?GPU[I]/Scale-CPU[I]/Scale:GPU[I],B=Scale>0?CPU[I]/Scale:0.;Difference+=A*A;Norm+=B*B;}
            const double Relative=FMath::Sqrt(Difference/(Norm>0?Norm:1.));
            const uint32 ExpectedIterations=ControlCase==TEXT("zero-rhs")?0u:1u;
            const bool ControlPassed=!Synthetic || (CPUIterations==ExpectedIterations && DP[1]==ExpectedIterations &&
                DP[2]==0 && DP[3]==uint32(ControlCase==TEXT("zero-rhs")) &&
                FMemory::Memcmp(GPU.GetData(),F.RHS.GetData(),8*F.N)==0 &&
                FMemory::Memcmp(CPU.GetData(),F.RHS.GetData(),8*F.N)==0);
            const bool Passed=ControlPassed && CPUSuccess && DP[0]==0 && DP[1]<=40 && CPUResidual<2e-5 && GPUResidual<2e-5 && Relative<1e-9;
            Failures+=!Passed;if(LastRepeat)++Completed;
            const uint32 CaseHeader[6]={F.Tag,F.N,DP[0],DP[1],DP[2],DP[3]};AppendBytes(Output,CaseHeader,24);
            // Only the final six cases use the existing independent-audit format.
            if(!LastRepeat)Output.SetNum(Output.Num()-24);
            else {AppendBytes(Output,&LastSolveMilliseconds,8);AppendBytes(Output,GPU.GetData(),8*F.N);AppendBytes(Output,CPU.GetData(),8*F.N);}
            bool Exact=true;
            if(PairedComparison)
            {
                TArray<uint8> Actual;AppendBytes(Actual,GPU.GetData(),8*F.N);AppendBytes(Actual,DP,16);
                if(Repeat==0)FirstResults[F.Tag]=MoveTemp(Actual);
                else {Exact=FirstResults[F.Tag]==Actual;Failures+=!Exact;}
            }
            Details.Add(FString::Printf(TEXT("%s case%u sample%d warmup%d parallel-reductions%d slot-major%d batched-loads%d: CPU/GPU iterations%u/%u diagnostic%u, true CSR residual %.12g/%.12g, relative solution difference %.12g, GPU clear+40CG shared-load sample %.6f ms; passed%d first-result-bits-exact%d; NOT native geometry/history/production cost/scene acceptance"),
                *SourceLabel,F.Tag,Repeat,PairedComparison && Repeat<2,ParallelReductions,SlotMajor,BatchedLoads,CPUIterations,DP[1],DP[0],CPUResidual,GPUResidual,Relative,LastSolveMilliseconds,Passed,Exact));
            Details.Add(FString::Printf(TEXT("CG schedule case%u sample%d fused-direction%d fused-reductions%d compute-dispatches%u diagnostic-snapshot-copies%u; original initialization,40CG iterations and final direction diagnostic retained"),
                F.Tag,Repeat,FuseDirection,FuseReductions,FuseReductions?205u:(FuseDirection?286u:325u),FuseReductions?120u:0u));
            Details.Add(FString::Printf(TEXT("CG host timing case%u sample%d slot-major%d submit_utc %s complete_utc %s host_execute_idle_ms %.6f"),
                F.Tag,Repeat,SlotMajor,*SubmitUTC,*CompleteUTC,HostMilliseconds));
            XRead.Unlock();DRead.Unlock();
        }
        }
    });
    FlushRenderingCommands();
    TestEqual(TEXT("Completed six explicitly labeled native range-PCG cases"),Completed,6u);
    TestEqual(TEXT("Unchanged 40-iteration/residual gates and native CPU/GPU parity"),Failures,0u);
    if(Completed==6)TestTrue(TEXT("Retain native solutions; synthetic controls use separate magic and audit"),FFileHelper::SaveArrayToFile(Output,*OutputPath));
    for(const auto& Detail:Details)AddInfo(Detail);
    return !HasAnyErrors();
}
#endif
