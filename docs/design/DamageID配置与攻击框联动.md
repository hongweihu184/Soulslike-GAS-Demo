# DamageID 配置与攻击框联动

已配置并通过运行验证，2026-10-23。新增玩法逻辑为蓝图，无 C++ 改动。

## 当前配置

配置表：`/Game/Gameplay/Data/DT_AttackDamage`。结构体：`ST_AttackDamage`。
**表的行名就是 DamageID**，无需再填一个重复的数字字段。

| DamageID（行名） | HitboxIDs | Damage | 对应攻击 |
|---|---|---:|---|
| 20001 | PlayerWeapon | 25 | 玩家第一段 |
| 20002 | PlayerWeapon | 25 | 玩家第二段 |
| 20003 | PlayerWeapon | 40 | 玩家第三段 |
| 30001 | Weapon_R | 25 | 怪物当前单次攻击 |

每行还有 `Enabled` 开关，当前四行均为 true。`HitboxIDs` 是 Name 数组，后续一行可以指定多个框。

## 三方对应关系

1. **碰撞框**：使用 Component Tags（组件标签）保存 HitboxID。
2. **伤害表**：DamageID 行中填写 HitboxIDs、Damage。
3. **蒙太奇**：攻击窗口通知 `ANS_ConfiguredDamageWindow` 的 `DamageID` 填对应行名。

DamageID 标识一次伤害配置，HitboxID 标识实际碰撞框。玩家三段共用一个武器框，因此该框只需一个 PlayerWeapon 标签，不需要重复创建三个框。

| 蓝图 | 原有碰撞组件 | Component Tags 中的 HitboxID |
|---|---|---|
| BP_Player | WeaponHitBox | PlayerWeapon |
| BP_Dummy | EnemyWeaponHitbox_L | Weapon_L |
| BP_Dummy | EnemyWeaponHitbox_R | Weapon_R |

左手框保留原配置，但当前怪物30001不引用Weapon_L，因此左手不参与这次攻击。

**本轮没有重新挂接碰撞框，也没有改位置、旋转、缩放、尺寸和骨骼挂点。**

## 蒙太奇配置位置

打开蒙太奇，选中攻击窗口通知 `ANS_ConfiguredDamageWindow`，在详情里的 Damage Config 分类填写 `DamageID`。

| 蒙太奇 | DamageID | 攻击窗口（秒） |
|---|---|---|
| Attack_PrimaryA_Montage | 20001 | 0.40–0.60 |
| Attack_PrimaryB_Montage | 20002 | 0.38–0.58 |
| Attack_PrimaryC_Montage | 20003 | 0.60–0.80 |
| AM_EnemyAttack | 30001 | 0.30–0.65 |

窗口时间沿用原配置。其他转向、位移、移动锁定、连击通知未替换。旧的 ANS_AttackWindow / ANS_EnemyAttackWindow 资产保留，但这四个蒙太奇的伤害窗口已切换到新通知。

## 运行链路

`通知开始 → BP_CombatCharacter.BeginConfiguredDamageWindow(DamageID) → 关闭上一窗口、清空命中名单 → 读取 DT_AttackDamage → 按 HitboxIDs 找到带标签的组件 → 只将选中框设为 QueryOnly`。

`框的 BeginOverlap → HandleConfiguredDamageHit → 检查窗口开启、框在本轮名单、目标有 ASC、不是自身、该目标本轮未结算 → 先记录目标 → 发 Event.Montage.Attack.Hit，Payload.EventMagnitude携带表中伤害`。

怪物组件事件额外限定 OtherActor 为 Player0；玩家可命中其他带 ASC 的角色。此处不是完整阵营系统。

`各自 GA 等待命中事件 → 确认 EventMagnitude > 0 → 创建共享 GE_Damage 的 Spec → AssignSetByCallerMagnitude(DataName=Damage) → 对目标施加 Spec → MyAttributeSet 扣血`。

玩家原生武器代码仍会发送默认 EventMagnitude=0 的旧事件，新的 GA 过滤这些事件，避免重复伤害；新窗口命中去重由共同父类蓝图维护。不要再用旧的直接 ApplyGameplayEffectToTarget 调 GE_Damage；新调用需要先给 Spec 的 Damage 参数赋值。

`通知结束 / GA正常结束或取消 → EndConfiguredDamageWindow → 关闭本轮所有框并清空目标名单`。

## 修改与扩展

- 改伤害：只改 DT_AttackDamage 对应行的 Damage。
- 改用哪只手：改该行 HitboxIDs，例如 Weapon_R 改 Weapon_L。
- 同一窗口开多个框：在 HitboxIDs 数组里加入多个标签。它们对同一目标共用本轮去重，因此同一窗口只结算一次该行伤害。
- 左右手分别结算：创建两个 DamageID，分别配置左右框与伤害，在蒙太奇上放两个**不重叠**的窗口。
- 新增框：保持其几何配置，添加唯一的 Component Tag，并像现有框一样，将 BeginOverlap 的 OverlappedComponent 和 OtherActor 接到 HandleConfiguredDamageHit。
- 找不到 DamageID、行被禁用或标签找不到框时，不会退回旧的固定50伤害。
- 当前最小版每个角色同时只维护一个活动窗口；新的窗口会结束前一个。不要同时叠放不同 DamageID 的通知。后续确需重叠窗口时，再增加窗口实例与独立命中名单。

## 验证结果

使用真实 GA、蒙太奇通知、碰撞重叠与 GE 结算：

- 玩家三段：怪物生命200→175→150→110，对应25、25、40。
- 怪物30001：玩家生命200→175，伤害25；窗口中只选中 EnemyWeaponHitbox_R，左框NoCollision。
- 所有窗口结束后碰撞均关闭；攻击过程中框的相对变换、尺寸与挂点保持不变。
- 怪物窗口打开后立即取消：窗口关闭、左右框均NoCollision、玩家生命不变。
- 相关蓝图严格编译通过。仍待用户实际试玩攻击范围和手感。

测试证据：`Saved/DamageConfig-RuntimeVerification.json`、`Saved/DamageConfig-CancelVerification.json`、`Saved/DamageConfig-StaticVerification.json`。备份：`LocalBackups/DamageConfig-2026-10-23`。
