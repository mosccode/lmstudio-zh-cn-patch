# LM Studio 简体中文补丁

给 [LM Studio](https://lmstudio.ai/) 桌面端补上完整简体中文界面。在上游汉化补丁的基础上，补充了插件面板、插件筛选、引擎加载参数、多行工具提示等上游未覆盖的文案，并带有版本校验和一键还原。另附联网搜索插件的国内后端补丁，让搜索在境内网络下可用，以及 ComfyUI 图片生成 MCP 的汉化补丁。

当前验证版本：**LM Studio 0.4.26+4（Windows）**，理论上适用于 0.4.15+ 的 Electron 版本。

## 功能

- 切换 i18next 语言并替换界面硬编码英文（上游词典，3000+ 处）。
- 补充属性、纯文本、设置词典、运行时渲染层文案（本项目增强）。
- 插件面板内部文案中文化：上下文压缩、长期记忆、代码解释器、与文件对话、知识库检索、联网搜索、技能系统的配置项、副标题、下拉选项、Tools 区域与工具说明。
- 插件筛选框支持中文别名（记忆 / 压缩 / 代码 / 文件 / 知识库 / 联网 / 技能），英文标识符仍可搜索。
- 引擎加载参数中文化：思考开关、物理批大小、上下文检查点、投机解码及其悬停提示。
- 版本校验：LM Studio 升级后，旧备份会自动存档，并按新版本重建英文备份；跨版本备份禁止用于还原。
- 联网搜索插件国内化：中文查询优先百度，英文查询优先必应中国，搜狗随后，DuckDuckGo 仅作兜底；请求与网页抓取均使用中文语言头。
- ComfyUI 图片生成 MCP 汉化：工具名、工具说明、参数说明、报错信息全部中文；同时修复 `*.meta.json` 被误当工作流解析导致的启动崩溃。

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
6. 可选：联网搜索插件国内化，双击 `2-应用国内搜索.cmd`；恢复插件原版双击 `3-还原国内搜索.cmd`。该补丁作用于已安装的 `altra/web-search` 插件，与界面汉化互不影响。
7. 可选：ComfyUI 图片生成 MCP 汉化，双击 `4-汉化图片生成MCP.cmd`；恢复原版双击 `5-还原图片生成MCP.cmd`。默认目录为 `W:\Comfy-Desktop\mcp\comfyui-mcp-server`，也可以在命令行用 `--dir` 指定。

也可以直接运行命令：

```bat
py -3 cn_localize.py apply
py -3 cn_localize.py restore
py -3 cn_localize.py status
py -3 patch_websearch_cn.py
py -3 patch_websearch_cn.py --restore
py -3 patch_websearch_cn.py --check
py -3 patch_comfyui_mcp_cn.py --dir "W:\Comfy-Desktop\mcp\comfyui-mcp-server"
py -3 patch_comfyui_mcp_cn.py --dir "..." --check
py -3 patch_comfyui_mcp_cn.py --dir "..." --restore
```

`status` 只读，显示界面语言、当前版本、备份版本与运行状态。

## 升级 LM Studio 之后

升级会覆盖 `main_window.js`，界面会回到英文。重新运行 `0-应用中文.cmd` 即可。

`cn_localize.py` 会把首次补丁前的英文界面备份到 `.backups/main_window.js.original`，并把版本记录在 `main_window.js.original.version`。如果检测到版本变化：

- 应用补丁时，旧备份改名为 `main_window.js.original.<旧版本>` 存档，再按新版本重建备份。
- 还原时，拒绝跨版本备份，避免把旧版界面文件写进新版程序。
- `status` 会显示版本不一致的警告。

## 联网搜索插件国内化

`2-应用国内搜索.cmd` 修改已安装的 `altra/web-search` 插件运行时文件：

```
~/.lmstudio/extensions/plugins/altra/web-search/.lmstudio/production.js
```

- 后端顺序：SearXNG（若已配置）→ 中文查询「百度 → 必应中国 → 搜狗」/ 英文查询「必应中国 → 百度 → 搜狗」→ DuckDuckGo 最后兜底。
- 必应固定使用 `cn.bing.com`（`setlang=zh-hans&cc=cn`），请求与网页抓取使用 `zh-CN` 语言头。
- 原文件备份为 `production.js.websearch-cn.orig`；重复运行不会叠加修改；语法检查失败会自动还原；插件版本变化导致锚点不匹配时拒绝修改。
- 恢复原版：`3-还原国内搜索.cmd`，或 `py -3 patch_websearch_cn.py --restore`。

## ComfyUI 图片生成 MCP 汉化

`patch_comfyui_mcp_cn.py` 修改已安装的 [joenorton/comfyui-mcp-server](https://github.com/joenorton/comfyui-mcp-server)（Apache-2.0）：

- 汉化工具说明：图片查看、任务队列、资产查询、模型与默认参数、工作流列表与运行、发布、重做，以及所有参数说明（提示词 / 宽高 / 种子 / 图片 / 去噪等）。
- 工作流工具的描述改为读取同名 `.meta.json`，可以直接写中文工具说明；找不到时回退为中文的「执行 ComfyUI 工作流「…」」。
- 修复 `_load_workflows` 把 `*.meta.json` 当作工作流解析、导致服务启动即崩的问题（`AttributeError: 'str' object has no attribute 'get'`）。
- 汉化常见报错：缺少必填参数、参数类型转换失败、工作流不存在、资产不存在、等待超时。
- 种子归一化：`seed` 为负数（LM Studio 常用 `-1` 表示随机）时自动换成随机正整数，避免 ComfyUI 报 `Value -1 smaller than min of 0` 的 400 错误。
- 等待上限提高到 300 秒；超时返回 `status: running` 与 `prompt_id`，可继续用 `get_job` 轮询，而不是误报失败。
- 原文件备份为 `*.zh-cn-orig`，重复运行幂等；改完逐个执行 `compile()` 检查，失败不写入任何文件。

前置条件：ComfyUI 已在 `http://127.0.0.1:8188` 运行；LM Studio 的 MCP 配置在 `~/.lmstudio/mcp.json`。示例：

```json
{
  "mcpServers": {
    "z-image-turbo": {
      "command": "W:\\Comfy-Desktop\\mcp\\comfyui-mcp-server\\.venv\\Scripts\\python.exe",
      "args": ["W:\\Comfy-Desktop\\mcp\\comfyui-mcp-server\\server.py", "--stdio"],
      "env": {
        "COMFYUI_URL": "http://127.0.0.1:8188",
        "COMFY_MCP_WORKFLOW_DIR": "W:\\Comfy-Desktop\\mcp\\comfyui-mcp-server\\workflows",
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

- 恢复原版：`5-还原图片生成MCP.cmd`，或加 `--restore`。
- 检查是否已汉化：`--check`，输出「已汉化 / 未汉化」。
- 依赖：上游 `requirements.txt`（requests / mcp / Pillow），不需要 torch，也不下载模型权重。
- 显存：Z-Image 的 DiT + 文本编码器约 9.3 GB。LM Studio 里另有一个 9B 模型（约 6.8 GB 权重 + KV）常驻时，12 GB 显卡装不下两者，ComfyUI 会大量使用内存/交换，单张图可能从约 20 秒变成几分钟。需要快速出图时先卸载 LM Studio 中的大模型；否则请等待，并把等待上限内的 `running` 结果用 `get_job` 继续轮询。

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `cn_localize.py` | 交互入口：关闭/重启 LM Studio、应用、还原、状态、版本校验 |
| `patch_lmstudio.py` | 上游补丁：语言切换与基础文本替换 |
| `T_dict.json` | 上游翻译词典 |
| `patch_extra.py` | 增强补丁：属性 / 纯文本 / 词典 / 渲染链 / 布局 |
| `T_extra.json` | 增强补丁的词典数据 |
| `patch_websearch_cn.py` | 联网搜索插件补丁：国内后端与中文请求头 |
| `patch_comfyui_mcp_cn.py` | ComfyUI MCP 汉化：工具/参数说明、`.meta.json` 崩溃修复 |
| `0-应用中文.cmd` / `1-还原英文.cmd` | 界面汉化双击入口 |
| `2-应用国内搜索.cmd` / `3-还原国内搜索.cmd` | 联网搜索插件双击入口 |
| `4-汉化图片生成MCP.cmd` / `5-还原图片生成MCP.cmd` | ComfyUI MCP 双击入口 |

补丁会先校验内嵌 JSON 和 JS 语法，失败时不会写入坏文件；应用补丁后若语法检查不通过，会自动还原。

## 实现概要

- 汉化补丁只修改渲染进程的界面文件 `resources/app/.webpack/renderer/main_window.js`，不改 `lms.exe`，不改模型与配置。
- 联网搜索补丁只修改 `altra/web-search` 插件的 `.lmstudio/production.js`，不涉及界面文件和其他插件。
- 增强部分按顺序执行：属性替换 → 纯文本替换 → 迁移旧译名 → 内嵌词典 → 渲染链映射 → 布局微调。
- 所有替换均为幂等操作，重复运行不会叠加或损坏文本。
- 正则和直接替换都避开路由名、schema 枚举、插件标识符等运行时数据。

## 已知限制

- 每次 LM Studio 升级后都需要重新应用补丁。
- 联网搜索插件更新会覆盖 `production.js`，更新插件后需要重新运行 `2-应用国内搜索.cmd`。
- ComfyUI MCP 更新会覆盖被改的 `.py`，更新后需要重新运行 `4-汉化图片生成MCP.cmd`。
- 百度 / 搜狗页面结构变化时，对应解析规则可能需要更新。
- 上游界面结构变动时，个别文案可能需要更新替换锚点。
- 仅覆盖界面文本；模型输出、插件元数据里的原始标识符保持英文。
- 首次运行会生成 30 MB 以上的原版界面备份，仓库不包含该备份。

## 许可与致谢

本项目以 MIT 协议发布，见 [LICENSE](LICENSE)。

基础汉化与词典来自 [C2H12O6/lm-studio-simplified-chinese](https://github.com/C2H12O6/lm-studio-simplified-chinese)（MIT），其版权声明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

ComfyUI MCP 汉化面向 [joenorton/comfyui-mcp-server](https://github.com/joenorton/comfyui-mcp-server)（Apache-2.0）；本项目只发布补丁脚本，不分发上游源码，其许可与 NOTICE 见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

LM Studio 是 LM Studio 公司的产品。本项目为第三方界面文本补丁，与 LM Studio 官方无关。
