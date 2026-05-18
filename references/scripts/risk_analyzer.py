#!/usr/bin/env python3
"""风险矩阵分析器 — 从 DESIGN.md 风险表格生成量化评估

输入 JSON 格式（从 DESIGN.md 风险表格解析）：
[
  {"name": "风险描述", "probability": "高", "impact": "中", "category": "technical",
   "financial_impact": 50000, "effort_days": { "optimistic": 2, "likely": 5, "pessimistic": 12 }},
  ...
]

概率/影响映射：低=1, 中=2, 高=3

用法：
    echo '[{"name":"依赖X不稳定","probability":"高","impact":"中","financial_impact":30000}]' | python3 risk_analyzer.py
    python3 risk_analyzer.py risks.json
    python3 risk_analyzer.py risks.json --format json
    python3 risk_analyzer.py risks.json --emv-budget 500000  # 计算风险调整预算
"""

import argparse
import json
import sys

LEVEL_MAP = {"低": 1, "中": 2, "高": 3, "low": 1, "medium": 2, "high": 3}

CATEGORY_WEIGHTS = {
    "technical": 1.2,
    "resource": 1.1,
    "financial": 1.4,
    "schedule": 1.0,
    "business": 1.0,
    "integration": 1.1,
}

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
    "resource": [
        "交叉培训，减少单点依赖",
        "预留 buffer 容量",
        "外部资源备选",
    ],
    "financial": [
        "分阶段预算审批",
        "预留应急储备",
        "成本监控告警",
    ],
}

# 风险分数 → 应对策略阈值（借鉴 pm-skills EMV 风险响应框架）
RESPONSE_STRATEGIES = [
    (18, "规避（Avoid）", "分数 > 18：通过范围或方案变更消除风险"),
    (12, "缓解（Mitigate）", "分数 12-18：通过主动干预降低概率或影响"),
    (8, "转移（Transfer）", "分数 8-12：通过合同/保险/合作转移风险"),
    (0, "接受（Accept）", "分数 < 8：监控并准备应急计划"),
]

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


def recommend_response(weighted_score):
    """按加权风险分数推荐应对策略"""
    for threshold, strategy, desc in RESPONSE_STRATEGIES:
        if weighted_score >= threshold:
            return strategy, desc
    return "接受（Accept）", "分数 < 8：监控并准备应急计划"


def three_point_estimate(optimistic, likely, pessimistic):
    """PERT 三点估算：期望值和标准差

    Returns: (expected_value, std_deviation)
    """
    expected = (optimistic + 4 * likely + pessimistic) / 6
    std_dev = (pessimistic - optimistic) / 6
    return round(expected, 1), round(std_dev, 1)


def calculate_emv(risks_results):
    """计算总 EMV（期望货币价值）和风险调整预算

    EMV = Σ(概率 × 财务影响)
    """
    total_emv = 0
    for r in risks_results:
        fi = r.get("financial_impact", 0)
        p_numeric = r.get("probability", 2)
        # 概率数值映射为百分比：1→20%, 2→50%, 3→80%
        prob_pct = {1: 0.2, 2: 0.5, 3: 0.8}.get(p_numeric, 0.5)
        emv = prob_pct * fi
        r["emv"] = round(emv)
        r["probability_pct"] = round(prob_pct * 100)
        total_emv += emv
    return round(total_emv)


