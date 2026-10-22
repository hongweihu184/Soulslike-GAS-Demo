# 21：DamageID 配置表与蒙太奇选框

用户要求先记录文档再配置：玩家20001/20002/20003沿用现有武器框，伤害25/25/40；怪物30001只用右框，伤害25。

主使用文档：`docs/design/DamageID配置与攻击框联动.md`，包含字段、编辑位置、运行链路、扩展方式和当前单活动窗口限制。

新增纯蓝图结构体ST_AttackDamage（Enabled、Damage、HitboxIDs数组）及DT_AttackDamage，四行已填；行名作为DamageID。新增ANS_ConfiguredDamageWindow，DamageID为实例可编辑Name，已替换四个蒙太奇原伤害窗口通知，保留原窗口时间及其他通知。

共同父类BP_CombatCharacter新增BeginConfiguredDamageWindow/EndConfiguredDamageWindow/HandleConfiguredDamageHit，按表行选组件标签，开关碰撞，按每窗口每目标去重。PlayerWeapon标签对应原WeaponHitBox，Weapon_L/R标签对应怪物原左右框。BeginOverlap转共享父类；怪物仍过滤Player0。无运行时重新挂接或尺寸覆盖。

GE_Damage改SetByCaller(DataName=Damage)，四个攻击GA改读Payload.EventMagnitude，过滤默认0旧事件后创建Spec、赋Damage、施加目标；玩家和怪物保留各自GA。四GA的OnEnd均关闭配置窗口。原玩家C++注册发送默认0事件仍在但不结算，新伤害逻辑和去重为蓝图，无C++修改。旧怪物双框函数与旧ANS资产保留兼容但四个蒙太奇已走新通知。

实测真实GA+蒙太奇+重叠+GE：怪物HP200→175→150→110；玩家被怪物30001命中200→175，怪物仅右框QueryOnly，左框NoCollision。逐帧几何/挂点保持，窗口结束全部关闭。取消测试窗口开启后CancelAttack，立即关闭且无扣血。相关蓝图严格编译，15个资产强制保存，测试证据Saved/DamageConfig-*.json。

结构体字段创建采用之前用户允许的引擎公开编辑函数方式，对新建结构体调用AddVariable和RenameVariable；使用live对象与livePinType参数，不改引擎源码、DLL或uasset二进制。其他资产由MCP/官方Python编辑API修改。

修改前12资产备份LocalBackups/DamageConfig-2026-10-23。PIE停止、后台节流恢复true、Pythonremote读回false，已打开DT_AttackDamage供用户查看。未提交/推送Git、未更新公开内容快照。仍待用户实际试玩判定范围与手感；不以扣血验证代替手感验收。
