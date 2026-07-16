#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
UMaterialInstanceDynamic* CreatePreviewColorMaterial(UObject* Outer, const FLinearColor& Color)
{
    UMaterialInterface* BaseMaterial = LoadOrCreatePreviewColorMaterial();
    if (!BaseMaterial)
    {
        BaseMaterial = LoadPreviewBaseMaterial();
    }

    if (BaseMaterial)
    {
        UMaterialInstanceDynamic* Material = UMaterialInstanceDynamic::Create(BaseMaterial, Outer);
        Material->SetVectorParameterValue(TEXT("PreviewColor"), Color);
        Material->SetVectorParameterValue(TEXT("Color"), Color);
        Material->SetVectorParameterValue(TEXT("BaseColor"), Color);
        Material->SetVectorParameterValue(TEXT("Albedo"), Color);
        return Material;
    }

    return nullptr;
}

UMaterialInstanceDynamic* CreatePreviewTranslucentColorMaterial(UObject* Outer, const FLinearColor& Color, float Opacity)
{
    UMaterialInterface* BaseMaterial = LoadOrCreatePreviewTranslucentColorMaterial();
    if (BaseMaterial)
    {
        UMaterialInstanceDynamic* Material = UMaterialInstanceDynamic::Create(BaseMaterial, Outer);
        Material->SetVectorParameterValue(TEXT("PreviewColor"), Color);
        Material->SetScalarParameterValue(TEXT("PreviewOpacity"), FMath::Clamp(Opacity, 0.02f, 0.85f));
        return Material;
    }

    return nullptr;
}

TArray<FVector> ComputePreviewMeshNormals(const TArray<FVector>& Vertices, const TArray<int32>& Triangles)
{
    TArray<FVector> Normals;
    Normals.Init(FVector::ZeroVector, Vertices.Num());

    for (int32 TriangleIndex = 0; TriangleIndex + 2 < Triangles.Num(); TriangleIndex += 3)
    {
        const int32 A = Triangles[TriangleIndex];
        const int32 B = Triangles[TriangleIndex + 1];
        const int32 C = Triangles[TriangleIndex + 2];
        if (!Vertices.IsValidIndex(A) || !Vertices.IsValidIndex(B) || !Vertices.IsValidIndex(C))
        {
            continue;
        }

        const FVector FaceNormal = FVector::CrossProduct(Vertices[B] - Vertices[A], Vertices[C] - Vertices[A]).GetSafeNormal();
        Normals[A] += FaceNormal;
        Normals[B] += FaceNormal;
        Normals[C] += FaceNormal;
    }

    for (FVector& Normal : Normals)
    {
        Normal = Normal.GetSafeNormal(UE_SMALL_NUMBER, FVector::UpVector);
        if (Normal.Z < 0.0f)
        {
            Normal *= -1.0f;
        }
    }

    return Normals;
}

bool LoadPreviewPngImage(const FString& RelativePath, FRaftSimPreviewImage& OutImage)
{
    OutImage = FRaftSimPreviewImage();
    if (RelativePath.IsEmpty())
    {
        return false;
    }

    const FString AbsolutePath = FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), RelativePath));
    TArray<uint8> CompressedImage;
    if (!FFileHelper::LoadFileToArray(CompressedImage, *AbsolutePath))
    {
        UE_LOG(LogRaftSimEditorEnvironment, Warning, TEXT("Failed to load preview drape image: %s"), *AbsolutePath);
        return false;
    }

    IImageWrapperModule& ImageWrapperModule =
        FModuleManager::LoadModuleChecked<IImageWrapperModule>(FName(TEXT("ImageWrapper")));
    TSharedPtr<IImageWrapper> ImageWrapper = ImageWrapperModule.CreateImageWrapper(EImageFormat::PNG, *AbsolutePath);
    if (!ImageWrapper.IsValid() || !ImageWrapper->SetCompressed(CompressedImage.GetData(), CompressedImage.Num()))
    {
        UE_LOG(LogRaftSimEditorEnvironment, Warning, TEXT("Failed to decode preview drape image header: %s"), *AbsolutePath);
        return false;
    }

    TArray<uint8> RawBgra;
    if (!ImageWrapper->GetRaw(ERGBFormat::BGRA, 8, RawBgra))
    {
        UE_LOG(LogRaftSimEditorEnvironment, Warning, TEXT("Failed to decode preview drape pixels: %s"), *AbsolutePath);
        return false;
    }

    OutImage.Width = ImageWrapper->GetWidth();
    OutImage.Height = ImageWrapper->GetHeight();
    if (OutImage.Width <= 0 || OutImage.Height <= 0 || RawBgra.Num() != OutImage.Width * OutImage.Height * 4)
    {
        UE_LOG(LogRaftSimEditorEnvironment, Warning, TEXT("Preview drape image dimensions are invalid: %s"), *AbsolutePath);
        OutImage = FRaftSimPreviewImage();
        return false;
    }

    OutImage.Pixels.Reserve(OutImage.Width * OutImage.Height);
    for (int32 PixelIndex = 0; PixelIndex < OutImage.Width * OutImage.Height; ++PixelIndex)
    {
        const int32 ByteIndex = PixelIndex * 4;
        OutImage.Pixels.Add(FLinearColor(
            static_cast<float>(RawBgra[ByteIndex + 2]) / 255.0f,
            static_cast<float>(RawBgra[ByteIndex + 1]) / 255.0f,
            static_cast<float>(RawBgra[ByteIndex]) / 255.0f,
            static_cast<float>(RawBgra[ByteIndex + 3]) / 255.0f));
    }

    return true;
}

void ApplyPreviewColor(UMeshComponent* Component, const FLinearColor& Color)
{
    if (!Component)
    {
        return;
    }

    if (UMaterialInstanceDynamic* Material = CreatePreviewColorMaterial(Component, Color))
    {
        const int32 MaterialCount = FMath::Max(1, Component->GetNumMaterials());
        for (int32 MaterialIndex = 0; MaterialIndex < MaterialCount; ++MaterialIndex)
        {
            Component->SetMaterial(MaterialIndex, Material);
        }
    }
}

void ApplyPreviewTranslucentColor(UMeshComponent* Component, const FLinearColor& Color, float Opacity)
{
    if (!Component)
    {
        return;
    }

    if (UMaterialInstanceDynamic* Material = CreatePreviewTranslucentColorMaterial(Component, Color, Opacity))
    {
        const int32 MaterialCount = FMath::Max(1, Component->GetNumMaterials());
        for (int32 MaterialIndex = 0; MaterialIndex < MaterialCount; ++MaterialIndex)
        {
            Component->SetMaterial(MaterialIndex, Material);
        }
    }
}

float SmoothPreviewStep(float Edge0, float Edge1, float Value)
{
    if (FMath::IsNearlyEqual(Edge0, Edge1))
    {
        return Value >= Edge1 ? 1.0f : 0.0f;
    }

    const float T = FMath::Clamp((Value - Edge0) / (Edge1 - Edge0), 0.0f, 1.0f);
    return T * T * (3.0f - 2.0f * T);
}

FLinearColor ClampPreviewColor(const FLinearColor& Color)
{
    return FLinearColor(
        FMath::Clamp(Color.R, 0.0f, 1.0f),
        FMath::Clamp(Color.G, 0.0f, 1.0f),
        FMath::Clamp(Color.B, 0.0f, 1.0f),
        FMath::Clamp(Color.A, 0.0f, 1.0f));
}

FLinearColor ScalePreviewColor(const FLinearColor& Color, float Scale)
{
    return ClampPreviewColor(FLinearColor(Color.R * Scale, Color.G * Scale, Color.B * Scale, Color.A));
}

float GetPreviewColorLuma(const FLinearColor& Color)
{
    return FMath::Max(0.001f, Color.R * 0.2126f + Color.G * 0.7152f + Color.B * 0.0722f);
}

