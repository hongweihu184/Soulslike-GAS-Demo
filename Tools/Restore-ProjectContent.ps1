param(
    [switch]$Overwrite
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$snapshotRoot = Join-Path $projectRoot 'ProjectContentSnapshot\Content'
$contentRoot = Join-Path $projectRoot 'Content'

if (-not (Test-Path -LiteralPath $snapshotRoot -PathType Container)) {
    throw "找不到 GitHub 自有资产快照：$snapshotRoot"
}

$snapshotFiles = @(Get-ChildItem -LiteralPath $snapshotRoot -Recurse -File)
if ($snapshotFiles.Count -eq 0) {
    throw "资产快照为空：$snapshotRoot"
}

$conflicts = @()
foreach ($file in $snapshotFiles) {
    $relativePath = $file.FullName.Substring($snapshotRoot.Length).TrimStart('\', '/')
    $targetPath = Join-Path $contentRoot $relativePath
    if (Test-Path -LiteralPath $targetPath -PathType Leaf) {
        $sourceHash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
        $targetHash = (Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash
        if ($sourceHash -ne $targetHash) {
            $conflicts += $relativePath
        }
    }
}

if ($conflicts.Count -gt 0 -and -not $Overwrite) {
    $conflictList = $conflicts -join [Environment]::NewLine
    throw "发现内容不同的同路径文件，未复制任何文件。请先备份并核对：`n$conflictList`n确认覆盖后使用 -Overwrite。"
}

New-Item -ItemType Directory -Path $contentRoot -Force | Out-Null
$copied = 0
$unchanged = 0
foreach ($file in $snapshotFiles) {
    $relativePath = $file.FullName.Substring($snapshotRoot.Length).TrimStart('\', '/')
    $targetPath = Join-Path $contentRoot $relativePath
    $targetDirectory = Split-Path -Parent $targetPath
    New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null

    if (Test-Path -LiteralPath $targetPath -PathType Leaf) {
        $sourceHash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
        $targetHash = (Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash
        if ($sourceHash -eq $targetHash) {
            $unchanged++
            continue
        }
    }

    Copy-Item -LiteralPath $file.FullName -Destination $targetPath -Force:$Overwrite
    $copied++
}

Write-Output "资产恢复完成：复制 $copied 个文件；已有且校验相同 $unchanged 个文件。"
