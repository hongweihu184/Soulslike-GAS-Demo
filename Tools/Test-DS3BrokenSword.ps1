param([string]$Script='Tools/verify_ds3_broken_sword_runtime.py',[string]$Report='Saved/DS3-RuntimeVerification.json',[int]$TimeoutSeconds=90)
$ErrorActionPreference='Stop'
. "$PSScriptRoot/UnrealMcpHelpers.ps1"
$settings=@{refPath='/Script/UnrealEd.Default__EditorPerformanceSettings'}
$toolset='editor_toolset.toolsets.object.ObjectTools'
$original=(Invoke-UnrealTool 'get_properties' @{instance=$settings;properties=@('bThrottleCPUWhenNotForeground')} $toolset)|ConvertFrom-Json
$started=$false
try {
 Invoke-UnrealTool 'set_properties' @{instance=$settings;values='{"bThrottleCPUWhenNotForeground":false}'} $toolset|Out-Null
 Invoke-UnrealTool 'StartPIE' @{options=@{bSimulate=$false;playMode='PlayMode_InViewPort';warmupSeconds=0}} 'EditorToolset.EditorAppToolset'|Out-Null
 $started=$true;$begin=Get-Date
 & "$PSScriptRoot/Invoke-ScopedUnrealPython.ps1" -Script $Script
 $deadline=(Get-Date).AddSeconds($TimeoutSeconds);$fresh=$false
 while((Get-Date) -lt $deadline) {
  if((Test-Path -LiteralPath $Report) -and (Get-Item -LiteralPath $Report).LastWriteTime -ge $begin){$fresh=$true;break}
  Start-Sleep -Milliseconds 300
 }
 if(!$fresh){throw 'No fresh DS3 runtime report before timeout.'}
 $result=Get-Content -LiteralPath $Report -Raw|ConvertFrom-Json
 $result|Select-Object passed,reason,exception|ConvertTo-Json
 $result.tests|ConvertTo-Json -Depth 6
} finally {
 if($started){try{Invoke-UnrealTool 'StopPIE' @{} 'EditorToolset.EditorAppToolset'|Out-Null}catch{Write-Warning $_}}
 $restore=@{bThrottleCPUWhenNotForeground=[bool]$original.bThrottleCPUWhenNotForeground}|ConvertTo-Json -Compress
 Invoke-UnrealTool 'set_properties' @{instance=$settings;values=$restore} $toolset|Out-Null
 Write-Output 'PIE stopped; CPU throttling restored.'
}
