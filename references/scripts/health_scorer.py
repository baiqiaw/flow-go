#!/usr/bin/env python3
"""项目健康评分器 — 从 flow-go 工件计算 7 维健康分数，追加趋势到 health-history.jsonl

用法：cat metrics.json | python3 health_scorer.py
     python3 health_scorer.py metrics.json [--format json]

输入 JSON：ac_total, ac_passed, test_rounds_completed/skipped, review_rounds,
  code_lines_added/removed, files_changed, boundary_violations, hallucination_flags,
  artifacts_complete, change_id(可选)"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone


DIMENSIONS = {
    "ac_coverage": {
        "label": "AC 通过率",
        "weight": 0.22,
    },
    "test_completeness": {
        "label": "测试覆盖",
        "weight": 0.18,
    },
    "review_efficiency": {
        "label": "评审效率",
        "weight": 0.13,
    },
    "code_quality": {
        "label": "代码质量",
        "weight": 0.13,
    },
    "boundary_hygiene": {
        "label": "边界卫生",
        "weight": 0.13,
    },
    "doc_completeness": {
        "label": "文档完备",
        "weight": 0.10,
    },
    "token_efficiency": {
        "label": "资源效率",
        "weight": 0.11,
    },
}

EXPECTED_ARTIFACTS = [
    "CHANGE.md", "REQUIREMENT.md", "DESIGN.md",
    "TASK.md", "SUMMARY.md", "TEST.md",
]


def score_ac_coverage(data):
    total = data.get("ac_total", 0)
    passed = data.get("ac_passed", 0)
    if total == 0:
        return 100
    return round(passed / total * 100)


def score_test_completeness(data):
    completed = data.get("test_rounds_completed", 0)
    skipped = data.get("test_rounds_skipped", 0)
    total = completed + skipped
    if total == 0:
        return 50
    return round(completed / total * 100)


def score_review_efficiency(data):
    rounds = data.get("review_rounds", 1)
    if rounds <= 1:
        return 100
    if rounds == 2:
        return 80
    if rounds == 3:
        return 50
    return 30


def score_code_quality(data):
    added = data.get("code_lines_added", 0)
    removed = data.get("code_lines_removed", 0)
    total = added + removed
    hallucination = data.get("hallucination_flags", 0)
    if total == 0:
        return 80
    base = 90 if hallucination == 0 else 50
    if total < 200:
        return base
    if total < 500:
        return base - 10
    return base - 20


def score_boundary_hygiene(data):
    violations = data.get("boundary_violations", 0)
    if violations == 0:
        return 100
    if violations == 1:
        return 70
    if violations <= 3:
        return 40
    return 20


def score_doc_completeness(data):
    artifacts = data.get("artifacts_complete", [])
    if not artifacts:
        return 50
    present = sum(1 for a in EXPECTED_ARTIFACTS if a in artifacts)
    return round(present / len(EXPECTED_ARTIFACTS) * 100)


def score_token_efficiency(data):
    """资源效率评分：基于改动代码量与产出 AC 的比值

    效率 = AC 通过数 / (代码行数 / 100)
    高效 = 少代码多 AC 通过 = 高分
    """
    ac_passed = data.get("ac_passed", 0)
    code_lines = data.get("code_lines_added", 0) + data.get("code_lines_removed", 0)

    if ac_passed == 0:
        return 50  # 无 AC 通过，基线分

    if code_lines == 0:
        return 100  # 无代码改动但 AC 通过（如配置/文档变更）

    efficiency = ac_passed / (code_lines / 100)

    if efficiency >= 1.0:
        return 100  # 每 100 行代码 >= 1 个 AC
    if efficiency >= 0.5:
        return 80
    if efficiency >= 0.2:
        return 60
    return 40  # 代码量大但 AC 覆盖少


SCORERS = {
    "ac_coverage": score_ac_coverage,
    "test_completeness": score_test_completeness,
    "review_efficiency": score_review_efficiency,
    "code_quality": score_code_quality,
    "boundary_hygiene": score_boundary_hygiene,
    "doc_completeness": score_doc_completeness,
    "token_efficiency": score_token_efficiency,
}


def compute(data):
    scores = {}
    for dim, scorer in SCORERS.items():
        scores[dim] = scorer(data)

    total_weight = sum(d["weight"] for d in DIMENSIONS.values())
    composite = sum(
        scores[dim] * DIMENSIONS[dim]["weight"]
        for dim in DIMENSIONS
    ) / total_weight

    composite = round(composite, 1)

    if composite >= 85:
        grade = "A"
    elif composite >= 70:
        grade = "B"
    elif composite >= 55:
        grade = "C"
    else:
        grade = "D"

    # RAG 状态：综合 + 最低维度双判定
    min_score = min(scores.values())
    if composite >= 80 and min_score >= 60:
        rag = "Green"
    elif composite >= 60 and min_score >= 40:
        rag = "Amber"
    else:
        rag = "Red"

    return {
        "scores": {DIMENSIONS[dim]["label"]: scores[dim] for dim in DIMENSIONS},
        "composite": composite,
        "grade": grade,
        "rag": rag,
    }


def format_markdown(report):
    rag_icon = {"Green": "🟢", "Amber": "🟡", "Red": "🔴"}.get(report["rag"], "⚪")
    lines = ["## 项目健康评分\n"]
    lines.append(f"**综合评分：{report['composite']} / 100（{report['grade']}级）{rag_icon} {report['rag']}**\n")
    lines.append("| 维度 | 分数 | 权重 |")
    lines.append("|------|------|------|")
    for dim, score in report["scores"].items():
        w = next(d["weight"] for d in DIMENSIONS.values() if d["label"] == dim)
        lines.append(f"| {dim} | {score} | {int(w * 100)}% |")
    lines.append(f"\n**RAG 判定**：综合 ≥ 80 且最低维度 ≥ 60 → 🟢 Green；综合 ≥ 60 且最低维度 ≥ 40 → 🟡 Amber；其余 → 🔴 Red")
    return "\n".join(lines)


def _read_previous_score(history_path):
    """读取 health-history.jsonl 最后一条的 composite 值"""
    try:
        with open(history_path, encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
    except (FileNotFoundError, OSError):
        return None
    if not lines:
        return None
    try:
        return json.loads(lines[-1]).get("composite")
    except (json.JSONDecodeError, IndexError):
        return None


# ── 测试阶段专属健康评分 ──

TEST_DIMENSIONS = {
    "functional_coverage": {
        "label": "功能覆盖",
        "weight": 0.30,
    },
    "performance_compliance": {
        "label": "性能达标",
        "weight": 0.20,
    },
    "security_compliance": {
        "label": "安全合规",
        "weight": 0.20,
    },
    "compatibility_coverage": {
        "label": "兼容覆盖",
        "weight": 0.15,
    },
    "observability_completeness": {
        "label": "可观测完备",
        "weight": 0.15,
    },
}


def score_functional_coverage(data):
    """功能覆盖：AC 通过率"""
    total = data.get("ac_total", 0)
    passed = data.get("ac_passed", 0)
    if total == 0:
        return 100
    return round(passed / total * 100)


def score_performance_compliance(data):
    """性能达标：性能指标达标率"""
    total = data.get("perf_total", 0)
    passed = data.get("perf_passed", 0)
    if total == 0:
        return 100  # 未测性能=不扣分（可能已跳过）
    return round(passed / total * 100)


def score_security_compliance(data):
    """安全合规：按发现扣分"""
    score = 100
    score -= data.get("sec_critical", 0) * 40
    score -= data.get("sec_high", 0) * 20
    score -= data.get("sec_medium", 0) * 10
    score -= data.get("sec_low", 0) * 5
    return max(0, score)


def score_compatibility_coverage(data):
    """兼容覆盖：目标平台覆盖"""
    total = data.get("compat_total", 0)
    tested = data.get("compat_tested", 0)
    if total == 0:
        return 100
    return round(tested / total * 100)


def score_observability_completeness(data):
    """可观测完备：检查点覆盖"""
    total = data.get("obs_total", 0)
    covered = data.get("obs_covered", 0)
    if total == 0:
        return 100
    return round(covered / total * 100)


TEST_SCORERS = {
    "functional_coverage": score_functional_coverage,
    "performance_compliance": score_performance_compliance,
    "security_compliance": score_security_compliance,
    "compatibility_coverage": score_compatibility_coverage,
    "observability_completeness": score_observability_completeness,
}


def compute_test_score(data):
    """计算测试阶段专属健康评分（5 维加权）

    输入 JSON 字段：
      ac_total, ac_passed,
      perf_total, perf_passed（可选，0 表示跳过性能轮次），
      sec_critical, sec_high, sec_medium, sec_low（各严重度发现数），
      compat_total, compat_tested（目标平台数 / 已测平台数），
      obs_total, obs_covered（可观测检查点总数 / 已覆盖数），
      baseline_score（可选，上次测试评分，用于对比）
    """
    scores = {}
    for dim, scorer in TEST_SCORERS.items():
        scores[dim] = scorer(data)

    total_weight = sum(d["weight"] for d in TEST_DIMENSIONS.values())
    composite = sum(
        scores[dim] * TEST_DIMENSIONS[dim]["weight"]
        for dim in TEST_DIMENSIONS
    ) / total_weight
    composite = round(composite, 1)

    if composite >= 85:
        grade = "A"
    elif composite >= 70:
        grade = "B"
    elif composite >= 55:
        grade = "C"
    else:
        grade = "D"

    # 基线对比
    baseline = data.get("baseline_score")
    delta = None
    if baseline is not None:
        delta = round(composite - baseline, 1)

    return {
        "scores": {TEST_DIMENSIONS[dim]["label"]: scores[dim] for dim in TEST_DIMENSIONS},
        "composite": composite,
        "grade": grade,
        "baseline_delta": delta,
        "dimensions": {
            dim: {
                "score": scores[dim],
                "weight": TEST_DIMENSIONS[dim]["weight"],
            }
            for dim in TEST_DIMENSIONS
        },
    }


def format_test_score_markdown(report):
    """格式化测试健康评分为 Markdown"""
    lines = ["## 测试健康评分\n"]
    delta_str = ""
    if report["baseline_delta"] is not None:
        d = report["baseline_delta"]
        icon = "⚠️" if d < 0 else "✅"
        delta_str = f" {icon} 较基线{'下降' if d < 0 else '上升'} {abs(d)} 分"
    lines.append(f"**综合评分：{report['composite']} / 100（{report['grade']}级）**{delta_str}\n")
    lines.append("| 维度 | 分数 | 权重 |")
    lines.append("|------|------|------|")
    for dim_label, score in report["scores"].items():
        w = next(d["weight"] for d in TEST_DIMENSIONS.values() if d["label"] == dim_label)
        lines.append(f"| {dim_label} | {score} | {int(w * 100)}% |")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="项目健康评分器")
    parser.add_argument("input", nargs="?", help="JSON 文件路径，省略则读 stdin")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--test-score", action="store_true",
                        help="计算测试阶段专属健康评分（5 维）")
    args = parser.parse_args()

    source = open(args.input, encoding="utf-8") if args.input else sys.stdin
    try:
        data = json.load(source)
    except json.JSONDecodeError as e:
        print(f"错误：输入不是合法 JSON — {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if args.input:
            source.close()

    if args.test_score:
        report = compute_test_score(data)
        if args.format == "json":
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(format_test_score_markdown(report))
        return

    report = compute(data)

    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(report))

    # 趋势追踪：追加到 health-history.jsonl
    try:
        hp = os.environ.get("FLOWGO_HISTORY", "health-history.jsonl")
        previous = _read_previous_score(hp)
        entry = json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(),
            "change_id": data.get("change_id", "unknown"),
            "composite": report["composite"], "grade": report["grade"],
            "rag": report["rag"],
            "scores": report["scores"],
            "changes_made": data.get("files_changed", data.get("changes_made", [])),
            "trigger": data.get("trigger", "manual"),
            "previous_score": previous,
        }, ensure_ascii=False)
        with open(hp, "a", encoding="utf-8") as hf:
            hf.write(entry + "\n")
    except OSError:
        pass


# ── 趋势分析 + 自动分诊（借鉴进化引擎 performance_monitor.py）──


def analyze_trends(history_path="health-history.jsonl", window=10):
    """分析健康评分趋势，返回退步领域和分诊优先级"""
    try:
        with open(history_path, encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
    except FileNotFoundError:
        return {"trend": "no_data", "declining_dimensions": [], "triage": []}

    records = []
    for line in lines[-window:]:
        try:
            rec = json.loads(line)
            rec.setdefault("changes_made", [])
            rec.setdefault("trigger", None)
            rec.setdefault("previous_score", None)
            records.append(rec)
        except json.JSONDecodeError:
            continue

    if len(records) < 2:
        return {"trend": "insufficient_data", "declining_dimensions": [], "triage": []}

    # 趋势判定：最近 3 个 vs 之前 3 个的平均
    recent_window = min(3, len(records))
    recent = records[-recent_window:]
    if len(records) > recent_window:
        older = records[:-recent_window][-recent_window:]
    else:
        older = records[:1]

    recent_avg = sum(r.get("composite", 0) for r in recent) / len(recent)
    older_avg = sum(r.get("composite", 0) for r in older) / len(older)
    delta = recent_avg - older_avg

    if delta < -3:
        trend = "declining"
    elif delta > 3:
        trend = "improving"
    else:
        trend = "stable"

    # 维度级趋势
    declining_dims = []
    for dim_label in DIMENSIONS.values():
        label = dim_label["label"]
        recent_vals = [r.get("scores", {}).get(label, 0) for r in recent]
        older_vals = [r.get("scores", {}).get(label, 0) for r in older]
        if not recent_vals or not older_vals:
            continue
        r_avg = sum(recent_vals) / len(recent_vals)
        o_avg = sum(older_vals) / len(older_vals)
        if r_avg < o_avg - 5:
            declining_dims.append({"dimension": label, "delta": round(r_avg - o_avg, 1)})

    # 自动分诊：按 改进潜力 × 使用频率 排序
    latest = records[-1]
    triage = []
    for dim_key, dim_info in DIMENSIONS.items():
        label = dim_info["label"]
        current = latest.get("scores", {}).get(label, 50)
        # 使用频率：该维度在最近记录中被触发（非满分即算有改进空间）的次数
        triggered = sum(
            1 for r in records if r.get("scores", {}).get(label, 100) < 100
        ) / len(records)
        potential = max(0, 100 - current) / 100
        priority = round(potential * triggered, 3)
        if priority > 0:
            triage.append({
                "dimension": label,
                "current_score": current,
                "potential": round(potential, 2),
                "frequency": round(triggered, 2),
                "priority": priority,
            })
    triage.sort(key=lambda x: x["priority"], reverse=True)

    # 连续退步告警
    if len(records) >= 3:
        last_3 = [r.get("composite", 0) for r in records[-3:]]
        if last_3[0] > last_3[1] > last_3[2]:
            return {
                "trend": "declining",
                "alert": "连续 3 个 Change 评分下降，建议运行进化分析",
                "declining_dimensions": declining_dims,
                "triage": triage[:5],
            }

    return {
        "trend": trend,
        "delta": round(delta, 1),
        "declining_dimensions": declining_dims,
        "triage": triage[:5],
    }

if __name__ == "__main__":
    main()
