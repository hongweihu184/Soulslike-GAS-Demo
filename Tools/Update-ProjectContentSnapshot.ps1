param([string]$Date = (Get-Date -Format 'yyyy-MM-dd'))
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$contentRoot = Join-Path $projectRoot 'Content'
$snapshotRoot = Join-Path $projectRoot 'ProjectContentSnapshot/Content'
$manifestPath = Join-Path $projectRoot 'docs/reproduction/project-content-manifest.json'
$previous = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$excluded = @($previous.excluded_mixamo_assets)
$allowedFolders = @('Gameplay', 'Input', 'Maps', '__ExternalActors__', '__ExternalObjects__')
$sourceFiles = @(
    foreach ($folder in $allowedFolders) {
        Get-ChildItem -LiteralPath (Join-Path $contentRoot $folder) -Recurse -File |
            Where-Object Extension -in @('.uasset', '.umap')
    }
    foreach ($name in @('NewMap.umap', 'NewMap_HLOD0_Instancing.uasset')) {
        Get-Item -LiteralPath (Join-Path $contentRoot $name)
    }
)
$selected = @{}
foreach ($file in $sourceFiles) {
    $relative = $file.FullName.Substring($contentRoot.Length).TrimStart('\', '/').Replace('\', '/')
    if ($relative -in $excluded -or $relative.StartsWith('Gameplay/Anims/Roll/Source/')) { continue }
    $selected[$relative] = $file
}
$updated = 0
$entries = @(
    foreach ($relative in ($selected.Keys | Sort-Object)) {
        $file = $selected[$relative]
        $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        $destination = Join-Path $snapshotRoot $relative
        if (-not (Test-Path -LiteralPath $destination) -or
            (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant() -ne $hash) {
            New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
            Copy-Item -LiteralPath $file.FullName -Destination $destination
            $updated++
        }
        if ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant() -ne $hash) {
            throw "Snapshot hash mismatch: $relative"
        }
        [ordered]@{path=$relative; sha256=$hash}
    }
)
$removed = 0
$snapshotPrefix = [IO.Path]::GetFullPath($snapshotRoot).TrimEnd('\') + '\'
foreach ($file in Get-ChildItem -LiteralPath $snapshotRoot -Recurse -File) {
    $relative = $file.FullName.Substring($snapshotRoot.Length).TrimStart('\', '/').Replace('\', '/')
    if (-not $selected.ContainsKey($relative)) {
        if (-not $file.FullName.StartsWith($snapshotPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to remove a file outside snapshot: $($file.FullName)"
        }
        Remove-Item -LiteralPath $file.FullName
        $removed++
    }
}
$totalBytes = ($selected.Values | Measure-Object Length -Sum).Sum
$manifest = [ordered]@{
    date=$Date
    snapshot_files=$entries.Count
    snapshot_mib=[Math]::Round($totalBytes / 1MB, 2)
    excluded_mixamo_assets=$excluded
    files=$entries
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8
[pscustomobject]@{Files=$entries.Count; MiB=$manifest.snapshot_mib; Updated=$updated; Removed=$removed; HashesVerified=$true}
