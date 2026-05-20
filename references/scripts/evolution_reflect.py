#!/usr/bin/env python3
"""进化反思器 — 从信号生成可操作的改进假设

借鉴进化引擎 reflector.py 的信号→假设→签名去重→目标路由→置信度/风险评估。
将信号转化为假设（root_cause + action_type + target_file + proposed_change），
通过 risk×confidence 决策矩阵判断是否可自动采纳。

用法：
    python3 evolution_reflect.py --signals .specs/evolution/<change-id>-signals.json
    python3 evolution_reflect.py --signals signals.json --output hypotheses.json
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


# ── action_type 风险等级 ──────────────────────────────────

RISK_RULES = {
    "modify_stage": "medium",
    "modify_artifact": "medium",
    "modify_config": "critical",
    "add_lesson": "low",
    "modify_script": "high",
    "modify_review_checklist": "low",
}

# 顿悟触发阈值：同一 signature 出现此次数后生成持久洞察
INSIGHT_THRESHOLD = 3

# ── 优先级分级定义 ──────────────────────────────────────────
# P1-P6 优先级映射条件：key=优先级, value=dict(level, label, condition_check)
PRIORITY_LEVELS = {
    "P1": {
        "level": 1,
        "label": "修崩溃",
        "signal_types": {"gate_blocked", "hotfix_trigger"},
        "extra_condition": "attribution_freq_gte_2",  # 归因频率≥2
    },
    "P2": {
        "level": 2,
        "label": "利用成功",
        "signal_types": set(),  # CAPTURE 策略信号，由 health_score≥8.5 判断
        "extra_condition": "capture_health_gte_8_5",
    },
    "P3": {
        "level": 3,
        "label": "攻克持久失败",
        "signal_types": set(),  # 由 signature 历史次数≥3 判断
        "extra_condition": "signature_history_gte_3",
    },
    "P4": {
        "level": 4,
        "label": "探索新方向",
        "signal_types": set(),  # 新信号类型 或 P1-P3 无 evidence 降级
        "extra_condition": "new_signal_or_demoted",
    },
    "P5": {
        "level": 5,
        "label": "简化",
        "signal_types": {"blast_radius", "similar_error"},
        "extra_condition": "frequency_eq_1",
    },
    "P6": {
        "level": 6,
        "label": "激进变异",
        "signal_types": set(),  # 用户显式要求，无历史数据
        "extra_condition": "user_explicit_no_history",
    },
}

# 信号类型 → action_type 映射
SIGNAL_ACTION_MAP = {
    "review_rework": ("modify_stage", 0.80, "交叉评审反复未通过说明阶段指南不够明确"),
    "test_repeated": ("modify_stage", 0.78, "测试反复失败说明开发阶段的验证步骤不足"),
    "hotfix_trigger": ("add_lesson", 0.90, "热修触发说明失败模式值得长期记住"),
    "user_correction": ("modify_stage", 0.82, "用户纠正说明流程与预期不匹配"),
    "gate_blocked": ("modify_stage", 0.75, "闸门阻断说明前置条件定义需要调整"),
    "similar_error": ("add_lesson", 0.85, "重复犯同样错误说明 LESSONS 不够突出或检索不足"),
    "role_violation": ("modify_artifact", 0.72, "角色越界说明红线提醒不够强"),
    "blast_radius": ("modify_artifact", 0.70, "blast radius 触发说明任务拆分粒度过大"),
    "tool_pitfall": ("add_lesson", 0.88, "工具坑点值得记录到 LESSONS"),
}

# 根因映射
ROOT_CAUSES = {
    "review_rework": "阶段指南中质量标准定义不够具体，导致反复返工",
    "test_repeated": "开发阶段的 TDD 红绿环或 verify 命令覆盖不足",
    "hotfix_trigger": "测试阶段未覆盖到该场景，导致问题泄漏到生产",
    "user_correction": "流程输出与用户期望不一致，缺少确认节点",
    "gate_blocked": "闸门前置条件与实际工件不完全匹配",
    "similar_error": "LESSONS 检索机制未被有效使用，或教训不够具体",
    "role_violation": "角色红线提醒时机不对（太晚或太弱）",
    "blast_radius": "任务拆分粒度过大，单任务改动文件过多",
    "tool_pitfall": "工具使用文档缺失关键注意事项",
}


def _is_auto_approve_eligible(risk, confidence):
    """risk×confidence 决策（借鉴 reflector.py:172-180）"""
    if risk == "critical":
        return False
    if risk == "high":
        return confidence >= 0.80
    if risk == "medium":
        return confidence >= 0.85
    if risk == "low":
        return confidence >= 0.70
    return False


def _route_target(action_type):
    """目标文件路由（借鉴 reflector.py:149-170，映射到 flow-go 文件体系）"""
    mapping = {
        "modify_stage": "references/stages/",
        "modify_artifact": "references/artifacts/",
        "modify_config": ".flowgo-config",
        "add_lesson": ".specs/LESSONS.md",
        "modify_script": "references/scripts/",
        "modify_review_checklist": "references/artifacts/quality-artifacts.md",
    }
    return mapping.get(action_type, "references/stages/")


def _generate_signature(action_type, signal_type):
    """签名生成（借鉴 reflector.py:182-188）"""
    return f"{action_type}-{signal_type}"


def _build_proposed_change(hypothesis):
    """构建建议描述"""
    action = hypothesis.get("action_type", "")
    root = hypothesis.get("root_cause", "")
    signal = hypothesis.get("signal_refs", [])
    return (
        f"[evolution] {root}\n"
        f"  action: {action}\n"
        f"  target: {hypothesis.get('target_file', '')}\n"
        f"  signals: {', '.join(signal[:3])}"
    )


def _load_history(history_path=None):
    """读取历史假设 JSONL（每行一个假设报告的 JSON）"""
    if not history_path or not Path(history_path).exists():
        return []
    try:
        lines = Path(history_path).read_text(encoding="utf-8").strip().split("\n")
        records = []
        for line in lines:
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records
    except OSError:
        return []


def _count_signature_frequency(current_hypotheses, history_records):
    """统计每个 signature 的历史出现次数（按 change_id 去重，含本次）"""
    freq = {}
    # 先统计历史（同一 change_id 只计一次）
    seen_changes = {}
    for record in history_records:
        cid = record.get("change_id", "")
        for h in record.get("hypotheses", []):
            sig = h.get("signature", "")
            if sig:
                key = (sig, cid)
                if key not in seen_changes:
                    seen_changes[key] = True
                    freq[sig] = freq.get(sig, 0) + 1
    # 加上本次
    for h in current_hypotheses:
        sig = h.get("signature", "")
        if sig:
            freq[sig] = freq.get(sig, 0) + 1
    return freq


def _generate_insights(current_hypotheses, history_records):
    """顿悟机制：同一 signature 出现 ≥ INSIGHT_THRESHOLD 次时生成持久洞察"""
    freq = _count_signature_frequency(current_hypotheses, history_records)
    insights = []

    for h in current_hypotheses:
        sig = h.get("signature", "")
        count = freq.get(sig, 0)
        if count < INSIGHT_THRESHOLD:
            continue

        # 检查历史中是否已生成过该 signature 的洞察（避免重复）
        already_insight = False
        for record in history_records:
            for ins in record.get("insights", []):
                if ins.get("signature") == sig:
                    already_insight = True
                    break
            if already_insight:
                break
        if already_insight:
            continue

        # 收集同 signature 的所有历史假设 ID（可追溯进化谱系）
        source_ids = [h["id"] for h in [h] if h.get("id")]
        for record in history_records:
            for rh in record.get("hypotheses", []):
                if rh.get("signature") == sig and rh.get("id"):
                    source_ids.append(rh["id"])

        insights.append({
            "id": f"INS-{datetime.now().strftime('%Y%m%d')}-{sig[:12]}",
            "signature": sig,
            "source_hypothesis_ids": list(set(source_ids)),
            "trigger_count": count,
            "root_cause": h.get("root_cause", ""),
            "advice": h.get("proposed_change", ""),
            "action_type": h.get("action_type", ""),
            "target_file": h.get("target_file", ""),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "status": "pending_approval",
        })

    return insights


def _rank_hypotheses(hypotheses, history_records):
    """为每个假设分配 P1-P6 优先级，按 P1→P6 排序返回。

    遍历每个 hypothesis，根据信号类型 + 归因频率分配优先级。
    P1-P3 条目必须有 trace_evidence（从 traces.jsonl 或 PROGRESS.md 提取），
    无 trace_evidence 则降级到 P4，标注 demoted=true + demoted_from。
    """
    sig_freq = _count_signature_frequency(hypotheses, history_records)

    # 收集历史中所有出现过的 signal_type，用于判断"新信号类型"
    historical_signal_types = set()
    for record in history_records:
        for h in record.get("hypotheses", []):
            for ref in h.get("signal_refs", []):
                historical_signal_types.add(ref)

    ranked = []

    for h in hypotheses:
        sig_type = h.get("signal_refs", [""])[0] if h.get("signal_refs") else ""
        signature = h.get("signature", "")
        freq = sig_freq.get(signature, 1)

        # 尝试提取 trace_evidence
        trace_evidence = _extract_trace_evidence(h, history_records)

        priority = None
        demoted = False
        demoted_from = None

        # ── P1: 修崩溃 — gate_blocked/hotfix_trigger + 归因频率≥2 ──
        p1_types = PRIORITY_LEVELS["P1"]["signal_types"]
        if sig_type in p1_types and freq >= 2:
            priority = "P1"

        # ── P3: 攻克持久失败 — signature 历史≥3次 ──
        if priority is None and freq >= 3:
            priority = "P3"

        # ── P5: 简化 — blast_radius/similar_error + 频率=1 ──
        p5_types = PRIORITY_LEVELS["P5"]["signal_types"]
        if priority is None and sig_type in p5_types and freq == 1:
            priority = "P5"

        # ── P2: 利用成功 — CAPTURE 策略 + 健康评分≥8.5 ──
        #   （CAPTURE 模式的假设 origin=CAPTURE，此处检查 origin）
        if priority is None and h.get("origin") == "CAPTURE":
            priority = "P2"

        # ── P4: 探索新方向 — 新信号类型 ──
        if priority is None and sig_type and sig_type not in historical_signal_types:
            priority = "P4"

        # ── 兜底：无匹配条件的统一归到 P4 ──
        if priority is None:
            priority = "P4"

        # ── P1-P3 无 trace_evidence → 降级到 P4 ──
        if priority in ("P1", "P2", "P3") and not trace_evidence:
            demoted = True
            demoted_from = priority
            priority = "P4"

        ranked.append({
            "hypothesis_id": h.get("id", ""),
            "priority": priority,
            "label": PRIORITY_LEVELS[priority]["label"],
            "signature": signature,
            "signal_type": sig_type,
            "trace_evidence": trace_evidence,
            "demoted": demoted,
            "demoted_from": demoted_from,
        })

    # 按 P1→P6 排序
    ranked.sort(key=lambda x: PRIORITY_LEVELS[x["priority"]]["level"])

    return ranked


def _extract_trace_evidence(hypothesis, history_records):
    """从历史记录中提取 trace_evidence（traces.jsonl 或假设的 signal_evidence）"""
    evidence = []

    # 从假设本身的 signal_evidence 提取
    for ev in hypothesis.get("signal_evidence", []):
        evidence.append(f"signal: {ev}")

    # 从历史记录中查找同 signature 的证据
    signature = hypothesis.get("signature", "")
    for record in history_records:
        for h in record.get("hypotheses", []):
            if h.get("signature") == signature:
                for ev in h.get("signal_evidence", []):
                    trace = f"history[{record.get('change_id', '')}]: {ev}"
                    if trace not in evidence:
                        evidence.append(trace)

    return evidence


def _analyze_signal(signal):
    """从单个信号生成假设（借鉴 reflector.py:93-130 _analyze_signal）"""
    sig_type = signal.get("type", "")
    sig_id = signal.get("type", "") + "-" + str(hash(tuple(signal.get("evidence", []))))[:8]

    mapping = SIGNAL_ACTION_MAP.get(sig_type)
    if not mapping:
        return None

    action_type, confidence, reasoning = mapping
    risk = RISK_RULES.get(action_type, "medium")
    root_cause = ROOT_CAUSES.get(sig_type, "信号不足以定位根因")

    hypothesis = {
        "id": f"H{datetime.now().strftime('%Y%m%d')}{hash(sig_id) % 1000:03d}",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "origin": "FIX",
        "parent_hypothesis_id": None,
        "signal_refs": [sig_type],
        "signal_evidence": signal.get("evidence", [])[:3],
        "root_cause": root_cause,
        "action_type": action_type,
        "confidence": round(confidence, 2),
        "risk": risk,
        "reasoning": reasoning,
        "auto_approve_eligible": _is_auto_approve_eligible(risk, confidence),
        "status": "pending",
    }
    hypothesis["target_file"] = _route_target(action_type)
    hypothesis["signature"] = _generate_signature(action_type, sig_type)
    hypothesis["proposed_change"] = _build_proposed_change(hypothesis)
    return hypothesis


def _deduplicate(hypotheses):
    """签名去重（借鉴 reflector.py:132-148 _deduplicate）"""
    merged = {}
    for h in hypotheses:
        sig = h.get("signature", "")
        if sig not in merged:
            merged[sig] = h
            continue
        existing = merged[sig]
        # 合并信号引用和父假设链
        refs = list(set(existing.get("signal_refs", []) + h.get("signal_refs", [])))
        existing["signal_refs"] = refs
        if h.get("id"):
            parents = existing.get("parent_hypothesis_id") or []
            parents.append(h["id"])
            existing["parent_hypothesis_id"] = list(set(parents))
        existing["confidence"] = round(max(
            float(existing.get("confidence", 0)),
            float(h.get("confidence", 0)),
        ), 2)
        existing["auto_approve_eligible"] = _is_auto_approve_eligible(
            existing.get("risk", "medium"),
            existing["confidence"],
        )

    deduped = list(merged.values())
    # 收集旧→新 ID 映射，避免 parent_hypothesis_id 引用断裂
    id_map = {}
    for idx, h in enumerate(deduped, 1):
        old_id = h.get("id", "")
        new_id = f"H{datetime.now().strftime('%Y%m%d')}{idx:03d}"
        if old_id:
            id_map[old_id] = new_id
        h["id"] = new_id
    # 重映射 parent 引用到新 ID
    for h in deduped:
        parents = h.get("parent_hypothesis_id")
        if parents and isinstance(parents, list):
            h["parent_hypothesis_id"] = [id_map.get(pid, pid) for pid in parents]
    return deduped


def reflect(signals_payload, history_path=None):
    """从信号报告生成假设清单，含顿悟机制"""
    hypotheses = []
    for signal in signals_payload.get("strong_signals", []) + signals_payload.get("medium_signals", []):
        hypothesis = _analyze_signal(signal)
        if hypothesis:
            hypotheses.append(hypothesis)

    hypotheses = _deduplicate(hypotheses)

    # 顿悟机制：读取历史，检查频率，生成洞察
    history_records = _load_history(history_path)
    insights = _generate_insights(hypotheses, history_records)

    # 分离可自动采纳和需确认的
    auto_approve = [h for h in hypotheses if h.get("auto_approve_eligible")]
    needs_approval = [h for h in hypotheses if not h.get("auto_approve_eligible")]

    # 优先级排序：P1→P6
    priority_ranking = _rank_hypotheses(hypotheses, history_records)

    return {
        "change_id": signals_payload.get("change_id", ""),
        "date": signals_payload.get("date", datetime.now().strftime("%Y-%m-%d")),
        "signal_count": signals_payload.get("strong_count", 0) + signals_payload.get("medium_count", 0),
        "hypothesis_count": len(hypotheses),
        "auto_approve_count": len(auto_approve),
        "needs_approval_count": len(needs_approval),
        "insight_count": len(insights),
        "hypotheses": hypotheses,
        "auto_approve": auto_approve,
        "needs_approval": needs_approval,
        "insights": insights,
        "priority_ranking": priority_ranking,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


# ── CAPTURE 模式（成功策略捕获）──────────────────────────

CAPTURE_HEALTH_THRESHOLD = 8.0


def _read_artifact(path):
    """安全读取工件文件（capture 模式专用）"""
    try:
        return Path(path).read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return ""


def _infer_task_type(task_content):
    """从 TASK.md 推断任务类型"""
    text = task_content.lower()
    if any(kw in text for kw in ["修复", "fix", "bug", "缺陷", "hotfix"]):
        return "bugfix"
    if any(kw in text for kw in ["重构", "refactor", "整理结构", "优化结构"]):
        return "refactor"
    if any(kw in text for kw in ["文档", "doc", "readme", "注释"]):
        return "doc"
    return "feature"


def _extract_approach(summary_content):
    """从 SUMMARY.md 提取成功做法描述"""
    if not summary_content:
        return ""
    match = re.search(r'##\s*做了什么\s*\n(.+?)(?=\n##|\Z)', summary_content, re.S)
    if match:
        return match.group(1).strip()[:200]
    return ""


def _extract_success_evidence(summary_content):
    """从 SUMMARY.md 提取成功指标"""
    evidence = []
    if not summary_content:
        return evidence
    if re.search(r'verify\s*通过率.*1/1.*首次', summary_content, re.I):
        evidence.append("verify 首次通过")
    review_round = re.search(r'评审轮次\s*[:：]?\s*(\d+)/3', summary_content)
    if review_round and int(review_round.group(1)) == 1:
        evidence.append("交叉评审 1 轮通过")
    reuse_count = len(re.findall(r'沿用', summary_content))
    if reuse_count:
        evidence.append(f"沿用既有抽象 {reuse_count} 个")
    return evidence


def _score_strategy(health_score, summary_content):
    """策略打分（0-100）"""
    base = health_score * 10
    review_round = re.search(r'评审轮次\s*[:：]?\s*(\d+)/3', summary_content or "")
    if review_round:
        rounds = int(review_round.group(1))
        if rounds == 1:
            base += 8
        elif rounds == 2:
            base += 2
    if re.search(r'verify\s*通过率.*1/1.*首次', summary_content or "", re.I):
        base += 5
    return min(round(base), 100)


def _extract_context(specs_dir):
    """从 DESIGN.md 提取 context（problem, architecture_pattern, key_decisions）"""
    design_path = Path(specs_dir) / "DESIGN.md"
    content = _read_artifact(design_path)
    if not content:
        return None

    context = {}

    # problem：架构图 section 后的首段文本
    arch_match = re.search(r'##\s*1[\.\s]*架构图\s*\n.*?```\s*\n', content, re.S)
    if arch_match:
        after_code = content[arch_match.end():]
        para_match = re.search(r'\n\s*\n\s*([^\n#`]{10,})', after_code, re.S)
        if para_match:
            text = para_match.group(1).strip().replace("\n", " ")
            context["problem"] = text[:100]
    if "problem" not in context:
        context["problem"] = None

    # architecture_pattern：从架构图中提取主要模式关键词
    arch_block_match = re.search(r'##\s*1[\.\s]*架构图\s*\n(.*?)```', content, re.S)
    if arch_block_match:
        block = arch_block_match.group(1)
        patterns = ["脚本调用链", "文件驱动", "管道", "分层", "事件驱动", "插件"]
        for p in patterns:
            if p in block:
                context["architecture_pattern"] = p
                break
    if "architecture_pattern" not in context:
        context["architecture_pattern"] = None

    # key_decisions：ADR 标题行
    adr_titles = re.findall(r'###\s*(ADR-\d+\s+.+)', content)
    context["key_decisions"] = adr_titles[:3] if adr_titles else None

    return context


def capture(specs_dir, health_score, output_path=None, strategies_path=None):
    """CAPTURE 模式：从成功变更提取策略，存入 strategies.jsonl"""
    specs_path = Path(specs_dir)
    change_id = specs_path.name

    if health_score < CAPTURE_HEALTH_THRESHOLD:
        return {"captured": False, "reason": f"健康评分 {health_score:.1f} < {CAPTURE_HEALTH_THRESHOLD}"}

    task_content = _read_artifact(specs_path / "TASK.md")
    summary_content = ""
    for f in specs_path.glob("*-SUMMARY.md"):
        summary_content += _read_artifact(f) + "\n"
    if not summary_content:
        summary_content = _read_artifact(specs_path / "SUMMARY.md")

    task_type = _infer_task_type(task_content)
    approach = _extract_approach(summary_content)
    evidence = _extract_success_evidence(summary_content)
    score = _score_strategy(health_score, summary_content)

    if not approach:
        return {"captured": False, "reason": "无法从 SUMMARY.md 提取做法描述"}

    strategy = {
        "strategy_id": f"S-{datetime.now().strftime('%Y%m%d')}-{change_id[:12]}",
        "change_id": change_id,
        "task_type": task_type,
        "approach": approach,
        "score": score,
        "evidence": evidence,
        "origin": "CAPTURE",
        "health_score": health_score,
        "context": _extract_context(specs_dir),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }

    strat_path = Path(strategies_path or specs_path.parent / "evolution" / "strategies.jsonl")
    strat_path.parent.mkdir(parents=True, exist_ok=True)
    with open(strat_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(strategy, ensure_ascii=False) + "\n")

    result = {
        "captured": True,
        "change_id": change_id,
        "strategy": strategy,
    }

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return result


# ── CLI 入口 ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="进化反思器 + 策略捕获")
    parser.add_argument("--mode", choices=["reflect", "capture"], default="reflect",
                        help="运行模式（默认 reflect）")
    parser.add_argument("--output", help="输出 JSON 路径（默认 stdout）")
    # reflect 模式
    parser.add_argument("--signals", help="信号 JSON 文件路径（reflect 模式）")
    parser.add_argument("--history", default=None, help="历史假设 JSONL 路径")
    # capture 模式
    parser.add_argument("--specs-dir", help=".specs/<change-id> 目录路径（capture 模式）")
    parser.add_argument("--health-score", type=float, help="健康评分（capture 模式）")
    parser.add_argument("--strategies", default=None, help="策略库 JSONL 路径")
    args = parser.parse_args()

    if args.mode == "capture":
        if not args.specs_dir or not args.health_score:
            parser.error("capture 模式需要 --specs-dir 和 --health-score")
        result = capture(args.specs_dir, args.health_score, args.output, args.strategies)
        if not args.output:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # reflect 模式
    if not args.signals:
        parser.error("reflect 模式需要 --signals")
    try:
        signals_payload = json.loads(Path(args.signals).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"错误：无法读取信号文件 — {e}", file=sys.stderr)
        sys.exit(1)

    result = reflect(signals_payload, history_path=args.history)
    output = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        tmp = Path(args.output).with_suffix(".json.tmp")
        tmp.write_text(output, encoding="utf-8")
        os.replace(tmp, Path(args.output))
        if args.history:
            try:
                Path(args.history).parent.mkdir(parents=True, exist_ok=True)
                compact = json.dumps(result, ensure_ascii=False)
                with open(args.history, "a", encoding="utf-8") as hf:
                    hf.write(compact + "\n")
            except OSError:
                pass
        print(f"假设已保存到 {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
