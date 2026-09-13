#include "RaftSimLiveWaterWindow.h"

#if RAFTSIM_HAS_LIVE_SOLVER

#include "Dom/JsonObject.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/ScopeLock.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

#include "raftsim_water/scenario.hpp"
#include "raftsim_water/solver.hpp"

namespace
{
// Clamp gameplay ticks so a hitch cannot explode the CFL substep count.
constexpr float kMaxStepSeconds = 0.1f;

// Minimum window span: the order-2 MUSCL stencil plus boundary columns need
// a few interior cells to be meaningful.
constexpr int32 kMinWindowCells = 8;

// ---------------------------------------------------------------------------
// SHA-256 (FIPS 180-4) for cooked-artifact hash verification. UE's
// FGenericPlatformMisc::GetSHA256Signature is unimplemented on Mac, so the
// loader carries its own compact implementation (validated against shasum).
// ---------------------------------------------------------------------------

uint32 Sha256RotR(uint32 Value, uint32 Bits)
{
    return (Value >> Bits) | (Value << (32u - Bits));
}

FString Sha256HexOf(const TArray<uint8>& Data)
{
    static const uint32 K[64] = {
        0x428a2f98u, 0x71374491u, 0xb5c0fbcfu, 0xe9b5dba5u, 0x3956c25bu, 0x59f111f1u,
        0x923f82a4u, 0xab1c5ed5u, 0xd807aa98u, 0x12835b01u, 0x243185beu, 0x550c7dc3u,
        0x72be5d74u, 0x80deb1feu, 0x9bdc06a7u, 0xc19bf174u, 0xe49b69c1u, 0xefbe4786u,
        0x0fc19dc6u, 0x240ca1ccu, 0x2de92c6fu, 0x4a7484aau, 0x5cb0a9dcu, 0x76f988dau,
        0x983e5152u, 0xa831c66du, 0xb00327c8u, 0xbf597fc7u, 0xc6e00bf3u, 0xd5a79147u,
        0x06ca6351u, 0x14292967u, 0x27b70a85u, 0x2e1b2138u, 0x4d2c6dfcu, 0x53380d13u,
        0x650a7354u, 0x766a0abbu, 0x81c2c92eu, 0x92722c85u, 0xa2bfe8a1u, 0xa81a664bu,
        0xc24b8b70u, 0xc76c51a3u, 0xd192e819u, 0xd6990624u, 0xf40e3585u, 0x106aa070u,
        0x19a4c116u, 0x1e376c08u, 0x2748774cu, 0x34b0bcb5u, 0x391c0cb3u, 0x4ed8aa4au,
        0x5b9cca4fu, 0x682e6ff3u, 0x748f82eeu, 0x78a5636fu, 0x84c87814u, 0x8cc70208u,
        0x90befffau, 0xa4506cebu, 0xbef9a3f7u, 0xc67178f2u};

    uint32 H[8] = {
        0x6a09e667u, 0xbb67ae85u, 0x3c6ef372u, 0xa54ff53au,
        0x510e527fu, 0x9b05688cu, 0x1f83d9abu, 0x5be0cd19u};

    TArray<uint8> Padded = Data;
    Padded.Add(0x80u);
    while (Padded.Num() % 64 != 56)
    {
        Padded.Add(0u);
    }
    const uint64 BitLength = static_cast<uint64>(Data.Num()) * 8u;
    for (int32 Shift = 56; Shift >= 0; Shift -= 8)
    {
        Padded.Add(static_cast<uint8>(BitLength >> Shift));
    }

    for (int32 Chunk = 0; Chunk < Padded.Num(); Chunk += 64)
    {
        uint32 W[64];
        for (int32 i = 0; i < 16; ++i)
        {
            const uint8* P = &Padded[Chunk + i * 4];
            W[i] = (static_cast<uint32>(P[0]) << 24) | (static_cast<uint32>(P[1]) << 16) |
                   (static_cast<uint32>(P[2]) << 8) | static_cast<uint32>(P[3]);
        }
        for (int32 i = 16; i < 64; ++i)
        {
            const uint32 S0 = Sha256RotR(W[i - 15], 7) ^ Sha256RotR(W[i - 15], 18) ^ (W[i - 15] >> 3);
            const uint32 S1 = Sha256RotR(W[i - 2], 17) ^ Sha256RotR(W[i - 2], 19) ^ (W[i - 2] >> 10);
            W[i] = W[i - 16] + S0 + W[i - 7] + S1;
        }
        uint32 A = H[0], B = H[1], C = H[2], D = H[3];
        uint32 E = H[4], F = H[5], G = H[6], Hh = H[7];
        for (int32 i = 0; i < 64; ++i)
        {
            const uint32 S1 = Sha256RotR(E, 6) ^ Sha256RotR(E, 11) ^ Sha256RotR(E, 25);
            const uint32 Ch = (E & F) ^ (~E & G);
            const uint32 Temp1 = Hh + S1 + Ch + K[i] + W[i];
            const uint32 S0 = Sha256RotR(A, 2) ^ Sha256RotR(A, 13) ^ Sha256RotR(A, 22);
            const uint32 Maj = (A & B) ^ (A & C) ^ (B & C);
            const uint32 Temp2 = S0 + Maj;
            Hh = G;
            G = F;
            F = E;
            E = D + Temp1;
            D = C;
            C = B;
            B = A;
            A = Temp1 + Temp2;
        }
        H[0] += A; H[1] += B; H[2] += C; H[3] += D;
        H[4] += E; H[5] += F; H[6] += G; H[7] += Hh;
    }

    FString Hex;
    Hex.Reserve(64);
    for (int32 i = 0; i < 8; ++i)
    {
        Hex += FString::Printf(TEXT("%08x"), H[i]);
    }
    return Hex;
}

// ---------------------------------------------------------------------------
// Minimal .npy reader for the cooked-field dtypes: little-endian float32
// ('<f4'), float64 ('<f8'), and uint8 ('|u1' / bool '|b1'), 2-D C-order.
// physics/cpp numpy_io only reads f8/b1, so the cooked float32 arrays need
// this dedicated reader.
// ---------------------------------------------------------------------------

struct FNpyArray
{
    int64 Ny = 0;
    int64 Nx = 0;
    // Populated for f4/f8 payloads.
    TArray<double> Float64;
    // Populated for u1/b1 payloads.
    TArray<uint8> Bytes;
    bool bIsFloat = false;
    int32 ElementBytes = 0;
};

bool ParseNpy(const TArray<uint8>& FileBytes, FNpyArray& OutArray, FString& OutError)
{
    if (FileBytes.Num() < 12 || FMemory::Memcmp(FileBytes.GetData(), "\x93NUMPY", 6) != 0)
    {
        OutError = TEXT("invalid .npy magic");
        return false;
    }
    const uint8 Major = FileBytes[6];
    const int32 HeaderLenSize = Major <= 1 ? 2 : 4;
    int64 HeaderLen = 0;
    if (HeaderLenSize == 2)
    {
        HeaderLen = static_cast<int64>(FileBytes[8]) | (static_cast<int64>(FileBytes[9]) << 8);
    }
    else
    {
        HeaderLen = static_cast<int64>(FileBytes[8]) | (static_cast<int64>(FileBytes[9]) << 8) |
                    (static_cast<int64>(FileBytes[10]) << 16) | (static_cast<int64>(FileBytes[11]) << 24);
    }
    const int64 DataOffset = 8 + HeaderLenSize + HeaderLen;
    if (DataOffset > FileBytes.Num())
    {
        OutError = TEXT(".npy header exceeds file size");
        return false;
    }

    FString Header;
    Header.Reserve(HeaderLen);
    for (int64 i = 8 + HeaderLenSize; i < DataOffset; ++i)
    {
        Header.AppendChar(static_cast<TCHAR>(FileBytes[i]));
    }

    if (Header.Contains(TEXT("'fortran_order': True")))
    {
        OutError = TEXT("fortran-order .npy arrays are not supported");
        return false;
    }

    int32 ElementSize = 0;
    if (Header.Contains(TEXT("<f4")))
    {
        ElementSize = 4;
        OutArray.bIsFloat = true;
    }
    else if (Header.Contains(TEXT("<f8")))
    {
        ElementSize = 8;
        OutArray.bIsFloat = true;
    }
    else if (Header.Contains(TEXT("|u1")) || Header.Contains(TEXT("|b1")))
    {
        ElementSize = 1;
        OutArray.bIsFloat = false;
    }
    else
    {
        OutError = FString::Printf(TEXT("unsupported .npy dtype in header: %s"), *Header);
        return false;
    }

    // Shape tuple: "'shape': (ny, nx)".
    int32 ShapeKey = Header.Find(TEXT("'shape'"));
    if (ShapeKey == INDEX_NONE)
    {
        OutError = TEXT(".npy header missing shape");
        return false;
    }
    const int32 Open = Header.Find(TEXT("("), ESearchCase::CaseSensitive, ESearchDir::FromStart, ShapeKey);
    const int32 Close = Header.Find(TEXT(")"), ESearchCase::CaseSensitive, ESearchDir::FromStart, Open);
    if (Open == INDEX_NONE || Close == INDEX_NONE)
    {
        OutError = TEXT(".npy header shape tuple malformed");
        return false;
    }
    TArray<FString> Dims;
    Header.Mid(Open + 1, Close - Open - 1).ParseIntoArray(Dims, TEXT(","), true);
    for (FString& Dim : Dims)
    {
        Dim.TrimStartAndEndInline();
    }
    Dims.RemoveAll([](const FString& Dim) { return Dim.IsEmpty(); });
    if (Dims.Num() != 2)
    {
        OutError = TEXT("only 2-D .npy arrays are supported");
        return false;
    }
    OutArray.Ny = FCString::Atoi64(*Dims[0]);
    OutArray.Nx = FCString::Atoi64(*Dims[1]);
    if (OutArray.Ny <= 0 || OutArray.Nx <= 0)
    {
        OutError = TEXT(".npy shape must be non-empty");
        return false;
    }

    if (OutArray.Nx > MAX_int32 || OutArray.Ny > MAX_int32/OutArray.Nx)
    {
        OutError = TEXT(".npy shape exceeds supported array size");
        return false;
    }
    OutArray.ElementBytes = ElementSize;
    const int64 Count = OutArray.Ny * OutArray.Nx;
    if (FileBytes.Num() - DataOffset < Count * ElementSize)
    {
        OutError = TEXT(".npy payload truncated");
        return false;
    }

    const uint8* Payload = FileBytes.GetData() + DataOffset;
    if (ElementSize == 1)
    {
        OutArray.Bytes.SetNumUninitialized(Count);
        FMemory::Memcpy(OutArray.Bytes.GetData(), Payload, Count);
    }
    else
    {
        OutArray.Float64.SetNumUninitialized(Count);
        if (ElementSize == 4)
        {
            for (int64 i = 0; i < Count; ++i)
            {
                float Value;
                FMemory::Memcpy(&Value, Payload + i * 4, 4);
                OutArray.Float64[i] = static_cast<double>(Value);
            }
        }
        else
        {
            FMemory::Memcpy(OutArray.Float64.GetData(), Payload, Count * 8);
        }
    }
    return true;
}

bool LoadCookedArray(
    const FString& CookedFieldsDir,
    const TSharedPtr<FJsonObject>& ArrayMeta,
    const TCHAR* Name,
    FNpyArray& OutArray,
    FString& OutError)
{
    FString RelativeFile;
    FString ExpectedSha;
    if (!ArrayMeta->TryGetStringField(TEXT("file"), RelativeFile) ||
        !ArrayMeta->TryGetStringField(TEXT("sha256"), ExpectedSha))
    {
        OutError = FString::Printf(TEXT("manifest array '%s' is missing file/sha256"), Name);
        return false;
    }

    const FString FullPath = FPaths::Combine(CookedFieldsDir, RelativeFile);
    TArray<uint8> FileBytes;
    if (!FFileHelper::LoadFileToArray(FileBytes, *FullPath))
    {
        OutError = FString::Printf(TEXT("could not read cooked array %s"), *FullPath);
        return false;
    }

    const FString ActualSha = Sha256HexOf(FileBytes);
    if (!ActualSha.Equals(ExpectedSha, ESearchCase::IgnoreCase))
    {
        OutError = FString::Printf(
            TEXT("sha256 mismatch for %s: manifest %s, file %s"),
            *RelativeFile, *ExpectedSha, *ActualSha);
        return false;
    }

    if (!ParseNpy(FileBytes, OutArray, OutError))
    {
        OutError = FString::Printf(TEXT("%s: %s"), *RelativeFile, *OutError);
        return false;
    }

    // Cross-check the parsed shape against the manifest contract.
    const TArray<TSharedPtr<FJsonValue>>* ShapeValues = nullptr;
    if (ArrayMeta->TryGetArrayField(TEXT("shape"), ShapeValues) && ShapeValues->Num() == 2)
    {
        const int64 ManifestNy = static_cast<int64>((*ShapeValues)[0]->AsNumber());
        const int64 ManifestNx = static_cast<int64>((*ShapeValues)[1]->AsNumber());
        if (ManifestNy != OutArray.Ny || ManifestNx != OutArray.Nx)
        {
            OutError = FString::Printf(
                TEXT("%s: shape (%lld, %lld) does not match manifest (%lld, %lld)"),
                *RelativeFile, OutArray.Ny, OutArray.Nx, ManifestNy, ManifestNx);
            return false;
        }
    }
    return true;
}

struct FSharedCartesianAtlas
{
    FNpyArray Bed, H, U, V;
    TArray<FVector2D> Origins;
    TArray<FVector2D> PhysicalWetExteriorCells;
    TMap<FIntPoint, int32> TileLookup;
    int32 TileNx=0, TileNy=0;
    double Spacing=0., Datum=0., DryTolerance=0.;

