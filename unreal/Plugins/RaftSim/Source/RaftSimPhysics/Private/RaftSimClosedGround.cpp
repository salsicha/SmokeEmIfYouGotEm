#include "RaftSimClosedGround.h"
#include "Algo/Sort.h"

void FRaftSimClosedGround::Build(TConstArrayView<FVector> Vertices,TConstArrayView<FIntVector> Faces)
{
    Components.Reset();ClosedComponents=0;
    TMap<FVector,int32> PositionIds;TArray<int32> VertexIds;
    for(const auto& V:Vertices)
    {
        if(const auto* Existing=PositionIds.Find(V))VertexIds.Add(*Existing);
        else {const int32 Id=PositionIds.Num();PositionIds.Add(V,Id);VertexIds.Add(Id);}
    }
    TArray<int32> Parents;Parents.SetNumUninitialized(Faces.Num());
    for(int32 I=0;I<Parents.Num();++I)Parents[I]=I;
    const auto Root=[&](int32 I){while(Parents[I]!=I){Parents[I]=Parents[Parents[I]];I=Parents[I];}return I;};
    struct FEdge {int32 Face=0,Count=0,DirectionSum=0;};
    TMap<uint64,FEdge> Edges;
    for(int32 I=0;I<Faces.Num();++I)
        for(int32 E=0;E<3;++E)
        {
            const int32 A=VertexIds[Faces[I][E]],B=VertexIds[Faces[I][(E+1)%3]];
            const uint64 Key=(uint64(FMath::Min(A,B))<<32)|uint32(FMath::Max(A,B));
            auto& Edge=Edges.FindOrAdd(Key);
            if(Edge.Count==0)Edge.Face=I;else Parents[Root(I)]=Root(Edge.Face);
            ++Edge.Count;Edge.DirectionSum+=A<B?1:A>B?-1:0;
        }
    TSet<int32> Open,Unoriented;
    for(const auto& Entry:Edges)
    {
        const auto& Edge=Entry.Value;const int32 R=Root(Edge.Face);
        if(Edge.Count==1)Open.Add(R);
        if(Edge.Count!=2 || Edge.DirectionSum!=0 || uint32(Entry.Key>>32)==uint32(Entry.Key))Unoriented.Add(R);
    }
    TMap<int32,int32> ComponentIds;
    for(int32 I=0;I<Faces.Num();++I)
    {
        const int32 R=Root(I);
        int32* Found=ComponentIds.Find(R);
        const int32 Index=Found?*Found:Components.AddDefaulted();
        if(!Found)
        {
            ComponentIds.Add(R,Index);auto& C=Components[Index];
            C.bOriented=!Unoriented.Contains(R);C.bClosed=!Open.Contains(R);
            C.RepresentativeVertex=Faces[I].X;if(C.bClosed)++ClosedComponents;
        }
        auto& C=Components[Index];if(C.bClosed)C.Faces.Add(I);
        for(int32 V=0;V<3;++V)C.Bounds+=Vertices[Faces[I][V]];
    }
    for(auto& C:Components)if(C.bClosed && C.bOriented)BuildNode(C,0,C.Faces.Num(),Vertices,Faces);
}

int32 FRaftSimClosedGround::BuildNode(FComponent& C,int32 Begin,int32 Count,
    TConstArrayView<FVector> Vertices,TConstArrayView<FIntVector> Faces)
{
    FNode Node;Node.Begin=Begin;Node.Count=Count;
    for(int32 I=Begin;I<Begin+Count;++I)for(int32 V=0;V<3;++V)Node.Bounds+=Vertices[Faces[C.Faces[I]][V]];
    const int32 Index=C.Nodes.Add(Node);
    if(Count>8)
    {
        const FVector Size=Node.Bounds.GetSize();int32 Axis=Size.Y>Size.X?1:0;if(Size.Z>Size[Axis])Axis=2;
        Algo::Sort(MakeArrayView(C.Faces.GetData()+Begin,Count),[&](int32 A,int32 B)
        {
            const auto& FA=Faces[A];const auto& FB=Faces[B];
            const double CA=Vertices[FA.X][Axis]+Vertices[FA.Y][Axis]+Vertices[FA.Z][Axis];
            const double CB=Vertices[FB.X][Axis]+Vertices[FB.Y][Axis]+Vertices[FB.Z][Axis];
            return CA==CB?A<B:CA<CB;
        });
        const int32 Left=BuildNode(C,Begin,Count/2,Vertices,Faces),Right=BuildNode(C,Begin+Count/2,Count-Count/2,Vertices,Faces);
        C.Nodes[Index].Left=Left;C.Nodes[Index].Right=Right;C.Nodes[Index].Count=0;
    }
    return Index;
}

