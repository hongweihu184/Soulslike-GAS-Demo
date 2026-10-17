# AI 交接备忘录(给下一位进场的 AI 助手)

> 这份文件是项目 AI 助手的"记忆备份"。不是对话记录,是提炼后的关键上下文。
> 如果你是刚被叫来协助本项目的 AI:**先读完这份文件,再开口说话**。读完约需 3 分钟,能避免你重蹈覆辙或问出用户已经回答过的问题。
> 最近更新:2026-10-17(按代码、双仓库提交及用户确认同步)

## 0. 新会话引导(上下文自救,先看这个)

**如果你是在一个全新的会话里被叫来继续这个项目**,用户只需对你说一句"读 docs/AI-MEMORY.md 继续"。你按顺序读:
1. 本文件(3 分钟)
2. `docs/checklist.html` —— 当前施工单,干活按这个走,别另起炉灶
3. `docs/reference/troubleshooting.html` —— 错题本 P1~P27,踩过的坑都在,开口给方案前先查它(P19 铁律:节点名/命令/格式必须先在引擎源码或错题本里验证,不许凭记忆)

当前状态一句话:**三连击、命中伤害、体力消耗/回复、HUD，以及攻击期间按输入平滑转向已完成并由用户确认可用。下一步进入翻滚、无敌帧与受击死亡。**

同步规则:每次改动同步对应文档与接手点。C++ 接口以 Source 为准;蓝图配置以保存资产和用户确认为准;提交标题仅作线索。未运行的检查不可写成已验收。

## 1. 项目是什么

- 魂类 ARPG 求职 demo,UE 5.8 + GAS(Gameplay Ability System),主角 Paragon Greystone,Boss Paragon Grux。
- 仓库:https://github.com/hongweihu184/Soulslike-GAS-Demo (外层:代码/文档)
- 本地工程:`E:\UE5.8Project\ProjectUnreal`;引擎:`E:\UE_5.8`
- 素材约 19GB 在 `Content/.git` 内层仓库,**只在本地,不在 GitHub**。迁移/重装时必须整文件夹对拷。
- 主线计划 12 章,见 `docs/index.html` 计划表。技术路线:**C++ 只打地基,90% 玩法在蓝图**。

## 2. 用户画像(重要,决定沟通方式)

