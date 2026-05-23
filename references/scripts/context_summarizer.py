#!/usr/bin/env python3
"""上下文摘要生成器 — 从上游工件提取当前阶段所需上下文

用法：
  python3 context_summarizer.py --stage 3 --specs-dir .specs/<id>
  python3 context_summarizer.py --stage 3 --specs-dir .specs/<id> --skill-dir /path/to/flow-go

输入：
  - 各阶段上下文需求清单（从对应 stages/*.md 读取）
  - 上游工件文件（REQUIREMENT.md、DESIGN.md 等）

输出（stdout，Markdown 格式）：
  - 按当前阶段的上下文需求清单，仅提取必选字段
  - 关键决策保留原文
  - 描述性内容压缩为一行

退出码：0=成功，1=参数错误，2=上游工件缺失
"""

import argparse
import os
import re
import sys


STAGE_FILES = {
    0: "0-requirement.md",
    1: "1-design.md",
    2: "2-task.md",
    3: "3-develop.md",
    4: "4-test.md",
    5: "5-review.md",
    6: "6-deploy.md",
    7: "7-acceptance.md",
}

ARTIFACT_MAP = {
    "REQUIREMENT.md": "REQUIREMENT",
    "DESIGN.md": "DESIGN",
    "TASK.md": "TASK",
    "CHANGE.md": "CHANGE",
    "CONTEXT.md": "CONTEXT",
    "LESSONS.md": "LESSONS",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="上下文摘要生成器 — 从上游工件提取阶段所需上下文",
        prog="context_summarizer",
    )
    parser.add_argument("--stage", required=True, type=int, choices=range(8),
                        help="目标阶段编号 0-7（必选）")
    parser.add_argument("--specs-dir", required=True,
                        help="当前 Change 的 spec 目录（必选）")
    parser.add_argument("--skill-dir",
                        help="flow-go skill 根目录（可选，默认从脚本路径推断）")
    return parser.parse_args()


def read_file(path):
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()


def infer_skill_dir():
    from _path_utils import resolve_skill_dir
    return resolve_skill_dir()


def parse_requirements_table(stage_content):
    """从阶段指南中解析上下文需求清单表格"""
    section_m = re.search(
        r"##\s*上下文需求清单\n(.+?)(?=\n##|\Z)",
        stage_content, re.DOTALL,
    )
    if not section_m:
        return None

    requirements = []
    for line in section_m.group(1).strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("|") and "---" in line:
            continue
        if line.startswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 4 and cells[0] and not cells[0].startswith("来源"):
                requirements.append({
                    "source": cells[0],
                    "field": cells[1],
                    "required": cells[2],
                    "preserve": cells[3],
                })
    return requirements if requirements else None


def extract_section(content, section_name):
    """提取 Markdown 指定章节的内容"""
    pattern = re.compile(
        rf"##\s+{re.escape(section_name)}\n(.+?)(?=\n##|\Z)",
        re.DOTALL,
    )
    m = pattern.search(content)
    return m.group(1).strip() if m else None


def compress_content(content, max_lines=3):
    """压缩描述性内容为一行摘要"""
    lines = [l.strip() for l in content.split("\n") if l.strip() and not l.strip().startswith("|") and not l.strip().startswith("#")]
    if not lines:
        return ""
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return lines[0] + f" ...（共 {len(lines)} 行，已压缩）"


def generate_summary(requirements, specs_dir):
    """按需求清单从工件生成摘要"""
    lines = []
    specs_dir = os.path.abspath(specs_dir)

    source_artifacts = {}
    for req in requirements:
        src = req["source"]
        if src not in source_artifacts:
            for filename, key in ARTIFACT_MAP.items():
                if key == src or filename == src:
                    path = os.path.join(specs_dir, filename)
                    content = read_file(path)
                    if content is None and key == "CONTEXT":
                        context_path = os.path.join(os.path.dirname(specs_dir), "CONTEXT.md")
                        content = read_file(context_path)
                    if content is None and key == "LESSONS":
                        lessons_path = os.path.join(os.path.dirname(specs_dir), "LESSONS.md")
                        content = read_file(lessons_path)
                    source_artifacts[src] = content
                    break

    grouped = {}
    for req in requirements:
        src = req["source"]
        if src not in grouped:
            grouped[src] = []
        grouped[src].append(req)

    for src, reqs in grouped.items():
        content = source_artifacts.get(src)
        tag = "必选" if any(r["required"] in ("必选", "必填") for r in reqs) else "可选"
        if content is None:
            lines.append(f"### {src}（{tag}）\n")
            lines.append(f"- 工件缺失\n")
            continue

        lines.append(f"### {src}（{tag}）\n")
        for req in reqs:
            field = req["field"]
            preserve = req.get("preserve", "压缩")
            section_content = extract_section(content, field)
            if section_content:
                if preserve in ("完整保留", "原文", "保留原文"):
                    lines.append(f"- {field}：\n")
                    for line in section_content.split("\n"):
                        lines.append(f"  {line}")
                else:
                    compressed = compress_content(section_content)
                    lines.append(f"- {field}：{compressed}")
            else:
                lines.append(f"- {field}：（未找到对应章节）")

    return "\n".join(lines)


def generate_full_summary(stage_num, specs_dir):
    """无需求清单时，全文输出主要工件"""
    specs_dir = os.path.abspath(specs_dir)
    lines = [f"## 上下文摘要（{stage_num}-阶段）\n"]
    lines.append("> 未找到上下文需求清单，输出主要工件全文\n")

    artifacts = ["CHANGE.md", "REQUIREMENT.md", "DESIGN.md", "TASK.md"]
    for artifact in artifacts:
        content = read_file(os.path.join(specs_dir, artifact))
        if content:
            key = ARTIFACT_MAP.get(artifact, artifact)
            lines.append(f"\n### {key}\n")
            lines.append(content)

    return "\n".join(lines)


def main():
    args = parse_args()

    specs_dir = os.path.abspath(args.specs_dir)
    if not os.path.isdir(specs_dir):
        print(f"错误：spec 目录不存在 — {args.specs_dir}", file=sys.stderr)
        sys.exit(2)

    skill_dir = os.path.abspath(args.skill_dir) if args.skill_dir else infer_skill_dir()
    stage_file = os.path.join(skill_dir, "references", "stages", STAGE_FILES[args.stage])

    stage_content = read_file(stage_file)
    if stage_content is None:
        print(f"错误：阶段指南文件不存在 — {stage_file}", file=sys.stderr)
        sys.exit(2)

    requirements = parse_requirements_table(stage_content)

    if requirements:
        stage_names = {
            0: "0-需求", 1: "1-设计", 2: "2-任务", 3: "3-开发",
            4: "4-测试", 5: "5-审查", 6: "6-部署", 7: "7-验收",
        }
        header = f"## 上下文摘要（{stage_names[args.stage]}阶段）\n"
        summary = generate_summary(requirements, specs_dir)
        print(header)
        print(summary)
    else:
        print(generate_full_summary(args.stage, specs_dir))


if __name__ == "__main__":
    main()
