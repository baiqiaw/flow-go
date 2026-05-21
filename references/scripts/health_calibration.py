#!/usr/bin/env python3
"""健康评分校准器 — 计算各维度与实际结果的相关性，输出权重校准建议

用法：
  python3 health_calibration.py --specs-dir .specs [--min-samples 5]

输入：
  - .specs/traces.jsonl（含 outcome 字段的记录）
  - references/scripts/health_scorer.py 的 DIMENSIONS 权重定义

输出（JSON）：
  sample_size / outcome_distribution / correlations / suggestions

退出码：0=成功，1=参数错误，2=样本不足
"""

import argparse
import json
import os
import statistics
import sys


CURRENT_WEIGHTS = {
    "ac_coverage": 0.22,
    "test_completeness": 0.18,
    "review_efficiency": 0.13,
    "code_quality": 0.13,
    "boundary_hygiene": 0.13,
    "doc_completeness": 0.10,
    "resource_efficiency": 0.11,
}

OUTCOME_SCORES = {
    "success": 1.0,
    "degraded": 0.5,
    "hotfixed": 0.3,
    "abandoned": 0.0,
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="健康评分校准器 — 计算维度与结果相关性",
        prog="health_calibration",
    )
    parser.add_argument("--specs-dir", required=True, help="项目 spec 根目录（必选）")
    parser.add_argument("--min-samples", type=int, default=5, help="最小样本数（可选，默认 5）")
    parser.add_argument("--format", choices=["text", "json"], default="json", dest="output_format",
                        help="输出格式（可选，默认 json）")
    return parser.parse_args()


def read_traces(specs_dir):
    path = os.path.join(os.path.abspath(specs_dir), "traces.jsonl")
    if not os.path.isfile(path):
        return []
    traces = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                traces.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
    return traces


def rank(values):
    sorted_vals = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(sorted_vals):
        j = i
        while j < len(sorted_vals) - 1 and sorted_vals[j + 1][1] == sorted_vals[j][1]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[sorted_vals[k][0]] = avg_rank
        i = j + 1
    return ranks


def spearman_rho(x, y):
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    rx = rank(x)
    ry = rank(y)
    n = len(x)
    d_sq = sum((rx[i] - ry[i]) ** 2 for i in range(n))
    return 1.0 - (6.0 * d_sq) / (n * (n * n - 1))


def format_text_output(report):
    """将校准报告格式化为可读文本"""
    lines = []
    lines.append("=" * 60)
    lines.append("健康评分校准报告")
    lines.append("=" * 60)
    lines.append("")

    # 概况
    lines.append(f"样本数量: {report['sample_size']}")
    lines.append("结果分布:")
    for outcome, count in report["outcome_distribution"].items():
        lines.append(f"  {outcome}: {count}")
    lines.append("")

    # 相关性分析
    lines.append("-" * 40)
    lines.append("维度相关性分析")
    lines.append("-" * 40)
    for dim, info in report["correlations"].items():
        rho = info["correlation"]
        direction = "正相关" if rho > 0 else ("负相关" if rho < 0 else "无相关")
        lines.append(f"  {dim}:")
        lines.append(f"    Spearman r = {rho}（{direction}）")
        lines.append(f"    当前权重: {info['current_weight']}  建议权重: {info['suggested_weight']}")
    lines.append("")

    # 权重调整建议
    if report["suggestions"]:
        lines.append("-" * 40)
        lines.append("权重调整建议")
        lines.append("-" * 40)
        for i, s in enumerate(report["suggestions"], 1):
            lines.append(f"  {i}. {s}")
    lines.append("")

    # 汇总
    lines.append("=" * 60)
    lines.append("汇总")
    lines.append("=" * 60)
    total = len(report["correlations"])
    high_corr = sum(1 for v in report["correlations"].values() if v["correlation"] > 0.3)
    lines.append(f"  共分析 {total} 个维度，其中 {high_corr} 个与结果中高度相关")
    lines.append("")

    return "\n".join(lines)


def main():
    args = parse_args()

    specs_dir = os.path.abspath(args.specs_dir)
    if not os.path.isdir(specs_dir):
        print(f"错误：spec 目录不存在 — {args.specs_dir}", file=sys.stderr)
        sys.exit(1)

    traces = read_traces(specs_dir)
    with_outcome = [t for t in traces if t.get("outcome") and t.get("health_dimensions")]

    if len(with_outcome) < args.min_samples:
        print(f"警告：有 outcome 的样本不足（{len(with_outcome)} < {args.min_samples}）", file=sys.stderr)
        if not with_outcome:
            fallback = {"sample_size": 0, "outcome_distribution": {}, "correlations": {}, "suggestions": ["样本不足，无法计算校准建议"]}
            if args.output_format == "text":
                print(format_text_output(fallback))
            else:
                print(json.dumps(fallback, ensure_ascii=False, indent=2))
            sys.exit(2)

    outcome_dist = {}
    for t in with_outcome:
        o = t["outcome"]
        outcome_dist[o] = outcome_dist.get(o, 0) + 1

    outcome_values = [OUTCOME_SCORES.get(t["outcome"], 0.5) for t in with_outcome]

    correlations = {}
    dim_names = set()
    for t in with_outcome:
        dim_names.update(t.get("health_dimensions", {}).keys())

    for dim in sorted(dim_names):
        dim_values = [t.get("health_dimensions", {}).get(dim, 0) for t in with_outcome]
        rho = round(spearman_rho(dim_values, outcome_values), 2)
        current_w = CURRENT_WEIGHTS.get(dim, 0.10)
        if rho > 0:
            suggested_w = round(min(0.35, current_w * (1 + rho * 0.3)), 2)
        else:
            suggested_w = round(max(0.05, current_w * (1 + rho * 0.3)), 2)
        correlations[dim] = {
            "correlation": rho,
            "current_weight": current_w,
            "suggested_weight": suggested_w,
        }

    suggestions = []
    sorted_corr = sorted(correlations.items(), key=lambda x: abs(x[1]["correlation"]), reverse=True)
    for dim, info in sorted_corr[:3]:
        rho = info["correlation"]
        if rho > 0.5:
            suggestions.append(f"{dim} 与实际结果高度相关（r={rho}），建议提高权重至 {info['suggested_weight']}")
        elif rho < -0.3:
            suggestions.append(f"{dim} 呈负相关（r={rho}），可能是噪音维度，建议降低权重")
        elif abs(rho) < 0.15:
            suggestions.append(f"{dim} 相关性低（r={rho}），对结果预测贡献有限")

    report = {
        "sample_size": len(with_outcome),
        "outcome_distribution": outcome_dist,
        "correlations": correlations,
        "suggestions": suggestions,
    }

    if args.output_format == "text":
        print(format_text_output(report))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if len(with_outcome) < args.min_samples:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
