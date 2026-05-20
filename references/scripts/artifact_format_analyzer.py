#!/usr/bin/env python3
"""工件格式分析器 — 解析 artifact 模板字段，交叉对比 stages 中的引用，输出 token 效率报告

用法：
  python3 artifact_format_analyzer.py --skill-dir <flow-go skill 目录> [--format json|text]

输入：
  - references/artifacts/*.md（工件模板文件）
  - references/stages/*.md（阶段指南，用于交叉引用字段使用情况）

输出（JSON 到 stdout）：
  templates / summary / suggestions
"""
import argparse
import json
import os
import re
import sys


ARTIFACT_DIR = "references/artifacts"
STAGE_DIR = "references/stages"

TEMPLATE_SECTIONS_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
TEMPLATE_FIELD_RE = re.compile(
    r"^\|\s*([^|]+)\s*\|", re.MULTILINE
)
ARTIFACT_NAME_RE = re.compile(r"^##\s+.*?(\S+\.md)", re.MULTILINE)


def parse_template_fields(filepath):
    """解析工件模板文件，提取各工件的字段定义"""
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    templates = {}
    current_artifact = None
    fields = []

    in_code_block = False
    for line in content.split("\n"):
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            if current_artifact:
                # 在代码块内提取字段：标题行、表格行、章节标题
                heading = re.match(r"^###?\s+(.+)$", stripped)
                if heading:
                    fields.append(heading.group(1).strip())
                elif stripped.startswith("|") and not re.match(
                    r"^\|\s*[-:]+", stripped
                ):
                    cells = [c.strip() for c in stripped.split("|")[1:-1]]
                    if cells:
                        field_name = cells[0]
                        if field_name and field_name not in ("字段", "维度", "#"):
                            fields.append(field_name)
                elif stripped.startswith("- [") or stripped.startswith("- "):
                    check_text = stripped.lstrip("- [ ]x").strip()
                    if check_text:
                        fields.append(check_text)
            continue

        # 在代码块外寻找工件名（## xxx.md 格式）
        artifact_match = re.match(r"^##\s+.*?(\w+\.md)", stripped)
        if artifact_match:
            if current_artifact and fields:
                templates[current_artifact] = fields
            current_artifact = artifact_match.group(1)
            fields = []
            continue

    if current_artifact and fields:
        templates[current_artifact] = fields

    return templates, content


