#pragma once

#include "Blueprint/UserWidget.h"
#include "RaftSimUIArt.h"
#include "RaftSimRiverBackdrop.generated.h"

/**
 * Original painted river-valley artwork (RaftSimUIArt), drawn in Slate without
 * textures or scene captures. Used full screen behind the front end and small
 * on each river card, with an optional legibility shade.
 */
UCLASS()
class RAFTSIMUI_API URaftSimRiverBackdrop : public UUserWidget
{
    GENERATED_BODY()
public:
    void SetLandscape(const RaftSimUIArt::FLandscape& InArt) { Art = InArt; }
    void SetAnimated(bool bInAnimated) { bAnimated = bInAnimated; }
    void SetShade(float Left, float Bottom, float Top)
    {
        ShadeLeft = Left;
        ShadeBottom = Bottom;
        ShadeTop = Top;
    }

protected:
    virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& Geometry,
        const FSlateRect& CullingRect, FSlateWindowElementList& Elements, int32 Layer,
        const FWidgetStyle& Style, bool ParentEnabled) const override;

    RaftSimUIArt::FLandscape Art = RaftSimUIArt::HomeLandscape();
    bool bAnimated = true;
    float ShadeLeft = 0.0f;
    float ShadeBottom = 0.0f;
    float ShadeTop = 0.0f;
};
