# ProjectUnreal · 魂类 ARPG Demo(UE 5.8 + GAS)

一个游戏策划在 AI 结对编程协助下,用 UE 5.8 + Gameplay Ability System 从零搭建魂类 ARPG 求职 demo 的**全程实录项目**。

## 从这里开始读

- **[跟做教程:从空工程到 GAS 战斗地基](docs/tutorial.html)** —— 主线流程,含全部翻车实录(给 AI 伙伴们的留言也在里面 🤖⭐)
- [开发者笔记 01 · GAS 地基](docs/notes/gas-foundation.html) —— 概念 + 完整代码 + 编辑器点击级步骤
- [开发者笔记 02 · 代码精读](docs/notes/code-walkthrough.html) —— 每行代码的中文逐行说明(零基础友好)
- [故障速查手册(错题本)](docs/reference/troubleshooting.html) —— P1~P14,按报错关键词索引,症状→快速解法
- [AI 交接备忘录](docs/AI-MEMORY.md) —— 给 AI 助手的关键上下文备份(新会话接手必读)
- [缺动作时：Mixamo 下载、重定向与复用提示词](docs/notes/mixamo-animation-workflow.md) —— 从找动作到接入技能的完整流程
- [项目主文档](docs/index.html) —— 计划表、各章节执行记录、资产清单

> 提示:docs 下是 HTML 文档,克隆到本地后用浏览器打开体验最佳;GitHub 网页上可直接读源码。

## 工程结构

- `Source/` — C++ 模块(GAS 地基:AttributeSet / BaseCharacter)
- `Config/` — 含 GameplayTags 配置
- `Content/` — 当前完整工作素材库(含本地内层 Git 和 Paragon 包,不整体推送)
- `ProjectContentSnapshot/Content/` — GitHub 可恢复的工程自有蓝图、地图与输入资产快照
- `docs/` — 全部教程、笔记、错题本、调研报告

## 在新电脑恢复

`Content/` 中的大部分体积来自 Epic Paragon 资源包，不由本仓库重新分发。GitHub 保存了我们自己的 Unreal 资产快照；恢复清单、资源包依赖说明和安全复制脚本见 [资产盘点与干净环境恢复](docs/reproduction/content-inventory.md)。取得有权访问的 Paragon 资源后，在工程根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\Tools\Restore-ProjectContent.ps1
```

该脚本将自有资产复制回 `Content/`，发现同路径内容不同时会停止，只有显式传入 `-Overwrite` 才覆盖。

## 进度

- 2026-10-20：新增共同蓝图父类 BP_CombatCharacter，玩家和木桩分别读取 Player / Enemy_Melee 行；差异表值已通过 PIE 验证。见[日志10](docs/log/10-角色与敌兵继承整理.md)。仍保留现有 C++ GAS 基础，尚未完成纯蓝图迁移。

截至 2026-10-19,按已保存资产和用户确认同步:

- 已完成:工程 C++ 化、GAS 基础、主角接入、三连击与伤害、攻击体力消耗。
- 已接入:玩家血条/体力条;空中禁普攻使用虚幻自带功能配置实现。
- 已完成体力回复和翻滚第一版：Mixamo 动作重定向、左 Shift 输入、移动取消及翻滚后摇接攻击窗口；修复混出后被打断导致技能不退出。
- 已接入翻滚、跳跃体力成本；GA_Jump 等待落地结束，攻击/翻滚/跳跃期间暂停回复，落地恢复。记录见[日志07](docs/log/07-翻滚跳跃体力与回复.md)。
- 下一步：核对攻击中翻滚窗口的输入判断，继续无敌帧与受击死亡，随后敌人 AI。
- 最新施工顺序：角色数值表 → UI 优化 → 敌兵行为树。数值表改为蓝图方案，本轮新增 C++ 已撤除，待创建蓝图结构体、重建数据表并接初始化，见[日志08](docs/log/08-角色数值表.md)；原未完成战斗规则继续保留。
- 翻滚使用的 Mixamo 动画数据仅保存在本地素材仓库，不在公开 GitHub 快照内；恢复步骤见资产盘点文档和[翻滚日志](docs/log/06-翻滚动画导入与重定向.md)。

当前入口见 [复工清单](docs/checklist.html),设计见 [战斗系统策划案](docs/design/战斗系统策划案.md)。历史教程不代替当前配置。
