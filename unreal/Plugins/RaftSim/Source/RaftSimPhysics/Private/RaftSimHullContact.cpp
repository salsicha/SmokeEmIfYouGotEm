#include "RaftSimHullContact.h"

namespace RaftSimHullContact
{
namespace
{
constexpr double SkinM=1.e-5,RoundoffM=1.e-9,ClosingTolerance=1.e-9;
double Energy(const FRaftSimFlexRigidState& S,double Mass,const FVector& I)
{return .5*(Mass*S.LinearVelocity.SizeSquared()+I.X*S.AngularVelocity.X*S.AngularVelocity.X+
    I.Y*S.AngularVelocity.Y*S.AngularVelocity.Y+I.Z*S.AngularVelocity.Z*S.AngularVelocity.Z);}
bool Finite(const FRaftSimFlexRigidState& S)
{return !S.Position.ContainsNaN() && !S.Orientation.ContainsNaN() &&
    FMath::Abs(S.Orientation.SizeSquared()-1.)<1.e-6 &&
    !S.LinearVelocity.ContainsNaN() && !S.AngularVelocity.ContainsNaN();}
}

FRaftSimHullContactResult Integrate(FRaftSimFlexRigidState& State,
    const FRaftSimFlexRigidState& Previous,const FRaftSimHullGeometry& Before,
    const FRaftSimHullGeometry& After,double Mass,const FVector& Inertia,double Dt,
    const FRaftSimHullGroundQuery& Query)
{
    using namespace RaftSimSurfaceSweep;
    FRaftSimHullContactResult Result;
    if(!Query || !Before.IsValid() || !After.IsValid() || Before.Faces!=After.Faces ||
        Before.VerticesM.Num()!=After.VerticesM.Num() || !FMath::IsFinite(Dt) || Dt<=1.e-12 ||
        !FMath::IsFinite(Mass) || Mass<=0. || Inertia.ContainsNaN() || Inertia.GetMin()<=0. ||
        !Finite(State) || !Finite(Previous))
    {Result.Failure=TEXT("invalid full-hull input or changed topology");return Result;}
    auto Current=State;Current.Position=Previous.Position;Current.Orientation=Previous.Orientation;
    const double InitialEnergy=Energy(Current,Mass,Inertia);
    double Radius=0.,ShapeSpeed=0.;
    for(int32 I=0;I<Before.VerticesM.Num();++I)
    {
        Radius=FMath::Max(Radius,FMath::Max(Before.VerticesM[I].Length(),After.VerticesM[I].Length()));
        ShapeSpeed=FMath::Max(ShapeSpeed,(After.VerticesM[I]-Before.VerticesM[I]).Length()/Dt);
    }
    const auto Local=[&](int32 I,double T){return FMath::Lerp(Before.VerticesM[I],After.VerticesM[I],FMath::Clamp(T/Dt,0.,1.));};
    struct FContact{FVector Before,After,Normal,Ground;};
    TArray<FContact,TInlineAllocator<32>> Contacts;
    TArray<FVector> StartCm,EndCm;StartCm.SetNumUninitialized(Before.VerticesM.Num());EndCm.SetNumUninitialized(StartCm.Num());
    const auto ContactLocal=[&](const FContact& C,double T){return FMath::Lerp(C.Before,C.After,FMath::Clamp(T/Dt,0.,1.));};
    const auto Apply=[&](const FVector& P,const FVector& Normal,const FVector& DeformationVelocity)
    {
        const FVector R=Current.Orientation.RotateVector(P);
        const double V=FVector::DotProduct(Current.PointVelocity(P),Normal);
        const double U=FVector::DotProduct(DeformationVelocity,Normal);
        if(V+U>=-ClosingTolerance)return false;
        const FVector Cross=FVector::CrossProduct(R,Normal);
        const FVector InvCross(Cross.X/Inertia.X,Cross.Y/Inertia.Y,Cross.Z/Inertia.Z);
        const double InvMass=1./Mass+FVector::DotProduct(Cross,InvCross);
        const double J=-(V+U)/InvMass;
        Current.LinearVelocity+=Normal*(J/Mass);Current.AngularVelocity+=InvCross*J;
        Result.PrescribedShapeWorkJ-=J*U;Result.DissipatedJ+=.5*J*J*InvMass;
        ++Result.Impulses;return true;
    };
    double Remaining=Dt,MaximumInterval=Dt;
    for(int32 Event=0;Event<512 && Remaining>1.e-12;++Event)
    {
        const double Omega=Current.AngularVelocity.Length();
        // For R(t)(a+t*b), |x''| <= omega^2*max|x|+2*omega*|b|.
        // A twice differentiable curve lies within max|x''|*h^2/8 of its chord.
        const double Curvature=Omega*Omega*Radius+2.*Omega*ShapeSpeed;
        const double Segment=FMath::Min(MaximumInterval,Curvature>0.?FMath::Min(Remaining,FMath::Sqrt(SkinM/Curvature)):Remaining);
        const double CurveBound=Curvature*Segment*Segment/8.;
        Result.MaximumCurveBoundM=FMath::Max(Result.MaximumCurveBoundM,CurveBound);
        const double Clearance=CurveBound+RoundoffM;
        const double Now=Result.ConsumedSeconds,Later=Now+Segment;
        auto Predicted=Current;RaftSimSweptGround::Advance(Predicted,Segment);
        for(int32 I=0;I<StartCm.Num();++I)
        {StartCm[I]=Current.WorldPoint(Local(I,Now))*100.;EndCm[I]=Predicted.WorldPoint(Local(I,Later))*100.;}
        const auto Hit=Query(StartCm,EndCm,Before.Faces,(SkinM+CurveBound)*100.,Clearance*100.);
        ++Result.Queries;Result.TrianglePairs+=Hit.TrianglePairs;
        if(Hit.Status==EStatus::Clear)
        {Current=Predicted;Remaining-=Segment;Result.ConsumedSeconds+=Segment;MaximumInterval=Dt;continue;}
        Result.MovingFace=Hit.MovingFace;Result.GroundFace=Hit.GroundFace;
        if(Hit.Status==EStatus::Unresolved && Segment>1.e-10)
        {MaximumInterval=Segment*.5;continue;}
        if(Hit.Status!=EStatus::Contact || !FMath::IsFinite(Hit.Time) || Hit.Time<0. || Hit.Time>1. ||
            !Before.Faces.IsValidIndex(Hit.MovingFace) || Hit.Normal.ContainsNaN() || Hit.Normal.IsNearlyZero() ||
            Hit.Witness.MovingBary.ContainsNaN() || Hit.Witness.MovingBary.GetMin()<0. ||
            FMath::Abs(Hit.Witness.MovingBary.X+Hit.Witness.MovingBary.Y+Hit.Witness.MovingBary.Z-1.)>1.e-8 ||
            Hit.Witness.GroundPoint.ContainsNaN())
        {Result.Failure=FString::Printf(TEXT("surface query refused status=%d moving_face=%d ground_face=%d"),int32(Hit.Status),Hit.MovingFace,Hit.GroundFace);return Result;}
        const double Advance=Segment*Hit.Time;
        RaftSimSweptGround::Advance(Current,Advance);Remaining-=Advance;Result.ConsumedSeconds+=Advance;
        if(Advance>1.e-12)MaximumInterval=Dt;
        const auto Face=Before.Faces[Hit.MovingFace];const auto B=Hit.Witness.MovingBary;
        FContact Fresh;Fresh.Before=Before.VerticesM[Face.X]*B.X+Before.VerticesM[Face.Y]*B.Y+Before.VerticesM[Face.Z]*B.Z;
        Fresh.After=After.VerticesM[Face.X]*B.X+After.VerticesM[Face.Y]*B.Y+After.VerticesM[Face.Z]*B.Z;
        Fresh.Normal=Hit.Normal/Hit.Normal.Length();Fresh.Ground=Hit.Witness.GroundPoint;
        Contacts.RemoveAll([&](const FContact& C){return FVector::DotProduct(Current.WorldPoint(ContactLocal(C,Result.ConsumedSeconds))-C.Ground,C.Normal)>4.*SkinM;});
        if(auto* Existing=Contacts.FindByPredicate([&](const FContact& C)
            {return (C.Before-Fresh.Before).Length()<1.e-7 && (C.After-Fresh.After).Length()<1.e-7 && FVector::DotProduct(C.Normal,Fresh.Normal)>1.-1.e-10;}))
            *Existing=Fresh;
        else Contacts.Add(Fresh);
        if(Contacts.Num()>128){Result.Failure=TEXT("full-hull manifold capacity exceeded");return Result;}
        const int32 BeforeImpulses=Result.Impulses;bool Resolved=false;
        const auto FutureConstraint=[&](const FContact& C,FVector& P,FVector& D)
        {
            auto Future=Current;const double H=FMath::Min(Remaining,Segment);RaftSimSweptGround::Advance(Future,H);
            const FVector FutureLocal=ContactLocal(C,Result.ConsumedSeconds+H);
            P=Current.Orientation.UnrotateVector(Future.Orientation.RotateVector(FutureLocal));
            D=Future.Orientation.RotateVector((C.After-C.Before)/Dt);
            return FVector::DotProduct(Future.WorldPoint(FutureLocal)-C.Ground,C.Normal)<Clearance;
        };
        for(int32 Pass=0;Pass<128;++Pass)
        {
            for(const auto& C:Contacts)
            {
                Apply(ContactLocal(C,Result.ConsumedSeconds),C.Normal,Current.Orientation.RotateVector((C.After-C.Before)/Dt));
                FVector P,D;if(FutureConstraint(C,P,D))Apply(P,C.Normal,D);
            }
            Resolved=true;
            for(const auto& C:Contacts)
            {
                const FVector P=ContactLocal(C,Result.ConsumedSeconds),D=Current.Orientation.RotateVector((C.After-C.Before)/Dt);
                Resolved &= FVector::DotProduct(Current.PointVelocity(P)+D,C.Normal)>=-ClosingTolerance;
                FVector FP,FD;if(FutureConstraint(C,FP,FD))Resolved &= FVector::DotProduct(Current.PointVelocity(FP)+FD,C.Normal)>=-ClosingTolerance;
            }
            if(Resolved)break;
        }
        if(!Resolved){Result.Failure=TEXT("full-hull manifold velocity solve did not converge");return Result;}
        if(Result.Impulses==BeforeImpulses && Advance<=1.e-12)
        {
            // A neutral witness can coexist with a different feature entering
            // later in this interval. Refine the proven curved-path enclosure,
            // then query ALL faces again. Neither elapsed time nor physical
            // skin is discarded/reduced; only a proven-clear interval advances.
            if(Segment>1.e-10){MaximumInterval=Segment*.5;continue;}
            Result.Failure=TEXT("zero-time full-hull contact cannot advance after interval refinement");return Result;
        }
        if(!Finite(Current)){Result.Failure=TEXT("nonfinite full-hull response");return Result;}
    }
    if(Remaining>1.e-12){Result.Failure=TEXT("full-hull event limit; unconsumed substep");return Result;}
    Result.KineticChangeJ=Energy(Current,Mass,Inertia)-InitialEnergy;
    if(!Finite(Current) || !FMath::IsFinite(Result.KineticChangeJ) ||
        FMath::Abs(Result.KineticChangeJ-Result.PrescribedShapeWorkJ+Result.DissipatedJ)>
            1.e-8+1.e-12*FMath::Max(InitialEnergy,FMath::Abs(Result.PrescribedShapeWorkJ)+Result.DissipatedJ))
    {Result.Failure=TEXT("full-hull impulse work balance failed");return Result;}
    // Preserve the existing force-integrated pose bit-for-bit for one clear
    // interval. No-contact segmented rotation follows its bounded exact arcs.
    if(Result.Impulses || Result.Queries>1)State=Current;
    Result.bCompleted=true;return Result;
}
}