    int32 CellIndex(int64 Column, int64 Row) const
    {
        const double KeyX = FMath::FloorToDouble(double(Column) / TileNx);
        const double KeyY = FMath::FloorToDouble(double(Row) / TileNy);
        if (FMath::Abs(KeyX) > 1.e8 || FMath::Abs(KeyY) > 1.e8) return INDEX_NONE;
        const FIntPoint Key{int32(KeyX), int32(KeyY)};
        const int32* Tile = TileLookup.Find(Key);
        if (!Tile) return INDEX_NONE;
        const int32 X = int32(Column - int64(Key.X)*TileNx);
        const int32 Y = int32(Row - int64(Key.Y)*TileNy);
        return (*Tile*TileNy + Y)*TileNx + X;
    }

    FRaftSimLiveWaterSampleResult Sample(const FVector2D& Position) const
    {
        FRaftSimLiveWaterSampleResult Result;
        const FVector2D Grid = (Position - Origins[0]) / Spacing;
        // The verified atlas permits at most 1e8 tiles of at most 4096 cells
        // from its origin. Reject nonfinite/overflowing queries before casts.
        if (Grid.ContainsNaN() || FMath::Abs(Grid.X) > 4.1e11 || FMath::Abs(Grid.Y) > 4.1e11)
            return Result;
        const int64 X = int64(FMath::FloorToDouble(Grid.X));
        const int64 Y = int64(FMath::FloorToDouble(Grid.Y));
        const double Fx = Grid.X-X, Fy = Grid.Y-Y;
        double BedValue = 0., Depth = 0., VelX = 0., VelY = 0.;
        for (int32 DY = 0; DY < 2; ++DY) for (int32 DX = 0; DX < 2; ++DX)
        {
            const double Weight = (DX ? Fx : 1.-Fx)*(DY ? Fy : 1.-Fy);
            if (Weight == 0.) continue;
            const int32 I = CellIndex(X+DX, Y+DY);
            // Interpolation may cross a real tile seam, but must never bridge
            // an unavailable hole or extrapolate past a physical river end.
            if (I == INDEX_NONE) return Result;
            BedValue += Weight*Bed.Float64[I]; Depth += Weight*H.Float64[I];
            VelX += Weight*U.Float64[I]; VelY += Weight*V.Float64[I];
        }
        Result.bValid = true;
        Result.DepthM = float(Depth);
        Result.BedHeightM = float(BedValue + Datum);
        Result.SurfaceHeightM = float(BedValue + Depth + Datum);
        Result.VelocityMps = FVector2D(float(VelX), float(VelY));
        Result.bWet = Depth > 1.e-4; // Same presentation wet threshold as the live sampler.
        const int32 Center = CellIndex(X, Y);
        const auto Surface = [this](int32 I) { return Bed.Float64[I] + H.Float64[I]; };
        const int32 L = CellIndex(X-1, Y), R = CellIndex(X+1, Y);
        const int32 D = CellIndex(X, Y-1), Up = CellIndex(X, Y+1);
        const auto Gradient = [&](int32 Before, int32 After)
        {
            if (Before != INDEX_NONE && After != INDEX_NONE)
                return (Surface(After)-Surface(Before))/(2.*Spacing);
            if (After != INDEX_NONE) return (Surface(After)-Surface(Center))/Spacing;
            if (Before != INDEX_NONE) return (Surface(Center)-Surface(Before))/Spacing;
            return 0.;
        };
        Result.SurfaceNormal = FVector(float(-Gradient(L,R)), float(-Gradient(D,Up)), 1.f).GetSafeNormal();
        return Result;
    }
};

FCriticalSection SharedAtlasMutex;
TSharedPtr<const FSharedCartesianAtlas,ESPMode::ThreadSafe> SharedAtlasCache;
FString SharedAtlasCacheKey;
int32 SharedAtlasLoadCount=0;

bool ReadFinitePair(const TSharedPtr<FJsonObject>& Object,const TCHAR* Name,FVector2D& Pair)
{
    const TArray<TSharedPtr<FJsonValue>>* Values=nullptr;
    return Object.IsValid() && Object->TryGetArrayField(Name,Values) && Values->Num()==2 &&
        (*Values)[0].IsValid() && (*Values)[1].IsValid() &&
        (*Values)[0]->TryGetNumber(Pair.X) && (*Values)[1]->TryGetNumber(Pair.Y) && !Pair.ContainsNaN();
}

TSharedPtr<const FSharedCartesianAtlas,ESPMode::ThreadSafe> LoadSharedCartesianAtlas(
    const FString& Directory,const TSharedPtr<FJsonObject>& Reference,FString& Error)
{
    Error=TEXT("invalid shared Cartesian state atlas");
    FString Relative,ExpectedHash;
    if (!Reference->TryGetStringField(TEXT("manifest"),Relative) ||
        !Reference->TryGetStringField(TEXT("sha256"),ExpectedHash) || ExpectedHash.Len()!=64) return nullptr;
    const FString Path=FPaths::ConvertRelativePathToFull(FPaths::Combine(Directory,Relative));
    const FString Key=Path+TEXT("|")+ExpectedHash.ToLower();
    FScopeLock Lock(&SharedAtlasMutex);
    // Keep one immutable verified atlas, not one copy per source window. A
    // changed digest/path requires a new load; failed loads never replace it.
    if (SharedAtlasCache.IsValid() && SharedAtlasCacheKey==Key) return SharedAtlasCache;
    TArray<uint8> Bytes;
    if (!FFileHelper::LoadFileToArray(Bytes,*Path) ||
        !Sha256HexOf(Bytes).Equals(ExpectedHash,ESearchCase::IgnoreCase)) return nullptr;
    FString Text;
    FFileHelper::BufferToString(Text,Bytes.GetData(),Bytes.Num());
    TSharedPtr<FJsonObject> Root;
    if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Root) || !Root.IsValid()) return nullptr;
    FString Schema;
    FVector2D Shape;
    const TArray<TSharedPtr<FJsonValue>>* Tiles=nullptr;
    const TArray<TSharedPtr<FJsonValue>>* Physical=nullptr;
    const TSharedPtr<FJsonObject>* Arrays=nullptr;
    auto Atlas=MakeShared<FSharedCartesianAtlas,ESPMode::ThreadSafe>();
    if (!Root->TryGetStringField(TEXT("schema"),Schema) || Schema!=TEXT("raftsim.cartesian_state_atlas.v1") ||
        !ReadFinitePair(Root,TEXT("tile_shape"),Shape) || Shape.X<2 || Shape.Y<2 ||
        Shape.X>4096 || Shape.Y>4096 || Shape.X!=FMath::FloorToDouble(Shape.X) || Shape.Y!=FMath::FloorToDouble(Shape.Y) ||
        !Root->TryGetNumberField(TEXT("grid_spacing_m"),Atlas->Spacing) || !FMath::IsFinite(Atlas->Spacing) || Atlas->Spacing<=0. ||
        !Root->TryGetNumberField(TEXT("source_elevation_datum_m"),Atlas->Datum) || !FMath::IsFinite(Atlas->Datum) ||
        !Root->TryGetNumberField(TEXT("dry_tolerance"),Atlas->DryTolerance) || !FMath::IsFinite(Atlas->DryTolerance) || Atlas->DryTolerance<=0. ||
        !Root->TryGetArrayField(TEXT("tiles"),Tiles) || Tiles->IsEmpty() ||
        !Root->TryGetArrayField(TEXT("physical_exterior_faces"),Physical) ||
        !Root->TryGetObjectField(TEXT("arrays"),Arrays)) return nullptr;
    Atlas->TileNy=int32(Shape.X); Atlas->TileNx=int32(Shape.Y);
    if (Tiles->Num()>MAX_int32/(Atlas->TileNx*Atlas->TileNy)) return nullptr;
    TMap<FIntPoint,int32> Occupied;
    TArray<FIntPoint> Keys;
    for (const auto& Value:*Tiles)
    {
        const TSharedPtr<FJsonObject>* Tile=nullptr;
        FVector2D Origin;
        if (!Value.IsValid() || !Value->TryGetObject(Tile) || !ReadFinitePair(*Tile,TEXT("origin_m"),Origin)) return nullptr;
        if (Atlas->Origins.IsEmpty()) Atlas->Origins.Add(Origin);
        const FVector2D Offset=Origin-Atlas->Origins[0];
        const FVector2D Index(Offset.X/(Atlas->TileNx*Atlas->Spacing),Offset.Y/(Atlas->TileNy*Atlas->Spacing));
        if (FMath::Abs(Index.X)>1.e8 || FMath::Abs(Index.Y)>1.e8 ||
            FMath::Abs(Index.X-FMath::RoundToDouble(Index.X))>1.e-8 ||
            FMath::Abs(Index.Y-FMath::RoundToDouble(Index.Y))>1.e-8) return nullptr;
        const FIntPoint TileKey(FMath::RoundToInt(Index.X),FMath::RoundToInt(Index.Y));
        if (Occupied.Contains(TileKey)) return nullptr;
        const int32 TileIndex=Keys.Num();
        Occupied.Add(TileKey,TileIndex); Keys.Add(TileKey);
        if (TileIndex>0) Atlas->Origins.Add(Origin);
    }
    const TPair<const TCHAR*,FNpyArray*> Loads[]={{TEXT("bed"),&Atlas->Bed},{TEXT("h"),&Atlas->H},
        {TEXT("u"),&Atlas->U},{TEXT("v"),&Atlas->V}};
    for (const auto& Load:Loads)
    {
        const TSharedPtr<FJsonObject>* Meta=nullptr;
        if (!(*Arrays)->TryGetObjectField(Load.Key,Meta) ||
            !LoadCookedArray(FPaths::GetPath(Path),*Meta,Load.Key,*Load.Value,Error) ||
            !Load.Value->bIsFloat || Load.Value->ElementBytes!=8 ||
            Load.Value->Nx!=Atlas->TileNx || Load.Value->Ny!=int64(Tiles->Num())*Atlas->TileNy) return nullptr;
    }
    for (int32 I=0;I<Atlas->H.Float64.Num();++I)
        if (!FMath::IsFinite(Atlas->Bed.Float64[I]) || !FMath::IsFinite(Atlas->H.Float64[I]) ||
            !FMath::IsFinite(Atlas->U.Float64[I]) || !FMath::IsFinite(Atlas->V.Float64[I]) ||
            Atlas->H.Float64[I]<0. || Atlas->H.Float64[I]>10. ||
            FMath::Square(Atlas->U.Float64[I])+FMath::Square(Atlas->V.Float64[I])>400.) return nullptr;
    const FIntPoint Deltas[]={{-1,0},{1,0},{0,-1},{0,1}};
    const FString Edges[]={TEXT("west"),TEXT("east"),TEXT("south"),TEXT("north")};
    TSet<int64> PhysicalFaces;
    for (const auto& Value:*Physical)
    {
        const TSharedPtr<FJsonObject>* Face=nullptr;
        double TileNumber=0.; FString Edge;
        if (!Value.IsValid() || !Value->TryGetObject(Face) ||
            !(*Face)->TryGetNumberField(TEXT("tile_index"),TileNumber) || !FMath::IsFinite(TileNumber) ||
            TileNumber<0 || TileNumber>=Tiles->Num() || TileNumber!=FMath::FloorToDouble(TileNumber) ||
            !(*Face)->TryGetStringField(TEXT("edge"),Edge)) return nullptr;
        int32 E=0; while (E<4 && Edges[E]!=Edge) ++E;
        if (E==4 || Occupied.Contains(Keys[int32(TileNumber)]+Deltas[E])) return nullptr;
        const int64 FaceKey=int64(TileNumber)*4+E;
        if (PhysicalFaces.Contains(FaceKey)) return nullptr;
        PhysicalFaces.Add(FaceKey);
    }
    // Independently establish the condition that makes outside captured-dry
    // context valid. Do not trust a manifest's generic "passed" flag.
    for (int32 Tile=0;Tile<Tiles->Num();++Tile) for (int32 E=0;E<4;++E)
    {
        if (Occupied.Contains(Keys[Tile]+Deltas[E])) continue;
        const bool bPhysical=PhysicalFaces.Contains(int64(Tile)*4+E);
        const int32 Count=E<2?Atlas->TileNy:Atlas->TileNx;
        for (int32 Along=0;Along<Count;++Along)
        {
            const int32 R=E<2?Along:(E==2?0:Atlas->TileNy-1);
            const int32 C=E>=2?Along:(E==0?0:Atlas->TileNx-1);
            if (Atlas->H.Float64[(Tile*Atlas->TileNy+R)*Atlas->TileNx+C]!=0.)
            {
                if (!bPhysical)
                { Error=TEXT("shared atlas has wet artificial exterior bank cells"); return nullptr; }
                // Internal crop ghosts must not replace a physical discharge
                // or outflow boundary with invented dry exterior state.
                Atlas->PhysicalWetExteriorCells.Add(Atlas->Origins[Tile]+
                    FVector2D(C+Deltas[E].X,R+Deltas[E].Y)*Atlas->Spacing);
            }
        }
    }
    Atlas->TileLookup = MoveTemp(Occupied);
    SharedAtlasCache=Atlas; SharedAtlasCacheKey=Key; ++SharedAtlasLoadCount;
    Error.Reset();
    return Atlas;
}

