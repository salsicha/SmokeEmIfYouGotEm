using UnrealBuildTool;

public class RaftSimPhysics : ModuleRules
{
    public RaftSimPhysics(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "RaftSimCore", "RaftSimWater" });
        PrivateDependencyModuleNames.AddRange(new[] { "Json" });
    }
}