TOptional<int32> FRaftSimClosedGround::RayWinding(const FComponent& C,const FVector& P,
    TConstArrayView<FVector> Vertices,TConstArrayView<FIntVector> Faces) const
{
    constexpr double Guard=1.e-10;
    const auto Orient=[](const FVector& A,const FVector& B){return A.X*B.Y-A.Y*B.X;};
    const auto Error=[](const FVector& A,const FVector& B){return 32.*DBL_EPSILON*(FMath::Abs(A.X*B.Y)+FMath::Abs(A.Y*B.X))+1.e-24;};
    TArray<int32,TInlineAllocator<64>> Pending;Pending.Add(0);int32 Winding=0;
    while(!Pending.IsEmpty())
    {
        const auto& N=C.Nodes[Pending.Pop(EAllowShrinking::No)];
        if(P.X<N.Bounds.Min.X-Guard || P.X>N.Bounds.Max.X+Guard ||
            P.Y<N.Bounds.Min.Y-Guard || P.Y>N.Bounds.Max.Y+Guard || P.Z>N.Bounds.Max.Z+Guard)continue;
        if(N.Count==0){Pending.Add(N.Left);Pending.Add(N.Right);continue;}
        for(int32 I=N.Begin;I<N.Begin+N.Count;++I)
        {
            const auto& F=Faces[C.Faces[I]];
            const FVector A=Vertices[F.X]-P,B=Vertices[F.Y]-P,D=Vertices[F.Z]-P;
            const FVector AB=B-A,AD=D-A;
            const double Den=Orient(AB,AD),DenError=Error(AB,AD);
            if(FMath::Abs(Den)<=DenError)
            {
                // A ray parallel to the triangle plane is harmless unless its
                // projection could actually lie on that plane. Ambiguity uses
                // the independent full solid-angle calculation below.
                const FVector Edge=AB.SizeSquared2D()>AD.SizeSquared2D()?AB:AD;
                if(FMath::Abs(Orient(Edge,A))<=Error(Edge,A))return {};
                continue;
            }
            const double Sign=Den>0.?1.:-1.;
            const double WA=Orient(B,D),WB=Orient(D,A),WC=Orient(A,B);
            const double EA=Error(B,D),EB=Error(D,A),EC=Error(A,B);
            if(Sign*WA < -EA || Sign*WB < -EB || Sign*WC < -EC)continue;
            if(FMath::Abs(WA)<=EA || FMath::Abs(WB)<=EB || FMath::Abs(WC)<=EC)return {};
            const double Height=(WA*A.Z+WB*B.Z+WC*D.Z)/Den;
            const double HeightError=Guard+(EA*FMath::Abs(A.Z)+EB*FMath::Abs(B.Z)+EC*FMath::Abs(D.Z)+FMath::Abs(Height)*DenError)/FMath::Abs(Den);
            if(!FMath::IsFinite(Height) || FMath::Abs(Height)<=HeightError)return {};
            if(Height>0.)Winding+=Den>0.?1:-1;
        }
    }
    return Winding;
}

void FRaftSimClosedGround::AddEnclosedRepresentatives(const FBox& Bounds,
    TConstArrayView<FVector> Vertices,TArray<FVector>& Points) const
{
    for(const auto& C:Components)
        if(Bounds.IsInsideOrOn(C.Bounds.Min) && Bounds.IsInsideOrOn(C.Bounds.Max))
            Points.Add(Vertices[C.RepresentativeVertex]);
}

FRaftSimClosedGround::ELocation FRaftSimClosedGround::Classify(const FVector& Point,
    TConstArrayView<FVector> Vertices,TConstArrayView<FIntVector> Faces,bool bAccelerated) const
{
    bool Unresolved=false;
    for(const auto& Component:Components)
    {
        if(!Component.bClosed || !Component.Bounds.IsInsideOrOn(Point))continue;
        if(!Component.bOriented){Unresolved=true;continue;}
        if(bAccelerated)
        {
            const auto Winding=RayWinding(Component,Point,Vertices,Faces);
            if(Winding.IsSet())
            {
                if(FMath::Abs(Winding.GetValue())==1)return ELocation::Inside;
                if(Winding.GetValue()!=0)Unresolved=true;
                continue;
            }
        }
        double Sum=0.,Correction=0.;bool Singular=false;
        for(const int32 Index:Component.Faces)
        {
            const auto& F=Faces[Index];FVector V[3];
            for(int32 I=0;I<3;++I)
            {
                V[I]=Vertices[F[I]]-Point;const double Length=V[I].Length();
                if(Length<=1.e-12){Singular=true;break;}
                V[I]/=Length;
            }
            if(Singular)break;
            const double Numerator=FVector::DotProduct(V[0],FVector::CrossProduct(V[1],V[2]));
            const double Denominator=1.+FVector::DotProduct(V[0],V[1])+FVector::DotProduct(V[1],V[2])+FVector::DotProduct(V[2],V[0]);
            if(FMath::Abs(Numerator)+FMath::Abs(Denominator)<1.e-14){Singular=true;break;}
            const double Angle=2.*FMath::Atan2(Numerator,Denominator);
            const double Y=Angle-Correction,T=Sum+Y;Correction=(T-Sum)-Y;Sum=T;
        }
        // This is an ambiguity bound on a dimensionless winding sum, not a
        // collision clearance. Ambiguous points refuse; they never become clear.
        if(!Singular && FMath::Abs(FMath::Abs(Sum)-4.*UE_DOUBLE_PI)<1.e-7)return ELocation::Inside;
        if(Singular || !FMath::IsFinite(Sum) || FMath::Abs(Sum)>1.e-7)Unresolved=true;
    }
    return Unresolved?ELocation::Unresolved:ELocation::Outside;
}