FLinearColor SampleFirstPartyMaterialAtlasTile(
    const FRaftSimPreviewImage* Atlas,
    int32 TileIndex,
    float LocalU,
    float LocalV)
{
    if (!Atlas || !Atlas->IsValid())
    {
        return FLinearColor::Black;
    }

    constexpr int32 AtlasColumns = 3;
    constexpr int32 AtlasRows = 2;
    const int32 ClampedTileIndex = FMath::Clamp(TileIndex, 0, AtlasColumns * AtlasRows - 1);
    const int32 Column = ClampedTileIndex % AtlasColumns;
    const int32 Row = ClampedTileIndex / AtlasColumns;
    const float WrappedU = FMath::Fmod(FMath::Fmod(LocalU, 1.0f) + 1.0f, 1.0f);
    const float WrappedV = FMath::Fmod(FMath::Fmod(LocalV, 1.0f) + 1.0f, 1.0f);
    const float AtlasU = (static_cast<float>(Column) + WrappedU) / static_cast<float>(AtlasColumns);
    const float TopOriginAtlasV = (static_cast<float>(Row) + WrappedV) / static_cast<float>(AtlasRows);
    return Atlas->SampleRaw(AtlasU, 1.0f - TopOriginAtlasV);
}

FLinearColor ApplyFirstPartyMaterialAtlasTint(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* Atlas,
    int32 TileIndex,
    const FLinearColor& BaseColor,
    float LocalU,
    float LocalV,
    float Weight)
{
    if (!Atlas || !Atlas->IsValid() || Weight <= 0.0f)
    {
        return BaseColor;
    }

    FLinearColor AtlasColor = ClampPreviewColor(SampleFirstPartyMaterialAtlasTile(Atlas, TileIndex, LocalU, LocalV));
    AtlasColor.A = BaseColor.A;
    const float BaseLuma = GetPreviewColorLuma(BaseColor);
    const float AtlasLuma = GetPreviewColorLuma(AtlasColor);
    const float MinAtlasLuma = BaseLuma * (Spec.bHasWaterfalls ? 0.50f : 0.58f);
    const float MaxAtlasLuma = BaseLuma * (Spec.bDesertCanyon ? 1.28f : 1.22f);
    const float TargetAtlasLuma = FMath::Clamp(AtlasLuma, MinAtlasLuma, MaxAtlasLuma);
    AtlasColor = ScalePreviewColor(AtlasColor, TargetAtlasLuma / AtlasLuma);
    AtlasColor.A = BaseColor.A;

    return ClampPreviewColor(FMath::Lerp(BaseColor, AtlasColor, FMath::Clamp(Weight, 0.0f, 0.32f)));
}

float SampleFirstPartyMaterialAtlasPackedHeight(
    const FRaftSimPreviewImage* PackedAtlas,
    int32 TileIndex,
    float LocalU,
    float LocalV,
    float DefaultHeight)
{
    if (!PackedAtlas || !PackedAtlas->IsValid())
    {
        return DefaultHeight;
    }

    return FMath::Clamp(SampleFirstPartyMaterialAtlasTile(PackedAtlas, TileIndex, LocalU, LocalV).B, 0.0f, 1.0f);
}

FLinearColor ApplyFirstPartyMaterialAtlasSurfaceResponse(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* NormalAtlas,
    const FRaftSimPreviewImage* PackedAtlas,
    int32 TileIndex,
    const FLinearColor& BaseColor,
    float LocalU,
    float LocalV,
    float Weight)
{
    if (Weight <= 0.0f)
    {
        return BaseColor;
    }

    const float ClampedWeight = FMath::Clamp(Weight, 0.0f, 0.30f);
    float ResponseScale = 1.0f;
    if (PackedAtlas && PackedAtlas->IsValid())
    {
        const FLinearColor Packed = ClampPreviewColor(SampleFirstPartyMaterialAtlasTile(PackedAtlas, TileIndex, LocalU, LocalV));
        const float AmbientOcclusion = FMath::Clamp(Packed.R, 0.0f, 1.0f);
        const float Roughness = FMath::Clamp(Packed.G, 0.0f, 1.0f);
        const float Height = FMath::Clamp(Packed.B, 0.0f, 1.0f);
        ResponseScale *= FMath::Clamp(
            1.0f - (1.0f - AmbientOcclusion) * 0.22f * ClampedWeight +
                (Roughness - 0.5f) * 0.10f * ClampedWeight +
                (Height - 0.5f) * 0.18f * ClampedWeight,
            0.86f,
            1.12f);
    }
    if (NormalAtlas && NormalAtlas->IsValid())
    {
        const FLinearColor Normal = ClampPreviewColor(SampleFirstPartyMaterialAtlasTile(NormalAtlas, TileIndex, LocalU, LocalV));
        const float SlopeEnergy = FMath::Clamp(FMath::Abs(Normal.R - 0.5f) + FMath::Abs(Normal.G - 0.5f), 0.0f, 1.0f);
        const float UpFacing = FMath::Clamp(Normal.B, 0.0f, 1.0f);
        ResponseScale *= FMath::Clamp(
            1.0f + SlopeEnergy * (Spec.bDesertCanyon ? 0.10f : 0.075f) * ClampedWeight -
                (1.0f - UpFacing) * 0.12f * ClampedWeight,
            0.90f,
            1.10f);
    }

    FLinearColor Result = ScalePreviewColor(BaseColor, ResponseScale);
    Result.A = BaseColor.A;
    return ClampPreviewColor(Result);
}

float GetFirstPartyMaterialAtlasMicroReliefCm(
    const FRaftSimPreviewImage* PackedAtlas,
    int32 TileIndex,
    float LocalU,
    float LocalV,
    float AmplitudeCm,
    float Weight)
{
    if (!PackedAtlas || !PackedAtlas->IsValid() || Weight <= 0.0f)
    {
        return 0.0f;
    }

    const float Height = SampleFirstPartyMaterialAtlasPackedHeight(PackedAtlas, TileIndex, LocalU, LocalV);
    return (Height - 0.5f) * AmplitudeCm * FMath::Clamp(Weight, 0.0f, 0.35f);
}

FLinearColor NormalizePreviewSourceDrapeAlbedo(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& RawColor,
    float SourceWaterT,
    float SourceVegetationT,
    float MaterialBlend)
{
    FLinearColor SourceColor = ClampPreviewColor(RawColor);
    SourceColor.A = 1.0f;

    const float Luma = FMath::Max(0.001f, SourceColor.R * 0.2126f + SourceColor.G * 0.7152f + SourceColor.B * 0.0722f);
    const float MinLuma = Spec.bDesertCanyon ? 0.23f : (Spec.bHasWaterfalls ? 0.125f : 0.18f);
    const float MaxLuma = Spec.bDesertCanyon ? 0.38f : (Spec.bHasWaterfalls ? 0.24f : 0.34f);
    float TargetLuma = Luma;
    if (Luma < MinLuma)
    {
        TargetLuma = FMath::Lerp(MinLuma, Luma, 0.22f);
        const float ShadowLiftT = FMath::Clamp((MinLuma - Luma) / MinLuma, 0.0f, 1.0f);
        const FLinearColor ShadowFill = Spec.bDesertCanyon
            ? FLinearColor(TargetLuma * 1.17f, TargetLuma * 0.92f, TargetLuma * 0.66f, 1.0f)
            : (Spec.bHasWaterfalls
                   ? FLinearColor(TargetLuma * 0.50f, TargetLuma * 0.86f, TargetLuma * 0.54f, 1.0f)
                   : FLinearColor(TargetLuma * 0.92f, TargetLuma * 0.86f, TargetLuma * 0.64f, 1.0f));
        SourceColor = FMath::Lerp(SourceColor, ShadowFill, FMath::Clamp(0.68f + ShadowLiftT * 0.24f, 0.0f, 0.92f));
    }
    else if (Luma > MaxLuma)
    {
        TargetLuma = FMath::Lerp(MaxLuma, Luma, 0.06f);
    }
    const float AdjustedLuma = FMath::Max(
        0.001f,
        SourceColor.R * 0.2126f + SourceColor.G * 0.7152f + SourceColor.B * 0.0722f);
    SourceColor = ScalePreviewColor(SourceColor, TargetLuma / AdjustedLuma);

    const FLinearColor BankMaterial = Spec.bDesertCanyon
        ? FLinearColor(0.48f, 0.32f, 0.20f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.060f, 0.105f, 0.060f) : Spec.TerrainColor);
    const FLinearColor VegetationMaterial = Spec.bDesertCanyon
        ? FLinearColor(0.27f, 0.29f, 0.15f)
        : ScalePreviewColor(Spec.FoliageColor, Spec.bHasWaterfalls ? 0.86f : 0.78f);
    const FLinearColor WetMaterial = Spec.bDesertCanyon
        ? FLinearColor(0.23f, 0.19f, 0.14f)
        : FMath::Lerp(ScalePreviewColor(Spec.RockColor, 0.42f), ScalePreviewColor(Spec.WaterColor, 0.30f), 0.36f);
    FLinearColor GuidedMaterial = FMath::Lerp(
        BankMaterial,
        VegetationMaterial,
        FMath::Clamp(SourceVegetationT * (Spec.bDesertCanyon ? 0.34f : 0.68f), 0.0f, 0.74f));
    GuidedMaterial = FMath::Lerp(
        GuidedMaterial,
        WetMaterial,
        FMath::Clamp(SourceWaterT * (Spec.bDesertCanyon ? 0.32f : 0.42f), 0.0f, 0.48f));

    return ClampPreviewColor(FMath::Lerp(SourceColor, GuidedMaterial, FMath::Clamp(MaterialBlend, 0.0f, 1.0f)));
}

