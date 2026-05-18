#!/usr/bin/env python3
"""复杂度分级器 — 多信号综合判定 flow-go 任务复杂度级别（LITE/STANDARD/HEAVY）

用法：python3 complexity_classifier.py --description <text> --project-dir <path> [--specs-dir <path>]

信号来源：
  1. 关键词扫描（description 中的 LITE/HEAVY 特征词）
  2. 项目结构分析（涉及目录数量）
  3. 已有工件分析（REQUIREMENT.md 的 AC 条数）
  4. 类型推断（bugfix/doc → LITE，refactor → HEAVY）

判定规则：
  HEAVY总分 ≥ 0.4 → HEAVY
  LITE总分 ≥ 0.5 且 HEAVY总分 < 0.4 → LITE
  其余 → STANDARD
  confidence < 0.5 → 标记低置信度
"""
import argparse
import json
import os
import re
import sys


LITE_KEYWORDS = [
    ("typo", 0.3), ("修正", 0.3), ("拼写", 0.3), ("配置调整", 0.3),
    ("文档更新", 0.3), ("命名", 0.3), ("单行", 0.3), ("readme", 0.3),
    ("注释", 0.3), ("格式化", 0.3),
]

HEAVY_KEYWORDS = [
    ("重构", 0.4), ("架构", 0.4), ("跨模块", 0.4), ("重写", 0.4),
    ("迁移", 0.4), ("数据库变更", 0.4), ("API变更", 0.4), ("api变更", 0.4),
]

BUGFIX_WORDS = ["fix", "bug", "hotfix", "patch", "修复", "修正", "修"]
DOC_WORDS = ["文档", "doc", "readme", "注释", "comment", "说明"]
REFACTOR_WORDS = ["重构", "refactor", "重写", "rewrite", "迁移", "migrate"]


def scan_keywords(description):
    """信号 1：关键词扫描"""
    signals = []
    lite = 0.0
    heavy = 0.0
    desc_lower = description.lower()
    for kw, w in LITE_KEYWORDS:
        if kw.lower() in desc_lower:
            lite += w
            signals.append({"type": "keyword", "value": kw, "weight": w})
    for kw, w in HEAVY_KEYWORDS:
        if kw.lower() in desc_lower:
            heavy += w
            signals.append({"type": "keyword", "value": kw, "weight": w})
    return lite, heavy, signals


def analyze_project_structure(project_dir):
    """信号 2：项目结构分析"""
    signals = []
    heavy = 0.0
    dir_count = 0
    try:
        for entry in os.listdir(project_dir):
            if os.path.isdir(os.path.join(project_dir, entry)) and not entry.startswith('.'):
                dir_count += 1
    except OSError:
        return 0.0, signals
    if dir_count > 10:
        heavy += 0.2
        signals.append({"type": "project_structure", "value": f"{dir_count} directories", "weight": 0.2})
    return heavy, signals


def analyze_artifacts(specs_dir):
    """信号 3：工件分析"""
    signals = []
    heavy = 0.0
    if not specs_dir:
        return 0.0, signals
    req_path = os.path.join(specs_dir, "REQUIREMENT.md")
    if not os.path.isfile(req_path):
        return 0.0, signals
    try:
        with open(req_path, encoding="utf-8") as f:
            content = f.read()
        ac_count = len(re.findall(r'^\s*[-*]\s+AC-', content, re.MULTILINE))
        if ac_count > 5:
            heavy += 0.2
            signals.append({"type": "artifact", "value": f"{ac_count} ACs", "weight": 0.2})
    except OSError:
        pass
    return heavy, signals


def infer_type(description):
    """信号 4：类型推断"""
    signals = []
    lite = 0.0
    heavy = 0.0
    desc_lower = description.lower()

    for w in BUGFIX_WORDS:
        if w in desc_lower:
            lite += 0.3
            signals.append({"type": "type_inference", "value": f"bugfix indicator: {w}", "weight": 0.3})
            break
    for w in DOC_WORDS:
        if w in desc_lower:
            lite += 0.3
            signals.append({"type": "type_inference", "value": f"doc indicator: {w}", "weight": 0.3})
            break
    for w in REFACTOR_WORDS:
        if w in desc_lower:
            heavy += 0.3
            signals.append({"type": "type_inference", "value": f"refactor indicator: {w}", "weight": 0.3})
            break

    return lite, heavy, signals


def classify(description, project_dir, specs_dir=None):
    lite_total = 0.0
    heavy_total = 0.0
    all_signals = []

    l1, h1, s1 = scan_keywords(description)
    lite_total += l1
    heavy_total += h1
    all_signals.extend(s1)

    h2, s2 = analyze_project_structure(project_dir)
    heavy_total += h2
    all_signals.extend(s2)

    h3, s3 = analyze_artifacts(specs_dir)
    heavy_total += h3
    all_signals.extend(s3)

    l4, h4, s4 = infer_type(description)
    lite_total += l4
    heavy_total += h4
    all_signals.extend(s4)

    # 判定
    if heavy_total >= 0.4:
        level = "heavy"
    elif lite_total >= 0.5 and heavy_total < 0.4:
        level = "lite"
    else:
        level = "standard"

    confidence = round(min(max(lite_total, heavy_total), 1.0), 2)

    parts = []
    if lite_total > 0:
        parts.append(f"LITE 信号总分 {lite_total:.1f}")
    if heavy_total > 0:
        parts.append(f"HEAVY 信号总分 {heavy_total:.1f}")
    if parts:
        reasoning = f"检测到 {', '.join(parts)} → {level.upper()}"
    else:
        reasoning = "未检测到 LITE/HEAVY 特征信号 → STANDARD"

    return {
        "level": level,
        "confidence": confidence,
        "signals": all_signals,
        "reasoning": reasoning,
    }


def main():
    parser = argparse.ArgumentParser(description="flow-go 复杂度分级器")
    parser.add_argument("--description", required=True, help="用户对任务的描述文本")
    parser.add_argument("--project-dir", required=True, help="项目根目录")
    parser.add_argument("--specs-dir", help=".specs/<change-id> 路径（可选）")
    args = parser.parse_args()

    result = classify(args.description, args.project_dir, args.specs_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
