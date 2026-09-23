#include "RaftSimCrewAvatarActor.h"
#include "RaftSimRaftActor.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "ProceduralMeshComponent.h"
#include "ProfilingDebugging/CsvProfiler.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

CSV_DEFINE_CATEGORY(RaftSimCrewContact,true);

bool ARaftSimRaftActor::SampleRenderedCrewSupport(const TArray<FVector>& Points,
    TArray<double>& Floor, TArray<double>& Solid, bool bForceReference) const
{
    CSV_SCOPED_TIMING_STAT(RaftSimCrewContact,SupportQuery);
    CSV_CUSTOM_STAT(RaftSimCrewContact,SupportQueries,1,ECsvCustomStatOp::Accumulate);
    if (!RaftVisual || Points.IsEmpty()) return false;
    Floor.Init(-DBL_MAX, Points.Num());
    Solid.Init(-DBL_MAX, Points.Num());
    FBox Bounds(ForceInit);
    for (const FVector& P : Points) { if (P.ContainsNaN()) return false; Bounds += P; }
    const FTransform ToActor = RaftVisual->GetRelativeTransform();
    static const bool bIndexedReview=FParse::Param(FCommandLine::Get(),TEXT("RaftSimReviewHighSideContact"));
    if(bIndexedReview && !bForceReference)
    {
        const auto Bin=[](const FVector& P){return FIntPoint(FMath::FloorToInt(P.X/20.),FMath::FloorToInt(P.Y/20.));};
        if(CrewSupportIndexRevision!=CrewSupportGeometryRevision || !CrewSupportIndexTransform.Equals(ToActor,1.e-6))
        {
            CrewSupportTriangles.Reset();CrewSupportBins.Reset();
            for(int32 SectionIndex:{0,1})
            {
                const FProcMeshSection* Section=RaftVisual->GetProcMeshSection(SectionIndex);
                if(!Section)return false;
                for(int32 I=0;I+2<Section->ProcIndexBuffer.Num();I+=3)
                {
                    FCrewSupportTriangle T;
                    T.A=ToActor.TransformPosition(FVector(Section->ProcVertexBuffer[Section->ProcIndexBuffer[I]].Position));
                    T.B=ToActor.TransformPosition(FVector(Section->ProcVertexBuffer[Section->ProcIndexBuffer[I+1]].Position));
                    T.C=ToActor.TransformPosition(FVector(Section->ProcVertexBuffer[Section->ProcIndexBuffer[I+2]].Position));
                    T.Determinant=(T.B.Y-T.C.Y)*(T.A.X-T.C.X)+(T.C.X-T.B.X)*(T.A.Y-T.C.Y);
                    T.bFloor=SectionIndex==1;
                    if(FMath::Abs(T.Determinant)<1.e-8)continue;
                    const int32 Index=CrewSupportTriangles.Add(T);
                    FBox TriangleBounds(ForceInit);TriangleBounds+=T.A;TriangleBounds+=T.B;TriangleBounds+=T.C;
                    // Cover the same small negative-barycentric tolerance as
                    // the reference scanner, including bin-edge queries.
                    const double Margin=FMath::Max(0.001,TriangleBounds.GetSize().GetMax()*1.e-5);
                    const FIntPoint Minimum=Bin(TriangleBounds.Min-FVector(Margin));
                    const FIntPoint Maximum=Bin(TriangleBounds.Max+FVector(Margin));
                    for(int32 X=Minimum.X;X<=Maximum.X;++X)for(int32 Y=Minimum.Y;Y<=Maximum.Y;++Y)
                        CrewSupportBins.FindOrAdd(FIntPoint(X,Y)).Add(Index);
                }
            }
            CrewSupportIndexRevision=CrewSupportGeometryRevision;
            CrewSupportIndexTransform=ToActor;
        }
        for(int32 J=0;J<Points.Num();++J)
        {
            const TArray<int32>* BinTriangles=CrewSupportBins.Find(Bin(Points[J]));
            if(!BinTriangles)continue;
            for(int32 Index:*BinTriangles)
            {
                const FCrewSupportTriangle& T=CrewSupportTriangles[Index];
                // Preserve reference whole-query bounds filtering and arithmetic.
                if(FMath::Max3(T.A.X,T.B.X,T.C.X)<Bounds.Min.X || FMath::Min3(T.A.X,T.B.X,T.C.X)>Bounds.Max.X ||
                    FMath::Max3(T.A.Y,T.B.Y,T.C.Y)<Bounds.Min.Y || FMath::Min3(T.A.Y,T.B.Y,T.C.Y)>Bounds.Max.Y)continue;
                const FVector& P=Points[J];
                const double U=((T.B.Y-T.C.Y)*(P.X-T.C.X)+(T.C.X-T.B.X)*(P.Y-T.C.Y))/T.Determinant;
                const double V=((T.C.Y-T.A.Y)*(P.X-T.C.X)+(T.A.X-T.C.X)*(P.Y-T.C.Y))/T.Determinant;
                const double W=1-U-V;
                if(FMath::Min3(U,V,W)<-1.e-6)continue;
                const double Z=U*T.A.Z+V*T.B.Z+W*T.C.Z;
                Solid[J]=FMath::Max(Solid[J],Z);
                if(T.bFloor)Floor[J]=FMath::Max(Floor[J],Z);
            }
        }
        return !Solid.Contains(-DBL_MAX);
    }
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
    // Airborne/rescue/reentry trajectories retain their authored motion.
    if (CurrentAction > ERaftSimCrewAvatarAction::HighSideStarboard || !HasProductionRiverBoots()) return;
    // The tube-stance candidate still fails bow/guide full-contact qualification.
    // Keep the existing ordinary seated fit; never ship the failed trial by default.
    static const bool bReviewHighSideContact = FParse::Param(FCommandLine::Get(),TEXT("RaftSimReviewHighSideContact"));
    if (CurrentAction > ERaftSimCrewAvatarAction::Brace && !bReviewHighSideContact) return;
    CSV_SCOPED_TIMING_STAT(RaftSimCrewContact,FitFeet);
    CSV_CUSTOM_STAT(RaftSimCrewContact,AttemptedPoses,1,ECsvCustomStatOp::Accumulate);
    ARaftSimRaftActor* Raft = Cast<ARaftSimRaftActor>(GetAttachParentActor());
    if (!Raft) { bFootPlacementBound = false; FootPlacementRaft.Reset(); return; }
    if (FootPlacementRaft.Get() != Raft) { bFootPlacementBound = false; FootPlacementRaft = Raft; }
    const bool bHighSide=CurrentAction==ERaftSimCrewAvatarAction::HighSidePort ||
        CurrentAction==ERaftSimCrewAvatarAction::HighSideStarboard;
    const int32 PlacementMode=bHighSide ? int32(CurrentAction) : 0;
    if(BoundFootPlacementMode!=PlacementMode)bFootPlacementBound=false;
    const int32 HighSideSign=CurrentAction==ERaftSimCrewAvatarAction::HighSidePort ? -1 : 1;
    const bool bStepOntoTube=bHighSide && HighSideSign==SeatSide;
    const FTransform ToRaft = GetActorTransform().GetRelativeTransform(Raft->GetActorTransform());
    const auto Idle = URaftSimCrewAvatarPoseLibrary::EvaluatePose(ERaftSimCrewAvatarAction::SeatedIdle, 0, SeatSide);
    FVector Feet[2] = {Idle.LeftFootCm, Idle.RightFootCm};
    // A fourteen-centimetre ankle stance fits two separate boot footprints
    // in each half of the raft. Search both together; never cross the feet.
    Feet[0].Y += 2.0; Feet[1].Y -= 2.0;
    // The outboard high-side stance steps onto the high tube. The opposite
    // seat braces on the floor while its pelvis moves inboard. A half-on-tube
    // footprint is rejected below, not lifted by one bounding-box corner.
    if(bStepOntoTube){Feet[0].Y=-7.;Feet[1].Y=7.;}
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
            double MinimumZ=DBL_MAX;
            for (int32 J = 0; J < Points.Num(); ++J)
            {
                if (bRequireFloor && Solid[J] > Floor[J]+0.5) return false;
                Z = FMath::Max(Z, Solid[J]);
                MinimumZ=FMath::Min(MinimumZ,Solid[J]);
            }
            return FMath::IsFinite(Z) && (!bHighSide || Z-MinimumZ<=4.0);
        };
    bool bFound = false;
    double SupportZ[2] = {0,0};
    const uint64 GeometryRevision = Raft->GetCrewSupportGeometryRevision();
    if (bFootPlacementBound)
    {
        // Supported seated actions retain the paired stance throughout motion.
        Feet[0] = BoundFootLocalCm[0];
        Feet[1] = BoundFootLocalCm[1];
        if (GeometryRevision != 0 && CachedFootSupportRevision == GeometryRevision &&
            ToRaft.Equals(CachedFootSupportToRaft,1.e-6))
        {
            CSV_CUSTOM_STAT(RaftSimCrewContact,CacheHits,1,ECsvCustomStatOp::Accumulate);
            SupportZ[0] = CachedFootSupportZ[0]; SupportZ[1] = CachedFootSupportZ[1];
            bFound = true;
        }
        else
        {
            CSV_CUSTOM_STAT(RaftSimCrewContact,GeometryMisses,int32(CachedFootSupportRevision != GeometryRevision),ECsvCustomStatOp::Accumulate);
            CSV_CUSTOM_STAT(RaftSimCrewContact,SeatMisses,int32(!ToRaft.Equals(CachedFootSupportToRaft,1.e-6)),ECsvCustomStatOp::Accumulate);
            bFound = Sample(0,Feet[0],SupportZ[0],false) && Sample(1,Feet[1],SupportZ[1],false);
        }
        if(!bFound && bHighSide)
        {
            // The live hull can change after an initially valid placement.
            // A failed old footprint must seek a new supported stance instead
            // of falling back to authored penetrating feet on every frame.
            bFootPlacementBound=false;
            Feet[0]=Idle.LeftFootCm;Feet[1]=Idle.RightFootCm;
            Feet[0].Y+=2.;Feet[1].Y-=2.;
            if(bStepOntoTube){Feet[0].Y=-7.;Feet[1].Y=7.;}
            CSV_CUSTOM_STAT(RaftSimCrewContact,InvalidatedStanceSearches,1,ECsvCustomStatOp::Accumulate);
        }
    }
    if (!bFootPlacementBound && bStepOntoTube)
    {
        // Curved bow/stern tubes do not admit a rigid side-by-side rectangle.
        // Search each foot, then pair only reachable, non-overlapping stances.
        // Geometry and all support/reach limits are shared with the floor fit.
        struct FCandidate { FVector Foot; double Support; double Cost; };
        TArray<FCandidate> Candidates[2];
        const FVector Hips[2] = {Pose.LeftHipCm,Pose.RightHipCm};
        const FVector RestHips[2] = {Idle.LeftHipCm,Idle.RightHipCm};
        const FVector Knees[2] = {Idle.LeftKneeCm,Idle.RightKneeCm};
        const FVector RestFeet[2] = {Idle.LeftFootCm,Idle.RightFootCm};
        const FVector Authored[2] = {Feet[0],Feet[1]};
        FBox FootBounds[2];
        for(int32 Foot=0;Foot<2;++Foot)
        {
            const FBox Source=Boots[Foot]->GetStaticMesh()->GetBoundingBox();
            FootBounds[Foot]=FBox(Source.Min*Boots[Foot]->GetRelativeScale3D(),Source.Max*Boots[Foot]->GetRelativeScale3D());
        }
        for(int32 Step=0;Step<=64 && !bFound;++Step)
        {
            const double Along=((Step+1)/2)*2*(Step%2 ? 1 : -1);
            for(int32 Shift=0;Shift<=96;++Shift)
            {
                const double Lateral=((Shift+1)/2)*(Shift%2 ? -1 : 1);
                for(int32 Foot=0;Foot<2;++Foot)
                {
                    FVector Candidate=Authored[Foot]+FVector(Along,Inboard*Lateral,0);
                    double Z=0;
                    if(!Sample(Foot,Candidate,Z,false))continue;
                    const FVector P=ToRaft.TransformPosition(Candidate);
                    Candidate.Z=ToRaft.InverseTransformPosition(FVector(P.X,P.Y,Z)).Z
                        -Boots[Foot]->GetStaticMesh()->GetBoundingBox().Min.Z*ProfileZ+0.1;
                    const double Upper=FVector::Distance(RestHips[Foot],Knees[Foot]);
                    const double Lower=FVector::Distance(Knees[Foot],RestFeet[Foot]);
                    const double Reach=FVector::Distance(Hips[Foot],Candidate);
                    if(Reach>=Upper+Lower-1.0 || Reach<=FMath::Abs(Upper-Lower)+1.0)continue;
                    Candidates[Foot].Add({Candidate,Z,Along*Along+Lateral*Lateral});
                }
            }
            double BestCost=DBL_MAX;
            for(const FCandidate& Left:Candidates[0])for(const FCandidate& Right:Candidates[1])
            {
                if(Right.Foot.Y-Left.Foot.Y<4.0 || FMath::Abs(Right.Foot.Z-Left.Foot.Z)>10.0)continue;
                const bool bSeparate=
                    Left.Foot.X+FootBounds[0].Max.X+1.0<=Right.Foot.X+FootBounds[1].Min.X ||
                    Right.Foot.X+FootBounds[1].Max.X+1.0<=Left.Foot.X+FootBounds[0].Min.X ||
                    Left.Foot.Y+FootBounds[0].Max.Y+1.0<=Right.Foot.Y+FootBounds[1].Min.Y;
                const double Cost=Left.Cost+Right.Cost;
                if(!bSeparate || Cost>=BestCost)continue;
                BestCost=Cost; bFound=true;
                Feet[0]=Left.Foot; Feet[1]=Right.Foot;
                SupportZ[0]=Left.Support; SupportZ[1]=Right.Support;
            }
        }
    }
    else if (!bFootPlacementBound)
    {
        const FVector Authored[2] = {Feet[0],Feet[1]};
        for (int32 Step = 0; Step <= (bGuide ? 32 : 16) && !bFound; ++Step)
                for (int32 Shift = 0; Shift <= (bStepOntoTube ? 96 : 24) && !bFound; ++Shift)
                {
                    // The stern seat needs forward reach into the narrowing
                    // floor. Try nearest forward/aft pairs before tube support.
                    const double Along = bGuide ? ((Step+1)/2)*2*(Step%2 ? 1 : -1) : -2*Step;
                    // Seats sit on the inner tube shoulder, not necessarily
                    // its crest. Search both lateral directions for a tube
                    // stance; an inboard-only search never reaches that crest.
                    const double Lateral = bStepOntoTube
                        ? ((Shift+1)/2)*(Shift%2 ? -1 : 1) : Shift;
                    for (int32 Foot = 0; Foot < 2; ++Foot)
                        Feet[Foot] = Authored[Foot]+FVector(Along,Inboard*Lateral,0);
                    // Floor stances require floor; tube stances require the
                    // same full-footprint support and height-span limit. A tube
                    // touched only by a bounding-box corner is not sole contact.
                    bFound = Sample(0,Feet[0],SupportZ[0],!bStepOntoTube) && Sample(1,Feet[1],SupportZ[1],!bStepOntoTube);
                    if (bFound)
                    {
                        const FVector Hips[2] = {Pose.LeftHipCm,Pose.RightHipCm};
                        const FVector RestHips[2] = {Idle.LeftHipCm,Idle.RightHipCm};
                        const FVector Knees[2] = {Idle.LeftKneeCm,Idle.RightKneeCm};
                        const FVector RestFeet[2] = {Idle.LeftFootCm,Idle.RightFootCm};
                        for (int32 Foot = 0; Foot < 2; ++Foot)
                        {
                            const FVector P = ToRaft.TransformPosition(Feet[Foot]);
                            FVector Candidate = Feet[Foot];
                            Candidate.Z = ToRaft.InverseTransformPosition(FVector(P.X,P.Y,SupportZ[Foot])).Z
                                - Boots[Foot]->GetStaticMesh()->GetBoundingBox().Min.Z*ProfileZ+0.1;
                            const double Upper = FVector::Distance(RestHips[Foot],Knees[Foot]);
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
        BoundFootPlacementMode=PlacementMode;
        UE_LOG(LogTemp,Display,TEXT("CREW_FOOT_BIND actor=%s left=%s right=%s"),
            *GetName(),*Feet[0].ToString(),*Feet[1].ToString());
    }
    Pose.LeftFootCm = Feet[0]; Pose.RightFootCm = Feet[1];
    Pose.LeftKneeCm = LeftKnee; Pose.RightKneeCm = RightKnee;
    Pose.bFeetPlanted = true;
    CSV_CUSTOM_STAT(RaftSimCrewContact,SolvedPoses,1,ECsvCustomStatOp::Accumulate);
}