bool GatherSharedCartesianState(const FString& Directory,const TSharedPtr<FJsonObject>& Reference,
    double OriginX,double OriginY,double Dx,double Dy,double Datum,double DryTolerance,
    const FNpyArray& Bed,const FNpyArray& CapturedWater,FNpyArray& H,FNpyArray& U,FNpyArray& V,
    FNpyArray& Wet,TArray<uint8>& Availability,
    TSharedPtr<const FSharedCartesianAtlas,ESPMode::ThreadSafe>& OutAtlas,FString& Error)
{
    const auto Atlas=LoadSharedCartesianAtlas(Directory,Reference,Error);
    if (!Atlas.IsValid()) return false;
    Error=TEXT("shared Cartesian atlas/source grid, datum, mask or bed mismatch");
    if (Atlas->Spacing!=Dx || Dx!=Dy || Atlas->Datum!=Datum || Atlas->DryTolerance!=DryTolerance ||
        !Bed.bIsFloat || Bed.ElementBytes!=8 || CapturedWater.bIsFloat ||
        CapturedWater.Nx!=Bed.Nx || CapturedWater.Ny!=Bed.Ny) return false;
    const int32 Count=Bed.Nx*Bed.Ny;
    for (FNpyArray* Array:{&H,&U,&V})
    { Array->Nx=Bed.Nx; Array->Ny=Bed.Ny; Array->bIsFloat=true; Array->ElementBytes=8; Array->Float64.Init(0.,Count); }
    Wet.Nx=Bed.Nx; Wet.Ny=Bed.Ny; Wet.Bytes.Init(0,Count);
    Availability.SetNumUninitialized(Count);
    for (int32 I=0;I<Count;++I)
    {
        if (CapturedWater.Bytes[I]>1) return false;
        Availability[I]=CapturedWater.Bytes[I]?0:1; // 0 unavailable; 1 captured-dry context; 2 solved.
    }
    for (int32 Tile=0;Tile<Atlas->Origins.Num();++Tile)
    {
        const FVector2D Offset=(Atlas->Origins[Tile]-FVector2D(OriginX,OriginY))/Dx;
        if (FMath::Abs(Offset.X)>MAX_int32/2. || FMath::Abs(Offset.Y)>MAX_int32/2. ||
            FMath::Abs(Offset.X-FMath::RoundToDouble(Offset.X))>1.e-7 ||
            FMath::Abs(Offset.Y-FMath::RoundToDouble(Offset.Y))>1.e-7) return false;
        const int32 X=FMath::RoundToInt(Offset.X),Y=FMath::RoundToInt(Offset.Y);
        const int32 X0=FMath::Max(0,X),Y0=FMath::Max(0,Y);
        const int32 X1=FMath::Min(int32(Bed.Nx),X+Atlas->TileNx),Y1=FMath::Min(int32(Bed.Ny),Y+Atlas->TileNy);
        for (int32 R=Y0;R<Y1;++R) for (int32 C=X0;C<X1;++C)
        {
            const int32 Dest=R*Bed.Nx+C;
            const int32 Source=(Tile*Atlas->TileNy+R-Y)*Atlas->TileNx+C-X;
            if (Availability[Dest]==2 || Bed.Float64[Dest]!=Atlas->Bed.Float64[Source]) return false;
            Availability[Dest]=2;
            H.Float64[Dest]=Atlas->H.Float64[Source]; U.Float64[Dest]=Atlas->U.Float64[Source]; V.Float64[Dest]=Atlas->V.Float64[Source];
            Wet.Bytes[Dest]=H.Float64[Dest]>DryTolerance?1:0;
        }
    }
    for (const FVector2D& Point:Atlas->PhysicalWetExteriorCells)
    {
        const FVector2D Offset=(Point-FVector2D(OriginX,OriginY))/Dx;
        const int32 C=FMath::RoundToInt(Offset.X),R=FMath::RoundToInt(Offset.Y);
        if (C>=0 && C<Bed.Nx && R>=0 && R<Bed.Ny)
        {
            if (Availability[R*Bed.Nx+C]==2) return false;
            Availability[R*Bed.Nx+C]=0;
        }
    }
    OutAtlas = Atlas;
    Error.Reset(); return true;
}

