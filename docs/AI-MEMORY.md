# AI 交接备忘录(给下一位进场的 AI 助手)
> **2026-10-23 GitHub归档基线**：用户明确要求提交GitHub。完整Content本地素材提交8ebb61c（33个自有资产改动，无远程）；外层ProjectContentSnapshot已同步为218文件、35.03MiB，并逐文件SHA256校验，继续排除Paragon/Mixamo原素材。包含日志14–22的怪物UI/动画/AI、DamageID选框与25/25/40/25伤害、双方零血销毁及用户保存的MoveSpeed/导航配置。README、恢复盘点、使用文档与精简运行证据同步；新增Update-ProjectContentSnapshot脚本。外层本次提交归档到main并推送origin；完整素材库不推送，Saved/LocalBackups不上传。该归档状态优先于下方各实施日志的历史“未提交”记录。
> **2026-10-23 玩家/怪物零血自动销毁已实现**：用户要求生命0死亡销毁。BP_CombatCharacter在读表及回复GE初始化后监听Health变化并做初始检查；新增IsDead、DeathHealthObserver、CheckForDeath/HandleDeath/StopDeathHealthObserver。零血只执行一次：关闭配置攻击窗→CancelAttack→禁用移动与碰撞→结束监听→可选停止BrainLogic→SetLifeSpan0.01，当前伤害广播结束后下一帧销毁；父类ReceiveDestroyed补监听清理。纯蓝图，无C++/伤害表/蒙太奇改动。三蓝图严格编译保存；真实GE验证双方200→1存活，怪物再1点/玩家再100点归零后销毁，怪物AIController销毁、玩家Controller保留且无Pawn，Saved/Death-RuntimeVerification.json passed=true。详见日志22，备份LocalBackups/Death-2026-10-23。只PIE测试销毁，未存地图；PIE停、节流true、remote=false，打开父类。无死亡动画、尸体或重生，无Git提交推送。
> **2026-10-23 DamageID表驱动已配置并实测，优先于日志20固定伤害实现**：用户指定玩家20001/20002/20003=25/25/40，共用现有WeaponHitBox；怪物30001=25，仅右框。新增Data/ST_AttackDamage和DT_AttackDamage（Enabled、Damage、HitboxIDs Name数组，行名即DamageID）；组件标签PlayerWeapon、Weapon_L/R；新ANS_ConfiguredDamageWindow实例DamageID绑定四蒙太奇，保持原窗口时间。共同父类新增Begin/EndConfiguredDamageWindow和HandleConfiguredDamageHit，按表开框、按窗口目标去重；四GA按事件Magnitude创建GE_Damage Spec并赋SetByCaller DataName=Damage，忽略原C++默认0命中事件，OnEnd关框。无C++改动、无重新挂接/几何改动。实测真实三连击怪物200→175→150→110，怪物右框攻击玩家200→175，左框始终关闭，取消与结束清理通过，严格编译并15资产保存。使用文档docs/design/DamageID配置与攻击框联动.md，技术日志21，Saved/DamageConfig-*验证；备份LocalBackups/DamageConfig-2026-10-23。当前每角色同时一个活动窗口，多DamageID通知不能时间重叠。PIE停、节流true、remote=false，已打开伤害表；无Git提交推送/公开快照更新。
> **2026-10-23 左右攻击框覆盖已修复，优先于日志19旧实现**：用户配置EnemyWeaponHitbox_L/R后指出GA运行时SnapToTarget覆盖位置范围，授权修改。已删除GA Attach/单框Register及缓存；保留两框全部变换/尺寸和weapon_l/r挂点。BP_Dummy专用Open/CloseEnemyAttackWindow只开关两框碰撞，两个Overlap事件窗口内且命中Player0才发Hit；新ANS_EnemyAttackWindow控制原0.30–0.65秒窗口，玩家ANS不改。GA WaitGameplayEvent OnlyTriggerOnce=true使双框同挥击只扣50，OnEnd关闭双框。三蓝图严格编译、保存；PIE左单框200→150、右单框150→100、双框同挥击100→50、取消50→50，逐帧几何及挂点保持，Saved/EnemyHitboxes-RuntimeVerification.json passed=true。详见日志20。PIE停、后台节流恢复true、remote关闭；无C++改动、Git提交推送。用户的框配置是权威来源，不再自动重挂或扩大判定。
> **2026-10-23 怪物伤害链路已保存、待手动试玩**：BP_Dummy新增EnemyWeaponHitbox半尺寸70/45/100，GA首次激活挂weapon_r并注册已有武器重叠事件，先WaitGameplayEvent再播蒙太奇；AM_EnemyAttack的ANS_AttackWindow区间0.30–0.65秒。GA只对Player0施加共享GE_Damage，当前固定50；已有C++按挥击目标去重，OnEndAbility强制关闭判定。严格编译与保存后新PIE验证通过：160距离玩家200→150仅一次，650挥空不扣血，前摇取消不扣血，结束碰撞及标签清理。后台3FPS的离散重叠可漏判，临时解除后台节流正常帧率验证后已恢复；未增加连续扫掠。原220发动距离/5秒冷却保留。详见日志19及Saved/EnemyDamage-RuntimeVerification.json。PIE停止、临时remote关闭，无C++改动、Git提交推送或公开快照同步。本段取代下条“无伤害”的历史状态。
> **2026-10-22 怪物单次攻击与5秒冷却已实现、待手动试玩**：用户先手动完成BB_Enemy/BP_EnemyAIController/BT_Enemy追踪、MoveSpeed表驱动，确认成功，随后授权MCP接攻击。最终树是新BT_EnemyMeleeCombat（原BT_Enemy保留），根Selector：左侧BTT_EnemyAttack附IsAtLocation水平距离220+Cooldown5秒；右侧Sequence MoveTo(TargetActor，中心距离150不附加胶囊半径)→Wait0.2。GA_EnemyAttack独立、单次AM_EnemyAttack，State.Attacking/MoveLocked持有到Completed/Interrupted/Cancelled退出；无伤害、成本、感知或脱战。BTT停步、水平朝向目标、按类激活GA，Tick等攻击标签移除后结束；Abort取消怪物攻击并FinishAbort。控制器OnPossess先查攻击类别能力防重，再GiveAbility，然后用户原黑板赋值→Run新树；BP_Dummy StartupAbilities保持原空列表。严格编译和树包重载/重开通过；PIE仅1技能，160/114.64距离发动，冷却中以300速度追踪600外目标，结束到下次开始约6.67秒（后台约3FPS，配置门槛5秒），中止后标签清零/蒙太奇停止。详见日志18及Saved/EnemyCombat-RuntimeVerification.json。曾清理临时蓝图触发编辑器崩溃；原生图修复风险经自动审批拒绝后向用户说明，用户明确“允许”再执行，最终已验证持久保存。失败草稿卸载后归档LocalBackups/EnemyCombat-2026-10-22/FailedDrafts。临时远程接口收尾关闭；无Git提交推送或公开快照同步。不得声称已完成怪物造成伤害或玩家手感验收。
> **2026-10-22 怪物基础动画已保存**：用户授权MCP制作移动状态机和一个单次攻击蒙太奇，黑板/行为树由用户手动复习创建。新增Gameplay/Anims/Enemy下ABP_EnemyMelee、BS_EnemyMove、AM_EnemyAttack。超级兵SK_Minion_Lane_Super骨架；Ground播放资源包混合空间副本（Y=Speed、X=0；待机0/战斗跑420/快速跑700），Locomotion→DefaultSlot→输出。事件图有效Pawn→VelocityXY→Speed，移除玩家空中状态。蒙太奇Attack_A_Dusk约1.1秒、单段一次、倍率1、自动混出，无攻击判定通知。BP_Dummy类默认与关卡中原先AnimClass=None的实例均已接新动画；外部Actor单独保存，修改前备份LocalBackups/EnemyAnimation-2026-10-22。ABP/Dummy严格编译；PIE真实动画类、实际移动Speed=200/位移约200/停止Speed=0、蒙太奇播放并自然结束验证通过。未做怪物GA、AI或命中伤害、未验收滑步/战斗手感。MCP动画节点限制使用官方本机Python接口补齐，临时远程设置收尾恢复关闭。用户提出GE/标签共用、GA各自独立，助手建议采用，细节见日志17；不要把建议写成已完成GA。无Git提交推送/快照同步。
> **2026-10-22 属性事件 HUD 与伤害跳字已通过 MCP 实现并保存，优先于下方旧轮询/未做跳字记录**：玩家 WBP_HUD 监听 Health/MaxHealth/Stamina/MaxStamina，怪物 WBP_EnemyHUD 监听 Health/MaxHealth，均无查询属性的 Event Tick；保留 ResourceBar 白条动画 Tick。初始化防重入、目标未就绪定时重试，Destruct 停止监听并清理定时器。怪物隐藏改为可重置定时器，仍出生隐藏/掉血4秒/归零1秒、预览可见；BP_Dummy 仍有旧的一次初始化 Tick 保护分支。BP_Dummy 监听实际 GameplayEffectApplied 的 Damage，独立生成 WBP_DamageNumberUI（继承 WBP_DamageNumber 数据参数）：白字黑影、随机偏移、上浮、0.9秒寿命、末尾0.3秒淡出，定时器仅随跳字存活。真实 GE 验证双方血量和玩家体力更新、敌条超时隐藏、同帧两次50分别跳字且到期清理；可见编辑器截图已确认两次50，截图临时延长运行实例寿命但资产默认仍0.9。五蓝图严格编译、清理测试资产后PIE初始化复测通过。用户尚未键鼠战斗/视觉手感验收，未做怪物数量压测。随后用户要求配置卫生，已真正删除显示子类的 HealthBar/StaminaBar，控件树只剩 Canvas；删除父类重复 OnPaint，实际绘制只在显示子类维护。三蓝图严格编译、保存两跳字资产，依赖核对无 ResourceBar/HUD；后续又清理 EnemyHUD 的 HideAtTime 旧截止时间判断及 HUD/Dummy 两个无接线空事件；真实GE验证100→50显示/4秒隐藏、50→0显示/1秒隐藏通过，临时测试资产与Actor已清理。备份 LocalBackups/DamageNumberCleanup-2026-10-22。详见日志16；Saved存测试证据，LocalBackups/DamageNumbers-2026-10-21存备份。无C++改动、Git提交推送或快照同步。

