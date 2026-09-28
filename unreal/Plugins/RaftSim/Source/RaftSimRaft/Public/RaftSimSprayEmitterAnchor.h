#pragma once
#include "CoreMinimal.h"

namespace RaftSimSprayEmitterAnchor
{
// Attach at the emitter's OWN horizontal position, not the crest-site centre.
// The sampler must return the visible wet carrier (including its render lift).
// Failure leaves the proposed origin unchanged; callers must disable emission.
// This anchors only the source centre, not its whole plane or particle paths.
template<class FSampler>
bool Attach(FVector& InOutOriginCm,double ClearanceCm,FSampler&& SampleWorld)
{
    if(InOutOriginCm.ContainsNaN() || !FMath::IsFinite(ClearanceCm) || ClearanceCm<0.)return false;
    FVector Carrier;
    if(!SampleWorld(InOutOriginCm,Carrier) || Carrier.ContainsNaN())return false;
    const double Height=Carrier.Z+ClearanceCm;
    if(!FMath::IsFinite(Height))return false;
    InOutOriginCm.Z=Height;
    return true;
}
}