bool ComputeCropRange(
    double WindowMin, double WindowMax, double OriginCenter, double CellSize, int64 CellCount,
    int32& OutFirst, int32& OutLast)
{
    // Cooked samples are cell-centered at Origin + index * CellSize.
    OutFirst = FMath::Clamp(
        static_cast<int32>(FMath::FloorToDouble((WindowMin - OriginCenter) / CellSize)),
        0, static_cast<int32>(CellCount) - 1);
    OutLast = FMath::Clamp(
        static_cast<int32>(FMath::CeilToDouble((WindowMax - OriginCenter) / CellSize)),
        0, static_cast<int32>(CellCount) - 1);
    while (OutLast - OutFirst + 1 < kMinWindowCells && (OutFirst > 0 || OutLast < CellCount - 1))
    {
        if (OutFirst > 0)
        {
            --OutFirst;
        }
        if (OutLast - OutFirst + 1 < kMinWindowCells && OutLast < CellCount - 1)
        {
            ++OutLast;
        }
    }
    return OutLast - OutFirst + 1 >= kMinWindowCells;
}

raftsim::BoundaryCondition MakeEdgeBoundary(const char* Edge, const char* Kind)
{
    raftsim::BoundaryCondition Boundary;
    Boundary.edge = Edge;
    Boundary.kind = Kind;
    return Boundary;
}

bool TryReadRuntimeBoundary(
    const TSharedPtr<FJsonObject>& Band, const FString& Edge,
    double VerticalDatum, raftsim::BoundaryCondition& OutBoundary)
{
    const TArray<TSharedPtr<FJsonValue>>* RuntimeBoundaries = nullptr;
    if (!Band.IsValid() || !Band->TryGetArrayField(TEXT("runtime_boundaries"), RuntimeBoundaries))
    {
        return false;
    }
    for (const TSharedPtr<FJsonValue>& Value : *RuntimeBoundaries)
    {
        const TSharedPtr<FJsonObject> Object = Value->AsObject();
        FString CandidateEdge;
        FString Kind;
        if (!Object.IsValid() || !Object->TryGetStringField(TEXT("edge"), CandidateEdge) ||
            CandidateEdge != Edge || !Object->TryGetStringField(TEXT("kind"), Kind))
        {
            continue;
        }
        OutBoundary = MakeEdgeBoundary(TCHAR_TO_UTF8(*CandidateEdge), TCHAR_TO_UTF8(*Kind));
        double Stage = 0.0;
        if (Object->TryGetNumberField(TEXT("stage"), Stage))
        {
            OutBoundary.has_stage = true;
            OutBoundary.stage = Stage - VerticalDatum;
        }
        double Depth = 0.0;
        if (Object->TryGetNumberField(TEXT("depth"), Depth))
        {
            OutBoundary.has_depth = true;
            OutBoundary.depth = Depth;
        }
        const TArray<TSharedPtr<FJsonValue>>* Velocity = nullptr;
        if (Object->TryGetArrayField(TEXT("velocity"), Velocity) && Velocity->Num() == 2)
        {
            OutBoundary.has_velocity = true;
            OutBoundary.velocity_x = (*Velocity)[0]->AsNumber();
            OutBoundary.velocity_y = (*Velocity)[1]->AsNumber();
        }
        return true;
    }
    return false;
}

} // namespace

struct FRaftSimLiveWaterWindow::FPresentationState
{
    TSharedPtr<const FSharedCartesianAtlas, ESPMode::ThreadSafe> Atlas;
};

FRaftSimLiveWaterWindow::FRaftSimLiveWaterWindow() = default;
FRaftSimLiveWaterWindow::~FRaftSimLiveWaterWindow() = default;

TUniquePtr<FRaftSimLiveWaterWindow> FRaftSimLiveWaterWindow::CreateFlatTank(
    const FVector2D& WorldOriginM, float SizeXM, float SizeYM, float CellSizeM,
    float SurfaceHeightM, float DepthM)
{
    const std::size_t Nx = FMath::Max<std::size_t>(8, static_cast<std::size_t>(SizeXM / CellSizeM));
    const std::size_t Ny = FMath::Max<std::size_t>(8, static_cast<std::size_t>(SizeYM / CellSizeM));

    raftsim::Scenario Scenario;
    Scenario.scenario_id = "raftsim_game_flat_tank";
    Scenario.scenario_type = "game_runtime";
    // No fixture_kind: nothing fixture-scoped can ever engage for game water.
    Scenario.fixture_kind.clear();
    Scenario.grid.nx = Nx;
    Scenario.grid.ny = Ny;
    Scenario.grid.dx = CellSizeM;
    Scenario.grid.dy = CellSizeM;
    Scenario.grid.origin_x = WorldOriginM.X + 0.5 * CellSizeM;
    Scenario.grid.origin_y = WorldOriginM.Y + 0.5 * CellSizeM;
    Scenario.fixed_dt = 1.0 / 120.0;
    Scenario.duration = 1.0e9;
    Scenario.bed = raftsim::Array2D(Ny, Nx, SurfaceHeightM - DepthM);
    Scenario.initial.h = raftsim::Array2D(Ny, Nx, DepthM);
    Scenario.initial.eta = raftsim::Array2D(Ny, Nx, SurfaceHeightM);
    Scenario.initial.wet.ny = Ny;
    Scenario.initial.wet.nx = Nx;
    Scenario.initial.wet.values.assign(Ny * Nx, 1);
    Scenario.initial.u = raftsim::Array2D(Ny, Nx, 0.0);
    Scenario.initial.v = raftsim::Array2D(Ny, Nx, 0.0);
    Scenario.initial.hu = raftsim::Array2D(Ny, Nx, 0.0);
    Scenario.initial.hv = raftsim::Array2D(Ny, Nx, 0.0);

    raftsim::SolverConfig Config;
    Config.solver_mode = "finite_volume";
    Config.flux_scheme = "hll";
    Config.spatial_order = 2;
    // Game water is always the genuine solver: never playback, never calibration.
    Config.disable_fixture_calibrations = true;

    TUniquePtr<FRaftSimLiveWaterWindow> Window(new FRaftSimLiveWaterWindow());
    Window->Solver = MakePimpl<raftsim::ReducedShallowWaterSolver>(
        MoveTemp(Scenario), Config);
    Window->OriginM = WorldOriginM + FVector2D(0.5 * CellSizeM, 0.5 * CellSizeM);
    Window->CellXM = CellSizeM;
    Window->CellYM = CellSizeM;
    Window->SeedWetFractionValue = 1.0;
    return Window;
}

#if WITH_AUTOMATION_TESTS
int32 FRaftSimLiveWaterWindow::GetSharedAtlasLoadCountForTesting()
{
    FScopeLock Lock(&SharedAtlasMutex);
    return SharedAtlasLoadCount;
}
#endif