> **2026-10-21 怪物血条固定长度及无背景已保存，优先于下条的长度描述**：用户明确怪物仅显示当前红条和延迟白条，背后没有背景/框，最大生命多少均同长。WBP_ResourceBar 新增 UseFixedLength、FixedLength（实例可编辑），UpdateResourceBar 选择固定宽度或原容量比例计算；PreConstruct 支持固定长度预览。新增 OverrideBackground（默认false）和 BackgroundBrush，只在启用覆盖时更新 PB_Trail 背景画刷，保留填充/跑马灯样式；前条背景原本已透明。WBP_EnemyHUD.HealthBar 配置固定200（保留用户当时长度上限200）、覆盖背景=NoDrawType且Alpha0。玩家实例继续比例长度、不覆盖背景。MCP严格编译、PIE测试50/100/500最大生命下宽度均200、占比0.5；玩家实际宽度1200/800符合各自原比例规则；截图确认怪物红条和白条可见且无底框。仅保存ResourceBar和EnemyHUD，本轮前已有的WBP_HUD、BP_Dummy及关卡外部Actor修改未覆盖或提交。无Git同步、未更新快照。审计Saved/ResourceBarStyle-RuntimeVerification.json，备份LocalBackups/MonsterBarStyle-2026-10-21。

> **2026-10-21 怪物血条已通过 MCP 接入，待用户试玩**：新增 WBP_EnemyHUD，复用现有 WBP_ResourceBar；BP_Dummy 添加 EnemyHUD 屏幕空间组件，在首次 Tick 显式配置位置/尺寸、创建 HUD、绑定 TargetActor=self 并缓存实例，EnemyHUDBound 阻止重复创建。HUD 每帧读取目标 Health/MaxHealth，出生隐藏、掉血后显示4秒并刷新截止时间、归零后保留1秒；时长可编辑，未实现怪物死亡动作/销毁。原 ResourceBar、玩家 HUD、C++ 未改。严格编译通过，PIE 临时属性 100→75→60→0 验证显示/刷新/超时/归零隐藏及拖尾；另已截图确认头顶红条位置，未做真实攻击闭环或玩家手感验收。已保存两份蓝图并打开 EnemyHUD，无 Git 提交/推送、未更新快照。跳字仅提出独立 WBP_DamageNumber + 伤害结算事件方案，未创建。备份 LocalBackups/MonsterHUD-2026-10-21，审计 Saved/MonsterHudRuntimeVerification.json。官方 scene.save_actor 对外部 Actor 包的 exists 检查失败，因此最终不依赖关卡实例配置保存，运行时初始化覆盖已有实例旧配置。

