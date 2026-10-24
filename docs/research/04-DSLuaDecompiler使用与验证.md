# DSLuaDecompiler 使用与验证

2026-10-24，Fork：[hongweihu184/DSLuaDecompiler](https://github.com/hongweihu184/DSLuaDecompiler)，上游：[katalash/DSLuaDecompiler](https://github.com/katalash/DSLuaDecompiler)。当前审查版本 `c27340ab1b898a584748dc7e43a516cc1f1684f6`。

## 当前状态

- 已通过 GitHub API 创建并核实 Fork 的 parent。
- 已下载 Fork 源码到 `Saved/Research/DSLuaForkDownload/DSLuaDecompiler-master`，入口文件哈希与编译使用的上游源码一致。当前 Git HTTPS 克隆连接反复被重置，故本地使用 GitHub 官方 ZIP 源码包，尚无完整 Git checkout；不能将此源码目录当成可直接 push 的克隆仓库。
- 已在本机将上游正式命令行入口编译为 Release，依赖 .NET 9。
- 程序：`E:\UE5.8Project\ProjectUnreal\Saved\Research\DSLuaTool\DSLuaDecompiler.exe`。
- 已检查帮助入口，并用自制的 Lua 5.0 距离决策样例完成正式 CLI 反编译。样例体现小于 140 返回后退到 200，大于 190 返回靠近到 150；它仅用于演示，不是黑魂脚本。
- 公开样例审查结果见 `Saved/Research/DSLuaAudit/REPORT.md`：32 个 Lua50 文件，19 个由原比较器判定匹配；比较器遗漏常量表，输出也有已确认逻辑错误，不能以此推断游戏整体成功率。
- 已取得用户目录中的真实黑魂 3 脚本：43 份全部反编译并重新编译成功，33 份通过包含原始常量的独立严格比较。已按条件给上游 Star 并回读确认。详见 [真实脚本实测与阅读入口](05-黑魂3脚本实测与阅读入口.md)。

## 先验证黑魂 3

README 明确将黑魂 3 列为目标。优先研究敌人 AI 的 Lua 5.0 文件，后续再看角色控制的 HavokScript。反编译 HKS 本身不需要 Havok 编译器，但 HKS 往返编译验证依赖额外的 HavokScript_FinalRelease.dll，仓库没有附带它。

黑魂 2 的敌人 AI 使用 ESD 相关体系，不能作为同一 Lua 工具的直接替代测试目标。[ESD 格式说明](https://soulsmodding.wikidot.com/format:esd)

需要安装目录中已解包的 `Game/script`，或已提取的敌人 Lua 字节码。若只有原始游戏数据包，先用适合该游戏的工具解出数据文件；`*.luabnd.dcx` 仍是二级封包，需要使用 WitchyBND 或 Yabber 继续解包。先检查文件实际头部，不能单凭 `.lua` 扩展名判断它已经是文本源码。

## 操作

在 ProjectUnreal 根目录运行包装入口，将路径换成实际提取出的敌人脚本：

```powershell
./Tools/Invoke-DSLuaDecompiler.ps1 -InputFile 'D:\DS3研究\某个敌人_battle.lua' -DebugComments
```

默认输出到项目 `Saved/Research/DSLuaOutput`。输入不会被修改；已存在输出也不会被覆盖。可以指定 `-OutputFile` 另存。

也可以直接调用正式程序：

```powershell
& './Saved/Research/DSLuaTool/DSLuaDecompiler.exe' 'D:\DS3研究\某个敌人_battle.lua' -o './Saved/Research/DSLuaOutput/enemy.dec.lua' --insert-debug-comments
```

自制演示输入：`Saved/Research/DSLuaAudit/bin/Debug/net9.0/spacing-demo.luac`；原始源码在同目录 `spacing-demo.source.lua`。正式 CLI 的输出示例：`Saved/Research/DSLuaTool/spacing-demo.decompiled.lua`。

## 如何判定对我们可用

1. 选一个有明确游戏内表现的普通近战敌人，记录脚本来源与游戏版本。
2. 完成解包与反编译，逐个检查 warning、空函数、未生成基本块和无法重建的条件。
3. 提取行为选择、距离判断、权重、计时器、Goal/子 Goal 调用及中断条件；函数名先按原样记录，不凭名称推断引擎实现。
4. 对影响结论的条件核对字节码，或用修正过比较器的往返测试及实际行为交叉验证。工具正常退出只证明流程跑通。
5. 能从真实脚本中核实一个对我们有用的行为机制后，再给上游 Star。本轮没有修改游戏文件，也没有安装 Mod 或启动游戏。

## 重新编译

已有源码包：`Saved/Research/DSLuaSource/DSLuaDecompiler-master`。其主 CLI 只依赖核心项目与 System.CommandLine，不要求先准备游戏文件。

```powershell
dotnet publish ./Saved/Research/DSLuaSource/DSLuaDecompiler-master/DSLuaDecompiler/DSLuaDecompiler.csproj -c Release -o ./Saved/Research/DSLuaTool
```

完整测试框架还引用 SoulsFormats Git 子模块；不能用普通 GitHub ZIP 中的空子模块目录直接运行完整解决方案。
