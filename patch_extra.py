#!/usr/bin/env python3
"""LM Studio 简体中文补丁增强：补充属性词典 + 纯文本节点。"""
import os, re, json, argparse

ATTRS = [
    "children", "title", "label", "tooltip", "placeholder", "aria-label",
    "description", "prettyName", "subtitle", "sectionTitle", "labelSubtext",
    "sectionNameTranslationKeyOrTitle", "displayName", "focusedPlaceholder",
]

I18N = {
    "llm.prediction.reasoning.budgetTokens/title": "推理预算",
    "llm.prediction.reasoning.budgetTokens/subTitle": "思考 token 预算：关闭表示不限制，0 表示立即结束，N > 0 表示限定 token 数",
    "llm.prediction.reasoning.parsing/title": "推理段解析",
    "llm.prediction.reasoning.parsing/subTitle": "如何解析模型输出中的推理段",
    "llm.load.llama.reasoningBudgetMessage/title": "思考预算提示消息",
    "llm.load.llama.reasoningBudgetMessage/subTitle": "思考预算耗尽时，在结束思考标签前注入的消息（默认：不注入）",
    "reasoningBudgetUncheckedHint": "不受限",
    "seedUncheckedHint": "随机种子",
    "ropeFrequencyBaseUncheckedHint": "自动",
    "ropeFrequencyScaleUncheckedHint": "自动",
    "llm.load.numParallelSessions/title": "最大并发预测数",
    "llm.load.numParallelSessions/subTitle": "模型同时最多可运行的预测数。并发越高，单条预测速度可能下降，但每条都能更快开始，总吞吐更高",
    "llm.load.useUnifiedKvCache/title": "统一 KV 缓存",
    "llm.load.useUnifiedKvCache/subTitle": "并发预测共享同一份 KV 缓存以节省内存；关闭后每条预测都能使用完整上下文，但占用更多内存",
    "llm.load.llama.contextCheckpoints/title": "上下文检查点",
    "llm.load.llama.contextCheckpoints/subTitle": "每个槽位保留的上下文检查点上限。数值越小，SWA/循环模型占用的内存越少；0 表示关闭",
    "llm.load.llama.physicalBatchSize/subTitle": "单次处理的提示词 token 上限。数值越大性能可能越好，但占用更多内存",
    "llm.load.llama.ropeFrequencyBase/title": "RoPE 频率基数",
    "ejectButtonText": "卸载",
    "unloadTooltip": "从内存中卸载模型",
    "loadButtonText": "加载",
    "cancelButtonText": "取消",
    "advancedSegmentText": "高级",
    "chatSegmentText": "对话",
    "sendMessageButtonText": "发送",
    "sendMessageButtonText/toolTip": "将提示词和对话历史发送给模型处理",
    "llm.load.promptTemplate/title": "对话模板",
    "llm.load.promptTemplate/subTitle": "引擎协议用于对话、工具、推理和多模态格式化的模板。修改后需要重新加载模型",
    "llm.load.mainGpu/title": "主 GPU",
    "llm.load.mainGpu/subTitle": "优先用于模型计算的 GPU",
    "llm.load.mainGpu/placeholder": "选择主 GPU...",
    "llm.load.splitStrategy/title": "拆分策略",
    "llm.load.splitStrategy/subTitle": "如何在多个 GPU 之间拆分模型计算",
    "llm.load.splitStrategy/placeholder": "选择拆分策略...",
    "llm.load.offloadKVCacheToGpu/title": "将 KV 缓存放入显存",
    "llm.load.offloadKVCacheToGpu/subTitle": "把 KV 缓存放到 GPU 显存。性能更好，但需要更多显存",
    "llm.load.seed/title": "随机种子",
    "llm.load.seed/subTitle": "文本生成所用随机数生成器的种子。-1 表示随机",
    "llm.load.seed/info": "随机种子：固定种子以获得可复现的结果",
    "llm.load.numCpuExpertLayersRatio/title": "强制 MoE 权重留在 CPU 的层数",
    "llm.load.numCpuExpertLayersRatio/subTitle": "强制专家留在 CPU 的层数。可节省显存，且可能比部分 GPU 卸载更快，不推荐手动调整",
    "llm.load.numCpuExpertLayersRatio/info": "指定强制专家留在 CPU 的层数。注意力层仍留在 GPU，节省显存的同时保持性能",
    "llm.load.numExperts/title": "专家数量",
    "llm.load.numExperts/subTitle": "模型中使用的专家数量",
    "llm.load.numExperts/info": "模型中使用的专家数量",
    "llm.load.llama.autoFit/title": "根据硬件自动优化",
    "llm.load.llama.autoFit/subTitle": "加载时由 llama.cpp 根据可用内存自动选择上下文和 GPU 分配",
    "llm.load.llama.evalBatchSize/title": "评估批大小",
    "llm.load.llama.evalBatchSize/subTitle": "提示词处理阶段每次调度的最大提示词 token 数。数值越大性能可能越好，但占用更多内存",
    "llm.load.llama.ropeFrequencyBase/subTitle": "RoPE 旋转位置编码的自定义基频。提高此值可能改善长上下文的性能和质量",
    "llm.load.llama.ropeFrequencyBase/info": "[高级] 调整旋转位置编码的基频，影响位置信息的编码方式",
    "llm.load.llama.ropeFrequencyScale/title": "RoPE 频率缩放",
    "llm.load.llama.ropeFrequencyScale/subTitle": "上下文长度按此系数缩放，以通过 RoPE 扩展有效上下文",
    "llm.load.llama.ropeFrequencyScale/info": "[高级] 修改旋转位置编码的频率缩放，以控制位置编码的梯度",
    "llm.load.llama.acceleration.offloadRatio/title": "GPU 卸载",
    "llm.load.llama.acceleration.offloadRatio/subTitle": "在 GPU 上计算的模型层数，用于 GPU 加速",
    "llm.load.llama.acceleration.offloadRatio/info": "设置卸载到 GPU 的层数。",
    "llm.load.llama.flashAttention/title": "快速注意力",
    "llm.load.llama.flashAttention/subTitle": "在部分模型上降低内存占用并缩短生成时间",
    "llm.load.llama.flashAttention/info": "加速注意力机制，处理更快更高效",
    "llm.load.llama.keepModelInMemory/title": "保留在内存中",
    "llm.load.llama.keepModelInMemory/subTitle": "即使已卸载到 GPU，也为模型保留系统内存。性能更好，但需要更多系统内存",
    "llm.load.llama.keepModelInMemory/info": "防止模型被换出到磁盘，访问更快，但占用更多内存",
    "llm.load.llama.useFp16ForKVCache/title": "KV 缓存使用 FP16",
    "llm.load.llama.useFp16ForKVCache/info": "以半精度（FP16）存储缓存，降低内存占用",
    "llm.load.llama.tryMmap/title": "尝试 mmap()",
    "llm.load.llama.tryMmap/subTitle": "缩短模型加载时间。当模型大于可用系统内存时，关闭此项可能提升性能",
    "llm.load.llama.tryMmap/info": "直接从磁盘把模型文件映射到内存",
    "llm.load.llama.cpuThreadPoolSize/title": "CPU 线程池大小",
    "llm.load.llama.cpuThreadPoolSize/subTitle": "分配给模型计算线程池的 CPU 线程数",
    "llm.load.llama.cpuThreadPoolSize/info": "分配给模型计算线程池的 CPU 线程数。增加线程数并不总是更快，默认值为 <{{dynamicValue}}>。",
    "llm.load.llama.kCacheQuantizationType/title": "K 缓存量化类型",
    "llm.load.llama.kCacheQuantizationType/subTitle": "数值越低内存占用越小，但可能损失质量。不同模型差异很大",
    "llm.load.llama.vCacheQuantizationType/title": "V 缓存量化类型",
    "llm.load.llama.vCacheQuantizationType/subTitle": "数值越低内存占用越小，但可能损失质量。不同模型差异很大",
    "llm.load.llama.vCacheQuantizationType/turnedOnWarning": "⚠️ 未启用快速注意力时必须关闭此项",
    "llm.load.llama.vCacheQuantizationType/disabledMessage": "仅在启用快速注意力时才能开启",
    "llm.load.llama.vCacheQuantizationType/invalidF32MetalState": "⚠️ 使用 F32 时必须关闭快速注意力",
    "appNavigationBarPositionLabel": "导航栏位置",
    "appNavigationBarPositionTop": "顶部",
    "appNavigationBarPositionLeft": "左侧",
    "sideButtonLabels": "显示侧边按钮文字",
    "showModelFileNames": "我的模型：始终显示完整模型文件名",
    "developerLabel": "开发者",
    "modelDefaultsLabel": "模型默认值",
    "showExperimentalFeaturesLabel": "显示实验性功能",
    "enableLocalService": "启用本地 LLM 服务",
    "enableLocalService.subtitle": "无需保持 LM Studio 应用打开，即可使用 LM Studio 的 LLM 服务",
    "enableLocalService.description": "启用后，LM Studio 本地 LLM 服务会随系统启动。关闭 LM Studio 后，本地服务仍会继续运行",
    "separateReasoningContentInResponses": "适用时，在 API 响应中分开 `reasoning_content` 与 `content`",
    "separateReasoningContentInResponses/hint": "此设置仅对 DeepSeek R1 等「推理」模型及其蒸馏版本有效",
    "expandConfigsOnClick": "单击展开配置而非悬停",
    "chat/alwaysShowPromptTemplate": "在对话侧栏中始终显示提示词模板",
    "chat/highlightChatMessageOnHover": "悬停时高亮对话消息",
    "chat/doubleClickMessageToEdit": "双击对话消息以编辑",
    "chat/aiNaming/emoji": "在 AI 生成的对话名称中使用表情符号",
    "showPromptSuggestionsLabel": "新建对话时显示提示词建议",
    "firstTimeExperienceLabel": "对话首次使用引导",
    "firstTimeExperienceMarkCompletedLabel": "标记为已完成",
    "firstTimeExperienceResetLabel": "重置",
    "onboarding/blockTitle": "新手引导",
    "onboarding/resetAllHints": "重置所有新手引导提示",
    "onboarding/resetHintTooltip": "单击以重新启用此新手引导提示",
    "onboarding/noneDismissed": "当前没有已关闭的提示，所有新手引导提示都会显示，直到下次关闭",
    "useHFProxy.label": "使用 LM Studio 的 Hugging Face 代理",
    "useHFProxy.hint": "通过 LM Studio 的 Hugging Face 代理搜索并下载模型，可帮助访问 Hugging Face 有困难的用户",
    "autoFitMinContextLength.label": "自动适配的最低上下文长度",
    "autoFitMinContextLength.description": "要求自动适配至少提供这么多 token 的上下文。无法满足此下限的模型将加载失败",
    "modelLoadingGuardrails.custom.label": "内存上限：",
    "modelLoadingGuardrails.custom.description": "为模型加载设置自定义内存上限。若加载会超过此上限，模型将不会加载",
    "modelLoadingGuardrails.alwaysAllowLoadAnyway": "（不推荐）始终允许「仍然加载」，无需按住 Alt/Option",
    "experimentalLoadPresets": "在预设中启用模型加载配置支持",
    "experimentalLoadPresets.description": "是否允许预设包含模型加载配置。此功能为实验性，欢迎反馈",
    "unloadPreviousJITModelOnLoad": "JIT 模型自动淘汰：确保任意时刻最多只有 1 个模型通过 JIT 加载（会卸载上一个模型）",
    "autoDeleteExtensionPacks": "自动删除最久未使用的运行时扩展包",
    "autoUpdateExtensionPacks": "自动更新选中的运行时扩展包",
    "promptWhenCommittingUnsavedChangesWithNewFields": "预设：提交新字段到预设时显示确认对话框",
    "promptWhenCommittingUnsavedChangesWithNewFields.description": "这可防止意外向预设添加新字段",
    "backendDownloadChannel.label": "LM Studio 扩展包下载频道",
    "backendDownloadChannel.value.stable": "稳定版",
    "backendDownloadChannel.value.beta": "beta 测试版",
    "backendDownloadChannel.value.latest": "开发版",
    "backendDownloadChannel.shortLabel": "运行时下载频道",
    "appUpdateChannel.label": "更新频道",
    "appUpdateChannel.value.stable": "稳定版",
    "appUpdateChannel.value.beta": "beta 测试版",
    "appUpdateChannel.value.alpha": "alpha 测试版",
    "appUpdateChannel.shortLabel": "应用更新频道",
}

