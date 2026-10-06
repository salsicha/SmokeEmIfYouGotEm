#pragma once
#include "RaftSimSurfaceSweep.h"

namespace RaftSimHullArcClearance
{
// Exact motion derivatives at the interval start, with a proven global bound
// on |third derivative|. g''(t)>=g''(0)-J*h bounds the complete projected path
// below by a quadratic. A positive minimum for every source vertex separates
// its entire rotating/deforming triangle from this STATIC ground triangle.
// Unlike a uniform chord-error slab, this does not invent overlap at t=0.
inline bool PlaneSeparated(const RaftSimSurfaceSweep::FTriangle& Start,
    const RaftSimSurfaceSweep::FTriangle& Velocity,const RaftSimSurfaceSweep::FTriangle& Acceleration,
    const RaftSimSurfaceSweep::FTriangle& Ground,FVector Axis,double H,double JerkBound)
{
    const double Length=Axis.Length();
    if(Length<=1.e-14 || H<=0. || !FMath::IsFinite(H) || !FMath::IsFinite(JerkBound) || JerkBound<0.)return false;
    Axis/=Length;double GroundMax=-DBL_MAX;
    const FVector Origin=Ground.V[0];
    for(const auto& P:Ground.V)GroundMax=FMath::Max(GroundMax,FVector::DotProduct(P-Origin,Axis));
    for(int32 I=0;I<3;++I)
    {
        const double G=FVector::DotProduct(Start.V[I]-Origin,Axis)-GroundMax;
        const double V=FVector::DotProduct(Velocity.V[I],Axis);
        const double A=FVector::DotProduct(Acceleration.V[I],Axis)-JerkBound*H;
        const auto Lower=[&](double T){return G+V*T+.5*A*T*T;};
        double Minimum=FMath::Min(G,Lower(H));
        if(A>0.)Minimum=FMath::Min(Minimum,Lower(FMath::Clamp(-V/A,0.,H)));
        if(!FMath::IsFinite(Minimum) || Minimum<=1.e-9)return false;
    }
    return true;
}

// A rigid source face is fixed in its own rotating frame. Transform the actual
// STATIC ground triangle into that frame and bound its inverse rigid motion.
// This captures a resting ground CORNER against a rotating source face, where
// no fixed world plane separates every vertex for the whole interval.
inline bool RigidFaceSeparated(const RaftSimSurfaceSweep::FTriangle& SourceLocal,
    const RaftSimSurfaceSweep::FTriangle& GroundWorld,const FQuat& Q,const FVector& Position,
    const FVector& LinearVelocity,const FVector& AngularVelocity,double H)
{
    using namespace RaftSimSurfaceSweep;
    const FVector W=Q.UnrotateVector(AngularVelocity),L=Q.UnrotateVector(LinearVelocity);
    FTriangle GroundLocal,Velocity,Acceleration;double Radius=0.;
    for(int32 I=0;I<3;++I)
    {
        const FVector R=Q.UnrotateVector(GroundWorld.V[I]-Position);GroundLocal.V[I]=R;
        Velocity.V[I]=-L-FVector::CrossProduct(W,R);
        Acceleration.V[I]=FVector::CrossProduct(W,FVector::CrossProduct(W,R))+2.*FVector::CrossProduct(W,L);
        Radius=FMath::Max(Radius,R.Length());
    }
    const double Omega=W.Length(),Speed=L.Length();
    const double J=Omega*Omega*Omega*(Radius+Speed*H)+3.*Omega*Omega*Speed;
    const auto ClearAxis=[&](const FVector& N)
    {return PlaneSeparated(GroundLocal,Velocity,Acceleration,SourceLocal,N,H,J)
        || PlaneSeparated(GroundLocal,Velocity,Acceleration,SourceLocal,-N,H,J);};
    const FVector N=FVector::CrossProduct(SourceLocal.V[1]-SourceLocal.V[0],SourceLocal.V[2]-SourceLocal.V[0]);
    if(ClearAxis(N))return true;
    for(int32 I=0;I<3;++I)
        if(ClearAxis(FVector::CrossProduct(N,SourceLocal.V[(I+1)%3]-SourceLocal.V[I])))return true;
    return false;
}

// Rigid edge/edge separating axis N(t)=rotated_source_edge(t) x ground_edge.
// All NINE source/ground vertex differences must stay positive (or negative).
// Differentiating this unnormalised axis avoids a false fixed-plane enclosure
// while retaining a bounded complete-interval separation proof.
inline bool RigidEdgeAxisSeparated(const RaftSimSurfaceSweep::FTriangle& SourceLocal,
    const RaftSimSurfaceSweep::FTriangle& Ground,const FQuat& Q,const FVector& Position,
    const FVector& LinearVelocity,const FVector& W,double H,int32 SourceEdge,int32 GroundEdge)
{
    const FVector E=Q.RotateVector(SourceLocal.V[(SourceEdge+1)%3]-SourceLocal.V[SourceEdge]);
    const FVector G=Ground.V[(GroundEdge+1)%3]-Ground.V[GroundEdge];
    const double Base=E.Length()*G.Length(),Omega=W.Length(),Speed=LinearVelocity.Length();
    if(Base<=1.e-14 || H<=0. || !FMath::IsFinite(Base) || !FMath::IsFinite(H))return false;
    const FVector EW=FVector::CrossProduct(W,E),EWW=FVector::CrossProduct(W,EW);
    const FVector N=FVector::CrossProduct(E,G),N1=FVector::CrossProduct(EW,G),N2=FVector::CrossProduct(EWW,G);
    for(double Sign:{1.,-1.})
    {
        bool Clear=true;
        for(int32 I=0;I<3 && Clear;++I)for(int32 K=0;K<3 && Clear;++K)
        {
            const FVector R=Q.RotateVector(SourceLocal.V[I]);
            const FVector X=Position+R-Ground.V[K],V=LinearVelocity+FVector::CrossProduct(W,R);
            const FVector A=FVector::CrossProduct(W,FVector::CrossProduct(W,R));
            const double Radius=SourceLocal.V[I].Length();
            const double MaximumDistance=(Position-Ground.V[K]).Length()+Speed*H+Radius;
            const double J=Base*(Omega*Omega*Omega*(MaximumDistance+7.*Radius)+3.*Omega*Omega*Speed);
            const double Gap=Sign*FVector::DotProduct(N,X);
            const double Rate=Sign*(FVector::DotProduct(N1,X)+FVector::DotProduct(N,V));
            const double Acceleration=Sign*(FVector::DotProduct(N2,X)+2.*FVector::DotProduct(N1,V)+FVector::DotProduct(N,A))-J*H;
            const auto Lower=[&](double T){return Gap+Rate*T+.5*Acceleration*T*T;};
            double Minimum=FMath::Min(Gap,Lower(H));
            if(Acceleration>0.)Minimum=FMath::Min(Minimum,Lower(FMath::Clamp(-Rate/Acceleration,0.,H)));
            Clear=FMath::IsFinite(Minimum) && Minimum>1.e-9*Base;
        }
        if(Clear)return true;
    }
    return false;
}
}
