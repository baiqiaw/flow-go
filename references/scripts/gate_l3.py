#!/usr/bin/env python3
"""L3 跨 Change 回归检查 — 比对 traces.jsonl 最近记录的 gate_blocks 维度变化

L3 由 --enable-l3 参数显式触发。本模块读取 traces.jsonl 最后 3 条记录，
比对 gate_blocks 字段，检测是否有新的阻断维度（即之前为 0 但现在 > 0 的阶段）。

ADR-003：JSON 解析失败时返回 passed=true + detail，不阻断流程。

用法（编程接口）：
  from gate_l3 import check
  result = check(specs_dir, traces_path)
"""

import json
from pathlib import Path


def check(specs_dir, traces_path):
    """L3 跨 Change 回归检查

    参数：
        specs_dir: .specs/<change-id> 目录路径（暂未使用，预留扩展）
        traces_path: traces.jsonl 文件路径

    返回：
        dict: {"passed": bool, "detail": str, "new_blocks": list}
    """
    # traces.jsonl 不存在 → 跳过
    traces_file = Path(traces_path)
    if not traces_file.is_file():
        return {
            "passed": True,
            "detail": "traces.jsonl 不存在，跳过 L3",
            "new_blocks": [],
        }

    # 读取全部行，取最后 3 条
    try:
        raw_lines = traces_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {
            "passed": True,
            "detail": "traces.jsonl 读取失败，跳过 L3",
            "new_blocks": [],
        }

    non_empty = [line.strip() for line in raw_lines if line.strip()]
    if len(non_empty) < 2:
        return {
            "passed": True,
            "detail": f"traces.jsonl 仅 {len(non_empty)} 条记录，无需跨 Change 比对",
            "new_blocks": [],
        }

    last_3 = non_empty[-3:]

    # 解析记录
    records = []
    for line in last_3:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            return {
                "passed": True,
                "detail": "trace 解析失败，跳过 L3",
                "new_blocks": [],
            }

    # 比对 gate_blocks：检测最新记录相比之前是否有新的阻断维度
    current = records[-1]
    current_blocks = current.get("gate_blocks", {})

    # 合并所有历史（排除最新）的 gate_blocks，取各阶段的最大值作为基线
    historical_max = {}
    for record in records[:-1]:
        for stage, count in record.get("gate_blocks", {}).items():
            prev = historical_max.get(stage, 0)
            if count > prev:
                historical_max[stage] = count

    # 检测新阻断：当前 > 0 但历史 max == 0（新出现的维度）
    # 或当前 > 历史 max（阻断加剧）
    new_blocks = []
    for stage, count in current_blocks.items():
        if count > 0 and historical_max.get(stage, 0) == 0:
            new_blocks.append(stage)
        elif count > historical_max.get(stage, 0):
            new_blocks.append(f"{stage}(加剧)")

    if new_blocks:
        return {
            "passed": False,
            "detail": f"检测到 {len(new_blocks)} 个新/加剧阻断维度: {', '.join(sorted(new_blocks))}",
            "new_blocks": new_blocks,
        }

    return {
        "passed": True,
        "detail": "跨 Change 回归检查通过，无新阻断维度",
        "new_blocks": [],
    }
