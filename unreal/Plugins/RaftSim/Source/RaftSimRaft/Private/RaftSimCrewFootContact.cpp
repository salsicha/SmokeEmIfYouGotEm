#include "RaftSimCrewAvatarActor.h"
#include "RaftSimRaftActor.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "ProceduralMeshComponent.h"

bool ARaftSimRaftActor::SampleRenderedCrewSupport(const TArray<FVector>& Points,
    TArray<double>& Floor, TArray<double>& Solid) const
{
    if (!RaftVisual || Points.IsEmpty()) return false;
    Floor.Init(-DBL_MAX, Points.Num());
    Solid.Init(-DBL_MAX, Points.Num());
    FBox Bounds(ForceInit);
    for (const FVector& P : Points) { if (P.ContainsNaN()) return false; Bounds += P; }
    const FTransform ToActor = RaftVisual->GetRelativeTransform();
    for (int32 SectionIndex : {0, 1})
    {
        const FProcMeshSection* Section = RaftVisual->GetProcMeshSection(SectionIndex);
        if (!Section) return false;
        for (int32 I = 0; I + 2 < Section->ProcIndexBuffer.Num(); I += 3)
        {
            const FVector A = ToActor.TransformPosition(FVector(Section->ProcVertexBuffer[Section->ProcIndexBuffer[I]].Position));
            const FVector B = ToActor.TransformPosition(FVector(Section->ProcVertexBuffer[Section->ProcIndexBuffer[I+1]].Position));
            const FVector C = ToActor.TransformPosition(FVector(Section->ProcVertexBuffer[Section->ProcIndexBuffer[I+2]].Position));
            if (FMath::Max3(A.X,B.X,C.X) < Bounds.Min.X || FMath::Min3(A.X,B.X,C.X) > Bounds.Max.X ||
                FMath::Max3(A.Y,B.Y,C.Y) < Bounds.Min.Y || FMath::Min3(A.Y,B.Y,C.Y) > Bounds.Max.Y) continue;
            const double D = (B.Y-C.Y)*(A.X-C.X)+(C.X-B.X)*(A.Y-C.Y);
            if (FMath::Abs(D) < 1.e-8) continue;
            for (int32 J = 0; J < Points.Num(); ++J)
            {
                const FVector& P = Points[J];
                const double U = ((B.Y-C.Y)*(P.X-C.X)+(C.X-B.X)*(P.Y-C.Y))/D;
                const double V = ((C.Y-A.Y)*(P.X-C.X)+(A.X-C.X)*(P.Y-C.Y))/D;
                const double W = 1-U-V;
                if (FMath::Min3(U,V,W) < -1.e-6) continue;
                const double Z = U*A.Z+V*B.Z+W*C.Z;
                Solid[J] = FMath::Max(Solid[J], Z);
                if (SectionIndex == 1) Floor[J] = FMath::Max(Floor[J], Z);
            }
        }
    }
    return !Solid.Contains(-DBL_MAX);
}

bool ARaftSimCrewAvatarActor::TryGetRenderedPose(ERaftSimCrewAvatarAction Action,
    float Phase, FRaftSimCrewAvatarPose& OutPose) const
{
    if (!bHasRenderedPose || Action != CurrentAction || !FMath::IsNearlyEqual(Phase, AnimationPhase)) return false;
    OutPose = LastRenderedPose;
    return true;
}

