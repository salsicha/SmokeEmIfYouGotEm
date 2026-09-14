#pragma once
#include "RaftSimTotalDepthSource.h"

// Validation concerns source identity only. It never reconstructs evolved
// interiors from the mean and never fabricates a temporal boundary bracket.
struct FRaftSimWindowSourceTransition
{
    static bool SameWindow(const FRaftSimTotalDepthSource& A,const FRaftSimTotalDepthSource& B)
    {return A.Size==B.Size && A.CellMeters==B.CellMeters && A.OriginMeters==B.OriginMeters && A.Bed==B.Bed && A.ExteriorBed==B.ExteriorBed;}
    static bool Validate(const FRaftSimTotalDepthSource& Previous,const FRaftSimTotalDepthSource& Closing,
        const FRaftSimTotalDepthSource& Opening,FIntPoint& Offset,FString& Error)
    {
        if(!Closing.Validate(Error) || !Opening.Validate(Error))return false;
        if(Closing.ClosingWindowSource || !SameWindow(Previous,Closing) || Closing.SampleSeconds<Previous.SampleSeconds ||
            Closing.Revision<=Previous.Revision || Opening.SampleSeconds!=Closing.SampleSeconds || Opening.Revision<=Closing.Revision ||
            Opening.Size!=Closing.Size || Opening.CellMeters!=Closing.CellMeters)
        {Error=TEXT("Window move needs ordered, same-instant closing/entering sources on the unchanged old bed");return false;}
        const auto Shift=(Opening.OriginMeters-Closing.OriginMeters)/Opening.CellMeters;
        if(Shift.ContainsNaN() || FMath::Abs(Shift.X)>=Opening.Size.X || FMath::Abs(Shift.Y)>=Opening.Size.Y ||
            (Shift.X==0 && Shift.Y==0) || Shift.X!=FMath::FloorToFloat(Shift.X) || Shift.Y!=FMath::FloorToFloat(Shift.Y))
        {Error=TEXT("Window move requires nonzero cell-aligned overlap; teleports need a separate lifecycle");return false;}
        Offset=FIntPoint(int32(Shift.X),int32(Shift.Y));
        for(int32 Y=0;Y<Opening.Size.Y;++Y)for(int32 X=0;X<Opening.Size.X;++X)
        {
            const FIntPoint P=FIntPoint(X,Y)+Offset;
            if(P.X<0 || P.Y<0 || P.X>=Closing.Size.X || P.Y>=Closing.Size.Y)continue;
            const int32 I=Y*Opening.Size.X+X,J=P.Y*Closing.Size.X+P.X;
            if(Opening.Bed[I]!=Closing.Bed[J] || Opening.Reference[I]!=Closing.Reference[J] || Opening.State[I]!=Closing.State[J])
            {Error=TEXT("Same-instant window sources disagree on represented overlapping state/geometry");return false;}
        }
        if(Closing.SampleSeconds==Previous.SampleSeconds &&
            (Closing.State!=Previous.State || Closing.Reference!=Previous.Reference || Closing.ExteriorState!=Previous.ExteriorState ||
             Closing.FaceNormalVelocity!=Previous.FaceNormalVelocity))
        {Error=TEXT("Unadvanced native time changed the closing source");return false;}
        Error.Reset();return true;
    }
};
