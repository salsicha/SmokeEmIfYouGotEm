#pragma once
#include "CoreMinimal.h"

namespace RaftSimSurfaceWinding
{
// The production procedural carrier uses clockwise top faces (I0,I2,I1)
// with upward shading normals. Determine handedness from its actual local
// planar geometry, not river metadata that may already have been applied.
// Refinement inherits the same orientation. No position or membership edit.
inline bool NeedsClockwiseFlip(TConstArrayView<FVector> Positions,
    TConstArrayView<int32> Triangles)
{
    for (int32 I=0;I+2<Triangles.Num();I+=3)
    {
        const int32 A=Triangles[I],B=Triangles[I+1],C=Triangles[I+2];
        if (!Positions.IsValidIndex(A) || !Positions.IsValidIndex(B) ||
            !Positions.IsValidIndex(C)) return false;
        const FVector AB=Positions[B]-Positions[A],AC=Positions[C]-Positions[A];
        const double Cross=AB.X*AC.Y-AB.Y*AC.X;
        if (!FMath::IsFinite(Cross)) return false;
        if (FMath::Abs(Cross)>1.e-12) return Cross>0.;
    }
    return false;
}
}
