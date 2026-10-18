# LM Studio 简体中文补丁

给 [LM Studio](https://lmstudio.ai/) 桌面端补上完整简体中文界面。在上游汉化补丁的基础上，补充了插件面板、插件筛选、引擎加载参数、多行工具提示等上游未覆盖的文案，并带有版本校验和一键还原。

当前验证版本：**LM Studio 0.4.26+4（Windows）**，理论上适用于 0.4.15+ 的 Electron 版本。

## 功能

- 切换 i18next 语言并替换界面硬编码英文（上游词典，3000+ 处）。
- 补充属性、纯文本、设置词典、运行时渲染层文案（本项目增强）。
- 插件面板内部文案中文化：上下文压缩、长期记忆、代码解释器、与文件对话、知识库检索、联网搜索、技能系统的配置项、副标题、下拉选项、Tools 区域与工具说明。
- 插件筛选框支持中文别名（记忆 / 压缩 / 代码 / 文件 / 知识库 / 联网 / 技能），英文标识符仍可搜索。
- 引擎加载参数中文化：思考开关、物理批大小、上下文检查点、投机解码及其悬停提示。
- 版本校验：LM Studio 升级后，旧备份会自动存档，并按新版本重建英文备份；跨版本备份禁止用于还原。

## 环境要求

- Windows
- Python 3（`py` 启动器可用）
- LM Studio 0.4.15 及以上（已在 0.4.26+4 实测）
- 可选：Node.js（用于补丁后的 JS 语法检查）

## 使用

1. 下载本仓库全部文件（或 `git clone`）。
2. 把文件复制到 LM Studio 安装目录，例如：
   `C:\Users\<用户名>\AppData\Local\Programs\LM Studio`
3. 完全退出 LM Studio（包括托盘图标）。
4. 双击 `0-应用中文.cmd`。脚本会提示关闭正在运行的 LM Studio，并在完成后询问是否重新启动。
5. 需要还原时，双击 `1-还原英文.cmd`。

也可以直接运行命令：

```bat
py -3 cn_localize.py apply
py -3 cn_localize.py restore
py -3 cn_localize.py status
```

`status` 只读，显示界面语言、当前版本、备份版本与运行状态。

## 升级 LM Studio 之后

升级会覆盖 `main_window.js`，界面会回到英文。重新运行 `0-应用中文.cmd` 即可。

`cn_localize.py` 会把首次补丁前的英文界面备份到 `.backups/main_window.js.original`，并把版本记录在 `main_window.js.original.version`。如果检测到版本变化：

- 应用补丁时，旧备份改名为 `main_window.js.original.<旧版本>` 存档，再按新版本重建备份。
- 还原时，拒绝跨版本备份，避免把旧版界面文件写进新版程序。
- `status` 会显示版本不一致的警告。

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `cn_localize.py` | 交互入口：关闭/重启 LM Studio、应用、还原、状态、版本校验 |
| `patch_lmstudio.py` | 上游补丁：语言切换与基础文本替换 |
| `T_dict.json` | 上游翻译词典 |
| `patch_extra.py` | 增强补丁：属性 / 纯文本 / 词典 / 渲染链 / 布局 |
| `T_extra.json` | 增强补丁的词典数据 |
| `0-应用中文.cmd` / `1-还原英文.cmd` | 双击入口 |

补丁会先校验内嵌 JSON 和 JS 语法，失败时不会写入坏文件；应用补丁后若语法检查不通过，会自动还原。

## 实现概要

- 补丁只修改渲染进程的界面文件 `resources/app/.webpack/renderer/main_window.js`，不改 `lms.exe`，不改模型与配置。
- 增强部分按顺序执行：属性替换 → 纯文本替换 → 迁移旧译名 → 内嵌词典 → 渲染链映射 → 布局微调。
- 所有替换均为幂等操作，重复运行不会叠加或损坏文本。
- 正则和直接替换都避开路由名、schema 枚举、插件标识符等运行时数据。

## 已知限制

- 每次 LM Studio 升级后都需要重新应用补丁。
- 上游界面结构变动时，个别文案可能需要更新替换锚点。
- 仅覆盖界面文本；模型输出、插件元数据里的原始标识符保持英文。
- 首次运行会生成 30 MB 以上的原版界面备份，仓库不包含该备份。

## 许可与致谢

本项目以 MIT 协议发布，见 [LICENSE](LICENSE)。

基础汉化与词典来自 [C2H12O6/lm-studio-simplified-chinese](https://github.com/C2H12O6/lm-studio-simplified-chinese)（MIT），其版权声明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

LM Studio 是 LM Studio 公司的产品。本项目为第三方界面文本补丁，与 LM Studio 官方无关。
