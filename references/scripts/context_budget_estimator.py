#!/usr/bin/env python3
"""上下文预算估算器 — 分析 TASK.md，估算每个任务的上下文消耗并生成分组建议。

用法：python3 references/scripts/context_budget_estimator.py --task-file <TASK.md路径>
输出：JSON 格式，包含每个任务的预算级别和并行分组建议。
"""

import argparse
import json
import re
import sys
from pathlib import Path


def parse_tasks(task_content: str) -> list[dict]:
    """解析 TASK.md 中的 XML 任务块。"""
    tasks = []
    pattern = re.compile(
        r'<task\s+id="([^"]+)"[^>]*parallel="([^"]*)"[^>]*>'
        r'(.*?)</task>',
        re.DOTALL,
    )
    for m in pattern.finditer(task_content):
        task_block = m.group(3)
        task_id = m.group(1)
        parallel = m.group(2).lower() == "true"

        # 提取各字段
        def extract_field(block: str, tag: str) -> str:
            fm = re.search(rf"<{tag}>(.*?)</{tag}>", block, re.DOTALL)
            return fm.group(1).strip() if fm else ""

        read_files = extract_field(task_block, "read_files")
        action = extract_field(task_block, "action")
        depends_on = extract_field(task_block, "depends_on")
        existing_budget = extract_field(task_block, "context_budget")
        agent_hint = extract_field(task_block, "agent_hint")

        # 统计 read_files 中的文件模式数量
        file_patterns = [p.strip() for p in read_files.split(",") if p.strip()]
        file_count = len(file_patterns)

        # 统计 action 描述长度
        action_len = len(action)

        tasks.append({
            "id": task_id,
            "parallel": parallel,
            "read_file_count": file_count,
            "action_length": action_len,
            "depends_on": depends_on,
            "existing_budget": existing_budget,
            "agent_hint": agent_hint,
        })

    return tasks


def estimate_budget(task: dict) -> str:
    """估算单个任务的上下文预算级别。"""
    if task["existing_budget"] in ("small", "medium", "large"):
        return task["existing_budget"]

    fc = task["read_file_count"]
    al = task["action_length"]

    if fc <= 3 and al <= 50:
        return "small"
    elif fc <= 6 and al <= 100:
        return "medium"
    else:
        return "large"


def estimate_tokens(budget: str) -> int:
    """根据预算级别估算 token 数。"""
    return {"small": 1200, "medium": 3500, "large": 6000}.get(budget, 2000)


def generate_groups(tasks: list[dict]) -> list[dict]:
    """生成分组建议。"""
    groups = []
    parallel_small = []
    large_tasks = []

    for t in tasks:
        budget = t["budget"]
        if t["parallel"] and budget == "small" and not t["depends_on"]:
            parallel_small.append(t["id"])
        elif budget == "large":
            large_tasks.append(t["id"])

    if parallel_small:
        groups.append({
            "name": "并行组-A",
            "tasks": parallel_small,
            "strategy": "parallel_shared",
            "reason": f"均为 small，无互相依赖，共 {len(parallel_small)} 个任务",
        })

    for tid in large_tasks:
        groups.append({
            "name": f"独占组-{tid}",
            "tasks": [tid],
            "strategy": "exclusive",
            "reason": "large 任务独占上下文窗口",
        })

    return groups


def generate_warnings(tasks: list[dict]) -> list[str]:
    """生成警告信息。"""
    warnings = []
    for t in tasks:
        if t["budget"] == "large":
            warnings.append(f"{t['id']} 估算为 large，建议拆分为更小任务")
        if t["read_file_count"] > 8:
            warnings.append(f"{t['id']} 涉及 {t['read_file_count']} 个文件模式，可能超出上下文窗口")
    return warnings


def main():
    parser = argparse.ArgumentParser(description="上下文预算估算器")
    parser.add_argument(
        "--task-file", required=True, help="TASK.md 文件路径"
    )
    args = parser.parse_args()

    task_path = Path(args.task_file)
    if not task_path.exists():
        print(json.dumps({"error": f"文件不存在: {task_path}"}, ensure_ascii=False))
        sys.exit(1)

    content = task_path.read_text(encoding="utf-8")
    tasks = parse_tasks(content)

    if not tasks:
        print(json.dumps({"error": "未找到任务定义"}, ensure_ascii=False))
        sys.exit(1)

    # 估算预算
    for t in tasks:
        t["budget"] = estimate_budget(t)
        t["estimated_tokens"] = estimate_tokens(t["budget"])

    groups = generate_groups(tasks)
    warnings = generate_warnings(tasks)

    # 构建 agent_hint 映射
    hint_map = {}
    for g in groups:
        if g["strategy"] == "parallel_shared":
            for tid in g["tasks"]:
                hint_map[tid] = "可与其他 small 任务并行执行"
        elif g["strategy"] == "exclusive":
            for tid in g["tasks"]:
                hint_map[tid] = "独占执行"

    result = {
        "tasks": [
            {
                "id": t["id"],
                "budget": t["budget"],
                "read_file_count": t["read_file_count"],
                "estimated_tokens": t["estimated_tokens"],
                "agent_hint": t.get("agent_hint") or hint_map.get(t["id"], ""),
            }
            for t in tasks
        ],
        "groups": groups,
        "warnings": warnings,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