PLAIN = {
    "New Folder": "新建文件夹",
    "Empty Folder": "空文件夹",
    "Unnamed Chat": "未命名对话",
    "Save": "保存",
    "Integrations": "插件",
    " Install": " 安装",
    "Pin to chat input": "固定到对话输入框",
    "Unpin from chat input": "从对话输入框取消固定",
    "Integrations select": "插件选择",
    "Send a message to the model...": "向模型发送消息...",
    "Drop file to attach it to the chat": "松开以附加到对话",
    "Think": "思考",
    "Attach": "附加",
    "Attach...": "附加...",
    "Change role": "切换角色",
    "Insert message": "插入消息",
    "Stop generating": "停止生成",
    "Input tokens": "输入 token",
    "Type to filter models...": "输入以筛选模型...",
    "Type to filter plugins...": "输入以筛选插件...",
    "Filter models...": "筛选模型...",
    "Clear model filter": "清除模型筛选",
    "Clear plugin filter": "清除插件筛选",
    "Plugin options": "插件选项",
    "Physical Batch Size": "物理批大小",
    "Max Concurrent Predictions": "最大并发预测数",
    "Unified KV Cache": "统一 KV 缓存",
    "Unified KV Cache: ": "统一 KV 缓存：",
    "Context Checkpoints": "上下文检查点",
    "Enter text here": "在此输入",
    "Hide text": "隐藏文本",
    "Reveal text": "显示文本",
    "Currently Loaded ": "当前已加载 ",
    "Recency": "最近使用",
    "Size": "大小",
    "Downloaded": "已下载",
    "Eject": "卸载",
    " Eject": " 卸载",
    "Preload": "预加载",
    "Use Inference → Reasoning → Enable Thinking.": "在「推理」→「推理」中打开「启用思考」。",
    "This model's chat template does not expose Enable Thinking.": "此模型的对话模板未提供「启用思考」选项。",
    "Reasoning parsing is replaced by thinking controls for llama.cpp engines when LM Studio Engine Protocol is enabled. ": "启用 LM Studio Engine Protocol 时，llama.cpp 引擎的推理段解析由思考控制项替代。 ",
    "Offload KV Cache to GPU": "将 KV 缓存放入显存",
    "Number of Parallel Sessions": "并行会话数",
    "Use Unified KV Cache": "使用统一 KV 缓存",
    "Number of CPU Expert Layers": "CPU 专家层数",
    "Model Load Mode": "模型加载模式",
    "Tensor Parallelism": "张量并行",
    "AutoFit Resource Limits": "自动适配资源上限",
    "Vulkan Device UUIDs": "Vulkan 设备 UUID",
    "Live CUDA VRAM Usage": "CUDA 显存实时占用",
    "Sidecar Speculative Decoding AutoFit": "Sidecar 投机解码自动适配",
    "MTP Speculative Decoding": "MTP 投机解码",
    "DFlash Speculative Decoding": "DFlash 投机解码",
    "DSpark Speculative Decoding": "DSpark 投机解码",
    "Speculative Decoding": "投机解码",
    "MLX Vision Continuous Batching": "MLX 视觉连续批处理",
    "MLX Context AutoFit": "MLX 上下文自动适配",
    "MLX Prompt Disk Cache": "MLX 提示词磁盘缓存",
    "Auto-latch onto generating message": "自动跟随正在生成的消息",
    "Chats and folders you delete will be moved to your operating system's Trash bin.": "删除的对话和文件夹会移到系统回收站。",
    "Chats and folders you delete will be force deleted and cannot be recovered.": "删除的对话和文件夹会被永久删除，且无法恢复。",
    "Conversation Auto-Naming": "对话自动命名",
    "Tools you allow to run without confirmation will appear here": "允许无需确认运行的工具会显示在这里",
    "Allow the following tools to run without confirmation": "允许以下工具无需确认即可运行",
    "Developer mode": "开发者模式",
    "Model Defaults": "模型默认值",
    "Use the maximum context length supported by each model.": "使用每个模型支持的最大上下文长度。",
    "Set the default context length for loading new models. If the model\\'s supported maximum context length is lower, that value will be used.": "设置新模型加载时的默认上下文长度。若模型支持的最大上下文长度更短，则使用该值。",
    "Edit Settings as JSON": "以 JSON 编辑设置",
    " Use in New Chat": " 在新对话中使用",
    "Load Model": "加载模型",
    "View All": "全部",
    "Text Embedding": "文本嵌入",
    "Drafters": "草稿模型",
    "Sign in required": "需要登录",
    "Please sign in to your LM Studio account to use LM Link.": "请登录 LM Studio 账户以使用 LM Link。",
    "Sign in": "登录",
    "Complete in the browser...": "请在浏览器中完成...",
    "Pick a model ": "选择模型 ",
    " Load Model": " 加载模型",
    "Estimated Memory Usage": "预估内存占用",
    "Total": "总计",
    "Max draft tokens": "最大草稿 token 数",
    "Min draft tokens": "最小草稿 token 数",
    "Draft probability": "草稿概率",
    "Max Draft Tokens": "最大草稿 token 数",
    "Min Draft Tokens": "最小草稿 token 数",
    "Drafting Probability Cutoff": "草稿概率阈值",
    "Maximum number of draft tokens to generate.": "生成草稿 token 的最大数量。",
    "Minimum draft length to verify with the main model.": "交给主模型验证的最小草稿长度。",
    "Continue drafting while token probability is at or above this threshold.": "token 概率不低于此阈值时继续起草。",
    "Draft model": "草稿模型",
    "Configure load-time speculative decoding.": "配置加载时的投机解码。",
    "Reset all speculative decoding overrides.": "重置所有投机解码覆盖项。",
    "Select a model to see speculation options.": "选择模型后可查看投机选项。",
    "MTP speculation is not available for this model.": "此模型不支持 MTP 投机。",
    "MTP speculation is not supported by the selected runtime.": "所选运行时不支持 MTP 投机。",
    "MTP speculation is not configurable for this model.": "此模型无法配置 MTP 投机。",
    "Draft model speculation is not supported by the selected runtime.": "所选运行时不支持草稿模型投机。",
    "Select a draft model to use Draft Model speculation.": "选择草稿模型以启用草稿模型投机。",
    "Select an MTP sidecar model to use MTP speculation.": "选择 MTP sidecar 模型以启用 MTP 投机。",
    "No MTP sidecar models available": "没有可用的 MTP sidecar 模型",
    "Choose MTP sidecar model": "选择 MTP sidecar 模型",
    "DFlash speculation is not supported by the selected runtime.": "所选运行时不支持 DFlash 投机。",
    "DSpark speculation is not supported by the selected runtime.": "所选运行时不支持 DSpark 投机。",
    "No compatible DFlash draft models are indexed for this model.": "此模型未索引到兼容的 DFlash 草稿模型。",
    "Select a DFlash draft model to use DFlash speculation.": "选择 DFlash 草稿模型以启用 DFlash 投机。",
    "No compatible DSpark draft models are indexed for this model.": "此模型未索引到兼容的 DSpark 草稿模型。",
    "Select a DSpark draft model to use DSpark speculation.": "选择 DSpark 草稿模型以启用 DSpark 投机。",
    "Go to Load → Advanced Load Params → Speculative Decoding → Draft model.": "前往「加载」→「高级加载参数」→「投机解码」→「草稿模型」。",
    "When loading a model, enable Advanced Load Params and configure Speculative Decoding → Draft model.": "加载模型时，启用「高级加载参数」并配置「投机解码」→「草稿模型」。",
    "llama.cpp Arguments Override": "llama.cpp 参数覆盖",
    "Exclude all LM Studio configuration arguments": "排除所有 LM Studio 配置参数",
    "Required by LM Studio": "LM Studio 必需",
    "LM Studio configurations": "LM Studio 配置",
    "Exclude all Bionic configuration arguments": "排除所有 Bionic 配置参数",
    "Required by Bionic": "Bionic 必需",
    "Bionic configurations": "Bionic 配置",
    "Additional arguments": "附加参数",
    "Add argument": "添加参数",
    "Remove argument": "移除参数",
    "Override argument": "覆盖参数",
    "Export Overrides to Clipboard": "导出覆盖到剪贴板",
    "Import Overrides from Clipboard": "从剪贴板导入覆盖",
    "Replace existing overrides?": "替换现有覆盖？",
    "Importing will replace all configured llama.cpp argument overrides.": "导入将替换所有已配置的 llama.cpp 参数覆盖。",
    "Failed to export overrides": "导出覆盖失败",
    "Failed to import overrides": "导入覆盖失败",
    "The clipboard could not be accessed. Check your system permissions and try again.": "无法访问剪贴板。请检查系统权限后重试。",
    "The clipboard does not contain valid llama.cpp argument overrides.": "剪贴板中没有有效的 llama.cpp 参数覆盖。",
    "These settings are for advanced users only. Do not change them unless you know what you are doing. If you encounter issues after configuring overrides, please mention those overrides in your bug report. Changes made here may override values from sources that would otherwise have higher priority, including API requests.": "这些设置仅供高级用户使用。除非你清楚自己在做什么，否则不要修改。配置覆盖后若遇到问题，请在问题报告中注明这些覆盖项。此处的更改可能覆盖原本优先级更高的来源（含 API 请求）的值。",
}

