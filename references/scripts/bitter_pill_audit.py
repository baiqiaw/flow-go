#!/usr/bin/env python3
"""苦丸审计 — 扫描 flow-go skill 规则文本，分类 KEEP/REVIEW/CANDIDATE

用法：python3 bitter_pill_audit.py --skill-dir <path> [--output <path>] [--format text|json]

分类标准：
  KEEP: 角色红线、工件完整性、安全检查、数据一致性、跨角色协调
  REVIEW: 输出格式要求、分步执行顺序、特定措辞要求
  CANDIDATE: "不要忘记"/"务必注意"类提醒、重复覆盖的约束、高度具体的提示词措辞
"""
import argparse
import json
import os
import re
import sys


# KEEP 特征词：涉及角色红线、工件完整性、安全、数据一致性、跨角色协调
KEEP_PATTERNS = [
    r"禁止",
    r"红线",
    r"不得",
    r"不允许",
    r"必须.{0,10}(?:验证|检查|确认|存在)",
    r"角色.*红线",
    r"安全",
    r"数据一致",
    r"跨角色",
    r"闸门",
    r"HARD.GATE",
    r"工件.*完整",
    r"自检",
    r"中断恢复",
]

# REVIEW 特征词：输出格式、执行顺序、措辞要求
REVIEW_PATTERNS = [
    r"格式[：:]",
    r"输出.*格式",
    r"步骤\s*\d",
    r"第[一二三四五六七八九十]+步",
    r"模板",
    r"role.?declaration",
    r"角色声明",
    r"确保.*包含",
]

# CANDIDATE 特征词：提醒、重复、高度具体措辞
CANDIDATE_PATTERNS = [
    r"不要忘记",
    r"务必注意",
    r"请注意",
    r"千万(?:别|不要)",
    r"重要.*提醒",
    r"再次强调",
    r"特别(?:注意|提醒|说明)",
    r"绝对不能",
    r"务必确保",
]


def extract_rules(content):
    """从 Markdown 文本中提取规则条目"""
    rules = []
    lines = content.split("\n")

    for i, line in enumerate(lines):
        stripped = line.strip()

        # 列表项规则（- 或 * 开头）
        if re.match(r"^[-*]\s+", stripped):
            text = re.sub(r"^[-*]\s+", "", stripped)
            if len(text) > 5 and _is_rule_text(text):
                rules.append(text)

        # HARD-GATE 块内内容
        if "HARD-GATE" in stripped or "禁止" in stripped or "必须" in stripped:
            # 取当前行和后续 2 行作为上下文
            block = stripped
            for j in range(1, 3):
                if i + j < len(lines):
                    next_line = lines[i + j].strip()
                    if next_line and not next_line.startswith("#"):
                        block += " " + next_line
            if len(block) > 10 and block not in [r for r in rules]:
                rules.append(block)

    return rules


def _is_rule_text(text):
    """判断文本是否像规则指令（而非纯描述）"""
    indicators = ["必须", "禁止", "不得", "不允许", "确保", "验证",
                  "检查", "需要", "应当", "要 ", "不要", "务必",
                  "HARD-GATE", "闸门", "红线", "自检", "步骤"]
    return any(ind in text for ind in indicators)


def classify_rule(rule_text):
    """分类单条规则"""
    scores = {"keep": 0, "review": 0, "candidate": 0}

    for pattern in KEEP_PATTERNS:
        if re.search(pattern, rule_text):
            scores["keep"] += 1

    for pattern in REVIEW_PATTERNS:
        if re.search(pattern, rule_text):
            scores["review"] += 1

    for pattern in CANDIDATE_PATTERNS:
        if re.search(pattern, rule_text):
            scores["candidate"] += 1

    # 默认分类：无明确特征 → REVIEW（待人工判定）
    if max(scores.values()) == 0:
        return "REVIEW", "无明确分类特征，默认 REVIEW 待人工判定"

    best = max(scores, key=scores.get)
    category = best.upper()
    reason = f"匹配 {scores[best]} 条 {best} 特征词"

    return category, reason