TUniquePtr<FRaftSimLiveWaterWindow> FRaftSimLiveWaterWindow::CreateFromCookedFields(
    const FString& CookedFieldsDir, const FString& BandId,
    const FVector2D& WindowCenterM, const FVector2D& WindowExtentM,
    float RoughnessManning, FString& OutError, bool bRecenterHydraulicCrux)
{
    OutError.Reset();

    // --- Manifest --------------------------------------------------------
    const FString ManifestPath = FPaths::Combine(CookedFieldsDir, TEXT("manifest.json"));
    FString ManifestText;
    if (!FFileHelper::LoadFileToString(ManifestText, *ManifestPath))
    {
        OutError = FString::Printf(TEXT("could not read cooked manifest %s"), *ManifestPath);
        return nullptr;
    }
    TSharedPtr<FJsonObject> Root;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ManifestText);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        OutError = FString::Printf(TEXT("cooked manifest %s is not valid JSON"), *ManifestPath);
        return nullptr;
    }
    FString Schema;
    if (!Root->TryGetStringField(TEXT("schema"), Schema) ||
        Schema != TEXT("raftsim.cooked_flow_fields.v1"))
    {
        OutError = FString::Printf(TEXT("unsupported cooked manifest schema '%s'"), *Schema);
        return nullptr;
    }
    // Full-reach transit fields carry absolute DEM elevations. Named-rapid
    // cooks deliberately subtract their entry elevation before solving and
    // record that source datum here. Older/absolute manifests omit the field.
    double SourceElevationDatumM = 0.0;
    Root->TryGetNumberField(TEXT("source_elevation_datum_m"), SourceElevationDatumM);

    const TSharedPtr<FJsonObject>* Grid = nullptr;
    const TSharedPtr<FJsonObject>* Solver = nullptr;
    if (!Root->TryGetObjectField(TEXT("grid"), Grid) ||
        !Root->TryGetObjectField(TEXT("solver"), Solver))
    {
        OutError = TEXT("cooked manifest is missing grid/solver sections");
        return nullptr;
    }

    const int64 FullNx = static_cast<int64>((*Grid)->GetNumberField(TEXT("nx")));
    const int64 FullNy = static_cast<int64>((*Grid)->GetNumberField(TEXT("ny")));
    const double Dx = (*Grid)->GetNumberField(TEXT("dx_m"));
    const double Dy = (*Grid)->GetNumberField(TEXT("dy_m"));
    const double OriginX = (*Grid)->GetNumberField(TEXT("origin_x_m"));
    const double OriginY = (*Grid)->GetNumberField(TEXT("origin_y_m"));
    if (FullNx < kMinWindowCells || FullNy < kMinWindowCells || FullNx>MAX_int32 || FullNy>MAX_int32/FullNx ||
        !FMath::IsFinite(Dx) || !FMath::IsFinite(Dy) || !FMath::IsFinite(OriginX) || !FMath::IsFinite(OriginY) ||
        !FMath::IsFinite(SourceElevationDatumM) || Dx <= 0.0 || Dy <= 0.0)
    {
        OutError = TEXT("cooked grid is degenerate");
        return nullptr;
    }

    // --- Band ------------------------------------------------------------
    const TArray<TSharedPtr<FJsonValue>>* Bands = nullptr;
    if (!Root->TryGetArrayField(TEXT("bands"), Bands))
    {
        OutError = TEXT("cooked manifest has no bands");
        return nullptr;
    }
    TSharedPtr<FJsonObject> Band;
    for (const TSharedPtr<FJsonValue>& BandValue : *Bands)
    {
        const TSharedPtr<FJsonObject> Candidate = BandValue->AsObject();
        if (Candidate.IsValid() && Candidate->GetStringField(TEXT("band_id")) == BandId)
        {
            Band = Candidate;
            break;
        }
    }
    if (!Band.IsValid())
    {
        // Rivers name their flow bands differently (median_runnable,
        // rainfed_runnable, ...). When the requested band is absent, fall back
        // to the middle band of whatever the manifest provides so a map's
        // "reference" request resolves regardless of the river's band scheme.
        if (Bands->Num() > 0)
        {
            const int32 MidIndex = Bands->Num() / 2;
            Band = (*Bands)[MidIndex]->AsObject();
        }
        if (!Band.IsValid())
        {
            OutError = FString::Printf(TEXT("band '%s' not found in cooked manifest"), *BandId);
            return nullptr;
        }
    }
    const TSharedPtr<FJsonObject>* Arrays = nullptr;
    if (!Band->TryGetObjectField(TEXT("arrays"), Arrays))
    {
        OutError = FString::Printf(TEXT("band '%s' has no arrays section"), *BandId);
        return nullptr;
    }

    // --- Arrays (hash-verified) -----------------------------------------
    FNpyArray Bed, Depth, VelU, VelV, WetMask;
    TArray<uint8> SourceAvailability;
    TSharedPtr<const FSharedCartesianAtlas, ESPMode::ThreadSafe> SharedSource;
    const bool bSharedAtlas=Band->HasField(TEXT("shared_cartesian_state"));
    bool bCartesianCoupled=false, bReplayOfflineSolver=false;
    (*Solver)->TryGetBoolField(TEXT("runtime_cartesian_coupled_config"),bCartesianCoupled);
    (*Solver)->TryGetBoolField(TEXT("runtime_replay_offline_config"),bReplayOfflineSolver);
    if (bSharedAtlas && (!bCartesianCoupled || bReplayOfflineSolver || bRecenterHydraulicCrux))
    { OutError=TEXT("shared state atlas requires explicit Cartesian live crops"); return nullptr; }
    const TPair<const TCHAR*, FNpyArray*> Loads[] = {
        {TEXT("bed"), &Bed}, {TEXT("h"), &Depth}, {TEXT("u"), &VelU},
        {TEXT("v"), &VelV}, {TEXT("wet_mask"), &WetMask}};
    for (const TPair<const TCHAR*, FNpyArray*>& Load : Loads)
    {
        if (bSharedAtlas && Load.Value!=&Bed)
        {
            if ((*Arrays)->HasField(Load.Key))
            { OutError=TEXT("shared atlas cannot be mixed with dense h/u/v/wet arrays"); return nullptr; }
            continue;
        }
        const TSharedPtr<FJsonObject>* ArrayMeta = nullptr;
        if (!(*Arrays)->TryGetObjectField(Load.Key, ArrayMeta))
        {
            OutError = FString::Printf(TEXT("band '%s' is missing array '%s'"), *BandId, Load.Key);
            return nullptr;
        }
        if (!LoadCookedArray(CookedFieldsDir, *ArrayMeta, Load.Key, *Load.Value, OutError))
        {
            return nullptr;
        }
        if (Load.Value->Ny != FullNy || Load.Value->Nx != FullNx)
        {
            OutError = FString::Printf(
                TEXT("array '%s' shape (%lld, %lld) does not match the cooked grid (%lld, %lld)"),
                Load.Key, Load.Value->Ny, Load.Value->Nx, FullNy, FullNx);
            return nullptr;
        }
    }
    if (bSharedAtlas)
    {
        const TSharedPtr<FJsonObject>* Reference=nullptr;
        const TSharedPtr<FJsonObject>* CapturedMeta=nullptr;
        FNpyArray Captured;
        double DryTolerance=0.;
        if (!Band->TryGetObjectField(TEXT("shared_cartesian_state"),Reference) ||
            !(*Arrays)->TryGetObjectField(TEXT("captured_water_mask"),CapturedMeta) ||
            !(*Solver)->TryGetNumberField(TEXT("dry_tolerance"),DryTolerance) ||
            !LoadCookedArray(CookedFieldsDir,*CapturedMeta,TEXT("captured_water_mask"),Captured,OutError) ||
            !GatherSharedCartesianState(CookedFieldsDir,*Reference,OriginX,OriginY,Dx,Dy,SourceElevationDatumM,DryTolerance,
                Bed,Captured,Depth,VelU,VelV,WetMask,SourceAvailability,SharedSource,OutError))
        {
            if (OutError.IsEmpty()) OutError=TEXT("invalid shared Cartesian source reference");
            return nullptr;
        }
    }
    if (!Bed.bIsFloat || !Depth.bIsFloat || !VelU.bIsFloat || !VelV.bIsFloat || WetMask.bIsFloat)
    {
        OutError = TEXT("cooked array dtypes violate the raftsim.cooked_flow_fields.v1 contract");
        return nullptr;
    }

    // --- Window crop ------------------------------------------------------
    int32 Col0 = 0, Col1 = 0, Row0 = 0, Row1 = 0;
    if (!ComputeCropRange(
            WindowCenterM.X - 0.5 * WindowExtentM.X, WindowCenterM.X + 0.5 * WindowExtentM.X,
            OriginX, Dx, FullNx, Col0, Col1) ||
        !ComputeCropRange(
            WindowCenterM.Y - 0.5 * WindowExtentM.Y, WindowCenterM.Y + 0.5 * WindowExtentM.Y,
            OriginY, Dy, FullNy, Row0, Row1))
    {
        OutError = TEXT("window does not cover enough cooked cells");
        return nullptr;
    }
    const std::size_t Nx = static_cast<std::size_t>(Col1 - Col0 + 1);
    const std::size_t Ny = static_cast<std::size_t>(Row1 - Row0 + 1);

    if (bCartesianCoupled)
    {
        FString Coordinates;
        // Internal crops are not physical river inlets. They require the two
        // source-cell layers used by the offline MUSCL reconstruction, including
        // on north/south edges and where the current points west. Never clamp a
        // missing halo or reuse a whole-river discharge on a partial section.
        if (bReplayOfflineSolver || bRecenterHydraulicCrux ||
            !Root->TryGetStringField(TEXT("coordinate_system"), Coordinates) ||
            Coordinates != TEXT("cartesian_east_north_m") ||
            Col0 < 2 || Row0 < 2 || Col1 > FullNx-3 || Row1 > FullNy-3 ||
            (*Solver)->HasField(TEXT("experimental_west_discharge_m3s")))
        {
            OutError = TEXT("Cartesian coupled crop requires east/north coordinates, two complete source ghost layers, no crux recenter and no physical-inlet/survey replay configuration");
            return nullptr;
        }
        if (bSharedAtlas)
        {
            for (int32 R=Row0-2;R<=Row1+2;++R) for (int32 C=Col0-2;C<=Col1+2;++C)
                if (SourceAvailability[R*FullNx+C]==0)
                { OutError=TEXT("Cartesian crop/ghost reaches unavailable captured-water state"); return nullptr; }
        }
        // Validate the entire source, not just today's crop. A later handoff
        // must not expose invalid values hidden outside the initial window.
        for (int64 Index = 0; Index < FullNx*FullNy; ++Index)
        {
            if (!FMath::IsFinite(Bed.Float64[Index]) || !FMath::IsFinite(Depth.Float64[Index]) ||
                Depth.Float64[Index] < 0. || !FMath::IsFinite(VelU.Float64[Index]) ||
                !FMath::IsFinite(VelV.Float64[Index]) ||
                !FMath::IsFinite(Bed.Float64[Index]+Depth.Float64[Index]))
            {
                OutError = TEXT("Cartesian coupled source contains invalid bed/depth/velocity");
                return nullptr;
            }
        }
    }

    // --- Scenario seeded from the cooked steady state --------------------
    raftsim::Scenario Scenario;
    Scenario.scenario_id =
        std::string("raftsim_game_river_window_") + std::string(TCHAR_TO_UTF8(*BandId));
    Scenario.scenario_type = "game_runtime";
    Scenario.fixture_kind.clear();
    Scenario.grid.nx = Nx;
    Scenario.grid.ny = Ny;
    Scenario.grid.dx = Dx;
    Scenario.grid.dy = Dy;
    Scenario.grid.origin_x = OriginX + Col0 * Dx;
    Scenario.grid.origin_y = OriginY + Row0 * Dy;
    Scenario.fixed_dt = (*Solver)->HasField(TEXT("fixed_dt_s"))
        ? (*Solver)->GetNumberField(TEXT("fixed_dt_s"))
        : 1.0 / 60.0;
    Scenario.duration = 1.0e9;
    Scenario.roughness = RoughnessManning;

    Scenario.bed = raftsim::Array2D(Ny, Nx, 0.0);
    Scenario.initial.h = raftsim::Array2D(Ny, Nx, 0.0);
    Scenario.initial.eta = raftsim::Array2D(Ny, Nx, 0.0);
    Scenario.initial.u = raftsim::Array2D(Ny, Nx, 0.0);
    Scenario.initial.v = raftsim::Array2D(Ny, Nx, 0.0);
    Scenario.initial.hu = raftsim::Array2D(Ny, Nx, 0.0);
    Scenario.initial.hv = raftsim::Array2D(Ny, Nx, 0.0);
    Scenario.initial.wet.ny = Ny;
    Scenario.initial.wet.nx = Nx;
    Scenario.initial.wet.values.assign(Ny * Nx, 0);

    // Vertical datum: the cooked bed carries its absolute DEM elevation (e.g.
    // ~316 m for Troublemaker), but every river map places the raft, player,
    // and lighting around z=0. Re-zero the window to a local datum equal to the
    // mean wet free-surface elevation so the rendered water sits at ~z=0 and the
    // raft rests on it. Subtracting one constant from bed and eta leaves the
    // shallow-water dynamics identical (only bed gradients and depth h matter).
    double SurfaceSum = 0.0;
    int64 SurfaceSamples = 0;
    double BedSum = 0.0;
    // Horizontal datum: locate the reach's hydraulic crux (the strongest
    // whitewater) so the window can be re-centred on it. ColFroude sums the
    // Froude number per stream-wise column; the Froude-weighted row centroid
    // gives the crux's lateral position. Froude = |u| / sqrt(g h).
    constexpr double kGravity = 9.80665;
    TArray<double> ColFroude;
    ColFroude.Init(0.0, static_cast<int32>(Nx));
    double FroudeRowSum = 0.0;
    double FroudeTotal = 0.0;
    for (std::size_t Row = 0; Row < Ny; ++Row)
    {
        for (std::size_t Col = 0; Col < Nx; ++Col)
        {
            const int64 Source = (Row0 + static_cast<int64>(Row)) * FullNx + (Col0 + static_cast<int64>(Col));
            const double CellBed = Bed.Float64[Source];
            BedSum += CellBed;
            if (WetMask.Bytes[Source] != 0)
            {
                const double CellH = FMath::Max(Depth.Float64[Source], 0.0);
                SurfaceSum += CellBed + CellH;
                ++SurfaceSamples;
                if (CellH > 0.05)
                {
                    const double Speed = FMath::Sqrt(
                        VelU.Float64[Source] * VelU.Float64[Source] +
                        VelV.Float64[Source] * VelV.Float64[Source]);
                    const double Froude = Speed / FMath::Sqrt(kGravity * CellH);
                    ColFroude[static_cast<int32>(Col)] += Froude;
                    FroudeRowSum += static_cast<double>(Row) * Froude;
                    FroudeTotal += Froude;
                }
            }
        }
    }
    const double VerticalDatum = SurfaceSamples > 0
        ? SurfaceSum / static_cast<double>(SurfaceSamples)
        : BedSum / static_cast<double>(Nx * Ny);

    // Crux column = strongest cross-stream Froude; crux row = Froude-weighted
    // lateral centroid. Falls back to the window centre if no supercritical
    // flow was cooked (a calm window stays centred as before).
    std::size_t CruxCol = Nx / 2;
    if (FroudeTotal > 0.0)
    {
        double Best = -1.0;
        for (int32 Col = 0; Col < ColFroude.Num(); ++Col)
        {
            if (ColFroude[Col] > Best)
            {
                Best = ColFroude[Col];
                CruxCol = static_cast<std::size_t>(Col);
            }
        }
    }
    const std::size_t CruxRow = FroudeTotal > 0.0
        ? static_cast<std::size_t>(FMath::Clamp(
              FroudeRowSum / FroudeTotal, 0.0, static_cast<double>(Ny - 1)))
        : Ny / 2;

    int64 SeedWetCells = 0;
    for (std::size_t Row = 0; Row < Ny; ++Row)
    {
        for (std::size_t Col = 0; Col < Nx; ++Col)
        {
            const int64 Source = (Row0 + static_cast<int64>(Row)) * FullNx + (Col0 + static_cast<int64>(Col));
            const double CellBed = Bed.Float64[Source] - VerticalDatum;
            const double CellH = FMath::Max(Depth.Float64[Source], 0.0);
            const double CellU = VelU.Float64[Source];
            const double CellV = VelV.Float64[Source];
            const uint8 CellWet = WetMask.Bytes[Source] != 0 ? 1 : 0;
            Scenario.bed(Row, Col) = CellBed;
            Scenario.initial.h(Row, Col) = CellH;
            Scenario.initial.eta(Row, Col) = CellBed + CellH;
            Scenario.initial.u(Row, Col) = CellU;
            Scenario.initial.v(Row, Col) = CellV;
            Scenario.initial.hu(Row, Col) = CellH * CellU;
            Scenario.initial.hv(Row, Col) = CellH * CellV;
            Scenario.initial.wet.values[Row * Nx + Col] = CellWet;
            SeedWetCells += CellWet;
        }
    }

    // Boundaries: a crop edge uses transmissive copy-neighbor flow.  An edge
    // coincident with the full cooked grid restores its authored boundary,
    // including the stage/velocity inflow and stage outflow emitted by M3.
    // Authored stages share the pre-loader vertical datum, hence the same
    // datum shift applied to bed/eta above is applied here.
    const auto AddBoundary = [&Scenario, &Band, VerticalDatum](
                                 const TCHAR* Edge, bool bFullGridEdge,
                                 const char* FallbackKind)
    {
        raftsim::BoundaryCondition Boundary;
        if (!bFullGridEdge || !TryReadRuntimeBoundary(Band, Edge, VerticalDatum, Boundary))
        {
            Boundary = MakeEdgeBoundary(TCHAR_TO_UTF8(Edge), FallbackKind);
        }
        Scenario.boundaries.push_back(MoveTemp(Boundary));
    };
    AddBoundary(TEXT("west"), Col0 == 0, "transmissive");
    AddBoundary(TEXT("east"), Col1 == FullNx - 1, "transmissive");
    AddBoundary(TEXT("south"), Row0 == 0, Row0 == 0 ? "bank" : "transmissive");
    AddBoundary(TEXT("north"), Row1 == FullNy - 1, Row1 == FullNy - 1 ? "bank" : "transmissive");

    // --- Solver config: the manifest's cook settings ----------------------
    raftsim::SolverConfig Config;
    Config.solver_mode = TCHAR_TO_UTF8(*(*Solver)->GetStringField(TEXT("solver_mode")));
    Config.flux_scheme = TCHAR_TO_UTF8(*(*Solver)->GetStringField(TEXT("flux_scheme")));
    // The cooked 0.5 m state already contains the rapid's high-resolution
    // ledges, holes, and wave train. Reconstructing every interface twice on
    // the game thread costs ~51 ms per 160 x 80 m step at Troublemaker and
    // does not add visible geometry. First-order runtime evolution preserves
    // the same cells and conservative FV authority at less than half that
    // cost; offline cooking remains second-order.
    Config.spatial_order = 1;
    Config.cfl = (*Solver)->GetNumberField(TEXT("cfl"));
    Config.dry_tolerance = (*Solver)->GetNumberField(TEXT("dry_tolerance"));
    Config.roughness_scale = (*Solver)->GetNumberField(TEXT("roughness_scale"));
    Config.bed_slope_source_scale = (*Solver)->GetNumberField(TEXT("bed_slope_source_scale"));
    Config.feature_strength_scale = (*Solver)->HasField(TEXT("feature_strength_scale"))
        ? (*Solver)->GetNumberField(TEXT("feature_strength_scale"))
        : 0.0;
    Config.preserve_initial_mass = false;
    (*Solver)->TryGetBoolField(TEXT("preserve_initial_mass"), Config.preserve_initial_mass);
    // Game water is always the genuine solver, whatever the manifest says.
    Config.disable_fixture_calibrations = true;

    // Explicit geographically registered replay, never inferred from a river name. These
    // candidates must retain the offline boundary and roughness for meaningful
    // geometry/raft comparisons. Do not transplant a total-discharge boundary
    // to a crop covering only part of the inlet.
    if (bReplayOfflineSolver)
    {
        double PrescribedDischarge = -1.0;
        double Manning = 0.0;
        bool bMixedStage = false;
        if (Col0 != 0 || Col1 != FullNx - 1 || Row0 != 0 || Row1 != FullNy - 1 ||
            !(*Solver)->TryGetNumberField(TEXT("experimental_west_discharge_m3s"), PrescribedDischarge) ||
            !FMath::IsFinite(PrescribedDischarge) || PrescribedDischarge < 0.0 ||
            !(*Solver)->TryGetNumberField(TEXT("roughness_manning"), Manning) ||
            !FMath::IsFinite(Manning) || Manning <= 0.0 || Manning > 0.2 ||
            (*Solver)->GetIntegerField(TEXT("spatial_order")) != 2 ||
            Config.solver_mode != "finite_volume")
        {
            OutError = TEXT("Survey replay requires the complete grid and explicit valid MUSCL discharge/roughness settings");
            return nullptr;
        }
        (*Solver)->TryGetBoolField(TEXT("experimental_west_supercritical_stage"), bMixedStage);
        Config.spatial_order = 2;
        Config.boundary_mode = "scenario";
        Config.experimental_west_discharge_m3s = PrescribedDischarge;
        Config.experimental_west_supercritical_stage = bMixedStage;
        Scenario.roughness = Manning;
        UE_LOG(LogTemp, Display, TEXT("RaftSim survey replay: MUSCL full grid, Q=%.6f m3/s, Manning=%.4f"),
            PrescribedDischarge, Manning);
    }

    if (bCartesianCoupled)
    {
        double Manning = 0., SpatialOrder = 0.;
        if (!(*Solver)->TryGetNumberField(TEXT("roughness_manning"), Manning) ||
            !FMath::IsFinite(Manning) || Manning <= 0. || Manning > .2 ||
            !FMath::IsNearlyEqual(Manning, double(RoughnessManning), 1.e-8) ||
            !(*Solver)->TryGetNumberField(TEXT("spatial_order"), SpatialOrder) || SpatialOrder != 2. ||
            Config.solver_mode != "finite_volume" || Config.flux_scheme != "hll" ||
            !FMath::IsFinite(Config.cfl) || Config.cfl <= 0. || Config.cfl > .5 ||
            !FMath::IsFinite(Config.dry_tolerance) || Config.dry_tolerance <= 0. ||
            Config.roughness_scale != 1. || Config.bed_slope_source_scale != 1. ||
            Config.feature_strength_scale != 0. || Config.preserve_initial_mass ||
            !FMath::IsFinite(SourceElevationDatumM))
        {
            OutError = TEXT("Cartesian coupled crop requires explicit unforced MUSCL2/HLL settings and matching Manning roughness");
            return nullptr;
        }
        Config.spatial_order = 2;
        Config.boundary_mode = "scenario";
        Scenario.roughness = Manning;
        Scenario.boundaries.clear();
        for (const char* Edge : {"west", "east", "south", "north"})
        {
            auto Boundary = MakeEdgeBoundary(Edge, "ghost");
            const bool bWest = Boundary.edge == "west", bEast = Boundary.edge == "east";
            const bool bXEdge = bWest || bEast;
            const int32 Count = static_cast<int32>(bXEdge ? Ny : Nx);
            Boundary.ghost_cells.reserve(2*Count);
            for (int32 Layer = 0; Layer < 2; ++Layer)
            {
                for (int32 Along = 0; Along < Count; ++Along)
                {
                    const int64 Col = bXEdge ? (bWest ? Col0-1-Layer : Col1+1+Layer) : Col0+Along;
                    const int64 Row = bXEdge ? Row0+Along :
                        (Boundary.edge == "south" ? Row0-1-Layer : Row1+1+Layer);
                    const int64 Index = Row*FullNx+Col;
                    Boundary.ghost_cells.push_back({Bed.Float64[Index]-VerticalDatum,
                        Depth.Float64[Index], VelU.Float64[Index], VelV.Float64[Index]});
                }
            }
            Scenario.boundaries.push_back(MoveTemp(Boundary));
        }
    }

    const FVector2D RuntimeOriginM = bRecenterHydraulicCrux
        ? FVector2D(
              -static_cast<double>(CruxCol) * Dx,
              -static_cast<double>(CruxRow) * Dy)
        : FVector2D(Scenario.grid.origin_x, Scenario.grid.origin_y);
    TUniquePtr<FRaftSimLiveWaterWindow> Window(new FRaftSimLiveWaterWindow());
    Window->ElevationDatumM = VerticalDatum + SourceElevationDatumM;
    try
    {
        Window->Solver = MakePimpl<raftsim::ReducedShallowWaterSolver>(
            MoveTemp(Scenario), Config);
    }
    catch (const std::exception& Exception)
    {
        OutError = FString::Printf(
            TEXT("solver rejected the seeded river window: %hs"), Exception.what());
        return nullptr;
    }
    // Legacy fixed rapid maps re-centre their hydraulic crux on world origin.
    // Moving corridor windows retain global station/lateral coordinates so an
    // overlapping downstream crop addresses the same physical cells.
    Window->OriginM = RuntimeOriginM;
    Window->CellXM = static_cast<float>(Dx);
    Window->CellYM = static_cast<float>(Dy);
    Window->SeedWetFractionValue =
        static_cast<double>(SeedWetCells) / static_cast<double>(Nx * Ny);
    // Cooked river bands are rendered by the band water materials, whose
    // WPO animates the travelling bake wave; tanks stay flat-rendered.
    // A survey replay has no authored travelling-wave material. Adding the
    // legacy wave here would move raft support away from the measured field.
    Window->bHasTravelingWavePresentation = !bReplayOfflineSolver && !bCartesianCoupled;
    if (SharedSource.IsValid())
    {
        auto Presentation = MakeShared<FPresentationState, ESPMode::ThreadSafe>();
        Presentation->Atlas = MoveTemp(SharedSource);
        Window->PresentationState = MoveTemp(Presentation);
    }
    return Window;
}

