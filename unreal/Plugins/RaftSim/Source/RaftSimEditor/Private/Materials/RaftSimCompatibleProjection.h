#pragma once
#include "Internationalization/Regex.h"
#include "NiagaraDataInterfaceGrid3DCollection.h"
#include "RaftSimOutletStage.h"
#include "RaftSimLiquidPressureColoring.h"
#include "RaftSimLiquidRegionalProjection.h"

namespace RaftSimCompatibleProjection
{
inline FString InterfaceFor(const FString& Code,const FString& Method)
{
    FRegexMatcher Match(FRegexPattern(TEXT("\\b([A-Za-z_][A-Za-z0-9_]*)\\.")+Method),Code);
    return Match.FindNext()?Match.GetCaptureGroup(1):FString();
}

inline bool Install(UNiagaraSystem* System,const TSet<UNiagaraGraph*>& Graphs,
    TFunctionRef<UEdGraphPin*(UEdGraphPin*,const FNiagaraVariable&)> CloneRead,bool OutletStage=false,
    const RaftSimLiquidRegionalProjection::FLayout* Regional=nullptr)
{
    // Regional outlet queries use the validated read-only PARENT face table,
    // with local indices shifted into its grid. No internal region face is a
    // pressure reservoir. The legacy fixture keeps its original table/query.
    int32 Divergences=0,Pressures=0,Gradients=0,Colorings=0,Extrapolations=0;
    for (auto* Graph:Graphs)
        for (const auto& Item:Graph->Nodes)
        {
            auto* Call=Cast<UNiagaraNodeFunctionCall>(Item);
            if (!Call || !Call->FunctionScript) continue;
            const FString Name=Call->FunctionScript->GetName();
            const bool Div=Name==TEXT("Grid3D_ComputeDivergence");
            const bool Pressure=Name==TEXT("Grid3D_PressureIteration");
            // The unsuffixed gradient is the pressure stage; verify its binding.
            const bool Grad=Name==TEXT("Grid3D_ComputeGradient") && Call->GetFunctionName()==TEXT("Grid3D_ComputeGradient");
            const bool Extrapolate=Name==TEXT("Grid3D_ExtrapolateVelocity") && Call->GetFunctionName()==TEXT("Grid3D_ExtrapolateVelocity001");
            if (!Div && !Pressure && !Grad && !Extrapolate) continue;
            if (Grad)
            {
                bool PressureInput=false;
                for (const auto& N:Graph->Nodes) for (const auto* P:N->Pins)
                    if (P->Direction==EGPD_Input && P->PinName.ToString()==Call->GetFunctionName()+TEXT(".Grid") &&
                        P->LinkedTo.Num()==1 && P->LinkedTo[0]->PinName.ToString().Contains(TEXT("PressureGrid"))) PressureInput=true;
                if (!PressureInput) { UE_LOG(LogTemp,Error,TEXT("Compatible projection: pressure gradient binding not verified"));return false; }
            }
            auto* Owned=DuplicateObject<UNiagaraScript>(Call->FunctionScript,System,
                FName(*(TEXT("Compatible_")+Call->GetFunctionName())));
            TArray<UNiagaraNodeCustomHlsl*> Nodes;
            ForEachObjectWithOuter(Owned,[&](UObject* O){if(auto* N=Cast<UNiagaraNodeCustomHlsl>(O)) Nodes.Add(N);},EGetObjectsFlags::IncludeNestedObjects);
            for (auto* Node:Nodes)
            {
                auto* Property=FindFProperty<FStrProperty>(Node->GetClass(),TEXT("CustomHlsl"));
                if (!Property) return false;
                const FString Original=Property->GetPropertyValue_InContainer(Node);
                FString Code;
                UEdGraphPin* MetricSource=nullptr;
                if (Extrapolate && Original.Contains(TEXT("TotalWeight")) && Original.Contains(TEXT("GetPreviousVector4Value")) && Node->FindPin(TEXT("Velocity"),EGPD_Input) && Node->FindPin(TEXT("OutVelocity"),EGPD_Output))
                {
                    const FString B=InterfaceFor(Original,TEXT("GetPreviousVector4Value"));
                    if (B.IsEmpty() || !Node->FindPin(TEXT("Velocity"),EGPD_Input))
                    { UE_LOG(LogTemp,Error,TEXT("Compatible extrapolation interface mismatch: %s"),*Original);return false; }
                    Code=Original+TEXT("\n// CompatiblePreserveProjectedSupport: extrapolate only outside the pressure stencil.\n"
                        "#if GPU_SIMULATION\nint3 p=int3(IndexX,IndexY,IndexZ);\n"
                        "for(int axis=0;axis<3;++axis) { int3 e=int3(axis==0,axis==1,axis==2); float4 bm,bp;\n"
                        "BGRID.GetPreviousVector4Value<Attribute=\"SolidVelocity_Boundary\">(p.x-e.x,p.y-e.y,p.z-e.z,bm);\n"
                        "BGRID.GetPreviousVector4Value<Attribute=\"SolidVelocity_Boundary\">(p.x+e.x,p.y+e.y,p.z+e.z,bp);\n"
                        "if(round(Boundary)==1 || round(bm.w)==0 || round(bp.w)==0) OutVelocity[axis]=Velocity[axis]; }\n#endif\n");
                    Code.ReplaceInline(TEXT("BGRID"),*B);++Extrapolations;
                }
                else if (Div && Original.Contains(TEXT("Vx_right")) && Node->FindPin(TEXT("Div"),EGPD_Output))
                {
                    const FString Grid=InterfaceFor(Original,TEXT("GetGridValue"));
                    auto* Input=Node->FindPin(FName(*Grid),EGPD_Input);
                    if (Grid.IsEmpty() || !Input || Input->LinkedTo.Num()!=1) return false;
                    MetricSource=Input->LinkedTo[0];
                    const FNiagaraTypeDefinition Type(UNiagaraDataInterfaceGrid3DCollection::StaticClass());
                    auto* Read=CloneRead(Input->LinkedTo[0],FNiagaraVariable(Type,TEXT("Emitter.TransientGrid")));
                    if (!Read) return false;
                    Node->Signature.Inputs.Add(FNiagaraVariable(Type,TEXT("BoundaryGrid")));
                    auto* Pin=Node->CreatePin(EGPD_Input,UEdGraphSchema_Niagara::TypeDefinitionToPinType(Type),TEXT("BoundaryGrid"));
                    // History traversal indexes Signature by input-pin position;
                    // the dynamic Add sentinel must remain the final input.
                    Node->Pins.Remove(Pin);
                    int32 AddIndex=INDEX_NONE;
                    for (int32 I=0;I<Node->Pins.Num();++I)
                        if (Node->Pins[I]->Direction==EGPD_Input && Node->Pins[I]->PinName==TEXT("Add")) { AddIndex=I;break; }
                    if (AddIndex==INDEX_NONE) { UE_LOG(LogTemp,Error,TEXT("Compatible divergence missing dynamic input sentinel"));return false; }
                    Node->Pins.Insert(Pin,AddIndex);
                    Pin->MakeLinkTo(Read);
                    Code=TEXT(
                        "// CompatibleMaskedDivergence: D of the same constrained velocity used by projection.\n"
                        "Div=0; float3 h=float3(dx,dx,800.0/24.0); int3 p=int3(IndexX,IndexY,IndexZ);\n"
                        "for(int axis=0;axis<3;++axis) { int3 e=int3(axis==0,axis==1,axis==2);\n"
                        " for(int sign=-1;sign<=1;sign+=2) { int3 j=p+sign*e; float v; VGRID.GetGridValue(j.x,j.y,j.z,VectorIndex+axis,v);\n"
                        " float4 b,bm,bp; BoundaryGrid.GetPreviousVector4Value<Attribute=\"SolidVelocity_Boundary\">(j.x,j.y,j.z,b);\n"
                        " BoundaryGrid.GetPreviousVector4Value<Attribute=\"SolidVelocity_Boundary\">(j.x-e.x,j.y-e.y,j.z-e.z,bm);\n"
                        " BoundaryGrid.GetPreviousVector4Value<Attribute=\"SolidVelocity_Boundary\">(j.x+e.x,j.y+e.y,j.z+e.z,bp);\n"
                        " if(axis==2) { if(round(bp.w)==1) v=bp[axis]; if(round(bm.w)==1) v=bm[axis]; }\n"
                        " else { if(round(bm.w)==1) v=bm[axis]; if(round(bp.w)==1) v=bp[axis]; }\n"
                        " if(round(b.w)==1) v=b[axis]; Div+=sign*v/(2*h[axis]); } }\n");
                    Code.ReplaceInline(TEXT("VGRID"),*Grid);++Divergences;
                }
                else if (Pressure && Original.Contains(TEXT("FluidCellCount")) && Original.Contains(TEXT("GetOutputGridFloatValue")))
                {
                    const FString B=InterfaceFor(Original,TEXT("GetPreviousVector4Value"));
                    const FString P=InterfaceFor(Original,TEXT("GetOutputGridFloatValue"));
                    const FString D=InterfaceFor(Original,TEXT("GetPreviousFloatValue"));
                    if (B.IsEmpty() || P.IsEmpty() || D.IsEmpty())
                    {
                        UE_LOG(LogTemp,Error,TEXT("Compatible pressure DI lookup failed B=%s P=%s D=%s; source=%s"),*B,*P,*D,*Original);return false;
                    }
                    Code=TEXT(
                        "// CompatibleMaskedPressure: solve D M G, not the unrelated nearest-cell Laplacian.\n"
                        "Pressure=0; int3 p=int3(IndexX,IndexY,IndexZ); float3 h=float3(dx,dx,800.0/24.0);\n"
                        "float4 center; BGRID.GetPreviousVector4Value<Attribute=\"SolidVelocity_Boundary\">(p.x,p.y,p.z,center);\n"
                        "if(round(center.w)==0) { float sum=0,diagonal=0;\n"
                        " for(int axis=0;axis<3;++axis) { int3 e=int3(axis==0,axis==1,axis==2);\n"
                        "  for(int sign=-1;sign<=1;sign+=2) { int3 j=p+sign*e,k=p+2*sign*e; float4 middle,outer;\n"
                        "   BGRID.GetPreviousVector4Value<Attribute=\"SolidVelocity_Boundary\">(j.x,j.y,j.z,middle);\n"
                        "   BGRID.GetPreviousVector4Value<Attribute=\"SolidVelocity_Boundary\">(k.x,k.y,k.z,outer);\n"
                        "   if(round(middle.w)!=1 && round(outer.w)!=1) { float weight=1/(4*h[axis]*h[axis]); float neighbor=0;\n"
                        "    if(round(outer.w)==0) PGRID.GetOutputGridFloatValue<Attribute=\"Pressure\">(k.x,k.y,k.z,neighbor);\n"
                        "    sum+=weight*neighbor; diagonal+=weight; } } }\n"
                        " float div,old; DGRID.GetPreviousFloatValue<Attribute=\"SimFloat\">(p.x,p.y,p.z,div);\n"
                        " PGRID.GetOutputGridFloatValue<Attribute=\"Pressure\">(p.x,p.y,p.z,old);\n"
                        " if(diagonal>0) Pressure=lerp(old,(sum-div/dt)/diagonal,clamp(saturate(Relaxation)+1,0,1.99999)); }\n"
                        "PGRID.SetFloatValue<Attribute=\"Pressure\">(p.x,p.y,p.z,Pressure);\n");
                    Code.ReplaceInline(TEXT("BGRID"),*B);Code.ReplaceInline(TEXT("PGRID"),*P);Code.ReplaceInline(TEXT("DGRID"),*D);++Pressures;
                    if (OutletStage)
                    {
                        auto* Input=Node->FindPin(FName(*B),EGPD_Input);
                        if(!Input || Input->LinkedTo.Num()!=1) return false;
                        const FNiagaraVariable V(FNiagaraTypeDefinition(UNiagaraDataInterfaceArrayFloat3::StaticClass()),
                            Regional?TEXT("User.River Parent Exterior"):TEXT("User.River Grid Boundary"));
                        auto* StageRead=CloneRead(Input->LinkedTo[0],V);
                        if(!StageRead)
                        { UE_LOG(LogTemp,Error,TEXT("Stage pressure read clone failed from %s (%s), pin %s"),*Input->LinkedTo[0]->GetOwningNode()->GetPathName(),*Input->LinkedTo[0]->GetOwningNode()->GetClass()->GetName(),*Input->LinkedTo[0]->PinName.ToString());return false; }
                        if(!RaftSimAddCustomInput(Node,FNiagaraVariable(V.GetType(),TEXT("StageProfile")),StageRead)) return false;
                        const FString CenterQuery=TEXT("// NativeOutletStagePressure\nif(round(center.w)==3) {\n")+
                            RaftSimLiquidBoundaryGridPositionHlsl(Regional?*Regional->ParentIndexHlsl(TEXT("p")):TEXT("p"),TEXT("StageProfile"))+
                            RaftSimOutletStageQuery(TEXT("stageGridPosition"),TEXT("StageProfile"),true,Regional!=nullptr)+
                            TEXT("Pressure=externalPressure; }\n");
                        Code.ReplaceInline(TEXT("if(round(center.w)==0)"),*(CenterQuery+TEXT("if(round(center.w)==0)")));
                        const FString NeighborQuery=TEXT("if(round(outer.w)==3) {\n")+
                            RaftSimLiquidBoundaryGridPositionHlsl(Regional?*Regional->ParentIndexHlsl(TEXT("k")):TEXT("k"),TEXT("StageProfile"))+
                            RaftSimOutletStageQuery(TEXT("stageGridPosition"),TEXT("StageProfile"),true,Regional!=nullptr)+
                            TEXT("neighbor=externalPressure; }\n");
                        Code.ReplaceInline(TEXT("sum+=weight*neighbor;"),*(NeighborQuery+TEXT("sum+=weight*neighbor;")));
                    }
                    Code=RaftSimLiquidPressureColoring::Wrap(Code,P);
                    if (Regional)
                    {
                        const FString Index=TEXT("int3 p=int3(IndexX+pressureLane,IndexY,IndexZ);");
                        if (Code.ReplaceInline(*Index,*(Index+Regional->OwnsHlsl()),ESearchCase::CaseSensitive)!=1) return false;
                    }
                }
                else if (Pressure && Original.Contains(TEXT("IsBlack")) && Node->FindPin(TEXT("X"),EGPD_Output))
                {
                    // +/-2 pressure dependencies need coloring on floor(index/2).
                    // Each thread retains its parity lane; the pressure body
                    // handles a final incomplete four-cell group explicitly.
                    Code=TEXT("// CompatibleWideStencilColoring\nX=0;Y=0;Z=0;\n#if GPU_SIMULATION\n"
                        "Y=GDispatchThreadId.y; Z=GDispatchThreadId.z; int t=GDispatchThreadId.x;\n"
                        "X=(t/2)*4+t%2+2*((Y/2+Z/2+(IterationIndex % 2))%2);\n#endif\n");++Colorings;
                    if (Regional)
                        Code.ReplaceInline(TEXT("(IterationIndex % 2)"),*FString::Printf(TEXT("(IterationIndex %% 2)+%d"),Regional->Phase()));
                }
                // The other branch differentiates vector magnitude, not pressure.
                else if (Grad && Original.Contains(TEXT("S_right")) && Node->FindPin(TEXT("ScalarIndex"),EGPD_Input) && Node->FindPin(TEXT("Grad"),EGPD_Output))
                {
                    for (const FName Input:{FName(TEXT("dx")),FName(TEXT("IndexX")),FName(TEXT("IndexY")),FName(TEXT("IndexZ")),FName(TEXT("ScalarIndex"))})
                        if (!Node->FindPin(Input,EGPD_Input))
                        {
                            UE_LOG(LogTemp,Error,TEXT("Compatible gradient missing input %s: %s"),*Input.ToString(),*Original);return false;
                        }
                    const FString Grid=InterfaceFor(Original,TEXT("GetGridValue"));
                    if (Grid.IsEmpty()) return false;
                    if (OutletStage)
                    {
                        auto* Input=Node->FindPin(FName(*Grid),EGPD_Input);
                        if (!Input || Input->LinkedTo.Num()!=1) return false;
                        MetricSource=Input->LinkedTo[0];
                    }
                    Code=TEXT("// CompatibleAnisotropicGradient\nGrad=0; int3 p=int3(IndexX,IndexY,IndexZ); float3 h=float3(dx,dx,800.0/24.0);\n"
                        "for(int axis=0;axis<3;++axis) { int3 e=int3(axis==0,axis==1,axis==2); float plus,minus;\n"
                        "PGRID.GetGridValue(p.x+e.x,p.y+e.y,p.z+e.z,ScalarIndex,plus);\n"
                        "PGRID.GetGridValue(p.x-e.x,p.y-e.y,p.z-e.z,ScalarIndex,minus); Grad[axis]=(plus-minus)/(2*h[axis]); }\n");
                    Code.ReplaceInline(TEXT("PGRID"),*Grid);++Gradients;
                }
                if (!Code.IsEmpty())
                {
                    if (Regional && Code.Contains(TEXT("float3 h=float3(dx,dx,800.0/24.0);")))
                        if (Code.ReplaceInline(TEXT("float3 h=float3(dx,dx,800.0/24.0);"),*Regional->MetricHlsl(),ESearchCase::CaseSensitive)!=1) return false;
                    if (OutletStage && Code.Contains(TEXT("float3 h=float3(dx,dx,800.0/24.0);")))
                    {
                        // D, G and the pressure stencil must use the same XYZ
                        // metric. Pressure already has this read for stage;
                        // add it to divergence/gradient as well.
                        if (!Node->FindPin(TEXT("StageProfile"),EGPD_Input))
                        {
                            if (!MetricSource) return false;
                            const FNiagaraVariable V(FNiagaraTypeDefinition(UNiagaraDataInterfaceArrayFloat3::StaticClass()),TEXT("User.River Grid Boundary"));
                            auto* Read=CloneRead(MetricSource,V);
                            if (!Read || !RaftSimAddCustomInput(Node,FNiagaraVariable(V.GetType(),TEXT("StageProfile")),Read)) return false;
                        }
                        const FString Metric=RaftSimLiquidBoundaryLayoutHlsl(TEXT("StageProfile"),TEXT("projection"))+TEXT("float3 h=projectionStep;\n");
                        if (Code.ReplaceInline(TEXT("float3 h=float3(dx,dx,800.0/24.0);"),*Metric,ESearchCase::CaseSensitive)!=1) return false;
                    }
                    Property->SetPropertyValue_InContainer(Node,Code);
                    Node->MarkNodeRequiresSynchronization(TEXT("Compatible masked collocated projection"),true);
                }
            }
            Call->FunctionScript=Owned;Call->MarkNodeRequiresSynchronization(TEXT("Owned compatible projection operator"),true);
        }
    const bool Valid=Divergences==1 && Pressures==1 && Gradients==1 && Colorings==1 && Extrapolations==1;
    if (!Valid) UE_LOG(LogTemp,Error,TEXT("Compatible projection counts D=%d P=%d G=%d colors=%d extrapolate=%d"),Divergences,Pressures,Gradients,Colorings,Extrapolations);
    return Valid;
}
}
