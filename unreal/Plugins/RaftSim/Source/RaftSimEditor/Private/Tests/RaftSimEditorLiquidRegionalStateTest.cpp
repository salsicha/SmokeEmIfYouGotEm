#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "../Materials/RaftSimLiquidRegionalState.h"
#include "../Materials/RaftSimLiquidRegionalBoundary.h"
#include "../Materials/RaftSimLiquidContactProfile.h"
#include "../Materials/RaftSimLiquidRegionalContact.h"
#include "../Materials/RaftSimLiquidRegionalProjection.h"
#include "../Materials/RaftSimLiquidParentExterior.h"
#include "../Materials/RaftSimRegisteredTerrainQuery.h"
#include "NiagaraSystem.h"
#include "NiagaraEmitter.h"
#include "NiagaraEmitterHandle.h"
#include "NiagaraScript.h"
#include "NiagaraComponent.h"
#include "NiagaraDataInterfaceArrayFloat.h"
#include "NiagaraDataInterfaceArrayInt.h"
#include "NiagaraDataInterfaceGrid3DCollection.h"
#include "UObject/StrongObjectPtr.h"
#include "UObject/UnrealType.h"
#include "UObject/UObjectHash.h"
#include "NiagaraNodeCustomHlsl.h"
#include "Internationalization/Regex.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"