> **2026-10-21 本轮已验收并授权同步，优先于下方待审核记录**：用户试玩翻滚衔接反馈“很好，很舒适”，随后明确“这个我们改好了”，要求 Git/GitHub/skill/日志同步。正体力启动且扣后归零、五个 GA 主动成本 GE、GA_Roll 窗口重触发按本轮完成归档。用户自行调整并保存 AM_Roll 通知，编辑器已正常关闭。日志13记录实现与证据范围，不补写逐项边界测试。统一输入缓存已列清单、暂不做；用户同意后续先讲清小块蓝图再修改、改完沿线复盘。保留无敌帧、受击死亡、旧攻击取消窗口核对及近战敌兵行为树等待办。素材六文件及外层快照、skill案例004/005随本轮同步。

> **2026-10-21 翻滚接翻滚配置已保存**：用户授权 MCP 配置，通知轨道位置由用户自行放置。已仅修改 GA_Roll：bRetriggerInstancedAbility=true，移除 BlockAbilitiesWithTag 自身 Ability.Roll；CanActivateAbility 保留体力/属性有效性并增加“非 State.Rolling 或 State.RollCancelWindow”。复用原 ANS_RollCancelWindow / GE_RollCancelWindow，未新建 RollChainWindow；成功扣费到蒙太奇之间和 OnEndAbility 各清理一次 State.RollCancelWindow。严格编译和节点/配置核对通过；AM_Roll 哈希不变，已打开蒙太奇和通知资产。用户下一步在 AM_Roll 后摇放 ANS_RollCancelWindow，再测连滚；尚无窗口内外衔接或位移清理的实机验收。无输入缓存、无提交推送。修改前 GA_Roll 备份 LocalBackups/RollChain-2026-10-21；审计 Saved/RollChainBeforeAudit.json、RollChainAfterAudit.json。下方“此项尚未修改”等为历史。

