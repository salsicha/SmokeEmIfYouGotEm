#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimSouthForkOrganicGroundPresentationTest,
    "RaftSim.M9.EGroundCoverOrganicPresentation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimSouthForkOrganicGroundPresentationTest::RunTest(
    const FString& Parameters)
{
    using namespace RaftSimEditorEnvironment;

    constexpr int32 Width = 5;
    constexpr int32 Height = 5;
    TArray<FVector> PlaneVertices;
    PlaneVertices.Reserve(Width * Height);
    for (int32 Row = 0; Row < Height; ++Row)
    {
        for (int32 Column = 0; Column < Width; ++Column)
        {
            const float X = Column * 400.0f;
            const float Y = Row * 400.0f;
            PlaneVertices.Add(FVector(X, Y, X * 0.10f + Y * 0.20f));
        }
    }
    const TArray<FVector> Normals =
        BuildSouthForkSmoothedTerrainPresentationNormals(
            PlaneVertices, Width, Height, /*Radius=*/2);
    const FVector ExpectedNormal = FVector(-0.10f, -0.20f, 1.0f).GetSafeNormal();
    TestEqual(TEXT("Every DEM vertex receives a presentation normal"),
        Normals.Num(), PlaneVertices.Num());
    for (const FVector& Normal : Normals)
    {
        TestTrue(TEXT("Broad derivatives retain the source plane normal"),
            Normal.Equals(ExpectedNormal, 0.001f));
        TestTrue(TEXT("Terrain presentation normals face upward"), Normal.Z > 0.0f);
    }
    TestTrue(TEXT("Invalid terrain grids fail without partial output"),
        BuildSouthForkSmoothedTerrainPresentationNormals(
            PlaneVertices, Width - 1, Height, 2).IsEmpty());

    const FLinearColor RepresentativeDensity(0.55f, 0.68f, 0.35f, 0.72f);
    const FVector GroundLocation(125000.0f, -84000.0f, 4200.0f);
    FSouthForkGroundCoverPlacement Accepted;
    int32 AcceptedCoordinate = INDEX_NONE;
    for (int32 CoordinateIndex = 0; CoordinateIndex < 2048; ++CoordinateIndex)
    {
        Accepted = ComputeSouthForkGroundCoverPlacement(
            CoordinateIndex, 72, 56.0f, 0.12f,
            RepresentativeDensity, GroundLocation);
        if (Accepted.bAccepted)
        {
            AcceptedCoordinate = CoordinateIndex;
            break;
        }
    }
    TestTrue(TEXT("Representative dry bank admits a grass patch"),
        AcceptedCoordinate != INDEX_NONE);
    TestTrue(TEXT("An accepted sample expands into a visible compact patch"),
        Accepted.ClusterCount >= 3 && Accepted.ClusterCount <= 6);
    const FSouthForkGroundCoverPlacement Repeated =
        ComputeSouthForkGroundCoverPlacement(
            AcceptedCoordinate, 72, 56.0f, 0.12f,
            RepresentativeDensity, GroundLocation);
    TestTrue(TEXT("Ground-cover placement is deterministic"),
        Repeated.bAccepted == Accepted.bAccepted &&
            Repeated.ClusterCount == Accepted.ClusterCount &&
            FMath::IsNearlyEqual(Repeated.BaseScale, Accepted.BaseScale));

    TestFalse(TEXT("Grass stays out of the wetted shoreline corridor"),
        ComputeSouthForkGroundCoverPlacement(
            17, 72, 20.0f, 0.12f,
            RepresentativeDensity, GroundLocation).bAccepted);
    TestFalse(TEXT("Grass fades out beyond the detailed bank ribbon"),
        ComputeSouthForkGroundCoverPlacement(
            17, 72, 120.0f, 0.12f,
            RepresentativeDensity, GroundLocation).bAccepted);
    TestFalse(TEXT("Grass stays off implausibly steep DEM faces"),
        ComputeSouthForkGroundCoverPlacement(
            17, 72, 56.0f, 0.46f,
            RepresentativeDensity, GroundLocation).bAccepted);

    int32 AcceptedDryBankSamples = 0;
    for (int32 CoordinateIndex = 0; CoordinateIndex < 1024; ++CoordinateIndex)
    {
        const bool bAcceptedDryBank = ComputeSouthForkGroundCoverPlacement(
            CoordinateIndex, 72, 58.0f, 0.12f,
            RepresentativeDensity,
            GroundLocation + FVector(CoordinateIndex * 800.0f, 0.0f, 0.0f))
                                          .bAccepted;
        AcceptedDryBankSamples += bAcceptedDryBank ? 1 : 0;
    }
    TestTrue(TEXT("Dry-bank cover is dense enough to read as a mosaic"),
        AcceptedDryBankSamples >= 320);
    TestTrue(TEXT("Dry-bank cover retains deterministic open ground"),
        AcceptedDryBankSamples <= 850);

    const TCHAR* ScannedGroundCoverPaths[] = {
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/GrassBermuda01_1K/SM_GrassBermuda01_grass_bermuda_01_dead_a.SM_GrassBermuda01_grass_bermuda_01_dead_a"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/GrassBermuda01_1K/SM_GrassBermuda01_grass_bermuda_01_dead_b.SM_GrassBermuda01_grass_bermuda_01_dead_b"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/GrassBermuda01_1K/SM_GrassBermuda01_grass_bermuda_01_flattened_a.SM_GrassBermuda01_grass_bermuda_01_flattened_a"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/GrassBermuda01_1K/SM_GrassBermuda01_grass_bermuda_01_medium_a.SM_GrassBermuda01_grass_bermuda_01_medium_a"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/GrassBermuda01_1K/SM_GrassBermuda01_grass_bermuda_01_medium_c.SM_GrassBermuda01_grass_bermuda_01_medium_c"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/GrassBermuda01_1K/SM_GrassBermuda01_grass_bermuda_01_medium_d.SM_GrassBermuda01_grass_bermuda_01_medium_d"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/GrassBermuda01_1K/SM_GrassBermuda01_grass_bermuda_01_medium_f.SM_GrassBermuda01_grass_bermuda_01_medium_f"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/GrassBermuda01_1K/SM_GrassBermuda01_grass_bermuda_01_small_c.SM_GrassBermuda01_grass_bermuda_01_small_c")};
    for (int32 VariantIndex = 0;
         VariantIndex < UE_ARRAY_COUNT(ScannedGroundCoverPaths);
         ++VariantIndex)
    {
        UStaticMesh* Mesh = LoadObject<UStaticMesh>(
            nullptr, ScannedGroundCoverPaths[VariantIndex]);
        TestNotNull(
            *FString::Printf(
                TEXT("Reviewed scanned grass form %d loads"),
                VariantIndex + 1),
            Mesh);
        const FVector Calibration =
            GetSouthForkScannedGroundCoverScaleCalibration(VariantIndex);
        TestTrue(
            *FString::Printf(
                TEXT("Scanned grass form %d has positive calibration"),
                VariantIndex + 1),
            Calibration.X > 0.0f && Calibration.Y > 0.0f &&
                Calibration.Z > 0.0f);
    }
    TestTrue(TEXT("Scanned ground-cover calibration is deterministic"),
        GetSouthForkScannedGroundCoverScaleCalibration(4).Equals(
            GetSouthForkScannedGroundCoverScaleCalibration(4)));

    return true;
}

#endif
