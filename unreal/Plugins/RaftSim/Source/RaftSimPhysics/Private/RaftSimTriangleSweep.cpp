#include "RaftSimTriangleSweep.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "PhysicsEngine/BodySetup.h"
#include "Interface_CollisionDataProviderCore.h"
#include "Algo/Sort.h"

namespace
{
UStaticMesh* CollisionSource(UStaticMesh* Mesh)
{
#if WITH_EDITORONLY_DATA
    if(Mesh && Mesh->ComplexCollisionMesh && Mesh->ComplexCollisionMesh!=Mesh)return Mesh->ComplexCollisionMesh;
#endif
    return Mesh;
}
bool EntryRoot(double A,double B,double C,double& T)
{
    if(A<=1.e-28)return false;
    const double Disc=B*B-4.*A*C;
    if(Disc<0.)return false;
    const double Root=FMath::Sqrt(Disc);
    const double Q=-.5*(B+(B>=0.?Root:-Root));
    double First,Second;
    if(FMath::Abs(Q)>1.e-28){First=Q/A;Second=C/Q;if(First>Second)Swap(First,Second);}
    else First=Second=-B/(2.*A);
    // Only the entering root. The exit from a capsule's infinite cylinder
    // must not become an artificial impact; endcaps are tested separately.
    T=First;
    return T>=0. && T<=1.;
}
bool Better(const FHitResult& A,const FHitResult& B)
{
    if(A.bStartPenetrating!=B.bStartPenetrating)return A.bStartPenetrating;
    if(A.bStartPenetrating)return A.PenetrationDepth>B.PenetrationDepth;
    return A.Time<B.Time;
}
}

bool RaftSimTriangleSweep::Triangle(const FVector& Start,const FVector& End,double Radius,
    const FVector& A,const FVector& B,const FVector& C,FHitResult& Hit)
{
    const FVector Delta=End-Start,AB=B-A,AC=C-A;
    const FVector Cross=FVector::CrossProduct(AB,AC);
    const double Area2=Cross.Length();
    if(Area2<=1.e-18)return false; // zero-area source faces have no surface
    const FVector N=Cross/Area2;
    const FVector Closest=FMath::ClosestPointOnTriangleToPoint(Start,A,B,C);
    const FVector Separation=Start-Closest;
    const double Distance=Separation.Length();
    if(Distance<Radius)
    {
        Hit=FHitResult();Hit.Time=0;Hit.bStartPenetrating=true;
        Hit.PenetrationDepth=float(Radius-Distance);
        Hit.Normal=Distance>1.e-15?Separation/Distance:(FVector::DotProduct(Delta,N)<0.?N:-N);
        Hit.ImpactNormal=Hit.Normal;Hit.Location=Start;Hit.ImpactPoint=Closest;
        return true;
    }
    bool Found=false;double Earliest=1.;
    const auto Accept=[&](double T,const FVector& Point,const FVector& Normal)
    {
        if(T<0. || T>Earliest || FVector::DotProduct(Delta,Normal)>=-1.e-14)return;
        Earliest=T;Found=true;Hit=FHitResult();Hit.Time=float(T);
        Hit.Normal=Normal;Hit.ImpactNormal=Normal;Hit.Location=Start+Delta*T;Hit.ImpactPoint=Point;
    };
    const double StartDistance=FVector::DotProduct(Start-A,N);
    const double NormalMotion=FVector::DotProduct(Delta,N);
    for(double Sign:{-1.,1.})
    {
        if(Sign*NormalMotion>=-1.e-14)continue;
        const double T=(Sign*Radius-StartDistance)/NormalMotion;
        if(T<0. || T>Earliest)continue;
        const FVector Point=Start+Delta*T-N*(Sign*Radius);
        // Edge half-spaces in double precision. Tolerance is only roundoff
        // scaled by source triangle area, not a contact/clearance allowance.
        const double Tol=1.e-12*Area2;
        if(FVector::DotProduct(FVector::CrossProduct(B-A,Point-A),N)>=-Tol &&
           FVector::DotProduct(FVector::CrossProduct(C-B,Point-B),N)>=-Tol &&
           FVector::DotProduct(FVector::CrossProduct(A-C,Point-C),N)>=-Tol)
            Accept(T,Point,N*Sign);
    }
    const FVector V[3]={A,B,C};
    for(int32 I=0;I<3;++I)
    {
        const FVector E=V[(I+1)%3]-V[I];const double Length=E.Length();
        if(Length<=1.e-15)continue;
        const FVector Axis=E/Length,Offset=Start-V[I];
        const FVector Perp=Offset-Axis*FVector::DotProduct(Offset,Axis);
        const FVector Motion=Delta-Axis*FVector::DotProduct(Delta,Axis);
        double T;
        if(EntryRoot(Motion.SizeSquared(),2.*FVector::DotProduct(Perp,Motion),Perp.SizeSquared()-Radius*Radius,T))
        {
            const FVector Centre=Start+Delta*T;
            const double Along=FVector::DotProduct(Centre-V[I],Axis);
            if(Along>=0. && Along<=Length)
            {
                const FVector Point=V[I]+Axis*Along;
                Accept(T,Point,(Centre-Point).GetSafeNormal());
            }
        }
        if(EntryRoot(Delta.SizeSquared(),2.*FVector::DotProduct(Offset,Delta),Offset.SizeSquared()-Radius*Radius,T))
            Accept(T,V[I],(Start+Delta*T-V[I]).GetSafeNormal());
    }
    return Found;
}

