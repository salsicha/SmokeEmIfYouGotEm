#include "Misc/AutomationTest.h"
#include "RaftSimSupportBandLayout.h"
#include "Serialization/MemoryReader.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "HAL/FileManager.h"
#include "Misc/Paths.h"
#include "Misc/ScopeExit.h"
#include <limits>

#if WITH_AUTOMATION_TESTS
namespace
{
// Exact virtual file extent and four count words; no allocation of a 700 MB
// fixture. Preflight must only read those words, never request array payloads.
class FBandExtentArchive final:public FArchive
{
public:
    int64 Position=24,Extent=0;int32 Reads=0;
    TMap<int64,int32> Words;
    FBandExtentArchive(int32 Width,int32 Rows)
    {
        SetIsLoading(true);
        const int64 Cells=int64(Width)*Rows;
        int64 At=24;
        const int32 Counts[]={Rows,int32(Cells),int32(Cells),int32(Cells)};
        const int32 Strides[]={4,4,4,1};
        for(int32 I=0;I<4;++I){Words.Add(At,Counts[I]);At+=4+int64(Counts[I])*Strides[I];}
        Extent=At;
    }
    virtual int64 Tell() override{return Position;}
    virtual int64 TotalSize() override{return Extent;}
    virtual void Seek(int64 At) override{if(At<0 || At>Extent)SetError();else Position=At;}
    virtual void Serialize(void* Data,int64 Count) override
    {
        const int32* Word=Words.Find(Position);
        if(Count!=4 || !Word || Position+4>Extent){SetError();return;}
        FMemory::Memcpy(Data,Word,4);Position+=4;++Reads;
    }
};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSupportBandLayoutTest,
    "RaftSim.Water.SupportBandAllocationPreflight",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimSupportBandLayoutTest::RunTest(const FString&)
{
    for(const FIntPoint Shape:{FIntPoint(2,2),FIntPoint(512,200000),FIntPoint(351,225158)})
    {
        FBandExtentArchive File(Shape.X,Shape.Y);
        TestTrue(TEXT("supported complete layout"),RaftSimSupportBandLayout::Preflight(File,Shape.X,Shape.Y,-350,2));
        TestEqual(TEXT("only four count words read"),File.Reads,4);
        TestEqual(TEXT("reset to native deserialization start"),File.Tell(),int64(24));
    }
    FBandExtentArchive TooLarge(512,200001);
    TestFalse(TEXT("original byte budget retained"),RaftSimSupportBandLayout::Preflight(TooLarge,512,200001,0,2));
    for(const FIntPoint Shape:{FIntPoint(MAX_int32,MAX_int32),FIntPoint(MIN_int32,MIN_int32),FIntPoint(512,MAX_int32)})
    {
        FBandExtentArchive File(2,2);
        TestFalse(TEXT("reject extreme dimensions without overflow"),RaftSimSupportBandLayout::Preflight(File,Shape.X,Shape.Y,0,2));
        TestEqual(TEXT("invalid dimensions do not read payload"),File.Reads,0);
    }
    for(int32 Delta:{-1,1})
    {
        FBandExtentArchive File(351,225158);File.Extent+=Delta;
        TestFalse(TEXT("reject truncated or trailing payload"),RaftSimSupportBandLayout::Preflight(File,351,225158,0,2));
        TestEqual(TEXT("no payload allocation/read"),File.Reads,0);
    }
    for(int32 Slot=0;Slot<4;++Slot)
    {
        FBandExtentArchive File(2,2);TArray<int64> Keys;File.Words.GetKeys(Keys);Keys.Sort();
        File.Words[Keys[Slot]]=MAX_int32;
        TestFalse(TEXT("reject malicious serialized count"),RaftSimSupportBandLayout::Preflight(File,2,2,0,2));
    }
    FBandExtentArchive InvalidSpacing(2,2),InvalidOrigin(2,2);
    TestFalse(TEXT("positive spacing required"),RaftSimSupportBandLayout::Preflight(InvalidSpacing,2,2,0,0));
    TestFalse(TEXT("finite origin required"),RaftSimSupportBandLayout::Preflight(InvalidOrigin,2,2,std::numeric_limits<float>::infinity(),2));
    // Exercise a real native memory archive as well as the sparse extent fixture.
    TArray<uint8> Bytes;Bytes.SetNumZeroed(84);
    for(const TPair<int64,int32> Entry:FBandExtentArchive(2,2).Words)FMemory::Memcpy(Bytes.GetData()+Entry.Key,&Entry.Value,4);
    FMemoryReader Small(Bytes);Small.Seek(24);
    TestTrue(TEXT("native archive layout"),RaftSimSupportBandLayout::Preflight(Small,2,2,0,2));
    // Real production deserialization past the former 200000-row limit.
    // Two columns keep the fixture small; the full-width extent is checked above.
    const FString Path=FPaths::Combine(FPaths::ProjectSavedDir(),TEXT("Automation"),
        TEXT("long-support-band-")+FGuid::NewGuid().ToString()+TEXT(".bin"));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Path),true);
    ON_SCOPE_EXIT { IFileManager::Get().Delete(*Path); };
    {
        TUniquePtr<FArchive> Writer(IFileManager::Get().CreateFileWriter(*Path));
        if(!TestTrue(TEXT("long-band fixture writer"),Writer.IsValid()))return false;
        uint32 Magic=0x52534246u,Version=1;
        int32 Width=2,Rows=225158;
        float Origin=0.f,Spacing=2.f;
        TArray<float> Stations,Heights,Energy;TArray<uint8> Wet;
        Stations.SetNumUninitialized(Rows);
        for(int32 I=0;I<Rows;++I)Stations[I]=2.f*I;
        Heights.Init(700.f,Width*Rows);Energy.Init(.25f,Width*Rows);Wet.Init(1,Width*Rows);
        *Writer<<Magic<<Version<<Width<<Rows<<Origin<<Spacing;
        *Writer<<Stations<<Heights<<Energy<<Wet;
    }
    auto* Water=NewObject<URaftSimWaterRuntimeAdapter>();
    TestTrue(TEXT("long physical support loads"),Water->LoadRaftSupportBandFieldFromFile(Path));
    TestTrue(TEXT("long presentation baseline loads"),Water->LoadPresentationBaselineFieldFromFile(Path));
    TestTrue(TEXT("long observed whitewater loads"),Water->LoadObservedWhitewaterFieldFromFile(Path));
    FBox2D Bounds;
    TestTrue(TEXT("long baseline exposes coverage"),Water->GetCurvedPresentationBaselineBoundsM(Bounds));
    TestEqual(TEXT("last station remains accessible"),Bounds.Max.X,450314.);
    TestEqual(TEXT("whitewater samples beyond previous row limit"),
        Water->SampleObservedWhitewaterAtRiverCoordinates(FVector2D(450312.,1.)),.25f);
    return true;
}
#endif