# 已打过的旧译名 → 新译名，保证重复运行也能改名
MIGRATE = {
    '"集成"': '"插件"',
    '"集成选择"': '"插件选择"',
    '"开启集成以显示选项"': '"开启插件以显示选项"',
}


# 插件清单 schema 不接受显示名字段，只能在渲染层把 identifier 映射成中文名；
# 只改显示文本，标识符、搜索键、调用参数一律保持原样。
PLUGIN_ZH_FULL = [
    ("alexandreaxell/context-compactor", "上下文压缩"),
    ("esalesninja/memory", "长期记忆"),
    ("lmstudio/js-code-sandbox", "代码解释器"),
    ("lmstudio/rag-v1", "与文件对话"),
    ("taipeihugo/big-rag", "知识库检索"),
    ("altra/web-search", "联网搜索"),
    ("khtsly/skills", "技能系统"),
]
PLUGIN_ZH_SHORT = [
    ("context-compactor", "上下文压缩"),
    ("memory", "长期记忆"),
    ("js-code-sandbox", "代码解释器"),
    ("rag-v1", "与文件对话"),
    ("big-rag", "知识库检索"),
    ("web-search", "联网搜索"),
    ("skills", "技能系统"),
]
# 旧版补丁写入包里的是前四组映射；扩展时以它为锚点，避免整链重建。
PLUGIN_ZH_FULL_V1 = PLUGIN_ZH_FULL[:4]
PLUGIN_ZH_SHORT_V1 = PLUGIN_ZH_SHORT[:4]


def plugin_chain(expr, with_short=False, full=None, short=None):
    full = PLUGIN_ZH_FULL if full is None else full
    short = PLUGIN_ZH_SHORT if short is None else short
    pairs = full + (short if with_short else [])
    for en, zh in pairs:
        expr += '.replace("%s","%s")' % (en, zh)
    return expr


def lit(s):
    """把文案转成可安全嵌入 JS 双引号字符串的形式。"""
    return (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r", "\\r")
        .replace("\n", "\\n")
    )


# 插件配置面板的字段名/说明/选项由插件运行时提供，只能在通用配置行渲染时映射。
PLUGIN_FIELD_ZH = [
    # 上下文压缩
    ("Compaction trigger", "压缩触发阈值"),
    (
        "Compact once this fraction of the context window is used. Lower keeps the context short, "
        "which keeps generation fast, at the cost of compacting more often. Tool definitions are "
        "not counted by the measurement, so leave some headroom.",
        "上下文窗口用量达到此比例时执行压缩。设低一些可让上下文保持简短、生成更快，但压缩会更频繁。"
        "工具定义不计入该比例，请预留余量。",
    ),
    ("Recent context kept verbatim", "原样保留的近期上下文"),
    (
        "How many tokens at the end of the conversation are never summarized. Measured in tokens, "
        "not messages: one tool result can be worth forty ordinary replies, and a tail counted in "
        "messages can overflow the window on its own.",
        "对话末尾有多少 token 永不摘要。按 token 而非消息条数计算：一个工具结果可能相当于四十条普通回复，"
        "仅按消息条数估算的尾部就可能单独撑爆窗口。",
    ),
    ("Summarize in chunks of", "分块摘要大小"),
    (
        "Tokens of history per summary. Each chunk costs one model call whatever its size, and "
        "reading is far cheaper than writing — so smaller chunks make compaction slower, not "
        "faster. Lower it only if summaries are losing detail.",
        "每次摘要覆盖的历史 token 数。每块无论大小都要调用一次模型，而读取远比写入便宜——"
        "所以块越小，压缩越慢而不是越快。只有摘要丢失细节时才调低。",
    ),
    ("Maximum size of a tool result", "工具结果最大长度"),
    (
        "Tool results are truncated to this many tokens before the model sees them. Servers set no "
        "such limit of their own: reading one large file can return more than the context holds and "
        "kill the reply outright. Compaction cannot help — it runs before the reply, not during it.",
        "工具结果在模型看到之前会被截断到这个 token 数。服务端本身不设此限制：读取一个大文件就可能"
        "返回超出上下文容量的内容，直接中断回复。压缩帮不上忙——它在回复开始前运行，而不是过程中。",
    ),
    ("Archive folder (optional)", "归档文件夹（可选）"),
    (
        "Folder where the verbatim transcript and the consolidated state note are written on every "
        "compaction — an Obsidian vault works well. Leave empty to keep everything in memory and "
        "write nothing to disk.",
        "每次压缩时，把逐字记录和汇总状态笔记写入此文件夹——Obsidian 库就很合适。"
        "留空则全部保留在内存中，不写磁盘。",
    ),
    ("Announce compaction in chat", "在对话中提示压缩"),
    (
        "Show a one-line notice with the before/after token counts when compaction runs.",
        "压缩运行时显示一行提示，包含压缩前后的 token 数。",
    ),
    # 长期记忆
    ("Auto-Inject Memories", "自动注入记忆"),
    (
        "Automatically inject global and chat-specific memories into every prompt",
        "自动把全局记忆和当前对话的记忆注入每次提示词",
    ),
    (
        "On - inject memories into every prompt (recommended)",
        "开 — 每次提示词都注入记忆（推荐）",
    ),
    (
        "Off - only use memories when tools are called explicitly",
        "关 — 仅在显式调用工具时使用记忆",
    ),
    # 与文件对话
    ("Retrieval Limit", "检索数量上限"),
    (
        "When retrieval is triggered, this is the maximum number of chunks to return.",
        "触发检索时，最多返回的片段数。",
    ),
    ("Retrieval Affinity Threshold", "检索相似度阈值"),
    (
        "The minimum similarity score for a chunk to be considered relevant.",
        "片段被视为相关所需的最低相似度分数。",
    ),
]

# 旧包已写入上面的字段链；下面把新插件的字段追加到链尾。
PLUGIN_FIELD_ZH_V1 = list(PLUGIN_FIELD_ZH)
PLUGIN_FIELD_ZH += [
    # 知识库检索
    ("Documents Directory", "文档目录"),
    (
        "Root directory containing documents to index. All subdirectories will be scanned.",
        "要建立索引的文档根目录，所有子目录都会被扫描。",
    ),
    ("Vector Store Directory", "向量库目录"),
    (
        "Directory where the vector database will be stored.",
        "向量数据库的存储目录。",
    ),
    ("Embedding Model", "嵌入模型"),
    (
        "LM Studio accepts more than one spelling for the same model—for example "
        "mixedbread-ai/mxbai-embed-large-v1 (Hub / download) or "
        "text-embedding-mxbai-embed-large-v1 (as in lms ls). Both are valid; use one value "
        "consistently for indexing and chat so it matches .big-rag-embedding.json. "
        "Reindex after changing.",
        "LM Studio 允许同一模型有多种写法——例如 mixedbread-ai/mxbai-embed-large-v1（Hub / 下载）"
        "或 text-embedding-mxbai-embed-large-v1（lms ls 中的写法）。两者都有效；索引和对话要始终"
        "使用同一个值，才能与 .big-rag-embedding.json 匹配。修改后请重建索引。",
    ),
    (
        "Maximum number of chunks to return during retrieval.",
        "检索时最多返回的片段数。",
    ),
    (
        "Minimum similarity score for a chunk to be considered relevant.",
        "片段被视为相关所需的最低相似度分数。",
    ),
    ("Chunk Size", "分块大小"),
    (
        "Size of text chunks for embedding (in words).",
        "用于嵌入的文本块大小（按词数计）。",
    ),
    ("Chunk Overlap", "分块重叠"),
    (
        "Overlap between consecutive chunks (in words).",
        "相邻文本块之间的重叠量（按词数计）。",
    ),
    ("Max Concurrent Files", "并发文件数上限"),
    (
        "Maximum number of files to process concurrently during indexing. "
        "Recommend 1 for large PDF datasets.",
        "建立索引时同时处理的文件数上限。大型 PDF 数据集建议设为 1。",
    ),
    ("Parser Delay (ms)", "解析间隔（毫秒）"),
    (
        "Wait time before parsing each document (helps avoid WebSocket throttling).",
        "解析每个文档前的等待时间，可避免 WebSocket 限流。",
    ),
    ("Enable OCR", "启用 OCR"),
    (
        "Enable OCR for image files and image-based PDFs using LM Studio's built-in document parser.",
        "使用 LM Studio 内置文档解析器，对图片文件和图片型 PDF 启用 OCR。",
    ),
    ("Exclude filename patterns", "排除文件名模式"),
    (
        "Optional. One glob per line, matched against each file path relative to Documents Directory "
        "(use /). Lines starting with # are comments. Example: *.png excludes PNGs in any folder; "
        "archive/** excludes that subtree. Does not remove chunks already in the vector store—clear "
        "or reindex to drop old data.",
        "可选。每行一个通配模式，按相对于文档目录的路径匹配（使用 /）。以 # 开头的行是注释。"
        "示例：*.png 排除任意文件夹中的 PNG；archive/** 排除该子树。不会移除向量库中已有的片段"
        "——如需清除旧数据，请清空或重建索引。",
    ),
    ("Additional plain-text extensions", "额外纯文本扩展名"),
    (
        "Optional. One extension per line (e.g. .java, .cs, .py). Files are read as plain text. "
        "Binaries such as .exe and .zip are rejected. Built-in types like PDF and EPUB do not need "
        "to be listed.",
        "可选。每行一个扩展名（如 .java、.cs、.py）。文件按纯文本读取。.exe、.zip 等二进制文件"
        "会被拒绝。PDF、EPUB 等内置类型无需列出。",
    ),
    ("Manual Reindex Trigger", "手动重建索引"),
    (
        "Toggle ON to reindex on the next chat message. Turn it OFF again afterward "
        "(it does not auto-reset). Use “Skip Previously Indexed Files” to skip unchanged files.",
        "开启后，在下次对话消息时重建索引。完成后请再关闭（不会自动复位）。"
        "可用“跳过已索引文件”跳过未变更的文件。",
    ),
    ("Skip Previously Indexed Files", "跳过已索引文件"),
    (
        "Skip unchanged files for faster manual runs. Only indexes new files or changed files.",
        "跳过未变更的文件，让手动重建更快。只索引新增或已变更的文件。",
    ),
    ("Prompt Template", "提示词模板"),
    (
        "Supports {{rag_context}} (required) and {{user_query}} macros for customizing the final prompt.",
        "支持 {{rag_context}}（必需）和 {{user_query}} 宏，用于自定义最终提示词。",
    ),
    # 联网搜索
    ("Max Search Results", "搜索结果数上限"),
    (
        "Number of search results to retrieve per query.",
        "每次查询获取的搜索结果数量。",
    ),
    ("Max Pages to Read", "最多读取页面数"),
    (
        "How many pages to actually fetch and read per search. Higher = more thorough, slower.",
        "每次搜索实际抓取并阅读的页面数。数值越高越详尽，但更慢。",
    ),
    ("Page Fetch Timeout (ms)", "页面抓取超时（毫秒）"),
    (
        "How long to wait when reading a page before giving up.",
        "读取页面时的最长等待时间。",
    ),
    ("Search Language", "搜索语言"),
    (
        "Language/region for search results (e.g. 'en-us', 'en-gb'). Leave blank for global.",
        "搜索结果的语种/地区（如 'en-us'、'en-gb'）。留空表示全球。",
    ),
    ("SearXNG URL", "SearXNG 地址"),
    (
        "Base URL of your self-hosted SearXNG instance (e.g. http://localhost:8080). "
        "Leave blank to use the built-in DDG/Bing scraper. "
        "SearXNG aggregates many engines and has no rate limits.",
        "自建 SearXNG 实例的基础 URL（如 http://localhost:8080）。"
        "留空则使用内置的 DDG/Bing 抓取器。"
        "SearXNG 聚合多个引擎，且没有速率限制。",
    ),
    ("Search Recency Window", "搜索时间范围"),
    (
        "Limit all web searches to results published within this window. "
        "Options: day, week, month, year, any (no filter). "
        "Narrower windows give fresher results but may reduce result count.",
        "将所有网页搜索限制在此时间范围内发布的结果。"
        "可选值：day、week、month、year、any（不限）。"
        "范围越窄结果越新，但数量可能减少。",
    ),
    ("LM Studio URL", "LM Studio 地址"),
    (
        "Base URL of your LM Studio instance for embeddings (e.g. http://localhost:1234). "
        "Used to rerank search results via nomic-embed-text before fetching pages.",
        "LM Studio 实例的基础 URL，用于嵌入（如 http://localhost:1234）。"
        "用于在抓取页面前通过 nomic-embed-text 对搜索结果重排序。",
    ),
    # 技能系统
    ("Auto-Inject Skills List", "自动注入技能清单"),
    (
        "Automatically inject the list of available skills into every prompt so the model "
        "knows when to use them",
        "自动把可用技能清单注入每次提示词，让模型知道何时使用技能。",
    ),
    (
        "On - inject skill list into every prompt (recommended)",
        "开 — 每次提示词都注入技能清单（推荐）",
    ),
    (
        "Off - only use skills when tools are called explicitly",
        "关 — 仅在显式调用工具时使用技能",
    ),
    ("Max Skills in Context", "上下文内技能上限"),
    (
        "Maximum number of skills to list in the injected prompt (1-30)",
        "注入提示词中列出的技能数量上限（1-30）。",
    ),
    ("Skills Paths", "技能目录"),
    (
        lit('Semicolon-separated list of skill directories, loaded in order. Leave empty to use '
            'last saved paths. Enter "default" to reset to ~/.lmstudio/plugin-data/skills'),
        lit('以分号分隔的技能目录列表，按顺序加载。留空则使用上次保存的路径。'
            '输入 "default" 可重置为 ~/.lmstudio/plugin-data/skills'),
    ),
    ("Shell Path (optional)", "命令解释器路径（可选）"),
    (
        "Override the shell used by run_command. Leave empty to auto-detect "
        "(bash on Unix, pwsh/powershell/cmd on Windows).",
        "覆盖 run_command 使用的命令解释器。留空则自动检测"
        "（Unix 用 bash，Windows 用 pwsh/powershell/cmd）。",
    ),
    ("Windows Shell", "Windows 命令解释器"),
    (
        "Which shell run_command uses on Windows. Select PowerShell to prefer pwsh -> powershell.exe.",
        "run_command 在 Windows 下使用的命令解释器。选择 PowerShell 会优先使用 pwsh，"
        "其次 powershell.exe。",
    ),
    ("Command Prompt (cmd.exe)", "命令提示符（cmd.exe）"),
    ("PowerShell (powershell.exe)", "PowerShell（powershell.exe）"),
]

