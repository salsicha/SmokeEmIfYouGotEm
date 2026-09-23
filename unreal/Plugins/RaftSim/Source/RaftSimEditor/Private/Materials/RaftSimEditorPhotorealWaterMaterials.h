#pragma once
#include "CoreMinimal.h"
class UMaterial;

namespace RaftSimPhotorealMaterials
{
// Existing command builders; splitting source does not regenerate assets.
UMaterial* BuildPhotorealRiverWaterMaterial(
    const TCHAR* PackagePath = TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverWater"),
    const TCHAR* ObjectName = TEXT("M_RaftSim_PhotorealRiverWater"));
UMaterial* BuildLiveRiverSurfaceMaterial();
UMaterial* BuildPaddleWakeRippleMaterial();
}