FLinearColor NormalizePreviewTerrainProxyPatchColor(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& RawColor)
{
    FLinearColor Color = ClampPreviewColor(RawColor);
    Color.A = RawColor.A;

    const float Luma = GetPreviewColorLuma(Color);
    const float MinLuma = Spec.bDesertCanyon ? 0.300f : (Spec.bHasWaterfalls ? 0.220f : 0.260f);
    if (Luma >= MinLuma)
    {
        return Color;
    }

    const FLinearColor FillColor = Spec.bDesertCanyon
        ? FLinearColor(0.42f, 0.30f, 0.19f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.075f, 0.185f, 0.085f, Color.A)
                                : FLinearColor(0.27f, 0.25f, 0.17f, Color.A));
    const float LiftT = FMath::Clamp((MinLuma - Luma) / MinLuma, 0.0f, 1.0f);
    FLinearColor LiftedColor = FMath::Lerp(Color, FillColor, FMath::Clamp(LiftT * 0.78f, 0.0f, 0.78f));
    const float LiftedLuma = GetPreviewColorLuma(LiftedColor);
    const float TargetLuma = FMath::Lerp(MinLuma, Luma, Spec.bHasWaterfalls ? 0.18f : 0.14f);
    LiftedColor = ScalePreviewColor(LiftedColor, TargetLuma / LiftedLuma);
    LiftedColor.A = Color.A;
    return ClampPreviewColor(LiftedColor);
}

FLinearColor ApplyPreviewIntegratedTerrainCorridorTexture(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& RawColor,
    float X,
    float Y,
    float BankT,
    float CanyonT,
    float WetT,
    float SourceWaterT,
    float SourceVegetationT,
    float ChannelOffset,
    float ActiveRiverHalfWidth,
    float CellSeed)
{
    FLinearColor Color = ClampPreviewColor(RawColor);
    const float CorridorT = FMath::Clamp(
        SmoothPreviewStep(
            ActiveRiverHalfWidth + 110.0f,
            ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 2300.0f : 1420.0f),
            ChannelOffset) *
            (0.34f + BankT * 0.24f + CanyonT * 0.34f +
             SourceVegetationT * (Spec.bDesertCanyon ? 0.08f : 0.30f)) *
            (1.0f - FMath::Clamp(SourceWaterT * 0.72f + WetT * 0.18f, 0.0f, 0.82f)),
        0.0f,
        1.0f);
    if (CorridorT <= KINDA_SMALL_NUMBER)
    {
        return Color;
    }

    const float FineTextureNoise = FMath::Clamp(
        0.50f +
            0.31f * FMath::Sin(X * 0.018f + Y * (Spec.bDesertCanyon ? 0.011f : 0.017f) + CellSeed * 0.73f) +
            0.23f * FMath::Sin(X * 0.043f - Y * (Spec.bDesertCanyon ? 0.022f : 0.031f) + SourceVegetationT * 2.4f) +
            0.15f * FMath::Sin((X + Y) * 0.079f + CellSeed * 1.31f),
        0.0f,
        1.0f);
    const float FacetTextureNoise = FMath::Clamp(CellSeed * 0.46f + FineTextureNoise * 0.54f, 0.0f, 1.0f);

    FLinearColor TextureShadow;
    FLinearColor TextureMineral;
    FLinearColor TextureSunFace;
    FLinearColor TextureVegetation;
    FLinearColor TextureWetToe;
    if (Spec.bDesertCanyon)
    {
        TextureShadow = FLinearColor(0.245f, 0.145f, 0.085f, Color.A);
        TextureMineral = FLinearColor(0.665f, 0.390f, 0.205f, Color.A);
        TextureSunFace = FLinearColor(0.825f, 0.635f, 0.365f, Color.A);
        TextureVegetation = FLinearColor(0.375f, 0.400f, 0.235f, Color.A);
        TextureWetToe = FLinearColor(0.310f, 0.215f, 0.135f, Color.A);
    }
    else if (Spec.bHasWaterfalls)
    {
        TextureShadow = FLinearColor(0.020f, 0.070f, 0.030f, Color.A);
        TextureMineral = FLinearColor(0.085f, 0.145f, 0.060f, Color.A);
        TextureSunFace = FLinearColor(0.145f, 0.360f, 0.105f, Color.A);
        TextureVegetation = FLinearColor(0.070f, 0.310f, 0.075f, Color.A);
        TextureWetToe = FLinearColor(0.055f, 0.115f, 0.065f, Color.A);
    }
    else
    {
        TextureShadow = FLinearColor(0.135f, 0.130f, 0.075f, Color.A);
        TextureMineral = FLinearColor(0.430f, 0.390f, 0.215f, Color.A);
        TextureSunFace = FLinearColor(0.560f, 0.505f, 0.265f, Color.A);
        TextureVegetation = FLinearColor(0.210f, 0.365f, 0.125f, Color.A);
        TextureWetToe = FLinearColor(0.170f, 0.230f, 0.120f, Color.A);
    }

    const FLinearColor PaletteColor = FacetTextureNoise < 0.20f
        ? TextureShadow
        : (FacetTextureNoise < 0.44f
               ? TextureWetToe
               : (FacetTextureNoise < 0.66f
                      ? TextureMineral
                      : (FacetTextureNoise < 0.84f ? TextureVegetation : TextureSunFace)));
    const float PaletteBlend = FMath::Clamp(
        CorridorT *
            (Spec.bDesertCanyon ? 0.56f : (Spec.bHasWaterfalls ? 0.48f : 0.46f)) *
            (0.68f + FMath::Abs(FacetTextureNoise - 0.5f) * 0.62f),
        0.0f,
        Spec.bDesertCanyon ? 0.62f : 0.54f);
    Color = FMath::Lerp(Color, PaletteColor, PaletteBlend);

    const float LumaScale = FMath::Clamp(
        0.82f + FineTextureNoise * 0.34f + CellSeed * 0.10f,
        Spec.bHasWaterfalls ? 0.66f : 0.70f,
        Spec.bDesertCanyon ? 1.48f : 1.40f);
    Color = ScalePreviewColor(Color, LumaScale);

    const float LumaFloor =
        (Spec.bDesertCanyon ? 0.330f : (Spec.bHasWaterfalls ? 0.185f : 0.245f)) +
        SourceVegetationT * (Spec.bDesertCanyon ? 0.006f : 0.024f) +
        CanyonT * (Spec.bDesertCanyon ? 0.028f : 0.010f);
    const float ExistingLuma = GetPreviewColorLuma(Color);
    if (ExistingLuma < LumaFloor)
    {
        const FLinearColor FillColor = Spec.bDesertCanyon
            ? FLinearColor(0.455f, 0.305f, 0.180f, Color.A)
            : (Spec.bHasWaterfalls ? FLinearColor(0.075f, 0.185f, 0.075f, Color.A)
                                    : FLinearColor(0.295f, 0.285f, 0.155f, Color.A));
        Color = FMath::Lerp(
            Color,
            FillColor,
            FMath::Clamp(((LumaFloor - ExistingLuma) / LumaFloor) * CorridorT * 0.68f, 0.0f, 0.58f));
    }

    Color.A = RawColor.A;
    return ClampPreviewColor(Color);
}

