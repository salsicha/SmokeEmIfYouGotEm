#pragma once
#include "RaftSimHullGeometry.h"

namespace RaftSimHullContact
{
// Caller has already validated both original indexed hulls and positive Dt.
// sqrt and division by positive Dt are monotone: the maximum of their
// results equals applying them to the maximum input. Inspect every original
// vertex, but perform two square roots instead of three per vertex. No bound
// approximation, rest-shape assumption or collision-validation bypass.
inline void MeasureShapeEnclosure(const FRaftSimHullGeometry& Before,
    const FRaftSimHullGeometry& After,double Dt,double& Radius,double& ShapeSpeed)
{
    double RadiusSquared=0.,DisplacementSquared=0.;
    for(int32 I=0;I<Before.VerticesM.Num();++I)
    {
        RadiusSquared=FMath::Max(RadiusSquared,FMath::Max(
            Before.VerticesM[I].SizeSquared(),After.VerticesM[I].SizeSquared()));
        DisplacementSquared=FMath::Max(DisplacementSquared,
            (After.VerticesM[I]-Before.VerticesM[I]).SizeSquared());
    }
    Radius=FMath::Sqrt(RadiusSquared);
    ShapeSpeed=FMath::Sqrt(DisplacementSquared)/Dt;
}
}
