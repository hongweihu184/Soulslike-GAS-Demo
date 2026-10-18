# 缺少动作时：从 Mixamo 找动画并重定向到现有角色

> 记录日期：2026-10-19。案例：UE 5.8 的 Greystone 缺少翻滚，用户从 Mixamo 下载 Stand To Roll，AI 导入并重定向，用户在编辑器中制作技能与时间轴窗口，最终确认第一版可用。
>
> 本文是复用流程，不意味着所有 Mixamo 动作都能无调整套用。原动作的骨架、身体比例、根骨骼和持武器姿势需要逐次检查。

## 1. 什么时候使用这条路线

项目缺少翻滚、闪避、受击、交互等动作时，先检查本地资源，再考虑 [Mixamo 动画库](https://www.mixamo.com/)。可以保留当前角色，把其他骨架的动作转换给它；这个过程叫“动画重定向”。不必仅因缺一条动作就更换主角。

这次本地 Paragon 包没有找到名称明确、适合直接使用的翻滚，旧预研也只是待检查，不能作为素材已经存在的证据。AI 访问 Mixamo 的交互目录加载超时，实际动作由用户在网站上选择并下载；AI 随后验证本地 FBX，不能把这次过程写成 AI 已预览完整在线动作库。

## 2. 在网站上挑选动作

1. 用自己的 Adobe 账号登录 Mixamo，选择一个正常比例的人形源角色。
2. 用动作关键词搜索。翻滚可先试 `Roll`（翻滚），再看 `Dodge`（闪避）；其他需求按实际动作搜索，不保证这些词每次都对应同名资产。
3. 观看完整动作，而非只看缩略图。翻滚要看起始站姿、前冲、滚动、起身是否连贯，是否含多余等待、是否与角色持剑盾的姿势冲突。
4. 优先只选一条满足需求的动作，先验证在本项目角色上的效果，再扩充动作库。
5. 记录网站动作名、源角色名、下载选项和文件名。源角色比例会影响重定向，换源角色不能默认结果完全相同。本次动作名为 **Stand To Roll**；源角色名当时未记录，不能事后猜测补写。

## 3. 下载设置

| 选项 | 首次建立源角色时的建议 | 含义 |
| --- | --- | --- |
| Format | FBX Binary | 下载二进制 FBX |
| Skin | With Skin | 包含源模型，方便直接导入和检查 |
| Frames per Second | 30 | 初步保留 30 帧/秒采样 |
| Keyframe Reduction | None | 先不精简关键帧 |

首次导入建议 With Skin（带模型）。已有同一个源角色的骨架与预览模型时，再下载 Without Skin（不带模型）动画可以减少重复模型资源。各动作提供的可调选项不同；不要假定每条都有 In Place（原地）开关，也不要以“看起来向前走”证明它已有可用根运动。

**本次实际拿到的是 Without Skin。** `Stand To Roll.fbx` 约 504,656 字节，FBX 7700，65 根 Mixamo 骨骼，约 2.3667 秒，没有网格模型，最高层为 Hips，没有独立地面 root。最初建议补 With Skin，但实际通过简易源预览模型成功导入，用户无需重新下载。以后不要一见 Without Skin 就断言文件无效或必须重新下载。

不要把 Mixamo 骨架的动画直接强行指定为 Greystone Skeleton 来代替重定向。应保留独立源资源，再生成目标角色版本。

## 4. 把下载文件交给 AI

提供本地 FBX 的绝对路径、目标角色、用途和期望的位移方式。先要求只读检查，至少确认：

- 是否包含网格、骨架和动画；时长、帧率、关键骨骼名称。
- 最高层是 root 还是 Hips（髋部）；位移和旋转记录在哪根骨骼上。
- 是否已有可复用的同源骨架与 IK Rig；目标角色和原动画都不能被覆盖。
- 模型是否只是原地播放姿势，还是需要实际驱动角色位置。

本次原文件始终保留；所有中间文件写入项目 Saved/RollImport，正式输出在 Content/Gameplay/Anims/Roll。

## 5. 本次重定向实际做了什么

重定向使用 UE 自带的 **IK Rig（骨架链配置）**与 **IK Retargeter（骨架重定向器）**。基本过程是：准备源预览角色 → 配置源与目标的骨骼链 → 对齐参考姿势 → 预览 → 导出目标骨架的动画序列。骨骼数量、命名和比例可以不同，依据功能链对应，而非强制骨架完全一样。参考 [Epic 双足角色重定向说明](https://dev.epicgames.com/documentation/unreal-engine/retargeting-bipeds-with-ik-rig-in-unreal-engine?lang=en-US)。

这次无模型文件的具体处理：

1. 为原始骨架添加简易蒙皮预览几何体，每根骨骼使用四个顶点；保留原动画、骨骼与连接，原文件不改动。这个预览模型只用于导入与重定向，不作为游戏人物。
2. 使用传统 FBX 导入通道建立源 Skeletal Mesh 和 Skeleton；动画单独从原 FBX 导入该源骨架。
3. 分别建立 `IK_MixamoRoll` 和 `IK_GreystoneRoll`；UE 5.8 自动生成人形链，髋部对应 Hips → pelvis。
4. 创建 `RTG_Mixamo_Greystone_Roll`，匹配链并自动对齐目标姿势，导出 `AS_Greystone_StandToRoll`。
5. 单独处理根运动：默认拷贝 Hips 会把骨盆翻转与升降带到 root。改为从目标 pelvis 生成 root 水平运动，Z 固定地面、不随 pelvis 旋转、关闭 Maintain Offset From Pelvis，避免额外摆动。
6. 重新加载保存资产，抽查多帧坐标与目标骨架。最终模型穿插、节奏和手感由用户在编辑器和 PIE 中检查。

这次成功的简易模型方法是项目内脚本方案，不保证适用于任意 FBX 版本、骨架或变换设置；脚本有版本和骨骼变换断言。遇到不支持的文件应停在独立源目录处理，或改用带模型文件，不能破坏现有资源。

## 6. 姿势重定向与实际位移分开验收

**动作能播放，不代表实际位移已经正确。** 分两轮检查：

| 检查 | 看什么 |
| --- | --- |
| 动作姿势 | 肢体是否扭曲，头脚是否穿地，剑盾是否严重穿插，开始和结束能否衔接 |
| 位移与节奏 | 角色胶囊是否实际移动，距离和速度是否匹配翻滚，撞墙是否停止，被打断后是否还在位移 |

本次先生成了可用的地面根运动；最终用户选择了**序列关闭 Enable Root Motion、开启 Force Root Lock，通知 ANS_AttackLungeWindow 驱动位移**。AM_Roll 的 Rate Scale 调为 2。原动画约 2.37 秒，完整蒙太奇播放约 1.18 秒，窗口取消可能让动作提前结束。

因此以后询问 AI 时，要说明“最终用根运动还是窗口位移”。不要在已经有窗口位移时又随意打开根运动，避免两套位移同时生效。也不要把当前已经调好的 2 倍速和距离当成所有动作的通用参数。

## 7. 从序列接到本项目技能

1. 右键目标动画序列 → Create → Create AnimMontage，建立蒙太奇。
2. **先核对插槽：本项目当前是 UpperBody，不能保留默认 DefaultSlot。** 该名字本身不限制骨骼范围，实际影响范围由动画图的混合配置决定（P22）。
3. 按需配置转向、位移、移动锁和取消窗口；不要从攻击蒙太奇复制来一堆不需要的伤害/连击通知。
4. GA 先调用 CommitAbility，再播放蒙太奇；角色 StartupAbilities 要授予该 GA，输入标签容器必须真正有值（P33）。
5. PlayMontageAndWait 的完成、取消和打断接 EndAbility，勾选 Stop When Ability Ends；本次还必须开启 Allow Interrupt After Blend Out，修复混出后被打断遗留技能（P32）。
6. 本项目取消窗口：攻击上 RollCancelWindow 允许接翻滚；翻滚上 AttackCancelWindow 允许接攻击，查询不能颠倒（P34）。

## 8. 可直接复用的提示词

以下占位内容在使用前替换；提示词可以只提供给本项目的 AI，不需要安装额外插件。

### A. 缺少动作，先找资源

```text
先读 docs/AI-MEMORY.md、docs/checklist.html，以及 docs/notes/mixamo-animation-workflow.md。
当前角色是【目标角色】，我需要【动作名称与用途】。
先查本地动画库是否已有合适资源；没有再查看 Mixamo 等官方来源。
明确区分“只按名称找到”和“已实际预览确认”。不要凭记忆说某动作一定存在。
优先保留当前角色，把动作重定向给它。给我搜索关键词、挑选标准和下载选项。
目录无法访问就说明具体限制，不要编造预览结论。
```

### B. 下载完成，导入并重定向

```text
我已取得动画文件：【FBX 绝对路径】。
请先读项目记忆和 Mixamo 操作指南，检查文件是否带模型、骨架、动画与独立 root。
目标是【目标角色资产路径】，用于【用途】。
请在独立的新目录导入并重定向，原 FBX 保留，不覆盖已有 Roll 动画或其他玩法资产。
如果不带模型，先检查能否复用已有源骨架；必要时评估本项目的简易源预览模型方案，
不支持时说清原因，不强行套用旧脚本。需要修改脚本中的路径、资产名和输出目录，
不能原样运行 Tools 下的 Roll 专用脚本去覆盖原翻滚。
先验证姿势，再检查根运动、实际位移与打断后的清理。
最终希望使用【根运动 / 原地动画加窗口位移 / 先评估再决定】。
编辑器内的技能与时间轴调参由我完成；请给出步骤，并记录验证边界与恢复方法。
```

### C. 新动作已经能播，接入玩法并收尾

```text
动画序列【资产名】已重定向成功。请按本项目现有 GAS 和 ANS/GE 模式指导我接入。
先核对插槽、技能授予与激活标签，再做播放、位移、成本和取消窗口。
取消时机由动画时间轴配置，动作状态标签只用于区分正在做什么，
不要整段动作一律禁止另一个动作，也不要把窗口设为所有空闲动作的必需条件。
逐项验证：正常播放、窗口内/外接动作、打断后可再次发动、退出后无残留状态或位移。
完成后更新日志、错题本和接手点，提交本地完整资产，GitHub 只同步可公开的自有部分。
```

## 9. 脚本位置与复现范围

| 文件 | 作用 |
| --- | --- |
| Tools/prepare_roll_source.py | 项目外的独立 Python 执行；读取本次 FBX，生成源预览 FBX |
| Tools/import_retarget_roll.py | UE 编辑器 Python 执行；导入源资源并建立 IK 配置、烘焙目标序列 |
| Tools/finalize_roll_root_motion.py | UE 编辑器 Python 执行；调整 root 生成设置并重新烘焙 |
| Tools/verify_roll_retarget.py | UE 编辑器 Python 执行；抽样骨骼姿势并记录结果 |

这些脚本针对本次 Stand To Roll / Greystone 命名和路径编写，不是通用一键导入器。普通 Python 不能直接运行需要 `import unreal` 的脚本。原文件默认路径为 `C:/Users/10645/Downloads/Stand To Roll.fbx`，中间结果在 Saved/RollImport；正式资源在 `/Game/Gameplay/Anims/Roll`。重新烘焙后还须恢复最终用户选择的关闭根运动/强制根锁定配置。

## 10. 版本与素材备份

- Content 本地 Git 保存完整导入资源。2026-10-19 第一版提交为 `cca12f5`。
- LocalBackups/Roll-v1-2026-10-19 保存本轮变更资产压缩包与原始 FBX，是本地增量备份，不能替代完整 Content 或异地备份。
- 公开 GitHub 不包含 Mixamo 源动作、目标动作序列和源预览资源；包含我们自己的技能、通知、输入、蒙太奇和重定向配置。换机需要恢复外部依赖，不能只克隆后假定所有动作都在。
- Mixamo 的使用与原始文件分发是两回事。素材获取与使用参考 [Adobe 官方 FAQ](https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html)，原始资源再分发限制见 [Adobe 社区说明](https://community.adobe.com/questions-696/mixamo-faq-licensing-royalties-ownership-eula-and-tos-589400?lang=en)。

本次完整执行记录见 [日志06](../log/06-翻滚动画导入与重定向.md)，故障排查见 [P22](../reference/troubleshooting.html#p22)、[P32](../reference/troubleshooting.html#p32)、[P33](../reference/troubleshooting.html#p33)、[P34](../reference/troubleshooting.html#p34)。
