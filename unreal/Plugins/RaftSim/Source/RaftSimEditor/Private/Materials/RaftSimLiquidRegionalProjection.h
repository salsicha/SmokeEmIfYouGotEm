#pragma once
#include "RaftSimLiquidRegionalState.h"

// Immutable parent-grid coordinates for a regional pressure program. Numerical
// halos are not physical owners: imported pressure there must survive the local
// solve. Niagara Y runs opposite canonical lateral Y; reflect before coloring.
namespace RaftSimLiquidRegionalProjection
{
struct FLayout
{
    FIntVector Cells=FIntVector::ZeroValue,ParentCells=FIntVector::ZeroValue;
    FIntPoint Offset=FIntPoint::ZeroValue;
    FVector Spacing=FVector::ZeroVector;
    int32 Phase() const { return (Offset.X/2+Offset.Y/2)%2; }
    FString ParentIndexHlsl(const TCHAR* Index) const
    { return FString::Printf(TEXT("(%s+int3(%d,%d,0))"),Index,Offset.X,Offset.Y); }
    bool Shared(FIntPoint P) const
    {
        const FIntPoint G=P+Offset;
        return (P.X<2 || P.Y<2 || P.X>=Cells.X+2 || P.Y>=Cells.Y+2) &&
            G.X>=2 && G.Y>=2 && G.X<ParentCells.X+2 && G.Y<ParentCells.Y+2;
    }
    FString OwnsHlsl() const
    {
        return FString::Printf(TEXT(
            "// RegionalPressureOwner: imported shared halos are read-only.\n"
            "int2 regionalGlobal=p.xy+int2(%d,%d);\n"
            "bool regionalShared=(p.x<2 || p.y<2 || p.x>=%d || p.y>=%d) && "
            "regionalGlobal.x>=2 && regionalGlobal.y>=2 && regionalGlobal.x<%d && regionalGlobal.y<%d;\n"
            "if(regionalShared) continue;\n"),Offset.X,Offset.Y,Cells.X+2,Cells.Y+2,ParentCells.X+2,ParentCells.Y+2);
    }
    FString MetricHlsl() const
    {
        return FString::Printf(TEXT("// RegionalProjectionMetricCM\nfloat3 h=float3(%.17g,%.17g,%.17g);\n"),Spacing.X,Spacing.Y,Spacing.Z);
    }
};
inline bool Build(const RaftSimLiquidRegionalState::FParent& Parent,
    const RaftSimLiquidRegionalState::FState& Region,FLayout& Out,FString& Error)
{
    Out={};Error=TEXT("Regional pressure requires validated even-cell cuts in the parent metric");
    // The native NX/2 dispatch handles both parity lanes. Odd partition offsets
    // need a different dispatch mapping and must never silently use this one.
    const FIntPoint Offset(Region.FirstCell.X,Parent.Cells.Y-Region.FirstCell.Y-Region.Cells.Y);
    if (Region.FirstCell.X<0 || Region.FirstCell.Y<0 || Offset.X<0 || Offset.Y<0 ||
        (Offset.X%2)!=0 || (Offset.Y%2)!=0 || Region.Cells.X<2 || Region.Cells.Y<2 ||
        Region.Cells.X%2!=0 || Region.Cells.Y%2!=0 || Region.Cells.Z!=Parent.Cells.Z ||
        Region.FirstCell.X+Region.Cells.X>Parent.Cells.X ||
        Region.FirstCell.Y+Region.Cells.Y>Parent.Cells.Y ||
        Region.ComputationalCells!=Region.Cells+FIntVector(4,4,0) ||
        !Region.Extent.Equals(FVector(Region.ComputationalCells)*Parent.Spacing,1e-7) ||
        Parent.Spacing.ContainsNaN() || Parent.Spacing.GetMin()<=0 ||
        !Region.Frame.AxisX.Equals(Parent.Frame.AxisX,1e-9) || !Region.Frame.AxisY.Equals(Parent.Frame.AxisY,1e-9)) return false;
    Out.Cells=Region.Cells;Out.ParentCells=Parent.Cells;Out.Offset=Offset;Out.Spacing=Parent.Spacing;
    Error.Reset();return true;
}
}

// Installs metric D/P/G, globally aligned pressure colors, and pressure ownership
// on an unused allocated/contact-bound clone. Does NOT activate independent wet
// regions: boundary, momentum and particle exchange are still required.
bool RaftSimInstallRegionalLiquidProjection(UNiagaraSystem* System,
    const RaftSimLiquidRegionalState::FParent& Parent,
    const RaftSimLiquidRegionalState::FState& Region,FString& Error);
