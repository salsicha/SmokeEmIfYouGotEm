# Parser-only fixtures: no engine, native motion or FPS acceptance.
$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'capture_shared_water_map.ps1'),[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Capture script AST invalid'}
$definitions=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Get-RaftSimCompleteFeatureAudit'},$true))
if($definitions.Count -ne 1){throw 'Actual native audit parser missing'}
Invoke-Expression $definitions[0].Extent.Text
function New-Audit {
    $rows=foreach($t in 1..239){
        [pscustomobject]@{world_seconds=$t*.5;world_x_m=0;world_y_m=0;world_z_m=0
            yaw_deg=0;pitch_deg=0;roll_deg=0;speed_mps=.2;velocity_world_x_mps=.2
            velocity_world_y_mps=0;velocity_world_z_mps=0}
    }
    [pscustomobject]@{map='L_SouthFork_Troublemaker';requested_audit_duration_seconds=120
        audit_world_seconds=120;actual_boat_motion=@($rows)}
}
$complete=Get-RaftSimCompleteFeatureAudit (New-Audit) 120 'L_SouthFork_Troublemaker'
if(-not $complete.native_timer_duration_complete -or $complete.actual_samples -ne 239 -or
    $complete.maximum_sample_gap_seconds -ne .5){throw 'Complete native timer observations were not retained'}
$mutations=@(
    {param($a) $a.requested_audit_duration_seconds=60},
    {param($a) $a.audit_world_seconds=119.9},
    {param($a) $a.audit_world_seconds=[double]::NaN},
    {param($a) $a.map='L_Hance'},
    {param($a) $a.actual_boat_motion=@()},
    {param($a) $a.actual_boat_motion[-1].world_seconds=121},
    {param($a) $a.actual_boat_motion[1].world_seconds=.5},
    {param($a) $a.actual_boat_motion[1].speed_mps=[double]::PositiveInfinity},
    {param($a) $a.actual_boat_motion[1].PSObject.Properties.Remove('world_x_m')},
    {param($a) $a.actual_boat_motion=@($a.actual_boat_motion[0..235])},
    {param($a) $a.actual_boat_motion=@($a.actual_boat_motion[0]) + @($a.actual_boat_motion[4..238])},
    {param($a) $a.PSObject.Properties.Remove('requested_audit_duration_seconds')}
)
foreach($mutate in $mutations){
    $fixture=New-Audit;& $mutate $fixture
    $rejected=$false
    try{$null=Get-RaftSimCompleteFeatureAudit $fixture 120 'L_SouthFork_Troublemaker'}catch{$rejected=$true}
    if(-not $rejected){throw 'Incomplete, nonfinite or wrong-map native receipts must refuse'}
}
'PASS: complete 120s native timer observation plus 12 incomplete/malformed controls; parser fixtures only'
