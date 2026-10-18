#!/usr/bin/env python3
"""ComfyUI MCP Server 简体中文补丁（LM Studio 用）

把 joenorton/comfyui-mcp-server 的工具说明与参数说明汉化，并修复
*.meta.json 被误当作工作流解析导致启动崩溃的问题。

用法（py -3 或任意 Python 3.10+）：
    patch_comfyui_mcp_cn.py --dir <comfyui-mcp-server 目录>
    patch_comfyui_mcp_cn.py --dir <...> --check
    patch_comfyui_mcp_cn.py --dir <...> --restore

特性：
- 首次修改前把原文件备份为 *.zh-cn-orig
- 幂等：重复运行不会叠加修改
- 修改后做 Python 编译检查，失败自动回滚
"""

import argparse
import ast
import re
import shutil
import sys
from pathlib import Path

MARKER = ".zh-cn-applied"


DOCSTRINGS = {
    "tools/asset.py": {
        "view_image": """查看已生成图片的缩略图（仅支持图片）。

用于闭环迭代：生成 → 查看 → 调整 → 重新生成。
支持 PNG / JPEG / WebP / GIF；音视频请直接使用 asset_url。

参数：
    asset_id：生成工具返回的资产 ID
    mode："thumb" 返回缩略图（默认），"metadata" 只返回信息
    max_dim：最大边长像素（默认 512）
    max_b64_chars：base64 最大字符数（默认 100000，约 100KB）""",
    },
    "tools/job.py": {
        "get_queue_status": """获取 ComfyUI 当前队列状态。

返回正在运行和排队中的任务，包括运行中的 prompt、等待中的 prompt 和队列位置。
用于在轮询前判断任务是否仍在运行。""",
        "get_job": """查询指定 prompt ID 的任务状态与历史。

参数：
    prompt_id：提交工作流时返回的 prompt ID
    wait_seconds：任务仍在运行/排队时最多等待的秒数（默认 20，上限 40）

返回 status（completed / running / queued / processing / error / not_found）、
outputs、error、history 和说明文字。completed 时包含 asset_id，可直接用于 view_image。""",
        "list_assets": """列出本次会话最近生成的资产，便于模型记忆和继续迭代。

参数：
    limit：最多返回数量（默认 10）
    workflow_id：按工作流过滤
    session_id：按会话过滤""",
        "get_asset_metadata": """获取某个生成资产的完整元数据与来源信息。

包含尺寸、大小、类型、工作流、提示词、ComfyUI 历史快照和原始工作流。

参数：
    asset_id：生成工具或 list_assets 返回的资产 ID""",
        "cancel_job": """取消排队中或正在运行的任务。

参数：
    prompt_id：要取消的 prompt ID""",
    },
    "tools/configuration.py": {
        "list_models": """列出 ComfyUI 中可用的 checkpoint 模型。

本机使用 GGUF 版 Z-Image Turbo，列表可能为空；这不影响文生图/图生图工具。""",
        "get_defaults": """查看当前生效的图片 / 音频 / 视频默认参数。

优先级：运行时 > 配置文件 > 环境变量 > 内置默认值。""",
        "set_defaults": """设置图片 / 音频 / 视频的运行时默认参数。

参数：
    image / audio / video：参数字典
    persist：是否写入配置文件（~/.config/comfy-mcp/config.json）""",
    },
    "tools/workflow.py": {
        "list_workflows": """列出工作流目录中的全部工作流。

返回 ID、名称、说明、可调参数和可选元数据。""",
        "run_workflow": """运行一个已保存的 ComfyUI 工作流，并可覆盖参数。

参数：
    workflow_id：工作流 ID（文件名去掉 .json）
    overrides：参数覆盖，例如 {"prompt": "一只猫", "width": 1024}
    return_inline_preview：是否在结果中附带 256px 缩略图""",
    },
    "tools/publish.py": {
        "get_publish_info": """查看发布到网页目录的配置与状态。

包含项目根目录、发布目录、ComfyUI 输出目录是否可识别，以及缺失的配置项。""",
        "set_comfyui_output_root": """设置 ComfyUI 输出目录并持久保存（适合桌面版等非标准安装）。

参数：
    path：ComfyUI output 目录的绝对路径""",
        "publish_asset": """把本次会话生成的资产发布到网页项目目录。

参数：
    asset_id：资产 ID
    target_filename：演示模式下的固定文件名
    manifest_key：库模式下的清单键
    web_optimize：是否转成 WebP 并压缩到大小上限""",
    },
    "tools/generation.py": {
        "regenerate": """用新的参数重新生成已有资产。

参数：
    asset_id：要重做的资产 ID
    seed：新种子（None 随机，-1 沿用原种子）
    param_overrides：覆盖参数，例如 {"prompt": "新提示词", "denoise": 0.6}
    return_inline_preview：是否附带缩略图""",
    },
}


