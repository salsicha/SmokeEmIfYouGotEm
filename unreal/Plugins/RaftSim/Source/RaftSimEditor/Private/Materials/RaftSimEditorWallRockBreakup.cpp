#include "Environment/RaftSimEditorEnvironmentInternal.h"
#include "Materials/MaterialExpressionNoise.h"
#include "Materials/MaterialExpressionVectorNoise.h"
#include "HAL/IConsoleManager.h"

namespace RaftSimEditorEnvironment
{
namespace
{
UMaterialExpression* AddWallRockExpression(UMaterial* Material, UMaterialExpression* Expression)
{
    Material->GetExpressionCollection().AddExpression(Expression);
    return Expression;
}

UMaterialExpressionMultiply* MultiplyByConstant(UMaterial* Material, UMaterialExpression* A, float B)
{
    UMaterialExpressionMultiply* Multiply = NewObject<UMaterialExpressionMultiply>(Material);
    Multiply->A.Expression = A;
    Multiply->ConstB = B;
    AddWallRockExpression(Material, Multiply);
    return Multiply;
}

// World position displaced by smooth vector noise: Amplitude cm of drift
// over a WavelengthCm-scale field, plus a fixed offset.
UMaterialExpression* WarpedWorldPosition(UMaterial* Material, UMaterialExpression* WorldPosition,
                                         float WavelengthCm, float AmplitudeCm, const FLinearColor& OffsetCm)
{
    UMaterialExpressionConstant3Vector* Offset = NewObject<UMaterialExpressionConstant3Vector>(Material);
    Offset->Constant = OffsetCm;
    AddWallRockExpression(Material, Offset);
    UMaterialExpressionAdd* Shifted = NewObject<UMaterialExpressionAdd>(Material);
    Shifted->A.Expression = WorldPosition;
    Shifted->B.Expression = Offset;
    AddWallRockExpression(Material, Shifted);
    UMaterialExpressionVectorNoise* Field = NewObject<UMaterialExpressionVectorNoise>(Material);
    Field->NoiseFunction = VNF_VectorALU;
    Field->Position.Expression = MultiplyByConstant(Material, Shifted, 1.0f / WavelengthCm);
    AddWallRockExpression(Material, Field);
    UMaterialExpressionAdd* Warped = NewObject<UMaterialExpressionAdd>(Material);
    Warped->A.Expression = Shifted;
    Warped->B.Expression = MultiplyByConstant(Material, Field, AmplitudeCm);
    AddWallRockExpression(Material, Warped);
    return Warped;
}
}

FRaftSimWallRockBreakup BuildWallRockBreakup(UMaterial* Material)
{
    // A world-aligned scan repeats on a fixed axis-aligned lattice: on a
    // 60 m Hance wall the 6.5 m Rock037 tile's horizontal cracks lined up
    // into rows of identical dashes, so the cliffs read as tiled ("the
    // cliffs of the grand canyon look tessellated", 2026-10-06). Each layer
    // is sampled twice, from two differently drifting projections, and a
    // noise mask picks between them in patches of about 15 m, so no two
    // repeats line up.
    FRaftSimWallRockBreakup Breakup;
    UMaterialExpressionWorldPosition* WorldPosition = NewObject<UMaterialExpressionWorldPosition>(Material);
    AddWallRockExpression(Material, WorldPosition);
    Breakup.PositionA = WarpedWorldPosition(Material, WorldPosition, 3100.0f, 110.0f, FLinearColor(0.0f, 0.0f, 0.0f));
    Breakup.PositionB = WarpedWorldPosition(Material, WorldPosition, 2600.0f, 110.0f, FLinearColor(3770.0f, 1910.0f, 2330.0f));
    UMaterialExpressionNoise* Patches = NewObject<UMaterialExpressionNoise>(Material);
    Patches->Position.Expression = WorldPosition;
    Patches->NoiseFunction = NOISEFUNCTION_GradientALU;
    Patches->Scale = 1.0f / 1500.0f;
    Patches->Levels = 2;
    Patches->OutputMin = 0.0f;
    Patches->OutputMax = 1.0f;
    AddWallRockExpression(Material, Patches);
    // Sharpened about 0.5, so most of a wall shows one projection at full
    // contrast and only the seams between patches mix the two.
    UMaterialExpressionAdd* Centred = NewObject<UMaterialExpressionAdd>(Material);
    Centred->A.Expression = MultiplyByConstant(Material, Patches, 3.0f);
    Centred->ConstB = -1.0f;
    AddWallRockExpression(Material, Centred);
    UMaterialExpressionSaturate* Blend = NewObject<UMaterialExpressionSaturate>(Material);
    Blend->Input.Expression = Centred;
    AddWallRockExpression(Material, Blend);
    Breakup.Blend = Blend;
    return Breakup;
}

UMaterialExpression* AddWorldAlignedWallRock(UMaterial* Material, UTexture2D* Texture, EMaterialSamplerType SamplerType,
                                             const TCHAR* Name, float TileCm, bool bNormal,
                                             UMaterialExpression* WorldPosition, int32& OutIndex)
{
    UMaterialExpressionTextureObjectParameter* TextureObject =
        NewObject<UMaterialExpressionTextureObjectParameter>(Material);
    TextureObject->ParameterName = Name;
    TextureObject->Texture = Texture;
    TextureObject->SamplerType = SamplerType;
    TextureObject->Group = TEXT("RaftSimEvidenceWallRock");
    AddWallRockExpression(Material, TextureObject);
    UMaterialExpressionConstant3Vector* Size = NewObject<UMaterialExpressionConstant3Vector>(Material);
    Size->Constant = FLinearColor(TileCm, TileCm, TileCm, 1.0f);
    AddWallRockExpression(Material, Size);
    UMaterialFunctionInterface* Function = LoadObject<UMaterialFunctionInterface>(nullptr, bNormal
        ? TEXT("/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedNormal.WorldAlignedNormal")
        : TEXT("/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture.WorldAlignedTexture"));
    UMaterialExpressionMaterialFunctionCall* Call = NewObject<UMaterialExpressionMaterialFunctionCall>(Material);
    AddWallRockExpression(Material, Call);
    if (!Function || !Call->SetMaterialFunction(Function))
    {
        return nullptr;
    }
    bool bPositionConnected = WorldPosition == nullptr;
    for (int32 Index = 0; Index < Call->FunctionInputs.Num(); ++Index)
    {
        const FString InputName = Call->GetInputName(Index).ToString();
        FExpressionInput& Input = Call->FunctionInputs[Index].Input;
        if (InputName.Contains(TEXT("TextureObject"), ESearchCase::IgnoreCase))
        {
            Input.Expression = TextureObject;
        }
        else if (InputName.Contains(TEXT("TextureSize"), ESearchCase::IgnoreCase))
        {
            Input.Expression = Size;
        }
        else if (WorldPosition && InputName.Replace(TEXT(" "), TEXT("")).Contains(TEXT("WorldPosition"), ESearchCase::IgnoreCase))
        {
            Input.Expression = WorldPosition;
            bPositionConnected = true;
        }
    }
    if (!bPositionConnected)
    {
        UE_LOG(LogTemp, Error, TEXT("%s has no world position input; the wall rock cannot drift."), *Function->GetPathName());
        return nullptr;
    }
    for (int32 Index = 0; Index < Call->FunctionOutputs.Num(); ++Index)
    {
        if (Call->FunctionOutputs[Index].Output.OutputName.ToString().Equals(
                TEXT("XYZ Texture"), ESearchCase::IgnoreCase))
        {
            OutIndex = Index;
            return Call;
        }
    }
    return nullptr;
}

UMaterialExpression* AddBrokenUpWallRock(UMaterial* Material, const FRaftSimWallRockBreakup& Breakup, UTexture2D* Texture,
                                         EMaterialSamplerType SamplerType, const TCHAR* Name, float TileCm, bool bNormal,
                                         int32& OutIndex)
{
    // The second projection's tile is 1.585x the first, so the two never
    // share a repeat.
    int32 OutputA = 0, OutputB = 0;
    UMaterialExpression* A = AddWorldAlignedWallRock(
        Material, Texture, SamplerType, Name, TileCm, bNormal, Breakup.PositionA, OutputA);
    UMaterialExpression* B = AddWorldAlignedWallRock(
        Material, Texture, SamplerType, Name, TileCm * 1.585f, bNormal, Breakup.PositionB, OutputB);
    if (!A || !B)
    {
        return nullptr;
    }
    UMaterialExpressionLinearInterpolate* Mixed = NewObject<UMaterialExpressionLinearInterpolate>(Material);
    Mixed->A.Expression = A;
    Mixed->A.OutputIndex = OutputA;
    Mixed->B.Expression = B;
    Mixed->B.OutputIndex = OutputB;
    Mixed->Alpha.Expression = Breakup.Blend;
    AddWallRockExpression(Material, Mixed);
    OutIndex = 0;
    return Mixed;
}

// Re-author one landscape candidate's material in place without rebuilding
// its map (the map build also reinstalls terrain, water and props).
static FAutoConsoleCommand GRefreshLandscapeCandidateMaterialCommand(
    TEXT("RaftSim.RefreshLandscapeCandidateMaterial"),
    TEXT("Re-author and save the landscape material of one candidate river (river_id) in place, without rebuilding its map."),
    FConsoleCommandWithArgsDelegate::CreateLambda([](const TArray<FString>& Args)
    {
        if (Args.Num() != 1)
        {
            UE_LOG(LogTemp, Error, TEXT("Usage: RaftSim.RefreshLandscapeCandidateMaterial <river_id>"));
            return;
        }
        for (const FRaftSimLandscapeImportCandidateSpec& Candidate : GetLandscapeImportCandidateSpecs())
        {
            if (Candidate.PreviewSpec.RiverId != Args[0])
            {
                continue;
            }
            FString Summary;
            const UMaterialInterface* Material = LoadOrCreateLandscapeCandidateMaterial(Candidate, Summary);
            UE_LOG(LogTemp, Display, TEXT("RAFTSIM_LANDSCAPE_MATERIAL_REFRESH river=%s material=%s %s"),
                *Args[0], Material ? *Material->GetPathName() : TEXT("FAILED"), *Summary);
            return;
        }
        UE_LOG(LogTemp, Error, TEXT("No landscape import candidate for %s"), *Args[0]);
    }));
}
