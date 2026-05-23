#!/usr/bin/env python3
"""轨迹采集器 — 采集 Change 执行轨迹，生成 TRACE.md 和 traces.jsonl 记录

用法：
  python3 trace_collector.py --specs-dir .specs/<id> --change-id <id>
  python3 trace_collector.py --specs-dir .specs/<id> --change-id <id> \
    --health-score 7.8 --complexity STANDARD --path-mode full

输入：
  - STATE.md（项目根）
  - .specs/<id>/ 下所有工件
  - health-history.jsonl
  - CHANGE.md

输出：
  - TRACE.md（人类可读版）
  - traces.jsonl 追加一条记录

退出码：0=成功，1=参数错误，2=工件缺失
"""

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone


STAGE_NAMES = {
    0: ("0-需求", "产品经理"),
    1: ("1-设计", "技术经理"),
    2: ("2-任务", "项目经理"),
    3: ("3-开发", "开发员"),
    4: ("4-测试", "测试员"),
    5: ("5-审查", "技术经理"),
    6: ("6-部署", "运维"),
    7: ("7-验收", "产品经理+项目经理"),
}

STAGE_ARTIFACTS = {
    0: ("CHANGE.md", "REQUIREMENT.md"),
    1: ("DESIGN.md",),
    2: ("TASK.md",),
    3: ("*-SUMMARY.md",),
    4: ("TEST.md",),
    5: ("REVIEW.md",),
    6: ("DEPLOY.md",),
    7: ("UAT.md",),
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="轨迹采集器 — 采集 Change 执行轨迹",
        prog="trace_collector",
    )
    # 互斥模式：常规采集 vs outcome 检查
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--change-id", help="常规采集模式：Change-ID（必选）")
    mode.add_argument("--check-outcome", action="store_true", help="outcome 检查模式：扫描并更新 traces.jsonl 中 outcome 为 null 的记录")
    parser.add_argument("--specs-dir", required=True, help="spec 目录路径（必选）")
    parser.add_argument("--health-score", type=float, help="健康评分（可选，默认从 health-history.jsonl 读取）")
    parser.add_argument("--complexity", choices=["LITE", "STANDARD", "HEAVY"], help="复杂度（可选，默认从 CHANGE.md 推断）")
    parser.add_argument("--path-mode", choices=["full", "incremental", "shortest"], default="full", help="路径模式（可选，默认 full）")
    parser.add_argument("--tags", help="额外标签 JSON（可选，如 {\"change_type\":\"feature\"}）")
    parser.add_argument("--output-trace", help="TRACE.md 输出路径（可选，默认 <specs-dir>/TRACE.md）")
    parser.add_argument("--output-jsonl", help="traces.jsonl 路径（可选，默认 <specs-dir>/../traces.jsonl）")
    parser.add_argument("--outcome-days", type=int, default=7, help="outcome 自动检测窗口天数（可选，默认 7）")
    return parser.parse_args()


def read_file(path):
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()


def _project_root(specs_dir):
    from _path_utils import resolve_project_root
    return resolve_project_root(specs_dir)


def read_state(specs_dir):
    """从 .specs/<id>/STATE.md 读取 change 级详细状态"""
    change_state_path = os.path.join(specs_dir, "STATE.md")
    content = read_file(change_state_path)
    if not content:
        return None
    info = {}
    for field in ["当前阶段", "当前任务", "阶段进度"]:
        m = re.search(rf"## {re.escape(field)}\s*\n-?\s*(.+)", content)
        if m:
            info[field] = m.group(1).strip()
    return info


def derive_path(specs_dir, path_mode):
    completed = set()
    for stage, patterns in STAGE_ARTIFACTS.items():
        for pattern in patterns:
            if pattern.startswith("*"):
                matches = glob.glob(os.path.join(specs_dir, pattern))
                if matches:
                    completed.add(stage)
            else:
                if os.path.isfile(os.path.join(specs_dir, pattern)):
                    completed.add(stage)
    if path_mode == "full":
        return list(range(8))
    return sorted(completed)


STAGE_TYPE_MAP = {0: "scope", 1: "architecture", 2: "task"}


def parse_frontmatter_stage(content):
    fm = re.search(r"^---\n(.+?)\n---", content, re.DOTALL)
    if fm:
        stage_m = re.search(r"stage:\s*(\d+)", fm.group(1))
        if stage_m:
            return int(stage_m.group(1))
    return None


