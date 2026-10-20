# 工程资产盘点与干净环境恢复

> 盘点日期：2026-10-18；翻滚版本快照更新：2026-10-19
> 工程：Unreal Engine 5.8 / `ProjectUnreal`
> 目标：把工程自有蓝图、地图、C++ 和文档放入 GitHub，同时不把 Epic Paragon 素材包重新托管到 GitHub。

## 结论

当前 `Content` 目录约 19GB，其中绝大多数是 8 个 `Paragon*` 资源包。工程自有内容集中在 `Gameplay/`、`Input/`、`Maps/` 和地图外置 Actor 数据中。本仓库通过 `ProjectContentSnapshot/Content/` 保存了这部分自有资产的快照，当前快照共 200 个文件、约 33.29 MiB；恢复时运行 `Tools/Restore-ProjectContent.ps1` 即可按原相对路径复制回工程 `Content/`。

Paragon 资源包不包含在 GitHub 快照中。恢复完整工程时，需要使用有权访问这些资源的 Epic 账号重新安装/添加资源包，并保持它们在 `Content/Paragon.../` 下的路径。资源包目录记录在下表；当前盘点只确认文件夹名和体积，未逐项核实 Epic 账户中的可获取状态、Marketplace/Fab 商品标识或版本。

## 目录清单

| 当前 Content 路径 | 文件数 | 约占空间 | 分类与恢复方式 |
| --- | ---: | ---: | --- |
| `Gameplay/` | 30 | 1.24 MiB | 工程自有 Gameplay 蓝图、GAS 资产、攻击 Montage 与 HUD；快照中保存 |
| `Input/` | 5 | 0.01 MiB | 工程输入资产；快照中保存 |
| `Maps/` | 1 | 0.01 MiB | 工程地图；快照中保存 |
| `__ExternalActors__/` | 139 | 31.22 MiB | `NewMap` 的外置 Actor 数据；快照中保存。它可能引用 Paragon 内容 |
| `__ExternalObjects__/` | 5 | 约 0.01 MiB | 地图外置对象数据；快照中保存 |
| 根目录 `NewMap.umap`、`NewMap_HLOD0_Instancing.uasset` | 2 | 少于 0.01 MiB | 根目录地图文件；快照中保存 |
| 8 个 `Paragon*` 目录 | 13,812 | 约 18.90 GiB | Epic Paragon 角色资源包；不上传 GitHub，按账号权限重新获取 |

Paragon 目录体积（本机 2026-10-18 实测，GiB）：

| 目录 | GiB |
| --- | ---: |
| `ParagonMinions/` | 4.75 |
| `ParagonGrux/` | 2.90 |
| `ParagonNarbash/` | 2.63 |
| `ParagonGreystone/` | 2.11 |
| `ParagonKhaimera/` | 2.08 |
| `ParagonCountess/` | 1.78 |
| `ParagonSevarog/` | 1.35 |
| `ParagonBoris/` | 1.30 |

项目自己的 C++ 位于 `Source/`，项目配置位于 `Config/` 和 `ProjectUnreal.uproject`，开发与恢复说明位于 `docs/`；这些文件由外层 Git 仓库直接版本管理。

## 为什么不直接推送当前 Content 内层仓库

`Content/.git` 是本地素材仓库，没有远程地址；它的现有 Git 对象包约 12.44 GiB，并含有 Paragon 资源包的历史版本。直接把它接到 GitHub 并推送，会把历史中保留的 Marketplace 文件也一并上传。为避免这件事，外层仓库只保存经过筛选的 32.49 MiB 工程自有资产快照；原有内层仓库保持本地，用于现有素材历史和完整工作副本。

## 在干净电脑恢复