> **后续讨论**：用户要求将统一输入缓存列入后续清单，暂不实现；已记入策划案第9节。翻滚接翻滚先讨论“窗口内按键打断后摇”，不含缓存。只读 MCP 确认 GA_Roll 的 InstancingPolicy=InstancedPerActor、bRetriggerInstancedAbility=false，BlockAbilitiesWithTag 包含 Ability.Roll；后续若采用原生重触发需移除此自阻止并在 CanActivateAbility 中限制正在翻滚时必须有衔接窗口。此项尚未修改资产。

> **2026-10-21 体力规则续作，待用户审核**：用户明确要纯蓝图“Stamina > 0 即可发动，扣后最低归零”，不做负数透支，并授权通过虚幻 MCP 修改。已改并保存 GA_Attack_Light_1/2/3、GA_Roll、GA_Jump：默认 Cost 槽清空，K2_CanActivateAbility 用传入 ActorInfo 的 ASC 读体力并判断 >0；激活图再次检查、CommitAbility 成功后主动应用原 GE_Cost 一次，再进入原动作。三段攻击实际旧节点为 CommitAbilityCost 且结果未分支，本轮已统一为 CommitAbility+成功分支。C++、原成本 GE、恢复 GE 未改。五个蓝图 warnings_as_errors 编译和接线审计通过，PIE 启停通过，尚未实际验证5点/0点边界和连续动作手感。已打开第一段攻击供审核，未提交推送，未更新快照。修改前五个资产备份在 LocalBackups/StaminaPositiveGate-2026-10-21；前后审计在 Saved/StaminaBeforeAudit.json、StaminaAfterAudit.json。下方“余额必须足额”“Cost由Commit自动扣”等旧说明已被本条更新。

