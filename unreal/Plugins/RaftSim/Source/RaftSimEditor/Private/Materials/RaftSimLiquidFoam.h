#pragma once
#include "NiagaraNodeAssignment.h"
#include "NiagaraDataInterfaceRenderTargetVolume.h"
#include "NiagaraDataInterfaceGrid3DCollection.h"
#include "NiagaraScriptVariable.h"
#include "ViewModels/Stack/NiagaraStackGraphUtilities.h"
#include "Engine/TextureRenderTarget2D.h"
#include "UObject/UObjectHash.h"

namespace RaftSimLiquidFoam
{
// A surface-aeration model, not a resolved two-phase air/water solver. Quantities
// use the same local cm and seconds as the actual 3D velocity field.
inline FString EvolutionHlsl()
{
    return TEXT(
        "// AdvectedRiverFoam: read previous SimRT only in stage16; stage17 writes it.\n"
        "Foam=0; int nx,ny,nz,ix,iy,iz; Sdf.GetNumCells(nx,ny,nz); Sdf.ExecutionIndexToGridIndex(ix,iy,iz);\n"
        "float3 unit=(float3(ix,iy,iz)+0.5)/float3(nx,ny,nz); float phi;\n"
        "Sdf.GetPreviousFloatValue<Attribute=\"SDF\">(ix,iy,iz,phi);\n"
        "float cell=max(Extents.x/nx,max(Extents.y/ny,Extents.z/nz));\n"
        "if(abs(phi)<3*cell && DeltaTime>0) {\n"
        " float3 velocity; Flow.SamplePreviousGridVector3Value<Attribute=\"Velocity\">(unit,velocity);\n"
        " float3 previousUnit=unit-velocity*DeltaTime/Extents; float oldFoam=0;\n"
        " if(Age>1.5*DeltaTime && all(previousUnit>0) && all(previousUnit<1)) {\n"
        "  float4 previous; History.SampleRenderTargetValue(previousUnit,0,previous); oldFoam=isfinite(previous.g)?saturate(previous.g):0; }\n"
        " int vx,vy,vz; Flow.GetNumCells(vx,vy,vz); float3 du=1.0/float3(vx,vy,vz);\n"
        " float3 xp,xm,yp,ym,zp,zm;\n"
        " Flow.SamplePreviousGridVector3Value<Attribute=\"Velocity\">(unit+float3(du.x,0,0),xp);\n"
        " Flow.SamplePreviousGridVector3Value<Attribute=\"Velocity\">(unit-float3(du.x,0,0),xm);\n"
        " Flow.SamplePreviousGridVector3Value<Attribute=\"Velocity\">(unit+float3(0,du.y,0),yp);\n"
        " Flow.SamplePreviousGridVector3Value<Attribute=\"Velocity\">(unit-float3(0,du.y,0),ym);\n"
        " Flow.SamplePreviousGridVector3Value<Attribute=\"Velocity\">(unit+float3(0,0,du.z),zp);\n"
        " Flow.SamplePreviousGridVector3Value<Attribute=\"Velocity\">(unit-float3(0,0,du.z),zm);\n"
        " float3 dx=(xp-xm)/(2*du.x*Extents.x),dy=(yp-ym)/(2*du.y*Extents.y),dz=(zp-zm)/(2*du.z*Extents.z);\n"
        " float curl=length(float3(dy.z-dz.y,dz.x-dx.z,dx.y-dy.x));\n"
        " float compression=max(-(dx.x+dy.y),0);\n"
        " float surfaceBand=saturate(1-abs(phi)/(2*cell));\n"
        " float3 physical=abs((unit-0.5)*Extents);\n"
        " float edge=saturate((1050-max(physical.x,physical.y))/(2*max(du.x*Extents.x,du.y*Extents.y)));\n"
        " int3 bindex=clamp(int3(unit*float3(vx,vy,vz)),int3(0,0,0),int3(vx,vy,vz)-1);\n"
        " float4 boundary; Boundary.GetPreviousVector4Value<Attribute=\"SolidVelocity_Boundary\">(bindex.x,bindex.y,bindex.z,boundary);\n"
        " float rate=surfaceBand*edge*saturate((length(velocity)-50)/150)*\n"
        "  (max(curl-1.2,0)*0.35+max(compression-0.8,0)*0.5);\n"
        " if(round(boundary.w)==1) rate=0;\n"
        " rate=min(rate,8.0); float totalRate=rate+0.25; float equilibrium=rate/totalRate;\n"
        " Foam=saturate(equilibrium+(oldFoam-equilibrium)*exp(-totalRate*DeltaTime));\n"
        "}\n");
}

inline bool Connect(UNiagaraNodeFunctionCall* Call,FName ModuleName,UEdGraphPin* Source)
{
    const auto* Input=Call->GetCalledGraph()->GetScriptVariable(ModuleName);
    if (!Input || !Source) { UE_LOG(LogTemp,Error,TEXT("Foam missing input %s on %s"),*ModuleName.ToString(),*Call->GetFunctionName());return false; }
    const auto Alias=FNiagaraParameterHandle::CreateAliasedModuleParameterHandle(ModuleName,FName(*Call->GetFunctionName()));
    auto& Pin=FNiagaraStackGraphUtilities::GetOrCreateStackFunctionInputOverridePin(*Call,Alias,
        Input->Variable.GetType(),Input->Metadata.GetVariableGuid(),FGuid());
    Pin.BreakAllPinLinks();Pin.MakeLinkTo(Source);
    CastChecked<UNiagaraNode>(Pin.GetOwningNode())->MarkNodeRequiresSynchronization(TEXT("Explicit foam data flow"),true);
    return true;
}

inline bool Install(UNiagaraSystem* System,const TSet<UNiagaraGraph*>& Graphs,
    TFunctionRef<UEdGraphPin*(UEdGraphPin*,const FNiagaraVariable&)> CloneRead,
    bool NativeEvolution=true)
{
    // The inherited SDF-only volume is R16f: green writes silently disappear.
    // Allocate real RGBA storage before compile/activation so history survives.
    TArray<UObject*> Children;GetObjectsWithOuter(System,Children,EGetObjectsFlags::IncludeNestedObjects);
    int32 Volumes=0;
    for (auto* Child:Children)
        if (auto* Volume=Cast<UNiagaraDataInterfaceRenderTargetVolume>(Child))
        {
            if (Volume->bInheritUserParameterSettings) return false;
            Volume->bOverrideFormat=true;Volume->OverrideRenderTargetFormat=RTF_RGBA16f;
            Volume->OverrideRenderTargetFilter=TF_Bilinear;++Volumes;
        }
    if (Volumes==0) return false;
    struct FAssignment { UNiagaraNodeAssignment* Call;UEdGraphPin* Anchor;int32 Axis; };
    TArray<FAssignment> Assignments;UNiagaraNodeFunctionCall* Output=nullptr;int32 Outputs=0;
    for (auto* Graph:Graphs)
    {
        if (!Graph || !Graph->IsIn(System)) return false;
        for (const auto& Node:Graph->Nodes)
        {
            if (auto* Call=Cast<UNiagaraNodeFunctionCall>(Node);Call && Call->GetFunctionName()==TEXT("Grid3D_SetRTValues")) { Output=Call;++Outputs; }
            auto* Assignment=Cast<UNiagaraNodeAssignment>(Node);
            if (!Assignment || Assignment->FindAssignmentTarget(TEXT("Emitter.SDFGrid.SDF"))==INDEX_NONE) continue;
            const FString Target=Assignment->GetFunctionName()+TEXT(".Emitter.SDFGrid.SDF");
            for (const auto& N:Graph->Nodes) for (auto* P:N->Pins)
                if (P->Direction==EGPD_Input && P->PinName.ToString()==Target && P->LinkedTo.Num()==1)
                {
                    auto* Anchor=P->LinkedTo[0];const FString Name=Anchor->PinName.ToString();
                    if (!Name.Contains(TEXT("ConvolvedValue"))) continue;
                    // Engine template names are not ordered: unsuffixed is Y,
                    // 001 is X, 002 is Z. Generate after X has produced current SDF.
                    const int32 Axis=Name.Contains(TEXT("ConvolveAxis002"))?2:Name.Contains(TEXT("ConvolveAxis001"))?0:1;
                    Assignments.Add({Assignment,Anchor,Axis});
                }
        }
    }
    if (Assignments.Num()!=3 || Outputs!=1) { UE_LOG(LogTemp,Error,TEXT("Foam expected three surface assignments/one output, got%d/%d"),Assignments.Num(),Outputs);return false; }
    TSet<int32> Axes;UEdGraphPin* FinalFoam=nullptr;
    const auto Float=FNiagaraTypeDefinition::GetFloatDef();
    const FNiagaraVariable Foam(Float,TEXT("Emitter.SDFGrid.RiverFoam"));
    const FNiagaraTypeDefinition Grid(UNiagaraDataInterfaceGrid3DCollection::StaticClass());
    const FNiagaraTypeDefinition Volume(UNiagaraDataInterfaceRenderTargetVolume::StaticClass());
    for (const auto& A:Assignments)
    {
        if (Axes.Contains(A.Axis)) return false;Axes.Add(A.Axis);
        // The independent live GPU pass owns foam history. Keep the native
        // distance grid single-attribute so secondary grid readers use the
        // same RGBA layout. Preserve an upstream read anchor for the clock.
        if (!NativeEvolution) { FinalFoam=A.Anchor;continue; }
        A.Call->FunctionScript=DuplicateObject<UNiagaraScript>(A.Call->FunctionScript,System,
            FName(*FString::Printf(TEXT("RiverFoamSurfaceAssignment%d"),A.Axis)));
        A.Call->AddParameter(Foam,TEXT("0"));
        UEdGraphPin* Value=nullptr;
        if (A.Axis==1)
        {
            auto* Graph=A.Call->GetNiagaraGraph();auto* Node=NewObject<UNiagaraNodeCustomHlsl>(Graph);
            Node->CreateNewGuid();Graph->AddNode(Node,false,false);Node->ScriptUsage=ENiagaraScriptUsage::Function;
            Node->Signature.Name=TEXT("AdvectAndGenerateRiverFoam");
            Node->Signature.Inputs={FNiagaraVariable(Grid,TEXT("Sdf")),FNiagaraVariable(Grid,TEXT("Flow")),
                FNiagaraVariable(Volume,TEXT("History")),FNiagaraVariable(Grid,TEXT("Boundary")),
                FNiagaraVariable(Float,TEXT("DeltaTime")),FNiagaraVariable(Float,TEXT("Age")),
                FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("Extents"))};
            Node->Signature.Outputs={FNiagaraVariable(Float,TEXT("Foam"))};
            FindFProperty<FStrProperty>(Node->GetClass(),TEXT("CustomHlsl"))->SetPropertyValue_InContainer(Node,EvolutionHlsl());
            Node->AllocateDefaultPins();
            const FNiagaraVariable Reads[]={FNiagaraVariable(Grid,TEXT("Emitter.SDFGrid")),FNiagaraVariable(Grid,TEXT("Emitter.SimGrid")),
                FNiagaraVariable(Volume,TEXT("Emitter.SimRT")),FNiagaraVariable(Grid,TEXT("Emitter.TransientGrid")),
                FNiagaraVariable(Float,TEXT("Engine.DeltaTime")),FNiagaraVariable(Float,TEXT("Emitter.Age")),
                FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.World Grid Extents"))};
            for (int32 I=0;I<7;++I)
            {
                auto* Read=CloneRead(A.Anchor,Reads[I]);if (!Read) return false;
                Node->FindPin(Node->Signature.Inputs[I].GetName(),EGPD_Input)->MakeLinkTo(Read);
            }
            Node->MarkNodeRequiresSynchronization(TEXT("Read previous volume before output stage, advect and decay surface foam"),true);
            Value=Node->FindPin(TEXT("Foam"),EGPD_Output);
        }
        else Value=CloneRead(A.Anchor,Foam);
        if (!Connect(A.Call,TEXT("Module.Emitter.SDFGrid.RiverFoam"),Value)) return false;
        if (A.Axis==2) FinalFoam=Value;
        A.Call->MarkNodeRequiresSynchronization(TEXT("Carry independent foam through surface smoothing stages"),true);
        if (A.Axis>0)
        {
            // Adding an attribute may move SDF away from slot zero. The stock
            // Y/Z convolution takes a numeric slot; resolve SDF by name instead.
            auto* Graph=A.Call->GetNiagaraGraph();
            const FString ConvolveName=A.Axis==1?TEXT("Grid3D_ConvolveAxis"):TEXT("Grid3D_ConvolveAxis002");
            UNiagaraNodeFunctionCall* Convolve=nullptr;
            for (const auto& N:Graph->Nodes)
                if (auto* C=Cast<UNiagaraNodeFunctionCall>(N);C && C->GetFunctionName()==ConvolveName) Convolve=C;
            if (!Convolve) return false;
            auto* Index=NewObject<UNiagaraNodeCustomHlsl>(Graph);
            Index->CreateNewGuid();Graph->AddNode(Index,false,false);Index->ScriptUsage=ENiagaraScriptUsage::Function;
            Index->Signature.Name=TEXT("ResolveSurfaceDistanceAttribute");
            Index->Signature.Inputs={FNiagaraVariable(Grid,TEXT("Sdf"))};
            Index->Signature.Outputs={FNiagaraVariable(FNiagaraTypeDefinition::GetIntDef(),TEXT("Index"))};
            FindFProperty<FStrProperty>(Index->GetClass(),TEXT("CustomHlsl"))->SetPropertyValue_InContainer(Index,
                TEXT("Sdf.GetFloatAttributeIndex<Attribute=\"SDF\">(Index);"));
            Index->AllocateDefaultPins();
            auto* Read=CloneRead(A.Anchor,FNiagaraVariable(Grid,TEXT("Emitter.SDFGrid")));if (!Read) return false;
            // The anchor reads the convolution OUTPUT. An input of that same
            // convolution must instead read its upstream map, or a graph cycle
            // causes the Niagara compiler to recurse indefinitely.
            UEdGraphPin* Upstream=nullptr;
            for (auto* Pin:Convolve->Pins)
                if (Pin->Direction==EGPD_Input && Pin->PinType.PinSubCategoryObject==FNiagaraTypeDefinition::GetParameterMapDef().GetStruct() && Pin->LinkedTo.Num()==1)
                    Upstream=Pin->LinkedTo[0];
            if (!Upstream) return false;
            // GetOrCreateStackFunctionInputOverridePin reuses the parameter-map
            // set immediately before the module. Reading its output and then
            // writing an override into it is still a cycle; bypass that set.
            if (Upstream->GetOwningNode()->GetClass()->GetName()==TEXT("NiagaraNodeParameterMapSet"))
            {
                UEdGraphPin* BeforeOverrides=nullptr;
                for (auto* Pin:Upstream->GetOwningNode()->Pins)
                    if (Pin->Direction==EGPD_Input && Pin->PinType.PinSubCategoryObject==FNiagaraTypeDefinition::GetParameterMapDef().GetStruct() && Pin->LinkedTo.Num()==1)
                        BeforeOverrides=Pin->LinkedTo[0];
                if (!BeforeOverrides) return false;Upstream=BeforeOverrides;
            }
            for (auto* Pin:Read->GetOwningNode()->Pins)
                if (Pin->Direction==EGPD_Input && Pin->PinType.PinSubCategoryObject==FNiagaraTypeDefinition::GetParameterMapDef().GetStruct())
                { Pin->BreakAllPinLinks();Pin->MakeLinkTo(Upstream); }
            Index->FindPin(TEXT("Sdf"),EGPD_Input)->MakeLinkTo(Read);
            Index->MarkNodeRequiresSynchronization(TEXT("Never convolve foam as surface distance"),true);
            if (!Connect(Convolve,TEXT("Module.AttributeIndex"),Index->FindPin(TEXT("Index"),EGPD_Output))) return false;
        }
    }
    if (NativeEvolution)
    {
        if (!Connect(Output,TEXT("Module.Green"),FinalFoam)) return false;
    }
    else
    {
        const auto* Input=Output->GetCalledGraph()->GetScriptVariable(TEXT("Module.Green"));
        if (!Input) return false;
        const auto Alias=FNiagaraParameterHandle::CreateAliasedModuleParameterHandle(TEXT("Module.Green"),FName(*Output->GetFunctionName()));
        auto& Pin=FNiagaraStackGraphUtilities::GetOrCreateStackFunctionInputOverridePin(*Output,Alias,
            Input->Variable.GetType(),Input->Metadata.GetVariableGuid(),FGuid());
        Pin.BreakAllPinLinks();Pin.DefaultValue=TEXT("0");
        CastChecked<UNiagaraNode>(Pin.GetOwningNode())->MarkNodeRequiresSynchronization(TEXT("Independent GPU pass owns foam"),true);
    }
    // Carry the actual simulated emitter age alongside the surface. Splitting
    // whole/fractional seconds avoids the coarse age quantization of one half.
    // B/A are metadata; the optical candidate derives normals from SDF.r.
    auto* Clock=NewObject<UNiagaraNodeCustomHlsl>(Output->GetNiagaraGraph());
    Clock->CreateNewGuid();Output->GetNiagaraGraph()->AddNode(Clock,false,false);
    Clock->ScriptUsage=ENiagaraScriptUsage::Function;Clock->Signature.Name=TEXT("RiverSurfaceSimulationClock");
    Clock->Signature.Inputs={FNiagaraVariable(Float,TEXT("Age"))};
    Clock->Signature.Outputs={FNiagaraVariable(Float,TEXT("Whole")),FNiagaraVariable(Float,TEXT("Fraction"))};
    FindFProperty<FStrProperty>(Clock->GetClass(),TEXT("CustomHlsl"))->SetPropertyValue_InContainer(Clock,
        // Quantize to an exactly representable binary half value before the
        // native typed UAV store, which truncates arbitrary fractions on D3D12.
        TEXT("Whole=floor(Age); Fraction=round((Age-Whole)*2048.0)*(1.0/2048.0);"));
    Clock->AllocateDefaultPins();
    auto* AgeRead=CloneRead(FinalFoam,FNiagaraVariable(Float,TEXT("Emitter.Age")));
    if (!AgeRead) return false;
    Clock->FindPin(TEXT("Age"),EGPD_Input)->MakeLinkTo(AgeRead);
    Clock->MarkNodeRequiresSynchronization(TEXT("Actual GPU surface simulation time, not render frame time"),true);
    if (!Connect(Output,TEXT("Module.Blue"),Clock->FindPin(TEXT("Whole"),EGPD_Output)) ||
        !Connect(Output,TEXT("Module.Alpha"),Clock->FindPin(TEXT("Fraction"),EGPD_Output))) return false;
    Output->MarkNodeRequiresSynchronization(TEXT("Actual advected foam in surface volume green channel"),true);
    // Fail before Niagara's recursive history builder if a future template edit
    // creates a back-edge. Traversal follows only data inputs, not graph layout.
    for (auto* Graph:Graphs)
    {
        TMap<UEdGraphNode*,uint8> Colors;
        TFunction<bool(UEdGraphNode*)> Acyclic=[&](UEdGraphNode* Node)
        {
            if (Colors.FindRef(Node)==1) { UE_LOG(LogTemp,Error,TEXT("Foam graph cycle at %s"),*Node->GetName());return false; }
            if (Colors.FindRef(Node)==2) return true;
            Colors.Add(Node,1);
            for (auto* Pin:Node->Pins) if (Pin->Direction==EGPD_Input)
                for (auto* Link:Pin->LinkedTo) if (!Acyclic(Link->GetOwningNode())) return false;
            Colors.Add(Node,2);return true;
        };
        for (const auto& Node:Graph->Nodes) if (!Acyclic(Node.Get())) return false;
    }
    return true;
}
}
