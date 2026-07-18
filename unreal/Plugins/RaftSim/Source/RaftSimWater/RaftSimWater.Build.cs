using UnrealBuildTool;
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
    }
}
