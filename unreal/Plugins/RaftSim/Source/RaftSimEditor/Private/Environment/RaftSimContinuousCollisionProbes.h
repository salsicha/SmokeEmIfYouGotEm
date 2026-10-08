#pragma once
#include "CoreMinimal.h"
#include "HAL/FileManager.h"
#include "Serialization/Archive.h"
THIRD_PARTY_INCLUDES_START
#include <openssl/sha.h>
THIRD_PARTY_INCLUDES_END

// No river-sized byte array or FVector array. Probe files contain explicit
// little-endian IEEE754 triples, not native FVector layout/padding.
namespace RaftSimContinuousCollisionProbes
{
inline FString Hash(const FString& Path)
{
    TUniquePtr<FArchive> File(IFileManager::Get().CreateFileReader(*Path));
    if(!File)return {};
    SHA256_CTX Context;SHA256_Init(&Context);
    TArray<uint8> Buffer;Buffer.SetNumUninitialized(65536);
    while(File->Tell()<File->TotalSize())
    {
        const int64 Count=FMath::Min<int64>(Buffer.Num(),File->TotalSize()-File->Tell());
        File->Serialize(Buffer.GetData(),Count);
        if(File->IsError())return {};
        SHA256_Update(&Context,Buffer.GetData(),Count);
    }
    uint8 Digest[SHA256_DIGEST_LENGTH];SHA256_Final(Digest,&Context);
    return BytesToHex(Digest,SHA256_DIGEST_LENGTH).ToLower();
}

inline bool Visit(FArchive& File,int64 Count,TFunctionRef<bool(const FVector&)> Visitor,FString& Error)
{
    if(Count<=0 || Count>MAX_int32 || File.TotalSize()!=Count*24 || File.Tell()!=0)
    {Error=TEXT("Invalid wet-bed probe byte/count extent");return false;}
    uint8 Bytes[24];
    for(int64 I=0;I<Count;++I)
    {
        File.Serialize(Bytes,24);
        if(File.IsError()){Error=TEXT("Truncated wet-bed probe file");return false;}
        double XYZ[3];
        for(int32 Axis=0;Axis<3;++Axis)
        {
            uint64 Bits=0;
            for(int32 Byte=0;Byte<8;++Byte)Bits|=uint64(Bytes[Axis*8+Byte])<<(Byte*8);
            FMemory::Memcpy(&XYZ[Axis],&Bits,8);
        }
        const FVector P(XYZ[0],XYZ[1],XYZ[2]);
        if(P.ContainsNaN() || FMath::Abs(P.X)>1.e9 || FMath::Abs(P.Y)>1.e9)
        {Error=TEXT("Nonfinite or out-of-bounds wet-bed probe");return false;}
        if(!Visitor(P))return false;
    }
    return !File.IsError();
}

inline bool VisitFile(const FString& Path,int64 Count,const FString& Digest,
    TFunctionRef<bool(const FVector&)> Visitor,FString& Error)
{
    if(Digest.Len()!=64 || !Hash(Path).Equals(Digest,ESearchCase::IgnoreCase))
    {Error=TEXT("Changed chunk-owned wet-bed collision probes");return false;}
    TUniquePtr<FArchive> File(IFileManager::Get().CreateFileReader(*Path));
    if(!File){Error=TEXT("Missing wet-bed probe file");return false;}
    return Visit(*File,Count,Visitor,Error);
}
}
