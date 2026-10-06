#include "RaftSimHudArt.h"

#include "RaftSimUIArt.h"
#include "RaftSimUITheme.h"

namespace
{
FLinearColor Alpha(const FLinearColor& Color, float A) { return FLinearColor(Color.R, Color.G, Color.B, A); }

/** Annular sector between two radii, as a quad strip. */
void Wedge(RaftSimUIArt::FPainter& Paint, const FVector2f& Center, float Inner, float Outer,
    float From, float To, const FLinearColor& InnerColor, const FLinearColor& OuterColor)
{
    constexpr int32 Segments = 24;
    TArray<FVector2f> InnerArc, OuterArc;
    for (int32 Segment = 0; Segment <= Segments; ++Segment)
    {
        const float Angle = FMath::Lerp(From, To, Segment / float(Segments));
        const FVector2f Direction(FMath::Cos(Angle), FMath::Sin(Angle));
        InnerArc.Add(Center + Direction * Inner);
        OuterArc.Add(Center + Direction * Outer);
    }
    Paint.Strip(InnerArc, OuterArc, InnerColor, OuterColor);
}
}

int32 URaftSimHudArt::NativePaint(const FPaintArgs& Args, const FGeometry& Geometry,
    const FSlateRect& CullingRect, FSlateWindowElementList& Elements, int32 Layer,
    const FWidgetStyle& Style, bool ParentEnabled) const
{
    const FVector2f Size(Geometry.GetLocalSize());
    const float Opacity = Style.GetColorAndOpacityTint().A;
    RaftSimUIArt::FPainter Paint(Geometry, Elements, Opacity);
    const FLinearColor Gold = RaftSimUITheme::Gold();
    const FLinearColor Ink = RaftSimUITheme::Ink();

    if (Kind == ERaftSimHudArtKind::Shade)
    {
        Paint.Rect(FVector2f(0, 0), FVector2f(Size.X, Size.Y * 0.22f), Alpha(Ink, 0.50f), Alpha(Ink, 0.0f));
        Paint.Rect(FVector2f(0, Size.Y * 0.74f), Size, Alpha(Ink, 0.0f), Alpha(Ink, 0.55f));
        return Paint.Flush(Layer);
    }

    if (Kind == ERaftSimHudArtKind::TitleBand)
    {
        // Darkest through the middle, feathered top and bottom so the band
        // sits in the river view rather than on it.
        const float Mid = Size.Y * 0.5f;
        Paint.Rect(FVector2f(0, 0), FVector2f(Size.X, Mid), Alpha(Ink, 0.0f), Alpha(Ink, 0.58f));
        Paint.Rect(FVector2f(0, Mid), Size, Alpha(Ink, 0.58f), Alpha(Ink, 0.0f));
        return Paint.Flush(Layer);
    }

    if (Kind == ERaftSimHudArtKind::TitleRule)
    {
        const float Center = Size.X * 0.5f;
        const float Reach = Center * Progress;
        const float Top = Size.Y * 0.5f - 0.75f, Bottom = Size.Y * 0.5f + 0.75f;
        if (Reach > 0.5f)
        {
            Paint.HorizontalRect(FVector2f(Center - Reach, Top), FVector2f(Center, Bottom), Alpha(Accent, 0.0f), Alpha(Accent, 1.0f));
            Paint.HorizontalRect(FVector2f(Center, Top), FVector2f(Center + Reach, Bottom), Alpha(Accent, 1.0f), Alpha(Accent, 0.0f));
            Paint.Glow(FVector2f(Center, Size.Y * 0.5f), 10.0f * Progress, Alpha(Accent, 0.45f), Alpha(Accent, 0.0f));
        }
        return Paint.Flush(Layer);
    }

    if (Kind == ERaftSimHudArtKind::RouteRibbon)
    {
        const float Left = 14.0f, Right = Size.X - 26.0f;
        const float Mid = Size.Y * 0.5f;
        const float Half = 3.0f;
        const float Reach = FMath::Lerp(Left, Right, Progress);
        // Track, then the reach already run.
        Paint.Rect(FVector2f(Left, Mid - Half - 1.5f), FVector2f(Right, Mid + Half + 1.5f),
            Alpha(Ink, 0.70f), Alpha(Ink, 0.70f));
        Paint.HorizontalRect(FVector2f(Left, Mid - Half), FVector2f(Reach, Mid + Half),
            Alpha(Accent * 0.45f, 0.95f), Alpha(Accent, 1.0f));
        for (int32 Tick = 1; Tick < 4; ++Tick)
        {
            const float X = FMath::Lerp(Left, Right, Tick * 0.25f);
            Paint.Rect(FVector2f(X - 0.75f, Mid - 7.0f), FVector2f(X + 0.75f, Mid + 7.0f),
                Alpha(RaftSimUITheme::Paper(), 0.45f), Alpha(RaftSimUITheme::Paper(), 0.45f));
        }
        // Put-in and take-out markers.
        Paint.Disc(FVector2f(Left, Mid), 5.0f, Alpha(Accent, 1.0f));
        const FVector2f Pole(Right + 4.0f, Mid + 8.0f);
        Paint.Rect(Pole - FVector2f(0.8f, 18.0f), Pole + FVector2f(0.8f, 0.0f),
            Alpha(RaftSimUITheme::Paper(), 0.95f), Alpha(RaftSimUITheme::Paper(), 0.95f));
        for (int32 Row = 0; Row < 2; ++Row)
        {
            for (int32 Column = 0; Column < 3; ++Column)
            {
                const FVector2f Min = Pole + FVector2f(1.0f + Column * 4.0f, -18.0f + Row * 4.0f);
                const FLinearColor Square = (Row + Column) % 2 == 0
                    ? Alpha(RaftSimUITheme::Paper(), 0.95f) : Alpha(Ink, 0.95f);
                Paint.Rect(Min, Min + FVector2f(4.0f, 4.0f), Square, Square);
            }
        }
        // The raft: an amber diamond with a soft glow.
        const FVector2f Raft(Reach, Mid);
        Paint.Glow(Raft, 15.0f, Alpha(Gold, 0.55f), Alpha(Gold, 0.0f));
        Paint.Triangle(Raft + FVector2f(0, -9), Raft + FVector2f(-7, 0), Raft + FVector2f(7, 0), Alpha(Gold, 1.0f));
        Paint.Triangle(Raft + FVector2f(0, 9), Raft + FVector2f(-7, 0), Raft + FVector2f(7, 0),
            Alpha(Gold * 0.75f, 1.0f));
        return Paint.Flush(Layer);
    }

    // Command wheel.
    const FVector2f Center = Size * 0.5f;
    const float Outer = FMath::Min(Size.X, Size.Y) * 0.5f - 2.0f;
    const float Inner = Outer * 0.34f;
    const float Gap = 0.035f;
    for (int32 Petal = 0; Petal < 4; ++Petal)
    {
        // Up, right, down, left petals around the stop button.
        const float Middle = -HALF_PI + Petal * HALF_PI;
        Wedge(Paint, Center, Inner + 6.0f, Outer, Middle - PI * 0.25f + Gap, Middle + PI * 0.25f - Gap,
            Alpha(FLinearColor(0.02f, 0.05f, 0.055f), 0.88f), Alpha(FLinearColor(0.04f, 0.10f, 0.10f), 0.80f));
        Wedge(Paint, Center, Outer - 4.0f, Outer, Middle - PI * 0.25f + Gap, Middle + PI * 0.25f - Gap,
            Alpha(Accent, 0.85f), Alpha(Accent, 0.85f));
        const FVector2f Direction(FMath::Cos(Middle), FMath::Sin(Middle));
        const FVector2f Side(-Direction.Y, Direction.X);
        const FVector2f Tip = Center + Direction * (Outer - 16.0f);
        Paint.Triangle(Tip, Tip - Direction * 12.0f + Side * 9.0f, Tip - Direction * 12.0f - Side * 9.0f,
            Alpha(Gold, 0.95f));
    }
    Paint.Disc(Center, Inner, Alpha(FLinearColor(0.10f, 0.05f, 0.02f), 0.92f), 40);
    Wedge(Paint, Center, Inner - 3.0f, Inner, 0.0f, 2.0f * PI, Alpha(Gold, 0.9f), Alpha(Gold, 0.9f));
    return Paint.Flush(Layer);
}