# 长文案必须先于短字段名替换：短名可能是某段说明的一部分（例如 Documents
# Directory 就出现在 Exclude filename patterns 的说明里），若先替换短名，后面
# 整段说明就再也匹配不到了。
PLUGIN_FIELD_ZH.sort(key=lambda pair: len(pair[0]), reverse=True)

PLUGIN_TOOL_DESC_ZH = [
    # 代码解释器：SDK 的 text 模板会把单换行并成空格，段落间保留空行。
    (
        "Run a JavaScript code snippet using deno. You cannot import external modules but you have read/write access to the current working directory.\\n\\n"
        "Pass the code you wish to run as a string in the 'javascript' parameter.\\n\\n"
        "By default, the code will timeout in 5 seconds. You can extend this timeout by setting the 'timeout_seconds' parameter to a higher value in seconds, up to a maximum of 60 seconds.\\n\\n"
        "You will get the stdout and stderr output of the code execution, thus please print the output you wish to return using 'console.log' or 'console.error'.",
        "使用 deno 运行一段 JavaScript 代码。无法导入外部模块，但对当前工作目录有读写权限。\\n\\n"
        "把要运行的代码作为字符串传给 'javascript' 参数。\\n\\n"
        "默认超时 5 秒。可通过 'timeout_seconds' 参数延长，单位为秒，最长 60 秒。\\n\\n"
        "执行结束后会返回 stdout 与 stderr，请用 'console.log' 或 'console.error' 打印要返回的内容。",
    ),
    (
        "Read all global memories from ~/.lmstudio/memories/global.md. Each line is one memory entry.",
        "从 ~/.lmstudio/memories/global.md 读取所有全局记忆。每行是一条记忆。",
    ),
    (
        "Read memories for the current chat from ~/.lmstudio/memories/<chat-id>_<chat-name>.md "
        "(uses 'unnamed' when the chat has no name). Each line is one memory entry.",
        "从 ~/.lmstudio/memories/<chat-id>_<chat-name>.md 读取当前对话的记忆"
        "（对话未命名时使用 'unnamed'）。每行是一条记忆。",
    ),
    (
        "Append or replace a line in ~/.lmstudio/memories/global.md. Use `Label: value` format. "
        "User facts: `User name: Yusuf`. AI persona: `AI Name: Güzel`, `AI Tone: Direct`. Same "
        "label replaces the older global line. Prefer for facts that apply across all conversations.",
        "在 ~/.lmstudio/memories/global.md 中追加或替换一行。格式为 `标签: 值`。"
        "用户事实：`User name: Yusuf`。AI 设定：`AI Name: Güzel`、`AI Tone: Direct`。"
        "相同标签会替换旧的全局行。适用于跨所有对话都成立的事实。",
    ),
    (
        "Append or replace a line in the current chat memory file. Use `Label: value` format. Same "
        "label replaces the older chat line. Chat values override global values with the same label. "
        "Use for project/task/thread-specific context.",
        "在当前对话的记忆文件中追加或替换一行。格式为 `标签: 值`。相同标签会替换旧的对话行。"
        "对话值会覆盖同标签的全局值。适用于项目/任务/线程相关的上下文。",
    ),
    (
        "Remove a memory line by its 1-based line number from ~/.lmstudio/memories/global.md.",
        "按从 1 开始的行号，从 ~/.lmstudio/memories/global.md 删除一条记忆。",
    ),
    (
        "Remove a memory line by its 1-based line number from the current chat memory file.",
        "按从 1 开始的行号，从当前对话的记忆文件删除一条记忆。",
    ),
]