RaftSimSurfaceSweep::FResult FRaftSimTriangleSweepMesh::SweepSurface(
    TConstArrayView<FVector> StartCm,TConstArrayView<FVector> EndCm,
    TConstArrayView<FIntVector> Faces,double SkinCm,double ProvenClearanceCm,bool bGroupedBroadPhase) const
{
    using namespace RaftSimSurfaceSweep;
    FResult Best;
    if(!bValid || StartCm.IsEmpty() || StartCm.Num()!=EndCm.Num() || Faces.IsEmpty() ||
        !FMath::IsFinite(SkinCm) || SkinCm<=1.e-8 || !FMath::IsFinite(ProvenClearanceCm) || ProvenClearanceCm>=SkinCm)return Best;
    TArray<FVector> LocalStart,LocalEnd;
    FBox InitialBounds(ForceInit);
    if(bGroupedBroadPhase){LocalStart.SetNumUninitialized(StartCm.Num());LocalEnd.SetNumUninitialized(EndCm.Num());}
    for(int32 I=0;I<StartCm.Num();++I)
    {
        if(StartCm[I].ContainsNaN() || EndCm[I].ContainsNaN())return Best;
        // Exactly the reference arithmetic, once per original vertex rather
        // than repeated for each indexed face and its enclosing group.
        if(bGroupedBroadPhase){LocalStart[I]=(StartCm[I]-OriginCm)*.01;LocalEnd[I]=(EndCm[I]-OriginCm)*.01;}
        InitialBounds+=bGroupedBroadPhase?LocalStart[I]:(StartCm[I]-OriginCm)*.01;
    }
    for(const auto& F:Faces)
        if(!StartCm.IsValidIndex(F.X) || !StartCm.IsValidIndex(F.Y) || !StartCm.IsValidIndex(F.Z))return Best;
    if(ClosedGround.ComponentCount()>0)
    {
        if(MovingTopology.Num()!=Faces.Num() ||
            FMemory::Memcmp(MovingTopology.GetData(),Faces.GetData(),Faces.Num()*sizeof(FIntVector))!=0)
        {
            MovingTopology.Reset(Faces.Num());MovingTopology.Append(Faces.GetData(),Faces.Num());MovingRepresentatives.Reset();
            TArray<int32> Parents;Parents.SetNumUninitialized(StartCm.Num());
            for(int32 I=0;I<Parents.Num();++I)Parents[I]=I;
            const auto Root=[&](int32 I){while(Parents[I]!=I){Parents[I]=Parents[Parents[I]];I=Parents[I];}return I;};
            for(const auto& F:Faces){Parents[Root(F.Y)]=Root(F.X);Parents[Root(F.Z)]=Root(F.X);}
            TSet<int32> Seen;
            for(int32 I=0;I<Faces.Num();++I)
            {const int32 R=Root(Faces[I].X);if(!Seen.Contains(R)){Seen.Add(R);MovingRepresentatives.Add(FIntPoint(Faces[I].X,I));}}
        }
        // Every connected moving sheet is checked, not just the raft centre or
        // selected supports. If a sheet is not wholly on the representative's
        // side, its initial surface crossing is detected by the triangle sweep.
        for(const auto& Representative:MovingRepresentatives)
        {
            const auto Location=ClosedGround.Classify((StartCm[Representative.X]-OriginCm)*.01,Vertices,Triangles);
            if(Location!=FRaftSimClosedGround::ELocation::Outside)
            {
                Best.Status=Location==FRaftSimClosedGround::ELocation::Inside?EStatus::InitialIntersection:EStatus::Unresolved;
                Best.MovingFace=Representative.Y;return Best;
            }
        }
    }
    {
        // Reverse containment is possible only when the complete source
        // component bounds fit inside the initial hull bounds. Actual crossing
        // surfaces still use the full original-triangle narrow phase below.
        TArray<FVector> EnclosedGroundPoints;
        ClosedGround.AddEnclosedRepresentatives(InitialBounds,Vertices,EnclosedGroundPoints);
        if(!EnclosedGroundPoints.IsEmpty())
        {
            if(!bGroupedBroadPhase)
            {LocalStart.SetNumUninitialized(StartCm.Num());for(int32 I=0;I<StartCm.Num();++I)LocalStart[I]=(StartCm[I]-OriginCm)*.01;}
            // Rebuild from this exact deformed pose: separated seams must not
            // inherit closure from a rest mesh or a previous deformation.
            FRaftSimClosedGround ClosedHull;ClosedHull.Build(LocalStart,Faces);
            for(const auto& Point:EnclosedGroundPoints)
            {
                const auto Location=ClosedHull.Classify(Point,LocalStart,Faces);
                if(Location!=FRaftSimClosedGround::ELocation::Outside)
                {
                    Best.Status=Location==FRaftSimClosedGround::ELocation::Inside?EStatus::InitialIntersection:EStatus::Unresolved;
                    return Best;
                }
            }
        }
    }
    Best.Status=EStatus::Clear;Best.Time=1.;uint64 Pairs=0;
    TArray<int32,TInlineAllocator<64>> GroupLeaves;
    for(int32 Face=0;Face<Faces.Num();++Face)
    {
        if(bGroupedBroadPhase && Face%64==0)
        {
            // Amortize the upper tree walk across consecutive source faces.
            // This box contains EVERY endpoint in the group; no face, time,
            // deformation or source triangle is approximated or omitted.
            FBox GroupBounds(ForceInit);
            const double Limit=Best.Status==EStatus::Contact?Best.Time:1.;
            for(int32 F=Face;F<FMath::Min(Face+64,Faces.Num());++F)
                for(int32 V=0;V<3;++V)
                {
                    const int32 Index=Faces[F][V];
                    const FVector A=LocalStart[Index],B=LocalEnd[Index];
                    GroupBounds+=A;GroupBounds+=A+(B-A)*Limit;
                }
            GroupBounds=GroupBounds.ExpandBy(SkinCm*.01+1.e-10);
            GroupLeaves.Reset();TArray<int32,TInlineAllocator<64>> Pending;Pending.Add(0);
            while(!Pending.IsEmpty())
            {
                const int32 Index=Pending.Pop(EAllowShrinking::No);const auto& Node=Nodes[Index];
                if(!GroupBounds.Intersect(Node.Bounds))continue;
                if(Node.Count==0){Pending.Add(Node.Left);Pending.Add(Node.Right);}
                else GroupLeaves.Add(Index);
            }
        }
        if(bGroupedBroadPhase && GroupLeaves.IsEmpty())continue;
        const auto& Indices=Faces[Face];FTriangle Start,End;FBox Bounds(ForceInit);
        const double BoundLimit=Best.Status==EStatus::Contact?Best.Time:1.;
        for(int32 I=0;I<3;++I)
        {
            Start.V[I]=bGroupedBroadPhase?LocalStart[Indices[I]]:(StartCm[Indices[I]]-OriginCm)*.01;
            End.V[I]=bGroupedBroadPhase?LocalEnd[Indices[I]]:(EndCm[Indices[I]]-OriginCm)*.01;
            Bounds+=Start.V[I];Bounds+=Start.V[I]+(End.V[I]-Start.V[I])*BoundLimit;
        }
        Bounds=Bounds.ExpandBy(SkinCm*.01+1.e-10);
        TArray<int32,TInlineAllocator<64>> Stack;
        // Reverse insertion preserves the exact reference DFS leaf/pair order,
        // including first-hit ties. Per-face bounds still filter every leaf.
        if(bGroupedBroadPhase)
            for(int32 I=GroupLeaves.Num()-1;I>=0;--I)Stack.Add(GroupLeaves[I]);
        else Stack.Add(0);
        while(!Stack.IsEmpty())
        {
            const auto& Node=Nodes[Stack.Pop(EAllowShrinking::No)];
            if(!Bounds.Intersect(Node.Bounds))continue;
            if(Node.Count==0){Stack.Add(Node.Left);Stack.Add(Node.Right);continue;}
            for(int32 I=Node.Begin;I<Node.Begin+Node.Count;++I)
            {
                const int32 GroundFace=Order[I];const auto& T=Triangles[GroundFace];
                const FTriangle Ground{{Vertices[T.X],Vertices[T.Y],Vertices[T.Z]}};
                FBox FaceBounds(ForceInit);for(const auto& V:Ground.V)FaceBounds+=V;
                if(!Bounds.Intersect(FaceBounds))continue;
                // Once an impact is known, later events cannot change the
                // earliest result. Prove every other source pair only up to
                // that time, rather than entering already-forbidden geometry
                // and rejecting an irrelevant later near-tangent event.
                const double Limit=Best.Status==EStatus::Contact?Best.Time:1.;
                FTriangle ClippedEnd;
                for(int32 V=0;V<3;++V)ClippedEnd.V[V]=Start.V[V]+(End.V[V]-Start.V[V])*Limit;
                ++Pairs;auto Hit=RaftSimSurfaceSweep::Sweep(Start,ClippedEnd,Ground,SkinCm*.01,128,ProvenClearanceCm*.01);
                Hit.Time*=Limit;
                Hit.MovingFace=Face;Hit.GroundFace=GroundFace;
                // Witness positions returned in world metres; normals already
                // include the exact source component scale/reflection/rotation.
                Hit.Witness.MovingPoint+=OriginCm*.01;Hit.Witness.GroundPoint+=OriginCm*.01;
                if(Hit.Status==EStatus::Invalid || Hit.Status==EStatus::Unresolved || Hit.Status==EStatus::InitialIntersection)
                {Hit.TrianglePairs=Pairs;return Hit;}
                if(Hit.Status==EStatus::Contact && (Best.Status==EStatus::Clear || Hit.Time<Best.Time))Best=Hit;
            }
        }
    }
    Best.TrianglePairs=Pairs;return Best;
}