def scan_skill_dir(skill_dir):
    """扫描 skill 目录下所有 Markdown 文件"""
    files_to_scan = []

    skill_md = os.path.join(skill_dir, "SKILL.md")
    if os.path.isfile(skill_md):
        files_to_scan.append(skill_md)

    refs_dir = os.path.join(skill_dir, "references")
    if os.path.isdir(refs_dir):
        for root, dirs, files in os.walk(refs_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in sorted(files):
                if f.endswith('.md'):
                    files_to_scan.append(os.path.join(root, f))

    return files_to_scan


def format_markdown(results, skill_dir="."):
    """格式化为 BITTER-PILL.md"""
    lines = ["# BITTER-PILL 审计报告\n"]
    lines.append("| 分类 | 规则文本 | 来源 | 判定理由 |")
    lines.append("|------|---------|------|---------|")

    keep = [r for r in results if r["category"] == "KEEP"]
    review = [r for r in results if r["category"] == "REVIEW"]
    candidate = [r for r in results if r["category"] == "CANDIDATE"]

    lines.append(f"\n**统计**：KEEP {len(keep)} | REVIEW {len(review)} | CANDIDATE {len(candidate)} | 总计 {len(results)}\n")

    for category_name, group in [("KEEP", keep), ("REVIEW", review), ("CANDIDATE", candidate)]:
        if not group:
            continue
        lines.append(f"\n## {category_name}\n")
        for r in group:
            text_short = r["text"][:80] + ("..." if len(r["text"]) > 80 else "")
            source = os.path.relpath(r["source"], skill_dir).replace(os.sep, "/")
            lines.append(f"- [{category_name}] `{text_short}`")
            lines.append(f"  - 来源: {source}")
            lines.append(f"  - 理由: {r['reason']}")

    return "\n".join(lines)


def format_text(results, skill_dir="."):
    """格式化为可读的纯文本报告"""
    keep = [r for r in results if r["category"] == "KEEP"]
    review = [r for r in results if r["category"] == "REVIEW"]
    candidate = [r for r in results if r["category"] == "CANDIDATE"]

    lines = []
    lines.append("=" * 60)
    lines.append("苦丸审计报告")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"KEEP     : {len(keep)}")
    lines.append(f"REVIEW   : {len(review)}")
    lines.append(f"CANDIDATE: {len(candidate)}")
    lines.append(f"总计     : {len(results)}")
    lines.append("")

    for category_name, group in [("KEEP", keep), ("REVIEW", review), ("CANDIDATE", candidate)]:
        if not group:
            continue
        lines.append("-" * 60)
        lines.append(f"{category_name} ({len(group)} 条)")
        lines.append("-" * 60)
        for i, r in enumerate(group, 1):
            source = os.path.relpath(r["source"], skill_dir).replace(os.sep, "/")
            lines.append(f"  [{i}] {r['text']}")
            lines.append(f"      来源: {source}")
            lines.append(f"      理由: {r['reason']}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="flow-go 苦丸审计")
    parser.add_argument("--skill-dir", default=None, help="flow-go skill 根目录（默认自动发现）")
    parser.add_argument("--output", help="输出路径（默认 stdout）")
    parser.add_argument("--format", choices=["text", "json", "markdown"], default="markdown",
                        help="输出格式：text（可读报告）或 json（结构化数据），默认 json")
    args = parser.parse_args()

    # 自动发现 skill 目录（优先用户显式指定）
    from _path_utils import resolve_skill_dir_for_audit
    skill_dir = args.skill_dir or resolve_skill_dir_for_audit()

    files = scan_skill_dir(skill_dir)
    all_results = []

    for filepath in files:
        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue

        rules = extract_rules(content)
        for rule in rules:
            category, reason = classify_rule(rule)
            all_results.append({
                "text": rule,
                "source": filepath,
                "category": category,
                "reason": reason,
            })

    if args.format == "json":
        output = json.dumps(all_results, ensure_ascii=False, indent=2)
    elif args.format == "text":
        output = format_text(all_results, skill_dir)
    else:
        # markdown（向后兼容）
        output = format_markdown(all_results, skill_dir)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
