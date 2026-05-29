"""flow-go 脚本共享工具函数

消除各脚本中重复的文件读取、JSONL 解析、原子写入、评分等级计算等模式。
所有脚本仅使用 Python 标准库。
"""
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ── 阶段常量 ──────────────────────────────────────────────

STAGE_NAMES: Dict[int, str] = {
    0: "需求",
    1: "设计",
    2: "任务",
    3: "开发",
    4: "测试",
    5: "审查",
    6: "部署",
    7: "验收",
}

STAGE_ROLES: Dict[int, str] = {
    0: "产品经理",
    1: "技术经理",
    2: "项目经理",
    3: "开发员",
    4: "测试员",
    5: "技术经理",
    6: "运维",
    7: "产品经理+项目经理",
}

STAGE_FILES: Dict[int, str] = {
    0: "0-requirement.md",
    1: "1-design.md",
    2: "2-task.md",
    3: "3-develop.md",
    4: "4-test.md",
    5: "5-review.md",
    6: "6-deploy.md",
    7: "7-acceptance.md",
}


# ── 文件 I/O 工具 ────────────────────────────────────────

def safe_read_file(path, encoding="utf-8"):
    """安全读取文件内容，失败返回空字符串

    统一替代各脚本中重复的 try/except 文件读取模式。

    Args:
        path: 文件路径（str 或 Path）
        encoding: 文件编码，默认 utf-8

    Returns:
        str: 文件内容，失败时返回空字符串
    """
    try:
        return Path(path).read_text(encoding=encoding)
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return ""


def read_jsonl(path, encoding="utf-8"):
    """读取 JSONL 文件，返回解析后的字典列表

    自动跳过空行和解析失败的行。

    Args:
        path: JSONL 文件路径
        encoding: 文件编码

    Returns:
        list[dict]: 解析成功的记录列表
    """
    try:
        with open(path, encoding=encoding) as f:
            lines = [l.strip() for l in f if l.strip()]
    except (FileNotFoundError, OSError):
        return []

    records = []
    for line in lines:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def read_last_jsonl(path, encoding="utf-8"):
    """读取 JSONL 文件最后一条记录

    从文件末尾开始倒序读取，返回第一条成功解析的记录。
    适用于 health-history.jsonl、traces.jsonl 等追加写入的场景。

    Args:
        path: JSONL 文件路径
        encoding: 文件编码

    Returns:
        dict or None: 最后一条记录，无记录时返回 None
    """
    try:
        with open(path, encoding=encoding) as f:
            lines = [l.strip() for l in f if l.strip()]
    except (FileNotFoundError, OSError):
        return None

    for line in reversed(lines):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    return None


def atomic_write(path, content, encoding="utf-8"):
    """原子写入文件：先写临时文件再 rename，防止写入中断导致文件损坏

    Args:
        path: 目标文件路径
        content: 要写入的内容
        encoding: 文件编码
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    # 在同一目录创建临时文件，确保同文件系统 rename 是原子操作
    fd, tmp_path = tempfile.mkstemp(
        suffix=".tmp",
        prefix=target.stem + "_",
        dir=str(target.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(content)
        os.replace(tmp_path, str(target))
    except BaseException:
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ── 评分工具 ──────────────────────────────────────────────

def grade_for_score(composite):
    """将数值评分映射为字母等级

    评分 → 等级映射：
      >= 85 → A
      >= 70 → B
      >= 55 → C
      <  55 → D

    Args:
        composite: 数值评分（0-100）

    Returns:
        str: 字母等级（A/B/C/D）
    """
    if composite >= 85:
        return "A"
    elif composite >= 70:
        return "B"
    elif composite >= 55:
        return "C"
    else:
        return "D"


def rag_for_scores(composite, min_score):
    """根据综合评分和最低维度评分判定 RAG 状态

    Args:
        composite: 综合评分
        min_score: 最低维度评分

    Returns:
        str: RAG 状态（Green/Amber/Red）
    """
    if composite >= 80 and min_score >= 60:
        return "Green"
    elif composite >= 60 and min_score >= 40:
        return "Amber"
    else:
        return "Red"
