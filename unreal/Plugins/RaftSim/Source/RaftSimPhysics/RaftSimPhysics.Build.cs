using UnrealBuildTool;
using System.IO;

public class RaftSimPhysics : ModuleRules
{
    public RaftSimPhysics(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "RaftSimCore" });
        PrivateDependencyModuleNames.AddRange(new[] { "Json" });

        PublicDefinitions.Add("RAFTSIM_WATER_RUNTIME_NAME=\"raftsim_water_cpp_v1\"");
        PublicDefinitions.Add("RAFTSIM_WATER_RUNTIME_HEADER_ONLY_BRIDGE=1");
        PublicIncludePaths.Add(Path.GetFullPath(Path.Combine(ModuleDirectory, "../../../../../physics/cpp/include")));
    }
}