FRaftSimLiveWaterSampleResult FRaftSimLiveWaterWindow::SamplePresentationSource(const FVector2D& PositionM) const
{
    return PresentationState.IsValid() ? PresentationState->Atlas->Sample(PositionM) : FRaftSimLiveWaterSampleResult{};
}

bool FRaftSimLiveWaterWindow::GetFieldBoundsM(FBox2D& OutBounds) const
{
    if (!Solver.IsValid()) return false;
    const auto& Grid = Solver->scenario().grid;
    OutBounds = FBox2D(OriginM, OriginM + FVector2D((Grid.nx-1)*double(CellXM), (Grid.ny-1)*double(CellYM)));
    return true;
}

void FRaftSimLiveWaterWindow::Step(float DtSeconds)
{
    if (Solver.IsValid() && DtSeconds > 0.0f)
    {
        Solver->step(FMath::Min(DtSeconds, kMaxStepSeconds));
        ++StepCounter;
    }
}

double FRaftSimLiveWaterWindow::SimTimeSeconds() const
{
    return Solver.IsValid() ? Solver->time() : 0.0;
}

double FRaftSimLiveWaterWindow::TotalWaterVolumeM3() const
{
    if (!Solver.IsValid())
    {
        return 0.0;
    }
    const raftsim::Scenario& Scenario = Solver->scenario();
    double Total = 0.0;
    for (double Depth : Solver->state().h.values())
    {
        Total += FMath::Max(Depth, 0.0);
    }
    return Total * Scenario.grid.dx * Scenario.grid.dy;
}

