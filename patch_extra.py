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
]
PLUGIN_ZH_SHORT = [
    ("context-compactor", "上下文压缩"),
    ("memory", "长期记忆"),
    ("js-code-sandbox", "代码解释器"),
    ("rag-v1", "与文件对话"),
]


def plugin_chain(expr, with_short=False):
    pairs = PLUGIN_ZH_FULL + (PLUGIN_ZH_SHORT if with_short else [])
    for en, zh in pairs:
        expr += '.replace("%s","%s")' % (en, zh)
    return expr


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


def text_chain(expr, pairs):
    for en, zh in pairs:
        expr += '.replace("%s","%s")' % (en, zh)
    return expr


def plugin_alias_expr(ident):
    return (
        '('
        + ident + '==="alexandreaxell/context-compactor"?"上下文压缩":'
        + ident + '==="esalesninja/memory"?"长期记忆":'
        + ident + '==="lmstudio/js-code-sandbox"?"代码解释器":'
        + ident + '==="lmstudio/rag-v1"?"与文件对话":""'
        + ')'
    )


_TITLE_PREFIX = "`${e.owner}/${e.name}`"
_TITLE_CHAIN = plugin_chain(_TITLE_PREFIX)
_TITLE_REST = _TITLE_CHAIN[len(_TITLE_PREFIX):]
_RUN_JS_EN, _RUN_JS_ZH = PLUGIN_TOOL_DESC_ZH[0]
_FIRST_TOOL_EN, _FIRST_TOOL_ZH = PLUGIN_TOOL_DESC_ZH[1]

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
