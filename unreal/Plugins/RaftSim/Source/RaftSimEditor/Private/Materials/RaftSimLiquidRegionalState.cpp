#include "RaftSimLiquidRegionalState.h"
#include "RaftSimLiquidGridAllocation.h"
#include "RaftSimLiquidInitialState.h"
#include "RaftSimLiquidParticleIdentity.h"
#include "NiagaraComponent.h"
#include "NiagaraDataInterfaceArrayFloat.h"
#include "NiagaraDataInterfaceArrayInt.h"
#include "UObject/UnrealType.h"
#include "UObject/UObjectIterator.h"

namespace RaftSimLiquidRegionalState
{
namespace
{
bool Number(const TSharedPtr<FJsonValue>& Value,double& Out)
{ return Value.IsValid() && Value->TryGetNumber(Out) && FMath::IsFinite(Out); }
bool Number(const TSharedPtr<FJsonObject>& J,const TCHAR* Name,double& Out)
{ return J.IsValid() && J->TryGetNumberField(Name,Out) && FMath::IsFinite(Out); }
bool Vector(const TSharedPtr<FJsonValue>& Value,FVector& Out,int32 Size=3)
{
    const TArray<TSharedPtr<FJsonValue>>* A=nullptr;Out=FVector::ZeroVector;
    if (!Value.IsValid() || !Value->TryGetArray(A) || A->Num()!=Size) return false;
    for (int32 I=0;I<Size;++I)
        if (!Number((*A)[I],Out[I]) || !FMath::IsFinite(float(Out[I]))) return false;
    return true;
}
bool Vector(const TSharedPtr<FJsonObject>& J,const TCHAR* Name,FVector& Out,int32 Size=3)
{ return J.IsValid() && Vector(J->TryGetField(Name),Out,Size); }
bool Integer(double V,int32 Min,int32 Max)
{ return FMath::IsFinite(V) && V>=Min && V<=Max && FMath::FloorToDouble(V)==V; }
bool Counts(FVector V,FIntVector& Out,int32 Min=2,int32 Max=4096)
{
    for (int32 A=0;A<3;++A) if (!Integer(V[A],Min,Max)) return false;
    Out=FIntVector(int32(V.X),int32(V.Y),int32(V.Z));return true;
}
bool Text(const TSharedPtr<FJsonObject>& J,const TCHAR* Name,const TCHAR* Expected)
{ FString V;return J.IsValid() && J->TryGetStringField(Name,V) && V==Expected; }
bool False(const TSharedPtr<FJsonObject>& J,const TCHAR* Name)
{ bool V;return J.IsValid() && J->TryGetBoolField(Name,V) && !V; }
bool Axes(const FCanonicalFrame& Frame)
{
    return FMath::IsNearlyEqual(Frame.AxisX.SizeSquared(),1.,1e-9) &&
        FMath::IsNearlyEqual(Frame.AxisY.SizeSquared(),1.,1e-9) &&
        FMath::IsNearlyZero(FVector::DotProduct(Frame.AxisX,Frame.AxisY),1e-9) &&
        Frame.AxisX.Z==0 && Frame.AxisY.Z==0 && FVector::CrossProduct(Frame.AxisX,Frame.AxisY).Z>0;
}
bool Rows(const TSharedPtr<FJsonObject>& J,const TCHAR* Name,TArray<FVector>& Out,int32 Count)
{
    const TArray<TSharedPtr<FJsonValue>>* A=nullptr;
    if (!J->TryGetArrayField(Name,A) || A->Num()!=Count) return false;
    Out.Reserve(Count);
    for (const auto& V:*A) { FVector P;if (!Vector(V,P)) return false;Out.Add(P); }
    return true;
}
bool Ids(const TSharedPtr<FJsonObject>& J,const TCHAR* Name,TArray<int32>& Out,int32 ParentCount,int32 Limit)
{
    const TArray<TSharedPtr<FJsonValue>>* A=nullptr;
    if (!J->TryGetArrayField(Name,A) || A->Num()>Limit) return false;
    TSet<int32> Unique;Out.Reserve(A->Num());
    for (const auto& V:*A)
    {
        double N;if (!Number(V,N) || !Integer(N,0,ParentCount-1) || Unique.Contains(int32(N))) return false;
        Unique.Add(int32(N));Out.Add(int32(N));
    }
    return true;
}
bool Bounds(const TSharedPtr<FJsonObject>& J,const TCHAR* Name,FVector& Low,FVector& High)
{
    const TArray<TSharedPtr<FJsonValue>>* A=nullptr;
    return J->TryGetArrayField(Name,A) && A->Num()==2 && Vector((*A)[0],Low,2) && Vector((*A)[1],High,2);
}
}

bool DecodeParent(const TSharedPtr<FJsonObject>& Manifest,const TSharedPtr<FJsonObject>& Boundary,FParent& Out,FString& Error)
{
    Out=FParent();Error=TEXT("Invalid regional parent domain/frame");FParent P;
    const TSharedPtr<FJsonObject>* Domain=nullptr;
    const TArray<TSharedPtr<FJsonValue>>* Rows=nullptr;
    if (!Text(Manifest,TEXT("schema"),TEXT("raftsim.regional_liquid_ownership.v1")) ||
        !Text(Boundary,TEXT("schema"),TEXT("raftsim.liquid_grid_boundary.v3")) ||
        !Manifest->TryGetObjectField(TEXT("domain"),Domain) || !Boundary->TryGetArrayField(TEXT("packed_vectors"),Rows) || Rows->Num()<8) return false;
    FVector Header[8];for (int32 I=0;I<8;++I) if (!Vector((*Rows)[I],Header[I])) return false;
    P.Frame.AxisX=Header[0];P.Frame.AxisY=Header[1];P.Frame.Origin=Header[2];
    FVector C,Spacing,Low,High,Physical,Center;double Seeds,Sources;
    if (!Axes(P.Frame) || !Vector(*Domain,TEXT("physical_cells"),C) || !Counts(C,P.Cells) || P.Cells.X%2 ||
        !Vector(*Domain,TEXT("cell_size_m"),Spacing) || Spacing.GetMin()<=0 ||
        !Bounds(*Domain,TEXT("native_face_bounds_m"),Low,High) ||
        !Vector(*Domain,TEXT("physical_extents_m"),Physical) ||
        !Vector(*Domain,TEXT("centre_station_lateral_m"),Center,2) ||
        !Number(Manifest,TEXT("particle_count"),Seeds) || !Integer(Seeds,0,5000000) ||
        !Number(Manifest,TEXT("source_count"),Sources) || !Integer(Sources,0,1000000) ||
        !Number(*Domain,TEXT("nominal_particle_volume_m3"),P.ParticleVolume) || P.ParticleVolume<=0 ||
        !Number(Manifest,TEXT("external_inflow_m3_per_s"),P.Inflow) || P.Inflow<0) return false;
    P.Spacing=Spacing*100;P.Lower=FVector2D(Low.X,Low.Y);P.Seeds=int32(Seeds);P.Sources=int32(Sources);
    const FVector Computation=C+FVector(4,4,0),ExpectedCenter=(Low+High)*.5;
    if (!Center.Equals(ExpectedCenter,1e-9) ||
        !FMath::IsNearlyEqual(High.X-Low.X,Physical.X,1e-9) || !FMath::IsNearlyEqual(High.Y-Low.Y,Physical.Y,1e-9) ||
        !Physical.Equals(C*Spacing,1e-9) || !FMath::IsNearlyEqual(P.ParticleVolume,Spacing.X*Spacing.Y*Spacing.Z/4,1e-12) ||
        !Header[3].Equals(Physical*100,1e-7) || !Header[4].Equals(P.Spacing,1e-7) ||
        !Header[5].Equals(C,0) || !Header[6].Equals(Computation,0) || !Header[7].Equals(Computation*P.Spacing,1e-7) ||
        !FMath::IsNearlyEqual(P.Frame.Origin.X,(Center.X*P.Frame.AxisX.X+Center.Y*P.Frame.AxisY.X)*100,1e-7) ||
        !FMath::IsNearlyEqual(P.Frame.Origin.Y,(Center.X*P.Frame.AxisX.Y+Center.Y*P.Frame.AxisY.Y)*100,1e-7)) return false;
    Out=MoveTemp(P);Error.Reset();return true;
}

bool Decode(const TSharedPtr<FJsonObject>& Json,const FParent& Parent,FState& Out,FString& Error)
{
    Out=FState();Error=TEXT("Invalid regional liquid state; no arrays installed");FState S;
    double Id;FVector C,Comp,Extent,Low,High,First,End;
    if (!Text(Json,TEXT("schema"),TEXT("raftsim.regional_liquid_state.v1")) ||
        !Text(Json,TEXT("canonical_frame"),TEXT("parent-ENU-centimetres")) || !False(Json,TEXT("internal_source_emission")) ||
        !Number(Json,TEXT("id"),Id) || !Integer(Id,0,4095) ||
        !Vector(Json,TEXT("origin_canonical_cm"),S.Frame.Origin) ||
        !Vector(Json,TEXT("axis_x_canonical"),S.Frame.AxisX,2) || !Vector(Json,TEXT("axis_y_canonical"),S.Frame.AxisY,2) ||
        !S.Frame.AxisX.Equals(Parent.Frame.AxisX,1e-12) || !S.Frame.AxisY.Equals(Parent.Frame.AxisY,1e-12) ||
        !Vector(Json,TEXT("physical_cells"),C) || !Counts(C,S.Cells) || S.Cells.X%2 ||
        !Vector(Json,TEXT("computational_cells"),Comp) || !Counts(Comp,S.ComputationalCells) ||
        !Vector(Json,TEXT("computational_extents_m"),Extent) ||
        !Bounds(Json,TEXT("cell_bounds_xy"),First,End) || !Bounds(Json,TEXT("bounds_station_lateral_m"),Low,High)) return false;
    if (S.Cells.Z!=Parent.Cells.Z || Comp!=C+FVector(4,4,0) ||
        int64(S.ComputationalCells.X)*S.ComputationalCells.Y*S.ComputationalCells.Z*8>2000000) return false;
    for (int32 A=0;A<2;++A)
        if (!Integer(First[A],0,Parent.Cells[A]-2) || !Integer(End[A],2,Parent.Cells[A]) ||
            End[A]-First[A]!=C[A] ||
            !FMath::IsNearlyEqual(Low[A],Parent.Lower[A]+First[A]*Parent.Spacing[A]/100,1e-9) ||
            !FMath::IsNearlyEqual(High[A],Parent.Lower[A]+End[A]*Parent.Spacing[A]/100,1e-9)) return false;
    S.Id=int32(Id);S.FirstCell=FIntPoint(int32(First.X),int32(First.Y));S.Extent=Extent*100;
    const FVector Center=(Low+High)*.5,ExpectedOrigin=Parent.Frame.AxisX*(Center.X*100)+Parent.Frame.AxisY*(Center.Y*100)+FVector(0,0,Parent.Frame.Origin.Z);
    if (!S.Extent.Equals(Comp*Parent.Spacing,1e-7) || !S.Frame.Origin.Equals(ExpectedOrigin,1e-7) ||
        !Number(Json,TEXT("nominal_particle_volume_m3"),S.ParticleVolume) || S.ParticleVolume!=Parent.ParticleVolume ||
        !Number(Json,TEXT("external_inflow_m3_per_s"),S.Inflow) || S.Inflow<0 ||
        !Number(Json,TEXT("external_spawn_particles_per_second"),S.SpawnRate) || S.SpawnRate<0 || S.SpawnRate>100000 ||
        !Ids(Json,TEXT("seed_parent_ids"),S.SeedIds,Parent.Seeds,163840) ||
        !Ids(Json,TEXT("source_parent_ids"),S.SourceIds,Parent.Sources,65536) ||
        !Rows(Json,TEXT("positions_canonical_cm"),S.Positions,S.SeedIds.Num()) ||
        !Rows(Json,TEXT("velocities_canonical_cm_per_s"),S.Velocities,S.SeedIds.Num()) ||
        !Rows(Json,TEXT("source_positions_canonical_cm"),S.SourcePositions,S.SourceIds.Num()) ||
        !Rows(Json,TEXT("source_velocities_canonical_cm_per_s"),S.SourceVelocities,S.SourceIds.Num())) return false;
    const TArray<TSharedPtr<FJsonValue>>* Weights=nullptr;
    if (!Json->TryGetArrayField(TEXT("source_weights_m3_per_s"),Weights) || Weights->Num()!=S.SourceIds.Num()) return false;
    double Total=0;
    for (const auto& V:*Weights)
    {
        double W;if (!Number(V,W) || W<=0 || !FMath::IsFinite(float(W)) || float(W)<UE_SMALL_NUMBER) return false;
        S.SourceWeights.Add(W);Total+=W;
    }
    if (!FMath::IsNearlyEqual(Total,S.Inflow,1e-9) || !FMath::IsNearlyEqual(Total/S.ParticleVolume,S.SpawnRate,1e-7)) return false;
    for (const auto* Positions:{&S.Positions,&S.SourcePositions}) for (const FVector& P:*Positions)
    {
        if (P.Z<=S.Frame.Origin.Z || P.Z>=S.Frame.Origin.Z+Parent.Cells.Z*Parent.Spacing.Z) return false;
        const FVector SL(FVector::DotProduct(P,S.Frame.AxisX)/100,FVector::DotProduct(P,S.Frame.AxisY)/100,0);
        for (int32 A=0;A<2;++A)
            if (SL[A]<Low[A] || (SL[A]>=High[A] && !(End[A]==Parent.Cells[A] && SL[A]==High[A]))) return false;
    }
    Out=MoveTemp(S);Error.Reset();return true;
}

bool ValidateOwnership(const FParent& Parent,const TArray<FState>& Regions,FString& Error)
{
    Error=TEXT("Missing or duplicate region/seed/source/cell ownership");
    if (Parent.Cells.GetMin()<2 || Parent.Seeds<0 || Parent.Sources<0 || Regions.IsEmpty() || Regions.Num()>4096) return false;
    TBitArray<> Seed(false,Parent.Seeds),Source(false,Parent.Sources),Cell(false,Parent.Cells.X*Parent.Cells.Y);
    TSet<int32> RegionIds;double Q=0;
    for (const auto& R:Regions)
    {
        if (R.Id<0 || RegionIds.Contains(R.Id)) return false;RegionIds.Add(R.Id);Q+=R.Inflow;
        if (R.FirstCell.X<0 || R.FirstCell.Y<0 || R.Cells.X<2 || R.Cells.Y<2 || R.FirstCell.X+R.Cells.X>Parent.Cells.X || R.FirstCell.Y+R.Cells.Y>Parent.Cells.Y) return false;
        for (int32 Y=R.FirstCell.Y;Y<R.FirstCell.Y+R.Cells.Y;++Y) for (int32 X=R.FirstCell.X;X<R.FirstCell.X+R.Cells.X;++X)
        { const int32 Index=Y*Parent.Cells.X+X;if (Cell[Index]) return false;Cell[Index]=true; }
        for (int32 Id:R.SeedIds) { if (Id<0 || Id>=Seed.Num() || Seed[Id]) return false;Seed[Id]=true; }
        for (int32 Id:R.SourceIds) { if (Id<0 || Id>=Source.Num() || Source[Id]) return false;Source[Id]=true; }
    }
    if (Seed.CountSetBits()!=Seed.Num() || Source.CountSetBits()!=Source.Num() || Cell.CountSetBits()!=Cell.Num() || !FMath::IsNearlyEqual(Q,Parent.Inflow,1e-9)) return false;
    Error.Reset();return true;
}

bool InstallArrays(UNiagaraSystem* System,const FState& State,FString& Error)
{
    Error=TEXT("Regional arrays require an unused transient system and validated state");
    if (!System || System->GetOutermost()!=GetTransientPackage() || State.Id<0 || !Axes(State.Frame) ||
        State.Positions.Num()!=State.SeedIds.Num() || State.Velocities.Num()!=State.SeedIds.Num() || State.SeedIds.Num()>163840 ||
        State.SourcePositions.Num()!=State.SourceIds.Num() || State.SourceVelocities.Num()!=State.SourceIds.Num() || State.SourceWeights.Num()!=State.SourceIds.Num()) return false;
    for (TObjectIterator<UNiagaraComponent> It;It;++It) if (It->GetAsset()==System) return false; // Never reset live regional water.
    auto* Class=LoadClass<UNiagaraDataInterface>(nullptr,TEXT("/Script/Niagara.NiagaraDataInterfaceArrayDistributionInt"));
    auto* A=Class?FindFProperty<FArrayProperty>(Class,TEXT("ArrayData")):nullptr;
    auto* Entry=A?CastField<FStructProperty>(A->Inner):nullptr;
    auto* Value=Entry?FindFProperty<FIntProperty>(Entry->Struct,TEXT("Value")):nullptr;
    auto* Weight=Entry?FindFProperty<FFloatProperty>(Entry->Struct,TEXT("Weight")):nullptr;
    if (!Value || !Weight || !RaftSimInstallLiquidGridAllocation(System,State.ComputationalCells,FVector3f(State.Extent),Error)) return false;
    auto& Store=System->GetExposedParameters();
    const auto AddVectors=[&](const TCHAR* Name,const TArray<FVector>& V,bool Offset)
    {
        auto* Array=NewObject<UNiagaraDataInterfaceArrayFloat3>(System);
        for (FVector P:V)
        {
            const FVector World=Offset?State.Frame.WorldSourceOffset(P):FCanonicalFrame::WorldVector(P);
            Array->FloatData.Add(World);Array->InternalFloatData.Add(FVector3f(World));
        }
        const FNiagaraVariable Variable(FNiagaraTypeDefinition(Array->GetClass()),Name);
        Store.AddParameter(Variable);Store.SetDataInterface(Array,Variable);
    };
    AddVectors(TEXT("User.River Initial Positions"),State.Positions,false);
    AddVectors(TEXT("User.River Initial Velocities"),State.Velocities,false);
    AddVectors(TEXT("User.River Source Positions"),State.SourcePositions,true);
    AddVectors(TEXT("User.River Source Velocities"),State.SourceVelocities,false);
    const auto AddIds=[&](const TCHAR* Name,const TArray<int32>& Ids)
    {
        auto* Array=NewObject<UNiagaraDataInterfaceArrayInt32>(System);Array->IntData=Ids;
        const FNiagaraVariable Variable(FNiagaraTypeDefinition(Array->GetClass()),Name);
        Store.AddParameter(Variable);Store.SetDataInterface(Array,Variable);
    };
    AddIds(TEXT("User.River Initial Parent IDs"),State.SeedIds);AddIds(TEXT("User.River Source Parent IDs"),State.SourceIds);
    auto* Distribution=NewObject<UNiagaraDataInterface>(System,Class);
    FScriptArrayHelper Entries(A,A->ContainerPtrToValuePtr<void>(Distribution));Entries.Resize(State.SourceWeights.Num());
    for (int32 I=0;I<Entries.Num();++I)
    { Value->SetPropertyValue_InContainer(Entries.GetRawPtr(I),I);Weight->SetPropertyValue_InContainer(Entries.GetRawPtr(I),float(State.SourceWeights[I])); }
    FPropertyChangedEvent Changed(A);Distribution->PostEditChangeProperty(Changed);
    const FNiagaraVariable DistributionVariable(FNiagaraTypeDefinition(Class),TEXT("User.River Source Distribution"));
    Store.AddParameter(DistributionVariable);Store.SetDataInterface(Distribution,DistributionVariable);
    const auto Float=[&](const TCHAR* Name,float V)
    { const FNiagaraVariable Variable(FNiagaraTypeDefinition::GetFloatDef(),Name);Store.AddParameter(Variable);Store.SetParameterValue<float>(V,Variable); };
    Float(TEXT("User.Inlet Particle Rate"),float(State.SpawnRate));
    Float(TEXT("User.River Nominal Particle Volume M3"),float(State.ParticleVolume));
    const FNiagaraVariable Origin(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.River Region World Origin"));
    Store.AddParameter(Origin);Store.SetParameterValue<FVector3f>(FVector3f(FCanonicalFrame::WorldPosition(State.Frame.Origin)),Origin);
    TSet<UNiagaraGraph*> Graphs;
    for (const auto& Handle:System->GetEmitterHandles())
        if (Handle.GetName().ToString().Contains(TEXT("FluidControl")))
            if (auto* Data=Handle.GetInstance().GetEmitterData())
            {
                TArray<UNiagaraScript*> Scripts;Data->GetScripts(Scripts,false);
                for (auto* Script:Scripts) if (auto* Source=Cast<UNiagaraScriptSource>(Script->GetLatestSource())) Graphs.Add(Source->NodeGraph);
            }
    if (!RaftSimInstallLiquidInitialBurstCount(System,Graphs,State.SeedIds.Num()) ||
        !RaftSimInstallLiquidInitialStateReader(System,Graphs,true)) { Error=TEXT("Regional initial burst/reader installation failed");return false; }
    if (!RaftSimInstallLiquidParticleIdentity(System,Graphs,State.Id,Error)) return false;
    Error.Reset();return true;
}
}
