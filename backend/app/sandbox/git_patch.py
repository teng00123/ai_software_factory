"""
Git Patch 工具

负责将生成的代码转为 unified diff 格式，以及应用 patch。
"""
import difflib
from typing import List
from dataclasses import dataclass


@dataclass
class FilePatch:
    """单个文件的 patch"""
    file_path: str
    original: str  # 原始内容（空字符串表示新文件）
    modified: str  # 修改后内容


def generate_patch(file_patches: List[FilePatch]) -> str:
    """
    生成 unified diff 格式的 patch

    Args:
        file_patches: 文件 patch 列表

    Returns:
        unified diff 字符串
    """
    patches = []

    for fp in file_patches:
        original_lines = fp.original.splitlines(keepends=True) if fp.original else []
        modified_lines = fp.modified.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{fp.file_path}",
            tofile=f"b/{fp.file_path}",
        )
        patches.append("".join(diff))

    return "\n".join(patches)


def generate_patch_from_artifacts(artifacts: list) -> str:
    """
    从 artifacts 列表生成 patch

    Args:
        artifacts: [{"file_path": "...", "content": "..."}]

    Returns:
        unified diff
    """
    file_patches = [
        FilePatch(
            file_path=art["file_path"],
            original="",
            modified=art["content"],
        )
        for art in artifacts
    ]
    return generate_patch(file_patches)
