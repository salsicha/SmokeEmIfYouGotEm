#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "NiagaraSystem.h"
#include "NiagaraEmitter.h"
#include "NiagaraEmitterHandle.h"
#include "NiagaraScript.h"
#include "NiagaraScriptSource.h"
#include "NiagaraGraph.h"
#include "NiagaraNodeFunctionCall.h"
#include "NiagaraRendererProperties.h"
#include "NiagaraDataInterfaceArrayFloat.h"
#include "Editor.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "HAL/IConsoleManager.h"
#include "NiagaraComponent.h"
#include "UObject/Package.h"
#include "UObject/UObjectHash.h"
#include "Internationalization/Regex.h"
#include "NiagaraNodeCustomHlsl.h"
#include "EdGraphSchema_Niagara.h"
#include "../Materials/RaftSimOutletStage.h"
#include "../Materials/RaftSimLiquidOptics.h"
#include "../Materials/RaftSimLiquidSecondaryOptics.h"
#include "../Materials/RaftSimLiquidSecondarySurface.h"
#include "../Materials/RaftSimLiquidWindowProfile.h"
#include "../Materials/RaftSimRegisteredTerrainQuery.h"
#include "../Materials/RaftSimSecondaryTerrainSweep.h"
#include "../Materials/RaftSimLiquidContactProfile.h"
#include "UObject/StrongObjectPtr.h"
#include "NiagaraDataInterfaceRenderTargetVolume.h"
#include "Engine/TextureRenderTarget2D.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidContactEncodingTest,
    "RaftSim.Editor.LiquidContactEncoding",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidContactEncodingTest::RunTest(const FString&)
{
    auto Profile=MakeShared<FJsonObject>();
    Profile->SetStringField(TEXT("schema"),TEXT("raftsim.registered_liquid_contact.v2"));
    Profile->SetStringField(TEXT("vertex_encoding"),TEXT("nominal-quad-local-xy-and-world-z-centimetres"));
    TArray<TSharedPtr<FJsonValue>> Values;
    for (const FVector3f& P:TArray<FVector3f>{{10000,4000,50},{50,1,1},
        {0,0,100},{50,0,125},{0,-50,150},{50,0,125},{50,-50,175},{0,-50,150}})
        Values.Add(MakeShared<FJsonValueArray>(TArray<TSharedPtr<FJsonValue>>{
            MakeShared<FJsonValueNumber>(P.X),MakeShared<FJsonValueNumber>(P.Y),MakeShared<FJsonValueNumber>(P.Z)}));
    Profile->SetArrayField(TEXT("packed_vectors"),Values);
    TArray<FVector3f> Packed;
    if (!TestTrue(TEXT("Quad-relative profile decoded"),RaftSimLiquidContactProfile::Decode(Profile,Packed))) return false;
    TestEqual(TEXT("Per-table relative marker"),Packed[1].Y,-1.f);
    TestEqual(TEXT("No conversion back to imprecise absolute XY"),Packed[3],FVector3f(50,0,125));
    TestEqual(TEXT("Source metadata untouched"),Values[1]->AsArray()[1]->AsNumber(),1.);
    const auto Primary=RaftSimRegisteredTerrainQueryHlsl(TEXT("P"));
    const auto Secondary=RaftSimSecondaryTerrainSweepHlsl();
    TestTrue(TEXT("Primary subtracts anchored nominal quad origin before vertex"),Primary.Contains(TEXT("queryXY-=float2(meta.x+(c+(int)pageOffset.x)*meta.z,meta.y-(r+(int)pageOffset.y)*dims.x)")));
    TestTrue(TEXT("Secondary supports table-local encoding"),Secondary.Contains(TEXT("if(dims.y<0)")) && Secondary.Contains(TEXT("-quadOrigin)-a.xy")));
    if (RaftSimLiquidWindowProfile::Geographic())
        TestTrue(TEXT("Relative swept contact uses canonical endpoints"),Secondary.Contains(TEXT("(contactStart.xy-quadOrigin)")) && Secondary.Contains(TEXT("(contactEnd.xy-quadOrigin)")));
    Profile->SetStringField(TEXT("vertex_encoding"),TEXT("unknown"));
    TestFalse(TEXT("Unknown encoding rejected"),RaftSimLiquidContactProfile::Decode(Profile,Packed));
    TestTrue(TEXT("Failed decode cannot retain a previous table"),Packed.IsEmpty());
    Profile->SetStringField(TEXT("schema"),TEXT("raftsim.registered_liquid_contact.v1"));
    TestTrue(TEXT("Legacy profiles remain supported"),RaftSimLiquidContactProfile::Decode(Profile,Packed));
    TestEqual(TEXT("Legacy positive marker"),Packed[1].Y,1.f);
    Profile->SetStringField(TEXT("schema"),TEXT("raftsim.registered_liquid_contact.v3"));
    Profile->SetStringField(TEXT("vertex_encoding"),TEXT("nominal-quad-local-xy-and-world-z-centimetres"));
    Values.Insert(MakeShared<FJsonValueArray>(TArray<TSharedPtr<FJsonValue>>{
        MakeShared<FJsonValueNumber>(-1),MakeShared<FJsonValueNumber>(32),MakeShared<FJsonValueNumber>(0)}),2);
    Profile->SetArrayField(TEXT("packed_vectors"),Values);
    TestTrue(TEXT("Anchored page with signed global offsets decoded"),RaftSimLiquidContactProfile::Decode(Profile,Packed));
    if (Packed.Num()!=9) return false;
    TestEqual(TEXT("Per-table anchored marker"),Packed[1].Z,-1.f);
    TestEqual(TEXT("Original addressing anchor unchanged"),Packed[0],FVector3f(10000,4000,50));
    TestEqual(TEXT("Offset retained without translation"),Packed[2],FVector3f(-1,32,0));
    TestTrue(TEXT("Both queries branch on per-table header"),Primary.Contains(TEXT("header=dims.z<0?3:2")) && Secondary.Contains(TEXT("header=dims.z<0?3:2")));
    Values[2]=MakeShared<FJsonValueArray>(TArray<TSharedPtr<FJsonValue>>{
        MakeShared<FJsonValueNumber>(.5),MakeShared<FJsonValueNumber>(32),MakeShared<FJsonValueNumber>(0)});
    Profile->SetArrayField(TEXT("packed_vectors"),Values);
    TestFalse(TEXT("Fractional page offset rejected"),RaftSimLiquidContactProfile::Decode(Profile,Packed));
    Values[2]=MakeShared<FJsonValueArray>(TArray<TSharedPtr<FJsonValue>>{
        MakeShared<FJsonValueNumber>(0),MakeShared<FJsonValueNumber>(32),MakeShared<FJsonValueNumber>(0)});
    Values[1]=MakeShared<FJsonValueArray>(TArray<TSharedPtr<FJsonValue>>{
        MakeShared<FJsonValueNumber>(50),MakeShared<FJsonValueNumber>(257),MakeShared<FJsonValueNumber>(1)});
    Profile->SetArrayField(TEXT("packed_vectors"),Values);
    TestFalse(TEXT("Bounded table limit not relaxed"),RaftSimLiquidContactProfile::Decode(Profile,Packed));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidGeographicFrameTest,
    "RaftSim.Editor.LiquidGeographicFrame",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidGeographicFrameTest::RunTest(const FString&)
{
    using namespace RaftSimLiquidWindowProfile;
    if (!TestTrue(TEXT("Documented source frame loads"),InitializeGeographicFrame())) return false;
    const FVector A(123,-432,731),B(-83,517,432),V(-210,87,15);
    const FVector Delta=PresentPosition(A)-PresentPosition(B);
    TestTrue(TEXT("Position differences equal vector transform"),Delta.Equals(PresentVector(A-B),1e-9));
    TestTrue(TEXT("Reflection preserves lengths"),FMath::IsNearlyEqual(Delta.Size(),(A-B).Size(),1e-9));
    TestTrue(TEXT("Vector transform is its own inverse"),PresentVector(PresentVector(V)).Equals(V,1e-9));
    TestTrue(TEXT("No translation leaks into velocity"),FMath::IsNearlyEqual(PresentVector(V).Size(),V.Size(),1e-9));
    TestTrue(TEXT("Vertical datum unchanged"),FMath::IsNearlyEqual(PresentPosition(A).Z,A.Z,1e-9));
    if (Geographic())
    {
        TestTrue(TEXT("Geographic offset is not accidentally zero"),GeographicTranslation.Size()>100);
        TestTrue(TEXT("Position inverse restores source"),PresentVector(PresentPosition(A)-GeographicTranslation).Equals(A,1e-9));
        TestTrue(TEXT("Source Y direction is reflected"),PresentVector(FVector::YAxisVector).Equals(-FVector::YAxisVector));
        TestTrue(TEXT("Primary terrain query converts coordinates and normals"),RaftSimRegisteredTerrainQueryHlsl(TEXT("P")).Contains(TEXT("normal.y=-normal.y")));
        const FString Sweep=RaftSimSecondaryTerrainSweepHlsl();
        TestTrue(TEXT("Spray sweep converts both endpoints"),Sweep.Contains(TEXT("min(contactStart.xy,contactEnd.xy)")) && Sweep.Contains(TEXT("p=contactStart.xy-a.xy,q=contactEnd.xy-a.xy")));
        TestTrue(TEXT("Spray domain check stays in actual Niagara coordinates"),Sweep.Contains(TEXT("oldOffset=Position-origin,newOffset=OutPosition-origin")));
        TestTrue(TEXT("Grid-index stage query reflects lateral coordinate"),RaftSimOutletStageQuery(TEXT("P"),TEXT("Profile"),true).Contains(TEXT("stagePosition.y=-stagePosition.y")));
        TestFalse(TEXT("Canonical stage query is not reflected twice"),RaftSimOutletStageQuery(TEXT("P"),TEXT("Profile")).Contains(TEXT("stagePosition.y=-stagePosition.y")));
    }
    else
    {
        TestTrue(TEXT("Legacy source positions unchanged"),PresentPosition(A)==A);
        TestEqual(TEXT("Legacy query unchanged"),SourcePositionHlsl(TEXT("P")),FString(TEXT("P")));
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidBaseScatteringGraphTest,
    "RaftSim.Editor.LiquidFixtureBaseScatteringGraph",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidBaseScatteringGraphTest::RunTest(const FString&)
{
    auto* Source=LoadObject<UMaterial>(nullptr,TEXT("/NiagaraFluids/Materials/Grid3D/M_WaterSDF.M_WaterSDF"));
    if (!TestNotNull(TEXT("SDF material template"),Source)) return false;
    UMaterialExpressionSingleLayerWaterMaterialOutput* OriginalWater=nullptr;
    for (const auto& Expression:Source->GetExpressionCollection().Expressions)
        if (auto* Water=Cast<UMaterialExpressionSingleLayerWaterMaterialOutput>(Expression)) OriginalWater=Water;
    if (!TestNotNull(TEXT("Original water output"),OriginalWater)) return false;
    auto* OriginalScattering=OriginalWater->ScatteringCoefficients.Expression;
    TStrongObjectPtr<UMaterial> Candidate(RaftSimCreateLiquidScatteringReview(Source));
    if (!TestNotNull(TEXT("Transient optical candidate"),Candidate.Get())) return false;
    TestEqual(TEXT("Source scattering graph untouched"),OriginalWater->ScatteringCoefficients.Expression,OriginalScattering);
    TestEqual(TEXT("Transient ownership"),Candidate->GetOutermost(),GetTransientPackage());
    TestEqual(TEXT("Same shading model"),Candidate->GetShadingModels().GetShadingModelField(),Source->GetShadingModels().GetShadingModelField());
    for (auto Property:{MP_Normal,MP_WorldPositionOffset,MP_PixelDepthOffset,MP_OpacityMask,MP_Opacity})
    {
        const auto* A=Source->GetExpressionInputForProperty(Property);
        const auto* B=Candidate->GetExpressionInputForProperty(Property);
        TestEqual(TEXT("Geometry and opacity expression identity preserved"),A->Expression->GetName(),B->Expression->GetName());
        TestEqual(TEXT("Geometry output index preserved"),A->OutputIndex,B->OutputIndex);
    }
    int32 WaterCount=0;
    for (const auto& Expression:Candidate->GetExpressionCollection().Expressions)
        if (auto* Water=Cast<UMaterialExpressionSingleLayerWaterMaterialOutput>(Expression))
        {
            ++WaterCount;
            auto* Scattering=Cast<UMaterialExpressionMultiply>(Water->ScatteringCoefficients.Expression);
            if (!TestNotNull(TEXT("Base scattering is a direct coefficient product"),Scattering)) return false;
            auto* Parameter=Cast<UMaterialExpressionVectorParameter>(Scattering->A.Expression);
            if (!TestNotNull(TEXT("Base scattering vector"),Parameter)) return false;
            TestEqual(TEXT("Independent of the Whitewater multiplier"),Parameter->ParameterName,FName(TEXT("Scattering")));
            TestEqual(TEXT("RGB times coefficient alpha"),Scattering->B.OutputIndex,4);
            TestEqual(TEXT("Absorption graph preserved"),Water->AbsorptionCoefficients.Expression->GetName(),OriginalWater->AbsorptionCoefficients.Expression->GetName());
        }
    TestEqual(TEXT("Exactly one water output"),WaterCount,1);
    auto* SourceNormal=Source->GetExpressionInputForProperty(MP_Normal)->Expression;
    TestTrue(TEXT("World-normal correction accepts the transient candidate"),RaftSimCorrectLiquidWorldNormal(Candidate.Get()));
    TestFalse(TEXT("World-normal correction refuses the source asset"),RaftSimCorrectLiquidWorldNormal(Source));
    TestEqual(TEXT("Source normal untouched"),Source->GetExpressionInputForProperty(MP_Normal)->Expression,SourceNormal);
    auto* WorldNormal=Cast<UMaterialExpressionCustom>(Candidate->GetExpressionInputForProperty(MP_Normal)->Expression);
    if (!TestNotNull(TEXT("World-normal transform present"),WorldNormal)) return false;
    if (!TestEqual(TEXT("Grid normal and three world-basis inputs"),WorldNormal->Inputs.Num(),4)) return false;
    if (!TestNotNull(TEXT("Connected SDF normal input"),WorldNormal->Inputs[0].Input.Expression)) return false;
    TestEqual(TEXT("Original SDF normal used"),WorldNormal->Inputs[0].Input.Expression->GetName(),SourceNormal->GetName());
    for (int32 Axis=0;Axis<3;++Axis)
    {
        auto* Row=Cast<UMaterialExpressionVectorParameter>(WorldNormal->Inputs[Axis+1].Input.Expression);
        if (!TestNotNull(TEXT("World-basis parameter"),Row)) return false;
        TestEqual(TEXT("Uses actual grid-to-world matrix row"),Row->ParameterName,FName(*FString::Printf(TEXT("LocalToWorld%d"),Axis)));
    }
    TestTrue(TEXT("Mixed-frame depth test corrected"),RaftSimCorrectLiquidRayFrame(Candidate.Get()));
    TestFalse(TEXT("Depth correction refuses engine source"),RaftSimCorrectLiquidRayFrame(Source));
    int32 CorrectedDepthTests=0;
    for (const auto& Expression:Candidate->GetExpressionCollection().Expressions)
        if (auto* Custom=Cast<UMaterialExpressionCustom>(Expression))
        {
            TestFalse(TEXT("No mixed-frame camera-depth dot"),Custom->Code.Contains(TEXT("SceneDepth / dot(LocalRayDir, CameraDirectionVector)")));
            CorrectedDepthTests+=Custom->Code.Contains(TEXT("SceneDepth / max(dot(WorldRayDir, CameraDirectionVector),1e-6)"));
        }
    TestEqual(TEXT("One corrected ray depth path"),CorrectedDepthTests,1);
    // Reproduce the oblique fixture's failure, independent of shader graph text.
    const FVector LocalRay=FVector(17,23,-9.5).GetSafeNormal();
    const FVector WorldRay=FRotator(0,158.434789,0).RotateVector(LocalRay);
    TestTrue(TEXT("Old mixed-space dot rejects the forward oblique ray"),FVector::DotProduct(LocalRay,WorldRay)<0);
    TestEqual(TEXT("World-space camera depth is positive"),FVector::DotProduct(WorldRay,WorldRay),1.,1e-6);
    auto* BeforeMask=Candidate->GetExpressionInputForProperty(MP_OpacityMask)->Expression;
    auto* BeforeNormal=Candidate->GetExpressionInputForProperty(MP_Normal)->Expression;
    TestTrue(TEXT("Foam optics on owned candidate"),RaftSimConnectLiquidFoamOptics(Candidate.Get()));
    TestFalse(TEXT("Foam optics refuses engine source"),RaftSimConnectLiquidFoamOptics(Source));
    TestEqual(TEXT("Foam preserves single surface mask"),Candidate->GetExpressionInputForProperty(MP_OpacityMask)->Expression,BeforeMask);
    TestEqual(TEXT("Foam preserves corrected normal transform"),Candidate->GetExpressionInputForProperty(MP_Normal)->Expression,BeforeNormal);
    for (auto Property:{MP_BaseColor,MP_Roughness,MP_Opacity})
    {
        auto* Blend=Cast<UMaterialExpressionCustom>(Candidate->GetExpressionInputForProperty(Property)->Expression);
        if (!TestNotNull(TEXT("Foam BSDF blend"),Blend) || !TestEqual(TEXT("Three foam blend inputs"),Blend->Inputs.Num(),3)) return false;
        TestEqual(TEXT("Surface-hit whitewater output"),Blend->Inputs[1].Input.OutputIndex,2);
        auto* Hit=Cast<UMaterialExpressionCustom>(Blend->Inputs[1].Input.Expression);
        if (!TestNotNull(TEXT("Foam samples actual SDF hit"),Hit)) return false;
        TestTrue(TEXT("Coverage comes from volume green"),Hit->Code.Contains(TEXT("Whitewater = VolumeSample.g;")));
        TestFalse(TEXT("Foam never substitutes for SDF normals"),Hit->Code.Contains(TEXT("ComputeNormals > 1-1e-5")));
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidSecondaryOpticsTest,
    "RaftSim.Editor.LiquidFixtureSecondaryOptics",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidSecondaryOpticsTest::RunTest(const FString&)
{
    auto* Source=LoadObject<UMaterial>(nullptr,TEXT("/NiagaraFluids/Materials/Particles/WhitewaterMaterial.WhitewaterMaterial"));
    if (!TestNotNull(TEXT("Native secondary material"),Source)) return false;
    auto* SourceNormal=Source->GetExpressionInputForProperty(MP_Normal)->Expression;
    auto* SourceSpecular=Source->GetExpressionInputForProperty(MP_Specular)->Expression;
    TStrongObjectPtr<UMaterial> Candidate(RaftSimCreateSecondaryOptics(Source));
    if (!TestNotNull(TEXT("Owned secondary optics"),Candidate.Get())) return false;
    TestEqual(TEXT("Transient optics only"),Candidate->GetOutermost(),GetTransientPackage());
    TestEqual(TEXT("Same native lifetime opacity expression"),Candidate->GetExpressionInputForProperty(MP_Opacity)->Expression->GetName(),
        Source->GetExpressionInputForProperty(MP_Opacity)->Expression->GetName());
    TestEqual(TEXT("Same blend mode"),Candidate->BlendMode,Source->BlendMode);
    TestEqual(TEXT("Source normal unchanged"),Source->GetExpressionInputForProperty(MP_Normal)->Expression,SourceNormal);
    TestEqual(TEXT("Source specular unchanged"),Source->GetExpressionInputForProperty(MP_Specular)->Expression,SourceSpecular);
    TestTrue(TEXT("Normal uses sprite tangent frame"),Candidate->bTangentSpaceNormal!=0);
    for (const auto& Pair:TArray<TPair<EMaterialProperty,float>>{{MP_Roughness,.65f},{MP_Specular,.25f}})
    {
        auto* Value=Cast<UMaterialExpressionScalarParameter>(Candidate->GetExpressionInputForProperty(Pair.Key)->Expression);
        if (!TestNotNull(TEXT("Explicit bounded optical parameter"),Value)) return false;
        TestEqual(TEXT("Expected foam optical value"),Value->DefaultValue,Pair.Value);
    }
    TestNull(TEXT("No added surface displacement"),Candidate->GetExpressionInputForProperty(MP_WorldPositionOffset)->Expression);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidOutletShaderSubstitutionTest,
    "RaftSim.Editor.LiquidFixtureOutletShaderSubstitution",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidOutletShaderSubstitutionTest::RunTest(const FString&)
{
    const FString Code=RaftSimOutletStageQuery(TEXT("float3(1,2,3)"),TEXT("StageProfile"));
    TestTrue(TEXT("Local variable survives placeholder replacement"),Code.Contains(TEXT("float3 stagePosition=float3(1,2,3);")));
    TestTrue(TEXT("Later references preserve local variable"),Code.Contains(TEXT("stagePosition.z>stageRow.x")));
    TestTrue(TEXT("Profile input substituted"),Code.Contains(TEXT("StageProfile.Get(2,stageMeta)")));
    TestFalse(TEXT("No corrupted position identifier"),Code.Contains(TEXT("stagefloat3")));
    TestFalse(TEXT("No unresolved position placeholder"),Code.Contains(TEXT("POSITION"),ESearchCase::CaseSensitive));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidTerrainContactConfigurationTest,
    "RaftSim.Editor.LiquidFixtureTerrainContactConfiguration",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidTerrainContactConfigurationTest::RunTest(const FString&)
{
    auto* System=LoadObject<UNiagaraSystem>(nullptr,TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_SouthForkLiquidTerrainContactReview.NS_SouthForkLiquidTerrainContactReview"));
    auto* Baseline=LoadObject<UNiagaraSystem>(nullptr,TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_SouthForkLiquidTerrainReview.NS_SouthForkLiquidTerrainReview"));
    if (!TestNotNull(TEXT("Saved contact candidate"),System) || !TestNotNull(TEXT("Baseline"),Baseline)) return false;
    System->WaitForCompilationComplete(false,false);
    TestTrue(TEXT("Contact candidate reloads ready"),System->IsReadyToRun());
    TSet<UNiagaraGraph*> Graphs;
    int32 Renderers=0;
    for (const auto& Handle:System->GetEmitterHandles())
        if (auto* Data=Handle.GetInstance().GetEmitterData())
        {
            for (auto* Renderer:Data->GetRenderers()) Renderers+=Renderer->GetIsEnabled();
            if (!Handle.GetName().ToString().Contains(TEXT("FluidControl"))) continue;
            TArray<UNiagaraScript*> Scripts;Data->GetScripts(Scripts,false);
            for (auto* Script:Scripts)
                if (auto* Source=Cast<UNiagaraScriptSource>(Script->GetLatestSource())) Graphs.Add(Source->NodeGraph);
        }
    TestEqual(TEXT("One visible renderer, no added collision sprites"),Renderers,1);
    UNiagaraNodeFunctionCall* Contact=nullptr;
    int32 Contacts=0,DisabledRejects=0,Retirement=0;
    for (auto* Graph:Graphs)
        for (const auto& Node:Graph->Nodes)
            if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Node);Call && Call->FunctionScript)
            {
                if (Call->FunctionScript->GetPathName()==TEXT("/Niagara/Modules/Collision/Collision.Collision"))
                { Contact=Call;++Contacts; }
                if (Call->GetFunctionName()==TEXT("KillParticles"))
                    DisabledRejects+=Call->GetDesiredEnabledState()==ENodeEnabledState::Disabled;
                if (Call->FunctionScript->GetName()==TEXT("KillParticlesInVolume"))
                    Retirement+=Call->GetDesiredEnabledState()==ENodeEnabledState::Enabled;
            }
    TestEqual(TEXT("Exactly one actual contact module"),Contacts,1);
    TestEqual(TEXT("Solid-cell deletion disabled"),DisabledRejects,1);
    TestEqual(TEXT("Escape retirement retained"),Retirement,1);
    if (Contacts!=1) return false;
    TestTrue(TEXT("Contact enabled"),Contact->GetDesiredEnabledState()==ENodeEnabledState::Enabled);
    const auto Choice=[&](FName PinName,const TCHAR* EnumPath,const FString& Expected)
    {
        const auto* Pin=Contact->FindPin(PinName,EGPD_Input);
        auto* Enum=LoadObject<UEnum>(nullptr,EnumPath);
        if (!TestNotNull(*PinName.ToString(),Pin) || !TestNotNull(TEXT("Choice enum"),Enum)) return;
        const int32 Index=Enum->GetIndexByNameString(Pin->DefaultValue);
        TestTrue(*PinName.ToString(),Index!=INDEX_NONE && Enum->GetDisplayNameTextByIndex(Index).ToString().Contains(Expected));
    };
    Choice(TEXT("GPU Collision Type"),TEXT("/Niagara/Enums/ENiagara_GPUCollisionType.ENiagara_GPUCollisionType"),TEXT("Distance"));
    Choice(TEXT("Radius Calculation Type"),TEXT("/Niagara/Enums/ENiagaraCollisionRadiusOptions.ENiagaraCollisionRadiusOptions"),TEXT("Custom"));
    TMap<FString,FString> Defaults;
    const FString Prefix=Contact->GetFunctionName()+TEXT(".");
    for (auto* Graph:Graphs)
        for (const auto& Node:Graph->Nodes)
            for (const auto* Pin:Node->Pins)
                if (Pin->Direction==EGPD_Input && Pin->LinkedTo.IsEmpty() && Pin->PinName.ToString().StartsWith(Prefix))
                    Defaults.Add(Pin->PinName.ToString().RightChop(Prefix.Len()),Pin->DefaultValue);
    for (const auto& Setting:TArray<TPair<FString,FString>>{
        {TEXT("Collision Enabled"),TEXT("true")},{TEXT("Correct Interpenetration"),TEXT("true")},
        {TEXT("Kill On Collision"),TEXT("false")},{TEXT("Kill Particles Lodged Within Meshes"),TEXT("false")},
        {TEXT("Enable Rest State"),TEXT("false")},{TEXT("EnableMaxCollisionCount"),TEXT("false")},
        {TEXT("Particle Radius"),TEXT("2.0")},{TEXT("Restitution"),TEXT("0.0")},
        {TEXT("Friction"),TEXT("0.0")},{TEXT("Static Friction"),TEXT("0.0")}})
        TestEqual(*Setting.Key,Defaults.FindRef(Setting.Key),Setting.Value);
    for (const FName Name:{FName(TEXT("User.River Source Positions")),FName(TEXT("User.River Source Velocities"))})
    {
        const FNiagaraVariable Variable(FNiagaraTypeDefinition(UNiagaraDataInterfaceArrayFloat3::StaticClass()),Name);
        auto* Actual=Cast<UNiagaraDataInterfaceArrayFloat3>(System->GetExposedParameters().GetDataInterface(Variable));
        auto* Original=Cast<UNiagaraDataInterfaceArrayFloat3>(Baseline->GetExposedParameters().GetDataInterface(Variable));
        if (TestNotNull(TEXT("Candidate source table"),Actual) && TestNotNull(TEXT("Baseline source table"),Original))
            TestTrue(*Name.ToString(),Actual->InternalFloatData==Original->InternalFloatData);
    }
    // These graph invariants do not assert terrain separation or flux accuracy.
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidTerrainGridFrameTest,
    "RaftSim.Editor.LiquidFixtureTerrainGridFrameTransfer",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidTerrainGridFrameTest::RunTest(const FString&)
{
    auto* World=GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
    auto* Baseline=LoadObject<UNiagaraSystem>(nullptr,TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_SouthForkLiquidTerrainContactReview.NS_SouthForkLiquidTerrainContactReview"));
    if (!TestNotNull(TEXT("Editor world"),World) || !TestNotNull(TEXT("Contact baseline"),Baseline)) return false;
    const bool WasDirty=Baseline->GetOutermost()->IsDirty();
    TMap<FName,TArray<FVector3f>> OriginalSources;
    for (const FName Name:{FName(TEXT("User.River Source Positions")),FName(TEXT("User.River Source Velocities"))})
    {
        const FNiagaraVariable V(FNiagaraTypeDefinition(UNiagaraDataInterfaceArrayFloat3::StaticClass()),Name);
        const auto* Array=Cast<UNiagaraDataInterfaceArrayFloat3>(Baseline->GetExposedParameters().GetDataInterface(V));
        if (!TestNotNull(TEXT("Saved source arrays available"),Array)) return false;
        OriginalSources.Add(Name,Array->InternalFloatData);
    }
    TSharedPtr<FJsonObject> CenteredSources;
    if (RaftSimLiquidWindowProfile::Centered() &&
        !TestTrue(TEXT("Selected native source profile readable"),RaftSimLiquidWindowProfile::Read(TEXT("native_source_profile.json"),CenteredSources))) return false;
    FActorSpawnParameters Spawn;Spawn.ObjectFlags|=RF_Transient;
    auto* Actor=World->SpawnActor<AActor>(Spawn);
    if (!TestNotNull(TEXT("Transient fixture actor"),Actor)) return false;
    auto* Component=NewObject<UNiagaraComponent>(Actor);
    Component->SetAutoActivate(false);
    Actor->AddInstanceComponent(Component);
    for (const TCHAR* Variant:{TEXT("grid-frame"),TEXT("complete-gather"),TEXT("open-sides"),TEXT("wet-start"),TEXT("exact-triangles"),TEXT("grid-halo"),TEXT("driven-boundary"),TEXT("compatible-projection"),TEXT("outlet-stage"),TEXT("centered-transfer"),TEXT("centered-transfer pic-flip=1"),TEXT("vector-boundary"),TEXT("foam"),TEXT("surface-foam")})
    {
        const bool SurfaceFoam=FString(Variant)==TEXT("surface-foam");
        const bool Foam=SurfaceFoam || FString(Variant)==TEXT("foam");
        const bool VectorBoundary=Foam || FString(Variant)==TEXT("vector-boundary");
        const bool CenteredTransfer=VectorBoundary || FString(Variant).StartsWith(TEXT("centered-transfer"));
        const bool OutletStage=CenteredTransfer || FString(Variant)==TEXT("outlet-stage");
        const bool Compatible=OutletStage || FString(Variant)==TEXT("compatible-projection");
        const bool DrivenBoundary=Compatible || FString(Variant)==TEXT("driven-boundary");
        const bool GridHalo=DrivenBoundary || FString(Variant)==TEXT("grid-halo");
        const bool ExactTriangles=GridHalo || FString(Variant)==TEXT("exact-triangles");
        const bool WetState=ExactTriangles || FString(Variant)==TEXT("wet-start");
        Component->SetAsset(Baseline);
        IConsoleManager::Get().ProcessUserConsoleInput(
            *FString::Printf(TEXT("RaftSim.LiquidTerrainMomentumReview %s"),Variant),*GLog,World);
        auto* Candidate=Component->GetAsset();
        if (!TestTrue(TEXT("Command installed a separate unsaved candidate"),Candidate!=Baseline)) continue;
        TestTrue(TEXT("Transient package only"),Candidate->GetOutermost()==GetTransientPackage());
        TestTrue(TEXT("Compiled candidate ready"),Candidate->IsReadyToRun());
        if (Foam)
        {
            int32 Volumes=0;
            // Check the bound renderer DI, not unused custom-input defaults
            // which Niagara also creates beneath the transient system.
            for (const auto& Info:Candidate->GetSystemSpawnScript()->GetCachedDefaultDataInterfaces())
                if (Info.Name.ToString().EndsWith(TEXT(".SimRT")) || Info.CompileName.ToString().EndsWith(TEXT(".SimRT")))
                {
                    auto* Volume=Cast<UNiagaraDataInterfaceRenderTargetVolume>(Info.DataInterface);
                    if (!TestNotNull(TEXT("Bound SimRT is a render volume"),Volume)) continue;
                    ++Volumes;
                    TestTrue(TEXT("Explicit foam history format"),bool(Volume->bOverrideFormat));
                    TestEqual(TEXT("Foam green cannot be discarded by R16f storage"),int32(Volume->OverrideRenderTargetFormat),int32(RTF_RGBA16f));
                    TestEqual(TEXT("Interpolated transported volume"),int32(Volume->OverrideRenderTargetFilter),int32(TF_Bilinear));
                }
            TestEqual(TEXT("One bound surface render volume exists"),Volumes,1);
        }
        if (DrivenBoundary)
        {
            const auto& Store=Candidate->GetExposedParameters();
            const FNiagaraVariable V(FNiagaraTypeDefinition(UNiagaraDataInterfaceArrayFloat3::StaticClass()),TEXT("User.River Grid Boundary"));
            const auto* Array=Cast<UNiagaraDataInterfaceArrayFloat3>(Store.GetDataInterface(V));
            TestTrue(TEXT("Four complete flow face profiles"),Array && Array->InternalFloatData.Num()==(VectorBoundary ? 516 : 260));
            if (VectorBoundary && Array && Array->InternalFloatData.Num()==516)
            {
                int32 NonzeroTangents=0;
                for (int32 Face=0;Face<4;++Face) for (int32 Column=0;Column<64;++Column)
                {
                    const auto& Row=Array->InternalFloatData[4+Face*64+Column];
                    const auto& Velocity=Array->InternalFloatData[260+Face*64+Column];
                    const int32 Axis=Face<2?0:1;const float Sign=Face%2?-1.f:1.f;
                    TestEqual(TEXT("Full vector retains conservative normal"),Sign*Velocity[Axis],Row.Z,.001f);
                    NonzeroTangents+=Row.Z>0 && FMath::Abs(Velocity[1-Axis])>.01f;
                }
                TestTrue(TEXT("Native tangential inflow is present"),NonzeroTangents>0);
            }
            TestEqual(TEXT("Boundary velocity has unit scale"),Store.GetParameterValue<float>(
                FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("User.Collision Velocity Mult"))),1.f);
        }
        if (GridHalo)
        {
            const auto& Store=Candidate->GetExposedParameters();
            const FVector3f Extents=Store.GetParameterValue<FVector3f>(FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.World Grid Extents")));
            const FVector3f Cells=Store.GetParameterValue<FVector3f>(FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.RaftSim Allocation Cells")));
            TestEqual(TEXT("Explicit XYZ halo resolution"),Cells,FVector3f(68,68,24));
            TestEqual(TEXT("Halo extents"),Extents,FVector3f(2231.25f,2231.25f,800.f));
            TestEqual(TEXT("Unchanged hydraulic cell size"),Extents.X/Cells.X,2100.f/64.f);
            TestEqual(TEXT("Native face remains two cells inside grid"),(Extents.X-2100.f)*.5f,2.f*2100.f/64.f);
        }
        int32 CorrectedShaders=0;
        for (const auto& Handle:Candidate->GetEmitterHandles())
            if (const auto* Data=Handle.GetInstance().GetEmitterData())
            {
                TArray<UNiagaraScript*> Scripts;Data->GetScripts(Scripts,false);
                for (const auto* Script:Scripts)
                {
                    if (Handle.GetIsEnabled() && Script->GetUsage()==ENiagaraScriptUsage::ParticleGPUComputeScript)
                        TestTrue(TEXT("Actual GPU shader compilation succeeded"),Script->DidScriptCompilationSucceed(true));
                    const FString& Hlsl=Script->GetVMExecutableData().LastHlslTranslationGPU;
                    if (!Hlsl.Contains(TEXT("worldVelocity"))) continue;
                    ++CorrectedShaders;
                    if (SurfaceFoam)
                    {
                        TestFalse(TEXT("No redundant native foam attribute"),Hlsl.Contains(TEXT("RiverFoam")));
                        TestTrue(TEXT("Actual simulation clock retained"),Hlsl.Contains(TEXT("2048.0")));
                        TestTrue(TEXT("Surface green remains explicitly bound"),Hlsl.Contains(TEXT("Grid3D_SetRTValues.Green")));
                    }
                    else if (Foam)
                    {
                        TestTrue(TEXT("Actual GPU advected foam kernel"),Hlsl.Contains(TEXT("AdvectedRiverFoam")));
                        TestTrue(TEXT("Foam scratch carried between surface stages"),Hlsl.Contains(TEXT("RiverFoam")));
                        TestTrue(TEXT("Surface output green has a live binding"),Hlsl.Contains(TEXT("Grid3D_SetRTValues.Green")));
                        TestTrue(TEXT("Foam reset rejects stale history"),Hlsl.Contains(TEXT("In_Age>1.5*In_DeltaTime")));
                        TestTrue(TEXT("Convolution resolves SDF channel by name"),Hlsl.Contains(TEXT("GetFloatAttributeIndex_Emitter_SDFGrid_AttributeSDF(Out_Index)")));
                        TestTrue(TEXT("Foam reads history only after fresh X convolution"),Hlsl.Contains(TEXT("read previous SimRT only in stage16; stage17 writes it")));
                    }
                    if (VectorBoundary)
                        TestTrue(TEXT("Actual GPU consumes vector inflow"),Hlsl.Contains(TEXT("NativeVectorInflow")));
                    if (CenteredTransfer)
                    {
                        TestTrue(TEXT("Actual GPU centered metric transfer"),Hlsl.Contains(TEXT("CenteredMetricParticleTransfer")));
                        TestFalse(TEXT("No half-cell-biased X gather"),Hlsl.Contains(TEXT("x <= 0")));
                        TestTrue(TEXT("All supporting X bins"),Hlsl.Contains(TEXT("x <= 1")));
                        TestTrue(TEXT("Anisotropic Z cell metric"),Hlsl.Contains(TEXT("NumCellsZ/length(In_UnitToWorld[2].xyz)")));
                    }
                    if (OutletStage)
                        TestTrue(TEXT("Actual GPU native outlet pressure and classification"),Hlsl.Contains(TEXT("NativeOutletStagePressure")) &&
                            Hlsl.Contains(TEXT("NativeOutletStageClassification")) && Hlsl.Contains(TEXT("RetBoundary=3")));
                    if (Compatible)
                        for (const TCHAR* Marker:{TEXT("CompatibleMaskedDivergence"),TEXT("CompatibleMaskedPressure"),
                            TEXT("CompatibleWideStencilColoring"),TEXT("CompatiblePartialColorTail"),TEXT("CompatibleAnisotropicGradient"),TEXT("CompatiblePreserveProjectedSupport")})
                            TestTrue(Marker,Hlsl.Contains(Marker));
                    if (DrivenBoundary)
                        TestTrue(TEXT("Native face normal flux in compiled pressure boundary"),Hlsl.Contains(TEXT("PrescribedNativeFaceFlux")) &&
                            Hlsl.Contains(TEXT("Get_User_RiverGridBoundary")) && Hlsl.Contains(TEXT("Out_Distance=-0.01")));
                    if (FString(Variant)==TEXT("open-sides") || WetState)
                    {
                        // Check the complete control-to-axis binding in the compiled
                        // program. Custom-HLSL argument names alone swap Y and Z.
                        for (const auto& Binding:TArray<TPair<FString,FString>>{
                            {TEXT("ASC45X"),TEXT("Grid3D_FLIP_FLUID_CONTROLS.OpenBoundaryLeft")},
                            {TEXT("ASC43X"),TEXT("User.OpenOutlet")},
                            {TEXT("ASC45Y"),TEXT("Grid3D_FLIP_FLUID_CONTROLS.OpenBoundaryBack")},
                            {TEXT("ASC43Y"),TEXT("Grid3D_FLIP_FLUID_CONTROLS.OpenBoundaryFront")},
                            {TEXT("ASC45Z"),TEXT("Grid3D_FLIP_FLUID_CONTROLS.OpenBoundaryDown")},
                            {TEXT("ASC43Z"),TEXT("Grid3D_FLIP_FLUID_CONTROLS.OpenBoundaryUp")}})
                        {
                            const FRegexPattern Pattern(TEXT("OpenBoundary")+Binding.Key+
                                TEXT(" = [^;\\r\\n]+\\.")+Binding.Value.Replace(TEXT("."),TEXT("\\."))+TEXT(";"));
                            FRegexMatcher Matcher(Pattern,Hlsl);
                            TestTrue(*FString::Printf(TEXT("Compiled boundary %s maps to %s"),*Binding.Key,*Binding.Value),Matcher.FindNext());
                        }
                    }
                    TestTrue(TEXT("Normalize grid axes before velocity projection"),Hlsl.Contains(TEXT("normalize(In_UnitToWorld[0].xyz)")));
                    if (FString(Variant)!=TEXT("grid-frame"))
                        TestFalse(TEXT("No initial-density truncation in compiled gather"),Hlsl.Contains(TEXT("CurrNQCount = min(In_MaxParticlesPerCell, CurrNQCount)")));
                    if (WetState)
                        TestTrue(TEXT("Registered initial-state lookup in GPU program"),Hlsl.Contains(TEXT("Out_SeedKill=index>=count")) && Hlsl.Contains(TEXT("Get_User_RiverInitialPositions")));
                    if (ExactTriangles)
                        TestTrue(TEXT("Same triangle lookup in pressure and particle kernels"),Hlsl.Contains(TEXT("RegisteredTriangleBoundary")) &&
                            Hlsl.Contains(TEXT("Out_ProjectedPosition.z+=max(2.0-distance,0.0)")) && Hlsl.Contains(TEXT("Get_User_RiverContactTriangles")));
                }
            }
        TestTrue(TEXT("Correction present in actual compiled GPU program"),CorrectedShaders>0);
        const FNiagaraVariable Outlet(FNiagaraTypeDefinition::GetBoolDef(),TEXT("User.Open Outlet"));
        TestTrue(TEXT("Positive X outlet remains open"),Candidate->GetExposedParameters().GetParameterValue<FNiagaraBool>(Outlet).GetValue());
        if (FString(Variant)==TEXT("open-sides") || WetState)
        {
            TArray<UNiagaraNodeFunctionCall*> Controls;
            ForEachObjectWithOuter(Candidate,[&](UObject* Object)
            {
                if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Object);Call && Call->FunctionScript &&
                    Call->FunctionScript->GetName()==TEXT("Grid3D_FLIP_FLUID_CONTROLS") && Call->GetNiagaraGraph()->IsIn(Candidate)) Controls.Add(Call);
            },EGetObjectsFlags::IncludeNestedObjects);
            TestEqual(TEXT("One owned boundary control"),Controls.Num(),1);
            if (Controls.Num()==1)
            {
                TMap<FString,FString> Choices;
                const FString Prefix=Controls[0]->GetFunctionName()+TEXT(".Open Boundary ");
                for (const auto& Node:Controls[0]->GetNiagaraGraph()->Nodes)
                    for (const auto* Pin:Node->Pins)
                        if (Pin->Direction==EGPD_Input && Pin->LinkedTo.IsEmpty() && Pin->PinName.ToString().StartsWith(Prefix))
                            Choices.Add(Pin->PinName.ToString().RightChop(Prefix.Len()),Pin->DefaultValue);
                for (const TCHAR* Face:{TEXT("Right"),TEXT("Left"),TEXT("Back"),TEXT("Up"),TEXT("Front")})
                    TestEqual(Face,Choices.FindRef(Face),FString(TEXT("true")));
                TestEqual(TEXT("Bottom closed"),Choices.FindRef(TEXT("Down")),FString(TEXT("false")));
            }
        }
        if (WetState)
        {
            int32 Count=0;
            for (const FName Name:{FName(TEXT("User.River Initial Positions")),FName(TEXT("User.River Initial Velocities"))})
            {
                const FNiagaraVariable V(FNiagaraTypeDefinition(UNiagaraDataInterfaceArrayFloat3::StaticClass()),Name);
                const auto* Array=Cast<UNiagaraDataInterfaceArrayFloat3>(Candidate->GetExposedParameters().GetDataInterface(V));
                if (!TestNotNull(TEXT("Initial-state vector array"),Array)) continue;
                if (Count) TestEqual(TEXT("Matching initial position and velocity counts"),Array->InternalFloatData.Num(),Count);
                Count=Array->InternalFloatData.Num();
                TestTrue(TEXT("Fits inherited initial burst"),Count>0 && Count<=163840);
            }
        }
        for (const FName Name:{FName(TEXT("User.River Source Positions")),FName(TEXT("User.River Source Velocities"))})
        {
            const FNiagaraVariable V(FNiagaraTypeDefinition(UNiagaraDataInterfaceArrayFloat3::StaticClass()),Name);
            const auto* Actual=Cast<UNiagaraDataInterfaceArrayFloat3>(Candidate->GetExposedParameters().GetDataInterface(V));
            const auto* Original=Cast<UNiagaraDataInterfaceArrayFloat3>(Baseline->GetExposedParameters().GetDataInterface(V));
            TestTrue(TEXT("Saved source vectors unchanged"),Original && Original->InternalFloatData==OriginalSources[Name]);
            if (CenteredSources)
            {
                const auto& Rows=CenteredSources->GetArrayField(Name==FName(TEXT("User.River Source Positions"))
                    ? TEXT("positions_world_offset_cm") : TEXT("velocities_world_cm_per_s"));
                TArray<FVector3f> Expected;
                for (const auto& Row:Rows)
                {
                    const auto& XYZ=Row->AsArray();
                    if (!TestEqual(TEXT("Native source row has XYZ"),XYZ.Num(),3)) return false;
                    Expected.Add(FVector3f(float(XYZ[0]->AsNumber()),float(XYZ[1]->AsNumber()),float(XYZ[2]->AsNumber())));
                }
                TestTrue(TEXT("Recentered source vectors exactly match selected captured profile"),Actual && Actual->InternalFloatData==Expected);
            }
            else TestTrue(TEXT("Prescribed source vectors unchanged"),Actual && Original && Actual->InternalFloatData==Original->InternalFloatData);
        }
    }
    // Last variant is the clock-only, single-distance-grid candidate. Exercise
    // the real secondary installer without changing the saved source asset.
    IConsoleManager::Get().ProcessUserConsoleInput(TEXT("RaftSim.LiquidSecondaryReview shared-surface"),*GLog,World);
    auto* SecondarySystem=Component->GetAsset();
    int32 EnabledSecondary=0;
    for (const auto& Handle:SecondarySystem->GetEmitterHandles())
        if (Handle.GetName()==TEXT("Grid3D_FLIP_Secondary_Emitter"))
        {
            EnabledSecondary+=Handle.GetIsEnabled();
            const auto* Data=Handle.GetInstance().GetEmitterData();
            TestEqual(TEXT("Secondary GPU safety budget"),Data->MaxGPUParticlesSpawnPerFrame,2048);
            int32 Renderers=0;for (const auto* R:Data->GetRenderers()) Renderers+=R->GetIsEnabled();
            TestEqual(TEXT("Exactly one secondary sprite renderer"),Renderers,1);
            TArray<UNiagaraScript*> Scripts;Data->GetScripts(Scripts,false);int32 GPU=0;
            for (const auto* Script:Scripts) if (Script->GetUsage()==ENiagaraScriptUsage::ParticleGPUComputeScript)
            {
                ++GPU;TestTrue(TEXT("Secondary GPU shader compiled"),Script->DidScriptCompilationSucceed(true));
                const auto& Hlsl=Script->GetVMExecutableData().LastHlslTranslationGPU;
                for (const TCHAR* Marker:{TEXT("RiverMetricSecondaryCurl"),TEXT("RiverSurfaceEmissionRate"),TEXT("RiverSecondaryWorldVelocity"),TEXT("RiverSecondaryTimeIntegration")})
                    TestTrue(Marker,Hlsl.Contains(Marker));
                TestTrue(TEXT("Shared renderer field read in actual GPU program"),Hlsl.Contains(TEXT("RiverSharedSecondarySurface")) && Hlsl.Contains(TEXT("SampleRenderTargetValue_User_RiverSecondarySurface")));
                TestTrue(TEXT("GPU surface clock recorded"),Hlsl.Contains(TEXT("RiverSurfaceAge")));
                if (FParse::Param(FCommandLine::Get(),TEXT("RaftSimLiquidSecondaryExactContact")))
                {
                    TestTrue(TEXT("Exact secondary sweep executes in compiled GPU program"),Hlsl.Contains(TEXT("RiverSecondaryExactTerrainSweep")));
                    TestTrue(TEXT("Physical boundary parameter survives compilation"),Hlsl.Contains(TEXT("RiverSecondaryPhysicalExtents")));
                }
                if (FParse::Param(FCommandLine::Get(),TEXT("RaftSimLiquidSecondaryEndpointPrediction")))
                    TestTrue(TEXT("Endpoint phase prediction executes in compiled GPU program"),Hlsl.Contains(TEXT("RiverSecondaryEndpointPrediction")));
                if (FParse::Param(FCommandLine::Get(),TEXT("RaftSimLiquidSecondaryCurrentSurface")))
                    TestTrue(TEXT("Current-surface stage DI executes in compiled GPU program"),Hlsl.Contains(TEXT("RiverSecondaryCurrentSurfaceStage")) && Hlsl.Contains(TEXT("RiverCurrentSurfaceStage_Ready")));
            }
            TestEqual(TEXT("One actual compiled secondary GPU program"),GPU,1);
            TArray<FNiagaraVariableBase> Attributes;Data->GatherCompiledParticleAttributes(Attributes);
            // Executable dataset attributes have their Particles namespace
            // stripped (as do SimCache's Position and Velocity attributes).
            for (const TCHAR* Attribute:{TEXT("RiverSurfaceAge"),TEXT("RiverSurfacePhi")})
                TestTrue(Attribute,Attributes.ContainsByPredicate([&](const FNiagaraVariableBase& V)
                    {return V.GetName()==Attribute && V.GetType()==FNiagaraTypeDefinition::GetFloatDef();}));
        }
    TestEqual(TEXT("Existing secondary emitter enabled"),EnabledSecondary,1);
    if (FParse::Param(FCommandLine::Get(),TEXT("RaftSimLiquidSecondaryExactContact")))
    {
        const FNiagaraVariable Bounds(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.RiverSecondaryPhysicalExtents"));
        TestTrue(TEXT("Exact contact installs explicit physical bounds"),SecondarySystem->GetExposedParameters().IndexOf(Bounds)!=INDEX_NONE);
        const auto Physical=SecondarySystem->GetExposedParameters().GetParameterValue<FVector3f>(Bounds);
        TestTrue(TEXT("21m physical domain excludes the computational halo"),Physical.Equals(FVector3f(2100,2100,800),.001f));
    }
    auto* Surface=Cast<UNiagaraDataInterfaceRenderTargetVolume>(SecondarySystem->GetExposedParameters().GetDataInterface(RaftSimLiquidSecondarySurface::Variable()));
    if (TestNotNull(TEXT("Owned read-only secondary surface history"),Surface))
    {
        TestEqual(TEXT("Same rendering resolution"),Surface->Size,FIntVector(136,136,48));
        TestEqual(TEXT("RGBA preserves distance and clock"),Surface->OverrideRenderTargetFormat.GetValue(),RTF_RGBA16f);
    }
    const FString& SpawnHlsl=SecondarySystem->GetSystemSpawnScript()->GetVMExecutableData().LastHlslTranslation;
    FRegexMatcher Budget(FRegexPattern(TEXT("int (\\w+) = 2048;\\s+Context\\.Map\\.[^\\r\\n]*MaxSecondaryParticlesPerFrame = \\1;")),SpawnHlsl);
    TestTrue(TEXT("Compiled request matches budget, not the inherited 10000 batch"),Budget.FindNext());
    Actor->Destroy();
    TestEqual(TEXT("Saved source package not dirtied"),Baseline->GetOutermost()->IsDirty(),WasDirty);
    // Compilation/ownership is not a claim of physical or visual acceptance.
    return true;
}
