#!/usr/bin/env python3
"""LESSONS.md 信号写入器 — 将进化信号追加到 LESSONS.md

将 evolution_signal.py detect() 检测到的强信号以结构化表格行写入 LESSONS.md。
支持文件不存在时创建基础模板，原子写入保证数据安全。

用法：
    from lessons_writer import write
    result = write(signals_payload, lessons_path)
"""
import os
import tempfile
from pathlib import Path


# ── 基础模板 ──────────────────────────────────────────────

_BASE_TEMPLATE = """# LESSONS.md — 经验教训

> 本文件由 flow-go 进化信号检测自动维护，记录值得长期记住的经验教训。

## 待改进领域

| 归因标签 | 信号描述 | 改进建议 |
|---------|---------|---------|
"""

_SECTION_HEADER = "## 待改进领域"

_TABLE_HEADER = "| 归因标签 | 信号描述 | 改进建议 |"

_TABLE_DIVIDER = "|---------|---------|---------|"


def _ensure_section(content: str) -> str:
    """确保内容包含"待改进领域"章节，无则追加"""
    if _SECTION_HEADER in content:
        return content
    # 追加章节（含表格头）
    if not content.endswith("\n"):
        content += "\n"
    content += f"\n{_SECTION_HEADER}\n\n{_TABLE_HEADER}\n{_TABLE_DIVIDER}\n"
    return content


def _format_row(signal: dict) -> str:
    """将单个强信号格式化为表格行"""
    attr = signal.get("attribution", "")
    desc = signal.get("description", "")
    advice = signal.get("advice", "")
    # 转义表格中的竖线，防止破坏格式
    for ch in ("|",):
        attr = attr.replace(ch, "｜")
        desc = desc.replace(ch, "｜")
        advice = advice.replace(ch, "｜")
    return f"| {attr} | {desc} | {advice} |"


def _atomic_write(path: str, content: str):
    """原子写入：先写临时文件再 os.replace，防止写到一半崩溃"""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        suffix=".tmp",
        prefix="lessons_",
        dir=str(target.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, target)
    except BaseException:
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def write(signals_payload: dict, lessons_path: str) -> dict:
    """将强信号写入 LESSONS.md

    Args:
        signals_payload: evolution_signal.py detect() 的输出 JSON
        lessons_path: LESSONS.md 文件路径

    Returns:
        {"written": True, "count": N} 写入的信号数量
    """
    strong_signals = signals_payload.get("strong_signals", [])
    if not strong_signals:
        return {"written": False, "count": 0}

    # 第一层：文件不存在 → 创建基础模板
    p = Path(lessons_path)
    if p.is_file():
        content = p.read_text(encoding="utf-8")
        # 第二层：文件存在但无章节 → 追加章节标题
        content = _ensure_section(content)
    else:
        content = _BASE_TEMPLATE

    # 追加信号表格行
    rows = [_format_row(sig) for sig in strong_signals]
    # 确保表格最后一行后换行再追加
    if not content.endswith("\n"):
        content += "\n"
    content += "\n".join(rows) + "\n"

    _atomic_write(lessons_path, content)

    return {"written": True, "count": len(strong_signals)}
