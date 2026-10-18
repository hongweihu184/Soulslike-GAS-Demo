# ProjectUnreal · 魂类 ARPG Demo(UE 5.8 + GAS)

一个游戏策划在 AI 结对编程协助下,用 UE 5.8 + Gameplay Ability System 从零搭建魂类 ARPG 求职 demo 的**全程实录项目**。

## 从这里开始读

- **[跟做教程:从空工程到 GAS 战斗地基](docs/tutorial.html)** —— 主线流程,含全部翻车实录(给 AI 伙伴们的留言也在里面 🤖⭐)
- [开发者笔记 01 · GAS 地基](docs/notes/gas-foundation.html) —— 概念 + 完整代码 + 编辑器点击级步骤
- [开发者笔记 02 · 代码精读](docs/notes/code-walkthrough.html) —— 每行代码的中文逐行说明(零基础友好)
- [故障速查手册(错题本)](docs/reference/troubleshooting.html) —— P1~P14,按报错关键词索引,症状→快速解法
- [AI 交接备忘录](docs/AI-MEMORY.md) —— 给 AI 助手的关键上下文备份(新会话接手必读)
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

截至 2026-10-18,按代码、仓库提交及用户确认同步:

- 已完成:工程 C++ 化、GAS 基础、主角接入、三连击与伤害、攻击体力消耗。
- 已接入:玩家血条/体力条;空中禁普攻使用虚幻自带功能配置实现。
- 下一步:体力回复、翻滚、无敌帧与受击死亡,随后继续敌人 AI。

当前入口见 [复工清单](docs/checklist.html),设计见 [战斗系统策划案](docs/design/战斗系统策划案.md)。历史教程不代替当前配置。