# 旧包已写入上面的工具说明链；下面把新插件的工具说明追加到链尾。
PLUGIN_TOOL_DESC_ZH_V1 = list(PLUGIN_TOOL_DESC_ZH)
PLUGIN_TOOL_DESC_ZH += [
    # 知识库检索
    (
        lit("Search the Big RAG indexed document collection for passages relevant to a query. "
            "Returns matching text snippets with file names and similarity scores."),
        lit("在 Big RAG 已索引的文档集合中搜索与查询相关的段落。"
            "返回匹配的文本片段、文件名和相似度分数。"),
    ),
    (
        lit("Return Big RAG index statistics: chunk count, unique file count, and configured directories."),
        lit("返回 Big RAG 索引统计：片段数、去重文件数和已配置的目录。"),
    ),
    # 联网搜索
    (
        lit("ALWAYS call this tool FIRST before calling any search tool. Never skip this step, "
            "even if the question seems clear.\n\n"
            "This tool detects ambiguity in the user's question and tells you whether you need to "
            "ask the user clarifying questions before searching.\n\n"
            "Two outcomes: STATUS: READY    — question is specific enough, search immediately with "
            "the refined_query. STATUS: CLARIFY  — question is ambiguous or underspecified. Ask the "
            "user the listed questions first. Do NOT search until the user answers.\n\n"
            "Asking one focused round of questions upfront saves wasted searches and gives the user "
            "a much better, targeted answer."),
        lit("在调用任何搜索工具之前，务必先调用此工具。即使问题看起来很清楚，也不可跳过。\n\n"
            "此工具会检测用户问题中的歧义，并告诉你是否需要在搜索前向用户提出澄清问题。\n\n"
            "两种结果：STATUS: READY —— 问题足够具体，立即用 refined_query 搜索。"
            "STATUS: CLARIFY —— 问题含糊或信息不足，先向用户提出列出的问题。"
            "在用户回答前不要搜索。\n\n"
            "先进行一轮集中提问可以避免无效搜索，并给用户更有针对性的答案。"),
    ),
    (
        lit("The primary research tool. Unlike a basic search engine, this tool: • Retrieves search "
            "results AND actually reads the top pages (not just snippets) • Returns structured facts "
            "with source attribution • Surfaces the full page text for you to reason over • Flags "
            "source credibility for each result\n\n"
            "Use for: most questions that need factual answers from the web. Prefer deep_search when "
            "you need multiple angles or research_topic for comprehensive reports."),
        lit("主要的调研工具。与普通搜索引擎不同，此工具会：• 获取搜索结果，并实际阅读排名靠前的页面"
            "（不只是摘要）• 返回带来源归属的结构化事实 • 提供完整页面文本供你推理 • 为每个结果标记"
            "来源可信度\n\n"
            "适用场景：大多数需要从网络获取事实答案的问题。需要多角度时优先用 deep_search，"
            "需要综合报告时用 research_topic。"),
    ),
    (
        lit("Fetch a specific URL and read its full content. This is the tool that regular search "
            "CANNOT do — it gives you the actual article text, not a short snippet.\n\n"
            "Use when: • The user shares a URL and wants you to read it • A search result looks "
            "relevant but you need the full text • You need the exact wording of a policy, study, or "
            "article • You want to verify what a source actually says vs what's quoted elsewhere"),
        lit("抓取指定 URL 并阅读其完整内容。这是普通搜索做不到的——它给出文章的实际文本，"
            "而不是简短摘要。\n\n"
            "适用场景：• 用户提供了 URL 并希望你阅读 • 搜索结果看起来相关，但你需要全文 "
            "• 你需要政策、研究或文章的原文措辞 • 你想核实来源实际说了什么，而不是别处的引用"),
    ),
    (
        lit("Multi-angle research. Runs 3–5 separate searches from different perspectives on the "
            "same topic, reads pages for each, and returns everything together.\n\n"
            "This defeats single-search bias — you get coverage from different angles, not just the "
            "top SEO results for one query.\n\n"
            "Angles can be: different framings, pro/con, historical vs current, expert vs critic, "
            "technical vs practical, etc. Provide your own angles or let the tool pick.\n\n"
            "Use when: you need a complete picture, not just one answer. Complex topics, "
            "controversies, research questions, anything where one search could miss something "
            "important."),
        lit("多角度调研。针对同一主题从不同视角运行 3–5 次独立搜索，阅读每个角度的页面，"
            "并把结果汇总返回。\n\n"
            "这能避免单一搜索的偏差——你得到的覆盖来自不同角度，而不只是某个查询的 SEO 前列结果。\n\n"
            "角度可以是：不同表述、支持与反对、历史与现状、专家与批评者、技术与实践等。"
            "你可以自行提供角度，也可让工具选择。\n\n"
            "适用场景：你需要完整图景而不是单一答案时。复杂话题、争议、研究性问题，"
            "以及任何单次搜索可能遗漏重要信息的情况。"),
    ),
    (
        lit('Cross-check a specific claim against multiple sources — both supporting and opposing. '
            "Returns evidence for and against, then a verdict signal.\n\n"
            "Verdict signals: supported    — multiple independent sources confirm it "
            "disputed     — credible sources on both sides "
            "unsupported  — no solid evidence found for it "
            "nuanced      — true in some context but misleading as stated "
            "uncertain    — thin coverage, very recent, or inconclusive\n\n"
            'Use when: someone asserts something as fact and you want to verify it before repeating '
            'it, or when the user asks "is it true that...".'),
        lit("将某一具体说法与多个来源交叉核对——既包括支持方，也包括反对方。"
            "返回支持与反对的证据，并给出结论信号。\n\n"
            "结论信号：supported——多个独立来源确认；"
            "disputed——可信来源双方各执一词；"
            "unsupported——未找到可靠证据支持；"
            "nuanced——在某种语境下成立，但按原样陈述会误导；"
            "uncertain——覆盖不足、事件过新或尚无定论\n\n"
            "适用场景：有人把某件事当作事实陈述，你希望在复述前核实，"
            "或用户问“这是真的吗……”。"),
    ),
    (
        lit("Verify a specific number, percentage, or statistic and trace it to its primary source. "
            "Essential because statistics are often: • Outdated (cited from a 10-year-old study) "
            "• Misquoted (the real number is different) • Out of context (applies to a subset, not "
            "the general claim) • Fabricated (no original source exists)\n\n"
            "Returns: primary source candidates, original publisher, date, actual number found."),
        lit("核实具体数字、百分比或统计量，并追溯到原始来源。这很有必要，因为统计数据经常："
            "• 过时（引用的是十年前的研究）• 被误引（真实数字不同）"
            "• 脱离语境（只适用于子集，而非整体结论）• 系伪造（不存在原始来源）\n\n"
            "返回：主要来源候选、原始发布者、日期、实际找到的数值。"),
    ),
    (
        lit("Trace a claim back to its original source — the study, report, speech, or official "
            "document where it was first published. This matters because secondary and tertiary "
            "sources often distort the original finding.\n\n"
            "Use when: something is widely cited but the original source is unclear, or when you "
            "want the most authoritative version of a claim."),
        lit("把某个说法追溯回其原始来源——最早发布该内容的研究、报告、演讲或官方文件。"
            "这一点很重要，因为二手和三手来源常常会曲解原始结论。\n\n"
            "适用场景：某说法被广泛引用但原始出处不明，或你希望获得最权威的版本。"),
    ),
    (
        lit("Time-filtered search — only returns results from the specified window. Critical for "
            "fast-moving topics where older results can be actively misleading.\n\n"
            "Use when: asking about current events, recent developments, new research, product "
            "releases, policy changes, or anything where recency matters."),
        lit("按时间过滤的搜索——只返回指定时间窗口内的结果。对于快速变化的话题至关重要，"
            "因为较早的结果可能产生误导。\n\n"
            "适用场景：询问时事、近期进展、新研究、产品发布、政策变化，或任何时效性重要的内容。"),
    ),
    (
        lit("Fetch multiple sources on the same topic and surface where they agree, where they "
            "conflict, and what each source uniquely claims.\n\n"
            "This is the tool for detecting spin, bias, and framing differences. The same fact can "
            "be framed very differently by different publications.\n\n"
            "Use when: you have multiple URLs to compare, or want to compare coverage of an "
            "event/topic across different types of sources."),
        lit("抓取同一主题的多个来源，并列出它们在哪些方面一致、哪些方面冲突，"
            "以及各自独有的说法。\n\n"
            "这个工具用于发现倾向性、偏见和叙述框架差异。"
            "同一事实可能被不同出版物以截然不同的方式呈现。\n\n"
            "适用场景：你有多个 URL 需要对比，或想比较不同来源对某事件/话题的报道。"),
    ),
    (
        lit("Find what domain experts, researchers, and authoritative institutions actually say "
            "about a topic — not what random websites claim they say.\n\n"
            "Targets: academic papers, official statements, expert interviews, research organization "
            "reports, professional body guidelines.\n\n"
            "Use when: you need the scientific/expert consensus, not just the popular view. "
            "Especially useful for health, science, policy, and technical topics."),
        lit("查找领域专家、研究者和权威机构对某话题的实际看法——而不是普通网站声称他们说了什么。\n\n"
            "目标来源：学术论文、官方声明、专家访谈、研究机构报告、专业机构指南。\n\n"
            "适用场景：你需要科学/专家共识，而不只是流行观点。"
            "对健康、科学、政策和技术类话题尤其有用。"),
    ),
    (
        lit("Search specifically for academic papers, studies, and research publications. Targets: "
            "arXiv, Semantic Scholar, PubMed, and major research journals.\n\n"
            "Returns: paper titles, authors, abstracts, publication year, direct links.\n\n"
            "Use when: the question requires scientific evidence, medical guidance, technical "
            "research, or any topic where peer review matters."),
        lit("专门搜索学术论文、研究和科研出版物。目标来源：arXiv、Semantic Scholar、PubMed "
            "和主要研究期刊。\n\n"
            "返回：论文标题、作者、摘要、发表年份、直接链接。\n\n"
            "适用场景：问题需要科学证据、医学指导、技术研究，或任何同行评审很重要的领域。"),
    ),
    (
        lit("Full multi-step research. Runs multiple searches from different angles, reads key "
            "pages, and assembles everything into a structured research brief.\n\n"
            "Returns a comprehensive evidence base: key facts, source diversity, open questions, "
            "and confidence map.\n\n"
            "Depth levels: overview      — 3 search angles, 1–2 pages each (faster) "
            "detailed      — 5 angles, 2–3 pages each "
            "comprehensive — 7 angles, 3 pages each (thorough, takes longer)\n\n"
            "Use when: someone asks a complex question that needs a full picture, not a quick "
            "answer — and you want to do it properly in one call."),
        lit("完整的多步骤调研。从多个角度运行多次搜索，阅读关键页面，"
            "并把所有内容整理成结构化的调研简报。\n\n"
            "返回一份全面的证据基础：关键事实、来源多样性、待解问题和置信度图。\n\n"
            "深度级别：overview——3 个搜索角度，每个 1–2 页（较快）；"
            "detailed——5 个角度，每个 2–3 页；"
            "comprehensive——7 个角度，每个 3 页（详尽，耗时更长）\n\n"
            "适用场景：有人提出需要完整图景的复杂问题，而不是快速答案——"
            "并且你希望一次调用就做好。"),
    ),
    (
        lit("News-specific search. Targets established journalism and press sources, not SEO "
            "content farms. Returns recent news coverage with publication signals.\n\n"
            "Unlike search_recent (which filters by date), this filters by SOURCE TYPE — it actively "
            "prefers news outlets over blogs, product pages, and opinion sites.\n\n"
            "Use when: the question is about a current event, breaking news, policy change, "
            "corporate announcement, or anything where journalistic sourcing matters. Pair with "
            "search_recent for time-filtered news coverage."),
        lit("新闻类搜索。面向正规新闻业和媒体来源，而不是 SEO 内容农场。"
            "返回带有发布信号的近期新闻报道。\n\n"
            "与按日期过滤的 search_recent 不同，这里按来源类型过滤——"
            "会优先选择新闻媒体，而非博客、产品页面和观点网站。\n\n"
            "适用场景：问题涉及时事、突发新闻、政策变化、企业公告，"
            "或任何报道来源可靠性重要的内容。可与 search_recent 搭配，获取按时间过滤的新闻覆盖。"),
    ),
    (
        lit("Assess the credibility and reliability of a URL or domain. Returns: • Domain type "
            "(government, academic, news, blog, etc.) • Known credibility signals from the URL "
            "• Search results about the publication's reputation • Red flags to watch for\n\n"
            "Use when: a source looks unfamiliar, suspicious, or you want to know how much weight to "
            "give it before citing it."),
        lit("评估 URL 或域名的可信度与可靠性。返回：• 域名类型（政府、学术、新闻、博客等）"
            "• URL 中已知的可信度信号 • 有关该出版物声誉的搜索结果 • 需要警惕的危险信号\n\n"
            "适用场景：某个来源看起来陌生、可疑，或你想在引用前了解应给予它多少权重。"),
    ),
    # 技能系统
    (
        lit("List or search available skills. Without a query, returns all skills up to the limit. "
            "With a query, scores and ranks skills by relevance across name, tags, description, and "
            "SKILL.md body content - use this to find skills relevant to a task without needing all "
            "skills in context. Always call read_skill_file on any skill that looks relevant before "
            "starting work."),
        lit("列出或搜索可用技能。不提供查询时，返回上限内的所有技能。提供查询时，"
            "会根据名称、标签、描述和 SKILL.md 正文内容对技能进行相关度评分和排序——"
            "用它在不把全部技能放进上下文的情况下找到与任务相关的技能。"
            "开始工作前，务必对任何看起来相关的技能调用 read_skill_file。"),
    ),
    (
        lit("Read a file from within a skill directory. Accepts either a skill name (e.g. 'docx') or "
            "an absolute path to any file within a skill directory. Defaults to reading the SKILL.md "
            "entry point when no file_path is given. ALWAYS call this before starting any task the "
            "skill covers - the SKILL.md contains critical instructions built from trial and error. "
            "Multiple skills may be relevant to a task; read all of them before proceeding."),
        lit("读取技能目录中的文件。接受技能名称（如 'docx'）或技能目录内任意文件的绝对路径。"
            "未提供 file_path 时默认读取入口 SKILL.md。开始任何该技能覆盖的任务前，务必先调用此工具"
            "——SKILL.md 包含从试错中总结的关键说明。多个技能可能都相关；继续之前请全部读完。"),
    ),
    (
        lit("List all files inside a skill directory. Accepts either a skill name (e.g. 'docx') or an "
            "absolute path to a skill directory. Use this after reading SKILL.md when you need to "
            "discover additional supporting files such as helper scripts, templates, or supplementary "
            "documentation the SKILL.md references."),
        lit("列出技能目录内的所有文件。接受技能名称（如 'docx'）或技能目录的绝对路径。"
            "阅读 SKILL.md 后，当你需要查找它引用的辅助脚本、模板或补充文档时使用。"),
    ),
    (
        lit("Read the contents of any file in the user's workspace. Use this to inspect code, data, "
            "or configuration files outside of the skills directory."),
        lit("读取用户工作区中的任意文件。用它检查技能目录之外的代码、数据或配置文件。"),
    ),
    (
        lit("Create or overwrite a file completely with new content. Prefer this over run_command for "
            "writing code or text, as it avoids shell escaping issues."),
        lit("用新内容完整创建或覆盖文件。写代码或文本时优先使用它而不是 run_command，"
            "因为它能避免 shell 转义问题。"),
    ),
    (
        lit("Modify an existing file by replacing a specific search string with a new string. Prefer "
            "this over write_file when making small changes to large files."),
        lit("通过把特定搜索字符串替换为新字符串来修改现有文件。"
            "对大型文件做小改动时优先使用它而不是 write_file。"),
    ),
    (
        lit("Execute a shell command on the user's machine. On Windows this runs in PowerShell Core "
            "(pwsh.exe), PowerShell (powershell.exe), or cmd.exe - whichever is available, in that "
            "order. On macOS and Linux this runs in bash or sh. The platform and shell fields in the "
            "response tell you exactly which shell was used so you can adapt syntax accordingly. Use "
            "this to run scripts, install packages, or perform system tasks. IMPORTANT: Do NOT use "
            "this to write or edit files via `echo` or `cat`. Use the `write_file` or `patch_file` "
            "tools instead. Python scripts referenced by skills can be executed directly - copy the "
            "script path from list_skill_files and run it with python3 (or python on Windows)."),
        lit("在用户机器上执行 shell 命令。在 Windows 上会按顺序使用 PowerShell Core（pwsh.exe）、"
            "PowerShell（powershell.exe）或 cmd.exe 中可用的一个。在 macOS 和 Linux 上使用 bash "
            "或 sh。响应中的 platform 和 shell 字段会准确告诉你使用了哪个 shell，以便你相应调整语法。"
            "用它运行脚本、安装包或执行系统任务。重要：不要用它通过 `echo` 或 `cat` 写入或编辑文件，"
            "请改用 `write_file` 或 `patch_file`。技能引用的 Python 脚本可以直接执行——"
            "从 list_skill_files 复制脚本路径，并用 python3（Windows 上为 python）运行。"),
    ),
    (
        lit("Create a directory (and any missing parent directories) at the given path. Idempotent: "
            "succeeds silently if the directory already exists, so it is safe to call without "
            "checking first. Equivalent to `mkdir -p` / `New-Item -Force -ItemType Directory`."),
        lit("在指定路径创建目录（包括缺失的父目录）。幂等：目录已存在时静默成功，"
            "因此无需先检查即可安全调用。"
            "等价于 `mkdir -p` / `New-Item -Force -ItemType Directory`。"),
    ),
    (
        lit("Return path information about the user's environment: home directory, current working "
            "directory, platform, and path separator. Call this at the start of any task that "
            "involves absolute paths so you know the correct base path without guessing the username "
            "or drive letter (e.g. C:\\Users\\user on Windows, /Users/user on macOS, /home/user on "
            "Linux)."),
        lit("返回用户环境的路径信息：主目录、当前工作目录、平台和路径分隔符。"
            "开始任何涉及绝对路径的任务时调用它，这样无需猜测用户名或盘符就能知道正确的基础路径"
            "（例如 Windows 上的 C:\\Users\\user，macOS 上的 /Users/user，Linux 上的 /home/user）。"),
    ),
    (
        lit("List the contents of any directory on the user's machine, returning a tree of files and "
            "subdirectories. Use this to understand a project's structure before reading or editing "
            "files. Prefer this over running `ls` or `dir` via `run_command` - it works the same on "
            "every platform."),
        lit("列出用户机器上任意目录的内容，返回文件和子目录树。"
            "用它先了解项目结构，再读取或编辑文件。"
            "优先使用它，而不是通过 `run_command` 运行 `ls` 或 `dir`——它在所有平台上行为一致。"),
    ),
    (
        lit("Permanently delete a file or an empty directory. To delete a directory and all its "
            "contents recursively, set recursive to true - use with caution as this cannot be "
            "undone. Prefer this over shell commands like `rm` or `Remove-Item` for cross-platform "
            "reliability."),
        lit("永久删除文件或空目录。要递归删除目录及其全部内容，请把 recursive 设为 true"
            "——此操作不可撤销，请谨慎使用。"
            "为了跨平台可靠性，优先使用它而不是 `rm` 或 `Remove-Item` 等 shell 命令。"),
    ),
    (
        lit("Move a file or directory from one location to another. Works across the same filesystem "
            "volume. If you need to move across volumes, use run_command as a fallback. Fails if the "
            "destination already exists to prevent accidental overwrites."),
        lit("把文件或目录从一个位置移动到另一个位置。适用于同一文件系统卷。"
            "若需跨卷移动，可改用 run_command。目标已存在时会失败，以防意外覆盖。"),
    ),
    (
        lit("Rename a file or directory in place (same parent directory). For moving to a different "
            "location use move_file instead. Fails if a file with the new name already exists."),
        lit("在原位置重命名文件或目录（同一父目录）。要移动到其他位置，请改用 move_file。"
            "新名称已存在时会失败。"),
    ),
    (
        lit("Append text to the end of an existing file without reading or rewriting the whole thing. "
            "Ideal for adding lines to logs, .env files, config lists, or any growing file. Creates "
            "the file (and any missing parent directories) if it does not exist yet."),
        lit("在现有文件末尾追加文本，无需读取或重写整个文件。"
            "适合向日志、.env 文件、配置列表或任何不断增长的文件添加行。"
            "文件（及缺失的父目录）不存在时会自动创建。"),
    ),
]


