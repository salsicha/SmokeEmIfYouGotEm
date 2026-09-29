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
    struct FEndcap
    {
        bool Active=false;
        double Limit=0.;
        FVector2D First=FVector2D::ZeroVector,Last=FVector2D::ZeroVector;
        FPoint Inner{FVector2D::ZeroVector};
    };
    FEndcap Endcaps[2];
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
        Endcaps[0]=FEndcap{};Endcaps[1]=FEndcap{};
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
                C.Depth[Axis ? 2 : 1],WidthCm,R))return false;
            Crossings[Axis]=Origin;Crossings[Axis][Axis]=R.Position;
            double Step=0.;
            for(double V:{Origin[Axis],End[Axis]})for(float Direction:{-std::numeric_limits<float>::infinity(),std::numeric_limits<float>::infinity()})
                Step=FMath::Max(Step,FMath::Abs(double(std::nextafter(float(V),Direction))-V));
            Quantization=Up(Quantization+Up(Step/FMath::Abs(Delta[Axis])));
        }
        // Root proposals leave space for the final outward float conversion.
        // This never increases Width; lack of representable room fails closed.
        RootWidth=Down(Width-Quantization);
        Valid=RootWidth>0.;
        if(Valid){PrepareEndcap(0);PrepareEndcap(1);}
        return Valid;
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
    FPoint InnerPoint(const FPoint& P,double InWidth)const
    {
        if(InWidth==Width)for(int32 Free=0;Free<2;++Free)
        {
            const FEndcap& Cap=Endcaps[Free];if(!Cap.Active)continue;
            const FVector2D W=BufferPosition(P);const int32 Fixed=1-Free;
            if(W[Free]==Cap.First[Free] && W[Fixed]>=FMath::Min(Cap.First[Fixed],Cap.Last[Fixed]) &&
                W[Fixed]<=FMath::Max(Cap.First[Fixed],Cap.Last[Fixed]))return Cap.Inner;
        }
        const FPoint Radial=Inner(P,InWidth);
        if(P.X.Zero() || P.Y.Zero())return Radial;
        // Preserve the ordered radial fan whenever its dry witness proves.
        // Nearest-normal witnesses can reverse the inner fan at a fold.
        if(Curve.Value(Radial).Hi<=0.)return Radial;
        const double X=P.XY.X,Y=P.XY.Y;
        const double W0=(1.-X)*(1.-Y);
        const double W[]={W0,X*(1.-Y),(1.-X)*Y,X*Y};
        const double DX[]={-(1.-Y),1.-Y,-Y,Y},DY[]={-(1.-X),-X,1.-X,X};
        double Drop=0.,GX=0.,GY=0.,DropX=0.,DropY=0.;
        for(int32 I=1;I<4;++I)
        {
            const double D=Curve.Bed[0]-Curve.Bed[I];Drop+=W[I]*D;
            GX+=DX[I]*Curve.Depth[I];GY+=DY[I]*Curve.Depth[I];
            DropX+=DX[I]*D;DropY+=DY[I]*D;
        }
        GX-=DX[0]*Drop+W0*DropX;GY-=DY[0]*Drop+W0*DropY;
        const double Size=FMath::Abs(GX)+FMath::Abs(GY);
        if(!FMath::IsFinite(Size) || Size<=0.)return Radial;
        const double Error=FMath::Max(FMath::Abs(P.X.Lo-X),FMath::Abs(P.X.Hi-X))+
            FMath::Max(FMath::Abs(P.Y.Lo-Y),FMath::Abs(P.Y.Hi-Y));
        const double Distance=FMath::Max(0.,InWidth-128.*std::numeric_limits<double>::epsilon()-2.*Error);
        // A shallow contour can require only a small rotation of the radial
        // retreat. Jumping directly to its normal can reverse the inner fan.
        // Try componentwise inward proposals nearest the radial direction
        // first; the complete adjacent partition still decides acceptance.
        const double Radius=X+Y;
        const int32 Small=X<=Y ? 0 : 1;
        for(int32 Axis:{Small,1-Small})for(double Scale:{.875,.75,.625,.5,.25,0.})
        {
            FVector2D Direction=P.XY/Radius;
            Direction[Axis]*=Scale;Direction[1-Axis]=1.-Direction[Axis];
            const FVector2D V(FMath::Max(0.,X-Distance*Direction.X),FMath::Max(0.,Y-Distance*Direction.Y));
            const FPoint Rotated(V,V==FVector2D::ZeroVector);
            if(Curve.Value(Rotated).Hi<=0.)return Rotated;
        }
        const FVector2D Q(FMath::Clamp(X-Distance*(GX/Size),0.,1.),FMath::Clamp(Y-Distance*(GY/Size),0.,1.));
        const FPoint Candidate(Q,Q==FVector2D::ZeroVector);
        // Gradient direction is only a geometric proposal. Its actual dry
        // sign, full fan, orientation, partition and unchanged width must prove.
        return Curve.Value(Candidate).Hi<=0. ? Candidate : Radial;
    }
    double MapCoordinate(double V,int32 Axis,bool Away)const
    {
        const bool Increasing=End[Axis]>Origin[Axis];
        const FBound M=FBound(Origin[Axis])+(FBound(End[Axis])-FBound(Origin[Axis]))*FBound(V);
        const bool Upward=Increasing==Away;
        const double Bound=Upward ? M.Hi : M.Lo;float W=float(Bound);
        if(Upward ? double(W)<Bound : double(W)>Bound)
            W=std::nextafter(W,Upward ? std::numeric_limits<float>::infinity() : -std::numeric_limits<float>::infinity());
        return FMath::Clamp(double(W),FMath::Min(Origin[Axis],End[Axis]),FMath::Max(Origin[Axis],End[Axis]));
    }
    void PrepareEndcap(int32 Free)
    {
        // A first representable row can require a long tangential endcap.
        // Route back to the contour on that same stored free coordinate,
        // sharing one proved dry witness across the resulting vertical strip.
        // Every value below comes from this cell's original donors and GPU
        // spacing; no captured case or coordinate is special-cased.
        const int32 Fixed=1-Free;FStats Stats;
        const FPoint O(FVector2D::ZeroVector,true),Edge=Local(Crossings[Free]);
        const FPoint EdgeInner=Inner(Edge,Width);
        FVector2D Row=Origin;
        Row[Fixed]=double(std::nextafter(float(Origin[Fixed]),End[Fixed]>Origin[Fixed] ?
            std::numeric_limits<float>::infinity() : -std::numeric_limits<float>::infinity()));
        const auto OnRow=[&](double V){FVector2D W=Row;W[Free]=MapCoordinate(V,Free,true);return Local(W);};
        double Low=0.,High=1.;FPoint P=OnRow(High);
        if(!Certificate(Curve,Edge,P,P,true,Stats))return;
        for(int32 I=0;I<56;++I)
        {
            const double Mid=(Low+High)*.5;const FPoint Trial=OnRow(Mid);
            if(SamePoint(Trial,P))break;
            if(Certificate(Curve,Edge,Trial,Trial,true,Stats)){High=Mid;P=Trial;}else Low=Mid;
        }
        const FPoint Radial=Inner(P,Width);
        if(Curve.Value(Radial).Hi<=0.)return; // Existing radial path needs no bridge.
        const FPoint Alternative=InnerPoint(P,Width);
        const auto Proves=[&](const FPoint& A)
        {
            if(Curve.Value(A).Hi>0.)return false;
            if(Free==0)
            {
                if(Cross(O,Edge,P).Lo<=0. || Cross(Edge,P,A).Lo<0. ||
                    Cross(Edge,A,EdgeInner).Lo<0. || Cross(O,EdgeInner,A).Lo<0.)return false;
            }
            else if(Cross(O,P,Edge).Lo<=0. || Cross(P,Edge,EdgeInner).Lo<0. ||
                Cross(P,EdgeInner,A).Lo<0. || Cross(O,A,EdgeInner).Lo<0.)return false;
            return Certificate(Curve,O,EdgeInner,A,false,Stats);
        };
        if(!Proves(Alternative))return;
        // Find a close dry witness; a full normal retreat can reverse the
        // subsequent fan even though it has a valid pointwise dry sign.
        double Left=0.,Right=1.;FPoint A=Alternative;
        for(int32 I=0;I<56;++I)
        {
            const double Mid=(Left+Right)*.5;
            const FPoint Trial(Radial.XY+(Alternative.XY-Radial.XY)*Mid);
            if(Proves(Trial)){Right=Mid;A=Trial;}else Left=Mid;
            if((Alternative.XY-Radial.XY).GetAbs().X*(Right-Left)+
                (Alternative.XY-Radial.XY).GetAbs().Y*(Right-Left)<=RootWidth/65536.)break;
        }
        const FVector2D Start=BufferPosition(P);
        const auto OnLine=[&](double V){FVector2D W=Start;W[Fixed]=MapCoordinate(V,Fixed,false);return Local(W);};
        Low=P.XY[Fixed];High=FMath::Min(1.,FMath::Max(Low,A.XY[Fixed])+Width);
        FPoint Last=P;
        for(int32 I=0;I<56;++I)
        {
            const double Mid=(Low+High)*.5;const FPoint Trial=OnLine(Mid);
            if(SamePoint(Trial,Last))break;
            if(Certificate(Curve,P,Trial,Trial,true,Stats)){Low=Mid;Last=Trial;}else High=Mid;
        }
        if(!Proves(A))return;
        for(const FPoint* V:{&P,&Last})
        {
            const FBound DX=V->X-A.X,DY=V->Y-A.Y;
            if(Up(FMath::Max(FMath::Abs(DX.Lo),FMath::Abs(DX.Hi))+
                FMath::Max(FMath::Abs(DY.Lo),FMath::Abs(DY.Hi)))>Width)return;
        }
        // Preserve a proved one-point witness without emitting a new strip.
        // Every neighboring partition and depth certificate remains required.
        if(!SamePoint(P,Last) && (Free==0 ? Cross(P,Last,A).Lo<0. : Cross(Last,P,A).Lo<0.))return;
        FEndcap& Cap=Endcaps[Free];Cap.First=Start;Cap.Last=BufferPosition(Last);Cap.Inner=A;
        Cap.Limit=High/(P.XY[Free]+High);Cap.Active=true;
    }
    FPoint operator()(const FPoint& Proposal,double T)const
    {
        if(T==0.)return Local(Crossings[0]);if(T==1.)return Local(Crossings[1]);
        if(T>0. && T<1.)for(int32 Free=0;Free<2;++Free)
        {
            const FEndcap& Cap=Endcaps[Free];const double Along=Free==0 ? T : 1.-T;
            if(!Cap.Active || Along>Cap.Limit)continue;
            if(Cap.First==Cap.Last)continue; // Witness only; no outer strip.
            const int32 Fixed=1-Free;const FPoint First=Local(Cap.First),Last=Local(Cap.Last);
            const double V=FMath::Clamp(First.XY[Free]*Along/(1.-Along),First.XY[Fixed],Last.XY[Fixed]);
            FVector2D W=Cap.First;W[Fixed]=FMath::Clamp(MapCoordinate(V,Fixed,false),
                FMath::Min(Cap.First[Fixed],Cap.Last[Fixed]),FMath::Max(Cap.First[Fixed],Cap.Last[Fixed]));
            return Local(W);
        }
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
            // Only the first off-axis row closes against the shared edge.
            // Later rows connect through that endcap/bridge. Requiring their
            // direct edge chords to be wet can push them past the dry witness
            // band even when the consecutive-row partition is certified.
            const bool FirstRow=FMath::Abs(Stored[Fixed]-Origin[Fixed])==FixedStep;
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
                    if(!FirstRow)break; // Later rows connect through the first endcap.
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
                if(FirstRow)
                {
                    const auto RowPoint=[&](double Coordinate)
                    {
                        const FBound M=FBound(Origin[Free])+(FBound(End[Free])-FBound(Origin[Free]))*FBound(Coordinate);
                        const double Bound=Increasing ? M.Hi : M.Lo;float V=float(Bound);
                        if(Increasing ? double(V)<Bound : double(V)>Bound)
                            V=std::nextafter(V,Increasing ? std::numeric_limits<float>::infinity() : -std::numeric_limits<float>::infinity());
                        FVector2D W=Stored;W[Free]=FMath::Clamp(double(V),FMath::Min(Origin[Free],End[Free]),FMath::Max(Origin[Free],End[Free]));
                        return Local(W);
                    };
                    double Left=High,Right=1.;FPoint Best=RowPoint(Right);
                    if(Certificate(Curve,Edge,Best,Best,true,EndcapStats))
                    {
                        // Find a whole-wet connection on this actual GPU row.
                        // A long tangential step is allowed only when the
                        // independently certified dry witness stays within1mm.
                        for(int32 I=0;I<56;++I)
                        {
                            const double Mid=(Left+Right)*.5;const FPoint Trial=RowPoint(Mid);
                            if(SamePoint(Trial,Best))break;
                            if(Certificate(Curve,Edge,Trial,Trial,true,EndcapStats)){Right=Mid;Best=Trial;}
                            else Left=Mid;
                        }
                        if(Curve.Value(InnerPoint(Best,Width)).Hi<=0.)return Best;
                    }
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
