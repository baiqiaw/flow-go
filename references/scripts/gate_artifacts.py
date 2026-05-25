#!/usr/bin/env python3
"""工件检查 — 各阶段必需工件验证

从 gate_check.py 提取的 check_artifacts() 及其常量。
支持两个维度：
  - complexity（LITE/STANDARD/HEAVY）：影响闸门严格程度
  - path_mode（full/incremental/shortest）：影响经过的阶段和闸门工件列表
"""
import glob
import os
import re
import subprocess


# ── 完整路径（默认）各阶段必需工件 ──
STANDARD_GATES = {
    0: [],
    1: ["CHANGE.md", "REQUIREMENT.md"],
    2: ["REQUIREMENT.md", "DESIGN.md"],
    3: ["DESIGN.md", "TASK.md"],
    4: [],
    5: ["TEST.md"],
    6: ["REVIEW.md"],
    7: ["DEPLOY.md"],
}

# LITE 模式简化闸门
LITE_GATES = {
    0: [],
    1: [],       # LITE 跳过
    2: [],       # LITE 跳过
    3: ["CHANGE.md"],
    4: [],
    5: [],       # LITE 跳过
    6: [],       # LITE 跳过
    7: [],       # 由 4-测试通过 + CHANGE.md AC 替代
}

# HEAVY 同 STANDARD，额外标记 blast_radius 待检查
HEAVY_GATES = dict(STANDARD_GATES)

# ── 最短路径闸门（跳过 1-设计/2-任务/5-审查/6-部署） ──
# 最短路径只经过 0→3→4→7，其余阶段不进入不检查
SHORTEST_STANDARD_GATES = {
    0: [],
    3: ["CHANGE.md"],   # 仅需 CHANGE.md（含内联 AC），不检查 DESIGN.md / TASK.md
    4: [],               # 仅需代码已提交，不检查 SUMMARY.md
    7: [],               # 仅需 4-测试通过 + CHANGE.md AC 全部满足
}
SHORTEST_LITE_GATES = dict(SHORTEST_STANDARD_GATES)   # 最短路径已极度简化
SHORTEST_HEAVY_GATES = dict(SHORTEST_STANDARD_GATES)

# ── 增量路径闸门（跳过 6-部署） ──
# 经过 0→1→2→3→4→5→7
INCREMENTAL_STANDARD_GATES = {
    0: [],
    1: ["CHANGE.md", "REQUIREMENT.md"],
    2: ["REQUIREMENT.md", "DESIGN.md"],
    3: ["DESIGN.md", "TASK.md"],
    4: [],
    5: ["TEST.md"],
    7: [],   # 不需要 DEPLOY.md（跳过了 6-部署）
}
INCREMENTAL_LITE_GATES = {
    0: [],
    1: [],       # LITE 跳过
    2: [],       # LITE 跳过
    3: ["CHANGE.md"],
    4: [],
    5: [],       # LITE 跳过
    7: [],       # 不需要 DEPLOY.md
}
INCREMENTAL_HEAVY_GATES = dict(INCREMENTAL_STANDARD_GATES)

# 路径模式下跳过的阶段集合（用于报告提示）
SKIPPED_STAGES = {
    "full": set(),
    "incremental": {6},
    "shortest": {1, 2, 5, 6},
}


def _get_gate_table(complexity, path_mode):
    """根据复杂度和路径模式选择闸门表"""
    # 路径模式优先：不同路径模式使用不同的闸门表
    if path_mode == "shortest":
        if complexity == "lite":
            return SHORTEST_LITE_GATES
        elif complexity == "heavy":
            return SHORTEST_HEAVY_GATES
        else:
            return SHORTEST_STANDARD_GATES
    elif path_mode == "incremental":
        if complexity == "lite":
            return INCREMENTAL_LITE_GATES
        elif complexity == "heavy":
            return INCREMENTAL_HEAVY_GATES
        else:
            return INCREMENTAL_STANDARD_GATES
    else:
        # full（完整路径），使用原有逻辑
        if complexity == "lite":
            return LITE_GATES
        elif complexity == "heavy":
            return HEAVY_GATES
        else:
            return STANDARD_GATES