def text_chain(expr, pairs):
    for en, zh in pairs:
        expr += '.replace("%s","%s")' % (en, zh)
    return expr


def plugin_alias_expr(ident, pairs=None):
    pairs = PLUGIN_ZH_FULL if pairs is None else pairs
    expr = "("
    for en, zh in pairs:
        expr += '%s==="%s"?"%s":' % (ident, en, zh)
    return expr + '"")'


_TITLE_PREFIX = "`${e.owner}/${e.name}`"
_TITLE_CHAIN = plugin_chain(_TITLE_PREFIX)
_TITLE_REST = _TITLE_CHAIN[len(_TITLE_PREFIX):]
_RUN_JS_EN, _RUN_JS_ZH = PLUGIN_TOOL_DESC_ZH[0]
_FIRST_TOOL_EN, _FIRST_TOOL_ZH = PLUGIN_TOOL_DESC_ZH[1]

# 旧包里已写入的四组映射链，作为扩展新插件时的锚点。
_R_CHAIN_BASE = (
    't.typeParam.displayName?.replace("Enable Thinking","启用思考")'
    '.replace("Physical\\u0020Batch Size","物理批大小")'
    '.replace("Context\\u0020Checkpoints","上下文检查点")'
)
_D_CHAIN_BASE = (
    't.typeParam.subtitle?.replace("Controls thinking for chat templates that support enable_thinking.",'
    '"控制支持 enable_thinking 的对话模板是否先思考。")'
)
_FIELD_R_V1 = text_chain(_R_CHAIN_BASE, PLUGIN_FIELD_ZH_V1)
_FIELD_R_NEW = text_chain(_R_CHAIN_BASE, PLUGIN_FIELD_ZH)
_FIELD_D_V1 = text_chain(_D_CHAIN_BASE, PLUGIN_FIELD_ZH_V1)
_FIELD_D_NEW = text_chain(_D_CHAIN_BASE, PLUGIN_FIELD_ZH)
_DN_V1 = text_chain('(a.displayName??"")', PLUGIN_FIELD_ZH_V1)
_DN_NEW = text_chain('(a.displayName??"")', PLUGIN_FIELD_ZH)
_TDN_V1 = text_chain('(t.displayName??"")', PLUGIN_FIELD_ZH_V1)
_TDN_NEW = text_chain('(t.displayName??"")', PLUGIN_FIELD_ZH)
_A_V1 = text_chain("a", PLUGIN_FIELD_ZH_V1)
_A_NEW = text_chain("a", PLUGIN_FIELD_ZH)
_T_V1 = text_chain("t", PLUGIN_FIELD_ZH_V1)
_T_NEW = text_chain("t", PLUGIN_FIELD_ZH)
_TOOL_CHAIN_V1 = text_chain('(a.function.description??"")', PLUGIN_TOOL_DESC_ZH_V1)
_TOOL_CHAIN_NEW = text_chain('(a.function.description??"")', PLUGIN_TOOL_DESC_ZH)
_CHAIN_FULL_V1 = plugin_chain("", full=PLUGIN_ZH_FULL_V1)
_CHAIN_FULL_NEW = plugin_chain("")
_CHAIN_BOTH_V1 = plugin_chain("", True, PLUGIN_ZH_FULL_V1, PLUGIN_ZH_SHORT_V1)
_CHAIN_BOTH_NEW = plugin_chain("", True)
_ALIAS_V1 = plugin_alias_expr("t.identifier", PLUGIN_ZH_FULL_V1)
_ALIAS_NEW = plugin_alias_expr("t.identifier")

