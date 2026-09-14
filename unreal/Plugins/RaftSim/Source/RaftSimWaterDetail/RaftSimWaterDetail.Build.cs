using UnrealBuildTool;

public class RaftSimWaterDetail : ModuleRules
{
    public RaftSimWaterDetail(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "RHI", "RenderCore" });
        PrivateDependencyModuleNames.AddRange(new[] { "Projects" });
        if (Target.bBuildDeveloperTools)
            PrivateDependencyModuleNames.Add("Json");
    }
}
