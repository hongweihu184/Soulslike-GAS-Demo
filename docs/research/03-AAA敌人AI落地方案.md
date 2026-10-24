# AAA 敌人 AI 落地方案：公开资料核查

检索日期：2026-10-24。以下区分开发者/官方公开材料、社区工具作者的直接研究，以及对本项目的建议。公开案例不代表所有AAA或同系列后续作品都采用相同架构。

## 黑暗之魂：能确认什么

未找到 FromSoftware 官方公开的、可直接对应我们这棵“追击—警戒—攻击”树的完整敌人实现图。因此不能声称《黑暗之魂》就是用UE式Behavior Tree搭建，也不能仅凭游戏表现判定底层架构。

社区工具作者提供了更具体的技术证据：

- [DSLuaDecompiler 作者说明](https://github.com/katalash/DSLuaDecompiler)：其工具直接处理 FromSoftware 游戏中的 Lua AI 脚本，并区分 Lua AI 脚本与部分作品中的 HavokScript 角色控制逻辑。这是工具作者的一手技术说明，**不是开发商官方披露**。
- [DS1 Lua AI Common Function Repository](https://www.soulsmodding.com/doku.php?id=common-refmat%3Alua_ai_common_function_repository)：作者整理了 `AddSubGoal`、接近目标、转向、等待、攻击、接近后攻击等调用；包含完成距离、持续时间、移动方式和转向等参数。与我们的设计目标相近，但不能由此把其整套系统直接命名为UE行为树或GOAP。
- [ESD格式研究](https://soulsmodding.wikidot.com/format%3Aesd)：社区格式文档指出DS2的敌人AI使用AI ESD，提示**同一系列不同作品也可能有不同实现**，不宜把一代结论套用到全系列。

对本项目的启发：行为应有明确的开始、完成、失败与中止条件；接近、转向、攻击是可组合的执行单元。是否使用Lua、行为树或状态机，是工程组织方式，不决定最终战斗手感。

## 可核查的商业项目方案

| 项目与资料 | 公开实现要点 | 我们可以借鉴什么 |
|---|---|---|
| 《Halo 2》：[Microsoft官方AI行为表](https://learn.microsoft.com/en-us/halo-master-chief-collection/h2/ai/aibehaviorlist) | 明确列出行为树Root、Engage子树、Fight、Melee charge等行为；参数由角色数据配置 | 主干职责、可组合行为、数据调参；这是历史案例，不能称为最新方案 |
| 《最后生还者》：Mark Botta，[Infected AI in The Last of Us](https://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter33_Infected_AI_in_The_Last_of_Us.pdf)，第33章 | 高层Skills决定做什么，底层Behaviors负责怎么执行；两层用FSM实现；高层技能按优先级选择、可被更高优先级技能中止 | 将位置选择与导航执行分离；让动作有完成/失败结果，重视可调试性 |
| 《地平线：零之曙光》：[Guerrilla官方演讲](https://www.guerrilla-games.com/media/News/Files/The-AI-of-Horizon-Zero-Dawn.pdf)，第12–14页 | HTN把抽象任务按条件分解为可执行的行动计划 | 复杂多步行为可以由规划组织；目前我们的单招近战无需因此改用HTN |
| 《地平线：西之绝境》：[Guerrilla 2024-11-25公开演讲页](https://www.guerrilla-games.com/read/building-the-ai-behaviors-for-flying-and-swimming-machines-for-horizon-forbidden-west) | 以水翼兽为例介绍共享AI组件、飞行/水下导航移动及近战组件。页面确认范围，未据此断言其完整高层架构 | 决策、不同介质导航、移动和近战执行分别落地；这是比前述案例更近年的公开材料 |
| 行为树与效用选择的混合：[Bill Merrill，Building Utility Decisions into Your Existing Behavior Tree](https://www.gameaipro.com/GameAIPro/GameAIPro_Chapter10_Building_Utility_Decisions_into_Your_Existing_Behavior_Tree.pdf) | 在已有BT中引入效用评分处理多个同时可选的行为；不是某个最新项目的完整源码披露 | 多招式出现后可比较距离、冷却、风险等评分；现阶段先用清晰的条件和优先级 |

公开演讲通常比实际项目实现晚，且往往只披露某个子系统。本轮找到了近年案例，但没有依据声称掌握“截至2026所有最新AAA”的统一方案。GDC部分演讲链接维护或PDF抓取失败，未把未读到的内容当作已确认架构。

## 当前项目的落地取舍

采用UE行为树主干＋原生导航/朝向＋现有GAS和蒙太奇窗口：

1. 行为树选择追击、攻击或警戒；警戒内部选择后退、靠近或等待。
2. Service按0.2秒更新决策所需上下文；不在AIController Tick另建一套选择器。
3. Move To执行导航，Character Movement限制转速；一次警戒调整执行到完成，允许高优先级攻击中止。
4. GA/蒙太奇负责承诺出手、伤害窗口、攻击前进和动作取消，避免距离检查直接截断已经开始的攻击。

这是为本项目规模与可学习性作出的方案选择，不能称为《黑暗之魂》的原版架构，也不能仅凭主干结构证明手感已达标。
