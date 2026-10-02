#include "RaftSimTerrainRefinement.h"

#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "ProceduralMeshComponent.h"

int32 RaftSimTerrainRefinement::BuildRefinedGrid(
    int32 RowSize,
    int32 Rows,
    int32 N,
    const TArray<FVector>& Base,
    const TArray<bool>& WallCorner,
    TArray<FVector>& Vertices,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs,
    TArray<FLinearColor>& Colors,
    TArray<int32>& Triangles,
    TFunctionRef<float(int32 Ordinal, const FVector& BasePosition, bool bStraightEdge)> FineZ)
{
    const int32 CellsX = RowSize - 1;
    const int32 CellsY = Rows - 1;
    if (N < 2 || CellsX < 1 || CellsY < 1 || Vertices.Num() != RowSize * Rows || Base.Num() != Vertices.Num() ||
        WallCorner.Num() != Vertices.Num() || Normals.Num() != Vertices.Num() || UVs.Num() != Vertices.Num() ||
        Colors.Num() != Vertices.Num() || Triangles.Num() != CellsX * CellsY * 6)
    {
        return 0;
    }
    TMap<uint64, int32> FineIndex;
    auto Key = [](int32 FX, int32 FY)
    {
        return (static_cast<uint64>(static_cast<uint32>(FY)) << 32) | static_cast<uint32>(FX);
    };
    const int32 OriginalVertexCount = Vertices.Num();
    TArray<int32> NewTriangles;
    TArray<int32> FineTriangles;
    TArray<int32> Local;
    Local.SetNumUninitialized((N + 1) * (N + 1));
    NewTriangles.Reserve(Triangles.Num());
    int32 SplitCells = 0;
    int32 Ordinal = 0;
    for (int32 CY = 0; CY < CellsY; ++CY)
    {
        for (int32 CX = 0; CX < CellsX; ++CX)
        {
            const int32 Cell = CY * CellsX + CX;
            const int32 A = CY * RowSize + CX;
            const int32 B = A + 1;
            const int32 C = A + RowSize;
            const int32 D = C + 1;
            if (!WallCorner[A] && !WallCorner[B] && !WallCorner[C] && !WallCorner[D])
            {
                NewTriangles.Append(&Triangles[Cell * 6], 6);
                continue;
            }
            ++SplitCells;
            for (int32 J = 0; J <= N; ++J)
            {
                for (int32 I = 0; I <= N; ++I)
                {
                    int32& Slot = Local[J * (N + 1) + I];
                    if ((I == 0 || I == N) && (J == 0 || J == N))
                    {
                        Slot = I == 0 ? (J == 0 ? A : C) : (J == 0 ? B : D);
                        continue;
                    }
                    const uint64 FineKey = Key(CX * N + I, CY * N + J);
                    if (const int32* Existing = FineIndex.Find(FineKey))
                    {
                        Slot = *Existing;
                        continue;
                    }
                    const float U = static_cast<float>(I) / N;
                    const float V = static_cast<float>(J) / N;
                    auto Bilerp = [U, V](const auto& PA, const auto& PB, const auto& PC, const auto& PD)
                    {
                        return (PA * (1.0f - U) + PB * U) * (1.0f - V) + (PC * (1.0f - U) + PD * U) * V;
                    };
                    FVector Position = Bilerp(Base[A], Base[B], Base[C], Base[D]);
                    // An edge stays straight unless one of its corners is a
                    // wall corner: then every cell on it is split, the same
                    // way, in this tile and the next.
                    bool bStraightEdge = false;
                    if (J == 0 || J == N || I == 0 || I == N)
                    {
                        const int32 E0 = J == 0 ? A : J == N ? C : I == 0 ? A : B;
                        const int32 E1 = J == 0 ? B : J == N ? D : I == 0 ? C : D;
                        bStraightEdge = !WallCorner[E0] && !WallCorner[E1];
                    }
                    Position.Z = FineZ(Ordinal++, Position, bStraightEdge);
                    Slot = Vertices.Add(Position);
                    Normals.Add(FVector::UpVector);
                    UVs.Add(Bilerp(UVs[A], UVs[B], UVs[C], UVs[D]));
                    Colors.Add(Bilerp(Colors[A], Colors[B], Colors[C], Colors[D]));
                    FineIndex.Add(FineKey, Slot);
                }
            }
            for (int32 J = 0; J < N; ++J)
            {
                for (int32 I = 0; I < N; ++I)
                {
                    const int32 FA = Local[J * (N + 1) + I];
                    const int32 FB = Local[J * (N + 1) + I + 1];
                    const int32 FC = Local[(J + 1) * (N + 1) + I];
                    const int32 FD = Local[(J + 1) * (N + 1) + I + 1];
                    NewTriangles.Append({FA, FC, FB, FB, FC, FD});
                    FineTriangles.Append({FA, FC, FB, FB, FC, FD});
                }
            }
        }
    }
    Triangles = MoveTemp(NewTriangles);
    // Smooth normals for the re-meshed surface; vertices left on unsplit
    // ground keep their grid normals.
    TArray<FVector> Accumulated;
    Accumulated.SetNumZeroed(Vertices.Num());
    for (int32 Index = 0; Index + 2 < FineTriangles.Num(); Index += 3)
    {
        const int32 I0 = FineTriangles[Index];
        const int32 I1 = FineTriangles[Index + 1];
        const int32 I2 = FineTriangles[Index + 2];
        FVector Face = FVector::CrossProduct(Vertices[I2] - Vertices[I0], Vertices[I1] - Vertices[I0]);
        if (Face.Z < 0.0f)
        {
            Face = -Face;
        }
        Accumulated[I0] += Face;
        Accumulated[I1] += Face;
        Accumulated[I2] += Face;
    }
    for (int32 Index = 0; Index < Vertices.Num(); ++Index)
    {
        const bool bRemeshed = Index >= OriginalVertexCount || WallCorner[Index];
        if (bRemeshed && !Accumulated[Index].IsNearlyZero())
        {
            Normals[Index] = Accumulated[Index].GetSafeNormal();
        }
    }
    return SplitCells;
}