1. 克隆 GitHub 上的 `Soulslike-GAS-Demo`，安装与 `.uproject` 声明匹配的 Unreal Engine 5.8，以及本机编译所需的 Visual Studio C++ 工具链。
2. 使用有权访问 Paragon 资源包的 Epic 账号，通过 Epic Games Launcher 的资源库重新安装/添加本项目依赖的资源包；若安装后目录名或资源路径不同，先在编辑器中处理引用，不要直接在文件管理器里搬动 `.uasset`。
3. 在工程根目录运行：

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\Tools\Restore-ProjectContent.ps1
   ```

   脚本只复制 GitHub 快照内的自有资产，不会删除其他 `Content` 文件。若目标路径已存在且文件内容不同，脚本会停止并列出冲突；备份后确认要以 GitHub 快照覆盖时才传入 `-Overwrite`。

4. 用 `ProjectUnreal.uproject` 打开工程，允许编辑器生成本机缓存并编译 C++ 模块；检查 `GameplayAbilities` 等 `.uproject` 插件是否启用，随后打开 `Maps/NewMap` 或当前默认地图并运行 PIE。
5. 验收时确认 BP_Player、攻击 GA/GE、动画通知、输入映射、HUD 与地图均无 Missing Asset/引用丢失。仅克隆 GitHub 而没有取得 Paragon 资源授权的环境，可以验证文档、C++ 和自有资产文件已恢复，但不能算作完整的资源运行验收。

## 后续维护规则

- 在 Unreal 编辑器里修改工程自有蓝图/地图后，先保存，再更新 `ProjectContentSnapshot/Content/` 中对应文件，提交到外层仓库并推送。
- 不要把 `Paragon*` 原始资源包复制进快照。若新增 Marketplace/Fab 依赖，在本文件补记产品名、来源、版本/标识、获取步骤和被哪些自有资产引用。
- 只有经确认需要自托管、且许可允许的自有文件才纳入快照。大型外部资源仍通过原来源获取。

- Unreal 资产是二进制文件；Git 会保留版本，但无法像 C++ 一样展示蓝图节点/连线的逐行差异。重要图表改动应同步写入执行文档或附上编辑器截图。

## 2026-10-19 翻滚版本依赖与备份

本次更新自有玩法、输入、攻击/翻滚蒙太奇和重定向配置；精确文件清单与 SHA-256 见 `project-content-manifest.json`。上方 2026-10-18 目录表保留为首次盘点历史。

翻滚来自 Adobe Mixamo 的 **Stand To Roll**。公开仓库不含原始 FBX、`Gameplay/Anims/Roll/Source/` 或 `AS_Greystone_StandToRoll.uasset`。因此仅恢复 GitHub 快照会缺少这个动画依赖，不能声称完整工程无缺失。Mixamo 原始动作文件不作公开再分发，参见 [Adobe 社区分发说明](https://community.adobe.com/questions-696/mixamo-faq-licensing-royalties-ownership-eula-and-tos-589400?lang=en)。

恢复翻滚的方式：

1. 同一使用者换机时，从自己的完整 Content 备份恢复 Roll 目录；本轮备份压缩包在旧机 LocalBackups/Roll-v1-2026-10-19，内有本轮修改资产和原始 FBX，未上传公开 GitHub。它是增量备份，不含整个 19GB Paragon 素材库。
2. 或自行从 Mixamo 取得 Stand To Roll 的无模型 FBX，放到 Tools/prepare_roll_source.py 指定的位置，依次运行准备、导入重定向、根运动生成脚本。生成后按最终玩法把序列 Enable Root Motion 关闭、Force Root Lock 开启；AM_Roll 已保存 Rate Scale=2 和时间轴通知。第三方源动作姿势/比例可能因选择的 Mixamo 角色不同而变化，需重新预览验证。
3. 恢复后确认原三连击、GA_Roll、窗口通知和输入引用正确，再由用户 PIE 验收。

Content 内层本地 Git 仍包含上述完整动画资产，不添加远程、不推送整段 Paragon 历史。公开快照中的蒙太奇与 IK 资产会引用需要本地恢复的动画/源骨架，属于有记录的外部依赖。

## 2026-10-19 体力/跳跃续作快照

新增 GA_Jump；成本与回复 GE 移至 Gameplay/GAS/Effects/Cost。旧 Gameplay/GAS/Effects/GE_Cost.uasset 和旧 GE_StaminaRegen.uasset 已不在快照。对干净工程按新路径恢复即可；若在已有旧版本上恢复，复制脚本不会删除旧文件，需在编辑器核对引用与重定向器后清理，不能只覆盖后就认为路径迁移完成。Mixamo 动画排除规则保持不变。

## 2026-10-21 UI收工快照

新增WBP_ResourceBar，更新WBP_HUD和用户已保存的AM_Roll；含此前共同角色父类与移动视角蓝图迁移。自有快照200文件、33.29MiB，完整清单与SHA256见project-content-manifest.json。完整素材本地提交a1f38bd，Paragon和Mixamo原素材排除规则不变。
