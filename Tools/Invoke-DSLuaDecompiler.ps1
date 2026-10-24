param(
    [Parameter(Mandatory = $true)][string]$InputFile,
    [string]$OutputFile,
    [switch]$DebugComments
)

$ErrorActionPreference = 'Stop'
$projectDirectory = Split-Path -Parent $PSScriptRoot
$executable = Join-Path $projectDirectory 'Saved/Research/DSLuaTool/DSLuaDecompiler.exe'
if (!(Test-Path -LiteralPath $executable)) { throw '找不到已编译工具，请查看 docs/research/04-DSLuaDecompiler使用与验证.md。' }
$sourcePath = (Resolve-Path -LiteralPath $InputFile).Path
if ($sourcePath -match '\.(?:luabnd|dcx)$') { throw '这是封包文件，请先使用 WitchyBND 或 Yabber 解包，再选择其中的编译 Lua 文件。' }
$stream = [System.IO.File]::OpenRead($sourcePath)
try {
    $signature = [byte[]]::new(4)
    $read = $stream.Read($signature, 0, 4)
} finally { $stream.Dispose() }
if ($read -ne 4 -or [Convert]::ToHexString($signature) -ne '1B4C7561') {
    throw '输入不包含 Lua 字节码标记。文本 Lua 可以直接阅读，无需反编译；封包需要先解包。'
}
if (!$OutputFile) {
    $OutputFile = Join-Path $projectDirectory ('Saved/Research/DSLuaOutput/' + [IO.Path]::GetFileNameWithoutExtension($sourcePath) + '.dec.lua')
}
$destination = [IO.Path]::GetFullPath($OutputFile)
if ($sourcePath -eq $destination) { throw '输出不能覆盖输入文件。' }
if (Test-Path -LiteralPath $destination) { throw "输出已存在，请指定一个新的 OutputFile：$destination" }
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination)) | Out-Null
$arguments = @($sourcePath, '-o', $destination)
if ($DebugComments) { $arguments += '--insert-debug-comments' }
& $executable @arguments
if ($LASTEXITCODE -ne 0) { throw "反编译程序退出码为 $LASTEXITCODE。" }
if (!(Test-Path -LiteralPath $destination) -or (Get-Item -LiteralPath $destination).Length -eq 0) { throw '工具未产生有效输出。' }
Write-Output "输出：$destination"
if (Select-String -LiteralPath $destination -Pattern 'Warning:|THIS IS LIKELY A DECOMPILER BUG|Unimplemented opcode' -Quiet) {
    Write-Warning '输出含反编译警告，请先检查对应函数，不能直接当成原脚本逻辑。'
}
