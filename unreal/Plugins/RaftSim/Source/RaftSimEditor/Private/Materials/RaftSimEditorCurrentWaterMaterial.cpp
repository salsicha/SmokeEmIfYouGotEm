#include "Environment/RaftSimEditorEnvironmentInternal.h"
#include "Materials/MaterialExpressionCustom.h"
#include "Materials/MaterialExpressionCollectionParameter.h"
#include "Materials/MaterialExpressionClamp.h"

namespace RaftSimEditorEnvironment
{
namespace
{
template <typename T> T* AddCurrentWaterExpression(UMaterial* Material)
{
    T* Expression = NewObject<T>(Material);
    Material->GetExpressionCollection().AddExpression(Expression);
    return Expression;
}

bool ConfigureChilkoDensityFoam(UMaterial* Material, UMaterialExpression* Aeration)
{
    UMaterialExpressionCustom* DensityFoam = nullptr;
    UMaterialExpressionLinearInterpolate* WaterColor = nullptr;
    for (UMaterialExpression* Expression : Material->GetExpressions())
    {
        if (auto* Custom = Cast<UMaterialExpressionCustom>(Expression))
            if (Custom->Desc == TEXT("ChilkoDensityFoamV1")) DensityFoam = Custom;
        if (auto* Lerp = Cast<UMaterialExpressionLinearInterpolate>(Expression))
            if (auto* Color = Cast<UMaterialExpressionVectorParameter>(Lerp->B.Expression))
                if (Color->ParameterName == TEXT("WhitewaterFrothColor"))
                {
                    // A later drift-fleck tint uses the same colour parameter;
                    // its multiply alpha is not the hydraulic foam branch.
                    auto* Existing = Cast<UMaterialExpressionCustom>(Lerp->Alpha.Expression);
                    if (Cast<UMaterialExpressionClamp>(Lerp->Alpha.Expression) ||
                        (Existing && Existing->Desc == TEXT("ChilkoDensityFoamV1"))) WaterColor = Lerp;
                }
    }
    if (!WaterColor || !Aeration) return false;
    if (!DensityFoam)
    {
        // Follow the actual foam-colour branch, not another mask used by WPO.
        auto* Broken = Cast<UMaterialExpressionClamp>(WaterColor->Alpha.Expression);
        auto* Raw = Broken ? Cast<UMaterialExpressionMultiply>(Broken->Input.Expression) : nullptr;
        auto* Breakup = Raw ? Cast<UMaterialExpressionClamp>(Raw->B.Expression) : nullptr;
        auto* Contrast = Breakup ? Cast<UMaterialExpressionMultiply>(Breakup->Input.Expression) : nullptr;
        auto* Gain = Contrast ? Cast<UMaterialExpressionScalarParameter>(Contrast->B.Expression) : nullptr;
        auto* Biased = Contrast ? Cast<UMaterialExpressionAdd>(Contrast->A.Expression) : nullptr;
        if (!Gain || Gain->ParameterName != TEXT("HydraulicFoamColorBreakupGain") ||
            !Biased || !Biased->A.Expression) return false;
        DensityFoam = AddCurrentWaterExpression<UMaterialExpressionCustom>(Material);
        DensityFoam->Inputs.Reset();
        DensityFoam->Desc = TEXT("ChilkoDensityFoamV1");
        auto* Blend = AddCurrentWaterExpression<UMaterialExpressionScalarParameter>(Material);
        Blend->ParameterName = TEXT("ChilkoDenseFoamBlend");
        Blend->DefaultValue = 1.0f;
        const auto Input = [DensityFoam](const TCHAR* Name, UMaterialExpression* Source)
        {
            FCustomInput Entry;
            Entry.InputName = Name;
            Entry.Input.Connect(0, Source);
            DensityFoam->Inputs.Add(Entry);
        };
        Input(TEXT("Legacy"), Broken);
        Input(TEXT("Lace"), Biased->A.Expression);
        Input(TEXT("Aeration"), Aeration);
        Input(TEXT("Blend"), Blend);
    }
    // Remove the editor's default unbound input from an early saved version.
    DensityFoam->Inputs.RemoveAll([](const FCustomInput& Input)
        { return Input.Input.Expression == nullptr; });
    DensityFoam->OutputType = CMOT_Float1;
    DensityFoam->Code = TEXT(R"HLSL(
// Sparse transported foam retains its translucent, perforated response.
// Dense aeration closes progressively more of the SAME advected lace, with
// opaque interiors and open holes, rather than brightening every foam cell.
float dense = smoothstep(0.28, 0.72, saturate(Aeration));
float threshold = lerp(0.62, 0.06, dense);
float aa = max(fwidth(Lace), 0.06);
float packed = smoothstep(threshold - aa, threshold + aa, Lace);
return saturate(lerp(Legacy, max(Legacy, packed * 0.98), dense * saturate(Blend)));
)HLSL");
    WaterColor->Alpha.Connect(0, DensityFoam);

    UMaterialExpression* LegacyFoam = nullptr;
    for (const FCustomInput& Input : DensityFoam->Inputs)
        if (Input.InputName == TEXT("Legacy")) LegacyFoam = Input.Input.Expression;
    if (!LegacyFoam) return false;
    UMaterialExpressionCustom* OpticalFoam = nullptr;
    for (UMaterialExpression* Expression : Material->GetExpressions())
        if (auto* Custom = Cast<UMaterialExpressionCustom>(Expression))
            if (Custom->Desc == TEXT("ChilkoDensityFoamOpticsV1")) OpticalFoam = Custom;
    if (!OpticalFoam)
    {
        OpticalFoam = AddCurrentWaterExpression<UMaterialExpressionCustom>(Material);
        OpticalFoam->Desc = TEXT("ChilkoDensityFoamOpticsV1");
        OpticalFoam->Inputs.Reset();
        auto* Blend = AddCurrentWaterExpression<UMaterialExpressionScalarParameter>(Material);
        Blend->ParameterName = TEXT("ChilkoDenseFoamOpticsBlend");
        Blend->DefaultValue = 1.0f;
        const auto Input = [OpticalFoam](const TCHAR* Name, UMaterialExpression* Source)
        {
            FCustomInput Entry;
            Entry.InputName = Name;
            Entry.Input.Connect(0, Source);
            OpticalFoam->Inputs.Add(Entry);
        };
        Input(TEXT("Legacy"), LegacyFoam);
        Input(TEXT("Density"), DensityFoam);
        Input(TEXT("Blend"), Blend);
    }
    OpticalFoam->OutputType = CMOT_Float1;
    OpticalFoam->Code = TEXT("return lerp(Legacy, Density, saturate(Blend));");
    // Rewire only the three optical consumers. In particular, never replace
    // Legacy inside DensityFoam (a cycle), WPO, wet coverage or physical depth.
    bool bRoughness = false, bOpacity = false, bScattering = false;
    for (UMaterialExpression* Expression : Material->GetExpressions())
    {
        if (auto* Multiply = Cast<UMaterialExpressionMultiply>(Expression))
            if (auto* Scale = Cast<UMaterialExpressionScalarParameter>(Multiply->B.Expression))
                if (Scale->ParameterName == TEXT("FoamRoughness") &&
                    (Multiply->A.Expression == LegacyFoam || Multiply->A.Expression == OpticalFoam))
                { Multiply->A.Connect(0, OpticalFoam); bRoughness = true; }
        if (auto* Lerp = Cast<UMaterialExpressionLinearInterpolate>(Expression))
            if (auto* Opacity = Cast<UMaterialExpressionScalarParameter>(Lerp->B.Expression))
                if (Opacity->ParameterName == TEXT("FoamWaterOpacity") &&
                    (Lerp->Alpha.Expression == LegacyFoam || Lerp->Alpha.Expression == OpticalFoam))
                { Lerp->Alpha.Connect(0, OpticalFoam); bOpacity = true; }
        if (auto* Add = Cast<UMaterialExpressionAdd>(Expression))
            if (auto* Speed = Cast<UMaterialExpressionMultiply>(Add->B.Expression))
                if (auto* Fraction = Cast<UMaterialExpressionScalarParameter>(Speed->B.Expression))
                    if (Fraction->ParameterName == TEXT("SpeedAerationFraction") &&
                        (Add->A.Expression == LegacyFoam || Add->A.Expression == OpticalFoam))
                    { Add->A.Connect(0, OpticalFoam); bScattering = true; }
    }
    if (!bRoughness || !bOpacity || !bScattering)
    {
        UE_LOG(LogTemp, Error, TEXT("Chilko density optics missing consumer: roughness=%d opacity=%d scattering=%d"),
            bRoughness, bOpacity, bScattering);
        return false;
    }
    return true;
}
}

// River-specific optical detail, not another displaced surface. The normal
// follows the same integrated current displacement as the shared foam field.
UMaterial* LoadOrCreateCurrentGradientWaterParent(
    UMaterial* Shared, const FString& Path, const FString& RiverLabel,
    float FoamCutoff, float NormalStrength, FString& Summary)
{
    if (!Shared || !FMath::IsFinite(FoamCutoff) || FoamCutoff < 0.0f ||
        FoamCutoff > 1.0f || !FMath::IsFinite(NormalStrength) || NormalStrength < 0.0f)
    {
        Summary += TEXT("Invalid current-water parent or optical calibration.\n");
        return nullptr;
    }
    const FString AssetName = FPackageName::GetLongPackageAssetName(Path);
    const FString NormalMarker = RiverLabel + TEXT("CurrentGradientNormalV1");
    UPackage* Package = CreatePackage(*Path);
    UMaterial* Material = LoadObject<UMaterial>(nullptr, *(Path + TEXT(".") + AssetName));
    if (!Material)
    {
        Material = Cast<UMaterial>(StaticDuplicateObject(Shared, Package, *AssetName));
        if (!Material) return nullptr;
        FAssetRegistryModule::AssetCreated(Material);
    }
    UMaterialExpressionCustom* Detail = nullptr;
    UMaterialExpressionVectorParameter* Origin = nullptr;
    UMaterialExpressionCollectionParameter* Current = nullptr;
    for (UMaterialExpression* Expression : Material->GetExpressions())
    {
        if (auto* Candidate = Cast<UMaterialExpressionCustom>(Expression))
            if (Candidate->Desc == NormalMarker) Detail = Candidate;
        if (auto* Parameter = Cast<UMaterialExpressionVectorParameter>(Expression))
            if (Parameter->ParameterName == TEXT("RaftSimWaterUVOrigin")) Origin = Parameter;
        if (auto* Parameter = Cast<UMaterialExpressionCollectionParameter>(Expression))
            if (Parameter->ParameterName == TEXT("RaftSimFoamAdvectionMeters")) Current = Parameter;
    }
    if (!Origin || !Current)
    {
        Summary += TEXT("Current normal requires the migrated UV origin and current collection.\n");
        return nullptr;
    }
    // Locate the inherited intensity branch, not an arbitrary constant.
    // Each river supplies a cutoff calibrated against its resolved aeration.
    bool bFoundCutoff = false;
    UMaterialExpression* AerationSignal = nullptr;
    for (UMaterialExpression* Expression : Material->GetExpressions())
    {
        auto* Add = Cast<UMaterialExpressionAdd>(Expression);
        auto* Intensity = Add ? Cast<UMaterialExpressionMultiply>(Add->A.Expression) : nullptr;
        auto* Gain = Intensity ? Cast<UMaterialExpressionScalarParameter>(Intensity->B.Expression) : nullptr;
        auto* Cutoff = Add ? Cast<UMaterialExpressionConstant>(Add->B.Expression) : nullptr;
        if (Gain && Gain->ParameterName == TEXT("HydraulicFoamIntensity") && Cutoff)
        {
            Cutoff->R = -FoamCutoff;
            Cutoff->Desc = RiverLabel + TEXT("ResolvedAerationCutoff");
            bFoundCutoff = true;
            AerationSignal = Intensity;
        }
    }
    if (!bFoundCutoff)
    {
        Summary += TEXT("Current-water parent has no recognized aeration cutoff branch.\n");
        return nullptr;
    }
    if (!Detail)
    {
        Detail = AddCurrentWaterExpression<UMaterialExpressionCustom>(Material);
        Detail->Desc = NormalMarker;
        auto* UV = AddCurrentWaterExpression<UMaterialExpressionTextureCoordinate>(Material);
        auto* Color = AddCurrentWaterExpression<UMaterialExpressionVertexColor>(Material);
        auto* Strength = AddCurrentWaterExpression<UMaterialExpressionScalarParameter>(Material);
        Strength->ParameterName = FName(*(RiverLabel + TEXT("CurrentNormalStrength")));
        Strength->DefaultValue = NormalStrength;
        const auto Input = [Detail](const TCHAR* Name, UMaterialExpression* Expression, int32 Output = 0)
        {
            FCustomInput Entry;
            Entry.InputName = Name;
            Entry.Input.Connect(Output, Expression);
            Detail->Inputs.Add(Entry);
        };
        Input(TEXT("UV"), UV);
        Input(TEXT("Origin"), Origin);
        Input(TEXT("Current"), Current);
        Input(TEXT("Foam"), Color, 1);
        Input(TEXT("Strength"), Strength);
    }
    Detail->OutputType = CMOT_Float3;
    Detail->Code = TEXT(R"HLSL(
struct CurrentNoise
{
    float hash(float2 p)
    {
        float3 q = frac(float3(p.x, p.y, p.x) * 0.1031);
        q += dot(q, q.yzx + 33.33);
        return frac((q.x + q.y) * q.z);
    }
    float2 gradient(float2 p)
    {
        float2 i = floor(p), f = frac(p);
        float2 u = f * f * (3.0 - 2.0 * f);
        float2 du = 6.0 * f * (1.0 - f);
        float a = hash(i), b = hash(i + float2(1, 0));
        float c = hash(i + float2(0, 1)), d = hash(i + 1.0);
        return du * float2(lerp(b-a, d-c, u.y), lerp(c-a, d-b, u.x));
    }
};
CurrentNoise n;
float2 p = (UV + Origin.xy) * 3.0 - Current.xy;
float2 a = float2(0.857*p.x - 0.515*p.y, 0.515*p.x + 0.857*p.y) * 0.71;
float2 b = float2(0.391*p.x + 0.921*p.y, -0.921*p.x + 0.391*p.y) * 2.31 + 17.13;
float2 ga = n.gradient(a), gb = n.gradient(b);
// Transform the analytical derivatives back into river tangent space.
ga = float2(0.857*ga.x + 0.515*ga.y, -0.515*ga.x + 0.857*ga.y);
gb = float2(0.391*gb.x - 0.921*gb.y, 0.921*gb.x + 0.391*gb.y);
// Suppress subpixel detail before it aliases into flashing glints.
float footprint = max(length(ddx(p)), length(ddy(p)));
float fineFade = 1.0 - smoothstep(0.08, 0.40, footprint);
float coarseFade = 1.0 - smoothstep(0.35, 1.40, footprint);
float2 slope = (ga * 0.70 * coarseFade + gb * 0.30 * fineFade)
    * Strength * lerp(0.55, 1.5, saturate(Foam * 2.0));
return normalize(float3(-slope, 1.0));
)HLSL");
    const bool bUseTriangularCurrentGradient = RiverLabel == TEXT("Futaleufu") ||
        RiverLabel == TEXT("Chilko");
    if (bUseTriangularCurrentGradient)
    {
        // Terminator's smooth dark pools expose the square-cell derivative
        // pattern as bands even with rotated octaves (normal-only A/B).
        // A compact triangular gradient kernel has no orthogonal cell seams.
        // Chilko shares this cold-water variant; preserve the other variants.
        const FString TriangularKernel = TEXT(R"HLSL(
    float2 simplexGradient(float2 p)
    {
        const float F = 0.3660254038, G = 0.2113248654;
        float2 cell = floor(p + (p.x + p.y) * F);
        float2 x0 = p - cell + (cell.x + cell.y) * G;
        float2 corner = x0.x > x0.y ? float2(1,0) : float2(0,1);
        float2 result = 0;
        [unroll] for (int k = 0; k < 3; ++k)
        {
            float2 offset = k == 0 ? float2(0,0) : (k == 1 ? corner : float2(1,1));
            float2 x = x0 - offset + (offset.x + offset.y) * G;
            float2 lattice = cell + offset;
            float2 g = float2(hash(lattice), hash(lattice + 47.17)) * 2.0 - 1.0;
            g *= rsqrt(max(dot(g,g), 0.0001));
            float t = max(0.5 - dot(x,x), 0.0);
            float d = dot(g,x);
            result += t*t*t*t*g - 8.0*t*t*t*d*x;
        }
        return result * 45.0;
    }
    float2 gradient(float2 p)
)HLSL");
        Detail->Code.ReplaceInline(TEXT("float2 gradient(float2 p)"), *TriangularKernel);
        Detail->Code.ReplaceInline(TEXT("n.gradient("), TEXT("n.simplexGradient("));
    }
    Material->GetEditorOnlyData()->Normal.Connect(0, Detail);
    if (RiverLabel == TEXT("Chilko") && !ConfigureChilkoDensityFoam(Material, AerationSignal))
    {
        Summary += TEXT("Chilko density foam could not locate the existing advected foam colour branch.\n");
        return nullptr;
    }
    Material->StateId = FGuid::NewGuid();
    Material->UpdateCachedExpressionData();
    Package->MarkPackageDirty();
    FSavePackageArgs Args;
    Args.TopLevelFlags = RF_Public | RF_Standalone;
    Args.SaveFlags = SAVE_NoError;
    const FString Filename = FPackageName::LongPackageNameToFilename(Path, FPackageName::GetAssetPackageExtension());
    if (!UPackage::SavePackage(Package, Material, *Filename, Args)) return nullptr;
    Summary += TEXT("Saved current-carried gradient normals with pixel-footprint filtering.\n");
    return Material;
}
} // namespace RaftSimEditorEnvironment
