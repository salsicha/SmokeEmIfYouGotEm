#include "Misc/AutomationTest.h"
#include "NiagaraSystem.h"
#include "NiagaraEmitter.h"
#include "NiagaraEmitterHandle.h"
#include "NiagaraNodeFunctionCall.h"
#include "NiagaraRendererProperties.h"
#include "NiagaraDataInterfaceRigidMeshCollisionQuery.h"
#include "EdGraph/EdGraphNode.h"
#include "UObject/UObjectHash.h"
#include "Materials/MaterialInterface.h"
#include "UObject/Package.h"
#include "Engine/StaticMesh.h"
#include "StaticMeshResources.h"
#include "DistanceFieldAtlas.h"
#include "NiagaraDataInterfaceArrayFloat.h"
#include "RaftSimLiquidRedistanceGPU.h"
#include "RHICommandList.h"
#include "RenderingThread.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidDistanceGPURegression,
    "RaftSim.Editor.LiquidFixtureDistanceGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidDistanceGPURegression::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Real SM5+ GPU required for distance reconstruction"));return false; }
    const FIntVector Size(16,12,16);const FVector3f Cell(10,12,15);
    constexpr int32 Count=16*12*16;
    FTextureRHIRef Source,Target;TArray<FVector4f> Input;TArray<FFloat16Color> Actual;
    FString Error;bool Success=true,AliasRejected=false;
    double MaxError=0;bool Finite=true,Signs=true,Coverage=true;int32 CoverageDiagnostics=0;
    for (int32 Case=0;Case<5;++Case)
    {
        Input.SetNumUninitialized(Count);
        for (int32 Z=0;Z<Size.Z;++Z)for (int32 Y=0;Y<Size.Y;++Y)for (int32 X=0;X<Size.X;++X)
        {
            const float Phi=Case<3?((Z+.5f)*Cell.Z-(60+17*Case))*.01f:(Case==3?-1.f:1.f);
            Input[(Z*Size.Y+Y)*Size.X+X]=FVector4f(Phi,(X+1)/17.f,float(Case+10),(Z+1)/19.f);
        }
        ENQUEUE_RENDER_COMMAND(RaftSimDistanceAnalyticTest)([&](FRHICommandListImmediate& Cmd)
        {
            if (!Source.IsValid())
            {
                Source=Cmd.CreateTexture(FRHITextureCreateDesc::Create3D(TEXT("LiquidDistanceTestInput"),Size.X,Size.Y,Size.Z,PF_A32B32G32R32F)
                    .SetFlags(TexCreate_ShaderResource).SetInitialState(ERHIAccess::CopyDest));
                Target=Cmd.CreateTexture(FRHITextureCreateDesc::Create3D(TEXT("LiquidDistanceTestOutput"),Size.X,Size.Y,Size.Z,PF_FloatRGBA)
                    .SetFlags(TexCreate_ShaderResource|TexCreate_UAV).SetInitialState(ERHIAccess::UAVCompute));
            }
            else Cmd.Transition(FRHITransitionInfo(Source,ERHIAccess::Unknown,ERHIAccess::CopyDest));
            Cmd.UpdateTexture3D(Source,0,FUpdateTextureRegion3D(0,0,0,0,0,0,Size.X,Size.Y,Size.Z),
                Size.X*sizeof(FVector4f),Size.X*Size.Y*sizeof(FVector4f),reinterpret_cast<const uint8*>(Input.GetData()));
            Cmd.Transition(FRHITransitionInfo(Source,ERHIAccess::CopyDest,ERHIAccess::SRVMask));
            AliasRejected=!RaftSimLiquidRedistanceGPU(Cmd,Target,Target,Size,Cell,50,12,Error);
            Success=RaftSimLiquidRedistanceGPU(Cmd,Source,Target,Size,Cell,50,12,Error);
            if (Success) Cmd.Read3DSurfaceFloatData(Target,FIntRect(0,0,Size.X,Size.Y),FIntPoint(0,Size.Z),Actual);
        });
        FlushRenderingCommands();
        if (!TestTrue(TEXT("GPU distance dispatched"),Success) || !TestEqual(TEXT("All voxels read back"),Actual.Num(),Count))
        { AddError(Error);return false; }
        TestTrue(TEXT("In-place input/output alias rejected"),AliasRejected);
        for (int32 I=0;I<Count;++I)
        {
            const float Expected=FMath::Clamp(Input[I].X*100,-50.f,50.f);
            const auto Value=Actual[I].GetFloats();
            Finite &= FMath::IsFinite(Value.R);Signs &= (Value.R<0)==(Expected<0);
            MaxError=FMath::Max(MaxError,double(FMath::Abs(Value.R-Expected)));
            const bool CorrectCoverage=Value.G==FFloat16(Input[I].Y).GetFloat() &&
                Value.B==FFloat16(Input[I].Z).GetFloat() && Value.A==FFloat16(Input[I].W).GetFloat();
            if (!CorrectCoverage && CoverageDiagnostics++<5)
                AddInfo(FString::Printf(TEXT("Coverage mismatch case%d voxel%d: input %.9g, expectedhalf %.9g, actual GBA %.9g %.9g %.9g"),
                    Case,I,Input[I].Y,FFloat16(Input[I].Y).GetFloat(),Value.G,Value.B,Value.A));
            Coverage &= CorrectCoverage;
        }
    }
    ENQUEUE_RENDER_COMMAND(RaftSimDistanceAnalyticRelease)([&](FRHICommandListImmediate&){Source.SafeRelease();Target.SafeRelease();});
    FlushRenderingCommands();
    TestTrue(TEXT("Moving metric plane and empty/full fields match within 0.1cm"),Finite && Signs && MaxError<=.1);
    TestTrue(TEXT("Source coverage preserved exactly through each update"),Coverage);
    AddInfo(FString::Printf(TEXT("Five changing GPU inputs, max analytic distance error %gcm; not river animation acceptance"),MaxError));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidFixtureOwnershipTest,
    "RaftSim.Editor.LiquidFixtureOwnership",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidFixtureOwnershipTest::RunTest(const FString&)
{
    auto* System=LoadObject<UNiagaraSystem>(nullptr,
        TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_LiquidBodySDFReview.NS_LiquidBodySDFReview"));
    if (!TestNotNull(TEXT("Explicit project-owned SDF review asset"),System)) return false;
    System->WaitForCompilationComplete(false,false);
    TestTrue(TEXT("Saved system compiles and is ready"),System->IsReadyToRun());
    const auto& Store=System->GetExposedParameters();
    for (const auto& Setting:TArray<TPair<FName,int32>>{
        {TEXT("User.Num Cells Max Axis"),64},{TEXT("User.Particles Per Cell"),4},
        {TEXT("User.Pressure Iterations"),40}})
        TestEqual(*Setting.Key.ToString(),Store.GetParameterValue<int32>(
            FNiagaraVariable(FNiagaraTypeDefinition::GetIntDef(),Setting.Key)),Setting.Value);
    int32 ActiveRenderers=0;
    for (const auto& Handle:System->GetEmitterHandles())
    {
        const auto* Data=Handle.GetInstance().GetEmitterData();
        if (!Data) continue;
        for (auto* Renderer:Data->GetRenderers())
        {
            if (!Renderer->GetIsEnabled()) continue;
            ++ActiveRenderers;
            TArray<UMaterialInterface*> Materials;Renderer->GetUsedMaterials(nullptr,Materials);
            TestEqual(TEXT("One SDF material on active renderer"),Materials.Num(),1);
            for (auto* Material:Materials)
            {
                if (!TestNotNull(TEXT("SDF material"),Material)) continue;
                TestTrue(TEXT("SDF renderer, not a sprite or debug bounds material"),
                    Material->GetName().Contains(TEXT("M_WaterSDF_Inst")));
                TestTrue(TEXT("Material owned by copied project package"),
                    Material->GetOutermost()==System->GetOutermost());
            }
        }
    }
    TestEqual(TEXT("Exactly one enabled renderer in the entire fixture"),ActiveRenderers,1);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidFixtureCollisionConfigurationTest,
    "RaftSim.Editor.LiquidFixtureCollisionConfiguration",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidFixtureCollisionConfigurationTest::RunTest(const FString&)
{
    auto* System=LoadObject<UNiagaraSystem>(nullptr,
        TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_LiquidBodyCollisionReview.NS_LiquidBodyCollisionReview"));
    if (!TestNotNull(TEXT("Owned collision fixture"),System)) return false;
    System->WaitForCompilationComplete(false,false);
    TestTrue(TEXT("Collision fixture ready"),System->IsReadyToRun());
    const FNiagaraVariable Variable(FNiagaraTypeDefinition(UNiagaraDataInterfaceRigidMeshCollisionQuery::StaticClass()),TEXT("User.Collide_Meshes"));
    const auto* Collision=Cast<UNiagaraDataInterfaceRigidMeshCollisionQuery>(System->GetExposedParameters().GetDataInterface(Variable));
    if (!TestNotNull(TEXT("Rigid-mesh collision interface"),Collision)) return false;
    TestTrue(TEXT("Interface owned by project copy"),Collision->GetOutermost()==System->GetOutermost());
    TestEqual(TEXT("Bounded primitive capacity"),Collision->MaxNumPrimitives,16);
    TestEqual(TEXT("Exactly one explicit actor tag"),Collision->ActorTags.Num(),1);
    TestTrue(TEXT("Only fixture obstacle tag"),Collision->ActorTags.Contains(TEXT("RaftSimLiquidFixtureObstacle")));
    TestFalse(TEXT("Static obstacles can be searched"),Collision->OnlyUseMoveable);
    TestFalse(TEXT("Primitive test does not use complex collision"),Collision->UseComplexCollisions);
    int32 MeshOn=0,DistanceFieldOff=0,Renderers=0;
    ForEachObjectWithOuter(System,[&](UObject* Object)
    {
        if (auto* Node=Cast<UEdGraphNode>(Object))
            for (const auto* Pin:Node->Pins)
            {
                if (Pin->Direction!=EGPD_Input || !Pin->LinkedTo.IsEmpty()) continue;
                MeshOn+=Pin->PinName==TEXT("Grid3D_ComputeBoundary.Use Mesh Collisions") && Pin->DefaultValue==TEXT("true");
                DistanceFieldOff+=Pin->PinName==TEXT("Grid3D_ComputeBoundary.Use Mesh Distance Fields") && Pin->DefaultValue==TEXT("false");
            }
    },EGetObjectsFlags::IncludeNestedObjects);
    TestTrue(TEXT("Copied graph versions explicitly enable primitive collision"),MeshOn>=1);
    TestEqual(TEXT("Each enabled primitive path explicitly excludes mesh distance fields"),DistanceFieldOff,MeshOn);
    for (const auto& Handle:System->GetEmitterHandles())
        if (const auto* Data=Handle.GetInstance().GetEmitterData())
            for (auto* Renderer:Data->GetRenderers()) Renderers+=Renderer->GetIsEnabled();
    TestEqual(TEXT("No extra surface renderer in collision fixture"),Renderers,1);
    // Configuration is not proof of particle/obstacle separation. That is
    // measured separately through actual GPU sim-cache readback and a control.
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidChannelConfigurationTest,
    "RaftSim.Editor.LiquidFixtureChannelConfiguration",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidChannelConfigurationTest::RunTest(const FString&)
{
    auto* System=LoadObject<UNiagaraSystem>(nullptr,
        TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_LiquidChannelOwnedReview.NS_LiquidChannelOwnedReview"));
    if (!TestNotNull(TEXT("Owned flow-through fixture"),System)) return false;
    System->WaitForCompilationComplete(false,false);
    TestTrue(TEXT("Channel fixture compiles"),System->IsReadyToRun());
    for (const auto& Handle:System->GetEmitterHandles())
        if (const auto* Data=Handle.GetInstance().GetEmitterData())
            TestNull(TEXT("Owned channel cannot merge its boundary overrides from engine parent"),Data->GetParent().Emitter);
    const auto& Store=System->GetExposedParameters();
    TestEqual(TEXT("Runtime source velocity in cm/s"),Store.GetParameterValue<FVector3f>(
        FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.Inlet Velocity"))),FVector3f(250,0,0));
    TestEqual(TEXT("Source is in the upstream liquid, not overhead"),Store.GetParameterValue<FVector3f>(
        FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.Inlet Position"))),FVector3f(-135,0,60));
    TestEqual(TEXT("Explicit controllable source rate"),Store.GetParameterValue<float>(
        FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("User.Inlet Particle Rate"))),20000.f);
    int32 InletLinks=0,OutletLinks=0,OpenOutlet=0,ClosedInlet=0;
    TSet<FName> OutletInputs;
    ForEachObjectWithOuter(System,[&](UObject* Object)
    {
        if (auto* Node=Cast<UEdGraphNode>(Object))
            for (const auto* Pin:Node->Pins)
            {
                if (Pin->Direction!=EGPD_Input) continue;
                for (const auto* Link:Pin->LinkedTo)
                {
                    InletLinks+=Link->PinName.ToString().StartsWith(TEXT("User.Inlet "));
                    OutletLinks+=Link->PinName==TEXT("User.Open Outlet");
                    if (Link->PinName==TEXT("User.Open Outlet")) OutletInputs.Add(Pin->PinName);
                }
                if (!Pin->LinkedTo.IsEmpty()) continue;
                OpenOutlet+=Pin->PinName==TEXT("Grid3D_FLIP_FLUID_CONTROLS.Open Boundary Right") && Pin->DefaultValue==TEXT("true");
                ClosedInlet+=Pin->PinName==TEXT("Grid3D_FLIP_FLUID_CONTROLS.Open Boundary Left") && Pin->DefaultValue==TEXT("false");
            }
    },EGetObjectsFlags::IncludeNestedObjects);
    TestEqual(TEXT("Four dynamic inlet bindings"),InletLinks,4);
    // A saved standalone emitter has no duplicate parent graph. Require both
    // actual paths, not four references counted before the parent is detached.
    TestEqual(TEXT("Exactly two saved outlet bindings"),OutletLinks,2);
    TestTrue(TEXT("Regular boundary is connected to the runtime outlet"),
        OutletInputs.Contains(TEXT("Grid3D_ComputeBoundary.Open Boundary +X")));
    TestTrue(TEXT("High-precision boundary is connected to the runtime outlet"),
        OutletInputs.Contains(TEXT("Grid3D_ComputeHighPrecisionBoundary.Open Boundary +X")));
    TestTrue(TEXT("Explicit open outlet in copied graphs"),OpenOutlet>=1);
    TestEqual(TEXT("Each copied control graph closes the wall behind the inlet"),ClosedInlet,OpenOutlet);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidBoundedChannelConfigurationTest,
    "RaftSim.Editor.LiquidFixtureBoundedChannelConfiguration",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidBoundedChannelConfigurationTest::RunTest(const FString&)
{
    auto* System=LoadObject<UNiagaraSystem>(nullptr,
        TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_LiquidChannelBoundedReview.NS_LiquidChannelBoundedReview"));
    if (!TestNotNull(TEXT("Bounded channel asset"),System)) return false;
    System->WaitForCompilationComplete(false,false);
    TestTrue(TEXT("Bounded channel ready after reload"),System->IsReadyToRun());
    int32 RetirementModules=0;
    FString RetirementAlias;
    TMap<FName,FString> Defaults;
    ForEachObjectWithOuter(System,[&](UObject* Object)
    {
        if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Object))
            if (Call->FunctionScript && Call->FunctionScript->GetPathName()==
                TEXT("/Niagara/Modules/Update/Lifetime/KillParticlesInVolume.KillParticlesInVolume"))
            {
                ++RetirementModules;
                // Suggested stack display names are not stable function aliases.
                RetirementAlias=Call->GetFunctionName()+TEXT(".");
                const auto* Shape=Call->FindPin(TEXT("Kill Shape"),EGPD_Input);
                if (TestNotNull(TEXT("Explicit shape choice"),Shape))
                {
                    auto* Enum=LoadObject<UEnum>(nullptr,
                        TEXT("/Niagara/Enums/ENiagaraKillVolumeOptions.ENiagaraKillVolumeOptions"));
                    if (TestNotNull(TEXT("Shape enum"),Enum))
                    {
                        const int32 Index=Enum->GetIndexByNameString(Shape->DefaultValue);
                        TestTrue(TEXT("Retirement shape is Box"),Index!=INDEX_NONE &&
                            Enum->GetDisplayNameTextByIndex(Index).ToString()==TEXT("Box"));
                    }
                }
            }
    },EGetObjectsFlags::IncludeNestedObjects);
    TestEqual(TEXT("Exactly one retirement module"),RetirementModules,1);
    if (RetirementModules!=1) return false;
    ForEachObjectWithOuter(System,[&](UObject* Object)
    {
        if (auto* Node=Cast<UEdGraphNode>(Object))
            for (const auto* Pin:Node->Pins)
                if (Pin->Direction==EGPD_Input && Pin->LinkedTo.IsEmpty() &&
                    Pin->PinName.ToString().StartsWith(RetirementAlias))
                    Defaults.Add(FName(*Pin->PinName.ToString().RightChop(RetirementAlias.Len())),Pin->DefaultValue);
    },EGetObjectsFlags::IncludeNestedObjects);
    TestEqual(TEXT("Retire outside, never inside the domain"),Defaults.FindRef(TEXT("Invert Volume")),FString(TEXT("true")));
    TestEqual(TEXT("Retirement is enabled"),Defaults.FindRef(TEXT("Kill Volume Enabled")),FString(TEXT("true")));
    TestEqual(TEXT("Origin matches floor-zero fixture"),Defaults.FindRef(TEXT("Origin Offset")),FString(TEXT("0.000,0.000,250.000")));
    TestEqual(TEXT("Retirement volume matches the grid dimensions"),Defaults.FindRef(TEXT("Box Size")),FString(TEXT("400.000,400.000,500.000")));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidTerrainDistanceFieldTest,
    "RaftSim.Editor.LiquidFixtureTerrainDistanceField",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidTerrainDistanceFieldTest::RunTest(const FString&)
{
    auto* Mesh=LoadObject<UStaticMesh>(nullptr,
        TEXT("/Game/RaftSim/Environment/SouthForkLiquidWindow20260908/SM_SouthForkLiquidCollisionSolid.SM_SouthForkLiquidCollisionSolid"));
    if (!TestNotNull(TEXT("Exact clipped South Fork collision solid"),Mesh)) return false;
    const auto* RenderData=Mesh->GetRenderData();
    if (!TestNotNull(TEXT("Built terrain render data"),RenderData)) return false;
    if (!TestTrue(TEXT("Terrain has LOD0"),RenderData->LODResources.Num()>0)) return false;
    const auto* Distance=RenderData->LODResources[0].DistanceFieldData;
    if (!TestNotNull(TEXT("Actual generated mesh SDF, not just an enabled setting"),Distance)) return false;
    TestTrue(TEXT("Generated signed distance volume is valid"),Distance->IsValid());
    TestFalse(TEXT("Closed terrain solid is not treated as a two-sided sheet"),Distance->bMostlyTwoSided);
    TestTrue(TEXT("Resident distance field mip is nonempty"),Distance->AlwaysLoadedMip.Num()>0);
    const auto Dimensions=Distance->Mips[0].IndirectionDimensions;
    TestTrue(TEXT("Every SDF axis is present"),Dimensions.GetMin()>0);
    AddInfo(FString::Printf(TEXT("Terrain SDF indirection=%s bricks=%u resident_bytes=%d"),
        *Dimensions.ToString(),Distance->Mips[0].NumDistanceFieldBricks,Distance->AlwaysLoadedMip.Num()));
    // The separate import report checks every top triangle against engine
    // collision. This test establishes SDF availability, not GPU separation.
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidTerrainSourceTest,
    "RaftSim.Editor.LiquidFixtureTerrainSources",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidTerrainSourceTest::RunTest(const FString&)
{
    auto* System=LoadObject<UNiagaraSystem>(nullptr,
        TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_SouthForkLiquidTerrainReview.NS_SouthForkLiquidTerrainReview"));
    if (!TestNotNull(TEXT("Saved captured-terrain water system"),System)) return false;
    System->WaitForCompilationComplete(false,false);
    TestTrue(TEXT("Terrain system ready after reload"),System->IsReadyToRun());
    const auto& Store=System->GetExposedParameters();
    const auto Array=[&](FName Name)
    { return Cast<UNiagaraDataInterfaceArrayFloat3>(Store.GetDataInterface(
        FNiagaraVariable(FNiagaraTypeDefinition(UNiagaraDataInterfaceArrayFloat3::StaticClass()),Name))); };
    auto* Positions=Array(TEXT("User.River Source Positions"));
    auto* Velocities=Array(TEXT("User.River Source Velocities"));
    if (!TestNotNull(TEXT("Persistent source positions"),Positions) ||
        !TestNotNull(TEXT("Persistent source velocities"),Velocities)) return false;
    TestEqual(TEXT("Exact source quadrature count"),Positions->InternalFloatData.Num(),4496);
    TestEqual(TEXT("Matched vector table lengths"),Velocities->InternalFloatData.Num(),Positions->InternalFloatData.Num());
    TestTrue(TEXT("Positions owned by this system"),Positions->GetOutermost()==System->GetOutermost());
    TestTrue(TEXT("Velocities owned by this system"),Velocities->GetOutermost()==System->GetOutermost());
    for (const auto& Value:Positions->InternalFloatData) if (Value.ContainsNaN())
    { AddError(TEXT("Nonfinite persisted source position"));break; }
    for (const auto& Value:Velocities->InternalFloatData) if (Value.ContainsNaN())
    { AddError(TEXT("Nonfinite persisted source velocity"));break; }
    int32 Renderers=0,WeightedSelectors=0,VectorSelectors=0,IndexLinks=0,MeshFields=0;
    for (const auto& Handle:System->GetEmitterHandles())
        if (const auto* Data=Handle.GetInstance().GetEmitterData())
            for (auto* Renderer:Data->GetRenderers()) Renderers+=Renderer->GetIsEnabled();
    ForEachObjectWithOuter(System,[&](UObject* Object)
    {
        if (const auto* Call=Cast<UNiagaraNodeFunctionCall>(Object))
            if (Call->FunctionScript)
            {
                WeightedSelectors+=Call->FunctionScript->GetName()==TEXT("SelectIntFromWeightedDistributionArray");
                VectorSelectors+=Call->FunctionScript->GetName()==TEXT("SelectVectorFromArray");
            }
        if (const auto* Node=Cast<UEdGraphNode>(Object))
            for (const auto* Pin:Node->Pins)
                if (Pin->Direction==EGPD_Input)
                {
                    MeshFields+=Pin->PinName==TEXT("Grid3D_ComputeBoundary.Use Mesh Distance Fields") &&
                        Pin->LinkedTo.IsEmpty() && Pin->DefaultValue==TEXT("true");
                    if (Pin->PinName.ToString().EndsWith(TEXT(".Direct Array Index")))
                        for (const auto* Link:Pin->LinkedTo)
                            IndexLinks+=Link->PinName==TEXT("Particles.RiverSourceIndex");
                }
    },EGetObjectsFlags::IncludeNestedObjects);
    TestEqual(TEXT("One visible liquid renderer"),Renderers,1);
    TestEqual(TEXT("Choose the weighted source only once per particle"),WeightedSelectors,1);
    TestEqual(TEXT("Two table selectors"),VectorSelectors,2);
    TestEqual(TEXT("Both selectors share the particle source index"),IndexLinks,2);
    TestEqual(TEXT("One enabled exact terrain distance field path"),MeshFields,1);
    return true;
}