bool FRaftSimTriangleSweepMesh::Matches(UStaticMeshComponent* Component) const
{
    UStaticMesh* Mesh=Component?Component->GetStaticMesh():nullptr;
    const UBodySetup* Body=Mesh?Mesh->GetBodySetup():nullptr;
    UStaticMesh* Source=CollisionSource(Mesh);
    return Mesh && Asset.Get()==Mesh && Body && BodyGuid==Body->BodySetupGuid &&
        TraceFlag==int32(Body->GetCollisionTraceFlag()) && CollisionAsset.Get()==Source &&
        Source && CollisionLightingGuid==Source->GetLightingGuid() &&
        Transform.Equals(Component->GetComponentTransform(),0.);
}

bool FRaftSimTriangleSweepMesh::Build(UStaticMeshComponent* Component)
{
    bValid=false;Vertices.Reset();Triangles.Reset();Order.Reset();Nodes.Reset();
    UStaticMesh* Mesh=Component?Component->GetStaticMesh():nullptr;
    if(!Mesh || !Mesh->HasValidRenderData() || !Mesh->GetBodySetup())return false;
    Asset=Mesh;BodyGuid=Mesh->GetBodySetup()->BodySetupGuid;
    CollisionAsset=CollisionSource(Mesh);CollisionLightingGuid=CollisionAsset->GetLightingGuid();
    TraceFlag=int32(Mesh->GetBodySetup()->GetCollisionTraceFlag());
    Transform=Component->GetComponentTransform();OriginCm=Transform.GetTranslation();
    // A simple-only substitute is not evidence for complex source triangles.
    if(TraceFlag==int32(CTF_UseSimpleAsComplex))return false;
    FTriMeshCollisionData Data;
    // false preserves the configured collision LOD and enabled sections;
    // the provider also resolves an explicitly assigned complex-collision mesh.
    if(!Mesh->GetPhysicsTriMeshData(&Data,false))return false;
    Vertices.Reserve(Data.Vertices.Num());
    for(const auto& V:Data.Vertices)
    {
        const FVector P=(Transform.TransformPosition(FVector(V))-OriginCm)*.01;
        if(P.ContainsNaN())return false;
        Vertices.Add(P);
    }
    Triangles.Reserve(Data.Indices.Num());Order.Reserve(Data.Indices.Num());
    for(const auto& T:Data.Indices)
    {
        if(!Vertices.IsValidIndex(T.v0) || !Vertices.IsValidIndex(T.v1) || !Vertices.IsValidIndex(T.v2))return false;
        Order.Add(Triangles.Add(FIntVector(T.v0,T.v1,T.v2)));
    }
    if(Triangles.IsEmpty())return false;
    ClosedGround.Build(Vertices,Triangles);MovingTopology.Reset();MovingRepresentatives.Reset();
    Nodes.Reserve(Triangles.Num()/4+1);BuildNode(0,Order.Num());
    bValid=true;return true;
}