- 游戏策划,**零 C++ 基础**(两年前写过 C#,已全忘,不要再提"你会 C#")。
- 英语不佳:解释代码时用中文,英文单词出现时当场翻译。
- 教学偏好(用户亲口反馈):**比喻太多反而不方便看,要直白说明**;要"完整代码逐行讲",不要只讲大概。
- 喜欢把经验沉淀成文档:错题本文化("某天再遇到能快速解决")。每章完成后:更新 index.html 状态 + 写执行记录 + 记错题本 + commit + push。
- 分工约定(用户决定):**C++ 归 AI,编辑器/蓝图/策划工作归用户**。不主动替用户做编辑器点击操作,给清晰步骤即可。

## 3. 环境与机器

- 历史机器记录(本轮未核实):笔记本 i7-12650H / **16GB 内存(最大瓶颈)** / RTX 4070 Laptop。开 UE 前提醒用户关浏览器/Steam/Epic 启动器。
- 历史迁移计划(本轮未核实):**计划迁移**到另一台:i9 14代 / 32GB / 3070 Ti / 4TB,刚重装系统的干净机器(充电器未到货,暂未完成迁移)。
- 网络:需代理,git 已配 `http(s).proxy=http://127.0.0.1:7897`;代理关闭后 push 失败就先怀疑这里(错题本 P12)。
- 装了腾讯电脑管家(QQPCTray):建议过加白名单或退出,可能拖慢文件 IO。
- UE 5.8 的 UBT 需要 .NET 10,**必须用引擎自带 dotnet**:
  `/e/UE_5.8/Engine/Binaries/ThirdParty/DotNet/10.0/win-x64/dotnet.exe /e/UE_5.8/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll [参数]`

## 4. 当前实现与已完成部分

- 工程 C++ 化、GAS 基础、Greystone 接入、三连击、武器碰撞伤害、攻击体力消耗已完成。
- BaseCharacter 纯动词:RequestAttack / CancelAttack / RequestJump / Move2D / Look2D。纯查询:IsMoveLocked / IsAttacking / GetHealthPercent / GetStaminaPercent。
- **空中禁普攻使用虚幻自带功能配置实现;自定义 IsAirborne 已由用户要求删除,不要补回。**
- 输入绑定与门控在 BP_Player。无锁无收刀窗:正常移动、不取消攻击;State.MoveLocked:吞输入;未锁且有 State.MoveCancelWindow:取消攻击后移动。
- ANS_MoveLock / ANS_MoveCancelWindow 管理各自区间;C++ 不包含收刀判别状态机。
- Event.Combo.WindowOpen 由 GA_1/2 解释,授予 GE_ComboWindow_1/2;GA_2/3 分别要求 State.Combo.Window.1/2。
- **窗口事件不立即 EndAbility;蒙太奇完成/取消/打断时结束 GA,Stop When Ability Ends 保持勾选。**
- 阻止矩阵:GA_1=.1;GA_2=.1+.2;GA_3 显式阻止 .1+.2+.3。
- 蓝图注册武器碰撞组件,ANS_AttackWindow 开关判定,C++ 每次挥击目标去重,命中事件携带 Target 与 TargetData;GA 应用 GE_Damage,属性集结算伤害。
- 三个攻击 GA 已补 CommitAbility,每段消耗 20 体力,失败时结束技能(P27)。
- WBP_HUD 已接入生命/体力显示;敌人血条和锁定指示尚待后续章节。
- 当前 DefaultGameplayTags.ini 有 15 条显式注册,分 Ability / State / Event。

## 5. 当前接手点

2026-10-17 用户确认最新版本正常并授权提交 ANS_AttackWindow 改动。当前基线依据 Source/Config、近期双仓库提交与用户确认;本轮未新增编译或运行验收。

攻击转向:蓝图 AnimNotifyState `ANS_AttackTurnWindow` 在通知状态 Tick 中读取 `BP_Player.Current Move Input`,按控制器 Yaw 合成相机相对方向,再用 `RInterp To Constant`(初始 360°/秒)驱动 `Set Actor Rotation`;用户已确认效果成功。三个攻击 Montage 已引用新状态,旧单次通知资产 `AN_AttackTurnToInput` 已删除。临时诊断函数 `BaseCharacter::DebugLogAttackTurn` 仍被 `BP_Player` 蓝图引用,移除调用并清理 C++ 函数之前需先在编辑器确认调用点。

下一步:实现翻滚输入、位移与资源消耗 → 无敌帧与受击死亡 → 敌人 AI。体力回复与攻击转向已完成,第 5~8 章预研只作参考,其中现有配置假设需按当前实现复核。不要重新施工第 4 章。

近期历史基线:外层 4093fa7,内层 5234a9c。本轮在用户确认后同步攻击转向窗口、体力回复与对应文档;本轮行动记录 `docs/log/05-体力回复与攻击转向.md`;当前入口见 checklist.html,设计契约见 design/战斗系统策划案.md,排错见 P24~P29。

## 6. 关键教训(血泪,别再犯)

- **不要碰 `E:\UE_5.8\Engine\` 下的任何缓存/标记文件**(BuildRules、InstalledBuild.txt)。删了只能靠 Epic 启动器"验证"恢复,还可能误触发全引擎重编译(数千任务)。要清理只清工程目录下的 Intermediate/Binaries/.vs。
- **.uproject 的 `"Modules"` 数组被编辑器覆写为空**曾导致游戏模块静默不加载(GE 找不到自定义属性)。症状:蓝图搜不到 C++ 类、日志零报错。解法:补回模块注册(错题本 P14)。
- **VisualStudioTools 插件已在 .uproject 禁用**(启动器版引擎 rules 冲突,错题本 P5/P6)。不要重新启用。
- 编辑器开着时外部编译必失败(Live Coding 锁,退出代码 8):编辑器内 Ctrl+Alt+F11 或关编辑器再编(P3)。
- Live Coding 假成功时先核对清单与编译输出;P4 为历史案例,不要据旧记录删除引擎缓存,遵守引擎目录保护约定。
- 永远不要在 VS 里"生成解决方案"——只生成 ProjectUnreal 项目;引擎测试项目报错(退出代码 6)永远无视(P2)。
- IntelliSense 红线是假错误:重新生成工程文件刷新(P1)。判断对错只看 UBT/Live Coding 输出。

## 7. 常用命令

```bash
# 全量编译(编辑器必须关闭)
/e/UE_5.8/Engine/Binaries/ThirdParty/DotNet/10.0/win-x64/dotnet.exe \
  /e/UE_5.8/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll \
  ProjectUnrealEditor Win64 Development \
  -project="E:\UE5.8Project\ProjectUnreal\ProjectUnreal.uproject" -waitmutex

# 重新生成工程文件(新建类/改插件/红线异常后)
同一 dll,参数换:-projectfiles -project="..." -game -rocket -progress

# 验证游戏模块是否被编辑器加载(模块失踪排查)
powershell -Command '(Get-Process UnrealEditor).Modules | ? {$_.ModuleName -like "*ProjectUnreal*"}'

# git:外层在工程根,内层在 Content/。推送只推外层。
```

## 8. 沟通风格提醒

- 用户的每份文档都要求"以后自己/别人能看懂",写文档像写教材,不像写日志。
- 报错排查时,先区分"真编译错误(有编号有行号)"和"IDE 假错误",并把这个判断过程讲给用户听——这是用户正在学习的核心技能。
- 用户情绪管理:遇到连续翻车会沮丧("没有 AI 我可能已经放弃了")。先稳定情绪、给事实(什么没坏),再给最短路径。
