# 属性事件 HUD 与伤害跳字

日期：2026-10-22（工作从 10 月 21 日继续）。用户授权通过虚幻 MCP 新增伤害跳字，并明确玩家、怪物一起改为属性事件更新。

## 已保存实现

- WBP_HUD 删除读取属性的 Event Tick，监听 Health、MaxHealth、Stamina、MaxStamina；WBP_EnemyHUD 监听 Health、MaxHealth。注册完成后主动刷新一次，后续由变化回调调用 RefreshResources。
- InitializeResourceObservers 用 ObserversBound 防止重复注册；目标尚未设置时以单次定时器重试；Destruct 停止监听、清理重试定时器。BP_Dummy 设置 EnemyHUD.TargetActor 后显式初始化。
- 敌人掉血后显示 4 秒、生命归零后保留 1 秒，由可重置定时器负责隐藏。保留出生隐藏、设计预览可见的区别。固定长度、透明背景、只显示红条和延迟白条继续保留。
- 共享 WBP_ResourceBar 的白条等待与平滑追赶保留原动画 Tick。BP_Dummy 原有初始化 Tick 的一次性保护仍在；本轮移除的是 HUD 每帧查询属性，并非关闭角色所有 Tick。
- BP_Dummy 注册 WaitGameplayEffectApplied，读取 Spec 的 Damage 修改量，大于零时生成独立跳字。监听实例缓存并在 EndPlay 停止。同帧两次命中分别生成两个数字。
- WBP_DamageNumber 提供伤害值、世界位置和显示参数；实际生成 WBP_DamageNumberUI 子类。白色粗体、黑色阴影、随机水平偏移，在命中位置上方上浮，默认 0.9 秒，末尾 0.3 秒淡出。投影随摄像机更新；0.016 秒循环定时器仅在跳字存活期间运行，移除时清理。
- 10 月 22 日按用户“注意配置卫生”要求继续清理：已在编辑器控件树中删除模板带入的 HealthBar、StaminaBar，现在仅保留空 Canvas 供 OnPaint 绘制。父类中已被子类覆盖的重复 OnPaint 图也已删除，父类仅保留共享数据参数，实际绘制逻辑只在子类维护。

本轮正式保存：WBP_HUD、WBP_EnemyHUD、BP_Dummy、WBP_DamageNumber、WBP_DamageNumberUI。C++ 未改，无提交/推送或内容快照同步。

## 验证与范围

1. 五个正式蓝图严格编译通过。清理测试资产后重新 PIE：玩家/怪物监听均成功绑定，怪物初始透明度 0；两个 HUD 图中均无属性轮询 Tick。
2. 临时测试器施加真实 GAS 效果：怪物 500→450、当前占比 0.9，白条仍为 1；玩家生命 500→450；体力消耗与并行回复后观测 289/300，HUD 正确更新。
3. 同一帧连续施加两次 50 伤害：生命 500→400，生成两个值为 50 的独立跳字，正常寿命结束后均移除。怪物血条超时隐藏通过。
4. 编辑器恢复可见后捕获画面，确认两次白色“50”显示在怪物头顶上方。为便于截图仅将本次运行中的跳字寿命临时延长至 8 秒，正式资产默认仍为 0.9 秒；最终复核过该默认值。之前过早截图未包含实际绘制帧，不作为显示失败的依据。

临时 BP_UIValidation、GE_UIReset 和关卡测试 Actor 已删除。尚待用户正常键鼠攻击试玩并验收字号、持续时间、位移和连击遮挡；未做大量怪物性能压测，也未实现怪物死亡动作/销毁。

证据位于被忽略的 Saved：UIEvents-RuntimeVerification.json、DamageNumbers-BurstVerification.json、DamageDebug.png、UIEvents-Finalize.json、UIEvents-FinalSmoke.json。修改前备份 LocalBackups/DamageNumbers-2026-10-21。

## 配置卫生复核（2026-10-22）

通过 computer-use 删除两个模板子控件，MCP 核对无 HealthBar/StaminaBar/TargetActor/ObserversBound 自有变量残留，图中无 HUD 属性读取逻辑。父类、显示子类及 BP_Dummy 严格编译通过；只保存两份跳字资产。保存后 DamageNumberUI 的依赖已无 WBP_ResourceBar / WBP_HUD，仅含引擎 UI 模块、字体和跳字父类。设计器层级截图确认只有画布；本轮清理未重新做伤害实机测试。默认 DamageAmount=0、Age=0、ShouldDraw=false、Lifetime=0.9、RiseSpeed=65。备份 LocalBackups/DamageNumberCleanup-2026-10-22，审计 Saved/DamageCleanup-FinalAudit.json。

## 其他蓝图配置卫生复核（2026-10-22）

用户追问其他资产，已检查本轮玩家 HUD、敌人 HUD、跳字父/子类和 BP_Dummy 的变量、所有图及接线。删除 EnemyHUD 的 HideAtTime、GetGameTime 与旧截止时间计算/透明度选择节点；现在仅在掉血时设透明度 1 并重置 HideHealthBar 定时器，属性普通刷新不再重复决定显隐。删除 WBP_HUD 完全未连接的 PreConstruct 和 BP_Dummy 完全未连接的 ActorBeginOverlap 空事件，保留引擎自动 ConstructionScript 入口。

真实 GE_Damage 再测：初始隐藏；100→50 时显示，4.3 秒后隐藏；50→0 时显示，1.3 秒后隐藏。临时 BP_HygieneCheck 及其场景 Actor 已删除。严格编译保存通过。审计 Saved/HUDHygiene-Audit.json、HUDHygiene-Cleanup.json、HUDHygiene-Verification.json、HUDHygiene-EmptyEvents.json。没有对全工程作全面审计，不扩大为所有历史资产均无残留的结论。
