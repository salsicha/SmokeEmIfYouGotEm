#include "RaftSimHullContact.h"
#include "RaftSimHullShapeEnclosure.h"
#include "RaftSimContactWitnessPrune.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/ScopeExit.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "ProfilingDebugging/CsvProfiler.h"

CSV_DEFINE_CATEGORY(RaftSimContact,true);

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
    const FRaftSimHullGroundQuery& Query,const FRaftSimHullGroundArcQuery& ArcQuery,bool bProbeClearFlight)
{
    CSV_SCOPED_TIMING_STAT(RaftSimContact,Integrate);
    using namespace RaftSimSurfaceSweep;
    FRaftSimHullContactResult Result;
    {
        CSV_SCOPED_TIMING_STAT(RaftSimContact,ValidateOriginalHull);
        if(!Query || !Before.IsValid() || !After.IsValid() || Before.Faces!=After.Faces ||
            Before.VerticesM.Num()!=After.VerticesM.Num() || !FMath::IsFinite(Dt) || Dt<=1.e-12 ||
            !FMath::IsFinite(Mass) || Mass<=0. || Inertia.ContainsNaN() || Inertia.GetMin()<=0. ||
            !Finite(State) || !Finite(Previous))
        {Result.Failure=TEXT("invalid full-hull input or changed topology");return Result;}
    }
    auto Current=State;Current.Position=Previous.Position;Current.Orientation=Previous.Orientation;
    // Opt-in native failure evidence. Does not change integration, limits or
    // acceptance. Preserve the first failure so it can be replayed exactly.
    FString FailurePath;
#if !UE_BUILD_SHIPPING
    FParse::Value(FCommandLine::Get(),TEXT("RaftSimHullFailurePath="),FailurePath);
#endif
    TArray<TSharedPtr<FJsonValue>> FailureEvents;
    ON_SCOPE_EXIT
    {
        if(Result.bCompleted || FailurePath.IsEmpty() || IFileManager::Get().FileExists(*FailurePath))return;
        const auto Vec=[](const FVector& V){return MakeShared<FJsonValueArray>(TArray<TSharedPtr<FJsonValue>>{
            MakeShared<FJsonValueNumber>(V.X),MakeShared<FJsonValueNumber>(V.Y),MakeShared<FJsonValueNumber>(V.Z)});};
        const auto Body=[&](const FRaftSimFlexRigidState& S)
        {auto J=MakeShared<FJsonObject>();J->SetField(TEXT("position"),Vec(S.Position));J->SetField(TEXT("velocity"),Vec(S.LinearVelocity));
         J->SetField(TEXT("omega"),Vec(S.AngularVelocity));const auto Q=S.Orientation;
         J->SetArrayField(TEXT("quaternion"),{MakeShared<FJsonValueNumber>(Q.X),MakeShared<FJsonValueNumber>(Q.Y),MakeShared<FJsonValueNumber>(Q.Z),MakeShared<FJsonValueNumber>(Q.W)});return J;};
        auto J=MakeShared<FJsonObject>();J->SetStringField(TEXT("schema"),TEXT("raftsim.full_hull_native_failure.v1"));
        J->SetStringField(TEXT("failure"),Result.Failure);J->SetNumberField(TEXT("mass_kg"),Mass);J->SetField(TEXT("inertia"),Vec(Inertia));J->SetNumberField(TEXT("dt"),Dt);
        J->SetObjectField(TEXT("previous"),Body(Previous));J->SetObjectField(TEXT("predicted"),Body(State));J->SetObjectField(TEXT("last_contact_state"),Body(Current));
        TArray<TSharedPtr<FJsonValue>> A,B,F;
        for(const auto& V:Before.VerticesM)A.Add(Vec(V));for(const auto& V:After.VerticesM)B.Add(Vec(V));
        for(const auto& Face:Before.Faces)F.Add(Vec(FVector(Face)));
        J->SetArrayField(TEXT("before_vertices"),A);J->SetArrayField(TEXT("after_vertices"),B);J->SetArrayField(TEXT("faces"),F);J->SetArrayField(TEXT("events"),FailureEvents);
        J->SetNumberField(TEXT("consumed_seconds"),Result.ConsumedSeconds);J->SetNumberField(TEXT("impulses"),Result.Impulses);
        FString Json;FJsonSerializer::Serialize(J,TJsonWriterFactory<>::Create(&Json));
        if(!FFileHelper::SaveStringToFile(Json,*FailurePath))UE_LOG(LogTemp,Warning,TEXT("Native full-hull failure snapshot could not be saved: %s"),*FailurePath);
    };
    const double InitialEnergy=Energy(Current,Mass,Inertia);
    double Radius=0.,ShapeSpeed=0.;
    {
        CSV_SCOPED_TIMING_STAT(RaftSimContact,ShapeEnclosure);
        MeasureShapeEnclosure(Before,After,Dt,Radius,ShapeSpeed);
    }
    const auto Local=[&](int32 I,double T){return FMath::Lerp(Before.VerticesM[I],After.VerticesM[I],FMath::Clamp(T/Dt,0.,1.));};
    using FContact=RaftSimContactWitnessPrune::FWitness;
    bool CompactCandidate=false;
#if !UE_BUILD_SHIPPING
    static const bool Compact=FParse::Param(FCommandLine::Get(),TEXT("RaftSimFlipCompactContactCandidate"));
    CompactCandidate=Compact;
#endif
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
    if(ArcQuery && bProbeClearFlight)
    {
        // Clear-only acceleration: enclose the ENTIRE curved/deforming path.
        // A contact or unresolved result is not integrated here; the unchanged
        // small-interval contact loop below owns all impulses and refusals.
        const double W=Current.AngularVelocity.Length();
        const double Bound=(W*W*Radius+2.*W*ShapeSpeed)*Dt*Dt/8.;
        auto End=Current;RaftSimSweptGround::Advance(End,Dt);
        {
            CSV_SCOPED_TIMING_STAT(RaftSimContact,EndpointTransforms);
            for(int32 I=0;I<StartCm.Num();++I)
            {StartCm[I]=Current.WorldPoint(Before.VerticesM[I])*100.;EndCm[I]=End.WorldPoint(After.VerticesM[I])*100.;}
        }
        FRaftSimHullArcPath Path{Current,&Before,&After,0.,Dt,Dt,W*W*W*Radius+3.*W*W*ShapeSpeed};
        const auto Flight=ArcQuery(StartCm,EndCm,Before.Faces,(SkinM+Bound)*100.,(Bound+RoundoffM)*100.,Path);
        ++Result.Queries;Result.TrianglePairs+=Flight.TrianglePairs;
        if(Flight.Status==EStatus::Clear)
        {Current=End;Result.ConsumedSeconds=Dt;Result.MaximumCurveBoundM=Bound;Remaining=0.;}
    }
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
        {
            CSV_SCOPED_TIMING_STAT(RaftSimContact,EndpointTransforms);
            for(int32 I=0;I<StartCm.Num();++I)
            {StartCm[I]=Current.WorldPoint(Local(I,Now))*100.;EndCm[I]=Predicted.WorldPoint(Local(I,Later))*100.;}
        }
        FRaftSimHullArcPath Path{Current,&Before,&After,Now,Segment,Dt,
            Omega*Omega*Omega*Radius+3.*Omega*Omega*ShapeSpeed};
        const auto Hit=ArcQuery ? ArcQuery(StartCm,EndCm,Before.Faces,(SkinM+CurveBound)*100.,Clearance*100.,Path)
            : Query(StartCm,EndCm,Before.Faces,(SkinM+CurveBound)*100.,Clearance*100.);
        if(!FailurePath.IsEmpty())
        {auto J=MakeShared<FJsonObject>();J->SetNumberField(TEXT("event"),Event);J->SetNumberField(TEXT("now"),Now);
         J->SetNumberField(TEXT("remaining"),Remaining);J->SetNumberField(TEXT("segment"),Segment);J->SetNumberField(TEXT("shape_speed"),ShapeSpeed);
         J->SetNumberField(TEXT("omega"),Omega);J->SetNumberField(TEXT("clearance"),Clearance);J->SetNumberField(TEXT("hit_time"),Hit.Time);
         J->SetNumberField(TEXT("status"),int32(Hit.Status));J->SetNumberField(TEXT("face"),Hit.MovingFace);J->SetNumberField(TEXT("ground_face"),Hit.GroundFace);
         J->SetNumberField(TEXT("impulses"),Result.Impulses);J->SetNumberField(TEXT("contacts"),Contacts.Num());
         FailureEvents.Add(MakeShared<FJsonValueObject>(J));}
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
        Fresh.MovingFace=Hit.MovingFace;
        if(ArcQuery && B.GetMin()>1.e-10)
        {
            const FVector A=Current.WorldPoint(Local(Face.X,Result.ConsumedSeconds));
            const FVector U=Current.WorldPoint(Local(Face.Y,Result.ConsumedSeconds))-A;
            const FVector V=Current.WorldPoint(Local(Face.Z,Result.ConsumedSeconds))-A;
            const double Align=FVector::DotProduct(FVector::CrossProduct(U,V).GetSafeNormal(),Fresh.Normal);
            Fresh.bRotatingSourceFace=FMath::Abs(Align)>1.-1.e-8;Fresh.bReverseFaceNormal=Align<0.;
        }
        if(ArcQuery && !Fresh.bRotatingSourceFace && Hit.bHasGroundFeature && Hit.GroundFeatureA!=Hit.GroundFeatureB)
        {
            int32 Positive=0,Missing=INDEX_NONE;
            for(int32 I=0;I<3;++I){if(B[I]>1.e-10)++Positive;else Missing=I;}
            if(Positive==2)
            {
                const FVector U=Current.WorldPoint(Local(Face[(Missing+2)%3],Result.ConsumedSeconds))
                    -Current.WorldPoint(Local(Face[(Missing+1)%3],Result.ConsumedSeconds));
                const FVector N=FVector::CrossProduct(U,Hit.GroundFeatureB-Hit.GroundFeatureA).GetSafeNormal();
                if(!N.IsNearlyZero())
                {
                    Fresh.bMovingEdge=true;Fresh.MissingCorner=Missing;
                    Fresh.GroundFeatureA=Hit.GroundFeatureA;Fresh.GroundFeatureB=Hit.GroundFeatureB;
                    Fresh.bReverseFaceNormal=FVector::DotProduct(N,Fresh.Normal)<0.;
                }
            }
        }
        Contacts.RemoveAll([&](const FContact& C){return FVector::DotProduct(Current.WorldPoint(ContactLocal(C,Result.ConsumedSeconds))-C.Ground,C.Normal)>4.*SkinM;});
        if(auto* Existing=Contacts.FindByPredicate([&](const FContact& C)
            {return (Fresh.bRotatingSourceFace && C.bRotatingSourceFace && C.MovingFace==Fresh.MovingFace
                && C.bReverseFaceNormal==Fresh.bReverseFaceNormal && C.Ground.Equals(Fresh.Ground,1.e-12))
                || (Fresh.bMovingEdge && C.bMovingEdge && Fresh.MovingFace==C.MovingFace && Fresh.MissingCorner==C.MissingCorner
                    && Fresh.GroundFeatureA==C.GroundFeatureA && Fresh.GroundFeatureB==C.GroundFeatureB
                    && Fresh.bReverseFaceNormal==C.bReverseFaceNormal)
                || ((C.Before-Fresh.Before).Length()<1.e-7 && (C.After-Fresh.After).Length()<1.e-7 && FVector::DotProduct(C.Normal,Fresh.Normal)>1.-1.e-10);}))
            *Existing=Fresh;
        else
        {
            // Error is below the solver's normal-velocity roundoff budget,
            // including endpoint interpolation and deformation velocity.
            const double Eps=FMath::Min(1.e-12,ClosingTolerance/(64.*(1.+Omega+2./Dt)));
            if(!CompactCandidate || !RaftSimContactWitnessPrune::Redundant(Fresh,Contacts,INDEX_NONE,Eps))Contacts.Add(Fresh);
            if(CompactCandidate)
                for(int32 I=Contacts.Num()-1;I>=0;--I)
                    if(RaftSimContactWitnessPrune::Redundant(Contacts[I],Contacts,I,Eps))Contacts.RemoveAt(I);
        }
        if(Contacts.Num()>128){Result.Failure=TEXT("full-hull manifold capacity exceeded");return Result;}
        const int32 BeforeImpulses=Result.Impulses;bool Resolved=false;
        const auto SourceSupport=[&](const FContact& C,const FRaftSimFlexRigidState& Body,double Time,
            FVector& Point,FVector& ShapeVelocity,FVector& Normal,double& Gap)
        {
            const auto Face=Before.Faces[C.MovingFace];FTriangle Triangle;
            for(int32 I=0;I<3;++I)Triangle.V[I]=Body.WorldPoint(Local(Face[I],Time));
            if(C.bMovingEdge)
            {
                const int32 I=(C.MissingCorner+1)%3,J=(C.MissingCorner+2)%3;
                const FTriangle MovingEdge{{Triangle.V[I],Triangle.V[J],Triangle.V[J]}};
                const FTriangle GroundEdge{{C.GroundFeatureA,C.GroundFeatureB,C.GroundFeatureB}};
                const auto Support=Distance(MovingEdge,GroundEdge);
                const double MovingT=Support.MovingBary.Y+Support.MovingBary.Z,GroundT=Support.GroundBary.Y+Support.GroundBary.Z;
                if(MovingT<=1.e-10 || MovingT>=1.-1.e-10 || GroundT<=1.e-10 || GroundT>=1.-1.e-10)return false;
                Normal=FVector::CrossProduct(Triangle.V[J]-Triangle.V[I],C.GroundFeatureB-C.GroundFeatureA).GetSafeNormal();
                if(C.bReverseFaceNormal)Normal=-Normal;if(Normal.IsNearlyZero())return false;
                Point=Support.MovingPoint-Body.Position;
                const FVector Shape=(After.VerticesM[Face[I]]-Before.VerticesM[Face[I]])*(1.-MovingT)
                    +(After.VerticesM[Face[J]]-Before.VerticesM[Face[J]])*MovingT;
                ShapeVelocity=Body.Orientation.RotateVector(Shape/Dt);Gap=FVector::DotProduct(Support.MovingPoint-Support.GroundPoint,Normal);
                return true;
            }
            const FTriangle GroundPoint{{C.Ground,C.Ground,C.Ground}};
            const auto Support=Distance(Triangle,GroundPoint);const auto Bary=Support.MovingBary;
            if(Bary.GetMin()<=1.e-10)return false;
            Normal=FVector::CrossProduct(Triangle.V[1]-Triangle.V[0],Triangle.V[2]-Triangle.V[0]).GetSafeNormal();
            if(C.bReverseFaceNormal)Normal=-Normal;if(Normal.IsNearlyZero())return false;
            Point=Support.MovingPoint-Body.Position;
            const FVector Shape=(After.VerticesM[Face.X]-Before.VerticesM[Face.X])*Bary.X
                +(After.VerticesM[Face.Y]-Before.VerticesM[Face.Y])*Bary.Y
                +(After.VerticesM[Face.Z]-Before.VerticesM[Face.Z])*Bary.Z;
            ShapeVelocity=Body.Orientation.RotateVector(Shape/Dt);Gap=FVector::DotProduct(Support.MovingPoint-C.Ground,Normal);
            return true;
        };
        // An interior source-face constraint expires at its edge; the next
        // full-triangle query owns that edge/vertex transition, not a ghost face.
        Contacts.RemoveAll([&](const FContact& C)
        {FVector P,D,N;double G;return (C.bRotatingSourceFace || C.bMovingEdge) && (!SourceSupport(C,Current,Result.ConsumedSeconds,P,D,N,G) || G>4.*SkinM);});
        const auto PresentConstraint=[&](const FContact& C,FVector& P,FVector& D,FVector& N)
        {
            P=ContactLocal(C,Result.ConsumedSeconds);D=Current.Orientation.RotateVector((C.After-C.Before)/Dt);N=C.Normal;
            if(C.bRotatingSourceFace || C.bMovingEdge)
            {FVector WorldPoint;double Gap;SourceSupport(C,Current,Result.ConsumedSeconds,WorldPoint,D,N,Gap);P=Current.Orientation.UnrotateVector(WorldPoint);}
        };
        const auto FutureConstraint=[&](const FContact& C,FVector& P,FVector& D,FVector& N)
        {
            auto Future=Current;const double H=FMath::Min(Remaining,Segment);RaftSimSweptGround::Advance(Future,H);
            const FVector FutureLocal=ContactLocal(C,Result.ConsumedSeconds+H);
            P=Current.Orientation.UnrotateVector(Future.Orientation.RotateVector(FutureLocal));
            D=Future.Orientation.RotateVector((C.After-C.Before)/Dt);N=C.Normal;
            if(C.bRotatingSourceFace || C.bMovingEdge)
            {
                // A static ground corner supported by a rotating source FACE
                // does not keep the same hull barycentric coordinate. Predict
                // the real source triangle and reproject that ground witness.
                // Using yesterday's hull point here creates Zeno-like repeats.
                FVector WorldPoint;double Gap;
                if(!SourceSupport(C,Future,Result.ConsumedSeconds+H,WorldPoint,D,N,Gap))return false;
                P=Current.Orientation.UnrotateVector(WorldPoint);return Gap<Clearance;
            }
            return FVector::DotProduct(Future.WorldPoint(FutureLocal)-C.Ground,C.Normal)<Clearance;
        };
        for(int32 Pass=0;Pass<128;++Pass)
        {
            for(const auto& C:Contacts)
            {
                FVector CP,CD,CN;PresentConstraint(C,CP,CD,CN);Apply(CP,CN,CD);
                FVector P,D,N;if(FutureConstraint(C,P,D,N))Apply(P,N,D);
            }
            Resolved=true;
            for(const auto& C:Contacts)
            {
                FVector P,D,N;PresentConstraint(C,P,D,N);
                Resolved &= FVector::DotProduct(Current.PointVelocity(P)+D,N)>=-ClosingTolerance;
                FVector FP,FD,FN;if(FutureConstraint(C,FP,FD,FN))Resolved &= FVector::DotProduct(Current.PointVelocity(FP)+FD,FN)>=-ClosingTolerance;
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
