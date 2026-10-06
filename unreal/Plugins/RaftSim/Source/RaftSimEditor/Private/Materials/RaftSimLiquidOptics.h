#pragma once

#include "Materials/Material.h"
#include "Materials/MaterialExpressionMultiply.h"
#include "Materials/MaterialExpressionScalarParameter.h"
#include "Materials/MaterialExpressionVectorParameter.h"
#include "Materials/MaterialExpressionSingleLayerWaterMaterialOutput.h"
#include "Materials/MaterialExpressionCustom.h"
#include "UObject/Package.h"

// Isolated base-water optics experiment, not a foam model. Keep the inherited
// raymarch, mask, depth, WPO, absorption and simulation bindings unchanged.
inline UMaterial* RaftSimCreateLiquidScatteringReview(UMaterial* Source)
{
    if (!Source || !Source->GetName().Equals(TEXT("M_WaterSDF"))) return nullptr;
    auto* Material=DuplicateObject<UMaterial>(Source,GetTransientPackage(),
        MakeUniqueObjectName(GetTransientPackage(),UMaterial::StaticClass(),TEXT("M_RaftSimLiquidBaseScatteringReview")));
    UMaterialExpressionMultiply* Scattering=nullptr;
    UMaterialExpressionSingleLayerWaterMaterialOutput* Water=nullptr;
    for (const auto& Expression:Material->GetExpressionCollection().Expressions)
    {
        if (auto* Output=Cast<UMaterialExpressionSingleLayerWaterMaterialOutput>(Expression)) Water=Output;
        if (auto* Multiply=Cast<UMaterialExpressionMultiply>(Expression))
        {
            auto* A=Cast<UMaterialExpressionVectorParameter>(Multiply->A.Expression);
            auto* B=Cast<UMaterialExpressionVectorParameter>(Multiply->B.Expression);
            if (A && A==B && A->ParameterName==TEXT("Scattering") && Multiply->A.OutputIndex==0 && Multiply->B.OutputIndex==4)
                Scattering=Multiply;
        }
    }
    if (!Water || !Scattering) return nullptr;
    Water->ScatteringCoefficients.Connect(0,Scattering);
    // Expose roughness independently; zero preserves the source value until an
    // explicit optical control changes it. No extra normal or texture layer.
    auto* Roughness=NewObject<UMaterialExpressionScalarParameter>(Material);
    Roughness->ParameterName=TEXT("River Roughness");Roughness->DefaultValue=0.f;
    Material->GetExpressionCollection().AddExpression(Roughness);
    Material->GetExpressionInputForProperty(MP_Roughness)->Connect(0,Roughness);
    return Material;
}

inline bool RaftSimCorrectLiquidWorldNormal(UMaterial* Material)
{
    if (!Material || Material->GetOutermost()!=GetTransientPackage() || Material->bTangentSpaceNormal) return false;
    auto* Input=Material->GetExpressionInputForProperty(MP_Normal);
    if (!Input || !Input->Expression) return false;
    auto* Normal=NewObject<UMaterialExpressionCustom>(Material);
    Normal->Description=TEXT("RaftSim grid-local SDF normal to world");
    Normal->OutputType=CMOT_Float3;
    Normal->Code=TEXT("float3 worldNormal=N.x*R0+N.y*R1+N.z*R2; return worldNormal*rsqrt(max(dot(worldNormal,worldNormal),1e-12));");
    Normal->Inputs.Reset();
    FCustomInput Local;Local.InputName=TEXT("N");Local.Input=*Input;Normal->Inputs.Add(Local);
    for (int32 Axis=0;Axis<3;++Axis)
    {
        auto* Row=NewObject<UMaterialExpressionVectorParameter>(Material);
        Row->ParameterName=FName(*FString::Printf(TEXT("LocalToWorld%d"),Axis));
        Material->GetExpressionCollection().AddExpression(Row);
        FCustomInput WorldRow;WorldRow.InputName=FName(*FString::Printf(TEXT("R%d"),Axis));
        WorldRow.Input.Connect(0,Row);Normal->Inputs.Add(WorldRow);
    }
    Material->GetExpressionCollection().AddExpression(Normal);
    Input->Connect(0,Normal);
    return true;
}

