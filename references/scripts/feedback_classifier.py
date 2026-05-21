#!/usr/bin/env python3
"""用户输入分类器 — 从 user-inputs.jsonl 提取反馈并分类

读取 .specs/<id>/user-inputs.jsonl，将用户输入分为四类：
- project：项目层反馈（代码/设计/架构改进）
- skill：skill 层反馈（流程/工具/阶段/角色改进）
- preference：偏好反馈（用户习惯/风格）
- noise：非反馈（确认/问候/纯指令）

skill 反馈自动追加到 .specs/evolution/skill-feedback.jsonl。

用法：
    python3 feedback_classifier.py --specs-dir .specs/<id>
    python3 feedback_classifier.py --specs-dir .specs/<id> --output .specs/evolution/<id>-classified.json
    python3 feedback_classifier.py --specs-dir .specs/<id> --complexity LITE
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


# ── 纯指令排除模式 ─────────────────────────────────────────

COMMAND_PATTERNS = [
    r'^go$', r'^/go$', r'^next$', r'^下一步$', r'^继续$',
    r'^ok$', r'^好$', r'^确认$', r'^是$', r'^对$', r'^可以$',
    r'^执行\s*T\d+$', r'^跑\s*T\d+$', r'^测试$', r'^审查$',
    r'^部署$', r'^验收$', r'^归档$', r'^收工$', r'^这个做完了$',
    r'^需求$', r'^设计$', r'^拆任务$', r'^保存$', r'^save$',
    r'^热修$', r'^hotfix$', r'^废弃$', r'^放弃$',
    r'^中断$', r'^暂停$', r'^并行$', r'^排队$',
    r'^飞轮巡检$', r'^飞轮报告$', r'^周报$',
    r'^整理$', r'^neat$', r'^同步$', r'^进化分析$',
    r'^反思一下$', r'^检查进化$', r'^进化信号$', r'^进化状态$',
    r'^回溯$', r'^recall$', r'^接着上次$', r'^resume$',
    r'^清理归档$', r'^归档维护$',
    r'^/lite$', r'^/heavy$',
]

# ── 分类关键词 ────────────────────────────────────────────

SKILL_KEYWORDS = [
    '流程', '阶段', '角色', '闸门', '工件', 'skill', 'flow-go',
    '路由', '自检', '角色红线', '交叉评审', '太复杂', '太简单',
    '太繁琐', '太冗长', '没必要', '多余', '应该', '建议',
    '改为', '换成', '优化流程', '简化流程', '流程改进',
    '阶段改进', '渐进式披露', '单一职责',
]

PROJECT_KEYWORDS = [
    '代码', '函数', '模块', 'API', '数据库', '测试', '性能',
    '安全', 'buffer', 'leak', 'crash', 'bug', '错误',
    '重构', '接口', '类型', '变量', '配置文件', '部署配置',
    '组件', '服务', '微服务', '缓存', '队列', '日志',
]

PREFERENCE_KEYWORDS = [
    '以后', '总是', '不要', '偏好', '风格', '默认',
    '习惯', '总是这样', '以后都用', '以后不要',
]

# 开发/测试阶段的代码关键词，用于上下文增强
CODE_STAGE_CONTEXT_KEYWORDS = [
    'def ', 'class ', 'import ', 'from ', 'return ',
    'function', 'const ', 'let ', 'var ', 'async ',
    'try', 'catch', 'if ', 'for ', 'while ',
]


def _read_user_inputs(specs_dir):
    """读取 user-inputs.jsonl"""
    path = Path(specs_dir) / "user-inputs.jsonl"
    if not path.is_file():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def _is_command(text):
    """判断是否是纯指令输入"""
    t = text.strip().lower()
    for pattern in COMMAND_PATTERNS:
        if re.match(pattern, t, re.I):
            return True
    # 短于 3 字且无实质内容
    if len(t) <= 2:
        return True
    return False


def _count_keyword_hits(text, keywords):
    """统计文本中命中的关键词数量"""
    t = text.lower()
    return sum(1 for kw in keywords if kw.lower() in t)


def _classify_single(record, complexity="STANDARD"):
    """分类单条用户输入"""
    text = record.get("input", "")
    stage = record.get("stage", "")

    if _is_command(text):
        return None  # noise，不产出记录

    skill_hits = _count_keyword_hits(text, SKILL_KEYWORDS)
    project_hits = _count_keyword_hits(text, PROJECT_KEYWORDS)
    preference_hits = _count_keyword_hits(text, PREFERENCE_KEYWORDS)

    # LITE 模式：只检测高置信度 skill 反馈
    if complexity == "LITE":
        if skill_hits < 2:
            return None

    # 上下文增强：开发/测试阶段 + 代码关键词 → 优先 project
    is_code_stage = any(s in stage for s in ["3-开发", "4-测试"])
    has_code_context = any(kw in text for kw in CODE_STAGE_CONTEXT_KEYWORDS)
    if is_code_stage and has_code_context and project_hits > 0:
        category = "project"
        confidence = min(0.6 + project_hits * 0.1, 0.95)
    # skill 关键词命中最多
    elif skill_hits > project_hits and skill_hits > preference_hits:
        category = "skill"
        confidence = min(0.6 + skill_hits * 0.1, 0.95)
    # preference 关键词命中最多
    elif preference_hits > skill_hits and preference_hits > project_hits:
        category = "preference"
        confidence = min(0.5 + preference_hits * 0.15, 0.9)
    # project 关键词命中最多
    elif project_hits > 0:
        category = "project"
        confidence = min(0.5 + project_hits * 0.1, 0.9)
    # skill 有命中但不高
    elif skill_hits > 0:
        category = "skill"
        confidence = min(0.4 + skill_hits * 0.1, 0.7)
    else:
        return None  # noise

    return {
        "category": category,
        "content": text[:200],
        "confidence": round(confidence, 2),
        "stage": stage,
        "change_id": record.get("change_id", ""),
        "ts": record.get("ts", ""),
    }


def classify(specs_dir, complexity="STANDARD"):
    """分类用户输入，返回分类结果"""
    records = _read_user_inputs(specs_dir)
    results = []

    for record in records:
        classified = _classify_single(record, complexity)
        if classified is not None:
            results.append(classified)

    return results


def _write_skill_feedback(classified_results, evolution_dir):
    """将 skill 反馈追加到 skill-feedback.jsonl"""
    skill_items = [r for r in classified_results if r["category"] == "skill"]
    if not skill_items:
        return 0

    Path(evolution_dir).mkdir(parents=True, exist_ok=True)
    feedback_path = Path(evolution_dir) / "skill-feedback.jsonl"

    count = 0
    with open(feedback_path, "a", encoding="utf-8") as f:
        for item in skill_items:
            entry = {
                "change_id": item["change_id"],
                "content": item["content"],
                "confidence": item["confidence"],
                "stage": item["stage"],
                "ts": item["ts"],
                "classified_at": datetime.now().isoformat(timespec="seconds"),
                "processed": False,
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            count += 1

    return count


def format_text_output(result):
    """将分类结果格式化为可读文本"""
    lines = []
    lines.append("=" * 50)
    lines.append("用户输入分类报告")
    lines.append("=" * 50)
    lines.append("")

    # 统计概览
    stats = result.get("stats", {})
    lines.append(f"变更 ID: {result.get('change_id', '')}")
    lines.append(f"分类时间: {result.get('classified_at', '')}")
    lines.append(f"总输入数: {result.get('total_inputs', 0)}")
    lines.append(f"  project:    {stats.get('project', 0)}")
    lines.append(f"  skill:      {stats.get('skill', 0)}")
    lines.append(f"  preference: {stats.get('preference', 0)}")
    lines.append(f"  noise:      {stats.get('noise', 0)}")
    lines.append("")

    # 分类详情
    for i, item in enumerate(result.get("results", []), 1):
        lines.append(f"--- [{i}] {item['category'].upper()} (置信度 {item['confidence']}) ---")
        lines.append(f"  阶段: {item.get('stage', '')}")
        lines.append(f"  内容: {item.get('content', '')}")
        # 关键信号
        text = item.get("content", "")
        signals = []
        for kw in SKILL_KEYWORDS:
            if kw.lower() in text.lower():
                signals.append(kw)
        for kw in PROJECT_KEYWORDS:
            if kw.lower() in text.lower():
                signals.append(kw)
        for kw in PREFERENCE_KEYWORDS:
            if kw.lower() in text.lower():
                signals.append(kw)
        if signals:
            lines.append(f"  关键信号: {', '.join(signals)}")
        lines.append("")

    lines.append("=" * 50)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="用户输入分类器")
    parser.add_argument("--specs-dir", required=True, help=".specs/<id> 目录路径")
    parser.add_argument("--output", help="分类结果输出 JSON 路径")
    parser.add_argument("--complexity", choices=["LITE", "STANDARD", "HEAVY"],
                        default="STANDARD", help="复杂度级别（影响分类灵敏度）")
    parser.add_argument("--format", choices=["text", "json"], default="json",
                        dest="fmt", help="输出格式（text 或 json）")
    args = parser.parse_args()

    results = classify(args.specs_dir, args.complexity)

    # 统计
    stats = {"project": 0, "skill": 0, "preference": 0, "noise": 0}
    for r in results:
        stats[r["category"]] = stats.get(r["category"], 0) + 1
    total_inputs = len(_read_user_inputs(args.specs_dir))
    stats["noise"] = total_inputs - len(results)

    # 写入 skill 反馈
    evolution_dir = str(Path(args.specs_dir).parent / "evolution")
    skill_count = _write_skill_feedback(results, evolution_dir)

    # 输出
    output = {
        "change_id": Path(args.specs_dir).name,
        "classified_at": datetime.now().isoformat(timespec="seconds"),
        "total_inputs": total_inputs,
        "stats": stats,
        "results": results,
    }

    output_json = json.dumps(output, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output_json, encoding="utf-8")
        print(f"分类结果已保存到 {args.output}", file=sys.stderr)

    # 摘要输出
    print(f"📊 反馈分类：project {stats['project']} / skill {stats['skill']} / "
          f"preference {stats['preference']} / noise {stats['noise']}", file=sys.stderr)
    if skill_count > 0:
        print(f"skill 反馈已追加到 {evolution_dir}/skill-feedback.jsonl（{skill_count} 条）",
              file=sys.stderr)

    if not args.output:
        if args.fmt == "text":
            print(format_text_output(output))
        else:
            print(output_json)


if __name__ == "__main__":
    main()