void ARaftSimCrewAvatarActor::FitFeetToRenderedRaft(FRaftSimCrewAvatarPose& Pose)
{
    // Deliver the qualified seated/rest/stroke/brace correction first.
    // High-side crosses curved tubes and still needs a separate contact solve;
    // retain its authored stance, as for airborne/rescue/reentry trajectories.
    if (CurrentAction > ERaftSimCrewAvatarAction::Brace || !HasProductionRiverBoots()) return;
    ARaftSimRaftActor* Raft = Cast<ARaftSimRaftActor>(GetAttachParentActor());
    if (!Raft) { bFootPlacementBound = false; FootPlacementRaft.Reset(); return; }
    if (FootPlacementRaft.Get() != Raft) { bFootPlacementBound = false; FootPlacementRaft = Raft; }
    const FTransform ToRaft = GetActorTransform().GetRelativeTransform(Raft->GetActorTransform());
    const auto Idle = URaftSimCrewAvatarPoseLibrary::EvaluatePose(ERaftSimCrewAvatarAction::SeatedIdle, 0, SeatSide);
    FVector Feet[2] = {Idle.LeftFootCm, Idle.RightFootCm};
    // A fourteen-centimetre ankle stance fits two separate boot footprints
    // in each half of the raft. Search both together; never cross the feet.
    Feet[0].Y += 2.0; Feet[1].Y -= 2.0;
    UStaticMeshComponent* Boots[2] = {ProductionLeftBoot, ProductionRightBoot};
    const double Inboard = SeatSide < 0 ? 1.0 : -1.0;
    const double ProfileZ = GetBodyProportionScale().Z;
    TArray<FVector> Offsets[2];
    for (int32 Foot = 0; Foot < 2; ++Foot)
    {
        const FBox Source = Boots[Foot]->GetStaticMesh()->GetBoundingBox();
        const FVector Scale = Boots[Foot]->GetRelativeScale3D();
        // Conservative full boot footprint; does not require stripped cooked
        // render buffers. Actual tread vertices are checked independently in UE.
        for (int32 X = 0; X <= 4; ++X) for (int32 Y = 0; Y <= 2; ++Y)
            Offsets[Foot].Add(FVector(FMath::Lerp(Source.Min.X,Source.Max.X,X/4.0)*Scale.X,
                FMath::Lerp(Source.Min.Y,Source.Max.Y,Y/2.0)*Scale.Y,0));
    }
    const auto Sample = [&](int32 Foot, const FVector& Local, double& Z, bool bRequireFloor) -> bool
        {
            TArray<FVector> Points;
            for (const FVector& Offset : Offsets[Foot])
            {
                const FVector Point = ToRaft.TransformPosition(Local+Offset);
                if (bRequireFloor && Point.Y*SeatSide < 1.0) return false;
                Points.Add(Point);
            }
            TArray<double> Floor, Solid;
            if (!Raft->SampleRenderedCrewSupport(Points, Floor, Solid)) return false;
            Z = -DBL_MAX;
            for (int32 J = 0; J < Points.Num(); ++J)
            {
                if (bRequireFloor && Solid[J] > Floor[J]+0.5) return false;
                Z = FMath::Max(Z, Solid[J]);
            }
            return FMath::IsFinite(Z);
        };
    bool bFound = false;
    double SupportZ[2] = {0,0};
    const uint64 GeometryRevision = Raft->GetCrewSupportGeometryRevision();
    if (bFootPlacementBound)
    {
        // Supported seated actions retain the paired stance throughout motion.
        Feet[0] = BoundFootLocalCm[0] + Pose.LeftFootCm-Idle.LeftFootCm;
        Feet[1] = BoundFootLocalCm[1] + Pose.RightFootCm-Idle.RightFootCm;
        if (GeometryRevision != 0 && CachedFootSupportRevision == GeometryRevision &&
            ToRaft.Equals(CachedFootSupportToRaft,1.e-6))
        {
            SupportZ[0] = CachedFootSupportZ[0]; SupportZ[1] = CachedFootSupportZ[1];
            bFound = true;
        }
        else bFound = Sample(0,Feet[0],SupportZ[0],false) && Sample(1,Feet[1],SupportZ[1],false);
    }
    else
    {
        const FVector Authored[2] = {Feet[0],Feet[1]};
        for (int32 Step = 0; Step <= (bGuide ? 32 : 16) && !bFound; ++Step)
                for (int32 Shift = 0; Shift <= 24 && !bFound; ++Shift)
                {
                    // The stern seat needs forward reach into the narrowing
                    // floor. Try nearest forward/aft pairs before tube support.
                    const double Along = bGuide ? ((Step+1)/2)*2*(Step%2 ? 1 : -1) : -2*Step;
                    for (int32 Foot = 0; Foot < 2; ++Foot)
                        Feet[Foot] = Authored[Foot]+FVector(Along,Inboard*Shift,0);
                    // Initial stance must fit inside the actual floor. A tube
                    // touched only by a bounding-box corner is not sole contact.
                    bFound = Sample(0,Feet[0],SupportZ[0],true) && Sample(1,Feet[1],SupportZ[1],true);
                    if (bFound)
                    {
                        const FVector Hips[2] = {Idle.LeftHipCm,Idle.RightHipCm};
                        const FVector Knees[2] = {Idle.LeftKneeCm,Idle.RightKneeCm};
                        const FVector RestFeet[2] = {Idle.LeftFootCm,Idle.RightFootCm};
                        for (int32 Foot = 0; Foot < 2; ++Foot)
                        {
                            const FVector P = ToRaft.TransformPosition(Feet[Foot]);
                            FVector Candidate = Feet[Foot];
                            Candidate.Z = ToRaft.InverseTransformPosition(FVector(P.X,P.Y,SupportZ[Foot])).Z
                                - Boots[Foot]->GetStaticMesh()->GetBoundingBox().Min.Z*ProfileZ+0.1;
                            const double Upper = FVector::Distance(Hips[Foot],Knees[Foot]);
                            const double Lower = FVector::Distance(Knees[Foot],RestFeet[Foot]);
                            const double Reach = FVector::Distance(Hips[Foot],Candidate);
                            // A supported but unreachable first candidate must
                            // not prevent finding the next feasible footprint.
                            bFound &= Reach < Upper+Lower-1.0 && Reach > FMath::Abs(Upper-Lower)+1.0;
                        }
                    }
                }
    }
    if (!bFound) return; // No invented support plane or geometry fallback.
    // Reuse only the same uploaded shape and the same relative seat. Every
    // production/review geometry upload invalidates this; moving the raft in
    // world space alone does not change its local support surface.
    CachedFootSupportRevision = GeometryRevision;
    CachedFootSupportToRaft = ToRaft;
    CachedFootSupportZ[0] = SupportZ[0]; CachedFootSupportZ[1] = SupportZ[1];
    for (int32 Foot = 0; Foot < 2; ++Foot)
    {
        const FBox Source = Boots[Foot]->GetStaticMesh()->GetBoundingBox();
        const FVector RaftPoint = ToRaft.TransformPosition(Feet[Foot]);
        const FVector SupportLocal = ToRaft.InverseTransformPosition(FVector(RaftPoint.X,RaftPoint.Y,SupportZ[Foot]));
        Feet[Foot].Z = SupportLocal.Z - Source.Min.Z*ProfileZ + 0.1;
    }
    const auto FitLeg = [](const FVector& Hip, const FVector& RestHip, const FVector& RestKnee,
        const FVector& RestFoot, const FVector& Foot, FVector& Knee)
    {
        const double Upper = FVector::Distance(RestHip,RestKnee), Lower = FVector::Distance(RestKnee,RestFoot);
        const FVector Axis = (Foot-Hip).GetSafeNormal();
        const double Distance = FVector::Distance(Hip,Foot);
        if (Distance < 1.e-4 || Distance >= Upper+Lower || Distance <= FMath::Abs(Upper-Lower)) return false;
        const double Along = (Upper*Upper-Lower*Lower+Distance*Distance)/(2*Distance);
        FVector Bend = Knee-Hip-Axis*FVector::DotProduct(Knee-Hip,Axis);
        if (Bend.Z < 0) Bend = FVector::UpVector-Axis*Axis.Z;
        Bend = Bend.GetSafeNormal();
        if (Bend.IsNearlyZero()) return false;
        Knee = Hip+Along*Axis+FMath::Sqrt(FMath::Max(0.0,Upper*Upper-Along*Along))*Bend;
        return true;
    };
    FVector LeftKnee = Pose.LeftKneeCm, RightKnee = Pose.RightKneeCm;
    if (!FitLeg(Pose.LeftHipCm,Idle.LeftHipCm,Idle.LeftKneeCm,Idle.LeftFootCm,Feet[0],LeftKnee) ||
        !FitLeg(Pose.RightHipCm,Idle.RightHipCm,Idle.RightKneeCm,Idle.RightFootCm,Feet[1],RightKnee)) return;
    if (!bFootPlacementBound)
    {
        BoundFootLocalCm[0] = Feet[0]; BoundFootLocalCm[1] = Feet[1]; bFootPlacementBound = true;
        UE_LOG(LogTemp,Display,TEXT("CREW_FOOT_BIND actor=%s left=%s right=%s"),
            *GetName(),*Feet[0].ToString(),*Feet[1].ToString());
    }
    Pose.LeftFootCm = Feet[0]; Pose.RightFootCm = Feet[1];
    Pose.LeftKneeCm = LeftKnee; Pose.RightKneeCm = RightKnee;
    Pose.bFeetPlanted = true;
}