FLinearColor ApplyPreviewSourceAwareTerrainSurfaceGranularity(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& RawColor,
    float X,
    float Y,
    float BankT,
    float CanyonT,
    float WetT,
    float SourceWaterT,
    float SourceVegetationT,
    float ChannelOffset,
    float ActiveRiverHalfWidth,
    float CellSeed)
{
    FLinearColor Color = ClampPreviewColor(RawColor);
    const float FirstPartyTerrainSurfaceGranularityT = FMath::Clamp(
        SmoothPreviewStep(
            ActiveRiverHalfWidth + 95.0f,
            ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 2600.0f : 1560.0f),
            ChannelOffset) *
            (0.38f + BankT * 0.28f + CanyonT * 0.34f +
             SourceVegetationT * (Spec.bDesertCanyon ? 0.10f : 0.34f)) *
            (1.0f - FMath::Clamp(SourceWaterT * 0.78f + WetT * 0.22f, 0.0f, 0.86f)),
        0.0f,
        1.0f);
    if (FirstPartyTerrainSurfaceGranularityT <= KINDA_SMALL_NUMBER)
    {
        return Color;
    }

    const float FirstPartyTerrainSurfaceGranularityNoise = FMath::Clamp(
        0.50f +
            0.24f * FMath::Sin(X * 0.031f + Y * (Spec.bDesertCanyon ? 0.019f : 0.028f) + CellSeed * 2.7f) +
            0.22f * FMath::Sin(X * 0.071f - Y * (Spec.bDesertCanyon ? 0.040f : 0.052f) + SourceVegetationT * 4.3f) +
            0.16f * FMath::Sin((X - Y) * 0.113f + CellSeed * 5.1f),
        0.0f,
        1.0f);
    const float FirstPartyTerrainSurfaceGranularityCell =
        FMath::Clamp(CellSeed * 0.58f + FirstPartyTerrainSurfaceGranularityNoise * 0.42f, 0.0f, 1.0f);

    FLinearColor DarkFleck;
    FLinearColor MidFleck;
    FLinearColor BrightFleck;
    FLinearColor OrganicFleck;
    if (Spec.bDesertCanyon)
    {
        DarkFleck = FLinearColor(0.225f, 0.135f, 0.080f, Color.A);
        MidFleck = FLinearColor(0.500f, 0.315f, 0.175f, Color.A);
        BrightFleck = FLinearColor(0.735f, 0.560f, 0.315f, Color.A);
        OrganicFleck = FLinearColor(0.340f, 0.360f, 0.205f, Color.A);
    }
    else if (Spec.bHasWaterfalls)
    {
        DarkFleck = FLinearColor(0.014f, 0.052f, 0.026f, Color.A);
        MidFleck = FLinearColor(0.055f, 0.125f, 0.050f, Color.A);
        BrightFleck = FLinearColor(0.130f, 0.270f, 0.090f, Color.A);
        OrganicFleck = FLinearColor(0.034f, 0.185f, 0.052f, Color.A);
    }
    else
    {
        DarkFleck = FLinearColor(0.120f, 0.115f, 0.070f, Color.A);
        MidFleck = FLinearColor(0.285f, 0.260f, 0.145f, Color.A);
        BrightFleck = FLinearColor(0.475f, 0.430f, 0.230f, Color.A);
        OrganicFleck = FLinearColor(0.155f, 0.275f, 0.090f, Color.A);
    }

    const FLinearColor GranularityColor = FirstPartyTerrainSurfaceGranularityCell < 0.22f
        ? DarkFleck
        : (FirstPartyTerrainSurfaceGranularityCell < 0.52f
               ? MidFleck
               : (FirstPartyTerrainSurfaceGranularityCell < (Spec.bDesertCanyon ? 0.76f : 0.70f)
                      ? OrganicFleck
                      : BrightFleck));
    const float FirstPartyTerrainGranularityBlend = FMath::Clamp(
        FirstPartyTerrainSurfaceGranularityT *
            (Spec.bDesertCanyon ? 0.34f : (Spec.bHasWaterfalls ? 0.32f : 0.30f)) *
            (0.66f + FMath::Abs(FirstPartyTerrainSurfaceGranularityCell - 0.5f) * 0.96f),
        0.0f,
        Spec.bDesertCanyon ? 0.36f : 0.33f);
    Color = FMath::Lerp(Color, GranularityColor, FirstPartyTerrainGranularityBlend);

    const float FirstPartyTerrainGranularityLumaScale = FMath::Clamp(
        0.86f + FirstPartyTerrainSurfaceGranularityNoise * 0.28f + CellSeed * 0.08f,
        Spec.bHasWaterfalls ? 0.68f : 0.72f,
        Spec.bDesertCanyon ? 1.42f : 1.36f);
    Color = ScalePreviewColor(Color, FirstPartyTerrainGranularityLumaScale);
    Color.A = RawColor.A;
    return ClampPreviewColor(Color);
}

FLinearColor GetPreviewSoftTerrainPatchFeatherBaseColor(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    float X,
    float Y,
    float Phase)
{
    const float BroadNoise = FMath::Clamp(
        0.50f + 0.34f * FMath::Sin(Phase * 0.67f + X * 0.00042f) +
            0.16f * FMath::Sin(Phase * 1.31f - Y * 0.00058f),
        0.0f,
        1.0f);

    FLinearColor BaseColor;
    if (Spec.bDesertCanyon)
    {
        BaseColor = FMath::Lerp(FLinearColor(0.33f, 0.23f, 0.15f), FLinearColor(0.57f, 0.40f, 0.24f), BroadNoise);
    }
    else if (Spec.bHasWaterfalls)
    {
        BaseColor = FMath::Lerp(FLinearColor(0.028f, 0.060f, 0.038f), FLinearColor(0.070f, 0.130f, 0.060f), BroadNoise);
        BaseColor = FMath::Lerp(BaseColor, ScalePreviewColor(Spec.FoliageColor, 0.52f), 0.24f);
    }
    else
    {
        BaseColor = FMath::Lerp(FLinearColor(0.18f, 0.17f, 0.12f), FLinearColor(0.30f, 0.28f, 0.16f), BroadNoise);
        BaseColor = FMath::Lerp(BaseColor, ScalePreviewColor(Spec.TerrainColor, 0.88f), 0.38f);
    }

    const float LumaJitter = 0.94f + 0.07f * FMath::Sin(Phase * 0.43f + X * 0.00071f - Y * 0.00039f);
    return NormalizePreviewTerrainProxyPatchColor(Spec, ScalePreviewColor(BaseColor, LumaJitter));
}

float GetPreviewSoftTerrainPatchCoverage(float U, float V, float Phase)
{
    const float StartFeather = SmoothPreviewStep(0.035f, 0.24f, U);
    const float EndFeather = 1.0f - SmoothPreviewStep(0.76f, 0.965f, U);
    const float CrossCenterT = 1.0f - FMath::Clamp(FMath::Abs(V - 0.5f) * 2.0f, 0.0f, 1.0f);
    const float CrossFeather = SmoothPreviewStep(0.0f, 0.70f, CrossCenterT);
    const float OrganicFeather = FMath::Clamp(
        0.82f + 0.12f * FMath::Sin(Phase + U * 5.9f + V * 2.7f) +
            0.06f * FMath::Sin(Phase * 0.47f + U * 13.0f - V * 4.1f),
        0.62f,
        1.0f);
    return FMath::Clamp(StartFeather * EndFeather * CrossFeather * OrganicFeather, 0.0f, 1.0f);
}

FLinearColor BlendPreviewSoftTerrainPatchColor(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& FeatureColor,
    float X,
    float Y,
    float U,
    float V,
    float Phase,
    float Coverage)
{
    const FLinearColor FeatherBase = GetPreviewSoftTerrainPatchFeatherBaseColor(Spec, X, Y, Phase);
    const float MaxFeatureBlend = Spec.bDesertCanyon ? 0.14f : (Spec.bHasWaterfalls ? 0.12f : 0.13f);
    const float Blend = FMath::Clamp(Coverage * MaxFeatureBlend, 0.0f, 0.16f);
    return ClampPreviewColor(FMath::Lerp(FeatherBase, FeatureColor, Blend));
}

float GetPreviewTerrainNormalSofteningBlend(const FRaftSimEnvironmentPreviewSpec& Spec)
{
    return Spec.TerrainNormalSofteningBlend;
}

void SoftenPreviewTerrainNormals(TArray<FVector>& Normals, float UpBlend)
{
    const float Blend = FMath::Clamp(UpBlend, 0.0f, 0.85f);
    for (FVector& Normal : Normals)
    {
        FVector SourceNormal = Normal.GetSafeNormal(UE_SMALL_NUMBER, FVector::UpVector);
        if (SourceNormal.Z < 0.0f)
        {
            SourceNormal *= -1.0f;
        }
        Normal = (SourceNormal * (1.0f - Blend) + FVector::UpVector * Blend).GetSafeNormal();
    }
}