PLACEHOLDER_BLOCK = '''PLACEHOLDER_DESCRIPTIONS = {
    "prompt": "主提示词，决定画面内容。",
    "seed": "随机种子；不填或填 -1 时随机。",
    "width": "图片宽度（像素），默认 1024，需为 16 的倍数。",
    "height": "图片高度（像素），默认 1024，需为 16 的倍数。",
    "image": "输入图片文件名（须已存在于 ComfyUI 的 input 目录）。",
    "model": "模型文件名。",
    "steps": "采样步数；越高越慢。",
    "cfg": "提示词引导强度。",
    "sampler_name": "采样器名称。",
    "scheduler": "调度器名称。",
    "denoise": "去噪强度 0–1；图生图 0.35–0.55 保脸，0.6–0.75 改妆造，0.8 以上重画。",
    "negative_prompt": "负向提示词。",
    "tags": "音频描述标签，逗号分隔。",
    "lyrics": "歌词全文。",
    "seconds": "音频时长（秒）。",
    "lyrics_strength": "歌词影响强度 0–1。",
    "duration": "视频时长（秒）。",
    "fps": "视频帧率。",
}
'''


REPLACEMENTS = {
    "managers/workflow_manager.py": [
        (
            '''        for workflow_path in sorted(self.workflows_dir.glob("*.json")):
            try:''',
            '''        for workflow_path in sorted(self.workflows_dir.glob("*.json")):
            if workflow_path.name.endswith(".meta.json"):
                continue
            try:''',
        ),
        (
            '''            tool_name = self._dedupe_tool_name(self._derive_tool_name(workflow_path.stem))
            definition = WorkflowToolDefinition(
                workflow_id=workflow_path.stem,
                tool_name=tool_name,
                description=self._derive_description(workflow_path.stem),''',
            '''            tool_name = self._dedupe_tool_name(self._derive_tool_name(workflow_path.stem))
            metadata = self._load_workflow_metadata(workflow_path)
            definition = WorkflowToolDefinition(
                workflow_id=workflow_path.stem,
                tool_name=tool_name,
                description=metadata.get("description") or self._derive_description(workflow_path.stem),''',
        ),
        (
            '''        return f"Execute the '{readable}' ComfyUI workflow."''',
            '''        return f"执行 ComfyUI 工作流「{readable}」。"''',
        ),
        (
            '''            coerced_value = self._coerce_value(raw_value, param.annotation)
            for node_id, input_name in param.bindings:''',
            '''            coerced_value = self._coerce_value(raw_value, param.annotation)
            if param.name == "seed" and param.annotation is int and coerced_value < 0:
                # LM Studio 等客户端常用 -1 表示随机；ComfyUI 的 seed 下限是 0
                coerced_value = random.randint(0, 2**32 - 1)
            for node_id, input_name in param.bindings:''',
        ),
        (
            '"seed": "随机种子；不填则每次随机。"',
            '"seed": "随机种子；不填或填 -1 时随机。"',
        ),
        (
            '''                raise ValueError(f"Missing required parameter '{param.name}'")''',
            '''                raise ValueError(f"缺少必填参数「{param.name}」")''',
        ),
        (
            '''            raise ValueError(f"Cannot convert {value!r} to {annotation.__name__}: {e}")''',
            '''            raise ValueError(f"无法把 {value!r} 转换为 {annotation.__name__}：{e}")''',
        ),
    ],
    "tools/workflow.py": [
        (
            '''            return {"error": f"Workflow '{workflow_id}' not found"}''',
            '''            return {"error": f"工作流「{workflow_id}」不存在"}''',
        ),
    ],
    "tools/asset.py": [
        (
            '''            return {"error": f"Asset {asset_id} not found (registry is in-memory and resets on restart). Generate a new asset to regenerate."}''',
            '''            return {"error": f"资产 {asset_id} 不存在（资产表保存在内存中，服务重启后会清空）。请先生成新图片再重做。"}''',
        ),
    ],
    "comfyui_client.py": [
        (
            '''    def run_custom_workflow(self, workflow: Dict[str, Any], preferred_output_keys: Sequence[str] | None = None, max_attempts: int = 30):''',
            '''    def run_custom_workflow(self, workflow: Dict[str, Any], preferred_output_keys: Sequence[str] | None = None, max_attempts: int | None = None):
        if max_attempts is None:
            # LM Studio 的 MCP 客户端在 60 秒时硬超时，服务端必须先返回任务句柄。
            max_attempts = int(os.environ.get("COMFY_MCP_WAIT_SECONDS", "45"))''',
        ),
        (
            '''    def run_custom_workflow(self, workflow: Dict[str, Any], preferred_output_keys: Sequence[str] | None = None, max_attempts: int = 300):''',
            '''    def run_custom_workflow(self, workflow: Dict[str, Any], preferred_output_keys: Sequence[str] | None = None, max_attempts: int | None = None):
        if max_attempts is None:
            # LM Studio 的 MCP 客户端在 60 秒时硬超时，服务端必须先返回任务句柄。
            max_attempts = int(os.environ.get("COMFY_MCP_WAIT_SECONDS", "45"))''',
        ),
        (
            '''        if outputs is None:
            return {
                "status": "running",
                "prompt_id": prompt_id,
                "message": (
                    f"Workflow still running after {max_attempts}s. "
                    f"Use get_job(prompt_id='{prompt_id}') to poll for completion."
                ),
            }''',
            '''        if outputs is None:
            return {
                "status": "running",
                "prompt_id": prompt_id,
                "message": (
                    f"任务已提交，但 {max_attempts} 秒内未完成；ComfyUI 仍在生成，不是失败。"
                    f"不要重新提交同一任务。请每隔 10–20 秒调用一次 "
                    f"get_job(prompt_id='{prompt_id}')，直到 status 为 completed，"
                    "再用返回的 asset_id 调用 view_image 显示图片。"
                ),
                "next_tool": "get_job",
                "next_args": {"prompt_id": prompt_id},
            }''',
        ),
        (
            '''        if outputs is None:
            return {
                "status": "running",
                "prompt_id": prompt_id,
                "message": (
                    f"工作流在 {max_attempts} 秒后仍未完成。"
                    f"请用 get_job(prompt_id='{prompt_id}') 轮询结果。"
                ),
            }''',
            '''        if outputs is None:
            return {
                "status": "running",
                "prompt_id": prompt_id,
                "message": (
                    f"任务已提交，但 {max_attempts} 秒内未完成；ComfyUI 仍在生成，不是失败。"
                    f"不要重新提交同一任务。请每隔 10–20 秒调用一次 "
                    f"get_job(prompt_id='{prompt_id}')，直到 status 为 completed，"
                    "再用返回的 asset_id 调用 view_image 显示图片。"
                ),
                "next_tool": "get_job",
                "next_args": {"prompt_id": prompt_id},
            }''',
        ),
    ],
    "tools/job.py": [
        (
            '''import logging
from typing import Any, Dict, List, Optional''',
            '''import logging
import time
from typing import Any, Dict, List, Optional''',
        ),
        (
            '''    def get_job(prompt_id: str) -> dict:''',
            '''    def get_job(prompt_id: str, wait_seconds: int = 20) -> dict:''',
        ),
        (
            '''        if not prompt_id or not prompt_id.strip():
            return {
                "status": "error",
                "error": "Invalid prompt_id: empty or None",
                "prompt_id": prompt_id
            }
        
        try:''',
            '''        if not prompt_id or not prompt_id.strip():
            return {
                "status": "error",
                "error": "Invalid prompt_id: empty or None",
                "prompt_id": prompt_id
            }

        deadline = time.time() + max(0, min(wait_seconds, 40))
        while True:
            try:
                queue_data = comfyui_client.get_queue()
                active = any(
                    isinstance(item, list) and len(item) > 1 and item[1] == prompt_id
                    for item in queue_data.get("queue_running", []) + queue_data.get("queue_pending", [])
                )
            except Exception:
                active = False
            if not active or time.time() >= deadline:
                break
            time.sleep(2)
        
        try:''',
        ),
        (
            '''from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("MCP_Server")''',
            '''from mcp.server.fastmcp import FastMCP

from tools.helpers import register_and_build_response

logger = logging.getLogger("MCP_Server")''',
        ),
        (
            '''                    # Check if completed with outputs
                    if "outputs" in prompt_data and prompt_data["outputs"]:
                        return {
                            "status": "completed",
                            "prompt_id": prompt_id,
                            "outputs": prompt_data["outputs"],
                            "history": prompt_data,
                            "message": "Job completed successfully"
                        }''',
            '''                    # Check if completed with outputs
                    if "outputs" in prompt_data and prompt_data["outputs"]:
                        outputs = prompt_data["outputs"]
                        response = {
                            "status": "completed",
                            "prompt_id": prompt_id,
                            "outputs": outputs,
                            "history": prompt_data,
                            "message": "任务已完成。请用返回的 asset_id 调用 view_image 显示图片。"
                        }
                        try:
                            preferred = ("images", "image", "gifs", "gif", "audio", "audios", "files")
                            asset_info = comfyui_client._extract_first_asset_info(outputs, preferred)
                            workflow = None
                            prompt_meta = prompt_data.get("prompt")
                            if isinstance(prompt_meta, list) and len(prompt_meta) > 2 and isinstance(prompt_meta[2], dict):
                                workflow = prompt_meta[2]
                            metadata = comfyui_client._get_asset_metadata(
                                asset_info["asset_url"], outputs, preferred, workflow
                            )
                            built = register_and_build_response(
                                {
                                    "asset_url": asset_info["asset_url"],
                                    "filename": asset_info["filename"],
                                    "subfolder": asset_info["subfolder"],
                                    "folder_type": asset_info["type"],
                                    "prompt_id": prompt_id,
                                    "asset_metadata": metadata,
                                    "comfy_history": prompt_data,
                                    "submitted_workflow": workflow,
                                },
                                "generate_image",
                                asset_registry,
                                tool_name="get_job",
                            )
                            response.update({
                                "asset_id": built["asset_id"],
                                "asset_url": built["asset_url"],
                                "filename": built["filename"],
                                "width": built["width"],
                                "height": built["height"],
                                "mime_type": built["mime_type"],
                            })
                        except Exception as asset_error:
                            logger.warning(f"Failed to register asset for {prompt_id}: {asset_error}")
                        return response''',
        ),
    ],
}


