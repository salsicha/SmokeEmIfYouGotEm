#include "RaftSimLiveWaterWindow.h"

#if RAFTSIM_HAS_LIVE_SOLVER

#include "Dom/JsonObject.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
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

} // namespace

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

TUniquePtr<FRaftSimLiveWaterWindow> FRaftSimLiveWaterWindow::CreateFromCookedFields(
    const FString& CookedFieldsDir, const FString& BandId,
    const FVector2D& WindowCenterM, const FVector2D& WindowExtentM,
    float RoughnessManning, FString& OutError)
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
    if (FullNx < kMinWindowCells || FullNy < kMinWindowCells || Dx <= 0.0 || Dy <= 0.0)
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
        OutError = FString::Printf(TEXT("band '%s' not found in cooked manifest"), *BandId);
        return nullptr;
    }
    const TSharedPtr<FJsonObject>* Arrays = nullptr;
    if (!Band->TryGetObjectField(TEXT("arrays"), Arrays))
    {
        OutError = FString::Printf(TEXT("band '%s' has no arrays section"), *BandId);
        return nullptr;
    }

    // --- Arrays (hash-verified) -----------------------------------------
    FNpyArray Bed, Depth, VelU, VelV, WetMask;
    const TPair<const TCHAR*, FNpyArray*> Loads[] = {
        {TEXT("bed"), &Bed}, {TEXT("h"), &Depth}, {TEXT("u"), &VelU},
        {TEXT("v"), &VelV}, {TEXT("wet_mask"), &WetMask}};
    for (const TPair<const TCHAR*, FNpyArray*>& Load : Loads)
    {
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

    int64 SeedWetCells = 0;
    for (std::size_t Row = 0; Row < Ny; ++Row)
    {
        for (std::size_t Col = 0; Col < Nx; ++Col)
        {
            const int64 Source = (Row0 + static_cast<int64>(Row)) * FullNx + (Col0 + static_cast<int64>(Col));
            const double CellBed = Bed.Float64[Source];
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

    // Boundaries: cross-stream edges that coincide with the cooked banks keep
    // the bank condition the fields were cooked with; every cut edge is
    // transmissive (copy-neighbor). Scenario-level inflow/outflow forcing for
    // long-lived windows arrives with the moving-window recenter slice.
    Scenario.boundaries.push_back(MakeEdgeBoundary("west", "transmissive"));
    Scenario.boundaries.push_back(MakeEdgeBoundary("east", "transmissive"));
    Scenario.boundaries.push_back(
        MakeEdgeBoundary("south", Row0 == 0 ? "bank" : "transmissive"));
    Scenario.boundaries.push_back(
        MakeEdgeBoundary("north", Row1 == FullNy - 1 ? "bank" : "transmissive"));

    // --- Solver config: the manifest's cook settings ----------------------
    raftsim::SolverConfig Config;
    Config.solver_mode = TCHAR_TO_UTF8(*(*Solver)->GetStringField(TEXT("solver_mode")));
    Config.flux_scheme = TCHAR_TO_UTF8(*(*Solver)->GetStringField(TEXT("flux_scheme")));
    Config.spatial_order = static_cast<int>((*Solver)->GetNumberField(TEXT("spatial_order")));
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

    TUniquePtr<FRaftSimLiveWaterWindow> Window(new FRaftSimLiveWaterWindow());
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
    Window->OriginM = FVector2D(OriginX + Col0 * Dx, OriginY + Row0 * Dy);
    Window->CellXM = static_cast<float>(Dx);
    Window->CellYM = static_cast<float>(Dy);
    Window->SeedWetFractionValue =
        static_cast<double>(SeedWetCells) / static_cast<double>(Nx * Ny);
    return Window;
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
    if (Nx < 2 || Ny < 2)
    {
        return Result;
    }
    const double ClampedX = FMath::Clamp(GridX, 0.0, static_cast<double>(Nx - 2));
    const double ClampedY = FMath::Clamp(GridY, 0.0, static_cast<double>(Ny - 2));
    const std::size_t Col = static_cast<std::size_t>(ClampedX);
    const std::size_t Row = static_cast<std::size_t>(ClampedY);
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
    Result.BedHeightM = static_cast<float>(Bed);
    Result.SurfaceHeightM = static_cast<float>(Bed + FMath::Max(Depth, 0.0));
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