float GetPreviewRiverCenterY(const FRaftSimEnvironmentPreviewSpec& Spec, float X)
{
    const float Primary = FMath::Sin((X + 3800.0f) * 0.00043f) * Spec.BendAmplitudeCm;
    const float Secondary = FMath::Sin((X - 600.0f) * 0.00019f) * Spec.BendAmplitudeCm * 0.35f;
    return Primary + Secondary;
}

float GetPreviewActiveRiverHalfWidthCm(const FRaftSimEnvironmentPreviewSpec& Spec)
{
    return FMath::Max(80.0f, Spec.RiverHalfWidthCm * FMath::Max(0.35f, Spec.FlowWidthScale));
}

float GetPreviewWaterSurfaceBaseZCm(const FRaftSimEnvironmentPreviewSpec& Spec)
{
    return 10.0f + Spec.FlowWaterLevelOffsetCm;
}

void GetPreviewMaskUv(const FRaftSimEnvironmentPreviewSpec& Spec, float X, float Y, float& OutU, float& OutV)
{
    const float MinX = -5800.0f;
    const float MaxX = 26500.0f;
    const float HalfWidth = Spec.bDesertCanyon ? 4300.0f : 2750.0f;
    OutU = FMath::Clamp((X - MinX) / (MaxX - MinX), 0.0f, 1.0f);
    OutV = FMath::Clamp((Y + HalfWidth) / (HalfWidth * 2.0f), 0.0f, 1.0f);
}

float SamplePreviewMaskAtWorld(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* Mask,
    float X,
    float Y)
{
    if (!Mask || !Mask->IsValid())
    {
        return 0.0f;
    }

    float U = 0.0f;
    float V = 0.0f;
    GetPreviewMaskUv(Spec, X, Y, U, V);
    return Mask->SampleLuma(U, V);
}

float SamplePreviewTerrainReliefCm(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    float X,
    float Y,
    float ChannelOffset)
{
    if (!TerrainRelief || !TerrainRelief->IsValid() || Spec.TerrainReliefAmplitudeCm <= 0.0f)
    {
        return 0.0f;
    }

    const float MinX = -5800.0f;
    const float MaxX = 26500.0f;
    const float HalfWidth = Spec.bDesertCanyon ? 4300.0f : 2750.0f;
    const float U = FMath::Clamp((X - MinX) / (MaxX - MinX), 0.0f, 1.0f);
    const float V = FMath::Clamp((Y + HalfWidth) / (HalfWidth * 2.0f), 0.0f, 1.0f);
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float ReliefMask = SmoothPreviewStep(
        ActiveRiverHalfWidth + 110.0f,
        ActiveRiverHalfWidth + Spec.BankWidthCm + 740.0f,
        ChannelOffset);
    return (TerrainRelief->SampleLuma(U, V) - 0.5f) * Spec.TerrainReliefAmplitudeCm * ReliefMask;
}

float SamplePreviewHeightfieldCm(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* HeightfieldPreview,
    float X,
    float Y,
    float ChannelOffset)
{
    if (!HeightfieldPreview || !HeightfieldPreview->IsValid() || Spec.HeightfieldPreviewAmplitudeCm <= 0.0f)
    {
        return 0.0f;
    }

    const float MinX = -5800.0f;
    const float MaxX = 26500.0f;
    const float HalfWidth = Spec.bDesertCanyon ? 4300.0f : 2750.0f;
    const float U = FMath::Clamp((X - MinX) / (MaxX - MinX), 0.0f, 1.0f);
    const float V = FMath::Clamp((Y + HalfWidth) / (HalfWidth * 2.0f), 0.0f, 1.0f);
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const auto SampleSeamFeatheredLuma = [HeightfieldPreview, &Spec](float SampleU, float SampleV)
    {
        const float Feather = FMath::Clamp(Spec.HeightfieldSeamFeatherUv, 0.0f, 0.12f);
        const auto SampleAcrossU = [HeightfieldPreview, Feather](float UValue, float VValue)
        {
            const float DistanceToSeam = FMath::Abs(UValue - 0.5f);
            if (Feather <= KINDA_SMALL_NUMBER || DistanceToSeam >= Feather)
            {
                return HeightfieldPreview->SampleLumaBilinear(UValue, VValue);
            }

            const float Left = HeightfieldPreview->SampleLumaBilinear(0.5f - Feather, VValue);
            const float Right = HeightfieldPreview->SampleLumaBilinear(0.5f + Feather, VValue);
            return FMath::Lerp(Left, Right, FMath::Clamp((UValue - (0.5f - Feather)) / (2.0f * Feather), 0.0f, 1.0f));
        };

        const float DistanceToVSeam = FMath::Abs(SampleV - 0.5f);
        if (Feather <= KINDA_SMALL_NUMBER || DistanceToVSeam >= Feather)
        {
            return SampleAcrossU(SampleU, SampleV);
        }

        const float Lower = SampleAcrossU(SampleU, 0.5f - Feather);
        const float Upper = SampleAcrossU(SampleU, 0.5f + Feather);
        return FMath::Lerp(Lower, Upper, FMath::Clamp((SampleV - (0.5f - Feather)) / (2.0f * Feather), 0.0f, 1.0f));
    };
    const float HeightfieldMask = SmoothPreviewStep(
        ActiveRiverHalfWidth + 45.0f,
        ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 920.0f : 560.0f),
        ChannelOffset);
    const float SourceHeight = SampleSeamFeatheredLuma(U, V);
    const float FineRadiusU = 4.0f / static_cast<float>(FMath::Max(1, HeightfieldPreview->Width - 1));
    const float FineRadiusV = 4.0f / static_cast<float>(FMath::Max(1, HeightfieldPreview->Height - 1));
    const float BroadRadiusU = FineRadiusU * 3.5f;
    const float BroadRadiusV = FineRadiusV * 3.5f;
    const float FineMean = 0.25f * (
        SampleSeamFeatheredLuma(U - FineRadiusU, V) +
        SampleSeamFeatheredLuma(U + FineRadiusU, V) +
        SampleSeamFeatheredLuma(U, V - FineRadiusV) +
        SampleSeamFeatheredLuma(U, V + FineRadiusV));
    const float BroadMean = 0.25f * (
        SampleSeamFeatheredLuma(U - BroadRadiusU, V) +
        SampleSeamFeatheredLuma(U + BroadRadiusU, V) +
        SampleSeamFeatheredLuma(U, V - BroadRadiusV) +
        SampleSeamFeatheredLuma(U, V + BroadRadiusV));
    const float SourceLocalRelief = FMath::Clamp(
        (SourceHeight - FineMean) * 0.62f + (SourceHeight - BroadMean) * 0.38f,
        -0.12f,
        0.12f);
    const float MacroReliefCm = (SourceHeight - 0.5f) * Spec.HeightfieldPreviewAmplitudeCm;
    const float LocalReliefCm = SourceLocalRelief * Spec.HeightfieldLocalReliefAmplitudeCm;
    return (MacroReliefCm + LocalReliefCm) * HeightfieldMask;
}

float SamplePreviewBankUndercutShelfReliefCm(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    float X,
    float Y,
    float ChannelOffset)
{
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float WetBankScale = FMath::Max(0.35f, Spec.FlowWetBankScale);
    const float BankDistance = FMath::Max(0.0f, ChannelOffset - ActiveRiverHalfWidth);
    const float BankToeT = 1.0f - FMath::Clamp(
        FMath::Abs(BankDistance - 115.0f * WetBankScale) / FMath::Max(1.0f, 210.0f * WetBankScale),
        0.0f,
        1.0f);
    const float ShelfT = SmoothPreviewStep(120.0f * WetBankScale, 420.0f * WetBankScale, BankDistance) *
        (1.0f - SmoothPreviewStep(640.0f * WetBankScale, 1120.0f * WetBankScale, BankDistance));
    const float RootBenchT = SmoothPreviewStep(
        ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 360.0f : 260.0f),
        ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 940.0f : 620.0f),
        ChannelOffset);
    const float SideSign = Y >= GetPreviewRiverCenterY(Spec, X) ? 1.0f : -1.0f;
    const float LongNoise = 0.55f + 0.45f * FMath::Sin(X * 0.0027f + SideSign * 1.73f);
    const float CrossNoise = 0.50f + 0.50f * FMath::Sin(X * 0.0061f + Y * 0.0038f);
    const float UndercutDrop = (Spec.bDesertCanyon ? 20.0f : (Spec.bHasWaterfalls ? 36.0f : 26.0f)) *
        BankToeT * (0.58f + 0.42f * LongNoise);
    const float ShelfLift = (Spec.bDesertCanyon ? 58.0f : (Spec.bHasWaterfalls ? 42.0f : 36.0f)) *
        ShelfT * (0.46f + 0.54f * CrossNoise);
    const float RootBenchLift = Spec.bHasWaterfalls
        ? 34.0f * RootBenchT * (0.40f + 0.60f * LongNoise)
        : (Spec.bDesertCanyon ? 22.0f : 16.0f) * RootBenchT * (0.30f + 0.70f * CrossNoise);
    return ShelfLift + RootBenchLift - UndercutDrop;
}

