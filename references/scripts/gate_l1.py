#!/usr/bin/env python3
"""L1 快速门卫 — AC-4

三路 AND 检查：security × blast × structure
目标 < 5 秒返回（纯文件扫描 + git diff，无复杂计算）
"""
import os
import re

from gate_dimensions import DANGEROUS_PATTERNS
from gate_blast import check_blast_radius

# SKILL.md 关键章节标题（structure 检查用）
REQUIRED_SECTIONS = [
    "流程全景",
]


def _check_security(specs_dir):
    """扫描 specs 目录下 .md 文件中的危险模式"""
    warnings = []
    if not os.path.isdir(specs_dir):
        return {"passed": True, "warnings": [f"specs 目录不存在: {specs_dir}"]}

    for root, _dirs, files in os.walk(specs_dir):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(root, fname)
            try:
                content = open(fpath, encoding="utf-8").read()
            except OSError:
                continue
            for pattern in DANGEROUS_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    warnings.append(f"{fpath}: 匹配危险模式 {pattern}")

    return {"passed": len(warnings) == 0, "warnings": warnings}


def _check_structure(project_dir):
    """检查 SKILL.md 基本结构：文件存在 + 关键章节标题"""
    skill_path = os.path.join(project_dir, "SKILL.md")

    if not os.path.isfile(skill_path):
        return {"passed": False, "warnings": [f"SKILL.md 不存在: {skill_path}"]}

    try:
        content = open(skill_path, encoding="utf-8").read()
    except OSError as e:
        return {"passed": False, "warnings": [f"无法读取 SKILL.md: {e}"]}

    missing = [s for s in REQUIRED_SECTIONS if s not in content]
    if missing:
        return {"passed": False, "warnings": [f"SKILL.md 缺少章节: {missing}"]}

    return {"passed": True, "warnings": []}


def check(specs_dir, project_dir):
    """执行 L1 快速门卫检查

    Args:
        specs_dir: specs 目录路径（如 '.specs/skill-evolver-optimization'）
        project_dir: 项目根目录路径（如 '.'）

    Returns:
        dict: {passed: bool, dimensions: {security, blast, structure}}
    """
    security = _check_security(specs_dir)
    blast_result = check_blast_radius(project_dir)
    blast = {
        "passed": not blast_result["exceeded"],
        "file_count": blast_result["file_count"],
        "threshold": blast_result["threshold"],
        "exceeded": blast_result["exceeded"],
    }
    structure = _check_structure(project_dir)

    dims = {"security": security, "blast": blast, "structure": structure}
    passed = all(d["passed"] for d in dims.values())

    return {"passed": passed, "dimensions": dims}
