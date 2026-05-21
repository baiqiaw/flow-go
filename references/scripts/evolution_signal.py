#!/usr/bin/env python3
"""进化信号检测器 — 从 flow-go 工件自动提取强/中信号

借鉴进化引擎 signal_detector.py 的强/中信号分级 + Cheap Gate 机制。
从 SUMMARY.md / TEST.md / REVIEW.md / PROGRESS.md / STATE.md / LESSONS.md 提取信号，
至少 1 个强信号或 2 个中信号才值得进入反思环节。

用法：
    python3 evolution_signal.py --specs-dir .specs/<change-id>
    python3 evolution_signal.py --specs-dir .specs/<change-id> --format text
    python3 evolution_signal.py --specs-dir .specs/<change-id> --traces .specs/traces.jsonl
    python3 evolution_signal.py --specs-dir .specs/<change-id> --output .specs/evolution/<change-id>-signals.json
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


# ── 信号定义 ──────────────────────────────────────────────

STRONG_SIGNALS = {
    "review_rework": "交叉评审 2+ 轮才通过",
    "test_repeated": "测试阶段同一 bug 反复出现",
    "hotfix_trigger": "触发热修流程",
    "user_correction": "用户明确纠正了输出或行为",
    "gate_blocked": "闸门检查未通过，被阻断",
    "gate_blocked_trace": "Trace 记录显示闸门被阻断",
}

MEDIUM_SIGNALS = {
    "similar_error": "同类错误在 LESSONS.md 已有记录但再次出现",
    "role_violation": "跨越角色红线",
    "blast_radius": "blast radius check 触发（>5 文件）",
    "tool_pitfall": "工具/环境有值得长期记住的坑点",
}

# ── 归因标签（借鉴进化引擎归因分析）───────────────────────────
# 颜色：🔴严重  🟡中等  🟠轻度  🟢正常
# 归因 → 说明：为什么会出这个问题，下次怎么避免

ATTRIBUTIONS = {
    "review_rework": {
        "tag": "🔴 验证不足",
        "reason": "交叉评审反复未通过，说明自检步骤不够严格",
        "advice": "下次开发阶段增加 verify 命令自检，交叉评审前自查清单",
    },
    "test_repeated": {
        "tag": "🔴 太急躁",
        "reason": "测试反复失败，说明开发时想一步到位，验证不充分",
        "advice": "下次开发采用 TDD 红绿环，每步 verify 再继续",
    },
    "hotfix_trigger": {
        "tag": "🔴 验证不足",
        "reason": "问题泄漏到生产，说明测试阶段覆盖不全",
        "advice": "下次测试阶段补充边界用例，检查 AC 覆盖率",
    },
    "user_correction": {
        "tag": "🟡 方法不对路",
        "reason": "用户纠正说明流程输出与期望不匹配",
        "advice": "下次关键节点增加确认步骤，对齐期望再继续",
    },
    "gate_blocked": {
        "tag": "🟠 过度谨慎",
        "reason": "闸门阻断说明前置条件定义可能过严或工件格式不匹配",
        "advice": "检查闸门条件是否需要调整，或工件模板是否已更新",
    },
    "gate_blocked_trace": {
        "tag": "🟠 过度谨慎",
        "reason": "Trace 数据显示闸门被阻断，说明前置条件或工件质量存在问题",
        "advice": "检查 trace 中阻断的阶段，分析根因并修复",
    },
    "similar_error": {
        "tag": "🟡 思路太单一",
        "reason": "同类错误重复出现，说明 LESSONS 检索或提示不够",
        "advice": "下次开发前主动 grep LESSONS 相关关键词，参考历史教训",
    },
    "role_violation": {
        "tag": "🟡 方法不对路",
        "reason": "角色越界说明红线提醒时机或强度不够",
        "advice": "下次进入新角色时重新阅读角色红线",
    },
    "blast_radius": {
        "tag": "🟡 工具没用好",
        "reason": "单任务改动过多文件，说明任务拆分粒度过大",
        "advice": "下次任务拆分时控制 max_files_per_task",
    },
    "tool_pitfall": {
        "tag": "🟡 工具没用好",
        "reason": "工具/环境存在值得记录的坑点",
        "advice": "记录到 LESSONS.md 并标记触发关键词",
    },
}

# 关键词模式（借鉴 signal_detector.py 的 _CORRECTION_PATTERNS 等）
_CORRECTION_PATTERNS = ["不对", "改一下", "应该是", "我说的是", "你错了", "不是这个"]


# ── 信号提取器 ────────────────────────────────────────────

def _read_file(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return ""


def _extract_review_rework(specs_dir):
    """从 SUMMARY.md 交叉评审章节提取评审轮数"""
    content = _read_file(Path(specs_dir) / "SUMMARY.md")
    if not content:
        return []
    # 匹配"交叉评审" + "轮" 或 "round"
    round_matches = re.findall(r'(?:交叉评审|cross.?review).*?(\d+)\s*(?:轮|round)', content, re.I | re.S)
    if not round_matches:
        # 备选：匹配"第 N 轮"
        round_matches = re.findall(r'第\s*(\d+)\s*轮', content)
    evidence = []
    for r in round_matches:
        if int(r) >= 2:
            evidence.append(f"交叉评审经过 {r} 轮")
    if not evidence and ("交叉评审" in content or "cross_review" in content.lower()):
        # 默认至少检查了一次
        pass
    return evidence


def _extract_test_repeated(specs_dir):
    """从 TEST.md 提取反复出现的 bug"""
    content = _read_file(Path(specs_dir) / "TEST.md")
    if not content:
        return []
    evidence = []
    # 查找 bug 报告中的 rounds/重试次数
    bug_blocks = re.findall(r'(?:###?\s*(?:Bug|bug|缺陷).*?)(?=\n###?\s*(?:Bug|bug|缺陷)|\Z)', content, re.S)
    for block in bug_blocks:
        rounds = re.search(r'(?:轮次|rounds?|重试)\s*[:：]?\s*(\d+)', block, re.I)
        if rounds and int(rounds.group(1)) >= 2:
            title = block.split('\n')[0][:60]
            evidence.append(f"Bug 反复出现: {title}")
    return evidence[:3]


def _extract_hotfix(specs_dir):
    """从 STATE.md 检测热修标记"""
    # STATE.md 在项目根目录，specs_dir 是 .specs/<id>，向上一级
    state_path = Path(specs_dir).parent.parent / "STATE.md"
    content = _read_file(state_path)
    if not content:
        return []
    if re.search(r'(?:热修|hotfix|紧急修复)', content, re.I):
        return ["STATE.md 包含热修标记"]
    return []


def _extract_gate_blocked(specs_dir):
    """从 PROGRESS.md 提取闸门阻断记录"""
    content = ""
    for f in Path(specs_dir).glob("*-PROGRESS.md"):
        content += _read_file(f)
    if not content:
        return []
    evidence = []
    if re.search(r'(?:闸门|gate|blocked|阻断|未通过)', content, re.I):
        matches = re.findall(r'.*(?:闸门|gate|blocked|阻断|未通过).*', content, re.I)
        evidence.extend(matches[:3])
    return evidence


def _read_traces(traces_path, change_id):
    """从 traces.jsonl 读取指定 change_id 的 gate_blocks"""
    try:
        with open(traces_path, encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
    except (FileNotFoundError, OSError):
        return None
    for line in reversed(lines):
        try:
            record = json.loads(line)
            if record.get("change_id") == change_id:
                return record.get("gate_blocks", {})
        except json.JSONDecodeError:
            continue
    return None


def _extract_gate_blocked_trace(specs_dir, traces_path=None):
    """从 traces.jsonl 提取闸门阻断信号（结构化数据优先）"""
    if traces_path is None:
        return []
    change_id = Path(specs_dir).name
    gate_blocks = _read_traces(traces_path, change_id)
    if gate_blocks is None:
        print(f"警告：traces.jsonl 读取失败或无 {change_id} 记录，跳过 trace 信号", file=sys.stderr)
        return []
    evidence = []
    for stage, count in gate_blocks.items():
        if isinstance(count, int) and count > 0:
            evidence.append(f"阶段 {stage} 阻断 {count} 次")
    return evidence


def _extract_similar_error(specs_dir):
    """检查 TEST.md 中的错误是否在 LESSONS.md 已有记录"""
    test_content = _read_file(Path(specs_dir) / "TEST.md")
    lessons_content = _read_file(Path(specs_dir).parent / "LESSONS.md")
    if not test_content or not lessons_content:
        return []
    evidence = []
    # 提取 LESSONS 中的触发关键词
    keywords = re.findall(r'\*\*触发关键词\*\*[：:]\s*(.+)', lessons_content)
    all_kw = []
    for kw_line in keywords:
        all_kw.extend(k.strip() for k in kw_line.split("/") if k.strip())
    # 检查 TEST.md 是否包含这些关键词
    for kw in all_kw:
        if kw.lower() in test_content.lower():
            evidence.append(f"TEST.md 包含 LESSONS 已有教训关键词: {kw}")
    return evidence[:3]


def _extract_role_violation(specs_dir):
    """从交叉评审的范围控制维度提取角色越界"""
    for f in list(Path(specs_dir).glob("*-SUMMARY.md")) + [Path(specs_dir) / "SUMMARY.md"]:
        content = _read_file(f)
        if not content:
            continue
        if re.search(r'(?:范围控制|scope.?control).*(?:越界|violation|偏离)', content, re.I):
            matches = re.findall(r'.*(?:范围控制|scope.?control).*', content, re.I)
            return matches[:2]
    return []


def _extract_blast_radius(specs_dir):
    """从 SUMMARY.md 提取 blast radius 告警"""
    for f in list(Path(specs_dir).glob("*-SUMMARY.md")) + [Path(specs_dir) / "SUMMARY.md"]:
        content = _read_file(f)
        if not content:
            continue
        if re.search(r'(?:blast.?radius|影响范围).*(?:>\s*5|超过\s*5|\d+\s*文件)', content, re.I):
            matches = re.findall(r'.*(?:blast.?radius|影响范围).*', content, re.I)
            return matches[:2]
    return []


def _extract_tool_pitfall(specs_dir):
    """从 PROGRESS.md 的已排除方案提取工具坑点"""
    content = ""
    for f in Path(specs_dir).glob("*-PROGRESS.md"):
        content += _read_file(f)
    if not content:
        return []
    evidence = []
    # 提取"已排除方案"
    excluded = re.findall(r'(?:已排除方案|排除).*?\n((?:\s*-.+\n)+)', content)
    for block in excluded:
        lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
        evidence.extend(lines[:2])
    return evidence[:3]


# ── 核心逻辑 ──────────────────────────────────────────────

STRONG_EXTRACTORS = {
    "review_rework": _extract_review_rework,
    "test_repeated": _extract_test_repeated,
    "hotfix_trigger": _extract_hotfix,
    "gate_blocked": _extract_gate_blocked,
    "gate_blocked_trace": lambda sd: [],  # 由 detect() 单独调用，不自动执行
}

MEDIUM_EXTRACTORS = {
    "similar_error": _extract_similar_error,
    "role_violation": _extract_role_violation,
    "blast_radius": _extract_blast_radius,
    "tool_pitfall": _extract_tool_pitfall,
}


def detect(specs_dir, traces_path=None):
    """从工件目录提取信号，返回信号报告"""
    specs_path = Path(specs_dir)
    change_id = specs_path.name

    strong_signals = []
    for sig_type, extractor in STRONG_EXTRACTORS.items():
        if sig_type == "gate_blocked_trace":
            continue  # 由下方 trace 逻辑单独处理
        evidence = extractor(specs_dir)
        if evidence:
            attr = ATTRIBUTIONS.get(sig_type, {})
            strong_signals.append({
                "type": sig_type,
                "level": "strong",
                "description": STRONG_SIGNALS[sig_type],
                "evidence": evidence,
                "source": sig_type,
                "attribution": attr.get("tag", ""),
                "reason": attr.get("reason", ""),
                "advice": attr.get("advice", ""),
            })

    medium_signals = []

    # Trace 信号（优先于正则，source="trace" 标记）
    if traces_path:
        trace_evidence = _extract_gate_blocked_trace(specs_dir, traces_path)
        if trace_evidence:
            attr = ATTRIBUTIONS.get("gate_blocked_trace", {})
            strong_signals.append({
                "type": "gate_blocked_trace",
                "level": "strong",
                "description": STRONG_SIGNALS["gate_blocked_trace"],
                "evidence": trace_evidence,
                "source": "trace",
                "attribution": attr.get("tag", ""),
                "reason": attr.get("reason", ""),
                "advice": attr.get("advice", ""),
            })

    for sig_type, extractor in MEDIUM_EXTRACTORS.items():
        evidence = extractor(specs_dir)
        if evidence:
            attr = ATTRIBUTIONS.get(sig_type, {})
            medium_signals.append({
                "type": sig_type,
                "level": "medium",
                "description": MEDIUM_SIGNALS[sig_type],
                "evidence": evidence,
                "source": sig_type,
                "attribution": attr.get("tag", ""),
                "reason": attr.get("reason", ""),
                "advice": attr.get("advice", ""),
            })

    # Cheap Gate（借鉴 signal_detector.py:157-160）
    gate_passed = len(strong_signals) >= 1 or len(medium_signals) >= 2

    # 归因摘要：统计各归因标签出现次数
    attribution_summary = {}
    for sig in strong_signals + medium_signals:
        tag = sig.get("attribution", "")
        if tag:
            attribution_summary[tag] = attribution_summary.get(tag, 0) + 1

    return {
        "change_id": change_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "strong_signals": strong_signals,
        "medium_signals": medium_signals,
        "strong_count": len(strong_signals),
        "medium_count": len(medium_signals),
        "attribution_summary": attribution_summary,
        "should_reflect": gate_passed,
        "gate_passed": gate_passed,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def format_text_output(result):
    """将信号检测结果格式化为可读的文本报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("进化信号检测报告")
    lines.append("=" * 60)
    lines.append("")

    # Change ID 和日期
    lines.append(f"Change ID : {result.get('change_id', 'N/A')}")
    lines.append(f"日期       : {result.get('date', 'N/A')}")
    lines.append("")

    # 强信号
    strong = result.get("strong_signals", [])
    strong_count = result.get("strong_count", len(strong))
    lines.append(f"── 强信号 ({strong_count}) ──")
    if strong:
        for i, sig in enumerate(strong, 1):
            lines.append(f"  [{i}] 类型: {sig.get('type', '')}")
            lines.append(f"      描述: {sig.get('description', '')}")
            for ev in sig.get("evidence", []):
                lines.append(f"      证据: {ev}")
            lines.append(f"      归因: {sig.get('attribution', '')}")
            lines.append("")
    else:
        lines.append("  (无)")
        lines.append("")

    # 中信号
    medium = result.get("medium_signals", [])
    medium_count = result.get("medium_count", len(medium))
    lines.append(f"── 中信号 ({medium_count}) ──")
    if medium:
        for i, sig in enumerate(medium, 1):
            lines.append(f"  [{i}] 类型: {sig.get('type', '')}")
            lines.append(f"      描述: {sig.get('description', '')}")
            for ev in sig.get("evidence", []):
                lines.append(f"      证据: {ev}")
            lines.append(f"      归因: {sig.get('attribution', '')}")
            lines.append("")
    else:
        lines.append("  (无)")
        lines.append("")

    # 闸门判定
    gate = result.get("gate_passed", False)
    gate_label = "是" if gate else "否"
    lines.append(f"── 是否值得反思: {gate_label} ──")
    lines.append("")

    # 归因摘要
    attr_summary = result.get("attribution_summary", {})
    lines.append("── 归因摘要 ──")
    if attr_summary:
        for tag, count in attr_summary.items():
            lines.append(f"  {tag}: {count} 次")
    else:
        lines.append("  (无)")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="进化信号检测器")
    parser.add_argument("--specs-dir", required=True, help=".specs/<change-id> 目录路径")
    parser.add_argument("--traces", help="traces.jsonl 路径（可选，启用 trace 信号提取）")
    parser.add_argument("--output", help="输出路径（默认 stdout）")
    parser.add_argument("--format", choices=["text", "json"], default="json",
                        dest="fmt", help="输出格式（默认 json）")
    parser.add_argument("--write-lessons", action="store_true",
                        help="将 strong_signals 写入 LESSONS.md（AC-6）")
    args = parser.parse_args()

    result = detect(args.specs_dir, traces_path=args.traces)

    if args.fmt == "text":
        output = format_text_output(result)
    else:
        output = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        tmp = Path(args.output).with_suffix(".tmp")
        tmp.write_text(output, encoding="utf-8")
        os.replace(tmp, Path(args.output))
        print(f"信号已保存到 {args.output}", file=sys.stderr)
    else:
        print(output)

    if args.write_lessons:
        if result.get("strong_signals"):
            from lessons_writer import write
            lessons_path = str(Path(args.specs_dir).parent / "LESSONS.md")
            wr = write(result, lessons_path)
            print(f"LESSONS 写入: {wr}", file=sys.stderr)
        else:
            print("无强信号，跳过 LESSONS 写入", file=sys.stderr)


if __name__ == "__main__":
    main()
