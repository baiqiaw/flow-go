#!/usr/bin/env python3
"""完成率预测器 — 基于历史 health-history.jsonl 预测任务完成趋势

用法：
    python3 completion_forecaster.py health-history.jsonl
    python3 completion_forecaster.py health-history.jsonl --format json
    python3 completion_forecaster.py health-history.jsonl --tasks 8  # 预测 8 个任务的完成情况

输入：health-history.jsonl（由 health_scorer.py 生成）

输出：
- 趋势分析（improving/stable/declining）
- 完成率预测（50%/70%/85%/95% 置信区间）
- 维度级改善建议
"""

import argparse
import json
import math
import sys


def load_history(path):
    records = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except FileNotFoundError:
        return []
    return records


def calc_stats(values):
    if not values:
        return {"mean": 0, "std": 0, "min": 0, "max": 0}
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / max(n - 1, 1)
    std = math.sqrt(variance)
    return {
        "mean": round(mean, 1),
        "std": round(std, 1),
        "min": min(values),
        "max": max(values),
    }


def forecast_completion(history, target_tasks=None):
    """基于历史数据预测完成情况"""
    if len(history) < 2:
        return {
            "status": "insufficient_data",
            "message": "需要至少 2 条历史记录才能预测",
            "records_available": len(history),
        }

    scores = [r.get("composite", 0) for r in history]
    stats = calc_stats(scores)

    # 趋势分析：线性回归斜率
    n = len(scores)
    x_mean = (n + 1) / 2
    y_mean = stats["mean"]
    numerator = sum((i + 1 - x_mean) * (s - y_mean) for i, s in enumerate(scores))
    denominator = sum((i + 1 - x_mean) ** 2 for i in range(n))

    slope = numerator / denominator if denominator != 0 else 0

    if slope > 1.5:
        trend = "improving"
    elif slope < -1.5:
        trend = "declining"
    else:
        trend = "stable"

    # 预测下一个 Change 的评分（基于趋势 + 统计分布）
    next_predicted = scores[-1] + slope
    next_predicted = max(0, min(100, next_predicted))

    # 置信区间（基于历史标准差）
    std = stats["std"] if stats["std"] > 0 else 5
    intervals = {
        "50pct": round(max(0, min(100, next_predicted - 0.67 * std)), 1),
        "70pct": round(max(0, min(100, next_predicted - 1.04 * std)), 1),
        "85pct": round(max(0, min(100, next_predicted - 1.44 * std)), 1),
        "95pct": round(max(0, min(100, next_predicted - 1.96 * std)), 1),
    }

    # 维度级分析
    dim_analysis = {}
    all_dims = set()
    for r in history:
        scores_dict = r.get("scores", {})
        all_dims.update(scores_dict.keys())

    for dim in all_dims:
        dim_values = [r.get("scores", {}).get(dim, 0) for r in history]
        dim_stats = calc_stats(dim_values)
        if len(dim_values) >= 2:
            dim_slope = (dim_values[-1] - dim_values[0]) / len(dim_values)
        else:
            dim_slope = 0
        dim_analysis[dim] = {
            "current": dim_values[-1] if dim_values else 0,
            "avg": dim_stats["mean"],
            "trend": "improving" if dim_slope > 1 else ("declining" if dim_slope < -1 else "stable"),
            "potential": max(0, 100 - (dim_values[-1] if dim_values else 0)),
        }

    # 按改进潜力排序维度
    improvement_priority = sorted(
        [(d, info) for d, info in dim_analysis.items() if info["potential"] > 10],
        key=lambda x: x[1]["potential"],
        reverse=True,
    )

    # 任务完成预测（如指定目标任务数）
    task_forecast = None
    if target_tasks and target_tasks > 0:
        # 基于历史 AC 通过率估算
        ac_rates = []
        for r in history:
            ac_val = r.get("scores", {}).get("AC 通过率", 80)
            ac_rates.append(ac_val / 100)

        avg_ac_rate = sum(ac_rates) / len(ac_rates) if ac_rates else 0.8

        # 蒙特卡洛简化版：基于通过率分布
        expected_pass = round(target_tasks * avg_ac_rate)
        pessimistic = round(target_tasks * max(0, avg_ac_rate - 0.15))
        optimistic = round(target_tasks * min(1.0, avg_ac_rate + 0.10))

        task_forecast = {
            "target_tasks": target_tasks,
            "expected_pass": expected_pass,
            "optimistic": optimistic,
            "pessimistic": pessimistic,
            "historical_pass_rate": round(avg_ac_rate * 100, 1),
        }

    # RAG 预测
    if next_predicted >= 80:
        predicted_rag = "Green"
    elif next_predicted >= 60:
        predicted_rag = "Amber"
    else:
        predicted_rag = "Red"

    return {
        "status": "ok",
        "trend": trend,
        "slope": round(slope, 2),
        "current_score": scores[-1],
        "predicted_next": round(next_predicted, 1),
        "predicted_rag": predicted_rag,
        "confidence_intervals": intervals,
        "stats": stats,
        "records_analyzed": len(history),
        "dimension_analysis": dim_analysis,
        "improvement_priority": [(d, info) for d, info in improvement_priority[:5]],
        "task_forecast": task_forecast,
    }


