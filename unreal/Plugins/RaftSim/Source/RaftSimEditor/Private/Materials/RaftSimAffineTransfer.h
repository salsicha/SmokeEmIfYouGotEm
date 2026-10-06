#pragma once
#include "NiagaraNodeAssignment.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "RaftSimCompatibleAdvection.h"

// Isolated collocated adaptation of APIC fluid transfers (Jiang et al. 2015,
// equations 13-14). C columns map grid-local cm displacement to world cm/s.
// No extra force, turbulence noise, FLIP increment, or changed river boundary.
namespace RaftSimAffineTransfer
{
inline FString GatherHlsl(bool Quadratic=false,bool CompatibleAdvection=false)
{
    FString Code=TEXT(
        "// RiverAffineGridToParticle: exact trilinear value and derivatives.\n"
        "SamplePosition=Position;AffineX=0;AffineY=0;AffineZ=0;NewVelocity=OldVelocity;NewPosition=Position+OldVelocity*DeltaTime;\n"
        "int nx,ny,nz; Flow.GetNumCells(nx,ny,nz);int3 size=int3(nx,ny,nz);\n"
        "float3 unit=mul(float4(Position,1),WorldToUnit).xyz;SampleUnit=unit;float3 q=unit*float3(size)-0.5;\n"
        "int3 low=int3(floor(q));float3 t=q-float3(low);\n"
        "int3 parent=clamp(int3(unit*size),0,size-1);float4 boundary;\n"
        "Boundary.GetPreviousVector4Value<Attribute=\"SolidVelocity_Boundary\">(parent.x,parent.y,parent.z,boundary);\n"
        "if(all(low>=0) && all(low+1<size) && round(boundary.w)!=1) {\n"
        " float3 h=float3(length(UnitToWorld[0].xyz)/nx,length(UnitToWorld[1].xyz)/ny,length(UnitToWorld[2].xyz)/nz);\n"
        " float3 value=0;\n"
        " for(int z=0;z<2;++z) for(int y=0;y<2;++y) for(int x=0;x<2;++x) {\n"
        "  int3 bit=int3(x,y,z),i=low+bit;float3 v;Flow.GetPreviousVectorValue<Attribute=\"Velocity\">(i.x,i.y,i.z,v);\n"
        "  float3 world=v.x*normalize(UnitToWorld[0].xyz)+v.y*normalize(UnitToWorld[1].xyz)+v.z*normalize(UnitToWorld[2].xyz);\n"
        "  float3 w=lerp(1-t,t,float3(bit)),sign=2*float3(bit)-1;\n"
        "  value+=world*w.x*w.y*w.z;\n"
        "  AffineX+=world*(sign.x*w.y*w.z/h.x);AffineY+=world*(w.x*sign.y*w.z/h.y);AffineZ+=world*(w.x*w.y*sign.z/h.z);\n"
        " }\n"
        " NewVelocity=value;NewPosition=Position+value*DeltaTime;\n"
        "}\n");
    if (Quadratic)
    {
        Code.ReplaceInline(TEXT("exact trilinear value and derivatives."),TEXT("RiverQuadraticGridToParticle: quadratic value and APIC moment, not a point derivative."));
        Code.ReplaceInline(TEXT("floor(q)"),TEXT("floor(q-0.5)"));
        Code.ReplaceInline(TEXT("low+1<size"),TEXT("low+2<size"));
        for (const TCHAR* Axis:{TEXT("x"),TEXT("y"),TEXT("z")})
            Code.ReplaceInline(*FString::Printf(TEXT("%s<2"),Axis),*FString::Printf(TEXT("%s<3"),Axis));
        Code.ReplaceInline(TEXT("float3 w=lerp(1-t,t,float3(bit)),sign=2*float3(bit)-1;"),TEXT(
            "float3 r=float3(bit)-t,a=abs(r);float3 w;\n"
            "  for(int axis=0;axis<3;++axis) w[axis]=a[axis]<0.5?0.75-r[axis]*r[axis]:0.5*pow(max(1.5-a[axis],0),2);"));
        Code.ReplaceInline(TEXT("AffineX+=world*(sign.x*w.y*w.z/h.x);AffineY+=world*(w.x*sign.y*w.z/h.y);AffineZ+=world*(w.x*w.y*sign.z/h.z);"),TEXT(
            "float weight=w.x*w.y*w.z;\n"
            "  AffineX+=world*(4*weight*r.x/h.x);AffineY+=world*(4*weight*r.y/h.y);AffineZ+=world*(4*weight*r.z/h.z);"));
    }
    if (CompatibleAdvection) Code+=RaftSimCompatibleAdvectionHlsl();
    return Code;
}

inline bool Install(UNiagaraSystem* System,const TSet<UNiagaraGraph*>& Graphs,
    UNiagaraNodeFunctionCall* UpdateCall,TFunctionRef<UEdGraphPin*(UEdGraphPin*,const FNiagaraVariable&)> CloneRead)
{
    const auto Fail=[](const FString& Reason) { UE_LOG(LogTemp,Error,TEXT("Affine transfer: %s"),*Reason);return false; };
    const bool Quadratic=FParse::Param(FCommandLine::Get(),TEXT("RaftSimLiquidQuadraticTransfer"));
    const bool CompatibleAdvection=FParse::Param(FCommandLine::Get(),TEXT("RaftSimLiquidCompatibleAdvection"));
    if (CompatibleAdvection && !Quadratic) return Fail(TEXT("Compatible advection requires quadratic APIC control"));
    auto* Update=UpdateCall?UpdateCall->FunctionScript.Get():nullptr;
    if (!System || System->GetOutermost()!=GetTransientPackage() || !Update || !Update->IsIn(System)) return Fail(TEXT("System/update must be owned and transient"));
    const auto Vec=FNiagaraTypeDefinition::GetVec3Def();
    TArray<FNiagaraVariable> Attributes={FNiagaraVariable(Vec,TEXT("Particles.RiverAffineX")),
        FNiagaraVariable(Vec,TEXT("Particles.RiverAffineY")),FNiagaraVariable(Vec,TEXT("Particles.RiverAffineZ")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetPositionDef(),TEXT("Particles.RiverAffineSamplePosition")),
        FNiagaraVariable(Vec,TEXT("Particles.RiverAffineSampleUnit"))};
    TArray<FString> Defaults={TEXT("0,0,0"),TEXT("0,0,0"),TEXT("0,0,0"),TEXT("0,0,0"),TEXT("0,0,0")};
    if (CompatibleAdvection)
    {
        Attributes.Append({FNiagaraVariable(FNiagaraTypeDefinition::GetPositionDef(),TEXT("Particles.RiverAdvectedPosition")),
            FNiagaraVariable(Vec,TEXT("Particles.RiverAdvectedVelocity")),
            FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("Particles.RiverAdvectionStatus"))});
        Defaults.Append({TEXT("0,0,0"),TEXT("0,0,0"),TEXT("0")});
    }
    UNiagaraNodeOutput* Spawn=nullptr;int32 Spawns=0;
    UNiagaraNodeFunctionCall* Raster=nullptr;int32 Rasters=0;
    for(auto* Graph:Graphs) for(const auto& Node:Graph->Nodes)
    {
        if(auto* Output=Cast<UNiagaraNodeOutput>(Node);Output && Output->GetUsage()==ENiagaraScriptUsage::ParticleSpawnScript)
        { Spawn=Output;++Spawns; }
        if(auto* Call=Cast<UNiagaraNodeFunctionCall>(Node);Call && Call->FunctionScript &&
            Call->FunctionScript->GetName()==TEXT("TerrainGridFrameParticleTransfer")) { Raster=Call;++Rasters; }
    }
    if(Spawns!=1 || Rasters!=1) { UE_LOG(LogTemp,Error,TEXT("Affine transfer spawn/raster count %d/%d"),Spawns,Rasters);return false; }
    auto* Initialize=FNiagaraStackGraphUtilities::AddParameterModuleToStack(Attributes,*Spawn,0,Defaults);
    if(!Initialize) return Fail(TEXT("Could not initialize persistent affine attributes"));
    TArray<UObject*> Children;GetObjectsWithOuter(Raster->FunctionScript,Children,EGetObjectsFlags::IncludeNestedObjects);
    int32 Gathered=0;
    for(auto* Child:Children)
    {
        auto* Node=Cast<UNiagaraNodeCustomHlsl>(Child);if(!Node) continue;
        auto* Property=FindFProperty<FStrProperty>(Node->GetClass(),TEXT("CustomHlsl"));if(!Property) return Fail(TEXT("Missing custom HLSL property"));
        FString Code=Property->GetPropertyValue_InContainer(Node);
        if(!Code.Contains(TEXT("CenteredMetricParticleTransfer"))) continue;
        const FString Reader=RaftSimCompatibleProjection::InterfaceFor(Code,TEXT("GetVectorByIndex"));
        if(Reader.IsEmpty()) return Fail(TEXT("Centered raster has no vector particle reader"));
        FString Addition=TEXT(
            "// RiverAffineParticleToGrid: preserve local shear/rotation in P2G.\n"
            "float3 ax,ay,az;bool vx,vy,vz;\n"
            "READER.GetVectorByIndex<Attribute=\"RiverAffineX\">(ParticleIndex,vx,ax);\n"
            "READER.GetVectorByIndex<Attribute=\"RiverAffineY\">(ParticleIndex,vy,ay);\n"
            "READER.GetVectorByIndex<Attribute=\"RiverAffineZ\">(ParticleIndex,vz,az);\n"
            "float3 offset=World-CurrParticlePosition;\n"
            "float3 r=float3(dot(offset,normalize(UnitToWorld[0].xyz)),dot(offset,normalize(UnitToWorld[1].xyz)),dot(offset,normalize(UnitToWorld[2].xyz)));\n"
            "Velocity += (CurrParticleVelocity+ax*r.x+ay*r.y+az*r.z)*Weight;\n");
        Addition.ReplaceInline(TEXT("READER"),*Reader,ESearchCase::CaseSensitive);
        if(Code.ReplaceInline(TEXT("Velocity += CurrParticleVelocity * Weight;"),*Addition,ESearchCase::CaseSensitive)!=1) return Fail(TEXT("Expected exactly one centered velocity accumulation"));
        if (Quadratic && Code.ReplaceInline(TEXT("float3 W = saturate(1.0 - abs(IndexDifference));"),TEXT(
            "// RiverQuadraticParticleToGrid: matching C1 quadratic B-spline support.\n"
            "float3 a=abs(IndexDifference),W;\n"
            "for(int axis=0;axis<3;++axis) W[axis]=a[axis]<0.5?0.75-a[axis]*a[axis]:0.5*pow(max(1.5-a[axis],0),2);"),ESearchCase::CaseSensitive)!=1)
            return Fail(TEXT("Expected one verified tent basis for quadratic replacement"));
        Property->SetPropertyValue_InContainer(Node,Code);Node->MarkNodeRequiresSynchronization(TEXT("Affine P2G on centered metric support"),true);++Gathered;
    }
    if(Gathered!=1) return Fail(FString::Printf(TEXT("Expected one centered raster body, got %d"),Gathered));
    Raster->MarkNodeRequiresSynchronization(TEXT("Owned affine particle transfer"),true);
    // Follow the function call's selected version, not GetLatestSource(). The
    // stock caller pins an older version; editing latest silently leaves G2P
    // unchanged even though spawn and P2G compile the new attributes.
    const auto* UpdateSource=UpdateCall->GetFunctionScriptSource();
    if(!UpdateSource || !UpdateSource->NodeGraph || !UpdateSource->NodeGraph->IsIn(System)) return Fail(TEXT("Owned selected update graph missing"));
    UE_LOG(LogTemp,Display,TEXT("Affine G2P selected version %s source %s"),*UpdateCall->SelectedScriptVersion.ToString(),*UpdateSource->GetPathName());
    UNiagaraNodeCustomHlsl* Contact=nullptr;
    for(const auto& Child:UpdateSource->NodeGraph->Nodes) if(auto* Node=Cast<UNiagaraNodeCustomHlsl>(Child);Node && Node->Signature.Name==TEXT("ProjectTaggedTerrainContact"))
    { if(Contact) return Fail(TEXT("Multiple private terrain contact nodes"));Contact=Node; }
    if(!Contact) return Fail(TEXT("Private terrain contact node missing from owned update"));
    auto* Previous=Contact->FindPin(TEXT("PreviousPosition"),EGPD_Input);
    auto* VelocityInput=Contact->FindPin(TEXT("Velocity"),EGPD_Input);
    auto* PositionInput=Contact->FindPin(TEXT("Position"),EGPD_Input);
    auto* Projected=Contact->FindPin(TEXT("ProjectedPosition"),EGPD_Output);
    if(!Previous || Previous->LinkedTo.Num()!=1 || !VelocityInput || !PositionInput || !Projected || Projected->LinkedTo.Num()!=1) return Fail(TEXT("Contact input/output topology differs from expected single links"));
    auto* MapSet=Cast<UNiagaraNode>(Projected->LinkedTo[0]->GetOwningNode());
    if(!MapSet || MapSet->GetClass()->GetName()!=TEXT("NiagaraNodeParameterMapSet")) return Fail(FString::Printf(TEXT("Projected-position target is %s, expected parameter map set"),MapSet?*MapSet->GetClass()->GetName():TEXT("null")));
    auto* Graph=Contact->GetNiagaraGraph();auto* Node=NewObject<UNiagaraNodeCustomHlsl>(Graph);
    Node->CreateNewGuid();Graph->AddNode(Node,false,false);Node->ScriptUsage=ENiagaraScriptUsage::Function;
    Node->Signature.Name=TEXT("RiverAffineGridToParticle");
    const auto Grid=FNiagaraTypeDefinition(UNiagaraDataInterfaceGrid3DCollection::StaticClass());
    const auto Matrix=FNiagaraTypeDefinition::GetMatrix4Def();
    Node->Signature.Inputs={FNiagaraVariable(Grid,TEXT("Flow")),FNiagaraVariable(Grid,TEXT("Boundary")),
        FNiagaraVariable(Matrix,TEXT("WorldToUnit")),FNiagaraVariable(Matrix,TEXT("UnitToWorld")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetPositionDef(),TEXT("Position")),FNiagaraVariable(Vec,TEXT("OldVelocity")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("DeltaTime"))};
    Node->Signature.Outputs={FNiagaraVariable(FNiagaraTypeDefinition::GetPositionDef(),TEXT("NewPosition")),
        FNiagaraVariable(Vec,TEXT("NewVelocity")),FNiagaraVariable(Vec,TEXT("AffineX")),FNiagaraVariable(Vec,TEXT("AffineY")),FNiagaraVariable(Vec,TEXT("AffineZ")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetPositionDef(),TEXT("SamplePosition")),FNiagaraVariable(Vec,TEXT("SampleUnit"))};
    if (CompatibleAdvection) Node->Signature.Outputs.Append({
        FNiagaraVariable(FNiagaraTypeDefinition::GetPositionDef(),TEXT("AdvectedPosition")),
        FNiagaraVariable(Vec,TEXT("AdvectedVelocity")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("AdvectionStatus"))});
    FindFProperty<FStrProperty>(Node->GetClass(),TEXT("CustomHlsl"))->SetPropertyValue_InContainer(Node,GatherHlsl(Quadratic,CompatibleAdvection));Node->AllocateDefaultPins();
    const FNiagaraVariable Reads[]={FNiagaraVariable(Grid,TEXT("Emitter.SimGrid")),FNiagaraVariable(Grid,TEXT("Emitter.TransientGrid")),
        FNiagaraVariable(Matrix,TEXT("Emitter.WorldToUnit")),FNiagaraVariable(Matrix,TEXT("Emitter.UnitToWorld")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetPositionDef(),TEXT("Particles.Position")),FNiagaraVariable(Vec,TEXT("Particles.Velocity")),
        FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("Engine.DeltaTime"))};
    for(int32 I=0;I<7;++I)
    {
        auto* Read=CloneRead(Previous->LinkedTo[0],Reads[I]);if(!Read) return Fail(FString::Printf(TEXT("Could not clone parameter read %s"),*Reads[I].GetName().ToString()));
        Node->FindPin(Node->Signature.Inputs[I].GetName(),EGPD_Input)->MakeLinkTo(Read);
    }
    PositionInput->BreakAllPinLinks();PositionInput->MakeLinkTo(Node->FindPin(TEXT("NewPosition"),EGPD_Output));
    VelocityInput->BreakAllPinLinks();VelocityInput->MakeLinkTo(Node->FindPin(TEXT("NewVelocity"),EGPD_Output));
    for(int32 Axis=0;Axis<Attributes.Num();++Axis)
    {
        auto Type=UEdGraphSchema_Niagara::TypeDefinitionToPinType(Attributes[Axis].GetType());Type.PinSubCategory=Projected->LinkedTo[0]->PinType.PinSubCategory;
        auto* Pin=MapSet->CreatePin(EGPD_Input,Type,Attributes[Axis].GetName());
        Pin->MakeLinkTo(Node->FindPin(Node->Signature.Outputs[Axis+2].GetName(),EGPD_Output));
    }
    MapSet->MarkNodeRequiresSynchronization(TEXT("Persist affine state for next P2G"),true);
    Node->MarkNodeRequiresSynchronization(TEXT("Value and gradient of projected grid velocity"),true);
    Contact->MarkNodeRequiresSynchronization(TEXT("Terrain contact after affine advection"),true);
    UE_LOG(LogTemp,Display,TEXT("Affine transfer installed: three persistent C columns, quadratic-moment=%d, no FLIP increment; transient only"),Quadratic);
    return true;
}
}
