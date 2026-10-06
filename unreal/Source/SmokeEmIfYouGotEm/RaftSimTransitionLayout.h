#pragma once

#include "CoreMinimal.h"

namespace RaftSimTransitionLayout
{
struct FRegion
{
    FVector2D Position;
    FVector2D Size;
};

// Canvas root renders about its centre at the saved UI scale. Convert the
// viewport's safe bottom-left back to that root's local coordinates, rather
// than scaling an already bottom-anchored offset beyond the screen edge.
inline FRegion Resolve(FVector2D Viewport, float UiScale)
{
    const double Scale = FMath::Clamp(double(UiScale), 0.75, 1.5);
    const FVector2D Margin(FMath::Min(40.0, Viewport.X * 0.05),
        FMath::Min(40.0, Viewport.Y * 0.05));
    const FVector2D Centre = Viewport * 0.5;
    const FVector2D BottomLeft = Centre +
        (FVector2D(Margin.X, Viewport.Y - Margin.Y) - Centre) / Scale;
    return {BottomLeft - FVector2D(0.0, Viewport.Y),
        FVector2D(FMath::Min(780.0, (Viewport.X - 2.0 * Margin.X) / Scale),
            FMath::Min(400.0, Viewport.Y * 0.4 / Scale))};
}
}
