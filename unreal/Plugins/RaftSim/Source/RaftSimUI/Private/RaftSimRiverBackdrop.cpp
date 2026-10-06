#include "RaftSimRiverBackdrop.h"

#include "Application/SlateApplicationBase.h"

int32 URaftSimRiverBackdrop::NativePaint(const FPaintArgs& Args, const FGeometry& Geometry,
    const FSlateRect& CullingRect, FSlateWindowElementList& Elements, int32 Layer,
    const FWidgetStyle& Style, bool ParentEnabled) const
{
    const float Opacity = Style.GetColorAndOpacityTint().A;
    // Reduced motion freezes the scene at a fixed moment instead of hiding it.
    const double Time = bAnimated && FSlateApplicationBase::IsInitialized()
        ? FSlateApplicationBase::Get().GetCurrentTime() : 12.0;
    Layer = RaftSimUIArt::PaintLandscape(Geometry, Elements, Layer, Art, Time, Opacity);
    if (ShadeLeft > 0.0f || ShadeBottom > 0.0f || ShadeTop > 0.0f)
    {
        Layer = RaftSimUIArt::PaintShade(Geometry, Elements, Layer, ShadeLeft, ShadeBottom,
            ShadeTop, Opacity);
    }
    return Layer;
}
