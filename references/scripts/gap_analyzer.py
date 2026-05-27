#!/usr/bin/env python3
"""Gap 分析器 — 按标签维度分片统计健康评分，识别薄弱环节

用法：
  python3 gap_analyzer.py --specs-dir .specs [--min-samples 3] [--threshold 1.5]

输入：
  - .specs/traces.jsonl（含标签的轨迹记录）
  - .specs/LESSONS.md（关联失败经验）
  - .specs/.lessons.jsonl（索引，如存在）

输出（JSON）：
  slices/weak_slices/related_lessons/suggestion

退出码：0=成功，1=参数错误，2=样本不足
"""

import argparse
import json
import os
import re
import statistics
import sys
from datetime import datetime, timedelta, timezone


TAG_DIMENSIONS = [
    "change_type",
    "complexity",
    "bottleneck_stage",
    "rollback_count",
    "files_touched",
    "cross_subsystem",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Gap 分析器 — 按标签维度分片统计健康评分",
        prog="gap_analyzer",
    )
    parser.add_argument("--specs-dir", required=True, help="项目 spec 根目录（必选）")
    parser.add_argument("--min-samples", type=int, default=3, help="最小样本数（可选，默认 3）")
    parser.add_argument("--threshold", type=float, default=1.5, help="偏差阈值（可选，默认 1.5 分）")
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
            line = line.strip()
            if not line:
                continue
            try:
                traces.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return traces


def read_lessons(specs_dir):
    path = os.path.join(os.path.abspath(specs_dir), ".lessons.jsonl")
    if not os.path.isfile(path):
        path2 = os.path.join(os.path.abspath(specs_dir), "LESSONS.md")
        if os.path.isfile(path2):
            with open(path2, encoding="utf-8") as f:
                return _parse_lessons_md(f.read())
        return []
    lessons = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                lessons.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
    return lessons


def _parse_lessons_md(content):
    lessons = []
    pattern = re.compile(r"###\s+(L-\d+)\s+(.+?)\n", re.MULTILINE)
    for m in pattern.finditer(content):
        lessons.append({"id": m.group(1), "title": m.group(2).strip()})
    return lessons


def analyze_slices(traces, threshold):
    overall_scores = [t["health_score"] for t in traces if t.get("health_score") is not None]
    if not overall_scores:
        return [], []
    overall_avg = statistics.mean(overall_scores)

    dimension_slices = []
    weak_slices = []

    for dim in TAG_DIMENSIONS:
        groups = {}
        for t in traces:
            tags = t.get("tags", {})
            value = tags.get(dim)
            if value is None:
                continue
            key = str(value)
            if key not in groups:
                groups[key] = []
            if t.get("health_score") is not None:
                groups[key].append(t["health_score"])

        dim_slices = []
        for value, scores in sorted(groups.items()):
            if not scores:
                continue
            avg = round(statistics.mean(scores), 1)
            deviation = round(avg - overall_avg, 1)
            entry = {"value": value, "count": len(scores), "avg_score": avg, "deviation": deviation}
            if deviation < -threshold:
                entry["weak"] = True
                weak_slices.append({
                    "dimension": dim,
                    "value": value,
                    "avg_score": avg,
                    "deviation": deviation,
                    "related_lessons": [],
                    "suggestion": f"{dim}={value} 类型变更平均评分 {avg}（偏差 {deviation}），建议加强关注",
                })
            dim_slices.append(entry)

        if dim_slices:
            dimension_slices.append({"dimension": dim, "slices": dim_slices})

    return dimension_slices, weak_slices


def attach_lessons(weak_slices, lessons):
    for ws in weak_slices:
        query = f"{ws['dimension']} {ws['value']}"
        related = []
        for l in lessons:
            title = l.get("title", "").lower()
            keywords = " ".join(l.get("keywords", [])).lower()
            if query.lower() in title or query.lower() in keywords:
                related.append(f"{l.get('id', '?')} {l.get('title', '')}")
        ws["related_lessons"] = related[:5]