int32 FRaftSimTriangleSweepMesh::BuildNode(int32 Begin,int32 Count)
{
    FNode Node;Node.Begin=Begin;Node.Count=Count;
    for(int32 I=Begin;I<Begin+Count;++I)
    {
        const auto& T=Triangles[Order[I]];
        Node.Bounds+=Vertices[T.X];Node.Bounds+=Vertices[T.Y];Node.Bounds+=Vertices[T.Z];
    }
    const int32 Index=Nodes.Add(Node);
    if(Count>8)
    {
        const FVector Extent=Node.Bounds.GetSize();int32 Axis=0;
        if(Extent.Y>Extent.X)Axis=1;if(Extent.Z>Extent[Axis])Axis=2;
        Algo::Sort(MakeArrayView(Order.GetData()+Begin,Count),[&](int32 A,int32 B)
        {
            const auto& TA=Triangles[A];const auto& TB=Triangles[B];
            const double CA=Vertices[TA.X][Axis]+Vertices[TA.Y][Axis]+Vertices[TA.Z][Axis];
            const double CB=Vertices[TB.X][Axis]+Vertices[TB.Y][Axis]+Vertices[TB.Z][Axis];
            return CA==CB?A<B:CA<CB;
        });
        const int32 Left=BuildNode(Begin,Count/2),Right=BuildNode(Begin+Count/2,Count-Count/2);
        Nodes[Index].Left=Left;Nodes[Index].Right=Right;Nodes[Index].Count=0;
    }
    return Index;
}

