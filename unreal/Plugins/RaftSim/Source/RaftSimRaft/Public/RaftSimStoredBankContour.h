#pragma once
#include "RaftSimSharedBankCrossing.h"

// Cartesian candidate: every certificate encloses the inverse of an actual
// binary32 world coordinate. No local-depth tolerance and no datum rebasing.
namespace RaftSimStoredBankContour
{
using namespace RaftSimThreeWetBankContour;
struct FStorage
{
    FCurve Curve;
    FVector2D Origin,End,RenderOrigin;
    FVector2D Crossings[2];
    double Width=0.,RootWidth=0.;
    bool Valid=false;
    mutable int32 SignedNeighborFallbacks=0;
    static bool ExactDifference(double A,double B,double& D)
    {
        // Error-free TwoDiff, with explicit rounding points. Do not pretend
        // subtracting an arbitrary render origin was an exact translation.
        volatile double Difference=A-B;
        volatile double VirtualB=A-Difference;
        volatile double VirtualA=Difference+VirtualB;
        volatile double ErrorA=A-VirtualA;
        volatile double ErrorB=VirtualB-B;
        D=Difference;
        return FMath::IsFinite(D) && ErrorA+ErrorB==0.;
    }
    bool Init(const FCurve& C,const FVector2D& Dry,const FVector2D& WetX,const FVector2D& WetY,double WidthCm,
        FVector2D RequestedRenderOrigin=FVector2D::ZeroVector)
    {
        const FScopedIEEE Scope;Valid=false;SignedNeighborFallbacks=0;
        if(!C.Valid || !FMath::IsFinite(WidthCm) || WidthCm<=0. || Dry.ContainsNaN() ||
            WetX.ContainsNaN() || WetY.ContainsNaN() || Dry.Y!=WetX.Y || Dry.X!=WetY.X ||
            Dry.X==WetX.X || Dry.Y==WetY.Y)return false;
        if(RequestedRenderOrigin.ContainsNaN())return false;
        for(const FVector2D P:{Dry,WetX,WetY})for(int32 Axis=0;Axis<2;++Axis)
        {
            double V=0.;
            if(!FMath::IsFinite(P[Axis]) || !FMath::IsFinite(RequestedRenderOrigin[Axis]) ||
                !ExactDifference(P[Axis],RequestedRenderOrigin[Axis],V) || double(float(V))!=V)return false;
        }
        Curve=C;RenderOrigin=RequestedRenderOrigin;Origin=Dry-RenderOrigin;
        End=FVector2D(WetX.X,WetY.Y)-RenderOrigin;
        const FVector2D Delta=End-Origin;
        const FBound DX=End.X>Origin.X ? FBound(End.X)-FBound(Origin.X) : FBound(Origin.X)-FBound(End.X);
        const FBound DY=End.Y>Origin.Y ? FBound(End.Y)-FBound(Origin.Y) : FBound(Origin.Y)-FBound(End.Y);
        Width=DividePositive(FBound(WidthCm),FBound(FMath::Max(DX.Hi,DY.Hi))).Lo;
        if(Width<=256.*std::numeric_limits<double>::epsilon() || Width>=1.)return false;
        double Quantization=0.;
        for(int32 Axis=0;Axis<2;++Axis)
        {
            RaftSimSharedBankCrossing::FResult R;
            if(!RaftSimSharedBankCrossing::Build(End[Axis],Origin[Axis],C.Bed[Axis ? 2 : 1],C.Bed[0],
                C.Depth[Axis ? 2 : 1],Width*FMath::Abs(Delta[Axis]),R))return false;
            Crossings[Axis]=Origin;Crossings[Axis][Axis]=R.Position;
            double Step=0.;
            for(double V:{Origin[Axis],End[Axis]})for(float Direction:{-std::numeric_limits<float>::infinity(),std::numeric_limits<float>::infinity()})
                Step=FMath::Max(Step,FMath::Abs(double(std::nextafter(float(V),Direction))-V));
            Quantization=Up(Quantization+Up(Step/FMath::Abs(Delta[Axis])));
        }
        // Root proposals leave space for the final outward float conversion.
        // This never increases Width; lack of representable room fails closed.
        RootWidth=Down(Width-Quantization);
        Valid=RootWidth>0.;return Valid;
    }
    FBound Coordinate(double P,int32 Axis)const
    {
        if(P==Origin[Axis])return FBound(0.);
        if(P==End[Axis])return FBound(1.);
        return End[Axis]>Origin[Axis] ?
            DividePositive(FBound(P)-FBound(Origin[Axis]),FBound(End[Axis])-FBound(Origin[Axis])) :
            DividePositive(FBound(Origin[Axis])-FBound(P),FBound(Origin[Axis])-FBound(End[Axis]));
    }
    FPoint Local(const FVector2D& World)const
    {
        const FVector2D P=(World-Origin)/(End-Origin);
        return FPoint(P,Coordinate(World.X,0),Coordinate(World.Y,1));
    }
    FVector2D BufferPosition(const FPoint& P)const
    {
        // Export/retrieval only. Build certificates already enclose the exact
        // inverse map of this binary32 buffer point, not this rounded inverse.
        // The renderer MUST translate by RenderOrigin, also in its RT path.
        return FVector2D(double(float(Origin.X+(End.X-Origin.X)*P.XY.X)),
            double(float(Origin.Y+(End.Y-Origin.Y)*P.XY.Y)));
    }
    FPoint operator()(const FPoint& Proposal,double T)const
    {
        if(T==0.)return Local(Crossings[0]);if(T==1.)return Local(Crossings[1]);
        FVector2D Stored;
        double Candidates[2][3];
        for(int32 Axis=0;Axis<2;++Axis)
        {
            if(Proposal.XY[Axis]==0.){Stored[Axis]=Origin[Axis];Candidates[Axis][0]=Candidates[Axis][1]=Candidates[Axis][2]=Stored[Axis];continue;}
            if(Proposal.XY[Axis]==1.){Stored[Axis]=End[Axis];Candidates[Axis][0]=Candidates[Axis][1]=Candidates[Axis][2]=Stored[Axis];continue;}
            const bool Increasing=End[Axis]>Origin[Axis];
            const FBound Mapped=FBound(Origin[Axis])+(FBound(End[Axis])-FBound(Origin[Axis]))*FBound(Proposal.XY[Axis]);
            const double Bound=Increasing ? Mapped.Hi : Mapped.Lo;
            float P=float(Bound);
            if(Increasing ? double(P)<Bound : double(P)>Bound)
                P=std::nextafter(P,Increasing ? std::numeric_limits<float>::infinity() : -std::numeric_limits<float>::infinity());
            Stored[Axis]=double(P);
            Candidates[Axis][0]=double(P);
            Candidates[Axis][1]=double(std::nextafter(P,Increasing ? -std::numeric_limits<float>::infinity() : std::numeric_limits<float>::infinity()));
            Candidates[Axis][2]=double(std::nextafter(P,Increasing ? std::numeric_limits<float>::infinity() : -std::numeric_limits<float>::infinity()));
        }
        if(T>0. && T<1.)
        {
            FVector2D Preferred=Proposal.XY;
            // Near a canonical axis, one off-axis float step may be much
            // larger than the proposed coordinate. Search on that ACTUAL
            // stored row/column instead of retaining a now-dry radial root.
            // This is proposal generation only; every stored segment, wet
            // triangle, dry fan, partition and 1mm width still must certify.
            const int32 Fixed=T<=.5 ? 1 : 0,Free=1-Fixed;
            const double FixedStep=FMath::Abs(double(std::nextafter(float(Origin[Fixed]),
                End[Fixed]>Origin[Fixed] ? std::numeric_limits<float>::infinity() :
                    -std::numeric_limits<float>::infinity()))-Origin[Fixed]);
            const bool NearAxis=FMath::Abs(Stored[Fixed]-Origin[Fixed])<=2.*FixedStep;
            bool HasSignedNeighbor=false;
            for(int32 X=0;X<3;++X)for(int32 Y=0;Y<3;++Y)
            {
                const FPoint Neighbor=Local(FVector2D(Candidates[0][X],Candidates[1][Y]));
                if(Neighbor.X.Lo>0. && Neighbor.X.Hi<1. && Neighbor.Y.Lo>0. && Neighbor.Y.Hi<1. &&
                    Curve.Value(Neighbor).Lo>=0. && Curve.Value(Inner(Neighbor,Width)).Hi<=0.)HasSignedNeighbor=true;
            }
            // Quantization can also move a shallow, far-from-axis radial
            // proposal beyond all nine signed neighbors. Re-solve on its
            // actual stored row; final segment/partition proofs remain mandatory.
            if(NearAxis || !HasSignedNeighbor)
            {
                if(!NearAxis)++SignedNeighborFallbacks;
                FVector2D P=Local(Stored).XY;double Low=0.,High=1.;
                for(int32 I=0;I<56;++I)
                {
                    P[Free]=(Low+High)*.5;
                    if(Curve.Value(FPoint(P)).Lo>=0.)High=P[Free];else Low=P[Free];
                    if(Up(High-Low)<=Down(RootWidth/16.))break;
                }
                const bool Increasing=End[Free]>Origin[Free];
                // Wet endpoints alone do not prove the connection to the
                // shared crossing. Choose an actual fixed-row endpoint by
                // certifying that complete segment, with a dry inner point.
                // The fixed coordinate is never moved to another row here.
                const FPoint Edge=Local(Crossings[Free]);
                FStats EndcapStats;
                for(double Reserve:{.5,.625,.75,.875,.375,.25})
                {
                    if(!NearAxis)break; // Only an endcap is connected directly to the axis.
                    P[Free]=FMath::Min(1.,High+RootWidth*Reserve);
                    const FBound TrialMap=FBound(Origin[Free])+(FBound(End[Free])-FBound(Origin[Free]))*FBound(P[Free]);
                    const double TrialBound=Increasing ? TrialMap.Hi : TrialMap.Lo;
                    float Trial=float(TrialBound);
                    if(Increasing ? double(Trial)<TrialBound : double(Trial)>TrialBound)
                        Trial=std::nextafter(Trial,Increasing ? std::numeric_limits<float>::infinity() : -std::numeric_limits<float>::infinity());
                    FVector2D W=Stored;W[Free]=double(Trial);const FPoint Candidate=Local(W);
                    if(Candidate.X.Lo<=0. || Candidate.X.Hi>=1. || Candidate.Y.Lo<=0. || Candidate.Y.Hi>=1. ||
                        Curve.Value(Candidate).Lo<0. || Curve.Value(Inner(Candidate,Width)).Hi>0.)continue;
                    if(Certificate(Curve,Edge,Candidate,Candidate,true,EndcapStats))return Candidate;
                }
                P[Free]=FMath::Min(1.,High+RootWidth*.75);
                const FBound Mapped=FBound(Origin[Free])+(FBound(End[Free])-FBound(Origin[Free]))*FBound(P[Free]);
                const double Bound=Increasing ? Mapped.Hi : Mapped.Lo;float V=float(Bound);
                if(Increasing ? double(V)<Bound : double(V)>Bound)
                    V=std::nextafter(V,Increasing ? std::numeric_limits<float>::infinity() : -std::numeric_limits<float>::infinity());
                Stored[Free]=double(V);Candidates[Free][0]=double(V);
                Candidates[Free][1]=double(std::nextafter(V,Increasing ? -std::numeric_limits<float>::infinity() : std::numeric_limits<float>::infinity()));
                Candidates[Free][2]=double(std::nextafter(V,Increasing ? std::numeric_limits<float>::infinity() : -std::numeric_limits<float>::infinity()));
                // All proposals landing on the same near-axis GPU row must
                // select the same point. Mixing radial and fixed-row roots
                // reverses angular order as X grows while stored Y is fixed.
                Preferred=Local(Stored).XY;
            }
            // Rounding both axes outward can consume the entire geometric
            // band in a direction unlike the contour normal. Select among
            // neighboring representable pairs only when BOTH the stored point
            // and its inner band endpoint have proved signs. The complete
            // segment/triangle certificates still decide acceptance below.
            bool Found=false;double Best=std::numeric_limits<double>::infinity();
            FVector2D Choice=Stored;
            // A componentwise outward move is not necessarily wetter: the
            // captured v22 contour has a negative X derivative near its fold.
            // Include the next pixel on BOTH sides, with signs still proved.
            for(int32 X=0;X<3;++X)for(int32 Y=0;Y<3;++Y)
            {
                const FVector2D W(Candidates[0][X],Candidates[1][Y]);const FPoint P=Local(W);
                if(P.X.Lo<=0. || P.X.Hi>=1. || P.Y.Lo<=0. || P.Y.Hi>=1. ||
                    Curve.Value(P).Lo<0. || Curve.Value(Inner(P,Width)).Hi>0.)continue;
                const double Distance=FMath::Abs(P.XY.X-Preferred.X)+FMath::Abs(P.XY.Y-Preferred.Y);
                if(Distance<Best){Best=Distance;Choice=W;Found=true;}
            }
            if(Found)Stored=Choice;
        }
        return Local(Stored);
    }
};
inline bool Build(const FCurve& C,const FStorage& Storage,FResult& Out)
{
    if(!Storage.Valid){Out={};return false;}
    for(int32 I=0;I<4;++I)if(C.Bed[I]!=Storage.Curve.Bed[I] || C.Depth[I]!=Storage.Curve.Depth[I])
        {Out={};return false;}
    return BuildStored(C,Storage.Width,Out,Storage,Storage.RootWidth);
}
}
