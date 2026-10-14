# AI 交接备忘录(给下一位进场的 AI 助手)

> 这份文件是项目 AI 助手的"记忆备份"。不是对话记录,是提炼后的关键上下文。
> 如果你是刚被叫来协助本项目的 AI:**先读完这份文件,再开口说话**。读完约需 3 分钟,能避免你重蹈覆辙或问出用户已经回答过的问题。
> 最近更新:2026-10-08(第 4 章施工中)

## 0. 新会话引导(上下文自救,先看这个)

**如果你是在一个全新的会话里被叫来继续这个项目**,用户只需对你说一句"读 docs/AI-MEMORY.md 继续"。你按顺序读:
1. 本文件(3 分钟)
2. `docs/checklist.html` —— 当前施工单,干活按这个走,别另起炉灶
3. `docs/reference/troubleshooting.html` —— 错题本 P1~P23,踩过的坑都在,开口给方案前先查它(P19 铁律:节点名/命令/格式必须先在引擎源码或错题本里验证,不许凭记忆)

当前状态一句话:**第 4 章三连击施工中。伤害链已全通(木桩 100→50→0),架构已定为"时间轴即状态机",正在做连击装配(移动锁迁移 ANS + GA 窗口链 + 输入改按标签激活)**。

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

- 当前机器:笔记本 i7-12650H / **16GB 内存(最大瓶颈)** / RTX 4070 Laptop。开 UE 前提醒用户关浏览器/Steam/Epic 启动器。
- **计划迁移**到另一台:i9 14代 / 32GB / 3070 Ti / 4TB,刚重装系统的干净机器(充电器未到货,暂未完成迁移)。
- 网络:需代理,git 已配 `http(s).proxy=http://127.0.0.1:7897`;代理关闭后 push 失败就先怀疑这里(错题本 P12)。
- 装了腾讯电脑管家(QQPCTray):建议过加白名单或退出,可能拖慢文件 IO。
- UE 5.8 的 UBT 需要 .NET 10,**必须用引擎自带 dotnet**:
  `/e/UE_5.8/Engine/Binaries/ThirdParty/DotNet/10.0/win-x64/dotnet.exe /e/UE_5.8/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll [参数]`

## 4. 已完成(勿重做)

- **第 0 章**:嵌套双 git 仓库,GitHub 已推送。
- **第 1 章**:工程 C++ 化。Source 骨架齐全,Target.cs 用 `BuildSettingsVersion.V7`(V5 会报共享环境冲突)。
- **第 2 章 C++ 部分**:`Source/ProjectUnreal/` 下 `MyAttributeSet.h/.cpp`(Health/MaxHealth/Stamina/MaxStamina + 元属性 Damage,PreAttributeChange 钳制,PostGameplayEffectExecute 拆伤害包裹)、`BaseCharacter.h/.cpp`(挂 ASC、IAbilitySystemInterface、BeginPlay 三步打 GE)。编译通过,dll 已出。
- **GameplayTag 根**:已写入 `Config/DefaultGameplayTags.ini`(Ability/State/Event)。
- **文档体系**:`docs/` 下有 index.html(主文档)、tutorial.html(跟做教程,含给 AI 的 star 寄语)、gas-foundation.html(笔记01)、code-walkthrough.html(笔记02 逐行精读)、troubleshooting.html(错题本 P1~P14)、README.md。

## 5. 当前进行中的事(接手点)

**第 4 章进行中 — 里程碑:伤害链全通,三连击施工中(2026-10-08)**。完整施工单见 **docs/checklist.html**(复工清单),当前真实状态:
- 伤害链已打通:按键→GA激活→ANS判定窗→武器碰撞→TargetData 句柄→GA结算→木桩 100→50→0。根因修复:FGameplayEventData 的 Target(Actor) 和 TargetData(句柄) 是两个字段,C++ 补了 `Payload.TargetData = AbilityTargetDataFromActor(OtherActor)`(错题本 P24 待写)
- 标签注册已修复(P23):5.8 只认 `[/Script/GameplayTags.GameplayTagsSettings]` 段的 `+GameplayTagList=`,共 12 个标签(含 State.Combo.Window.1/.2)
- GA_1 配置完:阻止=父级 Ability.Attack.Light、实例化待确认 per Actor;GA_2/3 壳已复制;GE_ComboWindow_1/_2 已建
- **架构新决策(用户拍板):时间轴即状态机**——移动锁改由 ANS_MoveLock(待建)驱动,GA 的 Activation Owned Tags 不再管 MoveLocked;GA 在窗口帧自我了结(StopWhenAbilityEnds=false)
- 遗留破案:AN_SendGameplayEvent 改新通知标签会牵连旧通知,截图已排除图表硬编码,待跑 checklist.html 里的 Python dump 区分"没开实例可编辑"vs"对象共享"
- 体力消耗(GE_Cost 100→80)从未验收过

**接下来(按 checklist.html 顺序):**
0. ~~AN_SendGameplayEvent 共享问题破案~~ **已破(2026-10-08)**:根因=EventTag 变量没开"实例可编辑",当时改的是类默认值所以全体跟着变。现已勾选,预览日志证明三个不同标签值共存、实例独立。**剩余两个小尾巴**:① 蒙太奇 A 上有一个 EventTag=None 的多余通知,要删;② 新通知错设成 `State.Combo.Window.1`(状态标签不能当事件发),要改回 `Event.Combo.WindowOpen`(三段通用,GA 内部各自决定挂 GE_1/_2)
1. 移动锁迁移:GE_MoveLock 配 Infinite+State.MoveLocked(现为壳)→ 新建 ANS_MoveLock → GA 删 MoveLocked → 三蒙太奇拖区间
2. GA_1/2 接窗口链:WaitGameplayEvent(WindowOpen)→ApplyGameplayEffectToOwner(GE_ComboWindow_i)→EndAbility
3. BP_Player 输入换 TryActivateAbilitiesByTag(Ability.Attack.Light)
4. GA_2/3 配置补全(激活所需 Window.1/.2;GA_1 激活阻止=State.Combo.Window 父级)
5. 联调验收(含体力)→ 错题本 P24 → 文档/log/commit/push
- 旧详细记录见 docs/log/04-三连击与伤害.md;C++ OnAttackInput 是死通道(AttackAction 为空),无需处理

## 6. 关键教训(血泪,别再犯)

- **不要碰 `E:\UE_5.8\Engine\` 下的任何缓存/标记文件**(BuildRules、InstalledBuild.txt)。删了只能靠 Epic 启动器"验证"恢复,还可能误触发全引擎重编译(数千任务)。要清理只清工程目录下的 Intermediate/Binaries/.vs。
- **.uproject 的 `"Modules"` 数组被编辑器覆写为空**曾导致游戏模块静默不加载(GE 找不到自定义属性)。症状:蓝图搜不到 C++ 类、日志零报错。解法:补回模块注册(错题本 P14)。
- **VisualStudioTools 插件已在 .uproject 禁用**(启动器版引擎 rules 冲突,错题本 P5/P6)。不要重新启用。
- 编辑器开着时外部编译必失败(Live Coding 锁,退出代码 8):编辑器内 Ctrl+Alt+F11 或关编辑器再编(P3)。
- Live Coding 假成功("up to date" 但代码没编进去)→ 清单损坏,关编辑器删 `Engine/Intermediate/LiveCoding*.json` 全量编译(P4)。
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