inline bool RaftSimCorrectLiquidRayFrame(UMaterial* Material)
{
    if (!Material || Material->GetOutermost()!=GetTransientPackage()) return false;
    int32 Corrected=0;
    for (const auto& Expression:Material->GetExpressionCollection().Expressions)
        if (auto* Custom=Cast<UMaterialExpressionCustom>(Expression))
        {
            // Both directions must be world-space. A yawed local ray dotted
            // with world camera-forward can be negative even in front of the
            // camera, causing the entire valid SDF hit to fail its depth test.
            Corrected+=Custom->Code.ReplaceInline(
                TEXT("SceneDepth / dot(LocalRayDir, CameraDirectionVector)"),
                TEXT("SceneDepth / max(dot(WorldRayDir, CameraDirectionVector),1e-6)"),
                ESearchCase::CaseSensitive);
        }
    return Corrected==1;
}

// Surface coverage comes from the transported SimRT.g at the actual ray hit.
// It changes the BSDF on that same SDF surface, never adds a second white plane.
inline bool RaftSimConnectLiquidFoamOptics(UMaterial* Material)
{
    if (!Material || Material->GetOutermost()!=GetTransientPackage()) return false;
    UMaterialExpressionCustom* Raymarch=nullptr;int32 FoamOutput=INDEX_NONE;
    for (const auto& Expression:Material->GetExpressionCollection().Expressions)
        if (auto* Custom=Cast<UMaterialExpressionCustom>(Expression))
            for (int32 I=0;I<Custom->AdditionalOutputs.Num();++I)
                if (Custom->AdditionalOutputs[I].OutputName==TEXT("Whitewater") &&
                    Custom->Code.Contains(TEXT("Whitewater = VolumeSample.g;")))
                { if (Raymarch) return false;Raymarch=Custom;FoamOutput=I+1; }
    if (!Raymarch) return false;
    // G now holds coverage, not a normal component. Always derive normals from
    // SDF.r, including when inherited ComputeNormals was disabled.
    if (Raymarch->Code.ReplaceInline(TEXT("RetVal.a != 0 && ComputeNormals > 1-1e-5"),
        TEXT("RetVal.a != 0"),ESearchCase::CaseSensitive)!=1) return false;
    auto* Strength=NewObject<UMaterialExpressionScalarParameter>(Material);
    Strength->ParameterName=TEXT("River Foam Strength");Strength->DefaultValue=1.f;
    Material->GetExpressionCollection().AddExpression(Strength);
    for (auto Property:{MP_BaseColor,MP_Roughness,MP_Opacity})
    {
        auto* Original=Material->GetExpressionInputForProperty(Property);
        if (!Original || !Original->Expression) return false;
        auto* Blend=NewObject<UMaterialExpressionCustom>(Material);
        Blend->Description=FString::Printf(TEXT("RaftSim advected foam %s"),*UEnum::GetValueAsString(Property));
        Blend->OutputType=Property==MP_BaseColor?CMOT_Float3:CMOT_Float1;
        Blend->Code=Property==MP_BaseColor?TEXT("return lerp(Base,float3(0.85,0.88,0.87),saturate(Foam*Strength));"):
            Property==MP_Roughness?TEXT("return lerp(Base,0.7,saturate(Foam*Strength));"):
            TEXT("return lerp(Base,1.0,saturate(Foam*Strength));");
        Blend->Inputs.Reset();
        FCustomInput Base;Base.InputName=TEXT("Base");Base.Input=*Original;Blend->Inputs.Add(Base);
        FCustomInput Coverage;Coverage.InputName=TEXT("Foam");Coverage.Input.Connect(FoamOutput,Raymarch);Blend->Inputs.Add(Coverage);
        FCustomInput Gain;Gain.InputName=TEXT("Strength");Gain.Input.Connect(0,Strength);Blend->Inputs.Add(Gain);
        Material->GetExpressionCollection().AddExpression(Blend);
        Original->Connect(0,Blend);
    }
    return true;
}
