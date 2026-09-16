#include "Environment/RaftSimEditorSouthForkFullReachInternal.h"

namespace RaftSimEditorEnvironment
{
using namespace SouthForkFullReach;

bool ExportSouthForkSupportBandFields(FString& OutSummary)
{
    // Mirrors BuildSouthForkFullReachEnvironment's water-band pass without
    // touching content: stitch all thirteen tiles' rows into one
    // station-indexed grid of (baked absolute elevation, band energy, wet)
    // per flow band and write it beside the cooked flow fields. Rigid raft
    // support samples it so the authored band water no longer renders above
    // the ridden surface ("the boat submerged going into the rapid",
    // 2026-08-13). The shoreline-completion fringe is presentation-only and
    // deliberately excluded: it colours one dry vertex beyond the wet
    // channel, which must not widen the support field.
    TSharedPtr<FJsonObject> EnvironmentRoot;
    if (!LoadJsonObject(EnvironmentManifestRelativePath, EnvironmentRoot))
    {
        OutSummary += TEXT("Could not load the South Fork environment manifest.\n");
        return false;
    }
    TArray<FSouthForkCoordinatePoint> CoordinatePoints;
    float VerticalDatumM = 0.0f;
    FString CoordinateMapPath;
    if (!ParseCoordinateMap(
            EnvironmentRoot, CoordinatePoints, VerticalDatumM, CoordinateMapPath) ||
        CoordinatePoints.Num() < 2)
    {
        OutSummary += TEXT("Could not parse the South Fork coordinate map.\n");
        return false;
    }
    const TSharedPtr<FJsonObject>* UnrealImport = nullptr;
    const TArray<TSharedPtr<FJsonValue>>* TileValues = nullptr;
    if (!EnvironmentRoot->TryGetObjectField(TEXT("unreal_import"), UnrealImport) ||
        UnrealImport == nullptr ||
        !(*UnrealImport)->TryGetArrayField(TEXT("tiles"), TileValues) ||
        TileValues == nullptr || TileValues->Num() != 13)
    {
        OutSummary += TEXT("The manifest does not contain thirteen Unreal tiles.\n");
        return false;
    }

    const TCHAR* FlowBands[] = {
        TEXT("low_runnable"), TEXT("median_runnable"), TEXT("high_runnable")};
    int32 ExportedBandCount = 0;
    for (const TCHAR* FlowBand : FlowBands)
    {
        constexpr int32 Width = 21; // LateralM = -40 + 4 * Column
        const int32 RowCount = CoordinatePoints.Num();
        TArray<float> RowStationsM;
        TArray<float> ElevationAbsM;
        TArray<float> Energy;
        TArray<uint8> Wet;
        RowStationsM.SetNum(RowCount);
        ElevationAbsM.Init(0.0f, RowCount * Width);
        Energy.Init(0.0f, RowCount * Width);
        Wet.Init(0, RowCount * Width);
        for (int32 RowIndex = 0; RowIndex < RowCount; ++RowIndex)
        {
            RowStationsM[RowIndex] =
                static_cast<float>(CoordinatePoints[RowIndex].StationM);
        }

        bool bBandComplete = true;
        for (const TSharedPtr<FJsonValue>& TileValue : *TileValues)
        {
            const TSharedPtr<FJsonObject>* Tile = nullptr;
            if (!TileValue->TryGetObject(Tile) || Tile == nullptr)
            {
                bBandComplete = false;
                break;
            }
            const TArray<TSharedPtr<FJsonValue>>* RowRange = nullptr;
            const TSharedPtr<FJsonObject>* WaterBands = nullptr;
            const TSharedPtr<FJsonObject>* WaterEncoding = nullptr;
            if (!(*Tile)->TryGetArrayField(TEXT("row_range"), RowRange) ||
                RowRange == nullptr || RowRange->Num() != 2 ||
                !(*Tile)->TryGetObjectField(TEXT("water_bands"), WaterBands) ||
                WaterBands == nullptr ||
                !(*Tile)->TryGetObjectField(
                    TEXT("water_height_encoding"), WaterEncoding) ||
                WaterEncoding == nullptr)
            {
                bBandComplete = false;
                break;
            }
            double WaterMinimumM = 0.0;
            double WaterMaximumM = 0.0;
            (*WaterEncoding)->TryGetNumberField(
                TEXT("minimum_elevation_m"), WaterMinimumM);
            (*WaterEncoding)->TryGetNumberField(
                TEXT("maximum_elevation_m"), WaterMaximumM);
            const int32 GlobalRowStart =
                static_cast<int32>((*RowRange)[0]->AsNumber());
            const TSharedPtr<FJsonObject>* Band = nullptr;
            const TSharedPtr<FJsonObject>* SurfaceArtifact = nullptr;
            const TSharedPtr<FJsonObject>* PresentationArtifact = nullptr;
            FString SurfacePath;
            FString PresentationPath;
            if (!(*WaterBands)->TryGetObjectField(FlowBand, Band) ||
                Band == nullptr ||
                !(*Band)->TryGetObjectField(
                    TEXT("surface_height"), SurfaceArtifact) ||
                !(*Band)->TryGetObjectField(
                    TEXT("presentation"), PresentationArtifact) ||
                !(*SurfaceArtifact)->TryGetStringField(TEXT("path"), SurfacePath) ||
                !(*PresentationArtifact)
                     ->TryGetStringField(TEXT("path"), PresentationPath))
            {
                bBandComplete = false;
                break;
            }
            FSouthForkGray16Image WaterHeight;
            FRaftSimPreviewImage Presentation;
            if (!LoadGray16Png(SurfacePath, WaterHeight) ||
                !LoadPreviewPngImage(PresentationPath, Presentation) ||
                WaterHeight.Width != Width ||
                WaterHeight.Width != Presentation.Width ||
                WaterHeight.Height != Presentation.Height)
            {
                bBandComplete = false;
                break;
            }
            for (int32 Row = 0; Row < WaterHeight.Height; ++Row)
            {
                const int32 GlobalRow = FMath::Clamp(
                    GlobalRowStart + Row, 0, RowCount - 1);
                // Mirror of the render-side bend superelevation so the
                // hull rides the same tilted surface the water draws.
                const float RowCurvaturePerM =
                    ComputeSouthForkSignedCurvaturePerM(
                        CoordinatePoints, GlobalRow);
                TArray<float> RowSurfaceElevationsM;
                TArray<FLinearColor> RowHydraulicPresentation;
                int32 LeftWetColumn = INDEX_NONE;
                int32 RightWetColumn = INDEX_NONE;
                if (!PrepareSouthForkWaterSurfaceRow(
                        WaterHeight.Values, Presentation.Pixels, Width, Row,
                        WaterMinimumM, WaterMaximumM, RowSurfaceElevationsM,
                        RowHydraulicPresentation, LeftWetColumn, RightWetColumn))
                {
                    bBandComplete = false;
                    break;
                }
                for (int32 Column = 0; Column < Width; ++Column)
                {
                    const int32 CellIndex = GlobalRow * Width + Column;
                    const bool bWetColumn = LeftWetColumn != INDEX_NONE &&
                        Column >= LeftWetColumn && Column <= RightWetColumn;
                    if (!bWetColumn)
                    {
                        continue;
                    }
                    const FLinearColor& HydraulicPresentation =
                        RowHydraulicPresentation[Column];
                    const float ExportSpeedMps =
                        HydraulicPresentation.B * 8.0f;
                    const float ExportBendSlope = FMath::Clamp(
                        ExportSpeedMps * ExportSpeedMps * RowCurvaturePerM /
                            9.81f,
                        -0.008f, 0.008f);
                    const float ExportLateralM = -40.0f + 4.0f * Column;
                    ElevationAbsM[CellIndex] =
                        RowSurfaceElevationsM[Column] -
                        ExportBendSlope * ExportLateralM;
                    Energy[CellIndex] = FMath::Clamp(
                        HydraulicPresentation.R * 0.72f +
                            HydraulicPresentation.B * 0.48f,
                        0.0f, 1.0f);
                    Wet[CellIndex] = 1;
                }
            }
            if (!bBandComplete)
            {
                break;
            }
        }
        if (!bBandComplete)
        {
            OutSummary += FString::Printf(
                TEXT("Band %s: incomplete inputs, skipped.\n"), FlowBand);
            continue;
        }

        // The runtime resolves the field beside whichever cooked-fields
        // directory the map's water config points at; the full-reach map
        // uses the transit seed while the compact Troublemaker map uses the
        // scenario fields. Write both so either config finds it.
        const TCHAR* OutputDirs[] = {
            TEXT("physics/data/real_world/south_fork_american_chili_bar/")
            TEXT("scenario_troublemaker/cooked_flow_fields"),
            TEXT("physics/data/real_world/south_fork_american_chili_bar/")
            TEXT("full_hydraulics/full_reach_transit_seed")};
        int32 WrittenCopies = 0;
        FString WrittenPaths;
        for (const TCHAR* OutputDir : OutputDirs)
        {
            const FString OutputPath = AbsoluteRepoPath(FString::Printf(
                TEXT("%s/support_band_field_%s.bin"), OutputDir, FlowBand));
            TUniquePtr<FArchive> Writer(
                IFileManager::Get().CreateFileWriter(*OutputPath));
            if (!Writer.IsValid())
            {
                OutSummary += FString::Printf(
                    TEXT("Band %s: could not open %s for writing.\n"),
                    FlowBand, *OutputPath);
                continue;
            }
            uint32 Magic = 0x52534246u; // 'RSBF'
            uint32 Version = 1u;
            int32 WidthOut = Width;
            int32 RowCountOut = RowCount;
            float LateralOriginM = -40.0f;
            float LateralSpacingM = 4.0f;
            *Writer << Magic;
            *Writer << Version;
            *Writer << WidthOut;
            *Writer << RowCountOut;
            *Writer << LateralOriginM;
            *Writer << LateralSpacingM;
            *Writer << RowStationsM;
            *Writer << ElevationAbsM;
            *Writer << Energy;
            *Writer << Wet;
            Writer->Close();
            ++WrittenCopies;
            WrittenPaths += FString::Printf(TEXT(" %s"), *OutputPath);
        }
        if (WrittenCopies == 0)
        {
            continue;
        }
        int32 WetCells = 0;
        for (const uint8 Cell : Wet)
        {
            WetCells += Cell != 0 ? 1 : 0;
        }
        OutSummary += FString::Printf(
            TEXT("Band %s: %d rows x %d columns, %d wet cells ->%s\n"),
            FlowBand, RowCount, Width, WetCells, *WrittenPaths);
        ++ExportedBandCount;
    }
    return ExportedBandCount == UE_ARRAY_COUNT(FlowBands);
}

} // namespace RaftSimEditorEnvironment
