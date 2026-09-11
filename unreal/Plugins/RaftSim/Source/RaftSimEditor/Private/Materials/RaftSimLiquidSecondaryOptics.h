#pragma once

#include "Materials/Material.h"
#include "Materials/MaterialExpressionCustom.h"
#include "Materials/MaterialExpressionScalarParameter.h"
#include "Materials/MaterialExpressionTextureCoordinate.h"
#include "Materials/MaterialExpressionVectorParameter.h"
#include "UObject/Package.h"

// Own the sprite optics; never modify the engine's shared WhitewaterMaterial.
// These are lit sub-resolution foam aggregates, not a second river surface or
// a replacement for resolved breaking crests. Preserve the native lifetime and
// noise opacity graph so appearance changes do not change particle persistence.
inline UMaterial* RaftSimCreateSecondaryOptics(UMaterial* Source)
{
    if (!Source || Source->GetName()!=TEXT("WhitewaterMaterial")) return nullptr;
    auto* Material=DuplicateObject<UMaterial>(Source,GetTransientPackage(),
        MakeUniqueObjectName(GetTransientPackage(),UMaterial::StaticClass(),TEXT("M_RaftSimSecondaryFoamReview")));
    auto* Color=NewObject<UMaterialExpressionVectorParameter>(Material);
    Color->ParameterName=TEXT("River Secondary Color");Color->DefaultValue=FLinearColor(.82f,.84f,.83f,1.f);
    Material->GetExpressionCollection().AddExpression(Color);
    Material->GetExpressionInputForProperty(MP_BaseColor)->Connect(0,Color);
    for (const auto& Pair:TArray<TPair<EMaterialProperty,float>>{{MP_Roughness,.65f},{MP_Specular,.25f}})
    {
        auto* Parameter=NewObject<UMaterialExpressionScalarParameter>(Material);
        Parameter->ParameterName=Pair.Key==MP_Roughness?TEXT("River Secondary Roughness"):TEXT("River Secondary Specular");
        Parameter->DefaultValue=Pair.Value;
        Material->GetExpressionCollection().AddExpression(Parameter);
        Material->GetExpressionInputForProperty(Pair.Key)->Connect(0,Parameter);
    }
    // The source plugged a tangent-space tile normal into a world-space input.
    // A smooth aggregate normal is defined in the billboard tangent frame; it
    // rotates with the sprite rather than imposing a fixed world direction.
    auto* UV=NewObject<UMaterialExpressionTextureCoordinate>(Material);
    Material->GetExpressionCollection().AddExpression(UV);
    auto* Normal=NewObject<UMaterialExpressionCustom>(Material);
    Normal->Description=TEXT("River secondary aggregate tangent normal");Normal->OutputType=CMOT_Float3;
    Normal->Code=TEXT("float2 p=(UV*2.0-1.0)*0.65; return normalize(float3(p,sqrt(max(1.0-dot(p,p),0.01))));");
    Normal->Inputs.Reset();FCustomInput Input;Input.InputName=TEXT("UV");Input.Input.Connect(0,UV);Normal->Inputs.Add(Input);
    Material->GetExpressionCollection().AddExpression(Normal);
    Material->bTangentSpaceNormal=true;
    Material->GetExpressionInputForProperty(MP_Normal)->Connect(0,Normal);
    return Material;
}
