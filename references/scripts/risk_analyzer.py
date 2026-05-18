#!/usr/bin/env python3
"""风险矩阵分析器 — 从 DESIGN.md 风险表格生成量化评估

输入 JSON 格式（从 DESIGN.md 风险表格解析）：
[
  {"name": "风险描述", "probability": "高", "impact": "中", "category": "technical"},
  ...
]

概率/影响映射：低=1, 中=2, 高=3

用法：
    echo '[{"name":"依赖X不稳定","probability":"高","impact":"中"}]' | python3 risk_analyzer.py
    python3 risk_analyzer.py risks.json
    python3 risk_analyzer.py risks.json --format json
"""

import argparse
import json
import sys

LEVEL_MAP = {"低": 1, "中": 2, "高": 3, "low": 1, "medium": 2, "high": 3}

CATEGORY_MITIGATIONS = {
    "technical": [
        "技术验证（PoC/Spike）",
        "准备备选方案",
        "增量开发，分阶段验证",
    ],
    "schedule": [
        "关键路径分析，预留缓冲",
        "依赖解耦，并行推进",
        "范围裁剪，分期交付",
    ],
    "business": [
        "用户访谈验证假设",
        "竞品分析对比",
        "设置决策检查点",
    ],
    "integration": [
        "接口契约先行（API Mock）",
        "集成测试提前覆盖",
        "与依赖方对齐排期",
    ],
}

RISK_LEVELS = [
    (1, 3, "低"),
    (4, 6, "中"),
    (7, 9, "高"),
]


def score_risk(prob, impact):
    p = LEVEL_MAP.get(str(prob).lower(), 2)
    i = LEVEL_MAP.get(str(impact).lower(), 2)
    return p * i, p, i


def classify(score):
    for lo, hi, label in RISK_LEVELS:
        if lo <= score <= hi:
            return label
    return "高"


def analyze(risks):
    results = []
    for r in risks:
        score, p, i = score_risk(r.get("probability", "中"), r.get("impact", "中"))
        cat = r.get("category", "technical")
        mitigations = CATEGORY_MITIGATIONS.get(cat, CATEGORY_MITIGATIONS["technical"])
        results.append({
            "name": r["name"],
            "probability": p,
            "impact": i,
            "score": score,
            "level": classify(score),
            "category": cat,
            "mitigations": mitigations[:2],
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    high_count = sum(1 for r in results if r["level"] == "高")
    mid_count = sum(1 for r in results if r["level"] == "中")
    low_count = sum(1 for r in results if r["level"] == "低")

    return {
        "risks": results,
        "summary": {
            "total": len(results),
            "high": high_count,
            "medium": mid_count,
            "low": low_count,
            "avg_score": round(sum(r["score"] for r in results) / max(len(results), 1), 1),
        },
        "recommendation": (
            "高风险 ≥ 1：必须制定缓解方案并写回 DESIGN.md"
            if high_count > 0
            else "中风险为主：建议逐项评估是否需要缓解"
            if mid_count > 0
            else "风险可控：继续推进"
        ),
    }


def format_markdown(report):
    lines = ["## 风险矩阵分析结果\n"]
    s = report["summary"]
    lines.append(f"共 {s['total']} 项风险：高 {s['high']} / 中 {s['medium']} / 低 {s['low']}，平均分 {s['avg_score']}")
    lines.append(f"\n**建议**：{report['recommendation']}\n")
    lines.append("| 风险 | 概率 | 影响 | 分数 | 等级 | 缓解建议 |")
    lines.append("|------|------|------|------|------|----------|")
    for r in report["risks"]:
        mits = "；".join(r["mitigations"])
        lines.append(f"| {r['name']} | {r['probability']} | {r['impact']} | {r['score']} | {r['level']} | {mits} |")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="风险矩阵分析器")
    parser.add_argument("input", nargs="?", help="JSON 文件路径，省略则读 stdin")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    source = open(args.input, encoding="utf-8") if args.input else sys.stdin
    try:
        risks = json.load(source)
    except json.JSONDecodeError as e:
        print(f"错误：输入不是合法 JSON — {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if args.input:
            source.close()

    report = analyze(risks)

    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(report))


if __name__ == "__main__":
    main()