class PatchError(RuntimeError):
    pass


def _char_col(line: str, byte_col: int) -> int:
    """ast 的 col_offset 是 UTF-8 字节偏移，这里换算成字符偏移。"""
    return len(line.encode("utf-8")[:byte_col].decode("utf-8", errors="ignore"))


def replace_docstrings(source: str, mapping: dict, path: str) -> tuple[str, int]:
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    line_starts = [0]
    for line in lines:
        line_starts.append(line_starts[-1] + len(line))

    edits = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        text = mapping.get(node.name)
        if text is None or not node.body:
            continue
        first = node.body[0]
        if not (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            continue
        value = first.value
        start = line_starts[value.lineno - 1] + _char_col(
            lines[value.lineno - 1], value.col_offset
        )
        end = line_starts[value.end_lineno - 1] + _char_col(
            lines[value.end_lineno - 1], value.end_col_offset
        )
        indent = " " * _char_col(lines[value.lineno - 1], value.col_offset)
        body = text.strip("\n")
        new_literal = '"""' + body.replace("\n", "\n" + indent) + '"""'
        if source[start:end] != new_literal:
            edits.append((start, end, new_literal))

    for start, end, new_literal in sorted(edits, reverse=True):
        source = source[:start] + new_literal + source[end:]
    return source, len(edits)


def build_patched(root: Path, rel: str) -> tuple[Path, str, bool]:
    path = root / rel
    if not path.exists():
        raise PatchError(f"缺少文件：{path}")

    source = path.read_text(encoding="utf-8")
    changed = False

    if rel == "comfyui_client.py" and not re.search(r"(?m)^import os$", source):
        if "import requests\n" not in source:
            raise PatchError("comfyui_client.py 中找不到 import requests")
        source = source.replace("import requests\n", "import os\nimport requests\n", 1)
        changed = True

    if rel in DOCSTRINGS:
        source, count = replace_docstrings(source, DOCSTRINGS[rel], rel)
        changed = changed or count > 0

    if rel == "managers/workflow_manager.py":
        if '"prompt": "主提示词，决定画面内容。"' not in source:
            source, n = re.subn(
                r"PLACEHOLDER_DESCRIPTIONS = \{.*?\n\}\n",
                PLACEHOLDER_BLOCK,
                source,
                count=1,
                flags=re.S,
            )
            if n != 1:
                raise PatchError("未找到 PLACEHOLDER_DESCRIPTIONS 块")
            changed = True

    for old, new in REPLACEMENTS.get(rel, []):
        if old in source:
            source = source.replace(old, new, 1)
            changed = True
        elif new not in source:
            raise PatchError(f"{rel} 中找不到锚点，且也没有已汉化版本：\n{old[:120]}")

    return path, source, changed


def restore(root: Path) -> int:
    restored = 0
    for backup in root.rglob("*.zh-cn-orig"):
        target = backup.with_name(backup.name[: -len(".zh-cn-orig")])
        shutil.copyfile(backup, target)
        restored += 1
    marker = root / MARKER
    if marker.exists():
        marker.unlink()
    return restored


def main() -> int:
    parser = argparse.ArgumentParser(description="ComfyUI MCP Server 简体中文补丁")
    parser.add_argument("--dir", required=True, help="comfyui-mcp-server 目录")
    parser.add_argument("--restore", action="store_true", help="还原英文")
    parser.add_argument("--check", action="store_true", help="只检查是否已汉化")
    args = parser.parse_args()

    root = Path(args.dir).resolve()
    if not (root / "server.py").exists():
        print(f"错误：{root} 不像 comfyui-mcp-server 目录（找不到 server.py）")
        return 2

    if args.restore:
        count = restore(root)
        print(f"已还原 {count} 个文件。")
        return 0

    if args.check:
        marker = root / MARKER
        print("已汉化" if marker.exists() else "未汉化")
        return 0

    files = list(DOCSTRINGS) + [p for p in REPLACEMENTS if p not in DOCSTRINGS]
    staged = []
    try:
        for rel in files:
            path, source, changed = build_patched(root, rel)
            if changed:
                compile(source, str(path), "exec")
                staged.append((path, source))
    except (PatchError, SyntaxError) as exc:
        print(f"失败：{exc}")
        print("未写入任何修改。")
        return 1

    for path, source in staged:
        backup = path.with_name(path.name + ".zh-cn-orig")
        if not backup.exists():
            shutil.copyfile(path, backup)
        path.write_text(source, encoding="utf-8")

    (root / MARKER).write_text("ComfyUI MCP Server zh-CN patch\n", encoding="utf-8")
    if staged:
        print("已汉化文件：")
        for path, _ in staged:
            print("  -", path.relative_to(root))
    else:
        print("所有文件已是汉化版本，无需修改。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