def analyze(risks, budget=None):
    results = []
    for r in risks:
        score, p, i = score_risk(r.get("probability", "中"), r.get("impact", "中"))
        cat = r.get("category", "technical")
        cat_weight = CATEGORY_WEIGHTS.get(cat, 1.0)
        weighted_score = round(score * cat_weight, 1)
        mitigations = CATEGORY_MITIGATIONS.get(cat, CATEGORY_MITIGATIONS["technical"])
        response, response_desc = recommend_response(weighted_score)

        entry = {
            "name": r["name"],
            "probability": p,
            "impact": i,
            "score": score,
            "weighted_score": weighted_score,
            "level": classify(score),
            "category": cat,
            "mitigations": mitigations[:2],
            "response_strategy": response,
            "response_desc": response_desc,
            "financial_impact": r.get("financial_impact", 0),
        }

        # 三点估算（如有 effort_days 字段）
        effort = r.get("effort_days")
        if effort and all(k in effort for k in ("optimistic", "likely", "pessimistic")):
            expected, std_dev = three_point_estimate(
                effort["optimistic"], effort["likely"], effort["pessimistic"]
            )
            entry["estimate_expected_days"] = expected
            entry["estimate_std_dev"] = std_dev
            entry["estimate_confidence_85"] = round(expected + 1.04 * std_dev, 1)

        results.append(entry)

    # EMV 计算
    total_emv = calculate_emv(results)

    results.sort(key=lambda x: x["weighted_score"], reverse=True)

    high_count = sum(1 for r in results if r["level"] == "高")
    mid_count = sum(1 for r in results if r["level"] == "中")
    low_count = sum(1 for r in results if r["level"] == "低")

    report = {
        "risks": results,
        "summary": {
            "total": len(results),
            "high": high_count,
            "medium": mid_count,
            "low": low_count,
            "avg_score": round(sum(r["score"] for r in results) / max(len(results), 1), 1),
            "total_emv": total_emv,
        },
        "recommendation": (
            "高风险 ≥ 1：必须制定缓解方案并写回 DESIGN.md"
            if high_count > 0
            else "中风险为主：建议逐项评估是否需要缓解"
            if mid_count > 0
            else "风险可控：继续推进"
        ),
    }

    # 风险调整预算（如提供 base budget）
    if budget and budget > 0:
        portfolio_risk_score = report["summary"]["avg_score"]
        risk_premium = portfolio_risk_score * 0.02  # 每分风险 2% 预备金
        adjusted_budget = round(budget * (1 + risk_premium))
        report["risk_budget"] = {
            "base_budget": budget,
            "risk_premium_pct": round(risk_premium * 100, 1),
            "risk_adjusted_budget": adjusted_budget,
            "contingency_reserve": adjusted_budget - budget,
        }

    return report


def format_markdown(report):
    lines = ["## 风险矩阵分析结果\n"]
    s = report["summary"]
    lines.append(f"共 {s['total']} 项风险：高 {s['high']} / 中 {s['medium']} / 低 {s['low']}，平均分 {s['avg_score']}")

    if s["total_emv"] > 0:
        lines.append(f"\n**总 EMV（期望货币价值）**：¥{s['total_emv']:,}")

    lines.append(f"\n**建议**：{report['recommendation']}\n")

    # 主表
    lines.append("| 风险 | 概率 | 影响 | 分数 | 加权分 | 等级 | 应对策略 | 缓解建议 |")
    lines.append("|------|------|------|------|--------|------|----------|----------|")
    for r in report["risks"]:
        mits = "；".join(r["mitigations"])
        lines.append(
            f"| {r['name']} | {r['probability']} | {r['impact']} | {r['score']} "
            f"| {r['weighted_score']} | {r['level']} | {r['response_strategy']} | {mits} |"
        )

    # 三点估算表（如有）
    estimated = [r for r in report["risks"] if "estimate_expected_days" in r]
    if estimated:
        lines.append("\n### 工期三点估算（PERT）\n")
        lines.append("| 风险 | 期望工期（天） | 标准差 | 85%置信上限 |")
        lines.append("|------|---------------|--------|------------|")
        for r in estimated:
            lines.append(
                f"| {r['name']} | {r['estimate_expected_days']} | {r['estimate_std_dev']} "
                f"| {r['estimate_confidence_85']} |"
            )

    # 风险调整预算（如有）
    rb = report.get("risk_budget")
    if rb:
        lines.append("\n### 风险调整预算\n")
        lines.append(f"- 基础预算：¥{rb['base_budget']:,}")
        lines.append(f"- 风险预备金率：{rb['risk_premium_pct']}%")
        lines.append(f"- 风险调整后预算：¥{rb['risk_adjusted_budget']:,}")
        lines.append(f"- 应急储备：¥{rb['contingency_reserve']:,}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="风险矩阵分析器（含 EMV 量化 + 三点估算）")
    parser.add_argument("input", nargs="?", help="JSON 文件路径，省略则读 stdin")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--emv-budget", type=float, default=None, help="项目基础预算（用于计算风险调整预算）")
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

    report = analyze(risks, budget=args.emv_budget)

    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(report))


if __name__ == "__main__":
    main()