> **2026-10-21 最新收工，优先于下方历史计划**：用户要求保存、Git/GitHub和skill同步，今天停止。新WBP_ResourceBar已接HUD两份，变量绑定Percent；首次同步、消耗等待0.3秒、恒速追赶0.5比例/秒、回复同步、数值不变不重置倒计时；长度按MaxValue×LengthPerPoint并Clamp至MaxLength，厚度独立覆盖，BarColor实例控制前条颜色。用户确认体力基本正常及体力条变绿，生命消耗因暂无可战斗敌兵暂不测。预览刷新、默认BarColor透明度/白条背景及实际长度调参仍待复核。编辑器已关闭，按已落盘UI和AM_Roll存档；不要写成新完整回归。日志12和skill案例002/003已同步，EasyGas已放弃、原生属性集保留。下次先简查UI遗留，再第一只近战敌兵行为树及战斗闭环；继续保留无敌帧、受击死亡和取消窗口待办。用户希望蓝图学习，说明时分清变量Get与同名绑定函数，不能在绑定函数递归调用自身。

> 最新（2026-10-20）：用户否决EasyGas，不再作为下一步；保留原生属性集，继续玩法蓝图化。已把移动/视角迁到BP_Player.MoveFromInput / LookFromInput，删除C++ Move2D/Look2D；原门控/输入未改。完整C++编译、重开蓝图编译、PIE初始化及临时探针实际位移/Yaw/Pitch输出均通过，临时资产已清理。尚待用户手动键鼠与取消窗口验收。详见日志11，优先于下方历史“先装EasyGas”的旧计划。

> 战斗策划 Skill（2026-10-20）：用户授权开始制作并逐步强化。项目内入口 `.agents/skills/combat-design/SKILL.md`，协作案例在 `docs/design/combat-design-learning.md`。后续涉及战斗设计时读取并按真实取舍、纠正和验证结果维护；当前尚无已提炼的个人战斗设计原则，不把助手建议写成用户风格。此次仅制作本地草稿，尚未发布。

> **最新收工基线（2026-10-20，优先于下方历史提示）**：用户已手动测试走、跑、跳，暂未发现bug，并授权Git/GitHub存档。AI已完成三个角色蓝图编译、双方差异表值PIE验证，数值恢复100/100。继承为 C++ BaseCharacter → BP_CombatCharacter → BP_Player / BP_Dummy；敌兵读Enemy_Melee，玩家读Player。素材本地提交2b1d778，外层功能快照d6da680；本轮追加日志后推送外层main，完整Content不推送。明日先检查/获取免费EasyGas的UE5.8包并在测试属性集验证，成功后分步迁移剩余C++；未安装前不删除MyAttributeSet。之后继续UI黄条即时扣、白条延迟追赶，再敌兵行为树。未验收攻击、翻滚完整战斗与HUD视觉，不把走跑跳验收扩写为全功能通过。旧BP_BaseCharacter路径为历史资产，使用新共同父类，不按旧段落重做。

> 最新完成（2026-10-20）：官方MCP已完成继承整理，C++ BaseCharacter → 新BP_CombatCharacter → 原BP_Player / BP_Dummy。共同父类拥有读表函数、CharacterStatsRowName和出生初始化/回复，玩家行Player、木桩行Enemy_Melee；清空玩家旧InitAttributesEffect以防C++覆盖表值，GE顺序改为先上限后当前。三蓝图编译通过，PIE差异表值玩家200/150、敌兵300/80正确，已恢复100/100；玩家五个技能保留。尚未手动战斗回归；EasyGas未安装，C++未删。详见日志10，以本段替代此前“未改继承”的旧状态。

> 最新迁移状态（2026-10-20）：用户接受先评估蓝图属性替代，但明确优先免费，不购买。官方UE5.8.3 MCP已启用并成功测试创建/接线/编译独立蓝图，测试资产已清理；现有玩法未改。免费属性候选EasyGas须从Fab取得完整UE5.8包，尚未安装验证。BP_Player行名=Player，BP_Dummy无行名属性，旧BP_BaseCharacter路径疑似重定向至Player，需审计后重建共同父类。详见日志09后半节。不得直接删除旧属性集。

