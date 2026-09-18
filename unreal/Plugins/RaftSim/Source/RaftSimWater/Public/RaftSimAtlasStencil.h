#pragma once
#include "CoreMinimal.h"

// Query-local address reuse only. No water values, validity decisions or
// interpolation weights survive a query. Cross-tile neighbors use the exact
// original lookup, including missing tiles and negative global coordinates.
struct FRaftSimAtlasStencil
{
    int64 X,Y;
    int32 Nx,Ny,Center,LocalX=0,LocalY=0;

    template<typename Lookup>
    FRaftSimAtlasStencil(int64 InX,int64 InY,int32 InNx,int32 InNy,const Lookup& Index)
        : X(InX),Y(InY),Nx(InNx),Ny(InNy),Center(Index(X,Y))
    {
        if(Center!=INDEX_NONE)
        {
            LocalX=Center%Nx;
            LocalY=(Center/Nx)%Ny;
        }
    }

    template<typename Lookup>
    int32 At(int64 Column,int64 Row,const Lookup& Index) const
    {
        const int64 DX=Column-X,DY=Row-Y;
        if(DX==0 && DY==0)return Center;
        if(Center!=INDEX_NONE && LocalX+DX>=0 && LocalX+DX<Nx &&
            LocalY+DY>=0 && LocalY+DY<Ny)
            return int32(int64(Center)+DY*Nx+DX);
        return Index(Column,Row);
    }
};
