#pragma once
#include "RaftSimFlexibleRaftModel.h"

// Linearized implicit integration of the SAME six-point drag law. Freeze its
// speed-dependent coefficient over one step, not the relative velocity.
// Coupled translation/rotation preserves the point-force lever arms; the
// symmetric positive semidefinite resistance cannot amplify still-water
// kinetic energy. No orientation target or artificial capsize torque.
namespace RaftSimImplicitDrag
{
struct FSystem
{
    double K[6][6]={},B[6]={};
    void AddPoint(const FVector& R,const FVector& Water,double Blunt,
        double ForwardCorrection,const FVector& Forward)
    {
        const FVector Axes[3]={FVector(1,0,0),FVector(0,1,0),FVector(0,0,1)};
        FVector J[6];
        for(int32 I=0;I<3;++I){J[I]=Axes[I];J[I+3]=FVector::CrossProduct(Axes[I],R);}
        const auto Resistance=[&](const FVector& V)
            {return Blunt*V+ForwardCorrection*Forward*FVector::DotProduct(Forward,V);};
        for(int32 I=0;I<6;++I)
        {
            B[I]+=FVector::DotProduct(J[I],Resistance(Water));
            for(int32 L=0;L<6;++L)K[I][L]+=FVector::DotProduct(J[I],Resistance(J[L]));
        }
    }
    bool Advance(FRaftSimFlexRigidState& State,double Mass,const FVector& Inertia,
        const FVector& Force,const FVector& Torque,double Dt,FVector& DragForce,FVector& DragTorque) const
    {
        const double M[6]={Mass,Mass,Mass,Inertia.X,Inertia.Y,Inertia.Z};
        const double V[6]={State.LinearVelocity.X,State.LinearVelocity.Y,State.LinearVelocity.Z,
            State.AngularVelocity.X,State.AngularVelocity.Y,State.AngularVelocity.Z};
        const double F[6]={Force.X,Force.Y,Force.Z,Torque.X,Torque.Y,Torque.Z};
        double L[6][6]={},Rhs[6],Y[6],Next[6];
        if(!FMath::IsFinite(Dt) || Dt<=0.)return false;
        for(int32 I=0;I<6;++I)
        {
            if(!FMath::IsFinite(M[I]) || M[I]<=0.)return false;
            Rhs[I]=M[I]*V[I]+Dt*(F[I]+B[I]);
            for(int32 J=0;J<=I;++J)
            {
                double Sum=Dt*K[I][J]+(I==J ? M[I] : 0.);
                for(int32 N=0;N<J;++N)Sum-=L[I][N]*L[J][N];
                if(!FMath::IsFinite(Sum) || (I==J && Sum<=0.))return false;
                L[I][J]=I==J ? FMath::Sqrt(Sum) : Sum/L[J][J];
            }
            double Sum=Rhs[I];for(int32 J=0;J<I;++J)Sum-=L[I][J]*Y[J];Y[I]=Sum/L[I][I];
        }
        for(int32 I=5;I>=0;--I)
        {double Sum=Y[I];for(int32 J=I+1;J<6;++J)Sum-=L[J][I]*Next[J];Next[I]=Sum/L[I][I];if(!FMath::IsFinite(Next[I]))return false;}
        double Drag[6];
        for(int32 I=0;I<6;++I)
        {Drag[I]=B[I];for(int32 J=0;J<6;++J)Drag[I]-=K[I][J]*Next[J];}
        State.LinearVelocity=FVector(Next[0],Next[1],Next[2]);State.AngularVelocity=FVector(Next[3],Next[4],Next[5]);
        DragForce=FVector(Drag[0],Drag[1],Drag[2]);DragTorque=FVector(Drag[3],Drag[4],Drag[5]);return true;
    }
};
}