namespace
{
TSharedPtr<FJsonObject> ReadRegionalJson(const FString& Path)
{
    FString Text;TSharedPtr<FJsonObject> J;
    if (FFileHelper::LoadFileToString(Text,*Path)) FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),J);
    return J;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidRegionalGeometryTest,"RaftSim.Editor.LiquidRegionalGeometry",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidRegionalGeometryTest::RunTest(const FString&)
{
    using namespace RaftSimLiquidRegionalState;
    using namespace RaftSimLiquidRegionalBoundary;
    const FString Base=FPaths::ProjectDir()/TEXT("../tmp");
    const FString Directory=Base/TEXT("south-fork-liquid-regional-state-20260910");
    const FString Geometry=Base/TEXT("south-fork-liquid-regional-geometry-v4-20260910");
    const auto Manifest=ReadRegionalJson(Directory/TEXT("manifest.json"));
    const auto Boundary=ReadRegionalJson(Base/TEXT("south-fork-whole-rapid-liquid-float-seeds-20260910/grid_vector_boundary_profile.json"));
    FParent Parent;FString Error;
    if (!TestTrue(TEXT("Parent decoded"),DecodeParent(Manifest,Boundary,Parent,Error))) { AddError(Error);return false; }
    TArray<FState> States;
    for (const auto& Record:Manifest->GetArrayField(TEXT("region_files")))
    {
        FState State;
        if (!Decode(ReadRegionalJson(Directory/Record->AsObject()->GetStringField(TEXT("file"))),Parent,State,Error))
        { AddError(Error);return false; }
        States.Add(MoveTemp(State));
    }
    TArray<FRegion> Built;
    if (!TestTrue(TEXT("Complete shared/external cell mapping built"),Build(Parent,States,Boundary,Built,Error)))
    { AddError(Error);return false; }
    int32 Shared=0,External=0,ExteriorRows=0;
    for (const auto& R:Built)
    {
        const auto Json=ReadRegionalJson(Geometry/FString::Printf(TEXT("region-%03d-boundary.json"),R.Id));
        if (!TestTrue(TEXT("Prepared regional boundary present"),Json.IsValid())) return false;
        const auto& Faces=Json->GetArrayField(TEXT("faces"));
        for (int32 F=0;F<4;++F)
        {
            const auto Face=Faces[F]->AsObject();const auto& Actual=R.Faces[F];
            TestEqual(TEXT("External/shared classification agrees"),Actual.IsExternal(),Face->GetStringField(TEXT("kind"))==TEXT("external"));
            if (Actual.IsExternal())
            {
                const auto& Scalar=Face->GetArrayField(TEXT("bed_stage_inward_speed_cm"));
                const auto& Vector=Face->GetArrayField(TEXT("velocity_station_lateral_up_cm_per_s"));
                if (!TestEqual(TEXT("Exact exterior row count"),Actual.Velocity.Num(),Vector.Num())) return false;
                for (int32 I=0;I<Vector.Num();++I) for (int32 A=0;A<3;++A)
                {
                    if (Actual.Velocity[I][A]!=float(Vector[I]->AsArray()[A]->AsNumber()) ||
                        Actual.BedStageNormalSpeed[I][A]!=float(Scalar[I]->AsArray()[A]->AsNumber()))
                    { AddError(TEXT("Exterior row value changed"));return false; }
                }
                ExteriorRows+=Vector.Num();
            }
            else
            {
                TestEqual(TEXT("Shared neighbor agrees"),Actual.Neighbor,int32(Face->GetNumberField(TEXT("neighbor_region"))));
                TestTrue(TEXT("Internal face has no reservoir values"),Actual.Velocity.IsEmpty() && Actual.BedStageNormalSpeed.IsEmpty());
            }
        }
        const auto& ExpectedShared=Json->GetArrayField(TEXT("shared_halo_columns"));
        const auto& ExpectedExternal=Json->GetArrayField(TEXT("external_halo_columns"));
        if (!TestEqual(TEXT("All shared columns including corners"),R.Shared.Num(),ExpectedShared.Num()) ||
            !TestEqual(TEXT("All exterior columns including corners"),R.External.Num(),ExpectedExternal.Num())) return false;
        for (int32 I=0;I<R.Shared.Num();++I)
        {
            const auto& S=R.Shared[I];const auto& E=ExpectedShared[I]->AsArray();
            const int32 V[5]={S.Destination.X,S.Destination.Y,S.SourceRegion,S.Source.X,S.Source.Y};
            for (int32 A=0;A<5;++A) if (V[A]!=E[A]->AsNumber()) { AddError(TEXT("Shared address mismatch"));return false; }
        }
        for (int32 I=0;I<R.External.Num();++I)
        {
            const auto& S=R.External[I];const auto& E=ExpectedExternal[I]->AsArray();
            const int32 V[4]={S.Destination.X,S.Destination.Y,S.Parent.X,S.Parent.Y};
            for (int32 A=0;A<4;++A) if (V[A]!=E[A]->AsNumber()) { AddError(TEXT("Exterior address mismatch"));return false; }
        }
        Shared+=R.Shared.Num();External+=R.External.Num();
        const auto Contact=ReadRegionalJson(Geometry/FString::Printf(TEXT("region-%03d-contact.json"),R.Id));
        TArray<FVector3f> Packed;
        if (!TestTrue(TEXT("Actual anchored terrain page decodes below cap"),RaftSimLiquidContactProfile::Decode(Contact,Packed))) return false;
        TestTrue(TEXT("Actual terrain retains anchored relative ABI"),Packed[1].Y<0 && Packed[1].Z<0);
        TestEqual(TEXT("All pages retain original world anchor"),Packed[0],FVector3f(-13988.36328125,8830.2412109375,50));
        TestEqual(TEXT("Niagara reflection round trip"),NiagaraCell(NiagaraCell(FIntPoint(3,5),68),68),FIntPoint(3,5));
    }
    TestTrue(TEXT("Both types of halo present"),Shared>0 && External>0);
    TestEqual(TEXT("All exterior scalar/vector rows exactly once"),ExteriorRows,2*(Parent.Cells.X+Parent.Cells.Y));
    const FState Last=MoveTemp(States.Last());States.Pop();
    TestFalse(TEXT("Missing neighbor cannot turn into artificial tank boundary"),Build(Parent,States,Boundary,Built,Error));
    TestTrue(TEXT("Failure clears stale addresses"),Built.IsEmpty());States.Add(Last);
    Boundary->SetNumberField(TEXT("vector_rows_offset"),0);
    TestFalse(TEXT("Wrong parent row layout rejected"),Build(Parent,States,Boundary,Built,Error));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidRegionalContactTest,"RaftSim.Editor.LiquidRegionalContact",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidRegionalContactTest::RunTest(const FString&)
{
    using namespace RaftSimLiquidRegionalState;
    const FString Base=FPaths::ProjectDir()/TEXT("../tmp");
    const FString States=Base/TEXT("south-fork-liquid-regional-state-20260910");
    const FString Geometry=Base/TEXT("south-fork-liquid-regional-geometry-v4-20260910");
    FParent Parent;FString Error;
    if (!DecodeParent(ReadRegionalJson(States/TEXT("manifest.json")),
        ReadRegionalJson(Base/TEXT("south-fork-whole-rapid-liquid-float-seeds-20260910/grid_boundary_profile.json")),Parent,Error))
    { AddError(Error);return false; }
    auto* Source=LoadObject<UNiagaraSystem>(nullptr,TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_SouthForkLiquidTerrainReview.NS_SouthForkLiquidTerrainReview"));
    if (!TestNotNull(TEXT("Saved source available"),Source)) return false;
    const FString ExplicitQuery=RaftSimRegisteredTerrainQueryHlsl(TEXT("P"),true);
    {
        TGuardValue<FVector> OtherWindow(RaftSimLiquidWindowProfile::GeographicTranslation,FVector(100000,-200000,0));
        TestEqual(TEXT("Regional queries independent of legacy translation"),RaftSimRegisteredTerrainQueryHlsl(TEXT("P"),true),ExplicitQuery);
    }
    TestTrue(TEXT("Both position and normal reflect to the explicit world frame"),ExplicitQuery.Contains(TEXT("float3((P).x,-(P).y,(P).z)")) &&
        ExplicitQuery.Contains(TEXT("closest.y=-closest.y; normal.y=-normal.y;")));
    for (const int32 Id:{0,5,11})
    {
        FState R;const auto Contact=ReadRegionalJson(Geometry/FString::Printf(TEXT("region-%03d-contact.json"),Id));
        if (!Decode(ReadRegionalJson(States/FString::Printf(TEXT("region-%03d.json"),Id)),Parent,R,Error)) { AddError(Error);return false; }
        TStrongObjectPtr<UNiagaraSystem> Candidate(DuplicateObject<UNiagaraSystem>(Source,GetTransientPackage()));
        if (!InstallArrays(Candidate.Get(),R,Error)) { AddError(Error);return false; }
        TestFalse(TEXT("Projection cannot precede canonical contact"),RaftSimInstallRegionalLiquidProjection(Candidate.Get(),Parent,R,Error));
        const auto Wrong=ReadRegionalJson(Geometry/FString::Printf(TEXT("region-%03d-contact.json"),(Id+1)%12));
        TestFalse(TEXT("Reject another region's contact page before graph changes"),RaftSimInstallRegionalLiquidContact(Candidate.Get(),R,Wrong,Error));
        TestFalse(TEXT("Never mutate saved source"),RaftSimInstallRegionalLiquidContact(Source,R,Contact,Error));
        if (!RaftSimInstallRegionalLiquidContact(Candidate.Get(),R,Contact,Error)) { AddError(Error);return false; }
        Candidate->RequestCompile(true);Candidate->WaitForCompilationComplete(false,false);Candidate->WaitForCompilationComplete(true,false);
        TestTrue(TEXT("Regional particle/contact/pressure program ready"),Candidate->IsReadyToRun());
        int32 GPUPrograms=0;
        for (const auto& H:Candidate->GetEmitterHandles()) if (H.GetIsEnabled()) if (const auto* E=H.GetInstance().GetEmitterData())
        {
            TArray<UNiagaraScript*> Scripts;E->GetScripts(Scripts,false);
            for (const auto* S:Scripts) if (S->GetUsage()==ENiagaraScriptUsage::ParticleGPUComputeScript)
            {
                ++GPUPrograms;TestTrue(TEXT("Actual regional contact GPU shader compiled"),S->DidScriptCompilationSucceed(true));
                const auto& Code=S->GetVMExecutableData().LastHlslTranslationGPU;
                TestTrue(TEXT("Canonical contact array reaches GPU"),Code.Contains(TEXT("Get_User_RiverContactTriangles")));
                TestTrue(TEXT("Anchored page addressing reaches GPU"),Code.Contains(TEXT("pageOffset")));
                TestTrue(TEXT("Both exact-contact consumers reach GPU"),Code.Contains(TEXT("RegisteredTriangleBoundary")) && Code.Contains(TEXT("ProjectTaggedTerrainContact")));
                TestTrue(TEXT("Centered metric transfer reaches GPU"),Code.Contains(TEXT("CenteredMetricParticleTransfer")));
                TestTrue(TEXT("Immutable integer birth identity reaches native particle storage"),
                    Code.Contains(TEXT("MapSpawn.Particles.RiverBirthOwner =")) &&
                    Code.Contains(TEXT("MapSpawn.Particles.RiverBirthSequence =")) &&
                    Code.Contains(TEXT("MapUpdate.Particles.RiverBirthSequence = InputDataInt(")));
                // Niagara derives the symbol from the source script, not its
                // display label. Find that symbol without assuming a suffix.
                FRegexMatcher SpawnWriter(FRegexPattern(TEXT("Context\\.(MapSimStage[0-9]+_RegionalNeighborInsertion)\\.(AddParticleToNeighborQuery[0-9]*)\\.WorldToUnit = Context\\.[^.]+\\.Emitter\\.WorldToUnit;")),Code);
                const bool HasSpawnWriter=SpawnWriter.FindNext();
                const FString SpawnMap=HasSpawnWriter?SpawnWriter.GetCaptureGroup(1):FString();
                const FString SpawnSymbol=HasSpawnWriter?SpawnWriter.GetCaptureGroup(2):FString();
                // Parameter assignments compile through a GUID-named SetVariables
                // module. Verify both links and its actual invocation, not just
                // a particle attribute name or an assumed direct assignment.
                FRegexMatcher RememberWriter(FRegexPattern(TEXT("Context\\.(MapSimStage[0-9]+_RegionalNeighborInsertion)\\.(SetVariables_[A-Fa-f0-9]+)\\.Particles\\.RiverStepStartPosition = Context\\.[^.]+\\.Particles\\.Position;")),Code);
                const bool HasRememberWriter=RememberWriter.FindNext();
                const FString RememberMap=HasRememberWriter?RememberWriter.GetCaptureGroup(1):FString();
                const FString RememberSymbol=HasRememberWriter?RememberWriter.GetCaptureGroup(2):FString();
                TestTrue(TEXT("Actual pre-advection position retained in native particle stage"),HasSpawnWriter && HasRememberWriter &&
                    RememberMap==SpawnMap &&
                    Code.Contains(RememberMap+TEXT(".Particles.RiverStepStartPosition = Context.")+RememberMap+TEXT(".")+RememberSymbol+TEXT(".Particles.RiverStepStartPosition;")) &&
                    Code.Contains(RememberSymbol+TEXT("_Emitter_Func(Context);")) &&
                    Code.Contains(TEXT("MapUpdate.Particles.RiverStepStartPosition.x = InputDataFloat(")));
                TestTrue(TEXT("New particles enter native neighbors in their spawn step"),HasSpawnWriter &&
                    Code.Contains(TEXT("AddParticle_Emitter_NQ_UEImpureCall(Context.")+SpawnMap+TEXT(".")+SpawnSymbol+TEXT(".Enabled,")) &&
                    Code.Contains(SpawnSymbol+TEXT("_Emitter_Func(Context);")));
                TestFalse(TEXT("Spawn/update-relative indices cannot write overlapping NQ slots"),
                    Code.Contains(TEXT("AddParticle_Emitter_NQ_UEImpureCall(Context.MapSpawn.")) ||
                    Code.Contains(TEXT("AddParticle_Emitter_NQ_UEImpureCall(Context.MapUpdate.")));
                TestFalse(TEXT("No inherited fixture box may delete regional particles"),
                    Code.Contains(TEXT("KillParticlesInVolume_Emitter_Func(Context);")));
                TestFalse(TEXT("No Landscape height can override the captured terrain"),Code.Contains(TEXT("GetHeight_User_LandscapeCollisions")));
            }
        }
        TestEqual(TEXT("One primary GPU program"),GPUPrograms,1);
        TArray<FVector3f> Packed;RaftSimLiquidContactProfile::Decode(Contact,Packed);
        const FNiagaraVariable V(FNiagaraTypeDefinition(UNiagaraDataInterfaceArrayFloat3::StaticClass()),TEXT("User.River Contact Triangles"));
        auto* A=Cast<UNiagaraDataInterfaceArrayFloat3>(Candidate->GetExposedParameters().GetDataInterface(V));
        TestTrue(TEXT("Exact prepared page bytes bound, not reconstructed float32 vertices"),A && A->InternalFloatData==Packed);
        TestFalse(TEXT("Projection never mutates saved source"),RaftSimInstallRegionalLiquidProjection(Source,Parent,R,Error));
        auto WrongRegion=R;WrongRegion.Frame.Origin.X+=100;
        TestFalse(TEXT("Projection rejects mismatched regional origin"),RaftSimInstallRegionalLiquidProjection(Candidate.Get(),Parent,WrongRegion,Error));
        auto WrongMetricParent=Parent;WrongMetricParent.Spacing.X*=2;
        auto WrongMetricRegion=R;WrongMetricRegion.Extent.X*=2;
        TestFalse(TEXT("Projection cannot use a different metric than the allocated grid"),
            RaftSimInstallRegionalLiquidProjection(Candidate.Get(),WrongMetricParent,WrongMetricRegion,Error));
        if (!RaftSimInstallRegionalLiquidProjection(Candidate.Get(),Parent,R,Error)) { AddError(Error);return false; }
        Candidate->RequestCompile(true);Candidate->WaitForCompilationComplete(false,false);Candidate->WaitForCompilationComplete(true,false);
        TestTrue(TEXT("Regional compatible projection GPU program ready"),Candidate->IsReadyToRun());
        for (const auto& H:Candidate->GetEmitterHandles()) if (H.GetIsEnabled()) if (const auto* E=H.GetInstance().GetEmitterData())
        {
            TArray<UNiagaraScript*> Scripts;E->GetScripts(Scripts,false);
            for (const auto* S:Scripts) if (S->GetUsage()==ENiagaraScriptUsage::ParticleGPUComputeScript)
            {
                TestTrue(TEXT("Actual regional projection shader compiled"),S->DidScriptCompilationSucceed(true));
                const auto& Code=S->GetVMExecutableData().LastHlslTranslationGPU;
                TestTrue(TEXT("Pressure, divergence and gradient reach GPU"),Code.Contains(TEXT("CompatibleMaskedPressure")) &&
                    Code.Contains(TEXT("CompatibleMaskedDivergence")) && Code.Contains(TEXT("CompatibleAnisotropicGradient")));
                TestTrue(TEXT("Shared imported pressures survive local solve"),Code.Contains(TEXT("RegionalPressureOwner")) && Code.Contains(TEXT("if(regionalShared) continue;")));
                TestTrue(TEXT("Explicit regional XYZ metric reaches GPU"),Code.Contains(TEXT("RegionalProjectionMetricCM")));
                TestFalse(TEXT("No hidden fixed-fixture pressure metric"),Code.Contains(TEXT("float3 h=float3(dx,dx,800.0/24.0)")));
            }
        }
        TStrongObjectPtr<UNiagaraComponent> Component(NewObject<UNiagaraComponent>());Component->SetAsset(Candidate.Get());
        TestFalse(TEXT("Never replace contact on an assigned/live system"),RaftSimInstallRegionalLiquidContact(Candidate.Get(),R,Contact,Error));
        TestFalse(TEXT("Never replace projection on assigned/live system"),RaftSimInstallRegionalLiquidProjection(Candidate.Get(),Parent,R,Error));
        Component->SetAsset(nullptr);
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidRegionalStateTest,"RaftSim.Editor.LiquidRegionalState",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidRegionalStateTest::RunTest(const FString&)
{
    using namespace RaftSimLiquidRegionalState;
    const FString Directory=FPaths::ProjectDir()/TEXT("../tmp/south-fork-liquid-regional-state-20260910");
    const FString ParentDirectory=FPaths::ProjectDir()/TEXT("../tmp/south-fork-whole-rapid-liquid-float-seeds-20260910");
    const auto Manifest=ReadRegionalJson(Directory/TEXT("manifest.json"));
    const auto Boundary=ReadRegionalJson(ParentDirectory/TEXT("grid_boundary_profile.json"));
    FParent Parent;FString Error;
    if (!TestTrue(TEXT("Actual full-domain frame decoded without allocating whole grid"),DecodeParent(Manifest,Boundary,Parent,Error)))
    { AddError(Error);return false; }
    TestEqual(TEXT("Original full X retained"),Parent.Cells.X,490);
    TestEqual(TEXT("All initial identities declared"),Parent.Seeds,719335);
    TArray<FState> Regions;int32 EmptyInlets=0,TailRegions=0;
    for (const auto& Record:Manifest->GetArrayField(TEXT("region_files")))
    {
        const FString File=Record->AsObject()->GetStringField(TEXT("file"));
        if (!TestEqual(TEXT("Region path stays in declared directory"),FPaths::GetCleanFilename(File),File)) return false;
        FState State;const auto Json=ReadRegionalJson(Directory/File);
        if (!TestTrue(TEXT("Actual region decodes completely"),Decode(Json,Parent,State,Error)))
        { AddError(File+TEXT(": ")+Error);return false; }
        TailRegions+=State.ComputationalCells.X%4==2;
        EmptyInlets+=State.SourceIds.IsEmpty();
        TestTrue(TEXT("World actor frame remains proper after ENU reflection"),
            FVector::CrossProduct(State.Frame.WorldAxisX(),State.Frame.WorldAxisY()).Equals(FVector::UpVector,1e-9));
        for (int32 I=0;I<State.SourcePositions.Num();++I)
            if (!(State.Frame.WorldSourceOffset(State.SourcePositions[I])+FCanonicalFrame::WorldPosition(State.Frame.Origin)).Equals(
                FCanonicalFrame::WorldPosition(State.SourcePositions[I]),1e-9))
            { AddError(TEXT("Per-region source offset adds parent origin incorrectly"));return false; }
        // Exercise schema rejection against real arrays, without replacing the
        // in-memory validated result or changing any input file.
        Json->SetStringField(TEXT("canonical_frame"),TEXT("legacy-rebased-fixture"));
        FState Invalid=State;
        TestFalse(TEXT("Legacy translation cannot enter canonical region"),Decode(Json,Parent,Invalid,Error));
        TestEqual(TEXT("Failed decode clears stale water"),Invalid.Positions.Num(),0);
        Json->SetStringField(TEXT("canonical_frame"),TEXT("parent-ENU-centimetres"));
        Json->SetBoolField(TEXT("internal_source_emission"),true);
        TestFalse(TEXT("Internal emitter cannot create extra water"),Decode(Json,Parent,Invalid,Error));
        Regions.Add(MoveTemp(State));
    }
    TestTrue(TEXT("Final partial-color regions included"),TailRegions>0);
    TestTrue(TEXT("Interior regions need no artificial inlet"),EmptyInlets>0);
    if (!TestTrue(TEXT("All identities and physical cells owned once"),ValidateOwnership(Parent,Regions,Error)))
    { AddError(Error);return false; }
    const FState Duplicate=Regions.Last();Regions.Add(Duplicate);
    TestFalse(TEXT("Duplicate regional state rejected"),ValidateOwnership(Parent,Regions,Error));Regions.Pop();
    const auto Last=MoveTemp(Regions.Last());Regions.Pop();
    TestFalse(TEXT("Missing last region cannot truncate the river"),ValidateOwnership(Parent,Regions,Error));Regions.Add(Last);

    auto* Source=LoadObject<UNiagaraSystem>(nullptr,TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_SouthForkLiquidTerrainReview.NS_SouthForkLiquidTerrainReview"));
    if (!TestNotNull(TEXT("Saved Niagara template"),Source)) return false;
    TestFalse(TEXT("Never install regional state onto saved source"),InstallArrays(Source,Regions[0],Error));
    // One source-fed and one zero-inlet region test actual bound parameter
    // arrays. They remain unactivated; this is not pressure/contact coupling.
    TArray<int32> Examples;
    for (int32 I=0;I<Regions.Num();++I) if (!Regions[I].SourceIds.IsEmpty()) { Examples.Add(I);break; }
    for (int32 I=0;I<Regions.Num();++I) if (Regions[I].SourceIds.IsEmpty()) { Examples.Add(I);break; }
    Examples.AddUnique(Regions.Num()-1);
    for (int32 Index:Examples)
    {
        const auto& R=Regions[Index];
        TStrongObjectPtr<UNiagaraSystem> Candidate(DuplicateObject<UNiagaraSystem>(Source,GetTransientPackage()));
        if (!TestTrue(TEXT("Regional arrays and XYZ allocation installed on unused clone"),InstallArrays(Candidate.Get(),R,Error)))
        { AddError(Error);return false; }
        Candidate->RequestCompile(true);Candidate->WaitForCompilationComplete(false,false);Candidate->WaitForCompilationComplete(true,false);
        TestTrue(TEXT("Configured region is compiled but not activated"),Candidate->IsReadyToRun());
        int32 Kernels=0;
        for (const auto& Handle:Candidate->GetEmitterHandles())
            if (Handle.GetIsEnabled()) if (const auto* Data=Handle.GetInstance().GetEmitterData())
            {
                TArray<UNiagaraScript*> Scripts;Data->GetScripts(Scripts,false);
                for (const auto* Script:Scripts) if (Script->GetUsage()==ENiagaraScriptUsage::ParticleGPUComputeScript)
                {
                    ++Kernels;TestTrue(TEXT("Regional GPU program compiles"),Script->DidScriptCompilationSucceed(true));
                    const auto& Hlsl=Script->GetVMExecutableData().LastHlslTranslationGPU;
                    TestTrue(TEXT("Initial positions and velocities reach actual GPU spawn reader"),Hlsl.Contains(TEXT("Get_User_RiverInitialPositions")) && Hlsl.Contains(TEXT("Get_User_RiverInitialVelocities")));
                    TestTrue(TEXT("Subsequent external source branch retained"),Hlsl.Contains(TEXT("Get_User_RiverSourcePositions")) && Hlsl.Contains(TEXT("Get_User_RiverSourceVelocities")));
                }
            }
        TestEqual(TEXT("One primary regional GPU emitter"),Kernels,1);
        const auto& UpdateHlsl=Candidate->GetSystemUpdateScript()->GetVMExecutableData().LastHlslTranslation;
        TestTrue(TEXT("Exact regional count is in compiled initial timing gate"),UpdateHlsl.Contains(FString::Printf(TEXT(" = %d;"),R.SeedIds.Num())));
        TestFalse(TEXT("Initial burst no longer multiplies grid volume by particles per cell"),UpdateHlsl.Contains(TEXT("* Context.Map.Grid3D_FLIP_Tank_Spawn.ParticlesPerCell")));
        TestTrue(TEXT("Native one-time spawn info and indicator retained"),UpdateHlsl.Contains(TEXT("Grid3D_FLIP_Tank_Spawn.SpawnBurst =")) && UpdateHlsl.Contains(TEXT("Grid3D_FLIP_Tank_Spawn.HasSpawnedThisFrame =")));
        const auto& Store=Candidate->GetExposedParameters();
        for (const auto& Entry:TArray<TPair<FString,const TArray<FVector>*>>{
            {TEXT("User.River Initial Positions"),&R.Positions},{TEXT("User.River Initial Velocities"),&R.Velocities},
            {TEXT("User.River Source Positions"),&R.SourcePositions},{TEXT("User.River Source Velocities"),&R.SourceVelocities}})
        {
            const FNiagaraVariable V(FNiagaraTypeDefinition(UNiagaraDataInterfaceArrayFloat3::StaticClass()),FName(*Entry.Key));
            auto* A=Cast<UNiagaraDataInterfaceArrayFloat3>(Store.GetDataInterface(V));
            if (!TestNotNull(TEXT("Bound vector array"),A) || !TestEqual(TEXT("No seed or source truncation"),A->InternalFloatData.Num(),Entry.Value->Num())) return false;
            for (int32 I=0;I<Entry.Value->Num();++I)
            {
                const FVector P=(*Entry.Value)[I];
                const FVector3f Expected(Entry.Key==TEXT("User.River Source Positions")?R.Frame.WorldSourceOffset(P):FCanonicalFrame::WorldVector(P));
                if (A->InternalFloatData[I]!=Expected) { AddError(TEXT("Niagara position/velocity differs from explicit frame"));return false; }
            }
        }
        const FNiagaraVariable IdVar(FNiagaraTypeDefinition(UNiagaraDataInterfaceArrayInt32::StaticClass()),TEXT("User.River Initial Parent IDs"));
        auto* Ids=Cast<UNiagaraDataInterfaceArrayInt32>(Store.GetDataInterface(IdVar));
        TestTrue(TEXT("Stable parent identities accompany initial positions"),Ids && Ids->IntData==R.SeedIds);
        TestEqual(TEXT("Inlet rate uses same nominal volume"),Store.GetParameterValue<float>(FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("User.Inlet Particle Rate"))),float(R.SpawnRate));
        TStrongObjectPtr<UNiagaraComponent> Component(NewObject<UNiagaraComponent>());Component->SetAsset(Candidate.Get());
        TestFalse(TEXT("Cannot reinitialize a system already assigned to a component"),InstallArrays(Candidate.Get(),R,Error));
        Component->SetAsset(nullptr);
    }
    // Parent rows are checked directly, not just aggregate counts. This test
    // requires the prepared bytes; the independent SHA256 audit remains separate.
    const auto Initial=ReadRegionalJson(ParentDirectory/TEXT("hydraulic_initial_state.json"));
    if (!TestNotNull(TEXT("Parent initial state available for direct identity comparison"),Initial.Get())) return false;
    const auto& Positions=Initial->GetArrayField(TEXT("positions_world_cm"));
    const auto& Velocities=Initial->GetArrayField(TEXT("velocities_world_cm_per_s"));
    for (const auto& R:Regions) for (int32 I=0;I<R.SeedIds.Num();++I)
        for (int32 A=0;A<3;++A)
            if (R.Positions[I][A]!=Positions[R.SeedIds[I]]->AsArray()[A]->AsNumber() ||
                R.Velocities[I][A]!=Velocities[R.SeedIds[I]]->AsArray()[A]->AsNumber())
            { AddError(TEXT("Parent seed position/momentum changed during regional decode"));return false; }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidRegionalExteriorTest,"RaftSim.Editor.LiquidRegionalExterior",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidRegionalExteriorTest::RunTest(const FString&)
{
    using namespace RaftSimLiquidRegionalState;
    const FString Base=FPaths::ProjectDir()/TEXT("../tmp");
    const FString Directory=Base/TEXT("south-fork-liquid-regional-state-20260910");
    const auto Boundary=ReadRegionalJson(Base/TEXT("south-fork-whole-rapid-liquid-float-seeds-20260910/grid_vector_boundary_profile.json"));
    FParent Parent;FString Error;
    if (!DecodeParent(ReadRegionalJson(Directory/TEXT("manifest.json")),Boundary,Parent,Error)) { AddError(Error);return false; }
    TArray<FState> States;
    for (int32 Id=0;Id<12;++Id)
    {
        FState R;
        if (!Decode(ReadRegionalJson(Directory/FString::Printf(TEXT("region-%03d.json"),Id)),Parent,R,Error)) { AddError(Error);return false; }
        States.Add(MoveTemp(R));
    }
    RaftSimLiquidParentExterior::FProfile Profile,Invalid;
    if (!RaftSimLiquidParentExterior::FProfile::Build(Parent,States,Boundary,Profile,Error)) { AddError(Error);return false; }
    const auto Last=MoveTemp(States.Last());States.Pop();
    TestFalse(TEXT("Missing region cannot become a new inlet/outlet"),RaftSimLiquidParentExterior::FProfile::Build(Parent,States,Boundary,Invalid,Error));
    TestTrue(TEXT("Failed validation leaves no usable exterior table"),Invalid.Packed().IsEmpty());States.Add(Last);
    const auto SavedRows=Boundary->Values[TEXT("packed_vectors")];
    auto BadRows=Boundary->GetArrayField(TEXT("packed_vectors"));
    auto BadScalar=BadRows[8]->AsArray(),BadVector=BadRows[1312]->AsArray();
    BadScalar[2]=MakeShared<FJsonValueNumber>(100000);BadVector[0]=MakeShared<FJsonValueNumber>(100000);
    BadRows[8]=MakeShared<FJsonValueArray>(BadScalar);BadRows[1312]=MakeShared<FJsonValueArray>(BadVector);
    Boundary->SetArrayField(TEXT("packed_vectors"),BadRows);
    TestFalse(TEXT("Finite full-precision velocity cannot overflow the native half boundary"),
        RaftSimLiquidParentExterior::FProfile::Build(Parent,States,Boundary,Invalid,Error));
    TestTrue(TEXT("Overflow is rejected at the native format gate"),Error.Contains(TEXT("RGBA16F")));
    Boundary->Values[TEXT("packed_vectors")]=SavedRows;
    const auto& Original=Boundary->GetArrayField(TEXT("packed_vectors"));
    TestEqual(TEXT("Only bounded face metadata, no full-grid texture"),Profile.Packed().Num(),2616);
    for (int32 I=0;I<Original.Num();++I) for (int32 A=0;A<3;++A)
        if (Profile.Packed()[I][A]!=float(Original[I]->AsArray()[A]->AsNumber())*(I==3 && A==2?-1.f:1.f))
        { AddError(TEXT("Parent forcing values changed during binding preparation"));return false; }
    bool ExitBound=false;
    ENQUEUE_RENDER_COMMAND(RaftSimValidatedParentExit)([&](FRHICommandListImmediate& Cmd)
    {
        FRDGBuilder Graph(Cmd);TArray<FIntRect> Bounds;
        for(const auto& S:States) Bounds.Emplace(S.FirstCell,S.FirstCell+FIntPoint(S.Cells.X,S.Cells.Y));
        const FVector Lower=FCanonicalFrame::WorldPosition(Parent.Frame.AxisX*(Parent.Lower.X*100)+
            Parent.Frame.AxisY*(Parent.Lower.Y*100)+FVector(0,0,Parent.Frame.Origin.Z));
        auto Route=RaftSimBuildLiquidParticleRoutePlan(Graph,{Parent.Cells.X,Parent.Cells.Y},Bounds,Lower,
            FCanonicalFrame::WorldVector(Parent.Frame.AxisX),FCanonicalFrame::WorldVector(Parent.Frame.AxisY),
            {Parent.Spacing.X,Parent.Spacing.Y},Error);
        const auto Exit=Profile.ExitPlan(Graph,Route,Error);
        auto Wrong=Route;Wrong.LowerWorldCm.X+=1;
        ExitBound=Exit.FaceRows && Exit.HeightCm==float(Parent.Spacing.Z*Parent.Cells.Z) &&
            Exit.FaceRows->Desc.NumElements==uint32(2*(Parent.Cells.X+Parent.Cells.Y)) &&
            !Profile.ExitPlan(Graph,Wrong,Error).FaceRows && !Invalid.ExitPlan(Graph,Route,Error).FaceRows;
        Graph.Execute();
    });
    FlushRenderingCommands();
    TestTrue(TEXT("Exit classification shares the exact validated parent frame and face rows; reject shifted/unvalidated policies"),ExitBound);
    auto* Source=LoadObject<UNiagaraSystem>(nullptr,TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_SouthForkLiquidTerrainReview.NS_SouthForkLiquidTerrainReview"));
    if (!TestNotNull(TEXT("Saved source available"),Source)) return false;
    for (const int32 Id:{0,5,11})
    {
        const auto& R=States[Id];
        const auto Contact=ReadRegionalJson(Base/TEXT("south-fork-liquid-regional-geometry-v4-20260910")/FString::Printf(TEXT("region-%03d-contact.json"),Id));
        TStrongObjectPtr<UNiagaraSystem> Candidate(DuplicateObject<UNiagaraSystem>(Source,GetTransientPackage()));
        if (!InstallArrays(Candidate.Get(),R,Error)) { AddError(Error);return false; }
        TestFalse(TEXT("Unvalidated parent forcing cannot be installed"),RaftSimInstallRegionalLiquidContact(Candidate.Get(),R,Contact,Error,&Invalid));
        if (!RaftSimInstallRegionalLiquidContact(Candidate.Get(),R,Contact,Error,&Profile)) { AddError(Error);return false; }
        auto WrongParent=Parent;WrongParent.Frame.Origin.X+=1;
        TestFalse(TEXT("Outlet pressure must use the installed parent frame"),RaftSimInstallRegionalLiquidProjection(Candidate.Get(),WrongParent,R,Error));
        if (!RaftSimInstallRegionalLiquidProjection(Candidate.Get(),Parent,R,Error)) { AddError(Error);return false; }
        Candidate->RequestCompile(true);Candidate->WaitForCompilationComplete(false,false);Candidate->WaitForCompilationComplete(true,false);
        TestTrue(TEXT("Parent exterior regional program ready"),Candidate->IsReadyToRun());
        for (const auto& H:Candidate->GetEmitterHandles()) if (H.GetIsEnabled()) if (const auto* E=H.GetInstance().GetEmitterData())
        {
            TArray<UNiagaraScript*> Scripts;E->GetScripts(Scripts,false);
            for (const auto* S:Scripts) if (S->GetUsage()==ENiagaraScriptUsage::ParticleGPUComputeScript)
            {
                TestTrue(TEXT("Actual exterior GPU shader compiled"),S->DidScriptCompilationSucceed(true));
                const auto& Code=S->GetVMExecutableData().LastHlslTranslationGPU;
                TestTrue(TEXT("Parent table reaches native inflow and outlet consumers"),Code.Contains(TEXT("Get_User_RiverParentExterior")) &&
                    Code.Contains(TEXT("NativeVectorInflow")) && Code.Contains(TEXT("NativeOutletStageClassification")) && Code.Contains(TEXT("NativeOutletStagePressure")));
                const int32 RawWrite=Code.Find(TEXT("// RegionalRawP2G:"));
                const int32 Divide=Code.Find(TEXT("Out_Velocity /= TotalWeight;"));
                TestTrue(TEXT("Native NQ publishes raw momentum/volume before local normalization"),RawWrite>=0 && Divide>RawWrite &&
                    Code.Contains(TEXT("SetVector4Value_Emitter_RiverRawTransfer")));
                RaftSimLiquidRegionalProjection::FLayout L;RaftSimLiquidRegionalProjection::Build(Parent,R,L,Error);
                TestTrue(TEXT("Pressure lookup shifts local indices into parent grid"),Code.Contains(L.ParentIndexHlsl(TEXT("p"))));
                const int32 Inflow=Code.Find(TEXT("inflowSourcePosition="));
                AddInfo(TEXT("Compiled regional source coordinate: ")+Code.Mid(Inflow,220));
                TestFalse(TEXT("No legacy fixture table used for regional forcing"),Code.Contains(TEXT("Get_User_RiverGridBoundary")));
            }
        }
        const FNiagaraVariable V(FNiagaraTypeDefinition(UNiagaraDataInterfaceArrayFloat3::StaticClass()),TEXT("User.River Parent Exterior"));
        const auto* Data=Cast<UNiagaraDataInterfaceArrayFloat3>(Candidate->GetExposedParameters().GetDataInterface(V));
        TestTrue(TEXT("Bound parent rows unchanged"),Data && Data->InternalFloatData==Profile.Packed());
        const UNiagaraDataInterfaceGrid3DCollection* Raw=nullptr;int32 RawCount=0;
        for (const auto& Info:Candidate->GetSystemSpawnScript()->GetCachedDefaultDataInterfaces())
            if (Info.Name.ToString().EndsWith(TEXT(".RiverRawTransfer")) || Info.CompileName.ToString().EndsWith(TEXT(".RiverRawTransfer")))
            { Raw=Cast<UNiagaraDataInterfaceGrid3DCollection>(Info.DataInterface);++RawCount; }
        TestEqual(TEXT("One native emitter-owned raw transfer interface"),RawCount,1);
        TestTrue(TEXT("Raw transfer preserves full precision and explicit XYZ allocation"),Raw && Raw->bOverrideFormat &&
            Raw->OverrideBufferFormat==ENiagaraGpuBufferFormat::Float && Raw->NumCells==R.ComputationalCells &&
            Raw->NumAttributes==0 && Raw->SetResolutionMethod==ESetResolutionMethod::Independent);
        // Niagara renames custom-HLSL input pins during translation. Verify
        // the exact expression in the owned graph, and compiled consumers
        // above, rather than assuming an unrenamed GPU function parameter.
        bool CanonicalInflow=false;
        ForEachObjectWithOuter(Candidate.Get(),[&](UObject* O)
        {
            if (const auto* Node=Cast<UNiagaraNodeCustomHlsl>(O))
                if (const auto* P=FindFProperty<FStrProperty>(Node->GetClass(),TEXT("CustomHlsl")))
                    CanonicalInflow |= P->GetPropertyValue_InContainer(Node).Contains(TEXT("float3 inflowSourcePosition=float3(Position.x,-Position.y,Position.z)"));
        },EGetObjectsFlags::IncludeNestedObjects);
        TestTrue(TEXT("Regional inflow uses explicit canonical coordinates in the owned graph"),CanonicalInflow);
    }
    return true;
}
