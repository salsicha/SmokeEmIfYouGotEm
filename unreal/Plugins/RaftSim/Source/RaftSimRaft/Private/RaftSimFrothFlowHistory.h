#pragma once
#include "CoreMinimal.h"
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

// Diagnostic input history, not rendered foam or a new water solver. Called
// only after a successful Advance, with its exact start/end simulation clocks.
// Remaps retain each interval's original registration; teleports explicitly reset.
struct FRaftSimFrothFlowHistory
{
    struct FInterval
    {
        double Start=0,End=0,SampleElapsed=0;
        FIntPoint Size;
        FVector2f Origin;
        float Cell=0;
        TArray<FVector4f> Flow;
    };
    TArray<FInterval> Intervals;
    void Reset() { Intervals.Reset(); }
    bool Append(double Start,double End,double SampleElapsed,FIntPoint Size,
        FVector2f Origin,float Cell,const TArray<FVector4f>& Flow)
    {
        if(!FMath::IsFinite(Start) || !FMath::IsFinite(End) || Start<0 || End<=Start ||
            !FMath::IsFinite(SampleElapsed) || SampleElapsed<0 || Origin.ContainsNaN() ||
            !FMath::IsFinite(Cell) || Cell<=0 || Size.X<2 || Size.Y<2 ||
            int64(Size.X)*Size.Y!=Flow.Num())return false;
        if(!Intervals.IsEmpty() && Start!=Intervals.Last().End)return false;
        for(const auto& F:Flow)if(F.ContainsNaN() || F.X<0)return false;
        if(!Intervals.IsEmpty() && Intervals.Last().Size==Size &&
            Intervals.Last().Origin==Origin && Intervals.Last().Cell==Cell &&
            Intervals.Last().SampleElapsed==SampleElapsed && Intervals.Last().Flow==Flow)
            Intervals.Last().End=End;
        else
        {
            auto& I=Intervals.AddDefaulted_GetRef();I.Start=Start;I.End=End;
            I.SampleElapsed=SampleElapsed;I.Size=Size;I.Origin=Origin;I.Cell=Cell;I.Flow=Flow;
        }
        // Keep a complete interval crossing the 1.25-second retention boundary.
        while(Intervals.Num()>1 && Intervals[0].End<=End-1.25)
            Intervals.RemoveAt(0,1,EAllowShrinking::No);
        return true;
    }
    bool Save(const FString& Prefix) const
    {
        if(Intervals.IsEmpty())return false;
        const FString IndexPath=Prefix+TEXT(".history.json");
        if(FPaths::FileExists(IndexPath))return false;
        for(int32 N=0;N<Intervals.Num();++N)
            if(FPaths::FileExists(FString::Printf(TEXT("%s.history-%03d.f32"),*Prefix,N)))return false;
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(Prefix),true);
        TArray<TSharedPtr<FJsonValue>> Records;
        for(int32 N=0;N<Intervals.Num();++N)
        {
            const auto& I=Intervals[N];
            const FString Path=FString::Printf(TEXT("%s.history-%03d.f32"),*Prefix,N);
            TUniquePtr<FArchive> File(IFileManager::Get().CreateFileWriter(*Path,FILEWRITE_NoReplaceExisting));
            if(!File)return false;
            File->Serialize(const_cast<FVector4f*>(I.Flow.GetData()),int64(I.Flow.Num())*sizeof(FVector4f));
            const bool bGood=!File->IsError();if(!File->Close() || !bGood)return false;
            auto R=MakeShared<FJsonObject>();R->SetStringField(TEXT("file"),FPaths::GetCleanFilename(Path));
            R->SetNumberField(TEXT("start_s"),I.Start);R->SetNumberField(TEXT("end_s"),I.End);
            R->SetNumberField(TEXT("mean_sample_elapsed_s"),I.SampleElapsed);
            R->SetNumberField(TEXT("cell_m"),I.Cell);
            R->SetArrayField(TEXT("origin_m"),{MakeShared<FJsonValueNumber>(I.Origin.X),MakeShared<FJsonValueNumber>(I.Origin.Y)});
            R->SetArrayField(TEXT("shape"),{MakeShared<FJsonValueNumber>(I.Size.Y),MakeShared<FJsonValueNumber>(I.Size.X),MakeShared<FJsonValueNumber>(4)});
            Records.Add(MakeShared<FJsonValueObject>(R));
        }
        auto Root=MakeShared<FJsonObject>();Root->SetStringField(TEXT("schema"),TEXT("raftsim.froth_flow_history.v1"));
        Root->SetStringField(TEXT("dtype"),TEXT("little-endian float32"));
        Root->SetBoolField(TEXT("arrays_complete"),true);Root->SetBoolField(TEXT("visual_accepted"),false);
        Root->SetNumberField(TEXT("retention_seconds"),1.25);Root->SetArrayField(TEXT("intervals"),Records);
        FString Json;auto Writer=TJsonWriterFactory<>::Create(&Json);
        return FJsonSerializer::Serialize(Root,Writer) && FFileHelper::SaveStringToFile(Json,*IndexPath,
            FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM,&IFileManager::Get(),FILEWRITE_NoReplaceExisting);
    }
};