def extract_decisions(specs_dir):
    decisions = []
    review_files = glob.glob(os.path.join(specs_dir, "*REVIEW.md"))
    for rf in review_files:
        content = read_file(rf)
        if not content:
            continue
        stage = parse_frontmatter_stage(content)
        if stage is None:
            if "需求" in content or "REQUIREMENT" in content:
                stage = 0
            elif "设计" in content or "DESIGN" in content:
                stage = 1
            elif "任务" in content or "TASK" in content:
                stage = 2
            else:
                stage = None
        fix_section = re.search(r"修复记录\n(.+?)(?=\n---|\n##|\Z)", content, re.DOTALL)
        if fix_section:
            for fm in re.finditer(r"\d+\.\s+(.+?)(?:\n|$)", fix_section.group(1)):
                decisions.append({"stage": stage, "summary": fm.group(1).strip()[:100], "type": "review_fix"})
    artifact_stages = {"CHANGE.md": 0, "REQUIREMENT.md": 0, "DESIGN.md": 1, "TASK.md": 2}
    for artifact, stage in artifact_stages.items():
        content = read_file(os.path.join(specs_dir, artifact))
        if not content:
            continue
        fm_stage = parse_frontmatter_stage(content)
        effective_stage = fm_stage if fm_stage is not None else stage
        for section_name in ["Key Decisions", "Principles", "原则", "关键决策", "ADR"]:
            section_m = re.search(rf"##\s+{section_name}\n(.+?)(?=\n##|\Z)", content, re.DOTALL)
            if section_m:
                for b in re.findall(r"[-*]\s+(.+?)(?:\n|$)", section_m.group(1))[:3]:
                    decisions.append({
                        "stage": effective_stage,
                        "summary": b.strip()[:100],
                        "type": STAGE_TYPE_MAP.get(effective_stage, "implementation"),
                    })
                break
    return decisions


def extract_gate_blocks(specs_dir):
    blocks = {}
    review_files = glob.glob(os.path.join(specs_dir, "*REVIEW.md"))
    for rf in review_files:
        content = read_file(rf)
        if not content:
            continue
        stage = parse_frontmatter_stage(content)
        if stage is None:
            if "需求" in content:
                stage = 0
            elif "设计" in content:
                stage = 1
            elif "任务" in content:
                stage = 2
            else:
                continue
        rounds_m = re.search(r"评审轮次[：:]\s*(\d+)", content)
        rounds = int(rounds_m.group(1)) if rounds_m else 1
        blocks[str(stage)] = rounds - 1
    for i in range(8):
        if str(i) not in blocks:
            blocks[str(i)] = 0
    return blocks


def read_health_history(specs_dir):
    project_root = _project_root(specs_dir)
    content = read_file(os.path.join(project_root, "health-history.jsonl"))
    if not content:
        return None
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    if not lines:
        return None
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return None


def infer_complexity(specs_dir):
    content = read_file(os.path.join(specs_dir, "CHANGE.md"))
    if not content:
        return "STANDARD"
    file_count = len(re.findall(r"\.py|\.md|\.js|\.ts", content))
    if file_count > 10:
        return "HEAVY"
    if file_count <= 3:
        return "LITE"
    return "STANDARD"


def count_files(specs_dir):
    total = 0
    for _, _, files in os.walk(specs_dir):
        total += len(files)
    return total


def generate_trace_md(change_id, state_info, decisions, health_info, tags, complexity, path, gate_blocks):
    lines = [f"# TRACE — {change_id}\n"]
    lines.append("## 阶段流转\n")
    lines.append("| 阶段 | 角色 | 关键决策 | 闸门阻断 | 耗时估算 |")
    lines.append("|------|------|---------|---------|---------|")
    for stage_num in path:
        stage_name, role = STAGE_NAMES.get(stage_num, (f"{stage_num}-未知", "未知"))
        stage_decisions = [d for d in decisions if d.get("stage") == stage_num]
        summary = "; ".join(d["summary"][:50] for d in stage_decisions[:2]) or "—"
        block = gate_blocks.get(str(stage_num), 0)
        lines.append(f"| {stage_name} | {role} | {summary} | {block} | — |")
    lines.append("\n## 健康评分\n")
    if health_info:
        lines.append(f"- 总分：{health_info.get('composite', 'N/A')}/10")
        for dim, score in health_info.get("scores", {}).items():
            lines.append(f"  - {dim}: {score}")
    else:
        lines.append("- 总分：N/A（无历史评分）")
    lines.append("\n## 标签\n")
    lines.append(f"- 变更类型：{tags.get('change_type', 'unknown')}")
    lines.append(f"- 复杂度：{complexity}")
    lines.append(f"- 阶段瓶颈：{tags.get('bottleneck_stage') or 'null'}")
    lines.append(f"- 回溯次数：{tags.get('rollback_count', 0)}")
    lines.append(f"- 涉及文件数：{tags.get('files_touched', 0)}")
    lines.append(f"- 跨子系统：{'是' if tags.get('cross_subsystem') else '否'}")
    lines.append("\n## 实际结果\n")
    lines.append("- outcome：null")
    lines.append("- 检测时间：待标记")
    if state_info:
        lines.append(f"\n## 状态快照\n")
        lines.append(f"- 当前阶段：{state_info.get('当前阶段', 'N/A')}")
        lines.append(f"- 阶段进度：{state_info.get('阶段进度', 'N/A')}")
    return "\n".join(lines)


