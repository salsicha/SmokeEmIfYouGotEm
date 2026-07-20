using UnrealBuildTool;
using System;
using System.IO;

public class RaftSimWater : ModuleRules
{
    public RaftSimWater(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "RaftSimCore" });
        PrivateDependencyModuleNames.AddRange(new[] { "Json" });

        PublicDefinitions.Add("RAFTSIM_WATER_RUNTIME_NAME=\"raftsim_water_cpp_v1\"");
        PublicDefinitions.Add("RAFTSIM_WATER_RUNTIME_HEADER_ONLY_BRIDGE=1");
        PublicIncludePaths.Add(Path.GetFullPath(Path.Combine(ModuleDirectory, "../../../../../physics/cpp/include")));

        // Live game water: link the first-party FV solver static library
        // (build via unreal/Scripts/build_solver_lib.sh). Guarded so the
        // module still compiles before the lib exists on a fresh checkout.
        string SolverLib = Path.GetFullPath(
            Path.Combine(ModuleDirectory, "../../../../../physics/cpp/build-ue/libraftsim_water.a"));
        if (File.Exists(SolverLib))
        {
            PublicAdditionalLibraries.Add(SolverLib);
            PublicDefinitions.Add("RAFTSIM_HAS_LIVE_SOLVER=1");
            bEnableExceptions = true;
        }
        else
        {
            PublicDefinitions.Add("RAFTSIM_HAS_LIVE_SOLVER=0");
        }

        // Shipping builds need the same hash-verified fields used in editor.
        // Stage only runtime JSON/NumPy products, never raw DEM/imagery/source
        // acquisitions. ResolveRuntimeDataPath maps the preserved repo-relative
        // path under RaftSimRuntimeData beside the packaged executable.
        string RepoRoot = Path.GetFullPath(Path.Combine(ModuleDirectory, "../../../../.."));
        string[] RuntimeRoots =
        {
            "physics/data/real_world/south_fork_american_chili_bar/full_hydraulics",
            "physics/data/real_world/south_fork_american_chili_bar/cooked_flow_fields",
            "physics/data/real_world/south_fork_american_chili_bar/scenario_meat_grinder/cooked_flow_fields",
            "physics/data/real_world/south_fork_american_chili_bar/scenario_troublemaker/cooked_flow_fields"
        };
        foreach (string RelativeRoot in RuntimeRoots)
        {
            string SourceRoot = Path.Combine(RepoRoot, RelativeRoot);
            if (!Directory.Exists(SourceRoot))
            {
                continue;
            }
            foreach (string SourceFile in Directory.GetFiles(SourceRoot, "*", SearchOption.AllDirectories))
            {
                string Extension = Path.GetExtension(SourceFile).ToLowerInvariant();
                if (Extension != ".json" && Extension != ".npy")
                {
                    continue;
                }
                string RepoRelative = Path.GetRelativePath(RepoRoot, SourceFile).Replace('\\', '/');
                RuntimeDependencies.Add(
                    "$(TargetOutputDir)/RaftSimRuntimeData/" + RepoRelative,
                    SourceFile,
                    StagedFileType.NonUFS);
            }
        }
        string CoordinateMapRelative =
            "physics/data/real_world/south_fork_american_chili_bar/production_corridor/photoreal_environment/river_coordinate_map.json";
        string CoordinateMapSource = Path.Combine(RepoRoot, CoordinateMapRelative);
        if (File.Exists(CoordinateMapSource))
        {
            RuntimeDependencies.Add(
                "$(TargetOutputDir)/RaftSimRuntimeData/" + CoordinateMapRelative,
                CoordinateMapSource,
                StagedFileType.NonUFS);
        }
    }
}