float GetPreviewTerrainHeightCm(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    float X,
    float Y,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview)
{
    const float CenterY = GetPreviewRiverCenterY(Spec, X);
    const float Offset = FMath::Abs(Y - CenterY);
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float InnerBank = ActiveRiverHalfWidth;
    const float OuterBank = ActiveRiverHalfWidth + Spec.BankWidthCm;
    const float CanyonShoulder = OuterBank + (Spec.bDesertCanyon ? 1300.0f : 720.0f);
    const float BankT = SmoothPreviewStep(InnerBank, OuterBank, Offset);
    const float CanyonT = SmoothPreviewStep(OuterBank, CanyonShoulder, Offset);
    const float DownstreamSlope = -0.004f * (X + 5200.0f);
    const float GravelNoise =
        FMath::Sin(X * 0.0048f + Y * 0.0021f) * 18.0f + FMath::Sin(X * 0.0014f - Y * 0.0044f) * 11.0f;
    const float BankLift = Spec.bDesertCanyon ? 250.0f : 145.0f;
    const float CanyonLift = Spec.CanyonHeightCm * (Spec.bDesertCanyon ? 0.72f : 0.38f);

    return -82.0f + DownstreamSlope + BankT * BankLift + CanyonT * CanyonLift +
        GravelNoise * (0.35f + BankT * 0.75f) +
        SamplePreviewBankUndercutShelfReliefCm(Spec, X, Y, Offset) +
        SamplePreviewHeightfieldCm(Spec, HeightfieldPreview, X, Y, Offset) +
        SamplePreviewTerrainReliefCm(Spec, TerrainRelief, X, Y, Offset);
}

FLinearColor ApplyPreviewSourceAwareTerrainPhotoMottle(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& RawColor,
    float X,
    float Y,
    float BankT,
    float CanyonT,
    float WetT,
    float SourceWaterT,
    float SourceVegetationT)
{
    FLinearColor Color = ClampPreviewColor(RawColor);
    const float BroadMottle = FMath::Clamp(
        0.50f + 0.24f * FMath::Sin(X * 0.0021f + Y * 0.0038f) +
            0.18f * FMath::Sin(X * 0.0047f - Y * 0.0019f) +
            0.08f * FMath::Sin((X + Y) * 0.0093f),
        0.0f,
        1.0f);
    const float FineMottle = FMath::Clamp(
        0.50f + 0.28f * FMath::Sin(X * 0.020f + Y * 0.017f) +
            0.18f * FMath::Sin(X * 0.037f - Y * 0.029f),
        0.0f,
        1.0f);
    const float SurfaceCoverage = FMath::Clamp(
        (BankT * 0.52f + CanyonT * 0.58f + WetT * 0.18f +
         SourceVegetationT * (Spec.bDesertCanyon ? 0.08f : 0.24f)) *
            (1.0f - SourceWaterT * 0.32f),
        0.0f,
        1.0f);

    FLinearColor ShadowColor;
    FLinearColor HighlightColor;
    FLinearColor MaterialFleckColor;
    if (Spec.bDesertCanyon)
    {
        ShadowColor = FLinearColor(0.28f, 0.19f, 0.12f, Color.A);
        HighlightColor = FLinearColor(0.66f, 0.50f, 0.31f, Color.A);
        MaterialFleckColor = FLinearColor(0.43f, 0.27f, 0.17f, Color.A);
    }
    else if (Spec.bHasWaterfalls)
    {
        ShadowColor = FLinearColor(0.030f, 0.066f, 0.044f, Color.A);
        HighlightColor = FLinearColor(0.095f, 0.170f, 0.075f, Color.A);
        MaterialFleckColor = FLinearColor(0.080f, 0.070f, 0.044f, Color.A);
    }
    else
    {
        ShadowColor = FLinearColor(0.17f, 0.165f, 0.125f, Color.A);
        HighlightColor = FLinearColor(0.34f, 0.31f, 0.20f, Color.A);
        MaterialFleckColor = FLinearColor(0.24f, 0.25f, 0.145f, Color.A);
    }

    Color = FMath::Lerp(
        Color,
        ShadowColor,
        FMath::Clamp((1.0f - BroadMottle) * SurfaceCoverage * (Spec.bHasWaterfalls ? 0.10f : 0.13f), 0.0f, 0.14f));
    Color = FMath::Lerp(
        Color,
        HighlightColor,
        FMath::Clamp(BroadMottle * SurfaceCoverage * (Spec.bDesertCanyon ? 0.15f : 0.10f), 0.0f, 0.16f));
    Color = FMath::Lerp(
        Color,
        MaterialFleckColor,
        FMath::Clamp(FineMottle * SurfaceCoverage * (Spec.bHasWaterfalls ? 0.18f : 0.12f), 0.0f, 0.18f));

    const FLinearColor WetToeColor = Spec.bDesertCanyon
        ? FLinearColor(0.25f, 0.19f, 0.13f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.018f, 0.050f, 0.040f, Color.A)
                                : FLinearColor(0.12f, 0.145f, 0.115f, Color.A));
    Color = FMath::Lerp(
        Color,
        WetToeColor,
        FMath::Clamp(FMath::Max(WetT * 0.18f, SourceWaterT * 0.20f) * SurfaceCoverage, 0.0f, 0.24f));

    return ClampPreviewColor(Color);
}

FLinearColor ApplyPreviewSourceConditionedFarBankAlbedoCalibration(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& RawColor,
    const FLinearColor& SourceDrapeColor,
    bool bHasSourceDrapeColor,
    float X,
    float Y,
    float BankT,
    float CanyonT,
    float WetT,
    float SourceWaterT,
    float SourceVegetationT,
    float ChannelOffset,
    float ActiveRiverHalfWidth)
{
    FLinearColor Color = ClampPreviewColor(RawColor);
    if (!bHasSourceDrapeColor)
    {
        return Color;
    }

    const float FarBankT = SmoothPreviewStep(
        ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 720.0f : 520.0f),
        ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 1320.0f : 820.0f),
        ChannelOffset);
    const float WaterReadabilityClearanceT = SmoothPreviewStep(
        ActiveRiverHalfWidth + 260.0f * FMath::Max(0.35f, Spec.FlowWetBankScale),
        ActiveRiverHalfWidth + 980.0f * FMath::Max(0.35f, Spec.FlowWetBankScale),
        ChannelOffset);
    const float FarBankSourceDrapeGain = Spec.bDesertCanyon ? 0.28f : (Spec.bHasWaterfalls ? 0.22f : 0.24f);
    const float SourceConditionedFarBankAlbedoT = FMath::Clamp(
        FarBankSourceDrapeGain *
            FarBankT *
            WaterReadabilityClearanceT *
            (0.44f + BankT * 0.18f + CanyonT * 0.28f + SourceVegetationT * (Spec.bDesertCanyon ? 0.06f : 0.18f)) *
            (1.0f - SourceWaterT * 0.62f),
        0.0f,
        Spec.bDesertCanyon ? 0.24f : 0.20f);
    Color = FMath::Lerp(Color, SourceDrapeColor, SourceConditionedFarBankAlbedoT);

    const float SourceConditionedTerrainLumaTarget =
        (Spec.bDesertCanyon ? 0.345f : (Spec.bHasWaterfalls ? 0.255f : 0.292f)) +
        SourceVegetationT * (Spec.bDesertCanyon ? 0.010f : 0.018f);
    const float ExistingLuma = GetPreviewColorLuma(Color);
    if (ExistingLuma < SourceConditionedTerrainLumaTarget)
    {
        const FLinearColor SourceConditionedFill = Spec.bDesertCanyon
            ? FLinearColor(0.46f, 0.32f, 0.20f, Color.A)
            : (Spec.bHasWaterfalls ? FLinearColor(0.065f, 0.160f, 0.070f, Color.A)
                                    : FLinearColor(0.29f, 0.280f, 0.165f, Color.A));
        const float LiftT = FMath::Clamp(
            ((SourceConditionedTerrainLumaTarget - ExistingLuma) / SourceConditionedTerrainLumaTarget) *
                FarBankT *
                WaterReadabilityClearanceT *
                (1.0f - WetT * 0.34f),
            0.0f,
            0.55f);
        Color = FMath::Lerp(Color, SourceConditionedFill, LiftT);
    }

    const float SourceConditionedSlopePhotoMottleT = FMath::Clamp(
        (0.48f + 0.26f * FMath::Sin(X * 0.0017f + Y * 0.0029f) +
         0.18f * FMath::Sin(X * 0.0046f - Y * 0.0011f)) *
            FarBankT *
            WaterReadabilityClearanceT,
        0.0f,
        1.0f);
    const FLinearColor SlopeHighlight = Spec.bDesertCanyon
        ? FLinearColor(0.58f, 0.40f, 0.25f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.082f, 0.190f, 0.080f, Color.A)
                                : FLinearColor(0.33f, 0.31f, 0.18f, Color.A));
    const FLinearColor SlopeShadow = Spec.bDesertCanyon
        ? FLinearColor(0.24f, 0.17f, 0.11f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.020f, 0.055f, 0.030f, Color.A)
                                : FLinearColor(0.14f, 0.13f, 0.085f, Color.A));
    Color = FMath::Lerp(
        Color,
        SourceConditionedSlopePhotoMottleT > 0.50f ? SlopeHighlight : SlopeShadow,
        FMath::Clamp(FMath::Abs(SourceConditionedSlopePhotoMottleT - 0.50f) * 0.20f, 0.0f, 0.10f));

    return ClampPreviewColor(Color);
}

