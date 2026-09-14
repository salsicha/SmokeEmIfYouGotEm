#pragma once
#include "CoreMinimal.h"
#include "RenderGraphFwd.h"

struct RAFTSIMWATERDETAIL_API FRaftSimPressureResidualCheck
{
    FRDGBufferRef Diagnostics=nullptr; // uint4(nonfinite/invalid values, raw-pole bits0/1 and physical-pole bits2/3,0,0)
    FRDGBufferRef Norms=nullptr; // one float4 norm record; optional second sqrt(h)-weighted record
};

// Qualify both poles' TRUE A*x-b residual, not the PCG recurrence residual.
// Per-pole scaling precedes squaring to avoid false passes from underflow or
// overflow. A zero RHS requires an exactly zero residual. Fixed2e-5 relative
// bound, no readback. Combine these flags with transport/pressure/solver errors.
// Optional same-stage Geometry=float2(h,bed) additionally enforces the SAME
// 2e-5 bound on sqrt(h)*(A*x-b), the conservative momentum-equation residual.
// Exponent normalization precedes multiplying depth roots, avoiding premature
// underflow/overflow. This adds a gate; it never replaces the raw residual gate.
RAFTSIMWATERDETAIL_API FRaftSimPressureResidualCheck RaftSimCheckPressureResidualGPU(
    FRDGBuilder& Graph,FRDGBufferRef RHS,FRDGBufferRef Residual,FIntPoint Size,FString& Error,FRDGBufferRef Geometry=nullptr);
