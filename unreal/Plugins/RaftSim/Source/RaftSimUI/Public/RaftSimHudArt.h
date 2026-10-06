#pragma once

#include "Blueprint/UserWidget.h"
#include "RaftSimHudArt.generated.h"

UENUM()
enum class ERaftSimHudArtKind : uint8
{
    /** Run progress: track, filled reach, raft marker and finish flag. */
    RouteRibbon,
    /** Four-way crew command wheel with a central stop. */
    CommandWheel,
    /** Soft top and bottom shade that keeps HUD text legible over bright water. */
    Shade,
    /** Feathered letterbox band behind a cinematic title. */
    TitleBand,
    /** Thin amber rule that fades out to both ends; Progress sets its reach. */
    TitleRule
};

/** Small painted HUD graphics (RaftSimUIArt primitives), no textures. */
UCLASS()
class RAFTSIMUI_API URaftSimHudArt : public UUserWidget
{
    GENERATED_BODY()
public:
    void SetKind(ERaftSimHudArtKind InKind) { Kind = InKind; }
    void SetProgress(float InProgress) { Progress = FMath::Clamp(InProgress, 0.0f, 1.0f); }
    void SetAccent(const FLinearColor& InAccent) { Accent = InAccent; }

protected:
    virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& Geometry,
        const FSlateRect& CullingRect, FSlateWindowElementList& Elements, int32 Layer,
        const FWidgetStyle& Style, bool ParentEnabled) const override;

    ERaftSimHudArtKind Kind = ERaftSimHudArtKind::Shade;
    float Progress = 0.0f;
    FLinearColor Accent = FLinearColor(0.16f, 0.74f, 0.68f);
};
