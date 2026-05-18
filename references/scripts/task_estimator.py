#!/usr/bin/env python3
"""任务工时预测器 — 从 TASK.md 任务列表估算完成时间置信区间

输入 JSON 格式（从 TASK.md 任务列表解析）：
[
  {"id": "T01", "estimate_hours": 2, "parallel": true, "depends_on": []},
  {"id": "T02", "estimate_hours": 4, "parallel": false, "depends_on": ["T01"]},
  ...
]

蒙特卡洛模拟给出概率分布。

用法：
    echo '[{"id":"T01","estimate_hours":2}]' | python3 task_estimator.py
    python3 task_estimator.py tasks.json
    python3 task_estimator.py tasks.json --format json
"""

import argparse
import json
import random
import sys
from collections import defaultdict


MIN_FACTOR = 0.7
MAX_FACTOR = 1.5
ITERATIONS = 5000
CONFIDENCE_LEVELS = [0.50, 0.70, 0.85, 0.95]


def build_dependency_graph(tasks):
    """构建依赖图，检测循环依赖和无效引用。"""
    graph = defaultdict(list)
    task_map = {t["id"]: t for t in tasks}
    all_ids = set(task_map.keys())
    for t in tasks:
        for dep in t.get("depends_on", []):
            if dep not in all_ids:
                print(f"警告：任务 {t['id']} 依赖不存在的 {dep}，已跳过", file=sys.stderr)
                continue
            graph[t["id"]].append(dep)

    visited, on_stack = set(), set()
    def has_cycle(tid):
        if tid in on_stack:
            return True
        if tid in visited:
            return False
        visited.add(tid)
        on_stack.add(tid)
        for dep in graph.get(tid, []):
            if has_cycle(dep):
                return True
        on_stack.remove(tid)
        return False

    for tid in task_map:
        if has_cycle(tid):
            print(f"错误：检测到循环依赖（涉及 {tid}），模拟终止", file=sys.stderr)
            sys.exit(1)

    return graph, task_map


def calc_critical_path(tasks, graph, task_map, samples):
    """用给定的样本计算关键路径长度（考虑并行）。"""
    completed = {}

    def finish_time(tid):
        if tid in completed:
            return completed[tid]
        t = task_map[tid]
        est = t.get("estimate_hours", 4)
        actual = est * samples.get(tid, 1.0)
        dep_times = [finish_time(d) for d in graph.get(tid, [])]
        start = max(dep_times) if dep_times else 0
        completed[tid] = start + actual
        return completed[tid]

    return max(finish_time(t["id"]) for t in tasks) if tasks else 0


def simulate(tasks):
    """蒙特卡洛模拟，返回各置信水平的工时预测。"""
    graph, task_map = build_dependency_graph(tasks)

    results = []
    for _ in range(ITERATIONS):
        samples = {
            t["id"]: random.uniform(MIN_FACTOR, MAX_FACTOR)
            for t in tasks
        }
        total = calc_critical_path(tasks, graph, task_map, samples)
        results.append(total)

    results.sort()

    estimates = {}
    for conf in CONFIDENCE_LEVELS:
        idx = min(int(conf * len(results)), len(results) - 1)
        estimates[f"{int(conf * 100)}%"] = round(results[idx], 1)

    return {
        "task_count": len(tasks),
        "parallel_groups": sum(1 for t in tasks if t.get("parallel")),
        "total_estimated": sum(t.get("estimate_hours", 4) for t in tasks),
        "confidence": estimates,
        "median": round(results[len(results) // 2], 1),
    }


def format_markdown(report):
    lines = ["## 工时预测\n"]
    lines.append(f"任务数：{report['task_count']}，可并行：{report['parallel_groups']}，")
    lines.append(f"原始估算总和：{report['total_estimated']}h\n")
    lines.append("| 置信度 | 预计工时 |")
    lines.append("|--------|---------|")
    for level, hours in report["confidence"].items():
        lines.append(f"| {level} | {hours}h |")
    lines.append(f"\n中位数：{report['median']}h")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="任务工时预测器")
    parser.add_argument("input", nargs="?", help="JSON 文件路径，省略则读 stdin")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    source = open(args.input, encoding="utf-8") if args.input else sys.stdin
    try:
        tasks = json.load(source)
    except json.JSONDecodeError as e:
        print(f"错误：输入不是合法 JSON — {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if args.input:
            source.close()

    report = simulate(tasks)

    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(report))


if __name__ == "__main__":
    main()
