#include "RaftSimUIArt.h"

#include "Application/SlateApplicationBase.h"
#include "Rendering/DrawElements.h"
#include "Rendering/SlateRenderer.h"
#include "Styling/CoreStyle.h"

namespace RaftSimUIArt
{
namespace
{
constexpr float TwoPi = 6.28318531f;

float Hash(int32 Seed, int32 Index)
{
    uint32 H = uint32(Seed) * 374761393u + uint32(Index) * 668265263u;
    H = (H ^ (H >> 13)) * 1274126177u;
    return float((H ^ (H >> 16)) & 0xFFFFFFu) / float(0xFFFFFFu);
}

/** Layered, peak-sharpened sines: reads as ridgelines at any width. */
float Ridge(float X, int32 Seed, int32 Octaves, float Sharpness)
{
    float Sum = 0.0f, Norm = 0.0f, Amplitude = 1.0f, Frequency = 1.3f;
    for (int32 Octave = 0; Octave < Octaves; ++Octave)
    {
        const float Phase = Hash(Seed, Octave) * TwoPi;
        const float Wave = FMath::Pow(0.5f + 0.5f * FMath::Sin(X * Frequency * TwoPi + Phase), Sharpness);
        Sum += Wave * Amplitude;
        Norm += Amplitude;
        Amplitude *= 0.48f;
        Frequency *= 2.17f;
    }
    return Sum / Norm;
}

float Smooth(float A, float B, float X)
{
    const float T = FMath::Clamp((X - A) / FMath::Max(B - A, 1.0e-4f), 0.0f, 1.0f);
    return T * T * (3.0f - 2.0f * T);
}

FLinearColor WithAlpha(const FLinearColor& Color, float Alpha)
{
    return FLinearColor(Color.R, Color.G, Color.B, Alpha);
}

struct FRiverShape
{
    float W = 0, H = 0, HorizonY = 0;
    int32 Seed = 0;

