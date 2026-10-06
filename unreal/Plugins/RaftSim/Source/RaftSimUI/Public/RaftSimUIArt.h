#pragma once

#include "CoreMinimal.h"
#include "Layout/Geometry.h"
#include "Rendering/RenderingCommon.h"
#include "Rendering/SlateResourceHandle.h"

class FSlateWindowElementList;

/**
 * Asset-free painted art for the front end and HUD: a layered river-valley
 * landscape (sky, sun, ridges, forest, river) drawn from Slate primitives, and
 * per-river looks so every menu card reads at a glance. Original vector art;
 * it depicts a mood, never a map or a real line.
 */
namespace RaftSimUIArt
{
struct RAFTSIMUI_API FLandscape
{
    FLinearColor SkyTop = FLinearColor(0.010f, 0.030f, 0.050f);
    FLinearColor SkyHorizon = FLinearColor(0.80f, 0.42f, 0.18f);
    FLinearColor SunGlow = FLinearColor(1.00f, 0.66f, 0.30f);
    FLinearColor FarRidge = FLinearColor(0.12f, 0.12f, 0.16f);
    FLinearColor MidRidge = FLinearColor(0.035f, 0.055f, 0.050f);
    FLinearColor NearRidge = FLinearColor(0.008f, 0.016f, 0.014f);
    FLinearColor WaterFar = FLinearColor(0.75f, 0.45f, 0.22f);
    FLinearColor WaterNear = FLinearColor(0.020f, 0.120f, 0.120f);
    FLinearColor Foam = FLinearColor(0.92f, 0.95f, 0.92f);
    float SunX = 0.68f;
    float Horizon = 0.56f;
    float Relief = 1.0f;
    float Gorge = 0.0f;
    float Snow = 0.0f;
    float Trees = 0.6f;
    float Whitewater = 0.6f;
    int32 Seed = 1;
};

/** Player-facing description of one runnable river for menu cards. */
struct RAFTSIMUI_API FRiverCard
{
    FText Title;
    FText Place;
    FText Grade;
    FText Hook;
    FLandscape Art;
};

RAFTSIMUI_API FLandscape HomeLandscape();
RAFTSIMUI_API FRiverCard RiverCardFor(FName ScenarioId, const FText& FallbackTitle);

/** Paints the landscape into Geometry; returns the last layer used. */
RAFTSIMUI_API int32 PaintLandscape(const FGeometry& Geometry, FSlateWindowElementList& Elements,
    int32 Layer, const FLandscape& Art, double TimeSeconds, float Opacity);

/** Darkens toward the left edge and the bottom so text over the art stays legible. */
RAFTSIMUI_API int32 PaintShade(const FGeometry& Geometry, FSlateWindowElementList& Elements,
    int32 Layer, float Left, float Bottom, float Top, float Opacity);

/** Filled polygon helpers shared by other painted widgets. */
class RAFTSIMUI_API FPainter
{
public:
    FPainter(const FGeometry& Geometry, FSlateWindowElementList& Elements, float Opacity);

    /** Quad strip between two polylines of equal length, graded per vertex. */
    void Strip(TConstArrayView<FVector2f> Upper, TConstArrayView<FVector2f> Lower,
        const FLinearColor& UpperColor, const FLinearColor& LowerColor);
    void Rect(const FVector2f& Min, const FVector2f& Max,
        const FLinearColor& TopColor, const FLinearColor& BottomColor);
    void HorizontalRect(const FVector2f& Min, const FVector2f& Max,
        const FLinearColor& LeftColor, const FLinearColor& RightColor);
    void Glow(const FVector2f& Center, float Radius, const FLinearColor& Inner,
        const FLinearColor& Outer, int32 Segments = 48);
    void Triangle(const FVector2f& A, const FVector2f& B, const FVector2f& C,
        const FLinearColor& Color);
    void Disc(const FVector2f& Center, float Radius, const FLinearColor& Color, int32 Segments = 32);
    /** Submits everything queued so far on Layer; returns Layer + 1. */
    int32 Flush(int32 Layer);

private:
    void Vertex(const FVector2f& Position, const FLinearColor& Color);
    FSlateWindowElementList& Elements;
    FSlateRenderTransform Transform;
    FSlateResourceHandle Handle;
    float Opacity = 1.0f;
    TArray<FSlateVertex> Verts;
    TArray<SlateIndex> Indexes;
};
}