def scan_stage_references(stage_dir):
    """扫描 stages/*.md，收集字段引用"""
    references = {}
    if not os.path.isdir(stage_dir):
        return references

    for fname in sorted(os.listdir(stage_dir)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(stage_dir, fname)
        with open(fpath, encoding="utf-8") as f:
            content = f.read()
        references[fname] = content

    return references


def check_field_referenced(field_name, stage_contents):
    """检查字段名是否在任一 stage 文件中被引用"""
    normalized = field_name.lower().strip()
    # 跳过通用词
    skip = {"字段", "说明", "状态", "必填", "格式", "默认值"}
    if normalized in skip:
        return True

    for content in stage_contents.values():
        if normalized in content.lower():
            return True
        # 也检查不带括号/标点的核心词
        core = re.sub(r"[（）()<>《》【】\[\]{}]", "", normalized).strip()
        if core and len(core) >= 2 and core in content.lower():
            return True
    return False


def find_redundancy(artifact_templates):
    """找出跨工件的语义重叠"""
    redundancies = []
    artifact_names = list(artifact_templates.keys())

    for i in range(len(artifact_names)):
        for j in range(i + 1, len(artifact_names)):
            a_name = artifact_names[i]
            b_name = artifact_names[j]
            a_fields = set(f.lower() for f in artifact_templates[a_name])
            b_fields = set(f.lower() for f in artifact_templates[b_name])
            overlap = a_fields & b_fields
            if overlap:
                redundancies.append({
                    "artifacts": [a_name, b_name],
                    "overlap_count": len(overlap),
                    "examples": list(overlap)[:3],
                })

    return redundancies


def compute_token_efficiency(template_content):
    """计算模板文件的 token 效率（信息行数 / 总行数）"""
    lines = template_content.split("\n")
    total = len([l for l in lines if l.strip()])
    if total == 0:
        return 0.0
    # 信息行：非空、非纯分隔符、非代码围栏
    info = 0
    in_code = False
    for line in lines:
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if not s or s in ("---", "***"):
            continue
        if re.match(r"^\|[-:\s|]+$", s):
            continue
        info += 1
    return round(info / total, 2) if total else 0.0


def analyze_templates(artifact_dir, stage_dir):
    """分析所有工件模板"""
    templates_report = []
    all_stage_content = scan_stage_references(stage_dir)
    all_templates = {}
    all_contents = {}

    if not os.path.isdir(artifact_dir):
        return templates_report, all_templates

    for fname in sorted(os.listdir(artifact_dir)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(artifact_dir, fname)
        artifact_fields, content = parse_template_fields(fpath)
        all_contents[fname] = content

        for artifact_name, fields in artifact_fields.items():
            all_templates[artifact_name] = fields
            unused = []
            for field in fields:
                if not check_field_referenced(field, all_stage_content):
                    unused.append(field)

            total_fields = len(fields)
            used_downstream = total_fields - len(unused)
            efficiency = round(used_downstream / total_fields, 2) if total_fields else 0.0

            suggestions = []
            if unused:
                suggestions.append(
                    f"{artifact_name} 有 {len(unused)} 个字段未被下游阶段引用"
                )

            templates_report.append({
                "file": fname,
                "artifact": artifact_name,
                "total_fields": total_fields,
                "used_downstream": used_downstream,
                "unused_fields": unused[:10],
                "token_efficiency": compute_token_efficiency(content),
                "suggestions": suggestions,
            })

    return templates_report, all_templates


def main():
    parser = argparse.ArgumentParser(
        description="工件格式分析器 — 解析模板字段并交叉对比下游引用"
    )
    parser.add_argument(
        "--skill-dir",
        required=True,
        help="flow-go skill 根目录（含 references/ 子目录）",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="输出格式（默认 json）",
    )
    args = parser.parse_args()

    artifact_dir = os.path.join(args.skill_dir, ARTIFACT_DIR)
    stage_dir = os.path.join(args.skill_dir, STAGE_DIR)

    if not os.path.isdir(artifact_dir):
        print(f"错误：工件目录不存在 — {artifact_dir}", file=sys.stderr)
        sys.exit(1)

    templates_report, all_templates = analyze_templates(artifact_dir, stage_dir)
    redundancies = find_redundancy(all_templates)

    total = len(templates_report)
    avg_efficiency = (
        round(sum(t["token_efficiency"] for t in templates_report) / total, 2)
        if total
        else 0.0
    )

    top_redundancy = ""
    if redundancies:
        redundancies.sort(key=lambda r: r["overlap_count"], reverse=True)
        top = redundancies[0]
        top_redundancy = (
            f"{top['artifacts'][0]} vs {top['artifacts'][1]} "
            f"({top['overlap_count']} 个重叠字段)"
        )

    report = {
        "templates": templates_report,
        "redundancies": redundancies,
        "summary": {
            "total_templates": total,
            "avg_efficiency": avg_efficiency,
            "top_redundancy": top_redundancy,
        },
    }

    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("== 工件格式分析报告 ==")
        print(f"模板总数：{total}")
        print(f"平均 token 效率：{avg_efficiency}")
        if top_redundancy:
            print(f"最大冗余：{top_redundancy}")
        print()
        for t in templates_report:
            print(f"--- {t['artifact']}（{t['file']}）---")
            print(f"  字段数：{t['total_fields']}，下游引用：{t['used_downstream']}")
            print(f"  token 效率：{t['token_efficiency']}")
            if t["unused_fields"]:
                print(f"  未引用字段：{', '.join(t['unused_fields'][:5])}")
            if t["suggestions"]:
                for s in t["suggestions"]:
                    print(f"  建议：{s}")
            print()


if __name__ == "__main__":
    main()