def format_markdown(result):
    if result["status"] == "insufficient_data":
        return f"**数据不足**：{result['message']}（当前 {result['records_available']} 条记录）"

    trend_icon = {"improving": "📈", "stable": "➡️", "declining": "📉"}.get(result["trend"], "➡️")
    rag_icon = {"Green": "🟢", "Amber": "🟡", "Red": "🔴"}.get(result["predicted_rag"], "⚪")

    lines = ["## 完成率预测\n"]
    lines.append(f"**趋势**：{trend_icon} {result['trend']}（斜率 {result['slope']}）")
    lines.append(f"**当前评分**：{result['current_score']}")
    lines.append(f"**预测下一个 Change**：{result['predicted_next']} {rag_icon} {result['predicted_rag']}")
    lines.append(f"**分析样本**：{result['records_analyzed']} 条历史记录\n")

    # 置信区间
    ci = result["confidence_intervals"]
    lines.append("### 预测置信区间\n")
    lines.append("| 置信度 | 预测下限 |")
    lines.append("|--------|---------|")
    lines.append(f"| 50% | {ci['50pct']} |")
    lines.append(f"| 70% | {ci['70pct']} |")
    lines.append(f"| 85% | {ci['85pct']} |")
    lines.append(f"| 95% | {ci['95pct']} |")

    # 维度改进优先级
    if result["improvement_priority"]:
        lines.append("\n### 改进优先级（按潜力排序）\n")
        lines.append("| 维度 | 当前分 | 平均分 | 趋势 | 改进潜力 |")
        lines.append("|------|--------|--------|------|---------|")
        for dim, info in result["improvement_priority"]:
            t_icon = "📈" if info["trend"] == "improving" else ("📉" if info["trend"] == "declining" else "➡️")
            lines.append(f"| {dim} | {info['current']} | {info['avg']} | {t_icon} {info['trend']} | {info['potential']} |")

    # 任务完成预测
    tf = result.get("task_forecast")
    if tf:
        lines.append("\n### 任务完成预测\n")
        lines.append(f"- 目标任务数：{tf['target_tasks']}")
        lines.append(f"- 历史通过率：{tf['historical_pass_rate']}%")
        lines.append(f"- 乐观估计：{tf['optimistic']} 个任务通过")
        lines.append(f"- 预期估计：{tf['expected_pass']} 个任务通过")
        lines.append(f"- 悲观估计：{tf['pessimistic']} 个任务通过")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="完成率预测器")
    parser.add_argument("input", help="health-history.jsonl 文件路径")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--tasks", type=int, default=None, help="目标任务数（用于预测任务完成情况）")
    args = parser.parse_args()

    history = load_history(args.input)
    result = forecast_completion(history, target_tasks=args.tasks)

    if args.format == "json":
        # 序列化时处理 tuple 列表
        output = dict(result)
        if "improvement_priority" in output:
            output["improvement_priority"] = [
                {"dimension": d, **info} for d, info in output["improvement_priority"]
            ]
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(result))


if __name__ == "__main__":
    main()