FLinearColor ApplyPreviewBroadSlopeTerrainExposureFill(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& RawColor,
    const FLinearColor& SourceDrapeColor,
    bool bHasSourceDrapeColor,
    float X,
    float Y,
    float BankT,
    float CanyonT,
    float WetT,
    float SourceWaterT,
    float SourceVegetationT,
    float ChannelOffset,
    float ActiveRiverHalfWidth)
{
    FLinearColor Color = ClampPreviewColor(RawColor);
    const float BroadSlopeTerrainExposureFillT = FMath::Clamp(
        SmoothPreviewStep(
            ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 560.0f : 420.0f),
            ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 1800.0f : 1040.0f),
            ChannelOffset) *
            SmoothPreviewStep(
                ActiveRiverHalfWidth + 260.0f * FMath::Max(0.35f, Spec.FlowWetBankScale),
                ActiveRiverHalfWidth + 920.0f * FMath::Max(0.35f, Spec.FlowWetBankScale),
                ChannelOffset) *
            (0.46f + BankT * 0.20f + CanyonT * 0.32f + SourceVegetationT * (Spec.bDesertCanyon ? 0.04f : 0.12f)) *
            (1.0f - FMath::Clamp(SourceWaterT * 0.78f + WetT * 0.30f, 0.0f, 0.86f)),
        0.0f,
        1.0f);
    if (BroadSlopeTerrainExposureFillT <= KINDA_SMALL_NUMBER)
    {
        return Color;
    }

    if (bHasSourceDrapeColor)
    {
        const float BroadSlopeSourceDrapeT = FMath::Clamp(
            BroadSlopeTerrainExposureFillT * (Spec.bDesertCanyon ? 0.085f : (Spec.bHasWaterfalls ? 0.060f : 0.070f)),
            0.0f,
            Spec.bDesertCanyon ? 0.085f : 0.070f);
        Color = FMath::Lerp(Color, SourceDrapeColor, BroadSlopeSourceDrapeT);
    }

    const float BroadSlopeTerrainLumaTarget =
        (Spec.bDesertCanyon ? 0.405f : (Spec.bHasWaterfalls ? 0.238f : 0.318f)) +
        SourceVegetationT * (Spec.bDesertCanyon ? 0.004f : 0.010f);
    const float ExistingLuma = GetPreviewColorLuma(Color);
    if (ExistingLuma < BroadSlopeTerrainLumaTarget)
    {
        const float ExposureScale = FMath::Clamp(
            BroadSlopeTerrainLumaTarget / FMath::Max(ExistingLuma, 0.010f),
            1.0f,
            Spec.bDesertCanyon ? 1.58f : 1.48f);
        const FLinearColor ExposureLiftedColor = ClampPreviewColor(FLinearColor(
            Color.R * ExposureScale,
            Color.G * ExposureScale,
            Color.B * ExposureScale,
            Color.A));
        const FLinearColor BroadSlopeTerrainExposureFillColor = Spec.bDesertCanyon
            ? FLinearColor(0.56f, 0.38f, 0.23f, Color.A)
            : (Spec.bHasWaterfalls ? FLinearColor(0.120f, 0.240f, 0.105f, Color.A)
                                    : FLinearColor(0.34f, 0.320f, 0.195f, Color.A));
        const FLinearColor FilledColor = FMath::Lerp(ExposureLiftedColor, BroadSlopeTerrainExposureFillColor, 0.36f);
        const float BroadSlopeTerrainExposureLiftT = FMath::Clamp(
            ((BroadSlopeTerrainLumaTarget - ExistingLuma) / BroadSlopeTerrainLumaTarget) *
                BroadSlopeTerrainExposureFillT *
                (Spec.bDesertCanyon ? 0.78f : 0.70f),
            0.0f,
            Spec.bDesertCanyon ? 0.62f : 0.56f);
        Color = FMath::Lerp(Color, FilledColor, BroadSlopeTerrainExposureLiftT);
    }

    const float BroadSlopeTerrainMaterialVariationT = FMath::Clamp(
        0.50f + 0.24f * FMath::Sin(X * 0.0013f + Y * 0.0019f) +
            0.18f * FMath::Sin(X * 0.0036f - Y * 0.0024f) +
            0.08f * FMath::Sin((X - Y) * 0.0065f),
        0.0f,
        1.0f);
    const FLinearColor BroadSlopeSunFaceColor = Spec.bDesertCanyon
        ? FLinearColor(0.64f, 0.44f, 0.27f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.150f, 0.285f, 0.115f, Color.A)
                                : FLinearColor(0.38f, 0.355f, 0.215f, Color.A));
    const FLinearColor BroadSlopeAmbientCreaseColor = Spec.bDesertCanyon
        ? FLinearColor(0.30f, 0.20f, 0.13f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.045f, 0.105f, 0.052f, Color.A)
                                : FLinearColor(0.18f, 0.165f, 0.108f, Color.A));
    Color = FMath::Lerp(
        Color,
        BroadSlopeTerrainMaterialVariationT >= 0.50f ? BroadSlopeSunFaceColor : BroadSlopeAmbientCreaseColor,
        FMath::Clamp(
            FMath::Abs(BroadSlopeTerrainMaterialVariationT - 0.50f) *
                BroadSlopeTerrainExposureFillT *
                (Spec.bDesertCanyon ? 0.22f : 0.18f),
            0.0f,
            Spec.bDesertCanyon ? 0.14f : 0.11f));

    return ClampPreviewColor(Color);
}