> 2026-10-20 收工：用户已建蓝图结构/数值表（Player、Enemy_Melee，木桩共用敌兵行）、初始化 GE 和读表函数。最后截图为 BeginPlay → 体力回复GE → Initialize Stats from Table，节点 Target is BP Player，未显示父类 BeginPlay；下次核对函数归属、父类执行顺序、角色行名和最终 GE 配置后再 PIE 测试。尚未验收，用户睡觉，详见日志08末节。

> 学习提醒（2026-10-20）：用户明确说 GE / Spec / Context、为什么需要 Spec 是知识盲区，目前尚未理解，要求记录以便以后复习。详见 docs/notes/gas-spec-context.md。解释过不等于掌握；教学先讲每个节点目的、输入输出，再接线，避免用更多术语解释术语。当前绿色 Make Context / Make Outgoing Spec 是纯节点，不接白线；Assign 共用同一个 Spec，串联只是更清楚，不是唯一有效接法。角色数值表蓝图已由用户创建，初始化函数正教学接线，尚未确认调用与 PIE 验收。

> 2026-10-19 最新决定：角色数值表 → UI → 行为树，全部优先蓝图教学。用户希望逐步迁移纯蓝图、减少黑箱；不要再默认添加 C++ 功能。已删除本轮 CharacterStatsRow.h、CharacterStats 属性和 C++ 读表初始化，保留原战斗/GAS 地基。已获用户授权删除旧 DT_CharacterStats.uasset，撤除新增 C++ 后完整编译成功；CSV 保留。下一步用户创建 ST_CharacterStats 蓝图结构，再新建数据表。详见日志08。

> 这份文件是项目 AI 助手的"记忆备份"。不是对话记录,是提炼后的关键上下文。
> 如果你是刚被叫来协助本项目的 AI:**先读完这份文件,再开口说话**。读完约需 3 分钟,能避免你重蹈覆辙或问出用户已经回答过的问题。

> 最近更新：2026-10-19 体力与跳跃续作。用户确认翻滚第一版可用并授权 Git/GitHub 同步。最新基线以下文和日志06末节为准。

> 当前翻滚：Mixamo Stand To Roll → Greystone，IA_Roll=左 Shift，GA_Roll→AM_Roll，UpperBody 插槽，蒙太奇 Rate Scale=2；序列根运动关闭、强制根锁定开启，ANS_AttackLungeWindow 驱动位移，ANS_AttackTurnWindow 转向。移动取消与翻滚后摇接攻击已配置。

> 已修复：AbilityRoll 默认标签容器为空（P33）；新蒙太奇默认插槽不匹配（P22）；混出后打断使旧翻滚不退出，已开启 Allow Interrupt After Blend Out（P32）；攻击输入误查 RollCancelWindow，现改查 AttackCancelWindow（P34）。用户做 PIE 手感验收，AI 只读复核保存资产，没有另跑完整回归。

> 最新体力：成本 GE 整理至 Gameplay/GAS/Effects/Cost，攻击/翻滚/跳跃当前都是25；GA_Jump 已授予并接入输入，State.Jump 随技能保持至落地。Jump → WaitMovementModeChange（Walking）→ On Change → EndAbility，修复跳跃状态瞬间消失导致空中回复的问题（P36），用户确认成功。GE_StaminaRegen 当前每0.05秒+2，持续排除 State.Attacking / State.Rolling / State.Jump。成本选择暂用复制 GE，未实现动态通用成本。详见日志07，素材提交9ce6c33。

> 下一步：继续无敌帧、受击死亡；此前攻击上的 RollCancelWindow 仍需核对输入消费及早段/后段意图，本轮未施工该规则。原三连击阻止矩阵保留。

> 归档：Content 内层 Git 保存完整已保存资产，只在本地提交；GitHub 保存自有玩法快照，不上传 Mixamo 动作序列及源预览资源。原 FBX 和本轮变更资产压缩包在 LocalBackups（被外层 Git 忽略）。恢复见 docs/reproduction/content-inventory.md；详情见 docs/log/06-翻滚动画导入与重定向.md。