void URaftSimTerrainRefinementComponent::BeginPlay()
{
    Super::BeginPlay();
    if (GetWorld() && GetWorld()->IsGameWorld())
    {
        ApplyRefinement();
    }
}

bool URaftSimTerrainRefinementComponent::ApplyRefinement()
{
    if (bApplied || !GetOwner() || WallCornerIndices.Num() != WallCornerZ.Num())
    {
        return false;
    }
    UProceduralMeshComponent* Mesh = GetOwner()->FindComponentByClass<UProceduralMeshComponent>();
    const FProcMeshSection* Section = Mesh ? Mesh->GetProcMeshSection(0) : nullptr;
    if (!Section || Section->ProcVertexBuffer.Num() != GridRowSize * GridRows)
    {
        return false;
    }
    TArray<FVector> Vertices;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> Colors;
    TArray<int32> Triangles;
    Vertices.Reserve(Section->ProcVertexBuffer.Num() + FineZ.Num());
    for (const FProcMeshVertex& Vertex : Section->ProcVertexBuffer)
    {
        Vertices.Add(FVector(Vertex.Position));
        Normals.Add(FVector(Vertex.Normal));
        UVs.Add(FVector2D(Vertex.UV0));
        Colors.Add(Vertex.Color.ReinterpretAsLinear());
    }
    Triangles.Reserve(Section->ProcIndexBuffer.Num() + FineZ.Num() * 6);
    for (const uint32 Index : Section->ProcIndexBuffer)
    {
        Triangles.Add(static_cast<int32>(Index));
    }
    const TArray<FVector> Base = Vertices;
    TArray<bool> WallCorner;
    WallCorner.Init(false, Vertices.Num());
    for (int32 Index = 0; Index < WallCornerIndices.Num(); ++Index)
    {
        const int32 Corner = WallCornerIndices[Index];
        if (Vertices.IsValidIndex(Corner))
        {
            WallCorner[Corner] = true;
            Vertices[Corner].Z = WallCornerZ[Index];
        }
    }
    const int32 SplitCells = RaftSimTerrainRefinement::BuildRefinedGrid(
        GridRowSize, GridRows, SplitCount, Base, WallCorner, Vertices, Normals, UVs, Colors, Triangles,
        [this](int32 Ordinal, const FVector& BasePosition, bool)
        {
            return FineZ.IsValidIndex(Ordinal) ? FineZ[Ordinal] : static_cast<float>(BasePosition.Z);
        });
    if (SplitCells <= 0)
    {
        return false;
    }
    Mesh->CreateMeshSection_LinearColor(
        0, Vertices, Triangles, Normals, UVs, Colors, TArray<FProcMeshTangent>(), false);
    bApplied = true;
    return true;
}