def format_text_output(report):
    """将分析报告格式化为可读的文本输出"""
    lines = []
    lines.append("=" * 60)
    lines.append("GAP 分析报告")
    lines.append("=" * 60)

    overall = report.get("overall_avg_score")
    lines.append(f"\n总轨迹数: {report.get('total_traces', 0)}")
    lines.append(f"整体平均评分: {overall if overall is not None else 'N/A'}")

    weak = report.get("weak_slices", [])
    if weak:
        lines.append(f"\n薄弱分片 ({len(weak)} 个):")
        lines.append("-" * 60)
        lines.append(f"{'维度':<16} {'值':<12} {'均分':>5} {'偏差':>6}  {'建议'}")
        lines.append("-" * 60)
        for ws in weak:
            lines.append(
                f"{ws['dimension']:<16} {ws['value']:<12} {ws['avg_score']:>5} {ws['deviation']:>+6.1f}  {ws['suggestion']}"
            )
            related = ws.get("related_lessons", [])
            if related:
                for rl in related:
                    lines.append(f"{'':>16} 关联经验: {rl}")
    else:
        lines.append("\n无薄弱分片（各维度均在阈值范围内）。")

    lines.append("=" * 60)
    return "\n".join(lines)


def analyze_skill_errors(specs_dir):
    """分析 skill 自身错误遥测数据

    读取 .specs/skill-errors.jsonl，统计：
      - 各脚本错误频率排名
      - 错误类型分布
      - 近 30 天趋势
    """
    path = os.path.join(os.path.abspath(specs_dir), "skill-errors.jsonl")
    if not os.path.isfile(path):
        return {"available": False, "message": "skill-errors.jsonl 不存在，无错误数据"}

    from collections import Counter

    records = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return {"available": False, "message": "skill-errors.jsonl 读取失败"}

    if not records:
        return {"available": True, "total_errors": 0, "message": "无 skill 错误记录"}

    # 各脚本错误频率
    script_counts = Counter(r.get("script", "?") for r in records)
    top_scripts = [{"script": s, "count": c} for s, c in script_counts.most_common(5)]

    # 错误类型分布
    type_counts = Counter(r.get("error_type", "Unknown") for r in records)
    type_distribution = {t: c for t, c in type_counts.most_common()}

    # 恢复类型分布
    recovery_counts = Counter(r.get("recovery", "?") for r in records)

    # 近 30 天趋势
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    recent = []
    older = []
    for r in records:
        try:
            ts = datetime.fromisoformat(r.get("ts", "").replace("Z", "+00:00"))
            if ts >= thirty_days_ago:
                recent.append(r)
            else:
                older.append(r)
        except (ValueError, TypeError):
            older.append(r)

    # 趋势：比较最近 15 天和前 15 天
    mid_point = now - timedelta(days=15)
    recent_parsed = [(r, _parse_ts(r)) for r in recent]
    period1 = [r for r, ts in recent_parsed if ts and ts < mid_point]
    period2 = [r for r, ts in recent_parsed if ts and ts >= mid_point]
    if len(period1) > 0 and len(period2) > 0:
        if len(period2) > len(period1) * 1.3:
            trend = "rising"
            trend_label = "上升"
        elif len(period1) > len(period2) * 1.3:
            trend = "falling"
            trend_label = "下降"
        else:
            trend = "stable"
            trend_label = "平稳"
    else:
        trend = "insufficient_data"
        trend_label = "数据不足"

    return {
        "available": True,
        "total_errors": len(records),
        "recent_30d": len(recent),
        "older": len(older),
        "trend": trend,
        "trend_label": trend_label,
        "top_scripts": top_scripts,
        "error_types": type_distribution,
        "recovery_distribution": dict(recovery_counts),
    }


def _parse_ts(record):
    try:
        return datetime.fromisoformat(record.get("ts", "").replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def main():
    args = parse_args()

    specs_dir = os.path.abspath(args.specs_dir)
    if not os.path.isdir(specs_dir):
        print(f"错误：spec 目录不存在 — {args.specs_dir}", file=sys.stderr)
        sys.exit(1)

    traces = read_traces(specs_dir)
    if len(traces) < args.min_samples:
        print(f"警告：样本不足（{len(traces)} < {args.min_samples}），结果可能不可靠", file=sys.stderr)

    lessons = read_lessons(specs_dir)
    dimension_slices, weak_slices = analyze_slices(traces, args.threshold)
    attach_lessons(weak_slices, lessons)

    overall_scores = [t["health_score"] for t in traces if t.get("health_score") is not None]
    report = {
        "total_traces": len(traces),
        "overall_avg_score": round(statistics.mean(overall_scores), 1) if overall_scores else None,
        "slices": dimension_slices,
        "weak_slices": weak_slices,
        "skill_health": analyze_skill_errors(specs_dir),
    }

    if args.output_format == "text":
        print(format_text_output(report))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if len(traces) < args.min_samples:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
