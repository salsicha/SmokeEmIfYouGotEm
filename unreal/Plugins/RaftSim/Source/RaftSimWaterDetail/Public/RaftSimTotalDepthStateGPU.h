#pragma once
#include "CoreMinimal.h"
#include "RenderGraphFwd.h"

// Conserved state is (h, hu, hv, transported foam density), never eta/q.
// A render offset is an output only: it must never be decoded back into h.
// This storage/projection stage does not implement pressure, boundaries or
// evolution, and is not enabled by the existing perturbation gameplay owner.
struct RAFTSIMWATERDETAIL_API FRaftSimTotalDepthStateResult
{
    FRDGBufferRef State=nullptr;
    FRDGBufferRef Surface=nullptr; // offset metres, dx, dy, bounded foam coverage
    FRDGBufferRef Diagnostics=nullptr; // invalid state, invalid reference, overlap, exposed
    FRDGBufferRef WindowExchange=nullptr; // cumulative entered-minus-departed h/hu/hv/foam, density units by slot
};

// Exact cell-aligned transfer. Retained cells are copied bit-for-bit even when
// the reference mean changes or becomes dry. Exposed cells use the explicitly
// supplied NewDomainState; no periodic wrap, zero reseed or mean-depth masking.
// Reference is float2 (actual bed, reference carrier surface), on the NEW grid.
// Surface is derived from this same immutable input state; no clock advances.
// Invalid values are counted, never repaired in State. An owner must reject
// publication of an invalid frame; diagnostics are not permission to render it.
RAFTSIMWATERDETAIL_API FRaftSimTotalDepthStateResult RaftSimTransferTotalDepthStateGPU(
    FRDGBuilder& Graph,FRDGBufferRef PreviousState,FRDGBufferRef NewDomainState,
    FRDGBufferRef Reference,FIntPoint Size,FIntPoint SourceOffset,float CellMeters,FString& Error,
    FRDGBufferRef PreviousWindowExchange=nullptr);
