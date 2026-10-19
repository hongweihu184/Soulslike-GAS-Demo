# 学习记录：GE、Spec、Context 与蓝图数据流

记录日期：2026-10-20。

## 当前学习状态

用户明确表示：这是知识盲区，目前还没有理解为什么 GAS 需要 Spec。此前解释过一次，但不能认为用户已经掌握。用户要求记录，以后忘记时可以重新解释。后续教学应先解释目的、输入和输出，再给接线；不要只报英文节点名或用更多术语解释术语。蓝图实现和可见接线是用户的学习偏好。

## 从本项目的例子解释

角色数值表保存 Player、Enemy_Melee 等角色的最大生命和最大体力。蓝图读取一行后，通过 GE_InitAttributes_FromTable 初始化角色。

- GE 资产：可重复使用的规则。它规定修改哪些属性、用 Override 覆盖、根据哪个 SetByCaller 标签取值。资产本身不是这一次使用的数据。
- Spec（GameplayEffectSpec，效果规格）：GAS 为某一次效果使用准备的数据结构，不是 CSV 那样的磁盘文件格式。它引用 GE 定义，并记录本次等级、Context、调用方传入的数值等；其他效果还可能使用捕获的属性和标签信息。
- Context（效果上下文）：记录效果来源、相关角色及可选的命中信息等。它不负责存放本例的生命和体力数值，也不会自动完成属性修改。Make Effect Context 根据能力系统已有角色信息建立上下文，后续可以补充来源对象或命中结果；不要承诺所有来源字段都会自动填写。
- Apply：根据本次 Spec 执行效果，才会真正修改属性。

玩家和敌兵可共用同一 GE，但分别创建 Spec。玩家的 Spec 填200生命、150体力，敌兵的 Spec 填100生命、100体力；不需要因此修改 GE 资产。

## 为什么需要 Spec

不能只说“引擎要求如此”。先说明需求：同一套效果规则会被重复使用，但每次等级、来源、数值可能不同，需要独立存放这些运行时数据。GAS 将其集中放进 Spec，并让通用应用接口接收它。对这个只有两个数值的初始化例子，单独看显得复杂；统一结构是为了同时支持伤害、治疗、增益等更丰富的效果。

“GE 定义怎么改，Spec 记录这次的数据，Apply 执行修改”可以作为复习结论，但不能代替逐项解释。

## 当前节点的职责

1. Get Data Table Row：找到角色配置行。Row Not Found 只打印错误，不执行初始化。
2. Make Effect Context：创建本次来源信息。
3. Make Outgoing Spec：根据 GE 类、等级和 Context 创建本次效果规格，尚不修改属性。
4. Assign Tag Set by Caller Magnitude（生命）：向同一 Spec 写入 SetByCaller.Init.MaxHealth。
5. Assign Tag Set by Caller Magnitude（体力）：向同一 Spec 写入 SetByCaller.Init.MaxStamina。
6. Apply Gameplay Effect Spec to Self：把该 Spec 应用到对应能力系统组件。

白线决定执行顺序，数据线传递输入值或对象引用。Spec Handle 是效果规格的句柄，两个 Assign 修改同一个规格，不是沿途生成多个独立效果。串联 Return Value 到下一个 Spec Handle 是为了清楚表达流程；若两次 Assign 使用同一个有效句柄且执行顺序正确，分别连接同一来源也可生效。

蓝色并不统一代表 Spec：Target 的蓝线指向 Ability System Component；Spec Handle 的线指向效果规格。必须按引脚类型解释。

## 本次教学中需避免重复的错误

- 用户截图中的 Make Effect Context、Make Outgoing Spec 为绿色纯节点，没有白色执行引脚；不要要求连接不存在的执行引脚。当前白线为 Row Found → Assign生命 → Assign体力 → Apply。
- 不要把串联 Spec 数据线描述成引擎唯一允许的接法。
- 不要把解释过等同于理解过；后续复习应允许用户继续追问“为什么”。

当前函数是否已最终修正、调用及 PIE 验收尚未确认；此文仅记录学习疑点与解释，不代表功能验收。
