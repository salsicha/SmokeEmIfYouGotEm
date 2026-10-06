#pragma once
#include "CoreMinimal.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"

// Lossless bounded diagnostic storage. Templates contain the complete observed
// participant records, including births/reset/iteration and generation. Never
// substitute an expected schedule for an observed one. Only frame/group vary
// outside the template. A full journal fails closed rather than dropping steps.
struct FRaftSimLiquidStageJournal
{
    static constexpr int32 MaxRecords=262144,MaxTemplates=4096,MaxTemplateChars=8*1024*1024;
    struct FRecord { uint32 Frame,Group,Template; };
    TArray<FRecord> Records;
    TArray<TSharedPtr<FJsonValue>> Templates;
    TMap<FString,uint32> Indices;
    int32 TemplateChars=0;
    bool Failed=false;

    bool Add(uint32 Frame,uint32 Group,const TSharedPtr<FJsonObject>& Observed)
    {
        if(Failed || Records.Num()>=MaxRecords) { Failed=true;return false; }
        FString Key;
        if(!FJsonSerializer::Serialize(Observed,TJsonWriterFactory<TCHAR,TCondensedJsonPrintPolicy<TCHAR>>::Create(&Key)))
        { Failed=true;return false; }
        const uint32* Existing=Indices.Find(Key);uint32 Index;
        if(Existing) Index=*Existing;
        else
        {
            if(Templates.Num()>=MaxTemplates || Key.Len()>MaxTemplateChars-TemplateChars)
            { Failed=true;return false; }
            Index=Templates.Num();TemplateChars+=Key.Len();Indices.Add(MoveTemp(Key),Index);
            Templates.Add(MakeShared<FJsonValueObject>(Observed));
        }
        Records.Add({Frame,Group,Index});return true;
    }
    TSharedPtr<FJsonObject> Json() const
    {
        auto J=MakeShared<FJsonObject>();J->SetStringField(TEXT("schema"),TEXT("raftsim.liquid_stage_journal.v1"));
        J->SetBoolField(TEXT("failed"),Failed);J->SetNumberField(TEXT("record_count"),Records.Num());
        J->SetNumberField(TEXT("template_chars"),TemplateChars);J->SetArrayField(TEXT("templates"),Templates);
        TArray<TSharedPtr<FJsonValue>> Rows;Rows.Reserve(Records.Num());
        for(const auto& R:Records)
        {
            TArray<TSharedPtr<FJsonValue>> Row;
            for(uint32 V:{R.Frame,R.Group,R.Template}) Row.Add(MakeShared<FJsonValueNumber>(V));
            Rows.Add(MakeShared<FJsonValueArray>(Row));
        }
        J->SetArrayField(TEXT("records"),Rows);return J;
    }
};