double FRaftSimLiveWaterWindow::WetCellFraction() const
{
    if (!Solver.IsValid())
    {
        return 0.0;
    }
    const std::vector<double>& Depths = Solver->state().h.values();
    if (Depths.empty())
    {
        return 0.0;
    }
    int64 WetCells = 0;
    for (double Depth : Depths)
    {
        if (Depth > 1.0e-6)
        {
            ++WetCells;
        }
    }
    return static_cast<double>(WetCells) / static_cast<double>(Depths.size());
}

bool FRaftSimLiveWaterWindow::HasNonFiniteState() const
{
    if (!Solver.IsValid())
    {
        return false;
    }
    const raftsim::WaterState& State = Solver->state();
    const raftsim::Array2D* Fields[] = {&State.h, &State.u, &State.v};
    for (const raftsim::Array2D* Field : Fields)
    {
        for (double Value : Field->values())
        {
            if (!FMath::IsFinite(Value))
            {
                return true;
            }
        }
    }
    return false;
}

int32 FRaftSimLiveWaterWindow::TransferOverlapStateFrom(
    const FRaftSimLiveWaterWindow& PreviousWindow)
{
    if (!Solver.IsValid() || !PreviousWindow.Solver.IsValid())
    {
        return 0;
    }
    const raftsim::Scenario& Scenario = Solver->scenario();
    const raftsim::Scenario& PreviousScenario = PreviousWindow.Solver->scenario();
    const double PreviousMaxX = PreviousWindow.OriginM.X +
        static_cast<double>(PreviousScenario.grid.nx - 1) * PreviousWindow.CellXM;
    const double PreviousMaxY = PreviousWindow.OriginM.Y +
        static_cast<double>(PreviousScenario.grid.ny - 1) * PreviousWindow.CellYM;
    const raftsim::WaterState& PreviousState = PreviousWindow.Solver->state();
    // Same Cartesian lattice means the cells are identical control volumes.
    // Going through Sample() rounded doubles to floats and applied its 1e-4 m
    // presentation wet threshold, losing shallow-cell momentum on each move.
    const double ColumnOffset = (OriginM.X - PreviousWindow.OriginM.X) / CellXM;
    const double RowOffset = (OriginM.Y - PreviousWindow.OriginM.Y) / CellYM;
    const double RoundedColumnOffset = FMath::RoundToDouble(ColumnOffset);
    const double RoundedRowOffset = FMath::RoundToDouble(RowOffset);
    const bool bSameLattice = CellXM == PreviousWindow.CellXM &&
        CellYM == PreviousWindow.CellYM &&
        FMath::Abs(ColumnOffset - RoundedColumnOffset) < 1.e-8 &&
        FMath::Abs(RowOffset - RoundedRowOffset) < 1.e-8 &&
        FMath::Abs(RoundedColumnOffset) < MAX_int32 &&
        FMath::Abs(RoundedRowOffset) < MAX_int32;
    const int64 ColumnShift = bSameLattice ? static_cast<int64>(RoundedColumnOffset) : 0;
    const int64 RowShift = bSameLattice ? static_cast<int64>(RoundedRowOffset) : 0;
    raftsim::WaterState State = Solver->state();
    int32 TransferredCells = 0;
    for (std::size_t Row = 0; Row < Scenario.grid.ny; ++Row)
    {
        for (std::size_t Col = 0; Col < Scenario.grid.nx; ++Col)
        {
            if (bSameLattice)
            {
                const int64 PreviousRow = static_cast<int64>(Row) + RowShift;
                const int64 PreviousCol = static_cast<int64>(Col) + ColumnShift;
                if (PreviousRow < 0 || PreviousCol < 0 ||
                    PreviousRow >= static_cast<int64>(PreviousScenario.grid.ny) ||
                    PreviousCol >= static_cast<int64>(PreviousScenario.grid.nx))
                {
                    continue;
                }
                const double Depth = PreviousState.h(PreviousRow, PreviousCol);
                State.h(Row, Col) = Depth;
                State.u(Row, Col) = PreviousState.u(PreviousRow, PreviousCol);
                State.v(Row, Col) = PreviousState.v(PreviousRow, PreviousCol);
                State.hu(Row, Col) = PreviousState.hu(PreviousRow, PreviousCol);
                State.hv(Row, Col) = PreviousState.hv(PreviousRow, PreviousCol);
                // eta belongs to the receiving solver's elevation datum.
                State.eta(Row, Col) = Scenario.bed(Row, Col) + Depth;
                State.wet.values[Row * Scenario.grid.nx + Col] =
                    PreviousState.wet.values[PreviousRow * PreviousScenario.grid.nx + PreviousCol];
                ++TransferredCells;
                continue;
            }
            const FVector2D WorldPosition(
                OriginM.X + static_cast<double>(Col) * CellXM,
                OriginM.Y + static_cast<double>(Row) * CellYM);
            if (WorldPosition.X < PreviousWindow.OriginM.X || WorldPosition.X > PreviousMaxX ||
                WorldPosition.Y < PreviousWindow.OriginM.Y || WorldPosition.Y > PreviousMaxY)
            {
                continue;
            }
            const FRaftSimLiveWaterSampleResult Sampled = PreviousWindow.Sample(WorldPosition);
            if (!Sampled.bValid)
            {
                continue;
            }
            const double Depth = FMath::Max(static_cast<double>(Sampled.DepthM), 0.0);
            State.h(Row, Col) = Depth;
            State.u(Row, Col) = Sampled.bWet ? static_cast<double>(Sampled.VelocityMps.X) : 0.0;
            State.v(Row, Col) = Sampled.bWet ? static_cast<double>(Sampled.VelocityMps.Y) : 0.0;
            State.eta(Row, Col) = Scenario.bed(Row, Col) + Depth;
            State.hu(Row, Col) = Depth * State.u(Row, Col);
            State.hv(Row, Col) = Depth * State.v(Row, Col);
            State.wet.values[Row * Scenario.grid.nx + Col] = Sampled.bWet ? 1 : 0;
            ++TransferredCells;
        }
    }
    if (TransferredCells == 0)
    {
        return 0;
    }
    try
    {
        Solver->replace_state(MoveTemp(State), PreviousWindow.SimTimeSeconds());
    }
    catch (const std::exception&)
    {
        return 0;
    }
    StepCounter = PreviousWindow.StepCounter;
    return TransferredCells;
}