## 0. 新会话引导(上下文自救,先看这个)

**如果你是在一个全新的会话里被叫来继续这个项目**,用户只需对你说一句"读 docs/AI-MEMORY.md 继续"。你按顺序读:
1. 本文件(3 分钟)
2. `docs/checklist.html` —— 当前施工单,干活按这个走,别另起炉灶
3. `docs/reference/troubleshooting.html` —— 错题本 P1~P27,踩过的坑都在,开口给方案前先查它(P19 铁律:节点名/命令/格式必须先在引擎源码或错题本里验证,不许凭记忆)

当前状态一句话：**三连击、伤害、攻击体力消耗/回复、HUD、攻击转向和翻滚第一版已完成。翻滚、跳跃体力已接入，空中暂停回复、落地恢复；下一步核对取消窗口输入，继续无敌帧与受击死亡。**

同步规则:每次改动同步对应文档与接手点。C++ 接口以 Source 为准;蓝图配置以保存资产和用户确认为准;提交标题仅作线索。未运行的检查不可写成已验收。

## 1. 项目是什么

- 魂类 ARPG 求职 demo,UE 5.8 + GAS(Gameplay Ability System),主角 Paragon Greystone,Boss Paragon Grux。
- 仓库:https://github.com/hongweihu184/Soulslike-GAS-Demo (外层:代码/文档与自有资产快照)
- 本地工程:`E:\UE5.8Project\ProjectUnreal`;引擎:`E:\UE_5.8`
- 完整 `Content/` 约 19GB，主体为 8 个 Paragon 资源包；`Content/.git` 本地历史约 12.44 GiB，禁止直接推送到 GitHub。
- GitHub 通过 `ProjectContentSnapshot/Content/` 保存工程自有蓝图、输入、地图和外置 Actor 快照（195 个文件，约 32.94 MiB）；恢复细则见 `docs/reproduction/content-inventory.md`，复制脚本为 `Tools/Restore-ProjectContent.ps1`。
- 换机时取得有权访问的 Paragon 资源包后再运行恢复脚本；脚本默认拒绝覆盖不同内容。新增/修改自有 `.uasset` 后，需同步更新快照并提交外层 Git。
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
- 当前 DefaultGameplayTags.ini 有 21 条显式注册,分 Ability / State / Event。

## 5. 当前接手点

2026-10-19 最新续作：先读日志07及 P35/P36。翻滚成本已完成，旧段落“Cost为空”仅为此前基线。跳跃 GA 必须等落地再结束；成本目录移动后不要恢复旧 GE_Cost / 旧路径 GE_StaminaRegen。当前成本和回复数值见日志07。

本次素材提交 `cca12f5`；公开自有资产快照 195 文件、约 32.94 MiB，完整清单见 docs/reproduction/project-content-manifest.json。缺动作时先看 docs/notes/mixamo-animation-workflow.md，其中记录下载选项、无模型 FBX 的处理、重定向边界和可复用提示词；不要直接运行 Roll 专用脚本覆盖既有资源。

用户在 2026-10-19 确认基础翻滚版本可用并要求收工备份。接手时先读日志06的“收工基线”，再读错题本 P22、P32~P34。不要按旧预研把整段攻击/翻滚标签当成互相禁止条件，取消时机由时间轴窗口决定。

复核窗口接线时区分 RollCancelWindow（攻击上，允许滚）和 AttackCancelWindow（翻滚上，允许攻击）。当前只完成后者的输入查询；攻击中翻滚窗口尚待补接。不要把“通知已放”当成“窗口已被输入消费”。

临时 DebugLogAttackTurn 仍在 C++，可能仍有蓝图引用；清理前先核对。体力基础值上限保护已编译，长期满体力再扣费的专项验收仍待确认。攻击位移曾因滑步被关闭，最终攻击蒙太奇仍有位移通知；后续修改以实际窗口和速度为准，不擅自删除用户调参结果。

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

> 2026-10-20 用户明确授权 AI 通过 Unreal MCP 操作蓝图并迁移旧C++玩法，先Git存档。素材存档d0ab72d；工具尚未接入。原生GAS属性集不可直接删除，已问用户迁移范围，详见日志09。
