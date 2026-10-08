#pragma once
#include "CoreMinimal.h"
#include "Serialization/Archive.h"

namespace RaftSimSupportBandLayout
{
// Keep the original worst-case allocation allowance (512 x 200000), rather
// than rejecting a longer, narrower river that uses fewer bytes. A full V9
// Colorado baseline is 351 x 225158: 712174794 encoded bytes, below this cap.
constexpr int64 MaxCells=int64(512)*200000;
constexpr int64 MaxEncodedBytes=40+int64(4)*200000+9*MaxCells;

inline bool Preflight(FArchive& Reader,int32 Width,int32 Rows,float Origin,float Spacing)
{
    // Reject untrusted dimensions before multiplying: arbitrary int32 headers
    // could otherwise overflow int64 when converted to an encoded byte size.
    if(Width<2 || Width>512 || Rows<2)return false;
    const int64 Cells=int64(Width)*Rows;
    const int64 Bytes=40+int64(4)*Rows+9*Cells;
    if(Reader.IsError() || Reader.Tell()!=24 ||
        Cells>MaxCells || Bytes>MaxEncodedBytes || Reader.TotalSize()!=Bytes ||
        !FMath::IsFinite(Origin) || !FMath::IsFinite(Spacing) || Spacing<=0.f)return false;
    // Check every serialized TArray count BEFORE operator<< can allocate it.
    // Seek over payloads; no full-field buffer is used by this inspection.
    const int32 Counts[]={Rows,int32(Cells),int32(Cells),int32(Cells)};
    const int32 Strides[]={4,4,4,1};
    for(int32 I=0;I<4;++I)
    {
        int32 Count=0;Reader<<Count;
        if(Reader.IsError() || Count!=Counts[I])return false;
        Reader.Seek(Reader.Tell()+int64(Count)*Strides[I]);
        if(Reader.IsError())return false;
    }
    if(Reader.Tell()!=Bytes)return false;
    Reader.Seek(24);
    return !Reader.IsError();
}
}