RENDER = [
    # 插件映射旧版把 owner 拼错成 esalesnjina，这里修回。
    (
        '.replace("esalesnjina/memory","长期记忆")',
        '.replace("esalesninja/memory","长期记忆")',
    ),
    # 旧版补丁重跑时，纯文本替换会把渲染链里的英文搜索串也换成中文，使其空转；这里修回。
    (
        '.replace("物理批大小","物理批大小")',
        '.replace("Physical\\u0020Batch Size","物理批大小")',
    ),
    (
        '.replace("上下文检查点","上下文检查点")',
        '.replace("Context\\u0020Checkpoints","上下文检查点")',
    ),
    (
        '.replace("投机解码","投机解码")',
        '.replace("Speculative\\u0020Decoding","投机解码")',
    ),
    (
        'j=_||(t.typeParam.hint?t.typeParam.hint:',
        'j=_||(t.typeParam.hint?t.typeParam.hint'
        '.replace("Configure\\u0020load-time speculative decoding.","配置加载时的投机解码。")'
        '.replace("Use\\u0020bundled multi-token prediction heads when loading the model.","加载模型时使用内置的多 token 预测头。")'
        '.replace("Use\\u0020a separate draft model for speculative decoding.","使用单独的草稿模型进行投机解码。")'
        '.replace("Use\\u0020a DFlash sidecar drafter model for speculative decoding.","使用 DFlash sidecar 草稿模型进行投机解码。")'
        '.replace("Use\\u0020a DSpark sidecar drafter model for speculative decoding.","使用 DSpark sidecar 草稿模型进行投机解码。")'
        '.replace("Use\\u0020an MTP sidecar drafter model for speculative decoding.","使用 MTP sidecar 草稿模型进行投机解码。")'
        '.replace("Maximum\\u0020number of draft tokens to generate.","生成草稿 token 的最大数量。")'
        '.replace("Minimum\\u0020draft length to verify with the main model.","交给主模型验证的最小草稿长度。")'
        '.replace("Continue\\u0020drafting while token probability is at or above this threshold.","token 概率不低于此阈值时继续起草。")'
        '.replace("Maximum\\u0020number of context checkpoints to keep per llama-server slot. 0 disables checkpoints.","每个 llama-server 槽位保留的上下文检查点数量上限，0 表示关闭。")'
        ':',
    ),
    (
        'key:a.formatMessage({defaultMessage:"Argument"})',
        'key:a.formatMessage({defaultMessage:"参数"})',
    ),
    (
        'key:"Argument",value:"Value"',
        'key:"参数",value:"值"',
    ),
    (
        'value:a.formatMessage({defaultMessage:"Value"})',
        'value:a.formatMessage({defaultMessage:"值"})',
    ),
    (
        'dynamicValue:a.formatMessage({defaultMessage:"dynamic",',
        'dynamicValue:a.formatMessage({defaultMessage:"动态",',
    ),
    (
        'dynamicValue:"dynamic"',
        'dynamicValue:"动态"',
    ),
    (
        'imported:a.formatMessage({defaultMessage:"Imported"})',
        'imported:a.formatMessage({defaultMessage:"已导入"})',
    ),
    (
        'imported:"Imported",copied:"Copied"',
        'imported:"已导入",copied:"已复制"',
    ),
    (
        'copied:a.formatMessage({defaultMessage:"Copied"})',
        'copied:a.formatMessage({defaultMessage:"已复制"})',
    ),
    (
        'cancel:a.formatMessage({defaultMessage:"Cancel"})',
        'cancel:a.formatMessage({defaultMessage:"取消"})',
    ),
    (
        'cancel:"Cancel",close:"Close"',
        'cancel:"取消",close:"关闭"',
    ),
    (
        'close:a.formatMessage({defaultMessage:"Close"})',
        'close:a.formatMessage({defaultMessage:"关闭"})',
    ),
    (
        'g=t.typeParam.displayName??c(`config:${u}/title`',
        'g=t.typeParam.displayName?.replace("Speculative\\u0020Decoding","投机解码")??c(`config:${u}/title`',
    ),
    (
        'case"off":return"Off";case"draftMtp":return"MTP";',
        'case"off":return"关";case"draftMtp":return"MTP";',
    ),
    (
        'R=d??t.typeParam.displayName??',
        'R=d??t.typeParam.displayName?.replace("Enable Thinking","启用思考").replace("Physical\\u0020Batch Size","物理批大小").replace("Context\\u0020Checkpoints","上下文检查点")??',
    ),
    (
        'R=d??t.typeParam.displayName?.replace("Enable Thinking","启用思考")??',
        'R=d??t.typeParam.displayName?.replace("Enable Thinking","启用思考").replace("Physical\\u0020Batch Size","物理批大小").replace("Context\\u0020Checkpoints","上下文检查点")??',
    ),
    (
        'D=t.typeParam.subtitle,',
        'D=t.typeParam.subtitle?.replace("Controls thinking for chat templates that support enable_thinking.","控制支持 enable_thinking 的对话模板是否先思考。"),',
    ),
    (
        'p=i.replaceAll("Enable Thinking","思考");return(0,n.jsxs)(r.Button,{variant:"buttonNone",tooltip:l,',
        'p=i.replaceAll("Enable Thinking","思考");return(0,n.jsxs)(r.Button,{variant:"buttonNone",tooltip:l?.replace("Controls thinking for chat templates that support enable_thinking.","控制支持 enable_thinking 的对话模板是否先思考。"),',
    ),
    (
        'K("models:loader.info.activePredictionLoopHandlerWarning")',
        '"存在活动的预测循环处理器"',
    ),
    (
        'k("models:loader.info.activePredictionLoopHandlerWarning")',
        '"存在活动的预测循环处理器"',
    ),
    (
        '{displayName:"Bubble",id:"bubble"}',
        '{displayName:"气泡",id:"bubble"}',
    ),
    (
        '{displayName:"Block",id:"block"}',
        '{displayName:"区块",id:"block"}',
    ),
    (
        '{displayName:"OFF",id:"off"},{displayName:"ON",id:"on"}',
        '{displayName:"关",id:"off"},{displayName:"开",id:"on"}',
    ),
    (
        'displayName:"Developer"',
        'displayName:"开发者"',
    ),
    (
        '[i.APP_PAGE_PATHS.models,"Library"]',
        '[i.APP_PAGE_PATHS.models,"模型库"]',
    ),
    (
        '[p.APP_PAGE_PATHS.models,"Library"]',
        '[p.APP_PAGE_PATHS.models,"模型库"]',
    ),
    (
        'defaultValue:"Decision Models"',
        'defaultValue:"决策模型"',
    ),
    (
        'if(s<45)return"Just now";if(s<i)return"Less than 1 minute ago";',
        'if(s<45)return"刚刚";if(s<i)return"不到 1 分钟前";',
    ),
    (
        'return 1===t?"1 min ago":`${t} mins ago`',
        'return 1===t?"1 分钟前":`${t} 分钟前`',
    ),
    (
        'return 1===t?"1 hour ago":`${t} hours ago`',
        'return 1===t?"1 小时前":`${t} 小时前`',
    ),
    (
        'return 1===t?"1 day ago":`${t} days ago`',
        'return 1===t?"1 天前":`${t} 天前`',
    ),
    (
        '{routeName:"Library"}',
        '{routeName:"模型库"}',
    ),
    (
        '{routeName:"Model Server"}',
        '{routeName:"模型服务"}',
    ),
    (
        'W={Info:{displayName:"Info",Icon:u.LmInfo}',
        'W={Info:{displayName:"信息",Icon:u.LmInfo}',
    ),
    (
        'Inference:{displayName:"Inference",Icon:V.LuActivity}',
        'Inference:{displayName:"推理",Icon:V.LuActivity}',
    ),
    (
        'Overrides:{displayName:"Overrides",Icon:h.LmFramework}',
        'Overrides:{displayName:"覆盖项",Icon:h.LmFramework}',
    ),
    (
        'Info:{displayName:"Info",Icon:o.LmInfo}',
        'Info:{displayName:"信息",Icon:o.LmInfo}',
    ),
    (
        'Inference:{displayName:"Inference",Icon:b.LuActivity}',
        'Inference:{displayName:"推理",Icon:b.LuActivity}',
    ),
    (
        'Overrides:{displayName:"Overrides",Icon:i.LmFramework}',
        'Overrides:{displayName:"覆盖项",Icon:i.LmFramework}',
    ),
    # 插件中文显示名（仅显示层）
    (
        'case"rag-v1":return"Chat with Files";case"js-code-sandbox":return"Code Interpreter";default:return u.name}return u.name',
        'case"rag-v1":return"与文件对话";case"js-code-sandbox":return"代码解释器";default:return u.name}'
        'return"context-compactor"===u.name?"上下文压缩":"memory"===u.name?"长期记忆":u.name',
    ),
    (
        'tooltip:`Click to ${k?"disable":"enable"} ${u.name}`',
        'tooltip:`点击${k?"停用":"启用"}：${O}`',
    ),
    (
        'children:at?et.replace("lmstudio/",""):et',
        "children:" + plugin_chain('(at?et.replace("lmstudio/",""):et)', with_short=True),
    ),
    # 旧版新值里带着自身搜索串，重跑会不断叠加；先把多出来的链收回括号内。
    (
        "title:(" + _TITLE_CHAIN + ")" + _TITLE_REST + _TITLE_REST,
        "title:(" + _TITLE_CHAIN + ")",
    ),
    (
        "title:" + _TITLE_CHAIN + _TITLE_REST + _TITLE_REST,
        "title:(" + _TITLE_CHAIN + ")",
    ),
    (
        "title:`${e.owner}/${e.name}`",
        "title:(" + _TITLE_CHAIN + ")",
    ),
    (
        '"text-foreground opacity-50")}),(0,n.jsx)("span",{className:(0,s.cn)("min-w-0 flex-1 truncate",!0===r?"text-lm-indigo-foreground":"text-foreground"),children:t.identifier})',
        '"text-foreground opacity-50")}),(0,n.jsx)("span",{className:(0,s.cn)("min-w-0 flex-1 truncate",!0===r?"text-lm-indigo-foreground":"text-foreground"),children:'
        + plugin_chain("t.identifier")
        + "})",
    ),
    (
        'children:(0,n.jsx)("span",{className:"font-mono text-xs",children:t.identifier})',
        'children:(0,n.jsx)("span",{className:"font-mono text-xs",children:'
        + plugin_chain("t.identifier")
        + "})",
    ),
    (
        'children:e?.name??"Plugin"',
        "children:" + plugin_chain('(e?.name??"Plugin")', with_short=True),
    ),
    # 插件配置字段：名称、说明与选项由插件运行时提供，只能在通用配置行渲染时映射。
    (
        'R=d??t.typeParam.displayName?.replace("Enable Thinking","启用思考")'
        '.replace("Physical\\u0020Batch Size","物理批大小")'
        '.replace("Context\\u0020Checkpoints","上下文检查点")??S(',
        "R=d??("
        + text_chain(
            't.typeParam.displayName?.replace("Enable Thinking","启用思考")'
            '.replace("Physical\\u0020Batch Size","物理批大小")'
            '.replace("Context\\u0020Checkpoints","上下文检查点")',
            PLUGIN_FIELD_ZH,
        )
        + ")??S(",
    ),
    (
        'D=t.typeParam.subtitle?.replace("Controls thinking for chat templates that support enable_thinking.","控制支持 enable_thinking 的对话模板是否先思考。"),',
        "D=("
        + text_chain(
            't.typeParam.subtitle?.replace("Controls thinking for chat templates that support enable_thinking.","控制支持 enable_thinking 的对话模板是否先思考。")',
            PLUGIN_FIELD_ZH,
        )
        + "),",
    ),
    (
        'return"object"==typeof a?a.displayName:a',
        'return"object"==typeof a?'
        + text_chain('(a.displayName??"")', PLUGIN_FIELD_ZH)
        + ':"string"==typeof a?'
        + text_chain("a", PLUGIN_FIELD_ZH)
        + ":a",
    ),
    (
        'const e="string"==typeof t,a=e?t:t.value,i=e?t:t.displayName;',
        'const e="string"==typeof t,a=e?t:t.value,i=e?'
        + text_chain("t", PLUGIN_FIELD_ZH)
        + ":"
        + text_chain('(t.displayName??"")', PLUGIN_FIELD_ZH)
        + ";",
    ),
    (
        '(0,n.jsx)(l.LuHammer,{}),"Tools"]',
        '(0,n.jsx)(l.LuHammer,{}),"工具"]',
    ),
    (
        'children:["Allow all ",(0,n.jsx)(o.FiX,{})]',
        'children:["全部允许 ",(0,n.jsx)(o.FiX,{})]',
    ),
    (
        'label:a.function.description,hide:void 0===a.function.description',
        "label:"
        + text_chain('(a.function.description??"")', PLUGIN_TOOL_DESC_ZH)
        + ",hide:void 0===a.function.description",
    ),
    # 旧包里工具说明链已生成；把代码解释器的多行说明插到链首（新包整链已含它，不会命中）。
    (
        'label:(a.function.description??"").replace("%s","%s")' % (_FIRST_TOOL_EN, _FIRST_TOOL_ZH),
        'label:(a.function.description??"").replace("%s","%s").replace("%s","%s")'
        % (_RUN_JS_EN, _RUN_JS_ZH, _FIRST_TOOL_EN, _FIRST_TOOL_ZH),
    ),
    # 筛选框把中文别名并进搜索串，英文标识符仍可按原样搜索。
    (
        "L.filter((t=>t.identifier.toLowerCase().includes(b.toLowerCase())))",
        'L.filter((t=>(t.identifier+" "+'
        + plugin_alias_expr("t.identifier")
        + ").toLowerCase().includes(b.toLowerCase())))",
    ),
    (
        "f.filter((t=>t.identifier.toLowerCase().includes(v.toLowerCase())))",
        'f.filter((t=>(t.identifier+" "+'
        + plugin_alias_expr("t.identifier")
        + ").toLowerCase().includes(v.toLowerCase())))",
    ),
    # 新插件：包里已存在旧四组映射链，以下条目把链原位扩展到七组。
    (
        "R=d??(" + _FIELD_R_V1 + ")??S(",
        "R=d??(" + _FIELD_R_NEW + ")??S(",
    ),
    (
        "D=(" + _FIELD_D_V1 + "),j=_||(",
        "D=(" + _FIELD_D_NEW + "),j=_||(",
    ),
    (
        'return"object"==typeof a?' + _DN_V1 + ':"string"==typeof a?' + _A_V1 + ':a})(l)',
        'return"object"==typeof a?' + _DN_NEW + ':"string"==typeof a?' + _A_NEW + ':a})(l)',
    ),
    (
        'const e="string"==typeof t,a=e?t:t.value,i=e?' + _T_V1 + ':' + _TDN_V1
        + ';return(0,n.jsx)(r.SelectItem,',
        'const e="string"==typeof t,a=e?t:t.value,i=e?' + _T_NEW + ':' + _TDN_NEW
        + ';return(0,n.jsx)(r.SelectItem,',
    ),
    (
        "label:" + _TOOL_CHAIN_V1 + ",hide:void 0===a.function.description",
        "label:" + _TOOL_CHAIN_NEW + ",hide:void 0===a.function.description",
    ),
    (
        "t.identifier" + _CHAIN_FULL_V1 + '}),!0===e?',
        "t.identifier" + _CHAIN_FULL_NEW + '}),!0===e?',
    ),
    (
        "t.identifier" + _CHAIN_FULL_V1 + '})})})})},t.identifier)',
        "t.identifier" + _CHAIN_FULL_NEW + '})})})})},t.identifier)',
    ),
    (
        '(e?.name??"Plugin")' + _CHAIN_BOTH_V1
        + '}),(0,r.jsx)("span",{className:"flex-none",children:" README"})',
        '(e?.name??"Plugin")' + _CHAIN_BOTH_NEW
        + '}),(0,r.jsx)("span",{className:"flex-none",children:" README"})',
    ),
    (
        "title:(" + _TITLE_PREFIX + _CHAIN_FULL_V1 + "),Icon:l.LuBot",
        "title:(" + _TITLE_PREFIX + _CHAIN_FULL_NEW + "),Icon:l.LuBot",
    ),
    (
        '(at?et.replace("lmstudio/",""):et)' + _CHAIN_BOTH_V1
        + '}),(0,n.jsx)(_.PluginListingBadges',
        '(at?et.replace("lmstudio/",""):et)' + _CHAIN_BOTH_NEW
        + '}),(0,n.jsx)(_.PluginListingBadges',
    ),
    (
        'L.filter((t=>(t.identifier+" "+' + _ALIAS_V1 + ').toLowerCase().includes(b.toLowerCase())))',
        'L.filter((t=>(t.identifier+" "+' + _ALIAS_NEW + ').toLowerCase().includes(b.toLowerCase())))',
    ),
    (
        'f.filter((t=>(t.identifier+" "+' + _ALIAS_V1 + ').toLowerCase().includes(v.toLowerCase())))',
        'f.filter((t=>(t.identifier+" "+' + _ALIAS_NEW + ').toLowerCase().includes(v.toLowerCase())))',
    ),
    # 聊天输入框的插件胶囊：取 manifest 的 owner/name，走独立的三元映射。
    (
        'return"context-compactor"===u.name?"上下文压缩":"memory"===u.name?"长期记忆":u.name',
        'return"context-compactor"===u.name?"上下文压缩":"memory"===u.name?"长期记忆"'
        ':"big-rag"===u.name?"知识库检索":"web-search"===u.name?"联网搜索"'
        ':"skills"===u.name?"技能系统":u.name',
    ),
]