FLinearColor ApplyPreviewSourceAwareTerrainSlopeFacetTexture(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& RawColor,
    float X,
    float Y,
    float BankT,
    float CanyonT,
    float WetT,
    float SourceWaterT,
    float SourceVegetationT,
    float ChannelOffset,
    float ActiveRiverHalfWidth)
{
    FLinearColor Color = ClampPreviewColor(RawColor);
    const float SourceAwareTerrainSlopeFacetTextureT = FMath::Clamp(
        SmoothPreviewStep(
            ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 420.0f : 300.0f),
            ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 2300.0f : 1380.0f),
            ChannelOffset) *
            (0.34f + BankT * 0.24f + CanyonT * 0.40f +
             SourceVegetationT * (Spec.bDesertCanyon ? 0.04f : 0.18f)) *
            (1.0f - FMath::Clamp(SourceWaterT * 0.82f + WetT * 0.28f, 0.0f, 0.90f)),
        0.0f,
        1.0f);
    if (SourceAwareTerrainSlopeFacetTextureT <= KINDA_SMALL_NUMBER)
    {
        return Color;
    }

    const float SourceAwareTerrainSlopeFacetNoise = FMath::Clamp(
        0.50f +
            0.31f * FMath::Sin(X * 0.0024f + Y * (Spec.bDesertCanyon ? 0.0033f : 0.0041f)) +
            0.19f * FMath::Sin(X * 0.0060f - Y * (Spec.bDesertCanyon ? 0.0021f : 0.0037f)) +
            0.10f * FMath::Sin((X + Y) * 0.011f + SourceVegetationT * 3.2f),
        0.0f,
        1.0f);
    const float SourceAwareTerrainSlopeFacetSunFaceT =
        SmoothPreviewStep(0.56f, 0.90f, SourceAwareTerrainSlopeFacetNoise) *
        SourceAwareTerrainSlopeFacetTextureT;
    const float SourceAwareTerrainSlopeFacetCreaseT =
        SmoothPreviewStep(0.12f, 0.48f, 1.0f - SourceAwareTerrainSlopeFacetNoise) *
        SourceAwareTerrainSlopeFacetTextureT;
    const float SourceAwareTerrainSlopeFacetStrataT = FMath::Clamp(
        (0.50f + 0.50f * FMath::Sin(Y * (Spec.bDesertCanyon ? 0.010f : 0.014f) + X * 0.0012f)) *
            SourceAwareTerrainSlopeFacetTextureT,
        0.0f,
        1.0f);

    const FLinearColor SlopeSunColor = Spec.bDesertCanyon
        ? FLinearColor(0.67f, 0.46f, 0.28f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.105f, 0.215f, 0.085f, Color.A)
                                : FLinearColor(0.365f, 0.335f, 0.205f, Color.A));
    const FLinearColor SlopeCreaseColor = Spec.bDesertCanyon
        ? FLinearColor(0.25f, 0.165f, 0.105f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.020f, 0.060f, 0.034f, Color.A)
                                : FLinearColor(0.135f, 0.125f, 0.082f, Color.A));
    const FLinearColor SlopeStrataColor = Spec.bDesertCanyon
        ? FLinearColor(0.48f, 0.315f, 0.190f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.060f, 0.130f, 0.060f, Color.A)
                                : FLinearColor(0.245f, 0.225f, 0.140f, Color.A));

    Color = FMath::Lerp(
        Color,
        SlopeCreaseColor,
        FMath::Clamp(
            SourceAwareTerrainSlopeFacetCreaseT * (Spec.bDesertCanyon ? 0.24f : 0.18f),
            0.0f,
            Spec.bDesertCanyon ? 0.20f : 0.16f));
    Color = FMath::Lerp(
        Color,
        SlopeSunColor,
        FMath::Clamp(
            SourceAwareTerrainSlopeFacetSunFaceT * (Spec.bDesertCanyon ? 0.22f : 0.16f),
            0.0f,
            Spec.bDesertCanyon ? 0.19f : 0.14f));
    Color = FMath::Lerp(
        Color,
        SlopeStrataColor,
        FMath::Clamp(
            FMath::Abs(SourceAwareTerrainSlopeFacetStrataT - 0.50f) *
                SourceAwareTerrainSlopeFacetTextureT *
                (Spec.bDesertCanyon ? 0.20f : 0.13f),
            0.0f,
            Spec.bDesertCanyon ? 0.14f : 0.10f));

    return ClampPreviewColor(Color);
}

FLinearColor ApplyPreviewSourceAwareRiparianCanopyMassTexture(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& RawColor,
    float X,
    float Y,
    float BankT,
    float CanyonT,
    float WetT,
    float SourceWaterT,
    float SourceVegetationT,
    float ChannelOffset,
    float ActiveRiverHalfWidth)
{
    FLinearColor Color = ClampPreviewColor(RawColor);
    const float SourceAwareRiparianCanopyMassTextureT = FMath::Clamp(
        SmoothPreviewStep(
            ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 520.0f : 260.0f),
            ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 2100.0f : 1280.0f),
            ChannelOffset) *
            (Spec.bDesertCanyon
                 ? (0.12f + BankT * 0.20f + SourceVegetationT * 0.26f)
                 : (Spec.bHasWaterfalls
                        ? (0.18f + BankT * 0.28f + CanyonT * 0.24f + SourceVegetationT * 0.62f)
                        : (0.16f + BankT * 0.30f + CanyonT * 0.12f + SourceVegetationT * 0.48f))) *
            (1.0f - FMath::Clamp(SourceWaterT * 0.88f + WetT * 0.42f, 0.0f, 0.92f)),
        0.0f,
        1.0f);
    if (SourceAwareRiparianCanopyMassTextureT <= KINDA_SMALL_NUMBER)
    {
        return Color;
    }

    const float SourceAwareRiparianCanopyMassNoise = FMath::Clamp(
        0.50f +
            0.28f * FMath::Sin(X * 0.0032f + Y * (Spec.bDesertCanyon ? 0.0021f : 0.0065f)) +
            0.18f * FMath::Sin(X * 0.0090f - Y * (Spec.bDesertCanyon ? 0.0035f : 0.0054f)) +
            0.12f * FMath::Sin((X - Y) * 0.0140f + SourceVegetationT * 2.7f),
        0.0f,
        1.0f);
    const float SourceAwareRiparianCanopyUnderstoryShadowT =
        SmoothPreviewStep(0.10f, 0.48f, 1.0f - SourceAwareRiparianCanopyMassNoise) *
        SourceAwareRiparianCanopyMassTextureT;
    const float SourceAwareRiparianCanopyLeafHighlightT =
        SmoothPreviewStep(0.56f, 0.92f, SourceAwareRiparianCanopyMassNoise) *
        SourceAwareRiparianCanopyMassTextureT;
    const float SourceAwareRiparianCanopyPatchBreakupT = FMath::Clamp(
        (0.50f + 0.50f * FMath::Sin(X * 0.0041f + Y * 0.0087f)) *
            SourceAwareRiparianCanopyMassTextureT,
        0.0f,
        1.0f);

    const FLinearColor CanopyShadowColor = Spec.bDesertCanyon
        ? FLinearColor(0.18f, 0.165f, 0.105f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.006f, 0.052f, 0.022f, Color.A)
                                : FLinearColor(0.095f, 0.145f, 0.060f, Color.A));
    const FLinearColor CanopyMidColor = Spec.bDesertCanyon
        ? FLinearColor(0.28f, 0.245f, 0.145f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.024f, 0.125f, 0.038f, Color.A)
                                : FLinearColor(0.155f, 0.240f, 0.090f, Color.A));
    const FLinearColor CanopyLeafHighlightColor = Spec.bDesertCanyon
        ? FLinearColor(0.36f, 0.315f, 0.180f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.052f, 0.205f, 0.064f, Color.A)
                                : FLinearColor(0.235f, 0.330f, 0.120f, Color.A));

    Color = FMath::Lerp(
        Color,
        CanopyMidColor,
        FMath::Clamp(
            SourceAwareRiparianCanopyMassTextureT * (Spec.bDesertCanyon ? 0.10f : (Spec.bHasWaterfalls ? 0.20f : 0.16f)),
            0.0f,
            Spec.bDesertCanyon ? 0.09f : (Spec.bHasWaterfalls ? 0.18f : 0.14f)));
    Color = FMath::Lerp(
        Color,
        CanopyShadowColor,
        FMath::Clamp(
            SourceAwareRiparianCanopyUnderstoryShadowT *
                (Spec.bDesertCanyon ? 0.12f : (Spec.bHasWaterfalls ? 0.28f : 0.22f)),
            0.0f,
            Spec.bDesertCanyon ? 0.10f : (Spec.bHasWaterfalls ? 0.24f : 0.19f)));
    Color = FMath::Lerp(
        Color,
        CanopyLeafHighlightColor,
        FMath::Clamp(
            SourceAwareRiparianCanopyLeafHighlightT *
                (0.45f + SourceAwareRiparianCanopyPatchBreakupT * 0.55f) *
                (Spec.bDesertCanyon ? 0.10f : (Spec.bHasWaterfalls ? 0.19f : 0.15f)),
            0.0f,
            Spec.bDesertCanyon ? 0.08f : (Spec.bHasWaterfalls ? 0.17f : 0.13f)));

    return ClampPreviewColor(Color);
}
} // namespace RaftSimEditorEnvironment
