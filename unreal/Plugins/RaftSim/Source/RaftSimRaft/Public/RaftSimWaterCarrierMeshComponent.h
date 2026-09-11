#pragma once
#include "CoreMinimal.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimWaterCarrierMeshComponent.generated.h"

// WPO changes geometry without a CPU vertex upload. Culling must follow the
// live hydraulic bounds, not the immutable mesh's startup height.
UCLASS()
class RAFTSIMRAFT_API URaftSimWaterCarrierMeshComponent : public UProceduralMeshComponent
{
    GENERATED_BODY()
public:
    void SetHydraulicBounds(const FBox& InHydraulicBounds)
    {
        HydraulicBounds=InHydraulicBounds;UpdateBounds();MarkRenderTransformDirty();
    }
    virtual FBoxSphereBounds CalcBounds(const FTransform& LocalToWorld) const override
    {
        return HydraulicBounds.IsValid ? FBoxSphereBounds(HydraulicBounds).TransformBy(LocalToWorld) : Super::CalcBounds(LocalToWorld);
    }
private:
    FBox HydraulicBounds=FBox(ForceInit);
};