LAYOUT = [
    (
        '"p",{className:"flex items-center gap-1.5 text-[15px] font-medium whitespace-nowrap",children:',
        '"p",{className:"flex items-center gap-1.5 text-[15px] font-medium",style:{whiteSpace:"nowrap"},children:',
    ),
    (
        '"p",{className:"flex items-center gap-1.5 text-[15px] font-medium",children:',
        '"p",{className:"flex items-center gap-1.5 text-[15px] font-medium",style:{whiteSpace:"nowrap"},children:',
    ),
]


def js_unescape(s):
    out = []
    i = 0
    mapping = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v", "0": "\0"}
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s):
            nxt = s[i + 1]
            if nxt in mapping:
                out.append(mapping[nxt])
                i += 2
                continue
            if nxt == "u" and i + 6 <= len(s):
                try:
                    out.append(chr(int(s[i + 2:i + 6], 16)))
                    i += 6
                    continue
                except ValueError:
                    pass
            out.append(nxt)
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def validate_embedded_json(content):
    """内嵌 JSON.parse('{...}') 字符串必须仍可解析，避免值里带转义引号时被截断。"""
    errors = []
    token = "JSON.parse("
    idx = 0
    while True:
        i = content.find(token, idx)
        if i < 0:
            break
        q = i + len(token)
        while q < len(content) and content[q] in " \t\r\n":
            q += 1
        if q >= len(content) or content[q] not in "'\"":
            idx = i + len(token)
            continue
        quote = content[q]
        j = q + 1
        while j < len(content):
            if content[j] == "\\":
                j += 2
                continue
            if content[j] == quote:
                break
            j += 1
        raw = content[q + 1:j]
        decoded = js_unescape(raw)
        if decoded[:1] in "{[":
            try:
                json.loads(decoded)
            except Exception as e:
                errors.append((i, str(e)))
        idx = j + 1
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=os.path.dirname(os.path.abspath(__file__)))
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    js = os.path.join(args.path, "resources", "app", ".webpack", "renderer", "main_window.js")
    if not os.path.exists(js):
        print("错误: 未找到", js)
        return 1

    with open(os.path.join(here, "T_extra.json"), "r", encoding="utf-8") as f:
        extra = json.load(f)
    with open(js, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    pattern = re.compile("(" + "|".join(re.escape(a) for a in ATTRS) + '):"([^"]+)"')
    attr_count = 0

    def repl(m):
        nonlocal attr_count
        en = m.group(2)
        if en not in extra:
            return m.group(0)
        attr_count += 1
        return m.group(1) + ':"' + extra[en] + '"'

    content = pattern.sub(repl, content)

    plain_count = 0
    for en, zh in PLAIN.items():
        old = '"' + en + '"'
        new = '"' + zh + '"'
        c = content.count(old)
        if c:
            content = content.replace(old, new)
            plain_count += c

    migrate_count = 0
    for old, new in MIGRATE.items():
        c = content.count(old)
        if c:
            content = content.replace(old, new)
            migrate_count += c

    i18n_count = 0
    for key, zh in I18N.items():
        quoted_key = '"' + key + '"'
        pattern_i18n = re.compile(re.escape(quoted_key) + r':"((?:[^"\\]|\\.)*)"')

        def repl_i18n(m, zh=zh, quoted_key=quoted_key):
            nonlocal i18n_count
            i18n_count += 1
            return quoted_key + ':"' + zh + '"'

        content = pattern_i18n.sub(repl_i18n, content)

    render_count = 0
    for old, new in RENDER:
        c = content.count(old)
        if c:
            content = content.replace(old, new)
            render_count += c

    layout_count = 0
    for old, new in LAYOUT:
        c = content.count(old)
        if c:
            content = content.replace(old, new)
            layout_count += c

    errors = validate_embedded_json(content)
    if errors:
        print("错误: 补丁会破坏内嵌 JSON，已中止写入（界面文件未改动）")
        for pos, msg in errors[:5]:
            print(f"  @{pos}: {msg}")
        return 1

    with open(js, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"增强补丁完成: 属性替换 {attr_count} 处, 纯文本替换 {plain_count} 处, 译名迁移 {migrate_count} 处, 词典条目 {i18n_count} 处, 渲染映射 {render_count} 处, 布局修正 {layout_count} 处")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
