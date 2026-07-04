using UnrealBuildTool;

public class RaftSimGeo : ModuleRules
{
    public RaftSimGeo(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "RaftSimCore", "RaftSimRiver" });
        PrivateDependencyModuleNames.AddRange(new[] { "Json", "Projects" });
    }
}