def check_artifacts(stage, specs_dir, complexity="standard", path_mode="full", project_dir=None):
    """工件检查模式

    Args:
        stage: 目标阶段编号 (0-7)
        specs_dir: .specs/<change-id> 目录路径
        complexity: LITE/standard/heavy
        path_mode: full/incremental/shortest
        project_dir: 项目根目录（可选，用于 git 状态检查）
    """
    # 阶段名称映射（用于交叉评审章节定位）
    STAGE_NAMES = {0: "需求", 1: "设计", 2: "任务"}
    gates = _get_gate_table(complexity, path_mode)
    required = gates.get(stage, [])

    # 如果阶段不在闸门表中，说明路径模式下跳过了该阶段
    if stage not in gates and stage != 0:
        return {
            "passed": True,
            "missing": [],
            "warnings": [f"阶段 {stage} 在 {path_mode} 路径模式下被跳过，无需闸门检查"],
            "info": [f"path_mode={path_mode}, skipped_stages={sorted(SKIPPED_STAGES.get(path_mode, set()))}"],
        }

    missing = []
    warnings = []

    for artifact in required:
        path = os.path.join(specs_dir, artifact)
        if not os.path.isfile(path):
            missing.append(artifact)
        elif os.path.getsize(path) == 0:
            missing.append(f"{artifact}（空文件）")

    if complexity == "heavy" and stage >= 3:
        warnings.append("HEAVY 模式：blast_radius 检查待执行（gate_check.py --mode blast-radius）")

    # 7-验收特殊检查：LITE 和最短路径都需要 CHANGE.md + TEST.md
    # 合并逻辑，避免 shortest+lite 组合重复添加
    if stage == 7 and (complexity == "lite" or path_mode == "shortest"):
        change_path = os.path.join(specs_dir, "CHANGE.md")
        label = "CHANGE.md（含内联 AC）" if path_mode == "shortest" else "CHANGE.md"
        if not os.path.isfile(change_path):
            missing.append(label)
        test_path = os.path.join(specs_dir, "TEST.md")
        if not os.path.isfile(test_path):
            wlabel = "最短路径" if path_mode == "shortest" else "LITE"
            warnings.append(f"{wlabel} 7-验收：TEST.md 不存在，无法确认测试通过")

    # ── 阶段 4 特殊检查：代码已提交 + SUMMARY.md ──
    if stage == 4:
        # 检查 SUMMARY.md（STANDARD/HEAVY，完整/增量路径）
        need_summary = (
            complexity in ("standard", "heavy")
            and path_mode in ("full", "incremental")
        )
        if need_summary:
            summary_files = glob.glob(os.path.join(specs_dir, "*-SUMMARY.md"))
            if not summary_files:
                missing.append("*-SUMMARY.md（开发阶段未产出任何任务摘要）")

        # 检查代码已提交（git diff HEAD）
        if project_dir and os.path.isdir(os.path.join(project_dir, ".git")):
            try:
                proc = subprocess.run(
                    ["git", "diff", "--name-only", "HEAD"],
                    cwd=project_dir,
                    capture_output=True, text=True, timeout=10,
                )
                changed = [f for f in proc.stdout.strip().split("\n") if f]
                if changed:
                    missing.append(
                        f"代码未提交（{len(changed)} 个文件有未提交变更：{', '.join(changed[:3])}）"
                    )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                warnings.append("无法检查 git 提交状态")

        # 检查是否有未完成的任务（PROGRESS 文件残留）
        progress_files = glob.glob(os.path.join(specs_dir, "*-PROGRESS.md"))
        if progress_files:
            missing.append(f"存在未完成任务（{len(progress_files)} 个 PROGRESS 文件）")

    # ── 交叉评审 PASS 验证（阶段 1/2/3 的进入闸门） ──
    # 验证上游阶段的交叉评审已在 <change-id>-REVIEW.md 中产出且 6 维全 PASS
    # 阶段 1 需要 0-需求 评审 PASS，阶段 2 需要 1-设计 评审 PASS，阶段 3 需要 2-任务 评审 PASS
    REVIEW_REQUIRED_STAGES = {1: 0, 2: 1, 3: 2}
    if stage in REVIEW_REQUIRED_STAGES and complexity != "lite" and path_mode in ("full", "incremental"):
        upstream_stage = REVIEW_REQUIRED_STAGES[stage]
        upstream_name = STAGE_NAMES.get(upstream_stage, str(upstream_stage))
        # 查找 <change-id>-REVIEW.md
        review_files = glob.glob(os.path.join(specs_dir, "*-REVIEW.md"))
        if not review_files:
            missing.append(f"<change-id>-REVIEW.md（缺少 {upstream_stage}-{upstream_name} 交叉评审报告）")
        else:
            review_path = review_files[0]
            try:
                with open(review_path, encoding="utf-8") as f:
                    content = f.read()
                # 宽松匹配上游阶段评审章节：容忍标题格式变体
                # 接受: "## 0-需求 评审", "### 0-需求 交叉评审", "## 0-需求阶段", "## 0-需求 交叉评审（第 1 轮）"
                section_pattern = rf"##?\s*{upstream_stage}-.*(?:评审|阶段)"
                section_match = re.search(section_pattern, content)
                if not section_match:
                    missing.append(
                        f"REVIEW.md 缺少 {upstream_stage}-{upstream_name} 评审章节"
                        f"（交叉评审未执行）"
                    )
                else:
                    # 提取该章节内容（到下一个 ## 级别标题或文件末尾）
                    section_start = section_match.start()
                    next_section = re.search(r"\n## ", content[section_start + len(section_match.group()):])
                    section = content[section_start:] if not next_section else content[section_start:section_start + len(section_match.group()) + next_section.start()]
                    # 检查评审矩阵中是否有 FAIL
                    fail_matches = re.findall(r"\|\s*(?:上游一致性|下游充分性|用户意图对齐|完备性|反幻觉|范围控制)\s*\|\s*FAIL", section)
                    pass_count = len(re.findall(r"\|\s*(?:上游一致性|下游充分性|用户意图对齐|完备性|反幻觉|范围控制)\s*\|\s*PASS", section))
                    if fail_matches:
                        missing.append(
                            f"REVIEW.md {upstream_stage}-{upstream_name} 评审有 {len(fail_matches)} 个 FAIL 维度"
                            f"（交叉评审未通过，需修复后重评）"
                        )
                    elif pass_count < 6:
                        missing.append(
                            f"REVIEW.md {upstream_stage}-{upstream_name} 评审矩阵不完整"
                            f"（仅 {pass_count}/6 维有 PASS 判定）"
                        )
            except (OSError, UnicodeDecodeError):
                warnings.append(f"无法读取 REVIEW.md 进行交叉评审验证")

    return {
        "passed": len(missing) == 0,
        "missing": missing,
        "warnings": warnings,
        "info": [f"path_mode={path_mode}"],
    }