    FVector2f Point(float T) const
    {
        const float Wind = 0.13f * FMath::Sin(T * 3.1f + Hash(Seed, 7) * TwoPi) +
            0.05f * FMath::Sin(T * 7.3f + Hash(Seed, 8) * TwoPi);
        const float X = W * (0.53f + Wind * (0.20f + 0.80f * T));
        const float Y = HorizonY + (H - HorizonY) * (0.035f + 0.965f * FMath::Pow(T, 1.45f));
        return FVector2f(X, Y);
    }
    float HalfWidth(float T) const { return W * (0.004f + 0.27f * FMath::Pow(T, 1.75f)); }
};
}

FPainter::FPainter(const FGeometry& Geometry, FSlateWindowElementList& InElements, float InOpacity)
    : Elements(InElements)
    , Transform(Geometry.GetAccumulatedRenderTransform())
    , Opacity(InOpacity)
{
    if (FSlateApplicationBase::IsInitialized() && FSlateApplicationBase::Get().GetRenderer())
    {
        Handle = FSlateApplicationBase::Get().GetRenderer()->GetResourceHandle(
            *FCoreStyle::Get().GetBrush("GenericWhiteBox"));
    }
}

void FPainter::Vertex(const FVector2f& Position, const FLinearColor& Color)
{
    const FLinearColor Faded(Color.R, Color.G, Color.B, Color.A * Opacity);
    Verts.Add(FSlateVertex::Make<ESlateVertexRounding::Disabled>(
        Transform, Position, FVector2f(0.5f, 0.5f), Faded.ToFColor(true)));
}

void FPainter::Strip(TConstArrayView<FVector2f> Upper, TConstArrayView<FVector2f> Lower,
    const FLinearColor& UpperColor, const FLinearColor& LowerColor)
{
    const int32 Count = FMath::Min(Upper.Num(), Lower.Num());
    if (Count < 2) return;
    const SlateIndex Base = SlateIndex(Verts.Num());
    for (int32 Index = 0; Index < Count; ++Index)
    {
        Vertex(Upper[Index], UpperColor);
        Vertex(Lower[Index], LowerColor);
    }
    for (int32 Index = 0; Index + 1 < Count; ++Index)
    {
        const SlateIndex A = Base + SlateIndex(2 * Index);
        Indexes.Append({A, SlateIndex(A + 1), SlateIndex(A + 2), SlateIndex(A + 1),
            SlateIndex(A + 3), SlateIndex(A + 2)});
    }
}

void FPainter::Rect(const FVector2f& Min, const FVector2f& Max,
    const FLinearColor& TopColor, const FLinearColor& BottomColor)
{
    const FVector2f Upper[] = {Min, FVector2f(Max.X, Min.Y)};
    const FVector2f Lower[] = {FVector2f(Min.X, Max.Y), Max};
    Strip(Upper, Lower, TopColor, BottomColor);
}

void FPainter::HorizontalRect(const FVector2f& Min, const FVector2f& Max,
    const FLinearColor& LeftColor, const FLinearColor& RightColor)
{
    const SlateIndex Base = SlateIndex(Verts.Num());
    Vertex(Min, LeftColor);
    Vertex(FVector2f(Max.X, Min.Y), RightColor);
    Vertex(FVector2f(Min.X, Max.Y), LeftColor);
    Vertex(Max, RightColor);
    Indexes.Append({Base, SlateIndex(Base + 1), SlateIndex(Base + 2), SlateIndex(Base + 1),
        SlateIndex(Base + 3), SlateIndex(Base + 2)});
}

void FPainter::Glow(const FVector2f& Center, float Radius, const FLinearColor& Inner,
    const FLinearColor& Outer, int32 Segments)
{
    const SlateIndex Base = SlateIndex(Verts.Num());
    Vertex(Center, Inner);
    for (int32 Segment = 0; Segment <= Segments; ++Segment)
    {
        const float Angle = TwoPi * Segment / Segments;
        Vertex(Center + Radius * FVector2f(FMath::Cos(Angle), FMath::Sin(Angle)), Outer);
    }
    for (int32 Segment = 0; Segment < Segments; ++Segment)
    {
        Indexes.Append({Base, SlateIndex(Base + 1 + Segment), SlateIndex(Base + 2 + Segment)});
    }
}

void FPainter::Disc(const FVector2f& Center, float Radius, const FLinearColor& Color, int32 Segments)
{
    Glow(Center, Radius, Color, Color, Segments);
}

void FPainter::Triangle(const FVector2f& A, const FVector2f& B, const FVector2f& C,
    const FLinearColor& Color)
{
    const SlateIndex Base = SlateIndex(Verts.Num());
    Vertex(A, Color);
    Vertex(B, Color);
    Vertex(C, Color);
    Indexes.Append({Base, SlateIndex(Base + 1), SlateIndex(Base + 2)});
}

int32 FPainter::Flush(int32 Layer)
{
    if (Verts.IsEmpty() || !Handle.IsValid())
    {
        Verts.Reset();
        Indexes.Reset();
        return Layer;
    }
    FSlateDrawElement::MakeCustomVerts(Elements, Layer, Handle, Verts, Indexes, nullptr, 0, 0);
    Verts.Reset();
    Indexes.Reset();
    return Layer + 1;
}

int32 PaintLandscape(const FGeometry& Geometry, FSlateWindowElementList& Elements,
    int32 Layer, const FLandscape& Art, double TimeSeconds, float Opacity)
{
    const FVector2f Size(Geometry.GetLocalSize());
    const float W = Size.X, H = Size.Y;
    if (W <= 1.0f || H <= 1.0f) return Layer;
    const float Time = float(FMath::Fmod(TimeSeconds, 3600.0));
    const float HorizonY = H * Art.Horizon;
    FPainter Paint(Geometry, Elements, Opacity);
    FRiverShape River{W, H, HorizonY, Art.Seed};
    const float RiverX0 = River.Point(0.0f).X;

    // Sky and sun.
    const FLinearColor SkyMid = FMath::Lerp(Art.SkyTop, Art.SkyHorizon, 0.38f);
    Paint.Rect(FVector2f(0, 0), FVector2f(W, HorizonY * 0.55f), Art.SkyTop, SkyMid);
    Paint.Rect(FVector2f(0, HorizonY * 0.55f), FVector2f(W, HorizonY + 2.0f), SkyMid, Art.SkyHorizon);
    const FVector2f Sun(W * Art.SunX, HorizonY - H * 0.045f);
    Paint.Glow(Sun, H * 0.62f, WithAlpha(Art.SunGlow, 0.42f), WithAlpha(Art.SunGlow, 0.0f));
    Paint.Glow(Sun, H * 0.16f, WithAlpha(Art.SunGlow, 0.55f), WithAlpha(Art.SunGlow, 0.0f));
    Paint.Disc(Sun, H * 0.032f, FLinearColor(1.0f, 0.93f, 0.78f, 0.95f));
    Layer = Paint.Flush(Layer);

    // Far ridge with atmospheric haze, optional snow caps.
    constexpr int32 Samples = 120;
    TArray<FVector2f> Upper, Lower;
    Upper.Reserve(Samples + 1);
    Lower.Reserve(Samples + 1);
    float FarPeak = 0.0f;
    TArray<float> FarHeights;
    for (int32 Index = 0; Index <= Samples; ++Index)
    {
        const float U = Index / float(Samples);
        const float Height = Ridge(U * 1.4f + 0.3f, Art.Seed + 11, 4, 1.7f);
        FarHeights.Add(Height);
        FarPeak = FMath::Max(FarPeak, Height);
        Upper.Add(FVector2f(W * U, HorizonY - H * (0.05f + 0.20f * Art.Relief * Height)));
        Lower.Add(FVector2f(W * U, HorizonY + H * 0.06f));
    }
    Paint.Strip(Upper, Lower, Art.FarRidge, FMath::Lerp(Art.FarRidge, Art.SkyHorizon, 0.45f));
    if (Art.Snow > 0.01f)
    {
        TArray<FVector2f> SnowLower;
        for (int32 Index = 0; Index <= Samples; ++Index)
        {
            const float Depth = H * 0.028f * Art.Snow *
                Smooth(0.55f * FarPeak, FarPeak, FarHeights[Index]);
            SnowLower.Add(Upper[Index] + FVector2f(0.0f, Depth));
        }
        Paint.Strip(Upper, SnowLower, FLinearColor(0.95f, 0.96f, 1.0f, 0.85f),
            FLinearColor(0.85f, 0.88f, 0.95f, 0.0f));
    }
    // Haze band where the far ridge meets the valley.
    Paint.Rect(FVector2f(0, HorizonY - H * 0.10f), FVector2f(W, HorizonY + H * 0.03f),
        WithAlpha(Art.SkyHorizon, 0.0f), WithAlpha(Art.SkyHorizon, 0.28f));
    Layer = Paint.Flush(Layer);

    // Mid ridge: valley walls, rising into canyon walls beside the river notch.
    TArray<FVector2f> MidTop;
    Upper.Reset();
    Lower.Reset();
    for (int32 Index = 0; Index <= Samples; ++Index)
    {
        const float U = Index / float(Samples);
        const float X = W * U;
        const float Distance = FMath::Abs(X - RiverX0) / W;
        const float Wall = Art.Gorge * Smooth(0.03f, 0.24f, Distance) *
            (0.70f + 0.30f * Ridge(U * 3.0f, Art.Seed + 23, 2, 1.0f));
        const float Hills = 0.03f + 0.10f * Art.Relief * Ridge(U * 1.8f + 0.7f, Art.Seed + 17, 4, 1.3f);
        const float Top = HorizonY - H * (Hills + 0.30f * Wall) + H * 0.015f;
        Upper.Add(FVector2f(X, Top));
        Lower.Add(FVector2f(X, H));
        MidTop.Add(FVector2f(X, Top));
    }
    {
        // Lit faces near the crest fall into shade within a short height, so
        // the valley walls read as volume instead of one flat band.
        TArray<FVector2f> Shaded, Rim;
        for (int32 Index = 0; Index <= Samples; ++Index)
        {
            Shaded.Add(Upper[Index] + FVector2f(0.0f, H * 0.20f));
            Rim.Add(Upper[Index] + FVector2f(0.0f, H * 0.012f));
        }
        Paint.Strip(Upper, Shaded, FMath::Lerp(Art.MidRidge, Art.SkyHorizon, 0.12f),
            FMath::Lerp(Art.MidRidge, Art.NearRidge, 0.55f));
        Paint.Strip(Shaded, Lower, FMath::Lerp(Art.MidRidge, Art.NearRidge, 0.55f), Art.NearRidge);
        Paint.Strip(Upper, Rim, WithAlpha(Art.SunGlow, 0.22f), WithAlpha(Art.SunGlow, 0.0f));
    }
    Layer = Paint.Flush(Layer);

    // Distant forest on the mid ridge.
    if (Art.Trees > 0.01f)
    {
        const int32 Count = FMath::RoundToInt(110 * Art.Trees);
        for (int32 Tree = 0; Tree < Count; ++Tree)
        {
            const float U = Hash(Art.Seed + 31, Tree);
            const int32 Index = FMath::Clamp(FMath::RoundToInt(U * Samples), 0, Samples);
            const FVector2f Base = MidTop[Index] + FVector2f(0.0f, H * 0.006f);
            const float Height = H * (0.012f + 0.016f * Hash(Art.Seed + 37, Tree));
            Paint.Triangle(Base + FVector2f(0, -Height), Base + FVector2f(-Height * 0.32f, 0),
                Base + FVector2f(Height * 0.32f, 0), FMath::Lerp(Art.MidRidge, Art.NearRidge, 0.55f));
        }
        Layer = Paint.Flush(Layer);
    }

    // Forested foothills between the valley walls and the near slopes.
    {
        TArray<FVector2f> HillTop;
        Upper.Reset();
        Lower.Reset();
        for (int32 Index = 0; Index <= Samples; ++Index)
        {
            const float U = Index / float(Samples);
            const float Top = HorizonY + H * (0.055f + 0.020f * Art.Gorge) -
                H * 0.075f * Art.Relief * Ridge(U * 2.4f + 0.2f, Art.Seed + 61, 3, 1.2f);
            Upper.Add(FVector2f(W * U, Top));
            Lower.Add(FVector2f(W * U, H));
            HillTop.Add(FVector2f(W * U, Top));
        }
        const FLinearColor HillColor = FMath::Lerp(Art.MidRidge, Art.NearRidge, 0.35f);
        TArray<FVector2f> HillShade, HillRim;
        for (int32 Index = 0; Index <= Samples; ++Index)
        {
            HillShade.Add(Upper[Index] + FVector2f(0.0f, H * 0.16f));
            HillRim.Add(Upper[Index] + FVector2f(0.0f, H * 0.010f));
        }
        Paint.Strip(Upper, HillShade, FMath::Lerp(HillColor, Art.SkyHorizon, 0.10f), Art.NearRidge);
        Paint.Strip(HillShade, Lower, Art.NearRidge, Art.NearRidge);
        Paint.Strip(Upper, HillRim, WithAlpha(Art.SunGlow, 0.16f), WithAlpha(Art.SunGlow, 0.0f));
        Layer = Paint.Flush(Layer);
        if (Art.Trees > 0.01f)
        {
            const int32 Count = FMath::RoundToInt(150 * Art.Trees);
            for (int32 Tree = 0; Tree < Count; ++Tree)
            {
                const float U = Hash(Art.Seed + 67, Tree);
                const int32 Index = FMath::Clamp(FMath::RoundToInt(U * Samples), 0, Samples);
                const FVector2f Base = HillTop[Index] + FVector2f(0.0f, H * (0.004f + 0.02f * Hash(Art.Seed + 71, Tree)));
                const float Height = H * (0.020f + 0.026f * Hash(Art.Seed + 73, Tree));
                Paint.Triangle(Base + FVector2f(0, -Height), Base + FVector2f(-Height * 0.30f, 0),
                    Base + FVector2f(Height * 0.30f, 0), FMath::Lerp(HillColor, Art.NearRidge, 0.6f));
            }
            Layer = Paint.Flush(Layer);
        }
    }

    // Near slopes framing the river.
    const FVector2f NearLeft = River.Point(1.0f) - FVector2f(River.HalfWidth(1.0f), 0.0f);
    const FVector2f NearRight = River.Point(1.0f) + FVector2f(River.HalfWidth(1.0f), 0.0f);
    const float Lift = (H - HorizonY) * (0.55f + 0.25f * Art.Relief + 0.45f * Art.Gorge);
    for (int32 Side = 0; Side < 2; ++Side)
    {
        Upper.Reset();
        Lower.Reset();
        TArray<FVector2f> Edge;
        const float Start = Side == 0 ? -W * 0.02f : NearRight.X - W * 0.04f;
        const float End = Side == 0 ? NearLeft.X + W * 0.04f : W * 1.02f;
        for (int32 Index = 0; Index <= 60; ++Index)
        {
            const float U = Index / 60.0f;
            const float X = FMath::Lerp(Start, End, U);
            const float Toward = Side == 0 ? U : 1.0f - U;
            const float Rough = 0.035f * (H - HorizonY) *
                Ridge(X / W * 4.0f, Art.Seed + 41 + Side, 3, 1.0f);
            const float Top = H - Lift * FMath::Pow(1.0f - Toward, 1.35f) - Rough + H * 0.02f;
            Upper.Add(FVector2f(X, Top));
            Lower.Add(FVector2f(X, H + 2.0f));
            Edge.Add(FVector2f(X, Top));
        }
        Paint.Strip(Upper, Lower, FMath::Lerp(Art.NearRidge, Art.MidRidge, 0.35f), Art.NearRidge);
        Layer = Paint.Flush(Layer);
        if (Art.Trees > 0.01f)
        {
            const int32 Count = FMath::RoundToInt(26 * Art.Trees);
            for (int32 Tree = 0; Tree < Count; ++Tree)
            {
                const float U = Hash(Art.Seed + 53 + Side, Tree);
                const int32 Index = FMath::Clamp(FMath::RoundToInt(U * 60.0f), 0, 60);
                const FVector2f Base = Edge[Index] + FVector2f(0.0f, H * 0.012f);
                const float Near = FMath::Clamp((Base.Y - HorizonY) / (H - HorizonY), 0.0f, 1.0f);
                const float Height = H * (0.04f + 0.10f * Near) * (0.65f + 0.7f * Hash(Art.Seed + 59, Tree));
                const FLinearColor Needle = Art.NearRidge * 0.7f;
                for (int32 Tier = 0; Tier < 3; ++Tier)
                {
                    const float Y = Base.Y - Height * (0.25f + 0.25f * Tier);
                    const float Half = Height * (0.30f - 0.07f * Tier);
                    Paint.Triangle(FVector2f(Base.X, Y - Height * 0.45f),
                        FVector2f(Base.X - Half, Y), FVector2f(Base.X + Half, Y), WithAlpha(Needle, 1.0f));
                }
                Paint.Rect(Base - FVector2f(Height * 0.03f, Height * 0.30f),
                    Base + FVector2f(Height * 0.03f, 0.0f), WithAlpha(Needle, 1.0f), WithAlpha(Needle, 1.0f));
            }
            Layer = Paint.Flush(Layer);
        }
    }

    // The river: sky reflection far, deep water near, pale banks.
    constexpr int32 RiverSamples = 72;
    TArray<FVector2f> LeftBank, RightBank, LeftShore, RightShore;
    for (int32 Index = 0; Index <= RiverSamples; ++Index)
    {
        const float T = Index / float(RiverSamples);
        const FVector2f P = River.Point(T);
        const float Half = River.HalfWidth(T);
        LeftBank.Add(P - FVector2f(Half, 0.0f));
        RightBank.Add(P + FVector2f(Half, 0.0f));
        const float Shore = 2.0f + Half * 0.06f;
        LeftShore.Add(P - FVector2f(Half + Shore, 0.0f));
        RightShore.Add(P + FVector2f(Half + Shore, 0.0f));
    }
    const FLinearColor ShoreColor = FMath::Lerp(Art.MidRidge, Art.SkyHorizon, 0.30f);
    for (int32 Index = 0; Index < RiverSamples; ++Index)
    {
        const float T0 = Index / float(RiverSamples);
        const float T1 = (Index + 1) / float(RiverSamples);
        const FLinearColor C0 = FMath::Lerp(Art.WaterFar, Art.WaterNear, Smooth(0.0f, 0.65f, T0));
        const FLinearColor C1 = FMath::Lerp(Art.WaterFar, Art.WaterNear, Smooth(0.0f, 0.65f, T1));
        const FVector2f LeftShorePair[] = {LeftShore[Index], LeftShore[Index + 1]};
        const FVector2f RightShorePair[] = {RightShore[Index], RightShore[Index + 1]};
        const FVector2f LeftPair[] = {LeftBank[Index], LeftBank[Index + 1]};
        const FVector2f RightPair[] = {RightBank[Index], RightBank[Index + 1]};
        Paint.Strip(LeftShorePair, RightShorePair, ShoreColor, ShoreColor);
        Paint.Strip(LeftPair, RightPair, C0, C1);
    }
    Layer = Paint.Flush(Layer);

    // Moving light: highlights drift toward the viewer; rapids flicker white.
    const int32 Streaks = 22;
    for (int32 Streak = 0; Streak < Streaks; ++Streak)
    {
        const float Base = Hash(Art.Seed + 101, Streak);
        const float T = FMath::Frac(Base + Time * 0.022f * (0.6f + Base));
        const float Lateral = (Hash(Art.Seed + 103, Streak) * 2.0f - 1.0f) * 0.75f;
        const FVector2f P = River.Point(T) + FVector2f(Lateral * River.HalfWidth(T), 0.0f);
        const float Length = River.HalfWidth(T) * (0.12f + 0.20f * Hash(Art.Seed + 107, Streak));
        const float Thick = 0.6f + 2.2f * T;
        const float Alpha = 0.10f + 0.30f * FMath::Sin(PI * T);
        Paint.Rect(P - FVector2f(Length, Thick * 0.5f), P + FVector2f(Length, Thick * 0.5f),
            WithAlpha(FMath::Lerp(Art.Foam, Art.SunGlow, 0.25f), Alpha),
            WithAlpha(FMath::Lerp(Art.Foam, Art.SunGlow, 0.25f), Alpha));
    }
    if (Art.Whitewater > 0.01f)
    {
        for (int32 Zone = 0; Zone < 3; ++Zone)
        {
            const float Center = 0.30f + 0.22f * Zone + 0.05f * (Hash(Art.Seed + 111, Zone) - 0.5f);
            const int32 Flecks = FMath::RoundToInt(30 * Art.Whitewater);
            for (int32 Fleck = 0; Fleck < Flecks; ++Fleck)
            {
                const float T = Center + 0.045f * (Hash(Art.Seed + 113 + Zone, Fleck) - 0.5f);
                const float Lateral = (Hash(Art.Seed + 127 + Zone, Fleck) * 2.0f - 1.0f) * 0.85f;
                const FVector2f P = River.Point(T) + FVector2f(Lateral * River.HalfWidth(T), 0.0f);
                const float Rate = 2.5f + 4.0f * Hash(Art.Seed + 131, Fleck);
                const float Flicker = 0.35f + 0.65f * (0.5f + 0.5f * FMath::Sin(Time * Rate +
                    Hash(Art.Seed + 137, Fleck) * TwoPi));
                const float Length = River.HalfWidth(T) * (0.05f + 0.10f * Hash(Art.Seed + 139, Fleck));
                const float Thick = 0.8f + 3.0f * T;
                Paint.Rect(P - FVector2f(Length, Thick * 0.5f), P + FVector2f(Length, Thick * 0.5f),
                    WithAlpha(Art.Foam, 0.85f * Flicker * Art.Whitewater),
                    WithAlpha(Art.Foam, 0.55f * Flicker * Art.Whitewater));
            }
        }
    }
    Layer = Paint.Flush(Layer);

    // Low mist breathing over the valley floor.
    const float Breath = 0.5f + 0.5f * FMath::Sin(Time * 0.21f + Art.Seed);
    Paint.Rect(FVector2f(0, HorizonY - H * 0.01f), FVector2f(W, HorizonY + H * 0.05f),
        WithAlpha(Art.SkyHorizon, 0.0f), WithAlpha(Art.SkyHorizon, 0.05f + 0.07f * Breath));
    Paint.Rect(FVector2f(0, HorizonY + H * 0.05f), FVector2f(W, HorizonY + H * 0.12f),
        WithAlpha(Art.SkyHorizon, 0.05f + 0.07f * Breath), WithAlpha(Art.SkyHorizon, 0.0f));
    Layer = Paint.Flush(Layer);

    // A few birds riding the valley air.
    for (int32 Bird = 0; Bird < 3; ++Bird)
    {
        const float X = W * FMath::Frac(Hash(Art.Seed + 151, Bird) + Time * (0.006f + 0.003f * Bird));
        const float Y = H * (0.16f + 0.08f * Hash(Art.Seed + 157, Bird)) +
            H * 0.01f * FMath::Sin(Time * 0.7f + Bird);
        const float Span = H * (0.010f + 0.004f * Bird);
        const float Flap = Span * 0.45f * FMath::Sin(Time * (5.0f + Bird));
        TArray<FVector2f> Wings{FVector2f(X - Span, Y - Flap), FVector2f(X, Y),
            FVector2f(X + Span, Y - Flap)};
        FSlateDrawElement::MakeLines(Elements, Layer, Geometry.ToPaintGeometry(), Wings,
            ESlateDrawEffect::None, FLinearColor(0.02f, 0.03f, 0.03f, 0.75f * Opacity), true, 1.6f);
    }
    return Layer + 1;
}

int32 PaintShade(const FGeometry& Geometry, FSlateWindowElementList& Elements,
    int32 Layer, float Left, float Bottom, float Top, float Opacity)
{
    const FVector2f Size(Geometry.GetLocalSize());
    FPainter Paint(Geometry, Elements, Opacity);
    const FLinearColor Ink(0.004f, 0.010f, 0.012f);
    if (Left > 0.0f)
    {
        Paint.HorizontalRect(FVector2f(0, 0), FVector2f(Size.X * Left, Size.Y),
            WithAlpha(Ink, 0.88f), WithAlpha(Ink, 0.0f));
    }
    if (Bottom > 0.0f)
    {
        Paint.Rect(FVector2f(0, Size.Y * (1.0f - Bottom)), Size,
            WithAlpha(Ink, 0.0f), WithAlpha(Ink, 0.92f));
    }
    if (Top > 0.0f)
    {
        Paint.Rect(FVector2f(0, 0), FVector2f(Size.X, Size.Y * Top),
            WithAlpha(Ink, 0.70f), WithAlpha(Ink, 0.0f));
    }
    return Paint.Flush(Layer);
}

FLandscape HomeLandscape()
{
    FLandscape Art;
    Art.SkyTop = FLinearColor(0.008f, 0.028f, 0.060f);
    Art.SkyHorizon = FLinearColor(0.95f, 0.46f, 0.15f);
    Art.SunGlow = FLinearColor(1.0f, 0.62f, 0.24f);
    Art.Gorge = 0.55f;
    Art.Trees = 0.75f;
    Art.Seed = 3;
    return Art;
}

FRiverCard RiverCardFor(FName ScenarioId, const FText& FallbackTitle)
{
    FRiverCard Card;
    Card.Art = HomeLandscape();
    const FString Id = ScenarioId.ToString();
    auto Set = [&Card](const TCHAR* Title, const TCHAR* Place, const TCHAR* Grade, const TCHAR* Hook)
    {
        Card.Title = FText::FromString(Title);
        Card.Place = FText::FromString(Place);
        Card.Grade = FText::FromString(Grade);
        Card.Hook = FText::FromString(Hook);
    };
    FLandscape& A = Card.Art;
    if (Id == TEXT("south_fork_full_descent") || Id.StartsWith(TEXT("south_fork")))
    {
        Set(TEXT("South Fork American"), TEXT("Chili Bar to Salmon Falls  ·  California"),
            TEXT("CLASS III"), TEXT("Thirty-three kilometres of golden foothill whitewater, Troublemaker included."));
        A.SkyTop = FLinearColor(0.035f, 0.11f, 0.24f);
        A.SkyHorizon = FLinearColor(0.96f, 0.66f, 0.34f);
        A.FarRidge = FLinearColor(0.26f, 0.25f, 0.32f);
        A.MidRidge = FLinearColor(0.22f, 0.16f, 0.06f);
        A.NearRidge = FLinearColor(0.025f, 0.040f, 0.015f);
        A.WaterFar = FLinearColor(0.88f, 0.62f, 0.36f);
        A.WaterNear = FLinearColor(0.025f, 0.15f, 0.14f);
        A.Relief = 0.75f; A.Gorge = 0.25f; A.Trees = 0.5f; A.Whitewater = 0.55f; A.Seed = 5;
    }
    else if (Id == TEXT("hance_challenge"))
    {
        Set(TEXT("Colorado River"), TEXT("Hance Rapid  ·  Grand Canyon, Arizona"),
            TEXT("CLASS IV"), TEXT("Big water in the heart of the Grand Canyon."));
        A.SkyTop = FLinearColor(0.04f, 0.13f, 0.30f);
        A.SkyHorizon = FLinearColor(0.98f, 0.60f, 0.30f);
        A.SunGlow = FLinearColor(1.0f, 0.62f, 0.28f);
        A.FarRidge = FLinearColor(0.50f, 0.24f, 0.18f);
        A.MidRidge = FLinearColor(0.40f, 0.12f, 0.045f);
        A.NearRidge = FLinearColor(0.10f, 0.035f, 0.015f);
        A.WaterFar = FLinearColor(0.82f, 0.52f, 0.32f);
        A.WaterNear = FLinearColor(0.10f, 0.20f, 0.12f);
        A.Relief = 1.25f; A.Gorge = 1.0f; A.Trees = 0.0f; A.Whitewater = 0.85f; A.Seed = 7; A.SunX = 0.42f;
    }
    else if (Id == TEXT("upper_huacas_challenge"))
    {
        Set(TEXT("Pacuare"), TEXT("Upper Huacas  ·  Costa Rica"),
            TEXT("CLASS IV"), TEXT("Rain-fed rapids through deep tropical forest."));
        A.SkyTop = FLinearColor(0.07f, 0.17f, 0.20f);
        A.SkyHorizon = FLinearColor(0.78f, 0.82f, 0.66f);
        A.SunGlow = FLinearColor(1.0f, 0.90f, 0.70f);
        A.FarRidge = FLinearColor(0.18f, 0.28f, 0.24f);
        A.MidRidge = FLinearColor(0.025f, 0.11f, 0.040f);
        A.NearRidge = FLinearColor(0.004f, 0.035f, 0.010f);
        A.WaterFar = FLinearColor(0.62f, 0.66f, 0.50f);
        A.WaterNear = FLinearColor(0.10f, 0.15f, 0.07f);
        A.Relief = 1.0f; A.Gorge = 0.6f; A.Trees = 1.0f; A.Whitewater = 0.7f; A.Seed = 11; A.SunX = 0.30f;
    }
    else if (Id == TEXT("terminator_challenge"))
    {
        Set(TEXT("Futaleufú"), TEXT("Terminator  ·  Patagonia, Chile"),
            TEXT("CLASS V"), TEXT("Turquoise glacial water at full force."));
        A.SkyTop = FLinearColor(0.03f, 0.12f, 0.28f);
        A.SkyHorizon = FLinearColor(0.68f, 0.80f, 0.92f);
        A.SunGlow = FLinearColor(1.0f, 0.95f, 0.85f);
        A.FarRidge = FLinearColor(0.28f, 0.34f, 0.46f);
        A.MidRidge = FLinearColor(0.040f, 0.080f, 0.070f);
        A.NearRidge = FLinearColor(0.008f, 0.022f, 0.018f);
        A.WaterFar = FLinearColor(0.50f, 0.78f, 0.82f);
        A.WaterNear = FLinearColor(0.015f, 0.36f, 0.38f);
        A.Relief = 1.4f; A.Gorge = 0.7f; A.Snow = 0.95f; A.Trees = 0.7f; A.Whitewater = 1.0f; A.Seed = 13;
    }
    else if (Id == TEXT("lava_canyon_challenge"))
    {
        Set(TEXT("Chilko"), TEXT("Lava Canyon  ·  British Columbia"),
            TEXT("CLASS IV"), TEXT("Continuous whitewater beneath dark volcanic walls."));
        A.SkyTop = FLinearColor(0.03f, 0.06f, 0.11f);
        A.SkyHorizon = FLinearColor(0.86f, 0.55f, 0.34f);
        A.FarRidge = FLinearColor(0.20f, 0.20f, 0.27f);
        A.MidRidge = FLinearColor(0.055f, 0.055f, 0.055f);
        A.NearRidge = FLinearColor(0.008f, 0.018f, 0.013f);
        A.WaterFar = FLinearColor(0.72f, 0.55f, 0.40f);
        A.WaterNear = FLinearColor(0.030f, 0.22f, 0.24f);
        A.Relief = 1.2f; A.Gorge = 0.85f; A.Snow = 0.5f; A.Trees = 0.8f; A.Whitewater = 0.85f; A.Seed = 17;
    }
    else if (Id == TEXT("zambezi_reference_run") || Id == TEXT("zambezi_upper_gorge_challenge"))
    {
        const bool bUpper = Id == TEXT("zambezi_upper_gorge_challenge");
        if (bUpper)
        {
            Set(TEXT("Zambezi Upper Gorge"), TEXT("Boiling Pot to Stairway to Heaven"),
                TEXT("CLASS V"), TEXT("Low-water drops in the shadow of Victoria Falls."));
        }
        else
        {
            Set(TEXT("Zambezi"), TEXT("Batoka Gorge  ·  Zambia / Zimbabwe"),
                TEXT("CLASS IV–V"), TEXT("Twenty-five big-water rapids below Victoria Falls."));
        }
        A.SkyTop = FLinearColor(0.06f, 0.07f, 0.17f);
        A.SkyHorizon = FLinearColor(1.0f, 0.52f, 0.18f);
        A.SunGlow = FLinearColor(1.0f, 0.50f, 0.15f);
        A.FarRidge = FLinearColor(0.38f, 0.20f, 0.15f);
        A.MidRidge = FLinearColor(0.11f, 0.065f, 0.045f);
        A.NearRidge = FLinearColor(0.018f, 0.012f, 0.008f);
        A.WaterFar = FLinearColor(0.96f, 0.55f, 0.24f);
        A.WaterNear = FLinearColor(0.09f, 0.11f, 0.07f);
        A.Relief = 1.1f; A.Gorge = 1.0f; A.Trees = 0.25f; A.Whitewater = 1.0f;
        A.Seed = bUpper ? 23 : 19;
        A.SunX = bUpper ? 0.74f : 0.30f;
    }
    else if (Id == TEXT("training_eddy_basics"))
    {
        Set(TEXT("Guide School"), TEXT("Training Eddy  ·  flat water"),
            TEXT("TRAINING"), TEXT("Learn the calls before the river tests them."));
        A.SkyTop = FLinearColor(0.08f, 0.22f, 0.38f);
        A.SkyHorizon = FLinearColor(0.86f, 0.80f, 0.64f);
        A.SunGlow = FLinearColor(1.0f, 0.88f, 0.62f);
        A.FarRidge = FLinearColor(0.28f, 0.36f, 0.40f);
        A.MidRidge = FLinearColor(0.05f, 0.13f, 0.07f);
        A.NearRidge = FLinearColor(0.012f, 0.035f, 0.018f);
        A.WaterFar = FLinearColor(0.78f, 0.76f, 0.64f);
        A.WaterNear = FLinearColor(0.040f, 0.19f, 0.19f);
        A.Relief = 0.6f; A.Gorge = 0.0f; A.Trees = 0.85f; A.Whitewater = 0.04f; A.Seed = 29; A.SunX = 0.22f;
    }
    else
    {
        Set(*FallbackTitle.ToString(), TEXT(""), TEXT("FREE RUN"), TEXT(""));
        A.Seed = int32(GetTypeHash(ScenarioId) % 97u) + 31;
    }
    return Card;
}
}
