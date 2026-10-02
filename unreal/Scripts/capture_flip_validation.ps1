<# Actual production raft and native water-force lab; not a pose animation.
   Every invocation requires fresh evidence and a shared-engine idle minute.
   Stable drag remains an explicit lab candidate, not a gameplay promotion.
#>
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9_.-]+$')][string]$Scene,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9_.-]+$')][string]$Label,
    [ValidateRange(60,900)][int]$TimeoutS=600,
    [ValidateRange(12,40)][int]$DurationSeconds=12
)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $root "tmp/$Label"
$receipt=Join-Path $root "unreal/Saved/FlipDemo/$Label.json"
if((Test-Path -LiteralPath $out) -or (Test-Path -LiteralPath $receipt)){throw 'Preserve prior evidence; use a fresh label'}
$known=@('calm','small_broadside','large_broadside','large_broadside_mirror','large_bow_on','eddy_line',
    'hydraulic_broadside','rock_oblique','breaking_broadside','breaking_broadside_mirror',
    'breaking_broadside_1p8m','breaking_broadside_2m','breaking_broadside_2p4m',
    'breaking_broadside_2p4m_mirror','breaking_bow_on_2p4m','pinned_breaker',
    'breaking_broadside_2p8m','breaking_broadside_3p2m','breaking_broadside_3p2m_mirror','breaking_bow_on_3p2m',
    'rolling_entry_control','rolling_entry_port','rolling_entry_starboard','rock_pillow_broadside','rock_pillow_calm')
if($Scene -notin $known){throw 'Unknown native flip scene'}
$deadline=(Get-Date).AddMinutes(15);$idleSince=$null
do {
    $busy=@(Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match '^(UnrealEditor|UnrealBuildTool|SmokeEm|raftsim_cartesian_cook|raftsim_water_solver|blender|link\.exe)' -or
        ($_.Name -in @('dotnet.exe','cmd.exe') -and $_.CommandLine -match 'UnrealBuildTool|Build\.bat|RunUAT|AutomationTool')
    })
    if($busy.Count){$idleSince=$null}
    elseif($null -eq $idleSince){$idleSince=Get-Date}
    if($null -ne $idleSince -and ((Get-Date)-$idleSince).TotalSeconds -ge 60){break}
    if((Get-Date) -ge $deadline){throw 'Other engine work remains active; no duplicate launched'}
    Start-Sleep -Seconds 5
} while($true)
New-Item -ItemType Directory -Path $out | Out-Null
$binary='C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$dll=Join-Path $root 'unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-RaftSimRaft.dll'
$physicsDll=Join-Path $root 'unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-RaftSimPhysics.dll'
$arguments=@((Join-Path $root 'unreal/SmokeEmIfYouGotEm.uproject'),'/Game/RaftSim/Maps/L_RaftSimTestTank',
    '-game','-RaftSimEphemeralProfile','-RaftSimFlipStableDragCandidate','-RenderOffscreen','-Unattended',
    '-NoSplash','-NoSound','-d3d12','-ResX=1280','-ResY=720','-Windowed',
    "-RaftSimFlipValidationDuration=$DurationSeconds",
    "-AbsLog=$out/engine.log","-ExecCmds=raftsim.RecordingDir $out,RaftSim.FlipDemo $Scene $Label")
$launch=[ordered]@{schema='raftsim.native_flip_validation_launch.v1';scene=$Scene;label=$Label;
    scope='Actual production mesh/crew and sampled authored-water forces. Lab-only pressure/implicit-drag candidate; normal gameplay unchanged.';
    raft_dll_sha256=(Get-FileHash -LiteralPath $dll -Algorithm SHA256).Hash.ToLower();
    physics_dll_sha256=(Get-FileHash -LiteralPath $physicsDll -Algorithm SHA256).Hash.ToLower();
    arguments=$arguments;requested_duration_seconds=$DurationSeconds;launched_at=(Get-Date).ToUniversalTime().ToString('o')}
$start=New-Object System.Diagnostics.ProcessStartInfo
$start.FileName=$binary;$start.WorkingDirectory=$root;$start.UseShellExecute=$false;$start.CreateNoWindow=$true
$start.Arguments=($arguments | ForEach-Object {'"'+[regex]::Replace([regex]::Replace($_,'(\\*)"','$1$1\"'),'(\\+)$','$1$1')+'"'}) -join ' '
$process=[System.Diagnostics.Process]::Start($start);$launch['owned_process_id']=$process.Id
if(-not $process.WaitForExit($TimeoutS*1000)){
    $process.Kill();$launch['timed_out']=$true
    $launch | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath "$out/launch.json" -Encoding UTF8
    throw 'Only this owned validation process was stopped after timeout'
}
$process.WaitForExit();$launch['exit_code']=$process.ExitCode
$launch['finished_at']=(Get-Date).ToUniversalTime().ToString('o')
$launch | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath "$out/launch.json" -Encoding UTF8
if($process.ExitCode -ne 0){throw "Native flip process exited $($process.ExitCode)"}
if((Get-FileHash -LiteralPath $dll -Algorithm SHA256).Hash.ToLower() -ne $launch.raft_dll_sha256 -or
    (Get-FileHash -LiteralPath $physicsDll -Algorithm SHA256).Hash.ToLower() -ne $launch.physics_dll_sha256){throw 'Loaded code changed during validation'}
$log=Get-Content -LiteralPath "$out/engine.log" -Raw
$errors=@([regex]::Matches($log,'(?m)^.*\bLog\w+: (?:Error|Fatal):[^\r\n]*') | ForEach-Object {$_.Value})
$videos=@(Get-ChildItem -LiteralPath $out -Filter '*.mp4')
if($errors.Count -or -not (Test-Path -LiteralPath $receipt) -or $videos.Count -ne 1){throw 'Incomplete or error-bearing native flip evidence'}
Copy-Item -LiteralPath $receipt -Destination "$out/motion.json"
$motion=Get-Content -LiteralPath "$out/motion.json" -Raw | ConvertFrom-Json
if($motion.failed -or $motion.simulated_seconds -lt $DurationSeconds-.01){throw 'Native motion failed or incomplete; retain evidence, no acceptance'}
[ordered]@{scene=$Scene;label=$Label;receipt="$out/motion.json";video=$videos[0].FullName;
    first_capsize_seconds=$motion.first_capsize_seconds;minimum_up_z=$motion.minimum_up_z;
    rendered_fps_mean=$motion.rendered_fps_mean;initial_up_z=$motion.initial_up_z;
    initial_omega_rad_s=$motion.initial_omega_rad_s} | ConvertTo-Json