def main():
    args = parse_args()

    # outcome 检查模式
    if args.check_outcome:
        specs_dir = os.path.abspath(args.specs_dir)
        jsonl_path = args.output_jsonl or os.path.join(specs_dir, "traces.jsonl")
        check_outcome(specs_dir, args.outcome_days, jsonl_path)
        return

    # 常规采集模式
    specs_dir = os.path.abspath(args.specs_dir)
    if not os.path.isdir(specs_dir):
        print(f"错误：spec 目录不存在 — {args.specs_dir}", file=sys.stderr)
        sys.exit(2)

    state_info = read_state(specs_dir)
    decisions = extract_decisions(specs_dir)
    health_info = read_health_history(specs_dir)
    health_score = args.health_score
    if health_score is None and health_info:
        health_score = health_info.get("composite")

    complexity = args.complexity or infer_complexity(specs_dir)
    gate_blocks = extract_gate_blocks(specs_dir)
    path = derive_path(specs_dir, args.path_mode)
    files_touched = count_files(specs_dir)

    tags = {
        "change_type": "feature",
        "complexity": complexity,
        "bottleneck_stage": None,
        "rollback_count": 0,
        "files_touched": files_touched,
        "cross_subsystem": files_touched > 3,
    }
    if args.tags:
        try:
            tags.update(json.loads(args.tags))
        except json.JSONDecodeError:
            print("错误：--tags 参数不是合法 JSON", file=sys.stderr)
            sys.exit(1)

    health_dimensions = {}
    if health_info and "scores" in health_info:
        for dim, score in health_info["scores"].items():
            health_dimensions[dim] = round(score / 100, 2) if score > 1 else score

    record = {
        "change_id": args.change_id,
        "timestamp": datetime.now().astimezone().isoformat(),
        "path": path,
        "path_mode": args.path_mode,
        "complexity": complexity,
        "decisions": decisions,
        "gate_blocks": gate_blocks,
        "health_score": health_score,
        "health_dimensions": health_dimensions,
        "manual_interventions": 0,
        "files_touched": files_touched,
        "tags": tags,
        "outcome": None,
        "outcome_timestamp": None,
    }

    trace_path = args.output_trace or os.path.join(specs_dir, "TRACE.md")
    trace_content = generate_trace_md(args.change_id, state_info, decisions, health_info, tags, complexity, path, gate_blocks)
    with open(trace_path, "w", encoding="utf-8") as f:
        f.write(trace_content)

    jsonl_path = args.output_jsonl or os.path.join(os.path.dirname(specs_dir), "traces.jsonl")
    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"轨迹已采集：{args.change_id}")
    print(f"  TRACE.md → {trace_path}")
    print(f"  traces.jsonl → {jsonl_path}")


def check_outcome(specs_dir, outcome_days, jsonl_path):
    """扫描 traces.jsonl 中 outcome==null 的记录，检查并更新 outcome"""
    archive_dir = os.path.join(specs_dir, "archive")

    if not os.path.isfile(jsonl_path):
        print("traces.jsonl 不存在，无需检查", file=sys.stderr)
        return

    with open(jsonl_path, encoding="utf-8") as f:
        lines = f.readlines()

    updated = 0
    now = datetime.now(timezone.utc)
    new_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            new_lines.append(line + "\n")
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            new_lines.append(line + "\n")
            continue

        if record.get("outcome") is not None:
            new_lines.append(line + "\n")
            continue

        change_id = record.get("change_id", "")
        outcome = None

        # 检查 archive 目录
        if os.path.isdir(archive_dir):
            for entry in os.listdir(archive_dir):
                entry_path = os.path.join(archive_dir, entry)
                if not os.path.isdir(entry_path):
                    continue
                # 检查 ABANDONED.md
                if os.path.isfile(os.path.join(entry_path, "ABANDONED.md")):
                    content = read_file(os.path.join(entry_path, "ABANDONED.md")) or ""
                    if change_id in content:
                        outcome = "abandoned"
                        break
                # 检查 CHANGE.md 是否引用该 change-id（热修标记）
                for root, _, files in os.walk(entry_path):
                    for fn in files:
                        if fn == "CHANGE.md":
                            c = read_file(os.path.join(root, fn)) or ""
                            if "热修" in c or "hotfix" in c.lower():
                                if change_id in c:
                                    outcome = "hotfixed"
                                    break
                    if outcome:
                        break
                if outcome:
                    break

        # 无引用且超时 → success
        if outcome is None:
            ts_str = record.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_str)
                if (now - ts).days > outcome_days:
                    outcome = "success"
            except (ValueError, TypeError):
                pass

        if outcome:
            record["outcome"] = outcome
            record["outcome_timestamp"] = now.isoformat()
            new_lines.append(json.dumps(record, ensure_ascii=False) + "\n")
            updated += 1
            print(f"  {change_id} → {outcome}")
        else:
            new_lines.append(line + "\n")

    with open(jsonl_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"outcome 检查完成：{updated} 条已更新")


if __name__ == "__main__":
    main()