bool FRaftSimTriangleSweepMesh::Sweep(const FVector& StartCm,const FVector& EndCm,double RadiusCm,FHitResult& Hit) const
{
    if(!bValid)return false;
    const FVector Start=(StartCm-OriginCm)*.01,End=(EndCm-OriginCm)*.01;
    const double Radius=RadiusCm*.01;
    FBox Bounds(ForceInit);Bounds+=Start;Bounds+=End;Bounds=Bounds.ExpandBy(Radius);
    TArray<int32,TInlineAllocator<64>> Stack;Stack.Add(0);bool Found=false;
    while(!Stack.IsEmpty())
    {
        const auto& Node=Nodes[Stack.Pop(EAllowShrinking::No)];
        if(!Bounds.Intersect(Node.Bounds))continue;
        if(Node.Count==0){Stack.Add(Node.Left);Stack.Add(Node.Right);continue;}
        for(int32 I=Node.Begin;I<Node.Begin+Node.Count;++I)
        {
            const int32 Face=Order[I];const auto& T=Triangles[Face];FHitResult Candidate;
            if(RaftSimTriangleSweep::Triangle(Start,End,Radius,Vertices[T.X],Vertices[T.Y],Vertices[T.Z],Candidate) &&
                (!Found || Better(Candidate,Hit)))
            {Hit=Candidate;Hit.FaceIndex=Face;Found=true;}
        }
    }
    if(Found)
    {
        Hit.Location=OriginCm+Hit.Location*100.;Hit.ImpactPoint=OriginCm+Hit.ImpactPoint*100.;
        Hit.PenetrationDepth*=100.f;Hit.Distance=float((Hit.Location-StartCm).Length());Hit.bBlockingHit=true;
    }
    return Found;
}