FRaftSimLiveWaterSampleResult FRaftSimLiveWaterWindow::Sample(
    const FVector2D& WorldPositionM) const
{
    FRaftSimLiveWaterSampleResult Result;
    if (!Solver.IsValid())
    {
        return Result;
    }
    const raftsim::Scenario& Scenario = Solver->scenario();
    const raftsim::WaterState& State = Solver->state();

    // OriginM is the center of cell (0,0), so this is directly the fractional
    // cell-center index.
    const double GridX = (WorldPositionM.X - OriginM.X) / CellXM;
    const double GridY = (WorldPositionM.Y - OriginM.Y) / CellYM;
    const std::size_t Nx = Scenario.grid.nx;
    const std::size_t Ny = Scenario.grid.ny;
    if (Nx < 2 || Ny < 2 || GridX < 0.0 || GridY < 0.0 ||
        GridX > static_cast<double>(Nx - 1) || GridY > static_cast<double>(Ny - 1))
    {
        return Result;
    }
    const double ClampedX = FMath::Clamp(GridX, 0.0, static_cast<double>(Nx - 1));
    const double ClampedY = FMath::Clamp(GridY, 0.0, static_cast<double>(Ny - 1));
    const std::size_t Col = FMath::Min(
        static_cast<std::size_t>(FMath::FloorToDouble(ClampedX)), Nx - 2);
    const std::size_t Row = FMath::Min(
        static_cast<std::size_t>(FMath::FloorToDouble(ClampedY)), Ny - 2);
    const double Fx = ClampedX - static_cast<double>(Col);
    const double Fy = ClampedY - static_cast<double>(Row);

    const auto Bilinear = [&](const raftsim::Array2D& Field) -> double
    {
        const double V00 = Field(Row, Col);
        const double V01 = Field(Row, Col + 1);
        const double V10 = Field(Row + 1, Col);
        const double V11 = Field(Row + 1, Col + 1);
        return FMath::Lerp(FMath::Lerp(V00, V01, Fx), FMath::Lerp(V10, V11, Fx), Fy);
    };

    const double Depth = Bilinear(State.h);
    const double Bed = Bilinear(Scenario.bed);
    Result.bValid = true;
    Result.DepthM = static_cast<float>(FMath::Max(Depth, 0.0));
    // Cooked river fields are shifted near zero before entering the solver to
    // preserve floating-point precision. Restore that private solver datum at
    // this boundary so every caller receives the source-data elevation. The
    // runtime adapter is then solely responsible for applying the Unreal
    // world's global river datum exactly once.
    Result.BedHeightM = static_cast<float>(Bed + ElevationDatumM);
    Result.SurfaceHeightM = static_cast<float>(
        Bed + FMath::Max(Depth, 0.0) + ElevationDatumM);
    Result.bWet = Depth > 1.0e-4;
    Result.VelocityMps = FVector2D(
        static_cast<float>(Bilinear(State.u)), static_cast<float>(Bilinear(State.v)));

    // Surface normal from central differences of the free surface.
    const auto SurfaceAt = [&](std::size_t R, std::size_t C) -> double
    { return Scenario.bed(R, C) + FMath::Max(State.h(R, C), 0.0); };
    const std::size_t CL = Col > 0 ? Col - 1 : Col;
    const std::size_t CR = FMath::Min(Col + 1, Nx - 1);
    const std::size_t RD = Row > 0 ? Row - 1 : Row;
    const std::size_t RU = FMath::Min(Row + 1, Ny - 1);
    const double DzDx = (SurfaceAt(Row, CR) - SurfaceAt(Row, CL)) /
                        (CellXM * static_cast<double>(CR - CL == 0 ? 1 : CR - CL));
    const double DzDy = (SurfaceAt(RU, Col) - SurfaceAt(RD, Col)) /
                        (CellYM * static_cast<double>(RU - RD == 0 ? 1 : RU - RD));
    Result.SurfaceNormal =
        FVector(static_cast<float>(-DzDx), static_cast<float>(-DzDy), 1.0f).GetSafeNormal();
    return Result;
}

#endif // RAFTSIM_HAS_LIVE_SOLVER
